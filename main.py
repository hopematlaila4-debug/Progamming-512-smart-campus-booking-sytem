"""
main.py - start the Smart Campus Resource Booking System.

Run this file from PyCharm (right-click > Run 'main').
The first run creates data/campus_booking.db and fills it with demo data.
"""
import sqlite3
import tkinter as tk
from tkinter import messagebox

from database.db_manager import DatabaseManager
from gui.app import App


def main():
    try:
        db = DatabaseManager()
    except sqlite3.Error as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database error", f"The database could not be opened.\n\n{error}")
        return
    App(db).mainloop()


if __name__ == "__main__":
    main()
