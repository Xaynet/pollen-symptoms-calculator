"""Strato di persistenza su SQLite.

Il database è un singolo file su disco (in Documenti per impostazione
predefinita), facilmente copiabile per i backup. Memorizziamo solo i
valori NON nulli (livello > 0): l'assenza di una riga equivale ad
"Assente", così il file resta compatto.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path


def default_db_path() -> Path:
    """Percorso predefinito del database.

    Si può forzare un percorso alternativo con la variabile d'ambiente
    POLLEN_DB_PATH (utile per test o per spostare i dati su un altro disco).
    """
    override = os.environ.get("POLLEN_DB_PATH")
    if override:
        return Path(override)
    base = Path.home() / "Documents" / "PollenSymptomsCalculator"
    return base / "pollen_data.db"


class Database:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False non serve: tutto gira sul thread della UI.
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS days (
                date       TEXT PRIMARY KEY,   -- formato YYYY-MM-DD
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pollen (
                date  TEXT NOT NULL,
                plant TEXT NOT NULL,
                level INTEGER NOT NULL,         -- 0..3
                PRIMARY KEY (date, plant),
                FOREIGN KEY (date) REFERENCES days(date) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS symptoms (
                date    TEXT NOT NULL,
                symptom TEXT NOT NULL,
                level   INTEGER NOT NULL,       -- 0..5
                PRIMARY KEY (date, symptom),
                FOREIGN KEY (date) REFERENCES days(date) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    # --- Scrittura -----------------------------------------------------------
    def save_day(self, date: str, pollen: dict[str, int], symptoms: dict[str, int]) -> None:
        """Salva (o aggiorna) un giorno. I dizionari mappano chiave -> livello;
        i livelli pari a 0 non vengono memorizzati."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO days(date, updated_at) VALUES(?, ?) "
            "ON CONFLICT(date) DO UPDATE SET updated_at=excluded.updated_at",
            (date, datetime.now().isoformat(timespec="seconds")),
        )
        # Riscriviamo da zero i livelli del giorno (semplice e robusto).
        cur.execute("DELETE FROM pollen WHERE date = ?", (date,))
        cur.execute("DELETE FROM symptoms WHERE date = ?", (date,))
        cur.executemany(
            "INSERT INTO pollen(date, plant, level) VALUES(?, ?, ?)",
            [(date, p, lv) for p, lv in pollen.items() if lv > 0],
        )
        cur.executemany(
            "INSERT INTO symptoms(date, symptom, level) VALUES(?, ?, ?)",
            [(date, s, lv) for s, lv in symptoms.items() if lv > 0],
        )
        self.conn.commit()

    def delete_day(self, date: str) -> None:
        self.conn.execute("DELETE FROM days WHERE date = ?", (date,))
        self.conn.commit()

    # --- Lettura -------------------------------------------------------------
    def is_compiled(self, date: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM days WHERE date = ?", (date,))
        return cur.fetchone() is not None

    def get_day(self, date: str) -> tuple[dict[str, int], dict[str, int]]:
        """Restituisce (pollini, sintomi) per un giorno; livelli mancanti = 0."""
        pollen = {
            row[0]: row[1]
            for row in self.conn.execute(
                "SELECT plant, level FROM pollen WHERE date = ?", (date,)
            )
        }
        symptoms = {
            row[0]: row[1]
            for row in self.conn.execute(
                "SELECT symptom, level FROM symptoms WHERE date = ?", (date,)
            )
        }
        return pollen, symptoms

    def month_summary(self, year: int, month: int) -> dict[str, dict]:
        """Per ogni giorno compilato del mese restituisce un riepilogo:
        {'YYYY-MM-DD': {'max_symptom': int, 'total_symptom': int}}.
        """
        prefix = f"{year:04d}-{month:02d}-"
        result: dict[str, dict] = {}
        for (date,) in self.conn.execute(
            "SELECT date FROM days WHERE date LIKE ?", (prefix + "%",)
        ):
            result[date] = {"max_symptom": 0, "total_symptom": 0}
        for date, mx, tot in self.conn.execute(
            "SELECT date, MAX(level), SUM(level) FROM symptoms "
            "WHERE date LIKE ? GROUP BY date",
            (prefix + "%",),
        ):
            if date in result:
                result[date]["max_symptom"] = mx or 0
                result[date]["total_symptom"] = tot or 0
        return result

    def all_days(self) -> list[str]:
        return [row[0] for row in self.conn.execute("SELECT date FROM days ORDER BY date")]

    def load_all(self) -> dict[str, dict]:
        """Carica tutti i dati per l'analisi:
        {'YYYY-MM-DD': {'pollen': {pianta: lv}, 'symptoms': {sintomo: lv}}}.
        """
        data: dict[str, dict] = {
            d: {"pollen": {}, "symptoms": {}} for d in self.all_days()
        }
        for date, plant, level in self.conn.execute("SELECT date, plant, level FROM pollen"):
            if date in data:
                data[date]["pollen"][plant] = level
        for date, sym, level in self.conn.execute("SELECT date, symptom, level FROM symptoms"):
            if date in data:
                data[date]["symptoms"][sym] = level
        return data

    def close(self) -> None:
        self.conn.close()
