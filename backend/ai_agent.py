"""
ElectroMart India — AI Sales Voice Agent Orchestrator
Coordinates RAG context retrieval, accurate product catalog question answering,
OpenAI LLM reasoning (with robust rule-based Demo Mode fallback), BANT lead scoring,
sentiment tracking, and multi-step conversational appointment booking.
"""
import os
import re
import time
import datetime
from typing import List, Dict, Optional, Tuple, Any
from dotenv import load_dotenv

from backend.config import (
    COMPANY_NAME, AGENT_NAME, OPENAI_MODEL_CHAT, OPENAI_BASE_URL,
    MAX_HISTORY_TURNS, AGENT_ROLE_DESCRIPTION, SHOWROOM_CITIES
)
from backend.rag import rag_engine
from backend.product_recommendation import (
    load_products_df, recommend_products, format_recommendations_for_agent,
    parse_budget_from_text, detect_category
)
from backend.lead_qualification import extract_lead_from_conversation, extract_customer_name, ExtractedLead
from backend.sentiment import analyze_sentiment, should_escalate
from backend.appointment import (
    parse_natural_datetime, book_appointment_in_db, get_available_slots,
    generate_ics_content
)
from database.db import SessionLocal
from database.models import Customer, Lead, Call, Message, RecommendedProduct, Appointment

load_dotenv()

# System Prompt
ELECTROMART_SYSTEM_PROMPT = f"""
{AGENT_ROLE_DESCRIPTION}

GUIDELINES FOR CONVERSATION:
1. Greet the customer warmly and politely in English, Telugu, Kannada, or Hindi (match customer language).
2. Understand what they are looking for (laptops, smartphones, tablets, or accessories).
3. If the customer asks specific product questions (e.g. brands available, RAM, processor, storage, price, warranty, stock), ANSWER DIRECTLY and accurately using the KNOWLEDGE BASE and CATALOG data. Do not deflect with generic recommendations unless asked for recommendations.
4. If asked about competitor brands (like HP, Dell, Lenovo, Apple), clarify that ElectroMart carries partner brands (VoltTech, Zenith, NovaCorp, Aura, PulseGaming, Apex, GreenTech) and offer the best catalog match.
5. For recommendations, recommend products ONLY from the provided CATALOG RECOMMENDATIONS context. Do not invent products or prices.
6. When a customer wants an appointment, follow the multi-step booking process:
   - Step 1: Acknowledge and ask for basic details (name, phone, product).
   - Step 2: Ask for preferred date and time.
   - Step 3: Ask for appointment type/location (Store visit, Online consultation, Callback).
   - Step 4: Confirm all details before booking.
   - Step 5: Confirm booking only after database verification.
7. Keep answers concise, consultative, and professional (under 3-4 sentences per turn).
"""

