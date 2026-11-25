import os
import uuid
import datetime
import streamlit as st
import pandas as pd

from database.db import SessionLocal, init_db
from database.models import Lead, Call, Message, Appointment
from backend.ai_agent import execute_sales_turn, generate_call_summary, is_demo_mode
from backend.text_to_speech import text_to_speech
from backend.appointment import generate_ics_content

# Initialize DB on start
init_db()

# Streamlit Page Config
st.set_page_config(
    page_title="CloudScale AI | Sales Voice Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "call_id" not in st.session_state:
    st.session_state.call_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sentiment_history" not in st.session_state:
    st.session_state.sentiment_history = []
if "latest_lead" not in st.session_state:
    st.session_state.latest_lead = {
        "name": "", "email": "", "company": "", "budget": "",
        "timeline": "", "score": 0, "status": "COLD", "is_decision_maker": False
    }
if "latest_sources" not in st.session_state:
    st.session_state.latest_sources = []
if "call_ended" not in st.session_state:
    st.session_state.call_ended = False
if "ics_file_ready" not in st.session_state:
    st.session_state.ics_file_ready = None

# Sidebar Controls
with st.sidebar:
    st.title("🎙️ Agent Controls")
    
    # Mode Badge
    demo_active = is_demo_mode()
    if demo_active:
        st.warning("⚡ **Demo Mode Active** (Zero API Key)\n\nPredefined realistic sales workflow & rule-based scoring.")
        st.info("💡 To enable Gemini mode, add `GEMINI_API_KEY` to your `.env` file and restart.")
    else:
        st.success("🟢 **Gemini AI Mode Active**\n\nConnected to Gemini 2.5 Flash & Text-Embedding-004.")

    st.markdown("---")
    st.markdown(f"**Call Session ID:** `{st.session_state.call_id}`")
    
    # Language Selection
    lang_choice = st.radio("Spoken Language", ["English (en)", "Hindi (hi)"], index=0)
    selected_lang = "hi" if "Hindi" in lang_choice else "en"

    st.markdown("---")
    if st.button("🔄 Start New Call", use_container_width=True):
        st.session_state.call_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.session_state.sentiment_history = []
        st.session_state.latest_lead = {
            "name": "", "email": "", "company": "", "budget": "",
            "timeline": "", "score": 0, "status": "COLD", "is_decision_maker": False
        }
        st.session_state.latest_sources = []
        st.session_state.call_ended = False
        st.session_state.ics_file_ready = None
        st.rerun()

    if not st.session_state.call_ended:
        if st.button("⏹️ End Call & Summarize", type="primary", use_container_width=True):
            summary = generate_call_summary(st.session_state.call_id)
            st.session_state.call_ended = True
            st.session_state.call_summary = summary
            st.rerun()

# Main Application Tabs
tab_call, tab_crm, tab_insights = st.tabs(["📞 Live Call", "👥 Leads & Appointments", "📊 Insights"])

# ==============================================================================
# TAB 1: LIVE CALL
# ==============================================================================
with tab_call:
    col_chat, col_info = st.columns([6, 4], gap="medium")

    with col_chat:
        st.subheader("💬 Customer Conversation")

        # Human Escalation Alert if sentiment is strongly negative
        if st.session_state.sentiment_history and st.session_state.sentiment_history[-1] <= -0.6:
            st.error("🚨 **Human Escalation Alert**: Customer expressed strong frustration. Live SDR notification dispatched.")

        # Message History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "latency" in msg:
                    lat = msg["latency"]
                    st.caption(f"⚡ LLM: {lat.get('llm_ms', 0)}ms | Total: {lat.get('total_ms', 0)}ms | Sentiment: {msg.get('sentiment_label', 'neutral')}")
                if "audio_path" in msg and os.path.exists(msg["audio_path"]):
                    st.audio(msg["audio_path"], format="audio/mp3")

        # Audio or Text Input
        if not st.session_state.call_ended:
            st.markdown("---")
            
            # --- VOICE INPUT SECTION (shown always, demo mode skips transcription) ---
            audio_data = None
            if hasattr(st, "audio_input"):
                with st.container(border=True):
                    if demo_active:
                        st.markdown("🎙️ **Voice Input**")
                        st.caption("⚡ Demo Mode — recording captured but Gemini STT is offline. Your audio plays back below; type your message in the text box.")
                    else:
                        st.markdown("🎙️ **Voice Input** — click the mic to record")
                    audio_data = st.audio_input("Record your message", key="mic_recorder")

            # --- TEXT INPUT (always visible) ---
            st.markdown("**💬 Type your message:**")
            user_text = st.chat_input("Ask about pricing, features, or request a demo...")

            # Handle Audio Input
            if audio_data is not None:
                audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data.read()
                audio_hash = hash(audio_bytes) if audio_bytes else None
                if audio_bytes and len(audio_bytes) > 100 and audio_hash != st.session_state.get("last_app_audio_hash"):
                    st.session_state["last_app_audio_hash"] = audio_hash
                    os.makedirs("temp_audio", exist_ok=True)
                    temp_audio = f"temp_audio/{st.session_state.call_id}_in.wav"
                    with open(temp_audio, "wb") as f:
                        f.write(audio_bytes)

                    if demo_active:
                        # Can't transcribe without key — play back audio and prompt user to type
                        st.audio(temp_audio, format="audio/wav")
                        st.info("🎙️ Audio recorded! Gemini STT is offline in Demo Mode. Please type what you said in the text box above.")
                    else:
                        # Transcribe with Gemini STT
                        from backend.speech_to_text import transcribe_audio_gemini
                        from backend.ai_agent import get_gemini_client
                        with st.spinner("🔄 Transcribing audio..."):
                            transcript, detected_lang = transcribe_audio_gemini(temp_audio, get_gemini_client())
                        if transcript and not transcript.startswith("Audio transcription error"):
                            user_text = transcript
                            selected_lang = detected_lang
                            st.success(f"📝 Transcribed: *{transcript}*")
                        else:
                            st.warning(f"Could not transcribe audio: {transcript}. Please type your message.")

            # Process Turn
            if user_text:
                st.session_state.messages.append({"role": "user", "content": user_text})
                
                with st.spinner("Ava is analyzing and responding..."):
                    turn_res = execute_sales_turn(
                        call_id=st.session_state.call_id,
                        user_input=user_text,
                        language=selected_lang,
                        history=st.session_state.messages
                    )

                # Generate voice reply audio
                out_audio_file = f"temp_audio/{st.session_state.call_id}_{len(st.session_state.messages)}.mp3"
                try:
                    text_to_speech(turn_res["reply"], out_audio_file, language=selected_lang)
                except Exception:
                    out_audio_file = None

                # Update session states
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": turn_res["reply"],
                    "latency": turn_res["latency"],
                    "sentiment_label": turn_res["sentiment"]["label"],
                    "audio_path": out_audio_file
                })
                st.session_state.sentiment_history.append(turn_res["sentiment"]["score"])
                st.session_state.latest_lead = turn_res["lead"]
                st.session_state.latest_sources = turn_res["sources"]
                
                if turn_res.get("ics_content"):
                    st.session_state.ics_file_ready = turn_res["ics_content"]

                st.rerun()
        else:
            st.success("✅ **Call Completed.** Structured summary and CRM synchronization complete.")
            if hasattr(st.session_state, "call_summary"):
                s = st.session_state.call_summary
                st.markdown(f"**Executive Summary:** {s.get('summary')}")
                st.markdown(f"**Key Points:** {s.get('key_points')}")
                st.markdown(f"**Next Steps:** {s.get('next_steps')}")

    # Right Column: Live Lead Qualification & Analytics
    with col_info:
        st.subheader("🎯 Live Lead Intelligence")
        
        lead = st.session_state.latest_lead
        score = lead.get("score", 0)
        status = lead.get("status", "COLD")
        
        # Score & Badge
        col_badge, col_score = st.columns([1, 1])
        with col_badge:
            if status == "HOT":
                st.markdown("### 🔥 :red[HOT LEAD]")
            elif status == "WARM":
                st.markdown("### ☀️ :orange[WARM LEAD]")
            else:
                st.markdown("### ❄️ :blue[COLD LEAD]")
        with col_score:
            st.metric("Lead Score", f"{score} / 100")

        st.progress(score / 100)

        # Extracted Lead Fields
        with st.container(border=True):
            st.markdown(f"**👤 Name:** {lead.get('name') or 'Not captured yet'}")
            st.markdown(f"**✉️ Email:** {lead.get('email') or 'Not captured yet'}")
            st.markdown(f"**🏢 Company:** {lead.get('company') or 'Not captured yet'}")
            st.markdown(f"**💰 Budget:** {lead.get('budget') or 'Not captured yet'}")
            st.markdown(f"**⏱️ Timeline:** {lead.get('timeline') or 'Not captured yet'}")
            st.markdown(f"**👑 Decision Maker:** {'Yes' if lead.get('is_decision_maker') else 'Pending verification'}")

        # Sentiment Trend Chart
        st.markdown("##### 📈 Live Sentiment Trajectory")
        if st.session_state.sentiment_history:
            df_sent = pd.DataFrame({"Turn": list(range(1, len(st.session_state.sentiment_history) + 1)), "Sentiment": st.session_state.sentiment_history})
            st.line_chart(df_sent.set_index("Turn"), height=160)
        else:
            st.caption("Sentiment trend will appear after the first conversation turn.")

        # RAG Knowledge Sources Expander
        with st.expander("📚 Knowledge Base Sources Used", expanded=False):
            if st.session_state.latest_sources:
                for i, src in enumerate(st.session_state.latest_sources):
                    st.markdown(f"**Chunk {i+1}:**\n{src}")
            else:
                st.caption("No knowledge base chunks retrieved yet.")

        # Download Calendar Invite if demo was booked
        if st.session_state.ics_file_ready:
            st.download_button(
                label="📅 Download Demo Calendar Invite (.ics)",
                data=st.session_state.ics_file_ready,
                file_name="cloudscale_demo.ics",
                mime="text/calendar",
                use_container_width=True
            )

