"""CLI interface for Telebrief."""

import argparse
import sys

from .core import DataExporter, MetricsAnalyzer, TelegramParser
from .models import Metrics
from .utils import Config, setup_logger


def create_parser() -> argparse.ArgumentParser:
    """Creates command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="telebrief",
        description="Telegram channel analysis and marketing metrics calculation",
        epilog="""
Usage examples:

  # Analyze one channel for 30 days
  uv run telebrief bloomberg

  # Analyze multiple channels for 7 days
  uv run telebrief bloomberg,insiderpaper,realta_rent_il --days 7

  # Analyze channels from file
  uv run telebrief --channels-file channels.txt --days 7

  # Limit number of posts (useful for active channels)
  uv run telebrief bloomberg --days 30 --max-posts 100

  # Export to CSV
  uv run telebrief bloomberg --format csv

  # Use proxy
  uv run telebrief bloomberg --proxy 127.0.0.1:8081

  # Analyze multiple periods
  uv run telebrief bloomberg --periods 7,30

Supported channel formats:
  - channel (simple name)
  - @channel (with @ symbol)
  - t.me/channel (short URL)
  - t.me/s/channel (short URL for public channels)
  - https://t.me/channel (full URL)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "channels",
        nargs="?",
        help="Channel(s) to analyze. Supports: channel1,@channel2,t.me/channel3,https://t.me/channel4",
    )

    parser.add_argument(
        "--channels-file",
        "-c",
        type=str,
        help="File with list of channels (one per line or comma-separated)",
    )

    parser.add_argument(
        "--days",
        "-d",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)",
    )

    parser.add_argument(
        "--max-posts",
        type=int,
        help="Maximum number of posts to collect from each channel",
    )

    parser.add_argument(
        "--periods", type=str, help="List of periods to compare, comma-separated (e.g., 7,30)"
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "both"],
        default="json",
        help="Output format (default: json)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output",
        help="Directory to save results (default: output)",
    )

    parser.add_argument(
        "--no-metrics", action="store_true", help="Don't calculate metrics (data collection only)"
    )

    parser.add_argument(
        "--proxy", type=str, help="Proxy in host:port format (e.g., 127.0.0.1:8081)"
    )

    parser.add_argument(
        "--no-ssl", action="store_true", help="Disable SSL certificate verification"
    )

    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level"
    )

    parser.add_argument(
        "--no-age-info", action="store_true", help="Don't fetch channel age information"
    )

    return parser


def parse_channels(channels_str: str) -> list[str]:
    """
    Parses channel string into a list.

    Supports various formats:
    - channel1,channel2
    - @channel1,@channel2
    - https://t.me/channel1,https://t.me/channel2
    - t.me/s/channel1,t.me/s/channel2
    """
    if not channels_str:
        return []

    def extract_channel_name(text: str) -> str:
        """Extract channel name from various formats."""
        text = text.strip()

        if text.startswith(("https://", "http://")):
            text = text.split("://", 1)[1]

        if text.startswith("t.me/"):
            text = text[5:]
            if text.startswith("s/"):
                text = text[2:]

        if text.startswith("@"):
            text = text[1:]

        text = text.split("/")[0].split("?")[0]

        return text

    channels = []
    for raw_channel in channels_str.split(","):
        channel_text = raw_channel.strip()
        if channel_text:
            channel_name = extract_channel_name(channel_text)
            if channel_name:
                channels.append(channel_name)

    return channels


def parse_periods(periods_str: str) -> list[int]:
    """Parses period string into a list."""
    if not periods_str:
        return []

    try:
        return [int(p.strip()) for p in periods_str.split(",") if p.strip()]
    except ValueError as e:
        raise ValueError("Periods must be numbers") from e


