"""
ElectroMart India — Synthetic Dataset Generator
Generates products.csv, customers.csv, sample_leads.csv, sample_conversations.json,
appointments.csv, offers.csv, faqs.json, and data_dictionary.md.
"""
import os
import json
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 1. PRODUCTS (25 products: 8 laptops, 7 phones, 5 tablets, 5 accessories)
products = [
    # Laptops (8)
    {
        "product_id": "LAP-101", "category": "Laptops", "product_name": "VoltBook Student 14",
        "brand": "VoltTech", "processor": "Intel Core i3 12th Gen", "ram": "8GB DDR4",
        "storage": "256GB NVMe SSD", "graphics": "Intel UHD Graphics", "display": "14-inch FHD Anti-Glare",
        "battery": "Up to 8 hours (45Wh)", "price_inr": 34999, "stock_status": "In Stock",
        "warranty": "1 Year Standard Warranty", "best_use_case": "Students / Online Classes / Web Browsing",
        "description": "Affordable and lightweight laptop designed for high school and college students with long battery life."
    },
    {
        "product_id": "LAP-102", "category": "Laptops", "product_name": "ZenithBook Air 15",
        "brand": "Zenith", "processor": "AMD Ryzen 5 5500U", "ram": "16GB DDR4",
        "storage": "512GB NVMe SSD", "graphics": "AMD Radeon Vega 7", "display": "15.6-inch FHD IPS",
        "battery": "Up to 10 hours (54Wh)", "price_inr": 48999, "stock_status": "In Stock",
        "warranty": "1 Year Standard Warranty", "best_use_case": "Office Work / Multitasking / Students",
        "description": "Slim aluminum body with comfortable backlit keyboard, ideal for daily office tasks and productivity."
    },
    {
        "product_id": "LAP-103", "category": "Laptops", "product_name": "CodeMaster Pro 15",
        "brand": "NovaCorp", "processor": "Intel Core i5 13500H", "ram": "16GB DDR5",
        "storage": "512GB Gen4 SSD", "graphics": "Intel Iris Xe", "display": "15.6-inch 2K 100% sRGB",
        "battery": "Up to 9 hours (65Wh)", "price_inr": 64999, "stock_status": "In Stock",
        "warranty": "2 Years On-Site Warranty", "best_use_case": "Programming / Software Development",
        "description": "Engineered for developers: fast 13th Gen H-series processor, 16GB high-speed DDR5 RAM, and high-res screen for code clarity."
    },
    {
        "product_id": "LAP-104", "category": "Laptops", "product_name": "DevForge Extreme 16",
        "brand": "NovaCorp", "processor": "AMD Ryzen 7 7735HS", "ram": "16GB DDR5 (Expandable to 64GB)",
        "storage": "1TB NVMe SSD", "graphics": "NVIDIA GeForce RTX 3050 6GB", "display": "16-inch WQXGA 120Hz",
        "battery": "Up to 8 hours (75Wh)", "price_inr": 79999, "stock_status": "In Stock",
        "warranty": "2 Years Comprehensive Warranty", "best_use_case": "Programming / Docker / Machine Learning",
        "description": "Powerhouse for full-stack developers, mobile app devs, and data scientists running virtual machines and heavy compilers."
    },
    {
        "product_id": "LAP-105", "category": "Laptops", "product_name": "OmniBook Slim 13",
        "brand": "Aura", "processor": "Intel Core i7 1360P", "ram": "16GB LPDDR5",
        "storage": "1TB NVMe SSD", "graphics": "Intel Iris Xe", "display": "13.3-inch OLED 2.8K",
        "battery": "Up to 12 hours (60Wh)", "price_inr": 89999, "stock_status": "In Stock",
        "warranty": "1 Year International Warranty", "best_use_case": "Office Work / Business Travel / Executive",
        "description": "Ultra-portable 1.1kg premium ultrabook featuring a stunning OLED display and all-day battery life."
    },
    {
        "product_id": "LAP-106", "category": "Laptops", "product_name": "CyberPulse G15",
        "brand": "PulseGaming", "processor": "AMD Ryzen 7 7840HS", "ram": "16GB DDR5",
        "storage": "1TB Gen4 SSD", "graphics": "NVIDIA GeForce RTX 4060 8GB GDDR6", "display": "15.6-inch QHD 165Hz",
        "battery": "Up to 6 hours (80Wh)", "price_inr": 94999, "stock_status": "In Stock",
        "warranty": "1 Year Accidental Damage Protection", "best_use_case": "Gaming / Video Editing / 3D Modeling",
        "description": "High-performance gaming machine with liquid metal cooling, MUX switch, and vibrant 165Hz display."
    },
    {
        "product_id": "LAP-107", "category": "Laptops", "product_name": "StudioCraft Pro 16",
        "brand": "Apex", "processor": "Intel Core i9 13900H", "ram": "32GB DDR5",
        "storage": "2TB NVMe SSD", "graphics": "NVIDIA GeForce RTX 4070 8GB Studio", "display": "16-inch 4K Mini-LED 120Hz",
        "battery": "Up to 7 hours (90Wh)", "price_inr": 149999, "stock_status": "Low Stock",
        "warranty": "3 Years On-Site Professional Care", "best_use_case": "Professional Use / Creative Studio / VFX",
        "description": "Ultimate creator workstation with calibrated color accuracy, studio drivers, and massive storage capacity."
    },
    {
        "product_id": "LAP-108", "category": "Laptops", "product_name": "EcoBook Lite 15",
        "brand": "GreenTech", "processor": "Intel Celeron N4500", "ram": "8GB LPDDR4",
        "storage": "128GB eMMC + 256GB SSD", "graphics": "Intel UHD Graphics", "display": "15.6-inch HD",
        "battery": "Up to 9 hours (42Wh)", "price_inr": 24999, "stock_status": "In Stock",
        "warranty": "1 Year Standard Warranty", "best_use_case": "Budget / Students / Casual Browsing",
        "description": "Eco-friendly recycled chassis, basic daily computing for school projects, video streaming, and document editing."
    },

    # Smartphones (7)
    {
        "product_id": "PHN-201", "category": "Smartphones", "product_name": "Apex Phone Neo 5G",
        "brand": "ApexMobile", "processor": "MediaTek Dimensity 6020", "ram": "6GB RAM",
        "storage": "128GB UFS 2.2", "graphics": "Mali-G57", "display": "6.56-inch 90Hz HD+ LCD",
        "battery": "5000mAh with 18W charging", "price_inr": 11999, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Budget / Daily Use / 5G Entry",
        "description": "Affordable 5G smartphone with massive 5000mAh battery and AI dual 50MP rear camera."
    },
    {
        "product_id": "PHN-202", "category": "Smartphones", "product_name": "Pulse Velocity 5G",
        "brand": "PulseMobile", "processor": "Snapdragon 695 5G", "ram": "8GB RAM",
        "storage": "128GB UFS 2.2", "graphics": "Adreno 619", "display": "6.67-inch 120Hz AMOLED FHD+",
        "battery": "5000mAh with 33W Fast Charge", "price_inr": 16999, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Mid-Range / Multimedia / Battery Life",
        "description": "Smooth 120Hz AMOLED screen, stereo speakers, and 64MP OIS camera delivering flagship-grade entertainment."
    },
    {
        "product_id": "PHN-203", "category": "Smartphones", "product_name": "Nova Edge 11 Pro",
        "brand": "NovaCorp", "processor": "MediaTek Dimensity 8200", "ram": "8GB LPDDR5",
        "storage": "256GB UFS 3.1", "graphics": "Mali-G610", "display": "6.7-inch 144Hz 1.5K Curved AMOLED",
        "battery": "4600mAh with 80W TurboCharge", "price_inr": 27999, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Mid-Range / Photography / Fast Charging",
        "description": "Curved edge AMOLED display, 108MP portrait sensor, and 0-50% charge in just 12 minutes."
    },
    {
        "product_id": "PHN-204", "category": "Smartphones", "product_name": "Zenith CamPro 5G",
        "brand": "Zenith", "processor": "Snapdragon 7+ Gen 2", "ram": "12GB LPDDR5",
        "storage": "256GB UFS 3.1", "graphics": "Adreno 725", "display": "6.74-inch 120Hz AMOLED HDR10+",
        "battery": "5000mAh with 67W SuperVOOC", "price_inr": 34999, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Mid-Range Premium / Photography / Gaming",
        "description": "Co-engineered triple 50MP Sony sensor camera system with optical image stabilization and flagship processor."
    },
    {
        "product_id": "PHN-205", "category": "Smartphones", "product_name": "Aura Flagship X",
        "brand": "Aura", "processor": "Snapdragon 8 Gen 3", "ram": "12GB LPDDR5X",
        "storage": "256GB UFS 4.0", "graphics": "Adreno 750", "display": "6.8-inch 120Hz LTPO QHD+ AMOLED",
        "battery": "5400mAh with 100W Wired + 50W Wireless", "price_inr": 64999, "stock_status": "In Stock",
        "warranty": "2 Years VIP Priority Warranty", "best_use_case": "Premium / Flagship Performance / All-Rounder",
        "description": "True flagship experience: titanium alloy frame, periscope telephoto lens with 100x zoom, and IP68 water resistance."
    },
    {
        "product_id": "PHN-206", "category": "Smartphones", "product_name": "Titan Fold Z",
        "brand": "TitanMobile", "processor": "Snapdragon 8 Gen 3", "ram": "16GB LPDDR5X",
        "storage": "512GB UFS 4.0", "graphics": "Adreno 750", "display": "7.9-inch Foldable Dynamic AMOLED 2X",
        "battery": "4800mAh with 45W Fast Charging", "price_inr": 124999, "stock_status": "Low Stock",
        "warranty": "2 Years Screen Replacement Care", "best_use_case": "Premium / Foldable / Executive Productivity",
        "description": "Revolutionary zero-gap hinge foldable smartphone with tablet-sized productivity screen and multi-window multitasking."
    },
    {
        "product_id": "PHN-207", "category": "Smartphones", "product_name": "Volt PowerMax 5G",
        "brand": "VoltTech", "processor": "Snapdragon 4 Gen 2", "ram": "6GB RAM",
        "storage": "128GB Storage", "graphics": "Adreno 613", "display": "6.79-inch 90Hz FHD+ IPS",
        "battery": "6000mAh Monster Battery", "price_inr": 13999, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Battery Life / Delivery Partners / Long Travel",
        "description": "Massive 6000mAh battery providing up to 2.5 days of continuous usage on a single charge."
    },

    # Tablets (5)
    {
        "product_id": "TAB-301", "category": "Tablets", "product_name": "TabStudy 10.1",
        "brand": "VoltTech", "processor": "Octa-Core Helio G80", "ram": "4GB RAM",
        "storage": "64GB (expandable to 512GB)", "graphics": "Mali-G52", "display": "10.1-inch FHD IPS",
        "battery": "7000mAh with 15W charging", "price_inr": 14999, "stock_status": "In Stock",
        "warranty": "1 Year Standard Warranty", "best_use_case": "Students / E-Learning / Reading",
        "description": "Budget student tablet with eye-comfort TUV certification, parental controls, and dual stereo speakers."
    },
    {
        "product_id": "TAB-302", "category": "Tablets", "product_name": "NovaPad Air 11",
        "brand": "NovaCorp", "processor": "Snapdragon 778G", "ram": "6GB LPDDR4X",
        "storage": "128GB UFS 2.2", "graphics": "Adreno 642L", "display": "11-inch 2.5K 120Hz IPS",
        "battery": "8000mAh with 33W Fast Charge", "price_inr": 24999, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Multimedia / Notes / Light Office",
        "description": "Sleek 6.9mm metallic tablet with 120Hz smooth refresh rate and stylus pen support for digital note-taking."
    },
    {
        "product_id": "TAB-303", "category": "Tablets", "product_name": "Zenith Pad Creator 12",
        "brand": "Zenith", "processor": "MediaTek Dimensity 9000", "ram": "8GB LPDDR5",
        "storage": "256GB UFS 3.1", "graphics": "Mali-G710", "display": "12.4-inch 144Hz 3K LCD",
        "battery": "10000mAh with 67W SuperVOOC", "price_inr": 38999, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Digital Art / Sketching / Video Streaming",
        "description": "Creator-focused tablet bundle with magnetic pressure stylus, 4096 pressure levels, and quad Dolby Atmos speakers."
    },
    {
        "product_id": "TAB-304", "category": "Tablets", "product_name": "Aura Slate Pro 13",
        "brand": "Aura", "processor": "Apple M2 Equivalent Custom Octa-Core", "ram": "16GB RAM",
        "storage": "512GB High Speed Storage", "graphics": "Custom 10-Core GPU", "display": "12.9-inch Tandem OLED 120Hz",
        "battery": "10500mAh with 45W Fast Charging", "price_inr": 74999, "stock_status": "In Stock",
        "warranty": "2 Years Premium Care", "best_use_case": "Professional Work / CAD / Music Production",
        "description": "Desktop-class tablet with detachable magnetic keyboard support, thunderbolt port, and ultra-bright 1600 nits OLED."
    },
    {
        "product_id": "TAB-305", "category": "Tablets", "product_name": "EcoTab Mini 8.4",
        "brand": "GreenTech", "processor": "Unisoc T616", "ram": "4GB RAM",
        "storage": "64GB Storage", "graphics": "Mali-G57", "display": "8.4-inch FHD IPS",
        "battery": "5500mAh with 10W charging", "price_inr": 9999, "stock_status": "In Stock",
        "warranty": "1 Year Standard Warranty", "best_use_case": "E-Reader / Commute / Kids",
        "description": "Compact one-hand tablet for book lovers and lightweight reading during daily commutes."
    },

    # Accessories (5)
    {
        "product_id": "ACC-401", "category": "Accessories", "product_name": "Aura SoundBeats ANC Headset",
        "brand": "Aura", "processor": "Custom DSP Audio Chip", "ram": "N/A",
        "storage": "N/A", "graphics": "N/A", "display": "N/A",
        "battery": "Up to 50 hours ANC off / 35h ANC on", "price_inr": 4999, "stock_status": "In Stock",
        "warranty": "1 Year Replacement Warranty", "best_use_case": "Office Calls / Travel / Music",
        "description": "Over-ear wireless headphones with 40mm beryllium drivers, 38dB Active Noise Cancellation and multipoint Bluetooth 5.3."
    },
    {
        "product_id": "ACC-402", "category": "Accessories", "product_name": "Pulse BassBuds Pro TWS",
        "brand": "PulseAudio", "processor": "Bluetooth 5.3 SoC", "ram": "N/A",
        "storage": "N/A", "graphics": "N/A", "display": "N/A",
        "battery": "32 hours total with case (8h earbuds)", "price_inr": 2499, "stock_status": "In Stock",
        "warranty": "1 Year Brand Warranty", "best_use_case": "Gym / Daily Commute / Calls",
        "description": "True wireless earbuds featuring 12mm deep-bass drivers, quad-mic ENC for crystal-clear calls, and IPX5 sweat resistance."
    },
    {
        "product_id": "ACC-403", "category": "Accessories", "product_name": "VoltCharge 100W GaN Desktop Charger",
        "brand": "VoltTech", "processor": "GaNFast Smart IC", "ram": "N/A",
        "storage": "N/A", "graphics": "N/A", "display": "N/A",
        "battery": "N/A (Wall Adapter)", "price_inr": 3499, "stock_status": "In Stock",
        "warranty": "18 Months Replacement Warranty", "best_use_case": "Multi-Device Charging / Laptops & Phones",
        "description": "Ultra-compact Gallium Nitride 4-port charger (3 USB-C + 1 USB-A) capable of powering laptops, phones, and tablets simultaneously."
    },
    {
        "product_id": "ACC-404", "category": "Accessories", "product_name": "MechKeys RGB Wireless Mechanical Keyboard",
        "brand": "NovaCorp", "processor": "Anti-Ghosting Microcontroller", "ram": "N/A",
        "storage": "N/A", "graphics": "N/A", "display": "N/A",
        "battery": "4000mAh rechargeable (up to 200 hours)", "price_inr": 3999, "stock_status": "In Stock",
        "warranty": "1 Year Standard Warranty", "best_use_case": "Coding / Gaming / Office Desk Setup",
        "description": "75% compact hot-swappable mechanical keyboard with pre-lubed red switches, sound-dampening foam, and multi-device pairing."
    },
    {
        "product_id": "ACC-405", "category": "Accessories", "product_name": "PrecisionGlide Ergonomic Wireless Mouse",
        "brand": "NovaCorp", "processor": "PixArt Optical Sensor", "ram": "N/A",
        "storage": "N/A", "graphics": "N/A", "display": "N/A",
        "battery": "Up to 90 days on USB-C charge", "price_inr": 1999, "stock_status": "In Stock",
        "warranty": "1 Year Standard Warranty", "best_use_case": "Ergonomics / Office / Long Working Hours",
        "description": "57-degree natural vertical angle reduces wrist strain, silent click switches, and dual Bluetooth/2.4GHz wireless connectivity."
    }
]

