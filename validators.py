"""
validators.py
-------------
Input validation helpers. Every function either returns the cleaned value
or raises ValidationError with a message that can be shown to the user.
"""
from __future__ import annotations

import re
from datetime import date, datetime

from utils.errors import ValidationError

_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,59}$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,20}$")
_CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,14}$")


def validate_full_name(value: str) -> str:
    value = (value or "").strip()
    if not _NAME_RE.match(value):
        raise ValidationError(
            "Full name must be 2-60 characters and contain only letters, "
            "spaces, apostrophes, dots or hyphens."
        )
    return value


def validate_username(value: str) -> str:
    value = (value or "").strip()
    if not _USERNAME_RE.match(value):
        raise ValidationError(
            "Username must be 3-20 characters: letters, numbers, '_' or '.' only."
        )
    return value


def validate_password(password: str, confirm: str | None = None) -> str:
    password = password or ""
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one letter and one number.")
    if confirm is not None and password != confirm:
        raise ValidationError("Passwords do not match.")
    return password


def validate_resource_code(value: str) -> str:
    value = (value or "").strip().upper()
    if not _CODE_RE.match(value):
        raise ValidationError(
            "Resource ID must be 3-15 characters (letters, numbers, '-'), "
            "e.g. DBN-LAB-01."
        )
    return value


def validate_resource_name(value: str) -> str:
    value = (value or "").strip()
    if not (3 <= len(value) <= 50):
        raise ValidationError("Resource name must be between 3 and 50 characters.")
    return value


def validate_capacity(value) -> int:
    try:
        capacity = int(str(value).strip())
    except ValueError:
        raise ValidationError("Capacity must be a whole number.")
    if not (1 <= capacity <= 1000):
        raise ValidationError("Capacity must be between 1 and 1000.")
    return capacity


def validate_purpose(value: str) -> str:
    value = (value or "").strip()
    if not (3 <= len(value) <= 100):
        raise ValidationError("Purpose of booking must be between 3 and 100 characters.")
    return value


def parse_date(text: str) -> date:
    """Parse 'YYYY-MM-DD' into a date object."""
    try:
        return datetime.strptime((text or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Date must be a real date in YYYY-MM-DD format, e.g. 2026-11-05.")
