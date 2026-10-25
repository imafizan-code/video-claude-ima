"""Generates the HyperFrames composition for the MY alrajhi tutorial.

python3 build/gen.py   (from the project root) -> index.html, compositions/overlays.html, compositions/captions.html
All timing comes from the edit decision list (EDL) below: media in/out per kept take.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920

# ---------------------------------------------------------------- EDL
# (id, clip, media_in, media_out, mode)  mode: face = full-frame talking head, demo = PiP + phone/card
EDL = [
    ("h1", "0399", 0.00, 4.18, "face"),   # Kau tahu tak, sekarang ni kita boleh buka bank tanpa perlu pergi ke cawangan pun
    ("h2", "0399", 4.72, 7.30, "face"),   # tak perlu nak beratur, tak perlu nak ambil nombor giliran   ("So" removed)
    ("h3", "0399", 7.66, 8.56, "face"),   # Nak tahu macam mana?                                      ("Baik, saya tunjuk" removed)
    ("s1", "0408", 0.00, 4.02, "demo"),   # Mula-mula korang download dulu app MY alrajhi bank dekat phone korang
    ("s2a", "0424", 0.00, 2.12, "demo"),  # Lepas itu, ikut arahan untuk pendaftaran,
    ("s2b", "0424", 2.44, 4.50, "demo"),  # isi maklumat pengesahan yang diperlukan
    ("s3", "0431", 0.10, 2.22, "face"),   # dan top up minimum RM20 je.
    ("s4a", "0484", 0.00, 3.80, "face"),  # Bila dah berjaya aktifkan DuitPlus Savings Account-i ni,
    ("s4b", "0484", 3.80, 8.86, "demo"),  # korang akan dapat referral code dan bolehlah korang share dengan family dan kawan-kawan.
    ("r1", "0494", 0.46, 4.64, "face"),   # Boleh guna referral code ini dan kedua-dua belah pihak akan dapat manis-manis
    ("r2", "0494", 5.24, 7.50, "face"),   # selepas account berjaya diaktifkan.     ("RM10" removed: brief says manis-manis only)
    ("p1", "0529", 0.00, 3.48, "face"),   # dan duit korang pun selamat sebab dilindungi oleh PIDM.
    ("b1", "0503", 0.00, 4.48, "face"),   # lagi satu yang tengah simpan duit untuk beli rumah, kahwin atau pergi umrah
    ("t1", "0518", 0.46, 8.62, "face"),   # alrajhi bank Malaysia menawarkan TD-i Advantage Campaign, ... profit rate sehingga 4%
    ("t2", "0519", 0.14, 1.44, "face"),   # selama 12 bulan
    ("c1", "0540", 0.86, 7.24, "demo"),   # tunggu apa lagi, korang download je MY alrajhi app, aktifkan DuitPlus Savings Account-i dan  ("So" removed)
    ("c2", "0541", 0.08, 1.20, "demo"),   # guna referral code ni
    ("e1", "0553", 0.60, 1.38, "face"),   # Jom nabung.
]
END_HOLD = 0.9

SEG = {}
t = 0.0
for sid, clip, a, b, mode in EDL:
    SEG[sid] = dict(id=sid, clip=clip, a=a, b=b, mode=mode, start=round(t, 3), dur=round(b - a, 3))
    t += b - a
TOTAL = round(t + END_HOLD, 3)


def at(sid, media_t):
    """Output time of a media time inside a kept segment."""
    s = SEG[sid]
    return round(s["start"] + (media_t - s["a"]), 3)


def seg_end(sid):
    return round(SEG[sid]["start"] + SEG[sid]["dur"], 3)


# Face centre per clip (from face detection), used for punch-ins and the PiP circle.
FACE = {"0399": (537, 1031), "0408": (547, 973), "0424": (545, 981), "0431": (583, 971), "0484": (556, 930),
        "0494": (622, 932), "0503": (599, 894), "0518": (573, 912), "0519": (553, 901), "0529": (563, 873),
        "0540": (582, 868), "0541": (593, 881), "0553": (643, 865)}

# ---------------------------------------------------------------- layout constants
PIP_D = 340                                    # PiP circle diameter on canvas
PIP_X, PIP_Y = 692, 196                        # PiP top-left on canvas
PIP_SCALE = 0.40
PIP_R_SRC = PIP_D / 2 / PIP_SCALE              # circle radius in source pixels
PH_X, PH_Y, BEZ = 56, 300, 10                  # phone card
SW = 452; SH = round(SW * 1920 / 888)          # phone screen size (screen recording aspect)
K = SW / 888                                   # screen-recording px -> screen px

# ---------------------------------------------------------------- mode transitions
modes = []
for sid, *_r, mode in EDL:
    if not modes or modes[-1][1] != mode:
        modes.append((SEG[sid]["start"], mode, sid))
TRANS = 0.55

# ---------------------------------------------------------------- phone content (inside the screen, at screen px)
# Each item: kind, src, start, dur, media_start, rate
s1, s2a, s2b = SEG["s1"]["start"], SEG["s2a"]["start"], SEG["s2b"]["start"]
A_START = s1 + 2.55                     # registration recording starts playing after the logo beat
B_START = A_START + 3.0                 # clip A: media 0.0-3.0 at 1x
B_RATE, B_IN, B_OUT = 1.3, 5.6, 7.3
C_START = B_START + (B_OUT - B_IN) / B_RATE
C_RATE, C_IN, C_OUT = 1.5, 10.0, 10.6   # nickname screen: tap field, keyboard rises (no typing shown)
K_START = C_START + (C_OUT - C_IN) / C_RATE
K_END = seg_end("s2b")
REF_START, REF_END = SEG["s4b"]["start"], seg_end("s4b")

PHONE_ITEMS = [
    dict(id="ph-welcome", kind="img", src="assets/screen/welcome.png", start=s1, dur=A_START - s1),
    dict(id="ph-reg-a", kind="video", src="assets/screen/register.mp4", start=A_START, dur=3.0, ms=0.0, rate=1),
    dict(id="ph-reg-b", kind="video", src="assets/screen/register.mp4", start=B_START, dur=(B_OUT - B_IN) / B_RATE, ms=B_IN, rate=B_RATE),
    dict(id="ph-reg-c", kind="video", src="assets/screen/register.mp4", start=C_START, dur=(C_OUT - C_IN) / C_RATE, ms=C_IN, rate=C_RATE),
    dict(id="ph-mykad", kind="img", src="assets/screen/mykad.png", start=K_START, dur=K_END - K_START),
]


def rec_t(clip_start, media_in, rate, media_t):
    return round(clip_start + (media_t - media_in) / rate, 3)


# taps: (time, x, y) in screen px
TAPS = [
    (rec_t(A_START, 0, 1, 0.65), 444 * K, 1435 * K),     # Get started now
    (rec_t(A_START, 0, 1, 1.80), 444 * K, 1200 * K),     # New to alrajhi bank Malaysia
    (rec_t(B_START, B_IN, B_RATE, 5.85), 81 * K, 1285 * K),   # acknowledge checkbox
    (rec_t(B_START, B_IN, B_RATE, 6.60), 444 * K, 1738 * K),  # Next
    (rec_t(C_START, C_IN, C_RATE, 10.15), 300 * K, 710 * K),  # nickname field
    (round(K_END - 0.22, 3), 0.5 * SW, 2287 / 2532 * SH),     # Start verification process (MyKad screen)
]
# zooms: (start, end, scale, cx, cy) in screen px; eases in, holds, eases out
ZOOMS = [
    (A_START - 0.15, A_START + 1.05, 1.55, 0.5 * SW, 1380 * K),
    (B_START - 0.05, B_START + 1.15, 1.45, 0.5 * SW, 1480 * K),
]

# referral screenshot sits at the top of a white screen; code + copy icon in screen px
REF_W = SW; REF_H = round(SW * 686 / 1170); REF_TOP = 150
REF_COPY = (1010 / 1170 * SW, REF_TOP + 545 / 686 * REF_H)
TAPS.append((at("s4b", 5.05), REF_COPY[0], REF_COPY[1]))
ZOOMS.append((at("s4b", 4.45), at("s4b", 5.7), 1.25, 0.4 * SW, REF_TOP + 0.6 * REF_H))

# ---------------------------------------------------------------- captions
FIX = {"jarahan": "arahan", "belia": "belah", "kawin": "kahwin", "dihendungi": "dilindungi", "kecawangan": "ke cawangan",
       "TDI": "TD-i", "account": "account"}
words_raw = json.load(open(os.path.join(ROOT, "build", "words.json")))


def clip_words(clip):
    out = []
    for w in words_raw["IMG_" + clip]:
        txt = w["w"].strip()
        if txt.startswith("-") and out:                       # "Mula" "-mula" -> "Mula-mula"
            out[-1]["w"] += txt; out[-1]["e"] = w["e"]; continue
        if txt == "%" and out:
            out[-1]["w"] += "%"; out[-1]["e"] = w["e"]; continue
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
    for w in out:
        core = w["w"].strip(",.?!")
        if core in FIX:
            w["w"] = w["w"].replace(core, FIX[core])
        w["w"] = w["w"].replace("TD -i", "TD-i")
    return out


CAP = []   # (start, end, text, mode)
for sid, clip, a, b, mode in EDL:
    if sid in ("h1", "e1"):
        continue                                               # the hook headline carries these words
    for w in clip_words(clip):
        mid = (w["s"] + w["e"]) / 2
        if a <= mid <= b:
            s = max(w["s"], a); e = min(w["e"], b)
            for part in w["w"].split(" "):
                CAP.append([at(sid, s), at(sid, e), part, mode, sid])

groups, cur = [], []
for i, w in enumerate(CAP):
    cur.append(w)
    nxt = CAP[i + 1] if i + 1 < len(CAP) else None
    limit = 3 if w[3] == "demo" else 4
    chars = sum(len(x[2]) + 1 for x in cur)
    brk = (nxt is None or re.search(r"[,.?!]$", w[2]) or len(cur) >= limit or chars > (16 if w[3] == "demo" else 22)
           or (nxt and nxt[0] - w[1] > 0.15) or (nxt and nxt[4] != w[4]))
    if brk:
        groups.append(cur); cur = []

# ---------------------------------------------------------------- HTML helpers
def clip_attrs(start, dur, track):
    return f'class="clip" data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="{track}"'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


FONTS = "'Outfit', 'Inter', sans-serif"

# ================================================================= index.html
face_videos = []
for sid, clip, a, b, mode in EDL:
    s = SEG[sid]
    face_videos.append(
        f'<video id="v-{sid}" {clip_attrs(s["start"], s["dur"], 1)} src="assets/face/f{clip}.mp4" '
        f'data-media-start="{a:.3f}" data-has-audio="true" data-volume="1" playsinline '
        f'style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover"></video>')
# the final hold keeps the last face frame: a still from the end of the last take
last = SEG["e1"]
face_videos.append(
    f'<img id="v-hold" {clip_attrs(seg_end("e1"), END_HOLD, 1)} src="assets/face/hold.jpg" '
    f'style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover" alt="">')

phone_media = []
for it in PHONE_ITEMS:
    style = f"position:absolute;left:0;top:0;width:{SW}px;height:{SH}px;object-fit:cover"
    if it["kind"] == "img":
        phone_media.append(f'<img id="{it["id"]}" {clip_attrs(it["start"], it["dur"], 3)} src="{it["src"]}" style="{style}" alt="">')
    else:
        phone_media.append(
            f'<video id="{it["id"]}" {clip_attrs(it["start"], it["dur"], 3)} src="{it["src"]}" muted playsinline '
            f'data-media-start="{it["ms"]:.3f}" data-playback-rate="{it["rate"]}" style="{style}"></video>')
phone_media.append(
    f'<div id="ph-ref" {clip_attrs(REF_START, REF_END - REF_START, 3)} style="position:absolute;left:0;top:0;width:{SW}px;height:{SH}px;background:#fff">'
    f'<img src="assets/screen/referral.png" style="position:absolute;left:0;top:{REF_TOP}px;width:{REF_W}px;height:{REF_H}px" alt="">'
    f'<div class="share-line" id="share-a"></div><div class="share-line" id="share-b"></div>'
    f'<div class="share-chip" id="share-fam"><span class="dot"></span>Family</div>'
    f'<div class="share-chip" id="share-kwn"><span class="dot"></span>Kawan-kawan</div></div>')

ripples = []
for i, (tt, x, y) in enumerate(TAPS):
    ripples.append(f'<div class="ripple" id="rp{i}" style="left:{x - 60:.1f}px;top:{y - 60:.1f}px"><i></i><b></b></div>')

# audio
SFX = []   # (id, file, time, volume)
for i, (tt, *_xy) in enumerate(TAPS):
    SFX.append((f"sx-tap{i}", "click-soft", tt + 0.033, 0.55 if i % 2 else 0.45))
for i, (mt, _m, sid) in enumerate(modes[1:]):
    SFX.append((f"sx-wh{i}", "whoosh-short", mt + 0.12, 0.30 if i % 2 else 0.22))

LOGO_T = at("s1", 1.95)
SFX.append(("sx-logo", "sparkle", LOGO_T + 0.03, 0.35))

# overlay beat times (shared with overlays.html)
B = dict(
    hook_words=[(at("h1", w["s"]), w["w"]) for w in clip_words("0399") if w["s"] < 4.18],
    beratur=at("h2", 5.32), giliran=at("h2", 6.88),
    aktif=at("s4a", 0.95), rm20=at("s3", 1.26), share=at("s4b", 6.6),
    gift=at("r1", 3.7), aktifkan2=at("r2", 6.85), pidm=at("p1", 2.95),
    rumah=at("b1", 1.95), kahwin=at("b1", 2.8), umrah=at("b1", 3.65),
    tdi=at("t1", 2.6), rate=at("t1", 7.7), bulan=at("t2", 0.65),
    cta1=at("c1", 2.2), cta2=at("c1", 4.4), cta3=at("c1", 6.3), jom=at("e1", 0.62),
)
for k, v in [("beratur", "pop"), ("giliran", "pop"), ("rumah", "pop"), ("kahwin", "pop"), ("umrah", "pop"),
             ("aktif", "chime"), ("pidm", "pop"), ("rate", "ping"), ("gift", "pop"), ("cta1", "pop"), ("cta2", "pop"), ("cta3", "pop")]:
    tt = SEG["p1"]["start"] + 0.2 if k == "pidm" else B[k]
    SFX.append((f"sx-{k}", v, tt + 0.08, 0.26 if v == "pop" else 0.30))
SFX.append(("sx-share", "whoosh-short", B["share"] + 0.05, 0.18))

audio = [f'<audio id="music" class="clip" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="8" src="assets/music/bed.mp3" '
         f'data-media-start="10" data-volume="0.12" data-fade-in="0.4" data-fade-out="1.4"></audio>']
DUR = {"click-soft": 0.366, "whoosh-short": 0.575, "sparkle": 1.8, "pop": 0.72, "chime": 2.5, "ping": 1.32}
for i, (aid, f, tt, vol) in enumerate(sorted(SFX, key=lambda x: x[2])):
    d = min(DUR[f], TOTAL - tt - 0.01)
    audio.append(f'<audio id="{aid}" class="clip" data-start="{tt:.3f}" data-duration="{d:.3f}" data-track-index="{9 + i % 3}" '
                 f'src="assets/sfx/{f}.mp3" data-volume="{vol}"></audio>')

# GSAP for root: punch-ins, PiP morph, phone in/out, zooms, ripples, share
js = []
cx0, cy0 = FACE["0399"]
js.append(f'tl.set("#facewrap", {{x:0, y:0, scale:1, clipPath:"circle(1500px at {cx0}px {cy0}px)"}}, 0);')
# #phone, #pipring and #ctacard start hidden through CSS (opacity:0); their first tween sets the rest
punch = [1.0, 1.10, 1.0, 1.07, 1.0, 1.12]
pi = 0
for sid, clip, a, b, mode in EDL:
    s = SEG[sid]; fx, fy = FACE[clip]
    if mode == "face":
        sc = punch[pi % len(punch)]; pi += 1
        js.append(f'tl.set("#punch", {{scale:{sc}, transformOrigin:"{fx}px {fy}px"}}, {s["start"]:.3f});')
    else:
        js.append(f'tl.set("#punch", {{scale:1, transformOrigin:"{fx}px {fy}px"}}, {s["start"]:.3f});')
js.append(f'tl.set("#punch", {{scale:1.07}}, {seg_end("e1"):.3f});')

last_holder = "#phone"
seen = {}
for mt, mode, sid in modes[1:]:
    fx, fy = FACE[SEG[sid]["clip"]]
    t0 = max(0, mt - 0.18)
    holder = "#ctacard" if sid.startswith("c") else "#phone"
    if mode == "demo":
        px = PIP_X + PIP_D / 2 - fx * PIP_SCALE; py = PIP_Y + PIP_D / 2 - fy * PIP_SCALE
        js.append(f'tl.to("#facewrap", {{clipPath:"circle({PIP_R_SRC:.0f}px at {fx}px {fy}px)", x:{px:.1f}, y:{py:.1f}, scale:{PIP_SCALE}, '
                  f'transformOrigin:"0px 0px", duration:{TRANS}, ease:"power3.inOut"}}, {t0:.3f});')
        ir = "" if not seen.get("#pipring") else ", immediateRender:false"; seen["#pipring"] = 1
        js.append(f'tl.fromTo("#pipring", {{opacity:0, scale:0.8}}, {{opacity:1, scale:1, duration:0.35, ease:"power2.out"{ir}}}, {t0 + 0.35:.3f});')
        ir = "" if not seen.get(holder) else ", immediateRender:false"; seen[holder] = 1
        js.append(f'tl.fromTo("{holder}", {{opacity:0, y:140, filter:"blur(10px)"}}, {{opacity:1, y:0, filter:"blur(0px)", duration:0.6, ease:"expo.out"{ir}}}, {t0 + 0.22:.3f});')
        last_holder = holder
    else:
        js.append(f'tl.to("{last_holder}", {{opacity:0, y:90, filter:"blur(8px)", duration:0.3, ease:"power3.in"}}, {t0:.3f});')
        js.append(f'tl.to("#pipring", {{opacity:0, scale:0.9, duration:0.2, ease:"power2.in"}}, {t0:.3f});')
        js.append(f'tl.to("#facewrap", {{clipPath:"circle(1500px at {fx}px {fy}px)", x:0, y:0, scale:1, duration:{TRANS}, ease:"power3.inOut"}}, {t0 + 0.05:.3f});')

for i, (z0, z1, sc, cx, cy) in enumerate(ZOOMS):
    x = min(0, max(SW - SW * sc, SW / 2 - cx * sc)); y = min(0, max(SH - SH * sc, SH / 2 - cy * sc))
    js.append(f'tl.to("#zoom", {{scale:{sc}, x:{x:.1f}, y:{y:.1f}, duration:0.6, ease:"power2.inOut"}}, {z0:.3f});')
    js.append(f'tl.to("#zoom", {{scale:1, x:0, y:0, duration:0.5, ease:"power2.inOut"}}, {max(z0 + 0.65, z1 - 0.5):.3f});')
js.append('tl.set("#zoom", {scale:1, x:0, y:0, transformOrigin:"0px 0px"}, 0);')

for i, (tt, x, y) in enumerate(TAPS):
    js.append(f'tl.fromTo("#rp{i} i", {{scale:0.2, opacity:0.55}}, {{scale:1.6, opacity:0, duration:0.55, ease:"power2.out"}}, {tt:.3f});')
    js.append(f'tl.fromTo("#rp{i} b", {{scale:1.25, opacity:0}}, {{scale:0.85, opacity:0.95, duration:0.12, ease:"power2.out"}}, {tt - 0.12:.3f});')
    js.append(f'tl.to("#rp{i} b", {{scale:1, opacity:0, duration:0.25, ease:"power2.in"}}, {tt + 0.08:.3f});')

sh = B["share"]
js.append(f'tl.fromTo("#share-a", {{scaleY:0}}, {{scaleY:1, duration:0.35, ease:"power2.out"}}, {sh - 0.2:.3f});')
js.append(f'tl.fromTo("#share-b", {{scaleY:0}}, {{scaleY:1, duration:0.35, ease:"power2.out"}}, {sh - 0.1:.3f});')
js.append(f'tl.fromTo("#share-fam", {{opacity:0, y:30, scale:0.8}}, {{opacity:1, y:0, scale:1, duration:0.45, ease:"back.out(1.6)"}}, {at("s4b", 7.15):.3f});')
js.append(f'tl.fromTo("#share-kwn", {{opacity:0, y:30, scale:0.8}}, {{opacity:1, y:0, scale:1, duration:0.45, ease:"back.out(1.6)"}}, {at("s4b", 8.2):.3f});')

# CTA card rows
for i, k in enumerate(["cta1", "cta2", "cta3"]):
    js.append(f'tl.fromTo("#cta-r{i}", {{opacity:0, x:-40, filter:"blur(6px)"}}, {{opacity:1, x:0, filter:"blur(0px)", duration:0.45, ease:"expo.out"}}, {B[k]:.3f});')
js.append(f'tl.fromTo("#cta-code", {{opacity:0, scale:0.9}}, {{opacity:1, scale:1, duration:0.5, ease:"back.out(1.5)"}}, {B["cta3"] + 0.25:.3f});')

cta_rows = [("1", "Download <b>MY alrajhi app</b>"), ("2", "Aktifkan <b>DuitPlus Savings Account-i</b>"), ("3", "Guna referral code aku")]
cta_html = "".join(f'<div class="cta-row" id="cta-r{i}"><span class="n">{n}</span><span class="t">{t}</span></div>' for i, (n, t) in enumerate(cta_rows))

index = f"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      :root {{ --brand:#251CFC; --brand2:#5B54FF; --ink:#0A0E2A; --mint:#2EE6A6; --paper:#F6F7FF; --font:{FONTS}; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:var(--ink); }}
      #root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:var(--font); }}
      #bg {{ position:absolute; inset:0; background:
              radial-gradient(900px 700px at 80% 12%, rgba(91,84,255,.55), transparent 60%),
              radial-gradient(800px 800px at 10% 85%, rgba(37,28,252,.45), transparent 60%),
              linear-gradient(170deg, #0D1240 0%, #070A22 100%); }}
      #grid {{ position:absolute; inset:0; opacity:.22;
              background-image: radial-gradient(rgba(255,255,255,.55) 1.4px, transparent 1.6px); background-size:44px 44px; }}
      #facewrap {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; will-change:transform, clip-path; z-index:5; }}
      #phone, #pipring, #ctacard {{ opacity:0; }}
      #punch {{ position:absolute; inset:0; }}
      #pipring {{ position:absolute; left:{PIP_X - 8}px; top:{PIP_Y - 8}px; width:{PIP_D + 16}px; height:{PIP_D + 16}px; border-radius:50%;
              border:6px solid transparent; z-index:6;
              background: linear-gradient(var(--ink), var(--ink)) padding-box, conic-gradient(from 200deg, var(--mint), var(--brand2), var(--brand), var(--mint)) border-box;
              -webkit-mask: radial-gradient(circle, transparent {PIP_D / 2}px, #000 {PIP_D / 2 + 1}px); mask: radial-gradient(circle, transparent {PIP_D / 2}px, #000 {PIP_D / 2 + 1}px); }}
      #phone {{ position:absolute; left:{PH_X}px; top:{PH_Y}px; width:{SW + 2 * BEZ}px; height:{SH + 2 * BEZ}px; border-radius:58px; padding:{BEZ}px;
              background:linear-gradient(160deg,#2A2F55,#0B0E24); z-index:7;
              box-shadow: 0 0 0 2px rgba(255,255,255,.12), 0 40px 90px rgba(0,0,0,.55), 0 0 120px rgba(37,28,252,.45); }}
      #screen {{ position:relative; width:{SW}px; height:{SH}px; border-radius:48px; overflow:hidden; background:#fff; }}
      #zoom {{ position:absolute; left:0; top:0; width:{SW}px; height:{SH}px; }}
      .ripple {{ position:absolute; width:120px; height:120px; pointer-events:none; z-index:20; }}
      .ripple i {{ position:absolute; inset:0; border-radius:50%; border:6px solid var(--brand); background:rgba(37,28,252,.18); opacity:0; }}
      .ripple b {{ position:absolute; left:36px; top:36px; width:48px; height:48px; border-radius:50%; background:rgba(10,14,42,.35);
                   box-shadow:0 0 0 3px rgba(255,255,255,.9); opacity:0; }}
      .share-line {{ position:absolute; width:4px; background:repeating-linear-gradient(var(--brand) 0 10px, transparent 10px 18px); transform-origin:top; }}
      #share-a {{ left:{SW * 0.28:.0f}px; top:{REF_TOP + REF_H + 10}px; height:150px; }}
      #share-b {{ left:{SW * 0.70:.0f}px; top:{REF_TOP + REF_H + 10}px; height:290px; }}
      .share-chip {{ position:absolute; display:flex; align-items:center; gap:12px; padding:16px 26px; border-radius:999px; background:var(--brand);
                    color:#fff; font:800 30px var(--font); box-shadow:0 12px 30px rgba(37,28,252,.35); white-space:nowrap; }}
      .share-chip .dot {{ width:16px; height:16px; border-radius:50%; background:var(--mint); }}
      #share-fam {{ left:{SW * 0.28 - 90:.0f}px; top:{REF_TOP + REF_H + 165}px; }}
      #share-kwn {{ left:{SW * 0.70 - 175:.0f}px; top:{REF_TOP + REF_H + 305}px; }}
      #ctacard {{ position:absolute; left:{PH_X}px; top:{PH_Y}px; width:480px; z-index:7; padding:40px 34px; border-radius:44px;
                  background:rgba(255,255,255,.07); border:2px solid rgba(255,255,255,.14); box-shadow:0 40px 90px rgba(0,0,0,.45); }}
      #ctacard h2 {{ color:#fff; font:900 52px/1.05 var(--font); letter-spacing:-.02em; margin-bottom:34px; }}
      #ctacard h2 em {{ font-style:normal; color:var(--mint); }}
      .cta-row {{ display:flex; align-items:center; gap:22px; padding:22px 0; border-top:2px solid rgba(255,255,255,.10); }}
      .cta-row .n {{ flex:none; width:64px; height:64px; border-radius:20px; background:var(--brand); color:#fff; font:900 34px var(--font);
                     display:flex; align-items:center; justify-content:center; }}
      .cta-row .t {{ color:rgba(255,255,255,.85); font:600 31px/1.2 var(--font); }}
      .cta-row .t b {{ color:#fff; font-weight:800; }}
      #cta-code {{ margin-top:26px; padding:26px 28px; border-radius:28px; background:#fff; display:flex; align-items:center; justify-content:space-between; }}
      #cta-code .lbl {{ font:700 28px var(--font); color:#6B6F8F; letter-spacing:.08em; }}
      #cta-code .code {{ font:900 40px var(--font); color:var(--brand); letter-spacing:.04em; }}
      #cta-code svg {{ width:54px; height:54px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="{W}" data-height="{H}">
      <div id="bg"><div id="grid"></div></div>
      <div id="facewrap"><div id="punch">
        {chr(10).join('        ' + v for v in face_videos).strip()}
      </div></div>
      <div id="pipring"></div>
      <div id="phone"><div id="screen"><div id="zoom">
        {chr(10).join('        ' + v for v in phone_media).strip()}
        {''.join(ripples)}
      </div></div></div>
      <div id="ctacard">
        <h2>Jom mula <em>sekarang</em></h2>
        {cta_html}
        <div id="cta-code"><div><div class="lbl">REFERRAL CODE</div><div class="code">MYA04620NHH</div></div>
          <svg viewBox="0 0 24 24" fill="none" stroke="#251CFC" stroke-width="2"><rect x="8" y="8" width="12" height="12" rx="3"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg></div>
      </div>
      <div id="overlays" data-composition-id="overlays" data-composition-src="compositions/overlays.html" data-track-kind="graphics"
           data-start="0" data-duration="{TOTAL:.3f}" data-track-index="5" data-width="{W}" data-height="{H}" style="z-index:30"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-track-kind="captions"
           data-start="0" data-duration="{TOTAL:.3f}" data-track-index="6" data-width="{W}" data-height="{H}" style="z-index:40"></div>
      {chr(10).join('      ' + a for a in audio).strip()}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join('      ' + j for j in js).strip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open(os.path.join(ROOT, "index.html"), "w").write(index)

# ================================================================= overlays.html
OV, OJS = [], []


def ov(id_, start, end, html, cls="", style=""):
    OV.append(f'<div id="{id_}" class="clip ov {cls}" data-start="{start:.3f}" data-duration="{end - start:.3f}" data-track-index="{len(OV) % 3}" style="{style}">{html}</div>')


def fin(sel, t0, kind="blur", d=0.5):
    if kind == "blur":
        OJS.append(f'tl.fromTo("{sel}", {{opacity:0, filter:"blur(10px)", y:16}}, {{opacity:1, filter:"blur(0px)", y:0, duration:{d}, ease:"expo.out"}}, {t0:.3f});')
    elif kind == "pop":
        OJS.append(f'tl.fromTo("{sel}", {{opacity:0, scale:0.6}}, {{opacity:1, scale:1, duration:{d}, ease:"back.out(1.7)"}}, {t0:.3f});')
    elif kind == "left":
        OJS.append(f'tl.fromTo("{sel}", {{opacity:0, x:-60, filter:"blur(8px)"}}, {{opacity:1, x:0, filter:"blur(0px)", duration:{d}, ease:"expo.out"}}, {t0:.3f});')


def fout(sel, t1, d=0.22):
    OJS.append(f'tl.to("{sel}", {{opacity:0, filter:"blur(8px)", duration:{d}, ease:"power2.in"}}, {t1 - d - 0.02:.3f});')


# ---- hook headline: words arrive with the voice
hw = B["hook_words"]
line1, line2 = ["Kau", "tahu", "tak,", "sekarang", "ni", "boleh", "buka", "akaun", "bank"], []
head_words = [("Boleh", "boleh"), ("buka", "buka"), ("akaun", "bank"), ("bank", "bank"), ("tanpa", "tanpa"), ("pergi", "pergi"),
              ("cawangan?", "kecawangan")]
times = {w.strip(",.?!").lower(): t_ for t_, w in hw}
spans = []
for i, (txt, key) in enumerate(head_words):
    cls = ' class="hl"' if txt in ("tanpa",) else ""
    spans.append(f'<span id="hw{i}"{cls}>{txt}</span>')
    OJS.append(f'tl.fromTo("#hw{i}", {{opacity:0.0, filter:"blur(8px)"}}, {{opacity:1, filter:"blur(0px)", duration:0.16, ease:"power2.out"}}, {max(0.0, times.get(key, 0) - 0.05):.3f});')
hook_end = seg_end("h1")
ov("hook", 0, hook_end + 0.05, f'<div class="kicker">TIPS BANK DIGITAL</div><div class="head">{" ".join(spans[:4])}<br>{" ".join(spans[4:])}</div>', "glass", "left:60px;top:200px;width:960px;padding:30px 40px")
OJS.append('tl.set("#hw0,#hw1,#hw2,#hw3", {opacity:1, filter:"blur(0px)"}, 0);')   # frame 0 already carries the hook
fout("#hook", hook_end + 0.05)

# ---- no queue, no number
xsvg = '<svg viewBox="0 0 24 24" width="40" height="40"><circle cx="12" cy="12" r="11" fill="#FF4D6D"/><path d="M8 8l8 8M16 8l-8 8" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/></svg>'
ov("no1", B["beratur"] - 0.1, seg_end("h3"), f'{xsvg}<span>Beratur</span><s></s>', "chip", "left:60px;top:220px")
ov("no2", B["giliran"] - 0.1, seg_end("h3"), f'{xsvg}<span>Nombor giliran</span><s></s>', "chip", "left:350px;top:220px")
fin("#no1", B["beratur"] - 0.1, "pop", 0.4); fin("#no2", B["giliran"] - 0.1, "pop", 0.4)
OJS.append(f'tl.fromTo("#no1 s", {{scaleX:0}}, {{scaleX:1, duration:0.25, ease:"power2.out"}}, {B["beratur"] + 0.25:.3f});')
OJS.append(f'tl.fromTo("#no2 s", {{scaleX:0}}, {{scaleX:1, duration:0.25, ease:"power2.out"}}, {B["giliran"] + 0.25:.3f});')
fout("#no1", seg_end("h3")); fout("#no2", seg_end("h3"))

# ---- step labels
STEPS = [("st1", "STEP 1", "Download MY alrajhi app", SEG["s1"]["start"], seg_end("s1")),
         ("st2", "STEP 2", "Daftar &amp; sahkan akaun", SEG["s2a"]["start"], seg_end("s2b")),
         ("st3", "STEP 3", "Top up minimum RM20", SEG["s3"]["start"], seg_end("s3")),
         ("st4", "STEP 4", "Aktifkan DuitPlus Savings Account-i", SEG["s4a"]["start"], seg_end("s4a")),
         ("st5", "STEP 5", "Ambil &amp; share referral code", SEG["s4b"]["start"], seg_end("s4b")),
         ("st6", "BONUS", "Simpanan masa depan", SEG["b1"]["start"], seg_end("b1"))]
for sid_, k, txt, a_, b_ in STEPS:
    ov(sid_, a_ + 0.15, b_, f'<span class="k">{k}</span><span class="t">{txt}</span>', "step", "left:56px;top:196px")
    fin(f"#{sid_}", a_ + 0.15, "left", 0.5); fout(f"#{sid_}", b_)

# ---- logo: once, when the app is first named
ov("logo", LOGO_T - 0.05, LOGO_T + 1.0, '<img src="assets/screen/alrajhi-mark.png" alt=""><div>MY alrajhi</div>', "logo",
   f"left:{PH_X + BEZ + SW / 2 - 120:.0f}px;top:{PH_Y + 40}px")
OJS.append(f'tl.fromTo("#logo", {{opacity:0, scale:0.5, filter:"blur(10px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", duration:0.45, ease:"back.out(1.6)"}}, {LOGO_T - 0.05:.3f});')
OJS.append(f'tl.to("#logo", {{opacity:0, scale:0.85, filter:"blur(8px)", duration:0.25, ease:"power2.in"}}, {LOGO_T + 0.72:.3f});')

# ---- cards in the face shots (top band, above the head)
ov("c-rm20", SEG["s3"]["start"] + 0.1, seg_end("s3"), '<div class="big">RM20</div><div class="sub">top up minimum<br>untuk aktifkan akaun</div>', "glass card row", "left:56px;top:300px")
fin("#c-rm20", SEG["s3"]["start"] + 0.1, "pop", 0.45); fout("#c-rm20", seg_end("s3"))
check = '<svg viewBox="0 0 24 24" width="54" height="54"><circle cx="12" cy="12" r="12" fill="#2EE6A6"/><path class="tick" d="M6.5 12.5l3.5 3.5 7.5-8" stroke="#0A0E2A" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
ov("c-aktif", B["aktif"] - 0.15, seg_end("s4a"), f'{check}<div><div class="sub">DuitPlus Savings Account-i</div><div class="big2">AKTIF</div></div>', "glass card row", "left:56px;top:300px")
fin("#c-aktif", B["aktif"] - 0.15, "pop", 0.45); fout("#c-aktif", seg_end("s4a"))
gift = ('<svg viewBox="0 0 48 48" width="70" height="70"><rect x="7" y="20" width="34" height="22" rx="4" fill="#5B54FF"/><rect x="4" y="13" width="40" height="9" rx="3" fill="#251CFC"/>'
        '<rect x="21" y="13" width="6" height="29" fill="#2EE6A6"/><path d="M24 13c-4-8-12-6-9 0M24 13c4-8 12-6 9 0" stroke="#2EE6A6" stroke-width="3" fill="none"/></svg>')
ov("c-gift", B["gift"] - 0.2, seg_end("r2"), f'{gift}{gift}<div><div class="big2">Dua-dua dapat<br>manis-manis</div><div class="tc">*T&amp;C applied</div></div>', "glass card row", "left:56px;top:200px")
fin("#c-gift", B["gift"] - 0.2, "pop", 0.5); fout("#c-gift", seg_end("r2"))
ov("c-akt2", B["aktifkan2"] - 0.2, seg_end("r2"), 'Selepas akaun <b>diaktifkan</b>', "chip mint", "left:56px;top:420px")
fin("#c-akt2", B["aktifkan2"] - 0.2, "pop", 0.4); fout("#c-akt2", seg_end("r2"))
shield = ('<svg viewBox="0 0 48 56" width="64" height="74"><path d="M24 2l20 8v16c0 14-9 24-20 28C13 50 4 40 4 26V10z" fill="#251CFC"/>'
          '<path d="M14 28l7 7 14-15" stroke="#2EE6A6" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ov("c-pidm", SEG["p1"]["start"] + 0.2, seg_end("p1"), f'{shield}<div><div class="sub">Duit korang selamat</div><div class="big2">Dilindungi PIDM</div></div>', "glass card row", "left:56px;top:200px")
fin("#c-pidm", SEG["p1"]["start"] + 0.2, "pop", 0.45); fout("#c-pidm", seg_end("p1"))
for i, (k, txt) in enumerate([("rumah", "Rumah"), ("kahwin", "Kahwin"), ("umrah", "Umrah")]):
    ov(f"g-{k}", B[k] - 0.1, seg_end("b1"), f'<span class="tickc">{check}</span>{txt}', "chip", f"left:{56 + i * 300}px;top:300px")
    fin(f"#g-{k}", B[k] - 0.1, "pop", 0.4); fout(f"#g-{k}", seg_end("b1"))
ov("c-tdi", B["tdi"] - 0.2, seg_end("t2") + 0.02,
   '<div class="tl"><div class="sub">TD-i Advantage Campaign</div><div class="pre">profit rate sehingga</div><div class="term" id="term">tempoh <b>12 bulan</b></div></div>'
   '<div class="num"><span id="ratenum">0.0</span>%</div><div class="tc">*Tertakluk pada T&amp;C. Rujuk website alrajhi bank Malaysia.</div>', "glass card tdi", "left:56px;top:196px;width:968px")
fin("#c-tdi", B["tdi"] - 0.2, "blur", 0.5); fout("#c-tdi", seg_end("t2") + 0.02)
OJS.append(f'const rc = {{v:0}}; tl.fromTo(rc, {{v:0}}, {{v:4, duration:0.9, ease:"power3.out", '
           f'onUpdate:function(){{ document.querySelector("#ratenum").textContent = rc.v.toFixed(1); }}}}, {B["rate"] - 0.7:.3f});')
fin("#term", B["rate"] + 0.3, "pop", 0.4)

# ---- the close
ov("jom", B["jom"] - 0.1, TOTAL, 'Jom <span class="hl">menabung!</span>', "glass jom", "left:60px;top:250px;width:960px")
fin("#jom", B["jom"] - 0.1, "pop", 0.5)

overlays = f"""<template>
  <style>
    #root {{ position:absolute; inset:0; pointer-events:none; font-family:{FONTS}; }}
    .ov {{ position:absolute; }}
    .glass {{ background:rgba(10,14,42,.88); border:2px solid rgba(255,255,255,.14); border-radius:34px; color:#fff;
             box-shadow:0 24px 60px rgba(0,0,0,.35); }}
    #hook .kicker {{ font:800 28px var(--f, {FONTS}); letter-spacing:.18em; color:#2EE6A6; margin-bottom:10px; }}
    #hook .head {{ font:900 70px/1.08 {FONTS}; letter-spacing:-.02em; color:#fff; }}
    #hook .hl {{ color:#2EE6A6; }}
    .chip {{ display:flex; align-items:center; gap:14px; padding:16px 28px 16px 18px; border-radius:999px; background:rgba(10,14,42,.82);
            color:#fff; font:800 36px {FONTS}; white-space:nowrap; border:2px solid rgba(255,255,255,.14); }}
    .chip s {{ position:absolute; left:74px; right:24px; top:50%; height:5px; background:#FF4D6D; transform-origin:left; border-radius:3px; }}
    .chip.mint {{ background:#2EE6A6; color:#0A0E2A; border-color:transparent; padding:16px 30px; }}
    .chip .tickc svg {{ width:44px; height:44px; }}
    .step {{ display:flex; align-items:center; gap:0; border-radius:20px; overflow:hidden; box-shadow:0 16px 40px rgba(0,0,0,.35); white-space:nowrap; }}
    .step .k {{ background:#251CFC; color:#fff; font:900 30px {FONTS}; letter-spacing:.08em; padding:18px 22px; }}
    .step .t {{ background:#fff; color:#0A0E2A; font:800 32px {FONTS}; padding:18px 26px; }}
    .card {{ padding:26px 34px; }}
    .row {{ display:flex; align-items:center; gap:22px; }}
    .card .big {{ font:900 92px/1 {FONTS}; color:#2EE6A6; letter-spacing:-.02em; }}
    .card .big2 {{ font:900 50px/1.05 {FONTS}; color:#fff; letter-spacing:-.01em; }}
    .card .sub {{ font:700 30px/1.25 {FONTS}; color:rgba(255,255,255,.75); }}
    .card .tc {{ font:600 28px {FONTS}; color:rgba(255,255,255,.82); margin-top:8px; }}
    .tdi {{ display:grid; grid-template-columns:1fr auto; align-items:center; column-gap:20px; }}
    .tdi .sub {{ color:#fff; font-weight:900; font-size:38px; }}
    .tdi .pre {{ font:700 30px/1.15 {FONTS}; color:rgba(255,255,255,.75); margin-top:6px; }}
    .tdi .num {{ font:900 150px/1 {FONTS}; color:#2EE6A6; letter-spacing:-.03em; }}
    .tdi .tc {{ grid-column:1 / span 2; }}
    .tdi .term {{ display:inline-block; margin-top:14px; font:700 32px {FONTS}; color:#0A0E2A; background:#fff; padding:10px 22px; border-radius:999px; }}
    .logo {{ width:240px; text-align:center; padding:26px 0 20px; border-radius:40px; background:#fff; box-shadow:0 30px 80px rgba(37,28,252,.45); }}
    .logo img {{ width:130px; height:auto; }}
    .logo div {{ margin-top:8px; font:900 34px {FONTS}; color:#251CFC; }}
    .jom {{ text-align:center; padding:34px 0; font:900 92px/1 {FONTS}; color:#fff; letter-spacing:-.02em; }}
    .jom .hl {{ color:#2EE6A6; }}
  </style>
  <div id="root" data-composition-id="overlays" data-width="{W}" data-height="{H}">
    {chr(10).join('    ' + o for o in OV).strip()}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join('    ' + j for j in OJS).strip()}
    window.__timelines["overlays"] = tl;
  </script>
</template>
"""
open(os.path.join(ROOT, "compositions", "overlays.html"), "w").write(overlays)

# ================================================================= captions.html
CG, CJS = [], []
FACE_CAP_Y = {"default": 470, "h2": 330, "h3": 330, "t1": 500, "t2": 500, "r1": 430, "r2": 520, "p1": 430, "s3": 540, "s4a": 470, "b1": 430}
for gi, g in enumerate(groups):
    g0 = g[0][0] - 0.06; g1 = g[-1][1] + 0.10
    if gi + 1 < len(groups):
        g1 = min(g1, groups[gi + 1][0][0] - 0.06)
    mode, sid = g[0][3], g[0][4]
    if mode == "demo":
        style = "left:560px;width:400px;top:600px;text-align:left"
        cls = "cg demo"
    else:
        style = f"left:0;width:{W}px;top:{FACE_CAP_Y.get(sid, FACE_CAP_Y['default'])}px;text-align:center"
        cls = "cg"
    words = " ".join(f'<span class="w" id="cw{gi}_{wi}">{esc(w[2])}</span>' for wi, w in enumerate(g))
    CG.append(f'<div id="cg{gi}" class="clip {cls}" data-start="{g0:.3f}" data-duration="{g1 - g0:.3f}" data-track-index="0" style="{style}"><span class="pill">{words}</span></div>')
    CJS.append(f'tl.fromTo("#cg{gi} .pill", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.14, ease:"power2.out"}}, {g0:.3f});')
    for wi, w in enumerate(g):
        CJS.append(f'tl.to("#cw{gi}_{wi}", {{color:"#2EE6A6", duration:0.06}}, {w[0]:.3f});')
    CJS.append(f'tl.to("#cg{gi} .pill", {{opacity:0, duration:0.08, ease:"power2.in"}}, {g1 - 0.09:.3f});')

captions = f"""<template>
  <style>
    #root {{ position:absolute; inset:0; pointer-events:none; }}
    .cg {{ position:absolute; overflow:visible; }}
    .pill {{ display:inline-block; padding:14px 28px 18px; border-radius:26px; background:rgba(10,14,42,.82);
            font:900 62px/1.12 {FONTS}; color:#fff; letter-spacing:-.01em; box-shadow:0 14px 40px rgba(0,0,0,.30); }}
    .cg.demo .pill {{ font-size:52px; padding:14px 24px 16px; }}
    .w {{ color:#fff; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">
    {chr(10).join('    ' + c for c in CG).strip()}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join('    ' + j for j in CJS).strip()}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""
open(os.path.join(ROOT, "compositions", "captions.html"), "w").write(captions)

json.dump(dict(total=TOTAL, segments=SEG, modes=modes, taps=TAPS, beats=B, groups=[" ".join(w[2] for w in g) for g in groups]),
          open(os.path.join(ROOT, "build", "timeline.json"), "w"), indent=1)
print(f"total {TOTAL}s, {len(groups)} caption groups, {len(TAPS)} taps, {len(SFX)} sfx, modes={[(m[0], m[1]) for m in modes]}")
