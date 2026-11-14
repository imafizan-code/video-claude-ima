"""Synthesise the soundtrack: cheerful ukulele/glockenspiel music + SFX from out/sfx.json.
Usage: python3 render/make_audio.py out/sfx.json out/audio.wav [duration]"""
import json, sys, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(7)
sfx_path, out_path = sys.argv[1], sys.argv[2]
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 106.0
N = int(SR * DUR)
music = np.zeros((N, 2))
fx = np.zeros((N, 2))


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, t, sig, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    j = min(len(buf), i + len(sig))
    s = sig[: j - i] * gain
    buf[i:j, 0] += s * np.sqrt(0.5 * (1 - pan))
    buf[i:j, 1] += s * np.sqrt(0.5 * (1 + pan))


def pluck(freq, dur=1.2, bright=0.5):
    n = int(SR * dur)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for k in range(n):
        out[k] = buf[k % p]
        buf[k % p] = (1 - bright * 0.02) * 0.5 * (buf[k % p] + buf[(k + 1) % p])
    return out * np.exp(-np.linspace(0, 3.5, n))


_pluck_cache = {}


def pluck_c(m, dur=1.2):
    if m not in _pluck_cache:
        _pluck_cache[m] = pluck(mtof(m), dur)
    return _pluck_cache[m]


def bell(freq, dur=1.6):
    t = np.arange(int(SR * dur)) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
         + 0.2 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 10))
    return s * np.exp(-t * 3.2) * np.minimum(1, t * 400)


def sine(freq, dur, decay=4.0):
    t = np.arange(int(SR * dur)) / SR
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * decay) * np.minimum(1, t * 300)


def noise(dur, decay=20.0):
    t = np.arange(int(SR * dur)) / SR
    return rng.uniform(-1, 1, len(t)) * np.exp(-t * decay)


def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


