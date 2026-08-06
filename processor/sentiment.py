"""
Sentiment Analysis Module
Analyzes text sentiment using VADER and custom coffee-specific rules.
Returns positive/neutral/negative classification with scores.
"""

import logging
import re
from typing import Dict, Tuple

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import POSITIVE_WORDS, NEGATIVE_WORDS

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Multi-layered sentiment analyzer combining VADER with
    domain-specific coffee sentiment rules.
    """

    def __init__(self):
        self._vader = SentimentIntensityAnalyzer()
        self._enhance_vader_lexicon()
        logger.info("Sentiment analyzer initialized.")

    def _enhance_vader_lexicon(self):
        """Add coffee-specific words to VADER's sentiment lexicon."""
        coffee_positive = {
            "delicious": 2.5, "aromatic": 2.0, "smooth": 1.8,
            "perfect": 2.5, "amazing": 2.2, "creamy": 1.5,
            "velvety": 1.8, "rich": 1.5, "bold": 1.0,
            "heavenly": 2.5, "incredible": 2.0, "obsessed": 2.0,
            "favorite": 2.0, "perfectly": 2.2, "beautiful": 1.8,
            "cozy": 1.5, "blissful": 2.0, "ritual": 0.8,
        }
        
        coffee_negative = {
            "burnt": -2.0, "bitter": -1.5, "stale": -2.0,
            "watery": -1.5, "overpriced": -1.5, "disappointing": -1.8,
            "bland": -1.5, "weak": -1.2, "gross": -2.0,
            "terrible": -2.5, "worst": -2.5, "disgusting": -2.5,
        }

        for word, score in coffee_positive.items():
            self._vader.lexicon[word] = score
        
        for word, score in coffee_negative.items():
            self._vader.lexicon[word] = score

    def analyze(self, text: str) -> Dict:
        """
        Analyze the sentiment of a text string.
        
        Args:
            text: The text to analyze.
        
        Returns:
            Dictionary with sentiment classification and scores.
        """
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0
            }

        # Get VADER scores
        vader_scores = self._vader.polarity_scores(text)
        compound = vader_scores["compound"]

        # Apply custom coffee rules
        compound = self._apply_coffee_rules(text, compound)

        # Classify sentiment
        if compound >= 0.05:
            sentiment = "positive"
        elif compound <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Calculate confidence
        confidence = abs(compound)

        return {
            "sentiment": sentiment,
            "score": round(compound, 4),
            "confidence": round(confidence, 4),
            "vader_details": {
                "pos": vader_scores["pos"],
                "neu": vader_scores["neu"],
                "neg": vader_scores["neg"],
            }
        }

    def _apply_coffee_rules(self, text: str, score: float) -> float:
        """Apply domain-specific rules for coffee sentiment."""
        text_lower = text.lower()
        
        # Count domain-specific positive words
        pos_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
        neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)

        # Coffee-specific emoji detection
        emoji_positives = ["☕", "❤️", "😍", "🔥", "✨", "💪", "🌟", "🎉", "👌"]
        emoji_negatives = ["😤", "😠", "👎", "💔"]
        
        pos_emoji_count = sum(1 for emoji in emoji_positives if emoji in text)
        neg_emoji_count = sum(1 for emoji in emoji_negatives if emoji in text)

        # Adjust score based on word and emoji counts
        if pos_count > neg_count:
            score += min(pos_count * 0.05, 0.4)
        elif neg_count > pos_count:
            score -= min(neg_count * 0.08, 0.5)

        if pos_emoji_count > neg_emoji_count:
            score += pos_emoji_count * 0.03
        elif neg_emoji_count > pos_emoji_count:
            score -= neg_emoji_count * 0.05

        # Clamp score to [-1, 1]
        return max(-1.0, min(1.0, score))


# Singleton instance
_sentiment_analyzer = None


def get_analyzer() -> SentimentAnalyzer:
    """Get or create the global sentiment analyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


def analyze_sentiment(text: str) -> Dict:
    """Convenience function for single text sentiment analysis."""
    return get_analyzer().analyze(text)
