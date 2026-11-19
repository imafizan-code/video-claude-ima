"""Build index.html (HyperFrames composition) from the edit decision list below.

Run:  python3 scripts/build.py
Everything is static + deterministic. Edit the EDL / OVERLAYS and rebuild.
"""
import json

W, H = 1080, 1920
# Safe zone: 220 top, 480 bottom, 120 left/right  ->  x 120..960, y 220..1440

# ---- Edit decision list: (clip, start_in_film, duration, media_start, muted)
EDL = [
    ("IMG_1544", 1.5, 0.0, False),   # hook: Choco Chipster close-up
    ("IMG_1586", 1.5, 0.4, False),   # hook: full set cards
    ("IMG_1536", 3.0, 2.2, False),   # pull blind box from case
    ("IMG_1558", 1.4, 0.3, False),   # box front
    ("IMG_1529", 1.5, 0.6, False),   # cards inside
    ("IMG_1532", 2.8, 0.1, False),   # foil crinkle (ASMR peak)
    ("IMG_1551", 1.8, 0.3, False),   # mini desk in plastic
    ("IMG_1553", 2.4, 0.4, False),   # sticker sheet peel
    ("IMG_1556", 1.6, 0.1, False),   # tiny laptop DUE TODAY
    ("IMG_1590", 1.5, 0.8, True),    # tiny detail  (MUTED as requested)
    ("IMG_1560", 2.2, 0.3, False),   # Choco Chipster at desk
    ("IMG_1568", 2.4, 1.5, False),   # Blue Buddy
    ("IMG_1576", 2.4, 0.9, False),   # Pinky Boo
    ("IMG_1578", 2.3, 0.6, False),   # Bean Boss
    ("IMG_1580", 2.2, 0.2, False),   # Porta Pal
    ("IMG_1583", 2.8, 1.6, False),   # Frappe Fren
    ("IMG_1581", 6.7, 0.0, False),   # end card bg
]

t = 0.0
CLIPS = []
for name, dur, ms, muted in EDL:
    CLIPS.append(dict(name=name, start=round(t, 3), dur=dur, ms=ms, muted=muted))
    t += dur
TOTAL = round(t, 3)
S = {c["name"]: c["start"] for c in CLIPS}

NAVY = "#1B2B8F"
YEL = "#FFD84D"

# ---- Overlays: (id, start, end, html, css-position)
# headline = big rounded white text with yellow highlight (Jolly Jelly style, ZUS palette)
OVER = []


def headline(i, st, en, lines, top, size=104):
    inner = "".join(f'<div class="hl-line">{ln}</div>' for ln in lines)
    OVER.append((i, st, en, f'<div class="hl" style="font-size:{size}px">{inner}</div>', f"top:{top}px"))


def pill(i, st, en, html, top, cls="pill"):
    OVER.append((i, st, en, f'<div class="{cls}">{html}</div>', f"top:{top}px"))


# Hook (0-3s)
headline("o-hook", 0.08, 2.95, ['Dapat <span class="y">FREE</span>', '1 full set', '<span class="y">ZUS Buddy</span>?!'], 290, 118)
pill("o-hook2", 1.2, 2.95, '6 buddy, <b>1 set!</b>', 1140)
# Unboxing beats
headline("o-asmr", S["IMG_1536"] + 0.15, S["IMG_1558"] - 0.05, ['ASMR', '<span class="y">unboxing</span> time'], 290, 100)
pill("o-box", S["IMG_1558"] + 0.1, S["IMG_1529"] - 0.05, 'blind box <b>comel</b>', 1140)
pill("o-card", S["IMG_1529"] + 0.1, S["IMG_1532"] - 0.05, 'siap ada <b>kad koleksi</b>', 1140)
OVER.append(("o-krsk", S["IMG_1532"] + 0.2, S["IMG_1551"] - 0.05,
             '<div class="onoma"><span>krsk</span><span>krsk</span><span>krsk~</span></div>', "top:300px"))
