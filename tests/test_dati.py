# -*- coding: utf-8 -*-
"""Controlli sull'integrità dei dati generati (assets/)."""

import json
import os
import struct
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

import config as C  # noqa: E402
from dati import Dati  # noqa: E402
from partita import distrattori_propri  # noqa: E402


def dimensioni_png(percorso):
    with open(percorso, "rb") as f:
        testa = f.read(24)
    assert testa[:8] == b"\x89PNG\r\n\x1a\n", percorso
    return struct.unpack(">II", testa[16:24])


class TestDati(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dati = Dati()
        cls.esclusi = cls.dati.esclusi_predefiniti()
        cls.pool = cls.dati.giocabili(cls.esclusi)

    def test_elenco_stati(self):
        iso = set(self.dati.stati)
        self.assertEqual(len(iso), 197)  # 193 ONU + Vaticano, Kosovo, Palestina, Taiwan
        for k in ("VAT", "XKX", "PSE", "TWN", "ITA", "SOM", "CYP"):
            self.assertIn(k, iso)
        for k in ("ESH", "GRL", "PRI", "SOL", "CYN", "GUF"):
            self.assertNotIn(k, iso)
        self.assertEqual(self.esclusi, {"KIR", "TUV", "MHL", "MDV", "NRU", "PLW", "FSM", "SYC"})

    def test_nomi_unici_e_corretti(self):
        nomi = [s.nome for s in self.dati.elenco]
        self.assertEqual(len(nomi), len(set(nomi)))
        attesi = {"COD": "Repubblica Democratica del Congo", "SWZ": "Eswatini",
                  "MKD": "Macedonia del Nord", "TLS": "Timor Est", "VAT": "Città del Vaticano"}
        for k, v in attesi.items():
            self.assertEqual(self.dati[k].nome, v)

    def test_file_e_campi(self):
        for s in self.dati.elenco:
            with self.subTest(stato=s.iso):
                p = C.asset(*s.sagoma.split("/"))
                self.assertTrue(os.path.exists(p))
                w, h = dimensioni_png(p)
                self.assertEqual(max(w, h), 1024)
                self.assertTrue(os.path.exists(C.asset(*s.bandiera.split("/"))))
                self.assertIn(s.fascia, (1, 2, 3, 4, 5))
                self.assertTrue(s.continente and s.regione)

    def test_vicini(self):
        for s in self.dati.elenco:
            with self.subTest(stato=s.iso):
                self.assertGreaterEqual(len(s.vicini), 1, "nessun vicino o paese più vicino")
                self.assertLessEqual(len(s.vicini), 3)
                for v in s.vicini:
                    self.assertNotEqual(v["iso"], s.iso)
                    self.assertIn(v["iso"], self.dati.stati)
                    self.assertIn(v["tipo"], ("confinante", "vicino", "vicino_isola"))
                    self.assertTrue(os.path.exists(C.asset(*v["immagine"].split("/"))))
                    ex, ey = v["etichetta"]
                    self.assertTrue(0 <= ex <= 1 and 0 <= ey <= 1)
                if s.confinanti:
                    self.assertEqual(s.vicini[0]["tipo"], "confinante")
                else:
                    self.assertEqual(s.vicini[0]["tipo"], "vicino_isola")

    def test_confinanti_noti(self):
        conf = lambda k: set(self.dati[k].confinanti)  # noqa: E731
        self.assertTrue({"FRA", "CHE", "AUT", "SVN", "SMR", "VAT"} <= conf("ITA"))
        self.assertEqual(conf("PRT"), {"ESP"})
        self.assertEqual(conf("LSO"), {"ZAF"})
        self.assertNotIn("FRA", conf("BRA"))      # la Guyana francese non fa parte della sagoma
        self.assertEqual(conf("ISL"), set())
        self.assertEqual(conf("JPN"), set())

    def test_fasce(self):
        tutte = {f: 0 for f in range(1, 6)}
        for s in self.dati.elenco:
            tutte[s.fascia] += 1
        giocabili = self.dati.conteggio_fasce(self.esclusi)
        for f in range(1, 6):
            self.assertGreaterEqual(tutte[f], 20, f"fascia {f}")
            self.assertGreaterEqual(giocabili[f], 20, f"fascia {f} (giocabili)")
        for k in ("ITA", "CHL", "JPN", "AUS", "IND", "BRA", "USA", "RUS", "GBR", "ISL", "NZL", "GRC",
                  "NOR", "ESP", "FRA"):
            self.assertEqual(self.dati[k].fascia, 1, k)
        for k in ("BFA", "CAF", "GNB", "TKM", "LSO", "VCT", "LIE"):
            self.assertEqual(self.dati[k].fascia, 5, k)

    def test_similarita(self):
        for s in self.dati.elenco:
            with self.subTest(stato=s.iso):
                self.assertEqual(len(s.simili), 15)
                self.assertNotIn(s.iso, s.simili)
                self.assertEqual(len(set(s.simili)), 15)

    def test_distrattori_per_fase(self):
        """Almeno 3 distrattori validi per ogni fase, per ogni stato giocabile."""
        for s in self.pool:
            for fase in (1, 2, 3):
                with self.subTest(stato=s.iso, fase=fase):
                    cand = distrattori_propri(s, fase, self.pool)
                    validi = [c for c in cand if c.iso != s.iso and c.iso not in self.esclusi]
                    self.assertGreaterEqual(len({c.iso for c in validi}), 3)
                    if fase == 1:
                        self.assertTrue(all(c.continente != s.continente for c in validi))
                    elif fase == 2:
                        self.assertTrue(all(c.continente == s.continente for c in validi))
                    else:
                        self.assertTrue(all(c.iso in s.simili for c in validi))

    def test_mappa(self):
        with open(C.asset("mondo", "stati_mappa.json"), encoding="utf-8") as f:
            m = json.load(f)
        for s in self.dati.elenco:
            self.assertIn(s.iso, m["stati"])
            self.assertTrue(m["stati"][s.iso]["anelli"], s.iso)
        self.assertTrue(os.path.exists(C.asset("mondo", "mappa.png")))

    def test_altri_asset(self):
        for nome in ("tensione", "suspense", "blocco", "giusta", "sbagliata", "aiuto", "vittoria", "clic"):
            self.assertTrue(os.path.exists(C.asset("suoni", nome + ".wav")), nome)
        for nome in ("Montserrat-Regular.ttf", "Montserrat-SemiBold.ttf", "Montserrat-Bold.ttf",
                     "Montserrat-ExtraBold.ttf", "OFL.txt"):
            self.assertTrue(os.path.exists(C.asset("font", nome)), nome)
        self.assertTrue(os.path.exists(C.asset("icona.ico")))


if __name__ == "__main__":
    unittest.main()
