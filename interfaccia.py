# -*- coding: utf-8 -*-
"""Grafica e schermate del gioco. Tutto viene disegnato su una tela logica
1920x1080 (config.LARGHEZZA x config.ALTEZZA) che main.py scala sulla finestra."""

import math
import random

import pygame

import aiuti as A
import config as C
import dati as D
import lingua as L
from partita import LETTERE, Partita


def T(chiave, **valori):
    """Etichetta tradotta "pigra": il testo si calcola al momento del disegno,
    così i pulsanti seguono subito il cambio di lingua."""
    return lambda: L.t(chiave, **valori)

# ---------------------------------------------------------------------------
# Testo
# ---------------------------------------------------------------------------
_FILE_FONT = {
    "regular": "Montserrat-Regular.ttf",
    "medium": "Montserrat-Medium.ttf",
    "semibold": "Montserrat-SemiBold.ttf",
    "bold": "Montserrat-Bold.ttf",
    "extrabold": "Montserrat-ExtraBold.ttf",
}
_cache_font = {}
_cache_testo = {}


def font(dim, peso="semibold"):
    """Font Montserrat (OFL); se manca, il font predefinito di pygame."""
    chiave = (dim, peso)
    if chiave not in _cache_font:
        try:
            _cache_font[chiave] = pygame.font.Font(C.asset("font", _FILE_FONT[peso]), dim)
        except Exception:
            _cache_font[chiave] = pygame.font.Font(None, int(dim * 1.35))
    return _cache_font[chiave]


def render(s, dim, peso="semibold", colore=C.TESTO):
    chiave = (s, dim, peso, colore)
    img = _cache_testo.get(chiave)
    if img is None:
        if len(_cache_testo) > 3000:
            _cache_testo.clear()
        img = font(dim, peso).render(s, True, colore)
        _cache_testo[chiave] = img
    return img


def scrivi(sup, s, dim, pos, colore=C.TESTO, peso="semibold", ancora="center", ombra=True, alpha=255):
    img = render(s, dim, peso, colore)
    r = img.get_rect(**{ancora: (int(pos[0]), int(pos[1]))})
    if ombra:
        sh = render(s, dim, peso, (0, 0, 0))
        sh.set_alpha(min(alpha, 160))
        sup.blit(sh, r.move(2, 3))
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    sup.blit(img, r)
    return r


def scrivi_contornato(sup, s, dim, pos, colore=C.BIANCO, contorno=(0, 0, 0), peso="bold", ancora="center"):
    img = render(s, dim, peso, colore)
    nero = render(s, dim, peso, contorno)
    r = img.get_rect(**{ancora: (int(pos[0]), int(pos[1]))})
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            if dx or dy:
                sup.blit(nero, r.move(dx, dy))
    sup.blit(img, r)
    return r


def dimensione_adatta(s, larghezza, dim, peso="semibold", minimo=16):
    while dim > minimo and font(dim, peso).size(s)[0] > larghezza:
        dim -= 2
    return dim


def a_capo(s, dim, peso, larghezza):
    parole = s.split()
    righe, riga = [], ""
    for p in parole:
        prova = (riga + " " + p).strip()
        if font(dim, peso).size(prova)[0] <= larghezza or not riga:
            riga = prova
        else:
            righe.append(riga)
            riga = p
    if riga:
        righe.append(riga)
    return righe


