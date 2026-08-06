"""
Data Processing Pipeline
Orchestrates the full data processing pipeline:
1. Ingest raw scraped posts
2. Extract drink types and keywords
3. Analyze sentiment
4. Compute derived fields
5. Save to database
"""

import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional

from processor.sentiment import analyze_sentiment
from processor.drink_extractor import (
    extract_drink_types, estimate_age_group, get_extractor
)
from models import get_session, SocialPost

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Processes raw scraped posts through the full analytics pipeline.
    """

    def __init__(self):
        self._extractor = get_extractor()
        logger.info("Processing pipeline initialized.")

    def process_batch(self, posts: List[Dict]) -> List[SocialPost]:
        """
        Process a batch of raw scraped posts.
        
        Args:
            posts: List of raw post dictionaries from scrapers.
        
        Returns:
            List of processed SocialPost ORM objects ready for database insertion.
        """
        processed_posts = []

        for post_data in posts:
            try:
                social_post = self._process_single_post(post_data)
                if social_post:
                    processed_posts.append(social_post)
            except Exception as e:
                logger.error(f"Error processing post {post_data.get('post_id')}: {e}")
                continue

        logger.info(f"Processed {len(processed_posts)}/{len(posts)} posts successfully.")
        return processed_posts

    def _process_single_post(self, post_data: Dict) -> Optional[SocialPost]:
        """
        Process a single raw post through the pipeline.
        
        Returns:
            Processed SocialPost object, or None if processing fails.
        """
        text = post_data.get("text", "")
        if not text:
            return None

        # Step 1: Sentiment analysis
        sentiment_result = analyze_sentiment(text)

        # Step 2: Extract drink types
        drink_types = extract_drink_types(text)

        # Step 3: Extract keywords
        keywords = self._extractor.extract_keywords(text)

        # Step 4: Estimate age group
        age_group = estimate_age_group(text)

        # Step 5: Build the ORM object
        social_post = SocialPost(
            source=post_data.get("source", "unknown"),
            post_id=post_data.get("post_id", ""),
            platform_url=post_data.get("platform_url", ""),
            author=post_data.get("author", "anonymous"),
            text=text,
            timestamp=post_data.get("timestamp", datetime.now(timezone.utc)),
            drink_types=json.dumps(drink_types) if drink_types else None,
            sentiment=sentiment_result["sentiment"],
            sentiment_score=sentiment_result["score"],
            likes=post_data.get("likes", 0),
            comments=post_data.get("comments", 0),
            shares=post_data.get("shares", 0),
            hour_of_day=post_data.get("hour_of_day"),
            day_of_week=post_data.get("day_of_week"),
            engagement_score=post_data.get("engagement_score", 0),
            estimated_age_group=age_group,
            keywords_found=json.dumps(keywords) if keywords else None,
            is_active=True
        )

        return social_post

    def save_to_db(self, posts: List[SocialPost]) -> int:
        """
        Save processed posts to the database.
        
        Args:
            posts: List of SocialPost ORM objects.
        
        Returns:
            Number of posts successfully saved.
        """
        if not posts:
            return 0

        session = get_session()
        saved_count = 0

        try:
            for post in posts:
                # Check for duplicates
                existing = session.query(SocialPost).filter_by(
                    post_id=post.post_id
                ).first()

                if existing:
                    logger.debug(f"Duplicate post skipped: {post.post_id}")
                    continue

                session.add(post)
                saved_count += 1

            session.commit()
            logger.info(f"Saved {saved_count} new posts to database.")

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving posts to database: {e}")
            return 0
        finally:
            session.close()

        return saved_count

    def process_and_save(self, raw_posts: List[Dict]) -> Dict:
        """
        Full pipeline: process raw posts and save to database.
        
        Args:
            raw_posts: List of raw post dictionaries from scrapers.
        
        Returns:
            Dictionary with processing statistics.
        """
        logger.info(f"Starting pipeline with {len(raw_posts)} raw posts...")

        # Process
        processed = self.process_batch(raw_posts)

        # Save
        saved = self.save_to_db(processed)

        stats = {
            "raw_posts": len(raw_posts),
            "processed": len(processed),
            "saved": saved,
            "skipped_duplicates": len(processed) - saved,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Pipeline complete. Stats: {stats}")
        return stats
