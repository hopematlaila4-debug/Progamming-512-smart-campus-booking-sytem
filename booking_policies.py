"""
booking_policies.py
-------------------
Campus-specific booking rules, kept completely separate from the core
booking logic (requirement 5.2).

HOW IT WORKS
    * BookingPolicy is the base class. It holds default values and one
      method, validate(), that checks a requested booking against them.
    * Each campus policy is a small subclass that only overrides the values
      that differ (polymorphism / inheritance).
    * The @register_policy decorator stores each class in POLICY_REGISTRY
      (a dictionary). A campus row in the database just stores the policy
      key, so the correct rules are found automatically.

ADDING A NEW CAMPUS OR RULE (minimal change)
    1. Write a new subclass below and decorate it with @register_policy.
    2. Insert a campus row whose policy_key matches the new class key.
    No other file needs to change.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from utils.timeutils import format_days, format_duration, minutes_to_hhmm

# Dictionary: policy key -> policy class
POLICY_REGISTRY: dict[str, type["BookingPolicy"]] = {}


def register_policy(cls):
    """Class decorator that adds a policy class to the registry."""
    POLICY_REGISTRY[cls.key] = cls
    return cls


class BookingPolicy:
    """Base booking policy. Subclasses override the class attributes."""

    key = "default"
    name = "Standard Policy"

    max_duration_minutes = 120                    # maximum length of one session
    open_minutes = 8 * 60                         # earliest start (minutes since midnight)
    close_minutes = 17 * 60                       # latest finish
    allowed_weekdays = frozenset({0, 1, 2, 3, 4})  # 0 = Monday ... 6 = Sunday
    max_advance_days = 30                         # how far ahead a booking may be made
    max_active_bookings = 5                       # upcoming bookings per lecturer
    # Resource-type specific rules (dictionaries so they are easy to extend)
    type_duration_limits: dict[str, int] = {}     # e.g. {"Computer Lab": 60}
    priority_notice_hours: dict[str, int] = {}    # e.g. {"Computer Lab": 24}

    # ------------------------------------------------------------------ rules
    def duration_limit_for(self, resource_type: str) -> int:
        """Longest allowed session for this resource type."""
        return min(
            self.max_duration_minutes,
            self.type_duration_limits.get(resource_type, self.max_duration_minutes),
        )

    def notice_hours_for(self, resource_type: str) -> int:
        """Minimum advance notice (priority access rule) for this resource type."""
        return self.priority_notice_hours.get(resource_type, 0)

    def extra_checks(self, resource_type, booking_date, start_minutes,
                     duration_minutes) -> list[str]:
        """Hook for future special rules. Return a list of problem messages."""
        return []

    # -------------------------------------------------------------- validation
    def validate(self, resource_type: str, booking_date: date, start_minutes: int,
                 duration_minutes: int, now: datetime | None = None,
                 active_bookings: int = 0) -> list[str]:
        """Return a list of rule violations (an empty list means the booking is allowed)."""
        now = now or datetime.now()
        problems: list[str] = []
        end_minutes = start_minutes + duration_minutes

        if duration_minutes <= 0:
            problems.append("Duration must be greater than zero.")

        limit = self.duration_limit_for(resource_type)
        if duration_minutes > limit:
            problems.append(
                f"Maximum session for a {resource_type} on this campus is "
                f"{format_duration(limit)} (you asked for {format_duration(duration_minutes)})."
            )

        if start_minutes < self.open_minutes or end_minutes > self.close_minutes:
            problems.append(
                f"Bookings must fall within {minutes_to_hhmm(self.open_minutes)}-"
                f"{minutes_to_hhmm(self.close_minutes)} on this campus."
            )

        if booking_date.weekday() not in self.allowed_weekdays:
            problems.append(
                f"This campus only accepts bookings on {format_days(self.allowed_weekdays)}."
            )

        if (booking_date - now.date()).days > self.max_advance_days:
            problems.append(
                f"Bookings may be made at most {self.max_advance_days} days in advance."
            )

        notice = self.notice_hours_for(resource_type)
        start_dt = datetime.combine(booking_date, datetime.min.time()) + timedelta(minutes=start_minutes)
        if notice and start_dt - now < timedelta(hours=notice):
            problems.append(
                f"{resource_type} bookings need at least {notice} hours' notice (priority access rule)."
            )

        if active_bookings >= self.max_active_bookings:
            problems.append(
                f"You already hold {active_bookings} upcoming bookings; this campus allows "
                f"a maximum of {self.max_active_bookings} at a time."
            )

        problems.extend(self.extra_checks(resource_type, booking_date, start_minutes, duration_minutes))
        return problems

    # ------------------------------------------------------------ presentation
    def describe(self) -> list[str]:
        """Human-readable list of the rules, shown in the GUI."""
        lines = [
            f"Maximum session: {format_duration(self.max_duration_minutes)}",
            f"Booking hours: {minutes_to_hhmm(self.open_minutes)} - {minutes_to_hhmm(self.close_minutes)}",
            f"Booking days: {format_days(self.allowed_weekdays)}",
            f"Book up to {self.max_advance_days} days ahead",
            f"Max upcoming bookings per lecturer: {self.max_active_bookings}",
        ]
        for rtype, minutes in self.type_duration_limits.items():
            lines.append(f"{rtype}: max {format_duration(minutes)} per session")
        for rtype, hours in self.priority_notice_hours.items():
            lines.append(f"Priority access: {rtype} needs {hours}h notice")
        return lines

    def summary(self) -> str:
        """One-line summary for banners."""
        return (
            f"{self.name}: max {format_duration(self.max_duration_minutes)} | "
            f"{minutes_to_hhmm(self.open_minutes)}-{minutes_to_hhmm(self.close_minutes)} | "
            f"{format_days(self.allowed_weekdays)}"
        )

    def next_valid_date(self, start: date | None = None) -> date:
        """First date from tomorrow onwards that this campus accepts bookings on."""
        day = (start or date.today()) + timedelta(days=1)
        for _ in range(14):
            if day.weekday() in self.allowed_weekdays:
                return day
            day += timedelta(days=1)
        return day


# ============================================================================
# Concrete campus policies
# ============================================================================
@register_policy
class StandardPolicy(BookingPolicy):
    """Fallback policy used if a campus has an unknown policy key."""
    key = "default"
    name = "Standard Policy"


@register_policy
class DurbanPolicy(BookingPolicy):
    """Durban: balanced rules, computer labs reserved for assessments."""
    key = "durban"
    name = "Durban Campus Policy"
    max_duration_minutes = 180
    open_minutes = 8 * 60
    close_minutes = 17 * 60
    allowed_weekdays = frozenset({0, 1, 2, 3, 4})
    max_advance_days = 30
    max_active_bookings = 5
    priority_notice_hours = {"Computer Lab": 24}


@register_policy
class JohannesburgPolicy(BookingPolicy):
    """Johannesburg: busy campus - short sessions, long opening hours, strict limits."""
    key = "johannesburg"
    name = "Johannesburg Campus Policy"
    max_duration_minutes = 120
    open_minutes = 7 * 60
    close_minutes = 20 * 60
    allowed_weekdays = frozenset({0, 1, 2, 3, 4})
    max_advance_days = 14
    max_active_bookings = 3
    priority_notice_hours = {"Seminar Room": 48}


@register_policy
class CapeTownPolicy(BookingPolicy):
    """Cape Town: flexible - long sessions, Saturday access, long planning window."""
    key = "cape_town"
    name = "Cape Town Campus Policy"
    max_duration_minutes = 240
    open_minutes = 8 * 60
    close_minutes = 18 * 60
    allowed_weekdays = frozenset({0, 1, 2, 3, 4, 5})
    max_advance_days = 60
    max_active_bookings = 6


@register_policy
class PretoriaPolicy(BookingPolicy):
    """Pretoria: limited opening hours and tight limits on computer labs."""
    key = "pretoria"
    name = "Pretoria Campus Policy"
    max_duration_minutes = 90
    open_minutes = 8 * 60
    close_minutes = 16 * 60
    allowed_weekdays = frozenset({0, 1, 2, 3, 4})
    max_advance_days = 21
    max_active_bookings = 4
    type_duration_limits = {"Computer Lab": 60}


def get_policy(policy_key: str) -> BookingPolicy:
    """Look up a policy by key (falls back to the standard policy)."""
    return POLICY_REGISTRY.get(policy_key, StandardPolicy)()
