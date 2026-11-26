"""
ElectroMart India — AI Sales Voice Agent Orchestrator
Coordinates RAG context retrieval, catalog product recommendations, OpenAI LLM reasoning
(with comprehensive rule-based Demo Mode fallback), BANT lead scoring, sentiment tracking, and booking.
"""
import os
import re
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

from backend.config import (
    COMPANY_NAME, AGENT_NAME, OPENAI_MODEL_CHAT, OPENAI_BASE_URL,
    MAX_HISTORY_TURNS, AGENT_ROLE_DESCRIPTION
)
from backend.rag import rag_engine
from backend.product_recommendation import (
    recommend_products, format_recommendations_for_agent,
    parse_budget_from_text, detect_category
)
from backend.lead_qualification import extract_lead_from_conversation, extract_customer_name, ExtractedLead
from backend.sentiment import analyze_sentiment, should_escalate
from backend.appointment import parse_natural_datetime, book_appointment_in_db, generate_ics_content
from database.db import SessionLocal, init_db
from database.models import Customer, Lead, Call, Message, RecommendedProduct

load_dotenv()

# System Prompt
ELECTROMART_SYSTEM_PROMPT = f"""
{AGENT_ROLE_DESCRIPTION}

GUIDELINES FOR CONVERSATION:
1. Greet the customer warmly and politely in English, Telugu, or Kannada (match customer language).
2. Understand what they are looking for (laptops, smartphones, tablets, or accessories).
3. Ask about their budget and intended use (e.g. programming, gaming, students, office, photography).
4. Recommend products ONLY from the provided CATALOG RECOMMENDATIONS context. Do not invent products or prices.
5. Explain clearly why each recommended product suits their needs.
6. Answer questions about pricing, warranty, delivery, GST, and return policies using the KNOWLEDGE BASE context.
7. Offer to arrange a showroom visit or consultation demo.
8. Keep answers concise, consultative, and professional (under 3-4 sentences per turn).
"""

