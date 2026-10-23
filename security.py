"""
security.py
-----------
Password hashing helpers. Passwords are NEVER stored in plain text: each
password gets its own random salt and is hashed with PBKDF2-HMAC-SHA256.
"""
import hashlib
import hmac
import os

_ITERATIONS = 120_000


def generate_salt() -> str:
    """Return a new random salt as a hex string."""
    return os.urandom(16).hex()


def hash_password(password: str, salt: str) -> str:
    """Hash a password with the given salt and return the hex digest."""
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    )
    return digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Constant-time comparison of a login attempt against the stored hash."""
    return hmac.compare_digest(hash_password(password, salt), expected_hash)