# ---------------- music ----------------
BPM = 112
beat = 60 / BPM
bar = beat * 4
chords = [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]]  # C G Am F
roots = [36, 43, 45, 41]
scale = [72, 74, 76, 79, 81, 84]
music_end = DUR - 1.0
nbars = int(music_end / bar) + 1
for b in range(nbars):
    t0 = b * bar
    if t0 > music_end:
        break
    ch = chords[b % 4]
    # strum pattern: D . D U . U D U
    for k, (pos, up) in enumerate([(0, 0), (1, 0), (1.5, 1), (2.5, 1), (3, 0), (3.5, 1)]):
        tt = t0 + pos * beat
        notes = ch[::-1] if up else ch
        for n_i, m in enumerate(notes):
            add(music, tt + n_i * 0.012, pluck_c(m), pan=-0.3 + n_i * 0.12, gain=0.10 if not up else 0.07)
    # bass
    add(music, t0, sine(mtof(roots[b % 4]), bar * 0.9, 1.5), gain=0.28)
    add(music, t0 + 2 * beat, sine(mtof(roots[b % 4] + 7), bar * 0.45, 3), gain=0.18)
    # glockenspiel melody (sparse, deterministic)
    if b >= 2:
        for k in range(8):
            if (b * 7 + k * 3) % 5 < 2:
                m = scale[(b * 3 + k * 2) % len(scale)]
                if m % 12 in [c % 12 for c in ch] or k % 2 == 0:
                    add(music, t0 + k * beat / 2, bell(mtof(m), 1.2), pan=0.3, gain=0.07)
    # shaker on off-beats
    for k in range(4):
        add(music, t0 + (k + 0.5) * beat, noise(0.06, 60) * 0.5, pan=0.4, gain=0.05)
    # soft kick
    for k in (0, 2):
        tt = np.arange(int(SR * 0.25)) / SR
        kick = np.sin(2 * np.pi * (50 + 80 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14)
        add(music, t0 + k * beat, kick, gain=0.25)

# fade in/out
env = np.ones(N)
fi = int(SR * 1.0); env[:fi] = np.linspace(0, 1, fi)
fo0, fo1 = int(SR * (DUR - 4.0)), int(SR * (DUR - 0.6))
env[fo0:fo1] = np.linspace(1, 0, fo1 - fo0); env[fo1:] = 0
music *= env[:, None]

# ---------------- sfx ----------------
cues = json.load(open(sfx_path))
for c in cues:
    t, k = c['t'], c['type']
    if k == 'whoosh':
        n = noise(0.6, 0)
        sw = np.sin(np.linspace(0, np.pi, len(n))) ** 2
        add(fx, t, lowpass(n, 0.08) * sw * 3.5, gain=0.35)
    elif k == 'shutter':
        add(fx, t, noise(0.03, 120), gain=0.6)
        add(fx, t + 0.07, noise(0.04, 90), gain=0.45)
        tt = np.arange(int(SR * 0.35)) / SR
        whine = np.sin(2 * np.pi * (2000 + 3000 * tt) * tt) * np.exp(-tt * 9) * 0.08
        add(fx, t + 0.02, whine, gain=0.5)
    elif k == 'pop':
        tt = np.arange(int(SR * 0.12)) / SR
        add(fx, t, np.sin(2 * np.pi * (300 + 900 * tt / 0.12) * tt) * np.exp(-tt * 30), gain=0.35)
    elif k == 'tap':
        add(fx, t, sine(1400, 0.06, 80), gain=0.35); add(fx, t, noise(0.02, 200), gain=0.15)
    elif k == 'ding':
        add(fx, t, bell(mtof(84), 1.5), gain=0.35); add(fx, t + 0.12, bell(mtof(88), 1.5), gain=0.3)
    elif k == 'tada':
        for i, m in enumerate([72, 76, 79, 84]):
            add(fx, t + i * 0.09, bell(mtof(m), 1.4), gain=0.25)
    elif k == 'chime':
        for i, m in enumerate([79, 84, 88, 91, 96]):
            add(fx, t + i * 0.12, bell(mtof(m), 2.2), pan=-0.4 + i * 0.2, gain=0.22)
    elif k == 'check':
        add(fx, t, sine(mtof(86), 0.25, 12), gain=0.25); add(fx, t + 0.06, sine(mtof(91), 0.3, 10), gain=0.25)
    elif k == 'notify':
        add(fx, t, bell(mtof(83), 0.8), gain=0.3); add(fx, t + 0.15, bell(mtof(88), 0.9), gain=0.3)
    elif k == 'print':
        tt = np.arange(int(SR * 0.85)) / SR
        motor = (np.sign(np.sin(2 * np.pi * 95 * tt)) * 0.3 + rng.uniform(-1, 1, len(tt)) * 0.4)
        motor = lowpass(motor, 0.15) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * tt) ** 2) * np.minimum(1, tt * 20) * np.minimum(1, (0.85 - tt) * 20)
        add(fx, t, motor, gain=0.35)

# ---------------- voiceover (optional 4th arg: vo/lines.json) ----------------
vo = np.zeros((N, 2))
if len(sys.argv) > 4:
    import subprocess, os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for l in json.load(open(sys.argv[4])):
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", os.path.join(root, l["file"]), "-af", "highpass=f=90,equalizer=f=220:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.2:g=1.5,aecho=0.85:0.5:35|60:0.10|0.06", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
        sig = np.frombuffer(raw, dtype=np.float32).astype(float)
        sig = sig / (np.max(np.abs(sig)) + 1e-9)
        add(vo, l["t"], sig, gain=1.25)
    # duck music under speech
    act = np.abs(vo[:, 0]) > 0.02
    env = np.convolve(act.astype(float), np.ones(int(SR * 0.25)) / int(SR * 0.25), mode="same")
    env = np.clip(env * 4, 0, 1)
    music *= (1 - 0.6 * env)[:, None]

mix = music * 0.9 + fx * 0.8 + vo
peak = np.max(np.abs(mix))
mix = np.tanh(mix / peak * 1.2) * 0.85
data = (mix * 32767).astype('<i2')
with wave.open(out_path, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('wrote', out_path, f'{DUR}s')