# Realistic Demo Mode response bank for offline testing
DEMO_REPLIES = {
    "greeting": f"Hello! Welcome to {COMPANY_NAME}. I'm {AGENT_NAME}, your AI electronics sales advisor. Are you looking for laptops, smartphones, tablets, or accessories today?",
    "programming_laptop": (
        "Based on your requirements for programming and multitasking, I recommend three great options:\n"
        "1. **CodeMaster Pro 15** (₹64,999) — 13th Gen Intel Core i5 H-series, 16GB DDR5 RAM, 2K display.\n"
        "2. **ZenithBook Air 15** (₹48,999) — AMD Ryzen 5, 16GB RAM, budget-friendly for daily coding.\n"
        "3. **DevForge Extreme 16** (₹79,999) — AMD Ryzen 7 with dedicated RTX 3050 GPU for heavy Docker & ML."
    ),
    "which_is_best": (
        "Based on your budget and programming requirements, I highly recommend the **CodeMaster Pro 15** (₹64,999). "
        "Its high-performance Intel 13th Gen H-series processor and 16GB DDR5 memory handle multiple IDEs, "
        "browser tabs, and local servers effortlessly without lag."
    ),
    "student_laptop": (
        "For students, our top choice is the **VoltBook Student 14** at ₹34,999! "
        "It features an Intel Core i3 12th Gen processor, 8GB RAM, and 8 hours of battery life. "
        "Plus, our Student Tech Pass offer gives you an additional ₹2,500 instant discount with your college ID."
    ),
    "gaming_laptop": (
        "For gaming under ₹1,00,000, the **CyberPulse G15** (₹94,999) is our powerhouse performer! "
        "It features an AMD Ryzen 7 7840HS, 16GB DDR5, and NVIDIA RTX 4060 8GB GPU with a fluid 165Hz QHD panel."
    ),
    "camera_phone": (
        "For photography and short video reels, I recommend the **Zenith CamPro 5G** (₹34,999). "
        "It comes equipped with triple 50MP Sony sensors with Optical Image Stabilization (OIS) and 67W fast charging."
    ),
    "battery_phone": (
        "If battery life is your priority, the **Volt PowerMax 5G** (₹13,999) is unmatched. "
        "It comes with a monster 6000mAh battery that delivers up to 2.5 days of continuous usage on a single charge."
    ),
    "flagship_phone": (
        "Our flagship recommendation is the **Aura Flagship X** (₹64,999) with Snapdragon 8 Gen 3, "
        "titanium alloy body, IP68 water resistance, and 100x zoom periscope telephoto camera."
    ),
    "tablets": (
        "We have three fantastic tablets: **TabStudy 10.1** (₹14,999) for students and e-learning, "
        "**NovaPad Air 11** (₹24,999) with 120Hz display, and the **Zenith Pad Creator 12** (₹38,999) "
        "which includes an active magnetic pressure stylus for digital sketching."
    ),
    "accessories": (
        "Our popular workspace accessories include the **MechKeys RGB Wireless Keyboard** (₹3,999), "
        "**PrecisionGlide Ergonomic Mouse** (₹1,999), **VoltCharge 100W GaN Charger** (₹3,499), "
        "and **Aura SoundBeats ANC Headphones** (₹4,999)."
    ),
    "store_visit": (
        "Certainly! I would be delighted to schedule a hands-on showroom appointment for you to test this in person. "
        "What date and time would be convenient for your visit (e.g. tomorrow at 4:00 PM), and which city showroom would you like to visit?"
    ),
    "store_hours": (
        "ElectroMart showrooms are open Monday through Sunday from 10:00 AM to 08:30 PM. "
        "We have flagship experience centres in Mumbai, Bengaluru, New Delhi, Hyderabad, Pune, Ahmedabad, Kolkata, and Chennai."
    ),
    "warranty_policy": (
        "All our electronics include an official brand warranty ranging from 1 to 3 years. "
        "We also offer a 7-day doorstep replacement guarantee for any transit or manufacturing defect, plus optional Extended Care."
    ),
    "delivery_policy": (
        "We provide express 24 to 48-hour delivery across metro cities with free open-box inspection for orders above ₹20,000. "
        "Standard delivery for other locations takes 3 to 5 business days with live GPS tracking."
    ),
    "payment_emi": (
        "We accept UPI, Credit/Debit cards, Net Banking, and Cash on Delivery up to ₹15,000. "
        "We also offer 0% No-Cost EMI for 3, 6, 9, and 12 months with leading banks on orders above ₹20,000."
    ),
    "gst_invoice": (
        "Yes! We provide full GST business tax invoices for input tax credit. "
        "Simply share your company name and 15-digit GSTIN during consultation or checkout."
    ),
    "offers": (
        "We have great offers running right now! Including 0% No-Cost EMI for up to 12 months, "
        "up to ₹5,000 extra exchange bonus on trading old devices, and a flat ₹2,500 Student Tech Pass discount with student ID."
    ),
    "comparison": (
        "Comparing CodeMaster Pro 15 (₹64,999) and DevForge Extreme 16 (₹79,999): "
        "CodeMaster Pro has an Intel i5 13500H with Iris Xe graphics, ideal for software and web development. "
        "DevForge Extreme adds a dedicated NVIDIA RTX 3050 GPU and 1TB SSD, making it superior for Docker, ML, and Android emulators."
    ),
    "telugu_greeting": (
        "నమస్కారం! ఎలక్ట్రోమార్ట్ ఇండియాకు స్వాగతం. నేను అన్య, మీ AI ఎలక్ట్రానిక్స్ సేల్స్ అసిస్టెంట్. "
        "మీరు లాప్‌టాప్‌లు, స్మార్ట్‌ఫోన్‌లు, టాబ్లెట్‌లు లేదా యాక్సెసరీస్ కోసం చూస్తున్నారా?"
    ),
    "telugu_laptop": (
        "నమస్కారం! కోడింగ్ మరియు ఆఫీస్ పనుల కోసం ZenithBook Air 15 (₹48,999) మరియు CodeMaster Pro 15 (₹64,999) "
        "అత్యుత్తమ ఎంపికలు. వీటిలో 16GB RAM మరియు శక్తివంతమైన ప్రాసెసర్ లభిస్తాయి. మీరు మా షోరూమ్‌లో ప్రత్యక్ష డెమో చూడాలనుకుంటున్నారా?"
    ),
    "telugu_phone": (
        "నమస్కారం! గేమింగ్ మరియు కెమెరా కోసం Pulse Velocity 5G (₹16,999) మరియు Zenith CamPro 5G (₹34,999) "
        "అద్భుతమైన స్మార్ట్‌ఫోన్‌లు. మీరు హైదరాబాద్ లేదా బెంగళూరు షోరూమ్ విజిట్ బుక్ చేయాలనుకుంటున్నారా?"
    ),
    "kannada_greeting": (
        "ನಮಸ್ಕಾರ! ಎಲೆಕ್ಟ್ರೋಮಾರ್ಟ್ ಇಂಡಿಯಾಗೆ ಸುಸ್ವಾಗತ. ನಾನು ಅನ್ಯಾ, ನಿಮ್ಮ AI ಎಲೆಕ್ಟ್ರಾನಿಕ್ಸ್ ಮಾರಾಟ ಸಲಹೆಗಾರ್ತಿ. "
        "ನೀವು ಲ್ಯಾಪ್‌ಟಾಪ್, ಸ್ಮಾರ್ಟ್‌ಫೋನ್, ಟ್ಯಾಬ್ಲೆಟ್ ಅಥವಾ ಆಕ್ಸೆಸರೀಸ್‌ಗಳಿಗಾಗಿ ಹುಡುಕುತ್ತಿದ್ದೀರಾ?"
    ),
    "kannada_laptop": (
        "ನಮಸ್ಕಾರ! ಕೋಡಿಂಗ್ ಮತ್ತು ಆಫೀಸ್ ಕೆಲಸಕ್ಕಾಗಿ ZenithBook Air 15 (₹48,999) ಮತ್ತು CodeMaster Pro 15 (₹64,999) "
        "ಉತ್ತಮ ಆಯ್ಕೆಗಳಾಗಿವೆ. ಇವುಗಳಲ್ಲಿ 16GB RAM ಮತ್ತು ವೇಗದ ಪ್ರೊಸೆಸರ್ ಲಭ್ಯವಿದೆ. ನೀವು ನಮ್ಮ ಶೋರೂಂನಲ್ಲಿ ಲೈವ್ ಡೆಮೊ ನೋಡಲು ಬಯಸುವಿರಾ?"
    ),
    "kannada_phone": (
        "ನಮಸ್ಕಾರ! ಗೇಮಿಂಗ್ ಮತ್ತು ದೈನಂದಿನ ಬಳಕೆಗಾಗಿ Pulse Velocity 5G (₹16,999) ಹಾಗೂ Volt PowerMax 5G (₹13,999) "
        "ಅತ್ಯುತ್ತಮ ಸ್ಮಾರ್ಟ್‌ಫೋನ್‌ಗಳಾಗಿವೆ. ನೀವು ನಮ್ಮ ಬೆಂಗಳೂರು ಶೋರೂಂ ಭೇಟಿ ಬುಕ್ ಮಾಡಲು ಬಯಸುವಿರಾ?"
    )
}


