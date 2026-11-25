"""
ElectroMart India — Lead Qualification Engine
Extracts BANT criteria from conversation text, calculates 0-100 score,
and classifies into HOT (70-100), WARM (40-69), and COLD (0-39).
"""
import re
from typing import Dict, Tuple, Optional
from pydantic import BaseModel, Field

# --- SCORING WEIGHTS (Exact specification from prompt) ---
# Keep in one dictionary for 1-minute live interview explanation
LEAD_SCORING_WEIGHTS = {
    "clear_requirement": 20,   # Customer expressed a clear product need / use case
    "budget_specified": 20,    # Customer specified an explicit budget or price range
    "urgent_timeline": 25,     # Purchase timeline within 30 days (immediate, this week, soon)
    "contact_info": 15,        # Captured phone number or email address
    "strong_intent": 20        # Expressed strong purchase intent (book visit, buy, store demo)
}

HOT_THRESHOLD = 70
WARM_THRESHOLD = 40

TIMELINE_30_DAYS_KEYWORDS = [
    "today", "tomorrow", "immediate", "asap", "urgent", "this week", "next week",
    "within 7 days", "within 15 days", "this month", "within 30 days", "soon", "now"
]

PURCHASE_INTENT_KEYWORDS = [
    "visit", "book", "demo", "buy", "purchase", "order", "call me", "appointment",
    "finalize", "ready", "interested in buying", "store", "callback", "kharidna"
]


class ExtractedLead(BaseModel):
    """Pydantic model for structured lead data validation."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    interested_category: Optional[str] = None
    budget: Optional[str] = None
    requirement: Optional[str] = None
    purchase_timeline: Optional[str] = None
    purchase_intent: Optional[str] = "Exploring"
    score: int = Field(default=0, ge=0, le=100)
    status: str = Field(default="COLD")
    score_breakdown: Dict[str, int] = Field(default_factory=dict)


def extract_lead_from_conversation(text: str) -> ExtractedLead:
    """Extract lead attributes from multi-turn dialogue text using robust pattern matching."""
    t_lower = text.lower()

    # 1. Contact Info
    email_match = re.search(r"[\w.\-]+@[\w.\-]+\.\w{2,}", text)
    email = email_match.group(0).lower() if email_match else None

    phone_match = re.search(r"(\+?91[\-\s]?)?[6-9]\d{9}|(\+?\d[\d\s\-]{8,}\d)", text)
    phone = phone_match.group(0).strip() if phone_match else None

    # Name: "My name is X", "I am X", "This is X"
    name = None
    name_match = re.search(r"(?:my name is|this is|i'm|call me|i am)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", text, re.IGNORECASE)
    if name_match:
        cand = name_match.group(1).title()
        # Filter out common false names
        if cand.lower() not in ["silent", "looking", "interested", "from", "searching", "here", "ready", "calling"]:
            name = cand

    # City: Check for major metro cities
    city = None
    for c in ["mumbai", "bengaluru", "delhi", "hyderabad", "pune", "ahmedabad", "kolkata", "chennai", "noida", "gurugram", "chandigarh", "jaipur"]:
        if re.search(r"\b" + c + r"\b", t_lower):
            city = c.title()
            break

    # 2. Category — Prioritize user's latest query or explicit intent over system greetings
    category = None
    # If the text has user messages, isolate user parts to avoid matching agent greeting words
    user_parts = re.findall(r"(?:USER:|user:)(.*?)(?:AGENT:|assistant:|$)", text, re.DOTALL | re.IGNORECASE)
    eval_text = " ".join(user_parts).lower() if user_parts else t_lower

    if any(w in eval_text for w in ["tablet", "tab", "ipad", "zenith pad", "tabstudy"]):
        category = "Tablets"
    elif any(w in eval_text for w in ["phone", "smartphone", "mobile", "android", "iphone", "campro", "velocity", "powermax"]):
        category = "Smartphones"
    elif any(w in eval_text for w in ["laptop", "notebook", "pc", "macbook", "codemaster", "voltbook", "devforge", "cyberpulse"]):
        category = "Laptops"
    elif any(w in eval_text for w in ["keyboard", "mouse", "headphone", "headset", "charger", "tws", "earbuds", "accessory"]):
        category = "Accessories"

    # 3. Budget
    budget = None
    from backend.product_recommendation import parse_budget_from_text
    parsed_b = parse_budget_from_text(text)
    if parsed_b:
        budget = f"₹{parsed_b:,}"

    # 4. Requirement
    requirement = None
    req_match = re.search(r"(?:for|need|looking for|want|use for)\s+([a-zA-Z0-9\s,\-]{5,60})(?:\.|$|,)", text, re.IGNORECASE)
    if req_match:
        requirement = req_match.group(0).strip()
    elif category:
        requirement = f"Interested in {category}"

    # 5. Purchase Timeline
    timeline = None
    for kw in TIMELINE_30_DAYS_KEYWORDS:
        if kw in t_lower:
            timeline = kw.title()
            break

    # 6. Purchase Intent
    intent = "Exploring"
    if any(kw in t_lower for kw in PURCHASE_INTENT_KEYWORDS):
        intent = "High (Visit / Booking requested)"

    # Compute Score & Breakdown
    score = 0
    breakdown = {}

    if requirement and len(requirement) > 5:
        score += LEAD_SCORING_WEIGHTS["clear_requirement"]
        breakdown["clear_requirement"] = LEAD_SCORING_WEIGHTS["clear_requirement"]

    if budget:
        score += LEAD_SCORING_WEIGHTS["budget_specified"]
        breakdown["budget_specified"] = LEAD_SCORING_WEIGHTS["budget_specified"]

    if timeline and any(kw in timeline.lower() for kw in TIMELINE_30_DAYS_KEYWORDS):
        score += LEAD_SCORING_WEIGHTS["urgent_timeline"]
        breakdown["urgent_timeline"] = LEAD_SCORING_WEIGHTS["urgent_timeline"]

    if email or phone:
        score += LEAD_SCORING_WEIGHTS["contact_info"]
        breakdown["contact_info"] = LEAD_SCORING_WEIGHTS["contact_info"]

    if intent.startswith("High"):
        score += LEAD_SCORING_WEIGHTS["strong_intent"]
        breakdown["strong_intent"] = LEAD_SCORING_WEIGHTS["strong_intent"]

    score = min(100, max(0, score))
    status = "HOT" if score >= HOT_THRESHOLD else ("WARM" if score >= WARM_THRESHOLD else "COLD")

    return ExtractedLead(
        name=name,
        email=email,
        phone=phone,
        city=city,
        interested_category=category,
        budget=budget,
        requirement=requirement,
        purchase_timeline=timeline,
        purchase_intent=intent,
        score=score,
        status=status,
        score_breakdown=breakdown
    )
