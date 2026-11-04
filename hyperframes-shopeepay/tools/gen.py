import sys, html, re
P=sys.argv[1]; DUR=36.5
# segment boundaries before/after lengthening word tails (so "ringgit"/"benda" are not clipped)
OLDB=[0,4.40,9.00,11.33,14.97,18.67,22.77,23.30,27.60,28.80,29.87,33.30,35.30]
NEWB=[0,4.67,9.37,11.97,15.70,19.50,23.60,24.23,28.53,29.73,30.80,34.40,36.50]
def R(t,end=False):
    for k in range(len(OLDB)-1):
        a,b=OLDB[k],OLDB[k+1]
        if (a<t<=b) if end else (a<=t<b):
            if end and b-t<0.12: return NEWB[k+1]
            return round(t-a+NEWB[k],3)
    return NEWB[-1] if end else round(t-OLDB[-1]+NEWB[-1],3)
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
CUT=[(4.45,5.98),(12.45,14.95),(14.99,18.65),(20.25,22.75),(24.50,27.58),(29.89,33.28)]
CAP=[(R(a),R(b,True),t,h) for a,b,t,h in CAP]
CUT=[(R(a),R(b,True)) for a,b in CUT]
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
def _oncut(s,e): return " on-cut" if any(a<=s and e<=b+0.01 for a,b in CUT) else ""
cap_html="\n".join(f'    <div class="cap{_oncut(s,e)}" id="cap-{i}" style="top:{cap_top(s,e)}px"><span class="cap-in">{capspan(t,h)}</span></div>' for i,(s,e,t,h) in enumerate(CAP))
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
    .on-cut .cap-in {{ background:rgba(20,8,4,.72); padding:6px 26px 10px; border-radius:22px; -webkit-text-stroke:0; }}
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

# ---------- RM100 celebration effects (deterministic: seeded positions) ----------
import random
FX_CSS = """
    .fx-rays { position:absolute; width:1400px; height:1400px; border-radius:50%; pointer-events:none;
               background:repeating-conic-gradient(from 0deg, rgba(255,214,90,.62) 0deg 9deg, rgba(255,214,90,0) 9deg 24deg);
               -webkit-mask-image:radial-gradient(circle, #000 18%, transparent 62%); mask-image:radial-gradient(circle, #000 18%, transparent 62%); }
    .fx-ring { position:absolute; width:520px; height:520px; border-radius:50%; border:16px solid #FFD23F; box-shadow:0 0 40px rgba(255,210,63,.9); pointer-events:none; }
    .fx-cf { position:absolute; top:0; border-radius:4px; pointer-events:none; }
    .fx-coin { position:absolute; top:0; width:54px; height:54px; border-radius:50%; background:radial-gradient(circle at 35% 30%, #FFE680, #F5B301 60%, #C98400);
               border:4px solid #FFF3C4; color:#8A5200; font:900 30px Poppins, sans-serif; display:flex; align-items:center; justify-content:center; pointer-events:none; }
    .fx-star { position:absolute; width:70px; height:70px; pointer-events:none; color:#FFD23F; filter:drop-shadow(0 0 10px rgba(255,230,120,.9)); }
    .fx-star svg { width:100%; height:100%; }
    .fx-shine { position:absolute; top:-20%; left:0; width:140px; height:140%; pointer-events:none;
                background:linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.75), rgba(255,255,255,0)); }
"""
STAR='<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c.8 6.4 4.8 10.4 12 12-7.2 1.6-11.2 5.6-12 12-.8-6.4-4.8-10.4-12-12C7.2 10.4 11.2 6.4 12 0z"/></svg>'
def fx_parts(p, cx, cy, w, seed):
    """html for rays (behind), front layer (confetti, coins, ring, stars); cx,cy = centre of the hero in container px"""
    rnd=random.Random(seed); cols=["#EE4D2D","#FFD23F","#FFFFFF","#FF8A65","#FFB300"]
    back=f'<div class="fx-rays" data-layout-ignore id="{p}-rays" style="left:{cx-700}px;top:{cy-700}px"></div>'
    front=[f'<div class="fx-ring" data-layout-ignore id="{p}-ring" style="left:{cx-260}px;top:{cy-260}px"></div>']
    pieces=[]
    for wave in (0,1):
        for i in range(16):
            pid=f"{p}-c{wave}-{i}"; x=int(rnd.uniform(-60,w+20)); coin = i%4==0
            if coin: front.append(f'<div class="fx-coin" data-layout-ignore id="{pid}" style="left:{x}px">S</div>')
            else:
                ww,hh=(rnd.choice([14,18,22]),rnd.choice([26,32,38]))
                front.append(f'<div class="fx-cf" data-layout-ignore id="{pid}" style="left:{x}px;width:{ww}px;height:{hh}px;background:{rnd.choice(cols)}"></div>')
            pieces.append((pid,wave,rnd.uniform(-90,90),rnd.uniform(-200,200),rnd.uniform(240,720),rnd.uniform(0,0.6),rnd.uniform(1.4,2.4),rnd.uniform(-420,0)))
    stars=[(cx-330,cy-360),(cx+290,cy-320),(cx-360,cy+250),(cx+320,cy+280),(cx-20,cy-430)]
    for j,(sx,sy) in enumerate(stars): front.append(f'<div class="fx-star" data-layout-ignore id="{p}-s{j}" style="left:{sx-35}px;top:{sy-35}px">{STAR}</div>')
    return back, "".join(front), pieces, len(stars)
