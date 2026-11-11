# -*- coding: utf-8 -*-
"""Gestione dei suoni (generati da tools/genera_suoni.py). Se il computer non
ha una scheda audio il gioco funziona lo stesso, in silenzio."""

import config

SUONI = ("tensione", "suspense", "blocco", "giusta", "sbagliata", "aiuto", "vittoria", "clic")
VOLUME = 0.7


class Audio:
    def __init__(self, attivo=True):
        self.attivo = attivo
        self.disponibile = False
        self.suoni = {}
        self._canale_tensione = None
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            for nome in SUONI:
                s = pygame.mixer.Sound(config.asset("suoni", nome + ".wav"))
                s.set_volume(VOLUME if nome != "tensione" else VOLUME * 0.8)
                self.suoni[nome] = s
            self.disponibile = True
        except Exception:
            self.disponibile = False

    def suona(self, nome):
        if self.attivo and self.disponibile and nome in self.suoni:
            try:
                self.suoni[nome].play()
            except Exception:
                pass

    def avvia_tensione(self):
        """Sottofondo di attesa in loop (non riparte se sta già suonando)."""
        if not (self.attivo and self.disponibile):
            return
        if self._canale_tensione is not None and self._canale_tensione.get_busy():
            return
        try:
            self._canale_tensione = self.suoni["tensione"].play(loops=-1, fade_ms=600)
        except Exception:
            self._canale_tensione = None

    def ferma_tensione(self, fade_ms=250):
        if self._canale_tensione is not None:
            try:
                self._canale_tensione.fadeout(fade_ms)
            except Exception:
                pass
            self._canale_tensione = None

    def ferma_tutto(self):
        self.ferma_tensione(0)
        if self.disponibile:
            try:
                import pygame
                pygame.mixer.stop()
            except Exception:
                pass

    def imposta(self, attivo):
        self.attivo = attivo
        if not attivo:
            self.ferma_tutto()
