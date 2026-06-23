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

# Versione corrente dello schema. Aumentala di 1 ogni volta che aggiungi una
# nuova voce in _MIGRATIONS, così le versioni future dell'app aggiornano da sole
# i database degli utenti senza perdere i dati già inseriti.
SCHEMA_VERSION = 2

# Schema di base (versione 1). Tutte le CREATE sono "IF NOT EXISTS" così la
# migrazione è sicura sia su un database nuovo sia su uno preesistente.
_SCHEMA_V1 = """
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

    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
"""


def _migration_1(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_V1)


def _migration_2(conn: sqlite3.Connection) -> None:
    """Rende esplicito il livello 0 ("Assente valutato") per tutti i pollini
    non presenti nei giorni già salvati.

    Prima dell'introduzione del filtro pollini, l'editor mostrava sempre tutte
    le piante: l'assenza di riga significava quindi "Assente". Da ora invece
    l'assenza di riga può indicare "non valutato" (filtro "solo Open-Meteo").
    Per non alterare il significato dei dati storici, marchiamo come valutate
    (livello 0) tutte le piante mancanti nei giorni preesistenti.
    """
    from .constants import PLANTS

    days = [r[0] for r in conn.execute("SELECT date FROM days")]
    for d in days:
        present = {
            r[0] for r in conn.execute("SELECT plant FROM pollen WHERE date = ?", (d,))
        }
        missing = [(d, p, 0) for p in PLANTS if p not in present]
        if missing:
            conn.executemany(
                "INSERT INTO pollen(date, plant, level) VALUES(?, ?, ?)", missing
            )


# Mappa: numero di versione -> funzione che porta lo schema a quella versione.
# Per evolvere il database in futuro (es. aggiungere una colonna) aggiungi qui
# _migration_3, ... e incrementa SCHEMA_VERSION.
_MIGRATIONS = {
    1: _migration_1,
    2: _migration_2,
}


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
        self._migrate()

    def _migrate(self) -> None:
        """Porta lo schema del database alla versione corrente applicando, in
        ordine, solo le migrazioni mancanti. La versione è memorizzata nel file
        stesso tramite PRAGMA user_version, così l'aggiornamento è automatico e
        i dati esistenti vengono preservati."""
        current = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if current >= SCHEMA_VERSION:
            return
        for version in range(current + 1, SCHEMA_VERSION + 1):
            migration = _MIGRATIONS.get(version)
            if migration is not None:
                migration(self.conn)
            # user_version non accetta parametri: l'intero è validato da range().
            self.conn.execute(f"PRAGMA user_version = {int(version)}")
        self.conn.commit()

    # --- Impostazioni (coppie chiave/valore) ---------------------------------
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        cur = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    # --- Scrittura -----------------------------------------------------------
    def save_day(self, date: str, pollen: dict[str, int], symptoms: dict[str, int]) -> None:
        """Salva (o aggiorna) un giorno.

        `pollen` contiene SOLO le piante effettivamente valutate (quelle mostrate
        nell'editor). Vengono memorizzate tutte, anche a livello 0 ("Assente
        valutato"), tramite upsert e SENZA cancellare le piante non passate: così,
        con il filtro "solo Open-Meteo" attivo, le altre piante restano "non
        valutate" per quel giorno (riga assente) e non influenzano le statistiche.

        I sintomi sono sempre tutti presenti nell'editor, quindi li riscriviamo da
        zero memorizzando solo quelli > 0 (l'assenza di riga = "Assente").
        """
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO days(date, updated_at) VALUES(?, ?) "
            "ON CONFLICT(date) DO UPDATE SET updated_at=excluded.updated_at",
            (date, datetime.now().isoformat(timespec="seconds")),
        )
        cur.executemany(
            "INSERT INTO pollen(date, plant, level) VALUES(?, ?, ?) "
            "ON CONFLICT(date, plant) DO UPDATE SET level=excluded.level",
            [(date, p, lv) for p, lv in pollen.items()],
        )
        cur.execute("DELETE FROM symptoms WHERE date = ?", (date,))
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

    # --- Backup / ripristino -------------------------------------------------
    def backup_to(self, dest_path) -> None:
        """Salva una copia completa e coerente del database nel file indicato,
        usando l'API di backup di SQLite (sicura anche con il db in uso)."""
        dest = sqlite3.connect(str(dest_path))
        try:
            with dest:
                self.conn.backup(dest)
        finally:
            dest.close()

    def restore_from(self, src_path) -> None:
        """Sostituisce TUTTI i dati attuali con quelli del file indicato.

        Solleva ValueError se il file non è un backup valido dell'app. Dopo il
        ripristino riallinea lo schema, nel caso il backup provenga da una
        versione più vecchia.
        """
        src = sqlite3.connect(str(src_path))
        try:
            valid = src.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='days'"
            ).fetchone()
            if not valid:
                raise ValueError(
                    "Il file selezionato non è un backup di Pollini & Sintomi."
                )
            self.conn.commit()  # evita transazioni aperte sul target
            src.backup(self.conn)
        except sqlite3.DatabaseError as exc:
            raise ValueError("Il file selezionato non è un database valido.") from exc
        finally:
            src.close()
        self._migrate()

    def close(self) -> None:
        self.conn.close()
