"""
report_panel.py
---------------
Campus-level report (requirement 7.1): total bookings, most used resources,
average booking duration, plus charts for usage trends.
Used by the administrator ("Usage & trends") and the operator ("Campus report").
"""
from tkinter import ttk

from gui.widgets import BarChart, Card, StatCard, Table
from utils.timeutils import WEEKDAY_NAMES, format_duration


class ReportPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.campus_id = app.campus.campus_id

        # row 0: headline numbers
        stats = ttk.Frame(self)
        stats.pack(fill="x")
        self.cards = {}
        for index, (key, caption) in enumerate([("total", "Total bookings"),
                                                ("avg", "Average booking duration"),
                                                ("hours", "Total hours booked"),
                                                ("util", "Utilisation (last 30 days)"),
                                                ("cancelled", "Cancelled bookings")]):
            stats.columnconfigure(index, weight=1, uniform="stat")
            self.cards[key] = StatCard(stats, caption)
            self.cards[key].grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))

        # row 1: top resources + usage chart
        middle = ttk.Frame(self)
        middle.pack(fill="x", pady=(12, 0))
        middle.columnconfigure(0, weight=2, uniform="m")
        middle.columnconfigure(1, weight=3, uniform="m")
        card = Card(middle, "Most frequently used resources")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.top_table = Table(card.body, [("#", 30, "center"), ("Resource", 170, "w"),
                                           ("Bookings", 80, "center"), ("Hours", 60, "center")], height=5)
        self.top_table.pack(fill="x")
        self.usage_chart = BarChart(middle, height=205)
        self.usage_chart.grid(row=0, column=1, sticky="nsew")

        # row 2: trends
        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True, pady=(12, 0))
        bottom.columnconfigure(0, weight=1, uniform="b")
        bottom.columnconfigure(1, weight=1, uniform="b")
        bottom.rowconfigure(0, weight=1)
        self.weekday_chart = BarChart(bottom, height=170)
        self.weekday_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.weekly_chart = BarChart(bottom, height=170)
        self.weekly_chart.grid(row=0, column=1, sticky="nsew")

    def show_campus(self, campus_id):
        self.campus_id = campus_id
        self.refresh()

    def refresh(self):
        report = self.app.reports.campus_report(self.campus_id)

        self.cards["total"].set(str(report["total"]))
        self.cards["avg"].set(format_duration(report["avg_minutes"]) if report["total"] else "-")
        self.cards["hours"].set(f"{report['total_hours']:.0f} h")
        self.cards["util"].set(f"{report['utilisation']:.0f}%")
        self.cards["cancelled"].set(str(report["cancelled"]))

        rows = []
        for rank, item in enumerate(report["top_resources"], start=1):
            rows.append((rank, (rank, item["name"], item["bookings"], f"{item['minutes'] / 60:.1f}"), None))
        self.top_table.set_rows(rows)

        everything = report["all_resources"]
        self.usage_chart.set_data("Bookings per resource",
                                  [r["code"].split("-", 1)[-1] for r in everything],
                                  [r["bookings"] for r in everything], lambda v: f"{v:.0f}")
        self.weekday_chart.set_data("Bookings by day of the week", WEEKDAY_NAMES,
                                    report["by_weekday"], lambda v: f"{v:.0f}")
        weeks = report["weekly_trend"]
        self.weekly_chart.set_data("Bookings per week (last 6 weeks, week starting)",
                                   [w[0] for w in weeks], [w[1] for w in weeks], lambda v: f"{v:.0f}")
