"""Metrics model for channel analysis."""

from dataclasses import dataclass

from .constants import (
    AVERAGE_ENGAGEMENT_THRESHOLD,
    BELOW_AVERAGE_ENGAGEMENT_THRESHOLD,
    EXCELLENT_ENGAGEMENT_THRESHOLD,
    GOOD_ENGAGEMENT_THRESHOLD,
    HIGH_CONSISTENCY_THRESHOLD,
    HIGH_FREQUENCY_THRESHOLD,
    LOW_FREQUENCY_THRESHOLD,
    MEDIUM_CONSISTENCY_THRESHOLD,
    MEDIUM_FREQUENCY_THRESHOLD,
)


@dataclass
class Metrics:
    """Metrics for Telegram channel analysis."""

    # === Basic Metrics ===
    total_posts: int = 0
    total_views: int = 0
    analysis_period_days: int = 0

    # === View Metrics ===
    avg_views_per_post: float = 0.0
    median_views_per_post: float = 0.0
    max_views: int = 0
    min_views: int = 0
    views_std_dev: float = 0.0
    views_cv: float = 0.0

    # === View-Rate Metrics ===
    average_vr_percent: float = 0.0
    median_vr_percent: float = 0.0
    percentile_90_vr: float = 0.0
    percentile_75_vr: float = 0.0
    consistency_index_percent: float = 0.0

    # === Activity Metrics ===
    posts_per_day: float = 0.0
    active_subs_estimate: int = 0
    activation_ratio_percent: float = 0.0

    # === Content Quality Metrics ===
    top_10_percent_share: float = 0.0
    gini_coefficient: float = 0.0

    def __post_init__(self) -> None:
        """Post-initialization processing."""

    def to_dict(self) -> dict:
        """Converts metrics to dictionary."""
        return {
            "total_posts": self.total_posts,
            "total_views": self.total_views,
            "analysis_period_days": self.analysis_period_days,
            "avg_views_per_post": round(self.avg_views_per_post, 2),
            "median_views_per_post": round(self.median_views_per_post, 2),
            "max_views": self.max_views,
            "min_views": self.min_views,
            "views_std_dev": round(self.views_std_dev, 2),
            "views_cv": round(self.views_cv, 2),
            "average_vr_percent": round(self.average_vr_percent, 2),
            "median_vr_percent": round(self.median_vr_percent, 2),
            "percentile_90_vr": round(self.percentile_90_vr, 2),
            "percentile_75_vr": round(self.percentile_75_vr, 2),
            "consistency_index_percent": round(self.consistency_index_percent, 2),
            "posts_per_day": round(self.posts_per_day, 2),
            "active_subs_estimate": self.active_subs_estimate,
            "activation_ratio_percent": round(self.activation_ratio_percent, 2),
            "top_10_percent_share": round(self.top_10_percent_share, 2),
            "gini_coefficient": round(self.gini_coefficient, 2),
            "engagement_quality": self.engagement_quality,
            "content_consistency": self.content_consistency,
            "posting_frequency": self.posting_frequency,
        }

    @property
    def engagement_quality(self) -> str:
        """Engagement quality assessment."""
        if self.average_vr_percent >= EXCELLENT_ENGAGEMENT_THRESHOLD:
            return "Excellent"
        elif self.average_vr_percent >= GOOD_ENGAGEMENT_THRESHOLD:
            return "Good"
        elif self.average_vr_percent >= AVERAGE_ENGAGEMENT_THRESHOLD:
            return "Average"
        elif self.average_vr_percent >= BELOW_AVERAGE_ENGAGEMENT_THRESHOLD:
            return "Below Average"
        else:
            return "Low"

    @property
    def content_consistency(self) -> str:
        """Content consistency assessment."""
        if self.views_cv <= HIGH_CONSISTENCY_THRESHOLD:
            return "High"
        elif self.views_cv <= MEDIUM_CONSISTENCY_THRESHOLD:
            return "Medium"
        else:
            return "Low"

    @property
    def posting_frequency(self) -> str:
        """Posting frequency assessment."""
        if self.posts_per_day >= HIGH_FREQUENCY_THRESHOLD:
            return "High"
        elif self.posts_per_day >= MEDIUM_FREQUENCY_THRESHOLD:
            return "Medium"
        elif self.posts_per_day >= LOW_FREQUENCY_THRESHOLD:
            return "Low"
        else:
            return "Rare"
