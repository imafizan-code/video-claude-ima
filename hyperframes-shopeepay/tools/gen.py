import sys, html
P=sys.argv[1]; DUR=35.3
# ---------- captions: (start,end,text,highlight-substring) ----------
CAP=[
(0.10,1.10,"Kalau korang user baru","user baru"),
(1.10,1.88,"korang boleh dapat",""),
(1.88,2.68,"Welcome Bonus","Welcome Bonus"),
(2.68,4.35,"sehingga RM100!","RM100!"),
(4.45,5.26,"Korang, ni je app",""),
(5.26,5.98,"yang korang perlu",""),
(5.98,6.88,"ShopeePay app","ShopeePay app"),
(6.88,7.98,"all-in-one e-wallet","all-in-one"),
(7.98,8.98,"macam T-N-G!",""),
(9.02,9.90,"Satu app saja",""),
(9.90,10.34,"boleh settle",""),
(10.34,11.30,"banyak benda!","banyak benda!"),
(11.37,12.50,"Nak Scan & Pay?","Scan & Pay?"),
(12.50,13.52,"scan je DuitNow QR","DuitNow QR"),
(13.52,14.95,"dekat mana-mana kedai",""),
(14.99,15.60,"Nak bayar bil","bayar bil"),
(15.60,16.95,"elektrik, air,",""),
(16.95,17.65,"data, internet",""),
(17.65,18.65,"semua pun boleh!",""),
(18.70,19.72,"Setiap kali bayar",""),
(19.72,20.25,"boleh kumpul",""),
(20.25,21.07,"Coins cashback","Coins cashback"),
(21.07,22.75,"sehingga 20,000 Coins!","20,000 Coins!"),
(22.79,23.28,"Senang kan?",""),
(23.32,24.36,"Cara dia senang je",""),
(24.36,24.78,"mula-mula",""),
(24.78,25.42,"download dulu","download"),
(25.42,26.40,"ShopeePay app","ShopeePay app"),
(26.40,27.58,"dekat telefon korang",""),
(27.62,28.78,"lepas tu Sign Up","Sign Up"),
(28.82,29.85,"untuk user baru,","user baru,"),
(29.89,30.83,"terus boleh claim","claim"),
(30.83,31.59,"Welcome Bonus","Welcome Bonus"),
(31.59,33.28,"sehingga RM100!","RM100!"),
(33.32,34.06,"Tunggu apa lagi?",""),
(34.06,34.82,"Download ShopeePay","Download ShopeePay"),
(34.82,35.25,"sekarang!",""),
]
# screen-recording cutaways (start,end) -- face hidden, captions go in a fixed band under the phone
CUT=[(4.45,5.98),(12.45,14.95),(14.99,18.65),(24.50,27.58)]
import json
_F=json.load(open(sys.argv[2])); _fps=_F["fps"]
def cap_top(s,e):
    if any(a<=s and e<=b+0.01 for a,b in CUT): return 1236
    c=[f["chin"] for f in _F["faces"] if f["chin"] and s*_fps-3<=f["f"]<=e*_fps+3]
    return int(min(1395,max(1200,max(c)+35)))
def capspan(t,h):
    if h and h in t:
        a,b=t.split(h,1); return html.escape(a)+f'<span class="hl">{html.escape(h)}</span>'+html.escape(b)
    return html.escape(t)
cap_html="\n".join(f'    <div class="cap" id="cap-{i}" style="top:{cap_top(s,e)}px"><span class="cap-in">{capspan(t,h)}</span></div>' for i,(s,e,t,h) in enumerate(CAP))
cap_js="\n".join(
 f'    tl.fromTo("#cap-{i} .cap-in",{{scale:0.86,y:14}},{{scale:1,y:0,duration:0.16,ease:"back.out(2.2)"}},{s});\n'
 f'    tl.set("#cap-{i}",{{opacity:1,visibility:"visible"}},{s});\n'
 f'    tl.to("#cap-{i}",{{opacity:0,duration:0.06,ease:"power2.in"}},{e-0.06:.2f});\n'
 f'    tl.set("#cap-{i}",{{opacity:0,visibility:"hidden"}},{e});'
 for i,(s,e,t,h) in enumerate(CAP))
