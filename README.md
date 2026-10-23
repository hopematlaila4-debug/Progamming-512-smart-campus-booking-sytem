# Smart Campus Resource Booking System
Programming 512 - Case Study (100 marks)  |  Python + Tkinter + SQLite

## How to run (PyCharm)
1. Unzip the folder and open it in PyCharm (File > Open > select `smart_campus_booking`).
2. Right-click `main.py` > **Run 'main'**. No packages need installing.
3. The first run creates `data/campus_booking.db` and fills it with demo data.
   To reset everything, close the program and delete the `data` folder.

## Demo accounts
| Role                 | Username        | Password      |
|----------------------|-----------------|---------------|
| Lecturer             | thandi.nkosi    | Lecturer@123  |
| Lecturer (more)      | sipho.dlamini, ayesha.patel, john.smith | Lecturer@123 |
| Campus Administrator | admin_dbn / admin_jhb / admin_cpt / admin_pta | Admin@123 |
| System Operator      | operator        | Operator@123  |

New lecturers can register themselves on the login screen.

## Campus booking policies (requirement 5.1)
| Campus       | Max session | Hours       | Days    | Book ahead | Max upcoming / lecturer | Extra rule |
|--------------|-------------|-------------|---------|------------|-------------------------|------------|
| Durban       | 3 h         | 08:00-17:00 | Mon-Fri | 30 days    | 5                       | Computer labs need 24 h notice |
| Johannesburg | 2 h         | 07:00-20:00 | Mon-Fri | 14 days    | 3                       | Seminar rooms need 48 h notice |
| Cape Town    | 4 h         | 08:00-18:00 | Mon-Sat | 60 days    | 6                       | - |
| Pretoria     | 1 h 30 m    | 08:00-16:00 | Mon-Fri | 21 days    | 4                       | Computer labs max 1 h |

## Project structure
```
smart_campus_booking/
  main.py                    start the program
  config.py                  constants (roles, statuses, file paths)
  database/
    db_manager.py            SQLite connection, tables, helper methods
    seed_data.py             demo campuses, resources, users, bookings
  models/
    user.py                  User -> Lecturer / CampusAdministrator / SystemOperator
    campus.py  resource.py  booking.py
  policies/
    booking_policies.py      BookingPolicy base class + one subclass per campus
  services/                  the logic, no GUI code in here
    auth_service.py  campus_service.py  resource_service.py
    booking_service.py  report_service.py  access.py
  gui/                       Tkinter screens (sky-blue theme in theme.py)
    app.py  login_view.py  campus_view.py  dashboard.py
    lecturer_view.py  admin_view.py  operator_view.py  report_panel.py
    theme.py  widgets.py
  utils/                     validators, time helpers, password hashing, errors
```

## Where each requirement is met
| Section | Requirement | Where |
|---------|-------------|-------|
| 2 | Lists, dictionaries, sets | `CampusService.campuses` (dict), `ResourceService.used_codes` (set), `POLICY_REGISTRY` (dict), report aggregation (dicts/lists) |
| 3 | Roles with OOP (classes, inheritance, encapsulation) | `models/user.py` - private attributes + properties, role subclasses with permission sets |
| 3.1 | Lecturer: register, login, select campus, view resources, book, history | `login_view.py`, `campus_view.py`, `lecturer_view.py` |
| 3.2 | Admin: add/update/remove resources, campus bookings, availability and usage | `admin_view.py`, `resource_service.py` |
| 3.3 | Operator: system-wide data, comparative reports | `operator_view.py`, `report_service.py` |
| 4.1 | Campus selection, active campus shown | `campus_view.py`, header in `app.py` |
| 4.2 | Unique resource ID, duplicates rejected | `ResourceService.add_resource` (set check + UNIQUE constraint) |
| 4.3 | Date, start time, duration; linked to lecturer + campus; no overlaps | `BookingService.create_booking` |
| 5.1 | 4 campuses with different rules, applied automatically, policy shown | `booking_policies.py`, header + policy panel |
| 5.2 | Rules separate from core logic; easy to extend | `@register_policy` classes; operator can add a campus on the "Campuses" page |
| 6.1 | View active bookings, cancel future ones, history | `ActiveBookingsPage`, `HistoryPage`, `BookingService.cancel_booking` |
| 6.2 | Live availability, block unavailable resources | `BookingService.availability` (auto-refresh every 30 s), maintenance resources cannot be booked |
| 7.1 | Campus report: total, most used, average duration | `ReportPanel` / `ReportService.campus_report` |
| 7.2 | Cross-campus comparison | `ComparePage` / `ReportService.comparison`, insights and CSV export |
| 8 | SQLite persistence | `database/db_manager.py` - users, campuses, resources, bookings |
| 10 | Readable, commented code, validation, error handling | `utils/validators.py`, `utils/errors.py`, `@safe` decorator in `widgets.py` |

## Adding a new campus rule or campus
1. In `policies/booking_policies.py` add a subclass of `BookingPolicy` with `@register_policy` and set its values.
2. Log in as the operator > Campuses > Add campus, and pick the new policy. No other file changes.
