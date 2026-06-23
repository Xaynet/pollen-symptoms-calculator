"""Precompilazione dei pollini tramite le API gratuite di Open-Meteo.

Open-Meteo (basato sui dati europei CAMS) espone solo alcuni pollini, che
mappiamo sulle piante usate dall'app:

    birch_pollen   -> betulla
    grass_pollen   -> graminacee
    mugwort_pollen -> assenzio
    olive_pollen   -> olivo
    ragweed_pollen -> ambrosia

Gli altri pollini della lista non sono coperti da nessuna fonte automatica e
restano da inserire a mano. I valori arrivano in granuli/m³ (media giornaliera)
e li convertiamo nei quattro livelli dell'app (Assente/Basso/Medio/Alto) con
soglie aerobiologiche approssimative, tarate per famiglia.

Usa solo la libreria standard (urllib): nessuna dipendenza aggiuntiva e nessuna
chiave API richiesta.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

# Pianta (chiave dell'app) -> variabile oraria di Open-Meteo
POLLEN_VARS = {
    "betulla": "birch_pollen",
    "graminacee": "grass_pollen",
    "assenzio": "mugwort_pollen",
    "olivo": "olive_pollen",
    "ambrosia": "ragweed_pollen",
}

# Le piante che questa fonte è in grado di precompilare.
COVERED_PLANTS = list(POLLEN_VARS.keys())

# Soglie in granuli/m³ (media giornaliera): (Basso, Medio, Alto).
# valore < Basso  -> 0 Assente
# valore < Medio  -> 1 Basso
# valore < Alto   -> 2 Medio
# valore >= Alto  -> 3 Alto
# Valori indicativi ispirati alle classi delle reti aerobiologiche; si possono
# ritoccare qui senza toccare il resto del codice.
THRESHOLDS = {
    "betulla": (1, 11, 51),
    "graminacee": (1, 6, 31),
    "assenzio": (1, 6, 26),
    "olivo": (1, 16, 81),
    "ambrosia": (1, 6, 21),
}

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_AIRQUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
_TIMEOUT = 12  # secondi


class OpenMeteoError(Exception):
    """Errore recuperabile da mostrare all'utente (rete, dati assenti, ecc.)."""


def _get_json(url: str, params: dict) -> dict:
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers={"User-Agent": "PolliniSintomi/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:  # rete assente / timeout / DNS
        raise OpenMeteoError(
            "Impossibile contattare Open-Meteo. Controlla la connessione a Internet."
        ) from exc
    except (ValueError, OSError) as exc:
        raise OpenMeteoError("Risposta non valida da Open-Meteo.") from exc


def geocode(city: str) -> tuple[float, float, str]:
    """Converte il nome di una località in (latitudine, longitudine, etichetta).

    Solleva OpenMeteoError se la località non viene trovata.
    """
    data = _get_json(
        _GEOCODE_URL,
        {"name": city.strip(), "count": 1, "language": "it", "format": "json"},
    )
    results = data.get("results") or []
    if not results:
        raise OpenMeteoError(f'Località "{city}" non trovata.')
    r = results[0]
    parts = [r.get("name")]
    if r.get("admin1"):
        parts.append(r["admin1"])
    if r.get("country"):
        parts.append(r["country"])
    label = ", ".join(p for p in parts if p)
    return float(r["latitude"]), float(r["longitude"]), label


def _to_level(plant: str, value: float) -> int:
    low, mid, high = THRESHOLDS[plant]
    if value < low:
        return 0
    if value < mid:
        return 1
    if value < high:
        return 2
    return 3


def fetch_pollen(lat: float, lon: float, date_iso: str) -> dict[str, int]:
    """Scarica i pollini per la data indicata e li converte in livelli 0..3.

    Restituisce {pianta: livello} solo per le piante coperte e per cui esistono
    dati. Solleva OpenMeteoError se per quella data non c'è alcun dato (ad es.
    date troppo lontane nel passato/futuro rispetto alla copertura del modello).
    """
    data = _get_json(
        _AIRQUALITY_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(POLLEN_VARS.values()),
            "start_date": date_iso,
            "end_date": date_iso,
            "timezone": "auto",
        },
    )
    hourly = data.get("hourly") or {}
    levels: dict[str, int] = {}
    for plant, var in POLLEN_VARS.items():
        series = hourly.get(var) or []
        valid = [v for v in series if v is not None]
        if not valid:
            continue
        daily_mean = sum(valid) / len(valid)
        levels[plant] = _to_level(plant, daily_mean)

    if not levels:
        raise OpenMeteoError(
            "Nessun dato sui pollini disponibile per questa data in questa zona."
        )
    return levels
