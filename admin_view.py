"""
admin_view.py
-------------
Campus administrator screens (the administrator works on one campus):
    Resources         - add, update and remove resources
    Campus bookings   - every booking on the campus, with filter and cancel
    Usage & trends    - campus report and availability monitoring
"""
import tkinter as tk
from tkinter import messagebox, ttk

import config
from gui import theme
from gui.dashboard import Dashboard
from gui.report_panel import ReportPanel
from gui.widgets import STATUS_TAGS, Card, Table, pretty_date, safe
from utils.errors import BookingError, ResourceError
from utils.timeutils import format_duration


class AdminDashboard(Dashboard):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.add_page("resources", "Manage resources", ResourcesPage)
        self.add_page("bookings", "Campus bookings", CampusBookingsPage)
        self.add_page("usage", "Usage & trends", UsagePage)
        self.show_page("resources")


# =============================================================================
class ResourcesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.campus = app.campus
        self.editing = None             # id of the resource being edited (None = adding a new one)
        self.resource_map = {}

        ttk.Label(self, text="Manage resources", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text=f"Resources registered at {self.campus.name}. Select a row to edit it, "
                       "or fill in the form to add a new one.").pack(anchor="w", pady=(0, 10))

        columns = ttk.Frame(self)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=3, uniform="cols")
        columns.columnconfigure(1, weight=2, uniform="cols")
        columns.rowconfigure(0, weight=1)

        card = Card(columns, "Campus resources and live status")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.table = Table(card.body, [("Resource ID", 100, "w"), ("Name", 135, "w"), ("Type", 112, "w"),
                                       ("Seats", 52, "center"), ("Live status", 140, "w")], height=14)
        self.table.pack(fill="both", expand=True)
        self.table.on_select(self.on_select)

        form_card = Card(columns, "Resource details")
        form_card.grid(row=0, column=1, sticky="new")
        form = form_card.body
        form.columnconfigure(1, weight=1)
        self.vars = {"code": tk.StringVar(), "name": tk.StringVar(), "type": tk.StringVar(value=config.RESOURCE_TYPES[0]),
                     "capacity": tk.StringVar(value="1"), "status": tk.StringVar(value=config.RESOURCE_STATUS_ACTIVE)}

        def row(index, label):
            ttk.Label(form, text=label, style="Card.TLabel").grid(row=index, column=0, sticky="w", pady=5)

        row(0, "Resource ID")
        self.code_entry = ttk.Entry(form, textvariable=self.vars["code"])
        self.code_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ttk.Label(form, text=f"Unique, e.g. {self.campus.code}-LAB-03", style="CardMuted.TLabel").grid(
            row=1, column=1, sticky="w", padx=(10, 0))
        row(2, "Name")
        ttk.Entry(form, textvariable=self.vars["name"]).grid(row=2, column=1, sticky="ew", padx=(10, 0))
        row(3, "Type")
        ttk.Combobox(form, textvariable=self.vars["type"], values=config.RESOURCE_TYPES,
                     state="readonly").grid(row=3, column=1, sticky="ew", padx=(10, 0))
        row(4, "Seats / capacity")
        ttk.Spinbox(form, textvariable=self.vars["capacity"], from_=1, to=1000, width=8).grid(
            row=4, column=1, sticky="w", padx=(10, 0))
        row(5, "Status")
        ttk.Combobox(form, textvariable=self.vars["status"], values=config.EDITABLE_RESOURCE_STATUSES,
                     state="readonly").grid(row=5, column=1, sticky="ew", padx=(10, 0))

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Add new", style="Primary.TButton", command=self.add).pack(side="left")
        ttk.Button(buttons, text="Update selected", command=self.update).pack(side="left", padx=6)
        ttk.Button(buttons, text="Remove", style="Danger.TButton", command=self.remove).pack(side="left")
        ttk.Button(form, text="Clear form", command=self.clear_form).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.note = ttk.Label(form, text="", style="CardMuted.TLabel", wraplength=300)
        self.note.grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def refresh(self):
        resources = self.app.resources.list_for_campus(self.campus.campus_id)
        status = self.app.bookings.availability(self.campus.campus_id)
        self.resource_map = {r.resource_id: r for r in resources}
        rows = [(r.resource_id, (r.code, r.name, r.resource_type, r.capacity, status[r.resource_id][0]),
                 status[r.resource_id][1]) for r in resources]
        self.table.set_rows(rows)

    def on_select(self):
        rid = self.table.selected_id()
        resource = self.resource_map.get(int(rid)) if rid else None
        if resource is None:
            return
        self.editing = resource.resource_id
        self.vars["code"].set(resource.code)
        self.vars["name"].set(resource.name)
        self.vars["type"].set(resource.resource_type)
        self.vars["capacity"].set(str(resource.capacity))
        self.vars["status"].set(resource.status)
        self.code_entry.state(["readonly"])          # the ID of an existing resource cannot change
        self.note.configure(text="Editing an existing resource. Its ID cannot be changed.")

    def clear_form(self):
        self.editing = None
        self.vars["code"].set("")
        self.vars["name"].set("")
        self.vars["type"].set(config.RESOURCE_TYPES[0])
        self.vars["capacity"].set("1")
        self.vars["status"].set(config.RESOURCE_STATUS_ACTIVE)
        self.code_entry.state(["!readonly"])
        self.table.tree.selection_remove(self.table.tree.selection())
        self.note.configure(text="")

    @safe
    def add(self):
        if self.editing is not None:
            raise ResourceError("A resource is selected. Click 'Clear form' first to add a new one.")
        v = self.vars
        resource = self.app.resources.add_resource(self.app.user, self.campus.campus_id, v["code"].get(),
                                                   v["name"].get(), v["type"].get(), v["capacity"].get())
        messagebox.showinfo("Resource added", f"{resource.name} ({resource.code}) was registered.")
        self.clear_form()
        self.refresh()

    @safe
    def update(self):
        if self.editing is None:
            raise ResourceError("Please select a resource in the table first.")
        v = self.vars
        self.app.resources.update_resource(self.app.user, self.editing, v["name"].get(), v["type"].get(),
                                           v["capacity"].get(), v["status"].get())
        messagebox.showinfo("Resource updated", "The changes were saved.")
        self.refresh()

    @safe
    def remove(self):
        if self.editing is None:
            raise ResourceError("Please select a resource in the table first.")
        name = self.vars["name"].get()
        if not messagebox.askyesno("Remove resource", f"Remove '{name}' from this campus?"):
            return
        self.app.resources.remove_resource(self.app.user, self.editing)
        messagebox.showinfo("Resource removed", f"{name} was removed. Its past bookings are kept for reports.")
        self.clear_form()
        self.refresh()


