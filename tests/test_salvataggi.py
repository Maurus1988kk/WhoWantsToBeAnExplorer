# -*- coding: utf-8 -*-
"""Impostazioni e classifica: salvataggio, rilettura e file danneggiati."""

import json
import os
import sys
import tempfile
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

import config as C  # noqa: E402
import lingua as L  # noqa: E402


class TestSalvataggi(unittest.TestCase):
    def setUp(self):
        self.cartella = tempfile.TemporaryDirectory()
        self.p_imp = os.path.join(self.cartella.name, "impostazioni.json")
        self.p_cla = os.path.join(self.cartella.name, "classifica.json")

    def tearDown(self):
        L.imposta("it")
        self.cartella.cleanup()

    def scrivi(self, percorso, contenuto):
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(contenuto)

    # --- impostazioni ---
    def test_impostazioni_andata_e_ritorno(self):
        imp = C.Impostazioni({"KIR"}, percorso=self.p_imp)
        imp.timer, imp.conferma, imp.audio, imp.lingua = True, False, False, "en"
        imp.esclusi = {"KIR", "ITA"}
        self.assertTrue(imp.salva())
        self.assertFalse(os.path.exists(self.p_imp + ".tmp"))
        di_nuovo = C.Impostazioni({"KIR"}, percorso=self.p_imp)
        self.assertEqual((di_nuovo.timer, di_nuovo.conferma, di_nuovo.audio, di_nuovo.lingua),
                         (True, False, False, "en"))
        self.assertEqual(di_nuovo.esclusi, {"KIR", "ITA"})

    def test_impostazioni_danneggiate(self):
        for contenuto in ("", "{non json", "[1, 2, 3]", "null", '"testo"',
                          '{"timer": "si", "audio": 1, "lingua": "xx", "stati_esclusi": "ITA"}',
                          '{"stati_esclusi": [1, null, "FRA"]}'):
            with self.subTest(contenuto=contenuto):
                self.scrivi(self.p_imp, contenuto)
                imp = C.Impostazioni({"KIR"}, percorso=self.p_imp)
                self.assertIs(imp.timer, False)
                self.assertIs(imp.conferma, True)
                self.assertIs(imp.audio, True)
                self.assertIn(imp.lingua, L.LINGUE)
                self.assertTrue(all(isinstance(x, str) for x in imp.esclusi))

    def test_impostazioni_senza_file(self):
        imp = C.Impostazioni({"KIR"}, percorso=self.p_imp)
        self.assertEqual(imp.esclusi, {"KIR"})
        self.assertIn(imp.lingua, L.LINGUE)

    # --- classifica ---
    def test_classifica_ordine_e_limite(self):
        cl = C.Classifica(self.p_cla)
        for livello in (3, 15, 0, 7, 10, 1, 2, 4, 5, 6, 8, 9):
            if cl.entra(C.miglia_grado(livello)):
                cl.aggiungi(f"Giocatore {livello}", livello)
        self.assertEqual(len(cl.voci), C.Classifica.MAX)
        miglia = [v["miglia"] for v in cl.voci]
        self.assertEqual(miglia, sorted(miglia, reverse=True))
        self.assertEqual(cl.voci[0]["grado"], 15)
        di_nuovo = C.Classifica(self.p_cla)
        self.assertEqual(di_nuovo.voci, cl.voci)

    def test_classifica_nome_vuoto(self):
        L.imposta("en")
        voce = C.Classifica(self.p_cla).aggiungi("   ", 3)
        self.assertEqual(voce["nome"], "Anonymous")

    def test_classifica_danneggiata(self):
        for contenuto in ("", "{rotto", '{"a": 1}', "42"):
            with self.subTest(contenuto=contenuto):
                self.scrivi(self.p_cla, contenuto)
                self.assertEqual(C.Classifica(self.p_cla).voci, [])
        voci = [
            {"nome": "Buona", "grado": 5, "miglia": 1000, "data": "2026-01-01 10:00"},
            {"nome": "Miglia sbagliate", "grado": 5, "miglia": "tante"},
            {"nome": "Grado assurdo", "grado": 99, "miglia": 5},
            {"nome": "Negativa", "grado": 1, "miglia": -5},
            "non un dizionario",
            None,
            {"nome": 12345, "grado": "10", "miglia": "32000"},
        ]
        self.scrivi(self.p_cla, json.dumps(voci))
        cl = C.Classifica(self.p_cla)
        self.assertEqual([v["nome"] for v in cl.voci], ["12345", "Buona"])
        self.assertEqual(cl.voci[0]["grado"], 10)

    def test_classifica_troppo_lunga_nel_file(self):
        # un file con più di 10 voci in disordine: si tengono le 10 migliori
        voci = [{"nome": str(i), "grado": i, "miglia": C.miglia_grado(i), "data": ""} for i in range(1, 16)]
        self.scrivi(self.p_cla, json.dumps(voci))
        cl = C.Classifica(self.p_cla)
        self.assertEqual([v["grado"] for v in cl.voci], list(range(15, 5, -1)))


if __name__ == "__main__":
    unittest.main()
