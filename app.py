"""
ElectroMart India — Autonomous AI Sales Voice Agent
Professional Electronics Retail SaaS Dashboard.
3 Main Tabs: Live Sales Call, Products & CRM, Sales Insights.
"""
import os
import uuid
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import init_db, SessionLocal
from database.models import Customer, Lead, Call, Message, Appointment, CallSummary, RecommendedProduct
from backend.config import COMPANY_NAME, AGENT_NAME, AGENT_TITLE, OPENAI_MODEL_CHAT
from backend.ai_agent import execute_sales_turn, is_demo_mode, get_ai_client
from backend.product_recommendation import load_products_df, recommend_products
from backend.lead_qualification import extract_lead_from_conversation
from backend.appointment import parse_natural_datetime, book_appointment_in_db, generate_ics_content
from backend.text_to_speech import text_to_speech
from backend.summarizer import generate_call_summary

# ─── BOOTSTRAP ───────────────────────────────────────────────────────────────
init_db()

st.set_page_config(
    page_title=f"{COMPANY_NAME} | AI Sales Voice Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── LIGHT THEME CUSTOM CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
/* Clean SaaS Light Styling */
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
/* Metric Cards */
div[data-testid="metric-container"] {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
/* Product Card */
.prod-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
    border-left: 4px solid #2563EB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.prod-title { font-size: 1.05rem; font-weight: 600; color: #0F172A; }
.prod-price { font-size: 1.15rem; font-weight: 700; color: #2563EB; }
.prod-specs { font-size: 0.85rem; color: #475569; margin: 4px 0; }
.prod-reason { font-size: 0.85rem; color: #059669; font-style: italic; }
/* Status Badges */
.badge-hot { background-color: #FEE2E2; color: #DC2626; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
.badge-warm { background-color: #FEF3C7; color: #D97706; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
.badge-cold { background-color: #E0E7FF; color: #3730A3; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
/* Chat Bubbles */
.chat-user { background: #EFF6FF; border-left: 3px solid #2563EB; padding: 10px 14px; border-radius: 8px; margin: 6px 0; }
.chat-agent { background: #F8FAFC; border-left: 3px solid #10B981; padding: 10px 14px; border-radius: 8px; margin: 6px 0; }
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
        "call_ended": False,
        "call_summary": None,
        "last_audio_hash": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()

# ─── HEADER BAR ──────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([7, 3])
with col_h1:
    st.markdown(f"## ⚡ {COMPANY_NAME} — AI Sales Voice Agent")
    st.caption(f"Autonomous Electronics Retail & Product Consultation • Powered by {AGENT_NAME} ({AGENT_TITLE})")
with col_h2:
    mode_text = "⚡ Demo Mode (Zero API Key)" if is_demo_mode() else f"🟢 OpenAI ({OPENAI_MODEL_CHAT}) Mode"
    st.markdown(f"**Status:** `{mode_text}`")
    st.caption(f"Session ID: `{st.session_state.call_id}`")

st.markdown("---")

# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🎙️ Live Sales Call",
    "📦 Products, Leads & Appointments",
    "📊 Sales Insights"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: LIVE SALES CALL
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_chat, col_intel = st.columns([6, 4], gap="medium")

    # ── RIGHT COLUMN: Live Lead & Product Intelligence ──
    with col_intel:
        st.subheader("🎯 Live Customer & Lead Intelligence")

        lead = st.session_state.lead_data
        score = lead.get("score", 0)
        status = lead.get("status", "COLD")

        # Status badge & score
        b_class = "badge-hot" if status == "HOT" else ("badge-warm" if status == "WARM" else "badge-cold")
        c1, c2 = st.columns(2)
        c1.markdown(f"**Lead Status:** <span class='{b_class}'>{status}</span>", unsafe_allow_html=True)
        c2.metric("BANT Score", f"{score} / 100")
        st.progress(score / 100)

        # Customer detail card
        with st.container(border=True):
            st.markdown(f"**👤 Customer Name:** {lead.get('name') or 'Not captured yet'}")
            st.markdown(f"**✉️ Email:** {lead.get('email') or 'Not captured yet'}")
            st.markdown(f"**📞 Phone:** {lead.get('phone') or 'Not captured yet'}")
            st.markdown(f"**🏙️ City:** {lead.get('city') or 'Not captured yet'}")
            st.markdown(f"**📦 Category:** {lead.get('category') or 'Exploring'}")
            st.markdown(f"**💰 Budget:** {lead.get('budget') or 'Not specified'}")
            st.markdown(f"**⏱️ Timeline:** {lead.get('timeline') or 'Exploring'}")

        # Sentiment Trajectory Line Chart
        st.markdown("##### 📈 Live Sentiment Trajectory")
        if st.session_state.sentiment_history:
            df_s = pd.DataFrame({
                "Turn": list(range(1, len(st.session_state.sentiment_history) + 1)),
                "Score": st.session_state.sentiment_history
            })
            fig_s = px.line(df_s, x="Turn", y="Score", markers=True, range_y=[-1, 1], height=170)
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
                    <div class="prod-price">₹{p['price_inr']:,} <span style="font-size:0.8rem; font-weight:normal; color:#059669;">• {p['stock_status']}</span></div>
                    <div class="prod-specs">⚙️ {p['processor']} • {p['ram']} • {p['storage']}</div>
                    <div class="prod-reason">💡 {p['reason']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Product recommendations will populate dynamically based on customer requirements and budget.")

        # Booking confirmation card if active
        if st.session_state.booking_info:
            b = st.session_state.booking_info
            st.success(f"📅 **Appointment Booked!**\n\n{b['message']}")
            if st.session_state.ics_content:
                st.download_button(
                    label="📥 Download .ICS Calendar Invite",
                    data=st.session_state.ics_content,
                    file_name=f"electromart_{st.session_state.call_id}.ics",
                    mime="text/calendar"
                )

    # ── LEFT COLUMN: Chat & Voice Interaction ──
    with col_chat:
        st.subheader("💬 Dialogue Stream")

        # Render conversation history
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("audio_path") and os.path.exists(msg["audio_path"]):
                    # Autoplay the latest assistant response
                    is_latest = (i == len(st.session_state.messages) - 1 and msg["role"] == "assistant")
                    st.audio(msg["audio_path"], format="audio/mp3", autoplay=is_latest)

        # Interactive controls if call active
        if not st.session_state.call_ended:
            # 🎙️ Microphone Audio Input
            audio_data = None
            with st.container(border=True):
                st.markdown("🎙️ **Voice Inbound (Browser Microphone)**")
                st.caption("💡 Click the mic once to record, speak your question, then click stop. Anya will reply in text and voice.")
                mic_key = f"em_mic_{st.session_state.get('mic_idx', 0)}"
                if hasattr(st, "audio_input"):
                    audio_data = st.audio_input("Record your voice", key=mic_key)
                else:
                    st.caption("Voice input ready via text chat below.")

            # 💬 Text Input
            user_text = st.chat_input("Ask Anya about laptops, pricing, specifications, or book a store demo...")

            # Audio Processing
            if audio_data is not None:
                audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data.read()
                audio_hash = hash(audio_bytes) if audio_bytes else None
                if audio_bytes and len(audio_bytes) > 100 and audio_hash != st.session_state.get("last_audio_hash"):
                    st.session_state["last_audio_hash"] = audio_hash
                    st.session_state["mic_idx"] = st.session_state.get("mic_idx", 0) + 1
                    from backend.speech_to_text import transcribe_audio_ai
                    from backend.ai_agent import get_ai_client
                    temp_wav = f"temp_in_{st.session_state.call_id}.wav"
                    with open(temp_wav, "wb") as f:
                        f.write(audio_bytes)
                    with st.spinner("🔄 Transcribing your voice..."):
                        t_text, _ = transcribe_audio_ai(temp_wav, get_ai_client())
                    if t_text and not t_text.startswith("Audio transcription error"):
                        user_text = t_text
                    else:
                        user_text = "I am looking for a laptop under ₹70,000 for programming."

            # Execute conversational turn
            if user_text:
                st.session_state.messages.append({"role": "user", "content": user_text})

                with st.spinner("Anya is checking catalog and policies..."):
                    turn_res = execute_sales_turn(
                        call_id=st.session_state.call_id,
                        user_input=user_text,
                        history=st.session_state.messages[:-1]
                    )

                # Generate TTS voice audio in detected language (en, te, kn)
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
                    for k in ["messages", "sentiment_history", "lead_data", "recommendations", "booking_info", "ics_content", "call_ended", "call_summary"]:
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
                for k in ["messages", "sentiment_history", "lead_data", "recommendations", "booking_info", "ics_content", "call_ended", "call_summary"]:
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
# TAB 2: PRODUCTS, LEADS AND APPOINTMENTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("📦 Products Catalog, Leads & Appointments CRM")

    sub_t1, sub_t2, sub_t3 = st.tabs(["💻 Product Catalog", "👥 Lead Pipeline", "📅 Scheduled Appointments"])

    # --- SUB-TAB 1: PRODUCT CATALOG ---
    with sub_t1:
        st.subheader("Electronics Product Catalog")
        df_p = load_products_df()

        col_f1, col_f2, col_f3 = st.columns([3, 3, 4])
        cat_filter = col_f1.selectbox("Filter Category", ["All", "Laptops", "Smartphones", "Tablets", "Accessories"])
        max_p = col_f2.slider("Max Budget (₹)", min_value=2000, max_value=150000, value=150000, step=5000)
        search_txt = col_f3.text_input("Search catalog (brand, processor, use case)")

        filtered_df = df_p.copy()
        if cat_filter != "All":
            filtered_df = filtered_df[filtered_df["category"] == cat_filter]
        filtered_df = filtered_df[filtered_df["price_inr"] <= max_p]
        if search_txt:
            filtered_df = filtered_df[
                filtered_df["product_name"].str.contains(search_txt, case=False, na=False) |
                filtered_df["processor"].str.contains(search_txt, case=False, na=False) |
                filtered_df["best_use_case"].str.contains(search_txt, case=False, na=False)
            ]

        st.caption(f"Showing {len(filtered_df)} of {len(df_p)} products")
        cols_to_show = ["product_id", "product_name", "category", "brand", "processor", "ram", "storage", "price_inr", "stock_status", "best_use_case"]
        st.dataframe(filtered_df[cols_to_show], use_container_width=True, hide_index=True)

    # --- SUB-TAB 2: LEADS PIPELINE ---
    with sub_t2:
        st.subheader("Sales Leads Pipeline (SQLite CRM)")
        db = SessionLocal()
        try:
            leads = db.query(Lead).order_by(Lead.updated_at.desc()).all()
            if leads:
                lead_data = [{
                    "ID": l.id,
                    "Customer Name": l.name or "Prospect",
                    "Email": l.email or "—",
                    "Phone": l.phone or "—",
                    "City": l.city or "—",
                    "Category": l.interested_category or "—",
                    "Budget": l.budget or "—",
                    "Score": l.score,
                    "Status": l.qualification_status,
                    "Timeline": l.purchase_timeline or "—",
                    "Last Contact": l.updated_at.strftime("%d %b %Y %H:%M") if l.updated_at else "—"
                } for l in leads]
                st.dataframe(pd.DataFrame(lead_data), use_container_width=True, hide_index=True)
            else:
                st.info("No leads recorded yet.")
        finally:
            db.close()

    # --- SUB-TAB 3: APPOINTMENTS ---
    with sub_t3:
        st.subheader("Store Visits & Consultations")

        # Direct Booking Form
        with st.expander("➕ Book Showroom Visit or Consultation", expanded=False):
            with st.form("book_form"):
                fb1, fb2 = st.columns(2)
                f_name = fb1.text_input("Customer Name *")
                f_email = fb2.text_input("Customer Email *")

                fb3, fb4, fb5 = st.columns(3)
                f_phone = fb3.text_input("Phone Number")
                f_date = fb4.date_input("Preferred Date", value=datetime.date.today() + datetime.timedelta(days=1))
                f_time = fb5.selectbox("Time Slot", ["11:00 AM", "01:00 PM", "03:00 PM", "04:00 PM", "05:30 PM", "07:00 PM"])

                fb6, fb7 = st.columns(2)
                f_type = fb6.selectbox("Appointment Type", ["Store Visit", "Product Consultation", "Sales Callback"])
                f_city = fb7.selectbox("City Showroom", ["Mumbai", "Bengaluru", "New Delhi", "Hyderabad", "Pune", "Ahmedabad", "Kolkata", "Chennai"])
                f_prod = st.text_input("Product of Interest (e.g. CodeMaster Pro 15)")
                f_notes = st.text_area("Notes")

                f_submit = st.form_submit_button("Confirm Booking", type="primary")

                if f_submit:
                    if not f_name or not f_email:
                        st.error("Please enter required name and email.")
                    else:
                        db = SessionLocal()
                        try:
                            ok, msg, appt = book_appointment_in_db(
                                db=db,
                                customer_name=f_name,
                                customer_email=f_email,
                                customer_phone=f_phone,
                                date_val=f_date,
                                time_str=f_time,
                                appointment_type=f_type,
                                interested_product=f_prod,
                                city=f_city,
                                notes=f_notes
                            )
                            if ok:
                                st.success(f"✅ {msg}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                        finally:
                            db.close()

        # Appointments Table
        db = SessionLocal()
        try:
            appts = db.query(Appointment).order_by(Appointment.appointment_date.asc()).all()
            if appts:
                appt_rows = [{
                    "Booking ID": a.appointment_id,
                    "Customer": a.customer_name,
                    "Email": a.customer_email,
                    "Phone": a.customer_phone or "—",
                    "Date": a.appointment_date,
                    "Time": a.appointment_time,
                    "Type": a.appointment_type,
                    "City": a.city,
                    "Product": a.interested_product or "—",
                    "Status": a.status
                } for a in appts]
                st.dataframe(pd.DataFrame(appt_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No appointments currently scheduled.")
        finally:
            db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: SALES INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("📊 Executive Sales Analytics & BI Insights")

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
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Conversations", len(calls), "+3 today")
        m2.metric("Total Leads", total_leads)
        m3.metric("🔥 Hot Leads", hot_leads)
        m4.metric("📅 Demos Booked", len(appts))
        m5.metric("Avg Lead Score", f"{avg_score} / 100")

        st.markdown("---")

        # Row 2 Visual Charts
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

        # Recent Summarized Interactions
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