open(f"{P}/compositions/captions.html","w").write(f'''<template>
  <style>
    #root {{ position:absolute; inset:0; pointer-events:none; }}
    /* Placed per group just under the chin (from face landmarks), x 60..900 clear of the right action rail */
    .cap {{ position:absolute; left:60px; width:840px; top:1200px; height:110px; white-space:nowrap;
           display:flex; align-items:center; justify-content:center; text-align:center;
           opacity:0; visibility:hidden; overflow:visible; }}
    .cap-in {{ display:inline-block; font-family:Poppins, sans-serif; font-weight:800; font-size:62px;
              line-height:1.1; color:#fff; letter-spacing:-0.01em;
              paint-order:stroke fill; -webkit-text-stroke:10px rgba(0,0,0,.85);
              text-shadow:0 6px 18px rgba(0,0,0,.55); }}
    .hl {{ color:#FFD23F; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{cap_html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{cap_js}
    window.__timelines["captions"] = tl;
  </script>
</template>
''')

# ---------- keyword graphics above the head ----------
ICON={
"qr":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><path d="M14 14h3v3h-3zM20 14v.01M14 20h.01M17 20h4v-3"/></svg>',
"bolt":'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg>',
"drop":'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.5S5 10.2 5 15a7 7 0 0 0 14 0c0-4.8-7-12.5-7-12.5z"/></svg>',
"wifi":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M2 8.8a15 15 0 0 1 20 0M5.5 12.5a10 10 0 0 1 13 0M9 16.2a5 5 0 0 1 6 0"/><circle cx="12" cy="19.6" r="1.2" fill="currentColor"/></svg>',
"dl":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M6.5 10 12 15.5 17.5 10M4 20h16"/></svg>',
"check":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>',
"gift":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><rect x="3" y="8" width="18" height="5" rx="1"/><path d="M5 13v8h14v-8M12 8v13M12 8S10.5 3 7.8 3.6C5.6 4.1 6.5 8 12 8zm0 0s1.5-5 4.2-4.4C18.4 4.1 17.5 8 12 8z"/></svg>',
"user":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
}
coin='<div class="coin" data-layout-ignore>S</div>'
KW=[
# id, start, end, inner html, extra js (relative to group)
("k-rm100",0.15,4.35,f'''<div class="card">
  <div class="tag" id="k-rm100-tag"><span class="ic">{ICON["user"]}</span>User Baru</div>
  <div class="big" id="k-rm100-big"><span class="ic gift">{ICON["gift"]}</span>RM100</div>
  <div class="sub">Welcome Bonus</div></div>''',
 [('"#k-rm100-big"','{scale:1}','{scale:1.18,duration:0.12,yoyo:true,repeat:1,ease:"power2.out"}',3.28)]),
("k-app",5.98,8.98,f'''<div class="card row">
  <div class="logo-wrap"><img src="assets/logo.png" alt="ShopeePay"/></div>
  <div class="pill" id="k-app-pill">All-in-one e-wallet</div></div>''',
 [('"#k-app-pill"','{opacity:0,y:16}','{opacity:1,y:0,duration:0.25,ease:"back.out(2)"}',6.88)]),
("k-settle",9.02,11.30,f'''<div class="card row">
  <div class="one">1</div><div class="stack"><div class="t1">App</div><div class="t2">Banyak benda settle</div></div>
  <div class="minis"><span class="mini">{ICON["qr"]}</span><span class="mini">{ICON["bolt"]}</span><span class="mini">{coin}</span></div></div>''',
 []),
("k-scan",11.37,12.45,f'''<div class="card row">
  <div class="sq">{ICON["qr"]}</div><div class="stack"><div class="t1">Scan &amp; Pay</div><div class="t2" id="k-scan-sub">DuitNow QR</div></div></div>''',
 []),
("k-coins",18.70,23.28,f'''<div class="card row">
  {coin}<div class="stack"><div class="t2">Coins cashback sehingga</div><div class="t1 num"><span id="k-coins-num">0</span> Coins</div></div></div>''',
 []),
("k-dl",23.32,24.50,f'''<div class="card row">
  <div class="sq">{ICON["dl"]}</div><div class="stack"><div class="t2">Cara claim?</div><div class="t1">3 langkah je!</div></div></div>''',
 []),
("k-steps",27.62,29.85,f'''<div class="card row steps">
  <span class="step done">{ICON["check"]}<b>Download</b></span><span class="arrow">›</span>
  <span class="step" id="k-step2"><i class="n">2</i><b>Sign Up</b></span><span class="arrow">›</span>
  <span class="step dim" id="k-step3"><i class="n">3</i><b>Claim</b></span></div>''',
 [('"#k-step2"','{backgroundColor:"rgba(255,255,255,0.18)"}','{backgroundColor:"#22C55E",duration:0.2}',28.10),
  ('"#k-step3"','{opacity:0.45}','{opacity:1,duration:0.2}',28.85)]),
("k-claim",29.89,33.28,f'''<div class="card row">
  <img class="banner" src="assets/welcome_bonus.jpg" alt="RM100 Welcome Bonus"/>
  <div class="stack"><div class="t2">Claim untuk user baru</div><div class="t1 num" id="k-claim-big">RM100</div><div class="t2">Welcome Bonus</div></div></div>''',
 [('"#k-claim-big"','{scale:1}','{scale:1.15,duration:0.12,yoyo:true,repeat:1,ease:"power2.out"}',32.19)]),
("k-cta",33.32,35.30,f'''<div class="card row">
  <div class="logo-wrap v"><img src="assets/logo_v.png" alt="ShopeePay"/></div>
  <div class="pill dl">{ICON["dl"]}Download sekarang</div></div>''',
 []),
]
kw_html="\n".join(f'    <div class="kw" id="{k}">{h}</div>' for k,s,e,h,_ in KW)
js=[]
for k,s,e,h,extra in KW:
    js.append(f'    tl.set("#{k}",{{opacity:1,visibility:"visible"}},{s});')
    js.append(f'    tl.fromTo("#{k} > .card",{{scale:0.5,y:40,rotation:-4}},{{scale:1,y:0,rotation:0,duration:0.32,ease:"back.out(1.9)"}},{s});')
    for sel,a,b,t in extra: js.append(f'    tl.fromTo({sel},{a},{b},{t});')
    js.append(f'    tl.to("#{k} > .card",{{scale:0.7,y:-30,opacity:0,duration:0.16,ease:"power2.in"}},{e-0.16:.2f});')
    js.append(f'    tl.set("#{k}",{{opacity:0,visibility:"hidden"}},{e});')
