"""Tiny frame-based motion-graphics engine for vertical (9:16) animatic videos.

Draws frames with Pillow, synthesises a music bed + SFX with numpy, and muxes
with ffmpeg. Used to render the Wall's Jolly Jelly sample concepts.
"""
import math
import os
import random
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 720, 1280, 30
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
if not os.path.exists(FONT_BLACK):
    FONT_BLACK = FONT_BOLD

PURPLE = (122, 40, 170)
GRAPE = (150, 70, 200)
LILAC = (196, 150, 235)
APPLE = (150, 210, 70)
YELLOW = (255, 214, 60)
PINK = (255, 105, 180)
WHITE = (255, 255, 255)
RED = (220, 30, 50)

_font_cache = {}


def font(size, black=True):
    key = (size, black)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_BLACK if black else FONT_BOLD, size)
    return _font_cache[key]


# ---------- easing / timing helpers ----------

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur) if dur > 0 else float(t >= start)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.9):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def lerp(a, b, x):
    return a + (b - a) * x


def mix(c1, c2, x):
    return tuple(int(lerp(a, b, x)) for a, b in zip(c1, c2))


# ---------- sprite helpers (drawn at 2x then downsampled for anti-aliasing) ----------

def ss_canvas(w, h, s=2):
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im), s


def ss_done(im, s=2):
    return im.resize((im.width // s, im.height // s), Image.LANCZOS)


def paste(dst, sprite, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    """Paste RGBA sprite centred at (cx, cy)."""
    if alpha <= 0 or scale <= 0.01:
        return
    sp = sprite
    if scale != 1.0:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if rot:
        sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = sp.getchannel("A").point(lambda v: int(v * alpha))
        sp = sp.copy()
        sp.putalpha(a)
    dst.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))


def vgradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None]
    arr = (np.array(top)[None, None, :] * (1 - t[..., None]) + np.array(bottom)[None, None, :] * t[..., None])
    arr = np.repeat(arr, w, axis=1).astype("uint8")
    return Image.fromarray(arr, "RGB").convert("RGBA")


def star(draw, cx, cy, r, color, points=4, inner=0.38, rot=0):
    pts = []
    for i in range(points * 2):
        ang = rot + math.pi * i / points
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.sin(ang), cy - rr * math.cos(ang)))
    draw.polygon(pts, fill=color)


def sparkle_sprite(r=40, color=(255, 240, 150)):
    im, d, s = ss_canvas(r * 2 + 4, r * 2 + 4)
    star(d, (r + 2) * s, (r + 2) * s, r * s, color + (255,))
    return ss_done(im)


def glow_sprite(r=300, color=(255, 220, 120)):
    im = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:r * 2, 0:r * 2]
    dist = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = (np.clip(1 - dist, 0, 1) ** 2 * 200).astype("uint8")
    arr = np.zeros((r * 2, r * 2, 4), "uint8")
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = color[0], color[1], color[2], a
    return Image.fromarray(arr, "RGBA")


# ---------- scenery ----------

