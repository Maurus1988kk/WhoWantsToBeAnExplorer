# -*- coding: utf-8 -*-
"""
Preparazione dei dati di WhoWantsToBeAnExplorer.

Lo script va eseguito UNA volta (o quando si vogliono rigenerare i dati) e
produce tutto quello che serve al gioco nella cartella assets/:

  assets/stati.json            elenco stati, fasce, vicini, similarità
  assets/eccezioni_sagome.json eccezioni manuali sulle sagome (letto, creato se manca)
  assets/sagome/ISO.png        sagome bianche su trasparente (1024 px lato lungo)
  assets/vicini/ISO_ISO.png    compositi "stato misterioso + vicino"
  assets/bandiere/ISO.png      bandiere
  assets/mondo/                mappa del mondo e contorni per l'evidenziazione
  assets/font/                 font Montserrat (OFL)
  assets/icona.ico/.png        icona del gioco
  anteprime/                   griglie di controllo visivo (non incluse nell'exe)

Dipendenze (solo per questo script, NON per il gioco): shapely, Pillow, numpy.

Uso:
  python tools/prepara_dati.py [--cache CARTELLA] [--ripristina]

  --ripristina  ignora i valori modificati a mano in assets/stati.json
                (fasce, esclusioni, nomi italiani e inglesi) e riparte dai
                valori predefiniti.
"""

import argparse
import datetime
import json
import math
import os
import urllib.request

import numpy as np
import shapely
from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely.ops import polylabel, unary_union
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Percorsi e sorgenti
# ---------------------------------------------------------------------------
RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(RADICE, "assets")
ANTEPRIME = os.path.join(RADICE, "anteprime")

URL_NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
# Versione "punto di vista italiano" di Natural Earth (confini secondo le
# posizioni ufficiali italiane: Crimea all'Ucraina, Marocco senza Sahara
# Occidentale, Cipro e Somalia unificate) + versione predefinita, usata solo
# per recuperare alcune piccole aree lasciate senza stato nella vista italiana.
FILE_NE_ITA = "ne_10m_admin_0_countries_ita.geojson"
FILE_NE_DEF = "ne_10m_admin_0_countries.geojson"

# Bandiere: hampusborgos/country-flags (pubblico dominio, "license": "PD").
# Le PNG sono state tolte dal ramo principale nel 2025: si usa l'ultimo commit
# che le contiene, fissato per hash così il risultato è riproducibile.
COMMIT_BANDIERE = "ba2cf4101bf029d2ada26da2f95121de74581a4d"
URL_BANDIERE = ("https://raw.githubusercontent.com/hampusborgos/country-flags/"
                + COMMIT_BANDIERE + "/png250px/{}.png")
URL_LICENZA_BANDIERE = ("https://raw.githubusercontent.com/hampusborgos/country-flags/"
                        + COMMIT_BANDIERE + "/README.md")

# Font Montserrat (SIL Open Font License 1.1)
URL_FONT = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/"
FILE_FONT = ["Montserrat-Regular.ttf", "Montserrat-Medium.ttf", "Montserrat-SemiBold.ttf",
             "Montserrat-Bold.ttf", "Montserrat-ExtraBold.ttf"]

