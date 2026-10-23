"""
booking.py
----------
Booking model. Times are stored as minutes since midnight; helper
properties convert them to datetimes for display and status checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import config
from utils.timeutils import minutes_to_hhmm

# Display statuses
STATUS_UPCOMING = "Upcoming"
STATUS_IN_PROGRESS = "In progress"
STATUS_COMPLETED = "Completed"
STATUS_CANCELLED = "Cancelled"


@dataclass
class Booking:
    booking_id: int
    resource_id: int
    resource_code: str
    resource_name: str
    resource_type: str
    lecturer_id: int
    lecturer_name: str
    campus_id: int
    campus_name: str
    booking_date: date
    start_minutes: int
    duration_minutes: int
    purpose: str
    db_status: str

    # ----------------------------------------------------------------- times
    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.duration_minutes

    @property
    def start_text(self) -> str:
        return minutes_to_hhmm(self.start_minutes)

    @property
    def end_text(self) -> str:
        return minutes_to_hhmm(self.end_minutes)

    @property
    def start_datetime(self) -> datetime:
        return datetime.combine(self.booking_date, datetime.min.time()) + timedelta(minutes=self.start_minutes)

    @property
    def end_datetime(self) -> datetime:
        return self.start_datetime + timedelta(minutes=self.duration_minutes)

    # ---------------------------------------------------------------- status
    def status(self, now: datetime | None = None) -> str:
        now = now or datetime.now()
        if self.db_status == config.BOOKING_CANCELLED:
            return STATUS_CANCELLED
        if self.end_datetime <= now:
            return STATUS_COMPLETED
        if self.start_datetime <= now:
            return STATUS_IN_PROGRESS
        return STATUS_UPCOMING

    def is_future(self, now: datetime | None = None) -> bool:
        """True for an active booking that has not started yet."""
        return self.status(now) == STATUS_UPCOMING

    def is_current_or_future(self, now: datetime | None = None) -> bool:
        return self.status(now) in (STATUS_UPCOMING, STATUS_IN_PROGRESS)

    @classmethod
    def from_row(cls, row) -> "Booking":
        return cls(
            booking_id=row["id"],
            resource_id=row["resource_id"],
            resource_code=row["resource_code"],
            resource_name=row["resource_name"],
            resource_type=row["resource_type"],
            lecturer_id=row["lecturer_id"],
            lecturer_name=row["lecturer_name"],
            campus_id=row["campus_id"],
            campus_name=row["campus_name"],
            booking_date=date.fromisoformat(row["booking_date"]),
            start_minutes=row["start_minutes"],
            duration_minutes=row["duration_minutes"],
            purpose=row["purpose"],
            db_status=row["db_status"],
        )
