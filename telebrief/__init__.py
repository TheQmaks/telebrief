"""
Telebrief - Professional Telegram Channel Analyzer.

A modern tool for parsing and analyzing marketing metrics
of public Telegram channels.

Main features:
- Channel and post information parsing
- View and engagement metrics calculation
- Audience activity analysis
- Data export in various formats
- Multiple channel support
- CLI interface

Usage example:

    from telebrief import TelegramParser, MetricsAnalyzer, DataExporter
    from telebrief.utils import Config

    config = Config()
    config.add_channel('bloomberg')

    parser = TelegramParser(config)
    channel = parser.parse_channel('bloomberg', days=30)

    analyzer = MetricsAnalyzer()
    metrics = analyzer.analyze_channel(channel)

    exporter = DataExporter()
    exporter.export_channel_json(channel, metrics=metrics)

Author: Anatoliy Fedorenko
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Anatoliy Fedorenko"
__license__ = "MIT"

from typing import Any

from .cli import main as cli_main
from .core import DataExporter, MetricsAnalyzer, TelegramParser
from .models import Channel, ChannelInfo, Metrics, Post
from .utils import Config, NetworkConfig, ParsingConfig

__all__ = [
    "Channel",
    "ChannelInfo",
    "Config",
    "DataExporter",
    "Metrics",
    "MetricsAnalyzer",
    "NetworkConfig",
    "ParsingConfig",
    "Post",
    "TelegramParser",
    "__author__",
    "__license__",
    "__version__",
    "cli_main",
]


def quick_analyze(channel_name: str, days: int = 30, **kwargs: Any) -> dict:
    """
    Quick channel analysis in one function.

    Args:
        channel_name: Channel name (without @)
        days: Number of days to analyze
        **kwargs: Additional configuration parameters

    Returns:
        Dictionary with analysis results

    Example:
        result = quick_analyze('bloomberg', days=7)
        print(f"View-Rate: {result['metrics']['average_vr_percent']:.1f}%")
    """
    config = Config()

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        elif hasattr(config.network, key):
            setattr(config.network, key, value)
        elif hasattr(config.parsing, key):
            setattr(config.parsing, key, value)

    parser = TelegramParser(config)
    channel = parser.parse_channel(channel_name, days)

    analyzer = MetricsAnalyzer()
    metrics = analyzer.analyze_channel(channel, days)

    return {"channel": channel.to_dict(), "metrics": metrics.to_dict()}


def get_version() -> str:
    """Returns library version."""
    return __version__


def get_info() -> dict:
    """Returns library information."""
    return {
        "name": "telebrief",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": "Telegram Channel Analyzer",
    }