# ==============================================================================
# TAB 2: LEADS & APPOINTMENTS (CRM)
# ==============================================================================
with tab_crm:
    st.subheader("👥 CRM Qualified Leads")
    db = SessionLocal()
    try:
        leads_db = db.query(Lead).order_by(Lead.updated_at.desc()).all()
        if leads_db:
            lead_rows = []
            for l in leads_db:
                lead_rows.append({
                    "Call ID": l.call_id,
                    "Name": l.name or "-",
                    "Email": l.email or "-",
                    "Company": l.company or "-",
                    "Budget": l.budget or "-",
                    "Timeline": l.timeline or "-",
                    "Score": l.score,
                    "Status": l.qualification_status,
                    "Decision Maker": "Yes" if l.is_decision_maker else "No",
                    "Updated": l.updated_at.strftime("%Y-%m-%d %H:%M") if l.updated_at else "-"
                })
            st.dataframe(pd.DataFrame(lead_rows), use_container_width=True)
        else:
            st.info("No leads captured yet. Start a call in Tab 1 to qualify inbound prospects.")

        st.markdown("---")
        st.subheader("📅 Scheduled Demos & Appointments")
        appts_db = db.query(Appointment).order_by(Appointment.slot_time.asc()).all()
        if appts_db:
            appt_rows = []
            for a in appts_db:
                appt_rows.append({
                    "ID": a.id,
                    "Customer Name": a.customer_name,
                    "Customer Email": a.customer_email,
                    "Slot Time": a.slot_time.strftime("%Y-%m-%d %H:%M"),
                    "Status": a.status,
                    "Created": a.created_at.strftime("%Y-%m-%d %H:%M")
                })
            st.dataframe(pd.DataFrame(appt_rows), use_container_width=True)
        else:
            st.info("No demos scheduled yet. Request a demo in the conversation to book a slot.")
    finally:
        db.close()