def fx_js(p, pieces, nstars, t0, t1, tpop, fall_from, fall_to, hero_img, shine):
    j=[f'tl.fromTo("#{p}-rays",{{opacity:0,rotation:0,scale:0.6}},{{opacity:1,scale:1,duration:0.35,ease:"power2.out"}},{t0});',
       f'tl.fromTo("#{p}-rays",{{rotation:0}},{{rotation:110,duration:{t1-t0:.2f},ease:"none",immediateRender:false}},{t0});',
       f'tl.fromTo("#{p}-ring",{{opacity:0,scale:0.3}},{{opacity:1,scale:0.32,duration:0.01}},{tpop});',
       f'tl.to("#{p}-ring",{{opacity:0,scale:2.6,duration:0.7,ease:"power2.out"}},{tpop+0.01:.2f});',
       f'tl.fromTo("#{shine}",{{x:-260}},{{x:900,duration:0.7,ease:"power2.inOut"}},{t0+0.45:.2f});',
       f'tl.to("#{shine}",{{x:-260,duration:0.01}},{tpop-0.05:.2f});',
       f'tl.to("#{shine}",{{x:900,duration:0.55,ease:"power2.inOut"}},{tpop:.2f});']
    if hero_img: j.append(f'tl.fromTo("{hero_img}",{{scale:1}},{{scale:1.13,duration:0.14,yoyo:true,repeat:1,ease:"power2.out"}},{tpop});')
    for pid,wave,rot,drift,spin,delay,dur,yoff in pieces:
        st=(t0+0.15 if wave==0 else tpop)+delay
        j.append(f'tl.fromTo("#{pid}",{{y:{fall_from+yoff:.0f},x:0,rotation:{rot:.0f},opacity:1}},{{y:{fall_to},x:{drift:.0f},rotation:{rot+spin:.0f},duration:{dur:.2f},ease:"power1.in"}},{st:.2f});')
        j.append(f'tl.to("#{pid}",{{opacity:0,duration:0.2}},{st+dur-0.2:.2f});')
    for k in range(nstars):
        j.append(f'tl.fromTo("#{p}-s{k}",{{scale:0,rotation:0,opacity:1}},{{scale:1.2,rotation:90,duration:0.25,ease:"back.out(3)"}},{tpop+0.05*k:.2f});')
        j.append(f'tl.to("#{p}-s{k}",{{scale:0,opacity:0,duration:0.3,ease:"power2.in"}},{tpop+0.5+0.05*k:.2f});')
    return ["    "+x for x in j]

