# -*- coding: utf-8 -*-
"""Testi del gioco in italiano e in inglese.

Nessuna dipendenza da pygame: i test controllano che le due lingue abbiano
le stesse chiavi e gli stessi segnaposto.

Uso:
    import lingua as L
    L.imposta("en")
    L.t("domanda_n", n=3, totale=15)   # "QUESTION 3 OF 15"
"""

import locale
import os
import sys
import unicodedata

LINGUE = ("it", "en")
NOMI_LINGUE = {"it": "Italiano", "en": "English"}

_corrente = "it"


def imposta(codice):
    """Cambia la lingua corrente (codici sconosciuti vengono ignorati)."""
    global _corrente
    if codice in LINGUE:
        _corrente = codice


def corrente():
    return _corrente


def lingua_di_sistema():
    """"it" se il sistema è in italiano, altrimenti "en"."""
    if sys.platform == "win32":
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return "it" if (langid & 0x3FF) == 0x10 else "en"   # 0x10 = LANG_ITALIAN
        except Exception:
            pass
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        valore = os.environ.get(var, "")
        if valore:
            return "it" if valore.lower().startswith("it") else "en"
    try:
        nome = (locale.getlocale()[0] or "").lower()
        if nome.startswith(("it", "italian")):
            return "it"
    except Exception:
        pass
    return "en"


def t(chiave, **valori):
    """Testo tradotto; con valori, riempie i segnaposto {nome}."""
    testo = TESTI[_corrente].get(chiave)
    if testo is None:
        testo = TESTI["it"][chiave]
    return testo.format(**valori) if valori else testo


def nome(stato):
    """Nome dello stato nella lingua corrente."""
    if _corrente == "en":
        return getattr(stato, "nome_en", "") or stato.nome
    return stato.nome


def luogo(testo):
    """Continente o regione (in stati.json sono in italiano)."""
    if _corrente == "en":
        return LUOGHI_EN.get(testo, testo)
    return testo


def grado(livello):
    """Titolo del grado (livello 0 = nessun grado)."""
    if livello <= 0:
        return t("nessun_grado")
    return GRADI[_corrente][livello - 1]


def numero(n):
    """1.000 in italiano, 1,000 in inglese."""
    s = f"{int(n):,}"
    return s.replace(",", ".") if _corrente == "it" else s


def chiave_ordinamento(testo):
    """Ordine alfabetico che ignora accenti e maiuscole (São Tomé tra le S)."""
    base = unicodedata.normalize("NFKD", testo)
    return "".join(c for c in base if not unicodedata.combining(c)).casefold()


def crediti():
    return CREDITI[_corrente]


# ---------------------------------------------------------------------------
# Gradi (miglia esplorate)
# ---------------------------------------------------------------------------
GRADI = {
    "it": ["Mozzo", "Marinaio", "Vedetta", "Timoniere", "Cartografo", "Nostromo", "Navigatore",
           "Secondo Ufficiale", "Primo Ufficiale", "Capitano", "Ammiraglio", "Esploratore",
           "Grande Esploratore", "Leggenda dei Mari", "Signore delle Mappe"],
    "en": ["Deckhand", "Sailor", "Lookout", "Helmsman", "Cartographer", "Boatswain", "Navigator",
           "Second Mate", "First Mate", "Captain", "Admiral", "Explorer",
           "Great Explorer", "Legend of the Seas", "Master of Maps"],
}

# Continenti e regioni di stati.json -> inglese
LUOGHI_EN = {
    "Europa": "Europe",
    "Asia": "Asia",
    "Africa": "Africa",
    "America del Nord": "North America",
    "America del Sud": "South America",
    "Oceania": "Oceania",
    "Europa meridionale": "Southern Europe",
    "Europa occidentale": "Western Europe",
    "Europa settentrionale": "Northern Europe",
    "Europa orientale": "Eastern Europe",
    "Asia occidentale": "Western Asia",
    "Asia centrale": "Central Asia",
    "Asia meridionale": "Southern Asia",
    "Asia orientale": "Eastern Asia",
    "Sud-est asiatico": "Southeast Asia",
    "Africa settentrionale": "Northern Africa",
    "Africa occidentale": "Western Africa",
    "Africa centrale": "Central Africa",
    "Africa orientale": "Eastern Africa",
    "Africa australe": "Southern Africa",
    "America settentrionale": "Northern America",
    "America centrale": "Central America",
    "Caraibi": "Caribbean",
    "America meridionale": "South America",
    "Australasia": "Australasia",
    "Melanesia": "Melanesia",
    "Micronesia": "Micronesia",
    "Polinesia": "Polynesia",
}

