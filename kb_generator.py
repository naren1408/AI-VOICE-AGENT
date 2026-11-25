"""
ElectroMart India — Knowledge Base Generator
Generates all 8 required RAG documents in knowledge_base/ from synthetic datasets:
1. company_profile.txt
2. product_catalog.txt
3. pricing_and_offers.txt
4. warranty_and_return_policy.txt
5. delivery_and_payment.txt
6. product_recommendation_guide.txt
7. sales_faq.txt
8. comparison_guide.txt
"""
import os
import json
import pandas as pd

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(KB_DIR, exist_ok=True)

df_prod = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
df_offers = pd.read_csv(os.path.join(DATA_DIR, "offers.csv"))
with open(os.path.join(DATA_DIR, "faqs.json"), "r", encoding="utf-8") as f:
    faqs = json.load(f)

# 1. company_profile.txt
company_profile = """# ElectroMart India — Company Profile

## Company Overview
ElectroMart India is a leading fictional multi-brand electronics retail and product advisory chain in India. Founded with the mission to simplify technology buying, ElectroMart India provides certified laptops, smartphones, tablets, and workspace accessories with personalized customer consultation, verified manufacturer warranties, and hassle-free local store support.

## Company Services
- Personalized In-Store & Virtual Product Consultation
- Certified Electronics Retail & Authorized Brand Distribution
- Trade-In / Old Device Exchange Program with instant bonus valuation
- Flexible Financing & 0% No-Cost EMI across 15+ banks
- ElectroMart Extended Care & Accidental Damage Protection
- Open-Box Quality Delivery and Setup Assistance for Laptops and Workstations

## Showroom & Store Details
ElectroMart India operates flagship experience centres across major Indian metropolitan cities:
- Mumbai: Linking Road, Bandra West & Phoenix Marketcity, Kurla
- Bengaluru: 100 Feet Road, Indiranagar & Koramangala 5th Block
- New Delhi: Connaught Place, Block C & Pacific Mall, Tagore Garden
- Hyderabad: Road No. 36, Jubilee Hills & Inorbit Mall, Cyberabad
- Pune: FC Road, Shivajinagar & Phoenix Mall, Viman Nagar
- Ahmedabad: CG Road, Navrangpura
- Kolkata: Park Street & South City Mall
- Chennai: Anna Nagar 2nd Avenue & Express Avenue Mall

## Business Hours
- Monday to Sunday: 10:00 AM to 08:30 PM (All 7 Days)
- AI Sales Voice Agent & Web Advisory: 24/7 Available

## Customer Support & Contact Process
- Toll-Free Helpline: 1800-ELE-MART (1800-353-6278) [9:00 AM – 8:00 PM Daily]
- Email: support@electromart-india.example.com
- Appointment Booking: Available 24/7 via the AI Sales Voice Agent for store demos, hands-on tests, or sales callbacks.
"""
with open(os.path.join(KB_DIR, "company_profile.txt"), "w", encoding="utf-8") as f:
    f.write(company_profile)

