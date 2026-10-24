"""Three sample concepts for Wall's Jolly Jelly Grape & Apple — "Treat to Glow".

Run:  python3 tools/concepts.py [1|2|3 ...]   (default: all)
Output: videos/*.mp4  (720x1280, 30fps)
"""
import math
import random
import sys

from vlib import *  # noqa: F401,F403

PACK = load_pack(560)
PACK_SM = load_pack(380)
SPARK = sparkle_sprite(30)


def sparkles(frame, t, cx, cy, radius, n=10, alpha=1.0, seed=1):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.random() * 6.28 + t * (0.4 + rnd.random())
        r = radius * (0.6 + 0.4 * rnd.random())
        tw = 0.5 + 0.5 * math.sin(t * 7 + i * 1.7)
        paste(frame, SPARK, cx + r * math.cos(a), cy + r * math.sin(a), scale=0.4 + 0.7 * tw, alpha=alpha)


# ============================================================
# 1. BATERI MOOD 5%  (BM, campus)
# ============================================================

def concept1():
    D = 23.0
    bg = campus_bg()
    chars = {m: character(m, shirt=(255, 170, 200), size=440) for m in ("tired", "neutral", "happy", "glow")}
    bar = ice_cream(330)
    bar_bite = ice_cream(330, bite=True)
    caps = [
        Caption("BATERI MOOD AKU LEPAS 3 KELAS PAGI:", 0.2, 3.0, y=170, size=50),
        Caption("Okay. Masa untuk CAS.", 3.1, 6.0, y=180, size=60),
        Caption("Luar: jelly grape CHEWY", 6.2, 8.4, y=180, size=54, fill=PURPLE, stroke=WHITE),
        Caption("Dalam: ais krim apple + nata de coco!", 8.4, 10.2, y=180, size=50, fill=PURPLE, stroke=WHITE),
        Caption("Charging happy...", 10.3, 14.6, y=170, size=58),
        Caption("GLOW MODE: ON", 14.7, 18.0, y=180, size=78, fill=YELLOW, stroke=PURPLE),
    ]
    subs = [
        (0.2, 3.0, "\"Serius... bateri aku tinggal 5%.\""),
        (3.1, 6.0, "\"Aku tak perlukan powerbank. Aku perlukan ni.\""),
        (6.2, 10.2, "\"Dengar tu? Chewy dia lain macam.\""),
        (10.3, 14.6, "\"Okay, okay... mood aku naik balik.\""),
        (14.7, 18.0, "\"Bila happy, memang terus glow.\""),
    ]

    def battery(frame, t, level, cx=W / 2, cy=440, sc=1.0):
        d = ImageDraw.Draw(frame)
        bw, bh = 300 * sc, 140 * sc
        x0, y0 = cx - bw / 2, cy - bh / 2
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], int(24 * sc), fill=(255, 255, 255, 230), outline=(40, 30, 50), width=int(8 * sc))
        d.rounded_rectangle([x0 + bw, cy - 26 * sc, x0 + bw + 22 * sc, cy + 26 * sc], int(8 * sc), fill=(40, 30, 50))
        col = RED if level < 0.2 else (mix(YELLOW, APPLE, (level - 0.2) / 0.5) if level < 0.7 else APPLE)
        if level < 0.2 and int(t * 4) % 2 == 0:
            col = (255, 120, 120)
        inner = (bw - 30 * sc) * max(0.04, level)
        d.rounded_rectangle([x0 + 15 * sc, y0 + 15 * sc, x0 + 15 * sc + inner, y0 + bh - 15 * sc], int(14 * sc), fill=col)
        pct = text_sprite(f"{int(round(level * 100))}%", size=int(60 * sc), fill=WHITE, stroke=(40, 30, 50))
        paste(frame, pct, cx, cy)

    def draw(t):
        f = bg.copy()
        dx, dy = shake(t, 0.3, 0.6, 16)
        # mood level timeline
        if t < 10.3:
            level = 0.05
        else:
            level = lerp(0.05, 1.0, ease_in_out(prog(t, 10.3, 4.0)))
        mood = "tired" if t < 6.0 else ("neutral" if t < 11.5 else ("happy" if t < 14.7 else "glow"))
        if t >= 14.7:
            paste(f, glow_sprite(360), W / 2, 830, scale=1 + 0.05 * math.sin(t * 5), alpha=prog(t, 14.7, 0.4))
        bob = 6 * math.sin(t * (2 if mood == "tired" else 5))
        paste(f, chars[mood], W / 2 + dx, 870 + bob + dy)
        if t < 10.3 or t >= 10.3:
            if t < 6.2 or t >= 10.3:
                battery(f, t, level, cy=430 if t < 14.7 else 420, sc=1.0 if t < 14.7 else 0.8)
        # 3-6: pack slides up into hand
        if 3.1 <= t < 6.2:
            p = back_out(prog(t, 3.3, 0.6))
            paste(f, PACK_SM, W / 2 + 190, lerp(1500, 880, p), rot=-12 + 4 * math.sin(t * 6))
        # 6-10: macro product moment
        if 6.2 <= t < 10.3:
            p = ease_out(prog(t, 6.2, 0.4))
            ov = vgradient(W, H, (240, 220, 255), (200, 160, 240))
            ov.putalpha(int(235 * p))
            f.alpha_composite(ov)
            sp = bar if t < 7.6 else bar_bite
            sc = lerp(1.2, 1.9, ease_in_out(prog(t, 6.2, 4.0)))
            paste(f, sp, W / 2, 680, scale=sc, rot=-8 + 3 * math.sin(t * 2), alpha=p)
            sparkles(f, t, W / 2, 680, 300, alpha=p)
            if t >= 7.6:
                lab = text_sprite("CHEWY!", size=70, fill=YELLOW, stroke=PURPLE)
                paste(f, lab, W / 2 + 170, 470, scale=back_out(prog(t, 7.6, 0.3)), rot=12)
        if 10.3 <= t < 14.7:
            for k in range(3):
                tk = 10.6 + k * 1.2
                if t >= tk:
                    p = prog(t, tk, 1.0)
                    plus = text_sprite("+HAPPY", size=40, fill=WHITE, stroke=PINK)
                    paste(f, plus, W / 2 + (k - 1) * 200, 600 - 160 * p, alpha=1 - p)
        if t >= 14.7:
            sparkles(f, t, W / 2, 820, 330, n=16)
            paste(f, bar, W / 2 + 200, 900, scale=0.9, rot=-15)
        for c in caps:
            c.draw(f, t)
        for a, b, s in subs:
            if a <= t < b:
                subtitle(f, s)
        tiktok_ui(f, caption="Bateri mood 5% -> 100% #WallsMalaysia #WallsJollyJelly")
        end_card(f, t, 18.0, "Jom ambil happy bite & Treat to Glow!", pack=PACK)
        return f

    events = [(0.3, "record"), (3.3, "whoosh"), (6.2, "whoosh"), (7.6, "crunch"), (7.62, "boing"),
              (10.3, "rise"), (10.6, "pop"), (11.8, "pop"), (13.0, "pop"), (14.7, "chime"), (18.0, "whoosh"), (18.7, "ding")]
    render("videos/01_bateri_mood_5persen.mp4", D, draw, events, bpm=120, key=62, duck=[(0.0, 3.0)])


