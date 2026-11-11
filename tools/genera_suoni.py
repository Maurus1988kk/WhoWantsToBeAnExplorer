# -*- coding: utf-8 -*-
"""
Genera i suoni ORIGINALI del gioco in assets/suoni/ usando solo la libreria
standard (moduli wave, math, array, random). Nessun campione esterno, nessuna
imitazione di sigle esistenti: sono semplici sintesi di onde sinusoidali.

Uso:  python tools/genera_suoni.py
"""

import array
import math
import os
import random
import wave

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARTELLA = os.path.join(RADICE, "assets", "suoni")
SR = 44100          # campioni al secondo
PICCO = 0.42        # volume massimo (moderato)

random.seed(20261109)


def nota(n):
    """Frequenza della nota MIDI n (69 = La 440 Hz)."""
    return 440.0 * 2 ** ((n - 69) / 12.0)


def vuoto(durata):
    return [0.0] * int(durata * SR)


def aggiungi(buf, inizio, campioni):
    i0 = int(inizio * SR)
    if i0 + len(campioni) > len(buf):
        buf.extend([0.0] * (i0 + len(campioni) - len(buf)))
    for i, v in enumerate(campioni):
        buf[i0 + i] += v


def campana(freq, durata, vol=0.5, decad=3.0, armoniche=((1, 1.0), (2, 0.35), (3, 0.12), (4.2, 0.06))):
    """Tono a campana: attacco rapido e decadimento esponenziale."""
    n = int(durata * SR)
    out = [0.0] * n
    for k in range(n):
        t = k / SR
        env = min(1.0, t / 0.006) * math.exp(-decad * t)
        s = 0.0
        for mult, amp in armoniche:
            s += amp * math.sin(2 * math.pi * freq * mult * t)
        out[k] = vol * env * s
    return out


def pad(freqs, durata, vol=0.3, attacco=0.4, rilascio=0.6, vibrato=0.0):
    """Accordo morbido tenuto."""
    n = int(durata * SR)
    out = [0.0] * n
    for k in range(n):
        t = k / SR
        env = min(1.0, t / attacco) * min(1.0, max(0.0, (durata - t) / rilascio))
        s = 0.0
        for j, f in enumerate(freqs):
            fv = f * (1 + vibrato * math.sin(2 * math.pi * 5.0 * t + j))
            s += math.sin(2 * math.pi * fv * t) + 0.25 * math.sin(4 * math.pi * fv * t)
        out[k] = vol * env * s / max(1, len(freqs))
    return out


def normalizza(buf, picco=PICCO):
    m = max(1e-9, max(abs(v) for v in buf))
    return [v * picco / m for v in buf]


def dissolvi(buf, inizio=0.004, fine=0.02):
    n = len(buf)
    a, b = int(inizio * SR), int(fine * SR)
    for i in range(min(a, n)):
        buf[i] *= i / a
    for i in range(min(b, n)):
        buf[n - 1 - i] *= i / b
    return buf


