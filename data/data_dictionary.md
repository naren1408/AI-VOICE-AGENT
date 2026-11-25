# ElectroMart India — Data Dictionary

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