# ============================================================
# 2. 4 LAPIS, 1 SENYUM  (ENG/BM mix, ASMR texture, lakeside)
# ============================================================

def concept2():
    D = 22.0
    bg = park_bg(5, lake=True)
    shock = character("shock", shirt=(150, 210, 255), hijab=(250, 200, 220), size=440)
    happy = character("happy", shirt=(150, 210, 255), hijab=(250, 200, 220), size=440)
    glow = character("glow", shirt=(150, 210, 255), hijab=(250, 200, 220), size=440)
    cut = ice_cream(560, cutaway=True)
    bar = ice_cream(300)
    layers = [
        ("1", "Jelly grape chewy", (160, 80, 205), (540, 270)),
        ("2", "Apple milk ice", (150, 200, 90), (540, 420)),
        ("3", "Ais krim apple", (230, 200, 120), (540, 560)),
        ("4", "Nata de coco!", (120, 120, 120), (540, 700)),
    ]
    caps = [
        Caption("WAIT... ais krim ni ada 4 LAPIS?!", 0.1, 2.8, y=180, size=58, fill=YELLOW, stroke=PURPLE),
        Caption("Jom kira sama-sama", 2.9, 5.0, y=170, size=56),
        Caption("Satu gigit, 4 lapis happy", 14.0, 17.0, y=180, size=56),
    ]
    subs = [
        (0.1, 2.8, "\"Kejap. Korang tahu tak benda ni ada 4 layer?\""),
        (2.9, 5.0, "\"Okay... jom kira.\""),
        (5.2, 14.0, "(ASMR: bunyi gigit chewy jelly)"),
        (14.0, 17.0, "\"Lepas makan, rasa happy... rasa glow.\""),
    ]

    def draw(t):
        f = bg.copy()
        dx, dy = shake(t, 0.15, 0.5, 18)
        if t < 5.0:
            ch = shock if t < 2.9 else happy
            paste(f, ch, W / 2 + dx, 880 + dy + 5 * math.sin(t * 5))
            if t >= 2.9:
                p = back_out(prog(t, 2.9, 0.5))
                paste(f, PACK, W / 2, lerp(1600, 640, p), scale=lerp(0.6, 0.95, prog(t, 3.0, 2.0)), rot=-6)
                # circle the "4 LAYERS" badge on the pack
                if t >= 3.8:
                    d = ImageDraw.Draw(f)
                    pr = prog(t, 3.8, 0.5)
                    cx, cy, r = W / 2 + 25, 690, 95
                    d.arc([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], 0, int(360 * pr), fill=RED, width=10)
        elif t < 14.0:
            ov = vgradient(W, H, (255, 240, 250), (225, 200, 250))
            f.alpha_composite(ov)
            sc = lerp(1.0, 1.08, prog(t, 5.0, 9.0))
            paste(f, cut, 175, 640, scale=sc, rot=0)
            for i, (num, label, col, (lx, ly)) in enumerate(layers):
                tk = 5.6 + i * 2.0
                if t >= tk:
                    p = back_out(prog(t, tk, 0.35))
                    d = ImageDraw.Draw(f)
                    # leader line from bar to label
                    tx = [275, 245, 230, 245][i]
                    ty = [230 + 60, 420, 560, 680][i]
                    d.line([tx, ty, lerp(tx, lx - 165, p), ly], fill=col, width=6)
                    badge = text_sprite(num, size=54, fill=WHITE, box=col + (255,), pad=14, radius=40)
                    paste(f, badge, lx - 165, ly, scale=p)
                    lab = text_sprite(label, size=34, fill=PURPLE, box=(255, 255, 255, 235), black=True, pad=14, maxw=300)
                    paste(f, lab, lx + 30, ly, scale=p)
            if t >= 13.0:
                caption = text_sprite("4/4  CONFIRM!", size=64, fill=YELLOW, stroke=PURPLE)
                paste(f, caption, W / 2, 1000, scale=back_out(prog(t, 13.0, 0.3)), rot=-5)
            sparkles(f, t, 175, 640, 260, n=8, alpha=0.8)
        else:
            ch = happy if t < 15.5 else glow
            if t >= 15.5:
                paste(f, glow_sprite(360), W / 2, 830, alpha=prog(t, 15.5, 0.4))
                sparkles(f, t, W / 2, 820, 320, n=14)
            paste(f, ch, W / 2, 880 + 6 * math.sin(t * 5))
            paste(f, bar, W / 2 + 190, 920, scale=0.95, rot=-18 + 4 * math.sin(t * 3))
        for c in caps:
            c.draw(f, t)
        for a, b, s in subs:
            if a <= t < b:
                subtitle(f, s)
        tiktok_ui(f, caption="4 lapis = 4x happy #WallsMalaysia #WallsJollyJelly")
        end_card(f, t, 17.0, "Take a happy bite & Treat to Glow!", pack=PACK)
        return f

    events = [(0.15, "record"), (2.9, "whoosh"), (3.8, "pop"), (5.0, "whoosh"), (5.3, "crunch"),
              (5.6, "ding"), (7.6, "ding"), (9.6, "ding"), (11.6, "ding"), (13.0, "boing"),
              (15.5, "chime"), (17.0, "whoosh"), (17.7, "ding")]
    render("videos/02_4lapis_1senyum.mp4", D, draw, events, bpm=104, key=60, duck=[(5.2, 13.0)])


