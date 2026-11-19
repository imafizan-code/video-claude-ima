"""Build index.html (HyperFrames composition) from the edit decision list below.

Run:  python3 scripts/build.py
Everything is static + deterministic. Edit the EDL / overlays and rebuild.

v2 story: proud "finally got the full set" after refreshing the app & errors.
- shaky clips (IMG_1557, IMG_1558, IMG_1581) removed
- only ASMR clips keep their own sound; all other clips muted
- no SFX on text; text only sits on empty areas (floor / bed), never on the objects
"""

W, H = 1080, 1920
# Safe zone: 220 top, 480 bottom, 120 left/right  ->  x 120..960, y 220..1440

# ---- Edit decision list: (clip, duration, media_start, asmr_sound)
EDL = [
    ("IMG_1567", 3.0, 0.0, False),   # hook: Choco Chipster (steadiest take) + title
    ("IMG_1586", 2.2, 0.3, False),   # full set of cards
    ("IMG_1590", 3.5, 0.0, False),   # refresh app story (empty bed on top)
    ("IMG_1538", 2.8, 0.0, True),    # ASMR: tapping blind boxes with nails
    ("IMG_1558", 1.9, 0.0, True),    # ASMR: shaking the box
    ("IMG_1536", 3.4, 2.0, True),    # ASMR: slide blind box out of case
    ("IMG_1529", 1.3, 0.6, False),   # cards inside box
    ("IMG_1532", 1.6, 0.1, True),    # ASMR: foil crinkle (trimmed: cut from 0:12 in v2)
    ("IMG_1551", 1.8, 0.3, True),    # ASMR: mini desk out of plastic  -> "meja"
    ("IMG_1553", 2.4, 0.4, True),    # ASMR: sticker peel  -> "struggle satu tangan"
    ("IMG_1556", 1.5, 0.1, True),    # ASMR: tiny laptop (unmuted per request)
    ("IMG_1568", 2.2, 1.6, False),   # Blue Buddy
    ("IMG_1576", 2.2, 1.0, False),   # Pinky Boo
    ("IMG_1578", 2.0, 0.7, False),   # Bean Boss
    ("IMG_1580", 2.0, 0.3, False),   # Porta Pal
    ("IMG_1583", 3.0, 1.4, False),   # Frappe Fren (last)
]

t = 0.0
CLIPS = []
for name, dur, ms, asmr in EDL:
    CLIPS.append(dict(name=name, start=round(t, 3), dur=dur, ms=ms, asmr=asmr))
    t += dur
TOTAL = round(t, 3)
S = {c["name"]: c["start"] for c in CLIPS}
END = {c["name"]: round(c["start"] + c["dur"], 3) for c in CLIPS}

NAVY = "#1B2B8F"
YEL = "#FFD84D"

OVER = []  # (id, start, end, html, css-position)


def headline(i, st, en, lines, top, size=88):
    inner = "".join(f'<div class="hl-line">{ln}</div>' for ln in lines)
    OVER.append((i, st, en, f'<div class="hl" style="font-size:{size}px">{inner}</div>', f"top:{top}px"))


# Hook title over Choco Chipster (empty bed y 285-500, laptop starts ~570)
headline("o-hook", 0.05, END["IMG_1567"] - 0.05,
         ['<span class="y">ZUS BUDDY</span>', 'Work In Progress'], 250, 88)

# Cards: proud line on empty floor above the sticker sheet
headline("o-cards", S["IMG_1586"] + 0.05, END["IMG_1586"] - 0.05,
         ['berbaloi refresh', 'sampai <span class="y">jari kebas</span> <span class="emo">😂</span>'], 300, 76)

# Story over IMG_1590 (empty bed y 290-650, hand starts ~450 at its highest)
b0 = S["IMG_1590"]
headline("o-refresh", b0 + 0.05, b0 + 1.1, ['lama gila', '<span class="y">refresh</span> app...'], 285, 76)
headline("o-part", b0 + 1.15, b0 + 2.45, ['ni part yg', '<span class="y">mane</span> eh <span class="emo">😂</span>'], 285, 76)
headline("o-finally", b0 + 2.5, END["IMG_1590"] - 0.05, ['<span class="y">FINALLY</span>', 'dapat pun!! <span class="emo">😭</span>'], 285, 76)

