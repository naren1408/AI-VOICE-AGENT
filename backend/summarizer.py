"""
ElectroMart India — Call Summarization Engine
Generates an executive sales summary upon call termination and stores it in SQLite.
"""
from typing import Dict, List, Optional
from database.models import CallSummary, Call, Lead, RecommendedProduct, Appointment


def generate_call_summary(
    db,
    call_id: str,
    extracted_lead,
    recommended_prods: List[Dict],
    messages: List[Dict],
    client=None
) -> CallSummary:
    """Compile structured executive summary and persist to CallSummary table."""
    cust_name = extracted_lead.name or "Prospective Customer"
    category = extracted_lead.interested_category or "Electronics"
    budget = extracted_lead.budget or "Not Specified"
    reqs = extracted_lead.requirement or "General Electronics Consultation"

    # Compile recommended products string
    rec_names = [f"{p['product_name']} (₹{p['price_inr']:,})" for p in recommended_prods]
    rec_str = ", ".join(rec_names) if rec_names else "None suggested"

    # Analyze questions and objections
    user_msgs = [m.get("text", "") for m in messages if m.get("sender") == "user"]
    all_user_text = " ".join(user_msgs).lower()

    questions = []
    if "price" in all_user_text or "cost" in all_user_text: questions.append("Pricing & Tiers")
    if "warranty" in all_user_text: questions.append("Warranty Terms")
    if "battery" in all_user_text: questions.append("Battery Life")
    if "emi" in all_user_text or "discount" in all_user_text: questions.append("Offers & EMI")
    if "visit" in all_user_text or "store" in all_user_text: questions.append("Store Visit")
    q_str = ", ".join(questions) if questions else "Product specifications enquiry"

    objections = []
    if "expensive" in all_user_text or "overpriced" in all_user_text: objections.append("Price sensitivity")
    if "heating" in all_user_text: objections.append("Thermal performance concern")
    obj_str = ", ".join(objections) if objections else "No major objections recorded"

    # Check appointment status
    appt = db.query(Appointment).filter(
        Appointment.customer_email == (extracted_lead.email or "").lower()
    ).order_by(Appointment.created_at.desc()).first()

    appt_details = (
        f"{appt.appointment_type} on {appt.appointment_date} at {appt.appointment_time} in {appt.city}"
        if appt else "No appointment scheduled"
    )

    # Next action
    if extracted_lead.status == "HOT":
        next_action = f"Priority follow-up within 24 hours: Prepare display unit for {cust_name} at showroom."
    elif extracted_lead.status == "WARM":
        next_action = "Send digital brochure and promotional offer link via WhatsApp/Email."
    else:
        next_action = "Add to monthly newsletter for new product launches and seasonal discounts."

    # Persist or update
    summary = db.query(CallSummary).filter(CallSummary.call_id == call_id).first()
    if not summary:
        summary = CallSummary(
            call_id=call_id,
            customer_name=cust_name,
            requirements=reqs,
            category=category,
            budget=budget,
            recommended_products=rec_str,
            key_questions=q_str,
            objections=obj_str,
            sentiment=extracted_lead.status,
            lead_score=extracted_lead.score,
            lead_status=extracted_lead.status,
            appointment_details=appt_details,
            next_action=next_action
        )
        db.add(summary)
    else:
        summary.requirements = reqs
        summary.budget = budget
        summary.recommended_products = rec_str
        summary.appointment_details = appt_details
        summary.lead_score = extracted_lead.score
        summary.lead_status = extracted_lead.status

    # Also update Call record
    call = db.query(Call).filter(Call.id == call_id).first()
    if call:
        call.summary = f"Discussion regarding {category} (Budget: {budget}). Recommended: {rec_str}."
        call.final_score = extracted_lead.score
        call.final_sentiment = extracted_lead.status

    db.commit()
    return summary
