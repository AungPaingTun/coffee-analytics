"""
Drink Type Extractor Module
Identifies coffee drink types mentioned in social media posts.
Uses pattern matching and NLP to extract drink references.
"""

import re
import logging
import json
from typing import List, Dict, Tuple

from config import COFFEE_KEYWORDS

logger = logging.getLogger(__name__)


class DrinkTypeExtractor:
    """
    Extracts coffee drink types from post text using
    pattern matching and contextual analysis.
    """

    # Comprehensive drink type patterns
    DRINK_PATTERNS = {
        "espresso": [
            r"\bespresso\b", r"\bdouble\s+shot\b", r"\bshot\s+of\s+(?:coffee|espresso)\b",
            r"\bextra?\s+shot\b"
        ],
        "latte": [
            r"\blatte\b", r"\bmilk\s+coffee\b"
        ],
        "cappuccino": [
            r"\bcappuccino\b", r"\bcap\b"
        ],
        "cold brew": [
            r"\bcold\s+brew\b", r"\bcb\b", r"\bcoldbrew\b"
        ],
        "iced coffee": [
            r"\biced\s+coffee\b", r"\bice\s+coffee\b", r"\bcoffee\s+on\s+ice\b"
        ],
        "iced latte": [
            r"\biced\s+latte\b", r"\bcold\s+latte\b"
        ],
        "americano": [
            r"\bamericano\b", r"\bblack\s+coffee\b", r"\blong\s+black\b"
        ],
        "flat white": [
            r"\bflat\s+white\b", r"\bflatwhite\b"
        ],
        "mocha": [
            r"\bmocha\b", r"\bchocolate\s+coffee\b", r"\bcoco\s+coffee\b"
        ],
        "macchiato": [
            r"\bmacchiato\b", r"\bespresso\s+macchiato\b"
        ],
        "cortado": [
            r"\bcortado\b", r"\bgibraltar\b"
        ],
        "pour over": [
            r"\bpour\s+over\b", r"\bpourover\b", r"\bv60\b", r"\bchemex\b",
            r"\bchemex\b"
        ],
        "french press": [
            r"\bfrench\s+press\b", r"\bplunger\b"
        ],
        "drip coffee": [
            r"\bdrip\s+coffee\b", r"\bfilter\s+coffee\b", r"\bbatch\s+brew\b"
        ],
        "nitro coffee": [
            r"\bnitro\b", r"\bnitrogen\s+coffee\b", r"\bnitro\s+brew\b"
        ],
        "frappuccino": [
            r"\bfrappuccino\b", r"\bfrappe\b", r"\bfrozen\s+coffee\b"
        ],
        "affogato": [
            r"\baffogato\b"
        ],
        "cortado": [
            r"\bcortado\b"
        ],
        "red eye": [
            r"\bred\s+eye\b", r"\bdepth\s+charge\b"
        ],
    }

    # Age-related pattern indicators from bios/text
    AGE_PATTERNS = {
        "18-24": [
            r"\bcollege\b", r"\buniversity\b", r"\bfreshman\b", r"\bsophomore\b",
            r"\bjunior\s+(?:year|at)\b", r"\bsenior\s+(?:year|at)\b", r"\bgen\s+z\b",
            r"\bzoomer\b", r"\btiktok\b", r"\binstagram\b.*\baddict\b",
            r"\bfirst\s+job\b", r"\bintern\b", r"\bgrad\s+student\b"
        ],
        "25-34": [
            r"\bmillennial\b", r"\byoung\s+professional\b", r"\bstartup\b",
            r"\btech\b", r"\bremote\s+work\b", r"\bwork\s+from\s+home\b",
            r"\bmom\s+of\b", r"\bdad\s+of\b", r"\bnew\s+parent\b",
            r"\bhome\s+owner\b", r"\bfirst\s+house\b"
        ],
        "35-44": [
            r"\bsenior\s+manager\b", r"\bdirector\b", r"\bleader\b",
            r"\bparent\s+of\b", r"\bkids?\s+school\b", r"\bmortgage\b",
            r"\bsuburb\b", r"\bmid[- ]career\b"
        ],
        "45-54": [
            r"\bempty\s+nester\b", r"\bretirement\s+planning\b",
            r"\bsenior\s+director\b", r"\bvp\b", r"\bexecutive\b",
            r"\bteen\b", r"\bcollege\s+kid\b"
        ],
        "55+": [
            r"\bretired\b", r"\bretirement\b", r"\bgrandparent\b",
            r"\bgrandchild\b", r"\bgolden\s+years\b", r"\bsenior\b",
            r"\bearly\s+bird\b", r"\broutine\b"
        ]
    }

    def extract_drink_types(self, text: str) -> List[str]:
        """
        Extract all coffee drink types mentioned in the text.
        
        Args:
            text: Post text to analyze.
        
        Returns:
            List of detected drink type strings.
        """
        if not text:
            return []

        text_lower = text.lower()
        found_drinks = set()

        for drink_name, patterns in self.DRINK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    found_drinks.add(drink_name)
                    break

        # If no specific drink found but coffee is mentioned, default to "coffee"
        if not found_drinks:
            for kw in COFFEE_KEYWORDS:
                if kw in text_lower:
                    found_drinks.add("coffee")
                    break

        return sorted(list(found_drinks))

    def estimate_age_group(self, text: str) -> str:
        """
        Estimate user age group based on text content and bio clues.
        
        Args:
            text: Post text or bio text to analyze.
        
        Returns:
            Estimated age group string, or None if indeterminate.
        """
        if not text:
            return None

        text_lower = text.lower()
        scores = {}

        for age_group, patterns in self.AGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
            scores[age_group] = score

        if not scores or max(scores.values()) == 0:
            return None

        # Return the highest scoring age group
        best_group = max(scores, key=scores.get)
        if scores[best_group] > 0:
            return best_group
        return None

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract all coffee-related keywords found in the text.
        
        Args:
            text: Post text to scan.
        
        Returns:
            List of matched coffee keywords.
        """
        if not text:
            return []

        text_lower = text.lower()
        return [kw for kw in COFFEE_KEYWORDS if kw in text_lower]


# Singleton instance
_extractor = None


def get_extractor() -> DrinkTypeExtractor:
    """Get or create the global extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = DrinkTypeExtractor()
    return _extractor


def extract_drink_types(text: str) -> List[str]:
    """Convenience function for drink type extraction."""
    return get_extractor().extract_drink_types(text)


def estimate_age_group(text: str) -> str:
    """Convenience function for age estimation."""
    return get_extractor().estimate_age_group(text)
