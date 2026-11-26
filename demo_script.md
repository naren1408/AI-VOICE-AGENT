# ElectroMart India — Live Demo Script

Use this script during your placement interview to demonstrate the complete sales pipeline: product inquiry, recommendation, comparison, lead qualification, and appointment booking.

---

## 💻 English Scenario (Programming Laptop & Store Visit)

### Step 1: Initial Requirement & Budget
**You (Customer):**
> *"I am looking for a laptop under ₹70,000."*

**Agent (Anya):**
> *"Sure! What will you mainly use the laptop for?"*
*(Lead status updates to **COLD**; budget recognized as ₹70,000).*

---

### Step 2: Use Case
**You (Customer):**
> *"Programming and multitasking."*

**Agent (Anya):**
> *"Do you have any preferred RAM or processor requirements?"*

---

### Step 3: Specifications & Recommendations
**You (Customer):**
> *"At least 16 GB RAM and a good processor."*

**Agent (Anya):**
> *"Based on your requirements, here are three matching options from our catalog:*
> *1. **CodeMaster Pro 15** (₹64,999) — 13th Gen Intel Core i5, 16GB DDR5 RAM, 2K display.*
> *2. **ZenithBook Air 15** (₹48,999) — AMD Ryzen 5, 16GB RAM, budget-friendly.*
> *3. **DevForge Extreme 16** (₹79,999) — AMD Ryzen 7 with dedicated RTX 3050 GPU for heavy Docker & ML."*
*(Notice the **Recommended Products** card dynamically populates in the right column).*

---

### Step 4: Comparison & Consultation
**You (Customer):**
> *"Which one is best for me?"*

**Agent (Anya):**
> *"Based on your budget and programming requirements, I recommend the **CodeMaster Pro 15** (₹64,999) because its high-performance 13th Gen Intel H-series processor and 16GB DDR5 memory handle multiple IDEs, browser tabs, and local servers effortlessly without lag."*

---

---

### Step 5: Conversational 5-Step Voice Appointment Booking
**You (Customer):**
> *"I want to book an appointment."*

**Agent (Anya):**
> *"Sure! I can help you book an appointment. Could you please fill in your basic details first (your name, phone number, and product of interest)?"*

**You (Customer):**
> *"My name is Priya Patel and my phone number is 9879122334. I am interested in CodeMaster Pro 15."*

**Agent (Anya):**
> *"Thank you, Priya Patel! What date and time would you prefer for your appointment?"*

**You (Customer):**
> *"Tomorrow at 4:00 PM."*

**Agent (Anya):**
> *"Where would you like to have the appointment? Would you prefer a store visit, an online consultation, or a callback?"*

**You (Customer):**
> *"Store visit in Mumbai showroom."*

**Agent (Anya):**
> *"Let me confirm your appointment: Priya Patel, [Tomorrow's Date], 04:00 PM, Store Visit, ElectroMart Experience Centre, Flagship Store, Mumbai. Is everything correct?"*

**You (Customer):**
> *"Yes, confirm!"*

**Agent (Anya):**
> *"Your appointment has been successfully booked. Booking ID: **APT-XXXXXX**. You will receive the confirmation details shortly."*
*(Lead Score jumps to **HOT (95/100)**; green appointment confirmation banner appears; **Download .ICS Invite** button becomes clickable).*

---

### Step 6: End Call & Review CRM Summary
1. Click **"⏹️ End Call & Generate Summary"**.
2. Review the structured executive summary card:
   - Customer: Priya Patel
   - Requirements: Programming and multitasking
   - Recommended Products: CodeMaster Pro 15
   - Lead Status: HOT (95/100)
   - Appointment: Store Visit confirmed
   - Recommended Next Action: Priority follow-up within 24 hours.
3. Open **📅 Appointments & Booking** from the left navigation sidebar to see the newly booked appointment in the database, or manage/edit it!
4. Open **👥 CRM & Leads** to view the qualified lead profile!
5. Open **📊 Business Insights** to view updated aggregate analytics!

---

## 🇮🇳 Accurate Product RAG Inquiries (Technical Specifications)

### 1. Laptop Brands Available
**Customer:** *"What brand laptops are available?"*  
**Agent:** Lists our 7 catalog partner brands: **NovaCorp, Zenith, VoltTech, PulseGaming, Aura, Apex, and GreenTech** with price points and target users.

### 2. Competitor Inquiries (HP / Dell / Apple)
**Customer:** *"Do you have HP laptops?"*  
**Agent:** Explains that ElectroMart carries curated partner brands and directly compares to equivalent catalog models (**CodeMaster Pro 15** or **ZenithBook Air 15**).

### 3. Direct Specification Questions
**Customer:** *"What is the RAM of CodeMaster Pro 15?"*  
**Agent:** *"The ElectroMart catalog lists the **CodeMaster Pro 15** (NovaCorp) with **16GB DDR5**."*

---

## 🇮🇳 Hindi Scenario (हिंदी संवाद्)

**Customer:**
> *"नमस्ते, मुझे गेमिंग और कैमरा के लिए एक अच्छा स्मार्टफोन देखना है।"*

**Agent (Anya):**
> *"नमस्ते! गेमिंग और कैमरा के लिए Pulse Velocity 5G (₹16,999) और Zenith CamPro 5G (₹34,999) शानदार स्मार्टफोन हैं। क्या आप स्टोर विज़िट शेड्यूल करना चाहते हैं?"*

---

## 🇮🇳 Telugu Scenario (తెలుగు సంభాషణ)

**Customer:**
> *"నమస్కారం, నాకు 50,000 లోపు కోడింగ్ కోసం ఒక మంచి లాప్‌టాప్ కావాలి."*

**Agent (Anya):**
> *"నమస్కారం! ₹50,000 బడ్జెట్‌లో ZenithBook Air 15 (₹48,999) మరియు CodeMaster Pro 15 (₹64,999) అత్యుత్తమ ఎంపికలు. వీటిలో 16GB RAM మరియు శక్తివంతమైన ప్రాసెసర్ లభిస్తాయి. మీరు మా షోరూమ్‌లో ప్రత్యక్ష డెమో చూడాలనుకుంటున్నారా?"*

---

## 🇮🇳 Kannada Scenario (ಕನ್ನಡ ಸಂಭಾಷಣೆ)

**Customer:**
> *"ನಮಸ್ಕಾರ, ನನಗೆ 20,000 ಒಳಗೆ ಉತ್ತಮ ಗೇಮಿಂಗ್ ಫೋನ್ ಬೇಕು."*

**Agent (Anya):**
> *"ನಮಸ್ಕಾರ! ₹20,000 ಬಜೆಟ್‌ನಲ್ಲಿ Pulse Velocity 5G (₹16,999) ಅತ್ಯುತ್ತಮ ಸ್ಮಾರ್ಟ್‌ಫೋನ್. ಇದರಲ್ಲಿ Snapdragon 695 5G ಮತ್ತು 120Hz ಸ್ಮೂತ್ ಡಿಸ್ಪ್ಲೇ ಇದೆ. ನೀವು ನಮ್ಮ ಬೆಂಗಳೂರು ಶೋರೂಂ ಭೇಟಿ ಬುಕ್ ಮಾಡಲು ಬಯಸುವಿರಾ?"*
