"""
TechNova Solutions — Sentiment Analysis
Keyword-based sentiment scoring that works with no external API.
"""
import re
from typing import Tuple

# Positive keywords (English + common Hindi transliterations)
POSITIVE_WORDS = [
    "great", "excellent", "love", "perfect", "wonderful", "amazing", "fantastic",
    "interested", "yes", "definitely", "good", "helpful", "impressed", "happy",
    "excited", "awesome", "brilliant", "superb", "nice", "glad", "thanks", "thank",
]
# Negative keywords
NEGATIVE_WORDS = [
    "terrible", "awful", "bad", "hate", "useless", "expensive", "disappointing",
    "never", "poor", "slow", "broken", "worst", "annoying", "frustrating",
    "complicated", "confusing", "overpriced", "waste", "difficult", "problem",
    "horrible", "unhappy", "angry", "scam"
]

ESCALATE_THRESHOLD = -0.5  # Score below this triggers escalation suggestion


def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyze sentiment of a text string using whole-word matching.
    Returns (label, score) where label is 'Positive'/'Neutral'/'Negative'
    and score is -1.0 to 1.0.
    """
    text_lower = text.lower()
    
    # Use word boundary matching to avoid false positives (e.g. 'no' inside 'technova' or 'know')
    pos = sum(1 for p in POSITIVE_WORDS if re.search(r"\b" + re.escape(p) + r"\b", text_lower))
    neg = sum(1 for n in NEGATIVE_WORDS if re.search(r"\b" + re.escape(n) + r"\b", text_lower))

    # Explicit check for stand-alone 'no' without negation context
    if re.search(r"\bno\b", text_lower) and not re.search(r"\bno problem\b|\bno worries\b", text_lower):
        neg += 1

    if pos > neg:
        score = min(1.0, 0.3 + pos * 0.2)
        return "Positive", round(score, 2)
    elif neg > pos:
        score = max(-1.0, -0.3 - neg * 0.25)
        return "Negative", round(score, 2)
    return "Neutral", 0.0


def should_escalate(score: float) -> bool:
    """Return True when customer frustration is very high."""
    return score <= ESCALATE_THRESHOLD