def get_ai_client():
    """Return OpenAI client if OPENAI_API_KEY is present in environment, else None."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        base_url = os.getenv("OPENAI_BASE_URL", None)
        return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    except Exception as e:
        print(f"OpenAI client init notice: {e}")
        return None


# Backward-compatible alias
get_gemini_client = get_ai_client


def is_demo_mode() -> bool:
    """True when no OpenAI API key is configured."""
    return get_ai_client() is None


def _clean_rag_chunk_for_speech(chunk: str) -> str:
    """Clean RAG chunk formatting for clean conversational reply."""
    clean = re.sub(r"\[.*?\.txt\]", "", chunk)
    clean = re.sub(r"#{1,6}\s*", "", clean)
    clean = clean.replace("**", "").replace("- ", "").strip()
    
    # If the chunk has FAQ structure "Q: ... Answer: ...", strip out the prompt artifacts and take the answer
    if "Answer:" in clean:
        clean = clean.split("Answer:", 1)[1].strip()
    elif "answer:" in clean:
        clean = clean.split("answer:", 1)[1].strip()

    # Return first 2 concise sentences
    sentences = [s.strip() for s in clean.split(".") if s.strip()]
    if sentences:
        return ". ".join(sentences[:2]) + "."
    return clean[:200]


def _generate_demo_reply(user_input: str, recs: List[Dict], context: str) -> str:
    """Generate realistic rule-based reply matching ElectroMart scenarios."""
    t = user_input.lower()

    # --- 0. Broad Catalog & Availability Inquiries ---
    # E.g. "can you display the items that are available on this website", "what products are available"
    if any(p in t for p in ["display the items", "available on this website", "items that are available", "what all products", "what products do you have", "show all products", "browse catalog", "full catalog", "what items are present", "what all do you sell"]):
        return (
            f"Welcome to {COMPANY_NAME}! We offer 25 top-rated electronics across 4 core categories:\n\n"
            "1. 💻 **Laptops (8 Models)** — Student laptops from ₹24,999 (VoltBook, SlimLite), Coding & Office work (CodeMaster Pro ₹64,999, ZenithBook Air ₹48,999), and High-Performance RTX Gaming (CyberPulse G15 ₹94,999, DevForge Extreme ₹79,999).\n"
            "2. 📱 **Smartphones (7 Models)** — 6000mAh monster battery (Volt PowerMax ₹13,999), 50MP Sony OIS Camera (Zenith CamPro ₹34,999), and Flagships (Aura Flagship X ₹64,999, Titan Fold Z ₹1,24,999).\n"
            "3. 📲 **Tablets (5 Models)** — E-learning & Students (TabStudy ₹14,999), 120Hz Media (NovaPad Air ₹24,999), and Stylus Creator pads (Zenith Pad Creator 12 ₹38,999).\n"
            "4. 🎧 **Accessories (5 Models)** — Mechanical keyboards (MechKeys ₹3,999), ergonomic mice (₹1,999), 100W GaN fast chargers (₹3,499), and ANC headphones (₹4,999).\n\n"
            "You can explore and filter all 25 products with live price filters in the **'Products, Leads & Appointments'** tab above! Which category would you like to explore?"
        )

    # --- 0.1 Catalog Scope & Availability Depth Queries ---
    # E.g. "there are only three phones available in this or there are more phones are available", "where only three smartphones available"
    if any(w in t for w in ["phone", "smartphone", "mobile"]) and any(w in t for w in ["only three", "only 3", "more phones", "how many", "all phones", "other phones", "more available", "where only", "why only"]):
        return (
            "We have a total of **7 smartphones** in our catalog! In addition to the three shown:\n"
            "• **Volt PowerMax 5G** (₹13,999) — 6000mAh battery champion (up to 2.5 days battery life).\n"
            "• **Zenith CamPro 5G** (₹34,999) — Triple 50MP Sony IMX sensors with Optical Image Stabilization (OIS).\n"
            "• **Aura Flagship X** (₹64,999) — Snapdragon 8 Gen 3 with 100x zoom and titanium build.\n"
            "• **Titan Fold Z** (₹1,24,999) — Dual 120Hz foldable screens for ultimate productivity.\n\n"
            "You can also browse all 7 smartphones in detail with full specifications under the **'Products, Leads & Appointments'** tab!"
        )

    if any(w in t for w in ["laptop", "laptops", "notebook"]) and any(w in t for w in ["only three", "only 3", "more laptops", "how many", "all laptops", "other laptops", "more available", "where only", "why only"]):
        return (
            "We carry **8 laptops** across every budget and use case!\n"
            "• **SlimLite 13** (₹24,999) & **VoltBook Student 14** (₹34,999) for students.\n"
            "• **ZenithBook Air 15** (₹48,999) & **OmniBook Flex 14 2-in-1** (₹54,999) for office and multitasking.\n"
            "• **CodeMaster Pro 15** (₹64,999) & **DevForge Extreme 16** (₹79,999) for programming & Docker.\n"
            "• **CyberPulse G15** (₹94,999) & **TitanBook Studio 16** (₹1,19,999) for RTX 4060/4070 gaming and 3D studio work.\n\n"
            "You can view and filter all 8 models in the Products tab!"
        )

    if any(w in t for w in ["tablet", "tablets", "tab"]) and any(w in t for w in ["only three", "only 3", "more tablets", "how many", "all tablets", "other tablets", "more available", "where only", "why only"]):
        return (
            "We have **5 tablets** in our catalog:\n"
            "• **MediaTab 8** (₹9,999) — Compact 8-inch for reading and streaming.\n"
            "• **TabStudy 10.1** (₹14,999) — Student e-learning tablet.\n"
            "• **NovaPad Air 11** (₹24,999) — 120Hz smooth display with quad speakers.\n"
            "• **Zenith Pad Creator 12** (₹38,999) — 2.8K display with active magnetic pressure stylus included.\n"
            "• **UltraSlate Pro 13** (₹59,999) — 13-inch OLED with Snapdragon X Elite for pro creative workflows!"
        )

    # --- 0.2 Personal introduction, name greetings & categories inquiry ---
    # E.g. "my name is Sai Narayan and I need to know what categories are present and can you introduce yourself"
    is_asking_intro = any(w in t for w in ["introduce yourself", "who are you", "what is your name", "tell me about yourself", "what are you", "introduce"])
    is_asking_categories = any(w in t for w in ["categories", "category", "what do you sell", "what products", "what do you offer", "what items", "what is present", "what are present"])

    user_name = extract_customer_name(user_input)

    if is_asking_intro or is_asking_categories or (user_name and not any(kw in t for kw in ["laptop", "phone", "tablet", "price", "70k", "70000", "35k", "visit", "tomorrow"])):
        greeting_prefix = f"Hello {user_name}! Pleasure to meet you. " if user_name else "Hello! "
        intro_part = f"I am {AGENT_NAME}, your AI electronics sales advisor at {COMPANY_NAME}. "
        categories_part = (
            "We offer four primary electronics categories:\n\n"
            "1. 💻 **Laptops** — from student models (₹24,999) to developer ultrabooks and RTX 4060 gaming.\n"
            "2. 📱 **Smartphones** — budget 5G phones to 50MP Sony OIS camera devices and foldables (₹11,999 to ₹1,24,999).\n"
            "3. 📲 **Tablets** — for e-learning, digital note-taking with magnetic stylus, and OLED workstations.\n"
            "4. 🎧 **Workspace Accessories** — mechanical keyboards, ergonomic mice, 100W GaN chargers, and ANC headsets.\n\n"
            "Which category or product type would you like to explore today?"
        )
        if is_asking_intro and is_asking_categories:
            return greeting_prefix + intro_part + categories_part
        elif is_asking_categories:
            return greeting_prefix + categories_part
        elif is_asking_intro:
            return greeting_prefix + intro_part + "I can assist you with product recommendations, specification comparisons, active discount offers, and booking showroom visits. What can I help you find today?"
        else:
            return greeting_prefix + f"Welcome to {COMPANY_NAME}! I'm {AGENT_NAME}. Are you looking for laptops, smartphones, tablets, or accessories today?"

    # 1. Telugu Greeting / Query (Script or transliteration)
    if any("\u0C00" <= ch <= "\u0C7F" for ch in user_input) or any(w in t for w in ["namaskaram", "namaskaramu", "telugu", "bagundi", "kavali", "chudali", "dharalu", "dharam"]):
        if any(w in t for w in ["phone", "mobile", "ఫోన్", "స్మార్ట్", "speed"]):
            return DEMO_REPLIES["telugu_phone"]
        elif any(w in t for w in ["laptop", "coding", "computer", "లాప్", "కంప్యూటర్"]):
            return DEMO_REPLIES["telugu_laptop"]
        return DEMO_REPLIES["telugu_greeting"]

    # 1.1 Kannada Greeting / Query (Script or transliteration)
    if any("\u0C80" <= ch <= "\u0CFF" for ch in user_input) or any(w in t for w in ["namaskara", "kannada", "chennagide", "beku", "nodabeku", "bele", "yavudu"]):
        if any(w in t for w in ["phone", "mobile", "ಫೋನ್", "ಸ್ಮಾರ್ಟ್"]):
            return DEMO_REPLIES["kannada_phone"]
        elif any(w in t for w in ["laptop", "coding", "computer", "ಲ್ಯಾಪ್", "ಕಂಪ್ಯೂಟರ್"]):
            return DEMO_REPLIES["kannada_laptop"]
        return DEMO_REPLIES["kannada_greeting"]

    # 2. English Greeting (whole words only to prevent 'hi' matching 'sketching')
    if re.search(r"\b(hello|hi|hey|good morning|good afternoon|greetings)\b", t):
        if not any(kw in t for kw in ["tablet", "laptop", "phone", "price", "budget", "recommend", "under", "need", "looking", "sketching"]):
            return DEMO_REPLIES["greeting"]

    # 2.5 Dynamic Recommendation Matching when user specified budget or non-laptop category
    has_budget = parse_budget_from_text(user_input) is not None
    detected_cat = detect_category(user_input)
    clean_t = re.sub(r"\b(phone number|mobile number|my phone|contact number)\b", "", t)
    is_phone_query = any(w in clean_t for w in ["phone", "smartphone", "mobile"])
    is_tablet_query = any(w in t for w in ["tablet", "tab", "ipad"])
    is_accessory_query = any(w in t for w in ["keyboard", "mouse", "headphone", "charger", "accessories", "accessory"])

    # If the user asked for a budget or specific category (e.g. "best gaming phone under 20000"), prioritize catalog matches!
    if recs and (has_budget or is_phone_query or is_tablet_query or is_accessory_query or (detected_cat and detected_cat != "Laptops")):
        return f"Based on your requirements, here are our top catalog recommendations:\n\n{format_recommendations_for_agent(recs)}\n\nWould you like to book a showroom demo to test these in person?"

    # 3. Direct Recommendation Questions
    if "which one is best" in t or "which is best" in t or "which should i buy" in t or "which do you recommend" in t:
        return DEMO_REPLIES["which_is_best"]

    if any(w in t for w in ["compare", "difference between", "versus", "vs"]):
        return DEMO_REPLIES["comparison"]

    if any(w in t for w in ["program", "code", "coding", "developer", "software", "python", "70,000", "70000", "70k"]):
        if not is_phone_query and not is_tablet_query:
            return DEMO_REPLIES["programming_laptop"]

    if any(w in t for w in ["student", "college", "school", "study", "35k", "35,000"]):
        if not is_phone_query and not is_tablet_query:
            return DEMO_REPLIES["student_laptop"]

    if any(w in t for w in ["gaming", "game", "rtx", "cyberpulse", "1 lakh", "100000", "fps"]):
        if not is_phone_query and not is_tablet_query:
            return DEMO_REPLIES["gaming_laptop"]

    # 4. Product Categories
    if any(w in t for w in ["tablet", "tab", "ipad", "zenith pad", "stylus"]):
        return DEMO_REPLIES["tablets"]

    if any(w in t for w in ["keyboard", "mouse", "headphone", "charger", "accessories", "accessory", "earbuds"]):
        return DEMO_REPLIES["accessories"]

    if any(w in t for w in ["battery phone", "battery life", "powermax", "6000mah"]):
        return DEMO_REPLIES["battery_phone"]

    if any(w in t for w in ["camera", "photo", "vlog", "reel", "campro", "photography"]):
        return DEMO_REPLIES["camera_phone"]

    if any(w in t for w in ["flagship", "expensive phone", "titan fold", "foldable", "best phone", "premium phone"]):
        return DEMO_REPLIES["flagship_phone"]

    # 5. Policies & Showroom / Appointment Requests
    if any(w in t for w in ["appointment", "have an appointment", "book an appointment", "schedule an appointment", "book slot", "book a slot", "book demo", "visit store", "store demo", "test this product", "test this", "hands on", "hands-on", "experience centre"]):
        return DEMO_REPLIES["store_visit"]

    if any(w in t for w in ["store", "showroom", "location", "address", "timings", "open", "timing", "hours"]):
        if any(w in t for w in ["visit", "book", "come", "tomorrow"]):
            return DEMO_REPLIES["store_visit"]
        return DEMO_REPLIES["store_hours"]

    if any(w in t for w in ["warranty", "return", "replace", "guarantee", "repair", "service center"]):
        return DEMO_REPLIES["warranty_policy"]

    if any(w in t for w in ["delivery", "shipping", "courier", "open box", "open-box", "timeline"]):
        return DEMO_REPLIES["delivery_policy"]

    if any(w in t for w in ["payment", "emi", "no cost emi", "no-cost", "card", "upi", "cod", "cash on delivery"]):
        return DEMO_REPLIES["payment_emi"]

    if any(w in t for w in ["gst", "invoice", "tax", "b2b", "gstin"]):
        return DEMO_REPLIES["gst_invoice"]

    if any(w in t for w in ["offer", "discount", "exchange", "cashback", "student tech pass"]):
        return DEMO_REPLIES["offers"]

    # 6. Recommendation Engine matches
    if recs:
        return f"Based on your requirements, here are our top catalog recommendations:\n\n{format_recommendations_for_agent(recs)}\n\nWould you like to book a showroom demo to test these in person?"

    # 7. RAG Context Extraction (Smart clean summary)
    if context and len(context) > 40:
        first_chunk = context.split("---")[0] if "---" in context else context
        cleaned = _clean_rag_chunk_for_speech(first_chunk)
        if len(cleaned) > 20:
            return f"{cleaned} Would you like more details on this or shall I help you book a showroom consultation?"

    return f"I can certainly help you with that! Are you looking for a laptop, smartphone, tablet, or accessories, and what budget or use case do you have in mind?"


def execute_sales_turn(
    call_id: str,
    user_input: str,
    language: str = "en",
    history: Optional[List[Dict]] = None
) -> Dict:
    """
    Execute one full conversational sales turn.
    Returns:
      {reply, mode, language, sentiment, lead, sources, recommendations, booking, ics_content, latency_ms}
    """
    db = SessionLocal()
    history = history or []

    try:
        start_t = time.time()
        lower_input = user_input.lower()

        # Language Detection (English, Telugu, Kannada)
        if any("\u0C00" <= ch <= "\u0C7F" for ch in user_input) or any(w in lower_input for w in ["namaskaram", "namaskaramu", "telugu", "bagundi", "kavali", "chudali"]):
            language = "te"
        elif any("\u0C80" <= ch <= "\u0CFF" for ch in user_input) or any(w in lower_input for w in ["namaskara", "kannada", "chennagide", "beku", "nodabeku"]):
            language = "kn"
        else:
            language = language or "en"

        # 1. RAG Context Retrieval
        rag_sources = rag_engine.retrieve(user_input, top_k=3)
        rag_context = rag_engine.get_context(user_input, top_k=3)

        # 2. Product Recommendations
        recs = recommend_products(user_input, max_results=3)

        # 3. Sentiment Analysis
        sentiment_label, sentiment_score = analyze_sentiment(user_input)

        # 4. Lead Extraction & BANT Scoring
        all_text = " ".join([h.get("content", "") for h in history]) + " " + user_input
        extracted_lead: ExtractedLead = extract_lead_from_conversation(all_text)

        # 5. Generate Response (OpenAI or Demo Mode)
        client = get_ai_client()
        agent_reply = ""
        mode = "Demo Mode"

        if client:
            try:
                system_content = f"""
{ELECTROMART_SYSTEM_PROMPT}

