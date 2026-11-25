"""
TechNova Solutions — Sentiment Analysis
Keyword-based sentiment scoring that works with no external API.
"""
from typing import Tuple

# Positive keywords (English + common Hindi transliterations)
POSITIVE_WORDS = [
    "great", "excellent", "love", "perfect", "wonderful", "amazing", "fantastic",
    "interested", "yes", "definitely", "good", "helpful", "impressed", "happy",
    "excited", "awesome", "brilliant", "superb", "nice", "glad", "thank",
]
# Negative keywords
NEGATIVE_WORDS = [
    "terrible", "awful", "bad", "hate", "useless", "expensive", "disappointing",
    "no", "never", "poor", "slow", "broken", "worst", "annoying", "frustrating",
    "complicated", "confusing", "overpriced", "waste", "difficult", "problem",
]

ESCALATE_THRESHOLD = -0.5  # Score below this triggers escalation suggestion


def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyze sentiment of a text string.
    Returns (label, score) where label is 'Positive'/'Neutral'/'Negative'
    and score is -1.0 to 1.0.
    """
    words = text.lower().split()
    pos = sum(1 for w in words if any(p in w for p in POSITIVE_WORDS))
    neg = sum(1 for w in words if any(n in w for n in NEGATIVE_WORDS))

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
