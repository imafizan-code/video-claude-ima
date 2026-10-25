"""MY alrajhi tutorial, styled after the reference creator video (v2).

python3 build/gen.py   (from the project root) -> index.html, compositions/overlays.html, compositions/captions.html
Look: full-frame talking head, ALL-CAPS heavy captions that build word by word at chest height
(keywords lime, numbers red), black pictogram stickers on the words, big stacked emphasis text,
hard jump cuts with alternating punch-ins, a full-screen cut to the screen recording for the
sign-up steps with hand-drawn red circles on the buttons, white screenshot cards for the code,
and a dimmed outro. Every graphic stays in the wall above the head or below the chin.
The v1 layout (phone + face card) is kept in build/gen_v1.py.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920

# ---------------------------------------------------------------- EDL  (id, clip, media_in, media_out, mode)
# mode: face = talking head, screen = full-screen cut to the screen recording
EDL = [
    ("h1", "0399", 0.00, 4.18, "face"),    # Kau tahu tak, sekarang ni kita boleh buka bank tanpa perlu pergi ke cawangan pun
    ("h2", "0399", 4.72, 7.30, "face"),    # tak perlu nak beratur, tak perlu nak ambil nombor giliran      ("So" cut)
    ("h3", "0399", 7.66, 8.56, "face"),    # Nak tahu macam mana?                                          ("Baik, saya tunjuk" cut)
    ("s1", "0408", 0.00, 4.02, "face"),    # Mula-mula korang download dulu app MY alrajhi bank dekat phone korang
    ("s2a", "0424", 0.00, 2.12, "screen"),  # Lepas itu, ikut arahan untuk pendaftaran,
    ("s2b", "0424", 2.44, 4.50, "screen"),  # isi maklumat pengesahan yang diperlukan
    ("s3", "0431", 0.10, 2.22, "face"),    # dan top up minimum RM20 je.
    ("s4a", "0484", 0.00, 3.80, "face"),   # Bila dah berjaya aktifkan DuitPlus Savings Account-i ni,
    ("s4b", "0484", 3.80, 8.86, "face"),   # korang akan dapat referral code dan bolehlah korang share dengan family dan kawan-kawan.
    ("r1a", "0494", 0.46, 1.90, "face"),   # Boleh guna referral code ini
    ("r1b", "0494", 2.13, 7.50, "face"),   # dan kedua-dua belah pihak akan dapat manis-manis RM10 selepas account berjaya diaktifkan.
    ("p1", "0529", 0.00, 3.48, "face"),    # dan duit korang pun selamat sebab dilindungi oleh PIDM.
    ("b1", "0503", 0.00, 4.48, "face"),    # lagi satu yang tengah simpan duit untuk beli rumah, kahwin atau pergi umrah
    ("t1a", "0518", 0.46, 4.36, "face"),   # alrajhi bank Malaysia menawarkan TD-i Advantage Campaign,
    ("t1b", "0518", 4.62, 8.62, "face"),   # di mana korang boleh dapatkan profit rate sehingga 4%
    ("t2", "0519", 0.14, 1.44, "face"),    # selama 12 bulan
    ("c1a", "0540", 0.86, 1.56, "face"),   # tunggu apa lagi,                                               ("So" cut)
    ("c1b", "0540", 1.86, 3.88, "face"),   # korang download je MY alrajhi app,
    ("c1c", "0540", 4.33, 7.24, "face"),   # aktifkan DuitPlus Savings Account-i dan
    ("c2", "0541", 0.08, 1.20, "face"),    # guna referral code ni
    ("e1", "0553", 0.60, 1.38, "face"),    # Jom nabung.
]
END_HOLD = 1.5

SEG = {}
t = 0.0
for sid, clip, a, b, mode in EDL:
    SEG[sid] = dict(id=sid, clip=clip, a=a, b=b, mode=mode, start=round(t, 3), dur=round(b - a, 3))
    t += b - a
TOTAL = round(t + END_HOLD, 3)


def at(sid, media_t):
    s = SEG[sid]
    return round(s["start"] + (media_t - s["a"]), 3)


def seg_end(sid):
    return round(SEG[sid]["start"] + SEG[sid]["dur"], 3)


# lowest point of the face in each clip (face detection) -> lift the frame so the chin clears the caption band
FACE_BOTTOM = {"0399": 1284, "0408": 1260, "0424": 1258, "0431": 1200, "0484": 1210, "0494": 1178, "0503": 1144,
               "0518": 1166, "0519": 1154, "0529": 1118, "0540": 1112, "0541": 1130, "0553": 1102}
CHIN_MAX = 1185

# ---------------------------------------------------------------- the full-screen cut to the screen recording
SX = (W - 888) // 2                               # recording drawn at its native 888x1920, centred
CUT_IN = at("s1", 2.92)                           # cut on "...bank dekat phone korang"
CUT_OUT = seg_end("s2b")
A_START = CUT_IN + 0.25                            # welcome still first, then the recording plays
A_DUR = 2.7                                        # media 0.0-2.7: Get started, New to alrajhi, declaration slides in
B_START, B_IN, B_OUT, B_RATE = A_START + A_DUR, 5.6, 7.0, 1.4      # tick the box, Next  (scrolling and loading skipped)
K_START = B_START + (B_OUT - B_IN) / B_RATE         # MyKad scan screen to the end of the step
SCREEN_ITEMS = [
    dict(id="sc-welcome", kind="img", src="assets/screen/welcome.png", start=CUT_IN, dur=A_START - CUT_IN),
    dict(id="sc-a", kind="video", src="assets/screen/register.mp4", start=A_START, dur=A_DUR, ms=0.0, rate=1),
    dict(id="sc-b", kind="video", src="assets/screen/register.mp4", start=B_START, dur=K_START - B_START, ms=B_IN, rate=B_RATE),
    dict(id="sc-mykad", kind="img", src="assets/screen/mykad.png", start=K_START, dur=CUT_OUT - K_START),
]


def rec_t(clip_start, media_in, rate, media_t):
    return round(clip_start + (media_t - media_in) / rate, 3)


# taps in recording px (888x1920): (time, x, y, ring_w, ring_h)
TAPS = [
    (rec_t(A_START, 0, 1, 0.65), 444, 1435, 760, 150),          # Get started now
    (rec_t(A_START, 0, 1, 1.80), 444, 1205, 800, 190),          # New to alrajhi bank Malaysia
    (rec_t(B_START, B_IN, B_RATE, 5.85), 81, 1285, 120, 120),   # acknowledge checkbox
    (rec_t(B_START, B_IN, B_RATE, 6.60), 444, 1738, 780, 140),  # Next
    (round(CUT_OUT - 0.4, 3), 444, 1734, 790, 140),             # Start verification process
]
ZOOMS = [  # (start, end, scale, cx, cy) in recording px
    (A_START - 0.05, A_START + 1.0, 1.35, 444, 1330),
    (B_START - 0.1, B_START + 0.85, 1.3, 444, 1480),
]

# ---------------------------------------------------------------- captions (ALL CAPS, build word by word)
FIX = {"jarahan": "arahan", "belia": "belah", "kawin": "kahwin", "dihendungi": "dilindungi", "kecawangan": "ke cawangan",
       "TDI": "TD-i"}
words_raw = json.load(open(os.path.join(ROOT, "build", "words.json")))


def clip_words(clip):
    out = []
    for w in words_raw["IMG_" + clip]:
        txt = w["w"].strip()
        if txt.startswith("-") and out:
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


def word_time(sid, word, nth=0):
    """Output time of a spoken word (case-insensitive prefix match) inside a kept segment."""
    s = SEG[sid]; hits = []
    for w in clip_words(s["clip"]):
        if s["a"] - 0.05 <= w["s"] <= s["b"] and w["w"].lower().strip(",.?!").startswith(word.lower()):
            hits.append(at(sid, max(w["s"], s["a"])))
    return hits[nth] if hits else SEG[sid]["start"]


CAP = []
for sid, clip, a, b, mode in EDL:
    if sid in ("h1", "e1"):
        continue                                   # big type carries the hook and the close
    for w in clip_words(clip):
        inside = min(w["e"], b) - max(w["s"], a)
        if inside >= min(0.12, (w["e"] - w["s"]) * 0.5):
            for part in w["w"].split(" "):
                CAP.append([at(sid, max(w["s"], a)), at(sid, min(w["e"], b)), part, sid])

groups, cur = [], []
for i, w in enumerate(CAP):
    cur.append(w)
    nxt = CAP[i + 1] if i + 1 < len(CAP) else None
    chars = sum(len(x[2]) + 1 for x in cur)
    crosses_cut = nxt is not None and any(w[0] < c <= nxt[0] + 0.05 for c in (CUT_IN, CUT_OUT))
    if (nxt is None or re.search(r"[,.?!]$", w[2]) or len(cur) >= 5 or chars > 24 or (nxt and nxt[0] - w[1] > 0.3) or crosses_cut):
        groups.append(cur); cur = []

LIME = {"my", "alrajhi", "duitplus", "savings", "account-i", "td-i", "advantage", "campaign", "referral", "code",
        "pidm", "manis-manis", "aktifkan", "diaktifkan", "download", "online"}


def tone(word):
    core = word.lower().strip(",.?!")
    if re.search(r"\d", core):
        return "red"
    return "lime" if core in LIME else ""


# ---------------------------------------------------------------- helpers
def clip_attrs(start, dur, track):
    return f'class="clip" data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="{track}"'


FONT = "'Montserrat', 'Inter', sans-serif"

# ================================================================= index.html
face_media = []
for sid, clip, a, b, mode in EDL:
    if mode != "face":
        continue
    s = SEG[sid]
    face_media.append(
        f'<video id="v-{sid}" {clip_attrs(s["start"], s["dur"], 1)} src="assets/face/f{clip}.mp4" data-media-start="{a:.3f}" '
        f'data-has-audio="true" data-volume="1" playsinline style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover"></video>')
face_media.append(f'<img id="v-hold" {clip_attrs(seg_end("e1"), END_HOLD, 1)} src="assets/face/hold.jpg" '
                  f'style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover" alt="">')

# the voice keeps playing under the screen recording: those takes play as audio only
voice_only = []
for sid, clip, a, b, mode in EDL:
    if mode == "screen":
        s = SEG[sid]
        voice_only.append(f'<audio id="vo-{sid}" {clip_attrs(s["start"], s["dur"], 2)} src="assets/face/f{clip}.mp4" '
                          f'data-media-start="{a:.3f}" data-volume="1"></audio>')

screen_media, screen_bg = [], []
for it in SCREEN_ITEMS:
    for layer, out, style in (("bg", screen_bg, f"position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover"),
                              ("fg", screen_media, f"position:absolute;left:0;top:0;width:888px;height:{H}px;object-fit:fill")):
        iid = it["id"] + ("-bg" if layer == "bg" else "")
        cls = "scr-bg" if layer == "bg" else "scr-fg"
        if it["kind"] == "img":
            out.append(f'<img id="{iid}" {clip_attrs(it["start"], it["dur"], 3 if layer == "fg" else 4)} src="{it["src"]}" style="{style}" alt="" data-cls="{cls}">')
        else:
            out.append(f'<video id="{iid}" {clip_attrs(it["start"], it["dur"], 3 if layer == "fg" else 4)} src="{it["src"]}" muted playsinline '
                       f'data-media-start="{it["ms"]:.3f}" data-playback-rate="{it["rate"]}" style="{style}" data-cls="{cls}"></video>')

marks = []
for i, (tt, x, y, rw, rh) in enumerate(TAPS):
    marks.append(f'<div class="ripple" id="rp{i}" style="left:{x - 60}px;top:{y - 60}px"><i></i><b></b></div>')
    marks.append(f'<svg class="ring" id="rg{i}" viewBox="0 0 {rw + 40} {rh + 40}" style="left:{x - rw / 2 - 20:.0f}px;top:{y - rh / 2 - 20:.0f}px;width:{rw + 40}px;height:{rh + 40}px">'
                 f'<path d="M{rw * 0.08 + 20:.0f} {rh * 0.35 + 20:.0f} C {rw * 0.02:.0f} {rh * 1.05 + 20:.0f}, {rw * 0.95 + 20:.0f} {rh * 1.12 + 20:.0f}, {rw + 25:.0f} {rh * 0.48 + 20:.0f} '
                 f'C {rw * 1.03 + 20:.0f} {rh * -0.12 + 20:.0f}, {rw * 0.15 + 20:.0f} {rh * -0.18 + 20:.0f}, {rw * 0.12 + 20:.0f} {rh * 0.55 + 20:.0f}" pathLength="100"/></svg>')

# ---- audio
SFX = []   # (id, file, time, volume)
for i, (tt, *_r) in enumerate(TAPS):
    SFX.append((f"sx-tap{i}", "click-soft", tt + 0.033, 0.5 if i % 2 else 0.42))
SFX.append(("sx-cutin", "whoosh-short", CUT_IN - 0.05, 0.26))
SFX.append(("sx-cutout", "whoosh-short", CUT_OUT - 0.05, 0.2))

js = []
# punch-ins: lift every take so the chin clears the captions, alternate the push on each cut
pi = 0
for sid, clip, a, b, mode in EDL:
    if mode != "face":
        continue
    base = [1.0, 1.1][pi % 2]; pi += 1
    fb = FACE_BOTTOM[clip]
    sc = base if fb * base <= CHIN_MAX else max(base, (H - CHIN_MAX) / (H - fb))   # lift the chin, keep the frame covered
    y = min(0.0, CHIN_MAX - fb * sc)
    js.append(f'tl.set("#punch", {{scale:{sc:.3f}, y:{y:.0f}, transformOrigin:"540px 0px"}}, {SEG[sid]["start"]:.3f});')
js.append(f'tl.set("#punch", {{scale:1.08, y:0}}, {seg_end("e1"):.3f});')

# the cut to the recording: hard cut with a small settle, hard cut back
js.append(f'tl.set("#screen", {{opacity:1}}, {CUT_IN:.3f});')
js.append(f'tl.fromTo("#scr-fit", {{scale:1.0, transformOrigin:"444px 1920px"}}, {{scale:0.92, duration:0.3, ease:"power3.out"}}, {CUT_IN:.3f});')
js.append(f'tl.set("#screen", {{opacity:0}}, {CUT_OUT:.3f});')
for z0, z1, sc, cx, cy in ZOOMS:
    x = min(0, max(888 - 888 * sc, 444 - cx * sc)); y = min(0, max(H - H * sc, H / 2 - cy * sc))
    js.append(f'tl.to("#zoom", {{scale:{sc}, x:{x:.0f}, y:{y:.0f}, duration:0.45, ease:"power2.inOut"}}, {z0:.3f});')
    js.append(f'tl.to("#zoom", {{scale:1, x:0, y:0, duration:0.4, ease:"power2.inOut"}}, {max(z0 + 0.5, z1 - 0.4):.3f});')
js.append('tl.set("#zoom", {scale:1, x:0, y:0, transformOrigin:"0px 0px"}, 0);')
for i, (tt, *_r) in enumerate(TAPS):
    js.append(f'tl.fromTo("#rg{i} path", {{strokeDashoffset:100}}, {{strokeDashoffset:0, duration:0.3, ease:"power2.out"}}, {tt - 0.35:.3f});')
    js.append(f'tl.to("#rg{i}", {{opacity:0, duration:0.15}}, {tt + 0.45:.3f});')
    js.append(f'tl.fromTo("#rp{i} i", {{scale:0.2, opacity:0.55}}, {{scale:1.6, opacity:0, duration:0.5, ease:"power2.out"}}, {tt:.3f});')
    js.append(f'tl.fromTo("#rp{i} b", {{scale:1.25, opacity:0}}, {{scale:0.85, opacity:0.95, duration:0.1, ease:"power2.out"}}, {tt - 0.1:.3f});')
    js.append(f'tl.to("#rp{i} b", {{scale:1, opacity:0, duration:0.22, ease:"power2.in"}}, {tt + 0.08:.3f});')

# outro: the frame dims under the closing line
js.append(f'tl.fromTo("#dim", {{opacity:0}}, {{opacity:0.62, duration:0.4, ease:"power2.out"}}, {SEG["e1"]["start"] + 0.2:.3f});')

# ================================================================= overlays (stickers, big type, cards, step tags)
OV, OJS = [], []
ICON = {
    "bank": '<path d="M12 2 2 7v2h20V7z"/><path d="M4 10h3v8H4zm6.5 0h3v8h-3zM17 10h3v8h-3z"/><path d="M2 19h20v3H2z"/>',
    "queue": '<circle cx="4.5" cy="6" r="2"/><circle cx="12" cy="6" r="2"/><circle cx="19.5" cy="6" r="2"/>'
             '<path d="M2 21v-8a2.5 2.5 0 0 1 5 0v8zm7.5 0v-8a2.5 2.5 0 0 1 5 0v8zm7.5 0v-8a2.5 2.5 0 0 1 5 0v8z"/>',
    "ticket": '<path d="M2 6h20v4a2 2 0 0 0 0 4v4H2v-4a2 2 0 0 0 0-4z"/><text x="12" y="15" text-anchor="middle" font-size="6.5" font-weight="900" fill="#fff" stroke="none">A12</text>',
    "download": '<path d="M10 2h4v9h4l-6 7-6-7h4z"/><path d="M3 19h18v3H3z"/>',
    "wallet": '<path d="M3 6a2 2 0 0 1 2-2h13v3H5v.01H20a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H5a2 2 0 0 1-2-2z"/><circle cx="17" cy="13.5" r="1.6" fill="#fff" stroke="none"/>',
    "toggle": '<rect x="1.5" y="6" width="21" height="12" rx="6"/><circle cx="16.5" cy="12" r="4.2" fill="#2BE38B" stroke="none"/>',
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8 11 8-4.5.9 1.7-8 4.5zm0 2 8 4.5.9-1.7-8-4.5z"/>',
    "people": '<circle cx="8" cy="7" r="3"/><circle cx="16.5" cy="8" r="2.5"/><path d="M2 20c0-4 2.7-6.5 6-6.5s6 2.5 6 6.5zm12.5 0c0-2.6-.7-4.5-2-5.8 1.2-.6 2.6-.8 4-.8 2.8 0 5 2.2 5 6.6z"/>',
    "gift": '<path d="M3 9h18v4H3zm1.5 5h15v8h-15z"/><path d="M11 9h2v13h-2z" fill="#fff" stroke="none"/><path d="M12 9C9 3 5 5 7 8.5M12 9c3-6 7-4 5-.5"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m7 12.5 3.2 3.2L17 9" fill="none" stroke="#2BE38B" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>',
    "shield": '<path d="M12 2 20 5v6c0 5.5-3.4 9.6-8 11-4.6-1.4-8-5.5-8-11V5z"/><path d="m8 12 3 3 5.5-6" fill="none" stroke="#2BE38B" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>',
    "house": '<path d="M12 3 2 11.5h3V21h5.5v-6h3v6H19v-9.5h3z"/>',
    "rings": '<circle cx="9" cy="14" r="5.5" fill="none" stroke-width="2.6"/><circle cx="15" cy="14" r="5.5" fill="none" stroke-width="2.6"/><path d="m8.2 5 1.8-2.5h4L15.8 5 12 8.6z"/>',
    "plane": '<path d="M21 15.5v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V8.5l-8 5v2l8-2.5V18l-2 1.5V21l3.5-1 3.5 1v-1.5l-2-1.5v-5z"/>',
    "calendar": '<path d="M3 5h18v16H3z"/><path d="M3 5h18v4H3z" fill="#FF3B30" stroke="none"/><path d="M7 2.5h2v4H7zm8 0h2v4h-2z"/>'
                '<text x="12" y="18.6" text-anchor="middle" font-size="8" font-weight="900" fill="#fff" stroke="none">12</text>',
    "hourglass": '<path d="M5 2h14v3c0 3-3 5.2-4.6 7C16 13.8 19 16 19 19v3H5v-3c0-3 3-5.2 4.6-7C8 10.2 5 8 5 5z"/>',
    "piggy": '<path d="M4 11c0-3.9 3.6-7 8-7 1.6 0 3 .4 4.3 1l2.7-1.5V7c1 .9 1.7 2 2 3.2h1v4h-1.5c-.6 1.2-1.6 2.3-2.8 3V21h-3v-2.4c-.6.1-1.2.1-1.7.1s-1.1 0-1.7-.1V21h-3v-3.8C5.4 15.9 4 13.6 4 11z"/>'
             '<circle cx="16.5" cy="9.5" r="1" fill="#fff" stroke="none"/><path d="M10 4.3h4" stroke="#fff" stroke-width="1.6"/>',
}
SLOT_X = {"L": 70, "C": 430, "R": 790}


def sticker(id_, icon, slot, t0, t1, y=300, size=210, cross=False, label=None):
    x = SLOT_X[slot] + (220 - size) // 2
    extra = '<svg class="x" viewBox="0 0 24 24"><path d="M4 4 20 20M20 4 4 20"/></svg>' if cross else ""
    lab = f'<div class="lab">{label}</div>' if label else ""
    OV.append(f'<div id="{id_}" class="clip st" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{len(OV) % 4}" '
              f'style="left:{x}px;top:{y}px;width:{size}px"><svg class="ic" viewBox="0 0 24 24">{ICON[icon]}</svg>{extra}{lab}</div>')
    OJS.append(f'tl.fromTo("#{id_} .ic", {{scale:0.3, rotation:-12, opacity:0}}, {{scale:1, rotation:0, opacity:1, duration:0.35, ease:"back.out(2.2)"}}, {t0:.3f});')
    if cross:
        OJS.append(f'tl.fromTo("#{id_} .x path", {{strokeDashoffset:30}}, {{strokeDashoffset:0, duration:0.22, ease:"power2.out"}}, {t0 + 0.3:.3f});')
    if label:
        OJS.append(f'tl.fromTo("#{id_} .lab", {{opacity:0, y:10}}, {{opacity:1, y:0, duration:0.2, ease:"power2.out"}}, {t0 + 0.15:.3f});')
    OJS.append(f'tl.to("#{id_}", {{opacity:0, scale:0.9, duration:0.14, ease:"power2.in"}}, {t1 - 0.16:.3f});')
    SFX.append((f"sx-{id_}", "pop", t0 + 0.06, 0.24))


def bigtext(id_, lines, t0, t1, top=230, size=96, word_times=None, slam=(), box=()):
    """Stacked emphasis type. lines = [[(word, tone), ...], ...]; words pop in on word_times (else all at t0)."""
    spans, k = [], 0
    for line in lines:
        ws = []
        for wtxt, tn in line:
            ws.append(f'<span class="bw {tn}{" box" if k in box else ""}" id="{id_}-w{k}">{wtxt}</span>'); k += 1
        spans.append(" ".join(ws))
    OV.append(f'<div id="{id_}" class="clip big" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{len(OV) % 4}" '
              f'style="top:{top}px;font-size:{size}px">{"<br>".join(spans)}</div>')
    for i in range(k):
        wt = word_times[i] if word_times else t0
        if wt <= 0.001:
            continue                                          # on screen from frame 0: the hook is already there
        if i in slam:                                         # lands like a hit: huge and blurred to its place
            rot = -3 if i in box else 0
            OJS.append(f'tl.fromTo("#{id_}-w{i}", {{scale:2.8, opacity:0, rotation:{rot}, filter:"blur(12px)"}}, '
                       f'{{scale:1, opacity:1, rotation:{rot}, filter:"blur(0px)", duration:0.2, ease:"back.out(1.6)"}}, {wt - 0.06:.3f});')
        else:
            OJS.append(f'tl.fromTo("#{id_}-w{i}", {{scale:1.35, opacity:0}}, {{scale:1, opacity:1, duration:0.16, ease:"power3.out"}}, {wt:.3f});')
    OJS.append(f'tl.to("#{id_}", {{opacity:0, duration:0.12, ease:"power2.in"}}, {t1 - 0.14:.3f});')


def card(id_, html, t0, t1, top=250, width=880):
    OV.append(f'<div id="{id_}" class="clip card" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{len(OV) % 4}" '
              f'style="left:{(W - width) // 2}px;top:{top}px;width:{width}px">{html}</div>')
    OJS.append(f'tl.fromTo("#{id_}", {{y:-40, opacity:0, scale:0.96}}, {{y:0, opacity:1, scale:1, duration:0.3, ease:"back.out(1.6)"}}, {t0:.3f});')
    OJS.append(f'tl.to("#{id_}", {{opacity:0, y:-20, duration:0.16, ease:"power2.in"}}, {t1 - 0.18:.3f});')
    SFX.append((f"sx-{id_}", "whoosh-short", t0 - 0.02, 0.18))


def tag(id_, text, t0, t1):
    OV.append(f'<div id="{id_}" class="clip tag" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{len(OV) % 4}">{text}</div>')
    OJS.append(f'tl.fromTo("#{id_}", {{x:-50, opacity:0}}, {{x:0, opacity:1, duration:0.25, ease:"power3.out"}}, {t0:.3f});')
    OJS.append(f'tl.to("#{id_}", {{opacity:0, duration:0.12}}, {t1 - 0.14:.3f});')


wt = word_time
# hook: the opening line is already on screen at frame 0, the rest lands with the voice
bigtext("hook", [[("BUKA", ""), ("AKAUN", ""), ("BANK", "lime")], [("TANPA", ""), ("PERGI", ""), ("CAWANGAN?", "lime")]],
        0, seg_end("h1"), top=220, size=90,
        word_times=[0, 0, 0, wt("h1", "tanpa"), wt("h1", "pergi"), wt("h1", "ke c")], slam=(3, 4, 5), box=(3,))
sticker("st-queue", "queue", "L", wt("h2", "beratur") - 0.05, seg_end("h2"), cross=True)
sticker("st-ticket", "ticket", "R", wt("h2", "giliran") - 0.15, seg_end("h2"), cross=True)
bigtext("how", [[("NAK", ""), ("TAHU", ""), ("MACAM", "")], [("MANA?", "lime")]], SEG["h3"]["start"], seg_end("h3"), top=230, size=96,
        word_times=[wt("h3", "nak"), wt("h3", "tahu"), wt("h3", "macam"), wt("h3", "mana")])

tag("tg1", "STEP 1 · DOWNLOAD APP", SEG["s1"]["start"] + 0.1, SEG["s2a"]["start"])
sticker("st-dl", "download", "L", wt("s1", "download") - 0.05, CUT_IN, y=290)
LOGO_T = wt("s1", "MY")
OV.append(f'<div id="logo" class="clip logo" data-start="{LOGO_T - 0.05:.3f}" data-duration="{CUT_IN - LOGO_T + 0.05:.3f}" data-track-index="3">'
          f'<img src="assets/screen/alrajhi-mark.png" alt=""><div>MY alrajhi</div></div>')
OJS.append(f'tl.fromTo("#logo", {{scale:0.4, opacity:0, rotation:8}}, {{scale:1, opacity:1, rotation:0, duration:0.4, ease:"back.out(2)"}}, {LOGO_T - 0.05:.3f});')
SFX.append(("sx-logo", "sparkle", LOGO_T, 0.32))
tag("tg2", "STEP 2 · DAFTAR &amp; SAHKAN", SEG["s2a"]["start"], CUT_OUT)

tag("tg3", "STEP 3 · TOP UP", SEG["s3"]["start"] + 0.05, seg_end("s3"))
sticker("st-wallet", "wallet", "L", SEG["s3"]["start"] + 0.2, seg_end("s3"), y=300)
bigtext("rm20", [[("MIN.", "")], [("RM20", "red")]], wt("s3", "minimum") - 0.05, seg_end("s3"), top=290, size=110)
OV[-1] = OV[-1].replace('class="clip big"', 'class="clip big right"')

tag("tg4", "STEP 4 · AKTIFKAN AKAUN", SEG["s4a"]["start"] + 0.05, seg_end("s4a"))
sticker("st-toggle", "toggle", "C", wt("s4a", "aktifkan") - 0.05, seg_end("s4a"), y=300, size=240)
SFX.append(("sx-on", "chime", wt("s4a", "aktifkan") + 0.15, 0.24))

tag("tg5", "STEP 5 · SHARE REFERRAL CODE", SEG["s4b"]["start"] + 0.05, seg_end("s4b"))
REF_T = wt("s4b", "referral")
card("ref-card", '<img src="assets/screen/referral-code.png" alt="" style="width:100%;display:block">'
                 '<svg class="ring2" viewBox="0 0 900 200"><path pathLength="100" d="M60 70 C 30 190, 820 200, 870 100 C 900 10, 120 -10, 90 110"/></svg>',
     REF_T - 0.1, wt("s4b", "share") - 0.05, top=280, width=860)
OJS.append(f'tl.fromTo("#ref-card .ring2 path", {{strokeDashoffset:100}}, {{strokeDashoffset:0, duration:0.35, ease:"power2.out"}}, {wt("s4b", "code") + 0.1:.3f});')
sticker("st-share", "share", "L", wt("s4b", "share") - 0.05, seg_end("s4b"))
sticker("st-fam", "people", "C", wt("s4b", "family") - 0.05, seg_end("s4b"), label="FAMILY")
sticker("st-kwn", "people", "R", wt("s4b", "kawan") - 0.05, seg_end("s4b"), label="KAWAN-KAWAN")

sticker("st-gift", "gift", "L", wt("r1b", "manis") - 0.1, seg_end("r1b"), y=300)
bigtext("manis", [[("DUA-DUA", "")], [("DAPAT", "")], [("MANIS-MANIS", "lime")], [("RM10", "red")]], wt("r1b", "kedua") - 0.05, wt("r1b", "diaktifkan"),
        top=210, size=78, word_times=[wt("r1b", "kedua"), wt("r1b", "dapat"), wt("r1b", "manis"), wt("r1b", "RM10")], slam=(3,))
OV[-1] = OV[-1].replace('class="clip big"', 'class="clip big right"')
OV.append(f'<div id="tnc" class="clip tnc" style="top:548px;left:330px;right:30px" data-start="{wt("r1b", "manis"):.3f}" data-duration="{seg_end("r1b") - wt("r1b", "manis"):.3f}" data-track-index="2">*T&amp;C APPLIED</div>')
sticker("st-ok", "check", "C", wt("r1b", "diaktifkan") - 0.1, seg_end("r1b"), y=270, size=230)

sticker("st-shield", "shield", "L", wt("p1", "selamat") - 0.05, seg_end("p1"), y=290, size=230)
bigtext("pidm", [[("DILINDUNGI", "")], [("PIDM", "lime")]], wt("p1", "dilindungi") - 0.05, seg_end("p1"), top=300, size=96,
        word_times=[wt("p1", "dilindungi"), wt("p1", "PIDM")])
OV[-1] = OV[-1].replace('class="clip big"', 'class="clip big right"')

tag("tgb", "BONUS · SIMPANAN", SEG["b1"]["start"] + 0.05, seg_end("b1"))
sticker("st-house", "house", "L", wt("b1", "rumah") - 0.1, seg_end("b1"), label="RUMAH")
sticker("st-rings", "rings", "C", wt("b1", "kahwin") - 0.1, seg_end("b1"), label="KAHWIN")
sticker("st-plane", "plane", "R", wt("b1", "umrah") - 0.1, seg_end("b1"), label="UMRAH")

bigtext("tdi", [[("TD-I", "lime"), ("ADVANTAGE", "lime")], [("CAMPAIGN", "lime")]], wt("t1a", "TD") - 0.05, seg_end("t1a"),
        top=250, size=92, word_times=[wt("t1a", "TD"), wt("t1a", "Advantage"), wt("t1a", "Campaign")])
RATE_T = wt("t1b", "4")
bigtext("rate", [[("SEHINGGA", "")], [("4%", "red")]], wt("t1b", "sehingga") - 0.05, seg_end("t2"), top=220, size=104,
        word_times=[wt("t1b", "sehingga"), RATE_T], slam=(1,))
OV[-1] = OV[-1].replace('class="clip big"', 'class="clip big right"').replace('>4%<', ' style="font-size:150px">4%<')
SFX.append(("sx-rate", "ping", RATE_T + 0.05, 0.3))
sticker("st-cal", "calendar", "L", wt("t2", "12") - 0.1, seg_end("t2"), y=280, size=230, label="12 BULAN")
OV.append(f'<div id="tnc2" class="clip tnc" style="top:500px;left:300px;right:20px;font-size:24px" data-start="{wt("t1a", "TD"):.3f}" data-duration="{seg_end("t2") - wt("t1a", "TD"):.3f}" data-track-index="2">*TERTAKLUK PADA T&amp;C · RUJUK WEBSITE ALRAJHI BANK MALAYSIA</div>')

sticker("st-wait", "hourglass", "C", SEG["c1a"]["start"] + 0.05, seg_end("c1a"), y=280, size=220)
sticker("st-dl2", "download", "L", wt("c1b", "download") - 0.05, seg_end("c1b"), y=290)
sticker("st-toggle2", "toggle", "C", wt("c1c", "aktifkan") - 0.05, seg_end("c1c"), y=300, size=240)
card("code-card", '<div class="lbl">Referral code</div><div class="field"><span>MYA04620NHH</span>'
                  '<svg viewBox="0 0 24 24" fill="none" stroke="#2A4BFF" stroke-width="2"><rect x="8" y="8" width="12" height="12" rx="3"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg></div>'
                  '<div class="hint">CODE AKU DALAM CAPTION ↓</div>',
     SEG["c2"]["start"] - 0.35, seg_end("c2") + 0.3, top=270, width=820)

sticker("st-piggy", "piggy", "C", SEG["e1"]["start"] + 0.1, TOTAL, y=250, size=250)
bigtext("jom", [[("JOM", "")], [("MENABUNG!", "lime")]], SEG["e1"]["start"] + 0.15, TOTAL, top=560, size=120,
        word_times=[SEG["e1"]["start"] + 0.2, SEG["e1"]["start"] + 0.5], slam=(0, 1))
OJS.append(f'tl.set("#jom", {{opacity:1}}, {TOTAL - 0.2:.3f});')

overlays = f"""<template>
  <style>
    #root {{ position:absolute; inset:0; pointer-events:none; font-family:{FONT}; }}
    .st {{ position:absolute; text-align:center; }}
    .st .ic {{ width:100%; height:auto; overflow:visible; fill:#111; stroke:#fff; stroke-width:1.3; stroke-linejoin:round; paint-order:stroke fill;
               filter: drop-shadow(0 8px 14px rgba(0,0,0,.35)); }}
    .st .x {{ position:absolute; left:6%; top:6%; width:88%; height:auto; overflow:visible; }}
    .st .x path {{ fill:none; stroke:#FF3B30; stroke-width:3.2; stroke-linecap:round; stroke-dasharray:30; }}
    .st .lab {{ margin-top:6px; font:900 34px {FONT}; color:#fff; -webkit-text-stroke:9px #111; paint-order:stroke fill; letter-spacing:.01em; }}
    .big {{ position:absolute; left:40px; right:40px; text-align:center; font-family:{FONT}; font-weight:900; line-height:1.0; color:#fff;
            -webkit-text-stroke:14px #111; paint-order:stroke fill; letter-spacing:-.01em; filter: drop-shadow(0 8px 16px rgba(0,0,0,.35)); }}
    .big.right {{ left:330px; right:30px; }}
    .bw {{ display:inline-block; }}
    .bw.box {{ background:#FF3B30; color:#fff; -webkit-text-stroke:0; padding:2px 18px 8px; border-radius:14px; border:7px solid #111; margin-right:6px; }}
    .lime {{ color:#E8FF3A; }}
    .red {{ color:#FF3B30; }}
    .tag {{ position:absolute; left:40px; top:196px; padding:12px 22px; border-radius:14px; background:#111; color:#fff; font:900 30px {FONT};
            letter-spacing:.04em; border:3px solid #fff; box-shadow:0 8px 20px rgba(0,0,0,.3); white-space:nowrap; }}
    .logo {{ position:absolute; left:780px; top:270px; width:240px; padding:26px 0 18px; border-radius:36px; background:#fff; text-align:center;
             border:5px solid #111; box-shadow:0 14px 30px rgba(0,0,0,.35); }}
    .logo img {{ width:130px; }}
    .logo div {{ font:900 34px {FONT}; color:#251CFC; margin-top:6px; }}
    .card {{ position:absolute; background:#fff; border-radius:28px; overflow:visible; box-shadow:0 22px 50px rgba(0,0,0,.35); padding:0; }}
    .card .ring2 {{ position:absolute; left:-10px; right:-10px; bottom:-14px; height:62%; width:calc(100% + 20px); overflow:visible; }}
    .card .ring2 path {{ fill:none; stroke:#FF3B30; stroke-width:9; stroke-linecap:round; stroke-dasharray:100; }}
    #code-card {{ padding:34px 40px 30px; }}
    #code-card .lbl {{ font:600 36px 'Inter', sans-serif; color:#6B6F80; }}
    #code-card .field {{ margin-top:16px; display:flex; justify-content:space-between; align-items:center; padding:26px 30px; border:3px solid #E3E5EE;
                         border-radius:22px; font:600 58px 'Inter', sans-serif; color:#16181F; letter-spacing:.02em; }}
    #code-card .field svg {{ width:60px; height:60px; }}
    #code-card .hint {{ margin-top:18px; font:900 34px {FONT}; color:#FF3B30; text-align:center; }}
    .tnc {{ position:absolute; left:0; right:0; top:1150px; text-align:center; font:800 28px {FONT}; color:#fff; -webkit-text-stroke:7px #111; paint-order:stroke fill; }}
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

# ================================================================= captions
CG, CJS = [], []
for gi, g in enumerate(groups):
    g0 = g[0][0] - 0.04; g1 = g[-1][1] + 0.18
    if gi + 1 < len(groups):
        g1 = min(g1, groups[gi + 1][0][0] - 0.04)
    words = " ".join(f'<span class="w {tone(w[2])}" id="cw{gi}_{wi}">{w[2].upper()}</span>' for wi, w in enumerate(g))
    w0 = g[0][0]
    if w0 >= CUT_OUT - 0.001:
        g0 = max(g0, CUT_OUT)                    # a line after the cut back never starts on the recording
    top = " top" if CUT_IN - 0.001 <= w0 < CUT_OUT - 0.001 else ""
    CG.append(f'<div id="cg{gi}" class="clip cg{top}" data-start="{g0:.3f}" data-duration="{g1 - g0:.3f}" data-track-index="0"><div class="ln">{words}</div></div>')
    for wi, w in enumerate(g):
        CJS.append(f'tl.fromTo("#cw{gi}_{wi}", {{opacity:0, y:12, scale:1.15}}, {{opacity:1, y:0, scale:1, duration:0.1, ease:"power2.out"}}, {max(g0, w[0] - 0.03):.3f});')
    CJS.append(f'tl.to("#cg{gi} .ln", {{opacity:0, duration:0.06}}, {g1 - 0.07:.3f});')

captions = f"""<template>
  <style>
    #root {{ position:absolute; inset:0; pointer-events:none; }}
    .cg {{ position:absolute; left:50px; right:50px; top:1188px; height:150px; display:flex; align-items:flex-end; justify-content:center; overflow:visible; }}
    .cg.top {{ top:250px; align-items:flex-start; }}
    .ln {{ text-align:center; font:900 64px/1.08 {FONT}; color:#fff; letter-spacing:-.005em; -webkit-text-stroke:11px #111; paint-order:stroke fill;
           filter: drop-shadow(0 6px 10px rgba(0,0,0,.35)); }}
    .w {{ display:inline-block; }}
    .lime {{ color:#E8FF3A; }}
    .red {{ color:#FF3B30; }}
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

# ---- hits: a short camera shake, a zoom bump and a white pop on the face plate, with an impact
SHAKE = [(1, -0.6, 1), (-0.85, 0.9, -1), (0.6, -0.5, 0.6), (-0.35, 0.3, -0.4), (0.15, -0.12, 0.2), (0, 0, 0)]
FLASH_N = [0]


def hit(t0, amp=16, zoom=1.08, flash=0.45, sfx=("impact-bass-2", 0.32)):
    for i, (dx, dy, dr) in enumerate(SHAKE):
        js.append(f'tl.to("#facewrap", {{x:{dx * amp:.1f}, y:{dy * amp * 0.6:.1f}, rotation:{dr * amp / 14:.2f}, duration:0.045, ease:"none"}}, {t0 + i * 0.045:.3f});')
    if zoom:
        js.append(f'tl.to("#facewrap", {{scale:{zoom}, duration:0.06, ease:"power2.out"}}, {t0:.3f});')
        js.append(f'tl.to("#facewrap", {{scale:1, duration:0.38, ease:"power3.out"}}, {t0 + 0.06:.3f});')
    if flash:
        js.append(f'tl.set("#pop", {{opacity:{flash}}}, {t0:.3f});')
        js.append(f'tl.to("#pop", {{opacity:0, duration:0.22, ease:"power2.out"}}, {t0 + 0.01:.3f});')
    if sfx:
        SFX.append((f"sx-hit{len(SFX)}", sfx[0], t0 - 0.01, sfx[1]))


js.append('tl.set("#facewrap", {transformOrigin:"540px 900px"}, 0);')
HOOK_T = wt("h1", "tanpa")
hit(HOOK_T, amp=24, zoom=1.14, flash=0, sfx=("impact-bass-1", 0.42))          # the registry flash carries this one
hit(wt("h1", "ke c"), amp=16, zoom=1.07, flash=0.35, sfx=("impact-bass-2", 0.3))
hit(wt("r1b", "RM10"), amp=14, zoom=1.06, flash=0.35)
hit(RATE_T, amp=14, zoom=1.06, flash=0.35, sfx=("impact-bass-2", 0.26))
hit(SEG["e1"]["start"] + 0.5, amp=12, zoom=1.05, flash=0.3)
js.append(f'tl.set("#pop", {{opacity:0.75}}, {CUT_IN:.3f}); tl.to("#pop", {{opacity:0, duration:0.2, ease:"power2.out"}}, {CUT_IN + 0.01:.3f});')
FLASH_D = 0.6
FLASH_START = HOOK_T - FLASH_D * 0.58                                           # the block peaks at 58% of its slot
SFX.append(("sx-hook-wh", "whoosh-short", HOOK_T - 0.3, 0.22))

# ---- audio tags (after the overlays added their own sounds)
DUR = {"click-soft": 0.366, "whoosh-short": 0.575, "sparkle": 1.8, "pop": 0.72, "chime": 2.5, "ping": 1.32,
       "impact-bass-1": 2.12, "impact-bass-2": 2.59}
audio = [f'<audio id="music" class="clip" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="8" src="assets/music/bed.mp3" '
         f'data-media-start="10" data-volume="0.12" data-fade-in="0.4" data-fade-out="1.4"></audio>']
lane_free = []                                       # first-fit lanes so no two sounds share a track while playing
for i, (aid, f, tt, vol) in enumerate(sorted(SFX, key=lambda x: x[2])):
    d = min(DUR[f], TOTAL - tt - 0.01)
    lane = next((k for k, free in enumerate(lane_free) if free <= tt), None)
    if lane is None:
        lane_free.append(0); lane = len(lane_free) - 1
    lane_free[lane] = tt + d
    audio.append(f'<audio id="{aid}" class="clip" data-start="{tt:.3f}" data-duration="{d:.3f}" data-track-index="{9 + lane}" '
                 f'src="assets/sfx/{f}.mp3" data-volume="{vol}"></audio>')

index = f"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
      #root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:{FONT}; }}
      #facewrap {{ position:absolute; inset:0; z-index:5; overflow:hidden; }}
      #punch {{ position:absolute; inset:0; }}
      #screen {{ position:absolute; inset:0; z-index:8; opacity:0; overflow:hidden; background:radial-gradient(900px 1200px at 50% 40%, #FFFFFF, #DCE0EC); }}
      #scr-bgwrap {{ position:absolute; inset:0; }}
      #scr-fit {{ position:absolute; left:{SX}px; top:0; width:888px; height:{H}px; overflow:hidden; box-shadow:0 0 60px rgba(0,0,0,.25); }}
      #zoom {{ position:absolute; left:0; top:0; width:888px; height:{H}px; }}
      .ripple {{ position:absolute; width:120px; height:120px; z-index:20; }}
      .ripple i {{ position:absolute; inset:0; border-radius:50%; border:7px solid #FF3B30; background:rgba(255,59,48,.15); opacity:0; }}
      .ripple b {{ position:absolute; left:34px; top:34px; width:52px; height:52px; border-radius:50%; background:rgba(17,17,17,.35);
                   box-shadow:0 0 0 4px rgba(255,255,255,.95); opacity:0; }}
      .ring {{ position:absolute; overflow:visible; z-index:19; }}
      .ring path {{ fill:none; stroke:#FF3B30; stroke-width:9; stroke-linecap:round; stroke-dasharray:100; stroke-dashoffset:100; }}
      #dim {{ position:absolute; inset:0; z-index:9; background:#000; opacity:0; }}
      #pop {{ position:absolute; inset:0; z-index:12; background:#FFF8EE; opacity:0; pointer-events:none; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="{W}" data-height="{H}">
      <div id="facewrap"><div id="punch">
        {chr(10).join('        ' + v for v in face_media).strip()}
      </div></div>
      <div id="screen">
        <div id="scr-fit"><div id="zoom">
        {chr(10).join('        ' + v for v in screen_media).strip()}
        {''.join(marks)}
        </div></div>
      </div>
      <div id="dim"></div>
      <div id="pop"></div>
      <div id="flash-hook" data-composition-id="editorial-flash-overlay" data-composition-src="compositions/editorial-flash-overlay.html"
           data-track-kind="graphics" data-start="{FLASH_START:.3f}" data-duration="{FLASH_D}" data-track-index="7" data-width="{W}" data-height="{H}"
           style="position:absolute;inset:0;z-index:13"></div>
      <div id="overlays" data-composition-id="overlays" data-composition-src="compositions/overlays.html" data-track-kind="graphics"
           data-start="0" data-duration="{TOTAL:.3f}" data-track-index="5" data-width="{W}" data-height="{H}" style="z-index:30"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-track-kind="captions"
           data-start="0" data-duration="{TOTAL:.3f}" data-track-index="6" data-width="{W}" data-height="{H}" style="z-index:40"></div>
      {chr(10).join('      ' + a for a in voice_only + audio).strip()}
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

json.dump(dict(total=TOTAL, segments=SEG, cut=[CUT_IN, CUT_OUT], taps=TAPS, groups=[" ".join(w[2] for w in g) for g in groups]),
          open(os.path.join(ROOT, "build", "timeline.json"), "w"), indent=1)
print(f"total {TOTAL}s, {len(groups)} caption groups, {len(OV)} overlay items, {len(SFX)} sfx, cut {CUT_IN}-{CUT_OUT}")
