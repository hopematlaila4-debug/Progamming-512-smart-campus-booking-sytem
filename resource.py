"""
resource.py
-----------
Resource model (computer lab, projector, seminar room, presentation equipment).
"""
from __future__ import annotations

from dataclasses import dataclass

import config


@dataclass
class Resource:
    resource_id: int
    code: str            # unique identifier, e.g. DBN-LAB-01
    name: str
    resource_type: str
    capacity: int
    campus_id: int
    status: str

    @property
    def is_bookable(self) -> bool:
        return self.status == config.RESOURCE_STATUS_ACTIVE

    @property
    def label(self) -> str:
        """Text shown in drop-down lists."""
        return f"{self.code} - {self.name} ({self.resource_type}, {self.capacity})"

    @classmethod
    def from_row(cls, row) -> "Resource":
        return cls(row["id"], row["resource_code"], row["name"], row["resource_type"],
                   row["capacity"], row["campus_id"], row["status"])