pill("o-desk", S["IMG_1551"] + 0.1, S["IMG_1553"] - 0.05, 'meja mini dia <b>pun ada!</b>', 1140)
headline("o-stick", S["IMG_1553"] + 0.15, S["IMG_1556"] - 0.05, ['stiker pun', '<span class="y">dapat!</span>'], 290, 100)
headline("o-due", S["IMG_1556"] + 0.1, S["IMG_1590"] - 0.05, ['"DUE TODAY"', '<span class="y">relate sangat</span>'], 290, 96)
pill("o-detail", S["IMG_1590"] + 0.1, S["IMG_1560"] - 0.05, 'detail <b>comel!</b>', 1140)
# Character reveals
headline("o-who", S["IMG_1560"] + 0.05, S["IMG_1568"] - 0.05, ['Siapa', '<span class="y">buddy</span> korang?'], 290, 100)
for clip, nm in [("IMG_1560", "Choco<br>Chipster"), ("IMG_1568", "Blue<br>Buddy"), ("IMG_1576", "Pinky<br>Boo"),
                 ("IMG_1578", "Bean<br>Boss"), ("IMG_1580", "Porta<br>Pal"), ("IMG_1583", "Frappe<br>Fren")]:
    c = next(x for x in CLIPS if x["name"] == clip)
    OVER.append((f"o-name-{clip}", c["start"] + 0.25, c["start"] + c["dur"] - 0.05,
                 f'<div class="nametag">{nm}</div>', "top:1040px"))
headline("o-relate", S["IMG_1580"] + 0.05, S["IMG_1583"] - 0.05, ['mood hari', '<span class="y">Isnin</span>'], 290, 100)
headline("o-frap", S["IMG_1583"] + 0.05, S["IMG_1581"] - 0.05, ['last but', '<span class="y">not least</span>'], 290, 100)

# End card
e0 = S["IMG_1581"]
END_HTML = f"""
<div class="endcard">
  <div class="ec-top">ZUS APP EXCLUSIVE</div>
  <div class="ec-title">FREE (1) Full Set of</div>
  <div class="ec-sub">ZUS BUDDY Work in Progress</div>
  <div class="ec-small">with purchase of any handcrafted drink*</div>
  <div class="ec-dates"><span>18 NOV, 3PM<br><i>East Malaysia</i></span><em></em><span>19 NOV, 3PM<br><i>West Malaysia</i></span></div>
</div>
"""
OVER.append(("o-end", e0 + 0.1, TOTAL, END_HTML, "top:300px"))
OVER.append(("o-endcta", e0 + 1.0, TOTAL, '<div class="pill pill-navy">Cepat, <b>stok terhad!</b></div>', "top:1090px;left:120px;width:660px"))
# 'Cepat, <b>stok terhad!</b>', 1090, "pill pill-navy")
OVER.append(("o-tnc", e0 + 1.0, TOTAL, '<div class="tnc">*6 karakter setiap box. Tertakluk pada<br>outlet, sementara stok ada. T&amp;C apply.</div>', "top:1190px;left:120px;width:660px"))

# ---- Doodles (twinkling sparkles / hearts), positions inside safe zone
SPARK = '<svg viewBox="0 0 40 40"><path d="M20 2 C22 15 25 18 38 20 C25 22 22 25 20 38 C18 25 15 22 2 20 C15 18 18 15 20 2Z" fill="#fff" stroke="#1B2B8F" stroke-width="2"/></svg>'
HEART = '<svg viewBox="0 0 40 40"><path d="M20 35 C6 25 2 17 6 10 C10 4 17 5 20 11 C23 5 30 4 34 10 C38 17 34 25 20 35Z" fill="none" stroke="#fff" stroke-width="3.5" stroke-linejoin="round"/></svg>'
DOODLES = [
    # id, start, end, svg, left, top, size
    ("d1", 0.1, 2.95, SPARK, 150, 290, 60),
    ("d2", 0.3, 2.95, SPARK, 880, 560, 44),
    ("d3", 0.5, 2.95, HEART, 860, 290, 64),
    ("d4", S["IMG_1553"] + 0.2, S["IMG_1556"], SPARK, 860, 300, 54),
    ("d5", S["IMG_1560"] + 0.1, S["IMG_1568"], SPARK, 160, 300, 50),
    ("d6", S["IMG_1576"] + 0.3, S["IMG_1578"], HEART, 820, 980, 70),
    ("d7", e0 + 0.4, TOTAL, SPARK, 140, 280, 60),
    ("d8", e0 + 0.6, TOTAL, SPARK, 890, 960, 48),
    ("d9", e0 + 0.8, TOTAL, HEART, 870, 280, 62),
]

