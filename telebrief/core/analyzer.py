"""Metrics analyzer for Telegram channels."""

import statistics
from datetime import datetime, timedelta

from ..models import Channel, Metrics, Post
from ..models.constants import (
    MAX_TREND_WINDOWS,
    MIN_VALUES_FOR_GINI,
    MIN_WINDOWS_FOR_TREND,
    PERCENTILE_75,
    PERCENTILE_90,
    TOP_POSTS_PERCENTAGE,
    TREND_DECLINE_THRESHOLD,
    TREND_GROWTH_THRESHOLD,
)
from ..utils import get_logger
from ..utils.date_utils import parse_date


class MetricsAnalyzer:
    """Metrics analyzer for calculating channel performance indicators."""

    def __init__(self) -> None:
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def analyze_channel(self, channel: Channel, days: int | None = None) -> Metrics:
        """
        Analyze channel metrics.

        Args:
            channel: Channel to analyze
            days: Number of days to analyze (if None, uses all posts)

        Returns:
            Calculated metrics
        """
        if not channel.posts:
            return Metrics()

        self.logger.info(f"Analyzing metrics for @{channel.info.channel} for {days} days")

        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            posts = [post for post in channel.posts if post.date and post.date >= cutoff_date]
        else:
            posts = channel.posts

        metrics = Metrics()
        metrics.total_posts = len(posts)
        metrics.total_views = sum(post.views for post in posts)
        metrics.analysis_period_days = days or 0

        self._calculate_view_metrics(metrics, posts)
        self._calculate_vr_metrics(metrics, posts, channel.info.subscribers)
        self._calculate_activity_metrics(metrics, posts, days or 0, channel.info.subscribers)
        self._calculate_quality_metrics(metrics, posts)

        self.logger.info(f"Analysis completed. VR: {metrics.average_vr_percent:.1f}%")

        return metrics

    def _calculate_view_metrics(self, metrics: Metrics, posts: list[Post]) -> None:
        """Calculate basic view metrics."""
        views = [p.views for p in posts]

        metrics.avg_views_per_post = statistics.mean(views)
        metrics.median_views_per_post = int(statistics.median(views))
        metrics.max_views = max(views)
        metrics.min_views = min(views)

        if len(views) > 1:
            metrics.views_std_dev = statistics.stdev(views)
            if metrics.avg_views_per_post > 0:
                metrics.views_cv = metrics.views_std_dev / metrics.avg_views_per_post
            else:
                metrics.views_cv = 0
        else:
            metrics.views_std_dev = 0
            metrics.views_cv = 0

    def _calculate_vr_metrics(self, metrics: Metrics, posts: list[Post], subscribers: int) -> None:
        """Calculate View-Rate metrics."""
        if subscribers == 0:
            return

        vr_values = [(p.views / subscribers) * 100 for p in posts]

        metrics.average_vr_percent = statistics.mean(vr_values)
        metrics.median_vr_percent = statistics.median(vr_values)

        sorted_vr = sorted(vr_values)
        n = len(sorted_vr)

        p90_index = (n - 1) * PERCENTILE_90
        if p90_index == int(p90_index):
            metrics.percentile_90_vr = sorted_vr[int(p90_index)]
        else:
            lower = int(p90_index)
            upper = lower + 1
            weight = p90_index - lower
            metrics.percentile_90_vr = sorted_vr[lower] * (1 - weight) + sorted_vr[upper] * weight

        p75_index = (n - 1) * PERCENTILE_75
        if p75_index == int(p75_index):
            metrics.percentile_75_vr = sorted_vr[int(p75_index)]
        else:
            lower = int(p75_index)
            upper = lower + 1
            weight = p75_index - lower
            metrics.percentile_75_vr = sorted_vr[lower] * (1 - weight) + sorted_vr[upper] * weight

        above_avg = sum(1 for vr in vr_values if vr >= metrics.average_vr_percent)
        metrics.consistency_index_percent = (above_avg / len(vr_values)) * 100

    def _calculate_activity_metrics(
        self, metrics: Metrics, posts: list[Post], period_days: int, subscribers: int
    ) -> None:
        """Calculate activity metrics."""
        if period_days > 0:
            metrics.posts_per_day = len(posts) / period_days
        else:
            metrics.posts_per_day = 0

        if posts:
            sorted_views = sorted([p.views for p in posts])
            n = len(sorted_views)

            p90_index = (n - 1) * PERCENTILE_90
            if p90_index == int(p90_index):
                metrics.active_subs_estimate = int(sorted_views[int(p90_index)])
            else:
                lower = int(p90_index)
                upper = min(lower + 1, n - 1)
                weight = p90_index - lower
                p90_views = sorted_views[lower] * (1 - weight) + sorted_views[upper] * weight
                metrics.active_subs_estimate = int(p90_views)

            if subscribers > 0:
                metrics.activation_ratio_percent = (
                    metrics.active_subs_estimate / subscribers
                ) * 100
            else:
                metrics.activation_ratio_percent = 0

    def _calculate_quality_metrics(self, metrics: Metrics, posts: list[Post]) -> None:
        """Calculate content quality metrics."""
        if not posts:
            return

        views = [p.views for p in posts]
        total_views = sum(views)

        sorted_views = sorted(views, reverse=True)
        top_10_count = max(1, len(posts) // TOP_POSTS_PERCENTAGE)
        top_10_views = sum(sorted_views[:top_10_count])

        if total_views > 0:
            metrics.top_10_percent_share = (top_10_views / total_views) * 100
        else:
            metrics.top_10_percent_share = 0

        metrics.gini_coefficient = self._calculate_gini([float(v) for v in views])

    def _calculate_gini(self, values: list[float]) -> float:
        """Calculate Gini coefficient for distribution."""
        if not values or len(values) < MIN_VALUES_FOR_GINI:
            return 0

        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = sum(sorted_values)

        if cumsum == 0:
            return 0

        index = sum((i + 1) * value for i, value in enumerate(sorted_values))
        return (2 * index) / (n * cumsum) - (n + 1) / n

    def compare_periods(self, channel: Channel, periods: list[int]) -> dict:
        """
        Compare metrics for different periods.

        Args:
            channel: Channel to analyze
            periods: List of periods in days

        Returns:
            Dictionary with metrics for each period
        """
        self.logger.info(f"Comparing periods {periods} for @{channel.info.channel}")

        results = {}
        for period in periods:
            metrics = self.analyze_channel(channel, period)
            results[f"{period}_days"] = metrics

        return results

    def get_trend_analysis(self, channel: Channel, window_days: int = 7) -> dict:
        """
        Analyze trends using time windows.

        Args:
            channel: Channel to analyze
            window_days: Window size in days

        Returns:
            Dictionary with trends
        """
        if not channel.posts:
            return {}

        windows = []
        current_date = datetime.now()

        while True:
            window_start = current_date - timedelta(days=window_days)
            window_posts = []
            for p in channel.posts:
                post_date = parse_date(p.date)
                if post_date and window_start <= post_date < current_date:
                    window_posts.append(p)

            if not window_posts:
                break

            avg_views = statistics.mean([p.views for p in window_posts])
            vr = (avg_views / channel.info.subscribers) * 100 if channel.info.subscribers else 0

            windows.append(
                {
                    "period": f"{window_start.strftime('%Y-%m-%d')} - {current_date.strftime('%Y-%m-%d')}",
                    "posts_count": len(window_posts),
                    "avg_views": round(avg_views, 0),
                    "vr_percent": round(vr, 2),
                    "posts_per_day": len(window_posts) / window_days if window_days > 0 else 0,
                }
            )

            current_date = window_start

            if len(windows) >= MAX_TREND_WINDOWS:
                break

        return {"windows": windows, "trend_direction": self._calculate_trend_direction(windows)}

    def _calculate_trend_direction(self, windows: list[dict]) -> str:
        """Determine trend direction."""
        if len(windows) < MIN_WINDOWS_FOR_TREND:
            return "insufficient_data"

        recent = windows[0]
        older = windows[-1]

        vr_change = recent["vr_percent"] - older["vr_percent"]

        if vr_change > TREND_GROWTH_THRESHOLD:
            return "growing"
        elif vr_change < TREND_DECLINE_THRESHOLD:
            return "declining"
        else:
            return "stable"
