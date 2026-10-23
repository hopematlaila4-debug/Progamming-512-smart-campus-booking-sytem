"""
dashboard.py
------------
Base screen for all three roles: a sky-blue sidebar with navigation buttons
on the left and the selected page on the right. The role screens only have
to call add_page() for the pages they need.
"""
from tkinter import ttk

from gui import theme


class Dashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pages = {}         # page key -> page frame
        self.buttons = {}       # page key -> sidebar button
        self.current = None

        side = ttk.Frame(self, style="Side.TFrame", width=215)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        ttk.Label(side, text=app.user.full_name, style="Side.TLabel", font=theme.FONT_BOLD,
                  wraplength=185).pack(anchor="w", padx=16, pady=(20, 0))
        ttk.Label(side, text=app.user.role, style="Side.TLabel",
                  font=theme.FONT_SMALL).pack(anchor="w", padx=16, pady=(0, 18))
        self.side = side

        self.content = ttk.Frame(self, padding=(20, 16))
        self.content.pack(side="left", fill="both", expand=True)

    def add_page(self, key, label, page_class):
        """Create a page and add a button for it in the sidebar."""
        self.pages[key] = page_class(self.content, self.app)
        button = ttk.Button(self.side, text=label, style="Nav.TButton",
                            command=lambda: self.show_page(key))
        button.pack(fill="x")
        self.buttons[key] = button

    def show_page(self, key):
        if self.current is not None:
            self.pages[self.current].pack_forget()
            self.buttons[self.current].configure(style="Nav.TButton")
        self.current = key
        self.buttons[key].configure(style="NavActive.TButton")
        page = self.pages[key]
        page.pack(fill="both", expand=True)
        page.refresh()          # every page reloads its data when it is opened
