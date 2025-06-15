"""Date utilities for Telebrief."""

import logging
from datetime import datetime


def parse_date(date_value: str | datetime | None) -> datetime | None:
    """
    Flexible date parsing function.

    Args:
        date_value: Date string, datetime object, or None

    Returns:
        Parsed datetime object or None (always offset-naive)
    """
    if date_value is None:
        return None

    if isinstance(date_value, datetime):
        return date_value.replace(tzinfo=None) if date_value.tzinfo else date_value

    if isinstance(date_value, str):
        date_value = date_value.replace("Z", "+00:00")

        try:
            parsed_dt = datetime.fromisoformat(date_value)
            return parsed_dt.replace(tzinfo=None)
        except ValueError:
            logging.warning(f"Failed to parse date: {date_value}")
            return None

    return None  # type: ignore[unreachable]


def datetime_to_str(dt: datetime | None) -> str | None:
    """
    Convert datetime to ISO string.

    Args:
        dt: Datetime object

    Returns:
        ISO format string or None
    """
    if dt is None:
        return None

    return dt.isoformat()
