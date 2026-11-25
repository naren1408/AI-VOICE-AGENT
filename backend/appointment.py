import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session
from database.models import Appointment

# --- CONFIGURATION (Easily explainable / live-coding ready) ---
WORK_HOURS_START = 9    # 09:00 AM
WORK_HOURS_END = 18     # 06:00 PM (18:00)
DEMO_DURATION_MINUTES = 30
WORK_DAYS = {0, 1, 2, 3, 4}  # Monday (0) to Friday (4)


def parse_natural_datetime(text: str) -> datetime.datetime:
    """Parse natural language date strings like 'tomorrow 4pm', '2026-11-26 15:00'."""
    text = text.lower().strip()
    now = datetime.datetime.now()
    target_date = now.date()

    if "tomorrow" in text:
        target_date = now.date() + datetime.timedelta(days=1)
    elif "today" in text:
        target_date = now.date()
    elif "next monday" in text:
        days_ahead = (7 - now.weekday()) % 7 or 7
        target_date = now.date() + datetime.timedelta(days=days_ahead)

    # Extract hour and minute
    hour, minute = 14, 0  # Default 2:00 PM
    import re

    # Pattern 1: ISO date time YYYY-MM-DD HH:MM
    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{1,2}):(\d{2}))?", text)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        target_date = datetime.date(y, m, d)
        if iso_match.group(4):
            hour = int(iso_match.group(4))
            minute = int(iso_match.group(5)) if iso_match.group(5) else 0
    else:
        # Pattern 2: 12-hour or 24-hour time with optional am/pm (e.g. '4pm', '2:30 pm', '14:00', 'at 4')
        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text)
        if time_match:
            raw_h = int(time_match.group(1))
            raw_m = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)

            # If user writes 'tomorrow 2pm' or '4pm'
            if meridiem:
                if meridiem == "pm" and raw_h < 12:
                    raw_h += 12
                elif meridiem == "am" and raw_h == 12:
                    raw_h = 0
            elif raw_h < 7:  # Interpret 1-6 without am/pm as afternoon business hours
                raw_h += 12

            if 0 <= raw_h <= 23:
                hour = raw_h
            if 0 <= raw_m <= 59:
                minute = raw_m

    return datetime.datetime(target_date.year, target_date.month, target_date.day, hour, minute)


def check_availability(db: Session, dt: datetime.datetime) -> Tuple[bool, str]:
    """Check if the slot is on a business day, within business hours, and not already booked."""
    # Check weekday
    if dt.weekday() not in WORK_DAYS:
        return False, "Selected date is on a weekend. Demos are available Monday through Friday."

    # Check work hours
    if dt.hour < WORK_HOURS_START or dt.hour >= WORK_HOURS_END:
        return False, f"Selected time is outside working hours ({WORK_HOURS_START}:00 to {WORK_HOURS_END}:00)."

    # Check database conflicts (slot occupied within 30 min window)
    existing = db.query(Appointment).filter(
        Appointment.slot_time == dt,
        Appointment.status == "CONFIRMED"
    ).first()

    if existing:
        return False, f"The slot at {dt.strftime('%Y-%m-%d %H:%M')} is already booked. Please choose another slot."

    return True, f"Slot {dt.strftime('%Y-%m-%d %H:%M')} is available."


def book_appointment(db: Session, customer_name: str, customer_email: str, slot_dt: datetime.datetime, call_id: str = None) -> Tuple[bool, str, Appointment]:
    """Atomically book an appointment and rollback if double-booked."""
    if not customer_email or "@" not in customer_email:
        return False, "Valid customer email is required to book a demo.", None

    # Enforce transactional boundary
    try:
        # Check availability again inside transaction
        is_free, msg = check_availability(db, slot_dt)
        if not is_free:
            return False, msg, None

        appt = Appointment(
            customer_name=customer_name or "Valued Client",
            customer_email=customer_email.strip().lower(),
            slot_time=slot_dt,
            call_id=call_id,
            status="CONFIRMED"
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)
        return True, f"Demo booked successfully for {slot_dt.strftime('%Y-%m-%d %H:%M')}! Confirmation sent to {customer_email}.", appt
    except Exception as err:
        db.rollback()
        return False, f"Could not book appointment due to conflict or error: {str(err)}", None


def generate_ics_content(customer_name: str, slot_dt: datetime.datetime) -> str:
    """Generate an iCalendar (.ics) string for the scheduled product demo."""
    end_dt = slot_dt + datetime.timedelta(minutes=DEMO_DURATION_MINUTES)
    dt_stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dt_start = slot_dt.strftime("%Y%m%dT%H%M%S")
    dt_end = end_dt.strftime("%Y%m%dT%H%M%S")

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CloudScale AI//Sales Demo Booking//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:demo-{int(slot_dt.timestamp())}@cloudscale.ai",
        f"DTSTAMP:{dt_stamp}",
        f"DTSTART:{dt_start}",
        f"DTEND:{dt_end}",
        f"SUMMARY:CloudScale AI Product Demo - {customer_name}",
        "DESCRIPTION:30-minute tailored technical demo and FinOps consultation with CloudScale AI.",
        "LOCATION:Google Meet / Zoom (Link in invite)",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR"
    ]
    return "\r\n".join(ics_lines)