js.append('''    const cn={v:0}, numEl=document.getElementById("k-coins-num");
    tl.fromTo(cn,{v:0},{v:20000,duration:2.6,ease:"power2.out",onUpdate:()=>{numEl.textContent=Math.round(cn.v).toLocaleString("en-US");}},18.9);''')
open(f"{P}/compositions/keywords.html","w").write('''<template>
  <style>
    #root { position:absolute; inset:0; pointer-events:none; }
    /* Graphics band: above the head, below platform top UI (TikTok ~170px, IG Reels ~250px), clear of right rail */
    .kw { position:absolute; left:60px; width:840px; top:265px; height:270px;
          display:flex; align-items:center; justify-content:center; opacity:0; visibility:hidden; overflow:visible; }
    .card { background:#fff; color:#1b1b1b; border-radius:34px; padding:22px 30px;
            box-shadow:0 14px 40px rgba(0,0,0,.28), 0 0 0 5px #EE4D2D inset;
            font-family:Poppins, sans-serif; display:flex; flex-direction:column; align-items:center; gap:4px; }
    .card.row { flex-direction:row; gap:22px; }
    .ic { width:40px; height:40px; display:inline-flex; color:#EE4D2D; }
    .ic svg, .sq svg, .mini svg, .bill svg, .pill svg, .step svg { width:100%; height:100%; }
    .tag { display:flex; align-items:center; gap:10px; background:#EE4D2D; color:#fff; font-weight:700; font-size:30px;
           padding:6px 20px; border-radius:999px; }
    .tag .ic { color:#fff; width:30px; height:30px; }
    .big { display:flex; align-items:center; gap:14px; font-weight:900; font-size:110px; line-height:1; color:#EE4D2D; letter-spacing:-0.03em; }
    .big .gift { width:84px; height:84px; }
    .sub { font-weight:800; font-size:40px; letter-spacing:.02em; text-transform:uppercase; }
    .logo-wrap { height:110px; display:flex; align-items:center; }
    .logo-wrap img { height:100px; width:auto; }
    .logo-wrap.v { height:170px; } .logo-wrap.v img { height:170px; }
    .pill { background:#EE4D2D; color:#fff; font-weight:800; font-size:36px; padding:14px 26px; border-radius:999px;
            display:flex; align-items:center; gap:12px; white-space:nowrap; }
    .pill.dl svg { width:38px; height:38px; }
    .one { font-weight:900; font-size:120px; line-height:1; color:#EE4D2D; }
    .stack { display:flex; flex-direction:column; align-items:flex-start; }
    .t1 { font-weight:900; font-size:62px; line-height:1.05; color:#1b1b1b; letter-spacing:-0.02em; }
    .t1.c { text-align:center; }
    .t1.num { color:#EE4D2D; font-size:72px; }
    .t2 { font-weight:700; font-size:30px; color:#555; }
    .minis { display:flex; gap:10px; }
    .mini { width:64px; height:64px; border-radius:18px; background:#FFF0EB; color:#EE4D2D; padding:12px; display:flex; align-items:center; justify-content:center; }
    .mini .coin { width:44px; height:44px; font-size:26px; border-width:3px; }
    .sq { width:120px; height:120px; border-radius:28px; background:#EE4D2D; color:#fff; padding:22px; display:flex; }
    .bills { display:flex; gap:16px; margin-top:8px; }
    .bill { display:flex; flex-direction:column; align-items:center; gap:6px; width:150px; padding:14px 8px; border-radius:22px;
            background:#FFF0EB; color:#EE4D2D; }
    .bill svg { width:56px; height:56px; }
    .bill b { font-size:28px; color:#1b1b1b; }
    .coin { width:120px; height:120px; border-radius:50%; background:radial-gradient(circle at 35% 30%, #FFE27A, #F5B301 60%, #D98E00);
            border:6px solid #FFF3C4; color:#9A5B00; font-weight:900; font-size:66px; display:flex; align-items:center; justify-content:center;
            text-shadow:0 2px 0 rgba(0,0,0,.18); flex:none; }
    .steps { gap:12px; }
    .step { display:flex; align-items:center; gap:10px; padding:12px 18px; border-radius:999px; background:#EE4D2D; color:#fff; }
    .step b { font-size:32px; font-weight:800; white-space:nowrap; }
    .step svg { width:34px; height:34px; }
    .step.done { background:#22C55E; }
    .step .n { font-style:normal; font-weight:900; font-size:28px; width:40px; height:40px; border-radius:50%; background:#fff; color:#EE4D2D;
               display:flex; align-items:center; justify-content:center; }
    .arrow { font-size:48px; font-weight:900; color:#EE4D2D; }
    .banner { width:200px; height:200px; border-radius:22px; object-fit:cover; }
  </style>
  <div id="root" data-composition-id="keywords" data-width="1080" data-height="1920">
''' + kw_html + '''
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
''' + "\n".join(js) + '''
    window.__timelines["keywords"] = tl;
  </script>
</template>
''')


