/* Merci Studio – TikTok 9:16 scenes, BM text, synced to Malay voiceover (VO from vo_timing.js). */

/* ---------------- camera ---------------- */
function cam(z, fx, fy) { g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-fx, -fy); }

/* ---------------- voiceover helpers ---------------- */
function talking(t, who) {
  for (const l of VO) {
    if (l.v !== who || t < l.t || t > l.t + l.dur) continue;
    for (const w of l.words) if (t >= l.t + w.s && t <= l.t + w.e + .04) return true;
  }
  return false;
}
const say = (t, who, base) => (talking(t, who) ? 'talk' : base);

function staff(o) { return char(Object.assign({ cap: true, shirt: C.shirt, logo: 'STAF', expr: 'happy' }, o)); }
/* ---------------- story clock + HUD ---------------- */
function storyMinutes(t) {
  if (t < 4.6) return -1;
  if (t < 15.4) return 0;
  if (t < 27.2) return lerp(0, 15, seg(t, 15.4, 27.2));
  if (t < 31.4) return 15;
  if (t < 35.8) return lerp(15, 20, seg(t, 31.4, 35.8));
  if (t < 37) return 20;
  if (t < 43) return lerp(20, 30, seg(t, 37, 43));
  if (t < 44.4) return 30;
  if (t < 49.2) return lerp(30, 40, seg(t, 44.4, 49.2));
  return 40;
}
function clockStr(m) {
  const tot = 12 * 60 + Math.floor(m + 1e-6);
  let hh = Math.floor(tot / 60) % 24; const mm = ((tot % 60) + 60) % 60;
  const ap = hh < 12 ? 'PG' : 'TGH'; hh = hh % 12 || 12;
  return `${hh}:${String(mm).padStart(2, '0')} ${ap}`;
}
function mmss(min) { const s = Math.max(0, Math.round(min * 60)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; }
function hudState(t) {
  const m = storyMinutes(t);
  if (t < 14.8) return { label: 'KETIBAAN PELANGGAN', value: t < 4.6 ? 'DALAM PERJALANAN' : 'TEPAT MASA!', prog: t < 4.6 ? seg(t, 0, 4.6) : 1, col: C.green };
  if (t < 27.4) return { label: 'PAKEJ A  ·  SESI SELF PHOTO', value: mmss(15 - Math.max(0, m)) + ' LAGI', prog: Math.max(0, m) / 15, col: C.green };
  if (t < 31.0) return { label: 'PAKEJ A  ·  SESI SELF PHOTO', value: 'SELESAI!', prog: 1, col: C.green };
  if (t < 36.4) return { label: 'MUAT TURUN GAMBAR  ·  5 MIN', value: mmss(20 - m) + ' LAGI', prog: (m - 15) / 5, col: '#5bb8ff' };
  if (t < 43.4) return { label: 'PILIH GAMBAR  ·  10 MIN', value: mmss(30 - m) + ' LAGI', prog: (m - 20) / 10, col: '#c08bff' };
  if (t < 49.6) return { label: 'CETAK 2 KEPING  ·  10 MIN', value: mmss(40 - m) + ' LAGI', prog: (m - 30) / 10, col: '#ff9f5a' };
  return { label: 'SEMUA SIAP!', value: 'GAMBAR + SOFTCOPY', prog: 1, col: C.green };
}
const HUD_Y = 150;
function drawHUD(t) {
  const a = 1 - seg(t, 54.6, 55.2);
  if (a <= 0) return;
  const st = hudState(t);
  g.save(); g.globalAlpha = a;
  const w = 720, h = 150, x = W / 2 - w / 2, y = HUD_Y;
  shadowOn(24, 10, .3); rr(x, y, w, h, 30); fs(C.navy); shadowOff();
  rr(x, y, w, h, 30); fs(null, '#0e1119', 5);
  text(st.label, W / 2, y + 30, F(800, 24), '#aab3c5');
  text(st.value, W / 2, y + 78, F(900, 54), C.yellow);
  rr(x + 46, y + 114, w - 92, 16, 8); fs('#3a4152');
  rr(x + 46, y + 114, Math.max(16, (w - 92) * clamp(st.prog)), 16, 8); fs(st.col);
  const m = storyMinutes(t);
  const flip = t >= 4.6 && t < 5.1 ? pop(t, 4.6, .4) : 1;
  g.save(); g.translate(W / 2, y + h + 46); g.scale(flip, flip);
  rr(-150, -32, 300, 64, 32); fs('#ffffff', C.ink, 5);
  text(clockStr(m), 0, 2, F(800, 36), C.ink);
  g.restore(); g.restore();
}

/* ---------------- captions from VO word timings ---------------- */
const CAP_Y = 1470;
const CAPS = (() => {
  const out = [];
  VO.forEach(l => {
    if (l.t > 55) return; // end card has its own text
    const ws = l.words, chunks = [];
    for (let i = 0; i < ws.length;) {
      const c = [ws[i++]];
      if (i < ws.length && c[0].w.length + ws[i].w.length <= 15 && ws[i].s - c[0].e < .2) c.push(ws[i++]);
      chunks.push(c);
    }
    chunks.forEach((c, k) => {
      const t0 = l.t + c[0].s, t1 = k + 1 < chunks.length ? l.t + chunks[k + 1][0].s : l.t + l.dur + .35;
      out.push({ t0, t1, words: c.map(w => ({ w: w.w.toUpperCase(), on: l.hl.includes(w.w.toLowerCase()) })) });
    });
  });
  return out;
})();
function drawCaption(t) {
  const c = CAPS.find(c => t >= c.t0 && t < c.t1);
  if (!c) return;
  const p = pop(t, c.t0, .2);
  g.save(); g.translate(W / 2, CAP_Y);
  g.font = F(900, 88);
  const gap = 24;
  const widths = c.words.map(wd => g.measureText(wd.w).width);
  const total = widths.reduce((a, b) => a + b, 0) + gap * (c.words.length - 1);
  const fit = Math.min(1, 980 / total);
  g.scale(p * fit, p * fit);
  let x = -total / 2;
  c.words.forEach((wd, i) => {
    g.textAlign = 'left'; g.textBaseline = 'middle'; g.lineJoin = 'round';
    g.strokeStyle = '#1b1d26'; g.lineWidth = 20; g.strokeText(wd.w, x, 7); g.strokeText(wd.w, x, 0);
    g.fillStyle = wd.on ? C.yellow : '#ffffff'; g.fillText(wd.w, x, 0);
    x += widths[i] + gap;
  });
  g.restore();
}

/* ====================================================================== */
/* SCENE 0 – cartoon Merci Studio building (0 – 9.9)                      */
/* ====================================================================== */
const MAROON = '#b0464c', MAROON2 = '#8b3238';
function cloud(x, y, s) {
  g.save(); g.translate(x, y); g.scale(s, s);
  const puffs = [[0, 0, 70], [70, -34, 64], [140, 0, 70], [70, 22, 62], [-60, 18, 50], [200, 22, 48]];
  g.fillStyle = '#c9d3df'; puffs.forEach(([a, b, r]) => { circle(a + 6, b + 12, r); g.fill(); });
  g.fillStyle = '#ffffff'; puffs.forEach(([a, b, r]) => { circle(a, b, r); g.fill(); });
  g.restore();
}
function louvre(x, y, w, h) {
  rr(x, y, w, h, 4); fs('#c9ccd2', C.ink, 4);
  g.strokeStyle = '#8c9098'; g.lineWidth = 3;
  for (let yy = y + 12; yy < y + h - 4; yy += 14) line(x + 6, yy, x + w - 6, yy);
}
function shophouse(t) {
  // neighbour left
  g.fillStyle = '#f1f0ec'; g.fillRect(-500, 500, 620, 460);
  rr(-470, 540, 540, 150, 6); fs('#fafafa', C.ink, 5);
  text('SYARIKAT AKAUNTAN', -200, 590, F(900, 38), '#2b2c31');
  text('AKAUNTAN BERTAULIAH', -200, 645, F(800, 26), '#2b2c31');
  g.fillStyle = '#9fb3bd'; g.fillRect(-460, 740, 520, 200); g.strokeStyle = C.ink; g.lineWidth = 4; g.strokeRect(-460, 740, 520, 200);
  g.fillStyle = MAROON; g.fillRect(-500, 440, 620, 60);
  // neighbour right
  g.fillStyle = '#f1f0ec'; g.fillRect(960, 500, 600, 460);
  louvre(1000, 560, 130, 380);
  g.fillStyle = MAROON; g.fillRect(960, 440, 600, 60);
  g.fillStyle = MAROON; g.fillRect(1180, 500, 50, 810);
  // ---- main unit ----
  g.fillStyle = '#f4f3ef'; g.fillRect(150, 480, 790, 480);
  g.fillStyle = '#ffffff'; g.fillRect(170, 410, 750, 70);
  rr(110, 380, 870, 56, 6); fs(MAROON, C.ink, 5);
  g.fillStyle = MAROON2; g.fillRect(116, 428, 858, 8);
  rr(100, 430, 64, 540, 4); fs(MAROON, C.ink, 5);
  rr(926, 430, 64, 540, 4); fs(MAROON, C.ink, 5);
  // signboard (cartoon version of the real sign)
  shadowOn(16, 8, .25); rr(190, 520, 710, 170, 8); fs('#eceef5'); shadowOff();
  rr(190, 520, 710, 170, 8); fs(null, '#3b3e46', 7);
  const glow = g.createLinearGradient(0, 520, 0, 690); glow.addColorStop(0, 'rgba(255,255,255,.7)'); glow.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = glow; g.fillRect(196, 526, 698, 80);
  text('KEDAI GAMBAR', 214, 546, F(700, 17), '#5a5e68', 'left');
  text('MERCI STUDIO', 549, 608, F(800, 74), '#9ea3ad');
  text('MERCI STUDIO', 545, 602, F(800, 74), '#33363e');
  text('MIRROR PHOTOBOOTH  X  HIGH ANGLE  X  SELF PHOTO', 545, 662, F(800, 19), '#33363e');
  // louvres + window
  louvre(180, 720, 100, 230); louvre(810, 720, 100, 230);
  rr(300, 710, 490, 240, 4); fs('#f8f8f8', C.ink, 5);
  const gl = g.createLinearGradient(310, 720, 780, 940); gl.addColorStop(0, '#30404c'); gl.addColorStop(.5, '#3f5664'); gl.addColorStop(1, '#25313a');
  g.fillStyle = gl; g.fillRect(314, 724, 462, 212);
  g.fillStyle = 'rgba(255,255,255,.12)'; g.beginPath(); g.moveTo(360, 724); g.lineTo(440, 724); g.lineTo(340, 936); g.lineTo(314, 936); g.lineTo(314, 820); g.closePath(); g.fill();
  g.strokeStyle = '#f8f8f8'; g.lineWidth = 9; line(470, 724, 470, 936); line(630, 724, 630, 936); line(314, 790, 776, 790);
  // ground floor
  g.fillStyle = '#e9e8e4'; g.fillRect(150, 960, 790, 350);
  rr(140, 972, 810, 92, 6); fs('#22357a', C.ink, 5);
  text('KEDAI PERKAKASAN', 545, 1006, F(900, 40), '#ffffff');
  text('PEMBEKAL BAHAN BINAAN, SIMEN DAN BATU PASIR', 545, 1046, F(700, 16), '#dfe6ff');
  // shop opening
  rr(440, 1084, 470, 226, 4); fs('#3b3631', C.ink, 5);
  for (let r = 0; r < 3; r++) for (let k = 0; k < 6; k++) {
    const bx = 470 + k * 72, by = 1250 - r * 52;
    rr(bx, by - 40, 52, 46, 6); fs('#f6f6f6', C.ink, 3);
    g.fillStyle = ['#3b82f6', '#ff7b86', '#ffc83d', '#58d26a'][(k + r) % 4]; g.fillRect(bx + 3, by - 26, 46, 14);
  }
  // stair door to the studio
  rr(190, 1110, 210, 200, 4); fs('#cdd1d6', C.ink, 5);
  g.strokeStyle = '#7b8089'; g.lineWidth = 5; for (let x = 206; x < 396; x += 20) line(x, 1116, x, 1306);
  rr(222, 1084, 64, 22, 4); fs('#ffffff', C.ink, 3); text('12-1', 254, 1095, F(800, 14), C.ink);
  rr(214, 1140, 162, 70, 10); fs('#ffffff', C.ink, 4);
  text('MERCI STUDIO', 295, 1163, F(900, 20), C.ink); text('TINGKAT 1  ↑', 295, 1190, F(800, 17), C.coral);
  // columns
  rr(116, 960, 40, 350, 4); fs('#f7f7f5', C.ink, 4); rr(934, 960, 40, 350, 4); fs('#f7f7f5', C.ink, 4);
  // bush
  [[40, 1290, 60], [90, 1270, 55], [10, 1250, 45], [70, 1235, 45]].forEach(([x, y, r]) => { circle(x, y, r); fs('#3f7d4a', '#24432a', 4); });
}
function street() {
  g.fillStyle = vgrad(1310, 1560, ['#e7e0d6', '#cfc3b4']); g.fillRect(-600, 1310, 2400, 260);
  g.strokeStyle = 'rgba(90,70,50,.2)'; g.lineWidth = 3;
  for (let i = -4; i < 14; i++) line(i * 120, 1310, i * 120 - 60, 1560);
  g.fillStyle = '#b8aea0'; g.fillRect(-600, 1560, 2400, 24);
  g.fillStyle = '#4a4e57'; g.fillRect(-600, 1584, 2400, 700);
  g.fillStyle = '#f2f2f2'; for (let i = -4; i < 14; i++) g.fillRect(i * 160, 1760, 90, 14);
}
function sceneArrive(t) {
  const pull = ease(seg(t, .2, 3.0));
  g.save(); cam(lerp(1.5, 1.14, pull) + seg(t, 3.0, 6.4) * .04, lerp(545, 520, pull), lerp(640, 930, pull));
  g.fillStyle = vgrad(-400, 1300, ['#8ea8c3', '#cbd8e4', '#eef2f5']); g.fillRect(-1000, -800, 3200, 2400);
  cloud(-100 + t * 12, 120, 1.1); cloud(560 + t * 8, 40, .9); cloud(900 + t * 10, 250, .8);
  shophouse(t);
  street();
  const p = seg(t, .4, 3.4);
  const walking = p > 0 && p < 1;
  const arrived = t > 3.5;
  const x = lerp(-180, 300, ease(p));
  const jump = t > 4.6 && t < 5.7 ? Math.sin(seg(t, 4.6, 5.5) * PI) * 70 : 0;
  customer({ x, y: 1400, s: .9, t, walk: walking ? t * 9 : null, aL: walking ? .32 + Math.sin(t * 9) * .4 : (t > 5.8 ? 2.6 + Math.sin(t * 9) * .3 : .3),
    aR: walking ? .32 - Math.sin(t * 9) * .4 : (t > 4.6 && t < 5.8 ? 2.6 : .3), expr: say(t, 'Y', arrived && t > 4.6 ? 'joy' : 'happy'), lx: 6, blink: blinking(t, 1), jump });
  if (t > 4.6 && t < 5.9) for (let i = 0; i < 4; i++) sparkle(300 + Math.cos(i * 1.6) * 210, 960 + Math.sin(i * 1.6) * 80, pop(t, 4.6 + i * .08), C.yellow, t * 2 + i);
  g.restore();
}

/* ====================================================================== */
/* SCENE 1a – stairs, real photo (9.9 – 14.2)                             */
/* ====================================================================== */
function bgPhoto(key) { g.drawImage(IMG[key + 'Blur'], -150, -150, W + 300, H + 300); }
function sceneStairs(t) {
  g.save(); cam(1 + seg(t, 6.2, 9.6) * .05, 540, 960);
  bgPhoto('stairs');
  g.fillStyle = 'rgba(255,250,244,.3)'; g.fillRect(-200, -200, W + 400, H + 400);
  polaroid(IMG.stairs, 540, 450, 660, -.02, 'JOM NAIK!', 1);
  const baseX = -10, baseY = 1620, sw = 160, sh = 46, n = 6;
  g.fillStyle = '#ece8e3'; g.fillRect(-200, baseY, 1500, 500);
  for (let i = n - 1; i >= 0; i--) {
    const x0 = baseX + i * sw, top = baseY - (i + 1) * sh;
    g.fillStyle = '#3f424b'; g.fillRect(x0, top, 1300 - x0, sh + 4);
    g.fillStyle = '#5b5e68'; g.fillRect(x0, top, 1300 - x0, 13);
    g.strokeStyle = '#25272e'; g.lineWidth = 3; line(x0, top, x0, top + sh);
  }
  const p = seg(t, 6.6, 9.2);
  const x = lerp(-60, 1000, ease(p));
  const fi = (x - baseX) / sw, k = clamp(Math.floor(fi) + 1, 0, n), frac = fi - Math.floor(fi);
  const y = baseY - k * sh - (fi > 0 && fi < n ? Math.sin(frac * PI) * 24 : 0);
  customer({ x, y, s: .82, t, walk: p > 0 && p < 1 ? t * 10 : null, aL: .5 + Math.sin(t * 10) * .4, aR: .5 - Math.sin(t * 10) * .4, expr: say(t, 'Y', 'grin'), blink: blinking(t, 2) });
  g.restore();
}

/* ====================================================================== */
/* Reception world (vertical)                                             */
/* ====================================================================== */
function receptionWorld(t) {
  room(1250);
  warmPool(260, 600, 600, .45); warmPool(800, 900, 600, .3);
  pendant(200, 330); pendant(290, 400);
  merciSign(110, 650, .95);
  plant(150, 1250, 1.25);
  frameOnWall(640, 520, 140, 170, 0); frameOnWall(820, 560, 130, 130, 3);
  wallClock(905, 820, 62, storyMinutes(t));
}
function receptionCounter() { counter(560, 1120, 470, 130); }

/* SCENE 1b – Welcome (14.2 – 22.4) */
function sceneWelcome(t) {
  g.save(); cam(1.0 + seg(t, 9.2, 15) * .05, 540, 960);
  receptionWorld(t);
  staff({ x: 820, y: 1250, face: -1, t, aL: .35, aR: t > 9.6 && t < 11.9 ? 2.5 + Math.sin(t * 9) * .35 : .3, expr: say(t, 'S', 'joy'), blink: blinking(t, 3) });
  receptionCounter();
  const p = seg(t, 9.5, 10.9), walking = p > 0 && p < 1;
  customer({ x: lerp(-180, 330, ease(p)), y: 1330, s: 1.05, t, walk: walking ? t * 9 : null,
    aL: walking ? .3 + Math.sin(t * 9) * .4 : .3, aR: t > 12.3 && t < 13.1 ? 2.6 + Math.sin(t * 10) * .3 : (walking ? .3 - Math.sin(t * 9) * .4 : .3),
    expr: say(t, 'Y', 'grin'), lx: 8, blink: blinking(t, 4) });
  g.restore();
}

/* ====================================================================== */
/* SCENE 2/3 – Self-photo studio + waiting lounge (22.4 – 47.4)           */
/* ====================================================================== */
const POSES = [
  { t: 20.4, d: .9, expr: 'grin', aR: 2.3, aL: .4, peaceL: true },
  { t: 22.3, d: .9, expr: 'wink', aL: 2.95, aR: 2.4, tilt: -.1 },
  { t: 24.3, d: .9, expr: 'joy', aL: 2.8, aR: 2.8 },
  { t: 25.9, d: .9, expr: 'joy', aL: 2.5, aR: 2.5, jump: 1 },
];
const FLASHES = POSES.map(p => ({ t: p.t + p.d }));
function flashAmt(t) { let f = 0; FLASHES.forEach(fl => { if (t >= fl.t && t < fl.t + .45) f = Math.max(f, 1 - (t - fl.t) / .45); }); return f; }
function photosTaken(t) { return FLASHES.filter(f => t >= f.t).length * 12; }

function remoteProp(press) {
  g.save(); g.rotate(-.3);
  rr(-14, -44, 28, 58, 8); fs('#22252e', C.ink, 4);
  circle(0, -24, 8); fs(press > 0 ? '#ff5d6c' : '#c33b48');
  g.restore();
  if (press > 0) { g.strokeStyle = `rgba(255,200,61,${press})`; g.lineWidth = 5; circle(-10, -30, 26 + (1 - press) * 30); g.stroke(); }
}
function softboxV(x, y, rot, flash) {
  g.save();
  g.strokeStyle = C.ink; g.lineWidth = 8; g.lineCap = 'round'; line(x, y, x, 1260); line(x, 1260, x - 60, 1285); line(x, 1260, x + 60, 1285);
  g.translate(x, y); g.rotate(rot);
  rr(-30, -10, 60, 34, 6); fs('#2f323d', C.ink, 5);
  g.beginPath(); g.moveTo(-120, -150); g.lineTo(120, -150); g.lineTo(46, -6); g.lineTo(-46, -6); g.closePath(); fs('#2f323d', C.ink, 6);
  g.beginPath(); g.moveTo(-112, -146); g.lineTo(112, -146); g.lineTo(100, -132); g.lineTo(-100, -132); g.closePath(); fs(`rgba(255,250,235,${.75 + flash * .25})`);
  g.restore();
}
function studioWorld(t) {
  const fl = flashAmt(t);
  room(1250, ['#f3e6da', '#e5d3c1']);
  g.fillStyle = '#5a4a40'; rr(220, 430, 700, 30, 15); g.fill();
  g.fillStyle = vgrad(450, 1300, ['#f9dfd8', C.paper, '#f0c7bf']);
  g.beginPath(); g.moveTo(240, 450); g.lineTo(900, 450); g.lineTo(900, 1180); g.quadraticCurveTo(900, 1260, 980, 1310);
  g.lineTo(160, 1310); g.quadraticCurveTo(240, 1260, 240, 1180); g.closePath(); g.fill();
  warmPool(580, 900, 520, .35 + fl * .45);
  softboxV(150, 760, .45, fl);
  if (fl > 0) { g.save(); g.globalAlpha = fl * .6; const gr = g.createRadialGradient(200, 640, 10, 200, 640, 420); gr.addColorStop(0, '#fffdf2'); gr.addColorStop(1, 'rgba(255,253,242,0)'); g.fillStyle = gr; g.fillRect(-300, 200, 1000, 900); g.restore(); }
  wallClock(960, 560, 50, storyMinutes(t));
  // door to the lounge
  g.fillStyle = '#e9dccd'; g.fillRect(1080, -300, 120, 1550);
  rr(1095, 700, 90, 550, 8); fs('#c99a6c', C.ink, 5);
  // lounge (x offset 1200)
  g.save(); g.translate(1200, 0);
  warmPool(540, 800, 620, .4); pendant(420, 420); pendant(700, 360);
  rr(120, 620, 360, 300, 10); fs('#cfe7f7', C.ink, 6); g.strokeStyle = C.ink; g.lineWidth = 5; line(300, 620, 300, 920); line(120, 770, 480, 770);
  text('RUANG MENUNGGU', 540, 540, F(800, 38), '#6b5644');
  frameOnWall(640, 650, 120, 150, 5); frameOnWall(800, 690, 130, 130, 1);
  sofa(540, 1310, '#f2a85a');
  plant(940, 1260, .8);
  g.restore();
}
function sceneStudio(t) {
  const panP = ease(seg(t, 29.0, 30.2));
  let z = lerp(1.12, 1.18, seg(t, 14.8, 27.4)), fx = 560 + panP * 1200, fy = 970;
  if (t > 27.4) z = lerp(1.18, 1.12, ease(seg(t, 27.4, 28.6)));
  g.save(); cam(z, fx, fy);
  studioWorld(t);
  let pose = null; POSES.forEach(p => { if (t >= p.t - .3) pose = p; });
  const pp = pose ? seg(t, pose.t - .3, pose.t + .2) : 0;
  const hasRemote = t > 15.9;
  const press = FLASHES.reduce((a, f) => (t >= f.t - .2 && t < f.t + .2 ? 1 - Math.abs(t - f.t) / .2 : a), 0);
  const holdRemote = hasRemote ? () => remoteProp(press) : null;
  if (t < 29.0) {
    const done = t > 27.4;
    const jumpAmt = done ? Math.abs(Math.sin(seg(t, 27.6, 29.0) * PI * 2)) * 70 : (pose && pose.jump ? Math.sin(seg(t, pose.t + .2, pose.t + 1.1) * PI) * 100 : 0);
    const intro = !pose || t < 20.1;
    customer({ x: 560, y: 1300, s: 1.15, t, noBag: true,
      expr: say(t, 'Y', done ? 'joy' : (intro ? 'happy' : pose.expr)),
      aL: done ? 2.7 : (intro ? .3 : lerp(.3, pose.aL ?? .3, pp)),
      aR: done ? 2.7 : (intro ? (t > 15.5 && t < 16.1 ? 1.3 : .5) : lerp(.5, pose.aR ?? .5, pp)),
      peaceL: !done && !intro && pose.peaceL && pp > .6, tilt: done || intro ? 0 : (pose.tilt || 0) * pp,
      jump: jumpAmt, blink: blinking(t, 5) && !done, holdR: holdRemote });
  } else {
    const p = seg(t, 29.0, 30.2), walking = p > 0 && p < 1;
    if (t < 30.2) customer({ x: lerp(560, 1740, ease(p)), y: 1300, s: 1.15, t, walk: walking ? t * 12 : null, aL: .3 + Math.sin(t * 12) * .4, aR: .3 - Math.sin(t * 12) * .4, expr: say(t, 'Y', 'grin'), blink: blinking(t, 6) });
    else customer({ x: 1740, y: 1230, s: 1.08, t, sit: true, aL: .7, aR: .7, expr: say(t, 'Y', 'happy'), lx: 8, ly: -6, blink: blinking(t, 6), bob: Math.sin(t * 3) * 2 });
  }
  tripod(880, 1320, 300);
  camera(880, 1010, .8, flashAmt(t));
  // staff hands over the remote, then leaves the room (no photographer)
  if (t < 19.0) {
    const leave = seg(t, 17.4, 18.9), lw = leave > 0 && leave < 1;
    staff({ x: lerp(760, 1260, ease(leave)), y: 1320, face: leave > 0 ? 1 : -1, t, walk: lw ? t * 9 : null,
      aR: leave > 0 ? .3 + Math.sin(t * 9) * .3 : (t < 15.9 ? lerp(.3, 1.35, seg(t, 15.0, 15.5)) : (t < 17.2 ? 2.5 + Math.sin(t * 9) * .3 : .3)),
      aL: leave > 0 ? 2.6 + Math.sin(t * 9) * .3 : .3,
      holdR: t < 15.9 ? () => remoteProp(0) : null, expr: say(t, 'S', 'joy'), blink: blinking(t, 7) });
  }
  FLASHES.forEach(f => {
    const q = seg(t, f.t, f.t + .6);
    if (q > 0 && q < 1) { g.save(); g.globalAlpha = 1 - q; text('KLIK!', 880, 860 - q * 60, F(900, 46), C.yellow, 'center', C.ink, 10); g.restore(); }
  });
  FLASHES.forEach((f, i) => {
    const q = seg(t, f.t + .1, f.t + 1.0);
    if (q > 0 && q < 1) {
      const x = lerp(860, 190, ease(q)), y = lerp(1000, 470, ease(q)) - Math.sin(q * PI) * 120;
      printPhoto(x, y, 90 * (1 - q * .5), i, Math.sin(q * 6) * .3);
    }
  });
  if (t > 27.4 && t < 29.1) {
    const sp = pop(t, 27.5, .4);
    g.save(); g.translate(560, 720); g.rotate(-.12); g.scale(sp, sp);
    rr(-230, -70, 460, 140, 30); fs(C.coral, C.ink, 7);
    text('SIAP!  12:15', 0, 4, F(900, 64), '#ffffff', 'center', C.ink, 10);
    g.restore();
    for (let i = 0; i < 6; i++) sparkle(560 + Math.cos(i + t) * 330, 760 + Math.sin(i * 2 + t) * 180, sp * .9, C.yellow, t + i);
  }
  if (t > 30.2) {
    const q = pop(t, 30.3, .4);
    g.save(); g.translate(1620, 820); g.scale(q, q);
    circle(110, 130, 14); fs('#fff', C.ink, 4); circle(140, 160, 9); fs('#fff', C.ink, 4);
    g.beginPath(); g.ellipse(0, 0, 220, 125, 0, 0, TAU); fs('#ffffff', C.ink, 6);
    [-1, 0, 1].forEach(k => printPhoto(k * 115, -6 + Math.sin(t * 4 + k) * 6, 82, k + 3, k * .15));
    g.restore();
  }
  g.restore();
  if (t > 15.0 && t < 29.0) {
    const a = seg(t, 15.0, 15.5) * (1 - seg(t, 28.5, 29.0));
    g.save(); g.globalAlpha = a; g.translate(190, 470);
    rr(-150, -42, 300, 84, 24); fs('#ffffff', C.ink, 5);
    g.save(); g.translate(-100, 0); g.scale(.45, .45); camera(0, 30, 1, 0); g.restore();
    text(`${photosTaken(t)} GAMBAR`, 30, 2, F(900, 30), C.ink);
    g.restore();
  }
  const fl = flashAmt(t);
  if (fl > 0) { g.fillStyle = `rgba(255,255,250,${fl * .5})`; g.fillRect(0, 0, W, H); }
}

/* ====================================================================== */
/* SCENE 4 – Download (47.4 – 57.4)                                       */
/* ====================================================================== */
function monitorScreen(t, x, y, w, h) {
  g.save(); rr(x, y, w, h, 8); g.clip();
  g.fillStyle = '#f4f6fb'; g.fillRect(x, y, w, h);
  g.fillStyle = '#e4e8f2'; g.fillRect(x, y, w, 48);
  [['#ff6b6b', 0], ['#ffc83d', 1], ['#58d26a', 2]].forEach(([c, i]) => { circle(x + 26 + i * 26, y + 24, 8); fs(c); });
  text('MERCI STUDIO  ·  SESI 12:00 TGH', x + w / 2 + 30, y + 25, F(800, 19), '#4b5163');
  const dl = seg(t, 31.7, 33.9);
  if (t < 34.0) {
    g.save(); g.translate(x + w / 2, y + h * .38);
    rr(-90, -66, 80, 24, 6); fs('#ffb84d'); rr(-90, -54, 180, 124, 12); fs('#ffc85f', C.ink, 4);
    g.restore();
    text(dl < 1 ? 'Sedang muat turun gambar...' : 'Muat turun selesai!', x + w / 2, y + h * .64, F(800, 32), C.ink);
    rr(x + 90, y + h * .72, w - 180, 28, 14); fs('#dde2ec');
    rr(x + 90, y + h * .72, Math.max(28, (w - 180) * dl), 28, 14); fs('#5bb8ff');
    text(`${Math.round(dl * 48)} / 48 gambar   ·   ${Math.round(dl * 100)}%`, x + w / 2, y + h * .85, F(700, 24), '#4b5163');
  } else {
    const cols = 4, gap = 14, tw = (w - gap * (cols + 1)) / cols, th = tw * .78;
    const scroll = ease(seg(t, 35.0, 36.4)) * (th + gap) * 3;
    for (let i = 0; i < 48; i++) {
      const c = i % cols, r = Math.floor(i / cols);
      const ap = seg(t, 34.0 + i * .025, 34.3 + i * .025);
      if (ap <= 0) continue;
      const px = x + gap + c * (tw + gap), py = y + 62 + r * (th + gap) - scroll;
      if (py > y + h || py + th < y + 48) continue;
      g.save(); g.globalAlpha = ap; const s = .7 + .3 * back(ap);
      g.translate(px + tw / 2, py + th / 2); g.scale(s, s);
      miniPhoto(-tw / 2, -th / 2, tw, th, i, { lw: 2 }); g.restore();
    }
  }
  g.restore();
}
function sceneDownload(t) {
  const zin = ease(seg(t, 31.3, 32.3)), zout = ease(seg(t, 35.6, 36.6));
  const k = zin - zout * .7;
  g.save(); cam(lerp(1, 1.22, k), 540, lerp(960, 820, k));
  room(1250, ['#eef1f4', '#dfe4ea']);
  warmPool(540, 700, 650, .35);
  rr(70, 380, 330, 290, 10); fs('#cfe7f7', C.ink, 6); g.strokeStyle = C.ink; g.lineWidth = 5; line(235, 380, 235, 670); line(70, 525, 400, 525);
  wallClock(900, 470, 60, storyMinutes(t));
  // desk
  rr(40, 1080, 1000, 36, 10); fs('#c99a6c', C.ink, 6);
  g.fillStyle = C.ink; g.fillRect(80, 1116, 24, 200); g.fillRect(976, 1116, 24, 200);
  // monitor
  rr(520, 1000, 40, 84, 6); fs('#bfc5d1', C.ink, 5); rr(450, 1068, 180, 18, 8); fs('#bfc5d1', C.ink, 5);
  rr(110, 570, 860, 450, 22); fs('#2a2d37', C.ink, 6);
  monitorScreen(t, 130, 590, 820, 410);
  rr(330, 1054, 260, 26, 8); fs('#e9ecf2', C.ink, 4);
  // card reader
  rr(140, 1056, 80, 24, 6); fs('#3a3e4b', C.ink, 4);
  circle(208, 1068, 5); fs(t > 31.7 && t < 33.9 && Math.floor(t * 6) % 2 ? '#58d26a' : '#2b8a3e');
  const cardIn = ease(seg(t, 31.0, 31.5));
  rr(160, 1020 + cardIn * 32, 36, 44, 4); fs('#3b82f6', C.ink, 3);
  // owner on chair
  rr(860, 1080, 150, 200, 30); fs('#3b3f4c', C.ink, 6);
  staff({ x: 900, y: 1190, face: -1, t, sit: true, aL: 1.2, aR: t > 34.3 ? 2.8 : .5, thumbR: t > 34.3, expr: say(t, 'S', t > 34.0 ? 'joy' : 'happy'), lx: 6, ly: -4, blink: blinking(t, 8) });
  g.strokeStyle = C.ink; g.lineWidth = 9; line(935, 1280, 935, 1320); line(890, 1320, 980, 1320);
  g.restore();
}

/* ====================================================================== */
/* SCENE 5 – Selection on iPad (57.4 – 69.4)                              */
/* ====================================================================== */
const SELECT_TAPS = [39.8, 41.3];
const SELECT_IDS = [4, 6];
const ZOOM_ID = 7;
const PRINT_TAP = 42.7;
function selectedCount(t) { return SELECT_TAPS.filter(x => t >= x).length; }
function ipadUI(t, x, y, w, h) {
  const cols = 3, gap = 22, tw = (w - gap * (cols + 1)) / cols, th = tw * 1.1;
  const scroll = ease(seg(t, 38.8, 39.5)) * (th + gap) * 1.0;
  const cell = i => [x + gap + (i % cols) * (tw + gap), y + 124 + Math.floor(i / cols) * (th + gap) - scroll];
  g.save(); rr(x, y, w, h, 18); g.clip();
  g.fillStyle = '#fbfaf8'; g.fillRect(x, y, w, h);
  for (let i = 0; i < 21; i++) {
    const [px, py] = cell(i);
    if (py > y + h || py + th < y + 100) continue;
    miniPhoto(px, py, tw, th, i, { stroke: false, r: 12 });
    const si = SELECT_IDS.indexOf(i);
    if (si >= 0 && t >= SELECT_TAPS[si]) {
      const q = pop(t, SELECT_TAPS[si], .35);
      rr(px, py, tw, th, 12); fs(null, C.coral, 8);
      g.save(); g.translate(px + tw - 36, py + 36); g.scale(q, q);
      circle(0, 0, 26); fs(C.coral, '#fff', 4); heart(0, 8, .85, '#ffffff'); g.restore();
    }
  }
  // header
  const n = selectedCount(t);
  g.fillStyle = '#ffffff'; g.fillRect(x, y, w, 104);
  g.fillStyle = 'rgba(0,0,0,.06)'; g.fillRect(x, y + 104, w, 3);
  text('Pilih gambar kegemaran', x + 34, y + 52, F(800, 34), C.ink, 'left');
  const ready = t > PRINT_TAP - .9;
  rr(x + w - 250, y + 26, 220, 54, 27); fs(ready ? C.coral : '#eceef3');
  text(ready ? 'CETAK 2 KEPING' : `DIPILIH ${n} / 2`, x + w - 140, y + 54, F(900, 21), ready ? '#fff' : C.ink);
  // zoomed photo
  const zp = 0;
  if (zp > .001) {
    g.fillStyle = `rgba(20,20,28,${.75 * zp})`; g.fillRect(x, y, w, h);
    const [sx, sy] = cell(ZOOM_ID);
    const pinch = 1 + ease(seg(t, 62.9, 63.5)) * .15;
    const fw = (w - 60) * pinch, fh = fw * 1.1;
    const cx = lerp(sx + tw / 2, x + w / 2, zp), cy = lerp(sy + th / 2, y + 104 + (h - 104) / 2, zp);
    const ww = lerp(tw, fw, zp), hh = lerp(th, fh, zp);
    miniPhoto(cx - ww / 2, cy - hh / 2, ww, hh, ZOOM_ID, { stroke: false, r: 16 });
    if (t > 63.9) { const q = pop(t, 63.9); g.save(); g.translate(cx + ww / 2 - 80, cy - hh / 2 + 80); g.scale(q * 1.6, q * 1.6); circle(0, 0, 26); fs(C.coral, '#fff', 4); heart(0, 8, .85, '#fff'); g.restore(); }
  }
  g.restore();
}
function fingerPath(t) {
  const K = [[38.0, .7, 1.2], [38.7, .55, .8], [39.3, .55, .45], [39.6, .5, .35], [39.8, .5, .3], [40.6, .2, .58], [41.3, .18, .6], [42.3, .8, .07], [42.7, .82, .07], [43.4, .9, 1.3]];
  if (t <= K[0][0]) return [K[0][1], K[0][2]];
  for (let i = 1; i < K.length; i++) if (t <= K[i][0]) { const q = ease(seg(t, K[i - 1][0], K[i][0])); return [lerp(K[i - 1][1], K[i][1], q), lerp(K[i - 1][2], K[i][2], q)]; }
  return [K[K.length - 1][1], K[K.length - 1][2]];
}
function lounge(t) {
  room(1250, ['#f3e6da', '#e5d3c1']);
  warmPool(540, 800, 620, .45); pendant(420, 420); pendant(700, 360);
  rr(120, 620, 360, 300, 10); fs('#cfe7f7', C.ink, 6); g.strokeStyle = C.ink; g.lineWidth = 5; line(300, 620, 300, 920); line(120, 770, 480, 770);
  text('RUANG MENUNGGU', 540, 540, F(800, 38), '#6b5644');
  frameOnWall(640, 650, 120, 150, 5); frameOnWall(800, 690, 130, 130, 1);
  wallClock(900, 470, 56, storyMinutes(t));
  sofa(540, 1310, '#f2a85a');
}
function sceneSelect(t) {
  if (t < 38.0) {
    const z = lerp(1, 1.08, seg(t, 36.2, 37.3)) + Math.pow(seg(t, 37.3, 38.0), 2) * 3.4;
    g.save(); cam(z, lerp(540, 520, seg(t, 37.3, 38)), lerp(960, 1140, seg(t, 37.3, 38)));
    lounge(t);
    customer({ x: 540, y: 1230, s: 1.12, t, sit: true, aL: 1.25, aR: 1.25, expr: say(t, 'Y', 'grin'), lx: 4, ly: 8, blink: blinking(t, 9),
      holdR: () => { g.save(); g.translate(-30, -10); ipadProp(104, 140, (sx, sy, sw, sh) => { for (let i = 0; i < 6; i++) miniPhoto(sx + 4 + (i % 2) * (sw / 2), sy + 4 + Math.floor(i / 2) * (sh / 3), sw / 2 - 6, sh / 3 - 6, i, { stroke: false, r: 2 }); }); g.restore(); } });
    g.restore();
    if (t > 37.7) { g.fillStyle = `rgba(255,255,255,${seg(t, 37.7, 38.0)})`; g.fillRect(0, 0, W, H); }
    return;
  }
  g.fillStyle = vgrad(0, H, ['#f8e7d8', '#efd2bd']); g.fillRect(0, 0, W, H);
  for (let i = 0; i < 14; i++) { circle(hash(i) * W, hash(i + 9) * H, 50 + hash(i + 3) * 110); g.fillStyle = 'rgba(255,215,170,.28)'; g.fill(); }
  const iw = 880, ih = 960, ix = W / 2 - iw / 2, iy = 470;
  const ent = easeOut(seg(t, 38.0, 38.5));
  g.save(); g.translate(W / 2, iy + ih / 2); g.scale(.9 + .1 * ent, .9 + .1 * ent); g.translate(-W / 2, -(iy + ih / 2));
  shadowOn(50, 24, .35); rr(ix - 34, iy - 34, iw + 68, ih + 68, 60); fs('#262932'); shadowOff();
  rr(ix - 34, iy - 34, iw + 68, ih + 68, 60); fs(null, C.ink, 6);
  ipadUI(t, ix, iy, iw, ih);
  g.restore();
  if (t < 38.3) { g.fillStyle = `rgba(255,255,255,${1 - seg(t, 38.0, 38.3)})`; g.fillRect(0, 0, W, H); }
  const [fx, fy] = fingerPath(t);
  let press = 0; [...SELECT_TAPS, PRINT_TAP].forEach(tp => { if (t >= tp && t < tp + .4) press = 1 - (t - tp) / .4; });
  finger(ix + iw * fx, iy + ih * fy, 1, press);
}

/* ====================================================================== */
/* SCENE 6 – Hand-over + printing (69.4 – 82.2)                           */
/* ====================================================================== */
const PRINT_T0 = 45.0, PRINT_DT = .9, NPRINT = 2;
function printerBox(x, y, t, printing) {
  const vib = printing ? Math.sin(t * 60) * 1.5 : 0;
  g.save(); g.translate(x, y + vib);
  shadowOn(26, 12, .25); rr(-230, -190, 460, 190, 30); fs('#f1f3f7'); shadowOff();
  rr(-230, -190, 460, 190, 30); fs(null, C.ink, 6);
  rr(-200, -160, 170, 70, 12); fs('#1f2533', C.ink, 4);
  text(printing ? 'MENCETAK' : 'SEDIA', -115, -125, F(800, 20), '#7fe39a');
  rr(-170, -60, 340, 20, 10); fs('#2b2e38');
  circle(170, -125, 12); fs(printing && Math.floor(t * 4) % 2 ? '#58d26a' : '#2b8a3e', C.ink, 3);
  text('PENCETAK FOTO', 50, -126, F(800, 16), '#8a90a0');
  g.restore();
}
function sceneHandover(t) {
  g.save(); cam(1.03, 540, 960);
  receptionWorld(t);
  const p = ease(seg(t, 43.5, 44.3));
  staff({ x: 820, y: 1250, face: -1, t, aL: .35, aR: p > .9 ? 1.4 : .3, expr: say(t, 'S', 'happy'), blink: blinking(t, 10) });
  receptionCounter();
  customer({ x: 360, y: 1330, s: 1.05, t, aR: lerp(1.6, .3, seg(t, 44.1, 44.4)), aL: .3, expr: say(t, 'Y', 'joy'), lx: 8, blink: blinking(t, 11) });
  const ipX = lerp(470, 690, p), ipY = lerp(1060, 1010, p) - Math.sin(p * PI) * 70;
  g.save(); g.translate(ipX, ipY); g.rotate(-.1 + p * .2);
  ipadProp(104, 140, (sx, sy, sw, sh) => { for (let i = 0; i < 2; i++) miniPhoto(sx + 4, sy + 4 + i * (sh / 2), sw - 8, sh / 2 - 8, SELECT_IDS[i], { stroke: false, r: 2 }); });
  g.restore();
  g.restore();
}
function scenePrint(t) {
  if (t < 44.6) return sceneHandover(t);
  const checkP = ease(seg(t, 46.9, 47.5));
  g.save(); cam(lerp(1.08, 1.0, checkP), 540, lerp(980, 1000, checkP));
  room(1150, ['#f5ede3', '#eadccb']);
  warmPool(450, 700, 600, .45); pendant(450, 360, 1);
  wallClock(900, 520, 60, storyMinutes(t));
  merciSign(90, 600, .6);
  g.fillStyle = vgrad(1100, 1920, ['#d8ab7d', '#b98a5e']); g.fillRect(-200, 1150, 1500, 900);
  g.fillStyle = '#e5be93'; g.fillRect(-200, 1130, 1500, 30);
  g.strokeStyle = C.ink; g.lineWidth = 6; line(-200, 1130, 1300, 1130);
  const holding = t > 47.3;
  staff({ x: 850, y: 1260, face: -1, t, aL: holding ? 1.9 : .3, aR: holding ? 1.5 : .3, expr: say(t, 'S', holding ? 'wow' : 'happy'), lx: -4, ly: holding ? -4 : 6, blink: blinking(t, 12),
    holdR: holding ? () => { g.save(); g.rotate(-.5); g.strokeStyle = C.ink; g.lineWidth = 12; line(0, 0, 0, -40); g.strokeStyle = '#7a5a3a'; g.lineWidth = 7; line(0, 0, 0, -40); circle(0, -80, 44); fs('rgba(200,235,255,.45)', C.ink, 8); g.restore(); } : null });
  g.fillStyle = vgrad(1100, 1920, ['#d8ab7d', '#b98a5e']); g.fillRect(640, 1180, 600, 800);
  g.strokeStyle = 'rgba(0,0,0,.15)'; g.lineWidth = 3; line(640, 1180, 1240, 1180);
  const printing = t > PRINT_T0 && t < PRINT_T0 + PRINT_DT * NPRINT + .2;
  for (let i = 0; i < NPRINT; i++) { const t0 = PRINT_T0 + i * PRINT_DT, out = seg(t, t0, t0 + .7); if (t >= t0 && out < 1) printPhoto(400, lerp(1100, 870, out), 150, SELECT_IDS[i], 0, out); }
  printerBox(400, 1160, t, printing);
  for (let i = 0; i < NPRINT; i++) {
    const t0 = PRINT_T0 + i * PRINT_DT;
    if (t < t0 + .7) continue;
    const slide = ease(seg(t, t0 + .7, t0 + 1.0));
    let x = lerp(400, 790, slide), y = lerp(870, 1240 - i * 6, slide), rot = lerp(0, -.08 + i * .04, slide), w = 150;
    const toRow = ease(seg(t, 46.9 + i * .1, 47.5 + i * .1));
    if (toRow > 0) { x = lerp(x, 330 + i * 300, toRow); y = lerp(y, 1360, toRow); rot = lerp(rot, 0, toRow); w = lerp(150, 210, toRow); }
    printPhoto(x, y, w, SELECT_IDS[i], rot, 1);
    if (t > 47.6 + i * .3) { const q = pop(t, 47.6 + i * .3); g.save(); g.translate(330 + i * 300 + 75, 1250); g.scale(q, q); circle(0, 0, 28); fs(C.green, C.ink, 5); g.strokeStyle = '#fff'; g.lineWidth = 7; g.beginPath(); g.moveTo(-12, 0); g.lineTo(-3, 10); g.lineTo(14, -10); g.stroke(); g.restore(); }
  }
  const done = clamp(Math.floor((t - PRINT_T0 - .7) / PRINT_DT) + 1, 0, NPRINT);
  if (t > PRINT_T0 - .4 && t < 47.0) { g.save(); g.translate(400, 760); rr(-150, -34, 300, 68, 34); fs('#fff', C.ink, 5); text(`${done} / 2 SIAP DICETAK`, 0, 2, F(900, 25), C.ink); g.restore(); }
  g.restore();
}

/* ====================================================================== */
/* SCENE 7 – Delivery + Google Drive link (82.2 – 92.8)                   */
/* ====================================================================== */
function photoFan() { g.save(); g.translate(0, -40); [-1, 1].forEach((k, i) => printPhoto(k * 22, -6, 96, SELECT_IDS[i], k * .18)); g.restore(); }
function photoFanSmall() { g.save(); g.scale(.8, .8); photoFan(); g.restore(); }
function folderIcon(x, y, s = 1) { g.save(); g.translate(x, y); g.scale(s, s); rr(-24, -20, 20, 9, 3); fs('#ffb84d'); rr(-24, -15, 48, 34, 5); fs('#ffc85f', C.ink, 2.5); g.restore(); }
function phoneUI(t, x, y, w, h) {
  g.save(); rr(x, y, w, h, 40); g.clip();
  g.fillStyle = '#f5f6fa'; g.fillRect(x, y, w, h);
  text('12:40', x + 56, y + 40, F(800, 24), C.ink, 'left');
  const msgP = pop(t, 51.5, .4);
  const open = ease(seg(t, 52.9, 53.3));
  if (open < 1) {
    g.save(); g.globalAlpha = 1 - open;
    text('Mesej', x + w / 2, y + 110, F(800, 32), C.ink);
    g.save(); g.translate(x + 28, y + 170); g.scale(1, msgP);
    rr(0, 0, w - 56, 380, 30); fs('#ffffff', '#dfe3ea', 3);
    circle(56, 56, 32); fs(C.ink); text('M', 56, 57, F(900, 30), '#fff');
    text('Merci Studio', 104, 46, F(800, 27), C.ink, 'left'); text('baru tadi', 104, 76, F(600, 19), '#8a90a0', 'left');
    text('Softcopy anda dah siap!', 28, 140, F(800, 26), C.ink, 'left');
    text('Kesemua 48 gambar ada dalam', 28, 180, F(600, 22), '#4b5163', 'left');
    text('folder Google Drive anda:', 28, 212, F(600, 22), '#4b5163', 'left');
    rr(24, 246, w - 104, 100, 18); fs('#eef4ff', '#b9d0ff', 3);
    folderIcon(74, 296, 1.1);
    text('Link Google Drive', 120, 280, F(800, 23), '#2f6fe0', 'left');
    text('Merci Studio · Softcopy', 120, 312, F(600, 19), '#4b5163', 'left');
    g.restore(); g.restore();
  }
  if (open > 0) {
    g.save(); g.globalAlpha = open;
    g.fillStyle = '#ffffff'; g.fillRect(x, y + 66, w, 110);
    folderIcon(x + 60, y + 122, 1.2);
    text('Merci Studio · Softcopy', x + 104, y + 106, F(800, 26), C.ink, 'left');
    text('48 gambar', x + 104, y + 140, F(600, 20), '#8a90a0', 'left');
    const cols = 3, gap = 10, tw = (w - gap * 4) / cols;
    const scroll = ease(seg(t, 53.4, 54.9)) * tw * 3.2;
    for (let i = 0; i < 33; i++) { const c = i % cols, r = Math.floor(i / cols); const py = y + 186 + r * (tw + gap) - scroll; if (py > y + h || py + tw < y + 176) continue; miniPhoto(x + gap + c * (tw + gap), py, tw, tw, i, { stroke: false, r: 6 }); }
    g.restore();
  }
  g.restore();
}
function sceneDeliver(t) {
  const up = ease(seg(t, 51.0, 51.5));
  g.save(); cam(1.03, 540, 960);
  receptionWorld(t);
  const p = ease(seg(t, 49.7, 50.4));
  const got = t > 50.5;
  staff({ x: 820, y: 1250, face: -1, t, aL: .35, aR: !got ? lerp(.3, 1.6, seg(t, 49.6, 50.0)) : (t > 50.8 ? 2.5 + Math.sin(t * 8) * .2 : .3), expr: 'joy', blink: blinking(t, 13) });
  receptionCounter();
  customer({ x: 380, y: 1330, s: 1.05, t, aR: got ? 2.2 : lerp(.3, 1.5, seg(t, 49.9, 50.4)), aL: t > 50.9 ? 1.5 : .3, expr: say(t, 'Y', got ? 'joy' : 'grin'), lx: 8, blink: blinking(t, 14),
    jump: got && t < 51.3 ? Math.abs(Math.sin(seg(t, 50.5, 51.3) * PI * 2)) * 60 : 0, holdR: got ? photoFan : null,
    holdL: t > 50.9 ? () => { g.save(); g.rotate(-.2); rr(-26, -48, 52, 92, 10); fs('#262932', C.ink, 4); rr(-20, -40, 40, 74, 6); fs('#dfeaff'); g.restore(); } : null });
  if (!got) { const x = lerp(690, 500, p), y = 1010 - Math.sin(p * PI) * 70; g.save(); g.translate(x, y); rr(-80, -55, 160, 110, 10); fs('#f3dfc4', C.ink, 5); text('MERCI', 0, 2, F(800, 26), '#6b5644'); g.restore(); }
  if (got && t < 51.4) for (let i = 0; i < 5; i++) heart(220 + i * 70, 820 - ((t - 50.5 + i * .3) % 1.6) * 120, .9, C.coral);
  g.restore();
  if (up > 0) {
    g.fillStyle = `rgba(30,20,15,${.4 * up})`; g.fillRect(0, 0, W, H);
    const pw = 600, ph = 1000, px = W / 2, py = lerp(H + 600, 940, up);
    g.save(); g.translate(px, py);
    shadowOn(50, 24, .45); rr(-pw / 2 - 18, -ph / 2 - 18, pw + 36, ph + 36, 66); fs('#23262f'); shadowOff();
    rr(-pw / 2 - 18, -ph / 2 - 18, pw + 36, ph + 36, 66); fs(null, C.ink, 6);
    phoneUI(t, -pw / 2, -ph / 2, pw, ph);
    rr(-70, -ph / 2 + 12, 140, 32, 16); fs('#23262f');
    g.restore();
    if (t > 52.3 && t < 53.0) finger(px - 20, py - 160, 1, 1 - seg(t, 52.6, 53.0));
  }
}

/* ====================================================================== */
/* SCENE 8 – Goodbye (92.8 – 99.8)                                        */
/* ====================================================================== */
function sceneGoodbye(t) {
  g.save(); cam(1.03, 540, 960);
  receptionWorld(t);
  staff({ x: 820, y: 1250, face: -1, t, aL: .35, aR: t > 95 ? 2.5 + Math.sin(t * 9) * .35 : .3, expr: say(t, 'S', 'joy'), blink: blinking(t, 15) });
  receptionCounter();
  const bow = Math.sin(seg(t, 93.0, 94.3) * PI) * .35;
  const p = ease(seg(t, 96.6, 99.5)), walking = p > 0 && p < 1;
  customer({ x: lerp(400, -160, p), y: 1330, s: 1.05, t, face: walking ? -1 : 1, tilt: bow, walk: walking ? t * 9 : null,
    aR: walking ? 2.5 + Math.sin(t * 10) * .4 : (t > 94.4 ? 2.4 + Math.sin(t * 10) * .3 : .3), aL: .4, expr: say(t, 'Y', bow > .05 ? 'joy' : 'grin'), lx: walking ? -14 : 8, blink: blinking(t, 16), holdL: photoFanSmall });
  for (let i = 0; i < 6; i++) { const hp = ((t - 92.8) * .7 + hash(i)) % 1; heart(150 + hash(i + 2) * 800, 1200 - hp * 600, .8 * Math.sin(hp * PI), C.coral); }
  g.restore();
}

/* ====================================================================== */
/* End card (99.8 – 107.5)                                                */
/* ====================================================================== */
function sceneEnd(t) {
  const gr = g.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 1300);
  gr.addColorStop(0, '#fff6ea'); gr.addColorStop(1, '#f2d2bb'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 46; i++) {
    const y = ((hash(i) * H + (t - 55) * (70 + hash(i + 5) * 90)) % (H + 100)) - 50;
    g.save(); g.translate(hash(i + 7) * W, y); g.rotate(t * (hash(i + 1) - .5) * 4);
    g.fillStyle = [C.coral, C.yellow, '#8fd3ff', '#a9e6bd', '#cdb5ff'][i % 5]; g.fillRect(-10, -6, 20, 12); g.restore();
  }
  const la = easeOut(seg(t, 55.0, 55.8));
  polaroid(IMG.store, lerp(-400, 320, la), 200, 480, -.07, 'STUDIO KAMI', 1);
  polaroid(IMG.stairs, lerp(W + 400, 770, la), 230, 520, .06, 'JOM NAIK!', 1);
  const t1 = pop(t, 55.4, .5), t2 = pop(t, 55.7, .5), t3 = pop(t, 56.5, .5);
  g.save(); g.translate(W / 2, 960); g.scale(t1, t1); heart(0, 0, 2.6, C.coral); g.restore();
  g.save(); g.translate(W / 2, 1130); g.scale(t2, t2);
  text('Terima Kasih Kerana', 0, -55, F(900, 74), '#ffffff', 'center', C.ink, 16);
  text('Memilih Kami!', 0, 45, F(900, 96), C.yellow, 'center', C.ink, 16);
  g.restore();
  g.save(); g.translate(W / 2, 1320); g.scale(t3, t3);
  rr(-480, -50, 960, 100, 50); fs(C.navy);
  text('Kenangan Anda, Dirakam Dengan Indah.', 0, 2, F(800, 38), '#ffffff');
  g.restore();
  const t4 = seg(t, 57.0, 57.5);
  g.save(); g.globalAlpha = t4;
  text('MERCI STUDIO', W / 2, 1450, F(900, 50), C.ink);
  text('Sampai 12:00 TGH  →  Gambar + softcopy siap 12:40 TGH', W / 2, 1505, F(700, 25), '#8a6f5a');
  g.restore();
  for (let i = 0; i < 8; i++) sparkle(W / 2 + Math.cos(i * .8) * (400 + i * 8), 1130 + Math.sin(i * 1.7) * 230, (0.6 + .4 * Math.sin(t * 3 + i)) * t2, C.yellow, t + i);
  if (t > 58.4) { g.fillStyle = `rgba(0,0,0,${seg(t, 58.4, 59.0)})`; g.fillRect(0, 0, W, H); }
}

