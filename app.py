"""
app.py
------
The main window. It owns the services, remembers who is logged in and which
campus is active, and swaps screens in and out:

    LoginView  ->  CampusView  ->  Lecturer / Admin / Operator dashboard
"""
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.admin_view import AdminDashboard
from gui.campus_view import CampusView
from gui.lecturer_view import LecturerDashboard
from gui.login_view import LoginView
from gui.operator_view import OperatorDashboard
from services.auth_service import AuthService
from services.booking_service import BookingService
from services.campus_service import CampusService
from services.report_service import ReportService
from services.resource_service import ResourceService

# Dictionary: role name -> dashboard screen to open
DASHBOARDS = {
    config.ROLE_LECTURER: LecturerDashboard,
    config.ROLE_ADMIN: AdminDashboard,
    config.ROLE_OPERATOR: OperatorDashboard,
}


class Header(ttk.Frame):
    """Top bar: shows the active campus and the booking policy that applies."""

    def __init__(self, parent, app):
        super().__init__(parent, style="Header.TFrame", padding=(16, 10))
        self.app = app

        left = ttk.Frame(self, style="Header.TFrame")
        left.pack(side="left")
        ttk.Label(left, text=config.APP_TITLE, style="HeaderBig.TLabel").pack(anchor="w")
        self.campus_label = ttk.Label(left, style="Header.TLabel", font=theme.FONT_BOLD)
        self.campus_label.pack(anchor="w")
        self.policy_label = ttk.Label(left, style="HeaderSmall.TLabel")
        self.policy_label.pack(anchor="w")

        right = ttk.Frame(self, style="Header.TFrame")
        right.pack(side="right")
        self.user_label = ttk.Label(right, style="Header.TLabel")
        self.user_label.pack(side="left", padx=(0, 14))
        self.switch_button = ttk.Button(right, text="Change campus", style="Header.TButton",
                                        command=app.show_campus_select)
        self.switch_button.pack(side="left", padx=4)
        ttk.Button(right, text="Log out", style="Header.TButton",
                   command=app.show_login).pack(side="left", padx=4)

    def refresh(self):
        user, campus = self.app.user, self.app.campus
        self.user_label.configure(text=f"{user.full_name}  |  {user.role}")
        self.campus_label.configure(text=f"Active campus: {campus.display_name}")
        self.policy_label.configure(text=f"Booking policy in effect - {campus.policy.summary()}")
        # an administrator only has one campus, so there is nothing to switch to
        if len(self.app.campuses.accessible_to(user)) > 1:
            self.switch_button.state(["!disabled"])
        else:
            self.switch_button.state(["disabled"])


class App(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title(config.APP_TITLE)
        self.geometry("1240x780")
        self.minsize(1100, 700)
        theme.apply_theme(self)

        # services (the "business logic" layer)
        self.auth = AuthService(db)
        self.campuses = CampusService(db)
        self.resources = ResourceService(db)
        self.bookings = BookingService(db, self.resources)
        self.reports = ReportService(db, self.campuses)

        self.user = None        # logged-in User object
        self.campus = None      # active Campus object

        self.header = Header(self, self)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)
        self.current_view = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_login()

    # ---------------------------------------------------------- navigation
    def _show(self, view):
        if self.current_view is not None:
            self.current_view.destroy()
        self.current_view = view
        view.pack(fill="both", expand=True)

    def show_login(self):
        self.user = None
        self.campus = None
        self.header.pack_forget()
        self._show(LoginView(self.body, self))

    def on_login(self, user):
        self.user = user
        self.show_campus_select()

    def show_campus_select(self):
        self.header.pack_forget()
        self._show(CampusView(self.body, self))

    def enter_campus(self, campus):
        self.campus = campus
        self.header.refresh()
        self.header.pack(fill="x", before=self.body)
        self._show(DASHBOARDS[self.user.role](self.body, self))

    def on_close(self):
        self.db.close()
        self.destroy()
