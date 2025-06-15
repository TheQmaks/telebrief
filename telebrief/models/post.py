"""Post model for storing Telegram post data."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Post:
    """Telegram post model."""

    post_id: str | None = None
    views: int = 0
    date: datetime | None = None
    author: str = ""
    text: str = ""

    @property
    def formatted_text(self) -> str:
        """Returns formatted text for display."""
        return self.text.replace("\n", " ").strip()

    def to_dict(self) -> dict:
        """Converts post to dictionary."""
        return {
            "post_id": self.post_id,
            "views": self.views,
            "date": self.date.isoformat() if self.date else None,
            "author": self.author,
            "text": self.text,
        }
