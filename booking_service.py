"""
booking_service.py
------------------
Creating, cancelling and listing bookings.

The campus rules themselves live in policies/booking_policies.py - this
file only asks the campus's policy object "is this booking allowed?".
That keeps rules and core logic separate (requirement 5.2).
"""
from datetime import datetime, time, timedelta

import config
from models.booking import Booking
from services.access import require
from utils.errors import BookingError, PermissionDenied, ValidationError
from utils.timeutils import hhmm_to_minutes, minutes_to_hhmm
from utils.validators import parse_date, validate_purpose

# One SELECT shared by every list below. The column names match Booking.from_row().
BOOKING_SELECT = """
SELECT b.id, b.resource_id, r.resource_code, r.name AS resource_name, r.resource_type,
       b.lecturer_id, u.full_name AS lecturer_name, b.campus_id, c.name AS campus_name,
       b.booking_date, b.start_minutes, b.duration_minutes, b.purpose,
       b.status AS db_status
FROM bookings b
JOIN resources r ON r.id = b.resource_id
JOIN users u     ON u.id = b.lecturer_id
JOIN campuses c  ON c.id = b.campus_id
"""
ORDER_BY = " ORDER BY b.booking_date, b.start_minutes"


class BookingService:
    def __init__(self, db, resource_service):
        self.db = db
        self.resources = resource_service

    # ------------------------------------------------------------ listing
    def _fetch(self, where="", params=()):
        rows = self.db.query(BOOKING_SELECT + where + ORDER_BY, params)
        return [Booking.from_row(row) for row in rows]

    def for_lecturer(self, lecturer_id, campus_id=None):
        if campus_id is None:
            return self._fetch("WHERE b.lecturer_id = ?", (lecturer_id,))
        return self._fetch("WHERE b.lecturer_id = ? AND b.campus_id = ?", (lecturer_id, campus_id))

    def for_campus(self, campus_id):
        return self._fetch("WHERE b.campus_id = ?", (campus_id,))

    def all_bookings(self):
        return self._fetch()

    def for_resource_on(self, resource_id, booking_date):
        """Active bookings of one resource on one day (used for the day schedule)."""
        return self._fetch("WHERE b.resource_id = ? AND b.booking_date = ? AND b.status = 'Active'",
                           (resource_id, booking_date.isoformat()))

    def get(self, booking_id):
        found = self._fetch("WHERE b.id = ?", (booking_id,))
        return found[0] if found else None

    # ------------------------------------------------------- availability
    def availability(self, campus_id):
        """
        Real-time availability for every resource on a campus.
        Returns a dictionary: resource id -> (text, tag)
        """
        now = datetime.now()
        now_min = now.hour * 60 + now.minute
        todays = self.db.query(
            "SELECT resource_id, start_minutes, duration_minutes FROM bookings "
            "WHERE campus_id = ? AND booking_date = ? AND status = 'Active' ORDER BY start_minutes",
            (campus_id, now.date().isoformat()))

        busy_until = {}      # resource id -> minute the current booking ends
        next_start = {}      # resource id -> start of its next booking today
        for row in todays:
            start = row["start_minutes"]
            end = start + row["duration_minutes"]
            if start <= now_min < end:
                busy_until[row["resource_id"]] = end
            elif start > now_min and row["resource_id"] not in next_start:
                next_start[row["resource_id"]] = start

        result = {}
        for res in self.resources.list_for_campus(campus_id):
            if not res.is_bookable:
                result[res.resource_id] = ("Under maintenance", "bad")
            elif res.resource_id in busy_until:
                result[res.resource_id] = (f"In use until {minutes_to_hhmm(busy_until[res.resource_id])}", "busy")
            elif res.resource_id in next_start:
                result[res.resource_id] = (f"Available until {minutes_to_hhmm(next_start[res.resource_id])}", "free")
            else:
                result[res.resource_id] = ("Available now", "free")
        return result

    # ------------------------------------------------------------ creating
    def create_booking(self, user, campus, resource_id, date_text, start_text, duration_text, purpose):
        """Check every rule, then save the booking. Raises BookingError if anything is wrong."""
        require(user, "book_resource")

        purpose = validate_purpose(purpose)
        booking_date = parse_date(date_text)
        start = hhmm_to_minutes(start_text)
        duration = self._parse_duration(duration_text)

        resource = self.resources.get(resource_id)
        if resource is None or resource.campus_id != campus.campus_id \
                or resource.status == config.RESOURCE_STATUS_REMOVED:
            raise BookingError("Please select a resource from the list first.")
        if not resource.is_bookable:
            raise BookingError(f"{resource.name} is under maintenance and cannot be booked right now.")

        start_dt = datetime.combine(booking_date, time()) + timedelta(minutes=start)
        if start_dt <= datetime.now():
            raise BookingError("Bookings must be for a future date and time.")

        # Campus rules (duration, hours, days, notice, booking limit)
        active = [b for b in self.for_lecturer(user.user_id, campus.campus_id)
                  if b.is_current_or_future()]
        problems = campus.policy.validate(resource.resource_type, booking_date, start,
                                          duration, active_bookings=len(active))
        if problems:
            raise BookingError(f"This booking breaks the {campus.policy.name}:\n\n- "
                               + "\n- ".join(problems))

        # Overlap check + insert together, so two bookings can never clash.
        with self.db.transaction():
            clash = self.db.query_one(
                "SELECT start_minutes, duration_minutes FROM bookings "
                "WHERE resource_id = ? AND booking_date = ? AND status = 'Active' "
                "AND start_minutes < ? AND start_minutes + duration_minutes > ?",
                (resource_id, booking_date.isoformat(), start + duration, start))
            if clash:
                taken_from = minutes_to_hhmm(clash["start_minutes"])
                taken_to = minutes_to_hhmm(clash["start_minutes"] + clash["duration_minutes"])
                raise BookingError(f"{resource.name} is already booked from {taken_from} to "
                                   f"{taken_to} on {booking_date}. Please choose another time.")
            cursor = self.db.conn.execute(
                "INSERT INTO bookings (resource_id, lecturer_id, campus_id, booking_date, "
                "start_minutes, duration_minutes, purpose) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (resource_id, user.user_id, campus.campus_id, booking_date.isoformat(),
                 start, duration, purpose))
        return self.get(cursor.lastrowid)

    # ----------------------------------------------------------- cancelling
    def cancel_booking(self, user, booking_id):
        """Cancel a future booking. Lecturers cancel their own; admins cancel on their campus."""
        booking = self.get(booking_id)
        if booking is None:
            raise BookingError("That booking could not be found. Please select one from the table.")

        owner = booking.lecturer_id == user.user_id
        campus_admin = user.can("cancel_campus_booking") and user.can_access_campus(booking.campus_id)
        if not (owner or campus_admin):
            raise PermissionDenied("You can only cancel your own bookings.")
        if not booking.is_future():
            raise BookingError("Only bookings that have not started yet can be cancelled.")

        self.db.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (booking_id,))

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _parse_duration(text):
        try:
            minutes = int(str(text).strip())
        except ValueError:
            raise ValidationError("Duration must be a whole number of minutes, e.g. 60.")
        if minutes < config.SLOT_STEP_MINUTES or minutes % config.SLOT_STEP_MINUTES:
            raise ValidationError(f"Duration must be a multiple of {config.SLOT_STEP_MINUTES} minutes.")
        return minutes