df_prod = pd.DataFrame(products)
df_prod.to_csv(os.path.join(DATA_DIR, "products.csv"), index=False)
print(f"Created products.csv with {len(df_prod)} items.")

# 2. CUSTOMERS (20 realistic synthetic customers)
customers = [
    {"customer_id": "CUST-001", "name": "Aarav Sharma", "email": "aarav.sharma@example.com", "phone": "+91-98201-11223", "city": "Mumbai", "customer_type": "Student"},
    {"customer_id": "CUST-002", "name": "Priya Patel", "email": "priya.patel@example.com", "phone": "+91-98791-22334", "city": "Ahmedabad", "customer_type": "Software Engineer"},
    {"customer_id": "CUST-003", "name": "Rohan Iyer", "email": "rohan.iyer@example.com", "phone": "+91-98401-33445", "city": "Bengaluru", "customer_type": "Startup Founder"},
    {"customer_id": "CUST-004", "name": "Ananya Sen", "email": "ananya.sen@example.com", "phone": "+91-98311-44556", "city": "Kolkata", "customer_type": "Graphic Designer"},
    {"customer_id": "CUST-005", "name": "Vikram Malhotra", "email": "vikram.m@example.com", "phone": "+91-98111-55667", "city": "New Delhi", "customer_type": "Corporate Manager"},
    {"customer_id": "CUST-006", "name": "Sneha Reddy", "email": "sneha.reddy@example.com", "phone": "+91-98491-66778", "city": "Hyderabad", "customer_type": "College Student"},
    {"customer_id": "CUST-007", "name": "Karan Joshi", "email": "karan.j@example.com", "phone": "+91-98221-77889", "city": "Pune", "customer_type": "Freelance Developer"},
    {"customer_id": "CUST-008", "name": "Divya Nair", "email": "divya.nair@example.com", "phone": "+91-98471-88990", "city": "Kochi", "customer_type": "Content Creator"},
    {"customer_id": "CUST-009", "name": "Amitabh Verma", "email": "amitabh.v@example.com", "phone": "+91-98391-99001", "city": "Lucknow", "customer_type": "Business Owner"},
    {"customer_id": "CUST-010", "name": "Meera Das", "email": "meera.das@example.com", "phone": "+91-98611-10112", "city": "Bhubaneswar", "customer_type": "Educator"},
    {"customer_id": "CUST-011", "name": "Siddharth Rao", "email": "sid.rao@example.com", "phone": "+91-98801-21223", "city": "Bengaluru", "customer_type": "DevOps Engineer"},
    {"customer_id": "CUST-012", "name": "Pooja Hegde", "email": "pooja.h@example.com", "phone": "+91-98231-32334", "city": "Mumbai", "customer_type": "Accountant"},
    {"customer_id": "CUST-013", "name": "Aditya Chauhan", "email": "aditya.c@example.com", "phone": "+91-98141-43445", "city": "Chandigarh", "customer_type": "Competitive Gamer"},
    {"customer_id": "CUST-014", "name": "Neha Kulkarni", "email": "neha.k@example.com", "phone": "+91-98241-54556", "city": "Pune", "customer_type": "HR Professional"},
    {"customer_id": "CUST-015", "name": "Rajesh Mehta", "email": "rajesh.m@example.com", "phone": "+91-98781-65667", "city": "Surat", "customer_type": "Retail Merchant"},
    {"customer_id": "CUST-016", "name": "Tanya Bhatia", "email": "tanya.b@example.com", "phone": "+91-98101-76778", "city": "Gurugram", "customer_type": "Marketing Specialist"},
    {"customer_id": "CUST-017", "name": "Naveen Sundaram", "email": "naveen.s@example.com", "phone": "+91-98411-87889", "city": "Chennai", "customer_type": "Systems Architect"},
    {"customer_id": "CUST-018", "name": "Kavita Singh", "email": "kavita.s@example.com", "phone": "+91-98521-98990", "city": "Patna", "customer_type": "Civil Services Aspirant"},
    {"customer_id": "CUST-019", "name": "Gaurav Agarwal", "email": "gaurav.a@example.com", "phone": "+91-98181-09101", "city": "Noida", "customer_type": "Financial Analyst"},
    {"customer_id": "CUST-020", "name": "Deepa Menon", "email": "deepa.m@example.com", "phone": "+91-98461-19202", "city": "Thiruvananthapuram", "customer_type": "Medical Student"}
]
df_cust = pd.DataFrame(customers)
df_cust.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False)
print(f"Created customers.csv with {len(df_cust)} items.")

