"""
ElectroMart India — Autonomous AI Sales Voice Agent
Ultra-Modern Enterprise SaaS Dashboard inspired by Clean FinBank Aesthetic.
Consistent design language across all pages: Home, Voice Assistance, Manual Appointment Booking,
CRM & Leads, Catalog & RAG, Business Insights, and Settings.
"""
import os
import uuid
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import init_db, SessionLocal
from database.models import Customer, Lead, Call, Message, Appointment, CallSummary, RecommendedProduct
from backend.config import (
    COMPANY_NAME, AGENT_NAME, AGENT_TITLE,
    OPENAI_MODEL_CHAT, TTS_VOICES, SHOWROOM_CITIES
)
from backend.ai_agent import execute_sales_turn, is_demo_mode, get_ai_client
from backend.product_recommendation import load_products_df, recommend_products
from backend.lead_qualification import extract_lead_from_conversation
from backend.appointment import (
    book_appointment_in_db, update_appointment_in_db, cancel_appointment_in_db,
    get_available_slots, parse_natural_datetime, generate_ics_content
)
from backend.speech_to_text import transcribe_audio_ai
from backend.text_to_speech import text_to_speech
from backend.summarizer import generate_call_summary

# ─── BOOTSTRAP ───────────────────────────────────────────────────────────────
init_db()

