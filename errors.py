"""
errors.py
---------
Custom exception hierarchy. The GUI catches AppError and shows the message
in a friendly dialog, so every error raised by the service layer is
written for the end user to read.
"""


class AppError(Exception):
    """Base class for all expected, user-facing errors."""


class ValidationError(AppError):
    """Raised when user input is missing or badly formatted."""


class AuthError(AppError):
    """Raised for login / registration problems."""


class PermissionDenied(AppError):
    """Raised when a user tries to do something their role does not allow."""


class ResourceError(AppError):
    """Raised for resource registration / maintenance problems."""


class BookingError(AppError):
    """Raised when a booking breaks a rule (overlap, policy, past date...)."""
