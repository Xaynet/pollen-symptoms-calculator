"""Finestra principale e controller di navigazione tra le viste."""

from datetime import date
from tkinter import filedialog, messagebox

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

        # Barra in basso: percorso del database + backup/ripristino
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", side="bottom", padx=14, pady=4)

        ctk.CTkButton(
            bottom, text="↩  Ripristina backup", width=150, height=28,
            font=theme.FONT_SMALL, fg_color=theme.SURFACE, text_color=theme.GREEN_DARK,
            hover_color=theme.SURFACE_ALT, command=self._restore_backup,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            bottom, text="💾  Esporta backup", width=140, height=28,
            font=theme.FONT_SMALL, fg_color=theme.SURFACE, text_color=theme.GREEN_DARK,
            hover_color=theme.SURFACE_ALT, command=self._export_backup,
        ).pack(side="right")

        self.statusbar = ctk.CTkLabel(
            bottom,
            text=f"Dati salvati in: {self.db.path}",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.statusbar.pack(side="left", fill="x", expand=True)

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

    # --- backup / ripristino -------------------------------------------------
    def _export_backup(self):
        path = filedialog.asksaveasfilename(
            title="Esporta backup",
            defaultextension=".db",
            initialfile=f"pollini_backup_{date.today().isoformat()}.db",
            filetypes=[("Backup Pollini & Sintomi", "*.db"), ("Tutti i file", "*.*")],
        )
        if not path:
            return
        try:
            self.db.backup_to(path)
        except Exception as exc:  # noqa: BLE001 - mostriamo l'errore all'utente
            messagebox.showerror("Backup non riuscito", str(exc))
            return
        messagebox.showinfo("Backup completato", f"Copia salvata in:\n{path}")

    def _restore_backup(self):
        if not messagebox.askyesno(
            "Ripristina backup",
            "Il ripristino sostituirà TUTTI i dati attuali con quelli del "
            "backup scelto.\n\nConsiglio: fai prima un'esportazione di sicurezza.\n\n"
            "Vuoi continuare?",
        ):
            return
        path = filedialog.askopenfilename(
            title="Scegli il file di backup da ripristinare",
            filetypes=[("Backup Pollini & Sintomi", "*.db"), ("Tutti i file", "*.*")],
        )
        if not path:
            return
        try:
            self.db.restore_from(path)
        except ValueError as exc:
            messagebox.showerror("Ripristino non riuscito", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Ripristino non riuscito", str(exc))
            return
        self.show_calendar()  # ricarica la vista con i dati ripristinati
        messagebox.showinfo("Ripristino completato", "I dati sono stati ripristinati dal backup.")

    def _on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()


def main():
    app = App()
    app.mainloop()
