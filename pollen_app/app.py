"""Finestra principale e controller di navigazione tra le viste."""

import customtkinter as ctk

from . import theme
from .db import Database
from .ui.analysis_view import AnalysisView
from .ui.calendar_view import CalendarView
from .ui.day_editor import DayEditor


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")

        self.db = Database()

        self.title("Pollini & Sintomi")
        self.geometry("920x720")
        self.minsize(820, 600)
        self.configure(fg_color=theme.BG)

        # Contenitore che ospita la vista corrente
        self.container = ctk.CTkFrame(self, fg_color=theme.BG)
        self.container.pack(fill="both", expand=True)

        # Barra di stato con il percorso del database (per i backup)
        self.statusbar = ctk.CTkLabel(
            self,
            text=f"Dati salvati in: {self.db.path}",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.statusbar.pack(fill="x", side="bottom", padx=14, pady=4)

        self.current_view = None
        self.show_calendar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _swap(self, view):
        if self.current_view is not None:
            self.current_view.destroy()
        self.current_view = view
        view.pack(fill="both", expand=True)

    def show_calendar(self):
        self._swap(CalendarView(self.container, self))

    def show_editor(self, date_iso: str):
        self._swap(DayEditor(self.container, self, date_iso))

    def show_analysis(self):
        self._swap(AnalysisView(self.container, self))

    def _on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()


def main():
    app = App()
    app.mainloop()
