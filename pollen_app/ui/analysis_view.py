"""Vista analisi: mostra i pollini più probabilmente responsabili dei
sintomi e i suggerimenti generati dai dati raccolti."""

import customtkinter as ctk

from .. import theme
from ..analysis import analyze, build_suggestions, correlation_label


class AnalysisView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color=theme.BG)
        self.controller = controller
        self.db = controller.db

        self._build_header()
        result = analyze(self.db.load_all())
        self._build_body(result)

    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(18, 6))
        ctk.CTkButton(
            bar, text="‹  Calendario", width=130, height=40, font=theme.FONT_H2,
            fg_color=theme.SURFACE, text_color=theme.GREEN_DARK,
            hover_color=theme.SURFACE_ALT, command=self.controller.show_calendar,
        ).pack(side="left")
        ctk.CTkLabel(
            bar, text="Analisi e suggerimenti", font=theme.FONT_TITLE,
            text_color=theme.GREEN_DARK,
        ).pack(side="left", padx=16)

    def _build_body(self, result):
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(4, 12))

        # Riquadro suggerimenti testuali
        card = ctk.CTkFrame(body, fg_color=theme.SURFACE, corner_radius=14,
                            border_width=1, border_color=theme.BORDER)
        card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(card, text="💡  Suggerimenti", font=theme.FONT_H2,
                     text_color=theme.GREEN_DARK).pack(anchor="w", padx=18, pady=(14, 4))
        for line in build_suggestions(result):
            ctk.CTkLabel(
                card, text=line, font=theme.FONT_NORMAL, text_color=theme.TEXT,
                wraplength=760, justify="left", anchor="w",
            ).pack(anchor="w", padx=18, pady=2)
        ctk.CTkLabel(card, text="", height=6).pack()

        if not result.get("enough_data"):
            return

        # Classifica pollini sospetti
        suspects = result["suspects"]
        if suspects:
            ctk.CTkLabel(body, text="🌿  Pollini sotto osservazione", font=theme.FONT_H2,
                         text_color=theme.GREEN_DARK).pack(anchor="w", pady=(6, 6))
            max_delta = max((abs(r["delta"]) for r in suspects if r["delta"] is not None),
                            default=1) or 1
            for r in suspects[:8]:
                self._suspect_row(body, r, max_delta)

        # Sintomi più impattanti
        stats = result["symptom_stats"]
        if stats:
            ctk.CTkLabel(body, text="🤧  Sintomi più impattanti", font=theme.FONT_H2,
                         text_color=theme.GREEN_DARK).pack(anchor="w", pady=(18, 6))
            for s in stats[:6]:
                self._symptom_row(body, s)

    def _suspect_row(self, parent, r, max_delta):
        card = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=12,
                            border_width=1, border_color=theme.BORDER)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(0, weight=0, minsize=190)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=r["name"], font=theme.FONT_H2, text_color=theme.TEXT,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=14, pady=(10, 0))

        corr_txt = (
            f"correlazione {correlation_label(r['corr'])} ({r['corr']:+.2f})"
            if r["corr"] is not None else "correlazione n/d"
        )
        ctk.CTkLabel(card, text=corr_txt, font=theme.FONT_SMALL,
                     text_color=theme.TEXT_MUTED, anchor="w").grid(
            row=0, column=1, sticky="w", padx=8, pady=(10, 0))

        # Barra proporzionale all'aumento di sintomi nei giorni "polline alto"
        if r["delta"] is not None:
            frac = max(0.0, min(1.0, r["delta"] / max_delta)) if max_delta else 0.0
            bar_bg = ctk.CTkFrame(card, fg_color=theme.SURFACE_ALT, height=14,
                                  corner_radius=7)
            bar_bg.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 4))
            bar_bg.grid_propagate(False)
            bar_bg.grid_columnconfigure(0, weight=0)
            fill = ctk.CTkFrame(bar_bg, fg_color=theme.GREEN, height=14, corner_radius=7,
                                width=max(6, int(frac * 720)))
            fill.grid(row=0, column=0, sticky="w")
            detail = (
                f"sintomi medi {r['avg_high']:.1f} con polline alto "
                f"({r['days_high']} gg) vs {r['avg_low']:.1f} negli altri"
            )
        else:
            detail = f"registrato in {r['days_recorded']} giorni"
        ctk.CTkLabel(card, text=detail, font=theme.FONT_SMALL,
                     text_color=theme.TEXT_MUTED, anchor="w").grid(
            row=2, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 10))

    def _symptom_row(self, parent, s):
        card = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=12,
                            border_width=1, border_color=theme.BORDER)
        card.pack(fill="x", pady=3)
        ctk.CTkLabel(
            card,
            text=f"{s['name']}  —  intensità media {s['avg_level']:.1f}, "
                 f"grave in {s['days_severe']} giorni (presente in {s['days_present']})",
            font=theme.FONT_NORMAL, text_color=theme.TEXT, anchor="w",
        ).pack(anchor="w", padx=14, pady=8)