def park_bg(seed=1, sky=((120, 200, 255), (215, 240, 255)), with_bench=True, lake=False):
    rnd = random.Random(seed)
    bg = vgradient(W, H, *sky)
    im, d, s = ss_canvas(W, H)
    # sun
    d.ellipse([560 * s, 90 * s, 680 * s, 210 * s], fill=(255, 236, 140, 255))
    # clouds
    for cx, cy in [(140, 160), (420, 250), (620, 380)]:
        for dx, dy, r in [(-40, 0, 38), (0, -18, 48), (45, 0, 36)]:
            d.ellipse([(cx + dx - r) * s, (cy + dy - r) * s, (cx + dx + r) * s, (cy + dy + r) * s], fill=(255, 255, 255, 235))
    horizon = 760
    if lake:
        d.rectangle([0, 700 * s, W * s, 800 * s], fill=(110, 175, 230, 255))
        for i in range(10):
            y = rnd.randint(710, 790)
            x = rnd.randint(0, W)
            d.rectangle([x * s, y * s, (x + rnd.randint(30, 90)) * s, (y + 3) * s], fill=(200, 230, 255, 200))
        horizon = 800
    # far trees
    for i in range(9):
        x = i * 90 + rnd.randint(-20, 20)
        r = rnd.randint(55, 85)
        y = (690 if lake else 720) - rnd.randint(0, 30)
        d.rectangle([(x - 8) * s, y * s, (x + 8) * s, (y + 90) * s], fill=(120, 80, 50, 255))
        d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r * 0.8) * s], fill=(70 + rnd.randint(0, 40), 165 + rnd.randint(0, 30), 80, 255))
    # grass
    d.rectangle([0, horizon * s, W * s, H * s], fill=(120, 200, 90, 255))
    d.ellipse([-200 * s, (horizon - 30) * s, (W + 200) * s, (horizon + 120) * s], fill=(130, 210, 95, 255))
    for i in range(70):
        x = rnd.randint(0, W)
        y = rnd.randint(horizon + 40, H)
        c = rnd.choice([(255, 255, 255), (255, 200, 230), (255, 230, 90)])
        d.ellipse([(x - 5) * s, (y - 5) * s, (x + 5) * s, (y + 5) * s], fill=c + (255,))
    if with_bench:
        by = 1010
        d.rounded_rectangle([60 * s, (by - 120) * s, 660 * s, (by - 95) * s], 8 * s, fill=(170, 110, 60, 255))
        d.rounded_rectangle([60 * s, (by - 80) * s, 660 * s, (by - 55) * s], 8 * s, fill=(170, 110, 60, 255))
        d.rounded_rectangle([40 * s, (by - 30) * s, 680 * s, by * s], 8 * s, fill=(190, 125, 70, 255))
        for x in (90, 610):
            d.rectangle([x * s, by * s, (x + 20) * s, (by + 90) * s], fill=(90, 90, 100, 255))
    bg.alpha_composite(ss_done(im))
    return bg


def campus_bg(seed=3):
    bg = park_bg(seed, sky=((255, 190, 220), (255, 235, 200)), with_bench=False)
    im, d, s = ss_canvas(W, H)
    # building
    d.rectangle([60 * s, 430 * s, 660 * s, 760 * s], fill=(245, 235, 225, 255))
    d.polygon([(40 * s, 440 * s), (360 * s, 330 * s), (680 * s, 440 * s)], fill=(200, 90, 90, 255))
    for row in range(3):
        for col in range(6):
            x = 95 + col * 95
            y = 470 + row * 90
            d.rounded_rectangle([x * s, y * s, (x + 55) * s, (y + 60) * s], 6 * s, fill=(130, 190, 240, 255))
    d.rounded_rectangle([320 * s, 660 * s, 400 * s, 760 * s], 10 * s, fill=(150, 90, 60, 255))
    d.rectangle([0, 760 * s, W * s, 800 * s], fill=(210, 200, 190, 255))
    bg.alpha_composite(ss_done(im))
    return bg


# ---------- character ----------

SKIN = (245, 205, 170)
HAIR = (55, 35, 30)


