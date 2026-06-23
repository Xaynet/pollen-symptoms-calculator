"""Vista calendario: panoramica mensile con i giorni compilati colorati
in base alla severità dei sintomi. Cliccando un giorno si apre l'editor."""

import calendar
from datetime import date

import customtkinter as ctk

from .. import theme
from ..dates_it import WEEKDAYS_SHORT, month_label


class CalendarView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color=theme.BG)
        self.controller = controller
        self.db = controller.db

        today = date.today()
        self.year = today.year
        self.month = today.month
        self._day_buttons: list[ctk.CTkButton] = []

        self._build_header()
        self._build_legend()
        self.grid_container = ctk.CTkFrame(self, fg_color=theme.BG)
        self.grid_container.pack(fill="both", expand=True, padx=24, pady=(4, 12))
        self._create_grid_structure()
        self._render_grid()

    # --- intestazione --------------------------------------------------------
    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkButton(
            bar, text="‹", width=44, height=40, font=(theme.FONT_FAMILY, 20, "bold"),
            fg_color=theme.SURFACE, text_color=theme.GREEN_DARK,
            hover_color=theme.SURFACE_ALT, command=self._prev_month,
        ).pack(side="left")

        self.month_lbl = ctk.CTkLabel(
            bar, text=month_label(self.year, self.month),
            font=theme.FONT_TITLE, text_color=theme.GREEN_DARK,
        )
        self.month_lbl.pack(side="left", padx=14)

        ctk.CTkButton(
            bar, text="›", width=44, height=40, font=(theme.FONT_FAMILY, 20, "bold"),
            fg_color=theme.SURFACE, text_color=theme.GREEN_DARK,
            hover_color=theme.SURFACE_ALT, command=self._next_month,
        ).pack(side="left")

        # Azioni rapide a destra
        ctk.CTkButton(
            bar, text="📊  Analisi", width=120, height=40, font=theme.FONT_H2,
            fg_color=theme.GREEN, hover_color=theme.GREEN_HOVER, text_color="white",
            command=self.controller.show_analysis,
        ).pack(side="right")

        ctk.CTkButton(
            bar, text="＋  Oggi", width=110, height=40, font=theme.FONT_H2,
            fg_color=theme.YELLOW, hover_color=theme.YELLOW_HOVER, text_color=theme.TEXT,
            command=lambda: self.controller.show_editor(date.today().isoformat()),
        ).pack(side="right", padx=(0, 10))

    def _build_legend(self):
        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(fill="x", padx=24)
        ctk.CTkLabel(
            legend, text="Compilato:", font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 6))
        labels = ["nessun sintomo", "", "", "", "", "max"]
        for i, color in enumerate(theme.SEVERITY_COLORS):
            sw = ctk.CTkFrame(legend, width=22, height=14, fg_color=color,
                              corner_radius=4, border_width=1, border_color=theme.BORDER)
            sw.pack(side="left", padx=1)
            if labels[i]:
                ctk.CTkLabel(legend, text=labels[i], font=theme.FONT_SMALL,
                             text_color=theme.TEXT_MUTED).pack(side="left", padx=(2, 8))
        ctk.CTkFrame(legend, width=22, height=14, fg_color=theme.DAY_EMPTY,
                     corner_radius=4, border_width=1, border_color=theme.BORDER).pack(
            side="left", padx=(12, 4))
        ctk.CTkLabel(legend, text="da compilare", font=theme.FONT_SMALL,
                     text_color=theme.TEXT_MUTED).pack(side="left")

    # --- griglia -------------------------------------------------------------
    def _create_grid_structure(self):
        """Crea una volta sola le 42 celle e le intestazioni della settimana."""
        for col in range(7):
            self.grid_container.grid_columnconfigure(col, weight=1, uniform="day")

        for col, name in enumerate(WEEKDAYS_SHORT):
            ctk.CTkLabel(
                self.grid_container, text=name, font=theme.FONT_H2,
                text_color=theme.GREEN_DARK,
            ).grid(row=0, column=col, pady=(0, 6), sticky="n")

        for i in range(42):
            r, col = divmod(i, 7)
            btn = ctk.CTkButton(
                self.grid_container, text="",
                font=theme.FONT_DAY, fg_color=theme.DAY_EMPTY,
                text_color=theme.DAY_EMPTY_TEXT, hover_color=theme.SURFACE_ALT,
                corner_radius=10, border_width=1, border_color=theme.BORDER,
            )
            btn.grid(row=r + 1, column=col, padx=4, pady=4, sticky="nsew")
            btn.grid_remove()
            self._day_buttons.append(btn)

    def _render_grid(self):
        """Aggiorna i bottoni esistenti senza distruggerli."""
        summary = self.db.month_summary(self.year, self.month)
        today_iso = date.today().isoformat()
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.year, self.month)

        for r in range(1, 7):
            if r <= len(weeks):
                self.grid_container.grid_rowconfigure(r, weight=1, uniform="wk", minsize=0)
            else:
                self.grid_container.grid_rowconfigure(r, weight=0, uniform="", minsize=0)

        grid = [[0] * 7 for _ in range(6)]
        for r, week in enumerate(weeks):
            for col, day in enumerate(week):
                grid[r][col] = day

        for idx, btn in enumerate(self._day_buttons):
            r, col = divmod(idx, 7)
            day = grid[r][col]
            if day:
                iso = f"{self.year:04d}-{self.month:02d}-{day:02d}"
                info = summary.get(iso)
                bg = theme.severity_color(info["max_symptom"]) if info else theme.DAY_EMPTY
                fg = theme.TEXT if info else theme.DAY_EMPTY_TEXT
                is_today = iso == today_iso
                btn.configure(
                    text=str(day),
                    fg_color=bg,
                    text_color=fg,
                    border_width=3 if is_today else 1,
                    border_color=theme.GREEN if is_today else theme.BORDER,
                    command=lambda d=iso: self.controller.show_editor(d),
                )
                btn.grid(row=r + 1, column=col, padx=4, pady=4, sticky="nsew")
            else:
                btn.grid_remove()

    # --- navigazione ---------------------------------------------------------
    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._refresh()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._refresh()

    def _refresh(self):
        self.month_lbl.configure(text=month_label(self.year, self.month))
        self._render_grid()
