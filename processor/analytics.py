"""
Analytics Processor Module
Computes all dashboard insights from stored post data:
- Popular coffee types
- Peak drinking hours
- Sentiment breakdown
- Age group distribution
- Trending keywords
- Engagement scores
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

from config import COFFEE_KEYWORDS
from models import get_session, SocialPost, DailyInsight, TrendingKeyword

logger = logging.getLogger(__name__)


class AnalyticsProcessor:
    """
    Processes stored social media data to generate
    actionable business insights for the dashboard.
    """

    def __init__(self):
        logger.info("Analytics processor initialized.")

    # ============================================================
    # Core Analytics Methods
    # ============================================================

    def get_popular_drink_types(self, limit: int = 10) -> Dict:
        """
        Get the most popular coffee drink types mentioned.
        
        Returns:
            Dictionary with drink types and their mention counts.
        """
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(SocialPost.is_active == True).all()
            
            drink_counts = Counter()
            for post in posts:
                if post.drink_types:
                    try:
                        drinks = json.loads(post.drink_types)
                        for drink in drinks:
                            drink_counts[drink] += 1
                    except json.JSONDecodeError:
                        pass

            # Sort by count
            top_drinks = dict(drink_counts.most_common(limit))
            
            total_mentions = sum(drink_counts.values())
            percentages = {
                drink: round(count / total_mentions * 100, 1)
                for drink, count in top_drinks.items()
            } if total_mentions > 0 else {}

            return {
                "drinks": top_drinks,
                "percentages": percentages,
                "total_mentions": total_mentions
            }
        finally:
            session.close()

    def get_peak_hours(self) -> Dict:
        """
        Analyze peak coffee discussion hours (time-of-day pattern).
        
        Returns:
            Dictionary with hourly activity counts and percentages.
        """
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.hour_of_day.isnot(None)
            ).all()

            hour_counts = Counter()
            hour_engagement = defaultdict(int)

            for post in posts:
                if post.hour_of_day is not None:
                    hour_counts[post.hour_of_day] += 1
                    hour_engagement[post.hour_of_day] += post.engagement_score or 0

            # Format for dashboard
            hourly_data = []
            for hour in range(24):
                hourly_data.append({
                    "hour": hour,
                    "hour_label": f"{hour:02d}:00",
                    "post_count": hour_counts.get(hour, 0),
                    "total_engagement": hour_engagement.get(hour, 0),
                    "avg_engagement": (
                        round(hour_engagement.get(hour, 0) / hour_counts.get(hour, 1), 1)
                        if hour_counts.get(hour, 0) > 0
                        else 0
                    )
                })

            total_posts = sum(hour_counts.values())
            peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 12

            return {
                "hourly_data": hourly_data,
                "peak_hour": peak_hour,
                "peak_hour_label": f"{peak_hour:02d}:00",
                "total_posts": total_posts
            }
        finally:
            session.close()

    def get_day_of_week_patterns(self) -> Dict:
        """
        Analyze coffee discussion patterns by day of week.
        
        Returns:
            Dictionary with daily activity counts and engagement.
        """
        session = get_session()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        try:
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.day_of_week.isnot(None)
            ).all()

            day_counts = Counter()
            day_engagement = defaultdict(int)

            for post in posts:
                if post.day_of_week is not None:
                    day_counts[post.day_of_week] += 1
                    day_engagement[post.day_of_week] += post.engagement_score or 0

            daily_data = []
            for day_idx in range(7):
                daily_data.append({
                    "day": day_names[day_idx],
                    "day_index": day_idx,
                    "post_count": day_counts.get(day_idx, 0),
                    "total_engagement": day_engagement.get(day_idx, 0)
                })

            return {
                "daily_data": daily_data,
                "busiest_day": day_names[day_counts.most_common(1)[0][0]] if day_counts else "Unknown"
            }
        finally:
            session.close()

    def get_sentiment_breakdown(self) -> Dict:
        """
        Analyze overall sentiment distribution.
        
        Returns:
            Dictionary with sentiment counts and percentages.
        """
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(SocialPost.is_active == True).all()

            sentiment_counts = Counter(
                post.sentiment for post in posts if post.sentiment
            )

            total = sum(sentiment_counts.values())
            breakdown = {
                "positive": {
                    "count": sentiment_counts.get("positive", 0),
                    "percentage": round(sentiment_counts.get("positive", 0) / total * 100, 1) if total > 0 else 0,
                    "avg_score": 0.0
                },
                "neutral": {
                    "count": sentiment_counts.get("neutral", 0),
                    "percentage": round(sentiment_counts.get("neutral", 0) / total * 100, 1) if total > 0 else 0,
                    "avg_score": 0.0
                },
                "negative": {
                    "count": sentiment_counts.get("negative", 0),
                    "percentage": round(sentiment_counts.get("negative", 0) / total * 100, 1) if total > 0 else 0,
                    "avg_score": 0.0
                }
            }

            # Calculate average sentiment scores
            for sentiment_type in ["positive", "neutral", "negative"]:
                scores = [
                    post.sentiment_score
                    for post in posts
                    if post.sentiment == sentiment_type and post.sentiment_score is not None
                ]
                if scores:
                    breakdown[sentiment_type]["avg_score"] = round(sum(scores) / len(scores), 3)

            # Sentiment by drink type
            sentiment_by_drink = defaultdict(lambda: Counter())
            for post in posts:
                if post.drink_types and post.sentiment:
                    try:
                        drinks = json.loads(post.drink_types)
                        for drink in drinks:
                            sentiment_by_drink[drink][post.sentiment] += 1
                    except json.JSONDecodeError:
                        pass

            breakdown["by_drink_type"] = {
                drink: dict(counts)
                for drink, counts in sentiment_by_drink.items()
            }

            breakdown["total_posts"] = total

            return breakdown
        finally:
            session.close()

    def get_age_distribution(self) -> Dict:
        """
        Analyze age group distribution of coffee discussions.
        
        Returns:
            Dictionary with age group counts and percentages.
        """
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.estimated_age_group.isnot(None)
            ).all()

            age_counts = Counter(
                post.estimated_age_group for post in posts
            )

            total = sum(age_counts.values())
            distribution = {}

            for age_group, count in age_counts.most_common():
                distribution[age_group] = {
                    "count": count,
                    "percentage": round(count / total * 100, 1) if total > 0 else 0
                }

            return {
                "distribution": distribution,
                "total_with_age_data": total,
                "total_posts": len(posts)
            }
        finally:
            session.close()

    def get_trending_keywords(self, limit: int = 20) -> Dict:
        """
        Get trending coffee-related keywords with frequencies.
        
        Returns:
            Dictionary with keyword frequencies and sentiment.
        """
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(SocialPost.is_active == True).all()

            keyword_counts = Counter()
            keyword_sentiments = defaultdict(list)

            for post in posts:
                if post.keywords_found:
                    try:
                        keywords = json.loads(post.keywords_found)
                        for kw in keywords:
                            keyword_counts[kw.lower()] += 1
                            if post.sentiment_score is not None:
                                keyword_sentiments[kw.lower()].append(post.sentiment_score)
                    except json.JSONDecodeError:
                        pass

            # Build result
            trending = []
            for keyword, count in keyword_counts.most_common(limit):
                avg_sentiment = 0.0
                if keyword_sentiments[keyword]:
                    avg_sentiment = round(
                        sum(keyword_sentiments[keyword]) / len(keyword_sentiments[keyword]),
                        3
                    )

                trending.append({
                    "keyword": keyword,
                    "frequency": count,
                    "avg_sentiment": avg_sentiment,
                    "sentiment_label": (
                        "positive" if avg_sentiment > 0.1
                        else "negative" if avg_sentiment < -0.1
                        else "neutral"
                    )
                })

            return {
                "trending": trending,
                "total_unique_keywords": len(keyword_counts),
                "total_mentions": sum(keyword_counts.values())
            }
        finally:
            session.close()

    def get_engagement_by_drink(self) -> Dict:
        """
        Calculate engagement scores broken down by drink type.
        
        Returns:
            Dictionary with engagement metrics per drink type.
        """
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.drink_types.isnot(None)
            ).all()

            drink_engagement = defaultdict(lambda: {
                "total_likes": 0,
                "total_comments": 0,
                "total_shares": 0,
                "total_posts": 0,
                "total_engagement_score": 0
            })

            for post in posts:
                if post.drink_types:
                    try:
                        drinks = json.loads(post.drink_types)
                        for drink in drinks:
                            stats = drink_engagement[drink]
                            stats["total_posts"] += 1
                            stats["total_likes"] += post.likes or 0
                            stats["total_comments"] += post.comments or 0
                            stats["total_shares"] += post.shares or 0
                            stats["total_engagement_score"] += post.engagement_score or 0
                    except json.JSONDecodeError:
                        pass

            # Calculate averages
            result = {}
            for drink, stats in drink_engagement.items():
                posts_count = stats["total_posts"]
                result[drink] = {
                    "total_posts": posts_count,
                    "avg_likes": round(stats["total_likes"] / posts_count, 1) if posts_count else 0,
                    "avg_comments": round(stats["total_comments"] / posts_count, 1) if posts_count else 0,
                    "avg_shares": round(stats["total_shares"] / posts_count, 1) if posts_count else 0,
                    "avg_engagement_score": round(
                        stats["total_engagement_score"] / posts_count, 1
                    ) if posts_count else 0,
                    "total_engagement_score": stats["total_engagement_score"]
                }

            # Sort by total engagement
            sorted_drinks = dict(
                sorted(result.items(), key=lambda x: x[1]["total_engagement_score"], reverse=True)
            )

            return {
                "drinks": sorted_drinks,
                "highest_engagement_drink": (
                    list(sorted_drinks.keys())[0] if sorted_drinks else "N/A"
                )
            }
        finally:
            session.close()

    def get_heatmap_data(self) -> Dict:
        """
        Generate day-of-week vs hour-of-day heatmap data.
        
        Returns:
            Dictionary with 2D matrix for heatmap visualization.
        """
        session = get_session()
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        try:
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.hour_of_day.isnot(None),
                SocialPost.day_of_week.isnot(None)
            ).all()

            # Build 2D grid
            heatmap = [[0] * 24 for _ in range(7)]

            for post in posts:
                day = post.day_of_week
                hour = post.hour_of_day
                if 0 <= day < 7 and 0 <= hour < 24:
                    heatmap[day][hour] += 1

            return {
                "day_labels": day_names,
                "hour_labels": [f"{h:02d}" for h in range(24)],
                "data": heatmap,
                "max_value": max(max(row) for row in heatmap) if heatmap else 0
            }
        finally:
            session.close()

    def get_source_breakdown(self) -> Dict:
        """
        Get breakdown of posts by social media source.
        
        Returns:
            Dictionary with source counts and averages.
        """
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(SocialPost.is_active == True).all()

            source_stats = defaultdict(lambda: {
                "count": 0,
                "total_engagement": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0
            })

            for post in posts:
                stats = source_stats[post.source]
                stats["count"] += 1
                stats["total_engagement"] += post.engagement_score or 0
                if post.sentiment == "positive":
                    stats["positive"] += 1
                elif post.sentiment == "negative":
                    stats["negative"] += 1
                else:
                    stats["neutral"] += 1

            result = {}
            for source, stats in source_stats.items():
                result[source] = {
                    "count": stats["count"],
                    "avg_engagement": round(
                        stats["total_engagement"] / stats["count"], 1
                    ) if stats["count"] else 0,
                    "sentiment_breakdown": {
                        "positive": stats["positive"],
                        "neutral": stats["neutral"],
                        "negative": stats["negative"]
                    }
                }

            return result
        finally:
            session.close()

    def get_overall_summary(self) -> Dict:
        """
        Get a high-level summary of all analytics.
        
        Returns:
            Dictionary with key metrics for the dashboard header.
        """
        session = get_session()
        try:
            total_posts = session.query(SocialPost).filter(
                SocialPost.is_active == True
            ).count()

            avg_sentiment = session.query(
                SocialPost.sentiment_score
            ).filter(
                SocialPost.is_active == True,
                SocialPost.sentiment_score.isnot(None)
            ).all()

            total_engagement = session.query(
                SocialPost.engagement_score
            ).filter(
                SocialPost.is_active == True
            ).all()

            positive_count = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.sentiment == "positive"
            ).count()

            unique_drinks = set()
            posts_with_drinks = session.query(SocialPost.drink_types).filter(
                SocialPost.is_active == True,
                SocialPost.drink_types.isnot(None)
            ).all()
            
            for post in posts_with_drinks:
                try:
                    drinks = json.loads(post.drink_types)
                    unique_drinks.update(drinks)
                except (json.JSONDecodeError, TypeError):
                    pass

            avg_sentiment_score = (
                round(sum(s[0] for s in avg_sentiment) / len(avg_sentiment), 3)
                if avg_sentiment else 0
            )
            
            avg_engagement = (
                round(sum(e[0] for e in total_engagement) / len(total_engagement), 1)
                if total_engagement else 0
            )

            return {
                "total_posts": total_posts,
                "unique_drinks_mentioned": len(unique_drinks),
                "average_sentiment_score": avg_sentiment_score,
                "average_engagement_score": avg_engagement,
                "positive_sentiment_percentage": (
                    round(positive_count / total_posts * 100, 1)
                    if total_posts > 0 else 0
                ),
                "sources_tracked": 3,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        finally:
            session.close()

    def compute_daily_insights(self, date_str: Optional[str] = None) -> Dict:
        """
        Compute and store daily insight aggregates.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. Defaults to today.
        
        Returns:
            Dictionary of computed daily insights.
        """
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        session = get_session()
        try:
            # Get posts for the date
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.scraped_at >= date_str
            ).all()

            if not posts:
                return {"date": date_str, "total_posts": 0}

            total = len(posts)
            sentiment_counts = Counter(p.sentiment for p in posts if p.sentiment)

            # Top drink types for the day
            drink_counts = Counter()
            for post in posts:
                if post.drink_types:
                    try:
                        for drink in json.loads(post.drink_types):
                            drink_counts[drink] += 1
                    except json.JSONDecodeError:
                        pass

            # Peak hour
            hour_counts = Counter(p.hour_of_day for p in posts if p.hour_of_day is not None)
            peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None

            insight = DailyInsight(
                date=date_str,
                total_posts=total,
                avg_sentiment=round(sum(p.sentiment_score for p in posts if p.sentiment_score) / total, 3),
                positive_ratio=round(sentiment_counts.get("positive", 0) / total, 3),
                neutral_ratio=round(sentiment_counts.get("neutral", 0) / total, 3),
                negative_ratio=round(sentiment_counts.get("negative", 0) / total, 3),
                top_drink_types=json.dumps(dict(drink_counts.most_common(5))),
                peak_hour=peak_hour,
                total_engagement=sum(p.engagement_score for p in posts if p.engagement_score)
            )

            session.add(insight)
            session.commit()

            return {
                "date": date_str,
                "total_posts": total,
                "avg_sentiment": insight.avg_sentiment,
                "positive_ratio": insight.positive_ratio,
                "neutral_ratio": insight.neutral_ratio,
                "negative_ratio": insight.negative_ratio,
                "top_drink_types": dict(drink_counts.most_common(5)),
                "peak_hour": peak_hour,
                "total_engagement": insight.total_engagement
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error computing daily insights: {e}")
            return {"date": date_str, "error": str(e)}
        finally:
            session.close()

    def get_all_dashboard_data(self) -> Dict:
        """
        Get all dashboard data in a single call.
        
        Returns:
            Comprehensive dictionary with all analytics data.
        """
        logger.info("Computing all dashboard analytics...")
        
        return {
            "summary": self.get_overall_summary(),
            "popular_drinks": self.get_popular_drink_types(),
            "peak_hours": self.get_peak_hours(),
            "day_patterns": self.get_day_of_week_patterns(),
            "sentiment": self.get_sentiment_breakdown(),
            "age_distribution": self.get_age_distribution(),
            "trending_keywords": self.get_trending_keywords(),
            "engagement_by_drink": self.get_engagement_by_drink(),
            "heatmap": self.get_heatmap_data(),
            "source_breakdown": self.get_source_breakdown(),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