# ---- SFX (file, time, volume)
SFX = [
    ("pop", 0.08, 0.45), ("sparkle", 0.45, 0.30), ("pop", 1.55, 0.40),
    ("whoosh", 2.9, 0.35),
    ("pop", S["IMG_1536"] + 0.15, 0.35),
    ("pop", S["IMG_1558"] + 0.1, 0.30),
    ("pop", S["IMG_1529"] + 0.1, 0.30),
    ("pop", S["IMG_1551"] + 0.1, 0.30),
    ("sparkle", S["IMG_1553"] + 0.15, 0.28),
    ("pop", S["IMG_1556"] + 0.1, 0.32),
    ("pop", S["IMG_1590"] + 0.1, 0.30),
    ("whoosh", S["IMG_1560"] - 0.1, 0.30),
]
for clip in ["IMG_1560", "IMG_1568", "IMG_1576", "IMG_1578", "IMG_1580", "IMG_1583"]:
    SFX.append(("boing", S[clip] + 0.25, 0.30))
SFX += [("whoosh", e0 - 0.1, 0.30), ("ding", e0 + 0.2, 0.40), ("sparkle", e0 + 0.9, 0.25)]
SFX_DUR = {"pop": 0.14, "whoosh": 0.45, "sparkle": 0.7, "ding": 0.9, "boing": 0.35}

# ---------------------------------------------------------------- HTML
css = f"""
:root {{ --navy:{NAVY}; --yel:{YEL}; --ground:#0d1440; --ink:#fff; --font-display:'Grandstander',system-ui,sans-serif; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:var(--ground); }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:var(--font-display); background:var(--ground); }}
.vid {{ position:absolute; inset:0; width:{W}px; height:{H}px; object-fit:cover; transform-origin:50% 45%; }}
.ov {{ position:absolute; left:120px; width:840px; display:flex; justify-content:center; z-index:10; }}
.hl {{ text-align:center; color:#fff; font-weight:900; line-height:0.98; letter-spacing:-0.01em;
      text-shadow: 0 5px 0 var(--navy), 0 -2px 0 var(--navy), 3px 0 0 var(--navy), -3px 0 0 var(--navy), 0 10px 22px rgba(10,15,60,.45); }}
.hl-line {{ display:block; }}
.hl .y {{ color:var(--yel); }}
.pill {{ background:#fff; color:var(--navy); font-family:'Nunito',sans-serif; font-weight:800; font-size:52px;
        padding:16px 34px; border-radius:999px; box-shadow:0 6px 0 var(--navy), 0 12px 24px rgba(0,0,0,.25); text-align:center; }}
.pill b {{ color:#2E5BFF; font-weight:900; }}
.pill-navy {{ background:var(--navy); color:#fff; box-shadow:0 6px 0 #fff, 0 12px 24px rgba(0,0,0,.3); }}
.pill-navy b {{ color:var(--yel); }}
.nametag {{ background:var(--navy); color:#fff; font-family:'Nunito',sans-serif; font-weight:900; font-size:62px; line-height:1.0;
           padding:20px 40px; border-radius:26px; text-align:center; border:5px solid #fff; transform:rotate(-4deg);
           box-shadow:0 10px 26px rgba(0,0,0,.3); }}
.onoma {{ display:flex; gap:18px; font-size:96px; font-weight:900; color:#fff; font-style:italic;
         -webkit-text-stroke:6px var(--navy); paint-order:stroke fill; text-shadow:0 8px 0 var(--navy), 0 14px 26px rgba(10,15,60,.5); }}
.onoma span {{ display:inline-block; }}
.onoma span:nth-child(2) {{ color:var(--yel); }}
.endcard {{ width:840px; background:var(--navy); border-radius:46px; padding:46px 36px 40px; text-align:center; color:#fff;
           border:6px solid #fff; box-shadow:0 18px 40px rgba(0,0,0,.35); font-family:'Nunito',sans-serif; }}
.ec-top {{ display:inline-block; font-weight:900; font-size:30px; letter-spacing:.12em; border:3px solid #fff; border-radius:12px; padding:6px 16px; margin-bottom:22px; }}
.ec-title {{ font-family:var(--font-display); font-weight:900; font-size:86px; line-height:1.0; }}
.ec-sub {{ font-weight:900; font-size:50px; margin-top:12px; color:var(--yel); }}
.ec-small {{ font-weight:700; font-size:34px; margin-top:12px; opacity:.92; }}
.ec-dates {{ display:flex; align-items:center; justify-content:center; gap:22px; margin-top:30px; background:#fff; color:var(--navy);
            border-radius:999px; padding:16px 26px; font-weight:900; font-size:36px; line-height:1.1; }}
.ec-dates i {{ font-style:normal; font-weight:700; font-size:28px; }}
.ec-dates em {{ width:3px; height:64px; background:var(--navy); }}
.tnc {{ font-family:'Nunito',sans-serif; font-weight:700; font-size:28px; color:#fff; text-align:center;
        text-shadow:0 2px 6px rgba(0,0,0,.7); }}
.doodle {{ position:absolute; z-index:11; }}
.doodle svg {{ width:100%; height:100%; display:block; }}
.flash {{ position:absolute; inset:0; background:#fff; z-index:20; opacity:0; pointer-events:none; }}
"""