KNOWLEDGE BASE CONTEXT:
{rag_context}

CATALOG RECOMMENDATIONS:
{format_recommendations_for_agent(recs)}
""".strip()
                messages = [{"role": "system", "content": system_content}]
                for h in history[-MAX_HISTORY_TURNS:]:
                    role = "assistant" if h.get("role") in ["assistant", "agent"] else "user"
                    messages.append({"role": role, "content": h.get("content", "")})

                messages.append({"role": "user", "content": user_input})

                completion = client.chat.completions.create(
                    model=OPENAI_MODEL_CHAT,
                    messages=messages,
                    temperature=0.3
                )
                agent_reply = completion.choices[0].message.content.strip()
                mode = f"OpenAI ({OPENAI_MODEL_CHAT})"
            except Exception as e:
                print(f"OpenAI API error, using demo fallback: {e}")
                agent_reply = _generate_demo_reply(user_input, recs, rag_context)
                mode = f"Demo Mode (API error: {str(e)[:40]})"
        else:
            agent_reply = _generate_demo_reply(user_input, recs, rag_context)
            mode = "Demo Mode"

        # 6. Appointment Booking Detection — Requires explicit booking intent, previous booking prompt, or contact submission + explicit time/date
        booking_result = None
        ics_data = None
        lower_input = user_input.lower()
        
        has_booking_intent = bool(re.search(r"\b(book|booking|schedule|reserve|slot|confirm visit|showroom visit|store visit|take an appointment)\b", lower_input))
        has_explicit_time = bool(re.search(r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|p\.m\.|a\.m\.)|\bat\s+\d{1,2}\b|\btomorrow\b|\btoday\b|\bmorning\b|\bevening\b|\bafternoon\b)", lower_input))

        # Check if previous agent turn was an appointment booking prompt
        prev_agent_prompt = False
        if history:
            for h in reversed(history):
                if h.get("role") in ["assistant", "agent"]:
                    prev_text = h.get("content", "").lower()
                    prev_agent_prompt = any(w in prev_text for w in ["what date and time", "convenient for your visit", "schedule a hands-on", "book a showroom demo"])
                    break

        has_contact_submission = bool(extracted_lead.email or extracted_lead.phone or extracted_lead.name) and has_explicit_time

        if (has_booking_intent or prev_agent_prompt or has_contact_submission) and has_explicit_time:
            target_date, target_time_str = parse_natural_datetime(user_input)
            cust_email = extracted_lead.email or "customer@example.com"
            cust_name = extracted_lead.name or "Valued Customer"

            # Derive product discussed from recommendations or conversation history
            prod_name = "Electronics Consultation"
            if recs:
                prod_name = recs[0]["product_name"]
            elif history:
                for h in reversed(history):
                    m_p = re.search(r"\*\*([A-Za-z0-9\s]{3,30})\*\*", h.get("content", ""))
                    if m_p:
                        prod_name = m_p.group(1).strip()
                        break

            success, b_msg, appt = book_appointment_in_db(
                db=db,
                customer_name=cust_name,
                customer_email=cust_email,
                customer_phone=extracted_lead.phone,
                date_val=target_date,
                time_str=target_time_str,
                appointment_type="Store Visit",
                interested_product=prod_name,
                city=extracted_lead.city or "Mumbai",
                notes="Booked via AI Voice Agent"
            )
            if success:
                booking_result = {
                    "status": "success",
                    "message": b_msg,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "time": target_time_str
                }
                ics_data = generate_ics_content(
                    cust_name, target_date, target_time_str,
                    product=prod_name
                )
                agent_reply = (
                    f"Thank you, {cust_name}! Your showroom appointment has been successfully confirmed for "
                    f"**{target_date.strftime('%d %B %Y')} at {target_time_str}** at our {extracted_lead.city or 'Mumbai'} experience centre for **{prod_name}**. "
                    f"Your Booking ID is **{appt.appointment_id}**. Your .ICS calendar invite is ready below!"
                )
            else:
                agent_reply = f"Hello {cust_name}! {b_msg}"

        # 7. Persist to Database
        lead = db.query(Lead).filter(Lead.call_id == call_id).first()
        if not lead:
            lead = Lead(
                call_id=call_id,
                name=extracted_lead.name,
                email=extracted_lead.email,
                phone=extracted_lead.phone,
                city=extracted_lead.city,
                interested_category=extracted_lead.interested_category,
                budget=extracted_lead.budget,
                requirement=extracted_lead.requirement,
                purchase_timeline=extracted_lead.purchase_timeline,
                purchase_intent=extracted_lead.purchase_intent,
                score=extracted_lead.score,
                qualification_status=extracted_lead.status
            )
            db.add(lead)
        else:
            if extracted_lead.name: lead.name = extracted_lead.name
            if extracted_lead.email: lead.email = extracted_lead.email
            if extracted_lead.phone: lead.phone = extracted_lead.phone
            if extracted_lead.city: lead.city = extracted_lead.city
            if extracted_lead.interested_category: lead.interested_category = extracted_lead.interested_category
            if extracted_lead.budget: lead.budget = extracted_lead.budget
            if extracted_lead.requirement: lead.requirement = extracted_lead.requirement
            if extracted_lead.purchase_timeline: lead.purchase_timeline = extracted_lead.purchase_timeline
            lead.score = max(lead.score, extracted_lead.score)
            lead.qualification_status = extracted_lead.status

        # Save Messages
        db.add(Message(call_id=call_id, sender="user", text=user_input, sentiment_label=sentiment_label, sentiment_score=sentiment_score))
        db.add(Message(call_id=call_id, sender="agent", text=agent_reply, sentiment_label="positive", sentiment_score=0.5))

        # Save Recommended Products
        for r in recs:
            db.add(RecommendedProduct(
                call_id=call_id,
                product_id=r["product_id"],
                product_name=r["product_name"],
                price_inr=r["price_inr"],
                reason=r["reason"]
            ))

        db.commit()

        latency_ms = int((time.time() - start_t) * 1000)

        return {
            "reply": agent_reply,
            "mode": mode,
            "language": language,
            "sentiment": {"label": sentiment_label, "score": sentiment_score},
            "lead": extracted_lead.model_dump() if hasattr(extracted_lead, "model_dump") else extracted_lead.dict(),
            "sources": [{"text": chunk[:140], "score": score} for chunk, score in rag_sources],
            "recommendations": recs,
            "booking": booking_result,
            "ics_content": ics_data,
            "latency_ms": latency_ms
        }
    finally:
        db.close()