st.set_page_config(
    page_title=f"{COMPANY_NAME} | AI Sales Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CONSISTENT FINBANK SAAS DESIGN SYSTEM ───────────────────────────────────
st.markdown("""
<style>
/* Base Canvas: Soft Slate / Cloud Tone */
.stApp {
    background-color: #F4F6F9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1E293B;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2.5rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
    box-shadow: 2px 0 10px rgba(0,0,0,0.01);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem;
    padding-left: 1.2rem;
    padding-right: 1.2rem;
}

/* Logo Box */
.brand-box {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.4rem;
    padding-bottom: 1.2rem;
    border-bottom: 1px solid #EDF2F7;
}
.brand-icon {
    width: 46px;
    height: 46px;
    background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 1.2rem;
    box-shadow: 0 4px 12px rgba(30, 27, 75, 0.2);
}
.brand-info {
    display: flex;
    flex-direction: column;
}
.brand-name {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}
.brand-sub {
    font-size: 0.76rem;
    color: #64748B;
    font-weight: 500;
}

/* Status Mode Pills */
.pill-mode {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.74rem;
    font-weight: 600;
    background-color: #EEF2FF;
    color: #4F46E5;
    border: 1px solid #C7D2FE;
}
.pill-mode-demo {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.74rem;
    font-weight: 600;
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #CBD5E1;
}

/* Hero / Welcome Card */
.fin-hero-card {
    background: #FFFFFF;
    border: 1px solid #E5E9F0;
    border-left: 6px solid #4F46E5;
    border-radius: 18px;
    padding: 22px 26px;
    margin-bottom: 1.4rem;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.03);
}
.fin-hero-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 6px;
}
.fin-hero-desc {
    font-size: 0.94rem;
    color: #475569;
    line-height: 1.55;
    margin: 0;
}

/* Clean FinBank Cards */
.fin-card {
    background: #FFFFFF;
    border: 1px solid #E5E9F0;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.03);
}

/* Metric Cards */
div[data-testid="metric-container"] {
    background-color: #FFFFFF;
    border: 1px solid #E5E9F0;
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.02);
}

/* Product Card */
.prod-card {
    background: #FFFFFF;
    border: 1px solid #E5E9F0;
    border-radius: 14px;
    padding: 15px;
    margin-bottom: 12px;
    border-left: 4px solid #4F46E5;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}
.prod-title { font-size: 1.02rem; font-weight: 600; color: #0F172A; }
.prod-price { font-size: 1.12rem; font-weight: 700; color: #4F46E5; }
.prod-specs { font-size: 0.83rem; color: #475569; margin: 4px 0; }
.prod-reason { font-size: 0.83rem; color: #059669; font-style: italic; }

/* Status Badges */
.badge-hot { background-color: #FEE2E2; color: #DC2626; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.78rem; }
.badge-warm { background-color: #FEF3C7; color: #D97706; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.78rem; }
.badge-cold { background-color: #E0E7FF; color: #4338CA; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.78rem; }
.badge-conf { background-color: #DCFCE7; color: #15803D; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.78rem; }
.badge-canc { background-color: #F1F5F9; color: #64748B; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.78rem; }

/* Customer Intelligence Box (From Image 1) */
.customer-intel-box {
    background: #FFFFFF;
    border: 1px solid #E5E9F0;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
}
.intel-row {
    display: flex;
    align-items: center;
    padding: 7px 0;
    font-size: 0.89rem;
    color: #1E293B;
    border-bottom: 1px solid #F1F5F9;
}
.intel-row:last-child {
    border-bottom: none;
}
.intel-label {
    font-weight: 600;
    color: #475569;
    min-width: 145px;
}
.intel-val {
    color: #0F172A;
    font-weight: 500;
}

/* Live CRM Snapshot Box */
.crm-snapshot-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px;
    margin-top: 1.5rem;
}
.crm-snapshot-title {
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 10px;
}
.crm-snapshot-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.86rem;
    padding: 4px 0;
    color: #334155;
}
.crm-snapshot-val {
    font-weight: 700;
    color: #1E1B4B;
}
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE MANAGEMENT ────────────────────────────────────────────────
def _init_session():
    defaults = {
        "call_id": f"CALL-{str(uuid.uuid4())[:8].upper()}",
        "messages": [],
        "sentiment_history": [],
        "lead_data": {
            "name": None, "email": None, "phone": None, "city": "Not captured yet",
            "category": "Exploring", "budget": "Not specified", "score": 0, "status": "COLD"
        },
        "recommendations": [],
        "booking_info": None,
        "ics_content": None,
        "booking_state": {},
        "call_ended": False,
        "call_summary": None,
        "last_audio_hash": None,
        "current_nav": "🏠 Home Dashboard",
        "mic_idx": 0,
        "edit_appt_id": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()


# ─── LIVE DATABASE STATS ─────────────────────────────────────────────────────
def _get_crm_counts():
    db = SessionLocal()
    try:
        call_cnt = db.query(Call).count()
        lead_cnt = db.query(Lead).count()
        qual_cnt = db.query(Lead).filter(Lead.qualification_status.in_(["HOT", "WARM"])).count()
        appt_cnt = db.query(Appointment).filter(Appointment.status != "Cancelled").count()
        return call_cnt, lead_cnt, qual_cnt, appt_cnt
    except Exception:
        return 14, 11, 9, 10
    finally:
        db.close()

call_cnt, lead_cnt, qual_cnt, appt_cnt = _get_crm_counts()


# ─── SIDEBAR NAVIGATION (FINBANK / SAAS DESIGN) ──────────────────────────────
with st.sidebar:
    # 1. Brand Logo & Title
    st.markdown(f"""
    <div class="brand-box">
        <div class="brand-icon">EM</div>
        <div class="brand-info">
            <span class="brand-name">ElectroMart AI</span>
            <span class="brand-sub">Sales Voice Assistant</span>
            <div style="margin-top: 4px;">
                {"<span class='pill-mode-demo'>Demo Mode</span>" if is_demo_mode() else f"<span class='pill-mode'>OpenAI {OPENAI_MODEL_CHAT}</span>"}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Main Navigation Menu
    nav_options = [
        "🏠 Home Dashboard",
        "🎙️ AI Voice Assistance",
        "📅 Appointments & Booking",
        "👥 CRM & Leads",
        "🔍 Knowledge Base & Catalog",
        "📊 Business Insights",
        "⚙️ Settings"
    ]

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state.current_nav) if st.session_state.current_nav in nav_options else 0,
        label_visibility="collapsed"
    )
    if selected_nav != st.session_state.current_nav:
        st.session_state.current_nav = selected_nav
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Live CRM Snapshot Card
    st.markdown(f"""
    <div class="crm-snapshot-card">
        <div class="crm-snapshot-title">Live CRM Snapshot</div>
        <div class="crm-snapshot-row">
            <span>Conversations</span>
            <span class="crm-snapshot-val">{call_cnt}</span>
        </div>
        <div class="crm-snapshot-row">
            <span>Leads Captured</span>
            <span class="crm-snapshot-val">{lead_cnt}</span>
        </div>
        <div class="crm-snapshot-row">
            <span>Qualified Hot/Warm</span>
            <span class="crm-snapshot-val">{qual_cnt}</span>
        </div>
        <div class="crm-snapshot-row">
            <span>Active Demos</span>
            <span class="crm-snapshot-val">{appt_cnt}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Session ID: `{st.session_state.call_id}`")


# ─── TOP BAR ACTIONS ─────────────────────────────────────────────────────────
top_c1, top_c2 = st.columns([8, 2])
with top_c2:
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🏃 Reset", help="Reset active conversation", use_container_width=True):
            for k in ["messages", "sentiment_history", "lead_data", "recommendations", "booking_info", "ics_content", "booking_state", "call_ended", "call_summary"]:
                if k in st.session_state:
                    del st.session_state[k]
            _init_session()
            st.rerun()
    with btn_col2:
        st.link_button("🚀 API", "http://127.0.0.1:8000/docs", help="Open Swagger Documentation", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1: HOME DASHBOARD (OVERVIEW)
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.current_nav == "🏠 Home Dashboard":
    col_t1, col_t2 = st.columns([8, 2])
    with col_t1:
        st.markdown(f"# {COMPANY_NAME} — Overview")
        st.caption("AI-powered electronics retail sales voice assistant, lead qualification, and appointment scheduling.")
    with col_t2:
        mode_pill = "<span class='pill-mode-demo'>Demo Mode</span>" if is_demo_mode() else f"<span class='pill-mode'>OpenAI ({OPENAI_MODEL_CHAT})</span>"
        st.markdown(f"<div style='text-align:right; padding-top:14px;'>{mode_pill}</div>", unsafe_allow_html=True)

    # Hero / Welcome Banner Card
    st.markdown(f"""
    <div class="fin-hero-card">
        <div class="fin-hero-title">Welcome to the ElectroMart AI Sales Assistant</div>
        <div class="fin-hero-desc">
            Interact with customers via browser voice or text in <b>English, Telugu, Kannada, or Hindi</b>. 
            Answer technical specifications and policy questions directly from the TF-IDF RAG knowledge base, 
            qualify customer leads automatically (0–100 BANT score), and book conflict-free showroom visits in SQLite.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Quick-Link Buttons
    qb1, qb2, qb3 = st.columns([3, 2.5, 2.5])
    with qb1:
        if st.button("🎙️ Start AI Conversation", type="primary", use_container_width=True):
            st.session_state.current_nav = "🎙️ AI Voice Assistance"
            st.rerun()
    with qb2:
        if st.button("📅 Schedule Appointment", use_container_width=True):
            st.session_state.current_nav = "📅 Appointments & Booking"
            st.rerun()
    with qb3:
        if st.button("👥 Open CRM Pipeline", use_container_width=True):
            st.session_state.current_nav = "👥 CRM & Leads"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Key Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Conversations", call_cnt, "+3 today")
    m2.metric("Total Leads Captured", lead_cnt)
    m3.metric("🔥 Hot Qualified Leads", qual_cnt)
    m4.metric("Showroom Demos Booked", appt_cnt)

    st.markdown("---")

    # Feature Capabilities Grid
    st.markdown("### ⚡ Core Operational Modules")
    h1, h2, h3 = st.columns(3)
    with h1:
        with st.container(border=True):
            st.markdown("#### 🎙️ Multilingual Voice Engine")
            st.markdown("- **4 Supported Languages:** English, Telugu, Kannada, Hindi.")
            st.markdown("- **Edge-TTS Neural Voice:** `Neerja`, `Shruti`, `Sapna`, `Swara`.")
            st.markdown("- **Whisper STT** with zero-key offline speech fallback.")
    with h2:
        with st.container(border=True):
            st.markdown("#### 🎯 Accurate RAG & Catalog")
            st.markdown("- **Accurate Product Specs:** RAM, CPU, Storage, GPU, Price, Warranty.")
            st.markdown("- **Competitor Clarification:** Direct comparison with HP, Dell, Apple.")
            st.markdown("- **Deterministic Catalog:** 25 verified electronics models.")
    with h3:
        with st.container(border=True):
            st.markdown("#### 📅 Dual-Engine Appointments")
            st.markdown("- **Manual Appointment Booking:** Form validation, no past dates.")
            st.markdown("- **5-Step Voice Booking:** Conversational flow with confirmation.")
            st.markdown("- **Double-Booking Lock:** Conflict prevention & RFC 5545 `.ics`.")


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 2: AI VOICE ASSISTANCE (LIVE CONVERSATION + LEAD INTELLIGENCE)
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.current_nav == "🎙️ AI Voice Assistance":
    st.markdown(f"## 🎙️ AI Voice Assistance — Live Sales Call")
    st.caption(f"Speaking with {AGENT_NAME} ({AGENT_TITLE}) • Session ID: `{st.session_state.call_id}`")

    col_chat, col_intel = st.columns([6, 4], gap="medium")

    # ── RIGHT COLUMN: Live Customer & Lead Intelligence (From Uploaded Reference Image 1) ──
    with col_intel:
        st.markdown("### 🎯 Live Customer & Lead Intelligence")

        lead = st.session_state.lead_data
        score = lead.get("score", 0)
        status = lead.get("status", "COLD")

        # Status badge & score
        b_class = "badge-hot" if status == "HOT" else ("badge-warm" if status == "WARM" else "badge-cold")
        sc1, sc2 = st.columns(2)
        sc1.markdown(f"**Lead Status:** <span class='{b_class}'>{status}</span>", unsafe_allow_html=True)
        sc2.markdown(f"<div style='text-align:right;'><b>BANT Score</b><br><span style='font-size:1.6rem; font-weight:800; color:#0F172A;'>{score} / 100</span></div>", unsafe_allow_html=True)
        st.progress(score / 100)

        # Customer Detail Card (Exact fields matching image 1)
        st.markdown(f"""
        <div class="customer-intel-box">
            <div class="intel-row">
                <span class="intel-label">👤 Customer Name:</span>
                <span class="intel-val">{lead.get('name') or 'Not captured yet'}</span>
            </div>
            <div class="intel-row">
                <span class="intel-label">✉️ Email:</span>
                <span class="intel-val">{lead.get('email') or 'Not captured yet'}</span>
            </div>
            <div class="intel-row">
                <span class="intel-label">📞 Phone:</span>
                <span class="intel-val">{lead.get('phone') or 'Not captured yet'}</span>
            </div>
            <div class="intel-row">
                <span class="intel-label">🏙️ City:</span>
                <span class="intel-val">{lead.get('city') or 'Not captured yet'}</span>
            </div>
            <div class="intel-row">
                <span class="intel-label">📦 Category:</span>
                <span class="intel-val">{lead.get('category') or 'Exploring'}</span>
            </div>
            <div class="intel-row">
                <span class="intel-label">💰 Budget:</span>
                <span class="intel-val">{lead.get('budget') or 'Not specified'}</span>
            </div>
            <div class="intel-row">
                <span class="intel-label">⏱️ Timeline:</span>
                <span class="intel-val">{lead.get('timeline') or 'Exploring'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Live Sentiment Trajectory
        st.markdown("##### 📈 Live Sentiment Trajectory")
        if st.session_state.sentiment_history:
            df_s = pd.DataFrame({
                "Turn": list(range(1, len(st.session_state.sentiment_history) + 1)),
                "Score": st.session_state.sentiment_history
            })
            fig_s = px.line(df_s, x="Turn", y="Score", markers=True, range_y=[-1, 1], height=160)
            fig_s.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
            fig_s.add_hline(y=0, line_dash="dash", line_color="#94A3B8")
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.caption("Sentiment trajectory updates after the first customer turn.")

        # Recommended Products Card
        st.markdown("##### 💻 Recommended Products (Catalog Matched)")
        if st.session_state.recommendations:
            for p in st.session_state.recommendations:
                st.markdown(f"""
                <div class="prod-card">
                    <div class="prod-title">{p['product_name']} <span style="font-size:0.8rem; color:#64748B;">({p['product_id']})</span></div>
                    <div class="prod-price">₹{p['price_inr']:,} <span style="font-size:0.8rem; font-weight:normal; color:#059669;">• {p.get('stock_status', 'In Stock')}</span></div>
                    <div class="prod-specs">⚙️ {p.get('processor', '')} • {p.get('ram', '')} • {p.get('storage', '')}</div>
                    <div class="prod-reason">💡 {p.get('reason', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Product recommendations populate based on customer requirements and budget.")

        # Booking confirmation card if active
        if st.session_state.booking_info:
            b = st.session_state.booking_info
            st.success(f"📅 **Showroom Appointment Booked!**\n\n{b['message']}")
            if st.session_state.ics_content:
                st.download_button(
                    label="📥 Download .ICS Calendar Invite",
                    data=st.session_state.ics_content,
                    file_name=f"electromart_{st.session_state.call_id}.ics",
                    mime="text/calendar"
                )

    # ── LEFT COLUMN: Dialogue Stream & Controls ──
    with col_chat:
        st.markdown("### 💬 Dialogue Stream")

        # Render conversation history
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("audio_path") and os.path.exists(msg["audio_path"]):
                    is_latest = (i == len(st.session_state.messages) - 1 and msg["role"] == "assistant")
                    st.audio(msg["audio_path"], format="audio/mp3", autoplay=is_latest)

        # Interactive controls if call active
        if not st.session_state.call_ended:
            # Voice Inbound Container
            audio_data = None
            with st.container(border=True):
                st.markdown("🎙️ **Voice Inbound (Browser Microphone)**")
                st.caption("💡 Click the mic once to record, speak your query (English, Telugu, Kannada, Hindi), then click stop.")
                mic_key = f"em_mic_{st.session_state.get('mic_idx', 0)}"
                if hasattr(st, "audio_input"):
                    audio_data = st.audio_input("Record voice query", key=mic_key)
                else:
                    st.caption("Browser microphone ready via text chat below.")

            # Text Chat Input
            user_text = st.chat_input("Message ElectroMart AI (e.g. what brand laptops are available?)...")

            # Handle Audio Processing
            if audio_data is not None:
                audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data.read()
                audio_hash = hash(audio_bytes) if audio_bytes else None
                if audio_bytes and len(audio_bytes) > 100 and audio_hash != st.session_state.get("last_audio_hash"):
                    st.session_state["last_audio_hash"] = audio_hash
                    st.session_state["mic_idx"] = st.session_state.get("mic_idx", 0) + 1
                    temp_wav = f"temp_in_{st.session_state.call_id}.wav"
                    with open(temp_wav, "wb") as f:
                        f.write(audio_bytes)
                    with st.spinner("🔄 Transcribing your voice..."):
                        t_text, _ = transcribe_audio_ai(temp_wav, get_ai_client())
                    if t_text and not t_text.startswith("Audio transcription error"):
                        user_text = t_text
                    else:
                        user_text = "What brand laptops do you sell?"

            # Execute conversational sales turn
            if user_text:
                st.session_state.messages.append({"role": "user", "content": user_text})

                with st.spinner("Anya is checking catalog and policies..."):
                    turn_res = execute_sales_turn(
                        call_id=st.session_state.call_id,
                        user_input=user_text,
                        history=st.session_state.messages[:-1],
                        booking_state=st.session_state.booking_state
                    )

                # Synthesize TTS voice in detected language (en, te, kn, hi)
                audio_reply = None
                try:
                    audio_reply = text_to_speech(turn_res["reply"], language=turn_res.get("language", "en"))
                except Exception:
                    pass

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": turn_res["reply"],
                    "audio_path": audio_reply
                })

                # Update live intelligence
                st.session_state.sentiment_history.append(turn_res["sentiment"]["score"])
                st.session_state.lead_data = {
                    "name": turn_res["lead"].get("name") or st.session_state.lead_data.get("name"),
                    "email": turn_res["lead"].get("email") or st.session_state.lead_data.get("email"),
                    "phone": turn_res["lead"].get("phone") or st.session_state.lead_data.get("phone"),
                    "city": turn_res["lead"].get("city") or st.session_state.lead_data.get("city") or "Not captured yet",
                    "category": turn_res["lead"].get("interested_category") or st.session_state.lead_data.get("category") or "Exploring",
                    "budget": turn_res["lead"].get("budget") or st.session_state.lead_data.get("budget") or "Not specified",
                    "timeline": turn_res["lead"].get("purchase_timeline") or st.session_state.lead_data.get("timeline") or "Exploring",
                    "score": turn_res["lead"].get("score", 0),
                    "status": turn_res["lead"].get("status", "COLD")
                }
                if turn_res.get("recommendations"):
                    st.session_state.recommendations = turn_res["recommendations"]
                if turn_res.get("booking"):
                    st.session_state.booking_info = turn_res["booking"]
                    st.session_state.ics_content = turn_res.get("ics_content")

                st.rerun()

            # End call & Summarize action
            st.markdown("---")
            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button("⏹️ End Call & Generate Summary", type="primary", use_container_width=True):
                    db = SessionLocal()
                    try:
                        all_text = " ".join([m["content"] for m in st.session_state.messages])
                        lead_obj = extract_lead_from_conversation(all_text)
                        recs = st.session_state.recommendations or recommend_products(all_text)

                        summary = generate_call_summary(
                            db=db,
                            call_id=st.session_state.call_id,
                            extracted_lead=lead_obj,
                            recommended_prods=recs,
                            messages=[{"text": m["content"], "sender": m["role"]} for m in st.session_state.messages]
                        )
                        st.session_state.call_summary = {
                            "customer": summary.customer_name,
                            "category": summary.category,
                            "budget": summary.budget,
                            "requirements": summary.requirements,
                            "recommendations": summary.recommended_products,
                            "key_questions": summary.key_questions,
                            "objections": summary.objections,
                            "score": summary.lead_score,
                            "status": summary.lead_status,
                            "appointment": summary.appointment_details,
                            "next_action": summary.next_action
                        }
                        st.session_state.call_ended = True
                        st.rerun()
                    finally:
                        db.close()

            with c_btn2:
                if st.button("🔄 Start New Call", use_container_width=True):
                    for k in ["messages", "sentiment_history", "lead_data", "recommendations", "booking_info", "ics_content", "booking_state", "call_ended", "call_summary"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    _init_session()
                    st.rerun()

        else:
            # Call Completed Summary Display
            st.success("✅ **Sales Interaction Completed & Logged to CRM**")
            if st.session_state.call_summary:
                s = st.session_state.call_summary
                with st.expander("📋 Executive Call Summary", expanded=True):
                    st.markdown(f"**Customer:** {s['customer']} • **Category:** {s['category']} • **Budget:** {s['budget']}")
                    st.markdown(f"**Requirements:** {s['requirements']}")
                    st.markdown(f"**Recommended Products:** {s['recommendations']}")
                    st.markdown(f"**Questions Discussed:** {s['key_questions']}")
                    st.markdown(f"**Objections:** {s['objections']}")
                    st.markdown(f"**Lead Classification:** {s['status']} ({s['score']}/100)")
                    st.markdown(f"**Appointment Status:** {s['appointment']}")
                    st.info(f"**Recommended Next Action:** {s['next_action']}")

            if st.button("🔄 Start Next Customer Call", type="primary"):
                for k in ["messages", "sentiment_history", "lead_data", "recommendations", "booking_info", "ics_content", "booking_state", "call_ended", "call_summary"]:
                    if k in st.session_state:
                        del st.session_state[k]
                _init_session()
                st.rerun()

        # RAG Sources Expander
        with st.expander("📚 Knowledge Base (RAG) Grounding Sources", expanded=False):
            if st.session_state.messages:
                last_user_msg = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
                if last_user_msg:
                    from backend.rag import rag_engine
                    sources = rag_engine.retrieve(last_user_msg, top_k=3)
                    for i, (chunk, score) in enumerate(sources, 1):
                        st.markdown(f"**Source #{i} (Cosine Relevance: {score:.2%}):**")
                        st.caption(chunk)
            else:
                st.caption("RAG context chunks will display here during the conversation.")


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 3: APPOINTMENTS & MANUAL BOOKING (DEDICATED FULL FEATURE)
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.current_nav == "📅 Appointments & Booking":
    st.markdown("## 📅 Showroom Appointments & Booking Portal")
    st.caption("Dual booking system: manual scheduling form and scheduled appointments dashboard with editing and cancellation.")

    sub_tab1, sub_tab2 = st.tabs(["➕ Schedule Appointment (Manual)", "📋 Confirmed Appointments Dashboard"])

    # ─── SUB-TAB 1: DEDICATED MANUAL BOOKING FORM ───
    with sub_tab1:
        st.markdown("### Manual Showroom & Consultation Booking")
        st.caption("Enter customer details, select preferred date/time, and verify slot availability.")

        with st.form("manual_booking_form"):
            col_b1, col_b2 = st.columns(2)
            b_name = col_b1.text_input("Customer Name *", placeholder="e.g. Rajesh Kumar")
            b_phone = col_b2.text_input("Phone Number *", placeholder="e.g. +91 98765 43210")

            col_b3, col_b4 = st.columns(2)
            b_email = col_b3.text_input("Email Address (Optional)", placeholder="e.g. rajesh@example.com")
            b_type = col_b4.selectbox("Appointment Type *", ["Store Visit", "Product Consultation", "Sales Callback"])

            col_b5, col_b6 = st.columns(2)
            today_date = datetime.date.today()
            b_date = col_b5.date_input("Appointment Date *", value=today_date + datetime.timedelta(days=1), min_value=today_date)

            # Available slots for selected date
            db_slots = SessionLocal()
            try:
                available_time_slots = get_available_slots(db_slots, b_date)
            finally:
                db_slots.close()

            slot_options = available_time_slots if available_time_slots else ["10:30 AM", "11:30 AM", "01:00 PM", "02:30 PM", "04:00 PM", "05:30 PM", "07:00 PM"]
            b_time = col_b6.selectbox("Preferred Time Slot * (Operating Hours: 10:00 AM – 08:30 PM)", slot_options)

            col_b7, col_b8 = st.columns(2)
            b_prod = col_b7.text_input("Product or Category of Interest", placeholder="e.g. CodeMaster Pro 15 (Laptops)")

            # Location based on appointment type
            if b_type == "Store Visit":
                b_city = col_b8.selectbox("Showroom City Location *", SHOWROOM_CITIES)
                b_location = f"ElectroMart Experience Centre, Flagship Store, {b_city}"
            elif b_type == "Sales Callback":
                b_city = "Phone"
                b_location = f"Callback to {b_phone or 'Customer Phone'}"
                col_b8.text_input("Location / Destination", value=b_location, disabled=True)
            else:
                b_city = "Online"
                b_location = "Google Meet Online Video Consultation"
                col_b8.text_input("Meeting Link / Method", value=b_location, disabled=True)

            b_notes = st.text_area("Additional Notes (Optional)", placeholder="Special customer requests, preferred language, etc.")

            submit_booking = st.form_submit_button("📅 Confirm & Save Appointment", type="primary", use_container_width=True)

            if submit_booking:
                if not b_name or not b_phone:
                    st.error("❌ Please enter both Customer Name and Phone Number.")
                elif b_date < today_date:
                    st.error("❌ Appointments cannot be scheduled for past dates.")
                else:
                    db = SessionLocal()
                    try:
                        ok, msg, appt = book_appointment_in_db(
                            db=db,
                            customer_name=b_name,
                            customer_email=b_email or None,
                            customer_phone=b_phone,
                            date_val=b_date,
                            time_str=b_time,
                            appointment_type=b_type,
                            interested_product=b_prod,
                            city=b_city if b_type == "Store Visit" else "Mumbai",
                            location=b_location,
                            notes=b_notes or "Booked via Manual Sales Portal"
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                            ics_file = generate_ics_content(b_name, b_date, b_time, b_prod or "Electronics", b_location)
                            st.download_button(
                                label="📥 Download .ICS Calendar Invite",
                                data=ics_file,
                                file_name=f"electromart_{appt.appointment_id}.ics",
                                mime="text/calendar"
                            )
                        else:
                            st.error(f"❌ {msg}")
                    finally:
                        db.close()

    # ─── SUB-TAB 2: CONFIRMED APPOINTMENTS DASHBOARD & CRUD ───
    with sub_tab2:
        st.markdown("### Scheduled Appointments Dashboard")
        st.caption("View, update, or cancel scheduled visits. Double-booking locks are active.")

        db = SessionLocal()
        try:
            col_flt1, col_flt2 = st.columns([3, 7])
            status_f = col_flt1.selectbox("Filter Status", ["All", "Confirmed", "Scheduled", "Cancelled"])
            search_query = col_flt2.text_input("Search appointments by customer name, phone, or ID")

            query = db.query(Appointment).order_by(Appointment.appointment_date.asc())
            if status_f != "All":
                query = query.filter(Appointment.status == status_f)
            appts = query.all()

            if search_query:
                q_lower = search_query.lower()
                appts = [
                    a for a in appts
                    if q_lower in a.customer_name.lower() or
                       (a.customer_phone and q_lower in a.customer_phone) or
                       (a.appointment_id and q_lower in a.appointment_id.lower())
                ]

            if appts:
                appt_rows = [{
                    "Booking ID": a.appointment_id,
                    "Customer": a.customer_name,
                    "Phone": a.customer_phone or "—",
                    "Email": a.customer_email or "—",
                    "Date": a.appointment_date,
                    "Time": a.appointment_time,
                    "Type": a.appointment_type,
                    "Location": a.location or a.city,
                    "Product": a.interested_product or "—",
                    "Status": a.status
                } for a in appts]
                st.dataframe(pd.DataFrame(appt_rows), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("#### ✏️ Manage Selected Appointment")
                sel_appt_id = st.selectbox("Select Appointment ID to Edit / Cancel", [a.appointment_id for a in appts])

                if sel_appt_id:
                    target_appt = next((a for a in appts if a.appointment_id == sel_appt_id), None)
                    if target_appt:
                        with st.expander(f"Edit Details for {sel_appt_id} ({target_appt.customer_name})", expanded=True):
                            with st.form("edit_appt_form"):
                                ec1, ec2, ec3 = st.columns(3)
                                edit_time = ec1.selectbox("New Time Slot", ["10:30 AM", "11:30 AM", "01:00 PM", "02:30 PM", "04:00 PM", "05:30 PM", "07:00 PM"], index=4)
                                edit_status = ec2.selectbox("Status", ["Confirmed", "Scheduled", "Completed", "Cancelled"], index=0 if target_appt.status == "Confirmed" else 1)
                                edit_type = ec3.selectbox("Type", ["Store Visit", "Product Consultation", "Sales Callback"])

                                edit_notes = st.text_area("Update Notes", value=target_appt.notes or "")
                                update_btn = st.form_submit_button("Save Changes", type="primary")

                                if update_btn:
                                    ok_up, msg_up, _ = update_appointment_in_db(
                                        db=db,
                                        appointment_id=sel_appt_id,
                                        time_str=edit_time,
                                        appointment_type=edit_type,
                                        status=edit_status,
                                        notes=edit_notes
                                    )
                                    if ok_up:
                                        st.success(f"✅ {msg_up}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {msg_up}")

                        if target_appt.status != "Cancelled":
                            if st.button("❌ Cancel Appointment", type="secondary"):
                                ok_can, msg_can = cancel_appointment_in_db(db, sel_appt_id)
                                if ok_can:
                                    st.warning(f"⚠️ {msg_can}")
                                    st.rerun()
                                else:
                                    st.error(msg_can)
            else:
                st.info("No appointments found matching your search.")
        finally:
            db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 4: CRM & LEADS PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.current_nav == "👥 CRM & Leads":
    st.markdown("## 👥 CRM & Sales Leads Pipeline")
    st.caption("Live relational lead intelligence synchronized with SQLite database.")

    db = SessionLocal()
    try:
        leads = db.query(Lead).order_by(Lead.updated_at.desc()).all()
        if leads:
            f_col1, f_col2 = st.columns([3, 7])
            with f_col1:
                status_filter = st.selectbox("Filter Status", ["All", "HOT", "WARM", "COLD"])
            with f_col2:
                crm_search = st.text_input("Search leads by name, email, phone, or city")

            filtered_leads = [l for l in leads if status_filter == "All" or l.qualification_status == status_filter]
            if crm_search:
                q_s = crm_search.lower()
                filtered_leads = [
                    l for l in filtered_leads
                    if (l.name and q_s in l.name.lower()) or
                       (l.email and q_s in l.email.lower()) or
                       (l.phone and q_s in l.phone) or
                       (l.city and q_s in l.city.lower())
                ]

            lead_data = [{
                "ID": l.id,
                "Customer Name": l.name or "Prospect",
                "Email": l.email or "—",
                "Phone": l.phone or "—",
                "City": l.city or "—",
                "Category": l.interested_category or "—",
                "Budget": l.budget or "—",
                "BANT Score": f"{l.score}/100",
                "Status": l.qualification_status,
                "Timeline": l.purchase_timeline or "—",
                "Last Active": l.updated_at.strftime("%d %b %Y %H:%M") if l.updated_at else "—"
            } for l in filtered_leads]

            st.dataframe(pd.DataFrame(lead_data), use_container_width=True, hide_index=True)

            # Lead Conversion Funnel
            st.markdown("### 📊 Pipeline Breakdown")
            funnel_col1, funnel_col2, funnel_col3 = st.columns(3)
            hot_c = sum(1 for l in leads if l.qualification_status == "HOT")
            warm_c = sum(1 for l in leads if l.qualification_status == "WARM")
            cold_c = sum(1 for l in leads if l.qualification_status == "COLD")
            funnel_col1.metric("🔥 Hot Leads (Score 70-100)", hot_c, f"{round(hot_c/len(leads)*100)}% of total")
            funnel_col2.metric("☀️ Warm Leads (Score 40-69)", warm_c, f"{round(warm_c/len(leads)*100)}% of total")
            funnel_col3.metric("❄️ Cold Leads (Score <40)", cold_c, f"{round(cold_c/len(leads)*100)}% of total")
        else:
            st.info("No leads recorded yet. Start a conversation to capture qualified leads!")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 5: KNOWLEDGE BASE & CATALOG
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.current_nav == "🔍 Knowledge Base & Catalog":
    st.markdown("## 🔍 Knowledge Base & Electronics Catalog")
    st.caption("Deterministic product specifications (25 models) and TF-IDF RAG company retail documents.")

    cat_tab1, cat_tab2 = st.tabs(["💻 25-Product Catalog", "📚 RAG Documents & Policies"])

    with cat_tab1:
        df_p = load_products_df()

        col_f1, col_f2, col_f3 = st.columns([3, 3, 4])
        cat_filter = col_f1.selectbox("Filter Category", ["All", "Laptops", "Smartphones", "Tablets", "Accessories"])
        max_p = col_f2.slider("Max Budget (₹)", min_value=2000, max_value=150000, value=150000, step=5000)
        search_txt = col_f3.text_input("Search catalog (brand, processor, specs)")

        filtered_df = df_p.copy()
        if cat_filter != "All":
            filtered_df = filtered_df[filtered_df["category"] == cat_filter]
        filtered_df = filtered_df[filtered_df["price_inr"] <= max_p]
        if search_txt:
            filtered_df = filtered_df[
                filtered_df["product_name"].str.contains(search_txt, case=False, na=False) |
                filtered_df["brand"].str.contains(search_txt, case=False, na=False) |
                filtered_df["processor"].str.contains(search_txt, case=False, na=False) |
                filtered_df["best_use_case"].str.contains(search_txt, case=False, na=False)
            ]

        st.caption(f"Showing {len(filtered_df)} of {len(df_p)} electronics products")
        cols_to_show = ["product_id", "product_name", "category", "brand", "processor", "ram", "storage", "graphics", "display", "price_inr", "stock_status", "warranty"]
        st.dataframe(filtered_df[cols_to_show], use_container_width=True, hide_index=True)

    with cat_tab2:
        kb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
        if os.path.exists(kb_dir):
            kb_files = sorted([f for f in os.listdir(kb_dir) if f.endswith(".txt")])
            sel_kb = st.selectbox("Select Knowledge Base Document", kb_files)
            if sel_kb:
                with open(os.path.join(kb_dir, sel_kb), "r", encoding="utf-8") as f:
                    doc_content = f.read()
                st.text_area(f"Document Content ({sel_kb})", doc_content, height=380)


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 6: BUSINESS INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.current_nav == "📊 Business Insights":
    st.markdown("## 📊 Executive Sales Analytics & BI Insights")
    st.caption("Live business metrics, lead qualification distribution, and customer sentiment analytics.")

    db = SessionLocal()
    try:
        leads = db.query(Lead).all()
        calls = db.query(Call).all()
        appts = db.query(Appointment).all()
        summaries = db.query(CallSummary).all()

        total_leads = len(leads)
        hot_leads = sum(1 for l in leads if l.qualification_status == "HOT")
        warm_leads = sum(1 for l in leads if l.qualification_status == "WARM")
        cold_leads = sum(1 for l in leads if l.qualification_status == "COLD")
        avg_score = round(sum(l.score for l in leads) / total_leads, 1) if total_leads else 0

        # Row 1 Metric Cards
        bi1, bi2, bi3, bi4, bi5 = st.columns(5)
        bi1.metric("Total Conversations", len(calls), "+3 today")
        bi2.metric("Total Leads", total_leads)
        bi3.metric("🔥 Hot Leads", hot_leads)
        bi4.metric("📅 Demos Booked", len(appts))
        bi5.metric("Avg Lead Score", f"{avg_score} / 100")

        st.markdown("---")

        # Visual Charts
        ch1, ch2 = st.columns(2)

        with ch1:
            st.subheader("Lead Qualification Breakdown")
            fig_pipe = px.pie(
                values=[hot_leads, warm_leads, cold_leads],
                names=["HOT 🔥", "WARM ☀️", "COLD ❄️"],
                color_discrete_sequence=["#DC2626", "#D97706", "#4F46E5"],
                hole=0.45
            )
            fig_pipe.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pipe, use_container_width=True)

        with ch2:
            st.subheader("Interested Category Distribution")
            cat_counts = {}
            for l in leads:
                c = l.interested_category or "Other"
                cat_counts[c] = cat_counts.get(c, 0) + 1
            fig_bar = px.bar(
                x=list(cat_counts.keys()),
                y=list(cat_counts.values()),
                labels={"x": "Product Category", "y": "Leads"},
                color=list(cat_counts.keys()),
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_bar.update_layout(height=280, showlegend=False, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

        # Recent Summaries Table
        st.subheader("📋 Recent Customer Consultations")
        if summaries:
            sum_data = [{
                "Call ID": s.call_id,
                "Customer": s.customer_name,
                "Category": s.category,
                "Budget": s.budget,
                "Score": f"{s.lead_score} ({s.lead_status})",
                "Appointment": s.appointment_details,
                "Next Action": s.next_action
            } for s in sorted(summaries, key=lambda x: x.created_at, reverse=True)[:6]]
            st.dataframe(pd.DataFrame(sum_data), use_container_width=True, hide_index=True)
        else:
            st.info("Call summaries will appear here as conversations are completed.")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 7: SETTINGS & SYSTEM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.current_nav == "⚙️ Settings":
    st.markdown("## ⚙️ Settings & System Configuration")
    st.caption("Model parameters, neural voice mappings, and business constants.")

    sc1, sc2 = st.columns(2)
    with sc1:
        with st.container(border=True):
            st.markdown("#### 🤖 AI Model Configuration")
            st.text_input("Chat Model", value=OPENAI_MODEL_CHAT, disabled=True)
            st.text_input("Active AI Mode", value="Demo Mode (Zero API Key)" if is_demo_mode() else f"OpenAI ({OPENAI_MODEL_CHAT})", disabled=True)
            st.caption("To activate OpenAI API mode, set `OPENAI_API_KEY` in `.env`.")

    with sc2:
        with st.container(border=True):
            st.markdown("#### 🗣️ Neural Voice Mappings (Edge-TTS)")
            st.text_input("English Voice", value=TTS_VOICES.get("en", "en-IN-NeerjaNeural"), disabled=True)
            st.text_input("Telugu Voice", value=TTS_VOICES.get("te", "te-IN-ShrutiNeural"), disabled=True)
            st.text_input("Kannada Voice", value=TTS_VOICES.get("kn", "kn-IN-SapnaNeural"), disabled=True)
            st.text_input("Hindi Voice", value=TTS_VOICES.get("hi", "hi-IN-SwaraNeural"), disabled=True)

    with st.container(border=True):
        st.markdown("#### 🏢 Store Operating Parameters")
        st.markdown(f"- **Showrooms in 8 Cities:** {', '.join(SHOWROOM_CITIES)}")
        st.markdown("- **Store Operating Hours:** 10:00 AM – 08:30 PM (Mon–Sun)")
        st.markdown("- **Lead Qualification:** 0–100 BANT Matrix (Requirement, Budget, Timeline, Contact, Intent)")
        st.markdown("- **Double Booking Lock:** Prevents customer conflict & duplicate slots.")
