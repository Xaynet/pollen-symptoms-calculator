"""Editor di una singola giornata: tutti i pollini e i sintomi in un'unica
schermata scorrevole, con selettori a un click per inserire i livelli
il più velocemente possibile."""

from datetime import date

import customtkinter as ctk

from .. import theme
from ..constants import (
    PLANTS,
    POLLEN_LEVELS,
    SYMPTOM_LEVELS,
    SYMPTOMS,
    display_name,
)
from ..dates_it import long_date


class DayEditor(ctk.CTkFrame):
    def __init__(self, master, controller, date_iso: str):
        super().__init__(master, fg_color=theme.BG)
        self.controller = controller
        self.db = controller.db
        self.date_iso = date_iso

        self.pollen_widgets: dict[str, ctk.CTkSegmentedButton] = {}
        self.symptom_widgets: dict[str, ctk.CTkSegmentedButton] = {}

        saved_pollen, saved_symptoms = self.db.get_day(date_iso)

        self._build_header()
        self._build_body(saved_pollen, saved_symptoms)

    # --- intestazione --------------------------------------------------------
    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(18, 6))

        ctk.CTkButton(
            bar, text="‹  Calendario", width=130, height=40, font=theme.FONT_H2,
            fg_color=theme.SURFACE, text_color=theme.GREEN_DARK,
            hover_color=theme.SURFACE_ALT, command=self.controller.show_calendar,
        ).pack(side="left")

        d = date.fromisoformat(self.date_iso)
        ctk.CTkLabel(
            bar, text=long_date(d), font=theme.FONT_TITLE, text_color=theme.GREEN_DARK,
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            bar, text="💾  Salva", width=130, height=40, font=theme.FONT_H2,
            fg_color=theme.GREEN, hover_color=theme.GREEN_HOVER, text_color="white",
            command=self._save_and_back,
        ).pack(side="right")

        if self.db.is_compiled(self.date_iso):
            self.status = ctk.CTkLabel(
                bar, text="già compilato", font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
            )
            self.status.pack(side="right", padx=10)

    # --- corpo scorrevole ----------------------------------------------------
    def _build_body(self, saved_pollen, saved_symptoms):
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(4, 10))
        body.grid_columnconfigure(0, weight=0, minsize=210)
        body.grid_columnconfigure(1, weight=1)

        row = 0
        row = self._section(body, row, "🌿  Pollini nell'aria")
        for plant in PLANTS:
            sb = self._make_row(
                body, row, display_name(plant), POLLEN_LEVELS,
                saved_pollen.get(plant, 0), kind="pollen",
            )
            self.pollen_widgets[plant] = sb
            row += 1

        row = self._section(body, row, "🤧  Sintomi")
        for symptom in SYMPTOMS:
            sb = self._make_row(
                body, row, display_name(symptom), SYMPTOM_LEVELS,
                saved_symptoms.get(symptom, 0), kind="symptom",
            )
            self.symptom_widgets[symptom] = sb
            row += 1

        # Pulsante salva anche in fondo + eventuale eliminazione
        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.grid(row=row, column=0, columnspan=2, sticky="ew", pady=18)
        ctk.CTkButton(
            actions, text="💾  Salva giornata", height=44, font=theme.FONT_H2,
            fg_color=theme.GREEN, hover_color=theme.GREEN_HOVER, text_color="white",
            command=self._save_and_back,
        ).pack(side="left")
        if self.db.is_compiled(self.date_iso):
            ctk.CTkButton(
                actions, text="🗑  Elimina giornata", height=44, font=theme.FONT_NORMAL,
                fg_color=theme.SURFACE, text_color="#B5462B",
                hover_color="#F6E0D8", command=self._delete_and_back,
            ).pack(side="left", padx=12)

    def _section(self, parent, row, title) -> int:
        ctk.CTkLabel(
            parent, text=title, font=theme.FONT_H2, text_color=theme.GREEN_DARK,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 6))
        return row + 1

    def _make_row(self, parent, row, label, values, selected_index, kind):
        bg = theme.SURFACE if row % 2 == 0 else theme.SURFACE_ALT
        ctk.CTkLabel(
            parent, text=label, font=theme.FONT_NORMAL, text_color=theme.TEXT,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=(6, 8), pady=3)

        sb = ctk.CTkSegmentedButton(
            parent,
            values=values,
            font=theme.FONT_SMALL,
            fg_color=theme.SURFACE_ALT,
            selected_color=theme.GREEN if kind == "pollen" else theme.YELLOW,
            selected_hover_color=theme.GREEN_HOVER if kind == "pollen" else theme.YELLOW_HOVER,
            unselected_color=theme.SURFACE,
            unselected_hover_color=theme.SURFACE_ALT,
            text_color=theme.TEXT,
        )
        sb.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=3)
        sb.set(values[selected_index])
        return sb

    # --- azioni --------------------------------------------------------------
    def _collect(self):
        pollen = {
            plant: POLLEN_LEVELS.index(sb.get())
            for plant, sb in self.pollen_widgets.items()
        }
        symptoms = {
            sym: SYMPTOM_LEVELS.index(sb.get())
            for sym, sb in self.symptom_widgets.items()
        }
        return pollen, symptoms

    def _save_and_back(self):
        pollen, symptoms = self._collect()
        self.db.save_day(self.date_iso, pollen, symptoms)
        self.controller.show_calendar()

    def _delete_and_back(self):
        self.db.delete_day(self.date_iso)
        self.controller.show_calendar()