def character(mood="neutral", shirt=(255, 255, 255), hijab=None, size=420, holding=False):
    """Cute chibi character bust. mood: tired|neutral|happy|shock|glow|wink."""
    w, h = size, int(size * 1.35)
    im, d, s = ss_canvas(w, h)
    S = lambda v: v * s * size / 420
    # body
    d.rounded_rectangle([S(90), S(380), S(330), S(600)], S(90), fill=shirt + (255,))
    # neck
    d.rectangle([S(185), S(330), S(235), S(400)], fill=SKIN + (255,))
    if hijab:
        d.ellipse([S(75), S(45), S(345), S(395)], fill=hijab + (255,))
        d.polygon([(S(95), S(260)), (S(325), S(260)), (S(360), S(470)), (S(60), S(470))], fill=hijab + (255,))
    else:
        d.ellipse([S(80), S(40), S(340), S(330)], fill=HAIR + (255,))
        d.rectangle([S(80), S(180), S(340), S(420)], fill=HAIR + (255,))
    # face
    d.ellipse([S(110), S(95), S(310), S(330)], fill=SKIN + (255,))
    if not hijab:
        d.chord([S(100), S(70), S(320), S(230)], 180, 360, fill=HAIR + (255,))
    ey = S(210)
    lx, rx = S(165), S(255)
    ink = (60, 35, 40, 255)
    if mood == "tired":
        for x in (lx, rx):
            d.line([x - S(22), ey + S(4), x + S(22), ey + S(4)], fill=ink, width=int(S(7)))
            d.arc([x - S(22), ey + S(10), x + S(22), ey + S(34)], 200, 340, fill=(150, 120, 160, 255), width=int(S(4)))
        d.arc([S(185), S(270), S(235), S(300)], 200, 340, fill=ink, width=int(S(6)))
        d.ellipse([S(285), S(150), S(300), S(175)], fill=(120, 190, 255, 255))  # sweat drop
    elif mood == "shock":
        for x in (lx, rx):
            d.ellipse([x - S(20), ey - S(24), x + S(20), ey + S(24)], fill=WHITE + (255,), outline=ink, width=int(S(5)))
            d.ellipse([x - S(10), ey - S(10), x + S(10), ey + S(10)], fill=ink)
        d.ellipse([S(192), S(262), S(228), S(305)], fill=(150, 40, 60, 255))
    elif mood == "wink":
        d.ellipse([lx - S(16), ey - S(20), lx + S(16), ey + S(20)], fill=ink)
        d.ellipse([lx - S(6), ey - S(14), lx + S(4), ey - S(4)], fill=WHITE + (255,))
        d.arc([rx - S(22), ey - S(14), rx + S(22), ey + S(18)], 200, 340, fill=ink, width=int(S(7)))
        d.chord([S(175), S(255), S(245), S(310)], 0, 180, fill=(170, 50, 70, 255))
    elif mood in ("happy", "glow"):
        for x in (lx, rx):
            d.arc([x - S(24), ey - S(16), x + S(24), ey + S(22)], 200, 340, fill=ink, width=int(S(8)))
        d.chord([S(170), S(250), S(250), S(315)], 0, 180, fill=(170, 50, 70, 255))
        d.chord([S(185), S(285), S(235), S(318)], 0, 180, fill=(255, 140, 160, 255))
    else:
        for x in (lx, rx):
            d.ellipse([x - S(16), ey - S(20), x + S(16), ey + S(20)], fill=ink)
            d.ellipse([x - S(6), ey - S(14), x + S(4), ey - S(4)], fill=WHITE + (255,))
        d.arc([S(185), S(265), S(235), S(295)], 20, 160, fill=ink, width=int(S(6)))
    if mood in ("happy", "glow", "wink", "shock", "neutral"):
        blush = (255, 120, 150, 150 if mood != "glow" else 220)
        d.ellipse([S(122), S(245), S(165), S(272)], fill=blush)
        d.ellipse([S(255), S(245), S(298), S(272)], fill=blush)
    out = ss_done(im, s)
    if mood == "glow":
        g = glow_sprite(int(size * 0.75), (255, 225, 140))
        base = Image.new("RGBA", out.size, (0, 0, 0, 0))
        paste(base, g, out.width / 2, out.height * 0.4)
        base.alpha_composite(out)
        out = base
    return out


# ---------- product ----------