# ---------------------------------------------------------------------------
# Testi dell'interfaccia
# ---------------------------------------------------------------------------
TESTI = {
    "it": {
        # titolo
        "gioca": "Gioca",
        "classifica": "Classifica",
        "impostazioni": "Impostazioni",
        "crediti": "Crediti",
        "esci": "Esci",
        "sottotitolo": "Il quiz delle sagome del mondo  ·  15 domande  ·  3 aiuti",
        "suggerimento_titolo": "F11 schermo intero  ·  Invio per giocare",
        # scala dei gradi
        "gradi_esploratore": "GRADI DELL'ESPLORATORE",
        "legenda_scala": "◆ = soglia di sicurezza · miglia esplorate",
        "nessun_grado": "Nessun grado",
        # gioco
        "mi_ritiro": "Mi ritiro",
        "si": "Sì",
        "no": "No",
        "avanti": "Avanti",
        "vedi_risultato": "Vedi il risultato",
        "domanda_n": "DOMANDA {n} DI {totale}",
        "aiuto_5050": "50:50 – elimina due risposte sbagliate",
        "aiuto_vicino": "Stato confinante – mostra uno stato vicino",
        "aiuto_bandiera": "Bandiera – mostra la bandiera dello stato",
        "didascalia_confinante": "Confinante",
        "didascalia_vicino_isola": "Paese più vicino",
        "didascalia_vicino": "Paese vicino",
        "didascalia": "{tipo}: {nome}",
        "conferma_risposta": "È la tua risposta definitiva?",
        "conferma_ritiro": "Vuoi ritirarti? Terrai il grado {grado} ({miglia} miglia)",
        "conferma_ritiro_zero": "Vuoi ritirarti? Non hai ancora conquistato nessun grado",
        "risposta_bloccata": "Risposta bloccata",
        "istruzioni_gioco": "Clicca una risposta oppure premi A, B, C, D  ·  Esc per ritirarti",
        "esito_vittoria": "Hai completato la rotta: {grado}!",
        "esito_giusta": "Esatto! Grado conquistato: {grado}",
        "esito_ritiro": "Ti ritiri con il grado {grado}",
        "esito_tempo": "Tempo scaduto!",
        "esito_sbagliata": "Risposta sbagliata.",
        "esito_soglia": "{prefisso} Scendi alla soglia: {grado}",
        "esito_zero": "{prefisso} Nessun grado conquistato",
        "titolo_giusta": "RISPOSTA ESATTA",
        "titolo_ritiro": "LA RISPOSTA ERA",
        "titolo_tempo": "TEMPO SCADUTO",
        "titolo_sbagliata": "RISPOSTA SBAGLIATA",
        "confina_con": "Confina con: {elenco}",
        "nessun_confine_vicino": "Nessun confine terrestre. Paese più vicino: {nome}",
        "nessun_confine": "Nessun confine terrestre.",
        "luogo": "{continente}  ·  {regione}",
        # fine partita
        "fine_vittoria": "ROTTA COMPLETATA!",
        "fine_ritiro": "TI SEI RITIRATO",
        "fine_sconfitta": "FINE DEL VIAGGIO",
        "il_tuo_viaggio": "Il tuo viaggio",
        "domanda_breve": "Domanda {n}",
        "esito_breve_giusta": "Giusta",
        "esito_breve_sbagliata": "Sbagliata",
        "esito_breve_tempo": "Tempo scaduto",
        "esito_breve_ritiro": "Ritirato",
        "nessuna_domanda": "Nessuna domanda giocata",
        "grado_raggiunto": "GRADO RAGGIUNTO",
        "miglia_esplorate": "{miglia} miglia esplorate",
        "risposte_esatte": "Risposte esatte: {giuste} su {totale}",
        "aiuti_usati": "Aiuti usati: {usati} su {totale}",
        "salvato_posizione": "Salvato! Sei {posizione}° in classifica",
        "nome_classifica": "Il tuo nome per la classifica:",
        "salva_classifica": "Salva in classifica",
        "gioca_ancora": "Gioca ancora",
        "menu": "Menu",
        "non_in_top10": "Punteggio non sufficiente per la top 10",
        "anonimo": "Anonimo",
        # classifica
        "titolo_classifica": "CLASSIFICA",
        "col_nome": "Nome",
        "col_grado": "Grado",
        "col_miglia": "Miglia",
        "col_data": "Data",
        "classifica_vuota": "Nessuna partita ancora: gioca per entrare in classifica!",
        "indietro": "Indietro",
        # impostazioni
        "titolo_impostazioni": "IMPOSTAZIONI",
        "lingua": "Lingua",
        "interruttore_si": "SÌ",
        "interruttore_no": "NO",
        "timer": "Timer",
        "timer_desc": "45 s per le domande 1-5, 60 s per 6-10, nessun limite per 11-15",
        "risposta_definitiva": "Risposta definitiva",
        "risposta_definitiva_desc": "Chiede conferma prima di bloccare la risposta",
        "audio": "Audio",
        "audio_desc": "Effetti sonori e sottofondo di tensione",
        "stati_per_fascia": "Stati in gioco per fascia",
        "fascia_breve": "F{n}",
        "fascia_conteggio": "F{n}: {conteggio}",
        "totale_stati": "Totale: {giocabili} su {totale}",
        "ripristina_esclusioni": "Ripristina esclusioni predefinite",
        "esclusioni_ripristinate": "Esclusioni predefinite ripristinate",
        "elenco_stati": "Stati in gioco (clic per includere/escludere)",
        "tutte": "Tutte",
        "fascia_n": "Fascia {n}",
        "minimo_per_fascia": "Servono almeno 3 stati giocabili in ogni fascia",
        "minimo_totale": "Servono almeno 20 stati giocabili",
        "troppi_esclusi": "Troppi stati esclusi: rimettine qualcuno in gioco",
        # crediti
        "titolo_crediti": "CREDITI",
        "versione": "Versione {versione}",
        # errori
        "errore_fatale": ("Si è verificato un errore imprevisto e il gioco deve chiudersi.\n\n"
                          "I dettagli sono nel file:\n{percorso}"),
    },
    "en": {
        # title
        "gioca": "Play",
        "classifica": "Leaderboard",
        "impostazioni": "Settings",
        "crediti": "Credits",
        "esci": "Quit",
        "sottotitolo": "The world silhouette quiz  ·  15 questions  ·  3 lifelines",
        "suggerimento_titolo": "F11 full screen  ·  Enter to play",
        # rank ladder
        "gradi_esploratore": "EXPLORER RANKS",
        "legenda_scala": "◆ = safety checkpoint · miles explored",
        "nessun_grado": "No rank",
        # game
        "mi_ritiro": "Walk away",
        "si": "Yes",
        "no": "No",
        "avanti": "Next",
        "vedi_risultato": "See results",
        "domanda_n": "QUESTION {n} OF {totale}",
        "aiuto_5050": "50:50 – removes two wrong answers",
        "aiuto_vicino": "Neighbor – shows a neighboring country",
        "aiuto_bandiera": "Flag – shows the country's flag",
        "didascalia_confinante": "Neighbor",
        "didascalia_vicino_isola": "Nearest country",
        "didascalia_vicino": "Nearby country",
        "didascalia": "{tipo}: {nome}",
        "conferma_risposta": "Is that your final answer?",
        "conferma_ritiro": "Walk away? You keep the rank of {grado} ({miglia} miles)",
        "conferma_ritiro_zero": "Walk away? You haven't earned a rank yet",
        "risposta_bloccata": "Answer locked in",
        "istruzioni_gioco": "Click an answer or press A, B, C, D  ·  Esc to walk away",
        "esito_vittoria": "You completed the voyage: {grado}!",
        "esito_giusta": "Correct! Rank earned: {grado}",
        "esito_ritiro": "You walk away as {grado}",
        "esito_tempo": "Time's up!",
        "esito_sbagliata": "Wrong answer.",
        "esito_soglia": "{prefisso} You drop back to the checkpoint: {grado}",
        "esito_zero": "{prefisso} No rank earned",
        "titolo_giusta": "CORRECT ANSWER",
        "titolo_ritiro": "THE ANSWER WAS",
        "titolo_tempo": "TIME'S UP",
        "titolo_sbagliata": "WRONG ANSWER",
        "confina_con": "Borders: {elenco}",
        "nessun_confine_vicino": "No land borders. Nearest country: {nome}",
        "nessun_confine": "No land borders.",
        "luogo": "{continente}  ·  {regione}",
        # end of game
        "fine_vittoria": "VOYAGE COMPLETE!",
        "fine_ritiro": "YOU WALKED AWAY",
        "fine_sconfitta": "END OF THE VOYAGE",
        "il_tuo_viaggio": "Your voyage",
        "domanda_breve": "Question {n}",
        "esito_breve_giusta": "Correct",
        "esito_breve_sbagliata": "Wrong",
        "esito_breve_tempo": "Time's up",
        "esito_breve_ritiro": "Walked away",
        "nessuna_domanda": "No questions played",
        "grado_raggiunto": "RANK REACHED",
        "miglia_esplorate": "{miglia} miles explored",
        "risposte_esatte": "Correct answers: {giuste} of {totale}",
        "aiuti_usati": "Lifelines used: {usati} of {totale}",
        "salvato_posizione": "Saved! You're #{posizione} on the leaderboard",
        "nome_classifica": "Your name for the leaderboard:",
        "salva_classifica": "Save to leaderboard",
        "gioca_ancora": "Play again",
        "menu": "Menu",
        "non_in_top10": "Score not high enough for the top 10",
        "anonimo": "Anonymous",
        # leaderboard
        "titolo_classifica": "LEADERBOARD",
        "col_nome": "Name",
        "col_grado": "Rank",
        "col_miglia": "Miles",
        "col_data": "Date",
        "classifica_vuota": "No games yet: play to get on the leaderboard!",
        "indietro": "Back",
        # settings
        "titolo_impostazioni": "SETTINGS",
        "lingua": "Language",
        "interruttore_si": "ON",
        "interruttore_no": "OFF",
        "timer": "Timer",
        "timer_desc": "45 s for questions 1-5, 60 s for 6-10, no limit for 11-15",
        "risposta_definitiva": "Final answer",
        "risposta_definitiva_desc": "Asks for confirmation before locking in your answer",
        "audio": "Sound",
        "audio_desc": "Sound effects and suspense background music",
        "stati_per_fascia": "Countries in play per tier",
        "fascia_breve": "T{n}",
        "fascia_conteggio": "T{n}: {conteggio}",
        "totale_stati": "Total: {giocabili} of {totale}",
        "ripristina_esclusioni": "Restore default exclusions",
        "esclusioni_ripristinate": "Default exclusions restored",
        "elenco_stati": "Countries in play (click to include/exclude)",
        "tutte": "All",
        "fascia_n": "Tier {n}",
        "minimo_per_fascia": "Each tier needs at least 3 playable countries",
        "minimo_totale": "At least 20 playable countries are needed",
        "troppi_esclusi": "Too many countries excluded: put some back in play",
        # credits
        "titolo_crediti": "CREDITS",
        "versione": "Version {versione}",
        # errors
        "errore_fatale": ("An unexpected error occurred and the game has to close.\n\n"
                          "Details are in this file:\n{percorso}"),
    },
}