# 3. SAMPLE LEADS (15 leads connected to customers)
leads = [
    {"customer_id": "CUST-002", "interested_category": "Laptops", "budget": "₹70,000", "requirement": "Laptop for Python and backend programming with 16GB RAM", "purchase_timeline": "Within 7 days", "lead_score": 95, "lead_status": "HOT"},
    {"customer_id": "CUST-003", "interested_category": "Laptops", "budget": "₹90,000", "requirement": "Ultra-lightweight laptop with long battery life for business pitch meetings", "purchase_timeline": "Immediate", "lead_score": 90, "lead_status": "HOT"},
    {"customer_id": "CUST-007", "interested_category": "Laptops", "budget": "₹80,000", "requirement": "Development laptop for full-stack web and Docker environments", "purchase_timeline": "Within 15 days", "lead_score": 85, "lead_status": "HOT"},
    {"customer_id": "CUST-013", "interested_category": "Laptops", "budget": "₹1,00,000", "requirement": "High refresh rate gaming laptop with RTX 4060 graphics", "purchase_timeline": "Within 30 days", "lead_score": 80, "lead_status": "HOT"},
    {"customer_id": "CUST-001", "interested_category": "Laptops", "budget": "₹35,000", "requirement": "Budget laptop for college assignments and online zoom classes", "purchase_timeline": "Next 2 weeks", "lead_score": 75, "lead_status": "HOT"},
    {"customer_id": "CUST-004", "interested_category": "Tablets", "budget": "₹40,000", "requirement": "Tablet with high-precision stylus support for digital illustration", "purchase_timeline": "This month", "lead_score": 65, "lead_status": "WARM"},
    {"customer_id": "CUST-005", "interested_category": "Smartphones", "budget": "₹65,000", "requirement": "Premium flagship smartphone with excellent telephoto camera and battery", "purchase_timeline": "Within 45 days", "lead_score": 60, "lead_status": "WARM"},
    {"customer_id": "CUST-008", "interested_category": "Smartphones", "budget": "₹35,000", "requirement": "Camera smartphone for social media vlog reels and short video shooting", "purchase_timeline": "Next month", "lead_score": 55, "lead_status": "WARM"},
    {"customer_id": "CUST-011", "interested_category": "Accessories", "budget": "₹5,000", "requirement": "Wireless mechanical keyboard for home office coding desk setup", "purchase_timeline": "Exploring options", "lead_score": 50, "lead_status": "WARM"},
    {"customer_id": "CUST-006", "interested_category": "Tablets", "budget": "₹15,000", "requirement": "Affordable tablet for PDF reading and video lectures", "purchase_timeline": "Within 60 days", "lead_score": 45, "lead_status": "WARM"},
    {"customer_id": "CUST-009", "interested_category": "Smartphones", "budget": "₹20,000", "requirement": "Dual-SIM phone with durable battery for retail shop communication", "purchase_timeline": "Within 2 months", "lead_score": 40, "lead_status": "WARM"},
    {"customer_id": "CUST-015", "interested_category": "Laptops", "budget": "Undecided", "requirement": "Looking at laptop prices for accounting software next year", "purchase_timeline": "Next year", "lead_score": 25, "lead_status": "COLD"},
    {"customer_id": "CUST-010", "interested_category": "Tablets", "budget": "Undecided", "requirement": "Just researching tablet options for school classroom integration", "purchase_timeline": "No fixed timeline", "lead_score": 20, "lead_status": "COLD"},
    {"customer_id": "CUST-012", "interested_category": "Accessories", "budget": "₹2,000", "requirement": "Browsing ergonomic mouse alternatives", "purchase_timeline": "Not decided", "lead_score": 20, "lead_status": "COLD"},
    {"customer_id": "CUST-018", "interested_category": "Laptops", "budget": "₹25,000", "requirement": "General enquiry about lowest price laptop", "purchase_timeline": "Unknown", "lead_score": 15, "lead_status": "COLD"}
]
df_leads = pd.DataFrame(leads)
df_leads.to_csv(os.path.join(DATA_DIR, "sample_leads.csv"), index=False)
print(f"Created sample_leads.csv with {len(df_leads)} items.")

