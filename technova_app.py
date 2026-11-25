"""
TechNova Solutions — Autonomous AI Sales Voice Agent
Streamlit Dashboard with 7-page sidebar navigation.
Run with: streamlit run technova_app.py
"""
import os
import uuid
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database.technova_db import init_tn_db, seed_demo_data, TNSession
from database.technova_models import TNLead, TNConversation, TNMessage, TNAppointment, TNCallReport
from backend.technova_agent import chat, summarize_conversation, is_demo_mode, AGENT_NAME, COMPANY_NAME
from backend.technova_sentiment import analyze_sentiment, should_escalate
from backend.technova_leads import extract_lead_info, score_lead
from backend.technova_appointment import validate_appointment, book_appointment_in_db
from backend.technova_tts import speak

# ─── BOOTSTRAP ───────────────────────────────────────────────────────────────
init_tn_db()
seed_demo_data()

st.set_page_config(
    page_title="TechNova AI Sales Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Dark sidebar */
[data-testid="stSidebar"] { background: #0D1117; }
/* Metric card styling */
div[data-testid="metric-container"] {
    background: #1C2333; border-radius: 12px; padding: 16px; border: 1px solid #30363D;
}
/* Chat bubbles */
.user-bubble  { background: #1F6FEB; border-radius: 12px; padding: 10px 14px; margin: 6px 0; color: white; max-width: 80%; float: right; clear: both; }
.agent-bubble { background: #21262D; border-radius: 12px; padding: 10px 14px; margin: 6px 0; color: #E6EDF3; max-width: 80%; float: left; clear: both; }
.clearfix { clear: both; }
/* Status badges */
.badge-hot  { background: #FF4B4B; color: white; border-radius: 8px; padding: 3px 10px; font-weight: bold; }
.badge-warm { background: #FF9B00; color: white; border-radius: 8px; padding: 3px 10px; font-weight: bold; }
.badge-cold { background: #0F8BFD; color: white; border-radius: 8px; padding: 3px 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "session_id":     str(uuid.uuid4())[:8],
        "messages":       [],           # {role, content, sentiment, timestamp}
        "lead_info":      {},
        "lead_score":     0,
        "lead_status":    "Cold",
        "sentiment_hist": [],
        "conv_saved":     False,
        "appt_booked":    False,
        "call_ended":     False,
        "call_summary":   None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1F6FEB/FFFFFF?text=TechNova", width=200)
    st.markdown("## 🚀 TechNova Solutions")
    st.markdown("*AI Sales Voice Agent — MVP Demo*")
    st.markdown("---")

    page = st.radio("Navigation", [
        "📊 Dashboard",
        "🤖 AI Voice Agent",
        "👥 Lead Management",
        "📅 Appointments",
        "📚 Knowledge Base",
        "📋 Call Reports",
        "⚙️ Settings",
    ], label_visibility="collapsed")

    st.markdown("---")
    if is_demo_mode():
        st.warning("⚡ **Demo Mode**\nNo OpenAI key detected.\nReplies use smart keyword matching.", icon="⚡")
        st.caption("Add `OPENAI_API_KEY` to `.env` for GPT-powered responses.")
    else:
        st.success("🟢 **OpenAI Mode Active**", icon="✅")

    st.markdown(f"**Session:** `{st.session_state.session_id}`")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Business Intelligence Dashboard")
    st.caption("Real-time analytics from TechNova CRM • Auto-refreshes on activity")

    db = TNSession()
    try:
        leads   = db.query(TNLead).all()
        convos  = db.query(TNConversation).all()
        appts   = db.query(TNAppointment).all()
        reports = db.query(TNCallReport).all()
        msgs    = db.query(TNMessage).all()

        total_leads = len(leads)
        hot_count   = sum(1 for l in leads if l.lead_status == "Hot")
        warm_count  = sum(1 for l in leads if l.lead_status == "Warm")
        cold_count  = sum(1 for l in leads if l.lead_status == "Cold")
        booked      = sum(1 for a in appts if a.status == "Scheduled")
        avg_score   = round(sum(l.score for l in leads) / len(leads), 1) if leads else 0

        # Metric Cards Row 1
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Leads",        total_leads, "+2 today")
        c2.metric("🔥 Hot Leads",       hot_count)
        c3.metric("☀️ Warm Leads",      warm_count)
        c4.metric("❄️ Cold Leads",      cold_count)
        c5.metric("📅 Demos Booked",    booked)

        c6, c7, c8 = st.columns(3)
        c6.metric("Total Conversations", len(convos))
        c7.metric("Total Messages",      len(msgs))
        c8.metric("Avg Lead Score",      f"{avg_score} / 100")

        st.markdown("---")
        col_a, col_b = st.columns(2)

        # Lead Status Pie Chart
        with col_a:
            st.subheader("Lead Distribution")
            if leads:
                fig = px.pie(
                    values=[hot_count, warm_count, cold_count],
                    names=["Hot 🔥", "Warm ☀️", "Cold ❄️"],
                    color_discrete_sequence=["#FF4B4B", "#FF9B00", "#0F8BFD"],
                    hole=0.4
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No leads yet. Start a conversation!")

        # Sentiment Distribution Bar Chart
        with col_b:
            st.subheader("Customer Sentiment")
            sent_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
            for m in msgs:
                if m.sender == "user" and m.sentiment:
                    sent_counts[m.sentiment] = sent_counts.get(m.sentiment, 0) + 1
            fig2 = px.bar(
                x=list(sent_counts.keys()),
                y=list(sent_counts.values()),
                color=list(sent_counts.keys()),
                color_discrete_map={"Positive": "#00C49F", "Neutral": "#FFB347", "Negative": "#FF6B6B"},
                labels={"x": "Sentiment", "y": "Messages"},
            )
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False, height=300)
            st.plotly_chart(fig2, use_container_width=True)

        # Recent Activity Table
        st.subheader("🕒 Recent Leads")
        if leads:
            df = pd.DataFrame([{
                "Name": l.name or "Unknown",
                "Company": l.company or "-",
                "Product Interest": l.interested_product or "-",
                "Score": l.score,
                "Status": l.lead_status,
                "Updated": l.updated_at.strftime("%d %b %Y") if l.updated_at else "-"
            } for l in sorted(leads, key=lambda x: x.updated_at or datetime.datetime.min, reverse=True)[:5]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No leads yet. Conversations appear here automatically.")

        # Upcoming Appointments
        st.subheader("📅 Upcoming Demos")
        upcoming = [a for a in appts if a.status == "Scheduled"]
        if upcoming:
            df2 = pd.DataFrame([{
                "Customer": a.customer_name,
                "Email": a.customer_email,
                "Date": a.appointment_date,
                "Time": a.appointment_time,
                "Product": a.product_interest or "-",
            } for a in upcoming])
            st.dataframe(df2, use_container_width=True, hide_index=True)
        else:
            st.info("No demos scheduled yet.")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — AI VOICE AGENT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Voice Agent":
    st.title(f"🤖 {AGENT_NAME} — AI Sales Agent")
    st.caption(f"Powered by {COMPANY_NAME} • {'Demo Mode' if is_demo_mode() else 'OpenAI Mode'}")

    col_chat, col_panel = st.columns([6, 4], gap="medium")

    # ── RIGHT PANEL: Live Lead Card ───────────────────────────────────────────
    with col_panel:
        st.subheader("🎯 Live Lead Intelligence")

        lead = st.session_state.lead_info
        score = st.session_state.lead_score
        status = st.session_state.lead_status

        badge = {"Hot": "🔥 HOT", "Warm": "☀️ WARM", "Cold": "❄️ COLD"}.get(status, "❄️ COLD")
        color = {"Hot": "red", "Warm": "orange", "Cold": "blue"}.get(status, "blue")
        st.markdown(f"### :{color}[{badge} LEAD]")
        st.metric("Lead Score", f"{score} / 100")
        st.progress(score / 100)

        with st.container(border=True):
            st.markdown(f"**👤 Name:** {lead.get('name') or '—'}")
            st.markdown(f"**✉️ Email:** {lead.get('email') or '—'}")
            st.markdown(f"**📞 Phone:** {lead.get('phone') or '—'}")
            st.markdown(f"**🏢 Company:** {lead.get('company') or '—'}")
            st.markdown(f"**💰 Budget:** {lead.get('budget') or '—'}")
            st.markdown(f"**⏱ Timeline:** {lead.get('timeline') or '—'}")
            st.markdown(f"**📦 Product Interest:** {lead.get('interested_product') or '—'}")

        # Sentiment Chart
        st.markdown("##### 📈 Sentiment Trajectory")
        if st.session_state.sentiment_hist:
            df_s = pd.DataFrame({
                "Turn": list(range(1, len(st.session_state.sentiment_hist) + 1)),
                "Score": st.session_state.sentiment_hist
            })
            fig = px.line(df_s, x="Turn", y="Score", markers=True,
                          color_discrete_sequence=["#1F6FEB"])
            fig.update_layout(yaxis_range=[-1, 1], paper_bgcolor="rgba(0,0,0,0)",
                              font_color="white", height=180, margin=dict(t=10, b=10))
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Sentiment chart appears after first message.")

        # Escalation alert
        if st.session_state.sentiment_hist and st.session_state.sentiment_hist[-1] <= -0.5:
            st.error("🚨 **Escalation Alert** — Consider connecting this customer to a human agent.")

    # ── LEFT PANEL: Chat Interface ────────────────────────────────────────────
    with col_chat:
        st.subheader("💬 Conversation")

        # Render chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("sentiment"):
                    st.caption(f"Sentiment: {msg['sentiment']}")
                if msg.get("audio_path") and os.path.exists(msg["audio_path"]):
                    st.audio(msg["audio_path"], format="audio/mp3")

        if not st.session_state.call_ended:
            # Voice Input
            audio_data = None
            with st.container(border=True):
                st.markdown("🎙️ **Voice Input**")
                if hasattr(st, "audio_input"):
                    audio_data = st.audio_input("Click the mic to record your question", key="tn_mic")
                    if is_demo_mode():
                        st.caption("⚡ Demo Mode: Google Web Speech used for transcription (internet required).")
                else:
                    st.caption("Upgrade Streamlit to use voice: `pip install -U streamlit`")

            user_text = st.chat_input(f"Ask {AGENT_NAME} about TechNova Solutions...")

            # Process audio input
            if audio_data is not None:
                from backend.technova_stt import transcribe_audio_file
                with st.spinner("🔄 Transcribing audio..."):
                    transcript, status_msg = transcribe_audio_file(audio_data.read())
                if transcript:
                    user_text = transcript
                    st.success(f"📝 You said: *{transcript}*")
                else:
                    st.warning(f"⚠️ {status_msg}")

            # Process user message
            if user_text:
                # Add user message
                s_label, s_score = analyze_sentiment(user_text)
                st.session_state.messages.append({
                    "role": "user", "content": user_text,
                    "sentiment": s_label,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                st.session_state.sentiment_hist.append(s_score)

                # Get agent reply
                with st.spinner(f"{AGENT_NAME} is thinking..."):
                    history = [{"role": m["role"], "content": m["content"]}
                               for m in st.session_state.messages[:-1]]
                    result = chat(user_text, history)

                # TTS audio for agent reply
                audio_path = None
                try:
                    audio_path = speak(result["reply"])
                except Exception:
                    pass

                # Add agent message
                st.session_state.messages.append({
                    "role": "assistant", "content": result["reply"],
                    "audio_path": audio_path,
                    "timestamp": datetime.datetime.now().isoformat()
                })

                # Update lead state
                st.session_state.lead_info   = result["lead_info"]
                st.session_state.lead_score  = result["lead_score"]
                st.session_state.lead_status = result["lead_status"]

                # Save to DB
                db = TNSession()
                try:
                    conv = db.query(TNConversation).filter(
                        TNConversation.session_id == st.session_state.session_id
                    ).first()
                    if not conv:
                        conv = TNConversation(session_id=st.session_state.session_id)
                        db.add(conv)
                        db.flush()

                    db.add(TNMessage(conversation_id=conv.id, sender="user", text=user_text,
                                     sentiment=s_label, sentiment_score=s_score))
                    db.add(TNMessage(conversation_id=conv.id, sender="agent", text=result["reply"]))
                    db.commit()
                finally:
                    db.close()

                st.rerun()

            # End Call button
            st.markdown("---")
            if st.button("⏹️ End Call & Generate Summary", type="primary"):
                msgs_for_summary = [{"sender": m["role"], "text": m["content"]}
                                    for m in st.session_state.messages]
                summary = summarize_conversation(msgs_for_summary)
                st.session_state.call_summary = summary
                st.session_state.call_ended   = True

                # Save lead and report to DB
                db = TNSession()
                try:
                    li = summary["lead_info"]
                    email = (li.get("email") or "").strip().lower() or None
                    lead_obj = db.query(TNLead).filter(TNLead.email == email).first() if email else None
                    if not lead_obj:
                        lead_obj = TNLead(
                            name=li.get("name"), email=email, phone=li.get("phone"),
                            company=li.get("company"), requirements=li.get("requirements"),
                            budget=li.get("budget"), timeline=li.get("timeline"),
                            interested_product=li.get("interested_product"),
                            lead_status=summary["lead_status"],
                            score=summary["lead_score"]
                        )
                        db.add(lead_obj)
                        db.flush()

                    # Attach conversation to lead
                    conv = db.query(TNConversation).filter(
                        TNConversation.session_id == st.session_state.session_id
                    ).first()
                    if conv:
                        conv.lead_id = lead_obj.id
                        conv.ended_at = datetime.datetime.utcnow()
                        conv.summary  = summary["summary"]
                        conv.overall_sentiment = summary["sentiment"]

                    db.add(TNCallReport(
                        conversation_id=conv.id if conv else None,
                        lead_name=li.get("name") or "Unknown",
                        summary=summary["summary"],
                        requirements=summary["requirements"],
                        products_discussed=summary["products_discussed"],
                        sentiment=summary["sentiment"],
                        lead_status=summary["lead_status"],
                        next_action=summary["next_action"]
                    ))
                    db.commit()
                finally:
                    db.close()
                st.rerun()

        else:
            # Show summary
            st.success("✅ Call Completed. Summary generated and saved to CRM.")
            if st.session_state.call_summary:
                s = st.session_state.call_summary
                with st.expander("📋 Call Summary", expanded=True):
                    st.markdown(f"**Summary:** {s['summary']}")
                    st.markdown(f"**Requirements:** {s.get('requirements', '—')}")
                    st.markdown(f"**Products Discussed:** {s['products_discussed']}")
                    st.markdown(f"**Sentiment:** {s['sentiment']}")
                    st.markdown(f"**Lead Status:** {s['lead_status']} ({s['lead_score']}/100)")
                    st.markdown(f"**Next Action:** {s['next_action']}")

            if st.button("🔄 Start New Conversation"):
                for key in ["messages", "lead_info", "lead_score", "lead_status",
                            "sentiment_hist", "conv_saved", "call_ended", "call_summary", "appt_booked"]:
                    del st.session_state[key]
                st.session_state.session_id = str(uuid.uuid4())[:8]
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — LEAD MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Lead Management":
    st.title("👥 Lead Management — CRM")

    db = TNSession()
    try:
        leads = db.query(TNLead).order_by(TNLead.updated_at.desc()).all()

        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        status_filter  = col_f1.selectbox("Filter by Status", ["All", "Hot", "Warm", "Cold"])
        product_filter = col_f2.selectbox("Filter by Product",
                            ["All", "TechNova CRM Suite", "TechNova ERP Pro", "TechNova Analytics Hub"])
        search         = col_f3.text_input("Search by name or company")

        filtered = leads
        if status_filter != "All":
            filtered = [l for l in filtered if l.lead_status == status_filter]
        if product_filter != "All":
            filtered = [l for l in filtered if product_filter in (l.interested_product or "")]
        if search:
            filtered = [l for l in filtered if search.lower() in (l.name or "").lower()
                        or search.lower() in (l.company or "").lower()]

        st.markdown(f"**{len(filtered)} leads found**")

        if filtered:
            df = pd.DataFrame([{
                "ID": l.id, "Name": l.name or "—", "Company": l.company or "—",
                "Email": l.email or "—", "Phone": l.phone or "—",
                "Product": l.interested_product or "—",
                "Budget": l.budget or "—", "Timeline": l.timeline or "—",
                "Score": l.score, "Status": l.lead_status,
                "Created": l.created_at.strftime("%d %b %Y") if l.created_at else "—"
            } for l in filtered])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Update lead status
            st.markdown("#### ✏️ Update Lead Status")
            col_u1, col_u2, col_u3 = st.columns(3)
            lead_id = col_u1.number_input("Lead ID", min_value=1, step=1)
            new_status = col_u2.selectbox("New Status", ["Hot", "Warm", "Cold"])
            if col_u3.button("Update", use_container_width=True):
                lead = db.query(TNLead).filter(TNLead.id == lead_id).first()
                if lead:
                    lead.lead_status = new_status
                    db.commit()
                    st.success(f"Lead #{lead_id} updated to **{new_status}**.")
                    st.rerun()
                else:
                    st.error(f"Lead #{lead_id} not found.")
        else:
            st.info("No leads match the filter. Start conversations in the AI Voice Agent page.")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — APPOINTMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Appointments":
    st.title("📅 Demo Appointments")

    db = TNSession()
    try:
        # Booking form
        with st.expander("➕ Book a New Demo Appointment", expanded=False):
            with st.form("appt_form"):
                col1, col2 = st.columns(2)
                name  = col1.text_input("Customer Name *")
                email = col2.text_input("Email Address *")
                col3, col4 = st.columns(2)
                date  = col3.text_input("Preferred Date (e.g. 2026-11-28)")
                time  = col4.text_input("Preferred Time (e.g. 3:00 PM)")
                col5, col6 = st.columns(2)
                product = col5.selectbox("Product Interest",
                    ["TechNova CRM Suite", "TechNova ERP Pro", "TechNova Analytics Hub", "Full Suite"])
                notes = col6.text_area("Notes")
                submitted = st.form_submit_button("📅 Book Appointment", type="primary")

            if submitted:
                if not name or not email or not date or not time:
                    st.error("Please fill in all required fields (Name, Email, Date, Time).")
                else:
                    success, msg = book_appointment_in_db(db, None, name, email, date, time, product, notes)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        # Appointment list
        appts = db.query(TNAppointment).order_by(TNAppointment.appointment_date.asc()).all()
        status_tab = st.radio("Show", ["All", "Scheduled", "Completed", "Cancelled"], horizontal=True)
        filtered_appts = [a for a in appts if status_tab == "All" or a.status == status_tab]

        if filtered_appts:
            df = pd.DataFrame([{
                "ID": a.id,
                "Customer": a.customer_name,
                "Email": a.customer_email,
                "Date": a.appointment_date,
                "Time": a.appointment_time,
                "Product": a.product_interest or "—",
                "Status": a.status,
                "Notes": (a.notes or "")[:40],
            } for a in filtered_appts])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Cancel / Complete
            col_a, col_b, col_c = st.columns(3)
            appt_id = col_a.number_input("Appointment ID", min_value=1, step=1)
            new_appt_status = col_b.selectbox("Update Status", ["Completed", "Cancelled"])
            if col_c.button("Update Status"):
                a = db.query(TNAppointment).filter(TNAppointment.id == appt_id).first()
                if a:
                    a.status = new_appt_status
                    db.commit()
                    st.success(f"Appointment #{appt_id} marked as {new_appt_status}.")
                    st.rerun()
        else:
            st.info("No appointments found.")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📚 Knowledge Base":
    st.title("📚 Knowledge Base Manager")

    kb_path = os.path.join("knowledge_base", "technova_info.txt")

    # View current KB
    with st.expander("📄 View Current Knowledge Base", expanded=True):
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.text_area("Current Knowledge Base Content", content, height=350, disabled=True)
        else:
            st.warning("Knowledge base file not found.")

    # RAG test
    st.subheader("🔍 Test Knowledge Retrieval")
    test_query = st.text_input("Enter a test query (e.g. 'What are your pricing plans?')")
    if test_query:
        from backend.technova_rag import tn_rag
        results = tn_rag.retrieve(test_query, top_k=3)
        if results:
            for i, (chunk, score) in enumerate(results, 1):
                with st.expander(f"Result #{i} — Relevance: {score:.2%}"):
                    st.write(chunk)
        else:
            st.info("No relevant chunks found for that query.")

    # Upload new document
    st.subheader("📤 Upload Additional Documents")
    uploaded = st.file_uploader("Upload a .txt or .md file to add to the knowledge base",
                                 type=["txt", "md"])
    if uploaded:
        new_text = uploaded.read().decode("utf-8", errors="ignore")
        # Append to existing knowledge base
        with open(kb_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n## Uploaded: {uploaded.name}\n{new_text}")
        st.success(f"✅ '{uploaded.name}' added to knowledge base. The RAG index will refresh on next query.")
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — CALL REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Call Reports":
    st.title("📋 Call Reports & Summaries")

    db = TNSession()
    try:
        reports = db.query(TNCallReport).order_by(TNCallReport.created_at.desc()).all()
        if reports:
            for r in reports:
                with st.expander(f"📞 {r.lead_name or 'Unknown'} — {r.created_at.strftime('%d %b %Y %H:%M') if r.created_at else ''}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Lead Status", r.lead_status or "—")
                    col2.metric("Sentiment",   r.sentiment  or "—")
                    col3.metric("Products",    r.products_discussed or "—")
                    st.markdown(f"**Summary:** {r.summary or 'No summary available.'}")
                    if r.requirements:
                        st.markdown(f"**Requirements:** {r.requirements}")
                    if r.next_action:
                        st.info(f"**Next Action:** {r.next_action}")
        else:
            st.info("No call reports yet. End a conversation in the AI Voice Agent page to generate a report.")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")

    st.subheader("🔑 API Configuration")
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        st.success("✅ OpenAI API key is configured.")
    else:
        st.warning("⚠️ No OpenAI API key detected. Running in Demo Mode.")
        st.code('OPENAI_API_KEY=sk-your-key-here', language="ini")
        st.caption("Add this to your `.env` file and restart the app to enable GPT-powered responses.")

    st.subheader("🤖 Agent Configuration")
    st.markdown(f"- **Agent Name:** {AGENT_NAME}")
    st.markdown(f"- **Company:** {COMPANY_NAME}")
    st.markdown("- **Model:** `gpt-3.5-turbo` (changeable in `backend/technova_agent.py` → `OPENAI_MODEL`)")
    st.markdown("- **TTS Voice (EN):** `en-US-JennyNeural`")
    st.markdown("- **TTS Voice (HI):** `hi-IN-SwaraNeural`")

    st.subheader("🗑️ Data Management")
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("🔄 Re-seed Demo Data", use_container_width=True):
        db = TNSession()
        try:
            db.query(TNCallReport).delete()
            db.query(TNAppointment).delete()
            db.query(TNMessage).delete()
            db.query(TNConversation).delete()
            db.query(TNLead).delete()
            db.commit()
        finally:
            db.close()
        seed_demo_data()
        st.success("✅ Demo data re-seeded successfully.")

    st.subheader("📊 System Status")
    st.json({
        "mode": "Demo Mode" if is_demo_mode() else "OpenAI Mode",
        "database": "SQLite (technova.db)",
        "rag_engine": "TF-IDF (scikit-learn)",
        "tts": "Edge-TTS (Microsoft Neural)",
        "stt": "Google Web Speech API (SpeechRecognition)",
        "version": "1.0.0 MVP"
    })
