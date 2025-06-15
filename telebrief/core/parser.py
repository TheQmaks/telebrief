"""
Telegram channel parser module.
"""

import html
import re
import time
from datetime import datetime, timedelta
from typing import Any, cast

import html2text
import requests
import urllib3
from bs4 import BeautifulSoup, Tag

from ..models import Channel, ChannelInfo, Post
from ..models.constants import DEFAULT_USER_AGENT, EARLIEST_POST_ID, POST_ID_PARTS_COUNT
from ..utils import Config, ProgressLogger, get_logger
from ..utils.date_utils import parse_date

# Constants
DEFAULT_POSTS_BATCH_SIZE = 20  # Batch size for posts from Telegram
K_MULTIPLIER = 1_000
M_MULTIPLIER = 1_000_000
MIN_CHANNEL_NAME_LENGTH = 3

# Pre-compiled regular expressions for performance
VIEWS_CLEANUP_REGEX = re.compile(r"[^\d.]")
NUMBER_CLEANUP_REGEX = re.compile(r"[^\d.,]")
BEFORE_REGEX = re.compile(r"before=(\d+)")


class TelegramParser:
    """Telegram channel parser for extracting posts and metadata."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize parser with configuration."""
        self.config = config or Config()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        self.session = requests.Session()
        self._setup_session()

        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0
        self.html_converter.wrap_links = False

    def _setup_session(self) -> None:
        """Configure HTTP session with proxy and SSL settings."""
        self.session.headers.update({
            "User-Agent": DEFAULT_USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        })

        if self.config.network.use_proxy and self.config.network.proxy_url:
            self.session.proxies = {
                "http": self.config.network.proxy_url,
                "https": self.config.network.proxy_url,
            }
            self.logger.info(f"Using proxy: {self.config.network.proxy_url}")

        self.session.verify = self.config.network.verify_ssl

        if not self.config.network.verify_ssl:
            self.logger.warning("SSL verification disabled")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def parse_channel(self, channel_name: str, days: int | None = None) -> Channel:
        """
        Parse Telegram channel.

        Args:
            channel_name: Channel name (without @)
            days: Number of days to analyze

        Returns:
            Channel object with posts and metrics
        """
        channel_name = channel_name.lstrip("@")
        days = days or self.config.parsing.default_days

        if days <= 0:
            raise ValueError("Number of days must be positive")

        if len(channel_name) < MIN_CHANNEL_NAME_LENGTH or " " in channel_name:
            raise ValueError(f"Invalid channel name: @{channel_name}")

        self.logger.info(f"Parsing @{channel_name} for {days} days")

        start_time = time.time()

        try:
            channel_info = self._get_channel_info(channel_name)
            self.logger.info(
                f"Channel found: {channel_info.name} ({channel_info.subscribers:,} subscribers)"
            )

            posts, latest_post_id = self._get_posts(channel_name, days)
            self.logger.info(f"Collected {len(posts)} posts for {days} days")

            channel = Channel(info=channel_info, posts=posts)

            if self.config.parsing.fetch_age_info:
                self._get_channel_age_info(channel.info, latest_post_id)

            elapsed_time = time.time() - start_time
            self.logger.info(
                f"Parsing channel @{channel_name} completed successfully in {elapsed_time:.2f} sec"
            )
            return channel

        except Exception as e:
            self.logger.error(f"Error parsing channel @{channel_name}: {e}")
            raise

    def parse_multiple_channels(
        self, channel_names: list[str], days: int | None = None
    ) -> dict[str, Channel]:
        """
        Parse multiple channels.

        Args:
            channel_names: List of channel names
            days: Number of days to analyze

        Returns:
            Dictionary {channel_name: Channel}
        """
        if not channel_names:
            raise ValueError("Channel list cannot be empty")

        days = days or self.config.parsing.default_days
        results = {}

        self.logger.info(f"Starting to parse {len(channel_names)} channels")

        progress = ProgressLogger(self.logger, len(channel_names), "Parsing channels")

        for i, channel_name in enumerate(channel_names, 1):
            try:
                self.logger.info(f"[{i}/{len(channel_names)}] Parsing @{channel_name}")

                channel = self.parse_channel(channel_name, days)
                results[channel_name] = channel

                progress.update()

                if i < len(channel_names):
                    delay = 1.0 / self.config.network.requests_per_second
                    self.logger.debug(f"Pause {delay:.1f}s before next channel")
                    time.sleep(delay)

            except Exception as e:
                self.logger.error(f"Error parsing @{channel_name}: {e}")
                continue

        progress.finish()
        self.logger.info(
            f"Parsing completed. Processed {len(results)} out of {len(channel_names)} channels"
        )

        return results

    def _get_channel_info(self, channel_name: str) -> ChannelInfo:
        """Get basic channel information."""
        url = f"{self.config.parsing.base_url}/{channel_name}"

        try:
            response = self._make_request("GET", url)
            soup = BeautifulSoup(response.text, "html.parser")

            title_elem = soup.find("div", {"class": "tgme_page_title"})
            if not title_elem:
                raise ValueError(f"Channel @{channel_name} not found")

            title = title_elem.get_text(strip=True)
            subscribers = self._extract_subscribers(soup)

            description_elem = soup.find("div", {"class": "tgme_page_description"})
            if description_elem:
                description_html = str(description_elem)
                description = self._html_to_markdown(description_html)
            else:
                description = ""

            channel_info = ChannelInfo(
                channel=channel_name, name=title, description=description, subscribers=subscribers
            )

            return channel_info

        except requests.RequestException as e:
            raise ValueError(f"Failed to load channel info @{channel_name}: {e}") from e

    def _extract_subscribers(self, soup: BeautifulSoup) -> int:
        """Extract subscriber count from HTML."""
        counter_elem = soup.find("div", {"class": "tgme_page_extra"})
        if not counter_elem:
            return 0

        counter_text = counter_elem.get_text(strip=True)
        return self._parse_number_with_suffix(counter_text)

    def _parse_number_with_suffix(self, text: str) -> int:
        """
        Parse numbers with suffixes (K, M) and without them.

        Args:
            text: Text containing number (e.g.: "1.2K", "5M", "1234")

        Returns:
            Number as int
        """
        if not text:
            return 0

        text = text.strip().upper()

        if "K" in text:
            number = float(VIEWS_CLEANUP_REGEX.sub("", text.replace("K", "")))
            return int(number * K_MULTIPLIER)
        elif "M" in text:
            number = float(VIEWS_CLEANUP_REGEX.sub("", text.replace("M", "")))
            return int(number * M_MULTIPLIER)
        else:
            clean_text = NUMBER_CLEANUP_REGEX.sub("", text)
            if clean_text:
                try:
                    return int(float(clean_text.replace(",", "")))
                except ValueError:
                    return 0

        return 0

    def _unescape_html_content(self, html_content: str) -> str:
        """Unescape HTML content from JSON."""
        if html_content.startswith('"') and html_content.endswith('"'):
            html_content = html_content[1:-1]

        html_content = html_content.replace('\\"', '"').replace("\\/", "/")
        return html.unescape(html_content)

    def _parse_posts_from_html(
        self, html_content: str, channel_name: str
    ) -> tuple[list[Post], str | None]:
        """
        Parse posts from HTML content.

        Returns:
            tuple: (list of posts, before value for next request or None)
        """
        if not html_content or not html_content.strip():
            return [], None

        html_content = self._unescape_html_content(html_content)
        soup = BeautifulSoup(html_content, "html.parser")

        post_elements = soup.find_all("div", {"class": "tgme_widget_message"})
        self.logger.debug(f"Found {len(post_elements)} post elements in HTML")

        posts = []
        for elem in post_elements:
            try:
                post = self._parse_single_post(elem, channel_name)
                if post:
                    posts.append(post)
                else:
                    self.logger.debug("Failed to parse post element - returned None")
            except Exception as e:
                self.logger.debug(f"Error parsing post: {e}")
                continue

        next_before = None
        more_wrap = soup.find("div", {"class": "js-messages_more_wrap"})
        if more_wrap and hasattr(more_wrap, "find") and isinstance(more_wrap, Tag):
            more_link = more_wrap.find("a", {"class": "js-messages_more"})
            if more_link and hasattr(more_link, "get") and isinstance(more_link, Tag):
                href = more_link.get("href")
                if isinstance(href, str):
                    match = BEFORE_REGEX.search(href)
                    if match:
                        next_before = match.group(1)

        return posts, next_before

    def _get_posts(self, channel_name: str, days: int) -> tuple[list[Post], int | None]:
        """
        Get channel posts for specified period and return latest post ID.

        Proper pagination logic with Telegram API:
        - Telegram provides link to next page
        - If no link - reached end of channel
        - No manual before value calculations needed

        Returns:
            Tuple of (posts list, latest post ID from first batch)
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        all_posts: list[Post] = []
        before = None
        max_posts = self.config.parsing.max_posts
        latest_post_id = None

        self.logger.debug(f"Getting posts from {cutoff_date.strftime('%Y-%m-%d %H:%M')}")
        if max_posts:
            self.logger.debug(f"Post limit: {max_posts}")

        url = f"{self.config.parsing.base_url}/s/{channel_name}"
        first_request = True

        while first_request or before:
            self.logger.debug(f"Loop iteration: first_request={first_request}, before={before}")
            first_request = False

            if max_posts and len(all_posts) >= max_posts:
                self.logger.info(f"Post limit reached: {max_posts}")
                break

            data: dict[str, str] = {}
            if before:
                data["before"] = before

            try:
                self.logger.debug(f"Request to {url} with params: {data}")
                response = self._make_request("POST", url, data=data)
                self.logger.debug(f"Response size: {len(response.text)} bytes")

                batch_posts, next_before = self._parse_posts_from_html(response.text, channel_name)

                if not batch_posts:
                    self.logger.debug("Empty batch received - no more posts available")
                    break

                if latest_post_id is None and batch_posts:
                    latest_post_id_str = batch_posts[0].post_id
                    # Convert string post_id to int
                    try:
                        latest_post_id = int(latest_post_id_str) if latest_post_id_str else None
                    except (ValueError, TypeError):
                        latest_post_id = None
                    self.logger.debug(f"Latest post ID: {latest_post_id}")

                valid_posts = []
                found_old_post = False

                for post in reversed(batch_posts):
                    post_date = parse_date(post.date)

                    if post_date and post_date >= cutoff_date:
                        valid_posts.append(post)

                        if max_posts and len(all_posts) + len(valid_posts) >= max_posts:
                            posts_needed = max_posts - len(all_posts)
                            valid_posts = valid_posts[:posts_needed]
                            next_before = None
                            break
                    else:
                        found_old_post = True
                        self.logger.debug(
                            f"Post {post.post_id} older than cutoff_date: {post_date} < {cutoff_date}"
                        )

                all_posts.extend(valid_posts)

                self.logger.debug(
                    f"Processed batch: {len(batch_posts)} posts, valid: {len(valid_posts)}, total collected: {len(all_posts)}"
                )

                if found_old_post and len(valid_posts) == 0:
                    self.logger.debug(
                        "All posts in batch are older than cutoff date - stopping pagination"
                    )
                    break

                if next_before is None:
                    self.logger.debug(
                        "Telegram didn't provide next page link - reached end of channel or pagination"
                    )
                    break

                before = next_before
                self.logger.debug(f"Moving to next batch, before: {before}")

                time.sleep(1.0 / self.config.network.requests_per_second)

            except requests.RequestException as e:
                self.logger.error(f"Error loading posts: {e}")
                if all_posts:
                    self.logger.warning(f"Returning {len(all_posts)} posts collected before error")
                    break
                raise ValueError(f"Failed to get posts for @{channel_name}: {e}") from e

        # Sort posts by date, filtering out posts with None dates
        all_posts_with_dates = [post for post in all_posts if post.date is not None]
        all_posts_with_dates.sort(key=lambda p: cast(datetime, p.date))
        all_posts = all_posts_with_dates

        if max_posts and len(all_posts) > max_posts:
            all_posts = all_posts[:max_posts]

        return all_posts, latest_post_id

    def _parse_single_post(self, post_elem: Tag, channel_name: str) -> Post | None:
        """Parse single post from HTML element."""
        post_id_raw = post_elem.get("data-post", "")
        post_id_full = post_id_raw if isinstance(post_id_raw, str) else ""

        if not post_id_full:
            self.logger.debug("No data-post attribute found")
            return None

        post_id = self._extract_numeric_id(post_id_full)
        if not post_id:
            self.logger.debug(f"Failed to extract numeric ID from: {post_id_full}")
            return None

        date_elem = post_elem.find("time", {"datetime": True})
        if not date_elem or not hasattr(date_elem, "get"):
            self.logger.debug(f"No time element with datetime attribute found for post {post_id}")
            return None

        datetime_str = date_elem.get("datetime", "")
        if not datetime_str or not isinstance(datetime_str, str):
            self.logger.debug(
                f"No datetime attribute for post {post_id}. Time element: {date_elem}"
            )
            self.logger.debug(
                f"Time element attrs: {date_elem.attrs if hasattr(date_elem, 'attrs') else 'no attrs'}"
            )
            return None

        post_date = parse_date(datetime_str)

        author_elem = post_elem.find("span", {"class": "tgme_widget_message_author_name"})
        author = author_elem.get_text(strip=True) if author_elem else channel_name

        text_elem = post_elem.find("div", {"class": "tgme_widget_message_text"})
        raw_text = ""
        if text_elem:
            raw_text = str(text_elem)

        text = self._html_to_markdown(raw_text)
        views = self._extract_views(post_elem)

        return Post(
            post_id=str(post_id),
            views=views,
            date=post_date,
            author=author,
            text=text.strip(),
        )

    def _extract_views(self, post_elem: Tag) -> int:
        """Extract post view count."""
        views_elem = post_elem.find("span", {"class": "tgme_widget_message_views"})
        if not views_elem:
            return 0

        views_text = views_elem.get_text(strip=True)
        return self._parse_number_with_suffix(views_text)

    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to Markdown using html2text."""
        if not html_content:
            return ""

        try:
            markdown = self.html_converter.handle(html_content)

            lines = [line.strip() for line in markdown.split("\n")]
            lines = [line for line in lines if line]

            result = "\n".join(lines)

            return result.strip()
        except Exception as e:
            self.logger.warning(f"Error converting HTML to Markdown: {e}")
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text(separator=" ", strip=True)

    def _get_channel_age_info(
        self, channel_info: ChannelInfo, _latest_post_id: int | None
    ) -> None:
        """Get channel age information and set first_post_date in channel_info."""
        try:
            posts = self._get_earliest_posts(channel_info.channel)
            if posts:
                # Filter posts with valid dates
                posts_with_dates = [post for post in posts if post.date is not None]
                if posts_with_dates:
                    first_post = min(posts_with_dates, key=lambda p: cast(datetime, p.date))
                    channel_info.first_post_date = first_post.date

        except Exception as e:
            self.logger.debug(f"Error getting age info: {e}")

    def _get_earliest_posts(self, channel_name: str) -> list[Post]:
        """Get earliest channel posts."""
        url = f"{self.config.parsing.base_url}/s/{channel_name}"
        data = {"before": str(EARLIEST_POST_ID)}

        self.logger.debug(f"Getting earliest posts with before={EARLIEST_POST_ID}")

        try:
            response = self._make_request("POST", url, data=data)
            posts, _ = self._parse_posts_from_html(response.text, channel_name)
            limit = max(1, self.config.parsing.age_posts_limit)
            return posts[:limit]
        except (requests.RequestException, ValueError, AttributeError) as e:
            self.logger.debug(f"Error getting early posts: {e}")
            return []

    def _extract_numeric_id(self, post_id: str) -> int | None:
        """Extract numeric part from post_id."""
        if not post_id:
            return None
        try:
            parts = post_id.split("/")
            if len(parts) >= POST_ID_PARTS_COUNT and parts[-1].isdigit():
                return int(parts[-1])
            return None
        except (AttributeError, IndexError, ValueError):
            return None

    def _make_request(
        self, method: str, url: str, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> requests.Response:
        """Make HTTP request with retry logic."""
        for attempt in range(self.config.network.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    data=data,
                    timeout=self.config.network.request_timeout,
                    **kwargs,
                )
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                is_last_attempt = attempt == self.config.network.retry_attempts - 1
                if is_last_attempt:
                    raise

                self.logger.debug(
                    f"Request failed (attempt {attempt + 1}/{self.config.network.retry_attempts}): {e}"
                )
                time.sleep(self.config.network.retry_delay * (attempt + 1))

        raise requests.RequestException("This should never be reached")