/* ---------------- timeline + transitions ---------------- */
const SCENES = [
  { a: 0, b: 6.4, fn: sceneArrive },
  { a: 6.4, b: 9.4, fn: sceneStairs },
  { a: 9.4, b: 14.8, fn: sceneWelcome },
  { a: 14.8, b: 31.0, fn: sceneStudio },
  { a: 31.0, b: 36.4, fn: sceneDownload },
  { a: 36.4, b: 43.4, fn: sceneSelect },
  { a: 43.4, b: 49.6, fn: scenePrint },
  { a: 49.6, b: 55.0, fn: sceneDeliver },
  { a: 55.0, b: 59.1, fn: sceneEnd },
];
const TRANS = { 6.4: ['whip', .6], 9.4: ['iris', .7], 14.8: ['whip', .6], 31.0: ['iris', .7], 36.4: ['whip', .6], 43.4: ['iris', .7], 49.6: ['whip', .6], 55.0: ['fade', .7] };
const bufA = document.createElement('canvas'), bufB = document.createElement('canvas');
bufA.width = bufB.width = W; bufA.height = bufB.height = H;
const ctxA = bufA.getContext('2d'), ctxB = bufB.getContext('2d');
function vignette() {
  const gr = g.createRadialGradient(W / 2, H / 2, 600, W / 2, H / 2, 1200);
  gr.addColorStop(0, 'rgba(60,30,10,0)'); gr.addColorStop(1, 'rgba(60,30,10,0.26)');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
}
function drawScene(sc, t, ctx) { const prev = g; g = ctx; g.save(); g.clearRect(0, 0, W, H); sc.fn(t); g.restore(); vignette(); g = prev; }
function render(t) {
  g = mainCtx; g.setTransform(1, 0, 0, 1, 0, 0);
  let done = false;
  for (let i = 1; i < SCENES.length; i++) {
    const b = SCENES[i].a, tr = TRANS[b];
    if (!tr) continue;
    const [type, d] = tr;
    if (t >= b - d / 2 && t < b + d / 2) {
      const p = ease(seg(t, b - d / 2, b + d / 2));
      drawScene(SCENES[i - 1], t, ctxA); drawScene(SCENES[i], t, ctxB);
      g.clearRect(0, 0, W, H);
      if (type === 'whip') {
        g.filter = `blur(${Math.sin(p * PI) * 18}px)`;
        g.drawImage(bufA, -p * W, 0); g.drawImage(bufB, (1 - p) * W, 0); g.filter = 'none';
      } else if (type === 'iris') {
        g.drawImage(bufA, 0, 0);
        g.save(); circle(W / 2, H / 2, p * 1150); g.clip(); g.drawImage(bufB, 0, 0); g.restore();
        if (p > 0 && p < 1) { circle(W / 2, H / 2, p * 1150); fs(null, '#ffffff', 18); }
      } else { g.drawImage(bufA, 0, 0); g.globalAlpha = p; g.drawImage(bufB, 0, 0); g.globalAlpha = 1; }
      done = true; break;
    }
  }
  if (!done) { const sc = SCENES.find(s => t >= s.a && t < s.b) || SCENES[SCENES.length - 1]; g.save(); sc.fn(t); g.restore(); vignette(); }
  drawHUD(t);
  drawCaption(t);
}