# ---------- screen-recording cutaways (phone mockup on brand background) ----------
BR=[
 # id, start, end, media html, chip html, extra js
 ("b-app",4.45,5.98,'<img id="b-app-media" class="clip media" src="assets/appstore.png" data-start="4.45" data-duration="1.53" alt="ShopeePay di App Store"/>',
  '<span class="chip-t">ShopeePay app</span><span class="chip-s">App Store &amp; Google Play</span>',
  ['tl.fromTo("#b-app-media",{scale:1.0,y:0},{scale:1.08,y:-30,duration:1.53,ease:"none"},4.45);']),
 ("b-scan",12.45,14.95,'<video id="b-scan-media" class="clip media" src="assets/rec_scan.mp4" data-start="12.45" data-duration="2.5" data-media-start="0.9" data-playback-rate="1.25" muted playsinline></video>',
  f'<span class="chip-ic">{ICON["qr"]}</span><span class="chip-t">Scan &amp; Pay</span><span class="chip-s">DuitNow QR</span>',[]),
 ("b-bil",14.99,18.65,'<video id="b-bil-media" class="clip media" src="assets/rec_bil.mp4" data-start="14.99" data-duration="3.66" data-media-start="11.25" muted playsinline></video>',
  f'<span class="chip-t">Bayar Bil</span><span class="bi" id="b-bil-1">{ICON["bolt"]}</span><span class="bi" id="b-bil-2">{ICON["drop"]}</span><span class="bi" id="b-bil-3">{ICON["wifi"]}</span>',
  ['tl.fromTo("#b-bil-1",{opacity:0,scale:0.5},{opacity:1,scale:1,duration:0.22,ease:"back.out(2.4)"},15.61);',
   'tl.fromTo("#b-bil-2",{opacity:0,scale:0.5},{opacity:1,scale:1,duration:0.22,ease:"back.out(2.4)"},16.51);',
   'tl.fromTo("#b-bil-3",{opacity:0,scale:0.5},{opacity:1,scale:1,duration:0.22,ease:"back.out(2.4)"},16.97);']),
 ("b-dl",24.50,27.58,'<video id="b-dl-media" class="clip media" src="assets/rec_download.mp4" data-start="24.50" data-duration="3.08" data-media-start="0.6" data-playback-rate="2.8" muted playsinline></video>',
  f'<span class="chip-ic">{ICON["dl"]}</span><span class="chip-t">Download ShopeePay app</span>',[]),
]
br_html="\n".join(f'''    <div class="cut" id="{k}">
      <div class="bg"></div>
      <div class="chip" id="{k}-chip">{chip}</div>
      <div class="phone" id="{k}-phone"><div class="screen">{media}</div></div>
    </div>''' for k,s0,e0,media,chip,_ in BR)
