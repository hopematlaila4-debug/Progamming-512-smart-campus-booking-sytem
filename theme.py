"""
theme.py
--------
Sky-blue colour scheme and ttk styles used by every screen.
Change the colours here and the whole application follows.
"""
from tkinter import ttk

# ---- colours ----------------------------------------------------------------
SKY = "#87CEEB"          # main sky blue (header, table headings)
SKY_MID = "#BFE4F5"      # sidebar, borders
SKY_LIGHT = "#E3F4FC"    # hover / alternate rows
SKY_PALE = "#F4FAFD"     # window background
SKY_DARK = "#2B8CC4"     # buttons, selected rows, accents
SKY_DEEP = "#1B6A99"     # button hover
NAVY = "#0B3954"         # text
GREY = "#5F7A8A"         # secondary text
WHITE = "#FFFFFF"
GREEN = "#1F8A5B"
ORANGE = "#C77D12"
RED = "#C0392B"

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_HEADING = ("Segoe UI", 12, "bold")
FONT_BIG = ("Segoe UI", 20, "bold")


def apply_theme(root):
    """Configure ttk widgets once, at start-up."""
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=SKY_PALE)
    root.option_add("*TCombobox*Listbox.font", FONT)
    root.option_add("*TCombobox*Listbox.selectBackground", SKY_DARK)

    style.configure(".", font=FONT, background=SKY_PALE, foreground=NAVY)
    style.configure("TFrame", background=SKY_PALE)
    style.configure("Card.TFrame", background=WHITE)
    style.configure("Panel.TFrame", background=WHITE, bordercolor=SKY_MID, relief="solid", borderwidth=1)
    style.configure("Header.TFrame", background=SKY)
    style.configure("Side.TFrame", background=SKY_MID)
    style.configure("Hero.TFrame", background=SKY)

    style.configure("TLabel", background=SKY_PALE, foreground=NAVY)
    style.configure("Card.TLabel", background=WHITE)
    style.configure("Muted.TLabel", background=SKY_PALE, foreground=GREY, font=FONT_SMALL)
    style.configure("CardMuted.TLabel", background=WHITE, foreground=GREY, font=FONT_SMALL)
    style.configure("Title.TLabel", background=SKY_PALE, font=FONT_TITLE)
    style.configure("Heading.TLabel", background=WHITE, font=FONT_HEADING)
    style.configure("PageTitle.TLabel", background=SKY_PALE, font=("Segoe UI", 15, "bold"))
    style.configure("Header.TLabel", background=SKY, foreground=NAVY)
    style.configure("HeaderBig.TLabel", background=SKY, foreground=NAVY, font=("Segoe UI", 13, "bold"))
    style.configure("HeaderSmall.TLabel", background=SKY, foreground=NAVY, font=FONT_SMALL)
    style.configure("Side.TLabel", background=SKY_MID, foreground=NAVY)
    style.configure("Hero.TLabel", background=SKY, foreground=NAVY)
    style.configure("HeroTitle.TLabel", background=SKY, foreground=NAVY, font=("Segoe UI", 22, "bold"))
    style.configure("Stat.TLabel", background=WHITE, foreground=SKY_DEEP, font=FONT_BIG)
    style.configure("Good.TLabel", background=WHITE, foreground=GREEN)
    style.configure("Bad.TLabel", background=WHITE, foreground=RED)

    # Buttons
    style.configure("TButton", padding=(12, 6), background=SKY_MID, foreground=NAVY,
                    bordercolor=SKY_MID, focuscolor=SKY_MID, relief="flat")
    style.map("TButton", background=[("active", SKY)])
    style.configure("Primary.TButton", background=SKY_DARK, foreground=WHITE,
                    bordercolor=SKY_DARK, font=FONT_BOLD)
    style.map("Primary.TButton", background=[("active", SKY_DEEP), ("disabled", SKY_MID)],
              foreground=[("disabled", GREY)])
    style.configure("Danger.TButton", background=RED, foreground=WHITE, bordercolor=RED, font=FONT_BOLD)
    style.map("Danger.TButton", background=[("active", "#962D22")])
    style.configure("Header.TButton", background=WHITE, foreground=NAVY, bordercolor=WHITE, padding=(10, 4))
    style.map("Header.TButton", background=[("active", SKY_LIGHT)])
    style.configure("Link.TButton", background=WHITE, foreground=SKY_DEEP, bordercolor=WHITE,
                    padding=(2, 2), font=FONT_BOLD)
    style.map("Link.TButton", foreground=[("active", NAVY)], background=[("active", WHITE)])
    style.configure("Nav.TButton", background=SKY_MID, foreground=NAVY, anchor="w",
                    padding=(16, 10), bordercolor=SKY_MID, font=FONT)
    style.map("Nav.TButton", background=[("active", SKY)])
    style.configure("NavActive.TButton", background=SKY_DARK, foreground=WHITE, anchor="w",
                    padding=(16, 10), bordercolor=SKY_DARK, font=FONT_BOLD)
    style.map("NavActive.TButton", background=[("active", SKY_DEEP)])

    # Inputs
    style.configure("TEntry", fieldbackground=WHITE, bordercolor=SKY_MID, padding=4)
    style.configure("TCombobox", fieldbackground=WHITE, bordercolor=SKY_MID, padding=4,
                    arrowcolor=SKY_DARK)
    style.map("TCombobox", fieldbackground=[("readonly", WHITE)])
    style.configure("TSpinbox", fieldbackground=WHITE, bordercolor=SKY_MID, padding=4)
    style.configure("TCheckbutton", background=WHITE)

    # Tables
    style.configure("Treeview", background=WHITE, fieldbackground=WHITE, rowheight=26,
                    bordercolor=SKY_MID, font=FONT)
    style.configure("Treeview.Heading", background=SKY, foreground=NAVY, font=FONT_BOLD,
                    padding=(6, 5), relief="flat")
    style.map("Treeview", background=[("selected", SKY_DARK)], foreground=[("selected", WHITE)])
    style.map("Treeview.Heading", background=[("active", SKY_MID)])
