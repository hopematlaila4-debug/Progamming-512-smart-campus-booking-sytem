"""
campus_view.py
--------------
Shown straight after login: the user picks the campus to work on.
Each card lists that campus's booking rules.
"""
from tkinter import ttk

from gui import theme

COLUMNS = 4     # campus cards per row


class CampusView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=30)
        self.app = app
        user = app.user

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Select a campus", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Log out", command=app.show_login).pack(side="right")
        ttk.Label(self, style="Muted.TLabel",
                  text=f"Welcome, {user.full_name} ({user.role}). The booking rules shown on each "
                       "card are applied automatically for the campus you choose.").pack(anchor="w", pady=(2, 20))

        grid = ttk.Frame(self)
        grid.pack(fill="both", expand=True)
        campuses = app.campuses.accessible_to(user)
        for index, campus in enumerate(campuses):
            grid.columnconfigure(index % COLUMNS, weight=1, uniform="card")
            self._card(grid, campus).grid(row=index // COLUMNS, column=index % COLUMNS,
                                          padx=8, pady=8, sticky="nsew")

    def _card(self, parent, campus):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        ttk.Label(card, text=campus.name, style="Heading.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(card, text=f"{campus.city}  |  code {campus.code}", style="CardMuted.TLabel").pack(anchor="w")
        ttk.Label(card, text=campus.policy.name, style="Card.TLabel", font=theme.FONT_BOLD,
                  foreground=theme.SKY_DEEP).pack(anchor="w", pady=(12, 4))
        for line in campus.policy.describe():
            ttk.Label(card, text="• " + line, style="Card.TLabel", font=theme.FONT_SMALL,
                      wraplength=210, justify="left").pack(anchor="w", pady=1)
        ttk.Button(card, text="Work on this campus", style="Primary.TButton",
                   command=lambda: self.app.enter_campus(campus)).pack(fill="x", pady=(16, 0), side="bottom")
        return card