CREDITI = {
    "it": [
        ("Sagome e mappa", "Natural Earth – Admin 0 Countries, scala 1:10m, versione \"punto di vista italiano\" "
                           "(naturalearthdata.com, repository nvkelso/natural-earth-vector). Dati di pubblico dominio."),
        ("Bandiere", "hampusborgos/country-flags su GitHub (PNG 250 px, commit ba2cf41). Le bandiere sono di "
                     "pubblico dominio (licenza dichiarata: \"PD\"), originariamente da Wikimedia Commons."),
        ("Carattere", "Montserrat di Julieta Ulanovsky e collaboratori (github.com/JulietaUla/Montserrat), "
                      "SIL Open Font License 1.1. Il testo della licenza è in assets/font/OFL.txt."),
        ("Suoni", "Sintetizzati appositamente per questo gioco (tools/genera_suoni.py). Nessun campione esterno."),
        ("Gioco", "WhoWantsToBeAnExplorer: grafica, nomi e suoni originali, realizzato in Python con pygame-ce "
                  "(licenza LGPL). Nessuna connessione di rete, nessuna raccolta dati."),
    ],
    "en": [
        ("Silhouettes and map", "Natural Earth – Admin 0 Countries, 1:10m scale, \"Italian point of view\" "
                                "version (naturalearthdata.com, nvkelso/natural-earth-vector repository). "
                                "Public domain data."),
        ("Flags", "hampusborgos/country-flags on GitHub (250 px PNG, commit ba2cf41). The flags are in the "
                  "public domain (declared license: \"PD\"), originally from Wikimedia Commons."),
        ("Typeface", "Montserrat by Julieta Ulanovsky and contributors (github.com/JulietaUla/Montserrat), "
                     "SIL Open Font License 1.1. The license text is in assets/font/OFL.txt."),
        ("Sounds", "Synthesized specifically for this game (tools/genera_suoni.py). No external samples."),
        ("Game", "WhoWantsToBeAnExplorer: original graphics, names and sounds, made in Python with pygame-ce "
                 "(LGPL license). No network connection, no data collection."),
    ],
}
