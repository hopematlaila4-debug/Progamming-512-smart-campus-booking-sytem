"""
timeutils.py
------------
Small helpers for working with times stored as "minutes since midnight".

Storing times as integers makes overlap checks simple and reliable:
    two bookings overlap  <=>  new_start < existing_end AND new_end > existing_start
"""
from __future__ import annotations

from utils.errors import ValidationError

WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def minutes_to_hhmm(minutes: int) -> str:
    """480 -> '08:00'."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def hhmm_to_minutes(text: str) -> int:
    """'08:30' -> 510. Raises ValidationError for bad input."""
    try:
        hours_text, minutes_text = text.strip().split(":")
        hours, minutes = int(hours_text), int(minutes_text)
    except (ValueError, AttributeError):
        raise ValidationError("Time must be in HH:MM format, e.g. 08:30.")
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValidationError("Time must be between 00:00 and 23:59.")
    return hours * 60 + minutes


def format_duration(minutes: float) -> str:
    """90 -> '1h 30m', 60 -> '1h', 45 -> '45m'."""
    minutes = int(round(minutes))
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours}h {rest}m"
    if hours:
        return f"{hours}h"
    return f"{rest}m"


def format_days(days) -> str:
    """Turn a set of weekday numbers into text, e.g. {0,1,2,3,4} -> 'Mon-Fri'."""
    ordered = sorted(days)
    if not ordered:
        return "No days"
    if ordered == list(range(ordered[0], ordered[-1] + 1)) and len(ordered) > 2:
        return f"{WEEKDAY_NAMES[ordered[0]]}-{WEEKDAY_NAMES[ordered[-1]]}"
    return ", ".join(WEEKDAY_NAMES[d] for d in ordered)


def time_slots(start_minutes: int, end_minutes: int, step: int) -> list[str]:
    """Build a list of 'HH:MM' strings, e.g. for a start-time drop-down."""
    return [minutes_to_hhmm(m) for m in range(start_minutes, end_minutes + 1, step)]
