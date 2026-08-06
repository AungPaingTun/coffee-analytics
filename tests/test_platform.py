"""
Test Suite for Coffee Analytics Platform
Tests for scraper, processor, analytics, and API endpoints.
"""

import os
import sys
import json
import pytest
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import COFFEE_KEYWORDS
from processor.sentiment import analyze_sentiment, SentimentAnalyzer
from processor.drink_extractor import extract_drink_types, estimate_age_group, DrinkTypeExtractor
from processor.pipeline import ProcessingPipeline
from processor.analytics import AnalyticsProcessor
from database import DatabaseService
from models import init_db, get_session, SocialPost


# ============================================================
# Test Sentiment Analysis
# ============================================================

class TestSentimentAnalysis:
    """Tests for the sentiment analyzer."""

    def test_positive_sentiment(self):
        result = analyze_sentiment("This coffee is absolutely amazing and delicious!")
        assert result["sentiment"] == "positive"
        assert result["score"] > 0

    def test_negative_sentiment(self):
        result = analyze_sentiment("This coffee was terrible and burnt. Worst I've ever had.")
        assert result["sentiment"] == "negative"
        assert result["score"] < 0

    def test_neutral_sentiment(self):
        result = analyze_sentiment("I had coffee today at the shop.")
        assert result["sentiment"] == "neutral"

    def test_empty_text(self):
        result = analyze_sentiment("")
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.0

    def test_emoji_positive(self):
        result = analyze_sentiment("Love my morning latte ☕❤️")
        assert result["sentiment"] == "positive"

    def test_emoji_negative(self):
        result = analyze_sentiment("Terrible coffee experience 😤👎")
        assert result["sentiment"] == "negative"

    def test_coffee_specific_words(self):
        result = analyze_sentiment("The velvety smooth espresso was heavenly!")
        assert result["sentiment"] == "positive"

    def test_confidence_score(self):
        result = analyze_sentiment("Amazing perfect coffee!")
        assert 0 <= result["confidence"] <= 1

    def test_score_range(self):
        result = analyze_sentiment("Great coffee shop with delicious pastries")
        assert -1.0 <= result["score"] <= 1.0


# ============================================================
# Test Drink Type Extraction
# ============================================================

class TestDrinkExtraction:
    """Tests for drink type extraction."""

    def test_single_drink(self):
        drinks = extract_drink_types("Had a great latte this morning")
        assert "latte" in drinks

    def test_multiple_drinks(self):
        drinks = extract_drink_types("Love espresso and cold brew")
        assert "espresso" in drinks
        assert "cold brew" in drinks

    def test_generic_coffee(self):
        drinks = extract_drink_types("Coffee is the best way to start the day")
        assert "coffee" in drinks

    def test_no_drink(self):
        drinks = extract_drink_types("Just had a great breakfast")
        assert len(drinks) == 0

    def test_iced_latte(self):
        drinks = extract_drink_types("The iced latte was refreshing")
        assert "iced latte" in drinks

    def test_pour_over(self):
        drinks = extract_drink_types("Made a pour over with V60 this morning")
        assert "pour over" in drinks

    def test_age_estimation_young(self):
        age = estimate_age_group("College student here, love coffee")
        assert age == "18-24"

    def test_age_estimation_millennial(self):
        age = estimate_age_group("Millennial here, love remote work and coffee")
        assert age == "25-34"

    def test_age_estimation_retired(self):
        age = estimate_age_group("Retired and enjoying morning coffee routines")
        assert age == "55+"

    def test_age_estimation_none(self):
        age = estimate_age_group("Coffee is great")
        assert age is None


# ============================================================
# Test Pipeline
# ============================================================

class TestPipeline:
    """Tests for the processing pipeline."""

    def setup_method(self):
        """Initialize database for tests."""
        init_db()

    def test_process_single_post(self):
        pipeline = ProcessingPipeline()
        raw_post = {
            "source": "test",
            "post_id": "test_1",
            "platform_url": "https://example.com",
            "author": "test_user",
            "text": "Amazing latte at the coffee shop today!",
            "timestamp": datetime.now(timezone.utc),
            "likes": 10,
            "comments": 3,
            "shares": 1,
            "keywords_found": json.dumps(["coffee", "latte"]),
            "hour_of_day": 9,
            "day_of_week": 2,
            "engagement_score": 14
        }

        processed = pipeline.process_batch([raw_post])
        assert len(processed) == 1
        assert processed[0].sentiment == "positive"
        assert processed[0].likes == 10

    def test_process_empty_batch(self):
        pipeline = ProcessingPipeline()
        result = pipeline.process_batch([])
        assert len(result) == 0

    def test_process_post_without_text(self):
        pipeline = ProcessingPipeline()
        raw_post = {
            "source": "test",
            "post_id": "test_2",
            "text": "",
            "timestamp": datetime.now(timezone.utc),
            "likes": 0,
            "comments": 0,
            "shares": 0
        }
        result = pipeline.process_batch([raw_post])
        assert len(result) == 0