parts = []
for i, c in enumerate(CLIPS):
    audio_attr = 'muted data-has-audio="false"' if c["muted"] else 'data-has-audio="true" data-volume="1"'
    parts.append(
        f'      <video id="v{i}" class="clip vid" src="assets/clips/{c["name"]}.mp4" data-start="{c["start"]}" '
        f'data-duration="{c["dur"]}" data-media-start="{c["ms"]}" data-track-index="0" playsinline {audio_attr}></video>'
    )
for oid, st, en, html, pos in OVER:
    parts.append(
        f'      <div id="{oid}" class="clip ov" style="{pos}" data-start="{round(st,3)}" data-duration="{round(en-st,3)}" data-track-index="1">{html}</div>'
    )
for did, st, en, svg, x, y, sz in DOODLES:
    parts.append(
        f'      <div id="{did}" class="clip doodle" style="left:{x}px;top:{y}px;width:{sz}px;height:{sz}px" data-start="{round(st,3)}" data-duration="{round(en-st,3)}" data-track-index="2">{svg}</div>'
    )
parts.append(f'      <div id="flash" class="flash"></div>')
# music bed
parts.append(
    f'      <audio id="music" src="assets/music/cheerful_bed.wav" data-start="0" data-duration="{TOTAL}" data-media-start="0" '
    f'data-volume="0.07" data-fade-in="0.4" data-fade-out="1.5" data-track-index="3"></audio>'
)
for k, (f, st, vol) in enumerate(SFX):
    parts.append(
        f'      <audio id="sfx{k}" src="assets/sfx/{f}.wav" data-start="{round(st,3)}" data-duration="{SFX_DUR[f]}" data-volume="{vol}" data-track-index="{4 + k % 3}"></audio>'
    )

# ---- GSAP
js = ["const tl = gsap.timeline({ paused: true });"]
# gentle push-in on every clip, small punch on hook
for i, c in enumerate(CLIPS):
    s0, d = c["start"], c["dur"]
    if i == 0:
        js.append(f'tl.fromTo("#v{i}", {{scale:1.18}}, {{scale:1.0, duration:{d}, ease:"power2.out"}}, {s0});')
    else:
        js.append(f'tl.fromTo("#v{i}", {{scale:1.0}}, {{scale:1.06, duration:{d}, ease:"none"}}, {s0});')
