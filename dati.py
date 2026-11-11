# -*- coding: utf-8 -*-
"""Caricamento dei dati generati da tools/prepara_dati.py (assets/stati.json)
e delle immagini (sagome, compositi, bandiere, mappa del mondo)."""

import json

import config
import lingua


class Stato:
    """Uno stato del quiz, come descritto in assets/stati.json."""

    def __init__(self, d):
        self.iso = d["iso"]
        self.iso2 = d.get("iso2", "")
        self.nome = d["nome"]
        self.nome_en = d.get("nome_en") or self.nome
        self.fascia = int(d["fascia"])
        self.escluso_predefinito = bool(d.get("escluso", False))
        self.continente = d.get("continente", "")
        self.regione = d.get("regione", "")
        self.sagoma = d["sagoma"]
        self.bandiera = d["bandiera"]
        self.confinanti = list(d.get("confinanti", []))
        # candidati per l'aiuto "stato confinante", già ordinati per preferenza
        self.vicini = list(d.get("vicini", []))
        self.simili = list(d.get("simili", []))

    def __repr__(self):
        return f"Stato({self.iso}, {self.nome}, F{self.fascia})"


class Dati:
    """Tutti gli stati, con funzioni di comodo per la logica di gioco."""

    def __init__(self, percorso=None):
        percorso = percorso or config.asset("stati.json")
        with open(percorso, encoding="utf-8") as f:
            grezzo = json.load(f)
        self.stati = {}
        for d in grezzo["stati"]:
            s = Stato(d)
            self.stati[s.iso] = s
        self.elenco = sorted(self.stati.values(), key=lambda s: s.nome)
        self._ordinati = {}

    def __getitem__(self, iso):
        return self.stati[iso]

    def ordinati(self):
        """Stati in ordine alfabetico secondo i nomi della lingua corrente."""
        codice = lingua.corrente()
        if codice not in self._ordinati:
            self._ordinati[codice] = sorted(
                self.stati.values(), key=lambda s: lingua.chiave_ordinamento(lingua.nome(s)))
        return self._ordinati[codice]

    def esclusi_predefiniti(self):
        return {s.iso for s in self.stati.values() if s.escluso_predefinito}

    def giocabili(self, esclusi):
        return [s for s in self.elenco if s.iso not in esclusi]

    def conteggio_fasce(self, esclusi):
        c = {f: 0 for f in range(1, 6)}
        for s in self.giocabili(esclusi):
            c[s.fascia] = c.get(s.fascia, 0) + 1
        return c


# ---------------------------------------------------------------------------
# Immagini (richiedono pygame; importato qui dentro così la logica e i test
# possono usare questo modulo anche senza finestra)
# ---------------------------------------------------------------------------
_cache_img = {}
_cache_scalate = {}


def immagine(relativo):
    """Carica un'immagine da assets/ (con cache)."""
    import pygame
    if relativo not in _cache_img:
        img = pygame.image.load(config.asset(*relativo.split("/")))
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            img = img.convert_alpha()
        _cache_img[relativo] = img
    return _cache_img[relativo]


def immagine_adattata(relativo, larghezza, altezza):
    """Immagine scalata (proporzioni mantenute) per stare in larghezza x altezza."""
    import pygame
    chiave = (relativo, int(larghezza), int(altezza))
    scalata = _cache_scalate.get(chiave)
    if scalata is None:
        img = immagine(relativo)
        w, h = img.get_size()
        k = min(larghezza / w, altezza / h)
        nuova = (max(1, int(w * k)), max(1, int(h * k)))
        scalata = pygame.transform.smoothscale(img, nuova)
        # la cache si svuota PRIMA di inserire, così l'immagine appena fatta resta disponibile
        if len(_cache_scalate) >= 400:
            _cache_scalate.clear()
        _cache_scalate[chiave] = scalata
    return scalata


def colora(superficie, colore):
    """Copia di una sagoma bianca colorata con il colore dato."""
    import pygame
    s = superficie.copy()
    s.fill((*colore, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return s


class Mappa:
    """Mappa del mondo (proiezione Equal Earth) con i contorni degli stati."""

    def __init__(self):
        with open(config.asset("mondo", "stati_mappa.json"), encoding="utf-8") as f:
            d = json.load(f)
        self.larghezza = d["larghezza"]
        self.altezza = d["altezza"]
        self.stati = d["stati"]
        self._base = {}
        self._evidenziata = (None, None)

    def base(self, larghezza):
        import pygame
        if larghezza not in self._base:
            img = immagine("mondo/mappa.png")
            h = int(round(img.get_height() * larghezza / img.get_width()))
            self._base[larghezza] = pygame.transform.smoothscale(img, (larghezza, h))
        return self._base[larghezza]

    def disegna(self, superficie, rect, iso, colore, tempo=0.0):
        """Disegna la mappa in rect (larghezza adattata) evidenziando lo stato iso."""
        import math
        import pygame
        base = self.base(rect.width)
        x0, y0 = rect.x, rect.y + (rect.height - base.get_height()) // 2
        k = rect.width / self.larghezza
        info = self.stati.get(iso)
        if not info:
            superficie.blit(base, (x0, y0))
            return
        # mappa con lo stato già colorato, preparata una volta sola
        chiave = (iso, rect.width, tuple(colore))
        if self._evidenziata[0] != chiave:
            img = base.copy()
            for anello in info["anelli"]:
                punti = [(x * k, y * k) for x, y in anello]
                if len(punti) >= 3:
                    pygame.draw.polygon(img, colore, punti)
            self._evidenziata = (chiave, img)
        superficie.blit(self._evidenziata[1], (x0, y0))
        px, py = info["punto"]
        cx, cy = x0 + px * k, y0 + py * k
        # stato piccolo sulla mappa: cerchio pulsante attorno, così si vede sempre
        if "dim" not in info:
            tutti = [p for an in info["anelli"] for p in an]
            if tutti:
                xs = [p[0] for p in tutti]
                ys = [p[1] for p in tutti]
                info["dim"] = max(max(xs) - min(xs), max(ys) - min(ys))
            else:
                info["dim"] = 0
        dim = info["dim"] * k
        if dim < 34:
            r = max(10, dim * 0.7) + 4 + 3 * math.sin(tempo * 5)
            pygame.draw.circle(superficie, colore, (int(cx), int(cy)), int(r), 3)
            if dim < 4:
                pygame.draw.circle(superficie, colore, (int(cx), int(cy)), 3)
