"""Data exporter for Telebrief."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import Channel, Metrics
from ..utils import get_logger


class DataExporter:
    """Data exporter in various formats."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def export_channel_json(
        self,
        channel: Channel,
        filename: str | None = None,
        include_metrics: bool = True,
        metrics: Metrics | None = None,
    ) -> str:
        """
        Export channel data to JSON.

        Args:
            channel: Channel to export
            filename: Filename (if None, generated automatically)
            include_metrics: Include metrics
            metrics: Metrics to include

        Returns:
            Path to created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{channel.info.channel}_{timestamp}.json"

        filepath = self.output_dir / filename

        data = channel.to_dict()

        if include_metrics and metrics:
            data["metrics"] = metrics.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Channel exported to JSON: {filepath}")
        return str(filepath)

    def export_multiple_channels_json(
        self,
        channels: dict[str, Channel],
        metrics: dict[str, Metrics] | None = None,
        filename: str | None = None,
    ) -> str:
        """
        Export multiple channels to one JSON file.

        Args:
            channels: Dictionary of channels
            metrics: Dictionary of metrics
            filename: Filename

        Returns:
            Path to created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"channels_analysis_{timestamp}.json"

        filepath = self.output_dir / filename

        data: dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "total_channels": len(channels),
            "channels": {},
        }

        for name, channel in channels.items():
            channel_data = channel.to_dict()

            if metrics and name in metrics:
                channel_data["metrics"] = metrics[name].to_dict()

            data["channels"][name] = channel_data

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Exported {len(channels)} channels to JSON: {filepath}")
        return str(filepath)

    def export_posts_csv(self, channel: Channel, filename: str | None = None) -> str:
        """
        Export channel posts to CSV.

        Args:
            channel: Channel to export
            filename: Filename

        Returns:
            Path to created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{channel.info.channel}_posts_{timestamp}.csv"

        filepath = self.output_dir / filename

        headers = ["channel", "post_id", "views", "date", "author", "text"]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for post in channel.posts:
                writer.writerow(
                    [
                        channel.info.channel,
                        post.post_id or "",
                        post.views,
                        post.date.isoformat() if post.date else "",
                        post.author,
                        post.text.replace("\n", " "),
                    ]
                )

        self.logger.info(f"Posts exported to CSV: {filepath}")
        return str(filepath)

    def export_metrics_csv(
        self,
        metrics_data: dict[str, Metrics | dict[str, Metrics]],
        filename: str | None = None,
    ) -> str:
        """
        Export metrics to CSV.

        Args:
            metrics_data: Metrics data (channel -> metrics or channel -> period -> metrics)
            filename: Filename

        Returns:
            Path to created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_analysis_{timestamp}.csv"

        filepath = self.output_dir / filename

        rows = []

        for channel_name, data in metrics_data.items():
            if isinstance(data, Metrics):
                row = self._metrics_to_row(channel_name, "default", data)
                rows.append(row)
            elif isinstance(data, dict):
                for period, metrics in data.items():
                    row = self._metrics_to_row(channel_name, period, metrics)
                    rows.append(row)

        if not rows:
            self.logger.warning("No data to export to CSV")
            return ""

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        self.logger.info(f"Metrics exported to CSV: {filepath}")
        return str(filepath)

    def _metrics_to_row(self, channel: str, period: str, metrics: Metrics) -> dict:
        """Converts metrics to CSV row."""
        return {
            "channel": channel,
            "period": period,
            "total_posts": metrics.total_posts,
            "analysis_period_days": metrics.analysis_period_days,
            "avg_views_per_post": metrics.avg_views_per_post,
            "median_views_per_post": metrics.median_views_per_post,
            "max_views": metrics.max_views,
            "min_views": metrics.min_views,
            "views_std_dev": metrics.views_std_dev,
            "views_cv": metrics.views_cv,
            "average_vr_percent": metrics.average_vr_percent,
            "median_vr_percent": metrics.median_vr_percent,
            "percentile_90_vr": metrics.percentile_90_vr,
            "percentile_75_vr": metrics.percentile_75_vr,
            "consistency_index_percent": metrics.consistency_index_percent,
            "posts_per_day": metrics.posts_per_day,
            "active_subs_estimate": metrics.active_subs_estimate,
            "activation_ratio_percent": metrics.activation_ratio_percent,
            "top_10_percent_share": metrics.top_10_percent_share,
            "gini_coefficient": metrics.gini_coefficient,
            "engagement_quality": metrics.engagement_quality,
            "content_consistency": metrics.content_consistency,
            "posting_frequency": metrics.posting_frequency,
        }

    def export_summary_report(
        self,
        channels: dict[str, Channel],
        metrics: dict[str, Metrics],
        filename: str | None = None,
    ) -> str:
        """
        Create summary report in text format.

        Args:
            channels: Dictionary of channels
            metrics: Dictionary of metrics
            filename: Filename

        Returns:
            Path to created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{timestamp}.txt"

        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("TELEBRIEF - CHANNEL ANALYSIS SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total channels: {len(channels)}\n\n")

            total_posts = sum(len(ch.posts) for ch in channels.values())
            total_subs = sum(ch.info.subscribers for ch in channels.values())

            f.write("OVERALL STATISTICS:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total posts: {total_posts:,}\n")
            f.write(f"Total subscribers: {total_subs:,}\n\n")

            f.write("CHANNEL DETAILS:\n")
            f.write("-" * 30 + "\n\n")

            for channel_name, channel in channels.items():
                f.write(f"@{channel_name} - {channel.info.name}\n")
                f.write(f"  Subscribers: {channel.info.subscribers:,}\n")
                f.write(f"  Posts in sample: {len(channel.posts)}\n")

                if channel_name in metrics:
                    m = metrics[channel_name]
                    f.write(f"  View-Rate: {m.average_vr_percent:.1f}%\n")
                    f.write(f"  Activity: {m.posts_per_day:.1f} posts/day\n")
                    f.write(f"  Quality: {m.engagement_quality}\n")

                f.write("\n")

            if metrics:
                sorted_channels = sorted(
                    metrics.items(), key=lambda x: x[1].average_vr_percent, reverse=True
                )

                f.write("TOP-5 CHANNELS BY VIEW-RATE:\n")
                f.write("-" * 30 + "\n")

                for i, (name, m) in enumerate(sorted_channels[:5], 1):
                    f.write(f"{i}. @{name}: {m.average_vr_percent:.1f}%\n")

        self.logger.info(f"Summary report created: {filepath}")
        return str(filepath)
