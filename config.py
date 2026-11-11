# -*- coding: utf-8 -*-
"""Costanti, percorsi, impostazioni e classifica di WhoWantsToBeAnExplorer."""

import datetime
import json
import os
import sys

import lingua

APP_NOME = "WhoWantsToBeAnExplorer"
VERSIONE = "1.1.0"

# Risoluzione "logica": tutto viene disegnato su questa tela e poi scalato
# in proporzione alla finestra.
LARGHEZZA, ALTEZZA = 1920, 1080
FPS = 60


def resource_path(relativo):
    """Percorso di una risorsa, valido sia da sorgente sia dentro l'exe di
    PyInstaller (che estrae i file nella cartella temporanea sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relativo)


def asset(*parti):
    return resource_path(os.path.join("assets", *parti))


def cartella_utente():
    """%APPDATA%\\WhoWantsToBeAnExplorer su Windows (altrove ~/.WhoWantsToBeAnExplorer)."""
    base = os.environ.get("APPDATA")
    if base:
        percorso = os.path.join(base, APP_NOME)
    else:
        percorso = os.path.join(os.path.expanduser("~"), "." + APP_NOME)
    try:
        os.makedirs(percorso, exist_ok=True)
    except OSError:
        pass
    return percorso


def scrivi_json(percorso, dati):
    """Scrittura atomica: prima un file temporaneo, poi la sostituzione.
    Se il gioco si chiude a metà, il file vecchio resta integro."""
    temporaneo = percorso + ".tmp"
    try:
        with open(temporaneo, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporaneo, percorso)
        return True
    except OSError:
        try:
            os.remove(temporaneo)
        except OSError:
            pass
        return False


def leggi_json(percorso):
    """Contenuto di un file JSON, oppure None se manca o non si legge."""
    try:
        with open(percorso, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Scala dei gradi (niente denaro: miglia esplorate). I titoli sono in lingua.py.
# ---------------------------------------------------------------------------
MIGLIA = [100, 200, 300, 500, 1_000, 2_000, 4_000, 8_000, 16_000, 32_000,
          64_000, 125_000, 250_000, 500_000, 1_000_000]
SOGLIE = (5, 10)            # gradi di sicurezza
NUM_DOMANDE = len(MIGLIA)

# Fascia di difficoltà per ciascuna delle 15 domande
FASCIA_DOMANDA = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]


def titolo_grado(livello):
    """Titolo del grado nella lingua corrente (livello 0 = nessun grado)."""
    return lingua.grado(livello)


def miglia_grado(livello):
    return MIGLIA[livello - 1] if livello > 0 else 0


def formatta_miglia(n):
    return lingua.numero(n)


def tempo_limite(numero_domanda):
    """Secondi a disposizione (timer attivo): 45 s per 1-5, 60 s per 6-10, illimitato dopo."""
    if numero_domanda <= 5:
        return 45
    if numero_domanda <= 10:
        return 60
    return None


# Pausa di suspense dopo la risposta definitiva (secondi)
DURATA_SUSPENSE = 1.8
DURATA_ESITO = 1.7

# ---------------------------------------------------------------------------
# Colori
# ---------------------------------------------------------------------------
NERO = (0, 0, 0)
BIANCO = (255, 255, 255)
BLU_NOTTE = (6, 12, 32)
BLU_PROFONDO = (10, 22, 56)
BLU_BORDO = (88, 140, 220)
BLU_CHIARO = (160, 200, 255)
ORO = (232, 178, 58)
ORO_CHIARO = (255, 214, 120)
AMBRA = (240, 160, 40)
VERDE = (40, 170, 90)
VERDE_CHIARO = (140, 240, 175)
ROSSO = (196, 52, 44)
ROSSO_CHIARO = (255, 130, 120)
GRIGIO = (120, 130, 150)
GRIGIO_SCURO = (40, 48, 70)
TESTO = (232, 238, 250)
TESTO_TENUE = (150, 165, 195)


# ---------------------------------------------------------------------------
# Impostazioni
# ---------------------------------------------------------------------------
class Impostazioni:
    """Impostazioni salvate in %APPDATA%\\WhoWantsToBeAnExplorer\\impostazioni.json."""

    def __init__(self, esclusi_predefiniti, percorso=None):
        self.esclusi_predefiniti = set(esclusi_predefiniti)
        self.timer = False
        self.conferma = True
        self.audio = True
        self.lingua = None          # None = lingua del sistema
        self.esclusi = set(self.esclusi_predefiniti)
        self.percorso = percorso or os.path.join(cartella_utente(), "impostazioni.json")
        self.carica()
        if self.lingua not in lingua.LINGUE:
            self.lingua = lingua.lingua_di_sistema()

    def carica(self):
        d = leggi_json(self.percorso)
        if not isinstance(d, dict):
            return
        for chiave in ("timer", "conferma", "audio"):
            if isinstance(d.get(chiave), bool):
                setattr(self, chiave, d[chiave])
        if d.get("lingua") in lingua.LINGUE:
            self.lingua = d["lingua"]
        if isinstance(d.get("stati_esclusi"), list):
            self.esclusi = {x for x in d["stati_esclusi"] if isinstance(x, str)}

    def salva(self):
        return scrivi_json(self.percorso, {
            "lingua": self.lingua,
            "timer": self.timer,
            "conferma": self.conferma,
            "audio": self.audio,
            "stati_esclusi": sorted(self.esclusi),
        })

    def ripristina_esclusi(self):
        self.esclusi = set(self.esclusi_predefiniti)


# ---------------------------------------------------------------------------
# Classifica locale (10 migliori partite)
# ---------------------------------------------------------------------------
class Classifica:
    MAX = 10

    def __init__(self, percorso=None):
        self.percorso = percorso or os.path.join(cartella_utente(), "classifica.json")
        self.voci = []
        self.carica()

    def carica(self):
        d = leggi_json(self.percorso)
        self.voci = []
        if isinstance(d, list):
            for v in d:
                voce = self._valida(v)
                if voce is not None:
                    self.voci.append(voce)
        self._ordina()
        self.voci = self.voci[: self.MAX]

    @staticmethod
    def _valida(v):
        """Voce ripulita, oppure None se non è valida (file modificato a mano)."""
        if not isinstance(v, dict):
            return None
        try:
            grado = int(v.get("grado", 0))
            miglia = int(v.get("miglia", 0))
        except (TypeError, ValueError):
            return None
        if not 0 <= grado <= NUM_DOMANDE or miglia < 0:
            return None
        return {
            "nome": str(v.get("nome", ""))[:20],
            "grado": grado,
            "titolo": str(v.get("titolo", "")),
            "miglia": miglia,
            "data": str(v.get("data", "")),
        }

    def _ordina(self):
        # più miglia prima; a parità, la partita più vecchia resta davanti
        self.voci.sort(key=lambda v: (-v["miglia"], v["data"]))

    def salva(self):
        return scrivi_json(self.percorso, self.voci)

    def entra(self, miglia):
        """True se un punteggio entrerebbe tra i primi 10."""
        if len(self.voci) < self.MAX:
            return True
        return miglia > int(self.voci[-1].get("miglia", 0))

    def aggiungi(self, nome, livello):
        voce = {
            "nome": nome.strip()[:20] or lingua.t("anonimo"),
            "grado": livello,
            "titolo": titolo_grado(livello),
            "miglia": miglia_grado(livello),
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.voci.append(voce)
        self._ordina()
        self.voci = self.voci[: self.MAX]
        self.salva()
        return voce if voce in self.voci else None