# "meja" over the plastic-wrapped desk clip (free floor y ~400-540 below the box corner)
headline("o-meja", S["IMG_1551"] + 0.1, END["IMG_1551"] - 0.05, ['<span class="y">meja</span>'], 410, 96)

# sticker clip: sheet top rises to ~y 350, so keep this line in 228-345
headline("o-struggle", S["IMG_1553"] + 0.1, END["IMG_1553"] - 0.05,
         ['Agak struggle ye unboxing', 'dgn satu tgn <span class="emo">😆</span>'], 228, 56)

# ---- Doodles (twinkling sparkles), only beside text on empty areas
SPARK = '<svg viewBox="0 0 40 40"><path d="M20 2 C22 15 25 18 38 20 C25 22 22 25 20 38 C18 25 15 22 2 20 C15 18 18 15 20 2Z" fill="#fff" stroke="#1B2B8F" stroke-width="2"/></svg>'
DOODLES = [
    ("d1", 0.25, END["IMG_1567"] - 0.05, 150, 260, 44),
    ("d2", 0.45, END["IMG_1567"] - 0.05, 900, 250, 36),
    ("d3", b0 + 2.55, END["IMG_1590"] - 0.05, 290, 290, 44),
    ("d4", b0 + 2.65, END["IMG_1590"] - 0.05, 770, 300, 36),
]

# ---- Music: split into segments so it ducks under the ASMR clips
MUSIC_LO, MUSIC_HI = 0.04, 0.11
music_segs = []
for c in CLIPS:
    vol = MUSIC_LO if c["asmr"] else MUSIC_HI
    if music_segs and music_segs[-1][2] == vol:
        music_segs[-1][1] += c["dur"]
    else:
        music_segs.append([c["start"], c["dur"], vol])

# ---------------------------------------------------------------- HTML
css = f"""
@font-face {{ font-family:"Noto Color Emoji"; src:url("assets/fonts/NotoColorEmoji.ttf") format("truetype"); }}
:root {{ --navy:{NAVY}; --yel:{YEL}; --ground:#0d1440; --ink:#fff; --font-display:'Grandstander',system-ui,sans-serif; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:var(--ground); }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:var(--font-display); background:var(--ground); }}
.vid {{ position:absolute; inset:0; width:{W}px; height:{H}px; object-fit:cover; transform-origin:50% 50%; }}
.ov {{ position:absolute; left:120px; width:840px; display:flex; justify-content:center; z-index:10; }}
.hl {{ text-align:center; color:#fff; font-weight:900; line-height:1.0; letter-spacing:-0.01em;
      -webkit-text-stroke:5px var(--navy); paint-order:stroke fill;
      text-shadow: 0 6px 0 var(--navy), 0 10px 22px rgba(10,15,60,.45); }}
.hl-line {{ display:block; white-space:nowrap; }}
.hl .y {{ color:var(--yel); }}
.emo {{ font-family:'Noto Color Emoji',sans-serif; -webkit-text-stroke:0; text-shadow:none; font-size:.85em; }}
.toastbox {{ position:relative; width:640px; height:150px; }}
.toast {{ position:absolute; inset:0; display:flex; align-items:center; gap:24px; background:#fff; border-radius:30px;
         padding:0 34px; box-shadow:0 12px 30px rgba(10,15,60,.35); font-family:'Nunito',sans-serif; color:#1d2033; }}
.ic {{ flex:none; width:78px; height:78px; border-radius:50%; color:#fff; font-weight:900; font-size:50px;
      display:flex; align-items:center; justify-content:center; }}
.ic-err {{ background:#E5484D; }}
.ic-ok {{ background:#2DB463; }}
.tt {{ font-weight:900; font-size:44px; line-height:1.05; }}
.ts {{ font-weight:700; font-size:32px; color:#5b6075; margin-top:4px; }}
.t-err, .t-ok {{ opacity:0; }}
.doodle {{ position:absolute; z-index:11; }}
.doodle svg {{ width:100%; height:100%; display:block; }}
"""

