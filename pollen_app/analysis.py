"""Analisi dei dati: individua i pollini più probabilmente responsabili
dei sintomi, correlando il livello di ciascuna pianta con la severità
sintomatica giornaliera.

Nessuna dipendenza esterna: la correlazione di Pearson è calcolata a mano
per mantenere l'app leggera.
"""

from math import sqrt

from .constants import (
    PARTICULATES,
    PLANTS,
    SYMPTOMS,
    display_name,
    particulate_name,
)

# Soglie
MIN_DAYS = 5            # giorni minimi per un'analisi sensata
HIGH_POLLEN = 2         # livello >= Medio considerato "alto"


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    syy = sum(y * y for y in ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    num = n * sxy - sx * sy
    den = sqrt((n * sxx - sx * sx) * (n * syy - sy * sy))
    if den == 0:
        return None  # nessuna variazione (es. pianta sempre "Assente")
    return num / den


def analyze(data: dict[str, dict]) -> dict:
    """Restituisce un dizionario con i risultati dell'analisi.

    `data` è il formato prodotto da Database.load_all().
    """
    dates = sorted(data.keys())
    n_days = len(dates)

    if n_days < MIN_DAYS:
        return {
            "enough_data": False,
            "n_days": n_days,
            "min_days": MIN_DAYS,
        }

    # Severità sintomatica giornaliera = somma dei livelli dei sintomi.
    day_total = {d: sum(data[d]["symptoms"].values()) for d in dates}

    plant_items = [(p, display_name(p)) for p in PLANTS]
    suspects = _rank_suspects(
        _category_results(dates, day_total, data, "pollen", plant_items)
    )

    dust_items = [(k, particulate_name(k)) for k in PARTICULATES]
    particulate_suspects = _rank_suspects(
        _category_results(dates, day_total, data, "particulate", dust_items)
    )

    # Sintomi più frequenti/gravi (giorni con livello >= Fastidioso).
    symptom_stats = []
    for sym in SYMPTOMS:
        levels = [data[d]["symptoms"].get(sym, 0) for d in dates]
        present = [lv for lv in levels if lv > 0]
        if not present:
            continue
        symptom_stats.append(
            {
                "symptom": sym,
                "name": display_name(sym),
                "days_present": len(present),
                "days_severe": sum(1 for lv in levels if lv >= 3),
                "avg_level": sum(present) / len(present),
                "max_level": max(present),
            }
        )
    symptom_stats.sort(key=lambda s: (s["days_severe"], s["avg_level"]), reverse=True)

    return {
        "enough_data": True,
        "n_days": n_days,
        "suspects": suspects,
        "particulate_suspects": particulate_suspects,
        "symptom_stats": symptom_stats,
    }


def _category_results(dates, day_total, data, category, items) -> list[dict]:
    """Correla il livello di ciascuna voce di una categoria (pollini o polveri)
    con la severità sintomatica giornaliera, usando SOLO i giorni in cui la voce
    è stata effettivamente valutata (riga presente)."""
    results = []
    for key, name in items:
        pairs = [
            (data[d][category][key], day_total[d])
            for d in dates
            if key in data[d].get(category, {})
        ]
        if not pairs:
            continue  # mai valutata: niente da dire
        levels = [lv for lv, _ in pairs]
        totals = [t for _, t in pairs]
        if all(lv == 0 for lv in levels):
            continue  # valutata ma sempre assente

        corr = _pearson([float(x) for x in levels], [float(y) for y in totals])
        high_totals = [t for lv, t in pairs if lv >= HIGH_POLLEN]
        low_totals = [t for lv, t in pairs if lv < HIGH_POLLEN]
        avg_high = sum(high_totals) / len(high_totals) if high_totals else None
        avg_low = sum(low_totals) / len(low_totals) if low_totals else None
        delta = (avg_high - avg_low) if (avg_high is not None and avg_low is not None) else None

        results.append(
            {
                "key": key,
                "name": name,
                "corr": corr,
                "avg_high": avg_high,
                "avg_low": avg_low,
                "delta": delta,
                "days_high": len(high_totals),
                "days_recorded": sum(1 for lv in levels if lv > 0),
                "days_assessed": len(levels),
            }
        )
    return results


def _rank_suspects(results: list[dict]) -> list[dict]:
    """Tiene solo le voci con un segnale positivo e le ordina: prima per
    correlazione (se disponibile), poi per aumento di severità."""
    def score(r):
        c = r["corr"] if r["corr"] is not None else -2
        d = r["delta"] if r["delta"] is not None else 0
        return (c, d)

    return sorted(
        [r for r in results if (r["corr"] or 0) > 0 or (r["delta"] or 0) > 0],
        key=score,
        reverse=True,
    )


def correlation_label(corr: float | None) -> str:
    """Etichetta qualitativa per un coefficiente di correlazione."""
    if corr is None:
        return "n/d"
    a = abs(corr)
    if a >= 0.7:
        return "forte"
    if a >= 0.4:
        return "moderata"
    if a >= 0.2:
        return "debole"
    return "trascurabile"


def build_suggestions(result: dict) -> list[str]:
    """Genera frasi di suggerimento leggibili a partire dall'analisi."""
    if not result.get("enough_data"):
        mancanti = result["min_days"] - result["n_days"]
        return [
            f"Servono più dati per un'analisi affidabile: hai compilato "
            f"{result['n_days']} giorni su {result['min_days']} consigliati "
            f"(ancora {mancanti}). Continua a registrare ogni giorno!"
        ]

    msgs: list[str] = []
    suspects = result["suspects"]
    if not suspects:
        msgs.append(
            "Per ora non emerge una relazione chiara tra i pollini registrati "
            "e i tuoi sintomi. Continua a raccogliere dati: con più giornate "
            "i pattern diventeranno evidenti."
        )
    else:
        msgs.append("Pollini più probabilmente responsabili dei tuoi sintomi:")
        for i, r in enumerate(suspects[:5], start=1):
            parts = [f"{i}. {r['name']}"]
            if r["corr"] is not None:
                parts.append(
                    f"correlazione {correlation_label(r['corr'])} ({r['corr']:+.2f})"
                )
            if r["delta"] is not None and r["avg_high"] is not None:
                parts.append(
                    f"sintomi medi {r['avg_high']:.1f} nei giorni con polline alto "
                    f"vs {r['avg_low']:.1f} negli altri"
                )
            msgs.append("   " + " — ".join(parts))

    dust = result.get("particulate_suspects") or []
    if dust:
        d0 = dust[0]
        extra = (
            f" (correlazione {correlation_label(d0['corr'])} {d0['corr']:+.2f})"
            if d0["corr"] is not None else ""
        )
        msgs.append(
            f"Tra le polveri, la più legata ai tuoi sintomi è {d0['name']}{extra}."
        )

    stats = result["symptom_stats"]
    if stats:
        top = stats[0]
        msgs.append(
            f"Sintomo più impattante: {top['name']} "
            f"(grave in {top['days_severe']} giorni, intensità media "
            f"{top['avg_level']:.1f})."
        )

    msgs.append(
        "Nota: la correlazione non implica causa certa. Usa questi spunti "
        "per parlarne con il tuo medico/allergologo."
    )
    return msgs
