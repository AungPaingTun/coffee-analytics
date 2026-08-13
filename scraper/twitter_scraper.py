"""
Twitter/X Scraper Module
Scrapes public tweets mentioning coffee-related keywords
using the Twitter v2 API.
"""

import logging
import json
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

import requests

from config import (
    TWITTER_BEARER_TOKEN, COFFEE_KEYWORDS, MAX_POSTS_PER_SOURCE
)

logger = logging.getLogger(__name__)


class TwitterScraper:
    """Scrapes Twitter/X for coffee-related tweets."""

    BASE_URL = "https://api.twitter.com/2/tweets/search/recent"

    def __init__(self):
        self._headers = {}
        if TWITTER_BEARER_TOKEN:
            self._headers = {
                "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
                "Content-Type": "application/json"
            }

    def scrape(self) -> List[Dict]:
        """Scrape coffee-related tweets from Twitter/X."""
        if not TWITTER_BEARER_TOKEN:
            logger.warning("Twitter API credentials not configured. Using mock data.")
            return self._get_mock_data()

        posts = []
        seen_ids = set()

        # Build search query from keywords
        search_query = " OR ".join(COFFEE_KEYWORDS[:10])
        search_query += " -is:retweet"

        params = {
            "query": search_query,
            "max_results": min(MAX_POSTS_PER_SOURCE, 100),
            "tweet.fields": "created_at,public_metrics,author_id,lang,text",
            "user.fields": "created_at",
            "expansions": "author_id",
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=self._headers,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                tweets = data.get("data", [])

                for tweet in tweets:
                    if tweet["id"] in seen_ids:
                        continue
                    seen_ids.add(tweet["id"])

                    post_data = self._extract_tweet_data(tweet, data.get("includes", {}))
                    if post_data:
                        posts.append(post_data)

                # Handle pagination
                while (
                    "next_token" in data.get("meta", {})
                    and len(posts) < MAX_POSTS_PER_SOURCE
                ):
                    time.sleep(1.5)  # Respect rate limits
                    params["pagination_token"] = data["meta"]["next_token"]
                    response = requests.get(
                        self.BASE_URL,
                        headers=self._headers,
                        params=params,
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        tweets = data.get("data", [])
                        for tweet in tweets:
                            if tweet["id"] in seen_ids:
                                continue
                            seen_ids.add(tweet["id"])
                            post_data = self._extract_tweet_data(
                                tweet, data.get("includes", {})
                            )
                            if post_data:
                                posts.append(post_data)
                    else:
                        break

            elif response.status_code == 429:
                logger.warning("Twitter API rate limit reached.")
                return posts

            else:
                logger.error(f"Twitter API error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Twitter API request failed: {e}")

        if not posts:
            return self._get_mock_data()

        logger.info(f"Scraped {len(posts)} tweets from Twitter.")
        return posts

    def _extract_tweet_data(self, tweet: Dict, includes: Dict) -> Optional[Dict]:
        """Extract structured data from a Twitter tweet."""
        try:
            text = tweet.get("text", "")
            if not text:
                return None

            # Check if tweet mentions coffee keywords
            text_lower = text.lower()
            found_keywords = [kw for kw in COFFEE_KEYWORDS if kw in text_lower]
            if not found_keywords:
                return None

            created_at = datetime.fromisoformat(
                tweet["created_at"].replace("Z", "+00:00")
            )

            metrics = tweet.get("public_metrics", {})
            likes = metrics.get("like_count", 0)
            replies = metrics.get("reply_count", 0)
            retweets = metrics.get("retweet_count", 0)

            return {
                "source": "twitter",
                "post_id": f"twitter_{tweet['id']}",
                "platform_url": f"https://twitter.com/i/status/{tweet['id']}",
                "author": f"tw_{tweet.get('author_id', 'unknown')}",
                "text": text[:280],
                "timestamp": created_at,
                "likes": likes,
                "comments": replies,
                "shares": retweets,
                "keywords_found": json.dumps(found_keywords),
                "drink_types": "",  # extracted in processor
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "hour_of_day": created_at.hour,
                "day_of_week": created_at.weekday(),
                "engagement_score": likes + replies + retweets,
                "estimated_age_group": None
            }
        except Exception as e:
            logger.error(f"Error extracting tweet data: {e}")
            return None

    def _get_mock_data(self) -> List[Dict]:
        """Generate mock Twitter data for testing."""
        import random

        mock_texts = [
            "Just found the best cold brew in town! This place is a hidden gem ☕",
            "Monday mornings require a double espresso. No exceptions.",
            "The latte art at this new coffee shop is absolutely stunning!",
            "Hot take: iced coffee in winter is peak human experience.",
            "Trying to perfect my home espresso setup. Any tips from fellow coffee nerds?",
            "That feeling when the coffee shop remembers your order ❤️",
            "Flat white appreciation thread. Fight me.",
            "Cappuccino art today: 4/10. Getting better though!",
            "Coffee shop WiFi + good coffee = productivity unlocked.",
            "The smell of freshly ground coffee in the morning is unbeatable.",
            "Just discovered oat milk latte and I'll never go back.",
            "Cold brew concentrate is the best investment for summer mornings.",
            "Pour over coffee is a ritual, not just a drink.",
            "My iced americano recipe: 2 shots espresso, ice, cold water. Simple perfection.",
            "Mocha latte on a rainy day = pure coziness.",
            "Espresso martini after dinner hits different.",
            "The barista at my local shop just made the most beautiful rosetta!",
            "Coffee subscription boxes are changing my morning routine.",
            "Ethiopian coffee beans have the most complex flavors. Highly recommend.",
            "Macchiato is criminally underrated in the coffee world.",
        ]

        age_groups = ["18-24", "25-34", "35-44", "45-54"]
        drink_types = [
            "espresso", "latte", "cappuccino", "cold brew", "americano",
            "flat white", "mocha", "iced coffee", "macchiato", "pour over"
        ]
        sentiments = ["positive", "neutral", "negative"]
        sentiment_scores = {
            "positive": random.uniform(0.4, 1.0),
            "neutral": random.uniform(-0.1, 0.1),
            "negative": random.uniform(-0.8, -0.2)
        }

        posts = []
        for i in range(40):
            hour = random.choices(
                list(range(6, 20)),
                weights=[1, 2, 3, 5, 6, 5, 4, 4, 3, 3, 2, 2, 1, 1],
                k=1
            )[0]
            day = random.randint(0, 6)
            sentiment = random.choices(
                sentiments, weights=[0.55, 0.35, 0.1], k=1
            )[0]

            posts.append({
                "source": "twitter",
                "post_id": f"twitter_mock_{i}",
                "platform_url": f"https://x.com/search?q=coffee&src=typed_query",
                "author": f"tw_mock_user_{i}",
                "text": random.choice(mock_texts),
                "timestamp": datetime.now(timezone.utc).replace(
                    hour=hour, minute=random.randint(0, 59)
                ),
                "likes": random.randint(0, 2000),
                "comments": random.randint(0, 500),
                "shares": random.randint(0, 300),
                "keywords_found": json.dumps(["coffee"]),
                "drink_types": json.dumps([random.choice(drink_types)]),
                "sentiment": sentiment,
                "sentiment_score": sentiment_scores[sentiment],
                "hour_of_day": hour,
                "day_of_week": day,
                "engagement_score": random.randint(5, 2500),
                "estimated_age_group": random.choice(age_groups)
            })

        logger.info(f"Generated {len(posts)} mock Twitter posts.")
        return posts
