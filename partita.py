# -*- coding: utf-8 -*-
"""Logica di una partita: scelta degli stati, distrattori, risposte, gradi.
Nessuna dipendenza da pygame: si può simulare e testare senza finestra."""

import random

import config

LETTERE = "ABCD"
MINIMO_STATI = 20


class TroppiEsclusi(ValueError):
    """Gli stati giocabili non bastano per una partita."""


class Domanda:
    def __init__(self, numero, stato, opzioni):
        self.numero = numero              # 1..15
        self.stato = stato                # Stato da indovinare
        self.opzioni = opzioni            # lista di 4 Stato
        self.corretta = opzioni.index(stato)
        self.eliminate = set()            # indici tolti dal 50:50
        self.vicino = None                # candidato mostrato dall'aiuto confinante
        self.bandiera = False             # aiuto bandiera usato su questa domanda
        self.scelta = None                # indice scelto
        self.esito = None                 # None, "giusta", "sbagliata", "tempo", "ritiro"

    @property
    def fascia(self):
        return self.stato.fascia

    @property
    def fase(self):
        """Fase dei distrattori: 1 (domande 1-5), 2 (6-10), 3 (11-15)."""
        return 1 if self.numero <= 5 else (2 if self.numero <= 10 else 3)


# ---------------------------------------------------------------------------
# Distrattori
# ---------------------------------------------------------------------------
def distrattori_fase1(stato, pool, rng):
    """Domande 1-5: stati di altri continenti, a caso."""
    altri = [s for s in pool if s.continente != stato.continente and s.iso != stato.iso]
    rng.shuffle(altri)
    return altri


def distrattori_fase2(stato, pool, rng):
    """Domande 6-10: stessa regione, poi stesso continente."""
    stessa_regione = [s for s in pool if s.regione == stato.regione and s.iso != stato.iso]
    stesso_cont = [s for s in pool if s.continente == stato.continente
                   and s.regione != stato.regione and s.iso != stato.iso]
    rng.shuffle(stessa_regione)
    rng.shuffle(stesso_cont)
    return stessa_regione + stesso_cont


def distrattori_fase3(stato, pool, rng):
    """Domande 11-15: le sagome più simili, preferibilmente dello stesso continente.
    Un po' di casualità tra i primi candidati rende le partite diverse."""
    per_iso = {s.iso: s for s in pool}
    simili = [per_iso[i] for i in stato.simili if i in per_iso and i != stato.iso]
    stessi = [s for s in simili if s.continente == stato.continente]
    altri = [s for s in simili if s.continente != stato.continente]
    ordinati = stessi + altri
    testa = ordinati[:5]
    rng.shuffle(testa)
    return testa + ordinati[5:]


def candidati_distrattori(stato, fase, pool, rng):
    """Lista (in ordine di preferenza, senza duplicati) di possibili distrattori.
    In coda aggiunge ripieghi, così ce ne sono sempre almeno 3."""
    if fase == 1:
        lista = distrattori_fase1(stato, pool, rng)
    elif fase == 2:
        lista = distrattori_fase2(stato, pool, rng)
    else:
        lista = distrattori_fase3(stato, pool, rng)
        lista += distrattori_fase2(stato, pool, rng)
    resto = [s for s in pool if s.iso != stato.iso]
    rng.shuffle(resto)
    lista += resto
    visti, out = set(), []
    for s in lista:
        if s.iso not in visti and s.iso != stato.iso:
            visti.add(s.iso)
            out.append(s)
    return out


def distrattori_propri(stato, fase, pool):
    """Distrattori "veri" della fase (senza ripieghi): usato dai test."""
    rng = random.Random(0)
    if fase == 1:
        return distrattori_fase1(stato, pool, rng)
    if fase == 2:
        return distrattori_fase2(stato, pool, rng)
    return distrattori_fase3(stato, pool, rng)


# ---------------------------------------------------------------------------
# Partita
# ---------------------------------------------------------------------------
class Partita:
    def __init__(self, dati, esclusi=(), rng=None):
        self.dati = dati
        self.rng = rng or random.Random()
        self.pool = dati.giocabili(set(esclusi))
        if len(self.pool) < MINIMO_STATI:
            raise TroppiEsclusi(f"Troppi stati esclusi: servono almeno {MINIMO_STATI} stati giocabili")
        self.domande = self._genera_domande()
        self.indice = 0                   # domanda corrente (0..14)
        self.livello = 0                  # risposte giuste finora
        self.aiuti = {"5050": True, "vicino": True, "bandiera": True}
        self.finita = False
        self.vinta = False
        self.ritirata = False
        self.livello_finale = 0

    # --- generazione ---
    def _stato_per_fascia(self, fascia, usati):
        pool = [s for s in self.pool if s.fascia == fascia and s.iso not in usati]
        if not pool:
            # ripiego: fascia più vicina con stati disponibili
            for d in (1, -1, 2, -2, 3, -3, 4, -4):
                pool = [s for s in self.pool if s.fascia == fascia + d and s.iso not in usati]
                if pool:
                    break
        return self.rng.choice(pool)

    def _genera_domande(self):
        domande = []
        usati = set()
        for numero in range(1, config.NUM_DOMANDE + 1):
            stato = self._stato_per_fascia(config.FASCIA_DOMANDA[numero - 1], usati)
            usati.add(stato.iso)
            fase = 1 if numero <= 5 else (2 if numero <= 10 else 3)
            cand = candidati_distrattori(stato, fase, self.pool, self.rng)
            opzioni = [stato] + cand[:3]
            self.rng.shuffle(opzioni)
            domande.append(Domanda(numero, stato, opzioni))
        return domande

    # --- stato corrente ---
    @property
    def domanda(self):
        return self.domande[self.indice]

    @property
    def numero(self):
        return self.indice + 1

    def soglia_raggiunta(self):
        """Ultimo grado di sicurezza raggiunto (0 se nessuno)."""
        raggiunte = [s for s in config.SOGLIE if self.livello >= s]
        return max(raggiunte) if raggiunte else 0

    # --- azioni ---
    def rispondi(self, indice):
        """Registra la risposta definitiva. Restituisce True se è giusta."""
        d = self.domanda
        if self.finita or d.esito is not None:
            raise RuntimeError("Domanda già chiusa")
        if indice in d.eliminate:
            raise ValueError("Risposta eliminata dal 50:50")
        d.scelta = indice
        if indice == d.corretta:
            d.esito = "giusta"
            self.livello = d.numero
            if d.numero == config.NUM_DOMANDE:
                self.finita = True
                self.vinta = True
                self.livello_finale = config.NUM_DOMANDE
            return True
        d.esito = "sbagliata"
        self._sconfitta()
        return False

    def tempo_scaduto(self):
        d = self.domanda
        if d.esito is None:
            d.esito = "tempo"
            self._sconfitta()

    def _sconfitta(self):
        self.finita = True
        self.livello_finale = self.soglia_raggiunta()

    def ritirati(self):
        d = self.domanda
        if d.esito is None:
            d.esito = "ritiro"
        self.finita = True
        self.ritirata = True
        self.livello_finale = self.livello

    def avanti(self):
        """Passa alla domanda successiva (dopo una risposta giusta)."""
        if not self.finita and self.domanda.esito == "giusta" and self.indice < config.NUM_DOMANDE - 1:
            self.indice += 1
            return True
        return False

    def domande_giocate(self):
        return [d for d in self.domande if d.esito is not None]