# 4. OFFERS (10 promotional offers)
offers = [
    {"offer_id": "OFFER-01", "product_category": "Laptops", "discount_title": "Student Tech Pass", "discount_details": "Flat ₹2,500 off on all laptops with valid student ID", "validity": "31-Dec-2026", "conditions": "Applicable on laptops above ₹30,000. Online & In-store."},
    {"offer_id": "OFFER-02", "product_category": "Laptops", "discount_title": "Developer Power Bundle", "discount_details": "Free MechKeys Wireless Keyboard with CodeMaster Pro 15", "validity": "30-Nov-2026", "conditions": "Valid on CodeMaster Pro 15 and DevForge Extreme 16."},
    {"offer_id": "OFFER-03", "product_category": "Smartphones", "discount_title": "5G Upgrade Exchange Bonus", "discount_details": "Up to ₹5,000 extra exchange bonus on trading any 4G phone", "validity": "31-Dec-2026", "conditions": "Old phone must be in working condition with original IMEI."},
    {"offer_id": "OFFER-04", "product_category": "Smartphones", "discount_title": "Festive Card Cashback", "discount_details": "Instant 10% cashback up to ₹3,000 on HDFC and ICICI cards", "validity": "15-Dec-2026", "conditions": "Minimum transaction value ₹15,000. Valid on credit & debit EMI."},
    {"offer_id": "OFFER-05", "product_category": "Tablets", "discount_title": "Stylus Bundle Special", "discount_details": "Get magnetic pressure stylus for ₹999 (regular ₹2,999) with Zenith Pad", "validity": "31-Dec-2026", "conditions": "Applies to Zenith Pad Creator 12 and NovaPad Air 11."},
    {"offer_id": "OFFER-06", "product_category": "Accessories", "discount_title": "Work-From-Home Duo", "discount_details": "Buy Keyboard and Mouse together, save flat ₹1,000", "validity": "31-Dec-2026", "conditions": "Valid on MechKeys Keyboard + PrecisionGlide Mouse combo."},
    {"offer_id": "OFFER-07", "product_category": "All Categories", "discount_title": "No-Cost EMI 12 Months", "discount_details": "0% interest EMI for up to 12 months across all leading banks", "validity": "31-Dec-2026", "conditions": "Cart value above ₹20,000 on major credit cards."},
    {"offer_id": "OFFER-08", "product_category": "Laptops", "discount_title": "Extended Care Protection", "discount_details": "2nd Year Warranty extension at 50% discount", "validity": "31-Dec-2026", "conditions": "Must be added at time of laptop purchase."},
    {"offer_id": "OFFER-09", "product_category": "Accessories", "discount_title": "SoundBeats Intro Offer", "discount_details": "Flat ₹1,000 discount on Aura SoundBeats ANC Headset", "validity": "30-Nov-2026", "conditions": "Promotional coupon code: SOUND1000."},
    {"offer_id": "OFFER-10", "product_category": "Smartphones", "discount_title": "Screen Shield Guarantee", "discount_details": "1-time free screen replacement for 6 months on Flagship X", "validity": "31-Dec-2026", "conditions": "Valid on Aura Flagship X and Titan Fold Z."}
]
df_offers = pd.DataFrame(offers)
df_offers.to_csv(os.path.join(DATA_DIR, "offers.csv"), index=False)
print(f"Created offers.csv with {len(df_offers)} items.")