/* ---------------- sound cues ---------------- */
const SFX = (() => {
  const s = [];
  Object.keys(TRANS).forEach(k => s.push({ t: +k - .3, type: 'whoosh' }));
  FLASHES.forEach(f => s.push({ t: f.t - .05, type: 'shutter' }));
  s.push({ t: 4.6, type: 'ding' }, { t: 27.5, type: 'tada' }, { t: 33.9, type: 'ding' }, { t: 50.5, type: 'tada' }, { t: 55.4, type: 'chime' }, { t: 51.5, type: 'notify' }, { t: 15.8, type: 'pop' });
  [...SELECT_TAPS, PRINT_TAP, 38.8, 52.6].forEach(t => s.push({ t, type: 'tap' }));
  for (let i = 0; i < NPRINT; i++) s.push({ t: PRINT_T0 + i * PRINT_DT, type: 'print' });
  for (let i = 0; i < NPRINT; i++) s.push({ t: 47.6 + i * .3, type: 'check' });
  return s.sort((a, b) => a.t - b.t);
})();

/* ---------------- boot ---------------- */
function loadImg(src) { return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; }); }
function makeBlur(img) {
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
  const s = Math.max(W / img.width, H / img.height);
  x.filter = 'blur(26px) brightness(0.78) saturate(1.1)';
  x.drawImage(img, (W - img.width * s) / 2, (H - img.height * s) / 2, img.width * s, img.height * s);
  x.filter = 'none'; x.fillStyle = 'rgba(255,200,150,0.12)'; x.fillRect(0, 0, W, H);
  return c;
}
async function boot() {
  for (const [w, f] of [[600, 'montserrat-600'], [700, 'montserrat-600'], [800, 'montserrat-800'], [900, 'montserrat-900']]) {
    const ff = new FontFace(FONT, `url(../assets/fonts/${f}.woff2)`, { weight: String(w) });
    await ff.load(); document.fonts.add(ff);
  }
  IMG.store = await loadImg('../assets/photos/storefront.jpg');
  IMG.stairs = await loadImg('../assets/photos/stairway.jpg');
  IMG.storeBlur = makeBlur(IMG.store);
  IMG.stairsBlur = makeBlur(IMG.stairs);
  window.READY = true;
}
window.render = render; window.boot = boot; window.SFX = SFX; window.DURATION = DURATION;