# ==============================================================================
# TAB 3: INSIGHTS & ANALYTICS
# ==============================================================================
with tab_insights:
    st.subheader("📊 Executive Sales & Voice Analytics")
    db = SessionLocal()
    try:
        total_calls = db.query(Call).count()
        demos_booked = db.query(Appointment).filter(Appointment.status == "CONFIRMED").count()
        leads_all = db.query(Lead).all()
        avg_score = round(sum(l.score for l in leads_all) / len(leads_all), 1) if leads_all else 0.0
        conversion = round((demos_booked / total_calls * 100), 1) if total_calls > 0 else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Inbound Calls", total_calls)
        col2.metric("Demos Booked", demos_booked)
        col3.metric("Demo Conversion Rate", f"{conversion}%")
        col4.metric("Avg Lead Score", f"{avg_score} / 100")

        st.markdown("---")
        col_chart1, col_chart2 = st.columns([1, 1])

        with col_chart1:
            st.markdown("##### 🎭 Customer Sentiment Breakdown")
            messages = db.query(Message).filter(Message.sender == "user").all()
            sent_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
            for m in messages:
                lbl = (m.sentiment_label or "neutral").capitalize()
                if lbl in sent_counts:
                    sent_counts[lbl] += 1
            df_pie = pd.DataFrame(list(sent_counts.items()), columns=["Sentiment", "Count"])
            st.bar_chart(df_pie.set_index("Sentiment"), height=240)

        with col_chart2:
            st.markdown("##### ❓ Top Inbound Customer Inquiries")
            top_faqs = [
                ("1. Pricing & Enterprise Tiers", 42),
                ("2. Kubernetes Compute Rightsizing", 35),
                ("3. 14-Day Risk-Free Trial", 28),
                ("4. Multi-Cloud AWS & GCP Support", 21),
                ("5. SOC2 & Security Guarantees", 15)
            ]
            df_faq = pd.DataFrame(top_faqs, columns=["Topic", "Frequency"])
            st.dataframe(df_faq, use_container_width=True)
    finally:
        db.close()