# Demo mode responses for offline testing
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
        "Could you please share your basic details (your name, phone number, and product of interest) so I can get that set up?"
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
    ),
    "hindi_greeting": (
        "नमस्ते! इलेक्ट्रोमार्ट इंडिया में आपका स्वागत है। मैं अन्या, आपकी AI इलेक्ट्रॉनिक्स सेल्स सलाहकार हूँ। "
        "क्या आप लैपटॉप, स्मार्टफोन, टैबलेट या एक्सेसरीज़ की तलाश में हैं?"
    ),
    "hindi_laptop": (
        "नमस्ते! कोडिंग और ऑफिस के काम के लिए ZenithBook Air 15 (₹48,999) और CodeMaster Pro 15 (₹64,999) "
        "बेहतरीन विकल्प हैं। इनमें 16GB RAM और पावरफुल प्रोसेसर मिलता है। क्या आप स्टोर डेमो देखना चाहेंगे?"
    ),
    "hindi_phone": (
        "नमस्ते! गेमिंग और कैमरा के लिए Pulse Velocity 5G (₹16,999) और Zenith CamPro 5G (₹34,999) "
        "शानदार स्मार्टफोन हैं। क्या आप स्टोर विज़िट शेड्यूल करना चाहते हैं?"
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


def is_demo_mode() -> bool:
    """True when no OpenAI API key is configured."""
    return get_ai_client() is None


def _clean_rag_chunk_for_speech(chunk: str) -> str:
    """Clean RAG chunk formatting for clean conversational reply."""
    clean = re.sub(r"\[.*?\.txt\]", "", chunk)
    clean = re.sub(r"#{1,6}\s*", "", clean)
    clean = clean.replace("**", "").replace("- ", "").strip()
    if "Answer:" in clean:
        clean = clean.split("Answer:", 1)[1].strip()
    elif "answer:" in clean:
        clean = clean.split("answer:", 1)[1].strip()

    sentences = [s.strip() for s in clean.split(".") if s.strip()]
    if sentences:
        return ". ".join(sentences[:2]) + "."
    return clean[:200]


def find_catalog_product(query_text: str, history: Optional[List[Dict]] = None) -> Optional[Dict]:
    """Identify which catalog product is being discussed in the query or recent conversation."""
    df_p = load_products_df()
    q_low = query_text.lower()

    # 1. Exact or partial match in current turn
    for _, row in df_p.iterrows():
        p_name = row["product_name"].lower()
        p_id = row["product_id"].lower()
        if p_name in q_low or p_id in q_low:
            return row.to_dict()

    # Match key product tokens
    token_map = {
        "voltbook": "VoltBook Student 14",
        "zenithbook": "ZenithBook Air 15",
        "codemaster": "CodeMaster Pro 15",
        "devforge": "DevForge Extreme 16",
        "omnibook": "OmniBook Slim 13",
        "cyberpulse": "CyberPulse G15",
        "studiocraft": "StudioCraft Pro 16",
        "ecobook": "EcoBook Lite 15",
        "campro": "Zenith CamPro 5G",
        "velocity": "Pulse Velocity 5G",
        "powermax": "Volt PowerMax 5G",
        "flagship x": "Aura Flagship X",
        "titan fold": "Titan Fold Z",
        "tabstudy": "TabStudy 10.1",
        "novapad": "NovaPad Air 11",
        "pad creator": "Zenith Pad Creator 12",
        "soundbeats": "Aura SoundBeats ANC Headset",
        "mechkeys": "MechKeys RGB Wireless Mechanical Keyboard",
        "precisionglide": "PrecisionGlide Ergonomic Wireless Mouse"
    }
    for token, full_name in token_map.items():
        if token in q_low:
            match = df_p[df_p["product_name"] == full_name]
            if not match.empty:
                return match.iloc[0].to_dict()

    # 2. Check history for previously discussed product
    if history:
        for h in reversed(history):
            content = h.get("content", "").lower()
            for token, full_name in token_map.items():
                if token in content:
                    match = df_p[df_p["product_name"] == full_name]
                    if not match.empty:
                        return match.iloc[0].to_dict()

    # Default to our premier developer laptop if discussing "this laptop" without explicit mention
    if any(w in q_low for w in ["this laptop", "the laptop"]):
        match = df_p[df_p["product_id"] == "LAP-103"]
        if not match.empty:
            return match.iloc[0].to_dict()

    return None


def answer_direct_product_question(user_input: str, history: Optional[List[Dict]] = None) -> Optional[str]:
    """
    Directly answer specific product questions regarding brands, RAM, processor,
    storage, graphics, price, warranty, stock, and competitors.
    """
    t = user_input.lower()
    df_p = load_products_df()

    # Direct appointment request from customer
    if any(w in t for w in ["an appointment", "appointment for this", "visit your store", "book an appointment", "take an appointment", "showroom appointment"]):
        return DEMO_REPLIES["store_visit"]

    # --- 1. Brands Inquiries ---
    # E.g. "what brand laptops are available", "what brands of laptops do you sell"
    if any(w in t for w in ["brand", "brands"]) and any(w in t for w in ["laptop", "laptops", "notebook"]):
        return (
            f"At {COMPANY_NAME}, we carry **7 verified laptop brands** across all use cases:\n\n"
            "1. **NovaCorp** — Professional developer workhorses (CodeMaster Pro 15 ₹64,999, DevForge Extreme 16 ₹79,999).\n"
            "2. **Zenith** — Premium slim aluminum notebooks (ZenithBook Air 15 ₹48,999).\n"
            "3. **VoltTech** — Affordable student & education laptops (VoltBook Student 14 ₹34,999).\n"
            "4. **PulseGaming** — High-performance RTX 4060 gaming laptops (CyberPulse G15 ₹94,999).\n"
            "5. **Aura** — Ultra-thin 2.8K OLED executive ultrabooks (OmniBook Slim 13 ₹89,999).\n"
            "6. **Apex** — 4K Mini-LED studio creator workstations (StudioCraft Pro 16 ₹1,49,999).\n"
            "7. **GreenTech** — Budget eco-friendly computing (EcoBook Lite 15 ₹24,999).\n\n"
            "Which brand or specific requirement would you like to explore?"
        )

    if any(w in t for w in ["brand", "brands"]) and any(w in t for w in ["phone", "phones", "smartphone", "smartphones"]):
        return (
            f"For smartphones, {COMPANY_NAME} offers **7 top models** from 6 trusted brands:\n\n"
            "• **ApexMobile** — Apex Phone Neo 5G (₹11,999)\n"
            "• **PulseMobile** — Pulse Velocity 5G 120Hz AMOLED (₹16,999)\n"
            "• **VoltTech** — Volt PowerMax 5G with monster 6000mAh battery (₹13,999)\n"
            "• **NovaCorp** — Nova Edge 11 Pro with 80W charging (₹27,999)\n"
            "• **Zenith** — Zenith CamPro 5G with 50MP Sony OIS (₹34,999)\n"
            "• **Aura & TitanMobile** — Aura Flagship X (₹64,999) and Titan Fold Z (₹1,24,999)."
        )

    # --- 2. Competitor Brands (HP, Dell, Lenovo, Apple/MacBook) ---
    if any(b in t for b in ["hp", "hewlett packard", "dell", "lenovo", "thinkpad", "macbook", "apple"]):
        return (
            f"At {COMPANY_NAME}, we specialize in our curated direct-manufacturer retail brands: "
            f"**NovaCorp, Zenith, VoltTech, PulseGaming, Aura, and Apex**.\n\n"
            f"We do not stock HP or Dell laptops, but our **CodeMaster Pro 15 (₹64,999)** and "
            f"**ZenithBook Air 15 (₹48,999)** offer equivalent or superior 16GB DDR5 memory, "
            f"Intel 13th Gen / AMD Ryzen processors, and comprehensive on-site warranties at significantly better value! "
            f"Would you like to compare their specifications?"
        )

    # --- 3. Which Brand is Better for Programming ---
    if ("programming" in t or "coding" in t or "developer" in t) and ("which brand" in t or "better brand" in t or "best brand" in t):
        return (
            "For programming and software development, **NovaCorp** is our top-rated brand! "
            "Their **CodeMaster Pro 15 (₹64,999)** is built specifically for coders with an Intel Core i5 13500H processor, "
            "16GB DDR5 RAM, and a crisp 2K 100% sRGB display. For heavy Docker, mobile emulation, and ML workloads, "
            "the **DevForge Extreme 16 (₹79,999)** adds an AMD Ryzen 7 and dedicated RTX 3050 GPU."
        )

    # --- 4. Product Specific Specifications Lookup ---
    prod = find_catalog_product(user_input, history)
    if prod:
        p_name = prod["product_name"]
        p_brand = prod["brand"]

        # RAM Question
        if any(w in t for w in ["ram", "memory", "16 gb", "16gb", "8 gb", "8gb", "32 gb", "32gb"]):
            if "16 gb" in t or "16gb" in t:
                if "16gb" in prod["ram"].lower():
                    return f"Yes! The ElectroMart catalog lists the **{p_name}** ({p_brand}) with **{prod['ram']}**."
                else:
                    return f"The **{p_name}** comes standard with **{prod['ram']}**. If you need 16GB RAM, our **ZenithBook Air 15 (₹48,999)** and **CodeMaster Pro 15 (₹64,999)** come standard with 16GB RAM."
            return f"The ElectroMart catalog lists the **{p_name}** ({p_brand}) with **{prod['ram']}**."

        # Processor Question
        if any(w in t for w in ["processor", "cpu", "chipset", "which processor", "what processor"]):
            return f"The **{p_name}** is powered by the **{prod['processor']}** processor."

        # Storage Question
        if any(w in t for w in ["storage", "ssd", "hard drive", "capacity", "disk", "nvme"]):
            return f"The ElectroMart catalog lists the **{p_name}** with **{prod['storage']}**."

        # Graphics Question
        if any(w in t for w in ["graphics", "gpu", "rtx", "geforce", "nvidia", "radeon", "graphics card"]):
            return f"The **{p_name}** features **{prod['graphics']}** graphics."

        # Price Question
        if any(w in t for w in ["price", "cost", "how much is", "how much does it cost", "rate"]):
            return f"The official price of the **{p_name}** is **₹{prod['price_inr']:,}** (inclusive of all taxes, with 0% EMI available)."

        # Warranty Question
        if any(w in t for w in ["warranty", "guarantee"]):
            return f"The **{p_name}** comes with official **{prod['warranty']}**, backed by our 7-day doorstep replacement policy."

        # Stock Question
        if any(w in t for w in ["in stock", "stock status", "available", "inventory"]):
            return f"The **{p_name}** is currently **{prod['stock_status']}** across our showrooms."

        # Display Question
        if any(w in t for w in ["display", "screen", "resolution"]):
            return f"The **{p_name}** features a **{prod['display']}** display."

        # Battery Question
        if any(w in t for w in ["battery", "battery life", "battery backup"]):
            return f"The **{p_name}** delivers **{prod['battery']}**."

    return None


def _handle_voice_appointment_flow(
    user_input: str,
    history: List[Dict],
    booking_state: Dict,
    language: str = "en"
) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
    """
    Executes the 6-step conversational voice appointment booking sequence.
    Returns: (agent_reply, booking_result, ics_content)
    """
    lower_input = user_input.lower()
    db = SessionLocal()

    try:
        current_step = booking_state.get("step")

        # Step 1: Detect Appointment Booking Intent
        is_appt_request = (
            bool(re.search(
                r"\b(?:book|take|want|need|schedule|have|get|make|request|fix)\s+(?:an?\s+)?appointment\b|"
                r"\b(?:an\s+appointment|appointment\s+for|appointment\s+booking|book\s+(?:a\s+)?(?:slot|demo|visit)|"
                r"visit\s+store|store\s+visit|showroom\s+visit|store\s+demo)\b", lower_input
            )) or any(w in lower_input for w in ["అపాయింట్‌మెంట్", "అపాయింట్మెంట్", "ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್", "अपॉइंटमेंट"])
        ) and not any(w in lower_input for w in ["reschedule", "cancel", "timing", "hours", "status"])

        if current_step is None and is_appt_request:
            # Check what information is already in state or conversation
            all_hist = " ".join([h.get("content", "") for h in history]) + " " + user_input
            extracted = extract_lead_from_conversation(all_hist)

            if extracted.name: booking_state["name"] = extracted.name
            if extracted.phone: booking_state["phone"] = extracted.phone
            if extracted.email: booking_state["email"] = extracted.email
            if extracted.city: booking_state["city"] = extracted.city
            if extracted.interested_category: booking_state["product"] = extracted.interested_category

            # Check if time/date was also provided upfront
            has_time_phrase = bool(re.search(r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|p\.m\.|a\.m\.)|\bat\s+\d{1,2}\b)", lower_input))
            if has_time_phrase:
                target_date, target_time_str = parse_natural_datetime(user_input)
                booking_state["date"] = target_date.strftime("%Y-%m-%d")
                booking_state["time"] = target_time_str

            # If name or contact is missing, ask for basic details
            if not booking_state.get("name") or not (booking_state.get("phone") or booking_state.get("email")):
                booking_state["step"] = "collect_details"
                if language == "te":
                    return "ఖచ్చితంగా! నేను అపాయింట్‌మెంట్ బుక్ చేయడంలో మీకు సహాయపడతాను. దయచేసి మీ ప్రాథమిక వివరాలు (పేరు, ఫోన్ నంబర్ మరియు ఆసక్తి ఉన్న ఉత్పత్తి) చెప్పండి.", None, None
                elif language == "kn":
                    return "ಖಂಡಿತ! ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬುಕ್ ಮಾಡಲು ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹೆಸರು, ಫೋನ್ ಸಂಖ್ಯೆ ಮತ್ತು ಆಸಕ್ತಿಯಿರುವ ಉತ್ಪನ್ನ ತಿಳಿಸಿ.", None, None
                elif language == "hi":
                    return "ज़रूर! मैं अपॉइंटमेंट बुक करने में आपकी मदद कर सकती हूँ। कृपया पहले अपना नाम, फ़ोन नंबर और पसंद का प्रोडक्ट बताएं।", None, None
                else:
                    return "Sure! I can help you book an appointment. Could you please fill in your basic details first (your name, phone number, and product of interest)?", None, None
            else:
                # Basic details already present! Advance to asking time or location
                if booking_state.get("date") and booking_state.get("time"):
                    booking_state["step"] = "ask_location"
                    if language == "te":
                        return "మీరు అపాయింట్‌మెంట్ ఎక్కడ కోరుకుంటున్నారు? మీరు షోరూమ్ విజిట్, ఆన్‌లైన్ కన్సల్టేషన్ లేదా కాల్‌బ్యాక్‌ను ఇష్టపడతారా?", None, None
                    elif language == "kn":
                        return "ನೀವು ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಎಲ್ಲಿ ಬಯಸುತ್ತೀರಿ? ಶೋರೂಂ ಭೇಟಿ, ಆನ್‌ಲೈನ್ ಸಮಾಲೋಚನೆ ಅಥವಾ ಕಾಲ್‌ಬ್ಯಾಕ್ ಬಯಸುವಿರಾ?", None, None
                    elif language == "hi":
                        return "आप अपॉइंटमेंट कहाँ रखना चाहेंगे? क्या आप स्टोर विज़िट, ऑनलाइन कंसल्टेशन या कॉलबैक पसंद करेंगे?", None, None
                    else:
                        return "Where would you like to have the appointment? Would you prefer a store visit, an online consultation, or a callback?", None, None
                else:
                    booking_state["step"] = "ask_time"
                    if language == "te":
                        return f"ధన్యవాదాలు {booking_state['name']}! మీ అపాయింట్‌మెంట్ కోసం మీరు ఏ తేదీ మరియు సమయాన్ని ఇష్టపడతారు?", None, None
                    elif language == "kn":
                        return f"ಧನ್ಯವಾದಗಳು {booking_state['name']}! ನಿಮ್ಮ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್‌ಗಾಗಿ ನೀವು ಯಾವ ದಿನಾಂಕ మరియు సమయాన్ని ಆದ್ಯತೆ ನೀಡುತ್ತೀರಿ?", None, None
                    elif language == "hi":
                        return f"धन्यवाद {booking_state['name']}! आप अपनी अपॉइंटमेंट के लिए कौन सी तारीख और समय पसंद करेंगे?", None, None
                    else:
                        return f"Thank you, {booking_state['name']}! What date and time would you prefer for your appointment?", None, None

        # Step 2: Collecting Customer Details
        if current_step == "collect_details":
            extracted = extract_lead_from_conversation(user_input)
            if extracted.name: booking_state["name"] = extracted.name
            if extracted.phone: booking_state["phone"] = extracted.phone
            if extracted.email: booking_state["email"] = extracted.email
            if extracted.interested_category: booking_state["product"] = extracted.interested_category

            # Also check for name regex if not caught
            name_cand = extract_customer_name(user_input)
            if name_cand: booking_state["name"] = name_cand

            # Check phone regex supporting space-separated digits
            m_ph = re.search(r"(\+?\d{1,3}[-.\s]?)?([6-9]\d{3,4}[\-\s]?\d{5,6}|\d{10})", user_input)
            if m_ph: booking_state["phone"] = re.sub(r"[^\d+]", "", m_ph.group(0))

            # Check if time/date was also supplied in this turn
            has_time_phrase = bool(re.search(r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|p\.m\.|a\.m\.)|\bat\s+\d{1,2}\b)", lower_input))
            if has_time_phrase:
                target_date, target_time_str = parse_natural_datetime(user_input)
                booking_state["date"] = target_date.strftime("%Y-%m-%d")
                booking_state["time"] = target_time_str

            # If still missing name
            if not booking_state.get("name"):
                return "May I have your name, please?", None, None
            # If missing contact
            if not booking_state.get("phone") and not booking_state.get("email"):
                return f"Thank you {booking_state['name']}! What is your phone number or email address?", None, None

            # Both captured! Advance to asking time or location
            if booking_state.get("date") and booking_state.get("time"):
                booking_state["step"] = "ask_location"
                if language == "te":
                    return "మీరు అపాయింట్‌మెంట్ ఎక్కడ కోరుకుంటున్నారు? మీరు షోరూమ్ విజిట్, ఆన్‌లైన్ కన్సల్టేషన్ లేదా కాల్‌బ్యాక్‌ను ఇష్టపడతారా?", None, None
                elif language == "kn":
                    return "ನೀವು ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಎಲ್ಲಿ ಬಯಸುತ್ತೀರಿ? ಶೋರೂಂ ಭೇಟಿ, ಆನ್‌ಲೈನ್ ಸಮಾಲೋಚನೆ ಅಥವಾ ಕಾಲ್‌ಬ್ಯಾಕ್ ಬಯಸುವಿರಾ?", None, None
                elif language == "hi":
                    return "आप अपॉइंटमेंट कहाँ रखना चाहेंगे? क्या आप स्टोर विज़िट, ऑनलाइन कंसल्टेशन या कॉलबैक पसंद करेंगे?", None, None
                else:
                    return "Where would you like to have the appointment? Would you prefer a store visit, an online consultation, or a callback?", None, None
            else:
                booking_state["step"] = "ask_time"
                if language == "te":
                    return f"ధన్యవాదాలు {booking_state['name']}! మీ అపాయింట్‌మెంట్ కోసం మీరు ఏ తేదీ మరియు సమయాన్ని ఇష్టపడతారు?", None, None
                elif language == "kn":
                    return f"ಧನ್ಯವಾದಗಳು {booking_state['name']}! ನಿಮ್ಮ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್‌ಗಾಗಿ ನೀವು ಯಾವ ದಿನಾಂಕ మరియు సమయాన్ని ಆದ್ಯತೆ ನೀಡುತ್ತೀರಿ?", None, None
                elif language == "hi":
                    return f"धन्यवाद {booking_state['name']}! आप अपनी अपॉइंटमेंट के लिए कौन सी तारीख और समय पसंद करेंगे?", None, None
                else:
                    return f"Thank you, {booking_state['name']}! What date and time would you prefer for your appointment?", None, None

        # Step 3: Ask Appointment Time
        if current_step == "ask_time":
            target_date, target_time_str = parse_natural_datetime(user_input)
            booking_state["date"] = target_date.strftime("%Y-%m-%d")
            booking_state["time"] = target_time_str
            booking_state["step"] = "ask_location"

            if language == "te":
                return "మీరు అపాయింట్‌మెంట్ ఎక్కడ కోరుకుంటున్నారు? మీరు షోరూమ్ విజిట్, ఆన్‌లైన్ కన్సల్టేషన్ లేదా కాల్‌బ్యాక్‌ను ఇష్టపడతారా?", None, None
            elif language == "kn":
                return "ನೀವು ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಎಲ್ಲಿ ಬಯಸುತ್ತೀರಿ? ಶೋರೂಂ ಭೇಟಿ, ಆನ್‌ಲೈನ್ ಸಮಾಲೋಚನೆ ಅಥವಾ ಕಾಲ್‌ಬ್ಯಾಕ್ ಬಯಸುವಿರಾ?", None, None
            elif language == "hi":
                return "आप अपॉइंटमेंट कहाँ रखना चाहेंगे? क्या आप स्टोर विज़िट, ऑनलाइन कंसल्टेशन या कॉलबैक पसंद करेंगे?", None, None
            else:
                return "Where would you like to have the appointment? Would you prefer a store visit, an online consultation, or a callback?", None, None

        # Step 4: Ask Location or Method
        if current_step == "ask_location":
            if any(w in lower_input for w in ["online", "video", "meet", "virtual"]):
                appt_type = "Product Consultation"
                location = "Online Video Consultation (Meeting link sent via SMS/Email)"
            elif any(w in lower_input for w in ["callback", "call", "phone"]):
                appt_type = "Sales Callback"
                location = f"Phone Callback to {booking_state.get('phone', 'Registered Number')}"
            else:
                appt_type = "Store Visit"
                city = booking_state.get("city") or "Mumbai"
                for c in SHOWROOM_CITIES:
                    if c.lower() in lower_input:
                        city = c
                        break
                location = f"ElectroMart Experience Centre, Flagship Store, {city}"

            booking_state["type"] = appt_type
            booking_state["location"] = location
            booking_state["step"] = "confirm"

            cust_name = booking_state.get("name", "Valued Customer")
            d_val = booking_state.get("date")
            t_val = booking_state.get("time")

            if language == "te":
                return f"నేను మీ అపాయింట్‌మెంట్‌ను ధృవీకరిస్తున్నాను: {cust_name}, తేదీ: {d_val}, సమయం: {t_val}, రకం: {appt_type}, ప్రదేశం: {location}. అంతా సరిగ్గా ఉందా?", None, None
            elif language == "kn":
                return f"ನಾನು ನಿಮ್ಮ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ದೃಢೀಕರಿಸುತ್ತಿದ್ದೇನೆ: {cust_name}, ದಿನಾಂಕ: {d_val}, ಸಮಯ: {t_val}, ಪ್ರಕಾರ: {appt_type}, ಸ್ಥಳ: {location}. ಎಲ್ಲವೂ ಸರಿಯಾಗಿದೆಯೇ?", None, None
            elif language == "hi":
                return f"मैं आपकी अपॉइंटमेंट की पुष्टि कर देती हूँ: {cust_name}, तारीख: {d_val}, समय: {t_val}, प्रकार: {appt_type}, स्थान: {location}। क्या सब कुछ सही है?", None, None
            else:
                return f"Let me confirm your appointment: {cust_name}, {d_val}, {t_val}, {appt_type}, {location}. Is everything correct?", None, None

        # Step 5 & 6: Confirm and Save to Database
        if current_step == "confirm":
            is_confirmed = any(w in lower_input for w in [
                "yes", "correct", "confirm", "proceed", "sounds good", "right", "sure",
                "ok", "fine", "yep", "done", "perfect", "అవును", "సరే", "ಹೌದು", "ಸರಿ", "हाँ", "सही", "पक्का"
            ])

            if is_confirmed:
                cust_name = booking_state.get("name") or "Valued Customer"
                cust_email = booking_state.get("email") or "customer@example.com"
                cust_phone = booking_state.get("phone")
                d_val = datetime.datetime.strptime(booking_state["date"], "%Y-%m-%d").date()
                t_val = booking_state["time"]
                appt_type = booking_state.get("type", "Store Visit")
                city = booking_state.get("city") or "Mumbai"
                location = booking_state.get("location")
                prod_name = booking_state.get("product") or "Electronics Consultation"

                ok, b_msg, appt = book_appointment_in_db(
                    db=db,
                    customer_name=cust_name,
                    customer_email=cust_email,
                    customer_phone=cust_phone,
                    date_val=d_val,
                    time_str=t_val,
                    appointment_type=appt_type,
                    interested_product=prod_name,
                    city=city,
                    location=location,
                    notes="Booked via Multi-Step AI Voice Assistant"
                )

                if ok:
                    booking_state["step"] = "booked"
                    booking_result = {
                        "status": "success",
                        "appointment_id": appt.appointment_id,
                        "date": booking_state["date"],
                        "time": t_val,
                        "location": location,
                        "message": b_msg
                    }
                    ics_data = generate_ics_content(cust_name, d_val, t_val, prod_name, location)
                    if language == "te":
                        reply = f"మీ అపాయింట్‌మెంట్ విజయవంతంగా బుక్ చేయబడింది. బుకింగ్ ID: **{appt.appointment_id}**. మీరు త్వరలో ధృవీకరణ వివరాలను అందుకుంటారు."
                    elif language == "kn":
                        reply = f"ನಿಮ್ಮ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಯಶಸ್ವಿಯಾಗಿ ಬುಕ್ ಆಗಿದೆ. ಬುಕಿಂಗ್ ID: **{appt.appointment_id}**. ನೀವು ಶೀಘ್ರದಲ್ಲೇ ದೃಢೀಕರಣ ವಿವರಗಳನ್ನು ಸ್ವೀಕರಿಸುತ್ತೀರಿ."
                    elif language == "hi":
                        reply = f"आपकी अपॉइंटमेंट सफलतापूर्वक बुक हो गई है। बुकिंग ID: **{appt.appointment_id}**। आपको जल्द ही विवरण प्राप्त हो जाएगा।"
                    else:
                        reply = f"Your appointment has been successfully booked. Booking ID: **{appt.appointment_id}**. You will receive the confirmation details shortly."
                    return reply, booking_result, ics_data
                else:
                    # Slot conflict, offer alternatives
                    avail_slots = get_available_slots(db, d_val, city)
                    alt_text = f" Available alternative slots: {', '.join(avail_slots[:3])}." if avail_slots else ""
                    booking_state["step"] = "ask_time"
                    return f"I apologize, {b_msg}.{alt_text} Which slot would you prefer instead?", None, None
            else:
                # Customer wants to change something
                booking_state["step"] = "ask_time"
                return "No problem! Which date or time would you prefer instead?", None, None

        return None, None, None
    finally:
        db.close()


def _generate_demo_reply(user_input: str, recs: List[Dict], context: str) -> str:
    """Generate realistic rule-based reply matching ElectroMart scenarios."""
    t = user_input.lower()

    # --- 0. Direct Product Specification or Brand Questions ---
    direct_ans = answer_direct_product_question(user_input)
    if direct_ans:
        return direct_ans

    # --- 0.1 Broad Catalog & Availability Inquiries ---
    if any(p in t for p in ["display the items", "available on this website", "items that are available", "what all products", "what products do you have", "show all products", "browse catalog", "full catalog", "what items are present", "what all do you sell"]):
        return (
            f"Welcome to {COMPANY_NAME}! We offer 25 top-rated electronics across 4 core categories:\n\n"
            "1. 💻 **Laptops (8 Models)** — Student laptops from ₹24,999 (VoltBook, SlimLite), Coding & Office work (CodeMaster Pro ₹64,999, ZenithBook Air ₹48,999), and High-Performance RTX Gaming (CyberPulse G15 ₹94,999, DevForge Extreme ₹79,999).\n"
            "2. 📱 **Smartphones (7 Models)** — 6000mAh monster battery (Volt PowerMax ₹13,999), 50MP Sony OIS Camera (Zenith CamPro ₹34,999), and Flagships (Aura Flagship X ₹64,999, Titan Fold Z ₹1,24,999).\n"
            "3. 📲 **Tablets (5 Models)** — E-learning & Students (TabStudy ₹14,999), 120Hz Media (NovaPad Air ₹24,999), and Stylus Creator pads (Zenith Pad Creator 12 ₹38,999).\n"
            "4. 🎧 **Accessories (5 Models)** — Mechanical keyboards (MechKeys ₹3,999), ergonomic mice (₹1,999), 100W GaN fast chargers (₹3,499), and ANC headphones (₹4,999).\n\n"
            "You can explore and filter all 25 products with live price filters in the **'Knowledge Base & Catalog'** tab! Which category would you like to explore?"
        )

    # Catalog Scope Queries
    if any(w in t for w in ["phone", "smartphone", "mobile"]) and any(w in t for w in ["only three", "only 3", "more phones", "how many", "all phones", "other phones", "more available", "where only", "why only"]):
        return (
            "We have a total of **7 smartphones** in our catalog! In addition to the three shown:\n"
            "• **Volt PowerMax 5G** (₹13,999) — 6000mAh battery champion (up to 2.5 days battery life).\n"
            "• **Zenith CamPro 5G** (₹34,999) — Triple 50MP Sony IMX sensors with Optical Image Stabilization (OIS).\n"
            "• **Aura Flagship X** (₹64,999) — Snapdragon 8 Gen 3 with 100x zoom and titanium build.\n"
            "• **Titan Fold Z** (₹1,24,999) — Dual 120Hz foldable screens for ultimate productivity.\n\n"
            "You can browse all 7 smartphones in detail with full specifications under the **'Knowledge Base & Catalog'** tab!"
        )

    # Personal Introduction & Categories
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

    # 1. Telugu Queries
    if any("\u0C00" <= ch <= "\u0C7F" for ch in user_input) or any(w in t for w in ["namaskaram", "namaskaramu", "telugu", "bagundi", "kavali", "chudali", "dharalu", "dharam"]):
        if any(w in t for w in ["phone", "mobile", "ఫోన్", "స్మార్ట్", "speed"]):
            return DEMO_REPLIES["telugu_phone"]
        elif any(w in t for w in ["laptop", "coding", "computer", "లాప్", "కంప్యూటర్"]):
            return DEMO_REPLIES["telugu_laptop"]
        return DEMO_REPLIES["telugu_greeting"]

    # 1.1 Kannada Queries
    if any("\u0C80" <= ch <= "\u0CFF" for ch in user_input) or any(w in t for w in ["namaskara", "kannada", "chennagide", "beku", "nodabeku", "bele", "yavudu"]):
        if any(w in t for w in ["phone", "mobile", "ಫೋನ್", "ಸ್ಮಾರ್ಟ್"]):
            return DEMO_REPLIES["kannada_phone"]
        elif any(w in t for w in ["laptop", "coding", "computer", "ಲ್ಯಾಪ್", "ಕಂಪ್ಯೂಟರ್"]):
            return DEMO_REPLIES["kannada_laptop"]
        return DEMO_REPLIES["kannada_greeting"]

    # 1.2 Hindi Queries
    if any("\u0900" <= ch <= "\u097F" for ch in user_input) or any(w in t for w in ["namaste", "hindi", "kripya", "chahiye", "kitne", "daam", "kimat"]):
        if any(w in t for w in ["phone", "mobile", "फ़ोन", "स्मार्टफोन"]):
            return DEMO_REPLIES["hindi_phone"]
        elif any(w in t for w in ["laptop", "coding", "computer", "लैपटॉप", "कंप्यूटर"]):
            return DEMO_REPLIES["hindi_laptop"]
        return DEMO_REPLIES["hindi_greeting"]

    # 2. English Greeting
    if re.search(r"\b(hello|hi|hey|good morning|good afternoon|greetings)\b", t):
        if not any(kw in t for kw in ["tablet", "laptop", "phone", "price", "budget", "recommend", "under", "need", "looking", "sketching"]):
            return DEMO_REPLIES["greeting"]

    # Recommendations when user has budget or category intent
    has_budget = parse_budget_from_text(user_input) is not None
    detected_cat = detect_category(user_input)
    clean_t = re.sub(r"\b(phone number|mobile number|my phone|contact number)\b", "", t)
    is_phone_query = any(w in clean_t for w in ["phone", "smartphone", "mobile"])
    is_tablet_query = any(w in t for w in ["tablet", "tab", "ipad"])
    is_accessory_query = any(w in t for w in ["keyboard", "mouse", "headphone", "charger", "accessories", "accessory"])

    if recs and (has_budget or is_phone_query or is_tablet_query or is_accessory_query or (detected_cat and detected_cat != "Laptops")):
        return f"Based on your requirements, here are our top catalog recommendations:\n\n{format_recommendations_for_agent(recs)}\n\nWould you like to book a showroom demo to test these in person?"

    # Direct recommendations
    if "which one is best" in t or "which is best" in t or "which should i buy" in t:
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

    if any(w in t for w in ["tablet", "tab", "ipad", "zenith pad", "stylus"]):
        return DEMO_REPLIES["tablets"]

    if any(w in t for w in ["hours", "timings", "timing", "open", "close", "store timing"]):
        return DEMO_REPLIES["store_hours"]

    if any(w in t for w in ["warranty", "guarantee"]):
        return DEMO_REPLIES["warranty_policy"]

    if any(w in t for w in ["deliver", "delivery", "shipping"]):
        return DEMO_REPLIES["delivery_policy"]

    if any(w in t for w in ["emi", "payment", "credit card", "finance"]):
        return DEMO_REPLIES["payment_emi"]

    if any(w in t for w in ["gst", "invoice", "tax", "input credit"]):
        return DEMO_REPLIES["gst_invoice"]

    if any(w in t for w in ["offer", "discount", "deal", "cashback"]):
        return DEMO_REPLIES["offers"]

    if recs:
        return f"Based on your requirements, here are our top catalog recommendations:\n\n{format_recommendations_for_agent(recs)}\n\nWould you like to book a showroom demo to test these in person?"

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
    history: Optional[List[Dict]] = None,
    booking_state: Optional[Dict] = None
) -> Dict:
    """
    Execute one full conversational sales turn with conversation memory,
    accurate product RAG, and multi-step voice appointment booking.
    """
    db = SessionLocal()
    history = history or []
    booking_state = booking_state if booking_state is not None else {}

    try:
        start_t = time.time()
        lower_input = user_input.lower()

        # Language Detection (English, Telugu, Kannada, Hindi)
        if any("\u0C00" <= ch <= "\u0C7F" for ch in user_input) or any(w in lower_input for w in ["namaskaram", "namaskaramu", "telugu", "bagundi", "kavali", "chudali"]):
            language = "te"
        elif any("\u0C80" <= ch <= "\u0CFF" for ch in user_input) or any(w in lower_input for w in ["namaskara", "kannada", "chennagide", "beku", "nodabeku"]):
            language = "kn"
        elif any("\u0900" <= ch <= "\u097F" for ch in user_input) or any(w in lower_input for w in ["namaste", "hindi", "kripya", "chahiye", "kitne", "daam"]):
            language = "hi"
        else:
            language = language or "en"

        # 1. Check Multi-Step Voice Appointment Booking State Machine
        booking_result = None
        ics_data = None
        appt_reply, b_res, ics_c = _handle_voice_appointment_flow(user_input, history, booking_state, language)
        if b_res:
            booking_result = b_res
        if ics_c:
            ics_data = ics_c

        # 2. RAG Context Retrieval & Product Recommendations
        rag_sources = rag_engine.retrieve(user_input, top_k=3)
        rag_context = rag_engine.get_context(user_input, top_k=3)
        recs = recommend_products(user_input, max_results=3)

        # 3. Sentiment Analysis
        sentiment_label, sentiment_score = analyze_sentiment(user_input)

        # 4. Lead Extraction & BANT Scoring
        all_text = " ".join([h.get("content", "") for h in history]) + " " + user_input
        extracted_lead: ExtractedLead = extract_lead_from_conversation(all_text)

        # 5. Determine Agent Reply
        agent_reply = ""
        mode = "Demo Mode"

        if appt_reply:
            # Multi-step appointment booking takes precedence
            agent_reply = appt_reply
            mode = "Appointment Assistant"
        else:
            # Check direct product question answering first
            direct_ans = answer_direct_product_question(user_input, history)
            if direct_ans:
                agent_reply = direct_ans
                mode = "RAG Catalog Knowledge"
            else:
                client = get_ai_client()
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

        # 6. Legacy/Direct booking fallback for single-turn testing compatibility (if test provides explicit full contact + slot in one shot)
        if not booking_result and bool(re.search(r"\b(book|booking|schedule|reserve|showroom visit)\b", lower_input)) and bool(re.search(r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|p\.m\.|a\.m\.)|\bat\s+\d{1,2}\b)", lower_input)) and (extracted_lead.email or extracted_lead.phone):
            target_date, target_time_str = parse_natural_datetime(user_input)
            cust_name = extracted_lead.name or "Valued Customer"
            cust_email = extracted_lead.email or "customer@example.com"
            prod_name = recs[0]["product_name"] if recs else "Electronics Consultation"
            city = extracted_lead.city or "Mumbai"

            ok, b_msg, appt = book_appointment_in_db(
                db=db,
                customer_name=cust_name,
                customer_email=cust_email,
                customer_phone=extracted_lead.phone,
                date_val=target_date,
                time_str=target_time_str,
                appointment_type="Store Visit",
                interested_product=prod_name,
                city=city,
                notes="Booked via AI Voice Agent"
            )
            if ok:
                booking_result = {
                    "status": "success",
                    "appointment_id": appt.appointment_id,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "time": target_time_str,
                    "message": b_msg
                }
                ics_data = generate_ics_content(cust_name, target_date, target_time_str, prod_name)
                agent_reply = (
                    f"Thank you, {cust_name}! Your showroom appointment has been successfully confirmed for "
                    f"**{target_date.strftime('%d %B %Y')} at {target_time_str}** at our {city} showroom for **{prod_name}**. "
                    f"Your Booking ID is **{appt.appointment_id}**."
                )

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
            "booking_state": booking_state,
            "latency_ms": latency_ms
        }
    finally:
        db.close()
