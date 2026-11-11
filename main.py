# -*- coding: utf-8 -*-
"""WhoWantsToBeAnExplorer – quiz di geografia sulle sagome degli stati.

Avvio:  python main.py
Il gioco disegna tutto su una tela 1920x1080 e la scala in proporzione alla
finestra (ridimensionabile; F11 per lo schermo intero). Ciclo a 60 FPS,
animazioni a tempo, nessuna pausa bloccante.
"""

import datetime
import os
import platform
import sys
import traceback

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

import config as C  # noqa: E402
import dati as D  # noqa: E402
import interfaccia as I  # noqa: E402
import lingua as L  # noqa: E402
from audio import Audio  # noqa: E402
from partita import TroppiEsclusi  # noqa: E402


def abilita_dpi():
    """Su Windows evita che il sistema "sfochi" la finestra sugli schermi ad alta densità."""
    if sys.platform == "win32":
        try:
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class App:
    def __init__(self):
        abilita_dpi()
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()
        pygame.display.set_caption(C.APP_NOME)
        try:
            pygame.display.set_icon(pygame.image.load(C.asset("icona.png")))
        except Exception:
            pass
        try:
            dw, dh = pygame.display.get_desktop_sizes()[0]
        except Exception:
            info = pygame.display.Info()
            dw, dh = info.current_w, info.current_h
        k = min(dw * 0.85 / C.LARGHEZZA, dh * 0.85 / C.ALTEZZA, 1.0)
        self.dim_finestra = (int(C.LARGHEZZA * k), int(C.ALTEZZA * k))
        self.schermo = pygame.display.set_mode(self.dim_finestra, pygame.RESIZABLE)
        self.schermo_intero = False
        self.tela = pygame.Surface((C.LARGHEZZA, C.ALTEZZA)).convert()
        self._scalata = None
        self._trasformazione = (0, 0, 1.0)

        self.dati = D.Dati()
        self.impostazioni = C.Impostazioni(self.dati.esclusi_predefiniti())
        self.impostazioni.esclusi &= set(self.dati.stati)
        L.imposta(self.impostazioni.lingua)
        self.classifica = C.Classifica()
        self.audio = Audio(self.impostazioni.audio)
        self.mappa = D.Mappa()
        self.sfondo = I.crea_sfondo().convert()
        self.tempo = 0.0
        self.mouse = (0, 0)
        self.attivo = True
        self.schermata = I.SchermataTitolo(self)
        self.schermata.entra()

    # --- navigazione ---
    def vai(self, nome, **kw):
        if nome == "titolo":
            self.audio.ferma_tensione()
            s = I.SchermataTitolo(self)
        elif nome == "classifica":
            s = I.SchermataClassifica(self)
        elif nome == "impostazioni":
            s = I.SchermataImpostazioni(self, avviso=kw.get("avviso"))
        elif nome == "crediti":
            s = I.SchermataCrediti(self)
        elif nome == "fine":
            s = I.SchermataFine(self, kw["partita"])
        else:
            raise ValueError(nome)
        self._mostra(s)

    def _mostra(self, schermata):
        # l'inserimento di testo serve solo nella schermata finale (nome per la classifica)
        try:
            pygame.key.stop_text_input()
        except pygame.error:
            pass
        self.schermata = schermata
        schermata.entra()

    def nuova_partita(self):
        try:
            s = I.SchermataGioco(self)
        except TroppiEsclusi:
            # troppi stati esclusi (per esempio impostazioni.json modificato a mano)
            self.vai("impostazioni", avviso="troppi_esclusi")
            return
        self._mostra(s)

    def esci(self):
        self.attivo = False

    # --- lingua ---
    def imposta_lingua(self, codice):
        if codice not in L.LINGUE:
            return
        L.imposta(codice)
        self.impostazioni.lingua = codice
        self.impostazioni.salva()

    # --- audio ---
    def imposta_audio(self, valore):
        self.impostazioni.audio = valore
        self.impostazioni.salva()
        self.audio.imposta(valore)
        if valore and isinstance(self.schermata, I.SchermataGioco) and self.schermata.fase in ("domanda", "conferma"):
            self.audio.avvia_tensione()

    def cambia_audio(self):
        self.imposta_audio(not self.impostazioni.audio)

    # --- finestra ---
    def cambia_schermo_intero(self):
        self.schermo_intero = not self.schermo_intero
        if self.schermo_intero:
            self.schermo = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.schermo = pygame.display.set_mode(self.dim_finestra, pygame.RESIZABLE)
        self._scalata = None

    def a_tela(self, pos):
        ox, oy, k = self._trasformazione
        return ((pos[0] - ox) / k, (pos[1] - oy) / k)

    def presenta(self):
        schermo = pygame.display.get_surface()
        sw, sh = schermo.get_size()
        k = min(sw / C.LARGHEZZA, sh / C.ALTEZZA)
        w, h = max(1, int(C.LARGHEZZA * k)), max(1, int(C.ALTEZZA * k))
        ox, oy = (sw - w) // 2, (sh - h) // 2
        self._trasformazione = (ox, oy, k)
        if (w, h) != (sw, sh):
            schermo.fill((0, 0, 0))
        if (w, h) == (C.LARGHEZZA, C.ALTEZZA):
            schermo.blit(self.tela, (ox, oy))
        else:
            if self._scalata is None or self._scalata.get_size() != (w, h):
                self._scalata = pygame.Surface((w, h)).convert()
            pygame.transform.smoothscale(self.tela, (w, h), self._scalata)
            schermo.blit(self._scalata, (ox, oy))
        pygame.display.flip()

    # --- ciclo principale ---
    def esegui(self):
        orologio = pygame.time.Clock()
        while self.attivo:
            dt = min(orologio.tick(C.FPS) / 1000.0, 0.1)
            self.tempo += dt
            self.mouse = self.a_tela(pygame.mouse.get_pos())
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.esci()
                    continue
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                    self.cambia_schermo_intero()
                    continue
                if ev.type == pygame.VIDEORESIZE and not self.schermo_intero:
                    self.dim_finestra = (max(480, ev.w), max(270, ev.h))
                    continue
                pos = self.a_tela(ev.pos) if hasattr(ev, "pos") else self.mouse
                self.schermata.evento(ev, pos)
            self.schermata.aggiorna(dt)
            self.schermata.disegna(self.tela)
            self.presenta()
        self.impostazioni.salva()
        self.audio.ferma_tutto()
        pygame.quit()


def scrivi_log_errore(testo):
    """Salva il dettaglio dell'errore in %APPDATA%\\WhoWantsToBeAnExplorer\\errore.log."""
    percorso = os.path.join(C.cartella_utente(), "errore.log")
    intestazione = (f"{C.APP_NOME} {C.VERSIONE} - {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
                    f"Python {platform.python_version()}, pygame-ce {pygame.version.ver}, "
                    f"{platform.platform()}\n\n")
    try:
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(intestazione + testo)
    except OSError:
        pass
    return percorso


def mostra_errore(messaggio):
    """Finestra di errore di Windows (l'exe non ha console)."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, messaggio, C.APP_NOME, 0x10)  # MB_ICONERROR
        except Exception:
            pass


def main():
    try:
        App().esegui()
    except Exception:
        testo = traceback.format_exc()
        percorso = scrivi_log_errore(testo)
        print(testo, file=sys.stderr)
        try:
            pygame.quit()   # chiude la finestra (anche a schermo intero) prima del messaggio
        except Exception:
            pass
        if getattr(sys, "frozen", False):
            # nell'exe: messaggio comprensibile invece del traceback
            mostra_errore(L.t("errore_fatale", percorso=percorso))
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