# ============================================================
# Test Analytics
# ============================================================

class TestAnalytics:
    """Tests for the analytics processor."""

    def setup_method(self):
        """Initialize database and insert test data."""
        init_db()
        self._insert_test_data()

    def _insert_test_data(self):
        """Insert sample data for testing, cleaning up first."""
        import time
        session = get_session()
        try:
            # Clean up previous test data
            session.query(SocialPost).filter(SocialPost.post_id.like('test_analytics_%')).delete()
            session.commit()
            
            ts = datetime.now(timezone.utc)
            for i in range(10):
                post = SocialPost(
                    source="test",
                    post_id=f"test_analytics_{int(time.time())}_{i}",
                    text="Great coffee experience",
                    timestamp=ts,
                    drink_types=json.dumps(["latte", "espresso"]),
                    sentiment="positive",
                    sentiment_score=0.7,
                    likes=10 * (i + 1),
                    comments=5 * (i + 1),
                    hour_of_day=i % 24,
                    day_of_week=i % 7,
                    engagement_score=15 * (i + 1),
                    estimated_age_group="25-34" if i % 2 == 0 else "18-24",
                    keywords_found=json.dumps(["coffee"]),
                    is_active=True
                )
                session.add(post)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def test_get_popular_drinks(self):
        analytics = AnalyticsProcessor()
        result = analytics.get_popular_drink_types()
        assert "drinks" in result
        assert "latte" in result["drinks"] or "espresso" in result["drinks"]

    def test_get_peak_hours(self):
        analytics = AnalyticsProcessor()
        result = analytics.get_peak_hours()
        assert "hourly_data" in result
        assert len(result["hourly_data"]) == 24

    def test_get_sentiment_breakdown(self):
        analytics = AnalyticsProcessor()
        result = analytics.get_sentiment_breakdown()
        assert "positive" in result
        assert "neutral" in result
        assert "negative" in result
        assert result["total_posts"] >= 10

    def test_get_trending_keywords(self):
        analytics = AnalyticsProcessor()
        result = analytics.get_trending_keywords()
        assert "trending" in result
        assert len(result["trending"]) > 0

    def test_get_overall_summary(self):
        analytics = AnalyticsProcessor()
        result = analytics.get_overall_summary()
        assert result["total_posts"] >= 10
        assert result["average_sentiment_score"] > 0


# ============================================================
# Test Database Service
# ============================================================

class TestDatabaseService:
    """Tests for the database service layer."""

    def setup_method(self):
        """Initialize database."""
        init_db()

    def test_save_and_retrieve_posts(self):
        import time
        db = DatabaseService()
        # Clean up any previous test data
        session = get_session()
        session.query(SocialPost).filter(SocialPost.post_id == 'db_test_1').delete()
        session.commit()
        session.close()
        
        posts = [
            {
                "source": "reddit",
                "post_id": f"db_test_{int(time.time())}",
                "platform_url": "https://reddit.com/test",
                "author": "user1",
                "text": "Test coffee post",
                "timestamp": datetime.now(timezone.utc),
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "likes": 5,
                "comments": 2,
                "shares": 0,
                "hour_of_day": 8,
                "day_of_week": 1,
                "engagement_score": 7,
                "drink_types": json.dumps(["coffee"]),
                "keywords_found": json.dumps(["coffee"]),
                "is_active": True
            }
        ]
        saved = db.save_posts(posts)
        assert saved == 1

        # Retrieve
        retrieved = db.get_recent_posts(limit=10)
        assert len(retrieved) >= 1

    def test_search_posts(self):
        db = DatabaseService()
        results = db.search_posts("coffee", limit=10)
        assert isinstance(results, list)

    def test_get_database_stats(self):
        db = DatabaseService()
        stats = db.get_database_stats()
        assert "total_posts" in stats
        assert "by_source" in stats


# ============================================================
# Test Config
# ============================================================

class TestConfig:
    """Tests for configuration module."""

    def test_coffee_keywords(self):
        assert len(COFFEE_KEYWORDS) > 0
        assert "coffee" in COFFEE_KEYWORDS
        assert "latte" in COFFEE_KEYWORDS
        assert "espresso" in COFFEE_KEYWORDS

    def test_config_values(self):
        from config import DATABASE_URL, MAX_POSTS_PER_SOURCE
        assert DATABASE_URL is not None
        assert MAX_POSTS_PER_SOURCE > 0


# ============================================================
# Run tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