# 5. APPOINTMENTS (10 appointments)
appointments = [
    {"appointment_id": "APT-501", "customer_name": "Priya Patel", "customer_email": "priya.patel@example.com", "customer_phone": "+91-98791-22334", "date": "2026-11-28", "time": "04:00 PM", "appointment_type": "Store Visit", "interested_product": "CodeMaster Pro 15", "city": "Ahmedabad", "status": "Confirmed", "notes": "Customer wants hands-on demo with keyboard and terminal."},
    {"appointment_id": "APT-502", "customer_name": "Rohan Iyer", "customer_email": "rohan.iyer@example.com", "customer_phone": "+91-98401-33445", "date": "2026-11-29", "time": "11:30 AM", "appointment_type": "Product Consultation", "interested_product": "OmniBook Slim 13", "city": "Bengaluru", "status": "Confirmed", "notes": "Checking lightweight ultrabook options for travel."},
    {"appointment_id": "APT-503", "customer_name": "Aditya Chauhan", "customer_email": "aditya.c@example.com", "customer_phone": "+91-98141-43445", "date": "2026-11-29", "time": "03:00 PM", "appointment_type": "Store Visit", "interested_product": "CyberPulse G15", "city": "Chandigarh", "status": "Confirmed", "notes": "Wants to test thermals and FPS on display unit."},
    {"appointment_id": "APT-504", "customer_name": "Ananya Sen", "customer_email": "ananya.sen@example.com", "customer_phone": "+91-98311-44556", "date": "2026-11-30", "time": "02:00 PM", "appointment_type": "Store Visit", "interested_product": "Zenith Pad Creator 12", "city": "Kolkata", "status": "Confirmed", "notes": "Testing stylus latency and pressure curves."},
    {"appointment_id": "APT-505", "customer_name": "Vikram Malhotra", "customer_email": "vikram.m@example.com", "customer_phone": "+91-98111-55667", "date": "2026-12-01", "time": "05:00 PM", "appointment_type": "Sales Callback", "interested_product": "Aura Flagship X", "city": "New Delhi", "status": "Scheduled", "notes": "Corporate bulk order discussion for 10 units."},
    {"appointment_id": "APT-506", "customer_name": "Karan Joshi", "customer_email": "karan.j@example.com", "customer_phone": "+91-98221-77889", "date": "2026-12-02", "time": "10:30 AM", "appointment_type": "Store Visit", "interested_product": "DevForge Extreme 16", "city": "Pune", "status": "Scheduled", "notes": "Evaluating 32GB RAM upgrade feasibility."},
    {"appointment_id": "APT-507", "customer_name": "Aarav Sharma", "customer_email": "aarav.sharma@example.com", "customer_phone": "+91-98201-11223", "date": "2026-12-02", "time": "01:00 PM", "appointment_type": "Store Visit", "interested_product": "VoltBook Student 14", "city": "Mumbai", "status": "Scheduled", "notes": "Applying Student Tech Pass offer discount."},
    {"appointment_id": "APT-508", "customer_name": "Divya Nair", "customer_email": "divya.nair@example.com", "customer_phone": "+91-98471-88990", "date": "2026-12-03", "time": "04:30 PM", "appointment_type": "Product Consultation", "interested_product": "Zenith CamPro 5G", "city": "Kochi", "status": "Scheduled", "notes": "Camera sample inspection in outdoor lighting."},
    {"appointment_id": "APT-509", "customer_name": "Siddharth Rao", "customer_email": "sid.rao@example.com", "customer_phone": "+91-98801-21223", "date": "2026-12-04", "time": "06:00 PM", "appointment_type": "Sales Callback", "interested_product": "MechKeys Wireless Keyboard", "city": "Bengaluru", "status": "Scheduled", "notes": "Enquiring about brown switch option."},
    {"appointment_id": "APT-510", "customer_name": "Sneha Reddy", "customer_email": "sneha.reddy@example.com", "customer_phone": "+91-98491-66778", "date": "2026-11-26", "time": "11:00 AM", "appointment_type": "Store Visit", "interested_product": "TabStudy 10.1", "city": "Hyderabad", "status": "Completed", "notes": "Demo completed, purchased with 1 year warranty."}
]
df_apt = pd.DataFrame(appointments)
df_apt.to_csv(os.path.join(DATA_DIR, "appointments.csv"), index=False)
print(f"Created appointments.csv with {len(df_apt)} items.")

