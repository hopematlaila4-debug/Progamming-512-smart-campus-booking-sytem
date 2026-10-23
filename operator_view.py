"""
operator_view.py
----------------
System operator screens (system-wide, read mostly):
    All bookings        - bookings from every campus, with filters
    All resources       - resources from every campus
    Campus report       - the campus-level report for any campus
    Compare campuses    - cross-campus comparison, insights, CSV export
    Campuses            - list campuses and add a new one
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gui import theme
from gui.dashboard import Dashboard
from gui.report_panel import ReportPanel
from gui.widgets import STATUS_TAGS, BarChart, Card, Table, pretty_date, safe
from utils.timeutils import format_duration

ALL_CAMPUSES = "All campuses"


class OperatorDashboard(Dashboard):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.add_page("compare", "Compare campuses", ComparePage)
        self.add_page("report", "Campus report", CampusReportPage)
        self.add_page("bookings", "All bookings", AllBookingsPage)
        self.add_page("resources", "All resources", AllResourcesPage)
        self.add_page("campuses", "Campuses", CampusesPage)
        self.show_page("compare")


def campus_choices(app):
    return [c.name for c in app.campuses.all()]


# =============================================================================
class AllBookingsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="All bookings", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text="Booking data from every campus.").pack(anchor="w", pady=(0, 10))
        card = Card(self)
        card.pack(fill="both", expand=True)

        bar = ttk.Frame(card.body, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 8))
        self.campus_var = tk.StringVar(value=ALL_CAMPUSES)
        self.status_var = tk.StringVar(value="All")
        ttk.Label(bar, text="Campus:", style="Card.TLabel").pack(side="left")
        self.campus_box = ttk.Combobox(bar, textvariable=self.campus_var, state="readonly", width=18)
        self.campus_box.pack(side="left", padx=(6, 14))
        ttk.Label(bar, text="Status:", style="Card.TLabel").pack(side="left")
        status_box = ttk.Combobox(bar, textvariable=self.status_var, state="readonly", width=14,
                                  values=["All", "Upcoming", "In progress", "Completed", "Cancelled"])
        status_box.pack(side="left", padx=6)
        self.count_label = ttk.Label(bar, text="", style="CardMuted.TLabel")
        self.count_label.pack(side="right")
        for box in (self.campus_box, status_box):
            box.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        self.table = Table(card.body, [("Ref", 50, "center"), ("Campus", 110, "w"), ("Resource", 160, "w"),
                                       ("Lecturer", 140, "w"), ("Date", 135, "w"), ("Time", 110, "center"),
                                       ("Duration", 70, "center"), ("Status", 90, "center")], height=15)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.campus_box.configure(values=[ALL_CAMPUSES] + campus_choices(self.app))
        campus, status = self.campus_var.get(), self.status_var.get()
        bookings = self.app.bookings.all_bookings()
        bookings.reverse()
        rows = []
        for b in bookings:
            state = b.status()
            if campus != ALL_CAMPUSES and b.campus_name != campus:
                continue
            if status != "All" and state != status:
                continue
            rows.append((b.booking_id, (b.booking_id, b.campus_name, b.resource_name, b.lecturer_name,
                                        pretty_date(b.booking_date), f"{b.start_text} - {b.end_text}",
                                        format_duration(b.duration_minutes), state), STATUS_TAGS[state]))
        self.table.set_rows(rows)
        self.count_label.configure(text=f"{len(rows)} booking(s)")


# =============================================================================
class AllResourcesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="All resources", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text="Resources registered on every campus.").pack(anchor="w", pady=(0, 10))
        card = Card(self)
        card.pack(fill="both", expand=True)
        bar = ttk.Frame(card.body, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 8))
        self.campus_var = tk.StringVar(value=ALL_CAMPUSES)
        ttk.Label(bar, text="Campus:", style="Card.TLabel").pack(side="left")
        self.campus_box = ttk.Combobox(bar, textvariable=self.campus_var, state="readonly", width=18)
        self.campus_box.pack(side="left", padx=6)
        self.campus_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.count_label = ttk.Label(bar, text="", style="CardMuted.TLabel")
        self.count_label.pack(side="right")

        self.table = Table(card.body, [("Campus", 120, "w"), ("Resource ID", 110, "w"), ("Name", 190, "w"),
                                       ("Type", 160, "w"), ("Seats", 60, "center"), ("Status", 110, "center")],
                           height=15)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.campus_box.configure(values=[ALL_CAMPUSES] + campus_choices(self.app))
        wanted = self.campus_var.get()
        rows = []
        for campus_name, r in self.app.resources.list_all():
            if wanted != ALL_CAMPUSES and campus_name != wanted:
                continue
            tag = "bad" if r.status != "Active" else None
            rows.append((r.resource_id, (campus_name, r.code, r.name, r.resource_type, r.capacity, r.status), tag))
        self.table.set_rows(rows)
        self.count_label.configure(text=f"{len(rows)} resource(s)")


# =============================================================================
class CampusReportPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Campus report", style="PageTitle.TLabel").pack(anchor="w")
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Label(bar, text="Campus:").pack(side="left")
        self.campus_var = tk.StringVar(value=app.campus.name)
        self.campus_box = ttk.Combobox(bar, textvariable=self.campus_var, state="readonly", width=20)
        self.campus_box.pack(side="left", padx=8)
        self.campus_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.panel = ReportPanel(self, app)
        self.panel.pack(fill="both", expand=True)

    def refresh(self):
        self.campus_box.configure(values=campus_choices(self.app))
        for campus in self.app.campuses.all():
            if campus.name == self.campus_var.get():
                self.panel.show_campus(campus.campus_id)


# =============================================================================
class ComparePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Compare campuses", style="PageTitle.TLabel").pack(side="left")
        ttk.Button(top, text="Export to CSV", command=self.export).pack(side="right")
        ttk.Label(self, style="Muted.TLabel",
                  text="Resource usage, booking trends and the effect of each campus's booking rules."
                  ).pack(anchor="w", pady=(0, 8))

        card = Card(self)
        card.pack(fill="x")
        self.table = Table(card.body, [("Campus", 115, "w"), ("Max session", 100, "center"),
                                       ("Hours", 105, "center"), ("Days", 75, "center"),
                                       ("Resources", 90, "center"), ("Bookings", 85, "center"),
                                       ("Cancelled", 90, "center"), ("Avg length", 95, "center"),
                                       ("Utilised", 80, "center"), ("Weekend", 85, "center")], height=5)
        self.table.pack(fill="x")

        charts = ttk.Frame(self)
        charts.pack(fill="x", pady=10)
        self.charts = []
        for index in range(3):
            charts.columnconfigure(index, weight=1, uniform="c")
            chart = BarChart(charts, height=165)
            chart.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 10, 0))
            self.charts.append(chart)

        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True)
        bottom.columnconfigure(0, weight=3, uniform="b")
        bottom.columnconfigure(1, weight=2, uniform="b")
        bottom.rowconfigure(0, weight=1)
        self.type_card = Card(bottom, "Usage by resource type (bookings)")
        self.type_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.type_table = None
        self.insight_card = Card(bottom, "What the differences show")
        self.insight_card.grid(row=0, column=1, sticky="nsew")
        self.insight_label = ttk.Label(self.insight_card.body, text="", style="Card.TLabel",
                                       wraplength=400, justify="left", font=theme.FONT_SMALL)
        self.insight_label.pack(anchor="nw", fill="x")
        # let the text wrap to whatever width the card currently has
        self.insight_card.body.bind("<Configure>",
                                    lambda e: self.insight_label.configure(wraplength=max(200, e.width - 10)))

    def refresh(self):
        rows = self.app.reports.comparison()
        self.table.set_rows([
            (i, (r["campus"], format_duration(r["max_session"]), r["hours"], r["days"], r["resources"],
                 r["bookings"], r["cancelled"], format_duration(r["avg_minutes"]) if r["bookings"] else "-",
                 f"{r['utilisation']:.0f}%", f"{r['weekend_pct']:.0f}%"), None)
            for i, r in enumerate(rows)])

        names = [r["campus"] for r in rows]
        self.charts[0].set_data("Total bookings", names, [r["bookings"] for r in rows], lambda v: f"{v:.0f}")
        self.charts[1].set_data("Average duration (minutes)", names,
                                [r["avg_minutes"] for r in rows], lambda v: f"{v:.0f}")
        self.charts[2].set_data("Utilisation, last 30 days (%)", names,
                                [r["utilisation"] for r in rows], lambda v: f"{v:.0f}%")

        # The type table has one column per campus, so it is rebuilt each time
        if self.type_table is not None:
            self.type_table.destroy()
        matrix = self.app.reports.usage_by_type(rows)
        columns = [("Resource type", 170, "w")] + [(n, 100, "center") for n in names]
        self.type_table = Table(self.type_card.body, columns, height=4)
        self.type_table.pack(fill="both", expand=True)
        self.type_table.set_rows([(i, (rtype,) + tuple(matrix[rtype][n] for n in names), None)
                                  for i, rtype in enumerate(matrix)])

        notes = self.app.reports.insights(rows)
        self.insight_label.configure(text="\n".join("• " + n for n in notes))

    @safe
    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="campus_comparison.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if path:
            self.app.reports.export_comparison_csv(path)
            messagebox.showinfo("Exported", f"Comparison saved to:\n{path}")


# =============================================================================
class CampusesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Campuses", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(self, style="Muted.TLabel",
                  text="Each campus is linked to a booking policy class. A new campus only needs a "
                       "code, a name and a policy.").pack(anchor="w", pady=(0, 10))

        columns = ttk.Frame(self)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=3, uniform="cols")
        columns.columnconfigure(1, weight=2, uniform="cols")
        columns.rowconfigure(0, weight=1)

        card = Card(columns, "Campuses and their booking policies")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.table = Table(card.body, [("Code", 60, "center"), ("Campus", 130, "w"), ("City", 110, "w"),
                                       ("Policy", 190, "w")], height=10)
        self.table.pack(fill="both", expand=True)
        self.table.on_select(self.show_rules)
        self.rules_label = ttk.Label(card.body, text="Select a campus to read its rules.",
                                     style="Card.TLabel", wraplength=480, justify="left")
        self.rules_label.pack(anchor="w", pady=(10, 0))

        form_card = Card(columns, "Add a campus")
        form_card.grid(row=0, column=1, sticky="new")
        form = form_card.body
        form.columnconfigure(1, weight=1)
        self.vars = {key: tk.StringVar() for key in ("code", "name", "city", "policy")}
        keys = self.app.campuses.policy_keys()
        if keys:
            self.vars["policy"].set(keys[0])
        for index, (label, key) in enumerate([("Campus code", "code"), ("Campus name", "name"), ("City", "city")]):
            ttk.Label(form, text=label, style="Card.TLabel").grid(row=index, column=0, sticky="w", pady=5)
            ttk.Entry(form, textvariable=self.vars[key]).grid(row=index, column=1, sticky="ew", padx=(10, 0))
        ttk.Label(form, text="Booking policy", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Combobox(form, textvariable=self.vars["policy"], values=keys, state="readonly").grid(
            row=3, column=1, sticky="ew", padx=(10, 0))
        ttk.Button(form, text="Add campus", style="Primary.TButton", command=self.add).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))

    def refresh(self):
        self.table.set_rows([(c.campus_id, (c.code, c.name, c.city, c.policy.name), None)
                             for c in self.app.campuses.all()])

    def show_rules(self):
        cid = self.table.selected_id()
        campus = self.app.campuses.get(int(cid)) if cid else None
        if campus:
            self.rules_label.configure(text=campus.policy.name + ":  " + "  |  ".join(campus.policy.describe()))

    @safe
    def add(self):
        v = self.vars
        self.app.campuses.add_campus(self.app.user, v["code"].get(), v["name"].get(),
                                     v["city"].get(), v["policy"].get())
        messagebox.showinfo("Campus added", "The campus is ready and will appear on the campus selection screen.")
        for key in ("code", "name", "city"):
            v[key].set("")
        self.refresh()
