# -*- coding: utf-8 -*-
"""Controlli sulle traduzioni (italiano e inglese)."""

import os
import string
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

import config as C  # noqa: E402
import lingua as L  # noqa: E402
from dati import Dati  # noqa: E402


def segnaposto(testo):
    return {campo for _, campo, _, _ in string.Formatter().parse(testo) if campo}


class TestLingua(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dati = Dati()

    def tearDown(self):
        L.imposta("it")

    def test_stesse_chiavi_e_segnaposto(self):
        it, en = L.TESTI["it"], L.TESTI["en"]
        self.assertEqual(set(it), set(en), "chiavi diverse tra italiano e inglese")
        for chiave in it:
            with self.subTest(chiave=chiave):
                self.assertTrue(it[chiave].strip() and en[chiave].strip())
                self.assertEqual(segnaposto(it[chiave]), segnaposto(en[chiave]))

    def test_tutti_i_testi_si_formattano(self):
        for codice in L.LINGUE:
            L.imposta(codice)
            for chiave, testo in L.TESTI[codice].items():
                with self.subTest(lingua=codice, chiave=chiave):
                    valori = {campo: "X" for campo in segnaposto(testo)}
                    self.assertNotIn("{", L.t(chiave, **valori))

    def test_gradi(self):
        for codice in L.LINGUE:
            L.imposta(codice)
            titoli = [C.titolo_grado(n) for n in range(1, C.NUM_DOMANDE + 1)]
            self.assertEqual(len(titoli), C.NUM_DOMANDE)
            self.assertEqual(len(set(titoli)), C.NUM_DOMANDE, codice)
            self.assertEqual(C.titolo_grado(0), L.t("nessun_grado"))
        L.imposta("it")
        self.assertEqual(C.titolo_grado(1), "Mozzo")
        self.assertEqual(C.titolo_grado(15), "Signore delle Mappe")
        L.imposta("en")
        self.assertEqual(C.titolo_grado(10), "Captain")

    def test_numeri(self):
        L.imposta("it")
        self.assertEqual(C.formatta_miglia(1_000_000), "1.000.000")
        L.imposta("en")
        self.assertEqual(C.formatta_miglia(1_000_000), "1,000,000")
        self.assertEqual(C.formatta_miglia(0), "0")

    def test_nomi_inglesi(self):
        nomi = [s.nome_en for s in self.dati.elenco]
        self.assertTrue(all(n.strip() for n in nomi))
        self.assertEqual(len(nomi), len(set(nomi)), "nomi inglesi duplicati")
        attesi = {"ITA": "Italy", "DEU": "Germany", "CIV": "Ivory Coast", "VAT": "Vatican City",
                  "COD": "Democratic Republic of the Congo", "COG": "Republic of the Congo",
                  "STP": "São Tomé and Príncipe", "MKD": "North Macedonia"}
        for iso, nome in attesi.items():
            self.assertEqual(self.dati[iso].nome_en, nome)
        L.imposta("en")
        self.assertEqual(L.nome(self.dati["ITA"]), "Italy")
        L.imposta("it")
        self.assertEqual(L.nome(self.dati["ITA"]), "Italia")

    def test_luoghi_tradotti(self):
        for s in self.dati.elenco:
            with self.subTest(stato=s.iso):
                self.assertIn(s.continente, L.LUOGHI_EN)
                self.assertIn(s.regione, L.LUOGHI_EN)

    def test_ordine_alfabetico(self):
        L.imposta("en")
        nomi = [L.nome(s) for s in self.dati.ordinati()]
        self.assertEqual(nomi[0], "Afghanistan")
        self.assertLess(nomi.index("San Marino"), nomi.index("São Tomé and Príncipe"))
        self.assertLess(nomi.index("São Tomé and Príncipe"), nomi.index("Saudi Arabia"))
        L.imposta("it")
        self.assertEqual(L.nome(self.dati.ordinati()[0]), "Afghanistan")

    def test_crediti(self):
        self.assertEqual(len(L.CREDITI["it"]), len(L.CREDITI["en"]))

    def test_lingua_di_sistema(self):
        self.assertIn(L.lingua_di_sistema(), L.LINGUE)

    def test_lingua_sconosciuta_ignorata(self):
        L.imposta("en")
        L.imposta("xx")
        self.assertEqual(L.corrente(), "en")


if __name__ == "__main__":
    unittest.main()
