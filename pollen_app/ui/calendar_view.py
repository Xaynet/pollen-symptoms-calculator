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

        self._build_header()
        self._build_legend()
        self.grid_container = ctk.CTkFrame(self, fg_color=theme.BG)
        self.grid_container.pack(fill="both", expand=True, padx=24, pady=(4, 12))
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
    def _render_grid(self):
        for w in self.grid_container.winfo_children():
            w.destroy()

        for col in range(7):
            self.grid_container.grid_columnconfigure(col, weight=1, uniform="day")

        # intestazioni giorni della settimana
        for col, name in enumerate(WEEKDAYS_SHORT):
            ctk.CTkLabel(
                self.grid_container, text=name, font=theme.FONT_H2,
                text_color=theme.GREEN_DARK,
            ).grid(row=0, column=col, pady=(0, 6), sticky="n")

        summary = self.db.month_summary(self.year, self.month)
        today_iso = date.today().isoformat()
        cal = calendar.Calendar(firstweekday=0)  # 0 = lunedì

        for r, week in enumerate(cal.monthdayscalendar(self.year, self.month), start=1):
            self.grid_container.grid_rowconfigure(r, weight=1, uniform="wk")
            for col, day in enumerate(week):
                if day == 0:
                    continue
                iso = f"{self.year:04d}-{self.month:02d}-{day:02d}"
                info = summary.get(iso)
                if info is not None:
                    bg = theme.severity_color(info["max_symptom"])
                    fg = theme.TEXT
                    border = theme.BORDER
                else:
                    bg = theme.DAY_EMPTY
                    fg = theme.DAY_EMPTY_TEXT
                    border = theme.BORDER

                is_today = iso == today_iso
                btn = ctk.CTkButton(
                    self.grid_container,
                    text=str(day),
                    font=theme.FONT_DAY,
                    fg_color=bg,
                    text_color=fg,
                    hover_color=theme.SURFACE_ALT,
                    corner_radius=10,
                    border_width=3 if is_today else 1,
                    border_color=theme.GREEN if is_today else border,
                    command=lambda d=iso: self.controller.show_editor(d),
                )
                btn.grid(row=r, column=col, padx=4, pady=4, sticky="nsew")

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