# 2. product_catalog.txt
catalog_lines = ["# ElectroMart India — Complete Product Catalog\n\nAll products, prices, and specifications listed below are synthetic demonstration records for ElectroMart India.\n"]
for _, row in df_prod.iterrows():
    catalog_lines.append(f"""## Product: {row['product_name']} ({row['product_id']})
- Category: {row['category']}
- Brand: {row['brand']}
- Price: ₹{row['price_inr']:,} (Inclusive of all taxes)
- Stock Status: {row['stock_status']}
- Processor: {row['processor']}
- RAM: {row['ram']}
- Storage: {row['storage']}
- Graphics: {row['graphics']}
- Display: {row['display']}
- Battery: {row['battery']}
- Warranty: {row['warranty']}
- Best Use Case: {row['best_use_case']}
- Overview: {row['description']}
""")
with open(os.path.join(KB_DIR, "product_catalog.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(catalog_lines))

# 3. pricing_and_offers.txt
pricing_lines = ["""# ElectroMart India — Pricing & Promotional Offers

## Category Pricing Structure
- Budget Laptops: Starting from ₹24,999 to ₹35,000 (Students, Light Browsing)
- Mid-Range & Developer Laptops: ₹48,000 to ₹80,000 (Coding, Office Multitasking)
- Premium & Gaming Laptops: ₹89,000 to ₹1,50,000 (AAA Gaming, VFX, Studio Work)
- Budget Smartphones: ₹11,999 to ₹16,999 (5G Entry, Everyday Utility)
- Mid-Range Smartphones: ₹27,999 to ₹35,000 (OIS Cameras, Fast Charging)
- Flagship Smartphones: ₹64,999 to ₹1,25,000 (Snapdragon 8 Gen 3, Foldables)
- Tablets: ₹9,999 to ₹74,999 (E-Learning to Professional OLED Workstations)
- Accessories: ₹1,999 to ₹4,999 (Keyboards, Mice, ANC Audio, 100W GaN Chargers)

## Active Promotional Offers
"""]
for _, row in df_offers.iterrows():
    pricing_lines.append(f"""### {row['discount_title']} ({row['offer_id']})
- Eligible Category: {row['product_category']}
- Benefit: {row['discount_details']}
- Validity: Up to {row['validity']}
- Terms & Conditions: {row['conditions']}
""")
pricing_lines.append("""
## Financing & Payment Terms
- 0% No-Cost EMI: 3, 6, 9, and 12-month tenures on purchases above ₹20,000 with HDFC, ICICI, SBI, Axis, and Bajaj Finserv.
- Instant Bank Discounts: 10% instant discount (up to ₹3,000) on selected credit and debit cards.
- Trade-In Exchange: Guaranteed value with up to ₹5,000 extra bonus when trading in any working 4G/5G smartphone or laptop.
""")
with open(os.path.join(KB_DIR, "pricing_and_offers.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(pricing_lines))

# 4. warranty_and_return_policy.txt
warranty_doc = """# ElectroMart India — Warranty, Returns & Replacement Policy

## Warranty Coverage
- Standard Warranty: Every electronic product includes a minimum of 1 Year Official Manufacturer Warranty.
- Workstation & Developer Laptops (CodeMaster Pro 15, DevForge Extreme 16): Include 2 Years On-Site Comprehensive Warranty.
- Creative Workstation (StudioCraft Pro 16): Includes 3 Years On-Site Care.
- Foldable Phones (Titan Fold Z): Includes 2 Years Screen Replacement Warranty.
- ElectroMart Extended Care: Customers can purchase 1 or 2 years additional warranty at a 50% discount during checkout.

## 7-Day Replacement Policy
- ElectroMart India offers a 7-day doorstep replacement for products delivered with manufacturing defects, physical transit damage, or hardware malfunctions.
- Requirements for Replacement:
  1. Original outer box and packaging.
  2. All standard accessories, chargers, and manuals included.
  3. Original tax invoice and warranty card.
  4. Device must not have user-inflicted physical cracks or water damage.

## Refund Policy
- If a replacement unit is unavailable in stock within 48 hours of return verification, 100% full refund is issued to the original payment source.
- Online refunds are credited within 3 to 5 business days.

## Service Centre Process
- On-Site Repairs: Available for laptops and large displays across 20+ cities. A certified technician visits your location within 24 to 48 hours.
- Carry-In Service: Walk into any authorized ElectroMart Service Desk located inside our showrooms nationwide.
"""
with open(os.path.join(KB_DIR, "warranty_and_return_policy.txt"), "w", encoding="utf-8") as f:
    f.write(warranty_doc)

# 5. delivery_and_payment.txt
delivery_doc = """# ElectroMart India — Delivery, Payment & Order Processing

## Delivery Timelines & Process
- Express Metro Delivery: 24 to 48 hours across Mumbai, Delhi NCR, Bengaluru, Hyderabad, Chennai, Pune, Ahmedabad, and Kolkata.
- Rest of India: 3 to 5 business days via insured express air couriers.
- Live Tracking: Real-time SMS and WhatsApp updates with GPS tracking for all dispatches.
- Open-Box Inspection: Free open-box inspection on delivery for laptops and flagships above ₹20,000. Customers inspect the physical seal before accepting.

## Payment Methods Accepted
- UPI: Google Pay, PhonePe, Paytm, BHIM (Zero transaction surcharge).
- Credit & Debit Cards: Visa, MasterCard, RuPay, American Express.
- No-Cost EMI: Available on 15+ leading bank credit cards.
- Net Banking: All scheduled commercial banks in India.
- Cash on Delivery (COD): Accepted for orders up to ₹15,000.

## Cancellation Process
- Orders can be cancelled with a single click or phone call before warehouse dispatch for a 100% immediate refund.
"""
with open(os.path.join(KB_DIR, "delivery_and_payment.txt"), "w", encoding="utf-8") as f:
    f.write(delivery_doc)

# 6. product_recommendation_guide.txt
rec_doc = """# ElectroMart India — Product Recommendation Guide

Use these verified guidelines to match customer needs to the best catalog product.

## 1. Laptops for Programming & Software Development
- Budget ₹60,000 to ₹70,000:
  **CodeMaster Pro 15 (₹64,999)**
  - Why: Intel Core i5-13500H (12 cores, 16 threads), 16GB DDR5 RAM, 512GB Gen4 SSD, crisp 2K 100% sRGB display. Perfect for VS Code, Python, Node.js, IntelliJ, and web dev.
- Budget ₹75,000 to ₹85,000:
  **DevForge Extreme 16 (₹79,999)**
  - Why: AMD Ryzen 7 7735HS, 16GB DDR5 (expandable to 64GB), 1TB SSD, and dedicated NVIDIA RTX 3050 6GB GPU. Essential for Docker containers, mobile app emulators, and local machine learning models.

## 2. Laptops for Students & Online Classes
- Budget under ₹35,000:
  **VoltBook Student 14 (₹34,999)**
  - Why: Intel Core i3 12th Gen, 8GB RAM, 256GB SSD, lightweight 1.4kg body, and 8 hours battery. Eligible for Student Tech Pass (₹2,500 extra discount).
- Budget under ₹25,000:
  **EcoBook Lite 15 (₹24,999)**
  - Why: Intel Celeron N4500, 8GB RAM, 128GB+256GB storage. Affordable for basic assignments and Zoom calls.

## 3. Laptops for Gaming & High-End 3D Work
- Budget under ₹1,00,000:
  **CyberPulse G15 (₹94,999)**
  - Why: AMD Ryzen 7 7840HS, 16GB DDR5, 1TB Gen4 SSD, NVIDIA RTX 4060 8GB GDDR6, 165Hz QHD panel. Handles AAA titles at high FPS.

## 4. Smartphones by Use Case
- Best for Photography & Vlogging (₹30,000–₹40,000):
  **Zenith CamPro 5G (₹34,999)** — Triple 50MP Sony sensors with OIS, 4K 60fps recording, 67W fast charging.
- Best for Battery Endurance (Under ₹15,000):
  **Volt PowerMax 5G (₹13,999)** — 6000mAh monster battery lasting 2.5 days.
- Best Flagship All-Rounder (Above ₹60,000):
  **Aura Flagship X (₹64,999)** — Snapdragon 8 Gen 3, titanium body, IP68, 100x periscope zoom.

## 5. Tablets by Use Case
- Best for Digital Sketching & Note-Taking:
  **Zenith Pad Creator 12 (₹38,999)** — 144Hz 3K display, included 4096-level magnetic pressure stylus.
- Best for Students & E-Learning:
  **TabStudy 10.1 (₹14,999)** — TUV certified eye-comfort screen, 7000mAh battery.
"""
with open(os.path.join(KB_DIR, "product_recommendation_guide.txt"), "w", encoding="utf-8") as f:
    f.write(rec_doc)

# 7. sales_faq.txt
faq_lines = ["# ElectroMart India — Sales & Customer Support FAQs\n"]
for item in faqs:
    faq_lines.append(f"""### Q: {item['question']}
- Category: {item['category']}
- Answer: {item['answer']}
""")
with open(os.path.join(KB_DIR, "sales_faq.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(faq_lines))

# 8. comparison_guide.txt
comparison_doc = """# ElectroMart India — Product Comparison Guide

## Comparison 1: Developer Laptops
### CodeMaster Pro 15 vs. DevForge Extreme 16
| Feature | CodeMaster Pro 15 (₹64,999) | DevForge Extreme 16 (₹79,999) |
| :--- | :--- | :--- |
| **Processor** | Intel Core i5 13500H (12 Cores) | AMD Ryzen 7 7735HS (8 Cores, 16 Threads) |
| **RAM** | 16GB DDR5 | 16GB DDR5 (Expandable to 64GB) |
| **Storage** | 512GB Gen4 NVMe SSD | 1TB Gen4 NVMe SSD |
| **Graphics** | Intel Iris Xe (Integrated) | NVIDIA GeForce RTX 3050 6GB Dedicated |
| **Display** | 15.6-inch 2K 100% sRGB | 16-inch WQXGA 120Hz |
| **Weight** | 1.65 kg | 1.95 kg |
| **Best For** | Web dev, Python, microservices, office | Docker, ML/AI, Android emulators, heavy builds |
| **Verdict** | Choose CodeMaster Pro for standard dev within ₹65k. Choose DevForge if you need dedicated GPU & 1TB SSD. |

---

## Comparison 2: Mid-Range 5G Smartphones
### Pulse Velocity 5G vs. Zenith CamPro 5G
| Feature | Pulse Velocity 5G (₹16,999) | Zenith CamPro 5G (₹34,999) |
| :--- | :--- | :--- |
| **Processor** | Snapdragon 695 5G | Snapdragon 7+ Gen 2 |
| **RAM / ROM** | 8GB / 128GB | 12GB / 256GB |
| **Main Camera**| 64MP OIS | Triple 50MP Sony OIS |
| **Display** | 6.67-inch 120Hz AMOLED FHD+ | 6.74-inch 120Hz AMOLED HDR10+ |
| **Charging** | 33W Fast Charge | 67W SuperVOOC |
| **Verdict** | Pulse Velocity is the budget champion. Zenith CamPro is the photography & creator choice. |

---

## Comparison 3: Tablets for Work & Study
### TabStudy 10.1 vs. Zenith Pad Creator 12
| Feature | TabStudy 10.1 (₹14,999) | Zenith Pad Creator 12 (₹38,999) |
| :--- | :--- | :--- |
| **Display** | 10.1-inch FHD 60Hz | 12.4-inch 3K 144Hz |
| **RAM / ROM** | 4GB / 64GB | 8GB / 256GB |
| **Stylus** | Touch Pen Optional | Active Magnetic Pressure Stylus Included |
| **Audio** | Dual Speakers | Quad Dolby Atmos Speakers |
| **Verdict** | TabStudy for student reading & lectures. Zenith Pad for drawing, design & multitasking. |
"""
with open(os.path.join(KB_DIR, "comparison_guide.txt"), "w", encoding="utf-8") as f:
    f.write(comparison_doc)

print("Generated all 8 RAG documents in knowledge_base/.")
