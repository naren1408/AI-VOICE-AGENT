"""
TechNova Solutions — AI Sales Agent
Supports two modes:
  - Demo Mode (no API key): Keyword-based responses using the RAG knowledge base.
  - OpenAI Mode (with OPENAI_API_KEY): GPT-3.5-turbo / GPT-4 powered responses.
"""
import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from backend.technova_rag import tn_rag
from backend.technova_leads import extract_lead_info, score_lead
from backend.technova_sentiment import analyze_sentiment

load_dotenv()

# --- CONFIGURATION (All in one place for easy live-coding) ---
OPENAI_MODEL    = "gpt-3.5-turbo"       # Change to 'gpt-4' for better quality
MAX_HISTORY     = 10                     # Number of conversation turns to remember
COMPANY_NAME    = "TechNova Solutions"
AGENT_NAME      = "Aria"                 # The AI agent's name

# --- SYSTEM PROMPT (Easily changeable during demo) ---
SYSTEM_PROMPT = f"""
You are {AGENT_NAME}, a professional sales assistant at {COMPANY_NAME}.
Your job is to help potential customers understand our products, answer their questions,
and guide them through the sales process.

GUIDELINES:
1. Answer questions strictly from the provided KNOWLEDGE BASE context.
2. If the answer is not in the knowledge base, say "Let me connect you with a specialist."
3. Be warm, concise, and consultative. Keep responses under 3 sentences.
4. Naturally collect: customer name, company, email, phone, requirements, budget, timeline.
5. If the customer wants a demo, collect their preferred date and time.
6. Always reply in the same language as the customer.

PRODUCTS: TechNova CRM Suite ($99/mo Starter, $299/mo Professional, Enterprise custom)
         TechNova ERP Pro, TechNova Analytics Hub.
"""

# --- DEMO MODE RESPONSES (Realistic keyword-driven replies) ---
DEMO_REPLIES = {
    "greeting":    f"Hi! I'm {AGENT_NAME} from {COMPANY_NAME}. How can I help you today?",
    "pricing":     ("Great question! Our plans start at $99/month (Starter, up to 10 users), "
                    "$299/month (Professional, up to 50 users), and custom Enterprise pricing. "
                    "Which plan size sounds right for your team?"),
    "crm":        ("TechNova CRM Suite helps you manage contacts, track deals, automate follow-ups, "
                    "and view real-time sales reports. It includes iOS and Android apps. "
                    "Would you like to see a live demo?"),
    "erp":        ("TechNova ERP Pro covers financials, inventory, HR, and procurement in one platform. "
                    "It integrates with QuickBooks and Xero. What industry is your business in?"),
    "analytics":  ("TechNova Analytics Hub gives you drag-and-drop dashboards, 150+ report templates, "
                    "and AI-powered sales forecasting. What metrics are most important to your team?"),
    "trial":      ("Absolutely! We offer a free 14-day trial — no credit card required. "
                    "May I have your email address to set that up for you?"),
    "demo":       ("I'd love to arrange a personalized product demo for you! "
                    "What date and time works best? We're available Monday to Friday, 9 AM to 6 PM."),
    "security":   ("TechNova is SOC 2 Type II certified, GDPR and CCPA compliant, "
                    "with AES-256 encryption and 99.9% uptime SLA. Would you like our security whitepaper?"),
    "support":    ("We offer email support for Starter, priority support for Professional, "
                    "and 24/7 dedicated support with a 1-hour SLA for Enterprise customers."),
    "migration":  ("Yes! We provide free data migration assistance for Professional and Enterprise customers. "
                    "Our team handles Salesforce, HubSpot, and CSV imports. What system are you migrating from?"),
    "default":    ("That's a great question. Let me pull up the most relevant information for you. "
                    "Could you share more about your business so I can tailor my answer?"),
}


def _keyword_reply(text: str, context: str) -> str:
    """Generate a demo reply using keywords + RAG context."""
    t = text.lower()
    if any(w in t for w in ["hello", "hi", "hey", "namaste", "good morning", "good afternoon"]):
        return DEMO_REPLIES["greeting"]
    if any(w in t for w in ["price", "cost", "pricing", "how much", "plan", "tier", "rate"]):
        return DEMO_REPLIES["pricing"] + (f"\n\n📚 *From our knowledge base:* {context[:200]}..." if context else "")
    if any(w in t for w in ["crm", "customer relationship", "sales pipeline", "contact management"]):
        return DEMO_REPLIES["crm"]
    if any(w in t for w in ["erp", "enterprise resource", "inventory", "hr", "payroll", "warehouse"]):
        return DEMO_REPLIES["erp"]
    if any(w in t for w in ["analytics", "report", "dashboard", "insight", "forecast", "bi", "business intelligence"]):
        return DEMO_REPLIES["analytics"]
    if any(w in t for w in ["trial", "free", "try", "test", "demo account"]):
        return DEMO_REPLIES["trial"]
    if any(w in t for w in ["demo", "book", "schedule", "appointment", "meeting", "call"]):
        return DEMO_REPLIES["demo"]
    if any(w in t for w in ["security", "compliance", "gdpr", "soc", "encrypt", "hipaa"]):
        return DEMO_REPLIES["security"]
    if any(w in t for w in ["support", "help", "ticket", "sla", "response time"]):
        return DEMO_REPLIES["support"]
    if any(w in t for w in ["migrate", "import", "transfer", "hubspot", "salesforce", "csv"]):
        return DEMO_REPLIES["migration"]
    # Use knowledge base context if available
    if context and len(context) > 50:
        return f"Based on our knowledge base: {context[:300]}... Is there anything specific you'd like to know more about?"
    return DEMO_REPLIES["default"]