# 6. FAQS (25 detailed electronics retail FAQs)
faqs = [
    {"faq_id": "FAQ-01", "category": "Warranty", "question": "What is the warranty period on laptops sold at ElectroMart India?", "answer": "All laptops come with an official manufacturer warranty ranging from 1 to 3 years. We also offer ElectroMart Extended Care providing an additional 1 or 2 years of coverage."},
    {"faq_id": "FAQ-02", "category": "Returns", "question": "What is the replacement and return policy?", "answer": "We offer a 7-day hassle-free replacement policy for defective or damaged electronics. The product must have original box, accessories, and invoice."},
    {"faq_id": "FAQ-03", "category": "Payment", "question": "What payment methods do you accept?", "answer": "We accept UPI (Google Pay, PhonePe, Paytm), Credit & Debit cards (Visa, MasterCard, RuPay), Net Banking, and Cash on Delivery up to ₹15,000."},
    {"faq_id": "FAQ-04", "category": "Offers", "question": "Are there any No-Cost EMI options available?", "answer": "Yes! We provide 0% interest No-Cost EMI for 3, 6, 9, and 12 months on all purchases above ₹20,000 with major credit cards and Bajaj Finserv."},
    {"faq_id": "FAQ-05", "category": "Delivery", "question": "How long does standard delivery take?", "answer": "Standard metro delivery takes 24 to 48 hours. Tier-2 and Tier-3 cities receive delivery within 3 to 5 business days with live GPS tracking."},
    {"faq_id": "FAQ-06", "category": "Store Visit", "question": "Can I test products hands-on in the physical store?", "answer": "Yes! You can book an appointment with our AI agent to visit your nearest ElectroMart showroom for a dedicated hands-on demo with an expert."},
    {"faq_id": "FAQ-07", "category": "Programming", "question": "Which laptop is recommended for coding and software development?", "answer": "The CodeMaster Pro 15 (₹64,999) and DevForge Extreme 16 (₹79,999) are top picks. Both offer fast H-series processors, 16GB DDR5 RAM, and high-resolution displays."},
    {"faq_id": "FAQ-08", "category": "Students", "question": "What is the best budget laptop for students?", "answer": "The VoltBook Student 14 at ₹34,999 with 8GB RAM, 256GB SSD, and 8 hours of battery life is our most popular student choice."},
    {"faq_id": "FAQ-09", "category": "Exchange", "question": "Do you offer exchange value on old phones or laptops?", "answer": "Yes, our Trade-In program offers up to ₹5,000 extra exchange bonus over market valuation on working old devices with valid IMEI/serial numbers."},
    {"faq_id": "FAQ-10", "category": "Battery", "question": "Which smartphone has the longest battery life?", "answer": "The Volt PowerMax 5G (₹13,999) features a massive 6000mAh monster battery that lasts up to 2.5 days on normal usage."},
    {"faq_id": "FAQ-11", "category": "Gaming", "question": "What gaming laptop under ₹1,00,000 is available?", "answer": "The CyberPulse G15 at ₹94,999 features an AMD Ryzen 7 7840HS, 16GB DDR5, and NVIDIA RTX 4060 8GB GPU with a 165Hz QHD panel."},
    {"faq_id": "FAQ-12", "category": "Tablets", "question": "Does the tablet come with a stylus pen included?", "answer": "The Zenith Pad Creator 12 includes the magnetic stylus in the box. For the NovaPad Air 11, the stylus is sold separately or at a discount bundle."},
    {"faq_id": "FAQ-13", "category": "Business Hours", "question": "What are ElectroMart showroom hours?", "answer": "Showrooms are open Monday through Sunday from 10:00 AM to 08:30 PM. Sales consultations can be booked anytime."},
    {"faq_id": "FAQ-14", "category": "Accessories", "question": "Does the VoltCharge 100W GaN charger support laptops?", "answer": "Yes! Its USB-C Power Delivery 3.0 ports output up to 100W, sufficient to fast-charge MacBooks, Dell, HP, Lenovo, and NovaCorp laptops."},
    {"faq_id": "FAQ-15", "category": "RAM Upgrade", "question": "Can I upgrade RAM on the laptops after purchase?", "answer": "The CodeMaster Pro 15, DevForge Extreme 16, and ZenithBook Air 15 have upgradeable RAM slots without voiding the warranty."},
    {"faq_id": "FAQ-16", "category": "Offers", "question": "Is there a student discount available?", "answer": "Yes! Our Student Tech Pass offer gives a flat ₹2,500 instant discount on laptops above ₹30,000 with a verified student ID."},
    {"faq_id": "FAQ-17", "category": "Cancellation", "question": "Can I cancel an order before dispatch?", "answer": "Yes, orders can be cancelled with 100% full refund through the customer portal or helpline before shipping."},
    {"faq_id": "FAQ-18", "category": "Photography", "question": "Which smartphone has optical image stabilization (OIS)?", "answer": "Both the Pulse Velocity 5G (₹16,999), Zenith CamPro 5G (₹34,999), and Aura Flagship X (₹64,999) feature hardware OIS."},
    {"faq_id": "FAQ-19", "category": "Foldables", "question": "What warranty does the Titan Fold Z have on its folding screen?", "answer": "The Titan Fold Z includes 2 years of VIP screen protection with a 1-time free inner screen replacement."},
    {"faq_id": "FAQ-20", "category": "Support", "question": "How do I reach customer support?", "answer": "Contact support via toll-free 1800-ELE-MART (1800-353-6278) or email support@electromart-india.example.com from 9 AM to 8 PM daily."},
    {"faq_id": "FAQ-21", "category": "Tablets", "question": "Can tablets be connected to external keyboards and monitors?", "answer": "Yes, Aura Slate Pro 13 and Zenith Pad Creator 12 support Type-C display output and magnetic/Bluetooth keyboard accessories."},
    {"faq_id": "FAQ-22", "category": "Delivery", "question": "Do you offer open-box delivery?", "answer": "Yes, open-box inspection is available across 15 major metro cities for all electronics priced above ₹20,000."},
    {"faq_id": "FAQ-23", "category": "Headphones", "question": "How effective is the ANC on Aura SoundBeats?", "answer": "Aura SoundBeats provides hybrid active noise cancellation up to 38dB, blocking low-frequency engine and office chatter."},
    {"faq_id": "FAQ-24", "category": "GST", "question": "Can I get a GST business tax invoice for input credit?", "answer": "Yes, simply enter your company name and 15-digit GSTIN during checkout or consultation to receive a compliant GST tax invoice."},
    {"faq_id": "FAQ-25", "category": "Appointment", "question": "Can I reschedule my booked store appointment?", "answer": "Yes, you can easily reschedule anytime by providing your appointment ID or email to our sales agent or helpline."}
]
with open(os.path.join(DATA_DIR, "faqs.json"), "w", encoding="utf-8") as f:
    json.dump(faqs, f, indent=2)
print(f"Created faqs.json with {len(faqs)} items.")