# ---------------------------------------------------------------------------
# Elenco degli stati: 193 membri ONU + Vaticano, Kosovo, Palestina, Taiwan.
# (ISO3, ISO2, nome italiano, fascia predefinita 1-5)
# La fascia misura quanto è riconoscibile la SAGOMA (1 iconica, 5 quasi impossibile).
# ---------------------------------------------------------------------------
STATI = [
    # --- Europa ---
    ("ITA", "IT", "Italia", 1), ("FRA", "FR", "Francia", 1), ("ESP", "ES", "Spagna", 1),
    ("PRT", "PT", "Portogallo", 1), ("GBR", "GB", "Regno Unito", 1), ("IRL", "IE", "Irlanda", 1),
    ("ISL", "IS", "Islanda", 1), ("NOR", "NO", "Norvegia", 1), ("GRC", "GR", "Grecia", 1),
    ("DEU", "DE", "Germania", 1), ("RUS", "RU", "Russia", 1),
    ("SWE", "SE", "Svezia", 2), ("FIN", "FI", "Finlandia", 2), ("DNK", "DK", "Danimarca", 2),
    ("POL", "PL", "Polonia", 2), ("UKR", "UA", "Ucraina", 2), ("CHE", "CH", "Svizzera", 2),
    ("AUT", "AT", "Austria", 2), ("HRV", "HR", "Croazia", 2), ("CZE", "CZ", "Repubblica Ceca", 2),
    ("HUN", "HU", "Ungheria", 2), ("ROU", "RO", "Romania", 2), ("NLD", "NL", "Paesi Bassi", 2),
    ("BEL", "BE", "Belgio", 2),
    ("BLR", "BY", "Bielorussia", 3), ("BGR", "BG", "Bulgaria", 3), ("SRB", "RS", "Serbia", 3),
    ("ALB", "AL", "Albania", 3), ("SVK", "SK", "Slovacchia", 3), ("SVN", "SI", "Slovenia", 3),
    ("EST", "EE", "Estonia", 3), ("LVA", "LV", "Lettonia", 3), ("LTU", "LT", "Lituania", 3),
    ("MLT", "MT", "Malta", 3), ("BIH", "BA", "Bosnia ed Erzegovina", 3),
    ("LUX", "LU", "Lussemburgo", 4), ("MDA", "MD", "Moldavia", 4), ("MKD", "MK", "Macedonia del Nord", 4),
    ("MNE", "ME", "Montenegro", 4), ("XKX", "XK", "Kosovo", 4),
    ("AND", "AD", "Andorra", 5), ("SMR", "SM", "San Marino", 5), ("MCO", "MC", "Monaco", 5),
    ("VAT", "VA", "Città del Vaticano", 5), ("LIE", "LI", "Liechtenstein", 5),
    # --- Asia ---
    ("JPN", "JP", "Giappone", 1), ("IND", "IN", "India", 1), ("CHN", "CN", "Cina", 1),
    ("LKA", "LK", "Sri Lanka", 1), ("TUR", "TR", "Turchia", 1),
    ("KOR", "KR", "Corea del Sud", 2), ("VNM", "VN", "Vietnam", 2), ("THA", "TH", "Thailandia", 2),
    ("IDN", "ID", "Indonesia", 2), ("PHL", "PH", "Filippine", 2), ("SAU", "SA", "Arabia Saudita", 2),
    ("IRN", "IR", "Iran", 2), ("MNG", "MN", "Mongolia", 2), ("KAZ", "KZ", "Kazakistan", 2),
    ("ISR", "IL", "Israele", 2), ("TWN", "TW", "Taiwan", 2), ("CYP", "CY", "Cipro", 2),
    ("MYS", "MY", "Malaysia", 2), ("AFG", "AF", "Afghanistan", 2), ("NPL", "NP", "Nepal", 2),
    ("PRK", "KP", "Corea del Nord", 3), ("PAK", "PK", "Pakistan", 3), ("IRQ", "IQ", "Iraq", 3),
    ("SYR", "SY", "Siria", 3), ("JOR", "JO", "Giordania", 3), ("YEM", "YE", "Yemen", 3),
    ("OMN", "OM", "Oman", 3), ("QAT", "QA", "Qatar", 3), ("MMR", "MM", "Myanmar", 3),
    ("LAO", "LA", "Laos", 3), ("KHM", "KH", "Cambogia", 3), ("BGD", "BD", "Bangladesh", 3),
    ("GEO", "GE", "Georgia", 3), ("AZE", "AZ", "Azerbaigian", 3),
    ("UZB", "UZ", "Uzbekistan", 4), ("ARE", "AE", "Emirati Arabi Uniti", 4), ("KWT", "KW", "Kuwait", 4),
    ("LBN", "LB", "Libano", 4), ("ARM", "AM", "Armenia", 4), ("KGZ", "KG", "Kirghizistan", 4),
    ("TJK", "TJ", "Tagikistan", 4), ("BTN", "BT", "Bhutan", 4), ("PSE", "PS", "Palestina", 4),
    ("TLS", "TL", "Timor Est", 4), ("SGP", "SG", "Singapore", 4), ("BHR", "BH", "Bahrein", 4),
    ("TKM", "TM", "Turkmenistan", 5), ("BRN", "BN", "Brunei", 5), ("MDV", "MV", "Maldive", 5),
    # --- Africa ---
    ("MDG", "MG", "Madagascar", 1), ("EGY", "EG", "Egitto", 1), ("ZAF", "ZA", "Sudafrica", 1),
    ("SOM", "SO", "Somalia", 2), ("MAR", "MA", "Marocco", 2),
    ("DZA", "DZ", "Algeria", 3), ("LBY", "LY", "Libia", 3), ("TUN", "TN", "Tunisia", 3),
    ("NGA", "NG", "Nigeria", 3), ("ETH", "ET", "Etiopia", 3), ("KEN", "KE", "Kenya", 3),
    ("TZA", "TZ", "Tanzania", 3), ("COD", "CD", "Repubblica Democratica del Congo", 3),
    ("AGO", "AO", "Angola", 3), ("NAM", "NA", "Namibia", 3), ("MOZ", "MZ", "Mozambico", 3),
    ("MWI", "MW", "Malawi", 3), ("GMB", "GM", "Gambia", 3),
    ("SDN", "SD", "Sudan", 4), ("SSD", "SS", "Sudan del Sud", 4), ("ERI", "ER", "Eritrea", 4),
    ("MLI", "ML", "Mali", 4), ("NER", "NE", "Niger", 4), ("TCD", "TD", "Ciad", 4),
    ("MRT", "MR", "Mauritania", 4), ("CMR", "CM", "Camerun", 4), ("GHA", "GH", "Ghana", 4),
    ("CIV", "CI", "Costa d'Avorio", 4), ("SEN", "SN", "Senegal", 4), ("TGO", "TG", "Togo", 4),
    ("ZMB", "ZM", "Zambia", 4), ("ZWE", "ZW", "Zimbabwe", 4), ("BWA", "BW", "Botswana", 4),
    ("UGA", "UG", "Uganda", 4), ("CPV", "CV", "Capo Verde", 4),
    ("BFA", "BF", "Burkina Faso", 5), ("CAF", "CF", "Repubblica Centrafricana", 5),
    ("GNB", "GW", "Guinea-Bissau", 5), ("LSO", "LS", "Lesotho", 5), ("SWZ", "SZ", "Eswatini", 5),
    ("BEN", "BJ", "Benin", 5), ("GIN", "GN", "Guinea", 5), ("SLE", "SL", "Sierra Leone", 5),
    ("LBR", "LR", "Liberia", 5), ("GAB", "GA", "Gabon", 5), ("COG", "CG", "Repubblica del Congo", 5),
    ("GNQ", "GQ", "Guinea Equatoriale", 5), ("RWA", "RW", "Ruanda", 5), ("BDI", "BI", "Burundi", 5),
    ("DJI", "DJ", "Gibuti", 5), ("STP", "ST", "São Tomé e Príncipe", 5), ("COM", "KM", "Comore", 5),
    ("MUS", "MU", "Mauritius", 5), ("SYC", "SC", "Seychelles", 5),
    # --- America del Nord, centrale e Caraibi ---
    ("USA", "US", "Stati Uniti", 1), ("CAN", "CA", "Canada", 1), ("MEX", "MX", "Messico", 1),
    ("CUB", "CU", "Cuba", 1),
    ("JAM", "JM", "Giamaica", 2), ("PAN", "PA", "Panama", 2),
    ("HTI", "HT", "Haiti", 3), ("DOM", "DO", "Repubblica Dominicana", 3), ("CRI", "CR", "Costa Rica", 3),
    ("GTM", "GT", "Guatemala", 3), ("HND", "HN", "Honduras", 3), ("NIC", "NI", "Nicaragua", 3),
    ("SLV", "SV", "El Salvador", 4), ("BLZ", "BZ", "Belize", 4), ("TTO", "TT", "Trinidad e Tobago", 4),
    ("BHS", "BS", "Bahamas", 4),
    ("ATG", "AG", "Antigua e Barbuda", 5), ("BRB", "BB", "Barbados", 5), ("DMA", "DM", "Dominica", 5),
    ("GRD", "GD", "Grenada", 5), ("KNA", "KN", "Saint Kitts e Nevis", 5), ("LCA", "LC", "Santa Lucia", 5),
    ("VCT", "VC", "Saint Vincent e Grenadine", 5),
    # --- America del Sud ---
    ("BRA", "BR", "Brasile", 1), ("ARG", "AR", "Argentina", 1), ("CHL", "CL", "Cile", 1),
    ("PER", "PE", "Perù", 2), ("COL", "CO", "Colombia", 2), ("VEN", "VE", "Venezuela", 2),
    ("BOL", "BO", "Bolivia", 2), ("ECU", "EC", "Ecuador", 2),
    ("URY", "UY", "Uruguay", 3), ("PRY", "PY", "Paraguay", 3),
    ("GUY", "GY", "Guyana", 4), ("SUR", "SR", "Suriname", 4),
    # --- Oceania ---
    ("AUS", "AU", "Australia", 1), ("NZL", "NZ", "Nuova Zelanda", 1),
    ("PNG", "PG", "Papua Nuova Guinea", 2),
    ("FJI", "FJ", "Figi", 4), ("SLB", "SB", "Isole Salomone", 4), ("VUT", "VU", "Vanuatu", 4),
    ("WSM", "WS", "Samoa", 5), ("TON", "TO", "Tonga", 5), ("KIR", "KI", "Kiribati", 5),
    ("MHL", "MH", "Isole Marshall", 5), ("FSM", "FM", "Micronesia", 5), ("NRU", "NR", "Nauru", 5),
    ("PLW", "PW", "Palau", 5), ("TUV", "TV", "Tuvalu", 5),
]

