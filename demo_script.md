# CloudScale AI: Autonomous Sales Voice Agent Demo Script

This script walks through the **13-step Golden Scenario (Section 20-C)**. It works identically in both **Demo Mode** (zero API keys) and **Gemini Mode** (live Google GenAI SDK).

---

## Pre-Demo Checklist
1. Start the FastAPI backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
2. In a separate terminal, launch the Streamlit interface:
   ```bash
   streamlit run app.py
   ```
3. Verify the **Demo Mode** badge is visible in the sidebar (or **Gemini Mode** if you added a key).

---

## Golden Scenario Utterances (Step-by-Step)

### Turn 1: Inquire About Pricing (RAG Knowledge Base Test)
* **What you say / type:**
  > "Hi, can you explain your pricing tiers and how much it costs?"
* **Expected Agent Response:**
  > Retrieves pricing details directly from `company_info.txt`. Explains Starter ($499/mo), Professional ($1,499/mo), and Enterprise ($4,500/mo). Asks about your current infrastructure size.
* **UI Verification:**
  - Notice the **"Knowledge Base Sources Used"** expander populates with retrieved chunks.
  - Sentiment shows as neutral/positive.

---

### Turn 2: Describe Scale & Pain Points (Lead Qualification Trigger)
* **What you say / type:**
  > "We run about 180 Kubernetes nodes on AWS and our compute bill has too much waste."
* **Expected Agent Response:**
  > Acknowledges the infrastructure scale and maps it to the **Professional Tier** (handles up to 250 nodes). Inquires about your implementation budget and timeline.
* **UI Verification:**
  - Need field updates: "Cloud compute optimization & FinOps cost reduction".

---

### Turn 3: Purchase Budget & Timeline (Score Increment)
* **What you say / type:**
  > "Our budget is $1,499 per month and we need to deploy this quarter."
* **Expected Agent Response:**
  > Confirms the budget matches the Professional plan and deployment window. Requests contact details to set up a personalized evaluation.
* **UI Verification:**
  - Budget extracted: `$1,499`.
  - Timeline extracted: `this quarter`.
  - Lead Score jumps to **WARM (50/100)**.

---

### Turn 4: Contact Information & Authority (Hot Lead Conversion)
* **What you say / type:**
  > "I am Sarah Connor, VP of Engineering at Cyberdyne. My email is sarah@cyberdyne.io and I make the technical decisions."
* **Expected Agent Response:**
  > Greets Sarah, verifies decision-maker authority, and immediately offers to book a tailored 30-minute technical demonstration.
* **UI Verification:**
  - Name: `Sarah`, Company: `Cyberdyne`, Email: `sarah@cyberdyne.io`, Decision Maker: `Yes`.
  - Lead Score jumps to **🔥 HOT LEAD (100/100)** with red badge and progress bar.

---

### Turn 5: Multilingual Inbound Inquiry (Hindi Turn)
* **What you say / type:**
  > "नमस्ते, क्या आप मुझे इसके फीचर्स और डेमो के बारे में बता सकते हैं?"
* **Expected Agent Response:**
  > Responds in natural Hindi using `hi-IN-SwaraNeural` voice via Edge-TTS:
  > *"नमस्ते! CloudScale AI आपके क्लाउड खर्च को 45% तक कम करने में मदद करता है। हमारा स्टार्टर प्लान $499 प्रति माह से शुरू होता है। क्या आप 30 मिनट का डेमो देखना चाहेंगे?"*
* **UI Verification:**
  - Spoken Hindi audio stream plays in the UI.

---

### Turn 6: Book Demo Appointment (Transactional Slot Lock)
* **What you say / type:**
  > "Yes, please book a demo for tomorrow 4pm."
* **Expected Agent Response:**
  > Confirms the demo for tomorrow at 4:00 PM. Confirms calendar invite dispatched to `sarah@cyberdyne.io`.
* **UI Verification:**
  - Blue download button appears: **"📅 Download Demo Calendar Invite (.ics)"**.
  - Check Tab 2 ("Leads & Appointments"): The appointment is locked in SQLite.
  - Attempting to book the same slot again will reject with a conflict alert.

---

### Turn 7: End Call & Summarize (Post-Call Intelligence)
* **Action:**
  - Click the **"⏹️ End Call & Summarize"** button in the sidebar.
* **Expected UI Output:**
  - Executive Summary, Key Points, Objections, and Next Steps are displayed.
  - CRM Webhook event is sent.
  - Switch to **"📊 Insights"** Tab: Total calls, demo conversion %, lead score averages, and sentiment charts reflect Sarah's call.