def salva(nome, buf):
    os.makedirs(CARTELLA, exist_ok=True)
    dati = array.array("h", (int(max(-1.0, min(1.0, v)) * 32767) for v in buf))
    with wave.open(os.path.join(CARTELLA, nome), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(dati.tobytes())
    print(f"  {nome}: {len(buf) / SR:.2f} s")


# ---------------------------------------------------------------------------
def tensione():
    """Sottofondo di attesa in loop (6 s): bordone grave che respira e un
    battito sordo. Tutte le frequenze compiono un numero intero di cicli in
    6 secondi, così il loop non ha giunture."""
    durata = 6.0
    n = int(durata * SR)
    buf = [0.0] * n
    for k in range(n):
        t = k / SR
        lfo = 0.65 + 0.35 * math.sin(2 * math.pi * t / 2.0)      # 3 respiri
        s = (math.sin(2 * math.pi * 55.0 * t) * 0.55
             + math.sin(2 * math.pi * 82.5 * t) * 0.35
             + math.sin(2 * math.pi * 110.0 * t) * 0.12 * lfo
             + math.sin(2 * math.pi * 330.0 * t) * 0.025 * (1 - lfo))
        buf[k] = s * lfo * 0.5
    # battito: due colpi ravvicinati ogni 1,5 s
    for b in range(4):
        for dt, vol in ((0.0, 0.7), (0.22, 0.45)):
            t0 = b * 1.5 + dt
            colpo = [vol * math.exp(-18 * (i / SR)) * math.sin(2 * math.pi * (70 - 25 * i / SR) * i / SR)
                     for i in range(int(0.35 * SR))]
            aggiungi(buf, t0, colpo)
    buf = buf[:n]
    return normalizza(buf, 0.30)


def suspense():
    """Attesa dopo la risposta definitiva (1,8 s): tremolo che sale."""
    durata = 1.8
    n = int(durata * SR)
    buf = [0.0] * n
    base = [nota(45), nota(52), nota(57)]
    for k in range(n):
        t = k / SR
        p = t / durata
        trem = 0.55 + 0.45 * math.sin(2 * math.pi * (6 + 10 * p) * t)
        sale = 1 + 0.06 * p
        s = sum(math.sin(2 * math.pi * f * sale * t) for f in base) / 3
        s += 0.2 * math.sin(2 * math.pi * nota(69) * sale * t) * p
        buf[k] = s * trem * (0.25 + 0.75 * p) * min(1.0, (durata - t) / 0.05)
    return normalizza(dissolvi(buf), 0.34)


def blocco():
    """Risposta bloccata: colpo sordo con accordo breve."""
    buf = vuoto(0.7)
    aggiungi(buf, 0, [0.9 * math.exp(-14 * (i / SR)) * math.sin(2 * math.pi * (95 - 40 * i / SR) * i / SR)
                      for i in range(int(0.5 * SR))])
    for f in (nota(57), nota(64)):
        aggiungi(buf, 0.0, campana(f, 0.6, 0.18, decad=6.0))
    return normalizza(dissolvi(buf), 0.34)


def giusta():
    """Risposta giusta: arpeggio maggiore luminoso che sale."""
    buf = vuoto(1.6)
    seq = [72, 76, 79, 84]
    for i, m in enumerate(seq):
        aggiungi(buf, i * 0.085, campana(nota(m), 1.3 - i * 0.1, 0.5, decad=3.2))
    aggiungi(buf, 0.34, pad([nota(60), nota(64), nota(67), nota(72)], 1.2, 0.35, attacco=0.05, rilascio=0.8))
    return normalizza(dissolvi(buf))


def sbagliata():
    """Risposta sbagliata: due toni gravi che scendono, leggermente dissonanti."""
    buf = vuoto(1.5)
    for i, (m1, m2) in enumerate(((52, 53), (47, 48))):
        dur = 0.55 if i == 0 else 0.85
        n = int(dur * SR)
        seg = []
        for k in range(n):
            t = k / SR
            env = min(1.0, t / 0.01) * math.exp(-2.2 * t)
            glis = 1 - 0.03 * t
            s = 0.0
            for m in (m1, m2):
                f = nota(m) * glis
                # onda quasi quadra ammorbidita (prime armoniche dispari)
                s += math.sin(2 * math.pi * f * t) + 0.3 * math.sin(6 * math.pi * f * t) + 0.12 * math.sin(10 * math.pi * f * t)
            seg.append(0.4 * env * s)
        aggiungi(buf, i * 0.42, seg)
    return normalizza(dissolvi(buf), 0.36)


def aiuto():
    """Uso di un aiuto: glissando che sale con scintille."""
    durata = 0.9
    n = int(durata * SR)
    buf = [0.0] * n
    fase = 0.0
    for k in range(n):
        t = k / SR
        p = t / durata
        f = 500 + 1100 * p * p
        fase += 2 * math.pi * f / SR
        env = min(1.0, t / 0.03) * (1 - p) ** 1.5
        buf[k] = 0.35 * env * (math.sin(fase) + 0.3 * math.sin(2 * fase))
    for i in range(9):
        t0 = 0.05 + i * 0.08 + random.uniform(0, 0.02)
        aggiungi(buf, t0, campana(nota(random.choice([84, 88, 91, 96])), 0.25, 0.18, decad=14))
    return normalizza(dissolvi(buf[:n]), 0.32)


def vittoria():
    """Vittoria finale: arpeggi ascendenti e accordo pieno."""
    buf = vuoto(4.2)
    passi = [60, 64, 67, 72, 76, 79, 84]
    for i, m in enumerate(passi):
        aggiungi(buf, i * 0.11, campana(nota(m), 1.0, 0.42, decad=2.6))
    aggiungi(buf, 0.85, pad([nota(48), nota(55), nota(60), nota(64), nota(67), nota(72)], 3.2, 0.5,
                            attacco=0.15, rilascio=1.6, vibrato=0.003))
    for i, m in enumerate([79, 84, 88, 91]):
        aggiungi(buf, 1.0 + i * 0.16, campana(nota(m), 1.6, 0.25, decad=2.0))
    aggiungi(buf, 1.9, campana(nota(96), 1.8, 0.2, decad=1.6))
    return normalizza(dissolvi(buf, fine=0.3))


def clic():
    """Piccolo tic per i pulsanti."""
    n = int(0.05 * SR)
    buf = [0.5 * math.exp(-90 * (k / SR)) * math.sin(2 * math.pi * 1800 * k / SR) for k in range(n)]
    return normalizza(dissolvi(buf, 0.001, 0.01), 0.22)


def main():
    print("Generazione suoni in", CARTELLA)
    salva("tensione.wav", tensione())
    salva("suspense.wav", suspense())
    salva("blocco.wav", blocco())
    salva("giusta.wav", giusta())
    salva("sbagliata.wav", sbagliata())
    salva("aiuto.wav", aiuto())
    salva("vittoria.wav", vittoria())
    salva("clic.wav", clic())
    print("Fatto.")


if __name__ == "__main__":
    main()