# Nomi inglesi (campo "nome_en" di stati.json, usato quando il gioco è in inglese).
NOMI_EN = {
    # Europe
    "ITA": "Italy", "FRA": "France", "ESP": "Spain", "PRT": "Portugal", "GBR": "United Kingdom",
    "IRL": "Ireland", "ISL": "Iceland", "NOR": "Norway", "GRC": "Greece", "DEU": "Germany",
    "RUS": "Russia", "SWE": "Sweden", "FIN": "Finland", "DNK": "Denmark", "POL": "Poland",
    "UKR": "Ukraine", "CHE": "Switzerland", "AUT": "Austria", "HRV": "Croatia", "CZE": "Czech Republic",
    "HUN": "Hungary", "ROU": "Romania", "NLD": "Netherlands", "BEL": "Belgium", "BLR": "Belarus",
    "BGR": "Bulgaria", "SRB": "Serbia", "ALB": "Albania", "SVK": "Slovakia", "SVN": "Slovenia",
    "EST": "Estonia", "LVA": "Latvia", "LTU": "Lithuania", "MLT": "Malta", "BIH": "Bosnia and Herzegovina",
    "LUX": "Luxembourg", "MDA": "Moldova", "MKD": "North Macedonia", "MNE": "Montenegro", "XKX": "Kosovo",
    "AND": "Andorra", "SMR": "San Marino", "MCO": "Monaco", "VAT": "Vatican City", "LIE": "Liechtenstein",
    # Asia
    "JPN": "Japan", "IND": "India", "CHN": "China", "LKA": "Sri Lanka", "TUR": "Turkey",
    "KOR": "South Korea", "VNM": "Vietnam", "THA": "Thailand", "IDN": "Indonesia", "PHL": "Philippines",
    "SAU": "Saudi Arabia", "IRN": "Iran", "MNG": "Mongolia", "KAZ": "Kazakhstan", "ISR": "Israel",
    "TWN": "Taiwan", "CYP": "Cyprus", "MYS": "Malaysia", "AFG": "Afghanistan", "NPL": "Nepal",
    "PRK": "North Korea", "PAK": "Pakistan", "IRQ": "Iraq", "SYR": "Syria", "JOR": "Jordan",
    "YEM": "Yemen", "OMN": "Oman", "QAT": "Qatar", "MMR": "Myanmar", "LAO": "Laos",
    "KHM": "Cambodia", "BGD": "Bangladesh", "GEO": "Georgia", "AZE": "Azerbaijan", "UZB": "Uzbekistan",
    "ARE": "United Arab Emirates", "KWT": "Kuwait", "LBN": "Lebanon", "ARM": "Armenia",
    "KGZ": "Kyrgyzstan", "TJK": "Tajikistan", "BTN": "Bhutan", "PSE": "Palestine", "TLS": "East Timor",
    "SGP": "Singapore", "BHR": "Bahrain", "TKM": "Turkmenistan", "BRN": "Brunei", "MDV": "Maldives",
    # Africa
    "MDG": "Madagascar", "EGY": "Egypt", "ZAF": "South Africa", "SOM": "Somalia", "MAR": "Morocco",
    "DZA": "Algeria", "LBY": "Libya", "TUN": "Tunisia", "NGA": "Nigeria", "ETH": "Ethiopia",
    "KEN": "Kenya", "TZA": "Tanzania", "COD": "Democratic Republic of the Congo", "AGO": "Angola",
    "NAM": "Namibia", "MOZ": "Mozambique", "MWI": "Malawi", "GMB": "Gambia", "SDN": "Sudan",
    "SSD": "South Sudan", "ERI": "Eritrea", "MLI": "Mali", "NER": "Niger", "TCD": "Chad",
    "MRT": "Mauritania", "CMR": "Cameroon", "GHA": "Ghana", "CIV": "Ivory Coast", "SEN": "Senegal",
    "TGO": "Togo", "ZMB": "Zambia", "ZWE": "Zimbabwe", "BWA": "Botswana", "UGA": "Uganda",
    "CPV": "Cape Verde", "BFA": "Burkina Faso", "CAF": "Central African Republic", "GNB": "Guinea-Bissau",
    "LSO": "Lesotho", "SWZ": "Eswatini", "BEN": "Benin", "GIN": "Guinea", "SLE": "Sierra Leone",
    "LBR": "Liberia", "GAB": "Gabon", "COG": "Republic of the Congo", "GNQ": "Equatorial Guinea",
    "RWA": "Rwanda", "BDI": "Burundi", "DJI": "Djibouti", "STP": "São Tomé and Príncipe",
    "COM": "Comoros", "MUS": "Mauritius", "SYC": "Seychelles",
    # North and Central America, Caribbean
    "USA": "United States", "CAN": "Canada", "MEX": "Mexico", "CUB": "Cuba", "JAM": "Jamaica",
    "PAN": "Panama", "HTI": "Haiti", "DOM": "Dominican Republic", "CRI": "Costa Rica",
    "GTM": "Guatemala", "HND": "Honduras", "NIC": "Nicaragua", "SLV": "El Salvador", "BLZ": "Belize",
    "TTO": "Trinidad and Tobago", "BHS": "Bahamas", "ATG": "Antigua and Barbuda", "BRB": "Barbados",
    "DMA": "Dominica", "GRD": "Grenada", "KNA": "Saint Kitts and Nevis", "LCA": "Saint Lucia",
    "VCT": "Saint Vincent and the Grenadines",
    # South America
    "BRA": "Brazil", "ARG": "Argentina", "CHL": "Chile", "PER": "Peru", "COL": "Colombia",
    "VEN": "Venezuela", "BOL": "Bolivia", "ECU": "Ecuador", "URY": "Uruguay", "PRY": "Paraguay",
    "GUY": "Guyana", "SUR": "Suriname",
    # Oceania
    "AUS": "Australia", "NZL": "New Zealand", "PNG": "Papua New Guinea", "FJI": "Fiji",
    "SLB": "Solomon Islands", "VUT": "Vanuatu", "WSM": "Samoa", "TON": "Tonga", "KIR": "Kiribati",
    "MHL": "Marshall Islands", "FSM": "Micronesia", "NRU": "Nauru", "PLW": "Palau", "TUV": "Tuvalu",
}

# Esclusi di default: la sagoma sarebbe solo una nuvola di puntini.
ESCLUSI_DEFAULT ={"KIR", "TUV", "MHL", "MDV", "NRU", "PLW", "FSM", "SYC"}

# Codice ADM0_A3 di Natural Earth quando è diverso dall'ISO3.
CODICE_NE = {"XKX": "KOS", "PSE": "PSX", "SSD": "SDS"}

# Unità di Natural Earth da fondere nello stato (enclavi, basi, unità separate):
# senza queste fusioni le sagome avrebbero buchi o tacche inesistenti.
FUSIONI = {
    "SOM": ["SOL"],                       # Somaliland
    "CYP": ["CYN", "CNM", "ESB", "WSB"],  # Cipro Nord, zona cuscinetto ONU, basi britanniche
    "CHN": ["HKG", "MAC"],                # Hong Kong e Macao
    "FIN": ["ALD"],                       # Isole Åland
    "CUB": ["USG"],                       # Guantánamo
    "KAZ": ["KAB"],                       # Baikonur
    "IND": ["KAS"],                       # Ghiacciaio del Siachen
    "BRA": ["BRI"],                       # Isola brasiliana
}

# Aree senza stato nella vista italiana: si attribuiscono all'amministratore
# de facto della vista predefinita, tranne questi casi.
LACUNE_DESTINAZIONE = {
    "ISR": ["SYR"],          # Alture del Golan: territorio siriano per l'Italia
    "SPI": ["CHL", "ARG"],   # Campo di ghiaccio Patagonico Sud: confine non definito
}

# Traduzione delle sottoregioni Natural Earth -> (continente, regione)
REGIONI = {
    "Southern Europe": ("Europa", "Europa meridionale"),
    "Western Europe": ("Europa", "Europa occidentale"),
    "Northern Europe": ("Europa", "Europa settentrionale"),
    "Eastern Europe": ("Europa", "Europa orientale"),
    "Western Asia": ("Asia", "Asia occidentale"),
    "Central Asia": ("Asia", "Asia centrale"),
    "Southern Asia": ("Asia", "Asia meridionale"),
    "Eastern Asia": ("Asia", "Asia orientale"),
    "South-Eastern Asia": ("Asia", "Sud-est asiatico"),
    "Northern Africa": ("Africa", "Africa settentrionale"),
    "Western Africa": ("Africa", "Africa occidentale"),
    "Middle Africa": ("Africa", "Africa centrale"),
    "Eastern Africa": ("Africa", "Africa orientale"),
    "Southern Africa": ("Africa", "Africa australe"),
    "Northern America": ("America del Nord", "America settentrionale"),
    "Central America": ("America del Nord", "America centrale"),
    "Caribbean": ("America del Nord", "Caraibi"),
    "South America": ("America del Sud", "America meridionale"),
    "Australia and New Zealand": ("Oceania", "Australasia"),
    "Melanesia": ("Oceania", "Melanesia"),
    "Micronesia": ("Oceania", "Micronesia"),
    "Polynesia": ("Oceania", "Polinesia"),
}

# Eccezioni manuali predefinite sulle sagome (scritte in assets/eccezioni_sagome.json
# se il file non esiste; poi vale quello che c'è nel file).
# "rimuovi": riquadri [lon_min, lat_min, lon_max, lat_max]: le parti il cui punto
#            interno cade dentro vengono tolte (e non fanno da "ponte").
# "mantieni": riquadri le cui parti vengono tenute comunque.
ECCEZIONI_DEFAULT = {
    "_nota": ("Eccezioni manuali alla regola automatica che sceglie le parti di ogni "
              "stato. Riquadri in gradi [lon_min, lat_min, lon_max, lat_max]. "
              "Dopo una modifica rilanciare tools/prepara_dati.py."),
    "parametri": {
        "alfa": 0.4,
        "beta": 1.2,
        "distanza_minima_km": 200.0,
        "puntini_frazione_dimensione": 0.004,
        "puntini_frazione_distanza": 0.03,
    },
    "stati": {
        "JPN": {"rimuovi": [[122.0, 23.0, 132.0, 29.3]],
                "nota": "Tolte Ryukyu/Okinawa: restano Hokkaido, Honshu, Shikoku, Kyushu e isole vicine"},
        "ESP": {"rimuovi": [[-6.0, 34.5, -1.5, 36.0]],
                "nota": "Tolte Ceuta, Melilla e le plazas de soberanía sulla costa africana"},
        "NOR": {"rimuovi": [[-12.0, 70.5, 40.0, 82.0], [2.0, -56.0, 5.0, -53.0]],
                "nota": "Tolte Svalbard, Jan Mayen, Bjørnøya e Bouvet"},
        "IND": {"mantieni": [[92.0, 6.0, 94.5, 14.2]],
                "nota": "Tenute Andamane e Nicobare (sono dentro il riquadro dell'India)"},
        "GNQ": {"mantieni": [[8.3, 3.1, 9.1, 3.9]],
                "nota": "Tenuta l'isola di Bioko (con la capitale Malabo)"},
        "STP": {"mantieni": [[7.2, 1.4, 7.6, 1.8]],
                "nota": "Tenuta l'isola di Príncipe"},
        "AUS": {"rimuovi": [[158.0, -32.0, 160.0, -31.0]],
                "nota": "Tolta Lord Howe"},
        "ECU": {"rimuovi": [[-93.0, -2.0, -88.0, 2.0]],
                "nota": "Tolte le Galápagos"},
        "TWN": {"rimuovi": [[117.5, 24.2, 120.6, 26.6]],
                "nota": "Tolte Kinmen e Matsu (a ridosso della costa cinese); restano Taiwan e Penghu"},
    },
}