def ice_cream(size=360, bite=False, cutaway=False):
    """Stylised Jolly Jelly bar: grape jelly coating over apple layers, on a stick."""
    w, h = int(size * 0.55), size
    im, d, s = ss_canvas(w, h)
    S = lambda v: v * s * size / 360
    d.rounded_rectangle([S(80), S(250), S(118), S(355)], S(14), fill=(225, 185, 130, 255))
    d.rounded_rectangle([S(12), S(10), S(186), S(275)], S(60), fill=(160, 80, 205, 255))
    # glossy jelly shine + jelly bits
    d.rounded_rectangle([S(30), S(35), S(55), S(200)], S(14), fill=(220, 180, 255, 200))
    for x, y in [(130, 70), (150, 160), (60, 230), (110, 120)]:
        d.ellipse([S(x - 6), S(y - 6), S(x + 6), S(y + 6)], fill=(235, 210, 255, 220))
    if cutaway:
        # 4-layer cross-section on the right half
        d.pieslice([S(100), S(10), S(186), S(140)], 270, 360, fill=(160, 80, 205, 255))
        d.rectangle([S(100), S(60), S(186), S(265)], fill=(160, 80, 205, 255))
        d.rectangle([S(108), S(68), S(178), S(258)], fill=(205, 240, 160, 255))   # apple milk ice
        d.rectangle([S(118), S(80), S(168), S(246)], fill=(250, 250, 225, 255))   # apple ice cream
        for x, y in [(132, 110), (152, 150), (134, 190), (154, 225)]:              # nata de coco
            d.rounded_rectangle([S(x - 9), S(y - 9), S(x + 9), S(y + 9)], S(3), fill=(255, 255, 255, 255), outline=(220, 220, 220, 255))
    if bite:
        # clean bite mark at the top-right corner (fresh bite, not half-eaten)
        for cx, cy, r in [(170, 30, 30), (140, 12, 26), (186, 70, 24)]:
            d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=(0, 0, 0, 0))
        for cx, cy, r in [(158, 46, 14), (176, 62, 10)]:
            d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=(215, 245, 165, 255))
    return ss_done(im, s)


def load_pack(height=520):
    p = Image.open(os.path.join(ASSETS, "pack.png")).convert("RGBA")
    return p.resize((int(p.width * height / p.height), height), Image.LANCZOS)


# ---------- text ----------

