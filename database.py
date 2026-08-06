"""
Database Service Layer
Provides a clean interface for data access operations.
Handles CRUD operations for social posts and insights.
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import func, or_

from models import get_session, SocialPost, DailyInsight, TrendingKeyword

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service layer for database operations.
    Provides methods for querying and managing social media data.
    """

    # ============================================================
    # Post Operations
    # ============================================================

    def save_posts(self, posts_data: List[Dict]) -> int:
        """
        Save a list of raw post dictionaries to the database.
        
        Args:
            posts_data: List of post dictionaries.
        
        Returns:
            Number of posts saved.
        """
        session = get_session()
        saved = 0
        try:
            for data in posts_data:
                post = SocialPost(**data)
                session.add(post)
                saved += 1
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving posts: {e}")
            return 0
        finally:
            session.close()
        return saved

    def get_recent_posts(self, limit: int = 100, source: Optional[str] = None) -> List[Dict]:
        """Get recent posts, optionally filtered by source."""
        session = get_session()
        try:
            query = session.query(SocialPost).filter(SocialPost.is_active == True)
            if source:
                query = query.filter(SocialPost.source == source)
            
            posts = query.order_by(SocialPost.timestamp.desc()).limit(limit).all()
            return [self._post_to_dict(p) for p in posts]
        finally:
            session.close()

    def get_posts_by_date_range(
        self, start_date: str, end_date: str, source: Optional[str] = None
    ) -> List[Dict]:
        """Get posts within a date range."""
        session = get_session()
        try:
            query = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.scraped_at >= start_date,
                SocialPost.scraped_at <= end_date
            )
            if source:
                query = query.filter(SocialPost.source == source)

            posts = query.order_by(SocialPost.timestamp.desc()).all()
            return [self._post_to_dict(p) for p in posts]
        finally:
            session.close()

    def get_post_count(self, source: Optional[str] = None) -> int:
        """Get total post count, optionally by source."""
        session = get_session()
        try:
            query = session.query(SocialPost).filter(SocialPost.is_active == True)
            if source:
                query = query.filter(SocialPost.source == source)
            return query.count()
        finally:
            session.close()

    # ============================================================
    # Search Operations
    # ============================================================

    def search_posts(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search posts by text content or keywords.
        
        Args:
            query: Search term.
            limit: Maximum results.
        
        Returns:
            List of matching post dictionaries.
        """
        session = get_session()
        try:
            search_term = f"%{query.lower()}%"
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                or_(
                    SocialPost.text.ilike(search_term),
                    SocialPost.keywords_found.ilike(search_term),
                    SocialPost.drink_types.ilike(search_term)
                )
            ).order_by(SocialPost.timestamp.desc()).limit(limit).all()

            return [self._post_to_dict(p) for p in posts]
        finally:
            session.close()

    # ============================================================
    # Aggregation Operations
    # ============================================================

    def get_drink_type_stats(self) -> List[Dict]:
        """Get aggregated statistics for each drink type."""
        session = get_session()
        try:
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.drink_types.isnot(None)
            ).all()

            stats = {}
            for post in posts:
                if post.drink_types:
                    try:
                        drinks = json.loads(post.drink_types)
                        for drink in drinks:
                            if drink not in stats:
                                stats[drink] = {"count": 0, "total_engagement": 0}
                            stats[drink]["count"] += 1
                            stats[drink]["total_engagement"] += post.engagement_score or 0
                    except json.JSONDecodeError:
                        pass

            return [
                {"drink": k, **v}
                for k, v in sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)
            ]
        finally:
            session.close()

    def get_sentiment_over_time(self, days: int = 7) -> List[Dict]:
        """Get sentiment trends over the last N days."""
        session = get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            posts = session.query(SocialPost).filter(
                SocialPost.is_active == True,
                SocialPost.scraped_at >= cutoff
            ).order_by(SocialPost.scraped_at.asc()).all()

            # Group by day
            daily_sentiment = {}
            for post in posts:
                day = post.scraped_at.strftime("%Y-%m-%d") if post.scraped_at else None
                if day:
                    if day not in daily_sentiment:
                        daily_sentiment[day] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
                    daily_sentiment[day][post.sentiment or "neutral"] += 1
                    daily_sentiment[day]["total"] += 1

            return [
                {"date": k, **v}
                for k, v in sorted(daily_sentiment.items())
            ]
        finally:
            session.close()

    # ============================================================
    # Maintenance Operations
    # ============================================================

    def cleanup_old_posts(self, days_to_keep: int = 90) -> int:
        """Remove posts older than specified days."""
        session = get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            deleted = session.query(SocialPost).filter(
                SocialPost.scraped_at < cutoff
            ).delete()
            session.commit()
            logger.info(f"Cleaned up {deleted} old posts.")
            return deleted
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up posts: {e}")
            return 0
        finally:
            session.close()

    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        session = get_session()
        try:
            total = session.query(SocialPost).filter(SocialPost.is_active == True).count()
            by_source = {}
            for source in ["reddit", "twitter", "instagram"]:
                by_source[source] = session.query(SocialPost).filter(
                    SocialPost.is_active == True,
                    SocialPost.source == source
                ).count()

            return {
                "total_posts": total,
                "by_source": by_source,
                "tables": {
                    "social_posts": total,
                    "daily_insights": session.query(DailyInsight).count(),
                    "trending_keywords": session.query(TrendingKeyword).count()
                }
            }
        finally:
            session.close()

    # ============================================================
    # Helper Methods
    # ============================================================

    @staticmethod
    def _post_to_dict(post: SocialPost) -> Dict:
        """Convert a SocialPost ORM object to a dictionary."""
        return {
            "id": post.id,
            "source": post.source,
            "post_id": post.post_id,
            "platform_url": post.platform_url,
            "author": post.author,
            "text": post.text,
            "timestamp": post.timestamp.isoformat() if post.timestamp else None,
            "drink_types": json.loads(post.drink_types) if post.drink_types else [],
            "sentiment": post.sentiment,
            "sentiment_score": post.sentiment_score,
            "likes": post.likes,
            "comments": post.comments,
            "shares": post.shares,
            "hour_of_day": post.hour_of_day,
            "day_of_week": post.day_of_week,
            "engagement_score": post.engagement_score,
            "estimated_age_group": post.estimated_age_group,
            "keywords_found": json.loads(post.keywords_found) if post.keywords_found else [],
            "scraped_at": post.scraped_at.isoformat() if post.scraped_at else None
        }
