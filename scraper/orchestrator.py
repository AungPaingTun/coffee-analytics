"""
Scraper Orchestrator
Coordinates scraping from all social media sources,
manages rate limiting, deduplication, and data flow to the processor.
"""

import logging
import time
import json
from datetime import datetime, timezone
from typing import List, Dict

from config import SCRAPE_INTERVAL_HOURS, MAX_POSTS_PER_SOURCE
from scraper.reddit_scraper import RedditScraper
from scraper.twitter_scraper import TwitterScraper
from scraper.instagram_scraper import InstagramScraper

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """
    Orchestrates the scraping process across all social media platforms.
    Handles scheduling, deduplication, and data handoff to the processor.
    """

    def __init__(self):
        self.reddit_scraper = RedditScraper()
        self.twitter_scraper = TwitterScraper()
        self.instagram_scraper = InstagramScraper()
        self._scraped_post_ids = set()
        self._last_scrape_time = None
        self._stats = {
            "total_scraped": 0,
            "reddit_count": 0,
            "twitter_count": 0,
            "instagram_count": 0,
            "duplicates_removed": 0,
            "errors": 0
        }

    def scrape_all(self) -> List[Dict]:
        """
        Scrape all configured sources and return combined results.
        
        Returns:
            List of post dictionaries ready for processing.
        """
        logger.info("=" * 50)
        logger.info("Starting social media scraping run")
        logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 50)

        all_posts = []
        self._stats = {
            "total_scraped": 0,
            "reddit_count": 0,
            "twitter_count": 0,
            "instagram_count": 0,
            "duplicates_removed": 0,
            "errors": 0
        }

        # Scrape Reddit
        try:
            reddit_posts = self.reddit_scraper.scrape()
            self._stats["reddit_count"] = len(reddit_posts)
            all_posts.extend(reddit_posts)
            logger.info(f"Reddit: collected {len(reddit_posts)} posts")
        except Exception as e:
            logger.error(f"Reddit scraping failed: {e}")
            self._stats["errors"] += 1

        # Small delay between sources to respect rate limits
        time.sleep(1)

        # Scrape Twitter
        try:
            twitter_posts = self.twitter_scraper.scrape()
            self._stats["twitter_count"] = len(twitter_posts)
            all_posts.extend(twitter_posts)
            logger.info(f"Twitter: collected {len(twitter_posts)} posts")
        except Exception as e:
            logger.error(f"Twitter scraping failed: {e}")
            self._stats["errors"] += 1

        time.sleep(1)

        # Scrape Instagram
        try:
            instagram_posts = self.instagram_scraper.scrape()
            self._stats["instagram_count"] = len(instagram_posts)
            all_posts.extend(instagram_posts)
            logger.info(f"Instagram: collected {len(instagram_posts)} posts")
        except Exception as e:
            logger.error(f"Instagram scraping failed: {e}")
            self._stats["errors"] += 1

        # Deduplicate posts
        all_posts = self._deduplicate(all_posts)

        # Update stats
        self._stats["total_scraped"] = len(all_posts)
        self._last_scrape_time = datetime.now(timezone.utc)

        logger.info(f"Total unique posts collected: {len(all_posts)}")
        logger.info(f"Scraping stats: {json.dumps(self._stats, indent=2)}")

        return all_posts

    def _deduplicate(self, posts: List[Dict]) -> List[Dict]:
        """Remove duplicate posts based on post_id."""
        seen = set()
        unique_posts = []

        for post in posts:
            post_id = post.get("post_id", "")
            if post_id and post_id not in seen:
                seen.add(post_id)
                unique_posts.append(post)
            else:
                self._stats["duplicates_removed"] += 1

        return unique_posts

    def get_stats(self) -> Dict:
        """Return current scraping statistics."""
        return {
            **self._stats,
            "last_scrape_time": (
                self._last_scrape_time.isoformat()
                if self._last_scrape_time
                else None
            ),
            "scrape_interval_hours": SCRAPE_INTERVAL_HOURS
        }

    def should_scrape(self) -> bool:
        """Check if enough time has passed since last scrape."""
        if self._last_scrape_time is None:
            return True
        
        elapsed = datetime.now(timezone.utc) - self._last_scrape_time
        return elapsed.total_seconds() >= SCRAPE_INTERVAL_HOURS * 3600

    def scrape_and_save(self, save_func) -> List[Dict]:
        """
        Scrape all sources and save results to database.
        
        Args:
            save_func: Function that accepts a list of post dicts and saves them.
        
        Returns:
            List of saved posts.
        """
        posts = self.scrape_all()
        if posts:
            save_func(posts)
        return posts
