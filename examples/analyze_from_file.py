#!/usr/bin/env python3
"""
Example of batch channel analysis from file.

This script demonstrates:
- Loading multiple channels from a text file
- Batch processing with progress tracking
- Comprehensive comparison and ranking
- Detailed CSV/JSON export

Run: python examples/analyze_from_file.py examples/simple_channels.txt
"""

import os
import sys

from telebrief import Config, DataExporter, MetricsAnalyzer, TelegramParser
from telebrief.utils import get_logger


def load_channels_from_file(filename: str) -> list[str]:
    """Load channel names from text file."""
    channels = []
    with open(filename, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line and not line.startswith("#"):
                channel = line.lstrip("@")
                if channel:
                    channels.append(channel)
    return channels


def main(channels_file: str) -> None:
    """Analyze multiple channels from file."""
    logger = get_logger("batch_analyzer")

    channels = load_channels_from_file(channels_file)
    logger.info(f"📂 Loaded {len(channels)} channels from {channels_file}")

    if not channels:
        logger.error("No channels found in file")
        return

    # Configuration for batch analysis
    config = Config()
    config.parsing.max_posts = 200  # Reasonable limit for batch processing

    parser = TelegramParser(config)
    analyzer = MetricsAnalyzer()
    exporter = DataExporter()

    all_channels = {}
    all_metrics = {}
    analysis_days = 14  # Two weeks for comprehensive analysis

    logger.info(f"🚀 Starting batch analysis ({analysis_days} days per channel)")

    for i, channel_name in enumerate(channels, 1):
        try:
            logger.info(f"[{i}/{len(channels)}] 📊 Analyzing @{channel_name}")

            channel = parser.parse_channel(channel_name, days=analysis_days)
            metrics = analyzer.analyze_channel(channel, days=analysis_days)

            all_channels[channel_name] = channel
            all_metrics[channel_name] = metrics

            logger.info(
                f"✅ @{channel_name}: {len(channel.posts)} posts, "
                f"VR: {metrics.average_vr_percent:.1f}%, "
                f"Quality: {metrics.engagement_quality}"
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing @{channel_name}: {e}")
            continue

    if not all_channels:
        logger.error("No channels were successfully analyzed")
        return

    logger.info(f"📁 Exporting results for {len(all_channels)} channels...")

    # Export comprehensive data
    json_file = exporter.export_multiple_channels_json(all_channels, all_metrics)
    logger.info(f"📊 JSON exported: {json_file}")

    csv_file = exporter.export_metrics_csv(all_metrics)
    logger.info(f"📈 CSV exported: {csv_file}")

    # Create summary report
    report_file = exporter.export_summary_report(all_channels, all_metrics)
    logger.info(f"📋 Summary report: {report_file}")

    # Display rankings
    sorted_channels = sorted(
        all_metrics.items(), key=lambda x: x[1].average_vr_percent, reverse=True
    )

    logger.info(f"\n🏆 Channel Rankings (Top {min(10, len(sorted_channels))}):")
    logger.info("-" * 80)
    for i, (name, m) in enumerate(sorted_channels[:10], 1):
        logger.info(
            f"{i:2d}. @{name:<20} "
            f"VR: {m.average_vr_percent:6.1f}% | "
            f"Posts: {m.total_posts:3d} | "
            f"Activity: {m.posts_per_day:4.1f}/day | "
            f"Quality: {m.engagement_quality}"
        )

    # Show statistics
    total_posts = sum(m.total_posts for m in all_metrics.values())
    avg_vr = sum(m.average_vr_percent for m in all_metrics.values()) / len(all_metrics)

    logger.info(f"\n📊 Batch Analysis Summary:")
    logger.info(f"   Channels processed: {len(all_channels)}")
    logger.info(f"   Total posts analyzed: {total_posts:,}")
    logger.info(f"   Average View-Rate: {avg_vr:.1f}%")
    logger.info(f"   Analysis period: {analysis_days} days")

    logger.info("✨ Batch analysis completed!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_from_file.py <channels_file>", file=sys.stderr)
        print()
        print("Example: python analyze_from_file.py examples/simple_channels.txt")
        sys.exit(1)

    channels_file = sys.argv[1]

    if not os.path.exists(channels_file):
        print(f"Error: File '{channels_file}' not found", file=sys.stderr)
        sys.exit(1)

    main(channels_file)
