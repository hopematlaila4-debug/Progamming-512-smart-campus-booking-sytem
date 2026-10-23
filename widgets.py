"""
widgets.py
----------
Small reusable GUI pieces shared by all screens:
    Table      - a Treeview with a scrollbar and striped rows
    Card       - a white panel with a heading
    StatCard   - a big number with a caption
    BarChart   - a simple bar chart drawn on a Canvas (no extra libraries needed)
    safe       - decorator that turns errors into friendly message boxes
"""
import functools
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from gui import theme
from utils.errors import AppError


def safe(method):
    """
    Wrap a button handler so any expected error becomes a message box instead
    of a crash (requirement: input validation and error handling).
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except AppError as error:
            messagebox.showwarning("Please check", str(error))
        except sqlite3.Error as error:
            messagebox.showerror("Database error",
                                 f"Something went wrong with the database.\n\n{error}")
    return wrapper


class Card(ttk.Frame):
    """White panel with an optional heading. Put your widgets in card.body."""

    def __init__(self, parent, title=None, **kwargs):
        super().__init__(parent, style="Panel.TFrame", padding=12, **kwargs)
        if title:
            ttk.Label(self, text=title, style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        self.body = ttk.Frame(self, style="Card.TFrame")
        self.body.pack(fill="both", expand=True)


class StatCard(ttk.Frame):
    """A big number with a small caption underneath."""

    def __init__(self, parent, caption):
        super().__init__(parent, style="Panel.TFrame", padding=(14, 10))
        self.value = ttk.Label(self, text="-", style="Stat.TLabel")
        self.value.pack(anchor="w")
        ttk.Label(self, text=caption, style="CardMuted.TLabel").pack(anchor="w")

    def set(self, text):
        self.value.configure(text=text)


class Table(ttk.Frame):
    """
    Treeview with scrollbar. Rows are added with set_rows():
        table.set_rows([(row_id, (value1, value2, ...), tag), ...])
    The row_id comes back from selected_id().
    """

    def __init__(self, parent, columns, height=8, **kwargs):
        """columns = [(heading, width, anchor), ...]"""
        super().__init__(parent, style="Card.TFrame", **kwargs)
        names = [f"c{i}" for i in range(len(columns))]
        self.tree = ttk.Treeview(self, columns=names, show="headings", height=height,
                                 selectmode="browse")
        for name, (heading, width, anchor) in zip(names, columns):
            self.tree.heading(name, text=heading, anchor=anchor)
            self.tree.column(name, width=width, anchor=anchor, stretch=True)
        self.height = height
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)

        # row colours
        self.tree.tag_configure("odd", background=theme.SKY_PALE)
        self.tree.tag_configure("even", background=theme.WHITE)
        self.tree.tag_configure("free", foreground=theme.GREEN)
        self.tree.tag_configure("busy", foreground=theme.ORANGE)
        self.tree.tag_configure("bad", foreground=theme.RED)
        self.tree.tag_configure("done", foreground=theme.GREY)

    def set_rows(self, rows):
        selected = self.selected_id()
        self.tree.delete(*self.tree.get_children())
        for index, (row_id, values, tag) in enumerate(rows):
            tags = ("odd" if index % 2 else "even",) + ((tag,) if tag else ())
            self.tree.insert("", "end", iid=str(row_id), values=values, tags=tags)
        # only show the scrollbar when there are more rows than fit
        if len(rows) > self.height:
            self.scroll.pack(side="right", fill="y")
        else:
            self.scroll.pack_forget()
        if selected is not None and self.tree.exists(selected):
            self.tree.selection_set(selected)

    def selected_id(self):
        chosen = self.tree.selection()
        return chosen[0] if chosen else None

    def selected_values(self):
        chosen = self.tree.selection()
        return self.tree.item(chosen[0], "values") if chosen else None

    def on_select(self, callback):
        self.tree.bind("<<TreeviewSelect>>", lambda event: callback())


class BarChart(tk.Canvas):
    """A small bar chart. Call set_data() and it redraws itself whenever resized."""

    def __init__(self, parent, height=200, color=theme.SKY_DARK):
        super().__init__(parent, height=height, bg=theme.WHITE, highlightthickness=1,
                         highlightbackground=theme.SKY_MID)
        self.color = color
        self.title = ""
        self.labels = []
        self.values = []
        self.fmt = lambda value: f"{value:g}"
        self.bind("<Configure>", lambda event: self.redraw())

    def set_data(self, title, labels, values, fmt=None):
        self.title = title
        self.labels = list(labels)
        self.values = list(values)
        if fmt:
            self.fmt = fmt
        self.redraw()

    def redraw(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 60 or height < 60:
            return
        self.create_text(12, 10, text=self.title, anchor="nw", fill=theme.NAVY,
                         font=theme.FONT_BOLD)
        if not self.values or max(self.values) == 0:
            self.create_text(width / 2, height / 2, text="No data yet", fill=theme.GREY)
            return

        top, bottom = 52, height - 34
        left, right = 16, width - 16
        slot = (right - left) / len(self.values)
        bar_width = min(56, slot * 0.62)
        highest = max(self.values)
        max_chars = max(3, int(slot / 6.5))

        self.create_line(left, bottom, right, bottom, fill=theme.SKY_MID)
        for index, (label, value) in enumerate(zip(self.labels, self.values)):
            x0 = left + slot * index + (slot - bar_width) / 2
            bar_height = (bottom - top) * value / highest
            y0 = bottom - bar_height
            self.create_rectangle(x0, y0, x0 + bar_width, bottom, fill=self.color, outline="")
            self.create_text(x0 + bar_width / 2, y0 - 4, text=self.fmt(value), anchor="s",
                             fill=theme.NAVY, font=theme.FONT_SMALL)
            short = label if len(label) <= max_chars else label[:max_chars - 1] + "."
            self.create_text(x0 + bar_width / 2, bottom + 6, text=short, anchor="n",
                             fill=theme.GREY, font=theme.FONT_SMALL)


# ---- helpers shared by the booking tables ------------------------------------
# booking status text -> row colour tag used by Table
STATUS_TAGS = {"Upcoming": "free", "In progress": "busy", "Completed": "done", "Cancelled": "bad"}


def pretty_date(day):
    """date -> 'Mon 26 Oct 2026'."""
    return day.strftime("%a %d %b %Y")
