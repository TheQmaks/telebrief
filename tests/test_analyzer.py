"""Tests for analyzer module."""

from datetime import datetime, timedelta

import pytest

from telebrief.core.analyzer import MetricsAnalyzer
from telebrief.models import Channel, ChannelInfo, Metrics, Post


class TestMetricsAnalyzer:
    """Tests for MetricsAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Creates an analyzer instance."""
        return MetricsAnalyzer()

    @pytest.fixture
    def test_channel(self):
        """Creates a test channel with posts."""
        info = ChannelInfo(
            channel="testchannel",
            name="Test Channel",
            description="Test",
            subscribers=1000
        )

        # Create posts with different view counts
        posts = []
        base_date = datetime.now() - timedelta(days=10)

        for i in range(10):
            post = Post(
                post_id=i+1,
                views=(i + 1) * 100,  # 100, 200, 300, ..., 1000
                date=base_date + timedelta(days=i),
                author="testchannel",
                text=f"Test post {i+1}"
            )
            posts.append(post)

        return Channel(info=info, posts=posts)

    def test_analyze_channel_basic(self, analyzer, test_channel):
        """Test basic channel analysis."""
        metrics = analyzer.analyze_channel(test_channel, days=30)

        # Check basic metrics
        assert metrics.total_posts == 10
        assert metrics.analysis_period_days == 30
        assert metrics.avg_views_per_post == 550  # (100+200+...+1000)/10
        assert metrics.median_views_per_post == 550  # (500+600)/2
        assert metrics.max_views == 1000
        assert metrics.min_views == 100

    def test_analyze_channel_vr_metrics(self, analyzer, test_channel):
        """Test View-Rate metrics calculation."""
        metrics = analyzer.analyze_channel(test_channel, days=30)

        # VR = (views / subscribers) * 100
        assert metrics.average_vr_percent == 55.0  # (550/1000)*100
        assert metrics.median_vr_percent == 55.0

        # Check percentiles
        assert metrics.percentile_90_vr > 0
        assert metrics.percentile_75_vr > 0

    def test_analyze_channel_activity(self, analyzer, test_channel):
        """Test activity metrics."""
        metrics = analyzer.analyze_channel(test_channel, days=30)

        # 10 posts over 30 days
        assert metrics.posts_per_day == pytest.approx(10 / 30, rel=0.01)

        # Active audience (90th percentile of views)
        assert metrics.active_subs_estimate > 0
        assert metrics.activation_ratio_percent > 0

    def test_analyze_empty_channel(self, analyzer):
        """Test empty channel analysis."""
        info = ChannelInfo(
            channel="empty",
            name="Empty Channel",
            description="",
            subscribers=1000
        )
        channel = Channel(info=info, posts=[])

        metrics = analyzer.analyze_channel(channel)

        assert metrics.total_posts == 0
        assert metrics.avg_views_per_post == 0
        assert metrics.average_vr_percent == 0

    def test_gini_coefficient(self, analyzer):
        """Test Gini coefficient calculation."""
        # Equal distribution
        equal_values = [100.0] * 10
        gini_equal = analyzer._calculate_gini(equal_values)
        assert gini_equal == pytest.approx(0.0, abs=0.01)

        # Unequal distribution
        unequal_values = [10.0, 20.0, 30.0, 40.0, 500.0]
        gini_unequal = analyzer._calculate_gini(unequal_values)
        assert gini_unequal > 0.5  # High inequality

    def test_compare_periods(self, analyzer, test_channel):
        """Test period comparison."""
        results = analyzer.compare_periods(test_channel, [7, 14, 30])

        assert "7_days" in results
        assert "14_days" in results
        assert "30_days" in results

        # Check that metrics are calculated for each period
        for _period_key, metrics in results.items():
            assert isinstance(metrics, Metrics)
            assert metrics.analysis_period_days > 0
