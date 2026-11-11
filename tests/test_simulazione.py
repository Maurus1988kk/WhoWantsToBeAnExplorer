# -*- coding: utf-8 -*-
"""1000 partite simulate: distribuzione per fascia, opzioni, aiuti, gradi."""

import collections
import os
import random
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

import aiuti as A  # noqa: E402
import config as C  # noqa: E402
from dati import Dati  # noqa: E402
from partita import Partita  # noqa: E402

N_PARTITE = 1000


class TestSimulazione(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dati = Dati()
        cls.esclusi = cls.dati.esclusi_predefiniti()

    def test_mille_partite(self):
        fasce_per_domanda = collections.defaultdict(collections.Counter)
        contatori = collections.Counter()
        for seme in range(N_PARTITE):
            rng = random.Random(seme)
            p = Partita(self.dati, self.esclusi, rng=random.Random(seme * 7919 + 1))
            # --- struttura della partita ---
            self.assertEqual(len(p.domande), 15)
            iso_risposte = [d.stato.iso for d in p.domande]
            self.assertEqual(len(set(iso_risposte)), 15, "stato ripetuto nella stessa partita")
            for d in p.domande:
                fasce_per_domanda[d.numero][d.fascia] += 1
                iso_opz = [o.iso for o in d.opzioni]
                self.assertEqual(len(iso_opz), 4)
                self.assertEqual(len(set(iso_opz)), 4, "opzioni duplicate")
                self.assertEqual(iso_opz.count(d.stato.iso), 1, "risposta giusta assente o doppia")
                self.assertEqual(d.opzioni[d.corretta].iso, d.stato.iso)
                self.assertTrue(all(i not in self.esclusi for i in iso_opz), "stato escluso tra le opzioni")
                distr = [o for o in d.opzioni if o.iso != d.stato.iso]
                if d.numero <= 5:
                    self.assertTrue(all(o.continente != d.stato.continente for o in distr))
                elif d.numero <= 10:
                    self.assertTrue(all(o.continente == d.stato.continente for o in distr))
                else:
                    simili = set(d.stato.simili)
                    contatori["fase3_simili"] += sum(1 for o in distr if o.iso in simili)
                    contatori["fase3_tot"] += len(distr)

            # --- gioco: aiuti a caso e risposte a caso (giuste al 85%) ---
            aiuti_da_usare = {nome: rng.randint(1, 15) for nome in A.AIUTI}
            while not p.finita:
                d = p.domanda
                for nome, quando in aiuti_da_usare.items():
                    if quando == d.numero and p.aiuti[nome]:
                        r = A.usa(p, nome)
                        if nome == "5050":
                            self.assertEqual(len(r), 2)
                            self.assertNotIn(d.corretta, d.eliminate, "il 50:50 ha eliminato la risposta giusta")
                            contatori["5050"] += 1
                        elif nome == "vicino":
                            self.assertIsNotNone(r)
                            self.assertNotEqual(r["iso"], d.stato.iso, "il confinante è lo stato misterioso")
                            altri = [v for v in d.stato.vicini if v["iso"] not in {o.iso for o in d.opzioni}]
                            if altri:
                                self.assertNotIn(r["iso"], {o.iso for o in d.opzioni})
                            contatori["vicino"] += 1
                        else:
                            self.assertTrue(d.bandiera)
                        self.assertFalse(p.aiuti[nome])
                        self.assertFalse(A.usa(p, nome))  # secondo uso: niente
                if rng.random() < 0.03:
                    livello = p.livello
                    p.ritirati()
                    self.assertEqual(p.livello_finale, livello)
                    contatori["ritiri"] += 1
                    break
                if rng.random() < 0.85:
                    scelta = d.corretta
                else:
                    scelta = rng.choice([i for i in range(4) if i != d.corretta and i not in d.eliminate])
                livello_prima = p.livello
                giusta = p.rispondi(scelta)
                self.assertEqual(giusta, scelta == d.corretta)
                if giusta:
                    if p.finita:
                        self.assertTrue(p.vinta)
                        self.assertEqual(p.livello_finale, 15)
                        contatori["vittorie"] += 1
                    else:
                        self.assertTrue(p.avanti())
                else:
                    attesa = 10 if livello_prima >= 10 else (5 if livello_prima >= 5 else 0)
                    self.assertEqual(p.livello_finale, attesa)
                    contatori["sconfitte"] += 1

        # --- distribuzione per fascia: domande 1-3 fascia 1, 4-6 fascia 2, ... ---
        for numero in range(1, 16):
            attesa = C.FASCIA_DOMANDA[numero - 1]
            self.assertEqual(dict(fasce_per_domanda[numero]), {attesa: N_PARTITE}, f"domanda {numero}")
        self.assertEqual(contatori["fase3_simili"], contatori["fase3_tot"])
        self.assertGreater(contatori["5050"], 0)
        self.assertGreater(contatori["vicino"], 0)
        self.assertGreater(contatori["vittorie"], 0)
        self.assertGreater(contatori["sconfitte"], 0)
        print(f"\n  {N_PARTITE} partite simulate: {dict(contatori)}")

    def test_tempo_scaduto(self):
        p = Partita(self.dati, self.esclusi, rng=random.Random(1))
        for _ in range(6):
            p.rispondi(p.domanda.corretta)
            p.avanti()
        p.tempo_scaduto()
        self.assertTrue(p.finita)
        self.assertEqual(p.livello_finale, 5)
        self.assertEqual(p.domanda.esito, "tempo")

    def test_scelta_vicino_preferisce_non_opzioni(self):
        s = self.dati["ITA"]
        primo = s.vicini[0]
        opzioni = [s, self.dati[primo["iso"]], self.dati["BRA"], self.dati["JPN"]]
        v = A.scegli_vicino(s, opzioni)
        self.assertNotEqual(v["iso"], primo["iso"])
        self.assertNotEqual(v["iso"], "ITA")

    def test_timer(self):
        self.assertEqual(C.tempo_limite(1), 45)
        self.assertEqual(C.tempo_limite(5), 45)
        self.assertEqual(C.tempo_limite(6), 60)
        self.assertEqual(C.tempo_limite(10), 60)
        self.assertIsNone(C.tempo_limite(11))


if __name__ == "__main__":
    unittest.main()
