"""
TechNova Solutions — Appointment Booking
Validates, stores, and retrieves demo appointments.
"""
import datetime
import re
from typing import Tuple, Optional

# Configuration
BUSINESS_HOURS_START = 9   # 9 AM
BUSINESS_HOURS_END   = 18  # 6 PM
BUSINESS_DAYS = {0, 1, 2, 3, 4}  # Mon–Fri


def parse_date(date_str: str) -> Optional[datetime.date]:
    """Try to parse a date string in common formats."""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%B %d %Y", "%d %B %Y"]
    date_str = date_str.strip()
    if "tomorrow" in date_str.lower():
        return datetime.date.today() + datetime.timedelta(days=1)
    if "today" in date_str.lower():
        return datetime.date.today()
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    # Try to extract date from free text e.g. "November 28"
    m = re.search(r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)", date_str, re.IGNORECASE)
    if m:
        try:
            return datetime.datetime.strptime(f"{m.group(1)} {m.group(2)} {datetime.date.today().year}", "%d %B %Y").date()
        except ValueError:
            pass
    return None


def parse_time(time_str: str) -> Optional[str]:
    """Normalize time string to 'HH:MM AM/PM' format."""
    time_str = time_str.strip().lower()
    # Match patterns like '3pm', '3:30 pm', '15:00'
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_str)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        meridiem = m.group(3)
        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        elif not meridiem and hour < 7:
            hour += 12  # Assume afternoon for ambiguous times like '3'
        ampm = "PM" if hour >= 12 else "AM"
        display_hour = hour % 12 or 12
        return f"{display_hour}:{minute:02d} {ampm}"
    return None


def validate_appointment(date_str: str, time_str: str) -> Tuple[bool, str]:
    """
    Validate that the appointment date/time is:
    - A valid date and time
    - On a business day (Mon–Fri)
    - During business hours (9 AM – 6 PM)
    - In the future
    """
    parsed_date = parse_date(date_str)
    if not parsed_date:
        return False, f"Could not understand the date '{date_str}'. Please use a format like 'November 28' or '2026-11-28'."

    if parsed_date < datetime.date.today():
        return False, "The appointment date must be in the future."

    if parsed_date.weekday() not in BUSINESS_DAYS:
        return False, f"{parsed_date.strftime('%A %d %B')} is a weekend. Demos are available Monday to Friday."

    parsed_time = parse_time(time_str)
    if not parsed_time:
        return False, f"Could not understand the time '{time_str}'. Please use a format like '3:00 PM' or '15:00'."

    # Check business hours
    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", parsed_time)
    if m:
        h, mi, ampm = int(m.group(1)), int(m.group(2)), m.group(3)
        hour_24 = h if ampm == "AM" else (h + 12 if h < 12 else h)
        if hour_24 < BUSINESS_HOURS_START or hour_24 >= BUSINESS_HOURS_END:
            return False, f"Demo slots are available between {BUSINESS_HOURS_START}:00 AM and {BUSINESS_HOURS_END - 12}:00 PM."

    return True, f"Appointment confirmed for {parsed_date.strftime('%A, %d %B %Y')} at {parsed_time}."


def book_appointment_in_db(db, lead_id: Optional[int], name: str, email: str,
                           date_str: str, time_str: str, product: str, notes: str) -> Tuple[bool, str]:
    """Save a validated appointment to the database."""
    from database.technova_models import TNAppointment
    if not email or "@" not in email:
        return False, "A valid email address is required to send the appointment confirmation."

    is_valid, msg = validate_appointment(date_str, time_str)
    if not is_valid:
        return False, msg

    # Check for duplicate (same email + date + time)
    existing = db.query(TNAppointment).filter(
        TNAppointment.customer_email == email.lower(),
        TNAppointment.appointment_date == date_str,
        TNAppointment.appointment_time == time_str,
        TNAppointment.status == "Scheduled"
    ).first()
    if existing:
        return False, "You already have an appointment at that time. Please choose a different slot."

    appt = TNAppointment(
        lead_id=lead_id,
        customer_name=name or "Valued Customer",
        customer_email=email.lower().strip(),
        appointment_date=date_str,
        appointment_time=time_str or parse_time(time_str) or "10:00 AM",
        product_interest=product or "TechNova Suite",
        notes=notes or "",
        status="Scheduled"
    )
    db.add(appt)
    db.commit()
    return True, f"Your demo appointment is confirmed for {date_str} at {time_str}. A confirmation will be sent to {email}."
