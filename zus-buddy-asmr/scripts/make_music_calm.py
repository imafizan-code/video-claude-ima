"""Calm, feel-good background loop (original, synthesized). ~78 BPM soft electric-piano lo-fi.

Run:  python3 scripts/make_music_calm.py  ->  assets/music/calm_bed.wav
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
rng = np.random.default_rng(3)
BPM = 78
beat = 60 / BPM
bars = 16  # ~49 s
total = int((bars * 4 * beat + 3) * SR)
mix = np.zeros((total, 2))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def ep(freq, dur, vel=1.0):
    """Soft electric-piano-ish tone: sine + bell partial, slow decay, gentle tremolo."""
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(t / 0.01, 1) * np.exp(-t / 1.6)
    tone = np.sin(2 * np.pi * freq * t) + 0.18 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t / 0.4) \
        + 0.06 * np.sin(2 * np.pi * freq * 3.98 * t) * np.exp(-t / 0.15)
    trem = 1 + 0.06 * np.sin(2 * np.pi * 4.5 * t)
    return tone * env * trem * vel


def bell(freq, dur, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(t / 0.004, 1) * np.exp(-t / 0.7)
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.2)) * env * vel


def add(sig, at, pan=0.0, gain=1.0):
    s = int(at * SR)
    e = min(total, s + len(sig))
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    mix[s:e, 0] += sig[: e - s] * l * gain
    mix[s:e, 1] += sig[: e - s] * r * gain


# Fmaj7 - Em7 - Dm7 - Cmaj7(add9)   (warm, relaxed, happy)
CH = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 62]]
BASS = [41, 40, 38, 36]
MEL = [[76, None, 74, 72], [71, None, 72, None], [69, None, 72, 74], [76, None, None, None],
       [77, None, 76, 74], [74, None, 72, None], [72, 74, 72, 69], [67, None, None, None]]

for bar in range(bars):
    b0 = bar * 4 * beat
    ch = CH[bar % 4]
    # chord on 1 (soft), light re-hit on the "and" of 2 (gentle swing feel)
    for j, n in enumerate(ch):
        add(ep(midi(n), 4 * beat + 0.8, 0.32), b0 + j * 0.018, pan=-0.25 + j * 0.17)
        add(ep(midi(n), 2 * beat, 0.13), b0 + 1.5 * beat + 0.06 + j * 0.012, pan=-0.25 + j * 0.17)
    # warm bass
    t = np.arange(int(3.5 * beat * SR)) / SR
    bass = np.sin(2 * np.pi * midi(BASS[bar % 4]) * t) * np.minimum(t / 0.02, 1) * np.exp(-t / 1.8)
    add(bass, b0, gain=0.55)
    add(np.sin(2 * np.pi * midi(BASS[bar % 4] + 7) * t[: int(beat * SR)]) * np.exp(-t[: int(beat * SR)] / 0.5), b0 + 3 * beat, gain=0.25)
    # melody (bell) from bar 4 onwards, sparse
    if bar >= 4:
        for k, n in enumerate(MEL[bar % 8]):
            if n is not None:
                add(bell(midi(n), 1.6, 0.22), b0 + k * beat, pan=0.2)
    # soft brushed hats + very soft kick from bar 2
    if bar >= 2:
        for i in range(8):
            ln = int(0.07 * SR)
            nz = rng.standard_normal(ln) * np.exp(-np.arange(ln) / SR / 0.02)
            bb, aa = butter(2, 6500 / (SR / 2), btype="high")
            swing = 0.06 if i % 2 else 0.0
            add(lfilter(bb, aa, nz), b0 + i * beat / 2 + swing, pan=0.3, gain=0.05 if i % 2 else 0.035)
        for k in (0, 2.5):
            t = np.arange(int(0.25 * SR)) / SR
            kick = np.sin(2 * np.pi * (45 + 60 * np.exp(-t * 30)) * t) * np.exp(-t / 0.12)
            add(kick, b0 + k * beat, gain=0.35)

# mellow it out: gentle low-pass, fades
bb, aa = butter(2, 5200 / (SR / 2))
mix = lfilter(bb, aa, mix, axis=0)
fi = int(1.0 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(3.0 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = mix / np.max(np.abs(mix)) * 0.85
wavfile.write("assets/music/calm_bed.wav", SR, (mix * 32767).astype(np.int16))
print("calm_bed.wav", round(total / SR, 1), "s")
