"""Channel model for storing Telegram channel data."""

from dataclasses import dataclass, field
from datetime import datetime

from ..utils import datetime_to_str
from .post import Post


@dataclass
class ChannelInfo:
    """Channel information."""

    channel: str = ""
    name: str = ""
    subscribers: int = 0
    description: str = ""
    first_post_date: datetime | None = None

    @property
    def channel_age_days(self) -> int:
        """Calculate channel age from first post date."""
        if self.first_post_date:
            return (datetime.now() - self.first_post_date).days
        return 0


@dataclass
class Channel:
    """Telegram channel model."""

    info: ChannelInfo = field(default_factory=ChannelInfo)
    posts: list[Post] = field(default_factory=list)

    def add_post(self, post: Post) -> None:
        """Add post to channel."""
        self.posts.append(post)

    @property
    def total_views(self) -> int:
        """Total views across all posts."""
        return sum(post.views for post in self.posts)

    @property
    def avg_views(self) -> float:
        """Average views per post."""
        if not self.posts:
            return 0.0
        return self.total_views / len(self.posts)

    def get_posts_by_date_range(self, start_date: datetime, end_date: datetime) -> list[Post]:
        """Get posts within date range."""
        return [post for post in self.posts if post.date and start_date <= post.date <= end_date]

    def to_dict(self) -> dict:
        """Convert channel to dictionary."""
        return {
            "info": {
                "channel": self.info.channel,
                "name": self.info.name,
                "subscribers": self.info.subscribers,
                "description": self.info.description,
                "first_post_date": datetime_to_str(self.info.first_post_date),
                "channel_age_days": self.info.channel_age_days,
            },
            "posts": [post.to_dict() for post in self.posts],
        }
