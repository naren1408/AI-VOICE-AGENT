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

### Step 5: Store Visit & Appointment Booking
**You (Customer):**
> *"Can I visit your store tomorrow?"*

**Agent (Anya):**
> *"Certainly! What time would be convenient for you?"*

**You (Customer):**
> *"4 PM. My name is Priya Patel, email is priya.patel@example.com, and phone is +91-98791-22334."*

**Agent (Anya):**
> *"Let me check availability and confirm your appointment. Confirmed for tomorrow at 4:00 PM at our showroom! [System: Store demo confirmed for 29 November at 04:00 PM. Calendar invite ready.]"*
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
3. Switch to **Tab 2: Products, Leads & Appointments** to see the newly booked appointment and updated lead in the SQLite CRM!
4. Switch to **Tab 3: Sales Insights** to view updated aggregate analytics!

---

## 🇮🇳 Hindi Scenario (हिंदी में बातचीत)

**Customer:**
> *"नमस्ते, मुझे 50,000 के अंदर कोडिंग के लिए एक अच्छा लैपटॉप चाहिए।"*

**Agent (Anya):**
> *"नमस्ते! 50,000 के बजट में ZenithBook Air 15 (₹48,999) सबसे बढ़िया विकल्प है। इसमें AMD Ryzen 5 प्रोसेसर और 16GB RAM है जो कोडिंग और मल्टीटास्किंग के लिए बहुत उपयुक्त है। क्या आप इस पर छात्र छूट या लाइव डेमो के बारे में जानना चाहते हैं?"*

**Customer:**
> *"क्या इस पर वारंटी मिलेगी?"*

**Agent (Anya):**
> *"हाँ, इस पर 1 साल की आधिकारिक ब्रांड वारंटी और 7 दिन की रिप्लेसमेंट पॉलिसी उपलब्ध है। क्या आप हमारे शोरूम में लाइव डेमो देखना चाहेंगे?"*
