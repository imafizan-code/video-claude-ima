"""Generate original SFX + a light cheerful background loop (no third-party samples).

Run:  python3 scripts/make_audio.py
Outputs WAV files into assets/sfx and assets/music.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import os

SR = 44100
rng = np.random.default_rng(7)
os.makedirs("assets/sfx", exist_ok=True)
os.makedirs("assets/music", exist_ok=True)


def save(path, x, peak=0.89):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    wavfile.write(path, SR, (x * 32767).astype(np.int16))


def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    e = np.minimum(t / a, 1.0) * np.exp(-t / d)
    return e


def t_(dur):
    return np.arange(int(dur * SR)) / SR


# --- pop: bubbly pitch drop sine
t = t_(0.14)
f = 900 * np.exp(-t * 28) + 280
pop = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.035)
save("assets/sfx/pop.wav", pop, 0.8)

# --- whoosh: band-passed noise with swell
t = t_(0.45)
n = rng.standard_normal(len(t))
b, a = butter(2, [600 / (SR / 2), 4000 / (SR / 2)], btype="band")
w = lfilter(b, a, n) * np.sin(np.pi * t / t[-1]) ** 2
save("assets/sfx/whoosh.wav", w, 0.6)

# --- sparkle: quick high bell arpeggio
out = np.zeros(int(0.7 * SR))
for i, fr in enumerate([1568, 2093, 2637, 3136]):
    st = int(i * 0.055 * SR)
    tt = t_(0.5)
    tone = (np.sin(2 * np.pi * fr * tt) + 0.3 * np.sin(2 * np.pi * fr * 2.01 * tt)) * env(len(tt), 0.002, 0.12)
    out[st:st + len(tt)] += tone[: len(out) - st]
save("assets/sfx/sparkle.wav", out, 0.55)

# --- ding: soft marimba-ish double note for CTA
out = np.zeros(int(0.9 * SR))
for i, fr in enumerate([784, 1175]):
    st = int(i * 0.12 * SR)
    tt = t_(0.7)
    tone = (np.sin(2 * np.pi * fr * tt) + 0.25 * np.sin(2 * np.pi * fr * 4 * tt) * np.exp(-tt * 30)) * env(len(tt), 0.002, 0.22)
    out[st:st + len(tt)] += tone[: len(out) - st]
save("assets/sfx/ding.wav", out, 0.7)

# --- boing for character reveals (cute)
t = t_(0.35)
f = 220 + 140 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 6) + 160 * np.exp(-t * 4)
boing = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.003, 0.12)
save("assets/sfx/boing.wav", boing, 0.6)


# --- background music: plucky ukulele-style loop, C G Am F, 112 BPM
def pluck(freq, dur, decay=0.996):
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = decay * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out


BPM = 112
beat = 60 / BPM
bars = 20  # ~43 s
total = int((bars * 4 * beat + 2) * SR)
mix = np.zeros(total)
N = {"C3": 130.81, "E3": 164.81, "G3": 196.0, "A3": 220.0, "B3": 246.94, "C4": 261.63, "D4": 293.66,
     "E4": 329.63, "F3": 174.61, "F4": 349.23, "G4": 392.0, "A4": 440.0, "C5": 523.25, "D5": 587.33, "E5": 659.25,
     "G2": 98.0, "A2": 110.0, "F2": 87.31, "C2": 65.41}
chords = [("C2", ["C4", "E4", "G4"]), ("G2", ["B3", "D4", "G4"]), ("A2", ["A3", "C4", "E4"]), ("F2", ["A3", "C4", "F4"])]
strum = [1, 0, 1, 1, 0, 1, 1, 0]  # 8th-note strum pattern
cache = {}


def get(name, dur, decay=0.996):
    k = (name, dur, decay)
    if k not in cache:
        cache[k] = pluck(N[name], dur, decay)
    return cache[k]


melody = ["E5", "D5", "C5", "G4", "D5", "C5", "A4", "G4", "C5", "A4", "E5", "D5", "C5", "A4", "G4", "A4"]
for bar in range(bars):
    root, ch = chords[bar % 4]
    bs = bar * 4 * beat
    # bass on beats 1 and 3
    for bt in (0, 2):
        s = int((bs + bt * beat) * SR)
        x = get(root, beat * 1.8, 0.998) * 0.9
        mix[s:s + len(x)] += x
    # strum
    for i, on in enumerate(strum):
        if not on:
            continue
        s0 = bs + i * beat / 2
        for j, nm in enumerate(ch):
            s = int((s0 + j * 0.012) * SR)
            x = get(nm, beat * 1.2, 0.994) * 0.35
            mix[s:s + len(x)] += x
    # light melody in bars after intro
    if bar >= 2:
        for k in range(4):
            if (bar + k) % 3 == 2:
                continue
            nm = melody[(bar * 4 + k) % len(melody)]
            s = int((bs + k * beat) * SR)
            x = get(nm, beat * 1.5, 0.997) * 0.28
            mix[s:s + len(x)] += x
    # shaker on off-beats
    for i in range(8):
        s = int((bs + i * beat / 2) * SR)
        ln = int(0.05 * SR)
        nz = rng.standard_normal(ln) * env(ln, 0.002, 0.015) * (0.10 if i % 2 else 0.05)
        b, a = butter(2, 5000 / (SR / 2), btype="high")
        mix[s:s + ln] += lfilter(b, a, nz)

# gentle fade-out
fo = int(2.5 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)
save("assets/music/cheerful_bed.wav", mix, 0.8)
print("done")

# --- diamond: glittery ascending shimmer for the happy title moment (v5)
dur = 1.4
out = np.zeros(int(dur * SR))
notes = [2093, 2637, 3136, 3951, 4186, 5274]
for i, fr in enumerate(notes):
    st = int(i * 0.045 * SR)
    tt = t_(1.1)
    tone = (np.sin(2 * np.pi * fr * tt) + 0.4 * np.sin(2 * np.pi * fr * 2.41 * tt) * np.exp(-tt * 9)) \
        * env(len(tt), 0.002, 0.35) * (0.9 - i * 0.08)
    out[st:st + len(tt)] += tone[: len(out) - st]
# glitter: tiny random high pings
for k in range(26):
    st = int(rng.uniform(0.05, 0.9) * SR)
    fr = rng.uniform(5000, 9000)
    tt = t_(0.08)
    out[st:st + len(tt)] += np.sin(2 * np.pi * fr * tt) * env(len(tt), 0.001, 0.02) * 0.25
# airy swell
n = rng.standard_normal(len(out))
b, a = butter(2, 6000 / (SR / 2), btype="high")
tt = t_(dur)
out += lfilter(b, a, n) * np.sin(np.pi * np.minimum(tt / 0.9, 1)) ** 2 * 0.08
save("assets/sfx/diamond.wav", out, 0.75)

# --- countup: 6 rising blips (1/6 -> 6/6) then a sparkle chime, for the FULL SET finale (v10)
STEP = 0.11
out = np.zeros(int((6 * STEP + 1.1) * SR))
for i, fr in enumerate([784, 880, 988, 1175, 1319, 1568]):
    st = int(i * STEP * SR)
    tt = t_(0.09)
    blip = np.sin(2 * np.pi * fr * tt) * env(len(tt), 0.002, 0.03) * 0.7
    out[st:st + len(tt)] += blip
st = int(6 * STEP * SR)
for k, fr in enumerate([2093, 2637, 3136, 4186]):
    s2 = st + int(k * 0.04 * SR)
    tt = t_(0.9)
    tone = (np.sin(2 * np.pi * fr * tt) + 0.35 * np.sin(2 * np.pi * fr * 2.41 * tt) * np.exp(-tt * 9)) * env(len(tt), 0.002, 0.3)
    out[s2:s2 + len(tt)] += tone[: len(out) - s2] * (0.8 - k * 0.12)
save("assets/sfx/countup.wav", out, 0.7)
