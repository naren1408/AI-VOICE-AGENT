"""
ElectroMart India — Product Recommendation Engine
Deterministic, explainable recommendation logic reading directly from data/products.csv.
The LLM never hallucinates or invents products; this engine is the single source of truth.
"""
import os
import re
from typing import List, Dict, Optional, Tuple
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PRODUCTS_CSV = os.path.join(DATA_DIR, "products.csv")


def load_products_df() -> pd.DataFrame:
    """Load products catalog as a DataFrame."""
    if os.path.exists(PRODUCTS_CSV):
        return pd.read_csv(PRODUCTS_CSV)
    return pd.DataFrame()


def parse_budget_from_text(text: str) -> Optional[int]:
    """
    Extract budget amount in INR from natural language text.
    Handles '70,000', '70000', '70k', '1 lakh', '35k', '₹50,000', etc.
    """
    t = text.lower()

    # Match Lakhs: e.g. "1 lakh", "1.5 lakh"
    m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs)", t)
    if m_lakh:
        return int(float(m_lakh.group(1)) * 100000)

    # Match 'k': e.g. "70k", "35k"
    m_k = re.search(r"(\d+)\s*k\b", t)
    if m_k:
        return int(m_k.group(1)) * 1000

    # Match currency symbol or standalone numbers: "₹70,000", "under 70000", "70,000"
    m_curr = re.search(r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+|\d{4,7})", t)
    if m_curr:
        raw_num = m_curr.group(1).replace(",", "")
        val = int(raw_num)
        # Avoid treating RAM (e.g. 16, 32) or years (2026) as budget
        if val > 1500 and val != 2026:
            return val

    return None


def detect_category(text: str) -> Optional[str]:
    """Detect product category from query text."""
    t = text.lower()
    if any(w in t for w in ["laptop", "notebook", "macbook", "computer", "pc", "voltbook", "codemaster", "devforge"]):
        return "Laptops"
    if any(w in t for w in ["phone", "smartphone", "mobile", "android", "iphone", "5g phone"]):
        return "Smartphones"
    if any(w in t for w in ["tablet", "tab", "ipad", "slate", "stylus pad"]):
        return "Tablets"
    if any(w in t for w in ["headphone", "headset", "earbuds", "tws", "charger", "keyboard", "mouse", "accessory", "accessories"]):
        return "Accessories"
    return None


def recommend_products(user_query: str, max_results: int = 3) -> List[Dict]:
    """
    Recommend up to max_results products based on category, budget, and use case.
    Returns list of dicts with product details and a tailored recommendation reason.
    """
    df = load_products_df()
    if df.empty:
        return []

    t = user_query.lower()
    budget = parse_budget_from_text(user_query)
    category = detect_category(user_query)

    filtered = df.copy()
    if category:
        filtered = filtered[filtered["category"].str.lower() == category.lower()]

    # Persona / Use-case keywords
    is_coding = any(w in t for w in ["program", "code", "coding", "developer", "software", "python", "java", "docker", "web dev", "compiler"])
    is_student = any(w in t for w in ["student", "college", "school", "study", "class", "assignments", "budget"])
    is_gaming = any(w in t for w in ["game", "gaming", "rtx", "gpu", "fps", "graphics card", "steam"])
    is_photo = any(w in t for w in ["photo", "camera", "reel", "video", "ois", "vlog", "sony sensor"])
    is_battery = any(w in t for w in ["battery", "backup", "mah", "long lasting", "travel"])
    is_office = any(w in t for w in ["office", "work", "business", "multitask", "excel", "corporate"])

    # Score each product
    scores = []
    for idx, row in filtered.iterrows():
        p_score = 0
        p_price = int(row["price_inr"])
        p_use = str(row["best_use_case"]).lower()
        p_desc = str(row["description"]).lower()
        p_proc = str(row["processor"]).lower()
        p_ram = str(row["ram"]).lower()

        # Budget adherence
        if budget:
            if p_price <= budget:
                p_score += 40
                # Give slight preference to products close to budget (better specs for budget)
                ratio = p_price / budget
                p_score += int(ratio * 20)
            else:
                # Slight penalty if over budget
                p_score -= 30
        else:
            p_score += 20

        # Use-case matching
        if is_coding and ("program" in p_use or "developer" in p_desc or "i5" in p_proc or "ryzen 7" in p_proc or "16gb" in p_ram):
            p_score += 35
        if is_student and ("student" in p_use or "budget" in p_use or p_price <= 40000):
            p_score += 35
        if is_gaming and ("gaming" in p_use or "rtx" in p_desc or "165hz" in p_desc):
            p_score += 40
        if is_photo and ("photo" in p_use or "camera" in p_desc or "ois" in p_desc):
            p_score += 35
        if is_battery and ("battery" in p_use or "6000mah" in p_desc or "10 hours" in p_desc):
            p_score += 35
        if is_office and ("office" in p_use or "business" in p_use or "ultrabook" in p_desc):
            p_score += 30

        # In-stock bonus
        if row["stock_status"] == "In Stock":
            p_score += 10

        scores.append((idx, p_score))

    # Rank products
    scores.sort(key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, _ in scores[:max_results]]
    top_df = filtered.loc[top_indices]

    results = []
    for _, row in top_df.iterrows():
        # Generate custom reasoning
        reason = f"Excellent fit for {row['best_use_case'].lower()} featuring {row['processor']}, {row['ram']}, and {row['storage']}."
        if budget and int(row["price_inr"]) <= budget:
            reason += f" Comfortably fits your ₹{budget:,} budget at ₹{int(row['price_inr']):,}."
        elif budget:
            reason += f" Slightly above budget at ₹{int(row['price_inr']):,}, but offers superior specifications."

        results.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "brand": row["brand"],
            "category": row["category"],
            "price_inr": int(row["price_inr"]),
            "stock_status": row["stock_status"],
            "processor": row["processor"],
            "ram": row["ram"],
            "storage": row["storage"],
            "display": row["display"],
            "battery": row["battery"],
            "warranty": row["warranty"],
            "best_use_case": row["best_use_case"],
            "reason": reason
        })

    return results


def format_recommendations_for_agent(recs: List[Dict]) -> str:
    """Format recommendation list into concise conversational text for the agent."""
    if not recs:
        return "I could not find exact catalog matches for those criteria. Let me connect you with an in-store specialist."

    lines = []
    for i, r in enumerate(recs, 1):
        lines.append(f"{i}. **{r['product_name']}** (₹{r['price_inr']:,}) — {r['reason']}")
    return "\n".join(lines)