def parse_channels_from_file(filepath: str) -> list[str]:
    """
    Reads list of channels from a file.

    Supported formats:
    - One channel per line
    - Comma-separated channels
    - Comments starting with #
    - Various URL formats:
      * https://t.me/channel
      * https://t.me/s/channel
      * t.me/channel
      * t.me/s/channel
      * @channel
      * channel

    Args:
        filepath: Path to file with channel list

    Returns:
        List of channels
    """
    channels = []

    def extract_channel_name(text: str) -> str:
        """Extract channel name from various formats."""
        text = text.strip()

        if text.startswith(("https://", "http://")):
            text = text.split("://", 1)[1]

        if text.startswith("t.me/"):
            text = text[5:]
            if text.startswith("s/"):
                text = text[2:]

        if text.startswith("@"):
            text = text[1:]

        text = text.split("/")[0].split("?")[0]

        return text

    try:
        with open(filepath, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.split("#")[0].strip()
                if not line:
                    continue

                if "," in line:
                    for raw_channel in line.split(","):
                        channel_text = raw_channel.strip()
                        if channel_text:
                            channel_name = extract_channel_name(channel_text)
                            if channel_name:
                                channels.append(channel_name)
                else:
                    channel_name = extract_channel_name(line)
                    if channel_name:
                        channels.append(channel_name)

    except FileNotFoundError as e:
        raise ValueError(f"File not found: {filepath}") from e
    except Exception as e:
        raise ValueError(f"Error reading file {filepath}: {e}") from e

    return channels


def setup_config_from_args(args: argparse.Namespace) -> Config:
    """Creates configuration from command line arguments."""
    config = Config()

    if hasattr(args, "channels") and args.channels:
        config.channels = parse_channels(args.channels)

    if hasattr(args, "days") and args.days is not None:
        config.parsing.default_days = args.days

    if hasattr(args, "max_posts") and args.max_posts is not None:
        config.parsing.max_posts = args.max_posts

    if hasattr(args, "proxy") and args.proxy:
        try:
            host, port = args.proxy.split(":")
            config.network.proxy_host = host
            config.network.proxy_port = int(port)
            config.network.use_proxy = True
        except ValueError as e:
            raise ValueError("Proxy must be in host:port format") from e

    if hasattr(args, "no_ssl") and args.no_ssl:
        config.network.verify_ssl = False

    if hasattr(args, "output") and args.output:
        config.output_dir = args.output

    if hasattr(args, "format") and args.format:
        config.output_format = args.format

    if hasattr(args, "no_metrics") and args.no_metrics:
        config.include_metrics = False

    if hasattr(args, "periods") and args.periods:
        config.analysis_periods = parse_periods(args.periods)

    if hasattr(args, "log_level") and args.log_level:
        config.log_level = args.log_level

    if hasattr(args, "no_age_info") and args.no_age_info:
        config.parsing.fetch_age_info = False

    return config


def main() -> int:
    """Main CLI function."""
    parser = create_parser()
    args = parser.parse_args()

    config = setup_config_from_args(args)
    logger = setup_logger(level=config.log_level, log_to_file=config.log_to_file, log_dir="logs")

    logger.info("Starting Telegram channel analysis")

    # Priority: --channels-file > channels argument
    if hasattr(args, "channels_file") and args.channels_file:
        try:
            config.channels = parse_channels_from_file(args.channels_file)
            logger.info(f"Loaded {len(config.channels)} channels from file {args.channels_file}")
        except ValueError as e:
            logger.error(str(e))
            return 1

    if not config.channels:
        logger.error("No channels specified for analysis")
        logger.info("Use one of these methods:")
        logger.info("  1. Pass channels as argument: uv run telebrief channel1,channel2")
        logger.info("  2. Use file: uv run telebrief --channels-file channels.txt")
        return 1

    logger.info(f"Channels to analyze: {config.channels}")

    try:
        parser_instance = TelegramParser(config)
        analyzer = MetricsAnalyzer()
        exporter = DataExporter(config.output_dir)

        periods = []
        if hasattr(args, "periods") and args.periods:
            periods = parse_periods(args.periods)
        else:
            periods = [args.days]

        logger.info(f"Analysis periods: {periods} days")

        channels = parser_instance.parse_multiple_channels(config.channels, max(periods))

        if not channels:
            logger.error("Failed to parse any channels")
            return 1

        all_metrics: dict[str, Metrics | dict[str, Metrics]] = {}
        if not args.no_metrics:
            for channel_name, channel in channels.items():
                channel_metrics = {}
                for period in periods:
                    metrics = analyzer.analyze_channel(channel, period)
                    channel_metrics[f"{period}_days"] = metrics

                if len(periods) == 1:
                    all_metrics[channel_name] = channel_metrics[f"{periods[0]}_days"]
                else:
                    all_metrics[channel_name] = channel_metrics

        created_files = []

        if args.format in ["json", "both"]:
            if len(channels) == 1:
                channel_name = next(iter(channels.keys()))
                channel = channels[channel_name]
                single_metrics: Metrics | None = None
                if not args.no_metrics:
                    channel_data = all_metrics.get(channel_name)
                    if isinstance(channel_data, Metrics):
                        single_metrics = channel_data
                    elif isinstance(channel_data, dict) and len(periods) == 1:
                        single_metrics = channel_data.get(f"{periods[0]}_days")

                json_file = exporter.export_channel_json(
                    channel, include_metrics=not args.no_metrics, metrics=single_metrics
                )
                created_files.append(json_file)
            else:
                export_metrics: dict[str, Metrics] | None = None
                if not args.no_metrics:
                    export_metrics = {}
                    for name in all_metrics:  # noqa: PLC0206
                        channel_data = all_metrics[name]
                        if isinstance(channel_data, Metrics):
                            export_metrics[name] = channel_data
                        elif isinstance(channel_data, dict):
                            main_period = max(periods) if periods else 30
                            period_metrics = channel_data.get(f"{main_period}_days")
                            if period_metrics:
                                export_metrics[name] = period_metrics

                json_file = exporter.export_multiple_channels_json(channels, export_metrics)
                created_files.append(json_file)

        if args.format in ["csv", "both"]:
            for _channel_name, channel in channels.items():
                csv_file = exporter.export_posts_csv(channel)
                created_files.append(csv_file)

            if not args.no_metrics and all_metrics:
                metrics_csv = exporter.export_metrics_csv(all_metrics)
                created_files.append(metrics_csv)

        if len(channels) > 1 and not args.no_metrics:
            main_metrics: dict[str, Metrics] = {}
            for name in all_metrics:  # noqa: PLC0206
                channel_data = all_metrics[name]
                if isinstance(channel_data, dict):
                    main_period = max(periods)
                    period_metrics = channel_data.get(f"{main_period}_days")
                    if period_metrics:
                        main_metrics[name] = period_metrics
                elif isinstance(channel_data, Metrics):
                    main_metrics[name] = channel_data

            if main_metrics:
                report_file = exporter.export_summary_report(channels, main_metrics)
                created_files.append(report_file)

        return 0

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
