"""
Reddit Scraper Module
Scrapes public Reddit posts mentioning coffee-related keywords
using the Reddit API (via PRAW).
"""

import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional

from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    COFFEE_KEYWORDS, MAX_POSTS_PER_SOURCE
)

logger = logging.getLogger(__name__)


class RedditScraper:
    """Scrapes Reddit for coffee-related posts."""

    SUBREDDITS = [
        "coffee", "Coffee", "coffeestation",
        "espresso", "barista", "roasting",
        "coldbrew", "latteart", "coffeeholic",
        "caffeine", "coffeeshops", "specialtycoffee",
        "homecafe", "coffeeart"
    ]

    def __init__(self):
        self._reddit = None
        self._initialize_praw()

    def _initialize_praw(self):
        """Initialize PRAW Reddit instance."""
        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            logger.warning("Reddit API credentials not configured. Using mock data.")
            return

        try:
            import praw
            self._reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT,
                check_for_async=False
            )
            logger.info("Reddit API client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self._reddit = None

    def scrape(self) -> List[Dict]:
        """Scrape coffee-related posts from Reddit."""
        if self._reddit is None:
            return self._get_mock_data()

        posts = []
        seen_ids = set()

        for subreddit_name in self.SUBREDDITS:
            try:
                subreddit = self._reddit.subreddit(subreddit_name)
                search_query = " OR ".join(COFFEE_KEYWORDS[:5])
                
                # Search recent posts
                for submission in subreddit.search(
                    search_query,
                    limit=MAX_POSTS_PER_SOURCE // len(self.SUBREDDITS),
                    sort="new",
                    time_filter="day"
                ):
                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)

                    post_data = self._extract_post_data(submission)
                    if post_data:
                        posts.append(post_data)
                    
                    if len(posts) >= MAX_POSTS_PER_SOURCE:
                        break

                if len(posts) >= MAX_POSTS_PER_SOURCE:
                    break

            except Exception as e:
                logger.error(f"Error scraping r/{subreddit_name}: {e}")
                continue

        logger.info(f"Scraped {len(posts)} posts from Reddit.")
        return posts

    def _extract_post_data(self, submission) -> Optional[Dict]:
        """Extract structured data from a Reddit submission."""
        try:
            text = submission.selftext or ""
            if not text and submission.title:
                text = submission.title

            if not text:
                return None

            # Check if post mentions coffee keywords
            text_lower = text.lower()
            found_keywords = [kw for kw in COFFEE_KEYWORDS if kw in text_lower]
            if not found_keywords:
                return None

            return {
                "source": "reddit",
                "post_id": f"reddit_{submission.id}",
                "platform_url": f"https://reddit.com{submission.permalink}",
                "author": f"u_{submission.id}",  # anonymized
                "text": text[:4000],  # limit text length
                "timestamp": datetime.fromtimestamp(
                    submission.created_utc, tz=timezone.utc
                ),
                "likes": submission.score or 0,
                "comments": submission.num_comments or 0,
                "shares": 0,
                "keywords_found": json.dumps(found_keywords),
                "drink_types": "",  # will be extracted in processor
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "hour_of_day": submission.created_utc % 86400 // 3600,
                "day_of_week": datetime.fromtimestamp(
                    submission.created_utc, tz=timezone.utc
                ).weekday(),
                "engagement_score": (submission.score or 0) + (submission.num_comments or 0),
                "estimated_age_group": None
            }
        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None

    def _get_mock_data(self) -> List[Dict]:
        """Generate mock data for testing when Reddit API is not configured."""
        import random
        
        mock_drinks = [
            "espresso", "latte", "cappuccino", "cold brew", "americano",
            "flat white", "mocha", "iced coffee", "macchiato"
        ]
        
        mock_texts = [
            "Just had the best latte at my local coffee shop! The barista really knows their craft. #coffeelover",
            "Cold brew season is here and I'm not disappointed. Smooth and refreshing all day long.",
            "Morning espresso is the only thing getting me through this Monday. Who else relates?",
            "Tried making a cappuccino at home today. The milk art didn't work out but the taste was amazing!",
            "There's nothing quite like a perfectly pulled espresso shot on a Sunday morning.",
            "I've been experimenting with different coffee bean origins. Ethiopian beans are my new favorite.",
            "The iced latte I got today was absolutely perfect. Not too sweet, great coffee flavor.",
            "Coffee shop hopping this weekend. Found a gem that does pour over right!",
            "My morning routine: fresh ground coffee, French press, and a good book.",
            "Flat white appreciation post. It's the perfect balance of espresso and silky milk.",
            "Just discovered that cold brew concentrate is a game changer for iced coffee at home.",
            "The coffee aroma in the morning is pure happiness. Nothing beats freshly brewed coffee.",
            "Trying to perfect my latte art. Today's attempt looked like a heart... sort of!",
            "Double shot americano hits different when you need that extra boost.",
            "Mocha latte for the win on a rainy afternoon. Cozy coffee vibes.",
        ]

        age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
        sentiments = ["positive", "neutral", "negative"]
        sentiment_scores = {
            "positive": random.uniform(0.5, 1.0),
            "neutral": random.uniform(-0.2, 0.2),
            "negative": random.uniform(-1.0, -0.3)
        }

        posts = []
        for i in range(50):
            hour = random.randint(5, 22)
            day = random.randint(0, 6)
            drink = random.choice(mock_drinks)
            text = random.choice(mock_texts)
            sentiment = random.choices(
                sentiments, weights=[0.6, 0.3, 0.1], k=1
            )[0]

            # Use valid Reddit URLs pointing to real r/coffee subreddit
            # so links are clickable and lead to a real page
            subreddit_name = random.choice(self.SUBREDDITS[:5])
            posts.append({
                "source": "reddit",
                "post_id": f"reddit_mock_{i}",
                "platform_url": f"https://www.reddit.com/r/{subreddit_name}/",
                "author": f"u_mock_user_{i}",
                "text": text,
                "timestamp": datetime.now(timezone.utc).replace(
                    hour=hour, minute=random.randint(0, 59)
                ),
                "likes": random.randint(0, 500),
                "comments": random.randint(0, 100),
                "shares": random.randint(0, 20),
                "keywords_found": json.dumps([drink, "coffee"]),
                "drink_types": json.dumps([drink]),
                "sentiment": sentiment,
                "sentiment_score": sentiment_scores[sentiment],
                "hour_of_day": hour,
                "day_of_week": day,
                "engagement_score": random.randint(10, 600),
                "estimated_age_group": random.choice(age_groups)
            })

        logger.info(f"Generated {len(posts)} mock Reddit posts.")
        return posts
