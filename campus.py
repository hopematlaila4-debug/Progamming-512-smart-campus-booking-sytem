"""
campus.py
---------
Campus model. Each campus owns a BookingPolicy object chosen from the
policy registry using the policy_key stored in the database.
"""
from __future__ import annotations

from policies.booking_policies import BookingPolicy, get_policy


class Campus:
    def __init__(self, campus_id: int, code: str, name: str, city: str, policy_key: str):
        self.campus_id = campus_id
        self.code = code
        self.name = name
        self.city = city
        self.policy_key = policy_key
        self._policy: BookingPolicy = get_policy(policy_key)

    @property
    def policy(self) -> BookingPolicy:
        return self._policy

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.code})"

    @classmethod
    def from_row(cls, row) -> "Campus":
        return cls(row["id"], row["code"], row["name"], row["city"], row["policy_key"])

    def __str__(self) -> str:
        return self.display_name
