"""
ElectroMart India — Customer Sentiment Analysis
Evaluates per-turn customer sentiment score (-1.0 to 1.0) and detects supervisor escalation flags.
Uses word boundaries to eliminate false-negative triggers.
"""
import re
from typing import Tuple

POSITIVE_KEYWORDS = [
    "great", "excellent", "love", "awesome", "perfect", "good", "helpful",
    "interested", "impressive", "thanks", "thank you", "yes", "definitely",
    "nice", "superb", "brilliant", "wonderful",
    # Telugu positive words
    "baagundi", "manchidi", "dhanyavadalu", "avunu", "baga",
    # Kannada positive words
    "chennagide", "dhanyavada", "houdu", "olleyadu", "uttam"
]

NEGATIVE_KEYWORDS = [
    "terrible", "awful", "bad", "expensive", "useless", "hate", "slow", "annoyed",
    "frustrated", "scam", "waste", "poor", "never", "cancel", "horrible",
    "overpriced",
    # Telugu negative words
    "baledu", "vaddu", "ekkuva", "kharidu", "dhandaga", "ledu",
    # Kannada negative words
    "chennagilla", "beda", "kharabu", "tumba jasti", "illa"
]

ESCALATION_THRESHOLD = -0.55


def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyze sentiment of a message turn.
    Returns (label, score) where label is 'positive', 'neutral', or 'negative'
    and score is between -1.0 and 1.0.
    """
    t_lower = text.lower()

    # Use regex word boundaries (\b) so 'no' inside 'electronics' or 'innovative' is never triggered
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", t_lower))
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", t_lower))

    # Stand-alone negative 'no'
    if re.search(r"\bno\b", t_lower) and not re.search(r"\bno problem\b|\bno worries\b", t_lower):
        neg_count += 1

    if pos_count > neg_count:
        score = min(1.0, 0.35 + (pos_count * 0.2))
        return "positive", round(score, 2)
    elif neg_count > pos_count:
        score = max(-1.0, -0.35 - (neg_count * 0.25))
        return "negative", round(score, 2)
    else:
        return "neutral", 0.0


def should_escalate(sentiment_score: float) -> bool:
    """Return True if customer sentiment is strongly negative, recommending human follow-up."""
    return sentiment_score <= ESCALATION_THRESHOLD
