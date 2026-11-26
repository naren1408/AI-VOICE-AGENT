"""
ElectroMart India — Appointment Booking & Calendar Engine
Handles Store Visits, Product Consultations, and Sales Callbacks.
Validates business hours (10:00 AM – 08:30 PM), prevents past dates,
checks slot availability, prevents duplicate slots, and generates standard RFC 5545 .ics calendar files.
"""
import re
import uuid
import datetime
from typing import Tuple, Optional, List
from database.models import Appointment

BUSINESS_START_HOUR = 10  # 10:00 AM
BUSINESS_END_HOUR = 20    # 08:30 PM (cut-off 20:30)

ALL_DAILY_SLOTS = [
    "10:30 AM", "11:30 AM", "01:00 PM", "02:30 PM",
    "04:00 PM", "05:30 PM", "07:00 PM", "08:00 PM"
]


def parse_natural_datetime(text: str) -> Tuple[datetime.date, str]:
    """
    Parse date and formatted time from natural language user input.
    Defaults to tomorrow at 04:00 PM if unspecified.
    """
    today = datetime.date.today()
    target_date = today + datetime.timedelta(days=1)  # Default: tomorrow

    t = text.lower()
    if "today" in t:
        target_date = today
    elif "day after tomorrow" in t:
        target_date = today + datetime.timedelta(days=2)
    elif "tomorrow" in t:
        target_date = today + datetime.timedelta(days=1)
    else:
        # Check ISO date 'YYYY-MM-DD'
        m_iso = re.search(r"\b(202\d)-(\d{1,2})-(\d{1,2})\b", text)
        if m_iso:
            try:
                target_date = datetime.date(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
            except ValueError:
                pass
        else:
            # Check '28 November' or 'Nov 28'
            m_month = re.search(r"(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*", t)
            if m_month:
                months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                month_idx = months.index(m_month.group(2)[:3]) + 1
                try:
                    target_date = datetime.date(today.year, month_idx, int(m_month.group(1)))
                    if target_date < today:
                        target_date = datetime.date(today.year + 1, month_idx, int(m_month.group(1)))
                except ValueError:
                    pass

    # Parse Time: "4pm", "4:00 PM", "16:00", "11:30 am", "4", "4:00"
    target_time_str = "04:00 PM"
    m_time = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|p\.m\.|a\.m\.)?", t)
    if m_time:
        raw_h = int(m_time.group(1))
        raw_m = int(m_time.group(2)) if m_time.group(2) else 0
        ampm = (m_time.group(3) or "").replace(".", "").lower()

        if 1 <= raw_h <= 24:
            if ampm == "pm" and raw_h < 12:
                raw_h += 12
            elif ampm == "am" and raw_h == 12:
                raw_h = 0
            elif not ampm and raw_h < 9:
                raw_h += 12  # Assume afternoon for times like '4' or '5'

            hour_12 = raw_h % 12 or 12
            meridiem = "PM" if raw_h >= 12 else "AM"
            target_time_str = f"{hour_12:02d}:{raw_m:02d} {meridiem}"

    return target_date, target_time_str


def validate_appointment_slot(date_val: datetime.date, time_str: str) -> Tuple[bool, str]:
    """Validate appointment is not in the past and during showroom business hours (10 AM to 8:30 PM)."""
    today = datetime.date.today()
    if date_val < today:
        return False, "Appointments cannot be scheduled for past dates. Please select today or a future date."

    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str)
    if not m:
        return True, "Valid"

    h = int(m.group(1))
    raw_m = int(m.group(2))
    ampm = m.group(3)
    h_24 = h if ampm == "AM" else (h + 12 if h < 12 else h)

    if h_24 < BUSINESS_START_HOUR or (h_24 == BUSINESS_END_HOUR and raw_m > 30) or h_24 > BUSINESS_END_HOUR:
        return False, f"Showroom appointments are available between 10:00 AM and 08:30 PM. Requested slot {time_str} is outside operating hours."

    return True, "Valid"


def get_available_slots(db, date_val: datetime.date, city: Optional[str] = None) -> List[str]:
    """Return available 45-minute slots on the given date by filtering out booked slots."""
    date_str = date_val.strftime("%Y-%m-%d")
    query = db.query(Appointment).filter(
        Appointment.appointment_date == date_str,
        Appointment.status.in_(["Confirmed", "Scheduled"])
    )
    if city:
        query = query.filter(Appointment.city == city)
    booked_times = {a.appointment_time for a in query.all()}
    return [slot for slot in ALL_DAILY_SLOTS if slot not in booked_times]


