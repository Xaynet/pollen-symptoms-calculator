"""Nomi di mesi e giorni in italiano, senza dipendere dal locale di sistema
(che su Windows potrebbe non essere impostato su italiano)."""

from datetime import date

MONTHS = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]

# Lunedì = 0 ... Domenica = 6 (come date.weekday())
WEEKDAYS_SHORT = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
WEEKDAYS_LONG = [
    "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica",
]


def month_label(year: int, month: int) -> str:
    return f"{MONTHS[month - 1]} {year}"


def long_date(d: date) -> str:
    return f"{WEEKDAYS_LONG[d.weekday()]} {d.day} {MONTHS[d.month - 1]} {d.year}"
