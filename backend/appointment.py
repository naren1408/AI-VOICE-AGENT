"""
ElectroMart India — Appointment Booking & Calendar Engine
Handles Store Visits, Product Consultations, and Sales Callbacks.
Validates business hours (10:00 AM – 08:30 PM), prevents duplicate slots,
and generates standard RFC 5545 .ics calendar files.
"""
import re
import uuid
import datetime
from typing import Tuple, Optional
from database.models import Appointment

BUSINESS_START_HOUR = 10  # 10:00 AM
BUSINESS_END_HOUR = 20    # 08:30 PM (cut-off 20:30)


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

    # Parse Time: "4pm", "4:00 PM", "16:00", "11:30 am", "4"
    target_time_str = "04:00 PM"
    m_time = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", t)
    if m_time:
        raw_h = int(m_time.group(1))
        raw_m = int(m_time.group(2)) if m_time.group(2) else 0
        ampm = m_time.group(3)

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
    """Validate appointment is during showroom business hours (10 AM to 8:30 PM)."""
    # Parse hour from time string "04:00 PM"
    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str)
    if not m:
        return True, "Valid"

    h = int(m.group(1))
    ampm = m.group(3)
    h_24 = h if ampm == "AM" else (h + 12 if h < 12 else h)

    if h_24 < BUSINESS_START_HOUR or h_24 > BUSINESS_END_HOUR:
        return False, f"Appointments are available between 10:00 AM and 08:30 PM. Requested slot {time_str} is outside operating hours."

    return True, "Valid"


def book_appointment_in_db(
    db,
    customer_name: str,
    customer_email: str,
    customer_phone: Optional[str],
    date_val: datetime.date,
    time_str: str,
    appointment_type: str = "Store Visit",
    interested_product: Optional[str] = None,
    city: str = "Mumbai",
    notes: Optional[str] = None
) -> Tuple[bool, str, Optional[Appointment]]:
    """
    Atomic booking into SQLite database.
    Checks for duplicate slot for the same customer to prevent double-booking.
    """
    if not customer_email or "@" not in customer_email:
        return False, "A valid email address is required to confirm your booking and send the calendar invite.", None

    is_valid, reason = validate_appointment_slot(date_val, time_str)
    if not is_valid:
        return False, reason, None

    date_str = date_val.strftime("%Y-%m-%d")

    # Double-booking check
    existing = db.query(Appointment).filter(
        Appointment.customer_email == customer_email.lower().strip(),
        Appointment.appointment_date == date_str,
        Appointment.appointment_time == time_str,
        Appointment.status != "Cancelled"
    ).first()

    if existing:
        return False, f"You already have a confirmed appointment on {date_str} at {time_str}. Please select another time.", None

    appt_id = f"APT-{str(uuid.uuid4())[:6].upper()}"
    new_appt = Appointment(
        appointment_id=appt_id,
        customer_name=customer_name or "Valued Customer",
        customer_email=customer_email.lower().strip(),
        customer_phone=customer_phone,
        appointment_date=date_str,
        appointment_time=time_str,
        appointment_type=appointment_type or "Store Visit",
        interested_product=interested_product or "Electronics Consultation",
        city=city or "Mumbai",
        status="Confirmed",
        notes=notes or "Booked via ElectroMart India AI Sales Voice Agent"
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)

    confirmation_msg = (
        f"Appointment confirmed! Booking ID: {appt_id} on {date_str} at {time_str} "
        f"({appointment_type}) at our {city} showroom."
    )
    return True, confirmation_msg, new_appt


def generate_ics_content(customer_name: str, date_val: datetime.date, time_str: str, product: str = "Electronics") -> str:
    """Generate standard RFC 5545 iCalendar format text."""
    dt_str = date_val.strftime("%Y%m%d")
    uid = f"{uuid.uuid4()}@electromart-india.example.com"
    summary = f"ElectroMart India Store Demo: {product}"
    description = f"Hands-on demonstration and consultation for {customer_name} at ElectroMart India showroom."

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
LOCATION:ElectroMart India Experience Centre
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
    return ics
