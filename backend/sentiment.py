import re
from typing import Tuple

# Keywords for rule-based sentiment scoring (-1.0 to 1.0)
POSITIVE_KEYWORDS = [
    "great", "excellent", "love", "awesome", "perfect", "good", "helpful",
    "interested", "impressive", "thanks", "thank you", "yes", "definitely",
    "badiya", "shandar", "sahi", "achha", "dhanyawad"
]

NEGATIVE_KEYWORDS = [
    "terrible", "bad", "expensive", "useless", "hate", "slow", "annoyed",
    "frustrated", "scam", "waste", "poor", "never", "cancel",
    "bekar", "kharab", "mehnga", "nahi"
]

ESCALATION_THRESHOLD = -0.6


def analyze_sentiment(text: str) -> Tuple[str, float]:
    """Analyze sentiment per conversation turn returning (label, score between -1 and 1)."""
    text_lower = text.lower()
    score = 0.0

    # Count positive and negative keyword occurrences using word boundaries to avoid false positives
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", text_lower))
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", text_lower))

    # Check stand-alone negative 'no'
    if re.search(r"\bno\b", text_lower) and not re.search(r"\bno problem\b|\bno worries\b", text_lower):
        neg_count += 1

    if pos_count > neg_count:
        score = min(1.0, 0.35 + (pos_count * 0.2))
        return "positive", round(score, 2)
    elif neg_count > pos_count:
        score = max(-1.0, -0.35 - (neg_count * 0.25))
        return "negative", round(score, 2)
    else:
        return "neutral", 0.0


def requires_human_escalation(sentiment_score: float) -> bool:
    """Return True if user exhibits strong negative sentiment."""
    return sentiment_score <= ESCALATION_THRESHOLD