def get_openai_client():
    """Return OpenAI client if key is configured, else None."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def is_demo_mode() -> bool:
    """True when no OpenAI API key is configured."""
    return get_openai_client() is None


def chat(user_message: str, history: Optional[List[Dict]] = None) -> Dict:
    """
    Main chat function.
    Returns: {reply, mode, sources, sentiment, lead_info, lead_score, lead_status}
    """
    history = history or []
    # 1. Retrieve relevant knowledge base context
    context = tn_rag.get_context(user_message, top_k=3)
    sources = tn_rag.retrieve(user_message, top_k=3)

    # 2. Analyze user sentiment
    sentiment_label, sentiment_score = analyze_sentiment(user_message)

    # 3. Extract lead information from full conversation
    full_convo = " ".join([m.get("content", "") for m in history]) + " " + user_message
    lead_info = extract_lead_info(full_convo)
    lead_score, lead_status = score_lead(lead_info)

    # 4. Generate reply
    client = get_openai_client()
    if client:
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nKNOWLEDGE BASE:\n{context}"}]
            messages += history[-MAX_HISTORY:]
            messages.append({"role": "user", "content": user_message})
            resp = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, max_tokens=300, temperature=0.7)
            reply = resp.choices[0].message.content.strip()
            mode = "OpenAI Mode"
        except Exception as e:
            reply = _keyword_reply(user_message, context)
            mode = f"Demo Mode (OpenAI error: {str(e)[:60]})"
    else:
        reply = _keyword_reply(user_message, context)
        mode = "Demo Mode"

    return {
        "reply": reply,
        "mode": mode,
        "context": context,
        "sources": [{"text": chunk[:150], "score": score} for chunk, score in sources],
        "sentiment": {"label": sentiment_label, "score": sentiment_score},
        "lead_info": lead_info,
        "lead_score": lead_score,
        "lead_status": lead_status,
    }


def summarize_conversation(messages: List[Dict]) -> Dict:
    """Generate a structured call summary from conversation messages."""
    full_text = "\n".join([f"{m['sender'].upper()}: {m['text']}" for m in messages])
    lead_info = extract_lead_info(full_text)
    lead_score, lead_status = score_lead(lead_info)

    # Detect products discussed
    products = []
    for kw in ["crm", "erp", "analytics"]:
        if kw in full_text.lower():
            products.append({"crm": "TechNova CRM Suite", "erp": "TechNova ERP Pro", "analytics": "TechNova Analytics Hub"}[kw])

    # Sentiment from user messages only
    user_texts = " ".join([m["text"] for m in messages if m.get("sender") == "user"])
    overall_sentiment, _ = analyze_sentiment(user_texts)

    # Next action recommendation
    if lead_status == "Hot":
        next_action = "Send personalised proposal and schedule technical demo within 24 hours."
    elif lead_status == "Warm":
        next_action = "Send product brochure and follow up in 3-5 business days."
    else:
        next_action = "Add to nurture email sequence. Follow up in 2 weeks."

    client = get_openai_client()
    summary_text = ""
    if client:
        try:
            prompt = (f"Summarize this sales call in 2 sentences covering: customer needs, "
                      f"products discussed, and recommended next step.\n\nTranscript:\n{full_text[:1500]}")
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            summary_text = resp.choices[0].message.content.strip()
        except Exception:
            pass

    if not summary_text:
        name = lead_info.get("name") or "the prospect"
        prod = ", ".join(products) or "TechNova Suite"
        summary_text = (f"Conversation with {name} regarding {prod}. "
                        f"Lead classified as {lead_status} with a score of {lead_score}/100.")

    return {
        "summary": summary_text,
        "requirements": lead_info.get("requirements", ""),
        "products_discussed": ", ".join(products) or "General enquiry",
        "sentiment": overall_sentiment,
        "lead_status": lead_status,
        "lead_score": lead_score,
        "next_action": next_action,
        "lead_info": lead_info,
    }
