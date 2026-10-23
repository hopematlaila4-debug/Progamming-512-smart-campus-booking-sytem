"""
user.py
-------
Object-oriented user model (requirement 3).

    User  (base class, encapsulated attributes)
     |-- Lecturer
     |-- CampusAdministrator
     |-- SystemOperator

Each subclass defines the permissions of its role. The rest of the program
asks   user.can("permission")   instead of checking role names, so access
control lives in one place.
"""
from __future__ import annotations

import config


class User:
    """Base class for every logged-in user."""

    ROLE = "User"
    PERMISSIONS: frozenset = frozenset()

    def __init__(self, user_id: int, username: str, full_name: str, campus_id: int | None = None):
        # Encapsulation: attributes are "private" and exposed through read-only properties.
        self.__user_id = user_id
        self.__username = username
        self.__full_name = full_name
        self.__campus_id = campus_id

    # ----------------------------------------------------------- properties
    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def full_name(self) -> str:
        return self.__full_name

    @property
    def campus_id(self) -> int | None:
        """Home campus (only meaningful for campus administrators)."""
        return self.__campus_id

    @property
    def role(self) -> str:
        return self.ROLE

    # ------------------------------------------------------- access control
    def can(self, permission: str) -> bool:
        return permission in self.PERMISSIONS

    def can_access_campus(self, campus_id: int) -> bool:
        """Which campuses this user may select. Overridden by subclasses."""
        return True

    def __str__(self) -> str:
        return f"{self.full_name} ({self.ROLE})"


class Lecturer(User):
    ROLE = config.ROLE_LECTURER
    PERMISSIONS = frozenset({
        "book_resource",
        "view_own_bookings",
        "cancel_own_booking",
        "view_availability",
    })


class CampusAdministrator(User):
    ROLE = config.ROLE_ADMIN
    PERMISSIONS = frozenset({
        "manage_resources",
        "view_campus_bookings",
        "cancel_campus_booking",
        "view_campus_reports",
        "view_availability",
    })

    def can_access_campus(self, campus_id: int) -> bool:
        # An administrator works only on their own campus.
        return campus_id == self.campus_id


class SystemOperator(User):
    ROLE = config.ROLE_OPERATOR
    PERMISSIONS = frozenset({
        "view_all_bookings",
        "view_all_resources",
        "view_campus_reports",
        "view_cross_campus_reports",
        "manage_campuses",
        "view_availability",
    })


# Dictionary used as a simple factory: role name -> class
_ROLE_CLASSES = {
    config.ROLE_LECTURER: Lecturer,
    config.ROLE_ADMIN: CampusAdministrator,
    config.ROLE_OPERATOR: SystemOperator,
}


def create_user(row) -> User:
    """Build the correct User subclass from a database row."""
    user_class = _ROLE_CLASSES[row["role"]]
    return user_class(row["id"], row["username"], row["full_name"], row["campus_id"])
