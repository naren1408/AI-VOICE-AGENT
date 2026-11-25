"""
TechNova Solutions — Lead Qualification Engine
Scores leads 0-100 and classifies them as Hot / Warm / Cold.
Weights are in one dictionary for easy live-coding demonstration.
"""
import re
from typing import Tuple

# --- SCORING WEIGHTS (Change these live during demo to show the system) ---
SCORING_WEIGHTS = {
    "has_budget":        25,   # Customer mentioned a budget
    "urgent_timeline":   25,   # Buying in < 6 months
    "has_email":         15,   # Email address captured
    "has_phone":         10,   # Phone number captured
    "has_company":       10,   # Company name captured
    "specific_product":  10,   # Mentioned a specific TechNova product
    "requirements_clear": 5,   # Described a specific business requirement
}

HOT_THRESHOLD  = 70
WARM_THRESHOLD = 40

TIMELINE_URGENT_KEYWORDS = [
    "immediate", "asap", "urgent", "now", "this month", "this quarter",
    "next month", "q1", "q2", "q3", "q4", "soon", "quickly", "immediately"
]

PRODUCT_KEYWORDS = {
    "crm": "TechNova CRM Suite",
    "erp": "TechNova ERP Pro",
    "analytics": "TechNova Analytics Hub",
    "enterprise": "TechNova ERP Pro",
    "suite": "Full Suite",
}


def extract_lead_info(text: str) -> dict:
    """Extract structured lead info from raw conversation text using regex."""
    info = {
        "name": None, "email": None, "phone": None,
        "company": None, "requirements": None,
        "budget": None, "timeline": None, "interested_product": None
    }

    # Email
    m = re.search(r"[\w.\-]+@[\w.\-]+\.\w{2,}", text)
    if m:
        info["email"] = m.group(0)

    # Phone (international-friendly)
    m = re.search(r"(\+?\d[\d\s\-]{7,}\d)", text)
    if m:
        info["phone"] = m.group(0).strip()

    # Budget ($, USD, INR, monthly)
    m = re.search(r"(\$[\d,]+|₹[\d,]+|\b\d{3,6}\b.*?(month|year|annual|budget))", text, re.IGNORECASE)
    if m:
        info["budget"] = m.group(0)

    # Timeline
    for kw in TIMELINE_URGENT_KEYWORDS:
        if kw in text.lower():
            info["timeline"] = kw
            break

    # Interested product
    for kw, product in PRODUCT_KEYWORDS.items():
        if kw in text.lower():
            info["interested_product"] = product
            break

    # Name: "my name is X" or "I am X"
    m = re.search(r"(?:my name is|i am|this is|i'm)\s+([A-Za-z]+(?:\s[A-Za-z]+)?)", text, re.IGNORECASE)
    if m:
        info["name"] = m.group(1).title()

    # Company: "from X" or "at X company" or "X company"
    m = re.search(r"(?:from|at|work(?:ing)? at|company(?:\s+is)?)\s+([A-Za-z0-9][\w\s]{1,30})", text, re.IGNORECASE)
    if m:
        info["company"] = m.group(1).strip().title()

    # Requirements: capture purpose/need phrases
    m = re.search(r"(?:need|looking for|want|require|help with)\s+(.{10,80}?)(?:\.|,|$)", text, re.IGNORECASE)
    if m:
        info["requirements"] = m.group(1).strip()

    return info


def score_lead(info: dict) -> Tuple[int, str]:
    """Calculate lead score and return (score, status)."""
    score = 0

    if info.get("budget"):
        score += SCORING_WEIGHTS["has_budget"]

    if info.get("timeline") and any(kw in str(info["timeline"]).lower() for kw in TIMELINE_URGENT_KEYWORDS):
        score += SCORING_WEIGHTS["urgent_timeline"]

    if info.get("email"):
        score += SCORING_WEIGHTS["has_email"]

    if info.get("phone"):
        score += SCORING_WEIGHTS["has_phone"]

    if info.get("company"):
        score += SCORING_WEIGHTS["has_company"]

    if info.get("interested_product"):
        score += SCORING_WEIGHTS["specific_product"]

    if info.get("requirements") and len(str(info["requirements"])) > 10:
        score += SCORING_WEIGHTS["requirements_clear"]

    score = min(100, max(0, score))
    status = "Hot" if score >= HOT_THRESHOLD else ("Warm" if score >= WARM_THRESHOLD else "Cold")
    return score, status