# quick white flash on the cut into character section and end card
for n, at in enumerate([S["IMG_1560"], e0]):
    ir = "" if n == 0 else ", immediateRender:false"
    js.append(f'tl.fromTo("#flash", {{opacity:0.0}}, {{opacity:0.55, duration:0.06, ease:"none"{ir}}}, {at - 0.06});')
    js.append(f'tl.to("#flash", {{opacity:0, duration:0.22, ease:"power1.out"}}, {at});')
# overlays
for oid, st, en, html, pos in OVER:
    st = round(st, 3)
    if oid.startswith("o-name"):
        js.append(f'tl.fromTo("#{oid} .nametag", {{scale:0, rotation:-20}}, {{scale:1, rotation:-4, duration:0.4, ease:"back.out(2.2)"}}, {st});')
    elif oid == "o-krsk":
        js.append(f'tl.fromTo("#{oid} .onoma span", {{scale:0, y:30}}, {{scale:1, y:0, duration:0.3, ease:"back.out(3)", stagger:0.45}}, {st});')
        js.append(f'tl.to("#{oid} .onoma span", {{rotation:6, duration:0.12, yoyo:true, repeat:15, ease:"sine.inOut"}}, {st + 0.3});')
    elif oid == "o-end":
        js.append(f'tl.fromTo("#{oid} .endcard", {{scale:0.6, y:80, opacity:0}}, {{scale:1, y:0, opacity:1, duration:0.5, ease:"back.out(1.8)"}}, {st});')
        js.append(f'tl.fromTo("#{oid} .ec-dates", {{scale:0.8, opacity:0}}, {{scale:1, opacity:1, duration:0.35, ease:"back.out(2)"}}, {st + 0.45});')
        js.append(f'tl.to("#{oid} .endcard", {{scale:1.03, duration:0.6, yoyo:true, repeat:5, ease:"sine.inOut"}}, {st + 0.8});')
    elif "pill" in html:
        js.append(f'tl.fromTo("#{oid} .pill", {{scale:0.4, y:40, opacity:0}}, {{scale:1, y:0, opacity:1, duration:0.35, ease:"back.out(2.4)"}}, {st});')
    elif oid == "o-tnc":
        js.append(f'tl.fromTo("#{oid} .tnc", {{opacity:0}}, {{opacity:1, duration:0.3}}, {st});')
    else:  # headline: lines pop in with stagger
        js.append(f'tl.fromTo("#{oid} .hl-line", {{scale:0.3, y:40, opacity:0}}, {{scale:1, y:0, opacity:1, duration:0.32, ease:"back.out(2.6)", stagger:0.12}}, {st});')
        # subtle exit
        js.append(f'tl.to("#{oid} .hl", {{scale:0.92, opacity:0, duration:0.12, ease:"power1.in"}}, {round(en - 0.12, 3)});')
# doodles twinkle
for did, st, en, svg, x, y, sz in DOODLES:
    reps = max(1, int((en - st) / 0.5))
    js.append(f'tl.fromTo("#{did}", {{scale:0, rotation:-30}}, {{scale:1, rotation:0, duration:0.3, ease:"back.out(3)"}}, {round(st,3)});')
    js.append(f'tl.to("#{did}", {{scale:0.75, rotation:12, duration:0.25, yoyo:true, repeat:{reps}, ease:"sine.inOut"}}, {round(st + 0.3,3)});')
js.append('window.__timelines = window.__timelines || {};')
js.append('window.__timelines["main"] = tl;')
js.append('tl.seek(0);')

html = f"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>ZUS Buddy ASMR</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Grandstander:wght@800;900&family=Nunito:wght@700;800;900&display=block" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>{css}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
{chr(10).join(parts)}
    </div>
    <script>
      {(chr(10) + '      ').join(js)}
    </script>
  </body>
</html>
"""
open("index.html", "w").write(html)
print("total", TOTAL, "clips", len(CLIPS), "overlays", len(OVER), "sfx", len(SFX))
