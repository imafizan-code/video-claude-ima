"""Self-made (royalty-free) upbeat background track, ducked under the voiceover.

usage: python3 bgm.py <voice.wav> <out.wav> <duration_s>
"""
import sys, wave, numpy as np
from scipy.signal import butter, sosfilt

voice_path, out_path, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
SR = 48000
BPM = 112
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int(DUR * SR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def add(buf, sig, t0):
    o = int(t0 * SR)
    if o >= len(buf):
        return
    e = min(len(buf), o + len(sig))
    buf[o:e] += sig[: e - o]


def env(n, att, dec):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(att, 1e-4)) * np.exp(-t / dec)


def saw(f, n):
    ph = (np.arange(n) * f / SR) % 1.0
    return 2 * ph - 1


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---- instruments -------------------------------------------------------
def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.12)


def clap():
    n = int(0.25 * SR)
    x = bp(rng.standard_normal(n), 900, 5000)
    e = np.zeros(n)
    for d in (0, 0.011, 0.022):  # three quick bursts = hand clap
        o = int(d * SR); e[o:] += np.exp(-np.arange(n - o) / SR / 0.012) * 0.6
    e += env(n, 0.001, 0.06) * 0.5
    return x * e


def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    return hp(rng.standard_normal(n), 7000) * env(n, 0.0005, 0.06 if open_ else 0.012)


def pluck(freqs, dur=0.35):
    n = int(dur * SR)
    y = sum(saw(f, n) + 0.5 * saw(f * 1.004, n) for f in freqs) / len(freqs)
    y = lp(y, 2600) * env(n, 0.003, 0.11)
    return y


def bass(f, dur):
    n = int(dur * SR)
    y = np.sin(2 * np.pi * f * np.arange(n) / SR) + 0.35 * lp(saw(f, n), 600)
    return y * env(n, 0.004, dur * 0.7)


def bell(f, dur=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / 0.08)
    return y * env(n, 0.002, 0.22)


# ---- arrangement -------------------------------------------------------
# C - G - Am - F (one bar each), bright and friendly
PROG = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
drums = np.zeros(N); bassl = np.zeros(N); keys = np.zeros(N); bells = np.zeros(N)
nbars = int(np.ceil(DUR / BAR)) + 1
for b in range(nbars):
    t0 = b * BAR
    root, chord = PROG[b % 4]
    for beat in range(4):
        tb = t0 + beat * BEAT
        add(drums, kick() * 0.9, tb)                         # four-on-the-floor, light
        if beat in (1, 3):
            add(drums, clap() * 0.55, tb)
        for half in (0, 1):                                  # swung 8th hats, open on the off-beat
            th = tb + half * BEAT * 0.56
            add(drums, hat(open_=(half == 1 and beat == 3)) * (0.22 if half == 0 else 0.3), th)
        # bass: root on the beat, octave pop on the "and"
        add(bassl, bass(midi(root), BEAT * 0.5) * 0.8, tb)
        add(bassl, bass(midi(root + 12), BEAT * 0.3) * 0.45, tb + BEAT * 0.56)
        # off-beat chord stabs
        add(keys, pluck([midi(m) for m in chord]) * 0.55, tb + BEAT * 0.56)
    # sparse bell motif every other bar (kept quiet; fills gaps rather than fighting speech)
    if b % 2 == 1:
        for i, m in enumerate([chord[2] + 12, chord[1] + 12, chord[0] + 12]):
            add(bells, bell(midi(m)) * 0.25, t0 + 2 * BEAT + i * BEAT * 0.5)

# carve space for the voice: dip the 1-4 kHz band in the musical parts
keys = keys - 0.55 * bp(keys, 1000, 4000)
bells = bells - 0.4 * bp(bells, 1000, 4000)
mix = 0.75 * drums + 0.9 * bassl + 0.7 * keys + 0.6 * bells
mix = hp(mix, 35)

# gentle intro swell and a clean ending (last chord rings, then fade)
fade_in = np.clip(t_all / 0.6, 0, 1)
fade_out = np.clip((DUR - t_all) / 1.2, 0, 1)
mix *= fade_in * fade_out

# ---- sidechain ducking from the actual voice ------------------------------
w = wave.open(voice_path)
v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
if w.getnchannels() == 2:
    v = v.reshape(-1, 2).mean(1)
v = np.pad(v, (0, max(0, N - len(v))))[:N]
hop = int(0.01 * SR)
rms = np.sqrt(np.convolve(v ** 2, np.ones(hop * 3) / (hop * 3), mode="same"))
talk = np.clip((20 * np.log10(rms + 1e-9) + 45) / 20, 0, 1)   # 0 = silence (-45 dB), 1 = speech (-25 dB)
# attack 30 ms, release 350 ms follower
g = np.zeros(N); a_att = np.exp(-1 / (0.03 * SR)); a_rel = np.exp(-1 / (0.35 * SR)); s = 0.0
step = 48
for i in range(0, N, step):
    x = talk[i]
    s = a_att * s + (1 - a_att) * x if x > s else a_rel ** step * s + (1 - a_rel ** step) * x
    g[i:i + step] = s
duck_db = -12.0 * g                                            # up to 12 dB lower while she talks
mix *= 10 ** (duck_db / 20)

# level: music RMS about -33.5 dBFS overall (voice sits around -17)
target = 10 ** (-33.5 / 20)
mix *= target / (np.sqrt(np.mean(mix ** 2)) + 1e-9)
pk = np.max(np.abs(mix))
if pk > 0.5:
    mix *= 0.5 / pk
st = np.stack([mix, mix], 1)
with wave.open(out_path, "wb") as o:
    o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
print("bgm rms dBFS", round(20 * np.log10(np.sqrt(np.mean(mix ** 2))), 1), "peak", round(20 * np.log10(np.max(np.abs(mix))), 1))
