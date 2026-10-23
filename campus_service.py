"""
campus_service.py
-----------------
Keeps all campuses in a dictionary (campus id -> Campus object) loaded from
the database, so the rest of the program never has to query for them again.
"""
import re
import sqlite3

from models.campus import Campus
from policies.booking_policies import POLICY_REGISTRY
from services.access import require
from utils.errors import ValidationError


class CampusService:
    def __init__(self, db):
        self.db = db
        self.campuses = {}          # dictionary: campus id -> Campus
        self.reload()

    def reload(self):
        rows = self.db.query("SELECT * FROM campuses ORDER BY name")
        self.campuses = {row["id"]: Campus.from_row(row) for row in rows}

    def all(self):
        return list(self.campuses.values())

    def get(self, campus_id):
        return self.campuses.get(campus_id)

    def accessible_to(self, user):
        """Campuses this user is allowed to select after logging in."""
        return [c for c in self.all() if user.can_access_campus(c.campus_id)]

    def policy_keys(self):
        """Policy keys available when creating a campus (from the registry dictionary)."""
        return sorted(key for key in POLICY_REGISTRY if key != "default")

    def add_campus(self, user, code, name, city, policy_key):
        """System operators can add a campus; its rules come from the chosen policy."""
        require(user, "manage_campuses")
        code = (code or "").strip().upper()
        name = (name or "").strip()
        city = (city or "").strip()
        if not re.match(r"^[A-Z]{2,5}$", code):
            raise ValidationError("Campus code must be 2-5 letters, e.g. PE.")
        if not (3 <= len(name) <= 40):
            raise ValidationError("Campus name must be between 3 and 40 characters.")
        if not (2 <= len(city) <= 40):
            raise ValidationError("City must be between 2 and 40 characters.")
        if policy_key not in POLICY_REGISTRY:
            raise ValidationError("Please choose a booking policy for the campus.")
        try:
            self.db.execute(
                "INSERT INTO campuses (code, name, city, policy_key) VALUES (?, ?, ?, ?)",
                (code, name, city, policy_key),
            )
        except sqlite3.IntegrityError:
            raise ValidationError("A campus with that code already exists.")
        self.reload()
