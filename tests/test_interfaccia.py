# -*- coding: utf-8 -*-
"""Prova dell'interfaccia senza finestra (driver video "dummy"): ogni schermata
viene disegnata in entrambe le lingue e si giocano partite complete con il
mouse e la tastiera simulati. Serve pygame-ce; senza, i test vengono saltati."""

import json
import os
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

try:
    import pygame
except ImportError:  # i test dei dati girano anche senza pygame
    pygame = None


def tearDownModule():
    if pygame is not None:
        pygame.quit()


@unittest.skipIf(pygame is None, "pygame-ce non installato")
class TestInterfaccia(unittest.TestCase):
    def setUp(self):
        import config as C
        import interfaccia as I
        import lingua as L
        import main
        self.C, self.I, self.L = C, I, L
        # impostazioni e classifica in una cartella temporanea, mai in %APPDATA%
        self.cartella = tempfile.TemporaryDirectory()
        self._cartella_utente = C.cartella_utente
        C.cartella_utente = lambda: self.cartella.name
        self.app = main.App()

    def tearDown(self):
        # pygame resta inizializzato tra un test e l'altro, come nel gioco vero:
        # font e immagini sono in cache a livello di modulo
        self.app.audio.ferma_tutto()
        self.C.cartella_utente = self._cartella_utente
        self.L.imposta("it")
        self.cartella.cleanup()

    # --- utilità ---
    def disegna(self, fotogrammi=2):
        for _ in range(fotogrammi):
            self.app.schermata.aggiorna(1 / 60)
            self.app.schermata.disegna(self.app.tela)
        self.app.presenta()

    def clic(self, pos):
        pos = (int(pos[0]), int(pos[1]))
        self.app.schermata.evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos), pos)

    def tasto(self, tasto):
        self.app.schermata.evento(pygame.event.Event(pygame.KEYDOWN, key=tasto, mod=0, unicode=""), (0, 0))

    def scrivi_testo(self, testo):
        self.app.schermata.evento(pygame.event.Event(pygame.TEXTINPUT, text=testo), (0, 0))

    def rispondi(self, gioco, indice):
        """Sceglie una risposta, la conferma e arriva alla rivelazione."""
        gioco.seleziona(indice)
        self.assertEqual(gioco.fase, "conferma")
        self.disegna()
        self.tasto(pygame.K_RETURN)
        self.assertEqual(gioco.fase, "suspense")
        self.disegna()
        gioco.aggiorna(self.C.DURATA_SUSPENSE + 0.01)
        self.assertEqual(gioco.fase, "esito")
        self.disegna()
        gioco.aggiorna(self.C.DURATA_ESITO + 0.01)
        self.assertEqual(gioco.fase, "rivelazione")
        self.disegna()

    # --- test ---
    def test_schermate_in_entrambe_le_lingue(self):
        for codice in self.L.LINGUE:
            with self.subTest(lingua=codice):
                self.app.imposta_lingua(codice)
                for nome in ("titolo", "classifica", "impostazioni", "crediti"):
                    self.app.vai(nome)
                    self.disegna()

    def test_cambio_lingua_dal_titolo(self):
        titolo = self.app.schermata
        self.assertIsInstance(titolo, self.I.SchermataTitolo)
        for codice in ("en", "it", "en"):
            self.clic(titolo.btn_lingue[codice].rect.center)
            self.assertEqual(self.L.corrente(), codice)
            self.disegna()
        with open(self.app.impostazioni.percorso, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["lingua"], "en")

    def test_partita_vinta_con_aiuti(self):
        for n, codice in enumerate(self.L.LINGUE, start=1):
            with self.subTest(lingua=codice):
                self.app.imposta_lingua(codice)
                self.app.nuova_partita()
                gioco = self.app.schermata
                for nome in ("5050", "vicino", "bandiera"):
                    gioco.usa_aiuto(nome)
                    self.disegna()
                for _ in range(self.C.NUM_DOMANDE):
                    self.rispondi(gioco, gioco.partita.domanda.corretta)
                    self.tasto(pygame.K_RETURN)
                fine = self.app.schermata
                self.assertIsInstance(fine, self.I.SchermataFine)
                self.assertTrue(fine.partita.vinta)
                self.disegna(10)
                self.scrivi_testo("Ada")
                self.tasto(pygame.K_RETURN)
                # a parità di miglia la vittoria precedente resta davanti
                self.assertEqual(fine.salvato, n)
                self.disegna()
                self.app.vai("classifica")
                self.disegna()

    def test_sconfitta_e_ritiro(self):
        for codice in self.L.LINGUE:
            with self.subTest(lingua=codice):
                self.app.imposta_lingua(codice)
                # errore alla prima domanda
                self.app.nuova_partita()
                gioco = self.app.schermata
                d = gioco.partita.domanda
                sbagliata = next(i for i in range(4) if i != d.corretta)
                self.rispondi(gioco, sbagliata)
                self.assertEqual(gioco.partita.livello_finale, 0)
                self.tasto(pygame.K_RETURN)
                self.assertIsInstance(self.app.schermata, self.I.SchermataFine)
                self.disegna()
                # sei risposte giuste, poi ritiro con Esc e Y (= Yes)
                self.tasto(pygame.K_RETURN)
                gioco = self.app.schermata
                for _ in range(6):
                    self.rispondi(gioco, gioco.partita.domanda.corretta)
                    self.tasto(pygame.K_RETURN)
                self.tasto(pygame.K_ESCAPE)
                self.assertEqual(gioco.fase, "ritiro")
                self.disegna()
                self.tasto(pygame.K_y)
                self.assertTrue(gioco.partita.ritirata)
                self.assertEqual(gioco.partita.livello_finale, 6)
                gioco.aggiorna(self.C.DURATA_ESITO + 0.01)
                self.disegna()
                self.tasto(pygame.K_RETURN)
                self.assertIsInstance(self.app.schermata, self.I.SchermataFine)
                self.disegna()

    def test_tempo_scaduto(self):
        self.app.impostazioni.timer = True
        for codice in self.L.LINGUE:
            with self.subTest(lingua=codice):
                self.app.imposta_lingua(codice)
                self.app.nuova_partita()
                gioco = self.app.schermata
                self.disegna()
                gioco.timer = 0.01
                gioco.aggiorna(0.05)
                self.assertEqual(gioco.partita.domanda.esito, "tempo")
                self.disegna()
                gioco.aggiorna(self.C.DURATA_ESITO + 0.01)
                self.disegna()

    def test_impostazioni(self):
        for codice in self.L.LINGUE:
            with self.subTest(lingua=codice):
                self.app.vai("impostazioni")
                imp = self.app.schermata
                self.clic(imp.btn_lingue[codice].rect.center)
                self.assertEqual(self.L.corrente(), codice)
                for sw in (imp.sw_timer, imp.sw_conferma, imp.sw_audio):
                    self.clic(sw.rect.center)
                    self.disegna()
                    self.clic(sw.rect.center)
                for b in imp.btn_filtri:
                    self.clic(b.rect.center)
                    self.disegna()
                self.clic(imp.btn_filtri[0].rect.center)
                imp.evento(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-3), (0, 0))
                self.disegna()
                # esclude e reinclude il primo stato visibile della lista
                cella = (imp.LISTA.x + 30, imp.LISTA.y + 10 + imp.RIGA // 2)
                stato = imp._stato_in(cella)
                self.assertIsNotNone(stato)
                prima = stato.iso in self.app.impostazioni.esclusi
                self.clic(cella)
                self.assertNotEqual(stato.iso in self.app.impostazioni.esclusi, prima)
                self.clic(cella)
                self.assertEqual(stato.iso in self.app.impostazioni.esclusi, prima)
                self.clic(imp.btn_ripristina.rect.center)
                self.disegna()
                self.clic(imp.btn_indietro.rect.center)
                self.assertIsInstance(self.app.schermata, self.I.SchermataTitolo)

    def test_troppi_esclusi(self):
        tutti = set(self.app.dati.stati)
        self.app.impostazioni.esclusi = tutti - set(sorted(tutti)[:5])
        self.app.nuova_partita()
        self.assertIsInstance(self.app.schermata, self.I.SchermataImpostazioni)
        self.assertEqual(self.app.schermata.messaggio, "troppi_esclusi")
        self.disegna()

    def test_cache_immagini_piena(self):
        """Regressione: con la cache piena immagine_adattata andava in KeyError
        (succedeva tornando più volte al titolo, che usa dimensioni casuali)."""
        import dati as D
        for k in range(450):
            img = D.immagine_adattata("sagome/ITA.png", 100 + k, 100)
            self.assertIsNotNone(img)
        for _ in range(20):
            self.app.vai("titolo")
            self.disegna(1)

    def test_nomi_entrano_nelle_caselle(self):
        """Ogni nome, in entrambe le lingue, entra nella casella di risposta."""
        larghezza = self.I.SchermataGioco.CASELLE[0].width - 150
        for codice in self.L.LINGUE:
            self.L.imposta(codice)
            for s in self.app.dati.elenco:
                nome = self.L.nome(s)
                dim = self.I.dimensione_adatta(nome, larghezza, 32, "bold", 18)
                with self.subTest(lingua=codice, stato=s.iso):
                    self.assertLessEqual(self.I.font(dim, "bold").size(nome)[0], larghezza)


if __name__ == "__main__":
    unittest.main()
