"""
seed_data.py
------------
Fills an EMPTY database with starter data:
    * four campuses, each with its own booking policy
    * resources for every campus
    * demo accounts (one operator, one administrator per campus, four lecturers)
    * about five weeks of past bookings and two weeks of upcoming bookings so
      that the reports and charts have something meaningful to show

The seed only runs when the campuses table is empty, so it never overwrites
real data. Delete data/campus_booking.db to reset the system.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

import config
from policies.booking_policies import get_policy
from utils.security import generate_salt, hash_password

# (code, name, city, policy_key)
CAMPUSES = [
    ("DBN", "Durban", "Durban", "durban"),
    ("JHB", "Johannesburg", "Johannesburg", "johannesburg"),
    ("CPT", "Cape Town", "Cape Town", "cape_town"),
    ("PTA", "Pretoria", "Pretoria", "pretoria"),
]

# Resources per campus: (suffix, name, type, capacity)
RESOURCE_TEMPLATES = [
    ("LAB-01", "Computer Lab A", "Computer Lab", 40),
    ("LAB-02", "Computer Lab B", "Computer Lab", 30),
    ("PRJ-01", "Multimedia Projector 1", "Projector", 1),
    ("PRJ-02", "Multimedia Projector 2", "Projector", 1),
    ("SEM-01", "Seminar Room 1", "Seminar Room", 25),
    ("SEM-02", "Seminar Room 2", "Seminar Room", 60),
    ("PRE-01", "Presentation Kit 1", "Presentation Equipment", 1),
]

LECTURERS = [
    ("thandi.nkosi", "Thandi Nkosi"),
    ("sipho.dlamini", "Sipho Dlamini"),
    ("ayesha.patel", "Ayesha Patel"),
    ("john.smith", "John Smith"),
]

PURPOSES = ["Lecture", "Practical session", "Assessment", "Tutorial", "Guest presentation",
            "Workshop", "Revision class", "Student presentations"]

OPERATOR_PASSWORD = "Operator@123"
ADMIN_PASSWORD = "Admin@123"
LECTURER_PASSWORD = "Lecturer@123"


def _add_user(db, username, full_name, password, role, campus_id=None) -> int:
    salt = generate_salt()
    return db.execute(
        "INSERT INTO users (username, full_name, password_hash, salt, role, campus_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (username, full_name, hash_password(password, salt), salt, role, campus_id),
    )


def seed_database(db) -> None:
    """Populate the database if (and only if) it is empty."""
    if db.query_one("SELECT 1 FROM campuses LIMIT 1") is not None:
        return

    campus_ids: dict[str, int] = {}
    resource_rows: dict[int, list[dict]] = {}          # campus id -> list of resource info

    # --- campuses and resources -------------------------------------------
    for code, name, city, policy_key in CAMPUSES:
        cid = db.execute(
            "INSERT INTO campuses (code, name, city, policy_key) VALUES (?, ?, ?, ?)",
            (code, name, city, policy_key),
        )
        campus_ids[code] = cid
        resource_rows[cid] = []
        for suffix, rname, rtype, capacity in RESOURCE_TEMPLATES:
            rid = db.execute(
                "INSERT INTO resources (resource_code, name, resource_type, capacity, campus_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"{code}-{suffix}", rname, rtype, capacity, cid),
            )
            resource_rows[cid].append({"id": rid, "type": rtype})

    # --- users ---------------------------------------------------------------
    _add_user(db, "operator", "Nomsa Mokoena", OPERATOR_PASSWORD, config.ROLE_OPERATOR)
    admin_names = {"DBN": "Zanele Khumalo", "JHB": "Pieter van Wyk",
                   "CPT": "Fatima Adams", "PTA": "Lerato Molefe"}
    for code, cid in campus_ids.items():
        _add_user(db, f"admin_{code.lower()}", admin_names[code], ADMIN_PASSWORD,
                  config.ROLE_ADMIN, cid)
    lecturer_ids = [
        _add_user(db, username, full_name, LECTURER_PASSWORD, config.ROLE_LECTURER)
        for username, full_name in LECTURERS
    ]

    # --- historical and upcoming bookings --------------------------------------
    rng = random.Random(512)                 # fixed seed -> same demo data every time
    today = date.today()
    campus_policies = {cid: get_policy(key) for (_, _, _, key), cid in zip(CAMPUSES, campus_ids.values())}

    for cid, resources in resource_rows.items():
        policy = campus_policies[cid]
        # Popularity weights so some resources are clearly busier than others.
        weights = [7, 4, 6, 2, 5, 3, 1]
        taken: dict[tuple[int, str], list[tuple[int, int]]] = {}   # (resource, date) -> busy slots
        # Keep room under the campus booking limit so the demo lecturers can still make new bookings.
        upcoming_cap = max(1, policy.max_active_bookings - 2)
        upcoming_count = {lid: 0 for lid in lecturer_ids}

        for offset in range(-35, 15):
            day = today + timedelta(days=offset)
            if day.weekday() not in policy.allowed_weekdays:
                continue
            for _ in range(rng.randint(7, 12)):
                resource = rng.choices(resources, weights=weights[:len(resources)])[0]
                limit = policy.duration_limit_for(resource["type"])
                duration = rng.choice([d for d in range(60, limit + 1, 30)] or [limit])
                latest_start = policy.close_minutes - duration
                if latest_start < policy.open_minutes:
                    continue
                start = rng.randrange(policy.open_minutes, latest_start + 1, 30)
                key = (resource["id"], day.isoformat())
                slots = taken.setdefault(key, [])
                if any(start < e and start + duration > s for s, e in slots):
                    continue                    # would overlap an existing booking
                slots.append((start, start + duration))
                status = "Cancelled" if rng.random() < 0.08 else "Active"
                lecturer = rng.choice(lecturer_ids)
                if offset >= 0 and status == "Active":
                    free = [lid for lid in lecturer_ids if upcoming_count[lid] < upcoming_cap]
                    if not free:
                        slots.pop()             # limit reached: drop this future booking
                        continue
                    lecturer = rng.choice(free)
                    upcoming_count[lecturer] += 1
                db.execute(
                    "INSERT INTO bookings (resource_id, lecturer_id, campus_id, booking_date, "
                    "start_minutes, duration_minutes, purpose, status) VALUES (?,?,?,?,?,?,?,?)",
                    (resource["id"], lecturer, cid, day.isoformat(),
                     start, duration, rng.choice(PURPOSES), status),
                )
