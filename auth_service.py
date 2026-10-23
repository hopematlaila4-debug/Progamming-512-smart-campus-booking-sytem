"""
auth_service.py
---------------
Registration and login. Only lecturers can register themselves; campus
administrators and system operators are created by the institution
(see database/seed_data.py).
"""
import sqlite3

import config
from models.user import create_user
from utils.errors import AuthError
from utils.security import generate_salt, hash_password, verify_password
from utils.validators import validate_full_name, validate_password, validate_username


class AuthService:
    def __init__(self, db):
        self.db = db

    def register_lecturer(self, full_name, username, password, confirm):
        """Validate the form, then store a new lecturer account."""
        full_name = validate_full_name(full_name)
        username = validate_username(username)
        validate_password(password, confirm)

        if self.db.query_one("SELECT 1 FROM users WHERE username = ?", (username,)):
            raise AuthError("That username is already taken. Please choose another one.")

        salt = generate_salt()
        try:
            self.db.execute(
                "INSERT INTO users (username, full_name, password_hash, salt, role) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, full_name, hash_password(password, salt), salt, config.ROLE_LECTURER),
            )
        except sqlite3.IntegrityError:
            raise AuthError("That username is already taken. Please choose another one.")

    def login(self, username, password):
        """Return the matching User object (Lecturer / CampusAdministrator / SystemOperator)."""
        username = (username or "").strip()
        if not username or not password:
            raise AuthError("Please enter both your username and your password.")

        row = self.db.query_one("SELECT * FROM users WHERE username = ?", (username,))
        # Same message for "no such user" and "wrong password" so nothing is leaked.
        if row is None or not verify_password(password, row["salt"], row["password_hash"]):
            raise AuthError("Incorrect username or password.")
        return create_user(row)