# Colori dei compositi "confinante"
COLORE_VICINO = (232, 178, 58)

R_TERRA = 6371.0088


# ---------------------------------------------------------------------------
# Utilità
# ---------------------------------------------------------------------------
_T0 = None


def log(*a):
    global _T0
    import time
    if _T0 is None:
        _T0 = time.time()
    print(f"[{time.time() - _T0:6.1f}s]", *a, flush=True)


def scarica(url, dest):
    """Scarica url in dest (se non è già presente)."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "prepara-dati-quiz/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        dati = r.read()
    with open(dest, "wb") as f:
        f.write(dati)
    return dest


def laea(lon, lat, lon0, lat0):
    """Proiezione azimutale equivalente di Lambert (sfera), risultato in km."""
    lam = np.radians(lon - lon0)
    phi = np.radians(lat)
    phi0 = math.radians(lat0)
    cosc = math.sin(phi0) * np.sin(phi) + math.cos(phi0) * np.cos(phi) * np.cos(lam)
    k = np.sqrt(2.0 / np.maximum(1.0 + cosc, 1e-12))
    x = R_TERRA * k * np.cos(phi) * np.sin(lam)
    y = R_TERRA * k * (math.cos(phi0) * np.sin(phi) - math.sin(phi0) * np.cos(phi) * np.cos(lam))
    return x, y


def laea_inversa(x, y, lon0, lat0):
    """Inversa della LAEA per un singolo punto (km -> gradi)."""
    rho = math.hypot(x, y)
    if rho < 1e-9:
        return lon0, lat0
    c = 2.0 * math.asin(min(1.0, rho / (2.0 * R_TERRA)))
    phi0 = math.radians(lat0)
    lat = math.asin(math.cos(c) * math.sin(phi0) + y * math.sin(c) * math.cos(phi0) / rho)
    lon = lon0 + math.degrees(math.atan2(x * math.sin(c),
                                         rho * math.cos(phi0) * math.cos(c) - y * math.sin(phi0) * math.sin(c)))
    return lon, math.degrees(lat)


def proietta(geom, lon0, lat0):
    def f(c):
        x, y = laea(c[:, 0], c[:, 1], lon0, lat0)
        return np.column_stack([x, y])
    return shapely.transform(geom, f)


def ricentra(geom, lon0):
    """Sposta le longitudini nell'intervallo [lon0-180, lon0+180]:
    così gli stati a cavallo dell'antimeridiano restano in un pezzo solo."""
    def f(c):
        lon = lon0 + ((c[:, 0] - lon0 + 180.0) % 360.0) - 180.0
        return np.column_stack([lon, c[:, 1]])
    return shapely.transform(geom, f)


def poligoni(geom):
    if geom is None or geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    out = []
    for g in getattr(geom, "geoms", []):
        out.extend(poligoni(g))
    return out


def multi(polys):
    polys = [p for p in polys if not p.is_empty]
    return MultiPolygon(polys) if polys else MultiPolygon()


