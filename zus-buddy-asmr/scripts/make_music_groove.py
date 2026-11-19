"""Upbeat-but-chill background loop (original, synthesized). ~100 BPM mellow electric piano groove.

Run:  python3 scripts/make_music_groove.py  ->  assets/music/groove_bed.wav
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
rng = np.random.default_rng(5)
BPM = 100
beat = 60 / BPM
bars = 20  # ~48 s
total = int((bars * 4 * beat + 3) * SR)
mix = np.zeros((total, 2))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def ep(freq, dur, vel=1.0, decay=0.9):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(t / 0.006, 1) * np.exp(-t / decay)
    tone = np.sin(2 * np.pi * freq * t) + 0.22 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t / 0.3) \
        + 0.07 * np.sin(2 * np.pi * freq * 3.98 * t) * np.exp(-t / 0.12)
    return tone * env * vel


def bell(freq, dur, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(t / 0.003, 1) * np.exp(-t / 0.45)
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.15)) * env * vel


def add(sig, at, pan=0.0, gain=1.0):
    s = int(at * SR)
    if s >= total:
        return
    e = min(total, s + len(sig))
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    mix[s:e, 0] += sig[: e - s] * l * gain
    mix[s:e, 1] += sig[: e - s] * r * gain


def noise_hit(dur, hp, tau):
    ln = int(dur * SR)
    nz = rng.standard_normal(ln) * np.exp(-np.arange(ln) / SR / tau)
    bb, aa = butter(2, hp / (SR / 2), btype="high")
    return lfilter(bb, aa, nz)


# I - vi - IV - V in C, with 7ths: Cmaj7 Am7 Fmaj7 G6  (happy, bouncy)
CH = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 64]]
BASS = [36, 33, 41, 43]
# bass pattern in 8ths (1 = root, 8 = octave, 5 = fifth, None = rest)
BPAT = [1, None, 1, 8, None, 5, 1, None]
MEL = [[79, None, 76, None, 74, 76, None, None], [72, None, 76, None, 79, None, 81, None],
       [81, None, 79, 77, 76, None, 74, None], [74, 76, None, 79, None, None, None, None]]
# chord stab rhythm in 8ths: offbeat-heavy for groove
STAB = [0, 1, 0, 1, 1, 0, 1, 0]

for bar in range(bars):
    b0 = bar * 4 * beat
    ch, root = CH[bar % 4], BASS[bar % 4]
    for i, on in enumerate(STAB):
        if on:
            for j, n in enumerate(ch):
                add(ep(midi(n), 0.6, 0.20, 0.25), b0 + i * beat / 2 + j * 0.008, pan=-0.3 + j * 0.2)
    # soft pad hold so it isn't choppy
    for j, n in enumerate(ch):
        add(ep(midi(n), 4 * beat, 0.07, 2.5), b0, pan=-0.3 + j * 0.2)
    for i, step in enumerate(BPAT):
        if step is None:
            continue
        n = root + {1: 0, 8: 12, 5: 7}[step]
        t = np.arange(int(0.42 * beat * 2 * SR)) / SR
        bass = (np.sin(2 * np.pi * midi(n) * t) + 0.15 * np.sin(2 * np.pi * midi(n) * 2 * t)) * np.minimum(t / 0.01, 1) * np.exp(-t / 0.22)
        add(bass, b0 + i * beat / 2, gain=0.5)
    if bar >= 2:  # drums
        for k in (0, 2):
            t = np.arange(int(0.25 * SR)) / SR
            add(np.sin(2 * np.pi * (48 + 70 * np.exp(-t * 35)) * t) * np.exp(-t / 0.13), b0 + k * beat, gain=0.45)
        add(np.sin(2 * np.pi * (48 + 70 * np.exp(-np.arange(int(0.2 * SR)) / SR * 35)) * np.arange(int(0.2 * SR)) / SR) * np.exp(-np.arange(int(0.2 * SR)) / SR / 0.1), b0 + 2.5 * beat, gain=0.3)
        for k in (1, 3):  # soft clap
            add(noise_hit(0.18, 1200, 0.045), b0 + k * beat, pan=0.1, gain=0.10)
        for i in range(8):  # hats
            add(noise_hit(0.05, 7000, 0.012), b0 + i * beat / 2, pan=0.35, gain=0.06 if i % 2 else 0.035)
    if bar >= 4:  # bouncy bell melody
        for k, n in enumerate(MEL[bar % 4]):
            if n is not None and not (bar % 8 >= 6 and k > 3):
                add(bell(midi(n), 0.9, 0.18), b0 + k * beat / 2, pan=0.15)

bb, aa = butter(2, 7000 / (SR / 2))
mix = lfilter(bb, aa, mix, axis=0)
fi = int(0.6 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(3.0 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = mix / np.max(np.abs(mix)) * 0.85
wavfile.write("assets/music/groove_bed.wav", SR, (mix * 32767).astype(np.int16))
print("groove_bed.wav", round(total / SR, 1), "s")