# 7. SAMPLE CONVERSATIONS (10 complete realistic dialogues)
conversations = [
    {
        "conversation_id": "CONV-001",
        "customer_id": "CUST-002",
        "customer_name": "Priya Patel",
        "category": "Laptops",
        "turns": [
            {"speaker": "customer", "text": "I am looking for a laptop under ₹70,000."},
            {"speaker": "agent", "text": "Sure! What will you mainly use the laptop for?"},
            {"speaker": "customer", "text": "Programming and multitasking."},
            {"speaker": "agent", "text": "Do you have any preferred RAM or processor requirements?"},
            {"speaker": "customer", "text": "At least 16 GB RAM and a good processor."},
            {"speaker": "agent", "text": "Based on your requirements, here are three matching options: CodeMaster Pro 15 (₹64,999, i5-13500H, 16GB DDR5), ZenithBook Air 15 (₹48,999, Ryzen 5, 16GB), and DevForge Extreme 16 (₹79,999)."},
            {"speaker": "customer", "text": "Which one is best for me?"},
            {"speaker": "agent", "text": "Based on your budget and programming requirements, I recommend the CodeMaster Pro 15 (₹64,999) because its high-performance 13th Gen Intel H-series CPU and 16GB DDR5 RAM handle code compilation and IDEs effortlessly."},
            {"speaker": "customer", "text": "Can I visit your store tomorrow?"},
            {"speaker": "agent", "text": "Certainly! What time would be convenient for you?"},
            {"speaker": "customer", "text": "4 PM."},
            {"speaker": "agent", "text": "Let me check availability and confirm your appointment. Confirmed for tomorrow at 4:00 PM at our showroom!"}
        ],
        "outcome": "Appointment Booked (APT-501)",
        "recommended_product": "CodeMaster Pro 15",
        "lead_score": 95,
        "lead_status": "HOT"
    },
    {
        "conversation_id": "CONV-002",
        "customer_id": "CUST-001",
        "category": "Laptops",
        "turns": [
            {"speaker": "customer", "text": "I need a budget laptop for college studies around 35k."},
            {"speaker": "agent", "text": "Hello! The VoltBook Student 14 is perfect for college coursework at ₹34,999. It features an Intel Core i3 12th Gen, 8GB RAM, and 256GB SSD with 8 hours battery life."},
            {"speaker": "customer", "text": "Are there student discounts?"},
            {"speaker": "agent", "text": "Yes! Our Student Tech Pass offer gives you an instant ₹2,500 discount with your student ID, bringing the price down to ₹32,499."},
            {"speaker": "customer", "text": "Great, I will visit the showroom this weekend."}
        ],
        "outcome": "Showroom Lead Created",
        "recommended_product": "VoltBook Student 14",
        "lead_score": 75,
        "lead_status": "HOT"
    },
    {
        "conversation_id": "CONV-003",
        "customer_id": "CUST-013",
        "category": "Laptops",
        "turns": [
            {"speaker": "customer", "text": "Looking for a heavy gaming laptop with RTX graphics under 1 lakh."},
            {"speaker": "agent", "text": "I recommend the CyberPulse G15 at ₹94,999. It is equipped with AMD Ryzen 7 7840HS, 16GB DDR5, and NVIDIA RTX 4060 8GB graphics with a 165Hz QHD screen."},
            {"speaker": "customer", "text": "Does it have heating issues?"},
            {"speaker": "agent", "text": "The CyberPulse G15 features dual fans with liquid metal thermal compound, keeping sustained CPU temperatures below 82 degrees during AAA gaming."}
        ],
        "outcome": "Warm Gaming Enquiry",
        "recommended_product": "CyberPulse G15",
        "lead_score": 80,
        "lead_status": "HOT"
    },
    {
        "conversation_id": "CONV-004",
        "customer_id": "CUST-004",
        "category": "Tablets",
        "turns": [
            {"speaker": "customer", "text": "Need a tablet for digital sketching and illustration under 40k."},
            {"speaker": "agent", "text": "The Zenith Pad Creator 12 at ₹38,999 is custom-built for digital art, featuring a 144Hz 3K display, Dimensity 9000, and magnetic stylus with 4096 pressure levels."},
            {"speaker": "customer", "text": "Can I test the pen in store?"},
            {"speaker": "agent", "text": "Yes! I can book a hands-on slot for you at our Kolkata store."}
        ],
        "outcome": "Stylus Consultation Booked",
        "recommended_product": "Zenith Pad Creator 12",
        "lead_score": 65,
        "lead_status": "WARM"
    },
    {
        "conversation_id": "CONV-005",
        "customer_id": "CUST-005",
        "category": "Smartphones",
        "turns": [
            {"speaker": "customer", "text": "What is your best premium smartphone for executive use?"},
            {"speaker": "agent", "text": "Our flagship is the Aura Flagship X (₹64,999) with Snapdragon 8 Gen 3, titanium body, IP68 water resistance, and 100x zoom periscope camera."},
            {"speaker": "customer", "text": "Do you offer corporate GST invoices?"},
            {"speaker": "agent", "text": "Yes, we provide full GST input tax invoices for all corporate and business purchases."}
        ],
        "outcome": "Corporate Sales Lead",
        "recommended_product": "Aura Flagship X",
        "lead_score": 60,
        "lead_status": "WARM"
    },
    {
        "conversation_id": "CONV-006",
        "customer_id": "CUST-008",
        "category": "Smartphones",
        "turns": [
            {"speaker": "customer", "text": "I want a phone with great camera under 35,000 for reels."},
            {"speaker": "agent", "text": "The Zenith CamPro 5G at ₹34,999 is exceptional for video and reels. It has triple 50MP Sony sensors with Optical Image Stabilization and 4K 60fps recording."},
            {"speaker": "customer", "text": "How fast is the charging?"},
            {"speaker": "agent", "text": "It includes 67W SuperVOOC charging, reaching 100% battery in just 38 minutes."}
        ],
        "outcome": "Camera Consultation",
        "recommended_product": "Zenith CamPro 5G",
        "lead_score": 55,
        "lead_status": "WARM"
    },
    {
        "conversation_id": "CONV-007",
        "customer_id": "CUST-011",
        "category": "Accessories",
        "turns": [
            {"speaker": "customer", "text": "Do you have mechanical keyboards for programming?"},
            {"speaker": "agent", "text": "Yes! The MechKeys RGB Wireless Keyboard (₹3,999) has pre-lubed red linear switches, 75% compact layout, and pairs with up to 3 devices."},
            {"speaker": "customer", "text": "Is there an offer if I buy a mouse too?"},
            {"speaker": "agent", "text": "Yes! Our Work-From-Home Duo offer gives you ₹1,000 off when bundled with the PrecisionGlide Ergonomic Mouse."}
        ],
        "outcome": "Accessory Bundle Lead",
        "recommended_product": "MechKeys RGB Wireless Mechanical Keyboard",
        "lead_score": 50,
        "lead_status": "WARM"
    },
    {
        "conversation_id": "CONV-008",
        "customer_id": "CUST-015",
        "category": "Laptops",
        "turns": [
            {"speaker": "customer", "text": "What are your general laptop price ranges?"},
            {"speaker": "agent", "text": "Our laptops range from ₹24,999 for the EcoBook Lite up to ₹1,49,999 for the StudioCraft Pro 16. Most student and office laptops fall between ₹35,000 and ₹65,000."},
            {"speaker": "customer", "text": "Okay, I will think about it next year."}
        ],
        "outcome": "Cold Info Request",
        "recommended_product": "VoltBook Student 14",
        "lead_score": 25,
        "lead_status": "COLD"
    },
    {
        "conversation_id": "CONV-009",
        "customer_id": "CUST-002",
        "category": "Hindi Consultation",
        "turns": [
            {"speaker": "customer", "text": "मुझे 50,000 के अंदर कोडिंग के लिए एक अच्छा लैपटॉप चाहिए।"},
            {"speaker": "agent", "text": "नमस्ते! 50,000 के बजट में ZenithBook Air 15 (₹48,999) सबसे बढ़िया विकल्प है। इसमें AMD Ryzen 5 प्रोसेसर और 16GB RAM है जो कोडिंग के लिए बहुत उपयुक्त है।"},
            {"speaker": "customer", "text": "क्या इस पर वारंटी मिलेगी?"},
            {"speaker": "agent", "text": "हाँ, इस पर 1 साल की आधिकारिक वारंटी और 7 दिन की रिप्लेसमेंट पॉलिसी उपलब्ध है।"}
        ],
        "outcome": "Hindi Consultation Completed",
        "recommended_product": "ZenithBook Air 15",
        "lead_score": 85,
        "lead_status": "HOT"
    },
    {
        "conversation_id": "CONV-010",
        "customer_id": "CUST-007",
        "category": "Laptops",
        "turns": [
            {"speaker": "customer", "text": "Compare CodeMaster Pro 15 and DevForge Extreme 16 please."},
            {"speaker": "agent", "text": "Certainly! CodeMaster Pro 15 (₹64,999) has Intel i5 13500H with Iris Xe graphics, ideal for standard software dev. DevForge Extreme 16 (₹79,999) adds an RTX 3050 GPU, Ryzen 7, and 1TB SSD, making it better for machine learning, Docker, and Android emulators."},
            {"speaker": "customer", "text": "DevForge looks worth the extra ₹15,000. Let me book a callback."}
        ],
        "outcome": "Callback Requested",
        "recommended_product": "DevForge Extreme 16",
        "lead_score": 85,
        "lead_status": "HOT"
    }
]
with open(os.path.join(DATA_DIR, "sample_conversations.json"), "w", encoding="utf-8") as f:
    json.dump(conversations, f, indent=2)