def haversine(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_TERRA * math.asin(min(1.0, math.sqrt(a)))


def area_approssimata(poly):
    """Area in km² approssimata di un poligono in gradi (per scegliere il principale)."""
    c = poly.centroid
    return poly.area * math.cos(math.radians(c.y)) * (111.32 ** 2)


# ---------------------------------------------------------------------------
# Rasterizzazione
# ---------------------------------------------------------------------------
def disegna_maschera(polys_px, larghezza, altezza):
    """Disegna i poligoni (in pixel) su una maschera L. I buchi vengono svuotati.
    I poligoni sono ordinati per area decrescente così un'isola dentro un lago
    viene ridisegnata dopo il buco che la contiene."""
    img = Image.new("L", (larghezza, altezza), 0)
    d = ImageDraw.Draw(img)
    for p in sorted(polys_px, key=lambda q: -q.area):
        ext = list(p.exterior.coords)
        if len(ext) >= 3:
            d.polygon(ext, fill=255)
        for r in p.interiors:
            ri = list(r.coords)
            if len(ri) >= 3:
                d.polygon(ri, fill=0)
    return img


def km_a_pixel(geom, minx, maxy, scala, pad):
    def f(c):
        return np.column_stack([(c[:, 0] - minx) * scala + pad, (maxy - c[:, 1]) * scala + pad])
    return shapely.transform(geom, f)


# ---------------------------------------------------------------------------
# Caricamento geometrie
# ---------------------------------------------------------------------------
def carica_geojson(percorso):
    with open(percorso, encoding="utf-8") as f:
        d = json.load(f)
    out = {}
    for feat in d["features"]:
        p = feat["properties"]
        g = shape(feat["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        out[p["ADM0_A3"]] = (p, g)
    return out


def costruisci_geometrie(ne_ita, ne_def):
    """Geometria grezza (lon/lat) di ogni stato secondo la vista italiana, con
    fusioni e lacune colmate. Restituisce dict ISO3 -> (proprietà NE, geometria)."""
    geo = {}
    for iso, _, _, _ in STATI:
        cod = CODICE_NE.get(iso, iso)
        if cod not in ne_ita:
            raise SystemExit(f"Stato {iso} ({cod}) non trovato in Natural Earth")
        props, g = ne_ita[cod]
        parti = [g]
        for extra in FUSIONI.get(iso, []):
            if extra in ne_ita:
                parti.append(ne_ita[extra][1])
        geo[iso] = [props, parti]

    # Lacune: terre presenti nella vista predefinita ma senza stato in quella italiana
    tutto_ita = unary_union([g for _, g in ne_ita.values()])
    for cod_def, (props_def, g_def) in ne_def.items():
        if cod_def == "ATA":
            continue
        resto = g_def.difference(tutto_ita)
        pezzi = [p for p in poligoni(resto) if p.area > 0.005]
        if not pezzi:
            continue
        dest = LACUNE_DESTINAZIONE.get(cod_def)
        if dest is None:
            # attribuisci all'amministratore de facto della vista predefinita
            iso = {v: k for k, v in CODICE_NE.items()}.get(cod_def, cod_def)
            for k, lst in FUSIONI.items():
                if cod_def in lst:
                    iso = k
            dest = [iso] if iso in geo else []
        for iso in dest:
            if iso in geo:
                geo[iso][1].extend(pezzi)
                log(f"  lacuna di {sum(p.area for p in pezzi):.3f} gradi² ({cod_def}) attribuita a {iso}")

    out = {}
    for iso, (props, parti) in geo.items():
        g = unary_union([p.buffer(0) for p in parti])
        out[iso] = (props, g)
    return out


# ---------------------------------------------------------------------------
# Scelta delle parti (parte principale + isole "naturalmente sue")
# ---------------------------------------------------------------------------
def in_riquadri(pt, riquadri):
    lon = ((pt.x + 180.0) % 360.0) - 180.0
    for r in riquadri:
        if r[0] <= lon <= r[2] and r[1] <= pt.y <= r[3]:
            return True
    return False


class GeoStato:
    pass


def prepara_stato(iso, geom_raw, eccezioni, parametri):
    """Gestisce l'antimeridiano, sceglie le parti da tenere e calcola la
    proiezione locale centrata sul centroide."""
    gs = GeoStato()
    gs.iso = iso
    gs.raw = geom_raw
    polys = poligoni(geom_raw)
    principale = max(polys, key=area_approssimata)
    lon_rif = principale.centroid.x

    # 1) antimeridiano: longitudini relative alla parte principale
    sp = ricentra(geom_raw, lon_rif)
    minx, _, maxx, _ = geom_raw.bounds
    if minx < -179.5 and maxx > 179.5:
        # i pezzi tagliati a ±180 ora combaciano: li fondiamo
        sp = sp.buffer(1e-6).buffer(-1e-6)
    sp = unary_union(sp)
    parti_ll = poligoni(sp)
    lat_rif = principale.centroid.y

    # 2) proiezione provvisoria per misurare aree e distanze in km
    parti_km = [proietta(p, lon_rif, lat_rif) for p in parti_ll]
    aree = np.array([p.area for p in parti_km])
    ordine = np.argsort(-aree)
    parti_ll = [parti_ll[i] for i in ordine]
    parti_km = [parti_km[i] for i in ordine]
    aree = aree[ordine]
    punti = [p.representative_point() for p in parti_ll]

    ecc = eccezioni.get(iso, {})
    rimuovi = ecc.get("rimuovi", [])
    mantieni = ecc.get("mantieni", [])
    alfa = parametri["alfa"]
    beta = parametri["beta"]
    dmin = parametri["distanza_minima_km"]

    n = len(parti_km)
    stato = np.zeros(n, dtype=int)  # 0 indeciso, 1 tenuto, -1 scartato
    for i in range(n):
        if rimuovi and in_riquadri(punti[i], rimuovi):
            stato[i] = -1
    semi = [0] if stato[0] == 0 else []
    for i in range(n):
        if mantieni and stato[i] == 0 and in_riquadri(punti[i], mantieni):
            semi.append(i)
    for i in semi:
        stato[i] = 1

    semplici = shapely.simplify(np.array(parti_km, dtype=object), 0.5)
    a_main = aree[0]
    soglie = np.maximum(dmin, alfa * math.sqrt(a_main) + beta * np.sqrt(aree))

    # 3) crescita a partire dalla parte principale (le catene di isole vengono seguite)
    coda = list(semi)
    while coda:
        i = coda.pop()
        indecisi = np.where(stato == 0)[0]
        if len(indecisi) == 0:
            break
        vicini = shapely.dwithin(semplici[i], semplici[indecisi], soglie[indecisi])
        for j in indecisi[vicini]:
            stato[j] = 1
            coda.append(j)

    tenuti = [i for i in range(n) if stato[i] == 1]

    # 4) pulizia dei "puntini": parti minuscole e staccate che allargano solo il riquadro
    for _ in range(2):
        mp = multi([parti_km[i] for i in tenuti])
        bx = mp.bounds
        lato = max(bx[2] - bx[0], bx[3] - bx[1], 1.0)
        piccoli = {i for i in tenuti if math.sqrt(aree[i]) < parametri["puntini_frazione_dimensione"] * lato}
        grandi = [i for i in tenuti if i not in piccoli]
        if not piccoli or not grandi:
            break
        unione_grandi = shapely.simplify(multi([parti_km[i] for i in grandi]), 1.0)
        forzati = set(semi)
        da_togliere = set()
        for i in piccoli:
            if i in forzati:
                continue
            if unione_grandi.distance(semplici[i]) > parametri["puntini_frazione_distanza"] * lato:
                da_togliere.add(i)
        if not da_togliere:
            break
        tenuti = [i for i in tenuti if i not in da_togliere]

    gs.scartate = [(punti[i], aree[i]) for i in range(n) if i not in tenuti]
    gs.tenute_ll = multi([parti_ll[i] for i in tenuti])

    # 5) proiezione definitiva centrata sul centroide delle parti tenute
    km = multi([parti_km[i] for i in tenuti])
    c = km.centroid
    gs.lon0, gs.lat0 = laea_inversa(c.x, c.y, lon_rif, lat_rif)
    gs.lon_rif = lon_rif
    # le parti tenute vanno ricentrate attorno a lon0 (non cambia nulla se vicino a lon_rif)
    gs.tenute_ll = ricentra(gs.tenute_ll, gs.lon0)
    gs.km = proietta(gs.tenute_ll, gs.lon0, gs.lat0)
    gs.km_semplice = shapely.simplify(gs.km, min(0.5, 0.01 * math.sqrt(max(gs.km.area, 1e-9))))
    # versione semplificata in gradi (~0,5 km), usata per i confronti tra stati
    tol_gradi = min(0.005, 0.01 * math.sqrt(max(gs.tenute_ll.area, 1e-12)))
    gs.tenute_ll_semplice = shapely.simplify(gs.tenute_ll, tol_gradi)
    b = gs.km.bounds
    gs.raggio = max(math.hypot(x, y) for x, y in [(b[0], b[1]), (b[0], b[3]), (b[2], b[1]), (b[2], b[3])])
    gs.area = gs.km.area
    gs.n_parti = len(tenuti)
    gs.n_scartate = n - len(tenuti)
    return gs


def proietta_su(gs_dest, geom_ll):
    """Proietta una geometria (lon/lat) nel sistema locale di gs_dest."""
    return proietta(ricentra(geom_ll, gs_dest.lon0), gs_dest.lon0, gs_dest.lat0)


# ---------------------------------------------------------------------------
# Sagome
# ---------------------------------------------------------------------------
def rendi_sagoma(gs, lato=1024, ss=4, pad=8):
    minx, miny, maxx, maxy = gs.km.bounds
    w, h = max(maxx - minx, 1e-6), max(maxy - miny, 1e-6)
    utile = lato - 2 * pad
    scala = utile / max(w, h)
    W = int(round(w * scala)) + 2 * pad
    H = int(round(h * scala)) + 2 * pad
    W, H = max(W, 2 * pad + 4), max(H, 2 * pad + 4)
    px = km_a_pixel(gs.km, minx, maxy, scala * ss, pad * ss)
    maschera = disegna_maschera(poligoni(px), W * ss, H * ss)
    maschera = maschera.resize((W, H), Image.Resampling.BOX)
    bianco = Image.new("L", (W, H), 255)
    return Image.merge("LA", (bianco, maschera))


# ---------------------------------------------------------------------------
# Vicini
# ---------------------------------------------------------------------------
def calcola_vicini(geos):
    """Per ogni stato: confinanti terrestri e stati più vicini (con distanze in km)."""
    codici = list(geos)
    centri = {k: (geos[k].lon0, geos[k].lat0) for k in codici}
    confinanti = {k: {} for k in codici}
    distanze = {k: {} for k in codici}
    for i, a in enumerate(codici):
        A = geos[a]
        for b in codici:
            if a == b:
                continue
            B = geos[b]
            dc = haversine(*centri[a], *centri[b])
            if dc > A.raggio + B.raggio + 4000:
                continue
            Bk = proietta_su(A, B.tenute_ll_semplice)
            d = A.km_semplice.distance(Bk)
            distanze[a][b] = d
            if d < 1.0:
                # lunghezza approssimata del confine comune
                lung = A.km_semplice.buffer(2.0).intersection(Bk.boundary).length
                confinanti[a][b] = lung
        if not distanze[a]:
            # stato isolatissimo: confronto con tutti
            for b in codici:
                if b != a:
                    B = geos[b]
                    distanze[a][b] = haversine(*centri[a], *centri[b]) - B.raggio
        if (i + 1) % 40 == 0:
            log(f"  vicini: {i + 1}/{len(codici)}")
    return confinanti, distanze


def scegli_candidati(iso, confinanti, distanze, fasce, max_n=3):
    """Lista ordinata di candidati per l'aiuto "stato confinante".
    Prima i confinanti più riconoscibili (fascia bassa, poi confine più lungo);
    se non bastano, gli stati più vicini."""
    cand = []
    conf = confinanti[iso]
    for b in sorted(conf, key=lambda k: (fasce[k], -conf[k])):
        cand.append((b, "confinante"))
    if len(cand) < max_n:
        tipo = "vicino_isola" if not conf else "vicino"
        vicini = [b for b in sorted(distanze[iso], key=lambda k: distanze[iso][k]) if b not in conf]
        vicini = vicini[: max(0, max_n - len(cand)) + (2 if not conf else 0)]
        vicini = sorted(vicini, key=lambda k: (fasce[k], distanze[iso][k])) if not conf else vicini
        for b in vicini:
            if len(cand) >= max_n:
                break
            cand.append((b, tipo))
    return cand[:max_n]


def rendi_composito(A, B, lato=800, ss=3):
    """Immagine con lo stato misterioso (bianco) e il vicino (oro), nella
    proiezione locale del misterioso. Restituisce (immagine, etichetta_norm)."""
    a = A.km
    b = proietta_su(A, B.tenute_ll)
    b = b.buffer(0) if not b.is_valid else b
    ax0, ay0, ax1, ay1 = a.bounds
    cx, cy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
    w, h = max(ax1 - ax0, 1e-3), max(ay1 - ay0, 1e-3)
    est = max(w, h)
    fattore = 2.5
    area_b = b.area
    for _ in range(14):
        # finestra massima: quadrato di lato fattore*estensione
        mx0, my0 = cx - fattore * est / 2, cy - fattore * est / 2
        mx1, my1 = cx + fattore * est / 2, cy + fattore * est / 2
        bb = b.bounds
        ux0, uy0 = min(ax0, bb[0]), min(ay0, bb[1])
        ux1, uy1 = max(ax1, bb[2]), max(ay1, bb[3])
        mx = 0.08 * max(ux1 - ux0, uy1 - uy0)
        x0, y0 = max(mx0, ux0 - mx), max(my0, uy0 - mx)
        x1, y1 = min(mx1, ux1 + mx), min(my1, uy1 + mx)
        # deve comunque contenere il misterioso con un po' di margine
        x0, y0 = min(x0, ax0 - 0.15 * w), min(y0, ay0 - 0.15 * h)
        x1, y1 = max(x1, ax1 + 0.15 * w), max(y1, ay1 + 0.15 * h)
        finestra = box(x0, y0, x1, y1)
        visibile = b.intersection(finestra).area
        if visibile >= min(0.5 * area_b, 0.03 * finestra.area):
            break
        fattore *= 1.3
    # proporzioni ragionevoli (tra 1:2 e 2:1)
    fw, fh = x1 - x0, y1 - y0
    if fw < 0.5 * fh:
        d = (0.5 * fh - fw) / 2
        x0, x1 = x0 - d, x1 + d
    elif fh < 0.5 * fw:
        d = (0.5 * fw - fh) / 2
        y0, y1 = y0 - d, y1 + d
    fw, fh = x1 - x0, y1 - y0
    finestra = box(x0, y0, x1, y1)
    scala = lato / max(fw, fh)
    W, H = max(int(round(fw * scala)), 8), max(int(round(fh * scala)), 8)

    b_vis = b.intersection(finestra.buffer(0.02 * max(fw, fh)))
    a_px = km_a_pixel(a, x0, y1, scala * ss, 0)
    b_px = km_a_pixel(b_vis, x0, y1, scala * ss, 0)
    ma = np.asarray(disegna_maschera(poligoni(a_px), W * ss, H * ss).resize((W, H), Image.Resampling.BOX),
                    dtype=np.float32) / 255.0
    mb = np.asarray(disegna_maschera(poligoni(b_px), W * ss, H * ss).resize((W, H), Image.Resampling.BOX),
                    dtype=np.float32) / 255.0
    mb = mb * (1.0 - ma)
    alpha = np.clip(ma + mb, 0, 1)
    rgb = np.zeros((H, W, 3), dtype=np.float32)
    col = np.array(COLORE_VICINO, dtype=np.float32)
    rgb += mb[..., None] * col
    rgb += ma[..., None] * 255.0
    with np.errstate(invalid="ignore", divide="ignore"):
        rgb = np.where(alpha[..., None] > 0, rgb / np.maximum(alpha[..., None], 1e-6), 0)
    arr = np.dstack([np.clip(rgb, 0, 255), alpha * 255.0]).astype(np.uint8)
    img = Image.fromarray(arr, "RGBA")

    # punto per l'etichetta: polo di inaccessibilità della parte visibile più grande del vicino
    interno = box(x0 + 0.06 * fw, y0 + 0.06 * fh, x1 - 0.06 * fw, y1 - 0.06 * fh)
    vis = b.intersection(interno)
    pezzi = poligoni(vis)
    if pezzi:
        grande = max(pezzi, key=lambda p: p.area)
        try:
            pt = polylabel(grande, tolerance=max(fw, fh) / 200.0)
        except Exception:
            pt = grande.representative_point()
    else:
        pt = b.representative_point()
    ex = (pt.x - x0) / fw
    ey = (y1 - pt.y) / fh
    return img, [round(min(max(ex, 0.0), 1.0), 4), round(min(max(ey, 0.0), 1.0), 4)]


# ---------------------------------------------------------------------------
# Similarità delle sagome
# ---------------------------------------------------------------------------
def maschere_normalizzate(gs, lato=64, scale=(0.85, 1.0, 1.15), ss=4):
    """Sagoma centrata sul centroide e scalata per area su una griglia lato x lato."""
    c = gs.km.centroid
    area_obiettivo = 0.08 * lato * lato
    out = []
    for s in scale:
        k = math.sqrt(area_obiettivo / max(gs.area, 1e-9)) * s

        def f(cc, k=k):
            return np.column_stack([(cc[:, 0] - c.x) * k * ss + lato * ss / 2,
                                    (c.y - cc[:, 1]) * k * ss + lato * ss / 2])
        px = shapely.transform(gs.km_semplice, f)
        px = px.intersection(box(-2, -2, lato * ss + 2, lato * ss + 2))
        m = disegna_maschera(poligoni(px), lato * ss, lato * ss).resize((lato, lato), Image.Resampling.BOX)
        out.append(np.asarray(m, dtype=np.float32).ravel() / 255.0)
    return out


def calcola_similarita(geos, codici):
    log("  rasterizzazione 64x64...")
    M = {k: maschere_normalizzate(geos[k]) for k in codici}
    base = np.stack([M[k][1] for k in codici])                 # (n, 4096)
    varianti = [np.stack([M[k][j] for k in codici]) for j in range(3)]
    n = len(codici)
    S = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        a = base[i][None, :]
        migliore = np.zeros(n, dtype=np.float32)
        for V in varianti:
            inter = np.minimum(a, V).sum(axis=1)
            unione = np.maximum(a, V).sum(axis=1)
            iou = inter / np.maximum(unione, 1e-6)
            migliore = np.maximum(migliore, iou)
        S[i] = migliore
    S = np.maximum(S, S.T)
    np.fill_diagonal(S, -1)
    return S


# ---------------------------------------------------------------------------
# Mappa del mondo (proiezione Equal Earth)
# ---------------------------------------------------------------------------
EE_A1, EE_A2, EE_A3, EE_A4 = 1.340264, -0.081106, 0.000893, 0.003796
EE_M = math.sqrt(3) / 2


def equal_earth(lon, lat):
    lam = np.radians(lon)
    phi = np.radians(lat)
    th = np.arcsin(EE_M * np.sin(phi))
    t2 = th * th
    t6 = t2 ** 3
    x = lam * np.cos(th) / (EE_M * (EE_A1 + 3 * EE_A2 * t2 + t6 * (7 * EE_A3 + 9 * EE_A4 * t2)))
    y = th * (EE_A1 + EE_A2 * t2 + t6 * (EE_A3 + EE_A4 * t2))
    return x, y


def prepara_mondo(ne_ita, geos_raw, geos, cartella, larghezza=1400, ss=3):
    os.makedirs(cartella, exist_ok=True)
    xmax, _ = equal_earth(np.array([180.0]), np.array([0.0]))
    xmax = float(xmax[0])
    _, ytop = equal_earth(np.array([0.0]), np.array([84.0]))
    _, ybot = equal_earth(np.array([0.0]), np.array([-57.0]))
    ytop, ybot = float(ytop[0]), float(ybot[0])
    scala = larghezza / (2 * xmax)
    altezza = int(round((ytop - ybot) * scala))

    def a_pixel(geom, k=1.0):
        def f(c):
            x, y = equal_earth(c[:, 0], np.clip(c[:, 1], -89.9, 89.9))
            return np.column_stack([(x + xmax) * scala * k, (ytop - y) * scala * k])
        return shapely.transform(geom, f)

    # base: tutte le terre (anche dipendenze), esclusa l'Antartide; per i 197 stati
    # si usa la geometria già fusa (così le lacune colmate compaiono anche qui)
    usati = {CODICE_NE.get(k, k) for k in geos_raw}
    for k in geos_raw:
        usati.update(FUSIONI.get(k, []))
    terre = [g for cod, (p, g) in ne_ita.items() if cod != "ATA" and cod not in usati]
    terre += [g for (p, g) in geos_raw.values()]
    W, H = larghezza * ss, altezza * ss
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    colore_terra = (52, 68, 102, 255)
    colore_bordo = (24, 32, 54, 255)
    for g in terre:
        for p in poligoni(a_pixel(g, ss)):
            ext = list(p.exterior.coords)
            if len(ext) >= 3:
                d.polygon(ext, fill=colore_terra, outline=colore_bordo, width=max(1, ss // 2))
    img = img.resize((larghezza, altezza), Image.Resampling.LANCZOS)
    img.save(os.path.join(cartella, "mappa.png"), optimize=True)

    # contorni di ogni stato (geometria completa) in pixel della mappa
    contorni = {}
    for iso, (props, g) in geos_raw.items():
        pg = a_pixel(g)
        pg = shapely.simplify(pg, 0.35)
        anelli = []
        for p in sorted(poligoni(pg), key=lambda q: -q.area):
            if p.area < 0.4 and anelli:
                continue
            coords = [[round(x, 1), round(y, 1)] for x, y in p.exterior.coords]
            if len(coords) >= 3:
                anelli.append(coords)
        # punto di riferimento: centro della parte principale (quella della sagoma)
        principale = max(poligoni(geos[iso].tenute_ll), key=lambda q: area_approssimata(q))
        rp = principale.representative_point()
        lon = ((rp.x + 180.0) % 360.0) - 180.0
        x, y = equal_earth(np.array([lon]), np.array([rp.y]))
        bx = pg.bounds
        contorni[iso] = {
            "anelli": anelli,
            "punto": [round(float((x[0] + xmax) * scala), 1), round(float((ytop - y[0]) * scala), 1)],
            "piccolo": bool(max(bx[2] - bx[0], bx[3] - bx[1]) < 10),
        }
    with open(os.path.join(cartella, "stati_mappa.json"), "w", encoding="utf-8") as f:
        json.dump({"larghezza": larghezza, "altezza": altezza, "stati": contorni}, f,
                  ensure_ascii=False, separators=(",", ":"))
    return larghezza, altezza


# ---------------------------------------------------------------------------
# Icona
# ---------------------------------------------------------------------------
def disegna_icona(percorso_ico, percorso_png):
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    # disco blu notte con anello dorato
    d.ellipse([24, 24, S - 24, S - 24], fill=(10, 18, 44, 255))
    d.ellipse([24, 24, S - 24, S - 24], outline=(232, 178, 58, 255), width=28)
    d.ellipse([110, 110, S - 110, S - 110], outline=(90, 130, 200, 255), width=8)
    # rosa dei venti a 8 punte

    def punta(ang, lung, larg, colore):
        a = math.radians(ang)
        px, py = c + lung * math.sin(a), c - lung * math.cos(a)
        l1 = (c + larg * math.sin(a - math.pi / 2), c - larg * math.cos(a - math.pi / 2))
        l2 = (c + larg * math.sin(a + math.pi / 2), c - larg * math.cos(a + math.pi / 2))
        d.polygon([l1, (px, py), l2, (c, c)], fill=colore)
    for ang in (45, 135, 225, 315):
        punta(ang, 300, 60, (120, 160, 220, 255))
    for ang in (0, 90, 180, 270):
        punta(ang, 400, 82, (245, 245, 250, 255))
    punta(0, 400, 82, (232, 178, 58, 255))
    d.ellipse([c - 46, c - 46, c + 46, c + 46], fill=(10, 18, 44, 255), outline=(232, 178, 58, 255), width=14)
    img.resize((256, 256), Image.Resampling.LANCZOS).save(percorso_png)
    img.save(percorso_ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


# ---------------------------------------------------------------------------
# Anteprime
# ---------------------------------------------------------------------------
def font_anteprima(dimensione):
    p = os.path.join(ASSETS, "font", "Montserrat-SemiBold.ttf")
    try:
        return ImageFont.truetype(p, dimensione)
    except Exception:
        return ImageFont.load_default()


def griglia_sagome(elenco, cartella, per_pagina=48, colonne=8, cella=230):
    os.makedirs(cartella, exist_ok=True)
    f = font_anteprima(15)
    pagine = []
    for n0 in range(0, len(elenco), per_pagina):
        blocco = elenco[n0:n0 + per_pagina]
        righe = math.ceil(len(blocco) / colonne)
        img = Image.new("RGB", (colonne * cella, righe * (cella + 22)), (0, 0, 0))
        d = ImageDraw.Draw(img)
        for k, (iso, nome, fascia, escluso) in enumerate(blocco):
            r, c = divmod(k, colonne)
            x, y = c * cella, r * (cella + 22)
            s = Image.open(os.path.join(ASSETS, "sagome", iso + ".png")).convert("RGBA")
            s.thumbnail((cella - 16, cella - 16), Image.Resampling.LANCZOS)
            img.paste(s, (x + (cella - s.width) // 2, y + (cella - s.height) // 2), s)
            d.rectangle([x, y, x + cella - 1, y + cella + 21], outline=(40, 50, 80))
            col = (255, 120, 120) if escluso else (255, 210, 90)
            d.text((x + 6, y + cella - 2), f"{nome} [{iso}] F{fascia}", fill=col, font=f)
        p = os.path.join(cartella, f"sagome_{n0 // per_pagina + 1:02d}.png")
        img.save(p)
        pagine.append(p)
    return pagine


def griglia_compositi(campioni, nomi, cartella, colonne=6, cella=300):
    f = font_anteprima(14)
    righe = math.ceil(len(campioni) / colonne)
    img = Image.new("RGB", (colonne * cella, righe * (cella + 20)), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, (iso, v) in enumerate(campioni):
        r, c = divmod(k, colonne)
        x, y = c * cella, r * (cella + 20)
        s = Image.open(os.path.join(ASSETS, v["immagine"])).convert("RGBA")
        s.thumbnail((cella - 10, cella - 10), Image.Resampling.LANCZOS)
        ox, oy = x + (cella - s.width) // 2, y + (cella - s.height) // 2
        img.paste(s, (ox, oy), s)
        ex, ey = v["etichetta"]
        lx, ly = ox + ex * s.width, oy + ey * s.height
        d.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(255, 0, 0))
        d.text((lx + 5, ly - 8), nomi[v["iso"]], fill=(255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
        d.rectangle([x, y, x + cella - 1, y + cella + 19], outline=(40, 50, 80))
        d.text((x + 5, y + cella), f"{nomi[iso]} + {nomi[v['iso']]} ({v['tipo']})", fill=(255, 210, 90), font=f)
    p = os.path.join(cartella, "compositi_esempio.png")
    img.save(p)
    return p


# ---------------------------------------------------------------------------
# Principale
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default=os.path.join(RADICE, "tools", "_cache"),
                    help="cartella per i file scaricati")
    ap.add_argument("--ripristina", action="store_true",
                    help="ignora le modifiche manuali in assets/stati.json")
    ap.add_argument("--solo", default="", help="(debug) elenco ISO3 separati da virgola")
    args = ap.parse_args()

    for sub in ("sagome", "vicini", "bandiere", "mondo", "font"):
        os.makedirs(os.path.join(ASSETS, sub), exist_ok=True)
    os.makedirs(ANTEPRIME, exist_ok=True)

    assert len(STATI) == 197, len(STATI)
    assert len({s[0] for s in STATI}) == 197
    assert set(NOMI_EN) == {s[0] for s in STATI}, set(NOMI_EN) ^ {s[0] for s in STATI}

    # --- valori modificabili già presenti in stati.json ---
    precedenti = {}
    p_stati = os.path.join(ASSETS, "stati.json")
    if os.path.exists(p_stati) and not args.ripristina:
        with open(p_stati, encoding="utf-8") as f:
            for s in json.load(f)["stati"]:
                precedenti[s["iso"]] = s
        log(f"Mantengo le modifiche manuali di {len(precedenti)} stati (usa --ripristina per azzerarle)")

    # --- download ---
    log("Download sorgenti...")
    p_ita = scarica(URL_NE + FILE_NE_ITA, os.path.join(args.cache, "ne", FILE_NE_ITA))
    p_def = scarica(URL_NE + FILE_NE_DEF, os.path.join(args.cache, "ne", FILE_NE_DEF))
    for nome in FILE_FONT + ["OFL.txt"]:
        scarica(URL_FONT + ("fonts/ttf/" + nome if nome.endswith(".ttf") else nome),
                os.path.join(args.cache, "font", nome))
    for iso, iso2, _, _ in STATI:
        scarica(URL_BANDIERE.format(iso2.lower()), os.path.join(args.cache, "bandiere", iso2.lower() + ".png"))
    scarica(URL_LICENZA_BANDIERE, os.path.join(args.cache, "bandiere", "README.md"))

    # --- font e bandiere ---
    for nome in FILE_FONT + ["OFL.txt"]:
        with open(os.path.join(args.cache, "font", nome), "rb") as fi, \
                open(os.path.join(ASSETS, "font", nome), "wb") as fo:
            fo.write(fi.read())
    for iso, iso2, nome, _ in STATI:
        src = os.path.join(args.cache, "bandiere", iso2.lower() + ".png")
        im = Image.open(src)
        im.load()
        if im.width < 50 or im.height < 20:
            raise SystemExit(f"Bandiera sospetta per {iso}: {im.size}")
        im.convert("RGBA").save(os.path.join(ASSETS, "bandiere", iso + ".png"), optimize=True)
    log("  bandiere: 197 ok")

    # --- eccezioni ---
    p_ecc = os.path.join(ASSETS, "eccezioni_sagome.json")
    if not os.path.exists(p_ecc):
        with open(p_ecc, "w", encoding="utf-8") as f:
            json.dump(ECCEZIONI_DEFAULT, f, ensure_ascii=False, indent=2)
    with open(p_ecc, encoding="utf-8") as f:
        eccezioni_file = json.load(f)
    parametri = dict(ECCEZIONI_DEFAULT["parametri"])
    parametri.update(eccezioni_file.get("parametri", {}))
    eccezioni = eccezioni_file.get("stati", {})

    # --- geometrie ---
    log("Lettura Natural Earth...")
    ne_ita = carica_geojson(p_ita)
    ne_def = carica_geojson(p_def)
    log("Costruzione geometrie (vista italiana + fusioni + lacune)...")
    geos_raw = costruisci_geometrie(ne_ita, ne_def)

    codici = [s[0] for s in STATI]
    if args.solo:
        codici = [c for c in args.solo.split(",") if c]
    log("Scelta delle parti e proiezione locale...")
    geos = {}
    for k, iso in enumerate(codici):
        geos[iso] = prepara_stato(iso, geos_raw[iso][1], eccezioni, parametri)
    log("  fatto")

    nomi = {s[0]: s[2] for s in STATI}
    fasce = {}
    esclusi = {}
    for iso, iso2, nome, fascia in STATI:
        pr = precedenti.get(iso, {})
        nomi[iso] = pr.get("nome", nome)
        fasce[iso] = int(pr.get("fascia", fascia))
        esclusi[iso] = bool(pr.get("escluso", iso in ESCLUSI_DEFAULT))

    # confronto con NAME_IT di Natural Earth (per documentazione)
    differenze = []
    for iso in codici:
        nit = geos_raw[iso][0].get("NAME_IT")
        if nit != nomi[iso]:
            differenze.append((iso, nit, nomi[iso]))

    log("Rendering sagome...")
    for iso in codici:
        rendi_sagoma(geos[iso]).save(os.path.join(ASSETS, "sagome", iso + ".png"), optimize=True)

    log("Calcolo vicini...")
    confinanti, distanze = calcola_vicini(geos)

    log("Rendering compositi 'confinante'...")
    for f in os.listdir(os.path.join(ASSETS, "vicini")):
        os.remove(os.path.join(ASSETS, "vicini", f))
    vicini_out = {}
    for iso in codici:
        cand = scegli_candidati(iso, confinanti, distanze, fasce)
        lista = []
        for b, tipo in cand:
            img, etichetta = rendi_composito(geos[iso], geos[b])
            rel = f"vicini/{iso}_{b}.png"
            img.save(os.path.join(ASSETS, rel), optimize=True)
            lista.append({"iso": b, "tipo": tipo, "immagine": rel, "etichetta": etichetta})
        vicini_out[iso] = lista

    log("Similarità delle sagome...")
    S = calcola_similarita(geos, codici)
    simili = {}
    for i, iso in enumerate(codici):
        ordine = np.argsort(-S[i])[:15]
        simili[iso] = [codici[j] for j in ordine]
        simili_punteggi = [round(float(S[i, j]), 3) for j in ordine]
        simili[iso + "_p"] = simili_punteggi

    log("Mappa del mondo...")
    prepara_mondo(ne_ita, {k: geos_raw[k] for k in codici}, geos, os.path.join(ASSETS, "mondo"))

    log("Icona...")
    disegna_icona(os.path.join(ASSETS, "icona.ico"), os.path.join(ASSETS, "icona.png"))

    # --- stati.json ---
    stati_out = []
    for iso, iso2, _, _ in STATI:
        if iso not in geos:
            continue
        props = geos_raw[iso][0]
        cont, reg = REGIONI.get(props["SUBREGION"], ("?", "?"))
        pr = precedenti.get(iso, {})
        stati_out.append({
            "iso": iso,
            "iso2": iso2,
            "nome": nomi[iso],
            "nome_en": pr.get("nome_en", NOMI_EN[iso]),
            "fascia": fasce[iso],
            "escluso": esclusi[iso],
            "continente": pr.get("continente", cont),
            "regione": pr.get("regione", reg),
            "sagoma": f"sagome/{iso}.png",
            "bandiera": f"bandiere/{iso}.png",
            "confinanti": sorted(confinanti[iso], key=lambda k: -confinanti[iso][k]),
            "vicini": vicini_out[iso],
            "simili": simili[iso],
            "simili_punteggio": simili[iso + "_p"],
            "parti": geos[iso].n_parti,
            "parti_scartate": geos[iso].n_scartate,
        })
    with open(p_stati, "w", encoding="utf-8") as f:
        json.dump({
            "_nota": ("Campi modificabili a mano: nome, nome_en, fascia (1-5), escluso (true/false), "
                      "continente, regione. Gli altri sono generati da tools/prepara_dati.py."),
            "generato": datetime.date.today().isoformat(),
            "fonte": "Natural Earth 10m admin_0_countries (vista ITA), pubblico dominio",
            "stati": stati_out,
        }, f, ensure_ascii=False, indent=1)
    log(f"Scritto {p_stati}: {len(stati_out)} stati")

    # --- riepilogo ---
    conteggi = {}
    for s in stati_out:
        if not s["escluso"]:
            conteggi[s["fascia"]] = conteggi.get(s["fascia"], 0) + 1
    log("Stati giocabili per fascia:", dict(sorted(conteggi.items())))
    log("Nomi corretti rispetto a NAME_IT:")
    for iso, a, b in differenze:
        log(f"  {iso}: '{a}' -> '{b}'")
    with open(os.path.join(ANTEPRIME, "nomi_corretti.txt"), "w", encoding="utf-8") as f:
        for iso, a, b in differenze:
            f.write(f"{iso}: '{a}' -> '{b}'\n")
    with open(os.path.join(ANTEPRIME, "parti_scartate.txt"), "w", encoding="utf-8") as f:
        for iso in codici:
            g = geos[iso]
            if g.scartate:
                grandi = sorted(g.scartate, key=lambda t: -t[1])[:6]
                desc = ", ".join(f"({((p.x + 180) % 360) - 180:.1f},{p.y:.1f}) {a:.0f}km²" for p, a in grandi)
                f.write(f"{iso} {nomi[iso]}: tenute {g.n_parti}, scartate {g.n_scartate}: {desc}\n")

    # --- anteprime ---
    log("Anteprime...")
    elenco = [(s["iso"], s["nome"], s["fascia"], s["escluso"]) for s in stati_out]
    griglia_sagome(elenco, ANTEPRIME)
    campioni = []
    for iso in ["ITA", "EST", "PRT", "VAT", "CHL", "JPN", "LSO", "GMB", "RUS", "NZL", "CUB", "FJI",
                "USA", "SMR", "BRN", "AUT", "KOR", "MDG", "ISL", "TLS", "QAT", "CAN", "MCO", "SGP"]:
        if iso in vicini_out and vicini_out[iso]:
            campioni.append((iso, vicini_out[iso][0]))
    griglia_compositi(campioni, nomi, ANTEPRIME)
    log("Fatto.")


if __name__ == "__main__":
    main()
