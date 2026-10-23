"""
resource_service.py
-------------------
Add, update, remove and list campus resources.

Duplicate detection (requirement 4.2) works on two levels:
    1. a Python set of every resource ID ever used (fast check, clear message)
    2. the UNIQUE constraint in SQLite (safety net)
Removing a resource is a "soft delete" (status = Removed) so old bookings
and reports still make sense.
"""
import sqlite3
from datetime import datetime

import config
from models.resource import Resource
from services.access import require, require_campus
from utils.errors import ResourceError, ValidationError
from utils.validators import (validate_capacity, validate_resource_code,
                              validate_resource_name)


class ResourceService:
    def __init__(self, db):
        self.db = db
        # set of all resource IDs (upper case) - sets cannot hold duplicates
        self.used_codes = {row["resource_code"].upper()
                           for row in db.query("SELECT resource_code FROM resources")}

    # ------------------------------------------------------------- reading
    def get(self, resource_id):
        row = self.db.query_one("SELECT * FROM resources WHERE id = ?", (resource_id,))
        return Resource.from_row(row) if row else None

    def list_for_campus(self, campus_id, include_removed=False):
        sql = "SELECT * FROM resources WHERE campus_id = ?"
        if not include_removed:
            sql += " AND status != 'Removed'"
        rows = self.db.query(sql + " ORDER BY resource_code", (campus_id,))
        return [Resource.from_row(r) for r in rows]

    def list_all(self):
        """Every resource on every campus: list of (campus name, Resource) pairs."""
        rows = self.db.query(
            "SELECT r.*, c.name AS campus_name FROM resources r "
            "JOIN campuses c ON c.id = r.campus_id WHERE r.status != 'Removed' "
            "ORDER BY c.name, r.resource_code")
        return [(row["campus_name"], Resource.from_row(row)) for row in rows]

    # ------------------------------------------------------------- writing
    def add_resource(self, user, campus_id, code, name, resource_type, capacity):
        require(user, "manage_resources")
        require_campus(user, campus_id)

        code = validate_resource_code(code)
        name = validate_resource_name(name)
        capacity = validate_capacity(capacity)
        self._check_type(resource_type)

        if code in self.used_codes:
            raise ResourceError(f"Resource ID {code} already exists. Every resource needs a unique ID.")
        same_name = self.db.query_one(
            "SELECT 1 FROM resources WHERE campus_id = ? AND status != 'Removed' "
            "AND LOWER(name) = LOWER(?)", (campus_id, name))
        if same_name:
            raise ResourceError(f"This campus already has a resource called '{name}'.")

        try:
            new_id = self.db.execute(
                "INSERT INTO resources (resource_code, name, resource_type, capacity, campus_id) "
                "VALUES (?, ?, ?, ?, ?)", (code, name, resource_type, capacity, campus_id))
        except sqlite3.IntegrityError:
            raise ResourceError(f"Resource ID {code} already exists.")
        self.used_codes.add(code)
        return self.get(new_id)

    def update_resource(self, user, resource_id, name, resource_type, capacity, status):
        require(user, "manage_resources")
        resource = self._get_for_admin(user, resource_id)

        name = validate_resource_name(name)
        capacity = validate_capacity(capacity)
        self._check_type(resource_type)
        if status not in config.EDITABLE_RESOURCE_STATUSES:
            raise ValidationError("Status must be Active or Maintenance.")

        same_name = self.db.query_one(
            "SELECT 1 FROM resources WHERE campus_id = ? AND status != 'Removed' "
            "AND LOWER(name) = LOWER(?) AND id != ?", (resource.campus_id, name, resource_id))
        if same_name:
            raise ResourceError(f"This campus already has a resource called '{name}'.")

        self.db.execute(
            "UPDATE resources SET name = ?, resource_type = ?, capacity = ?, status = ? WHERE id = ?",
            (name, resource_type, capacity, status, resource_id))

    def remove_resource(self, user, resource_id):
        require(user, "manage_resources")
        resource = self._get_for_admin(user, resource_id)

        now = datetime.now()
        pending = self.db.query_one(
            "SELECT COUNT(*) AS n FROM bookings WHERE resource_id = ? AND status = 'Active' "
            "AND (booking_date > ? OR (booking_date = ? AND start_minutes + duration_minutes > ?))",
            (resource_id, now.date().isoformat(), now.date().isoformat(), now.hour * 60 + now.minute))
        if pending["n"]:
            raise ResourceError(
                f"{resource.name} still has {pending['n']} upcoming booking(s). "
                "Cancel them first, or set the resource to Maintenance instead.")

        self.db.execute("UPDATE resources SET status = 'Removed' WHERE id = ?", (resource_id,))

    # ------------------------------------------------------------- helpers
    def _get_for_admin(self, user, resource_id):
        resource = self.get(resource_id)
        if resource is None or resource.status == config.RESOURCE_STATUS_REMOVED:
            raise ResourceError("Please select a resource from the table first.")
        require_campus(user, resource.campus_id)
        return resource

    @staticmethod
    def _check_type(resource_type):
        if resource_type not in config.RESOURCE_TYPES:
            raise ValidationError("Please choose a resource type from the list.")