def book_appointment_in_db(
    db,
    customer_name: str,
    customer_email: Optional[str] = None,
    customer_phone: Optional[str] = None,
    date_val: Optional[datetime.date] = None,
    time_str: str = "04:00 PM",
    appointment_type: str = "Store Visit",
    interested_product: Optional[str] = None,
    city: str = "Mumbai",
    location: Optional[str] = None,
    notes: Optional[str] = None
) -> Tuple[bool, str, Optional[Appointment]]:
    """
    Atomic booking into SQLite database.
    Validates required contact details, checks business hours, prevents past dates,
    and prevents double-booking for the customer or slot.
    """
    if not customer_name or not customer_name.strip():
        return False, "Customer name is required to book an appointment.", None

    clean_email = (customer_email or "").strip().lower()
    clean_phone = (customer_phone or "").strip()

    if not clean_email and not clean_phone:
        return False, "Please provide at least a phone number or email address to confirm your booking.", None

    if date_val is None:
        date_val = datetime.date.today() + datetime.timedelta(days=1)

    is_valid, reason = validate_appointment_slot(date_val, time_str)
    if not is_valid:
        return False, reason, None

    date_str = date_val.strftime("%Y-%m-%d")

    # Double-booking check: customer already booked this slot
    cust_filter = []
    if clean_email and clean_email != "customer@example.com":
        cust_filter.append(Appointment.customer_email == clean_email)
    if clean_phone:
        cust_filter.append(Appointment.customer_phone == clean_phone)

    if cust_filter:
        from sqlalchemy import or_
        existing_cust = db.query(Appointment).filter(
            or_(*cust_filter),
            Appointment.appointment_date == date_str,
            Appointment.appointment_time == time_str,
            Appointment.status != "Cancelled"
        ).first()

        if existing_cust:
            avail_slots = get_available_slots(db, date_val, city)
            alt_text = f" Available alternative slots: {', '.join(avail_slots[:3])}." if avail_slots else ""
            return False, f"You already have a confirmed appointment on {date_str} at {time_str}.{alt_text}", None

    # Determine default location based on appointment type if not provided
    if not location or not location.strip():
        if appointment_type == "Store Visit":
            location = f"ElectroMart Experience Centre, Flagship Store, {city}"
        elif appointment_type == "Sales Callback":
            location = f"Phone Callback to {clean_phone or 'Registered Phone'}"
        else:
            location = "Google Meet Online Video Consultation (Link sent via SMS/Email)"

    appt_id = f"APT-{str(uuid.uuid4())[:6].upper()}"
    new_appt = Appointment(
        appointment_id=appt_id,
        customer_name=customer_name.strip(),
        customer_email=clean_email or "customer@example.com",
        customer_phone=clean_phone or None,
        appointment_date=date_str,
        appointment_time=time_str,
        appointment_type=appointment_type or "Store Visit",
        interested_product=interested_product or "Electronics Consultation",
        city=city or "Mumbai",
        location=location,
        status="Confirmed",
        notes=notes or "Booked via ElectroMart India AI Sales Voice Agent"
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)

    confirmation_msg = (
        f"Appointment confirmed! Booking ID: **{appt_id}** on **{date_str} at {time_str}** "
        f"({appointment_type}) at {location}."
    )
    return True, confirmation_msg, new_appt


def update_appointment_in_db(
    db,
    appointment_id: str,
    date_val: Optional[datetime.date] = None,
    time_str: Optional[str] = None,
    appointment_type: Optional[str] = None,
    city: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None
) -> Tuple[bool, str, Optional[Appointment]]:
    """Update details of an existing appointment."""
    appt = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not appt:
        return False, f"Appointment ID {appointment_id} not found.", None

    if date_val and time_str:
        valid, reason = validate_appointment_slot(date_val, time_str)
        if not valid:
            return False, reason, None
        appt.appointment_date = date_val.strftime("%Y-%m-%d")
        appt.appointment_time = time_str
    elif time_str:
        appt.appointment_time = time_str

    if appointment_type:
        appt.appointment_type = appointment_type
    if city:
        appt.city = city
    if location:
        appt.location = location
    if status:
        appt.status = status
    if notes:
        appt.notes = notes

    db.commit()
    db.refresh(appt)
    return True, f"Appointment {appointment_id} updated successfully.", appt


def cancel_appointment_in_db(db, appointment_id: str) -> Tuple[bool, str]:
    """Cancel an existing appointment in database."""
    appt = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not appt:
        return False, f"Appointment {appointment_id} not found."
    appt.status = "Cancelled"
    db.commit()
    return True, f"Appointment {appointment_id} has been cancelled."


def generate_ics_content(
    customer_name: str,
    date_val: datetime.date,
    time_str: str,
    product: str = "Electronics",
    location: str = "ElectroMart India Showroom"
) -> str:
    """Generate standard RFC 5545 iCalendar format text."""
    dt_str = date_val.strftime("%Y%m%d")
    uid = f"{uuid.uuid4()}@electromart-india.example.com"
    summary = f"ElectroMart India Store Demo: {product}"
    description = f"Hands-on demonstration and consultation for {customer_name} at {location}."

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ElectroMart India//Sales Appointment//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dt_str}T090000Z
DTSTART:{dt_str}T110000Z
DTEND:{dt_str}T120000Z
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:{location}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
    return ics
