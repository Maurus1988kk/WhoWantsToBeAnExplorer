# -*- coding: utf-8 -*-
"""I tre aiuti (50:50, stato confinante, bandiera): logica e icone originali
disegnate con le primitive di pygame."""

import math

import lingua

AIUTI = ("5050", "vicino", "bandiera")


def descrizione(nome):
    """Testo del suggerimento sopra l'icona dell'aiuto."""
    return lingua.t("aiuto_" + nome)


def didascalia(tipo):
    """Etichetta del vicino mostrato: confinante, paese più vicino, paese vicino."""
    if tipo in ("confinante", "vicino_isola", "vicino"):
        return lingua.t("didascalia_" + tipo)
    return lingua.t("didascalia_vicino")


# ---------------------------------------------------------------------------
# Logica
# ---------------------------------------------------------------------------
def usa_5050(partita):
    """Elimina due risposte sbagliate scelte a caso. Restituisce gli indici."""
    d = partita.domanda
    if not partita.aiuti["5050"]:
        return set()
    sbagliate = [i for i in range(4) if i != d.corretta and i not in d.eliminate]
    tolte = set(partita.rng.sample(sbagliate, 2))
    d.eliminate |= tolte
    partita.aiuti["5050"] = False
    return tolte


def scegli_vicino(stato, opzioni):
    """Sceglie il vicino da mostrare: il primo candidato (già ordinato per
    riconoscibilità) che NON sia tra le 4 opzioni; se sono tutti tra le
    opzioni, il primo. Mai lo stato misterioso stesso."""
    iso_opzioni = {s.iso for s in opzioni}
    candidati = [v for v in stato.vicini if v["iso"] != stato.iso]
    for v in candidati:
        if v["iso"] not in iso_opzioni:
            return v
    return candidati[0] if candidati else None


def usa_vicino(partita):
    d = partita.domanda
    if not partita.aiuti["vicino"]:
        return None
    d.vicino = scegli_vicino(d.stato, d.opzioni)
    partita.aiuti["vicino"] = False
    return d.vicino


def usa_bandiera(partita):
    d = partita.domanda
    if not partita.aiuti["bandiera"]:
        return False
    d.bandiera = True
    partita.aiuti["bandiera"] = False
    return True


def usa(partita, nome):
    if nome == "5050":
        return usa_5050(partita)
    if nome == "vicino":
        return usa_vicino(partita)
    if nome == "bandiera":
        return usa_bandiera(partita)
    raise ValueError(nome)


# ---------------------------------------------------------------------------
# Icone (disegnate, nessuna immagine esterna)
# ---------------------------------------------------------------------------
def _blob(cx, cy, r, semi, fase=0.0, punti=28):
    """Una piccola "sagoma" irregolare chiusa attorno a (cx, cy)."""
    pts = []
    for i in range(punti):
        a = 2 * math.pi * i / punti
        k = 1.0
        for j, (amp, freq) in enumerate(semi):
            k += amp * math.sin(freq * a + fase + j)
        pts.append((cx + r * k * math.cos(a), cy + r * k * math.sin(a) * 1.15))
    return pts


def disegna_icona(superficie, nome, centro, raggio, colore, colore2, font):
    import pygame
    cx, cy = centro
    if nome == "5050":
        img = font.render("50:50", True, colore)
        superficie.blit(img, img.get_rect(center=(cx, cy + 1)))
    elif nome == "vicino":
        r = raggio * 0.36
        sx = raggio * 0.30
        pygame.draw.polygon(superficie, colore2, _blob(cx + sx, cy + 2, r, [(0.18, 3), (0.1, 5)], 1.3))
        pygame.draw.polygon(superficie, colore, _blob(cx - sx, cy - 2, r, [(0.2, 2), (0.12, 5)], 0.2))
    elif nome == "bandiera":
        # asta
        x0 = cx - raggio * 0.32
        pygame.draw.line(superficie, colore, (x0, cy - raggio * 0.48), (x0, cy + raggio * 0.5), 4)
        pygame.draw.circle(superficie, colore, (int(x0), int(cy - raggio * 0.5)), 4)
        # drappo ondulato a tre bande
        w, h = raggio * 0.75, raggio * 0.5
        top = cy - raggio * 0.42
        bande = [colore2, colore, colore2]
        for b in range(3):
            pts_a, pts_b = [], []
            for i in range(13):
                t = i / 12
                x = x0 + 2 + t * w
                onda = math.sin(t * math.pi * 2) * h * 0.08
                pts_a.append((x, top + b * h / 3 + onda))
                pts_b.append((x, top + (b + 1) * h / 3 + onda))
            pygame.draw.polygon(superficie, bande[b], pts_a + pts_b[::-1])


def disegna_barra(superficie, centro, raggio, colore):
    """Croce sopra un aiuto già usato."""
    import pygame
    cx, cy = centro
    d = raggio * 0.62
    pygame.draw.line(superficie, colore, (cx - d, cy - d), (cx + d, cy + d), 7)
    pygame.draw.line(superficie, colore, (cx - d, cy + d), (cx + d, cy - d), 7)