parts = []
for i, c in enumerate(CLIPS):
    audio_attr = 'data-has-audio="true" data-volume="1"' if c["asmr"] else 'muted data-has-audio="false"'
    parts.append(
        f'      <video id="v{i}" class="clip vid" src="assets/clips/{c["name"]}.mp4" data-start="{c["start"]}" '
        f'data-duration="{round(c["dur"], 3)}" data-media-start="{c["ms"]}" data-track-index="0" playsinline {audio_attr}></video>'
    )
for oid, st, en, html, pos in OVER:
    parts.append(
        f'      <div id="{oid}" class="clip ov" style="{pos}" data-start="{round(st,3)}" data-duration="{round(en-st,3)}" data-track-index="1">{html}</div>'
    )
for did, st, en, x, y, sz in DOODLES:
    parts.append(
        f'      <div id="{did}" class="clip doodle" style="left:{x}px;top:{y}px;width:{sz}px;height:{sz}px" data-start="{round(st,3)}" data-duration="{round(en-st,3)}" data-track-index="2">{SPARK}</div>'
    )
last = len(music_segs) - 1
for k, (st, dur, vol) in enumerate(music_segs):
    fi = 0.4 if k == 0 else 0.12
    fo = 1.5 if k == last else 0.12
    parts.append(
        f'      <audio id="music{k}" src="assets/music/calm_bed.wav" data-start="{round(st,3)}" data-duration="{round(dur,3)}" '
        f'data-media-start="{round(st,3)}" data-volume="{vol}" data-fade-in="{fi}" data-fade-out="{fo}" data-track-index="3"></audio>'
    )

# ---- GSAP
js = ["const tl = gsap.timeline({ paused: true });"]
for i, c in enumerate(CLIPS):  # gentle push-in, no shake
    js.append(f'tl.fromTo("#v{i}", {{scale:1.0}}, {{scale:1.04, duration:{c["dur"]}, ease:"none"}}, {c["start"]});')
for oid, st, en, html, pos in OVER:
    st = round(st, 3)
    if oid == "o-toast":
        js.append(f'tl.fromTo("#o-toast .t-err", {{scale:0.5, opacity:0}}, {{scale:1, opacity:1, duration:0.3, ease:"back.out(2.2)"}}, {st});')
        js.append(f'tl.to("#o-toast .t-err", {{x:14, duration:0.05, yoyo:true, repeat:5, ease:"none"}}, {st + 0.4});')
        js.append(f'tl.to("#o-toast .t-err", {{x:14, duration:0.05, yoyo:true, repeat:5, ease:"none"}}, {st + 0.85});')
        js.append(f'tl.to("#o-toast .t-err", {{scale:0.6, opacity:0, duration:0.1, ease:"power1.in"}}, {st + 1.2});')
    else:  # headline lines pop in, quick fade out
        js.append(f'tl.fromTo("#{oid} .hl-line", {{scale:0.4, y:30, opacity:0}}, {{scale:1, y:0, opacity:1, duration:0.3, ease:"back.out(2.4)", stagger:0.12}}, {st});')
        if en < TOTAL - 0.01:
            js.append(f'tl.to("#{oid} .hl", {{opacity:0, duration:0.1, ease:"power1.in"}}, {round(en - 0.1, 3)});')
for did, st, en, x, y, sz in DOODLES:
    reps = max(1, int((en - st - 0.3) / 0.5))
    js.append(f'tl.fromTo("#{did}", {{scale:0, rotation:-30}}, {{scale:1, rotation:0, duration:0.3, ease:"back.out(3)"}}, {round(st,3)});')
    js.append(f'tl.to("#{did}", {{scale:0.7, rotation:12, duration:0.25, yoyo:true, repeat:{reps}, ease:"sine.inOut"}}, {round(st + 0.3,3)});')
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
print("total", TOTAL, "clips", len(CLIPS), "overlays", len(OVER), "music segs", music_segs)
