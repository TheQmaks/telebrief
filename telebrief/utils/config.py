"""
Configuration system for Telebrief.
"""

import os
from dataclasses import dataclass, field

MAX_PORT_NUMBER = 65535
MIN_PORT_NUMBER = 1
MIN_TIMEOUT = 1
MAX_TIMEOUT = 300
MIN_RETRY_ATTEMPTS = 0
MAX_RETRY_ATTEMPTS = 10
MIN_REQUEST_RATE = 0.1
MAX_REQUEST_RATE = 100.0


@dataclass
class NetworkConfig:
    """Network interaction configuration."""

    proxy_host: str | None = "127.0.0.1"
    proxy_port: int | None = 8081
    use_proxy: bool = False

    verify_ssl: bool = False

    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

    requests_per_second: float = 1.0

    def __post_init__(self) -> None:
        """Parameter validation after initialization."""
        if self.proxy_port and not (MIN_PORT_NUMBER <= self.proxy_port <= MAX_PORT_NUMBER):
            raise ValueError(f"Invalid proxy port: {self.proxy_port}")

        if self.request_timeout < MIN_TIMEOUT or self.request_timeout > MAX_TIMEOUT:
            raise ValueError(f"Timeout must be between {MIN_TIMEOUT} and {MAX_TIMEOUT}")

        if self.retry_attempts < MIN_RETRY_ATTEMPTS or self.retry_attempts > MAX_RETRY_ATTEMPTS:
            raise ValueError(
                f"Number of attempts must be between {MIN_RETRY_ATTEMPTS} and {MAX_RETRY_ATTEMPTS}"
            )

        if (
            self.requests_per_second < MIN_REQUEST_RATE
            or self.requests_per_second > MAX_REQUEST_RATE
        ):
            raise ValueError(
                f"Request rate must be between {MIN_REQUEST_RATE} and {MAX_REQUEST_RATE}"
            )

    @property
    def proxy_url(self) -> str | None:
        """Returns proxy URL."""
        if not self.use_proxy or not self.proxy_host:
            return None
        return f"http://{self.proxy_host}:{self.proxy_port}"

    @property
    def proxies(self) -> dict[str, str] | None:
        """Returns proxy dictionary for requests."""
        if not self.use_proxy:
            return None
        proxy_url = self.proxy_url
        return {"http": proxy_url, "https": proxy_url} if proxy_url else None


@dataclass
class ParsingConfig:
    """Channel parsing configuration."""

    base_url: str = "https://t.me"
    default_days: int = 30
    max_posts_per_request: int = 20
    max_posts: int | None = None

    fetch_age_info: bool = True
    age_posts_limit: int = 5


@dataclass
class Config:
    """Application configuration."""

    output_dir: str = "output"
    log_level: str = "INFO"

    network: NetworkConfig = field(default_factory=NetworkConfig)
    parsing: ParsingConfig = field(default_factory=ParsingConfig)

    channels: list[str] = field(default_factory=list)

    output_format: str = "json"
    include_metrics: bool = True

    analysis_periods: list[int] = field(default_factory=lambda: [7, 30])

    log_to_file: bool = True

    def __post_init__(self) -> None:
        """Validation and additional processing after initialization."""
        os.makedirs(self.output_dir, exist_ok=True)
        self.channels = [self._clean_channel_name(ch) for ch in self.channels]
        self.analysis_periods = sorted(set(self.analysis_periods))

    def _clean_channel_name(self, channel: str) -> str:
        """Cleans channel name from extra characters."""
        return channel.strip().lstrip("@").lower()

    def add_channel(self, channel: str) -> None:
        """Adds channel to analysis list."""
        clean_name = self._clean_channel_name(channel)
        if clean_name not in self.channels:
            self.channels.append(clean_name)

    def remove_channel(self, channel: str) -> None:
        """Removes channel from list."""
        clean_name = self._clean_channel_name(channel)
        if clean_name in self.channels:
            self.channels.remove(clean_name)

    def to_dict(self) -> dict:
        """Converts configuration to dictionary."""
        return {
            "network": {
                "proxy_host": self.network.proxy_host,
                "proxy_port": self.network.proxy_port,
                "use_proxy": self.network.use_proxy,
                "verify_ssl": self.network.verify_ssl,
                "request_timeout": self.network.request_timeout,
                "retry_attempts": self.network.retry_attempts,
                "retry_delay": self.network.retry_delay,
                "requests_per_second": self.network.requests_per_second,
            },
            "parsing": {
                "base_url": self.parsing.base_url,
                "default_days": self.parsing.default_days,
                "max_posts_per_request": self.parsing.max_posts_per_request,
                "max_posts": self.parsing.max_posts,
                "fetch_age_info": self.parsing.fetch_age_info,
                "age_posts_limit": self.parsing.age_posts_limit,
            },
            "channels": self.channels,
            "output_dir": self.output_dir,
            "output_format": self.output_format,
            "include_metrics": self.include_metrics,
            "analysis_periods": self.analysis_periods,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
        }