bj=[]
for k,s0,e0,media,chip,extra in BR:
    bj.append(f'    tl.set("#{k}",{{opacity:1,visibility:"visible"}},{s0});')
    bj.append(f'    tl.fromTo("#{k} .bg",{{opacity:0}},{{opacity:1,duration:0.12}},{s0});')
    bj.append(f'    tl.fromTo("#{k}-phone",{{y:420,scale:0.85,rotation:4}},{{y:0,scale:1,rotation:0,duration:0.34,ease:"back.out(1.4)"}},{s0});')
    bj.append(f'    tl.fromTo("#{k}-chip",{{y:-60,opacity:0}},{{y:0,opacity:1,duration:0.26,ease:"back.out(2)"}},{s0+0.08:.2f});')
    bj+=["    "+x for x in extra]
    bj.append(f'    tl.to("#{k}",{{opacity:0,duration:0.12,ease:"power2.in"}},{e0-0.12:.2f});')
    bj.append(f'    tl.set("#{k}",{{opacity:0,visibility:"hidden"}},{e0});')
open(f"{P}/compositions/broll.html","w").write('''<template>
  <style>
    #root { position:absolute; inset:0; pointer-events:none; }
    .cut { position:absolute; inset:0; opacity:0; visibility:hidden; }
    .bg { position:absolute; inset:0; background:
          radial-gradient(circle at 25% 15%, rgba(255,255,255,.22), transparent 45%),
          radial-gradient(circle at 80% 85%, rgba(255,190,120,.35), transparent 50%),
          linear-gradient(160deg,#FF7A45 0%,#EE4D2D 55%,#D63A1D 100%); }
    /* chip: under platform top UI; phone: centred in the TikTok/IG safe column (x 60..900) */
    .chip { position:absolute; left:60px; width:840px; top:190px; height:110px; display:flex; align-items:center; justify-content:center; gap:16px;
            font-family:Poppins, sans-serif; color:#fff; }
    .chip-t { font-weight:900; font-size:50px; letter-spacing:-0.02em; white-space:nowrap; background:#fff; color:#C7361A; padding:10px 28px; border-radius:999px; box-shadow:0 8px 22px rgba(80,10,0,.3); }
    .chip-s { font-weight:800; font-size:30px; background:#1b1b1b; color:#fff; padding:8px 18px; border-radius:999px; white-space:nowrap; }
    .chip-ic, .bi { width:62px; height:62px; border-radius:18px; background:#fff; color:#EE4D2D; padding:12px; display:flex; flex:none; }
    .chip-ic svg, .bi svg { width:100%; height:100%; }
    .phone { position:absolute; left:271px; top:318px; width:418px; height:890px; border-radius:54px; background:#111; padding:12px;
             box-shadow:0 30px 70px rgba(80,10,0,.45), 0 0 0 4px rgba(255,255,255,.55); }
    .screen { position:relative; width:100%; height:100%; border-radius:44px; overflow:hidden; background:#fff; }
    .media { position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; object-position:top center; }
  </style>
  <div id="root" data-composition-id="broll" data-width="1080" data-height="1920">
'''+br_html+'''
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
'''+"\n".join(bj)+'''
    window.__timelines["broll"] = tl;
  </script>
</template>
''')

open(f"{P}/index.html","w").write(f'''<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ margin:0; width:1080px; height:1920px; overflow:hidden; background:#000; }}
      #root {{ position:relative; width:100%; height:100%; }}
      #talk {{ position:absolute; left:0; top:0; width:1080px; height:1920px; object-fit:cover; z-index:1; }}
      #keywords {{ z-index:2; }}
      #broll {{ z-index:3; }}
      #captions {{ z-index:4; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
      <video id="talk" class="clip" src="assets/talk.mp4" data-start="0" data-duration="{DUR}" data-track-index="0"
             playsinline data-has-audio="true" data-volume="1"></video>
      <div id="keywords" data-composition-id="keywords" data-composition-src="compositions/keywords.html"
           data-start="0" data-duration="{DUR}" data-track-index="1" data-track-kind="graphics"
           data-width="1080" data-height="1920"></div>
      <div id="broll" data-composition-id="broll" data-composition-src="compositions/broll.html"
           data-start="0" data-duration="{DUR}" data-track-index="3" data-track-kind="graphics"
           data-width="1080" data-height="1920"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
           data-start="0" data-duration="{DUR}" data-track-index="2" data-track-kind="captions"
           data-width="1080" data-height="1920"></div>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
''')
print("ok")
