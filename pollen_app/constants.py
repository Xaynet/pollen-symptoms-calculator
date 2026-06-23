"""Costanti di dominio: piante, sintomi e relativi livelli.

I valori testuali (chiavi) sono usati anche come identificatori nel
database, quindi NON vanno modificati una volta raccolti dei dati.
"""

# --- Piante monitorate (ordine come fornito dall'utente) ---------------------
PLANTS = [
    "aceracee",
    "betulla",
    "chenopodiacee/amarantacee",
    "assenzio",
    "ambrosia",
    "nocciolo",
    "ontano",
    "carpino",
    "carpino nero",
    "cupressacee/taxacee",
    "castagno",
    "faggio",
    "quercia",
    "graminacee",
    "olivo",
    "orno",
    "ligustro",
    "frassino",
    "frassino comune",
    "pinacee",
    "platanacee",
    "poligonacee",
    "pioppo",
    "salice",
    "ulmacee",
    "urticacee",
]

# --- Livelli di polline (indice = intensità) ---------------------------------
POLLEN_LEVELS = ["Assente", "Basso", "Medio", "Alto"]
POLLEN_LEVEL_INDEX = {name: i for i, name in enumerate(POLLEN_LEVELS)}

# --- Polveri / particolato (stessi 4 livelli dei pollini) --------------------
# Le chiavi sono usate come identificatori nel database: non modificarle.
PARTICULATES = ["pm10", "pm2.5"]
PARTICULATE_NAMES = {"pm10": "PM10", "pm2.5": "PM2.5"}


def particulate_name(key: str) -> str:
    return PARTICULATE_NAMES.get(key, key)

# --- Sintomi monitorati ------------------------------------------------------
SYMPTOMS = [
    "tosse",
    "gonfiore occhi",
    "gonfiore labbra",
    "prurito bocca",
    "prurito naso",
    "starnuti",
    "gonfiore mani",
    "muco",
    "stanchezza",
    "mal di testa",
    "difficoltà respiratoria",
    "sibilo",
]

# --- Livelli di sintomo (indice = intensità) ---------------------------------
SYMPTOM_LEVELS = [
    "Assente",
    "Molto lieve",
    "Tollerabile",
    "Fastidioso",
    "Problematico",
    "Eccessivo",
]
SYMPTOM_LEVEL_INDEX = {name: i for i, name in enumerate(SYMPTOM_LEVELS)}

# Massimo punteggio sintomatico in un giorno (per normalizzazioni grafiche)
MAX_SYMPTOM_LEVEL = len(SYMPTOM_LEVELS) - 1


def display_name(key: str) -> str:
    """Restituisce una versione leggibile (prima lettera maiuscola)
    di una chiave pianta/sintomo, gestendo anche i nomi con '/'."""
    return "/".join(part[:1].upper() + part[1:] for part in key.split("/"))
