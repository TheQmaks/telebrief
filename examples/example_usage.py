#!/usr/bin/env python3

"""
Basic example of Telebrief library usage.

This demonstrates the core functionality:
- Parsing a single channel
- Calculating metrics
- Exporting results

Run: python examples/example_usage.py
"""

import logging

from telebrief import Config, DataExporter, MetricsAnalyzer, TelegramParser
from telebrief.utils import get_logger


def setup_logging():
    """Configure logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)8s | %(message)s",
    )


def main():
    """Main function demonstrating basic library usage."""
    setup_logging()
    logger = get_logger("basic_example")

    logger.info("🚀 Basic Telebrief Example")

    # Single channel analysis with reasonable parameters
    channel_name = "bloomberg"  # Financial and business news
    days = 7  # One week analysis

    logger.info(f"📊 Analyzing @{channel_name} for {days} days")

    # Create instances
    config = Config()
    parser = TelegramParser(config)
    analyzer = MetricsAnalyzer()
    exporter = DataExporter()

    try:
        # Parse channel
        channel = parser.parse_channel(channel_name, days=days)
        logger.info(f"✅ Found {len(channel.posts)} posts")

        # Analyze metrics
        metrics = analyzer.analyze_channel(channel, days=days)
        logger.info(f"📈 View-Rate: {metrics.average_vr_percent:.1f}%")

        # Export results
        json_file = exporter.export_channel_json(channel, metrics=metrics)
        logger.info(f"💾 Results saved: {json_file}")

        # Show key metrics
        logger.info("📋 Key Metrics:")
        logger.info(f"   Posts: {metrics.total_posts}")
        logger.info(f"   Average views: {metrics.avg_views_per_post:,.0f}")
        logger.info(f"   View-Rate: {metrics.average_vr_percent:.1f}%")
        logger.info(f"   Activity: {metrics.posts_per_day:.1f} posts/day")
        logger.info(f"   Quality: {metrics.engagement_quality}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return

    logger.info("✨ Basic example completed!")


if __name__ == "__main__":
    main()