print(f"Created sample_conversations.json with {len(conversations)} items.")

# 8. DATA DICTIONARY
data_dict = """# ElectroMart India — Data Dictionary

This document describes all synthetic datasets provided in the `data/` directory for ElectroMart India demonstration.

---

## 1. `products.csv`
Contains the complete synthetic electronics retail catalog (25 products).

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `product_id` | String | Unique product identifier | `LAP-101` |
| `category` | String | High-level category (Laptops, Smartphones, Tablets, Accessories) | `Laptops` |
| `product_name` | String | Fictional commercial product title | `CodeMaster Pro 15` |
| `brand` | String | Fictional brand name | `NovaCorp` |
| `processor` | String | Processor specification | `Intel Core i5 13500H` |
| `ram` | String | Memory capacity and generation | `16GB DDR5` |
| `storage` | String | Storage capacity and interface | `512GB Gen4 SSD` |
| `graphics` | String | Display / GPU controller | `Intel Iris Xe` |
| `display` | String | Screen diagonal, resolution, panel type | `15.6-inch 2K 100% sRGB` |
| `battery` | String | Battery endurance & watt-hours | `Up to 9 hours (65Wh)` |
| `price_inr` | Integer | Selling price in Indian Rupees (INR) | `64999` |
| `stock_status` | String | Stock availability (In Stock, Low Stock, Out of Stock) | `In Stock` |
| `warranty` | String | Warranty duration and coverage terms | `2 Years On-Site Warranty` |
| `best_use_case` | String | Target persona or workflow | `Programming / Software Development` |
| `description` | String | Marketing narrative and key features | `Engineered for developers...` |

---

## 2. `customers.csv`
Synthetic customer profile records (20 customers).

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `customer_id` | String | Unique customer identifier | `CUST-002` |
| `name` | String | Full name | `Priya Patel` |
| `email` | String | Fictional example email domain | `priya.patel@example.com` |
| `phone` | String | Fictional contact number | `+91-98791-22334` |
| `city` | String | Indian metropolitan city | `Ahmedabad` |
| `customer_type` | String | Customer persona / profession | `Software Engineer` |

---

## 3. `sample_leads.csv`
Sales opportunity qualification pipeline records (15 leads).

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `customer_id` | String | Reference to `customers.csv` | `CUST-002` |
| `interested_category` | String | Product category sought | `Laptops` |
| `budget` | String | Target budget range | `₹70,000` |
| `requirement` | String | Specific functional requirement | `Laptop for Python with 16GB RAM` |
| `purchase_timeline` | String | Expected purchase window | `Within 7 days` |
| `lead_score` | Integer | BANT score (0-100) | `95` |
| `lead_status` | String | Priority band: HOT (>=70), WARM (40-69), COLD (<40) | `HOT` |

---

## 4. `offers.csv`
Active promotional discounts and seasonal campaigns (10 offers).

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `offer_id` | String | Unique offer code | `OFFER-01` |
| `product_category` | String | Eligible category or All | `Laptops` |
| `discount_title` | String | Campaign title | `Student Tech Pass` |
| `discount_details` | String | Commercial terms | `Flat ₹2,500 off with student ID` |
| `validity` | String | Expiry date | `31-Dec-2026` |
| `conditions` | String | Applicability constraints | `Laptops above ₹30,000` |

---

## 5. `appointments.csv`
Scheduled customer store visits and sales consultations (10 appointments).

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `appointment_id` | String | Unique booking reference | `APT-501` |
| `customer_name` | String | Customer name | `Priya Patel` |
| `customer_email` | String | Customer email | `priya.patel@example.com` |
| `customer_phone` | String | Contact phone | `+91-98791-22334` |
| `date` | String | Appointment date (YYYY-MM-DD) | `2026-11-28` |
| `time` | String | Time slot (HH:MM AM/PM) | `04:00 PM` |
| `appointment_type` | String | Store Visit, Product Consultation, Sales Callback | `Store Visit` |
| `interested_product`| String | Specific model requested | `CodeMaster Pro 15` |
| `city` | String | Showroom location | `Ahmedabad` |
| `status` | String | Confirmed, Scheduled, Completed, Cancelled | `Confirmed` |
| `notes` | String | Customer expectation details | `Hands-on demo with keyboard` |

---

## 6. `faqs.json`
Frequently asked questions and verified answers covering company policies (25 FAQs).

---

## 7. `sample_conversations.json`
Multi-turn sales dialogue transcripts representing diverse customer scenarios (10 conversations).
"""
with open(os.path.join(DATA_DIR, "data_dictionary.md"), "w", encoding="utf-8") as f:
    f.write(data_dict)
print("Created data_dictionary.md.")
