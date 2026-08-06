"""
Instagram Scraper Module
Scrapes public Instagram posts using coffee-related hashtags.
Uses BeautifulSoup to scrape public hashtag pages.
Respects rate limits and only collects publicly available data.
"""

import logging
import json
import time
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

from config import COFFEE_KEYWORDS, MAX_POSTS_PER_SOURCE

logger = logging.getLogger(__name__)


class InstagramScraper:
    """Scrapes Instagram for coffee-related public posts via hashtags."""

    HASHTAGS = [
        "coffee", "latte", "espresso", "cappuccino", "coldbrew",
        "icedcoffee", "coffeeshop", "latteart", "specialtycoffee",
        "coffeelover", "coffeetime", "morningcoffee", "baristalife",
        "coffeegram", "coffeelovers", "flatwhite", "mocha",
        "americano", "macchiato", "coffeelife"
    ]

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        self._can_scrape = True

    def scrape(self) -> List[Dict]:
        """Scrape coffee-related posts from Instagram."""
        try:
            # Test if we can reach Instagram
            test_url = "https://www.instagram.com/explore/tags/coffee/"
            response = self._session.get(test_url, timeout=10)
            if response.status_code == 200:
                return self._scrape_hashtag_pages()
            else:
                logger.warning(f"Instagram returned status {response.status_code}. Using mock data.")
                return self._get_mock_data()
        except Exception as e:
            logger.warning(f"Cannot reach Instagram: {e}. Using mock data.")
            return self._get_mock_data()

    def _scrape_hashtag_pages(self) -> List[Dict]:
        """Scrape posts from multiple coffee hashtags."""
        posts = []
        seen_ids = set()
        max_per_hashtag = MAX_POSTS_PER_SOURCE // len(self.HASHTAGS)

        for hashtag in self.HASHTAGS:
            if len(posts) >= MAX_POSTS_PER_SOURCE:
                break

            try:
                hashtag_posts = self._scrape_single_hashtag(hashtag, max_per_hashtag)
                for post in hashtag_posts:
                    if post["post_id"] not in seen_ids:
                        seen_ids.add(post["post_id"])
                        posts.append(post)

                # Respect rate limits
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error scraping #{hashtag}: {e}")
                continue

        logger.info(f"Scraped {len(posts)} posts from Instagram.")
        return posts

    def _scrape_single_hashtag(self, hashtag: str, limit: int) -> List[Dict]:
        """Scrape posts from a single Instagram hashtag page."""
        posts = []
        url = f"https://www.instagram.com/explore/tags/{hashtag}/"

        try:
            response = self._session.get(url, timeout=15)

            if response.status_code != 200:
                return posts

            # Parse the page for post data in the JSON embedded in the page
            soup = BeautifulSoup(response.text, "lxml")

            # Try to find the shared data in a script tag
            scripts = soup.find_all("script", type="text/javascript")
            for script in scripts:
                if script.string and "edge_hashtag_to_media" in str(script.string):
                    posts = self._parse_instagram_json(
                        script.string, hashtag, limit
                    )
                    break

            # If no JSON data found, try alternative parsing
            if not posts:
                posts = self._parse_alt_format(response.text, hashtag, limit)

        except Exception as e:
            logger.error(f"Error fetching #{hashtag}: {e}")

        return posts

    def _parse_instagram_json(self, script_content: str, hashtag: str, limit: int) -> List[Dict]:
        """Parse Instagram's embedded JSON data from script tags."""
        posts = []
        try:
            # Extract JSON from the script content
            json_match = re.search(
                r'"edge_hashtag_to_media":\s*\{"count":\d+,\s*"page_info":.*?"edges":\s*(\[[^\]]*\])',
                script_content
            )
            if not json_match:
                return posts

            edges_data = json.loads(json_match.group(1))
            
            for edge in edges_data[:limit]:
                node = edge.get("node", {})
                post_id = node.get("id", "")
                text = node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "")
                timestamp = datetime.fromtimestamp(
                    node.get("taken_at_timestamp", 0), tz=timezone.utc
                )

                if text:
                    text_lower = text.lower()
                    found_keywords = [kw for kw in COFFEE_KEYWORDS if kw in text_lower]
                    
                    likes = node.get("edge_liked_by", {}).get("count", 0)
                    comments = node.get("edge_media_to_comment", {}).get("count", 0)

                    posts.append({
                        "source": "instagram",
                        "post_id": f"insta_{post_id}",
                        "platform_url": f"https://www.instagram.com/p/{post_id}/",
                        "author": f"ig_{node.get('owner', {}).get('id', 'unknown')}",
                        "text": text[:2200],
                        "timestamp": timestamp,
                        "likes": likes,
                        "comments": comments,
                        "shares": 0,
                        "keywords_found": json.dumps(found_keywords if found_keywords else ["coffee"]),
                        "drink_types": "",
                        "sentiment": "neutral",
                        "sentiment_score": 0.0,
                        "hour_of_day": timestamp.hour,
                        "day_of_week": timestamp.weekday(),
                        "engagement_score": likes + comments,
                        "estimated_age_group": None
                    })

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
        except Exception as e:
            logger.error(f"Error parsing Instagram data: {e}")

        return posts

    def _parse_alt_format(self, html_content: str, hashtag: str, limit: int) -> List[Dict]:
        """Alternative parsing method for Instagram pages."""
        posts = []
        try:
            # Look for window._sharedData pattern
            match = re.search(
                r'window\._sharedData\s*=\s*(\{.*?\});\s*</script>',
                html_content,
                re.DOTALL
            )
            if match:
                data = json.loads(match.group(1))
                media_data = (
                    data.get("entry_data", {}).get("TagPage", [{}])[0]
                    .get("graphql", {}).get("hashtag", {})
                    .get("edge_hashtag_to_media", {}).get("edges", [])
                )

                for edge in media_data[:limit]:
                    node = edge.get("node", {})
                    post_id = node.get("id", "")
                    text_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                    text = text_edges[0].get("node", {}).get("text", "") if text_edges else ""

                    if text:
                        posts.append({
                            "source": "instagram",
                            "post_id": f"insta_{post_id}",
                            "platform_url": f"https://www.instagram.com/p/{post_id}/",
                            "author": f"ig_{node.get('owner', {}).get('id', 'unknown')}",
                            "text": text[:2200],
                            "timestamp": datetime.fromtimestamp(
                                node.get("taken_at_timestamp", 0), tz=timezone.utc
                            ),
                            "likes": node.get("edge_liked_by", {}).get("count", 0),
                            "comments": node.get("edge_media_to_comment", {}).get("count", 0),
                            "shares": 0,
                            "keywords_found": json.dumps(["coffee"]),
                            "drink_types": "",
                            "sentiment": "neutral",
                            "sentiment_score": 0.0,
                            "hour_of_day": datetime.fromtimestamp(
                                node.get("taken_at_timestamp", 0), tz=timezone.utc
                            ).hour,
                            "day_of_week": datetime.fromtimestamp(
                                node.get("taken_at_timestamp", 0), tz=timezone.utc
                            ).weekday(),
                            "engagement_score": node.get("edge_liked_by", {}).get("count", 0),
                            "estimated_age_group": None
                        })

        except Exception as e:
            logger.error(f"Alt parsing error: {e}")

        return posts

    def _get_mock_data(self) -> List[Dict]:
        """Generate mock Instagram data for testing."""
        import random

        mock_texts = [
            "☕ Morning latte ritual. Nothing starts my day better than a perfectly crafted latte with beautiful art. #coffee #latte #morningvibes",
            "This cold brew is everything! Smooth, rich, and the perfect afternoon pick-me-up. ❄️☕ #coldbrew #icedcoffee #coffeelover",
            "Barista life means making art one espresso shot at a time. Today's latte art came out perfectly! 🌿☕ #baristalife #latteart #espresso",
            "Found the coziest coffee shop in the neighborhood. Their flat white is to die for. ☕✨ #coffeeshop #flatwhite #specialtycoffee",
            "Sunday morning ritual: freshly ground beans, pour over coffee, and a good book. ☕📚 #pourover #morningcoffee #coffeetime",
            "Cappuccino art progress: from blobs to actual recognizable shapes! Day 47 of practicing. ☕🎨 #cappuccino #latteart #coffeegram",
            "That feeling when the iced americano hits just right on a hot summer day. 🧊☕ #icedcoffee #americano #summercoffee",
            "Oat milk latte is the future. I'll never go back to regular milk. ☕🌱 #latte #oatmilk #coffeelovers",
            "Double shot espresso = double the productivity. Monday motivation activated! ☕💪 #espresso #mondaymotivation #coffee",
            "The new specialty coffee shop downtown is incredible. Their single-origin pour overs are mind-blowing. ☕🤯 #specialtycoffee #pourover",
            "Mocha latte appreciation post. Chocolate + coffee = perfection. ☕🍫 #mocha #latte #coffeelife",
            "Home espresso setup is finally complete! Can't wait to experiment with different beans. ☕🏠 #espresso #homecafe #coffeelover",
            "Cold brew season is my favorite season. Stocked up and ready for all of summer! ❄️☕ #coldbrew #summer #coffeetime",
            "Cortado: the underrated hero of the coffee world. Perfect espresso-to-milk ratio. ☕ #cortado #espresso #specialtycoffee",
            "Coffee shop vibes on a rainy afternoon. Macchiato and good thoughts. ☕🌧️ #macchiato #coffeeshop #rainydays",
            "Just roasted my first batch of coffee beans at home. The aroma is incredible! 🔥☕ #roasting #coffeebeans #homecafe",
            "Iced latte with vanilla syrup is my guilty pleasure. ☕🍦 #icedcoffee #latte #coffeelover",
            "Flat white vs latte: today we settle this debate. My vote: flat white all the way. ☕ #flatwhite #latte #coffee",
            "The perfect espresso shot: golden crema, rich body, complex flavor. This is it. ☕✨ #espresso #baristalife",
            "Coffee subscription box arrived! 3 new origins to explore this month. ☕📦 #coffee #specialtycoffee",
        ]

        age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
        drink_types = [
            "latte", "espresso", "cappuccino", "cold brew", "iced coffee",
            "flat white", "americano", "mocha", "macchiato", "cortado"
        ]
        sentiments = ["positive", "neutral", "negative"]
        sentiment_scores = {
            "positive": random.uniform(0.5, 1.0),
            "neutral": random.uniform(-0.1, 0.1),
            "negative": random.uniform(-0.7, -0.2)
        }

        posts = []
        for i in range(45):
            hour = random.choices(
                list(range(6, 23)),
                weights=[1, 2, 3, 4, 6, 5, 3, 3, 4, 5, 4, 3, 3, 3, 2, 2, 1],
                k=1
            )[0]
            day = random.randint(0, 6)
            sentiment = random.choices(
                sentiments, weights=[0.65, 0.25, 0.1], k=1
            )[0]

            posts.append({
                "source": "instagram",
                "post_id": f"insta_mock_{i}",
                "platform_url": f"https://www.instagram.com/p/mock_{i}/",
                "author": f"ig_mock_user_{i}",
                "text": random.choice(mock_texts),
                "timestamp": datetime.now(timezone.utc).replace(
                    hour=hour, minute=random.randint(0, 59)
                ),
                "likes": random.randint(10, 5000),
                "comments": random.randint(0, 500),
                "shares": random.randint(0, 100),
                "keywords_found": json.dumps(["coffee"]),
                "drink_types": json.dumps([random.choice(drink_types)]),
                "sentiment": sentiment,
                "sentiment_score": sentiment_scores[sentiment],
                "hour_of_day": hour,
                "day_of_week": day,
                "engagement_score": random.randint(10, 5000),
                "estimated_age_group": random.choice(age_groups)
            })

        logger.info(f"Generated {len(posts)} mock Instagram posts.")
        return posts
