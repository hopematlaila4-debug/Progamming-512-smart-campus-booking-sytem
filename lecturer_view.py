"""
lecturer_view.py
----------------
Lecturer screens:
    Book a Resource   - live availability, booking form, day schedule, policy panel
    Active Bookings   - current and future bookings, with cancel
    Booking History   - past and cancelled bookings
All bookings are read from / written to SQLite through the booking service.
"""
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

import config
from gui import theme
from gui.dashboard import Dashboard
from gui.widgets import STATUS_TAGS, Card, Table, pretty_date, safe
from utils.errors import BookingError, ValidationError
from utils.timeutils import format_duration, time_slots
from utils.validators import parse_date


class LecturerDashboard(Dashboard):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.add_page("book", "Book a resource", BookPage)
        self.add_page("active", "Active bookings", ActiveBookingsPage)
        self.add_page("history", "Booking history", HistoryPage)
        self.show_page("book")


# =============================================================================
class BookPage(ttk.Frame):
    REFRESH_MS = 30000          # availability refreshes itself every 30 seconds

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.campus = app.campus
        self.resource_map = {}      # dictionary: resource id -> Resource
        self.selected = None        # the Resource chosen in the table
        self.timer = None

        ttk.Label(self, text="Book a resource", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text=f"Choose a resource at {self.campus.name}, then pick a date, start time and duration."
                  ).pack(anchor="w", pady=(0, 10))

        columns = ttk.Frame(self)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=3, uniform="cols")
        columns.columnconfigure(1, weight=2, uniform="cols")
        columns.rowconfigure(0, weight=1)
        left = ttk.Frame(columns)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        right = ttk.Frame(columns)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_left(left)
        self._build_form(right)
        self._build_policy(right)

    # ------------------------------------------------------------ layout
    def _build_left(self, left):
        card = Card(left, "Live resource availability")
        card.pack(fill="both", expand=True)
        top = ttk.Frame(card.body, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 6))
        self.updated = ttk.Label(top, text="", style="CardMuted.TLabel")
        self.updated.pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right")

        self.table = Table(card.body, [("ID", 98, "w"), ("Resource", 135, "w"), ("Type", 112, "w"),
                                       ("Seats", 52, "center"), ("Available now?", 140, "w")], height=8)
        self.table.pack(fill="both", expand=True)
        self.table.on_select(self.on_resource_selected)

        card2 = Card(left, None)
        card2.pack(fill="x", pady=(12, 0))
        self.schedule_title = ttk.Label(card2.body, text="Select a resource to see its bookings for the chosen date.",
                                        style="Card.TLabel", font=theme.FONT_BOLD)
        self.schedule_title.pack(anchor="w", pady=(0, 6))
        self.schedule = Table(card2.body, [("Time", 110, "w"), ("Lecturer", 170, "w"), ("Purpose", 220, "w")],
                              height=4)
        self.schedule.pack(fill="x")

    def _build_form(self, right):
        policy = self.campus.policy
        card = Card(right, "New booking")
        card.pack(fill="x")
        form = card.body
        form.columnconfigure(1, weight=1)

        self.resource_var = tk.StringVar(value="Select a resource from the table")
        self.date_var = tk.StringVar(value=policy.next_valid_date().isoformat())
        self.start_var = tk.StringVar(value="09:00")
        self.duration_var = tk.StringVar(value="60")
        self.purpose_var = tk.StringVar()

        ttk.Label(form, text="Resource", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(form, textvariable=self.resource_var, style="Card.TLabel", font=theme.FONT_BOLD,
                  wraplength=250, foreground=theme.SKY_DEEP).grid(row=0, column=1, sticky="w", padx=(10, 0))

        ttk.Label(form, text="Date", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        date_row = ttk.Frame(form, style="Card.TFrame")
        date_row.grid(row=1, column=1, sticky="w", padx=(10, 0))
        self.date_box = ttk.Combobox(date_row, textvariable=self.date_var, values=self._valid_dates(), width=13)
        self.date_box.pack(side="left")
        self.weekday_label = ttk.Label(date_row, text="", style="CardMuted.TLabel")
        self.weekday_label.pack(side="left", padx=8)
        self.date_box.bind("<<ComboboxSelected>>", lambda e: self.on_date_changed())
        self.date_box.bind("<FocusOut>", lambda e: self.on_date_changed())
        self.date_box.bind("<Return>", lambda e: self.on_date_changed())

        ttk.Label(form, text="Start time", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        slots = time_slots(policy.open_minutes, policy.close_minutes - config.SLOT_STEP_MINUTES,
                           config.SLOT_STEP_MINUTES)
        if self.start_var.get() not in slots:
            self.start_var.set(slots[0])
        ttk.Combobox(form, textvariable=self.start_var, values=slots, width=13).grid(
            row=2, column=1, sticky="w", padx=(10, 0))

        ttk.Label(form, text="Duration (min)", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        duration_row = ttk.Frame(form, style="Card.TFrame")
        duration_row.grid(row=3, column=1, sticky="w", padx=(10, 0))
        self.duration_box = ttk.Combobox(duration_row, textvariable=self.duration_var, width=13)
        self.duration_box.pack(side="left")
        self.duration_hint = ttk.Label(duration_row, text="", style="CardMuted.TLabel")
        self.duration_hint.pack(side="left", padx=8)
        self._set_duration_choices(policy.max_duration_minutes)

        ttk.Label(form, text="Purpose", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.purpose_var).grid(row=4, column=1, sticky="ew", padx=(10, 0))

        ttk.Button(form, text="Book this resource", style="Primary.TButton",
                   command=self.book).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.on_date_changed()

    def _build_policy(self, right):
        card = Card(right, "Booking policy in effect")
        card.pack(fill="x", pady=(12, 0))
        ttk.Label(card.body, text=self.campus.policy.name, style="Card.TLabel", font=theme.FONT_BOLD,
                  foreground=theme.SKY_DEEP).pack(anchor="w", pady=(0, 4))
        for line in self.campus.policy.describe():
            ttk.Label(card.body, text="• " + line, style="Card.TLabel", wraplength=330,
                      justify="left").pack(anchor="w", pady=1)

    # ------------------------------------------------------------ helpers
    def _valid_dates(self):
        """Dates this campus accepts bookings for (respects days and how far ahead)."""
        policy = self.campus.policy
        today = date.today()
        days = [today + timedelta(days=i) for i in range(policy.max_advance_days + 1)]
        return [d.isoformat() for d in days if d.weekday() in policy.allowed_weekdays]

    def _set_duration_choices(self, limit):
        choices = [str(m) for m in range(config.SLOT_STEP_MINUTES, limit + 1, config.SLOT_STEP_MINUTES)]
        self.duration_box.configure(values=choices)
        self.duration_hint.configure(text=f"max {format_duration(limit)}")
        if self.duration_var.get() not in choices:
            self.duration_var.set(choices[min(1, len(choices) - 1)])

    def on_resource_selected(self):
        rid = self.table.selected_id()
        self.selected = self.resource_map.get(int(rid)) if rid else None
        if self.selected:
            self.resource_var.set(f"{self.selected.name} ({self.selected.code})")
            self._set_duration_choices(self.campus.policy.duration_limit_for(self.selected.resource_type))
        self.refresh_schedule()

    def on_date_changed(self):
        try:
            self.weekday_label.configure(text=parse_date(self.date_var.get()).strftime("%A"))
        except ValidationError:
            self.weekday_label.configure(text="(invalid date)")
        self.refresh_schedule()

    # ------------------------------------------------------------ data
    def refresh(self):
        """Reload resources + live availability, then schedule the next automatic refresh."""
        if self.timer:
            self.after_cancel(self.timer)
        campus_id = self.campus.campus_id
        resources = self.app.resources.list_for_campus(campus_id)
        status = self.app.bookings.availability(campus_id)
        self.resource_map = {r.resource_id: r for r in resources}

        rows = []
        for r in resources:
            text, tag = status[r.resource_id]
            rows.append((r.resource_id, (r.code, r.name, r.resource_type, r.capacity, text), tag))
        self.table.set_rows(rows)
        self.updated.configure(text="Updated " + datetime.now().strftime("%H:%M:%S")
                                    + " (refreshes every 30 s)")
        self.refresh_schedule()
        self.timer = self.after(self.REFRESH_MS, self.refresh)

    def refresh_schedule(self):
        rows = []
        if self.selected is None:
            self.schedule_title.configure(text="Select a resource to see its bookings for the chosen date.")
        else:
            try:
                day = parse_date(self.date_var.get())
            except ValidationError:
                day = None
            if day is None:
                self.schedule_title.configure(text="Enter a valid date to see the schedule.")
            else:
                self.schedule_title.configure(text=f"Already booked: {self.selected.name} on {pretty_date(day)}")
                for b in self.app.bookings.for_resource_on(self.selected.resource_id, day):
                    rows.append((b.booking_id, (f"{b.start_text} - {b.end_text}", b.lecturer_name, b.purpose), None))
        self.schedule.set_rows(rows)

    @safe
    def book(self):
        if self.selected is None:
            raise BookingError("Please select a resource from the table first.")
        booking = self.app.bookings.create_booking(
            self.app.user, self.campus, self.selected.resource_id, self.date_var.get(),
            self.start_var.get(), self.duration_var.get(), self.purpose_var.get())
        messagebox.showinfo(
            "Booking confirmed",
            f"{booking.resource_name} ({booking.resource_code})\n"
            f"{pretty_date(booking.booking_date)}, {booking.start_text} - {booking.end_text}\n"
            f"Campus: {booking.campus_name}")
        self.purpose_var.set("")
        self.refresh()

    def destroy(self):
        if self.timer:
            self.after_cancel(self.timer)
        super().destroy()


# =============================================================================
class ActiveBookingsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="My active bookings", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text="Upcoming and in-progress bookings on all campuses. Only bookings that have "
                       "not started yet can be cancelled.").pack(anchor="w", pady=(0, 10))

        card = Card(self)
        card.pack(fill="both", expand=True)
        self.table = Table(card.body, [("Ref", 50, "center"), ("Campus", 110, "w"), ("Resource", 170, "w"),
                                       ("Date", 135, "w"), ("Time", 110, "center"), ("Duration", 70, "center"),
                                       ("Purpose", 190, "w"), ("Status", 90, "center")], height=14)
        self.table.pack(fill="both", expand=True)

        bar = ttk.Frame(card.body, style="Card.TFrame")
        bar.pack(fill="x", pady=(10, 0))
        self.count_label = ttk.Label(bar, text="", style="CardMuted.TLabel")
        self.count_label.pack(side="left")
        ttk.Button(bar, text="Cancel selected booking", style="Danger.TButton",
                   command=self.cancel).pack(side="right")

    def refresh(self):
        bookings = self.app.bookings.for_lecturer(self.app.user.user_id)
        active = [b for b in bookings if b.is_current_or_future()]
        rows = []
        for b in active:
            status = b.status()
            rows.append((b.booking_id, (b.booking_id, b.campus_name, b.resource_name,
                                        pretty_date(b.booking_date), f"{b.start_text} - {b.end_text}",
                                        format_duration(b.duration_minutes), b.purpose, status),
                         STATUS_TAGS[status]))
        self.table.set_rows(rows)
        self.count_label.configure(text=f"{len(active)} active booking(s)")

    @safe
    def cancel(self):
        booking_id = self.table.selected_id()
        if booking_id is None:
            raise BookingError("Please select a booking in the table first.")
        if not messagebox.askyesno("Cancel booking", "Are you sure you want to cancel this booking?"):
            return
        self.app.bookings.cancel_booking(self.app.user, int(booking_id))
        messagebox.showinfo("Booking cancelled", "The booking was cancelled and the resource is free again.")
        self.refresh()


# =============================================================================
class HistoryPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Booking history", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text="Your completed and cancelled bookings, newest first.").pack(anchor="w", pady=(0, 10))

        card = Card(self)
        card.pack(fill="both", expand=True)
        bar = ttk.Frame(card.body, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Show:", style="Card.TLabel").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        box = ttk.Combobox(bar, textvariable=self.filter_var, state="readonly", width=14,
                           values=["All", "Completed", "Cancelled"])
        box.pack(side="left", padx=8)
        box.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.summary = ttk.Label(bar, text="", style="CardMuted.TLabel")
        self.summary.pack(side="right")

        self.table = Table(card.body, [("Ref", 50, "center"), ("Campus", 110, "w"), ("Resource", 170, "w"),
                                       ("Date", 135, "w"), ("Time", 110, "center"), ("Duration", 70, "center"),
                                       ("Purpose", 190, "w"), ("Status", 90, "center")], height=14)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        wanted = self.filter_var.get()
        past = [b for b in self.app.bookings.for_lecturer(self.app.user.user_id)
                if not b.is_current_or_future()]
        past.reverse()                                  # newest first
        if wanted != "All":
            past = [b for b in past if b.status() == wanted]

        rows = []
        hours = 0
        for b in past:
            status = b.status()
            if status == "Completed":
                hours += b.duration_minutes / 60
            rows.append((b.booking_id, (b.booking_id, b.campus_name, b.resource_name,
                                        pretty_date(b.booking_date), f"{b.start_text} - {b.end_text}",
                                        format_duration(b.duration_minutes), b.purpose, status),
                         STATUS_TAGS[status]))
        self.table.set_rows(rows)
        self.summary.configure(text=f"{len(past)} record(s)  |  {hours:.1f} hours of completed sessions")
