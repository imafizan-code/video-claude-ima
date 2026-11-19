"""Upbeat, excited pop background track (original, synthesized). 122 BPM, four-on-the-floor.
No bell/mallet timbres. Bright filtered-saw chords, bouncy bass, square-wave lead, claps.

Run:  python3 scripts/make_music_upbeat.py  ->  assets/music/upbeat_bed.wav
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
rng = np.random.default_rng(11)
BPM = 122
beat = 60 / BPM
bars = 18  # ~35 s
total = int((bars * 4 * beat + 2.5) * SR)
mix = np.zeros((total, 2))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def saw(freq, t, harmonics=14):
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if freq * k > 12000:
            break
        out += np.sin(2 * np.pi * freq * k * t) / k
    return out


def square(freq, t, harmonics=9):
    out = np.zeros_like(t)
    for k in range(1, 2 * harmonics, 2):
        if freq * k > 12000:
            break
        out += np.sin(2 * np.pi * freq * k * t) / k
    return out


def adsr(n, a=0.005, d=0.12, s=0.5, r=0.06):
    t = np.arange(n) / SR
    dur = n / SR
    e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / d))
    rel = np.clip((dur - t) / r, 0, 1)
    return e * rel


def lp(x, fc):
    b, a = butter(2, fc / (SR / 2))
    return lfilter(b, a, x)


def hp(x, fc):
    b, a = butter(2, fc / (SR / 2), btype="high")
    return lfilter(b, a, x)


def add(sig, at, pan=0.0, gain=1.0):
    s = int(at * SR)
    if s >= total:
        return
    e = min(total, s + len(sig))
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    mix[s:e, 0] += sig[: e - s] * l * gain
    mix[s:e, 1] += sig[: e - s] * r * gain


cache = {}


def chord_stab(notes, dur):
    k = (tuple(notes), dur)
    if k not in cache:
        n = int(dur * SR)
        t = np.arange(n) / SR
        sig = np.zeros(n)
        for m in notes:
            for det in (-0.12, 0.12):  # light detune = wide, bright
                sig += saw(midi(m + det / 1.0), t, 10)
        cache[k] = lp(sig, 4200) * adsr(n, 0.004, 0.09, 0.35, 0.04)
    return cache[k]


def bass_note(m, dur):
    k = ("b", m, dur)
    if k not in cache:
        n = int(dur * SR)
        t = np.arange(n) / SR
        sig = lp(saw(midi(m), t, 8), 900) + 0.6 * np.sin(2 * np.pi * midi(m) * t)
        cache[k] = sig * adsr(n, 0.003, 0.1, 0.6, 0.03)
    return cache[k]


def lead_note(m, dur):
    k = ("l", m, dur)
    if k not in cache:
        n = int(dur * SR)
        t = np.arange(n) / SR
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(t / 0.2, 1)
        sig = lp(square(midi(m), t * vib, 7), 3800)
        cache[k] = sig * adsr(n, 0.006, 0.15, 0.55, 0.05)
    return cache[k]


KICK = (lambda t: np.sin(2 * np.pi * (50 + 110 * np.exp(-t * 40)) * t) * np.exp(-t / 0.16))(np.arange(int(0.3 * SR)) / SR)
CLAP = hp(rng.standard_normal(int(0.22 * SR)), 900) * np.exp(-np.arange(int(0.22 * SR)) / SR / 0.06)
HAT = hp(rng.standard_normal(int(0.06 * SR)), 8000) * np.exp(-np.arange(int(0.06 * SR)) / SR / 0.015)
OPENHAT = hp(rng.standard_normal(int(0.2 * SR)), 7000) * np.exp(-np.arange(int(0.2 * SR)) / SR / 0.07)

# I - V - vi - IV in D major (bright, excited): D  A  Bm  G
CH = [[62, 66, 69, 74], [61, 64, 69, 73], [62, 66, 71, 74], [62, 67, 71, 74]]
ROOT = [38, 33, 35, 31]
# off-beat pumping stabs (16th grid positions)
STABS = [2, 6, 10, 13, 14]
# bass: octave bounce in 8ths
BASSPAT = [0, 12, 0, 12, 0, 12, 7, 12]
# catchy lead (16th-grid, (pos, midi, len16))
HOOK = [
    [(0, 78, 2), (2, 76, 2), (4, 74, 2), (6, 76, 3), (10, 78, 2), (12, 81, 4)],
    [(0, 76, 2), (2, 73, 2), (4, 76, 3), (8, 73, 2), (10, 71, 2), (12, 69, 4)],
    [(0, 71, 2), (2, 74, 2), (4, 78, 3), (8, 76, 2), (10, 74, 2), (12, 71, 3)],
    [(0, 74, 2), (2, 76, 2), (4, 79, 4), (8, 78, 2), (10, 76, 2), (12, 74, 4)],
]
s16 = beat / 4

for bar in range(bars):
    b0 = bar * 4 * beat
    ch, root = CH[bar % 4], ROOT[bar % 4]
    intro = bar < 1
    for p in STABS:
        add(chord_stab(ch, s16 * 1.6), b0 + p * s16, pan=0.0, gain=0.11)
    for i, step in enumerate(BASSPAT):
        add(bass_note(root + step, beat / 2 * 0.85), b0 + i * beat / 2, gain=0.30)
    for k in range(4):  # four-on-the-floor
        add(KICK, b0 + k * beat, gain=0.55 if not intro else 0.35)
    if not intro:
        for k in (1, 3):
            add(CLAP, b0 + k * beat, pan=0.05, gain=0.20)
        for i in range(16):
            if i % 4 == 2:
                add(OPENHAT, b0 + i * s16, pan=0.3, gain=0.07)
            elif i % 2 == 1:
                add(HAT, b0 + i * s16, pan=-0.3, gain=0.06)
    if bar >= 2:
        for pos, m, ln in HOOK[bar % 4]:
            add(lead_note(m, ln * s16 * 0.95), b0 + pos * s16, pan=0.12, gain=0.10)
    # little riser + crash-ish sweep into bar 2
    if bar == 1:
        n = int(4 * beat * SR)
        tt = np.arange(n) / SR
        add(hp(rng.standard_normal(n), 3000) * (tt / tt[-1]) ** 2, b0, gain=0.05)

# glue: soft-clip + gentle sidechain-ish pump on chords already via stabs
mix = np.tanh(mix * 1.6) / 1.6
fi = int(0.15 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(2.0 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = mix / np.max(np.abs(mix)) * 0.85
wavfile.write("assets/music/upbeat_bed.wav", SR, (mix * 32767).astype(np.int16))
print("upbeat_bed.wav", round(total / SR, 1), "s")