HOOK_FX=fx_parts('hk',420,500,840,7)
KW=[
# id, start, end, inner html, extra js (relative to group)
("k-rm100",1.50,4.35,(lambda b:b[0]+'<div class="card ban"><img id="k-rm100-img" src="assets/banner_welcome_popup.png" alt="RM100 Welcome Bonus"/><div class="fx-shine" data-layout-ignore id="k-rm100-shine"></div></div>'+b[1])(HOOK_FX),
 []),
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
("k-coins",18.70,20.25,f'''<div class="card row">
  {coin}<div class="stack"><div class="t2">Coins cashback sehingga</div><div class="t1 num"><span id="k-coins-num">0</span> Coins</div></div></div>''',
 []),
("k-senang",22.78,23.52,f'''<div class="card kin"><div class="kin-l1"><span class="kl" id="ks-l0">S</span><span class="kl" id="ks-l1">e</span><span class="kl" id="ks-l2">n</span><span class="kl" id="ks-l3">a</span><span class="kl" id="ks-l4">n</span><span class="kl" id="ks-l5">g</span></div><div class="kin-l2"><span id="ks-kan">kan?</span><span class="kin-ok" id="ks-ok">{ICON["check"]}</span></div></div>''',
 [('"#ks-l0"','{y:-180,opacity:0,rotation:12}','{y:0,opacity:1,rotation:0,duration:0.28,ease:"back.out(3)"}',22.780),('"#ks-l1"','{y:-180,opacity:0,rotation:-14}','{y:0,opacity:1,rotation:0,duration:0.28,ease:"back.out(3)"}',22.815),('"#ks-l2"','{y:-180,opacity:0,rotation:12}','{y:0,opacity:1,rotation:0,duration:0.28,ease:"back.out(3)"}',22.850),('"#ks-l3"','{y:-180,opacity:0,rotation:-14}','{y:0,opacity:1,rotation:0,duration:0.28,ease:"back.out(3)"}',22.885),('"#ks-l4"','{y:-180,opacity:0,rotation:12}','{y:0,opacity:1,rotation:0,duration:0.28,ease:"back.out(3)"}',22.920),('"#ks-l5"','{y:-180,opacity:0,rotation:-14}','{y:0,opacity:1,rotation:0,duration:0.28,ease:"back.out(3)"}',22.955),
  ('"#ks-kan"','{scale:0,rotation:-25}','{scale:1,rotation:-6,duration:0.3,ease:"back.out(3.5)"}',23.02),
  ('"#ks-ok"','{scale:0,rotation:-90}','{scale:1,rotation:0,duration:0.3,ease:"back.out(3)"}',23.14)]),
("k-dl",23.52,24.50,f'''<div class="card row">
  <div class="sq">{ICON["dl"]}</div><div class="stack"><div class="t2">Cara claim?</div><div class="t1">3 langkah je!</div></div></div>''',
 []),
("k-steps",27.62,29.85,f'''<div class="card row steps">
  <span class="step done">{ICON["check"]}<b>Download</b></span><span class="arrow">›</span>
  <span class="step" id="k-step2"><i class="n">2</i><b>Sign Up</b></span><span class="arrow">›</span>
  <span class="step dim" id="k-step3"><i class="n">3</i><b>Claim</b></span></div>''',
 [('"#k-step2"','{backgroundColor:"rgba(255,255,255,0.18)"}','{backgroundColor:"#22C55E",duration:0.2}',28.10),
  ('"#k-step3"','{opacity:0.45}','{opacity:1,duration:0.2}',28.85)]),
("k-cta",33.32,35.30,'''<div class="card biglogo"><img id="k-cta-logo" src="assets/logo_cta.png" alt="ShopeePay"/></div>''',
 [('"#k-cta-logo"','{scale:1}','{scale:1.06,duration:0.5,yoyo:true,repeat:1,ease:"sine.inOut"}',34.0)]),
]
KW=[(k,R(a),R(b,True),h,[(x,y,z,R(t)) for x,y,z,t in ex]) for k,a,b,h,ex in KW]
kw_html="\n".join(f'    <div class="kw" id="{k}">{h}</div>' for k,s,e,h,_ in KW)
js=[]
for k,s,e,h,extra in KW:
    js.append(f'    tl.set("#{k}",{{opacity:1,visibility:"visible"}},{s});')
    js.append(f'    tl.fromTo("#{k} > .card",{{scale:0.5,y:40,rotation:-4}},{{scale:1,y:0,rotation:0,duration:0.32,ease:"back.out(1.9)"}},{s});')
    for sel,a,b,t in extra: js.append(f'    tl.fromTo({sel},{a},{b},{t});')
    js.append(f'    tl.to("#{k} > .card",{{scale:0.7,y:-30,opacity:0,duration:0.16,ease:"power2.in"}},{e-0.16:.2f});')
    js.append(f'    tl.set("#{k}",{{opacity:0,visibility:"hidden"}},{e});')
js += fx_js('hk',HOOK_FX[2],HOOK_FX[3],R(1.50),R(4.35,True),R(3.28),-560,1950,'#k-rm100','k-rm100-shine')
js.append('''    const cn={v:0}, numEl=document.getElementById("k-coins-num");
    tl.fromTo(cn,{v:0},{v:20000,duration:1.2,ease:"power2.out",onUpdate:()=>{numEl.textContent=Math.round(cn.v).toLocaleString("en-US");}},'''+f'{R(18.9)});')
