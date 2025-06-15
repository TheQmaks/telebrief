"""
Logging system for Telebrief.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import ClassVar


class ColoredFormatter(logging.Formatter):
    """Formatter with colored output for console."""

    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


def setup_logger(
    name: str = "telebrief",
    level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs",
    console_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Sets up logger for the application.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Log to file
        log_dir: Directory for log files
        console_output: Output logs to console
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger
    """

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    logger.handlers.clear()

    console_format = "%(asctime)s | %(levelname)8s | %(name)s | %(message)s"
    file_format = "%(asctime)s | %(levelname)8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"

    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"{name}.log")

        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logs are being saved to file: {log_file}")

    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Returns existing logger or creates new one.

    Args:
        name: Logger name (if None, uses 'telebrief')

    Returns:
        Logger
    """
    if name is None:
        name = "telebrief"

    if not name.startswith("telebrief") and "." not in name:
        name = f"telebrief.{name}"

    logger = logging.getLogger(name)

    if not logger.handlers and name == "telebrief":
        return setup_logger(name)

    return logger


class ProgressLogger:
    """Progress logger for long operations."""

    def __init__(self, logger: logging.Logger, total: int, description: str = "Progress"):
        """
        Args:
            logger: Logger for output
            total: Total number of items
            description: Process description
        """
        self.logger = logger
        self.total = total
        self.description = description
        self.current = 0
        self.last_percent = -1

    def update(self, amount: int = 1) -> None:
        """
        Updates progress.

        Args:
            amount: Number of processed items
        """
        self.current += amount
        percent = int((self.current / self.total) * 100)

        if percent != self.last_percent and percent % 10 == 0:
            self.logger.info(f"{self.description}: {percent}% ({self.current}/{self.total})")
            self.last_percent = percent

    def finish(self) -> None:
        """Completes progress."""
        self.logger.info(f"{self.description}: completed ({self.total}/{self.total})")


def configure_external_loggers() -> None:
    """Configures logging for external libraries."""

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
