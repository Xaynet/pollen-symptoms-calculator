"""Palette e costanti di stile (solarpunk: verdi, gialli, bianchi)."""

# Colori base
BG = "#F4F9EE"            # bianco-crema di sfondo
SURFACE = "#FFFFFF"       # superfici/card
SURFACE_ALT = "#E9F4DA"   # superfici alternate (righe)
BORDER = "#C7E0A6"        # bordi tenui

GREEN = "#5BA845"         # verde primario
GREEN_DARK = "#2E6B2E"    # verde scuro (testo/accenti)
GREEN_HOVER = "#4C9239"   # verde hover
YELLOW = "#F2C811"        # giallo solare (accento)
YELLOW_HOVER = "#DDB60C"

TEXT = "#244018"          # testo principale (verde molto scuro)
TEXT_MUTED = "#6A7D5A"    # testo secondario

# Calendario: colore di un giorno NON compilato
DAY_EMPTY = "#FFFFFF"
DAY_EMPTY_TEXT = "#9AAE87"

# Gradiente di severità per i giorni compilati, indicizzato dal livello
# massimo di sintomo registrato in quel giorno (0 = nessun sintomo ... 5 = eccessivo).
SEVERITY_COLORS = [
    "#D7EFBC",  # 0 - nessun sintomo (verde tenue)
    "#C2E791",  # 1 - molto lieve
    "#EFE06A",  # 2 - tollerabile (giallo)
    "#F4C84B",  # 3 - fastidioso
    "#EFA13C",  # 4 - problematico (ambra)
    "#E2742B",  # 5 - eccessivo (arancio)
]

# Caratteri (famiglia + dimensioni)
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_H2 = (FONT_FAMILY, 16, "bold")
FONT_NORMAL = (FONT_FAMILY, 13)
FONT_SMALL = (FONT_FAMILY, 11)
FONT_DAY = (FONT_FAMILY, 14, "bold")


def severity_color(max_symptom_level: int) -> str:
    """Colore di sfondo per un giorno compilato in base al sintomo più intenso."""
    idx = max(0, min(max_symptom_level, len(SEVERITY_COLORS) - 1))
    return SEVERITY_COLORS[idx]
