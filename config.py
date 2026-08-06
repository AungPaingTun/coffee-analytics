"""
Application configuration for Coffee Analytics Platform.
Loads settings from environment variables and .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

# === Database Configuration ===
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'coffee_analytics.db'}")

# === Scraping Configuration ===
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "coffee_analytics/1.0")

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

# === Scraper Settings ===
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
MAX_POSTS_PER_SOURCE = int(os.getenv("MAX_POSTS_PER_SOURCE", "100"))

# === Coffee Keywords ===
COFFEE_KEYWORDS = [
    "coffee", "latte", "espresso", "cappuccino", "mocha",
    "cold brew", "iced coffee", "americano", "flat white",
    "macchiato", "cortado", "cold brew coffee", "nitro coffee",
    "frappuccino", "pour over", "drip coffee", "coffee shop",
    "coffee beans", "specialty coffee", "coffee lover"
]

# === Sentiment Configuration ===
POSITIVE_WORDS = [
    "amazing", "best", "love", "perfect", "great", "excellent",
    "delicious", "wonderful", "fantastic", "favorite", "obsessed",
    "incredible", "superb", "awesome", "lovely", "enjoyed",
    "recommend", "heaven", "bliss", "perfect"
]

NEGATIVE_WORDS = [
    "bad", "terrible", "worst", "hate", "disgusting", "bitter",
    "burnt", "awful", "poor", "bland", "disappointing", "overpriced",
    "cold", "stale", "weak", "watery", "gross"
]

# === Dashboard Settings ===
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