# ============================================================
# 3. RAHSIA GLOWING  (BM comedy POV, two friends at the park)
# ============================================================

def concept3():
    D = 23.0
    bg = park_bg(9)
    me = {m: character(m, shirt=(255, 220, 90), size=360) for m in ("glow", "wink", "happy")}
    fr = {m: character(m, shirt=(170, 230, 190), hijab=(160, 120, 220), size=360) for m in ("shock", "neutral", "happy", "glow")}
    bar = ice_cream(240)
    caps = [
        Caption("POV: kawan kau tanya kenapa muka kau GLOWING", 0.1, 3.2, y=190, size=48),
        Caption("Serum?  BUKAN.", 3.3, 4.6, y=190, size=58),
        Caption("Toner?  BUKAN.", 4.6, 5.9, y=190, size=58),
        Caption("Rahsia aku: HAPPY.", 6.0, 10.0, y=190, size=64, fill=YELLOW, stroke=PURPLE),
        Caption("Bila hati happy, muka pun glow", 10.1, 14.5, y=190, size=52),
        Caption("Eh... aku pun dah glow?!", 14.6, 18.0, y=190, size=56, fill=YELLOW, stroke=PURPLE),
    ]
    subs = [
        (0.1, 3.2, "KAWAN: \"Weh, kau pakai skincare apa? Glowing gila!\""),
        (3.3, 6.0, "AKU: \"Nak tahu rahsia aku?\""),
        (6.0, 10.0, "AKU: \"Ni. Wall's Jolly Jelly. Little treat, big happy.\""),
        (10.1, 14.5, "KAWAN: \"Hmm... chewy dia sedap gila.\""),
        (14.6, 18.0, "KAWAN: \"Okay faham. You happy, you glow!\""),
    ]

    def bottle(label, col):
        im, d, s = ss_canvas(150, 260)
        d.rounded_rectangle([40 * s, 0, 110 * s, 50 * s], 10 * s, fill=(60, 60, 70, 255))
        d.rounded_rectangle([10 * s, 40 * s, 140 * s, 250 * s], 26 * s, fill=col + (255,))
        out = ss_done(im)
        lab = text_sprite(label, size=26, fill=WHITE, stroke=(60, 60, 70), black=True, pad=4)
        out.alpha_composite(lab, ((out.width - lab.width) // 2, 130))
        return out

    serum, toner = bottle("SERUM", (240, 170, 120)), bottle("TONER", (130, 200, 230))

    def cross(frame, cx, cy, p):
        d = ImageDraw.Draw(frame)
        r = 90 * p
        d.line([cx - r, cy - r, cx + r, cy + r], fill=RED, width=18)
        d.line([cx - r, cy + r, cx + r, cy - r], fill=RED, width=18)

    def draw(t):
        f = bg.copy()
        my_mood = "glow" if t < 3.3 else ("wink" if t < 6.0 else ("happy" if t < 10.1 else "glow"))
        fr_mood = "shock" if t < 3.3 else ("neutral" if t < 10.1 else ("happy" if t < 14.6 else "glow"))
        if my_mood == "glow":
            paste(f, glow_sprite(260), 210, 830, alpha=0.9)
            sparkles(f, t, 210, 800, 220, n=8, seed=3)
        if fr_mood == "glow":
            paste(f, glow_sprite(260), 520, 830, alpha=prog(t, 14.6, 0.4))
            sparkles(f, t, 520, 800, 220, n=10, seed=4)
        dx, dy = shake(t, 0.15, 0.5, 12)
        paste(f, me[my_mood], 210, 880 + 5 * math.sin(t * 4))
        paste(f, fr[fr_mood], 520 + dx, 880 + dy + 5 * math.sin(t * 4 + 1))
        if 3.3 <= t < 6.0:
            item, t0 = (serum, 3.3) if t < 4.6 else (toner, 4.6)
            p = back_out(prog(t, t0, 0.3))
            paste(f, item, W / 2, 520, scale=p)
            if t >= t0 + 0.45:
                cross(f, W / 2, 520, ease_out(prog(t, t0 + 0.45, 0.2)))
        if 6.0 <= t < 10.0:
            p = back_out(prog(t, 6.0, 0.5))
            paste(f, glow_sprite(300), W / 2, 560, alpha=prog(t, 6.0, 0.4))
            paste(f, PACK, W / 2, 570, scale=0.8 * p, rot=-8 + 4 * math.sin(t * 3))
            sparkles(f, t, W / 2, 570, 280, n=12)
        if t >= 10.1:
            paste(f, bar, 80, 930, scale=0.9, rot=15 + 3 * math.sin(t * 3))
            paste(f, bar, 655, 930, scale=0.9, rot=-15 + 3 * math.sin(t * 3 + 1))
            if 10.1 <= t < 14.6:
                for k in range(3):
                    tk = 10.5 + k * 1.3
                    if t >= tk:
                        p = prog(t, tk, 1.0)
                        h = text_sprite("chewy~", size=34, fill=WHITE, stroke=GRAPE)
                        paste(f, h, 360 + (k - 1) * 150, 640 - 140 * p, alpha=1 - p)
        for c in caps:
            c.draw(f, t)
        for a, b, s in subs:
            if a <= t < b:
                subtitle(f, s)
        tiktok_ui(f, caption="Rahsia glowing aku #WallsMalaysia #WallsJollyJelly")
        end_card(f, t, 18.0, "Ambil happy bite, Treat to Glow dengan Wall's Jolly Jelly!", pack=PACK)
        return f

    events = [(0.15, "record"), (3.3, "pop"), (3.75, "boing"), (4.6, "pop"), (5.05, "boing"), (6.0, "chime"),
              (10.1, "whoosh"), (10.3, "crunch"), (10.5, "pop"), (11.8, "pop"), (13.1, "pop"), (14.6, "chime"),
              (18.0, "whoosh"), (18.7, "ding")]
    render("videos/03_rahsia_glowing.mp4", D, draw, events, bpm=124, key=64, duck=[(0.0, 3.2)])


if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2", "3"]
    for w_ in which:
        {"1": concept1, "2": concept2, "3": concept3}[w_]()
        print("done", w_)
