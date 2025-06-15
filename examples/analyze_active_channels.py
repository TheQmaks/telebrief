#!/usr/bin/env python3
"""
Example of comparing multiple channels with performance optimization.

This script demonstrates:
- Comparing different types of channels
- Using post limits for efficient analysis  
- Performance optimization techniques
- Detailed comparison reporting

Run: python examples/analyze_active_channels.py
"""

import os
from datetime import datetime

from telebrief import MetricsAnalyzer, TelegramParser
from telebrief.utils import Config


def analyze_active_channels():
    """Analyzes and compares multiple channels with performance optimization."""

    # Different types of channels for comparison
    channels_to_compare = [
        'bloomberg',       # Bloomberg - financial and business news
        'insiderpaper',    # Insider Paper - breaking news  
        'realta_rent_il'   # Realta Rent - real estate updates
    ]

    print("=== Multi-Channel Comparison Analysis ===")
    print("🚀 Optimized analysis with performance tracking\n")

    config = Config()
    
    # Performance optimization settings
    config.parsing.max_posts = 100      # Limit for quick analysis
    config.parsing.fetch_age_info = False  # Skip age info for speed
    config.network.requests_per_second = 2  # Faster requests

    parser = TelegramParser(config)
    analyzer = MetricsAnalyzer()

    analysis_days = 14  # Two weeks for good comparison data
    print(f"⚡ Quick analysis mode: {config.parsing.max_posts} posts max")
    print(f"📅 Analysis period: {analysis_days} days")
    print(f"🔄 Request rate: {config.network.requests_per_second} req/sec\n")

    results = {}
    start_time = datetime.now()

    for i, channel in enumerate(channels_to_compare, 1):
        try:
            print(f"🔄 [{i}/{len(channels_to_compare)}] Analyzing @{channel}...")

            channel_data = parser.parse_channel(channel, days=analysis_days)
            metrics = analyzer.analyze_channel(channel_data, days=analysis_days)

            results[channel] = {
                'name': channel_data.info.name,
                'subscribers': channel_data.info.subscribers,
                'posts_collected': len(channel_data.posts),
                'view_rate': metrics.average_vr_percent,
                'posts_per_day': metrics.posts_per_day,
                'avg_views': metrics.avg_views_per_post,
                'quality': metrics.engagement_quality,
                'consistency': metrics.content_consistency
            }

            print(f"✅ {channel_data.info.name}")
            print(f"   📊 {len(channel_data.posts)} posts | VR: {metrics.average_vr_percent:.1f}%")
            print(f"   📈 {metrics.posts_per_day:.1f} posts/day | Quality: {metrics.engagement_quality}\n")

        except Exception as e:
            print(f"❌ Error analyzing @{channel}: {e}\n")
            continue

    if not results:
        print("❌ No channels were successfully analyzed")
        return

    # Performance summary
    elapsed = datetime.now() - start_time
    total_posts = sum(data['posts_collected'] for data in results.values())
    
    print(f"⏱️  Analysis completed in {elapsed.total_seconds():.1f}s")
    print(f"📊 Analyzed {total_posts} posts from {len(results)} channels")
    print(f"🚀 Average: {total_posts/elapsed.total_seconds():.1f} posts/second\n")

    # Results comparison table
    print("📋 Channel Comparison:")
    print("-" * 90)
    print(f"{'Channel':<25} {'Subs':>8} {'Posts':>6} {'VR%':>6} {'Activity':>10} {'Quality':>12} {'Consistency':>12}")
    print("-" * 90)

    # Sort by View-Rate for comparison
    sorted_results = sorted(results.items(), key=lambda x: x[1]['view_rate'], reverse=True)

    for channel, data in sorted_results:
        print(f"{data['name'][:24]:<25} {data['subscribers']:>8,} "
              f"{data['posts_collected']:>6} {data['view_rate']:>5.1f}% "
              f"{data['posts_per_day']:>9.1f} {data['quality']:>12} {data['consistency']:>12}")

    print("-" * 90)

    # Save comparison report
    print("\n💾 Saving comparison report...")
    os.makedirs("output/comparison", exist_ok=True)
    report_path = f"output/comparison/channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("MULTI-CHANNEL COMPARISON REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Period: {analysis_days} days\n")
        f.write(f"Post Limit: {config.parsing.max_posts} per channel\n")
        f.write(f"Processing Time: {elapsed.total_seconds():.1f} seconds\n")
        f.write(f"Total Posts: {total_posts}\n")
        f.write(f"Channels: {len(results)}\n\n")

        f.write("CHANNEL RANKINGS (by View-Rate):\n")
        f.write("-" * 40 + "\n")
        for i, (channel, data) in enumerate(sorted_results, 1):
            f.write(f"{i}. @{channel} - {data['name']}\n")
            f.write(f"   Subscribers: {data['subscribers']:,}\n")
            f.write(f"   Posts/day: {data['posts_per_day']:.1f}\n")
            f.write(f"   View-Rate: {data['view_rate']:.1f}%\n")
            f.write(f"   Quality: {data['quality']}\n")
            f.write(f"   Consistency: {data['consistency']}\n\n")

        # Comparison insights
        best_vr = max(results.items(), key=lambda x: x[1]['view_rate'])
        most_active = max(results.items(), key=lambda x: x[1]['posts_per_day'])
        largest = max(results.items(), key=lambda x: x[1]['subscribers'])
        
        f.write("COMPARISON INSIGHTS:\n")
        f.write("-" * 25 + "\n")
        f.write(f"Best View-Rate: @{best_vr[0]} ({best_vr[1]['view_rate']:.1f}%)\n")
        f.write(f"Most Active: @{most_active[0]} ({most_active[1]['posts_per_day']:.1f} posts/day)\n")
        f.write(f"Largest Audience: @{largest[0]} ({largest[1]['subscribers']:,} subscribers)\n")
        f.write(f"Average VR: {sum(d['view_rate'] for d in results.values())/len(results):.1f}%\n")

    print(f"   📋 Report saved: {report_path}")

    # Show insights
    print(f"\n🔍 Key Insights:")
    print(f"   🏆 Best View-Rate: @{best_vr[0]} ({best_vr[1]['view_rate']:.1f}%)")
    print(f"   📈 Most Active: @{most_active[0]} ({most_active[1]['posts_per_day']:.1f} posts/day)")
    print(f"   👥 Largest Audience: @{largest[0]} ({largest[1]['subscribers']:,} subscribers)")

    print("\n✨ Channel comparison completed!")
    print("\n💡 Analysis Tips:")
    print("   • Different channel types have different optimal metrics")
    print("   • View-Rate varies by content type and audience")
    print("   • Consider both quantity and quality metrics")
    print("   • Consistency often matters more than peak performance")

if __name__ == "__main__":
    analyze_active_channels()
