"""Precompilazione di pollini e polveri tramite le API gratuite di Open-Meteo.

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

# Polveri / particolato (chiave dell'app -> variabile oraria di Open-Meteo).
PARTICULATE_VARS = {
    "pm10": "pm10",
    "pm2.5": "pm2_5",
}
COVERED_PARTICULATES = list(PARTICULATE_VARS.keys())

# Tutte le soglie hanno forma (Basso, Medio, Alto):
#   valore < Basso  -> 0 Assente   |  valore < Medio -> 1 Basso
#   valore < Alto   -> 2 Medio     |  valore >= Alto -> 3 Alto

# Pollini: granuli/m³ (media giornaliera). Valori indicativi ispirati alle
# classi delle reti aerobiologiche.
THRESHOLDS = {
    "betulla": (1, 11, 51),
    "graminacee": (1, 6, 31),
    "assenzio": (1, 6, 26),
    "olivo": (1, 16, 81),
    "ambrosia": (1, 6, 21),
}

# Particolato: µg/m³ (media giornaliera). Soglie ispirate all'indice europeo
# di qualità dell'aria (EEA); per il PM10 50 µg/m³ è il valore limite giornaliero.
PARTICULATE_THRESHOLDS = {
    "pm10": (10, 25, 50),
    "pm2.5": (5, 15, 25),
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


def _to_level(value: float, thresholds: tuple[float, float, float]) -> int:
    low, mid, high = thresholds
    if value < low:
        return 0
    if value < mid:
        return 1
    if value < high:
        return 2
    return 3


def _daily_levels(hourly: dict, var_map: dict, threshold_map: dict) -> dict[str, int]:
    """Converte le serie orarie di Open-Meteo in livelli 0..3 (media del giorno),
    saltando le voci prive di dati."""
    levels: dict[str, int] = {}
    for key, var in var_map.items():
        series = hourly.get(var) or []
        valid = [v for v in series if v is not None]
        if not valid:
            continue
        daily_mean = sum(valid) / len(valid)
        levels[key] = _to_level(daily_mean, threshold_map[key])
    return levels


def fetch_air(lat: float, lon: float, date_iso: str) -> dict[str, dict[str, int]]:
    """Scarica pollini e polveri per la data indicata, convertiti in livelli 0..3.

    Restituisce {"pollen": {pianta: livello}, "particulate": {tipo: livello}},
    con solo le voci per cui esistono dati. Solleva OpenMeteoError se per quella
    data non c'è alcun dato (ad es. date troppo lontane nel passato/futuro
    rispetto alla copertura del modello).
    """
    data = _get_json(
        _AIRQUALITY_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join([*POLLEN_VARS.values(), *PARTICULATE_VARS.values()]),
            "start_date": date_iso,
            "end_date": date_iso,
            "timezone": "auto",
        },
    )
    hourly = data.get("hourly") or {}
    result = {
        "pollen": _daily_levels(hourly, POLLEN_VARS, THRESHOLDS),
        "particulate": _daily_levels(hourly, PARTICULATE_VARS, PARTICULATE_THRESHOLDS),
    }
    if not result["pollen"] and not result["particulate"]:
        raise OpenMeteoError(
            "Nessun dato su pollini o polveri disponibile per questa data in questa zona."
        )
    return result
