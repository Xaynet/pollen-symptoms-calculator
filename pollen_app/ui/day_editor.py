"""Editor di una singola giornata: tutti i pollini e i sintomi in un'unica
schermata scorrevole, con selettori a un click per inserire i livelli
il più velocemente possibile."""

import threading
from datetime import date

import customtkinter as ctk

from .. import openmeteo, theme
from ..constants import (
    PARTICULATES,
    PLANTS,
    POLLEN_LEVELS,
    SYMPTOM_LEVELS,
    SYMPTOMS,
    display_name,
    particulate_name,
)
from ..dates_it import long_date
from ..openmeteo import COVERED_PLANTS


class DayEditor(ctk.CTkFrame):
    def __init__(self, master, controller, date_iso: str):
        super().__init__(master, fg_color=theme.BG)
        self.controller = controller
        self.db = controller.db
        self.date_iso = date_iso

        self.pollen_widgets: dict[str, ctk.CTkSegmentedButton] = {}
        self.symptom_widgets: dict[str, ctk.CTkSegmentedButton] = {}
        self.particulate_widgets: dict[str, ctk.CTkSegmentedButton] = {}

        # Impostazione globale (non per giorno): quali pollini mostrare.
        self.show_all_pollen = self.db.get_setting("pollen_filter", "all") != "openmeteo"
        self.saved_pollen, self.saved_symptoms, self.saved_particulate = self.db.get_day(date_iso)
        self.body = None

        self._build_header()
        self._build_body(self.saved_pollen, self.saved_symptoms, self.saved_particulate)

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

    def _visible_plants(self):
        if self.show_all_pollen:
            return PLANTS
        covered = set(COVERED_PLANTS)
        return [p for p in PLANTS if p in covered]

    # --- corpo scorrevole ----------------------------------------------------
    def _build_body(self, pollen_vals, symptom_vals, particulate_vals):
        if self.body is not None:
            self.body.destroy()
        self.pollen_widgets = {}
        self.symptom_widgets = {}
        self.particulate_widgets = {}

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(4, 10))
        body.grid_columnconfigure(0, weight=0, minsize=210)
        body.grid_columnconfigure(1, weight=1)
        self.body = body

        row = 0
        row = self._section(body, row, "🌿  Pollini nell'aria")
        row = self._build_filter_bar(body, row)
        row = self._build_prefill_bar(body, row)
        for plant in self._visible_plants():
            sb = self._make_row(
                body, row, display_name(plant), POLLEN_LEVELS,
                pollen_vals.get(plant, 0), kind="pollen",
            )
            self.pollen_widgets[plant] = sb
            row += 1

        # Polveri / particolato (sempre visibili: sono tutte da Open-Meteo).
        row = self._section(body, row, "🌫  Polveri (particolato)")
        for kind in PARTICULATES:
            sb = self._make_row(
                body, row, particulate_name(kind), POLLEN_LEVELS,
                particulate_vals.get(kind, 0), kind="particulate",
            )
            self.particulate_widgets[kind] = sb
            row += 1

        row = self._section(body, row, "🤧  Sintomi")
        for symptom in SYMPTOMS:
            sb = self._make_row(
                body, row, display_name(symptom), SYMPTOM_LEVELS,
                symptom_vals.get(symptom, 0), kind="symptom",
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

    # --- filtro pollini (impostazione globale) -------------------------------
    def _build_filter_bar(self, parent, row) -> int:
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        self.pollen_filter_switch = ctk.CTkSwitch(
            bar, text="Mostra solo i pollini di Open-Meteo",
            font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED,
            progress_color=theme.GREEN, command=self._toggle_pollen_filter,
        )
        self.pollen_filter_switch.pack(side="left")
        if not self.show_all_pollen:
            self.pollen_filter_switch.select()
        return row + 1

    def _toggle_pollen_filter(self):
        only_om = bool(self.pollen_filter_switch.get())
        self.db.set_setting("pollen_filter", "openmeteo" if only_om else "all")
        # Conserva i valori inseriti finora senza perdere quelli dei pollini che
        # vengono nascosti: parto dai valori salvati e sovrascrivo con i correnti.
        cur_pollen, cur_symptoms, cur_particulate = self._collect()
        merged = dict(self.saved_pollen)
        merged.update(cur_pollen)
        self.saved_pollen = merged
        self.saved_symptoms = cur_symptoms
        self.saved_particulate = cur_particulate
        self.show_all_pollen = not only_om
        self._build_body(merged, cur_symptoms, cur_particulate)

    # --- precompilazione da Open-Meteo --------------------------------------
    def _build_prefill_bar(self, parent, row) -> int:
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.prefill_btn = ctk.CTkButton(
            bar, text="🌍  Precompila da Open-Meteo", height=34, font=theme.FONT_SMALL,
            fg_color=theme.YELLOW, hover_color=theme.YELLOW_HOVER, text_color=theme.TEXT,
            command=self._prefill_pollen,
        )
        self.prefill_btn.pack(side="left")

        ctk.CTkButton(
            bar, text="📍  Città", width=80, height=34, font=theme.FONT_SMALL,
            fg_color=theme.SURFACE, text_color=theme.GREEN_DARK,
            hover_color=theme.SURFACE_ALT, command=self._change_city,
        ).pack(side="left", padx=8)

        self.prefill_status = ctk.CTkLabel(
            bar, font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED,
            anchor="w", justify="left", wraplength=430,
            text="Riempie betulla, graminacee, assenzio, olivo, ambrosia e le polveri (PM10, PM2.5).",
        )
        self.prefill_status.pack(side="left", padx=10, fill="x", expand=True)
        return row + 1

    def _set_prefill_status(self, text, error=False):
        self.prefill_status.configure(
            text=text, text_color="#B5462B" if error else theme.TEXT_MUTED,
        )

    def _ask_city(self):
        """Chiede una città, la geolocalizza e la salva. Restituisce
        (lat, lon, etichetta) oppure None se annullata/non trovata."""
        dialog = ctk.CTkInputDialog(
            text="In quale località vuoi i pollini?", title="Località",
        )
        city = dialog.get_input()
        if not city or not city.strip():
            return None
        try:
            lat, lon, label = openmeteo.geocode(city)
        except openmeteo.OpenMeteoError as exc:
            self._set_prefill_status(str(exc), error=True)
            return None
        self.db.set_setting("loc_lat", str(lat))
        self.db.set_setting("loc_lon", str(lon))
        self.db.set_setting("loc_label", label)
        return lat, lon, label

    def _saved_location(self):
        lat = self.db.get_setting("loc_lat")
        lon = self.db.get_setting("loc_lon")
        if lat and lon:
            return float(lat), float(lon), self.db.get_setting("loc_label", "località salvata")
        return None

    def _change_city(self):
        loc = self._ask_city()
        if loc:
            self._set_prefill_status(f"Località impostata: {loc[2]}")

    def _prefill_pollen(self):
        loc = self._saved_location() or self._ask_city()
        if not loc:
            return
        lat, lon, label = loc
        self.prefill_btn.configure(state="disabled")
        self._set_prefill_status(f"Scarico i pollini per {label}…")
        threading.Thread(
            target=self._prefill_worker, args=(lat, lon, label), daemon=True,
        ).start()

    def _prefill_worker(self, lat, lon, label):
        try:
            air = openmeteo.fetch_air(lat, lon, self.date_iso)
        except openmeteo.OpenMeteoError as exc:
            self.after(0, lambda e=str(exc): self._prefill_done(None, label, e))
            return
        self.after(0, lambda: self._prefill_done(air, label, None))

    def _prefill_done(self, air, label, error):
        if not self.winfo_exists():
            return
        self.prefill_btn.configure(state="normal")
        if error:
            self._set_prefill_status(error, error=True)
            return

        def apply(values, widgets, name_fn):
            names = []
            for key, lv in values.items():
                sb = widgets.get(key)
                if sb is not None:
                    sb.set(POLLEN_LEVELS[lv])
                    self._update_segment_color(sb)
                    names.append(name_fn(key))
            return names

        applied = apply(air.get("pollen", {}), self.pollen_widgets, display_name)
        applied += apply(air.get("particulate", {}), self.particulate_widgets, particulate_name)
        self._set_prefill_status(
            f"Precompilate {len(applied)} voci da Open-Meteo ({label}): "
            f"{', '.join(applied)}. Controlla e salva."
        )

    def _make_row(self, parent, row, label, values, selected_index, kind):
        ctk.CTkLabel(
            parent, text=label, font=theme.FONT_NORMAL, text_color=theme.TEXT,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=(6, 8), pady=3)

        colors = theme.SYMPTOM_LEVEL_COLORS if kind == "symptom" else theme.POLLEN_LEVEL_COLORS
        sb = ctk.CTkSegmentedButton(
            parent,
            values=values,
            font=theme.FONT_SMALL,
            fg_color=theme.SURFACE_ALT,
            unselected_color=theme.SURFACE,
            unselected_hover_color=theme.SURFACE_ALT,
            text_color=theme.TEXT,
        )
        # Il colore del valore selezionato dipende dall'intensità scelta.
        sb._level_values = list(values)
        sb._level_colors = colors
        sb.configure(command=lambda v, w=sb: self._update_segment_color(w))
        sb.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=3)
        sb.set(values[selected_index])
        self._update_segment_color(sb)
        return sb

    def _update_segment_color(self, sb):
        """Imposta il colore del segmento selezionato in base al livello."""
        idx = sb._level_values.index(sb.get())
        color = sb._level_colors[idx]
        sb.configure(selected_color=color, selected_hover_color=color)

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
        particulate = {
            kind: POLLEN_LEVELS.index(sb.get())
            for kind, sb in self.particulate_widgets.items()
        }
        return pollen, symptoms, particulate

    def _save_and_back(self):
        pollen, symptoms, particulate = self._collect()
        self.db.save_day(self.date_iso, pollen, symptoms, particulate)
        self.controller.show_calendar()

    def _delete_and_back(self):
        self.db.delete_day(self.date_iso)
        self.controller.show_calendar()