def text_sprite(txt, size=64, fill=WHITE, stroke=PURPLE, stroke_w=None, box=None, maxw=640, pad=26, radius=28, black=True):
    f = font(size, black)
    sw = stroke_w if stroke_w is not None else max(3, size // 12)
    lines = wrap(txt, f, maxw - 2 * pad)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lh = int(size * 1.18)
    widths = [tmp.textlength(l, font=f) for l in lines]
    tw = int(max(widths)) + 2 * pad + 2 * sw
    th = lh * len(lines) + 2 * pad
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if box:
        d.rounded_rectangle([0, 0, tw - 1, th - 1], radius, fill=box)
    for i, l in enumerate(lines):
        x = (tw - widths[i]) / 2
        y = pad + i * lh
        d.text((x, y), l, font=f, fill=fill, stroke_width=0 if box else sw, stroke_fill=stroke)
    return im


def wrap(txt, f, maxw):
    out = []
    for para in txt.split("\n"):
        words, cur = para.split(" "), ""
        for w_ in words:
            test = (cur + " " + w_).strip()
            if ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(test, font=f) <= maxw or not cur:
                cur = test
            else:
                out.append(cur)
                cur = w_
        out.append(cur)
    return out


class Caption:
    """Pop-in caption shown between t0 and t1."""

    def __init__(self, txt, t0, t1, y=230, size=64, **kw):
        self.sp = text_sprite(txt, size=size, **kw)
        self.t0, self.t1, self.y = t0, t1, y

    def draw(self, frame, t):
        if not (self.t0 <= t <= self.t1):
            return
        p = prog(t, self.t0, 0.28)
        out = prog(t, self.t1 - 0.18, 0.18)
        sc = back_out(p) * (1 - 0.3 * out)
        paste(frame, self.sp, W / 2, self.y, scale=max(0.01, sc), alpha=1 - out)


def subtitle(frame, txt, y=1110):
    sp = text_sprite(txt, size=36, fill=WHITE, box=(0, 0, 0, 150), black=False, pad=16, radius=18, maxw=660)
    paste(frame, sp, W / 2, y)


def tiktok_ui(frame, handle="@kau.punya.handle", caption="Treat to Glow ✨ #WallsMalaysia #WallsJollyJelly"):
    """Light TikTok-style chrome so the mockup reads as a real post."""
    d = ImageDraw.Draw(frame)
    f1, f2 = font(26, False), font(22, False)
    d.text((24, 1180), handle, font=f1, fill=WHITE, stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((24, 1218), caption.replace("✨", "").strip(), font=f2, fill=WHITE, stroke_width=2, stroke_fill=(0, 0, 0))
    for i, y in enumerate((760, 860, 960)):
        d.ellipse([650, y, 700, y + 50], fill=(255, 255, 255, 90))
    d.text((W / 2 - 60, 40), "For You", font=f1, fill=WHITE, stroke_width=2, stroke_fill=(0, 0, 0))


def end_card(frame, t, t0, cta, tagline="Treat to Glow — You happy, you glow!", pack=None):
    p = prog(t, t0, 0.6)
    if p <= 0:
        return
    overlay = vgradient(W, H, (150, 60, 210), (255, 120, 190))
    overlay.putalpha(int(235 * ease_out(p)))
    frame.alpha_composite(overlay)
    glow = glow_sprite(330, (255, 230, 150))
    paste(frame, glow, W / 2, 620, scale=1 + 0.05 * math.sin(t * 4), alpha=p)
    if pack is not None:
        paste(frame, pack, W / 2, 640 + 10 * math.sin(t * 3), scale=back_out(prog(t, t0 + 0.1, 0.5)) * 0.95, rot=-6 + 3 * math.sin(t * 2))
    sp = sparkle_sprite(26)
    rnd = random.Random(7)
    for i in range(14):
        a = rnd.random() * 6.28 + t * 0.6
        r = 250 + rnd.random() * 60
        tw = 0.5 + 0.5 * math.sin(t * 6 + i)
        paste(frame, sp, W / 2 + r * math.cos(a), 640 + r * 1.15 * math.sin(a), scale=0.5 + 0.6 * tw, alpha=p)
    title = text_sprite(tagline, size=50, fill=WHITE, stroke=PURPLE)
    paste(frame, title, W / 2, 230, scale=back_out(prog(t, t0 + 0.3, 0.4)))
    cta_sp = text_sprite(cta, size=40, fill=PURPLE, box=(255, 236, 90, 255), black=True, pad=22)
    paste(frame, cta_sp, W / 2, 1010, scale=back_out(prog(t, t0 + 0.7, 0.4)) * (1 + 0.03 * math.sin(t * 8)))
    tags = text_sprite("#WallsMalaysia  #WallsJollyJelly", size=28, fill=WHITE, stroke=PURPLE, black=False)
    paste(frame, tags, W / 2, 1120, alpha=prog(t, t0 + 1.0, 0.4))


def shake(t, t0, dur=0.35, amp=14):
    p = prog(t, t0, dur)
    if p <= 0 or p >= 1:
        return 0, 0
    a = amp * (1 - p)
    return a * math.sin(t * 90), a * math.cos(t * 70)


# ---------- audio ----------

def note_freq(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def music_bed(duration, bpm=118, seed=0, key=60):
    """Bright pop loop: I-V-vi-IV pads, plucky arp, kick + clap + hats."""
    n = int(duration * SR)
    out = np.zeros(n)
    beat = 60 / bpm
    prog_ = [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]]
    t_all = np.arange(n) / SR
    bar = beat * 4
    for b in range(int(duration / bar) + 1):
        chord = prog_[b % 4]
        t0 = b * bar
        i0, i1 = int(t0 * SR), min(n, int((t0 + bar) * SR))
        if i0 >= n:
            break
        tt = t_all[i0:i1] - t0
        env = np.minimum(1, tt * 8) * np.exp(-tt * 0.4)
        for c in chord:
            f = note_freq(key + c - 12)
            out[i0:i1] += 0.05 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt))
        # arp, 8th notes
        for k in range(8):
            ts = t0 + k * beat / 2
            j0 = int(ts * SR)
            if j0 >= n:
                break
            j1 = min(n, j0 + int(0.25 * SR))
            tt2 = np.arange(j1 - j0) / SR
            f = note_freq(key + 12 + chord[k % 3] + (12 if k in (3, 7) else 0))
            out[j0:j1] += 0.07 * np.exp(-tt2 * 14) * np.sign(np.sin(2 * np.pi * f * tt2)) * 0.6
    rng = np.random.default_rng(seed)
    for k in range(int(duration / beat) + 1):
        ts = k * beat
        j0 = int(ts * SR)
        if j0 >= n:
            break
        j1 = min(n, j0 + int(0.3 * SR))
        tt = np.arange(j1 - j0) / SR
        out[j0:j1] += 0.5 * np.sin(2 * np.pi * (50 + 110 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
        if k % 2 == 1:
            j1c = min(n, j0 + int(0.15 * SR))
            tt = np.arange(j1c - j0) / SR
            out[j0:j1c] += 0.18 * rng.standard_normal(j1c - j0) * np.exp(-tt * 30)
        h0 = int((ts + beat / 2) * SR)
        if h0 < n:
            h1 = min(n, h0 + int(0.04 * SR))
            out[h0:h1] += 0.06 * rng.standard_normal(h1 - h0) * np.linspace(1, 0, h1 - h0)
    return out


def sfx(kind, dur=None):
    rng = np.random.default_rng(1)
    if kind == "pop":
        d = 0.12
        t = np.arange(int(d * SR)) / SR
        return 0.5 * np.sin(2 * np.pi * (300 + 900 * t / d) * t) * np.exp(-t * 35)
    if kind == "whoosh":
        d = dur or 0.45
        t = np.arange(int(d * SR)) / SR
        nz = rng.standard_normal(len(t))
        nz = np.convolve(nz, np.ones(18) / 18, mode="same")
        return 0.9 * nz * np.sin(np.pi * t / d) ** 2
    if kind == "chime":
        d = 1.2
        t = np.arange(int(d * SR)) / SR
        s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in [(1568, 3), (2093, 4), (2637, 5), (3136, 6)])
        return 0.12 * s
    if kind == "crunch":
        d = 0.35
        t = np.arange(int(d * SR)) / SR
        nz = rng.standard_normal(len(t))
        bursts = (np.sin(2 * np.pi * 28 * t) > 0.3).astype(float)
        return 0.45 * nz * bursts * np.exp(-t * 7)
    if kind == "boing":
        d = 0.5
        t = np.arange(int(d * SR)) / SR
        f = 180 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
        return 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    if kind == "record":
        d = 0.6
        t = np.arange(int(d * SR)) / SR
        f = 900 * np.exp(-t * 5)
        return 0.3 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 3)
    if kind == "ding":
        d = 0.8
        t = np.arange(int(d * SR)) / SR
        return 0.3 * (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 6)
    if kind == "rise":
        d = dur or 1.5
        t = np.arange(int(d * SR)) / SR
        f = 200 + 900 * (t / d) ** 2
        return 0.12 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d)
    raise ValueError(kind)


def build_audio(path, duration, events, bpm=118, key=60, duck=None):
    bed = music_bed(duration, bpm=bpm, key=key)
    if duck:
        # duck the music in [a, b) windows (e.g. a record-scratch pause)
        for a, b in duck:
            i0, i1 = int(a * SR), int(b * SR)
            bed[i0:i1] *= 0.12
    mixbuf = bed * 0.8
    for t0, kind in events:
        s = sfx(kind)
        i0 = int(t0 * SR)
        i1 = min(len(mixbuf), i0 + len(s))
        mixbuf[i0:i1] += s[: i1 - i0]
    fade = int(0.8 * SR)
    mixbuf[-fade:] *= np.linspace(1, 0, fade)
    mixbuf = np.tanh(mixbuf * 1.2) * 0.85
    pcm = (mixbuf * 32767).astype("<i2")
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


# ---------- render ----------

def render(out_path, duration, draw_fn, audio_events, bpm=118, key=60, duck=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wav = out_path + ".wav"
    build_audio(wav, duration, audio_events, bpm=bpm, key=key, duck=duck)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nframes = int(duration * FPS)
    for i in range(nframes):
        t = i / FPS
        frame = draw_fn(t)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    return out_path