# =============================================================================
class CampusBookingsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.campus = app.campus
        ttk.Label(self, text="Campus bookings", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text=f"Every booking made at {self.campus.name}.").pack(anchor="w", pady=(0, 10))

        card = Card(self)
        card.pack(fill="both", expand=True)
        bar = ttk.Frame(card.body, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Show:", style="Card.TLabel").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        box = ttk.Combobox(bar, textvariable=self.filter_var, state="readonly", width=14,
                           values=["All", "Upcoming", "In progress", "Completed", "Cancelled"])
        box.pack(side="left", padx=8)
        box.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.count_label = ttk.Label(bar, text="", style="CardMuted.TLabel")
        self.count_label.pack(side="right")

        self.table = Table(card.body, [("Ref", 50, "center"), ("Resource", 160, "w"), ("Lecturer", 140, "w"),
                                       ("Date", 135, "w"), ("Time", 110, "center"), ("Duration", 70, "center"),
                                       ("Purpose", 170, "w"), ("Status", 90, "center")], height=14)
        self.table.pack(fill="both", expand=True)
        ttk.Button(card.body, text="Cancel selected upcoming booking", style="Danger.TButton",
                   command=self.cancel).pack(anchor="e", pady=(10, 0))

    def refresh(self):
        wanted = self.filter_var.get()
        bookings = self.app.bookings.for_campus(self.campus.campus_id)
        bookings.reverse()                                  # newest first
        if wanted != "All":
            bookings = [b for b in bookings if b.status() == wanted]
        rows = []
        for b in bookings:
            status = b.status()
            rows.append((b.booking_id, (b.booking_id, b.resource_name, b.lecturer_name,
                                        pretty_date(b.booking_date), f"{b.start_text} - {b.end_text}",
                                        format_duration(b.duration_minutes), b.purpose, status),
                         STATUS_TAGS[status]))
        self.table.set_rows(rows)
        self.count_label.configure(text=f"{len(bookings)} booking(s)")

    @safe
    def cancel(self):
        booking_id = self.table.selected_id()
        if booking_id is None:
            raise BookingError("Please select a booking in the table first.")
        if not messagebox.askyesno("Cancel booking", "Cancel this booking on behalf of the lecturer?"):
            return
        self.app.bookings.cancel_booking(self.app.user, int(booking_id))
        self.refresh()


# =============================================================================
class UsagePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        ttk.Label(self, text="Usage & trends", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text=f"Campus report for {app.campus.name}.").pack(anchor="w", pady=(0, 10))
        self.panel = ReportPanel(self, app)
        self.panel.pack(fill="both", expand=True)

    def refresh(self):
        self.panel.refresh()