def scrivi_paragrafo(sup, s, dim, x, y, larghezza, colore=C.TESTO, peso="medium", interlinea=1.35, ancora="left"):
    for riga in a_capo(s, dim, peso, larghezza):
        if ancora == "center":
            scrivi(sup, riga, dim, (x + larghezza // 2, y), colore, peso, ancora="midtop", ombra=False)
        else:
            scrivi(sup, riga, dim, (x, y), colore, peso, ancora="topleft", ombra=False)
        y += int(dim * interlinea)
    return y


# ---------------------------------------------------------------------------
# Forme e sfondi
# ---------------------------------------------------------------------------
def mescola(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def crea_sfondo(w=C.LARGHEZZA, h=C.ALTEZZA):
    """Studio notturno: gradiente blu notte, bagliore centrale e una rosa dei
    venti appena accennata."""
    sup = pygame.Surface((w, h))
    alto, medio, basso = (3, 6, 18), (10, 22, 54), (2, 4, 12)
    for y in range(h):
        t = y / (h - 1)
        c = mescola(alto, medio, t / 0.55) if t < 0.55 else mescola(medio, basso, (t - 0.55) / 0.45)
        pygame.draw.line(sup, c, (0, y), (w, y))
    strato = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = int(w * 0.39), int(h * 0.45)
    for r in range(760, 0, -24):
        a = int(10 * (1 - r / 760) ** 1.6)
        pygame.draw.circle(strato, (60, 110, 220, a), (cx, cy), r)
    sup.blit(strato, (0, 0))
    rosa = pygame.Surface((w, h), pygame.SRCALPHA)
    R = int(h * 0.6)
    col = (120, 160, 230)
    for k, a in ((1.0, 16), (0.82, 12), (0.5, 10)):
        pygame.draw.circle(rosa, (*col, a), (cx, cy), int(R * k), 2)
    for i in range(72):
        ang = math.radians(i * 5)
        l1 = R * (0.95 if i % 2 else 0.9)
        pygame.draw.line(rosa, (*col, 14), (cx + l1 * math.sin(ang), cy - l1 * math.cos(ang)),
                         (cx + R * math.sin(ang), cy - R * math.cos(ang)), 2)
    for i in range(16):
        ang = math.radians(i * 22.5)
        pygame.draw.line(rosa, (*col, 9), (cx, cy), (cx + R * 0.82 * math.sin(ang), cy - R * 0.82 * math.cos(ang)), 1)
    for i in range(4):
        ang = math.radians(i * 90)
        punta = (cx + R * 0.78 * math.sin(ang), cy - R * 0.78 * math.cos(ang))
        l = (cx + 40 * math.sin(ang - math.pi / 2), cy - 40 * math.cos(ang - math.pi / 2))
        r_ = (cx + 40 * math.sin(ang + math.pi / 2), cy - 40 * math.cos(ang + math.pi / 2))
        pygame.draw.polygon(rosa, (*col, 7), [l, punta, r_])
    sup.blit(rosa, (0, 0))
    return sup


def disegna_rosa(sup, centro, R, angolo=0.0):
    """Emblema: rosa dei venti a 8 punte, nord dorato."""
    cx, cy = centro

    def punta(ang, lung, larg, colore):
        a = math.radians(ang + angolo)
        p = (cx + lung * math.sin(a), cy - lung * math.cos(a))
        l = (cx + larg * math.sin(a - math.pi / 2), cy - larg * math.cos(a - math.pi / 2))
        r = (cx + larg * math.sin(a + math.pi / 2), cy - larg * math.cos(a + math.pi / 2))
        pygame.draw.polygon(sup, colore, [l, p, r])
    pygame.draw.circle(sup, (90, 130, 200), (int(cx), int(cy)), int(R * 1.02), 3)
    for i in range(36):
        a = math.radians(i * 10 + angolo)
        r1 = R * (0.88 if i % 3 else 0.82)
        pygame.draw.line(sup, (90, 130, 200), (cx + r1 * math.sin(a), cy - r1 * math.cos(a)),
                         (cx + R * math.sin(a), cy - R * math.cos(a)), 2)
    for ang in (45, 135, 225, 315):
        punta(ang, R * 0.62, R * 0.13, (110, 150, 215))
    for ang in (90, 180, 270):
        punta(ang, R * 0.84, R * 0.17, (235, 240, 250))
    punta(0, R * 0.9, R * 0.17, C.ORO)
    pygame.draw.circle(sup, C.BLU_NOTTE, (int(cx), int(cy)), int(R * 0.1))
    pygame.draw.circle(sup, C.ORO, (int(cx), int(cy)), int(R * 0.1), 3)


_cache_pannelli = {}


def pannello(sup, rect, bordo=C.BLU_BORDO, riempimento=(8, 16, 40), raggio=18, alpha=235, bagliore=True, spessore=2):
    """Riquadro arrotondato con bordo luminoso (le superfici sono messe in cache)."""
    rect = pygame.Rect(rect)
    chiave = (rect.size, tuple(bordo), tuple(riempimento), raggio, alpha, bagliore, spessore)
    strato = _cache_pannelli.get(chiave)
    if strato is None:
        if len(_cache_pannelli) > 300:
            _cache_pannelli.clear()
        strato = _crea_pannello(rect.size, bordo, riempimento, raggio, alpha, bagliore, spessore)
        _cache_pannelli[chiave] = strato
    sup.blit(strato, (rect.x - 20, rect.y - 20))


def _crea_pannello(dim, bordo, riempimento, raggio, alpha, bagliore, spessore):
    rect = pygame.Rect((0, 0), dim)
    strato = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
    r = pygame.Rect(20, 20, rect.width, rect.height)
    if bagliore:
        for i, a in ((10, 18), (6, 30), (3, 55)):
            pygame.draw.rect(strato, (*bordo, a), r.inflate(i * 2, i * 2), width=3, border_radius=raggio + i)
    pygame.draw.rect(strato, (*riempimento, alpha), r, border_radius=raggio)
    pygame.draw.rect(strato, (*bordo, 255), r, width=spessore, border_radius=raggio)
    return strato


def poligono_esagono(rect):
    x, y, w, h = rect
    k = h * 0.5
    return [(x + k, y), (x + w - k, y), (x + w, y + h / 2), (x + w - k, y + h), (x + k, y + h), (x, y + h / 2)]


_STILI_CASELLA = {
    # stato: (riempimento alto, riempimento basso, bordo, testo, lettera)
    "normale": ((16, 32, 76), (6, 12, 34), C.BLU_BORDO, C.TESTO, C.ORO),
    "hover": ((30, 56, 120), (10, 22, 58), C.BLU_CHIARO, C.BIANCO, C.ORO_CHIARO),
    "selezionata": ((250, 186, 70), (205, 120, 20), C.ORO_CHIARO, (20, 14, 4), (60, 30, 0)),
    "giusta": ((70, 205, 120), (20, 120, 60), C.VERDE_CHIARO, (4, 24, 10), (4, 40, 16)),
    "sbagliata": ((225, 80, 70), (140, 26, 22), C.ROSSO_CHIARO, C.BIANCO, (60, 0, 0)),
    "eliminata": ((10, 16, 34), (5, 8, 20), (40, 56, 90), (60, 70, 95), (60, 70, 95)),
}
_cache_caselle = {}


def superficie_casella(w, h, stato):
    """Riquadro a esagono allungato con bordo luminoso (prerenderizzato)."""
    chiave = (w, h, stato)
    if chiave in _cache_caselle:
        return _cache_caselle[chiave]
    m = 14
    sup = pygame.Surface((w + 2 * m, h + 2 * m), pygame.SRCALPHA)
    alto, basso, bordo, _, _ = _STILI_CASELLA[stato]
    poly = poligono_esagono((m, m, w, h))
    # riempimento a gradiente: maschera esagonale x gradiente verticale
    grad = pygame.Surface((w + 2 * m, h + 2 * m), pygame.SRCALPHA)
    for y in range(h):
        pygame.draw.line(grad, (*mescola(alto, basso, y / max(1, h - 1)), 255), (0, m + y), (w + 2 * m, m + y))
    maschera = pygame.Surface((w + 2 * m, h + 2 * m), pygame.SRCALPHA)
    pygame.draw.polygon(maschera, (255, 255, 255, 255), poly)
    grad.blit(maschera, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    if stato != "eliminata":
        for spess, a in ((12, 22), (8, 40), (5, 70)):
            pygame.draw.polygon(sup, (*bordo, a), poly, spess)
    sup.blit(grad, (0, 0))
    pygame.draw.polygon(sup, (*bordo, 255), poly, 3)
    # riflesso superiore
    rifl = pygame.Surface((w + 2 * m, h + 2 * m), pygame.SRCALPHA)
    pygame.draw.polygon(rifl, (255, 255, 255, 18), poligono_esagono((m + 6, m + 4, w - 12, h * 0.42)))
    sup.blit(rifl, (0, 0))
    _cache_caselle[chiave] = sup
    return sup


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------
class Pulsante:
    """testo: una stringa oppure una funzione senza argomenti (vedi T())."""

    def __init__(self, rect, testo, dim=32, attivo=True, colore=C.BLU_BORDO, evidenziato=False):
        self.rect = pygame.Rect(rect)
        self.testo = testo
        self.dim = dim
        self.attivo = attivo
        self.colore = colore
        self.evidenziato = evidenziato
        self.hover = False

    def aggiorna(self, pos):
        self.hover = self.attivo and self.rect.collidepoint(pos)

    def clic(self, pos):
        return self.attivo and self.rect.collidepoint(pos)

    def disegna(self, sup):
        if not self.attivo:
            bordo, fondo, testo = (50, 62, 90), (10, 14, 28), (90, 100, 125)
        elif self.evidenziato:
            bordo = C.ORO_CHIARO if self.hover else C.ORO
            fondo = (70, 50, 12) if self.hover else (44, 30, 8)
            testo = C.BIANCO
        else:
            bordo = C.BLU_CHIARO if self.hover else self.colore
            fondo = (28, 52, 110) if self.hover else (12, 24, 58)
            testo = C.BIANCO
        pannello(sup, self.rect, bordo, fondo, raggio=self.rect.height // 2, bagliore=self.attivo)
        etichetta = self.testo() if callable(self.testo) else self.testo
        dim = dimensione_adatta(etichetta, self.rect.width - 30, self.dim, "bold")
        scrivi(sup, etichetta, dim, self.rect.center, testo, "bold")


class Interruttore:
    """Interruttore sì/no per le impostazioni."""

    def __init__(self, rect, valore):
        self.rect = pygame.Rect(rect)
        self.valore = valore
        self.hover = False

    def aggiorna(self, pos):
        self.hover = self.rect.collidepoint(pos)

    def clic(self, pos):
        if self.rect.collidepoint(pos):
            self.valore = not self.valore
            return True
        return False

    def disegna(self, sup):
        r = self.rect
        col = C.VERDE if self.valore else (50, 60, 85)
        pygame.draw.rect(sup, col, r, border_radius=r.height // 2)
        pygame.draw.rect(sup, C.BLU_CHIARO if self.hover else C.BLU_BORDO, r, 2, border_radius=r.height // 2)
        kx = r.right - r.height // 2 if self.valore else r.left + r.height // 2
        pygame.draw.circle(sup, C.BIANCO, (kx, r.centery), r.height // 2 - 5)
        scrivi(sup, L.t("interruttore_si" if self.valore else "interruttore_no"), 20,
               (r.left + r.width * (0.32 if self.valore else 0.68), r.centery), C.BIANCO, "bold", ombra=False)


def pulsanti_lingua(x, y, larghezza=175, altezza=54, passo=190):
    """Un pulsante per lingua ("Italiano", "English"), affiancati da (x, y)."""
    return {codice: Pulsante((x + i * passo, y, larghezza, altezza), L.NOMI_LINGUE[codice], 22)
            for i, codice in enumerate(L.LINGUE)}


def disegna_pulsanti_lingua(sup, pulsanti, mouse):
    for codice, b in pulsanti.items():
        b.evidenziato = codice == L.corrente()
        b.aggiorna(mouse)
        b.disegna(sup)


def icona_audio(sup, centro, r, attivo, hover):
    cx, cy = centro
    col = C.BLU_CHIARO if hover else C.BLU_BORDO
    pygame.draw.circle(sup, (12, 24, 58), centro, r)
    pygame.draw.circle(sup, col, centro, r, 3)
    s = r * 0.32
    pts = [(cx - s * 1.4, cy - s * 0.55), (cx - s * 0.6, cy - s * 0.55), (cx + s * 0.3, cy - s * 1.3),
           (cx + s * 0.3, cy + s * 1.3), (cx - s * 0.6, cy + s * 0.55), (cx - s * 1.4, cy + s * 0.55)]
    pygame.draw.polygon(sup, C.BIANCO, pts)
    if attivo:
        for k in (1.0, 1.6):
            rr = pygame.Rect(0, 0, s * 2 * k, s * 2.4 * k)
            rr.center = (cx + s * 0.3, cy)
            pygame.draw.arc(sup, C.BIANCO, rr, -0.9, 0.9, 3)
    else:
        pygame.draw.line(sup, C.ROSSO_CHIARO, (cx + s * 0.8, cy - s * 0.7), (cx + s * 2.0, cy + s * 0.7), 4)
        pygame.draw.line(sup, C.ROSSO_CHIARO, (cx + s * 0.8, cy + s * 0.7), (cx + s * 2.0, cy - s * 0.7), 4)


def segno_esito(sup, centro, r, esito):
    """Piccolo simbolo disegnato: spunta (giusta), croce (sbagliata), clessidra (tempo), bandierina (ritiro)."""
    cx, cy = centro
    if esito == "giusta":
        pygame.draw.circle(sup, C.VERDE, centro, r)
        pygame.draw.lines(sup, C.BIANCO, False, [(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.4)], 4)
    elif esito in ("sbagliata", "tempo"):
        pygame.draw.circle(sup, C.ROSSO, centro, r)
        if esito == "tempo":
            pygame.draw.polygon(sup, C.BIANCO, [(cx - r * 0.4, cy - r * 0.5), (cx + r * 0.4, cy - r * 0.5), (cx, cy)])
            pygame.draw.polygon(sup, C.BIANCO, [(cx - r * 0.4, cy + r * 0.5), (cx + r * 0.4, cy + r * 0.5), (cx, cy)])
        else:
            d = r * 0.4
            pygame.draw.line(sup, C.BIANCO, (cx - d, cy - d), (cx + d, cy + d), 4)
            pygame.draw.line(sup, C.BIANCO, (cx - d, cy + d), (cx + d, cy - d), 4)
    else:
        pygame.draw.circle(sup, C.ORO, centro, r)
        pygame.draw.line(sup, (40, 26, 0), (cx - r * 0.3, cy - r * 0.5), (cx - r * 0.3, cy + r * 0.55), 3)
        pygame.draw.polygon(sup, (40, 26, 0), [(cx - r * 0.3, cy - r * 0.5), (cx + r * 0.5, cy - r * 0.25), (cx - r * 0.3, cy)])


# ---------------------------------------------------------------------------
# Scala dei gradi (colonna laterale)
# ---------------------------------------------------------------------------
def disegna_scala(sup, rect, livello_attuale, evidenzia, finale=None, tempo=0.0):
    """livello_attuale: risposte giuste finora; evidenzia: grado in palio;
    finale: grado conquistato a fine partita (se c'è)."""
    rect = pygame.Rect(rect)
    pannello(sup, rect, (60, 96, 170), (6, 12, 30), raggio=22, alpha=220)
    scrivi(sup, L.t("gradi_esploratore"), 24, (rect.centerx, rect.y + 36), C.ORO, "extrabold")
    alto = rect.y + 70
    h = (rect.height - 104) / C.NUM_DOMANDE
    for liv in range(C.NUM_DOMANDE, 0, -1):
        titolo, miglia = C.titolo_grado(liv), C.miglia_grado(liv)
        y = alto + (C.NUM_DOMANDE - liv) * h
        riga = pygame.Rect(rect.x + 14, int(y) + 3, rect.width - 28, int(h) - 6)
        soglia = liv in C.SOGLIE
        if finale is not None and liv == finale and finale > 0:
            pulsa = 0.5 + 0.5 * math.sin(tempo * 4)
            pygame.draw.rect(sup, mescola((40, 140, 80), (80, 200, 120), pulsa), riga, border_radius=riga.height // 2)
            col_t, col_n = C.BIANCO, C.BIANCO
        elif liv == evidenzia and finale is None:
            pulsa = 0.5 + 0.5 * math.sin(tempo * 3)
            pygame.draw.rect(sup, mescola((200, 130, 20), (250, 190, 70), pulsa), riga, border_radius=riga.height // 2)
            pygame.draw.rect(sup, C.ORO_CHIARO, riga, 2, border_radius=riga.height // 2)
            col_t, col_n = (24, 14, 0), (24, 14, 0)
        elif liv <= livello_attuale:
            col_t, col_n = (130, 215, 160), (110, 190, 140)
        elif soglia:
            col_t, col_n = C.BIANCO, C.ORO_CHIARO
        else:
            col_t, col_n = (150, 175, 220), (110, 135, 180)
        peso = "extrabold" if soglia else "semibold"
        scrivi(sup, f"{liv}", 22, (riga.x + 30, riga.centery), col_n, "bold", ombra=False)
        if soglia:
            d = 7
            px = riga.x + 58
            pygame.draw.polygon(sup, col_n, [(px, riga.centery - d), (px + d, riga.centery), (px, riga.centery + d), (px - d, riga.centery)])
        dim = dimensione_adatta(titolo, 190, 21, peso)
        scrivi(sup, titolo, dim, (riga.x + 72, riga.centery), col_t, peso, ancora="midleft", ombra=False)
        scrivi(sup, C.formatta_miglia(miglia), 19, (riga.right - 14, riga.centery), col_n, "semibold",
               ancora="midright", ombra=False)
    legenda = L.t("legenda_scala")
    scrivi(sup, legenda, dimensione_adatta(legenda, rect.width - 24, 15, "medium", 11),
           (rect.centerx, rect.bottom - 18), C.TESTO_TENUE, "medium", ombra=False)


# ---------------------------------------------------------------------------
# Schermate
# ---------------------------------------------------------------------------
class Schermata:
    def __init__(self, app):
        self.app = app

    def entra(self):
        pass

    def evento(self, ev, pos):
        pass

    def aggiorna(self, dt):
        pass

    def disegna(self, sup):
        pass


# ---------------------------------------------------------------------- Titolo
class SchermataTitolo(Schermata):
    def __init__(self, app):
        super().__init__(app)
        x = C.LARGHEZZA // 2 - 230
        voci = ("gioca", "classifica", "impostazioni", "crediti", "esci")
        self.pulsanti = {}
        for i, k in enumerate(voci):
            self.pulsanti[k] = Pulsante((x, 560 + i * 92, 460, 72), T(k), 34, evidenziato=(k == "gioca"))
        self.btn_lingue = pulsanti_lingua(C.LARGHEZZA - 400, 28)
        self.sagome = []
        self._prepara_sagome()

    def _prepara_sagome(self):
        """Sagome che scorrono lentamente sullo sfondo, su tre corsie."""
        pool = [s for s in self.app.dati.elenco if s.iso not in self.app.impostazioni.esclusi]
        rng = random.Random()
        scelte = rng.sample(pool, min(30, len(pool)))
        corsie = [(150, 26.0), (520, 17.0), (900, 34.0)]
        self.sagome = []
        for k, (y, vel) in enumerate(corsie):
            x = rng.uniform(-200, 100)
            for s in scelte[k::3]:
                h = rng.uniform(110, 190)
                img = D.immagine_adattata(s.sagoma, h * 1.3, h).copy()
                img.set_alpha(rng.randint(22, 40))
                self.sagome.append([x, y + rng.uniform(-50, 50) - img.get_height() / 2, vel, img, k])
                x += img.get_width() + rng.uniform(90, 220)

    def aggiorna(self, dt):
        per_corsia = {}
        for sp in self.sagome:
            sp[0] -= sp[2] * dt
            per_corsia.setdefault(sp[4], []).append(sp)
        for corsia, lista in per_corsia.items():
            destra = max(sp[0] + sp[3].get_width() for sp in lista)
            for sp in lista:
                if sp[0] + sp[3].get_width() < -20:
                    sp[0] = max(destra, C.LARGHEZZA) + random.uniform(90, 220)
                    destra = sp[0] + sp[3].get_width()

    def evento(self, ev, pos):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for codice, b in self.btn_lingue.items():
                if b.clic(pos):
                    self.app.audio.suona("clic")
                    self.app.imposta_lingua(codice)
                    return
            for k, p in self.pulsanti.items():
                if p.clic(pos):
                    self.app.audio.suona("clic")
                    self._scegli(k)
                    return
        elif ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._scegli("gioca")
            elif ev.key == pygame.K_ESCAPE:
                self._scegli("esci")

    def _scegli(self, k):
        if k == "gioca":
            self.app.nuova_partita()
        elif k == "esci":
            self.app.esci()
        else:
            self.app.vai(k)

    def disegna(self, sup):
        sup.blit(self.app.sfondo, (0, 0))
        for x, y, _, img, _ in self.sagome:
            if -400 < x < C.LARGHEZZA:
                sup.blit(img, (x, y))
        for p in self.pulsanti.values():
            p.aggiorna(self.app.mouse)
        t = self.app.tempo
        disegna_rosa(sup, (C.LARGHEZZA // 2, 215), 120, angolo=math.sin(t * 0.4) * 6)
        # titolo bicolore con bagliore
        parte1, parte2 = "WhoWantsToBe", "AnExplorer"
        dim = 92
        w1 = font(dim, "extrabold").size(parte1)[0]
        w2 = font(dim, "extrabold").size(parte2)[0]
        x0 = C.LARGHEZZA // 2 - (w1 + w2) // 2
        y = 420
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            g = render(parte2, dim, "extrabold", C.ORO).copy()
            g.set_alpha(40)
            sup.blit(g, g.get_rect(midleft=(x0 + w1 + dx, y + dy)))
        scrivi(sup, parte1, dim, (x0, y), C.BIANCO, "extrabold", ancora="midleft")
        scrivi(sup, parte2, dim, (x0 + w1, y), C.ORO, "extrabold", ancora="midleft")
        scrivi(sup, L.t("sottotitolo"), 28, (C.LARGHEZZA // 2, 495), C.TESTO_TENUE, "medium")
        for p in self.pulsanti.values():
            p.disegna(sup)
        disegna_pulsanti_lingua(sup, self.btn_lingue, self.app.mouse)
        scrivi(sup, L.t("suggerimento_titolo"), 18, (C.LARGHEZZA // 2, C.ALTEZZA - 26),
               C.TESTO_TENUE, "medium", ombra=False)


# ---------------------------------------------------------------------- Gioco
class SchermataGioco(Schermata):
    AREA_SAGOMA = pygame.Rect(60, 186, 1400, 500)
    CASELLE = [pygame.Rect(60, 712, 680, 88), pygame.Rect(780, 712, 680, 88),
               pygame.Rect(60, 820, 680, 88), pygame.Rect(780, 820, 680, 88)]
    SCALA = pygame.Rect(1490, 24, 404, 1032)
    CENTRI_AIUTI = {"5050": (640, 80), "vicino": (760, 80), "bandiera": (880, 80)}
    RAGGIO_AIUTO = 46
    CENTRO_TIMER = (1075, 80)
    CENTRO_AUDIO = (1410, 80)

    def __init__(self, app):
        super().__init__(app)
        self.partita = Partita(app.dati, app.impostazioni.esclusi)
        self.btn_ritiro = Pulsante((60, 50, 240, 62), T("mi_ritiro"), 28)
        self.btn_si = Pulsante((560, 980, 180, 64), T("si"), 30, evidenziato=True)
        self.btn_no = Pulsante((780, 980, 180, 64), T("no"), 30)
        self.btn_avanti = Pulsante((1120, 966, 330, 72), T("avanti"), 32, evidenziato=True)
        self.nuova_domanda()

    # --- flusso ---
    def nuova_domanda(self):
        self.fase = "domanda"
        self.t_fase = 0.0
        self.scelta = None
        self.t_comparsa = 0.0
        lim = C.tempo_limite(self.partita.numero) if self.app.impostazioni.timer else None
        self.timer_totale = lim
        self.timer = float(lim) if lim else None
        self.app.audio.avvia_tensione()

    def _vai_fase(self, fase):
        self.fase = fase
        self.t_fase = 0.0

    def seleziona(self, i):
        d = self.partita.domanda
        if i in d.eliminate:
            return
        self.app.audio.suona("clic")
        self.scelta = i
        if self.app.impostazioni.conferma:
            self._vai_fase("conferma")
        else:
            self.blocca()

    def blocca(self):
        self._vai_fase("suspense")
        self.app.audio.ferma_tensione()
        self.app.audio.suona("blocco")
        self.app.audio.suona("suspense")

    def _rivela_esito(self):
        giusta = self.partita.rispondi(self.scelta)
        if giusta:
            self.app.audio.suona("vittoria" if self.partita.vinta else "giusta")
        else:
            self.app.audio.suona("sbagliata")
        self._vai_fase("esito")

    def usa_aiuto(self, nome):
        if not self.partita.aiuti.get(nome):
            return
        A.usa(self.partita, nome)
        self.app.audio.suona("aiuto")
        self.t_aiuto = 0.0

    def avanti(self):
        self.app.audio.suona("clic")
        if self.partita.finita:
            self.app.audio.ferma_tensione()
            self.app.vai("fine", partita=self.partita)
        else:
            self.partita.avanti()
            self.nuova_domanda()

    # --- eventi ---
    def evento(self, ev, pos):
        f = self.fase
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if math.dist(pos, self.CENTRO_AUDIO) <= 32:
                self.app.cambia_audio()
                return
            if f == "domanda":
                for i, r in enumerate(self.CASELLE):
                    if r.collidepoint(pos) and math_dentro_esagono(r, pos):
                        self.seleziona(i)
                        return
                for nome, c in self.CENTRI_AIUTI.items():
                    if math.dist(pos, c) <= self.RAGGIO_AIUTO:
                        self.usa_aiuto(nome)
                        return
                if self.btn_ritiro.clic(pos):
                    self.app.audio.suona("clic")
                    self._vai_fase("ritiro")
            elif f == "conferma":
                if self.btn_si.clic(pos):
                    self.blocca()
                elif self.btn_no.clic(pos):
                    self.app.audio.suona("clic")
                    self._vai_fase("domanda")
                else:
                    for i, r in enumerate(self.CASELLE):
                        if r.collidepoint(pos) and i not in self.partita.domanda.eliminate:
                            self.scelta = i
                            self.app.audio.suona("clic")
            elif f == "ritiro":
                if self.btn_si.clic(pos):
                    self._ritirati()
                elif self.btn_no.clic(pos):
                    self.app.audio.suona("clic")
                    self._vai_fase("domanda")
            elif f == "rivelazione":
                if self.btn_avanti.clic(pos):
                    self.avanti()
        elif ev.type == pygame.KEYDOWN:
            k = ev.key
            if f == "domanda":
                lettere = {pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2, pygame.K_d: 3}
                if k in lettere:
                    self.seleziona(lettere[k])
                elif k == pygame.K_ESCAPE:
                    self._vai_fase("ritiro")
            elif f in ("conferma", "ritiro"):
                # S = Sì, Y = Yes: valgono in entrambe le lingue
                if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_s, pygame.K_y):
                    self.blocca() if f == "conferma" else self._ritirati()
                elif k in (pygame.K_ESCAPE, pygame.K_n):
                    self._vai_fase("domanda")
                elif f == "conferma" and k in (pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d):
                    i = {pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2, pygame.K_d: 3}[k]
                    if i not in self.partita.domanda.eliminate:
                        self.scelta = i
            elif f == "rivelazione":
                if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.avanti()

    def _ritirati(self):
        self.app.audio.ferma_tensione()
        self.app.audio.suona("blocco")
        self.partita.ritirati()
        self._vai_fase("esito")

    # --- tempo ---
    def aggiorna(self, dt):
        self.t_fase += dt
        self.t_comparsa += dt
        if hasattr(self, "t_aiuto"):
            self.t_aiuto += dt
        if self.fase in ("domanda", "conferma") and self.timer is not None:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = 0
                self.app.audio.ferma_tensione()
                self.partita.tempo_scaduto()
                self.app.audio.suona("sbagliata")
                self._vai_fase("esito")
        if self.fase == "suspense" and self.t_fase >= C.DURATA_SUSPENSE:
            self._rivela_esito()
        elif self.fase == "esito" and self.t_fase >= C.DURATA_ESITO:
            self._vai_fase("rivelazione")

    # --- disegno ---
    def stato_casella(self, i, tempo):
        d = self.partita.domanda
        f = self.fase
        if i in d.eliminate:
            return "eliminata"
        if f in ("esito", "rivelazione"):
            if i == d.corretta:
                if f == "esito" and d.esito == "giusta" and int(self.t_fase * 6) % 2 == 1:
                    return "selezionata"
                return "giusta"
            if i == d.scelta and d.esito == "sbagliata":
                return "sbagliata"
            return "normale"
        if f in ("conferma", "suspense") and i == self.scelta:
            if f == "suspense":
                return "selezionata"
            return "selezionata"
        if f == "domanda" and self.CASELLE[i].collidepoint(self.app.mouse):
            return "hover"
        return "normale"

    def disegna(self, sup):
        t = self.app.tempo
        sup.blit(self.app.sfondo, (0, 0))
        d = self.partita.domanda
        self._disegna_barra(sup, t)
        scrivi(sup, L.t("domanda_n", n=d.numero, totale=C.NUM_DOMANDE), 26, (760, 158), C.ORO, "extrabold")
        if self.fase == "rivelazione":
            self._disegna_rivelazione(sup, t)
        else:
            self._disegna_sagoma(sup, t)
        for i, r in enumerate(self.CASELLE):
            self._disegna_casella(sup, i, r, t)
        self._disegna_fascia_bassa(sup, t)
        evid = None if self.partita.finita else self.partita.numero
        finale = self.partita.livello_finale if (self.partita.finita and self.fase == "rivelazione") else None
        disegna_scala(sup, self.SCALA, self.partita.livello, evid, finale, t)

    def _disegna_barra(self, sup, t):
        attivo_ritiro = self.fase == "domanda"
        self.btn_ritiro.attivo = attivo_ritiro
        self.btn_ritiro.aggiorna(self.app.mouse)
        self.btn_ritiro.disegna(sup)
        tooltip = None
        for nome, c in self.CENTRI_AIUTI.items():
            disponibile = self.partita.aiuti[nome]
            hover = disponibile and self.fase == "domanda" and math.dist(self.app.mouse, c) <= self.RAGGIO_AIUTO
            r = self.RAGGIO_AIUTO
            bordo = C.ORO_CHIARO if hover else (C.ORO if disponibile else (70, 70, 80))
            fondo = (40, 60, 120) if hover else ((14, 28, 70) if disponibile else (14, 16, 26))
            if disponibile:
                for k, a in ((10, 25), (6, 45)):
                    alone = pygame.Surface((2 * (r + k), 2 * (r + k)), pygame.SRCALPHA)
                    pygame.draw.circle(alone, (*bordo, a), (r + k, r + k), r + k)
                    sup.blit(alone, (c[0] - r - k, c[1] - r - k))
            pygame.draw.circle(sup, fondo, c, r)
            pygame.draw.circle(sup, bordo, c, r, 4)
            colore_icona = C.BIANCO if disponibile else (95, 100, 115)
            colore2 = C.ORO if disponibile else (80, 80, 90)
            A.disegna_icona(sup, nome, c, r, colore_icona, colore2, font(22, "extrabold"))
            if not disponibile:
                A.disegna_barra(sup, c, r, C.ROSSO_CHIARO)
            if hover:
                tooltip = A.descrizione(nome)
        if tooltip:
            scrivi(sup, tooltip, 18, (760, 138), C.ORO_CHIARO, "semibold", ombra=False)
        # timer
        if self.timer is not None and self.fase in ("domanda", "conferma"):
            c = self.CENTRO_TIMER
            frac = max(0.0, self.timer / self.timer_totale)
            col = C.ROSSO_CHIARO if self.timer < 10 else C.BLU_CHIARO
            pygame.draw.circle(sup, (12, 22, 50), c, 44)
            pygame.draw.circle(sup, (40, 56, 96), c, 44, 5)
            if frac > 0:
                rr = pygame.Rect(0, 0, 88, 88)
                rr.center = c
                pygame.draw.arc(sup, col, rr, math.pi / 2, math.pi / 2 + 2 * math.pi * frac, 6)
            scrivi(sup, str(int(math.ceil(self.timer))), 30, c, col, "extrabold")
        elif self.timer_totale is None and self.app.impostazioni.timer and self.fase == "domanda":
            scrivi(sup, "∞", 40, self.CENTRO_TIMER, C.TESTO_TENUE, "bold")
        hover_audio = math.dist(self.app.mouse, self.CENTRO_AUDIO) <= 32
        icona_audio(sup, self.CENTRO_AUDIO, 30, self.app.audio.attivo, hover_audio)

    def _area_sagoma(self):
        """Rettangolo della sagoma (si accorcia quando compare la bandiera)."""
        a = self.AREA_SAGOMA.inflate(-40, -36)
        if self.partita.domanda.bandiera:
            a.height -= 150
        return a

    def _disegna_sagoma(self, sup, t):
        d = self.partita.domanda
        pannello(sup, self.AREA_SAGOMA, (50, 80, 150), (0, 0, 0), raggio=26, alpha=255)
        area = self._area_sagoma()
        alpha = int(255 * min(1.0, self.t_comparsa / 0.6))
        if d.vicino:
            img = D.immagine_adattata(d.vicino["immagine"], area.width, area.height)
            r = img.get_rect(center=area.center)
            sup.blit(img, r)
            nome_v = L.nome(self.app.dati[d.vicino["iso"]])
            ex, ey = d.vicino["etichetta"]
            lx, ly = r.x + ex * r.width, r.y + ey * r.height
            w = font(30, "extrabold").size(nome_v)[0]
            lx = min(max(lx, area.left + w / 2 + 6), area.right - w / 2 - 6)
            ly = min(max(ly, area.top + 22), area.bottom - 22)
            scrivi_contornato(sup, nome_v, 30, (lx, ly), C.BIANCO, (40, 24, 0), "extrabold")
            didascalia = L.t("didascalia", tipo=A.didascalia(d.vicino["tipo"]), nome=nome_v)
            scrivi(sup, didascalia, 24, (self.AREA_SAGOMA.x + 28, self.AREA_SAGOMA.y + 26), C.ORO, "bold",
                   ancora="topleft")
        else:
            img = D.immagine_adattata(d.stato.sagoma, area.width, area.height)
            if alpha < 255:
                img = img.copy()
                img.set_alpha(alpha)
            sup.blit(img, img.get_rect(center=area.center))
        if d.bandiera:
            self._disegna_bandiera(sup, d.stato, pygame.Rect(area.centerx - 120, area.bottom + 16, 240, 124))

    def _disegna_bandiera(self, sup, stato, box):
        img = D.immagine_adattata(stato.bandiera, box.width, box.height)
        r = img.get_rect(center=box.center)
        cornice = r.inflate(14, 14)
        pygame.draw.rect(sup, (20, 26, 40), cornice, border_radius=6)
        pygame.draw.rect(sup, C.ORO, cornice, 3, border_radius=6)
        sup.blit(img, r)

    def _disegna_casella(self, sup, i, r, t):
        d = self.partita.domanda
        stato = self.stato_casella(i, t)
        img = superficie_casella(r.width, r.height, stato)
        sup.blit(img, (r.x - 14, r.y - 14))
        _, _, _, col_testo, col_lettera = _STILI_CASELLA[stato]
        scrivi(sup, LETTERE[i] + ":", 30, (r.x + 56, r.centery), col_lettera, "extrabold", ancora="midleft",
               ombra=False)
        if stato != "eliminata":
            nome = L.nome(d.opzioni[i])
            dim = dimensione_adatta(nome, r.width - 150, 32, "bold", 18)
            scrivi(sup, nome, dim, (r.x + 104, r.centery), col_testo, "bold", ancora="midleft",
                   ombra=stato in ("normale", "hover"))

    def _disegna_fascia_bassa(self, sup, t):
        f = self.fase
        if f == "conferma":
            testo = L.t("conferma_risposta")
            scrivi(sup, testo, dimensione_adatta(testo, 1350, 34, "extrabold"), (760, 950), C.BIANCO, "extrabold")
            self._disegna_si_no(sup)
        elif f == "ritiro":
            liv = self.partita.livello
            if liv:
                testo = L.t("conferma_ritiro", grado=C.titolo_grado(liv),
                            miglia=C.formatta_miglia(C.miglia_grado(liv)))
            else:
                testo = L.t("conferma_ritiro_zero")
            scrivi(sup, testo, dimensione_adatta(testo, 1350, 28, "bold"), (760, 950), C.BIANCO, "bold")
            self._disegna_si_no(sup)
        elif f == "suspense":
            puntini = "." * (1 + int(self.t_fase * 3) % 3)
            scrivi(sup, L.t("risposta_bloccata") + puntini, 30, (760, 990), C.ORO_CHIARO, "bold")
        elif f == "esito":
            self._scrivi_esito(sup, (760, 990))
        elif f == "rivelazione":
            self._scrivi_esito(sup, (590, 1002), corto=True)
            self.btn_avanti.testo = T("vedi_risultato" if self.partita.finita else "avanti")
            self.btn_avanti.aggiorna(self.app.mouse)
            self.btn_avanti.disegna(sup)
        else:
            testo = L.t("istruzioni_gioco")
            scrivi(sup, testo, dimensione_adatta(testo, 1350, 22, "medium"), (760, 990),
                   C.TESTO_TENUE, "medium", ombra=False)

    def _disegna_si_no(self, sup):
        for b in (self.btn_si, self.btn_no):
            b.aggiorna(self.app.mouse)
            b.disegna(sup)

    def _scrivi_esito(self, sup, pos, corto=False):
        d = self.partita.domanda
        p = self.partita
        if d.esito == "giusta":
            if p.vinta:
                testo, col = L.t("esito_vittoria", grado=C.titolo_grado(C.NUM_DOMANDE)), C.ORO_CHIARO
            else:
                testo, col = L.t("esito_giusta", grado=C.titolo_grado(p.livello)), C.VERDE_CHIARO
        elif d.esito == "ritiro":
            testo, col = L.t("esito_ritiro", grado=C.titolo_grado(p.livello_finale)), C.ORO_CHIARO
        else:
            prefisso = L.t("esito_tempo" if d.esito == "tempo" else "esito_sbagliata")
            if p.livello_finale:
                testo = L.t("esito_soglia", prefisso=prefisso, grado=C.titolo_grado(p.livello_finale))
            else:
                testo = L.t("esito_zero", prefisso=prefisso)
            col = C.ROSSO_CHIARO
        dim = dimensione_adatta(testo, 1000 if corto else 1350, 30, "bold")
        scrivi(sup, testo, dim, pos, col, "bold")

    def _disegna_rivelazione(self, sup, t):
        d = self.partita.domanda
        s = d.stato
        if d.esito == "giusta":
            col, titolo = (120, 230, 160), L.t("titolo_giusta")
        elif d.esito == "ritiro":
            col, titolo = C.ORO_CHIARO, L.t("titolo_ritiro")
        elif d.esito == "tempo":
            col, titolo = (255, 125, 115), L.t("titolo_tempo")
        else:
            col, titolo = (255, 125, 115), L.t("titolo_sbagliata")
        box = self.AREA_SAGOMA
        pannello(sup, box, col, (5, 10, 26), raggio=26, alpha=250)
        # sagoma colorata
        area_s = pygame.Rect(box.x + 30, box.y + 30, 520, box.height - 60)
        chiave = (s.iso, col, area_s.size)
        if getattr(self, "_colorata", (None, None))[0] != chiave:
            self._colorata = (chiave, D.colora(D.immagine_adattata(s.sagoma, area_s.width, area_s.height), col))
        img = self._colorata[1]
        sup.blit(img, img.get_rect(center=area_s.center))
        # testo
        x = box.x + 580
        scrivi(sup, titolo, 22, (x, box.y + 30), col, "extrabold", ancora="topleft", ombra=False)
        nome = L.nome(s)
        dim = dimensione_adatta(nome, box.right - x - 30, 58, "extrabold", 28)
        scrivi(sup, nome, dim, (x, box.y + 58), C.BIANCO, "extrabold", ancora="topleft")
        scrivi(sup, L.t("luogo", continente=L.luogo(s.continente), regione=L.luogo(s.regione)), 22,
               (x, box.y + 132), C.TESTO_TENUE, "medium", ancora="topleft", ombra=False)
        # bandiera
        self._disegna_bandiera(sup, s, pygame.Rect(x + 6, box.y + 182, 220, 140))
        # mappa del mondo
        mappa_r = pygame.Rect(x + 250, box.y + 172, box.right - x - 270, 230)
        self.app.mappa.disegna(sup, mappa_r, s.iso, C.ORO, t)
        # confinanti
        y = box.y + 414
        if s.confinanti:
            nomi = [L.nome(self.app.dati[i]) for i in s.confinanti if i in self.app.dati.stati]
            testo = L.t("confina_con", elenco=", ".join(nomi))
        else:
            vicini = [v for v in s.vicini if v["tipo"] == "vicino_isola" and v["iso"] in self.app.dati.stati]
            testo = (L.t("nessun_confine_vicino", nome=L.nome(self.app.dati[vicini[0]["iso"]]))
                     if vicini else L.t("nessun_confine"))
        larghezza = box.right - x - 30
        dim = 22
        righe = a_capo(testo, dim, "medium", larghezza)
        if len(righe) > 2:
            # tre righe entrano nel riquadro solo con un carattere un po' più piccolo
            dim = 20
            righe = a_capo(testo, dim, "medium", larghezza)
        if len(righe) > 3:
            # elenco ancora troppo lungo: si tronca la terza riga con i puntini
            righe = righe[:3]
            while righe[2] and font(dim, "medium").size(righe[2] + " …")[0] > larghezza:
                righe[2] = righe[2].rsplit(" ", 1)[0] if " " in righe[2] else righe[2][:-1]
            righe[2] = righe[2].rstrip(",") + " …"
        for riga in righe:
            scrivi(sup, riga, dim, (x, y), C.TESTO, "medium", ancora="topleft", ombra=False)
            y += dim + 7


def math_dentro_esagono(rect, pos):
    """True se pos cade dentro il riquadro esagonale (non solo nel rettangolo)."""
    x, y = pos
    k = rect.height * 0.5
    dy = abs(y - rect.centery)
    if x < rect.x + k:
        return (rect.x + k - x) <= k - dy
    if x > rect.right - k:
        return (x - (rect.right - k)) <= k - dy
    return True


# ------------------------------------------------------------------- Fine partita
class SchermataFine(Schermata):
    def __init__(self, app, partita):
        super().__init__(app)
        self.partita = partita
        self.nome = ""
        self.salvato = None
        self.livello = partita.livello_finale
        self.miglia = C.miglia_grado(self.livello)
        self.puo_salvare = app.classifica.entra(self.miglia)
        self.btn_salva = Pulsante((1330, 676, 520, 62), T("salva_classifica"), 28, evidenziato=True)
        self.btn_ancora = Pulsante((1330, 790, 520, 70), T("gioca_ancora"), 30, evidenziato=True)
        self.btn_classifica = Pulsante((1330, 880, 250, 64), T("classifica"), 26)
        self.btn_menu = Pulsante((1600, 880, 250, 64), T("menu"), 26)
        self.coriandoli = []
        if partita.vinta:
            rng = random.Random()
            for _ in range(160):
                self.coriandoli.append([rng.uniform(0, C.LARGHEZZA), rng.uniform(-C.ALTEZZA, 0),
                                        rng.uniform(60, 160), rng.uniform(0, 6.28),
                                        rng.choice([C.ORO, C.ORO_CHIARO, C.BIANCO, C.BLU_CHIARO])])

    def entra(self):
        pygame.key.start_text_input()
        if self.partita.vinta:
            self.app.audio.suona("vittoria")

    def _salva(self):
        if self.salvato is None and self.puo_salvare and self.nome.strip():
            voce = self.app.classifica.aggiungi(self.nome, self.livello)
            if voce is not None:
                self.salvato = self.app.classifica.voci.index(voce) + 1
            else:
                self.salvato = 0
            self.app.audio.suona("clic")

    def evento(self, ev, pos):
        if ev.type == pygame.TEXTINPUT and self.salvato is None and self.puo_salvare:
            for ch in ev.text:
                if len(self.nome) < 20 and ch.isprintable():
                    self.nome += ch
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_BACKSPACE and self.salvato is None:
                self.nome = self.nome[:-1]
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.salvato is None and self.puo_salvare and self.nome.strip():
                    self._salva()
                else:
                    self.app.nuova_partita()
            elif ev.key == pygame.K_ESCAPE:
                self.app.vai("titolo")
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.btn_salva.clic(pos):
                self._salva()
            elif self.btn_ancora.clic(pos):
                self.app.audio.suona("clic")
                self.app.nuova_partita()
            elif self.btn_classifica.clic(pos):
                self.app.audio.suona("clic")
                self.app.vai("classifica")
            elif self.btn_menu.clic(pos):
                self.app.audio.suona("clic")
                self.app.vai("titolo")

    def aggiorna(self, dt):
        for c in self.coriandoli:
            c[1] += c[2] * dt
            c[3] += dt * 3
            if c[1] > C.ALTEZZA + 20:
                c[1] = random.uniform(-200, -20)

    def disegna(self, sup):
        t = self.app.tempo
        sup.blit(self.app.sfondo, (0, 0))
        p = self.partita
        if p.vinta:
            titolo, col = L.t("fine_vittoria"), C.ORO_CHIARO
        elif p.ritirata:
            titolo, col = L.t("fine_ritiro"), C.ORO
        else:
            titolo, col = L.t("fine_sconfitta"), C.BLU_CHIARO
        scrivi(sup, titolo, 64, (C.LARGHEZZA // 2, 80), col, "extrabold")
        # riepilogo domande
        giocate = p.domande_giocate()
        scrivi(sup, L.t("il_tuo_viaggio"), 28, (80, 170), C.ORO, "extrabold", ancora="midleft")
        for k, d in enumerate(giocate):
            col_k, rig = divmod(k, 5)
            r = pygame.Rect(70 + col_k * 400, 200 + rig * 150, 385, 138)
            pannello(sup, r, (50, 80, 150), (6, 12, 30), raggio=16, alpha=220, bagliore=False)
            img = D.immagine_adattata(d.stato.sagoma, 104, 104)
            sup.blit(img, img.get_rect(center=(r.x + 66, r.centery)))
            scrivi(sup, L.t("domanda_breve", n=d.numero), 17, (r.x + 132, r.y + 26), C.TESTO_TENUE, "semibold",
                   ancora="midleft", ombra=False)
            dim = 24
            nome = L.nome(d.stato)
            righe = a_capo(nome, dim, "bold", r.width - 190)
            while dim > 15 and (len(righe) > 2 or any(font(dim, "bold").size(x)[0] > r.width - 190 for x in righe)):
                dim -= 2
                righe = a_capo(nome, dim, "bold", r.width - 190)
            yy = r.y + (52 if len(righe) == 1 else 44)
            for riga in righe[:2]:
                scrivi(sup, riga, dim, (r.x + 132, yy), C.BIANCO, "bold", ancora="topleft", ombra=False)
                yy += dim + 6
            esito_txt = L.t("esito_breve_" + d.esito)
            scrivi(sup, esito_txt, 17, (r.x + 132, r.bottom - 22), C.TESTO_TENUE, "medium", ancora="midleft",
                   ombra=False)
            segno_esito(sup, (r.right - 30, r.y + 30), 17, d.esito)
        if not giocate:
            scrivi(sup, L.t("nessuna_domanda"), 24, (80, 230), C.TESTO_TENUE, "medium", ancora="midleft")
        # pannello del grado
        r = pygame.Rect(1300, 150, 580, 396)
        pannello(sup, r, C.ORO, (14, 16, 34), raggio=24)
        scrivi(sup, L.t("grado_raggiunto"), 24, (r.centerx, r.y + 36), C.TESTO_TENUE, "bold")
        disegna_rosa(sup, (r.centerx, r.y + 122), 54, angolo=t * 8)
        nome_g = C.titolo_grado(self.livello)
        scrivi(sup, nome_g, dimensione_adatta(nome_g, r.width - 40, 48, "extrabold"), (r.centerx, r.y + 222),
               C.ORO_CHIARO, "extrabold")
        scrivi(sup, L.t("miglia_esplorate", miglia=C.formatta_miglia(self.miglia)), 30, (r.centerx, r.y + 276),
               C.BIANCO, "bold")
        giuste = sum(1 for d in giocate if d.esito == "giusta")
        scrivi(sup, L.t("risposte_esatte", giuste=giuste, totale=len(giocate)), 22, (r.centerx, r.y + 322),
               C.TESTO_TENUE, "medium", ombra=False)
        aiuti_usati = len(p.aiuti) - sum(1 for v in p.aiuti.values() if v)
        scrivi(sup, L.t("aiuti_usati", usati=aiuti_usati, totale=len(p.aiuti)), 22, (r.centerx, r.y + 356),
               C.TESTO_TENUE, "medium", ombra=False)
        # classifica
        if self.salvato:
            testo = L.t("salvato_posizione", posizione=self.salvato)
            scrivi(sup, testo, dimensione_adatta(testo, r.width, 26, "bold"), (r.centerx, 650), C.VERDE_CHIARO, "bold")
        elif self.puo_salvare:
            scrivi(sup, L.t("nome_classifica"), 21, (1330, 566), C.TESTO, "semibold", ancora="topleft",
                   ombra=False)
            campo = pygame.Rect(1330, 604, 520, 52)
            pygame.draw.rect(sup, (4, 8, 20), campo, border_radius=10)
            pygame.draw.rect(sup, C.BLU_CHIARO, campo, 2, border_radius=10)
            cursore = "|" if int(t * 2) % 2 == 0 else ""
            scrivi(sup, (self.nome or "") + cursore, 26, (campo.x + 16, campo.centery), C.BIANCO, "semibold",
                   ancora="midleft", ombra=False)
            self.btn_salva.attivo = bool(self.nome.strip())
            self.btn_salva.aggiorna(self.app.mouse)
            self.btn_salva.disegna(sup)
        else:
            scrivi(sup, L.t("non_in_top10"), 22, (r.centerx, 660), C.TESTO_TENUE, "medium")
        for b in (self.btn_ancora, self.btn_classifica, self.btn_menu):
            b.aggiorna(self.app.mouse)
            b.disegna(sup)
        for x, y, _, ang, col in self.coriandoli:
            w = 10 * abs(math.cos(ang)) + 2
            pygame.draw.rect(sup, col, (x, y, w, 8))


# ---------------------------------------------------------------------- Classifica
class SchermataClassifica(Schermata):
    def __init__(self, app):
        super().__init__(app)
        self.btn_indietro = Pulsante((C.LARGHEZZA // 2 - 180, 960, 360, 70), T("indietro"), 30)

    def evento(self, ev, pos):
        if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.btn_indietro.clic(pos)) or \
                (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_BACKSPACE)):
            self.app.audio.suona("clic")
            self.app.vai("titolo")

    def disegna(self, sup):
        sup.blit(self.app.sfondo, (0, 0))
        scrivi(sup, L.t("titolo_classifica"), 64, (C.LARGHEZZA // 2, 90), C.ORO, "extrabold")
        r = pygame.Rect(260, 160, 1400, 760)
        pannello(sup, r, C.BLU_BORDO, (6, 12, 30), raggio=24, alpha=230)
        colonne = [(r.x + 70, "#"), (r.x + 140, L.t("col_nome")), (r.x + 600, L.t("col_grado")),
                   (r.x + 1010, L.t("col_miglia")), (r.x + 1190, L.t("col_data"))]
        for x, t in colonne:
            scrivi(sup, t, 22, (x, r.y + 44), C.TESTO_TENUE, "bold", ancora="midleft", ombra=False)
        voci = self.app.classifica.voci
        if not voci:
            scrivi(sup, L.t("classifica_vuota"), 30, r.center, C.TESTO, "semibold")
        for i, v in enumerate(voci):
            y = r.y + 108 + i * 64
            if i % 2 == 0:
                pygame.draw.rect(sup, (14, 26, 60), (r.x + 30, y - 28, r.width - 60, 56), border_radius=12)
            col = C.ORO_CHIARO if i == 0 else C.BIANCO
            nome = v["nome"]
            titolo = C.titolo_grado(v["grado"])
            scrivi(sup, f"{i + 1}", 26, (colonne[0][0], y), col, "extrabold", ancora="midleft", ombra=False)
            scrivi(sup, nome, dimensione_adatta(nome, 440, 26, "bold", 16), (colonne[1][0], y), col, "bold",
                   ancora="midleft", ombra=False)
            scrivi(sup, titolo, dimensione_adatta(titolo, 390, 24, "semibold", 16), (colonne[2][0], y), col,
                   "semibold", ancora="midleft", ombra=False)
            scrivi(sup, C.formatta_miglia(v["miglia"]), 24, (colonne[3][0], y), col, "semibold",
                   ancora="midleft", ombra=False)
            scrivi(sup, v["data"], 20, (colonne[4][0], y), C.TESTO_TENUE, "medium", ancora="midleft",
                   ombra=False)
        self.btn_indietro.aggiorna(self.app.mouse)
        self.btn_indietro.disegna(sup)


# ---------------------------------------------------------------------- Impostazioni
class SchermataImpostazioni(Schermata):
    LISTA = pygame.Rect(880, 250, 980, 640)
    RIGA = 44

    def __init__(self, app, avviso=None):
        super().__init__(app)
        imp = app.impostazioni
        self.btn_lingue = pulsanti_lingua(380, 148)
        self.sw_timer = Interruttore((620, 250, 120, 50), imp.timer)
        self.sw_conferma = Interruttore((620, 380, 120, 50), imp.conferma)
        self.sw_audio = Interruttore((620, 510, 120, 50), imp.audio)
        self.btn_ripristina = Pulsante((100, 790, 640, 62), T("ripristina_esclusioni"), 24)
        self.btn_indietro = Pulsante((C.LARGHEZZA // 2 - 180, 975, 360, 70), T("indietro"), 30)
        self.filtro = 0   # 0 = tutte le fasce
        self.btn_filtri = [Pulsante((880 + i * 140, 175, 128, 50), T("tutte") if i == 0 else T("fascia_n", n=i), 20)
                           for i in range(6)]
        self.scroll = 0
        self.messaggio = None   # chiave del testo in lingua.py
        self.t_messaggio = 0.0
        if avviso:
            self._avvisa(avviso, 6.0)

    def _elenco(self):
        return [s for s in self.app.dati.ordinati() if self.filtro == 0 or s.fascia == self.filtro]

    def _max_scroll(self):
        righe = math.ceil(len(self._elenco()) / 2)
        return max(0, righe * self.RIGA - self.LISTA.height + 20)

    def _commuta(self, stato):
        imp = self.app.impostazioni
        if stato.iso in imp.esclusi:
            imp.esclusi.discard(stato.iso)
        else:
            prova = set(imp.esclusi) | {stato.iso}
            conteggi = self.app.dati.conteggio_fasce(prova)
            if conteggi.get(stato.fascia, 0) < 3:
                self._avvisa("minimo_per_fascia")
                return
            if sum(conteggi.values()) < 20:
                self._avvisa("minimo_totale")
                return
            imp.esclusi.add(stato.iso)

    def _avvisa(self, chiave, durata=3.0):
        self.messaggio = chiave
        self.t_messaggio = durata

    def evento(self, ev, pos):
        imp = self.app.impostazioni
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for codice, b in self.btn_lingue.items():
                if b.clic(pos):
                    self.app.audio.suona("clic")
                    self.app.imposta_lingua(codice)
                    self.scroll = 0
                    return
            if self.sw_timer.clic(pos):
                imp.timer = self.sw_timer.valore
            elif self.sw_conferma.clic(pos):
                imp.conferma = self.sw_conferma.valore
            elif self.sw_audio.clic(pos):
                self.app.imposta_audio(self.sw_audio.valore)
            elif self.btn_ripristina.clic(pos):
                imp.ripristina_esclusi()
                self._avvisa("esclusioni_ripristinate")
            elif self.btn_indietro.clic(pos):
                imp.salva()
                self.app.audio.suona("clic")
                self.app.vai("titolo")
                return
            else:
                for i, b in enumerate(self.btn_filtri):
                    if b.clic(pos):
                        self.filtro = i
                        self.scroll = 0
                        return
                if self.LISTA.collidepoint(pos):
                    s = self._stato_in(pos)
                    if s:
                        self._commuta(s)
            imp.salva()
            self.app.audio.suona("clic")
        elif ev.type == pygame.MOUSEWHEEL:
            self.scroll = min(max(0, self.scroll - ev.y * 66), self._max_scroll())
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            imp.salva()
            self.app.vai("titolo")

    def _stato_in(self, pos):
        x, y = pos
        col = 0 if x < self.LISTA.x + self.LISTA.width // 2 else 1
        riga = int((y - self.LISTA.y - 10 + self.scroll) // self.RIGA)
        elenco = self._elenco()
        righe = math.ceil(len(elenco) / 2)
        if riga < 0 or riga >= righe:
            return None
        i = col * righe + riga
        return elenco[i] if i < len(elenco) else None

    def aggiorna(self, dt):
        self.t_messaggio = max(0.0, self.t_messaggio - dt)

    def disegna(self, sup):
        sup.blit(self.app.sfondo, (0, 0))
        imp = self.app.impostazioni
        m = self.app.mouse
        scrivi(sup, L.t("titolo_impostazioni"), 60, (C.LARGHEZZA // 2, 80), C.ORO, "extrabold")
        scrivi(sup, L.t("lingua"), 32, (100, 175), C.BIANCO, "bold", ancora="midleft")
        disegna_pulsanti_lingua(sup, self.btn_lingue, m)
        voci = [
            (self.sw_timer, "timer"),
            (self.sw_conferma, "risposta_definitiva"),
            (self.sw_audio, "audio"),
        ]
        for sw, chiave in voci:
            sw.aggiorna(m)
            titolo = L.t(chiave)
            scrivi(sup, titolo, dimensione_adatta(titolo, 500, 32, "bold"), (100, sw.rect.centery - 14), C.BIANCO,
                   "bold", ancora="midleft")
            scrivi_paragrafo(sup, L.t(chiave + "_desc"), 19, 100, sw.rect.centery + 12, 480, C.TESTO_TENUE, "medium")
            sw.disegna(sup)
        # conteggi per fascia
        conteggi = self.app.dati.conteggio_fasce(imp.esclusi)
        scrivi(sup, L.t("stati_per_fascia"), 26, (100, 660), C.ORO, "bold", ancora="midleft")
        testo = "   ".join(L.t("fascia_conteggio", n=f, conteggio=conteggi.get(f, 0)) for f in range(1, 6))
        scrivi(sup, testo, 24, (100, 705), C.BIANCO, "semibold", ancora="midleft", ombra=False)
        scrivi(sup, L.t("totale_stati", giocabili=sum(conteggi.values()), totale=len(self.app.dati.elenco)), 20,
               (100, 742), C.TESTO_TENUE, "medium", ancora="midleft", ombra=False)
        self.btn_ripristina.aggiorna(m)
        self.btn_ripristina.disegna(sup)
        if self.t_messaggio > 0 and self.messaggio:
            testo = L.t(self.messaggio)
            scrivi(sup, testo, dimensione_adatta(testo, 740, 22, "bold"), (100, 890), C.ORO_CHIARO, "bold",
                   ancora="midleft")
        # elenco stati
        scrivi(sup, L.t("elenco_stati"), 24, (880, 140), C.ORO, "bold", ancora="midleft")
        for i, b in enumerate(self.btn_filtri):
            b.evidenziato = (i == self.filtro)
            b.aggiorna(m)
            b.disegna(sup)
        lista = self.LISTA
        pannello(sup, lista, C.BLU_BORDO, (4, 8, 22), raggio=16, alpha=230, bagliore=False)
        elenco = self._elenco()
        righe = math.ceil(len(elenco) / 2)
        sup.set_clip(lista.inflate(-6, -6))
        for i, s in enumerate(elenco):
            col_i, riga = divmod(i, righe) if righe else (0, 0)
            x = lista.x + 20 + col_i * (lista.width // 2)
            y = lista.y + 10 + riga * self.RIGA - self.scroll
            if y < lista.y - self.RIGA or y > lista.bottom:
                continue
            in_gioco = s.iso not in imp.esclusi
            cella = pygame.Rect(x - 8, y, lista.width // 2 - 24, self.RIGA - 4)
            if cella.collidepoint(m):
                pygame.draw.rect(sup, (20, 36, 80), cella, border_radius=8)
            box = pygame.Rect(x, y + 8, 26, 26)
            pygame.draw.rect(sup, C.VERDE if in_gioco else (40, 46, 64), box, border_radius=6)
            pygame.draw.rect(sup, C.BLU_CHIARO, box, 2, border_radius=6)
            if in_gioco:
                pygame.draw.lines(sup, C.BIANCO, False, [(box.x + 6, box.centery), (box.x + 11, box.bottom - 7),
                                                         (box.right - 5, box.y + 6)], 3)
            col_t = C.BIANCO if in_gioco else C.GRIGIO
            nome = L.nome(s)
            dim = dimensione_adatta(nome, lista.width // 2 - 130, 21, "semibold", 14)
            scrivi(sup, nome, dim, (x + 40, y + 21), col_t, "semibold", ancora="midleft", ombra=False)
            scrivi(sup, L.t("fascia_breve", n=s.fascia), 18, (cella.right - 12, y + 21),
                   C.ORO if in_gioco else C.GRIGIO, "bold", ancora="midright", ombra=False)
        sup.set_clip(None)
        if self._max_scroll() > 0:
            frac = self.scroll / self._max_scroll()
            h = max(60, lista.height * lista.height / (righe * self.RIGA + 20))
            barra = pygame.Rect(lista.right - 12, lista.y + 8 + frac * (lista.height - 16 - h), 6, h)
            pygame.draw.rect(sup, C.BLU_CHIARO, barra, border_radius=3)
        self.btn_indietro.aggiorna(m)
        self.btn_indietro.disegna(sup)


# ---------------------------------------------------------------------- Crediti
class SchermataCrediti(Schermata):
    def __init__(self, app):
        super().__init__(app)
        self.btn_indietro = Pulsante((C.LARGHEZZA // 2 - 180, 975, 360, 70), T("indietro"), 30)

    def evento(self, ev, pos):
        if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.btn_indietro.clic(pos)) or                 (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_BACKSPACE)):
            self.app.audio.suona("clic")
            self.app.vai("titolo")

    def disegna(self, sup):
        sup.blit(self.app.sfondo, (0, 0))
        scrivi(sup, L.t("titolo_crediti"), 64, (C.LARGHEZZA // 2, 90), C.ORO, "extrabold")
        r = pygame.Rect(300, 170, 1320, 770)
        pannello(sup, r, C.BLU_BORDO, (6, 12, 30), raggio=24, alpha=230)
        y = r.y + 40
        for titolo, testo in L.crediti():
            scrivi(sup, titolo, 28, (r.x + 50, y), C.ORO, "bold", ancora="topleft")
            y = scrivi_paragrafo(sup, testo, 22, r.x + 50, y + 42, r.width - 100, C.TESTO, "medium") + 22
        scrivi(sup, L.t("versione", versione=C.VERSIONE), 18, (r.centerx, r.bottom - 26), C.TESTO_TENUE, "medium",
               ombra=False)
        self.btn_indietro.aggiorna(self.app.mouse)
        self.btn_indietro.disegna(sup)
