"""
access.py
---------
Role-based access control helpers used by every service.
The services call these before doing anything sensitive, so a user can never
do something their role does not allow - even if the GUI is changed later.
"""
from utils.errors import PermissionDenied


def require(user, permission: str) -> None:
    """Stop with PermissionDenied unless the user's role has this permission."""
    if user is None or not user.can(permission):
        raise PermissionDenied("Your account is not allowed to perform this action.")


def require_campus(user, campus_id: int) -> None:
    """Stop unless the user is allowed to work on this campus."""
    if not user.can_access_campus(campus_id):
        raise PermissionDenied("You can only work on the campus assigned to your account.")