open(f"{P}/compositions/keywords.html","w").write('''<template>
  <style>
    #root { position:absolute; inset:0; pointer-events:none; }'''+FX_CSS+'''
    /* Graphics band: above the head, below platform top UI (TikTok ~170px, IG Reels ~250px), clear of right rail */
    .kw { position:absolute; left:60px; width:840px; top:250px; height:300px;
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
    .kw#k-rm100 { top:200px; height:1000px; }
    .kw#k-rm100 .card { position:relative; z-index:2; }
    .kw#k-rm100 .card.ban img { height:780px; }
    .kw#k-rm100 .fx-rays { z-index:0; } .kw#k-rm100 .fx-ring, .kw#k-rm100 .fx-cf, .kw#k-rm100 .fx-coin, .kw#k-rm100 .fx-star { z-index:3; }
    .kw#k-cta { top:190px; height:360px; }
    .card.biglogo { background:none; box-shadow:none; padding:0; }
    .card.biglogo img { display:block; width:820px; height:auto; filter:drop-shadow(0 10px 24px rgba(0,0,0,.18)) drop-shadow(0 0 2px #fff); }
    .kw#k-senang { top:200px; height:370px; }
    .card.kin { background:none; box-shadow:none; padding:0; gap:0; font-family:Poppins, sans-serif; }
    .kin-l1 { display:flex; font-weight:900; font-size:178px; line-height:1; letter-spacing:-0.02em; color:#fff;
              paint-order:stroke fill; -webkit-text-stroke:14px #EE4D2D; text-shadow:0 10px 0 #B8321A, 0 18px 30px rgba(0,0,0,.25); }
    .kl { display:inline-block; }
    .kin-l2 { display:flex; align-items:center; gap:18px; margin-top:-6px; }
    #ks-kan { display:inline-block; font-weight:900; font-size:150px; line-height:1; color:#FFD23F;
              paint-order:stroke fill; -webkit-text-stroke:14px #1b1b1b; text-shadow:0 10px 0 #1b1b1b; }
    .kin-ok { display:flex; width:120px; height:120px; border-radius:50%; background:#22C55E; color:#fff; padding:18px;
              box-shadow:0 0 0 7px #fff, 0 12px 26px rgba(0,0,0,.25); }
    .kin-ok svg { width:100%; height:100%; }
    .card.ban { position:relative; padding:0; overflow:hidden; border-radius:26px; box-shadow:0 14px 40px rgba(0,0,0,.3), 0 0 0 5px #fff; }
    .card.ban img { display:block; height:290px; width:auto; }
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
  '<span class="chip-t">ShopeePay app</span><span class="store" title="App Store"><svg viewBox="0 0 24 24"><defs><linearGradient id="asg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1AC8FC"/><stop offset="1" stop-color="#1A6FE8"/></linearGradient></defs><rect width="24" height="24" rx="5.4" fill="url(#asg)"/><g stroke="#fff" stroke-width="1.75" stroke-linecap="round" fill="none"><path d="M13.7 5.4 7.9 15.6"/><path d="M10.3 5.4 16.1 15.6"/><path d="M5.6 15.6h12.8"/><path d="M7.2 18.1 6.4 19.4"/></g></svg></span><span class="store" title="Google Play"><svg viewBox="0 0 24 24"><path fill="#00C3FF" d="M3.6 2.2 13.4 12 3.6 21.8c-.4-.2-.6-.6-.6-1.1V3.3c0-.5.2-.9.6-1.1z"/><path fill="#FFC400" d="m16.8 8.6-3.4 3.4 3.4 3.4 3.9-2.2c.8-.5.8-1.6 0-2.1z"/><path fill="#FF3A44" d="M13.4 12 3.6 21.8c.3.2.8.2 1.2 0l12-6.4z"/><path fill="#00D26A" d="M3.6 2.2c.4-.2.8-.2 1.2 0l12 6.4-3.4 3.4z"/></svg></span>',
  ['tl.fromTo("#b-app-media",{scale:1.0,y:0},{scale:1.08,y:-30,duration:1.53,ease:"none"},4.45);']),
 ("b-scan",12.45,14.95,'<video id="b-scan-media" class="clip media" src="assets/rec_scan.mp4" data-start="12.45" data-duration="2.5" data-media-start="0.9" data-playback-rate="1.25" muted playsinline></video>',
  f'<span class="chip-ic">{ICON["qr"]}</span><span class="chip-t">Scan &amp; Pay</span><span class="chip-s">DuitNow QR</span>',[]),
 ("b-bil",14.99,18.65,'<video id="b-bil-media" class="clip media" src="assets/rec_bil.mp4" data-start="14.99" data-duration="3.66" data-media-start="11.10" muted playsinline></video>',
  f'<span class="chip-t">Bayar Bil</span><span class="bi" id="b-bil-1">{ICON["bolt"]}</span><span class="bi" id="b-bil-2">{ICON["drop"]}</span><span class="bi" id="b-bil-3">{ICON["wifi"]}</span>',
  ['tl.fromTo("#b-bil-1",{opacity:0,scale:0.5},{opacity:1,scale:1,duration:0.22,ease:"back.out(2.4)"},15.61);',
   'tl.fromTo("#b-bil-2",{opacity:0,scale:0.5},{opacity:1,scale:1,duration:0.22,ease:"back.out(2.4)"},16.51);',
   'tl.fromTo("#b-bil-3",{opacity:0,scale:0.5},{opacity:1,scale:1,duration:0.22,ease:"back.out(2.4)"},16.97);']),
 ("b-coins",20.25,22.75,'<img id="b-coins-media" class="clip poster-img" src="assets/banner_coins.jpg" data-start="20.25" data-duration="2.5" alt="Mega Coins Bonanza: earn up to 20,000 Shopee Coins"/>','',
  ['tl.fromTo("#b-coins-media",{scale:1},{scale:1.05,duration:2.5,ease:"none"},20.25);']),
 ("b-claim",29.89,33.28,'<img id="b-claim-media" class="clip poster-img" src="assets/banner_welcome.jpg" data-start="29.89" data-duration="3.39" alt="RM100 Welcome Bonus"/>','',
  ['tl.fromTo("#b-claim-media",{scale:1},{scale:1.05,duration:3.39,ease:"none"},29.89);']),
 ("b-dl",24.50,27.58,'<video id="b-dl-media" class="clip media" src="assets/rec_download.mp4" data-start="24.50" data-duration="3.08" data-media-start="0.6" data-playback-rate="2.8" muted playsinline></video>',
  f'<span class="chip-ic">{ICON["dl"]}</span><span class="chip-t">Download ShopeePay app</span>',[]),
]
def _rb(k,a,b,media,chip,extra):
    na,nb=R(a),R(b,True)
    media=re.sub(r'data-start="[0-9.]+"',f'data-start="{na}"',media)
    media=re.sub(r'data-duration="[0-9.]+"',f'data-duration="{nb-na:.3f}"',media)
    ex=[]
    for x in extra:
        x=x.replace(f'duration:{b-a:.2f}',f'duration:{nb-na:.3f}')
        x=re.sub(r',([0-9.]+)\);$',lambda m:f',{R(float(m.group(1)))});',x)
        ex.append(x)
    return (k,na,nb,media,chip,ex)
BR=[_rb(*b) for b in BR]
br_html="\n".join(f'''    <div class="cut" id="{k}">
      <div class="bg"></div>
      <div class="chip" id="{k}-chip">{chip}</div>
      {('<div class="poster" id="'+k+'-poster">'+media+'</div>') if 'poster-img' in media else ('<div class="phone" id="'+k+'-phone"><div class="screen">'+media+'</div></div>')}
    </div>''' for k,s0,e0,media,chip,_ in BR)
CLAIM_FX=fx_parts('cl',480,712,1080,11)
br_html=br_html.replace('<div class="poster" id="b-claim-poster">', CLAIM_FX[0]+'<div class="poster" id="b-claim-poster">')
br_html=re.sub(r'(<div class="poster" id="b-claim-poster">.*?</div>)', lambda m: m.group(1)[:-6]+'<div class="fx-shine" data-layout-ignore id="b-claim-shine"></div></div>'+CLAIM_FX[1], br_html, count=1, flags=re.S)
bj=[]
for k,s0,e0,media,chip,extra in BR:
    bj.append(f'    tl.set("#{k}",{{opacity:1,visibility:"visible"}},{s0});')
    bj.append(f'    tl.fromTo("#{k} .bg",{{opacity:0}},{{opacity:1,duration:0.12}},{s0});')
    if 'poster-img' in media:
        bj.append(f'    tl.fromTo("#{k}-poster",{{y:380,scale:0.7,rotation:-5}},{{y:0,scale:1,rotation:0,duration:0.38,ease:"back.out(1.6)"}},{s0});')
    else:
        bj.append(f'    tl.fromTo("#{k}-phone",{{y:420,scale:0.85,rotation:4}},{{y:0,scale:1,rotation:0,duration:0.34,ease:"back.out(1.4)"}},{s0});')
        bj.append(f'    tl.fromTo("#{k}-chip",{{y:-60,opacity:0}},{{y:0,opacity:1,duration:0.26,ease:"back.out(2)"}},{s0+0.08:.2f});')
    bj+=["    "+x for x in extra]
    bj.append(f'    tl.to("#{k}",{{opacity:0,duration:0.12,ease:"power2.in"}},{e0-0.12:.2f});')
    bj.append(f'    tl.set("#{k}",{{opacity:0,visibility:"hidden"}},{e0});')
_bc=[b for b in BR if b[0]=="b-claim"][0]
bj += fx_js('cl',CLAIM_FX[2],CLAIM_FX[3],_bc[1],_bc[2],R(32.19),-300,2150,None,'b-claim-shine')
open(f"{P}/compositions/broll.html","w").write('''<template>
  <style>
    #root { position:absolute; inset:0; pointer-events:none; }'''+FX_CSS+'''
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
    .store { width:76px; height:76px; border-radius:20px; background:#fff; padding:8px; display:flex; flex:none; box-shadow:0 8px 22px rgba(80,10,0,.3); }
    .store svg { width:100%; height:100%; }
    .chip-ic, .bi { width:62px; height:62px; border-radius:18px; background:#fff; color:#EE4D2D; padding:12px; display:flex; flex:none; }
    .chip-ic svg, .bi svg { width:100%; height:100%; }
    .phone { position:absolute; left:271px; top:318px; width:418px; height:890px; border-radius:54px; background:#111; padding:12px;
             box-shadow:0 30px 70px rgba(80,10,0,.45), 0 0 0 4px rgba(255,255,255,.55); }
    .screen { position:relative; width:100%; height:100%; border-radius:44px; overflow:hidden; background:#fff; }
    /* official campaign banner (4:5) inside the safe column, captions sit below at 1236 */
    .poster { position:absolute; left:110px; top:250px; width:740px; height:925px; border-radius:40px; overflow:hidden;
              box-shadow:0 30px 70px rgba(80,10,0,.45), 0 0 0 8px #fff; background:#fff; }
    .poster-img { position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; }
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


# ---------- sound-effect cue list (same clock as the graphics) ----------
EV=[]
for k,a,b,h,ex in KW:
    if k=="k-rm100":
        EV+= [(a-0.05,"whoosh"),(a,"pop_big"),(a+0.15,"coins"),(R(3.28),"chime"),(R(3.28)+0.05,"coins")]
    elif k=="k-senang":
        EV+= [(a,"boing")]+[(a+0.035*i+0.12,"tick_pop") for i in range(0,6,2)]+[(R(23.02),"pop"),(R(23.14),"ding")]
    elif k=="k-cta":
        EV+= [(a-0.05,"whoosh"),(a,"pop_big")]
    else:
        EV.append((a,"pop"))
    if k=="k-app": EV.append((R(6.88),"pop_small"))
    if k=="k-steps": EV+= [(R(28.10),"ding"),(R(28.85),"pop_small")]
    if k=="k-coins": EV.append((R(18.9),"ticks"))
for k,a,b,media,chip,ex in BR:
    EV.append((a-0.08,"whoosh"))
    EV.append((a+0.06,"pop_big" if "poster-img" in media else "pop"))
    if k=="b-bil": EV+= [(R(15.61),"pop_small"),(R(16.51),"pop_small"),(R(16.97),"pop_small")]
    if k=="b-claim": EV+= [(a+0.15,"coins"),(R(32.19),"chime"),(R(32.19)+0.05,"coins")]
    if k=="b-coins": EV.append((a+0.12,"coins"))
import json as _j
_j.dump({"dur":DUR,"events":sorted((round(t,3),n) for t,n in EV)},open(sys.argv[3] if len(sys.argv)>3 else "sfx_events.json","w"),indent=0)

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
      <audio id="bgm" class="clip" src="assets/bgm.wav" data-start="0" data-duration="{DUR}" data-track-index="6" data-volume="1"></audio>
      <audio id="sfx" class="clip" src="assets/sfx.wav" data-start="0" data-duration="{DUR}" data-track-index="5" data-volume="0.55"></audio>
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
