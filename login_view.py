"""
login_view.py
-------------
Login and lecturer registration screen.
"""
import tkinter as tk
from tkinter import messagebox, ttk

import config
from gui import theme
from gui.widgets import safe


class LoginView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # ---- left: sky blue welcome panel -------------------------------------
        hero = ttk.Frame(self, style="Hero.TFrame", padding=40, width=430)
        hero.pack(side="left", fill="y")
        hero.pack_propagate(False)
        ttk.Label(hero, text=config.INSTITUTION, style="Hero.TLabel",
                  font=theme.FONT_HEADING).pack(anchor="w", pady=(60, 4))
        ttk.Label(hero, text="Smart Campus\nResource Booking", style="HeroTitle.TLabel",
                  justify="left").pack(anchor="w")
        ttk.Label(hero, style="Hero.TLabel", justify="left", wraplength=340,
                  text="\nBook computer labs, projectors, seminar rooms and presentation "
                       "equipment on any campus - without double bookings.").pack(anchor="w")
        for point in ("Live resource availability", "Campus-specific booking rules",
                      "Reports and campus comparisons"):
            ttk.Label(hero, text="✓  " + point, style="Hero.TLabel",
                      font=theme.FONT_BOLD).pack(anchor="w", pady=(10, 0))

        # ---- right: the forms ----------------------------------------------------
        area = ttk.Frame(self)
        area.pack(side="left", fill="both", expand=True)
        holder = ttk.Frame(area)
        holder.place(relx=0.5, rely=0.5, anchor="center")

        self.login_card = self._build_login(holder)
        self.register_card = self._build_register(holder)
        self.login_card.pack()

        hint = ("Demo logins\n"
                "Lecturer: thandi.nkosi / Lecturer@123\n"
                "Campus admin: admin_dbn / Admin@123\n"
                "System operator: operator / Operator@123")
        ttk.Label(holder, text=hint, style="Muted.TLabel", justify="left").pack(pady=(14, 0))

    # ---------------------------------------------------------------- login
    def _build_login(self, parent):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=30)
        ttk.Label(card, text="Welcome back", style="Heading.TLabel",
                  font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(card, text="Log in with your username and password.",
                  style="CardMuted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.login_user = tk.StringVar()
        self.login_pass = tk.StringVar()
        ttk.Label(card, text="Username", style="Card.TLabel").grid(row=2, column=0, sticky="w")
        user_entry = ttk.Entry(card, textvariable=self.login_user, width=34)
        user_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 10))
        ttk.Label(card, text="Password", style="Card.TLabel").grid(row=4, column=0, sticky="w")
        self.login_pass_entry = ttk.Entry(card, textvariable=self.login_pass, show="*", width=34)
        self.login_pass_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(2, 6))

        self.show_pass = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Show password", variable=self.show_pass,
                        command=self._toggle_password).grid(row=6, column=0, sticky="w")

        ttk.Button(card, text="Log in", style="Primary.TButton",
                   command=self.do_login).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(16, 8))
        ttk.Label(card, text="New lecturer?", style="CardMuted.TLabel").grid(row=8, column=0, sticky="e")
        ttk.Button(card, text="Create an account", style="Link.TButton",
                   command=self.show_register).grid(row=8, column=1, sticky="w")

        card.bind_all("<Return>", lambda event: self._enter_pressed())
        user_entry.focus_set()
        return card

    def _toggle_password(self):
        self.login_pass_entry.configure(show="" if self.show_pass.get() else "*")

    def _enter_pressed(self):
        # Enter submits whichever form is showing
        if self.login_card.winfo_ismapped():
            self.do_login()
        elif self.register_card.winfo_ismapped():
            self.do_register()

    @safe
    def do_login(self):
        user = self.app.auth.login(self.login_user.get(), self.login_pass.get())
        self.login_pass.set("")
        self.unbind_all("<Return>")
        self.app.on_login(user)

    # ------------------------------------------------------------- register
    def _build_register(self, parent):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=30)
        ttk.Label(card, text="Create a lecturer account", style="Heading.TLabel",
                  font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(card, text="Campus administrators and system operators are\n"
                             "set up by the institution.", style="CardMuted.TLabel",
                  justify="left").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.reg_vars = {name: tk.StringVar() for name in ("name", "user", "pass", "confirm")}
        fields = [("Full name", "name", ""), ("Username", "user", ""),
                  ("Password (6+ characters, letters and numbers)", "pass", "*"),
                  ("Confirm password", "confirm", "*")]
        row = 2
        for label, key, mask in fields:
            ttk.Label(card, text=label, style="Card.TLabel").grid(row=row, column=0, columnspan=2, sticky="w")
            ttk.Entry(card, textvariable=self.reg_vars[key], show=mask, width=34).grid(
                row=row + 1, column=0, columnspan=2, sticky="ew", pady=(2, 8))
            row += 2

        ttk.Button(card, text="Register", style="Primary.TButton",
                   command=self.do_register).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 8))
        ttk.Label(card, text="Already registered?", style="CardMuted.TLabel").grid(row=row + 1, column=0, sticky="e")
        ttk.Button(card, text="Back to login", style="Link.TButton",
                   command=self.show_login_form).grid(row=row + 1, column=1, sticky="w")
        return card

    def show_register(self):
        self.login_card.pack_forget()
        self.register_card.pack()

    def show_login_form(self):
        self.register_card.pack_forget()
        self.login_card.pack()

    @safe
    def do_register(self):
        values = {key: var.get() for key, var in self.reg_vars.items()}
        self.app.auth.register_lecturer(values["name"], values["user"], values["pass"], values["confirm"])
        messagebox.showinfo("Account created", "Your lecturer account is ready. You can log in now.")
        self.login_user.set(values["user"].strip())
        for var in self.reg_vars.values():
            var.set("")
        self.show_login_form()
