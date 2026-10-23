"""
config.py
---------
Central configuration for the Smart Campus Resource Booking System.

Keeping constants in one place means they can be changed without hunting
through the rest of the code base (supports the "future expansion" requirement).
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "campus_booking.db"

# ----------------------------------------------------------------------------
# Application text
# ----------------------------------------------------------------------------
APP_TITLE = "Smart Campus Resource Booking System"
INSTITUTION = "Richfield Graduate Institute"

# ----------------------------------------------------------------------------
# Roles (stored in the database exactly as written here)
# ----------------------------------------------------------------------------
ROLE_LECTURER = "Lecturer"
ROLE_ADMIN = "Campus Administrator"
ROLE_OPERATOR = "System Operator"
ALL_ROLES = (ROLE_LECTURER, ROLE_ADMIN, ROLE_OPERATOR)

# ----------------------------------------------------------------------------
# Resources
# ----------------------------------------------------------------------------
RESOURCE_TYPES = ("Computer Lab", "Projector", "Seminar Room", "Presentation Equipment")
RESOURCE_STATUS_ACTIVE = "Active"
RESOURCE_STATUS_MAINTENANCE = "Maintenance"
RESOURCE_STATUS_REMOVED = "Removed"   # soft delete: keeps booking history intact
EDITABLE_RESOURCE_STATUSES = (RESOURCE_STATUS_ACTIVE, RESOURCE_STATUS_MAINTENANCE)

# ----------------------------------------------------------------------------
# Bookings
# ----------------------------------------------------------------------------
BOOKING_ACTIVE = "Active"
BOOKING_CANCELLED = "Cancelled"
SLOT_STEP_MINUTES = 30          # booking start times / durations move in 30 min steps
