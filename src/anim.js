'use strict';
/* Merci Studio – customer journey promo.
 * Deterministic canvas animation: render(t) draws the frame at time t (seconds).
 * 1920x1080, 30fps. Story clock: arrive 12:00 -> shoot 15m -> download 5m ->
 * selection 10m -> printing 10m -> delivery 12:40.
 */
const W = 1920, H = 1080, FPS = 30, DURATION = 106;
const PI = Math.PI, TAU = Math.PI * 2;
const cv = document.getElementById('c');
const mainCtx = cv.getContext('2d');
let g = mainCtx;
const IMG = {};
const C = {
  ink: '#272b38', yellow: '#ffc83d', green: '#58d26a', navy: '#1d2230', coral: '#ff7b86',
  blush: 'rgba(255,120,145,0.40)', shirt: '#2c2f3b', wall: '#f5ede3', wall2: '#eadccb',
  floor: '#b78962', floor2: '#946a49', paper: '#f6d6cf',
};
const FONT = 'Montserrat';
const F = (w, s) => `${w} ${s}px ${FONT}, sans-serif`;

/* ---------------- math helpers ---------------- */
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, x) => a + (b - a) * x;
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const easeOut = x => 1 - Math.pow(1 - x, 3);
const back = x => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const pop = (t, a, d = .35) => back(seg(t, a, a + d));
function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function blinking(t, seed = 0) { const p = (t + hash(seed) * 3) % 3.3; return p < 0.12; }

/* ---------------- drawing primitives ---------------- */
function rr(x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function line(x1, y1, x2, y2) { g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke(); }
function circle(x, y, r) { g.beginPath(); g.arc(x, y, r, 0, TAU); }
function fs(fill, stroke, lw = 6) { if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke(); } }
function limb(x1, y1, x2, y2, w, fill) {
  g.lineCap = 'round';
  g.strokeStyle = C.ink; g.lineWidth = w + 11; line(x1, y1, x2, y2);
  g.strokeStyle = fill; g.lineWidth = w; line(x1, y1, x2, y2);
}
function blobGrad(cx, cy, r) {
  const gr = g.createRadialGradient(cx - r * .35, cy - r * .42, r * .05, cx, cy, r * 1.08);
  gr.addColorStop(0, '#ffffff'); gr.addColorStop(.55, '#f6f7fa'); gr.addColorStop(1, '#cfd5df');
  return gr;
}
function vgrad(y0, y1, stops) { const gr = g.createLinearGradient(0, y0, 0, y1); stops.forEach((c, i) => gr.addColorStop(i / (stops.length - 1), c)); return gr; }
function text(str, x, y, font, fill, align = 'center', stroke, lw = 10) {
  g.font = font; g.textAlign = align; g.textBaseline = 'middle';
  if (stroke) { g.lineJoin = 'round'; g.strokeStyle = stroke; g.lineWidth = lw; g.strokeText(str, x, y); }
  g.fillStyle = fill; g.fillText(str, x, y);
}
function heart(x, y, s, col) {
  g.save(); g.translate(x, y); g.scale(s, s);
  g.beginPath(); g.moveTo(0, 8);
  g.bezierCurveTo(-26, -10, -12, -32, 0, -16); g.bezierCurveTo(12, -32, 26, -10, 0, 8);
  fs(col || C.coral, C.ink, 3.5); g.restore();
}
function sparkle(x, y, s, col = C.yellow, rot = 0) {
  g.save(); g.translate(x, y); g.rotate(rot); g.scale(s, s);
  g.beginPath();
  for (let i = 0; i < 8; i++) { const r = i % 2 ? 7 : 24, a = i * PI / 4; g.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
  g.closePath(); fs(col, C.ink, 3); g.restore();
}
function shadowOn(blur = 30, oy = 12, a = .25) { g.shadowColor = `rgba(40,25,10,${a})`; g.shadowBlur = blur; g.shadowOffsetY = oy; g.shadowOffsetX = 0; }
function shadowOff() { g.shadowColor = 'transparent'; g.shadowBlur = 0; g.shadowOffsetY = 0; }

/* ---------------- character ---------------- */
/* o: x,y (feet), s, face (1 right / -1 left), expr, aL,aR (arm angle: 0 down, PI/2 sideways, PI up),
 *    walk (phase), jump, bob, tilt, sit, lx/ly (gaze), cap, bow, bag, shirt, logo, holdL/holdR (fn) */
function char(o) {
  const s = o.s || 1, face = o.face || 1, t = o.t || 0;
  g.save(); g.translate(o.x, o.y);
  if (!o.sit && o.shadow !== false) {
    const k = 1 - clamp((o.jump || 0) / 260) * .5;
    g.fillStyle = 'rgba(50,30,15,0.20)'; g.beginPath(); g.ellipse(0, 2, 78 * s * k, 14 * s * k, 0, 0, TAU); g.fill();
  }
  g.scale(s * face, s);
  g.translate(0, -(o.jump || 0));
  const walking = o.walk != null;
  const sw = walking ? Math.sin(o.walk) * .55 : 0;
  const lift = walking ? Math.abs(Math.cos(o.walk)) * 8 : 0;
  // legs
  const legA = o.sit ? [1.45, 1.3] : [sw + (o.legSpread || 0) * -1, -sw + (o.legSpread || 0)];
  [[-22, 0], [22, 1]].forEach(([hx, i]) => {
    const a = legA[i], len = o.sit ? 66 : 64;
    const fx = hx + Math.sin(a) * len, fy = -72 + Math.cos(a) * len;
    limb(hx, -74, fx, fy - 6, 27, '#ffffff');
    g.beginPath(); g.ellipse(fx + 7, fy - 7, 20, 12, 0, 0, TAU); fs(o.shoes || '#ffffff', C.ink, 5.5);
  });
  g.translate(0, -lift - (o.bob || 0));
  if (o.tilt) { g.translate(0, -74); g.rotate(o.tilt); g.translate(0, 74); }
  // bag strap behind arms
  // torso
  g.beginPath(); g.ellipse(0, -122, 50, 56, 0, 0, TAU);
  if (o.shirt) {
    fs(o.shirt, C.ink, 6);
    const gr = g.createRadialGradient(-20, -150, 4, 0, -122, 66);
    gr.addColorStop(0, 'rgba(255,255,255,0.20)'); gr.addColorStop(1, 'rgba(0,0,0,0.18)');
    g.fillStyle = gr; g.fill();
    if (o.logo) { text('M', 4, -118, F(900, 24), '#ffffff'); }
  } else fs(blobGrad(0, -125, 58), C.ink, 6);
  if (o.bag) {
    g.strokeStyle = C.ink; g.lineWidth = 11; line(-26, -168, 30, -86);
    g.strokeStyle = C.coral; g.lineWidth = 6; line(-26, -168, 30, -86);
    rr(14, -102, 40, 34, 9); fs(C.coral, C.ink, 5);
  }
  // arms
  [[-1, o.aL ?? .32, o.holdL], [1, o.aR ?? .32, o.holdR]].forEach(([side, a, hold]) => {
    const sx = side * 36, sy = -150, len = 70;
    const hx = sx + side * Math.sin(a) * len, hy = sy + Math.cos(a) * len;
    limb(sx, sy, hx, hy, 21, o.shirt && o.sleeves ? o.shirt : '#ffffff');
    circle(hx, hy, 16); fs('#ffffff', C.ink, 5);
    if ((side === 1 && o.peaceR) || (side === -1 && o.peaceL)) {
      g.save(); g.translate(hx, hy); g.rotate(side * (PI - a) * .9 + PI);
      [-.25, .25].forEach(r => { g.save(); g.rotate(r); rr(-6, -4, 12, 30, 6); fs('#fff', C.ink, 4.5); g.restore(); });
      circle(0, 0, 16); fs('#ffffff', C.ink, 5); g.restore();
    }
    if (o.thumbR && side === 1) { g.save(); g.translate(hx, hy); rr(-6, -34, 13, 26, 6); fs('#fff', C.ink, 4.5); circle(0, 0, 16); fs('#fff', C.ink, 5); g.restore(); }
    if (hold) { g.save(); g.translate(hx, hy); hold(); g.restore(); }
  });
  // head
  const hy = -236;
  circle(0, hy, 84); fs(blobGrad(0, hy, 84), C.ink, 6);
  if (o.hair) {
    g.save(); circle(0, hy, 84); g.clip();
    g.beginPath(); g.ellipse(-6, hy - 70, 92, 46, -.12, 0, TAU); g.fillStyle = o.hair; g.fill(); g.restore();
    circle(0, hy, 84); fs(null, C.ink, 6);
  }
  // face
  const lx = (o.lx || 0) + 10, ly = o.ly || 0, ey = hy - 4 + ly, ex = 27;
  const expr = o.expr || 'happy';
  const blink = o.blink;
  g.fillStyle = C.ink; g.strokeStyle = C.ink; g.lineCap = 'round';
  const eye = (x, closed, big, arc) => {
    if (arc) { g.lineWidth = 6; g.beginPath(); g.arc(x, ey + 6, 12, PI * 1.15, PI * 1.85); g.stroke(); return; }
    if (closed) { g.lineWidth = 6; line(x - 10, ey, x + 10, ey); return; }
    g.beginPath(); g.ellipse(x, ey, big ? 12 : 10, big ? 17 : 14, 0, 0, TAU); g.fillStyle = C.ink; g.fill();
    circle(x + 3.5, ey - 5, big ? 4.5 : 3.6); g.fillStyle = '#fff'; g.fill();
  };
  const joyEyes = expr === 'joy';
  eye(-ex + lx, blink && !joyEyes, expr === 'wow', joyEyes);
  eye(ex + lx, (blink && !joyEyes), expr === 'wow', joyEyes || expr === 'wink');
  // blush
  g.fillStyle = C.blush;
  g.beginPath(); g.ellipse(-50 + lx, hy + 20 + ly, 14, 8, 0, 0, TAU); g.fill();
  g.beginPath(); g.ellipse(50 + lx, hy + 20 + ly, 14, 8, 0, 0, TAU); g.fill();
  // mouth
  const my = hy + 30 + ly;
  g.strokeStyle = C.ink; g.lineWidth = 5.5;
  if (expr === 'joy' || expr === 'grin' || expr === 'talk') {
    const open = expr === 'talk' ? 6 + Math.abs(Math.sin(t * 16)) * 14 : 26;
    g.beginPath(); g.moveTo(lx - 21, my - 4); g.quadraticCurveTo(lx, my - 8, lx + 21, my - 4);
    g.quadraticCurveTo(lx + 18, my + open, lx, my + open); g.quadraticCurveTo(lx - 18, my + open, lx - 21, my - 4);
    g.closePath(); g.fillStyle = '#5a2330'; g.fill(); g.stroke();
    g.save(); g.clip(); g.beginPath(); g.ellipse(lx + 2, my + open, 13, 9, 0, 0, TAU); g.fillStyle = '#ff8b9a'; g.fill(); g.restore();
  } else if (expr === 'wow') {
    g.beginPath(); g.ellipse(lx, my + 6, 10, 13, 0, 0, TAU); g.fillStyle = '#5a2330'; g.fill(); g.stroke();
  } else if (expr === 'focus') {
    line(lx - 10, my + 4, lx + 12, my + 2);
  } else {
    g.beginPath(); g.arc(lx, my - 8, 18, PI * .18, PI * .82); g.stroke();
  }
  // accessories
  if (o.cap) {
    g.save(); circle(0, hy, 84); g.clip();
    g.beginPath(); g.ellipse(0, hy - 60, 100, 52, 0, 0, TAU); g.fillStyle = '#23262f'; g.fill(); g.restore();
    g.beginPath(); g.ellipse(0, hy - 60, 0, 0, 0, 0, TAU);
    g.beginPath(); g.arc(0, hy, 84, PI * 1.12, PI * 1.88); g.strokeStyle = C.ink; g.lineWidth = 6; g.stroke();
    g.beginPath(); g.ellipse(70, hy - 30, 46, 11, .12, 0, TAU); fs('#23262f', C.ink, 5);
    circle(0, hy - 84, 7); fs('#23262f', C.ink, 4);
  }
  if (o.bow) {
    g.save(); g.translate(48, hy - 66); g.rotate(.45);
    g.beginPath(); g.moveTo(0, 0); g.lineTo(-30, -18); g.lineTo(-30, 18); g.closePath(); fs(C.coral, C.ink, 4.5);
    g.beginPath(); g.moveTo(0, 0); g.lineTo(30, -18); g.lineTo(30, 18); g.closePath(); fs(C.coral, C.ink, 4.5);
    circle(0, 0, 9); fs('#ff5d6c', C.ink, 4.5); g.restore();
  }
  g.restore();
}

/* Cast presets */
function customer(o) { return char(Object.assign({ bow: true, bag: !o.noBag, expr: 'happy' }, o)); }
function owner(o) { return char(Object.assign({ cap: true, shirt: C.shirt, logo: true, expr: 'happy' }, o)); }

/* ---------------- props ---------------- */
function bubble(x, y, str, p, opts = {}) {
  if (p <= 0) return;
  const s = back(clamp(p));
  g.save(); g.translate(x, y); g.scale(s, s);
  g.font = F(800, opts.size || 40);
  const lines = str.split('\n');
  const tw = Math.max(...lines.map(l => g.measureText(l).width));
  const lh = (opts.size || 40) * 1.2;
  const w = tw + 70, h = lines.length * lh + 44;
  const tail = opts.tail || 1;
  shadowOn(20, 8, .18);
  g.beginPath(); g.roundRect(-w / 2, -h, w, h, 32);
  g.fillStyle = '#fff'; g.fill(); shadowOff();
  g.strokeStyle = C.ink; g.lineWidth = 6; g.stroke();
  g.beginPath(); g.moveTo(tail * 10 - 20, -3); g.lineTo(tail * 40, 34); g.lineTo(tail * 10 + 20, -3); g.closePath();
  g.fillStyle = '#fff'; g.fill();
  g.beginPath(); g.moveTo(tail * 10 - 20, 0); g.lineTo(tail * 40, 34); g.lineTo(tail * 10 + 20, 0); g.stroke();
  lines.forEach((l, i) => text(l, 0, -h + 22 + lh * (i + .5), F(800, opts.size || 40), opts.color || C.ink));
  g.restore();
}
function wallClock(x, y, r, minutes) {
  g.save(); g.translate(x, y);
  shadowOn(16, 6, .2); circle(0, 0, r); fs('#ffffff', C.ink, 7); shadowOff();
  for (let i = 0; i < 12; i++) { const a = i * PI / 6; g.lineWidth = i % 3 ? 3 : 6; g.strokeStyle = C.ink; line(Math.sin(a) * r * .78, -Math.cos(a) * r * .78, Math.sin(a) * r * .9, -Math.cos(a) * r * .9); }
  const hrs = 12 + minutes / 60;
  const ha = (hrs % 12) / 12 * TAU, ma = (minutes / 60) * TAU;
  g.lineCap = 'round'; g.strokeStyle = C.ink;
  g.lineWidth = 8; line(0, 0, Math.sin(ha) * r * .5, -Math.cos(ha) * r * .5);
  g.lineWidth = 5; line(0, 0, Math.sin(ma) * r * .76, -Math.cos(ma) * r * .76);
  circle(0, 0, 7); fs(C.ink); g.restore();
}
function pendant(x, len, glow = 1) {
  g.strokeStyle = '#3a3a3a'; g.lineWidth = 3; line(x, 0, x, len);
  const gr = g.createRadialGradient(x, len + 34, 4, x, len + 34, 230);
  gr.addColorStop(0, `rgba(255,236,190,${.55 * glow})`); gr.addColorStop(1, 'rgba(255,236,190,0)');
  g.fillStyle = gr; g.fillRect(x - 240, len - 200, 480, 480);
  circle(x, len + 36, 20); fs('#fffbe9');
  g.strokeStyle = '#2e2e2e'; g.lineWidth = 3;
  g.beginPath();
  const pts = [[0, 0], [-30, 22], [-24, 58], [0, 72], [24, 58], [30, 22]];
  pts.forEach(([dx, dy], i) => i ? g.lineTo(x + dx, len + dy) : g.moveTo(x + dx, len + dy)); g.closePath(); g.stroke();
  line(x, len, x, len + 72); line(x - 30, len + 22, x + 24, len + 58); line(x + 30, len + 22, x - 24, len + 58);
}
function merciSign(x, y, s) {
  g.save(); g.translate(x, y); g.scale(s, s);
  g.font = F(600, 110); g.textAlign = 'left'; g.textBaseline = 'alphabetic';
  g.fillStyle = 'rgba(0,0,0,0.12)'; g.fillText('MERCI', 46, 6); g.fillText('STUDIO', 6, 126);
  g.fillStyle = '#2b2c31'; g.fillText('MERCI', 40, 0); g.fillText('STUDIO', 0, 120);
  g.restore();
}
function plant(x, y, s) {
  g.save(); g.translate(x, y); g.scale(s, s);
  const leaves = [[-.55, 230], [-.32, 300], [-.12, 340], [.1, 320], [.3, 280], [.52, 220], [-.22, 200], [.22, 210]];
  leaves.forEach(([a, l], i) => {
    g.save(); g.translate(0, -60); g.rotate(a);
    g.strokeStyle = '#27412c'; g.lineWidth = 4; line(0, 0, 0, -l * .45);
    g.beginPath(); g.moveTo(0, -l * .35); g.quadraticCurveTo(26, -l * .7, 0, -l); g.quadraticCurveTo(-26, -l * .7, 0, -l * .35);
    fs(i % 2 ? '#2f5a37' : '#244a2c', '#1a2a1d', 3); g.restore();
  });
  g.beginPath(); g.moveTo(-42, -70); g.lineTo(42, -70); g.lineTo(32, 0); g.lineTo(-32, 0); g.closePath(); fs('#33353d', C.ink, 4);
  g.restore();
}
function camera(x, y, s, flash = 0) {
  g.save(); g.translate(x, y); g.scale(s, s);
  rr(-70, -46, 140, 92, 16); fs('#2c2f3a', C.ink, 6);
  rr(-40, -66, 60, 24, 6); fs('#3a3e4b', C.ink, 5);
  circle(-62, 0, 34); fs('#444958', C.ink, 6); circle(-62, 0, 20); fs('#1a1c24'); circle(-68, -6, 6); fs('rgba(255,255,255,.6)');
  rr(-12, -94, 46, 30, 6); fs(flash > 0 ? '#fffbe0' : '#e9eaee', C.ink, 5);
  if (flash > 0) {
    g.save(); g.globalAlpha = flash; const gr = g.createRadialGradient(10, -79, 2, 10, -79, 260);
    gr.addColorStop(0, 'rgba(255,255,240,1)'); gr.addColorStop(1, 'rgba(255,255,240,0)'); g.fillStyle = gr; g.fillRect(-250, -340, 520, 520);
    for (let i = 0; i < 10; i++) { const a = i * TAU / 10; g.strokeStyle = 'rgba(255,230,120,.9)'; g.lineWidth = 6; line(10 + Math.cos(a) * 50, -79 + Math.sin(a) * 50, 10 + Math.cos(a) * (90 + flash * 60), -79 + Math.sin(a) * (90 + flash * 60)); }
    g.restore();
  }
  g.restore();
}
function tripod(x, y, h) {
  g.strokeStyle = C.ink; g.lineWidth = 9; g.lineCap = 'round';
  line(x, y - h, x - 70, y); line(x, y - h, x + 70, y); line(x, y - h, x, y);
  g.strokeStyle = '#5b606e'; g.lineWidth = 4; line(x, y - h, x - 70, y); line(x, y - h, x + 70, y); line(x, y - h, x, y);
}
function softbox(x, y, rot, flash) {
  g.save();
  g.strokeStyle = C.ink; g.lineWidth = 8; line(x, y, x, 880); line(x, 880, x - 60, 900); line(x, 880, x + 60, 900);
  g.translate(x, y); g.rotate(rot);
  g.beginPath(); g.moveTo(-90, -110); g.lineTo(90, -110); g.lineTo(40, 0); g.lineTo(-40, 0); g.closePath();
  g.save(); g.rotate(PI / 2); g.restore();
  rr(-30, -10, 60, 34, 6); fs('#2f323d', C.ink, 5);
  g.beginPath(); g.moveTo(-120, -150); g.lineTo(120, -150); g.lineTo(46, -6); g.lineTo(-46, -6); g.closePath(); fs('#2f323d', C.ink, 6);
  const glow = .75 + flash * .25;
  g.beginPath(); g.moveTo(-112, -146); g.lineTo(112, -146); g.lineTo(100, -132); g.lineTo(-100, -132); g.closePath();
  fs(`rgba(255,250,235,${glow})`);
  g.restore();
  if (flash > 0) {
    g.save(); g.globalAlpha = flash * .6;
    const gr = g.createRadialGradient(x, y - 140, 10, x, y - 140, 380); gr.addColorStop(0, '#fffdf2'); gr.addColorStop(1, 'rgba(255,253,242,0)');
    g.fillStyle = gr; g.fillRect(x - 400, y - 540, 800, 800); g.restore();
  }
}
const THUMB_BG = [['#ffd6dc', '#ffb3c0'], ['#d8ecff', '#a9d2ff'], ['#fff1c9', '#ffd97a'], ['#dcf5e3', '#a9e6bd'], ['#eadcff', '#cdb5ff'], ['#ffe2cc', '#ffc199']];
const THUMB_POSE = [
  { expr: 'joy', aL: 2.7, aR: 2.7 }, { expr: 'grin', aR: 2.4, peaceR: true }, { expr: 'wink', aL: 2.9, aR: 2.9 },
  { expr: 'happy', aL: .9, aR: .9, tilt: .12 }, { expr: 'joy', aL: 2.2, aR: .3, jump: 26 }, { expr: 'grin', aL: .3, aR: 3.0, peaceR: true },
];
function miniPhoto(x, y, w, h, i, opts = {}) {
  g.save();
  rr(x, y, w, h, opts.r ?? Math.min(w, h) * .06); g.save(); g.clip();
  const [a, b] = THUMB_BG[i % THUMB_BG.length];
  const gr = g.createLinearGradient(x, y, x + w, y + h); gr.addColorStop(0, a); gr.addColorStop(1, b);
  g.fillStyle = gr; g.fillRect(x, y, w, h);
  g.fillStyle = 'rgba(255,255,255,.35)'; g.beginPath(); g.ellipse(x + w * .5, y + h * 1.02, w * .7, h * .18, 0, 0, TAU); g.fill();
  const reveal = opts.reveal ?? 1;
  if (reveal > 0) {
    g.globalAlpha = reveal;
    const pose = THUMB_POSE[(i * 7 + 3) % THUMB_POSE.length];
    const sc = Math.min(w, h * .85) / 360;
    customer(Object.assign({ x: x + w * (.5 + ((i % 3) - 1) * .06), y: y + h * .97, s: sc * (1 + (i % 2) * .15), shadow: false, face: i % 4 === 1 ? -1 : 1 }, pose));
    g.globalAlpha = 1;
  }
  if (reveal < 1) { g.fillStyle = `rgba(30,30,40,${(1 - reveal) * .85})`; g.fillRect(x, y, w, h); }
  g.restore();
  if (opts.stroke !== false) { rr(x, y, w, h, opts.r ?? Math.min(w, h) * .06); fs(null, opts.strokeCol || C.ink, opts.lw || 4); }
  g.restore();
}
function printPhoto(x, y, w, i, rot = 0, reveal = 1) {
  const h = w * 1.25;
  g.save(); g.translate(x, y); g.rotate(rot);
  shadowOn(14, 6, .25); rr(-w / 2, -h / 2, w, h, 6); fs('#ffffff'); shadowOff();
  rr(-w / 2, -h / 2, w, h, 6); fs(null, C.ink, 4);
  miniPhoto(-w / 2 + w * .07, -h / 2 + w * .07, w * .86, h - w * .3, i, { reveal, lw: 2.5, r: 3 });
  g.restore();
}
function polaroid(img, cx, top, ph, rot = 0, label = '', k = 1) {
  const pw = ph * img.width / img.height;
  const pad = 20, bottom = label ? 74 : 20;
  g.save(); g.translate(cx, top + (ph + pad + bottom) / 2); g.rotate(rot); g.scale(k, k);
  const fw = pw + pad * 2, fh = ph + pad + bottom;
  shadowOn(40, 18, .35); rr(-fw / 2, -fh / 2, fw, fh, 10); fs('#fffdf8'); shadowOff();
  g.drawImage(img, -pw / 2, -fh / 2 + pad, pw, ph); // photo drawn whole, untouched
  if (label) text(label, 0, fh / 2 - bottom / 2, F(700, 26), '#3a3a44');
  g.restore();
}
function finger(x, y, s = 1, press = 0) {
  g.save(); g.translate(x, y); g.scale(s, s);
  shadowOn(16, 8, .25);
  rr(-17, -6, 34, 120, 17); fs('#ffffff', C.ink, 5);
  g.beginPath(); g.ellipse(14, 110, 52, 56, 0, 0, TAU); fs('#ffffff', C.ink, 5);
  shadowOff();
  rr(-17, -6, 34, 70, 17); fs('#ffffff');
  if (press > 0) { g.strokeStyle = `rgba(255,200,61,${press})`; g.lineWidth = 6; circle(0, -6, 30 + (1 - press) * 30); g.stroke(); }
  g.restore();
}
function sofa(x, y, col = '#f0a34a') {
  g.save(); g.translate(x, y);
  rr(-260, -230, 520, 170, 50); fs(col, C.ink, 6);
  rr(-250, -110, 500, 90, 30); fs(shade(col, -12), C.ink, 6);
  rr(-300, -170, 90, 160, 40); fs(col, C.ink, 6);
  rr(210, -170, 90, 160, 40); fs(col, C.ink, 6);
  g.fillStyle = C.ink; g.fillRect(-250, -10, 16, 22); g.fillRect(234, -10, 16, 22);
  g.restore();
}
function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const r = clamp(((n >> 16) & 255) + amt, 0, 255), gg = clamp(((n >> 8) & 255) + amt, 0, 255), b = clamp((n & 255) + amt, 0, 255);
  return `rgb(${r},${gg},${b})`;
}
function ipadProp(w = 120, h = 86, screenFn) {
  g.save(); rr(-w / 2, -h / 2, w, h, 10); fs('#2b2e38', C.ink, 4);
  rr(-w / 2 + 7, -h / 2 + 7, w - 14, h - 14, 5); fs('#bfe0ff');
  if (screenFn) screenFn(-w / 2 + 7, -h / 2 + 7, w - 14, h - 14);
  g.restore();
}

/* ---------------- rooms ---------------- */
function room(floorY = 830, wallCol = [C.wall, C.wall2]) {
  g.fillStyle = vgrad(0, floorY, wallCol); g.fillRect(-2000, -400, 8000, floorY + 400);
  g.fillStyle = vgrad(floorY, 1300, [C.floor, C.floor2]); g.fillRect(-2000, floorY, 8000, 900);
  g.strokeStyle = 'rgba(80,50,30,.18)'; g.lineWidth = 3;
  for (let i = -20; i < 60; i++) line(i * 140, floorY, i * 140 - 300, 1300);
  g.fillStyle = '#e6d6c3'; g.fillRect(-2000, floorY - 22, 8000, 22);
  g.strokeStyle = 'rgba(0,0,0,.12)'; g.lineWidth = 3; line(-2000, floorY, 6000, floorY);
}
function warmPool(x, y, r, a = .35) {
  const gr = g.createRadialGradient(x, y, 10, x, y, r);
  gr.addColorStop(0, `rgba(255,214,150,${a})`); gr.addColorStop(1, 'rgba(255,214,150,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
}
function frameOnWall(x, y, w, h, i) {
  shadowOn(14, 6, .2); rr(x - 10, y - 10, w + 20, h + 20, 6); fs('#ffffff', C.ink, 5); shadowOff();
  miniPhoto(x, y, w, h, i, { lw: 2.5, r: 2 });
}
function counter(x, y, w, h) {
  rr(x, y, w, h, 14); fs('#fbf7f2', C.ink, 6);
  g.fillStyle = 'rgba(0,0,0,.06)'; g.fillRect(x + 6, y + h * .55, w - 12, h * .45 - 6);
  rr(x - 20, y - 26, w + 40, 34, 10); fs('#c99a6c', C.ink, 6);
  text('MERCI STUDIO', x + w / 2, y + h * .45, F(600, 30), '#2b2c31');
}

/* ---------------- camera ---------------- */
function cam(z, fx, fy) { g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-fx, -fy); }

/* ---------------- story clock + HUD ---------------- */
function storyMinutes(t) {
  if (t < 3.6) return -1;
  if (t < 21) return 0;
  if (t < 38) return lerp(0, 15, seg(t, 21, 38));
  if (t < 47) return 15;
  if (t < 55) return lerp(15, 20, seg(t, 47, 55));
  if (t < 57.5) return 20;
  if (t < 67.3) return lerp(20, 30, seg(t, 57.5, 67.3));
  if (t < 70) return 30;
  if (t < 80.6) return lerp(30, 40, seg(t, 70, 80.6));
  return 40;
}
function clockStr(m) {
  const tot = 12 * 60 + Math.floor(m + 1e-6);
  let hh = Math.floor(tot / 60) % 24, mm = ((tot % 60) + 60) % 60;
  const ap = hh >= 12 ? 'PM' : 'AM'; hh = hh % 12 || 12;
  return `${hh}:${String(mm).padStart(2, '0')} ${ap}`;
}
function mmss(min) { const s = Math.max(0, Math.round(min * 60)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; }
function hudState(t) {
  const m = storyMinutes(t);
  if (t < 21) return { label: 'CUSTOMER ARRIVAL', value: t < 3.6 ? 'ON THE WAY' : 'RIGHT ON TIME!', prog: t < 3.6 ? seg(t, 0, 3.6) : 1, col: C.green };
  if (t < 38.6) return { label: 'PACKAGE A  ·  PHOTOSHOOT', value: mmss(15 - m) + ' LEFT', prog: m / 15, col: C.green };
  if (t < 46.3) return { label: 'PACKAGE A  ·  PHOTOSHOOT', value: 'COMPLETE!', prog: 1, col: C.green };
  if (t < 56.3) return { label: 'DOWNLOADING PHOTOS  ·  5 MIN', value: mmss(20 - m) + ' LEFT', prog: (m - 15) / 5, col: '#5bb8ff' };
  if (t < 68.3) return { label: 'PHOTO SELECTION  ·  10 MIN', value: mmss(30 - m) + ' LEFT', prog: (m - 20) / 10, col: '#c08bff' };
  if (t < 81.3) return { label: 'PHOTO PRINTING  ·  10 MIN', value: mmss(40 - m) + ' LEFT', prog: (m - 30) / 10, col: '#ff9f5a' };
  return { label: 'ALL DONE', value: 'PRINTS + SOFTCOPY', prog: 1, col: C.green };
}
function drawHUD(t) {
  const a = 1 - seg(t, 97.6, 98.3);
  if (a <= 0) return;
  const st = hudState(t);
  g.save(); g.globalAlpha = a;
  const w = 600, h = 126, x = W / 2 - w / 2, y = 26;
  shadowOn(20, 8, .3); rr(x, y, w, h, 26); fs(C.navy); shadowOff();
  rr(x, y, w, h, 26); fs(null, '#0e1119', 5);
  text(st.label, W / 2, y + 26, F(800, 20), '#aab3c5');
  text(st.value, W / 2, y + 66, F(900, 46), C.yellow);
  rr(x + 40, y + 96, w - 80, 14, 7); fs('#3a4152');
  rr(x + 40, y + 96, Math.max(14, (w - 80) * clamp(st.prog)), 14, 7); fs(st.col);
  // time pill
  const m = storyMinutes(t);
  const flip = t >= 3.6 && t < 4.2 ? pop(t, 3.6, .4) : 1;
  g.save(); g.translate(W / 2, y + h + 38); g.scale(flip, flip);
  rr(-118, -26, 236, 52, 26); fs('#ffffff', C.ink, 5);
  text(clockStr(m), 0, 2, F(800, 30), C.ink);
  g.restore();
  g.restore();
}

/* ---------------- captions (reference style: 1–3 words, keyword in yellow) ---------------- */
const CAPTIONS = [
  [0.5, 3.4, 'THIS IS *MERCI STUDIO*'],
  [3.6, 7.0, "IT'S EXACTLY *12:00 PM*"],
  [7.5, 12.7, 'OUR CUSTOMER HEADS *UPSTAIRS*'],
  [13.4, 20.6, 'AND GETS A *WARM WELCOME!*'],
  [21.3, 25.0, '*PACKAGE A:* 15 MINUTE SHOOT'],
  [25.2, 31.0, 'SMILE, POSE AND *FLASH!*'],
  [31.2, 38.4, 'SO MANY *BEAUTIFUL* SHOTS'],
  [39.0, 42.0, '12:15 PM, *SESSION DONE!*'],
  [42.3, 46.0, 'NOW WE *WAIT* FOR THE PHOTOS'],
  [46.6, 51.2, 'THE OWNER *DOWNLOADS* EVERY PHOTO'],
  [51.4, 55.9, 'FIVE MINUTES, *ALL READY!*'],
  [56.6, 61.6, 'TIME TO *PICK FAVOURITES*'],
  [61.8, 67.8, 'SCROLL, ZOOM AND *CHOOSE*'],
  [68.6, 72.2, 'THE CHOSEN ONES GO TO *PRINT*'],
  [72.4, 76.9, 'FRESH PRINTS *COMING OUT*'],
  [77.1, 80.8, 'EVERY PRINT *CHECKED* WITH CARE'],
  [81.6, 85.5, 'PRINTED PHOTOS *IN HAND*'],
  [85.7, 91.8, 'PLUS A *GOOGLE DRIVE* LINK WITH EVERY *SOFTCOPY*'],
  [92.5, 97.6, '*THANK YOU!* SEE YOU AGAIN!'],
];
const CAP_CHUNKS = (() => {
  const out = [];
  CAPTIONS.forEach(([a, b, s]) => {
    let hl = false; const words = [];
    s.split(' ').forEach(w => {
      let on = hl;
      if (w.startsWith('*')) { on = true; w = w.slice(1); hl = true; }
      if (w.endsWith('*')) { w = w.slice(0, -1); hl = false; }
      words.push({ w, on });
    });
    const chunks = []; let cur = [];
    words.forEach(wd => { cur.push(wd); const len = cur.reduce((n, x) => n + x.w.length, 0); if (cur.length >= 2 || len > 9) { chunks.push(cur); cur = []; } });
    if (cur.length) chunks.push(cur);
    const d = (b - a) / chunks.length;
    chunks.forEach((c, i) => out.push({ t0: a + i * d, t1: a + (i + 1) * d, words: c }));
  });
  return out;
})();
function drawCaption(t) {
  const c = CAP_CHUNKS.find(c => t >= c.t0 && t < c.t1);
  if (!c) return;
  const p = pop(t, c.t0, .22);
  g.save(); g.translate(W / 2, 985); g.scale(p, p);
  g.font = F(900, 86);
  const gap = 26;
  const widths = c.words.map(wd => g.measureText(wd.w).width);
  const total = widths.reduce((a, b) => a + b, 0) + gap * (c.words.length - 1);
  let x = -total / 2;
  c.words.forEach((wd, i) => {
    g.fillStyle = 'rgba(0,0,0,.35)'; g.textAlign = 'left'; g.textBaseline = 'middle';
    g.lineJoin = 'round'; g.strokeStyle = '#1b1d26'; g.lineWidth = 18; g.strokeText(wd.w, x, 6); g.strokeText(wd.w, x, 0);
    g.fillStyle = wd.on ? C.yellow : '#ffffff'; g.fillText(wd.w, x, 0);
    x += widths[i] + gap;
  });
  g.restore();
}

/* ====================================================================== */
/* SCENES                                                                 */
/* ====================================================================== */

function bgPhoto(key) { g.drawImage(IMG[key + 'Blur'], -150, -100, W + 300, H + 200); }
function sidewalk(y) {
  g.fillStyle = vgrad(y, H, ['#efe5d9', '#cdbba7']); g.fillRect(-200, y, W + 400, H - y + 300);
  g.strokeStyle = 'rgba(90,70,50,.18)'; g.lineWidth = 3; line(0, y, W, y);
  for (let i = -1; i < 16; i++) line(i * 150 - 40, y, i * 150 - 190, H + 150);
}

/* S0 – Arrival outside (0 – 7.3) */
function sceneArrive(t) {
  g.save(); cam(1 + seg(t, 0, 7.3) * .04, 960, 540);
  bgPhoto('store');
  sidewalk(915);
  polaroid(IMG.store, 1420, 218 - (1 - easeOut(seg(t, 0, 1))) * 40, 600, .025, 'MERCI STUDIO  ·  KEDAI GAMBAR', 1 + seg(t, 0, 7.3) * .02);
  const p = seg(t, .3, 3.4);
  const x = lerp(-160, 720, p);
  const walking = p > 0 && p < 1;
  const arrived = t > 3.45;
  customer({ x, y: 965, s: 1.15, t, walk: walking ? t * 9 : null, aL: walking ? .32 + Math.sin(t * 9) * .4 : (arrived && t > 4.0 ? 2.5 : .3), aR: walking ? .32 - Math.sin(t * 9) * .4 : .3,
    expr: arrived ? (t < 4.0 ? 'wow' : 'joy') : 'happy', lx: 6, ly: arrived ? -6 : 0, blink: blinking(t, 1), jump: arrived && t < 4.4 ? Math.sin(seg(t, 3.6, 4.3) * PI) * 50 : 0 });
  if (t > 3.6 && t < 4.6) sparkle(800, 560, pop(t, 3.6) * 1.2, C.yellow, t * 2);
  bubble(760, 600, "12:00 PM.\nRight on time!", seg(t, 4.0, 4.4) * (1 - seg(t, 6.9, 7.1)));
  g.restore();
}

/* S1a – Up the stairs (7.3 – 13) */
function sceneStairs(t) {
  g.save(); cam(1 + seg(t, 7, 13) * .05, 900, 540);
  bgPhoto('stairs');
  g.fillStyle = 'rgba(255,250,244,.35)'; g.fillRect(0, 0, W, H);
  polaroid(IMG.stairs, 1420, 205, 640, -.03, 'UP TO THE STUDIO', 1);
  // drawn staircase echoing the photo (dark grey carpet)
  const baseX = 120, baseY = 990, sw = 112, sh = 50, n = 7;
  g.fillStyle = '#ece8e3'; g.fillRect(-200, baseY, 1300, 400);
  for (let i = n - 1; i >= 0; i--) {
    const x0 = baseX + i * sw, top = baseY - (i + 1) * sh;
    g.fillStyle = '#3f424b'; g.fillRect(x0, top, 1000 - x0 + 200, sh + 4);
    g.fillStyle = '#5b5e68'; g.fillRect(x0, top, 1000 - x0 + 200, 14);
    g.strokeStyle = '#25272e'; g.lineWidth = 3; line(x0, top, x0, top + sh);
  }
  // handrail
  g.strokeStyle = '#d9d4cc'; g.lineWidth = 10; g.lineCap = 'round'; line(baseX + 40, baseY - 210, baseX + 7 * sw + 80, baseY - 210 - 7 * sh);
  const p = seg(t, 7.8, 12.2);
  const x = lerp(30, baseX + n * sw - 30, ease(p));
  const fi = (x - baseX) / sw;
  const k = clamp(Math.floor(fi) + 1, 0, n);
  const frac = fi - Math.floor(fi);
  const y = baseY - k * sh - (fi > 0 && fi < n ? Math.sin(frac * PI) * 26 : 0);
  customer({ x, y, s: .95, t, walk: p > 0 && p < 1 ? t * 10 : null, aL: .5 + Math.sin(t * 10) * .4, aR: .5 - Math.sin(t * 10) * .4, expr: p >= 1 ? 'joy' : 'grin', blink: blinking(t, 2) });
  g.restore();
}

/* Reception world (used by welcome, hand-over, delivery, goodbye) */
function receptionWorld(t, m) {
  room(830);
  warmPool(560, 300, 520, .45); warmPool(1400, 420, 520, .3);
  pendant(330, 90); pendant(420, 150);
  merciSign(330, 290, 1.05);
  plant(300, 830, 1.15);
  frameOnWall(860, 300, 130, 160, 0); frameOnWall(1030, 330, 110, 110, 3); frameOnWall(1180, 290, 120, 150, 4);
  wallClock(1580, 230, 70, m);
}
function receptionCounterFront() { counter(1180, 712, 470, 118); }

/* S1b – Welcome (13 – 21) */
function sceneWelcome(t) {
  const m = storyMinutes(t);
  g.save(); cam(1.02 + seg(t, 13, 21) * .06, 960, 560);
  receptionWorld(t, m);
  const waving = t > 13.6;
  owner({ x: 1420, y: 830, face: -1, t, aL: .35, aR: waving ? 2.5 + Math.sin(t * 9) * .35 : .3, expr: t > 14.5 && t < 17.5 ? 'talk' : 'joy', blink: blinking(t, 3) });
  receptionCounterFront();
  const p = seg(t, 13.1, 15.9);
  const walking = p > 0 && p < 1;
  customer({ x: lerp(-180, 880, ease(p)), y: 900, s: 1.05, t, walk: walking ? t * 9 : null, aL: walking ? .3 + Math.sin(t * 9) * .4 : .3,
    aR: t > 16.2 && t < 18 ? 2.6 + Math.sin(t * 10) * .3 : (walking ? .3 - Math.sin(t * 9) * .4 : .3), expr: t > 17.6 && t < 20.4 ? 'talk' : 'grin', blink: blinking(t, 4) });
  bubble(1330, 330, 'Welcome to\nMerci Studio!', seg(t, 14.3, 14.7) * (1 - seg(t, 17.4, 17.6)), { tail: -1 });
  bubble(940, 520, 'Hi! I booked\nPackage A!', seg(t, 17.6, 18.0) * (1 - seg(t, 20.5, 20.7)), { tail: -1 });
  g.restore();
}

/* Studio world: shoot set (x 0–1920) + waiting lounge (x 1920–3840) */
const POSES = [
  { t: 21.6, expr: 'grin', aR: 2.5, aL: .4, peaceR: true },
  { t: 24.2, expr: 'joy', aL: 2.8, aR: 2.8 },
  { t: 26.8, expr: 'wink', aL: 2.95, aR: 2.95, tilt: -.1 },
  { t: 29.4, expr: 'joy', aL: 2.4, aR: 2.4, jump: 1 },
  { t: 32.0, expr: 'grin', aL: .9, aR: 2.6, peaceR: true, tilt: .12 },
  { t: 34.6, expr: 'joy', aL: 2.9, aR: .6, legSpread: .3 },
];
const FLASHES = POSES.map(p => p.t + 1.3);
function flashAmt(t) { let f = 0; FLASHES.forEach(ft => { if (t >= ft && t < ft + .45) f = Math.max(f, 1 - (t - ft) / .45); }); return f; }
function photosTaken(t) { return FLASHES.filter(ft => t >= ft).length * 8; }

function studioWorld(t, opts) {
  const m = storyMinutes(t);
  const fl = opts.flash || 0;
  room(860, ['#f3e6da', '#e5d3c1']);
  // backdrop paper
  g.fillStyle = '#5a4a40'; rr(360, 110, 840, 34, 17); g.fill();
  g.fillStyle = vgrad(130, 900, ['#f9dfd8', C.paper, '#f0c7bf']);
  g.beginPath(); g.moveTo(380, 130); g.lineTo(1180, 130); g.lineTo(1180, 820); g.quadraticCurveTo(1180, 900, 1260, 930);
  g.lineTo(300, 930); g.quadraticCurveTo(380, 900, 380, 820); g.closePath(); g.fill();
  g.strokeStyle = 'rgba(0,0,0,.08)'; g.lineWidth = 3; g.stroke();
  warmPool(780, 520, 520, .35 + fl * .4);
  softbox(220, 380, .5, fl);
  softbox(1330, 330, -.45, fl);
  wallClock(1600, 170, 60, m);
  // door to lounge
  g.fillStyle = '#e9dccd'; g.fillRect(1880, -300, 120, 1160);
  rr(1895, 220, 90, 640, 8); fs('#c99a6c', C.ink, 5);
  text('STUDIO', 1940, 180, F(800, 26), '#6b5644');
  // lounge
  g.save(); g.translate(1920, 0);
  warmPool(820, 380, 600, .4); pendant(700, 120); pendant(1000, 70);
  rr(380, 200, 360, 260, 10); fs('#cfe7f7', C.ink, 6); g.strokeStyle = C.ink; g.lineWidth = 5; line(560, 200, 560, 460); line(380, 330, 740, 330);
  text('WAITING LOUNGE', 1300, 250, F(800, 34), '#6b5644');
  frameOnWall(1180, 320, 120, 150, 5); frameOnWall(1340, 300, 150, 150, 1);
  sofa(820, 880, '#f2a85a');
  plant(1180, 860, .8);
  g.restore();
}

/* S2 – Photoshoot (21 – 39) and S3 – Done / Waiting (39 – 46.3) */
function sceneStudio(t) {
  const fl = flashAmt(t);
  const panP = ease(seg(t, 41.6, 43.6));
  let z = lerp(1.0, 1.12, ease(seg(t, 21, 38))), fx = lerp(900, 860, seg(t, 21, 38)), fy = 560;
  if (t > 39) { z = lerp(1.12, 1.0, ease(seg(t, 39, 41.5))); fx = lerp(860, 960, ease(seg(t, 39, 41.5))); }
  fx += panP * 1920 + (t > 43.6 ? 0 : 0);
  if (t > 43.6) { z = lerp(1, 1.1, ease(seg(t, 43.6, 46.3))); fy = lerp(560, 600, seg(t, 43.6, 46.3)); }
  g.save(); cam(z, fx, fy);
  studioWorld(t, { flash: fl });
  // pose state
  let pose = POSES[0]; POSES.forEach(p => { if (t >= p.t - .3) pose = p; });
  const pp = seg(t, pose.t - .3, pose.t + .2);
  // customer
  if (t < 41.6) {
    const done = t > 38.6;
    const jump = done ? Math.abs(Math.sin(seg(t, 39.1, 40.6) * PI * 2)) * 70 : (pose.jump ? Math.sin(seg(t, pose.t + .8, pose.t + 1.8) * PI) * 90 : 0);
    customer({ x: 780, y: 880, s: 1.18, t, noBag: true,
      expr: done ? 'joy' : (t < 21.6 ? 'happy' : pose.expr), aL: done ? 2.7 : lerp(.3, pose.aL ?? .3, pp), aR: done ? 2.7 : lerp(.3, pose.aR ?? .3, pp),
      peaceR: !done && pose.peaceR && pp > .6, tilt: done ? 0 : (pose.tilt || 0) * pp, legSpread: pose.legSpread || 0, jump, blink: blinking(t, 5) && !done });
  } else {
    const p = seg(t, 41.6, 43.9);
    const walking = p > 0 && p < 1;
    if (t < 43.9) customer({ x: lerp(780, 2640, ease(p)), y: 880, s: 1.18, t, walk: walking ? t * 10 : null, aL: .3 + Math.sin(t * 10) * .4, aR: .3 - Math.sin(t * 10) * .4, expr: 'grin', blink: blinking(t, 6) });
    else customer({ x: 2720, y: 810, s: 1.1, t, sit: true, aL: .7, aR: .7, expr: 'happy', lx: 8, ly: -6, blink: blinking(t, 6), bob: Math.sin(t * 3) * 2 });
  }
  // photographer + camera
  tripod(1500, 890, 300);
  const look = t < 38.6 && t > 21.6;
  owner({ x: 1630, y: 890, face: -1, t, aR: look ? 1.75 : (t > 39 && t < 41.6 ? 2.9 : .3), aL: .3, thumbR: t > 39 && t < 41.6, expr: look ? 'focus' : 'joy', blink: blinking(t, 7) });
  camera(1500, 570, 1, fl);
  // flying mini photos
  FLASHES.forEach((ft, i) => {
    const q = seg(t, ft + .1, ft + 1.1);
    if (q > 0 && q < 1) {
      const sx = 1460, sy = 550, ex = 1740, ey = 60;
      const x = lerp(sx, ex, ease(q)), y = lerp(sy, ey, ease(q)) - Math.sin(q * PI) * 140;
      printPhoto(x, y, 90 * (1 - q * .5), i, Math.sin(q * 6) * .3);
    }
  });
  if (t > 38.6 && t < 41.8) {
    const sp = pop(t, 38.9, .45);
    g.save(); g.translate(780, 420); g.rotate(-.12); g.scale(sp, sp);
    rr(-230, -70, 460, 140, 30); fs(C.coral, C.ink, 7);
    text('DONE!  12:15', 0, 4, F(900, 64), '#ffffff', 'center', C.ink, 10);
    g.restore();
    for (let i = 0; i < 6; i++) sparkle(780 + Math.cos(i + t) * 300, 450 + Math.sin(i * 2 + t) * 160, sp * .9, C.yellow, t + i);
  }
  if (t > 44) {
    const q = pop(t, 44.2, .4);
    g.save(); g.translate(2560, 420); g.scale(q, q);
    circle(120, 110, 14); fs('#fff', C.ink, 4); circle(150, 140, 9); fs('#fff', C.ink, 4);
    g.beginPath(); g.ellipse(0, 0, 210, 120, 0, 0, TAU); fs('#ffffff', C.ink, 6);
    [-1, 0, 1].forEach(k => { const b = Math.sin(t * 4 + k) * 6; printPhoto(k * 110, -6 + b, 80, k + 3, k * .15); });
    g.restore();
    const dots = Math.floor(t * 2.5) % 4;
    text('.'.repeat(dots), 2860, 620, F(900, 70), C.ink, 'left');
  }
  g.restore();
  // photo counter (screen space)
  if (t > 21.5 && t < 41.6) {
    const a = seg(t, 21.5, 22) * (1 - seg(t, 41, 41.6));
    g.save(); g.globalAlpha = a; g.translate(230, 90);
    rr(-150, -42, 300, 84, 24); fs('#ffffff', C.ink, 5);
    g.save(); g.translate(-100, 0); g.scale(.45, .45); camera(0, 30, 1, 0); g.restore();
    text(`${photosTaken(t)} PHOTOS`, 30, 2, F(900, 30), C.ink);
    g.restore();
  }
  if (fl > 0) { g.fillStyle = `rgba(255,255,250,${fl * .55})`; g.fillRect(0, 0, W, H); }
}

/* S4 – Downloading (46.3 – 56.3) */
function monitorScreen(t, x, y, w, h) {
  g.save(); rr(x, y, w, h, 8); g.clip();
  g.fillStyle = '#f4f6fb'; g.fillRect(x, y, w, h);
  g.fillStyle = '#e4e8f2'; g.fillRect(x, y, w, 46);
  [['#ff6b6b', 0], ['#ffc83d', 1], ['#58d26a', 2]].forEach(([c, i]) => { circle(x + 26 + i * 26, y + 23, 8); fs(c); });
  text('MERCI STUDIO  ·  SESSION 12:00 PM', x + w / 2, y + 24, F(800, 18), '#4b5163');
  const dl = seg(t, 47.4, 50.6);
  if (t < 50.9) {
    // folder + bar
    g.save(); g.translate(x + w / 2, y + h * .42);
    rr(-80, -60, 70, 22, 6); fs('#ffb84d'); rr(-80, -50, 160, 110, 12); fs('#ffc85f', C.ink, 4);
    g.restore();
    text(dl < 1 ? 'Downloading photos...' : 'Download complete!', x + w / 2, y + h * .66, F(800, 30), C.ink);
    rr(x + 120, y + h * .74, w - 240, 26, 13); fs('#dde2ec');
    rr(x + 120, y + h * .74, Math.max(26, (w - 240) * dl), 26, 13); fs('#5bb8ff');
    text(`${Math.round(dl * 48)} / 48   ·   ${Math.round(dl * 100)}%`, x + w / 2, y + h * .86, F(700, 22), '#4b5163');
  } else {
    const cols = 6, gap = 14, tw = (w - gap * (cols + 1)) / cols, th = tw * .78;
    const scroll = ease(seg(t, 53.4, 55.4)) * (th + gap) * 2;
    for (let i = 0; i < 48; i++) {
      const c = i % cols, r = Math.floor(i / cols);
      const ap = seg(t, 50.9 + i * .05, 51.2 + i * .05);
      if (ap <= 0) continue;
      const px = x + gap + c * (tw + gap), py = y + 60 + r * (th + gap) - scroll;
      if (py > y + h || py + th < y + 46) continue;
      g.save(); g.globalAlpha = ap; const s = .7 + .3 * back(ap);
      g.translate(px + tw / 2, py + th / 2); g.scale(s, s);
      miniPhoto(-tw / 2, -th / 2, tw, th, i, { lw: 2 }); g.restore();
    }
  }
  g.restore();
}
function sceneDownload(t) {
  const m = storyMinutes(t);
  let z = 1, fx = 960, fy = 560;
  const zin = ease(seg(t, 47.6, 49.4)), zout = ease(seg(t, 54.6, 56.1));
  z = lerp(1, 1.42, zin - zout * .45); fx = lerp(960, 900, zin); fy = lerp(560, 455, zin - zout * .3);
  g.save(); cam(z, fx, fy);
  room(860, ['#eef1f4', '#dfe4ea']);
  warmPool(900, 330, 650, .35);
  // window
  rr(120, 160, 380, 330, 10); fs('#cfe7f7', C.ink, 6); g.strokeStyle = C.ink; g.lineWidth = 5; line(310, 160, 310, 490); line(120, 325, 500, 325);
  wallClock(1660, 200, 64, m);
  // desk
  rr(420, 690, 1000, 34, 10); fs('#c99a6c', C.ink, 6);
  g.fillStyle = C.ink; g.fillRect(460, 724, 22, 150); g.fillRect(1358, 724, 22, 150);
  // monitor
  rr(880, 600, 40, 90, 6); fs('#bfc5d1', C.ink, 5); rr(820, 676, 160, 18, 8); fs('#bfc5d1', C.ink, 5);
  rr(560, 190, 680, 430, 22); fs('#2a2d37', C.ink, 6);
  monitorScreen(t, 580, 210, 640, 380);
  // keyboard + card reader
  rr(700, 662, 260, 26, 8); fs('#e9ecf2', C.ink, 4);
  rr(1060, 664, 80, 24, 6); fs('#3a3e4b', C.ink, 4);
  const blink = t > 47 && t < 50.6 && Math.floor(t * 6) % 2;
  circle(1128, 676, 5); fs(blink ? '#58d26a' : '#2b8a3e');
  const cardIn = ease(seg(t, 46.5, 47.3));
  rr(1080, 630 + cardIn * 30, 36, 44, 4); fs('#3b82f6', C.ink, 3);
  // chair + owner
  rr(1460, 640, 150, 200, 30); fs('#3b3f4c', C.ink, 6);
  owner({ x: 1500, y: 750, face: -1, t, sit: true, aL: t < 47.4 ? lerp(.4, 1.3, seg(t, 46.4, 46.9)) : 1.2, aR: t > 54.8 ? 2.8 : .5, thumbR: t > 54.8, expr: t > 50.8 ? 'joy' : 'happy', lx: 6, ly: -4, blink: blinking(t, 8) });
  g.strokeStyle = C.ink; g.lineWidth = 9; line(1535, 840, 1535, 880); line(1490, 880, 1580, 880);
  g.restore();
}

/* S5 – Selection (56.3 – 68.3) */
const SELECT_TAPS = [61.9, 62.7, 64.7, 66.0, 66.8];
const SELECT_IDS = [1, 6, 9, 11, 14];
function selectedCount(t) { return SELECT_TAPS.filter(x => t >= x).length; }
function ipadUI(t, x, y, w, h) {
  g.save(); rr(x, y, w, h, 18); g.clip();
  g.fillStyle = '#fbfaf8'; g.fillRect(x, y, w, h);
  const n = selectedCount(t);
  const header = () => {
  g.fillStyle = '#ffffff'; g.fillRect(x, y, w, 96);
  g.fillStyle = 'rgba(0,0,0,.06)'; g.fillRect(x, y + 96, w, 3);
  text('Pick your favourites', x + 40, y + 48, F(800, 38), C.ink, 'left');
  const btnP = pop(t, 67.2, .4);
  rr(x + w - 330, y + 22, 290, 54, 27); fs(n >= 5 && t > 67.2 ? C.coral : '#eceef3');
  text(n >= 5 && t > 67.2 ? 'PRINT 5 PHOTOS' : `SELECTED ${n}`, x + w - 185, y + 50, F(900, 24), n >= 5 && t > 67.2 ? '#fff' : C.ink);
  if (t > 67.2 && t < 67.8) { g.strokeStyle = `rgba(255,123,134,${1 - btnP * .5})`; g.lineWidth = 5; rr(x + w - 336, y + 16, 302, 66, 33); g.stroke(); }
  };
  const cols = 4, gap = 22, tw = (w - gap * (cols + 1)) / cols, th = tw * .75;
  const scroll = ease(seg(t, 59.9, 61.3)) * (th + gap) * 1.5;
  for (let i = 0; i < 24; i++) {
    const c = i % cols, r = Math.floor(i / cols);
    const px = x + gap + c * (tw + gap), py = y + 120 + r * (th + gap) - scroll;
    if (py > y + h || py + th < y + 96) continue;
    miniPhoto(px, py, tw, th, i, { lw: 0, stroke: false, r: 12 });
    const si = SELECT_IDS.indexOf(i);
    if (si >= 0 && t >= SELECT_TAPS[si]) {
      const q = pop(t, SELECT_TAPS[si], .35);
      rr(px, py, tw, th, 12); fs(null, C.coral, 8);
      g.save(); g.translate(px + tw - 34, py + 34); g.scale(q, q);
      circle(0, 0, 24); fs(C.coral, '#fff', 4); heart(0, 8, .8, '#ffffff'); g.restore();
    }
  }
  header();
  // zoomed photo view
  const zin = ease(seg(t, 63.1, 63.7)), zout = ease(seg(t, 65.2, 65.7));
  const zp = zin - zout;
  if (zp > 0.001) {
    g.fillStyle = `rgba(20,20,28,${.75 * zp})`; g.fillRect(x, y, w, h);
    const r = (scroll, i) => { const c = i % cols, rw = Math.floor(i / cols); return [x + gap + c * (tw + gap), y + 120 + rw * (th + gap) - scroll]; };
    const [sx, sy] = r(scroll, 9);
    const pinch = 1 + ease(seg(t, 63.9, 64.5)) * .18;
    const fw = (h - 120) / .75 * .95 * pinch, fh = (h - 120) * .95 * pinch;
    const cx = lerp(sx + tw / 2, x + w / 2, zp), cy = lerp(sy + th / 2, y + 96 + (h - 96) / 2, zp);
    const ww = lerp(tw, Math.min(fw, w - 60), zp), hh = lerp(th, fh, zp);
    miniPhoto(cx - ww / 2, cy - hh / 2, ww, hh, 9, { stroke: false, r: 16 });
    if (t > 64.7) { const q = pop(t, 64.7); g.save(); g.translate(cx + ww / 2 - 70, cy - hh / 2 + 70); g.scale(q * 1.6, q * 1.6); circle(0, 0, 26); fs(C.coral, '#fff', 4); heart(0, 8, .85, '#fff'); g.restore(); }
  }
  g.restore();
}
function fingerPath(t) {
  // keyframes [time, x, y] in iPad-local 0..1 coords
  const K = [[59.3, .7, 1.2], [59.8, .55, .75], [61.3, .55, .35], [61.6, .42, .45], [61.9, .4, .44], [62.4, .62, .5], [62.7, .66, .52],
    [63.0, .66, .64], [63.6, .62, .66], [64.4, .62, .64], [64.7, .82, .3], [65.4, .8, .45], [65.8, .2, .66], [66.0, .2, .66],
    [66.5, .62, .82], [66.8, .64, .82], [67.0, .8, .2], [67.25, .86, .12], [68.4, .9, 1.3]];
  if (t <= K[0][0]) return [K[0][1], K[0][2]];
  for (let i = 1; i < K.length; i++) if (t <= K[i][0]) { const q = ease(seg(t, K[i - 1][0], K[i][0])); return [lerp(K[i - 1][1], K[i][1], q), lerp(K[i - 1][2], K[i][2], q)]; }
  return [K[K.length - 1][1], K[K.length - 1][2]];
}
function sceneSelect(t) {
  const m = storyMinutes(t);
  if (t < 59.3) {
    const z = lerp(1, 1.08, seg(t, 56, 58.6)) + Math.pow(seg(t, 58.4, 59.3), 2) * 3.2;
    g.save(); cam(z, lerp(960, 1010, seg(t, 58.4, 59.3)), lerp(560, 600, seg(t, 58.4, 59.3)));
    room(860, ['#f3e6da', '#e5d3c1']);
    warmPool(900, 380, 620, .45); pendant(780, 120); pendant(1080, 70);
    rr(300, 200, 360, 260, 10); fs('#cfe7f7', C.ink, 6); g.strokeStyle = C.ink; g.lineWidth = 5; line(480, 200, 480, 460); line(300, 330, 660, 330);
    wallClock(1620, 220, 64, m);
    frameOnWall(1260, 320, 120, 150, 5); frameOnWall(1420, 300, 150, 150, 1);
    sofa(960, 880, '#f2a85a');
    customer({ x: 960, y: 810, s: 1.1, t, sit: true, aL: 1.25, aR: 1.25, expr: 'grin', lx: 4, ly: 8, blink: blinking(t, 9),
      holdR: () => { g.save(); g.translate(-30, -10); ipadProp(150, 104, (sx, sy, sw, sh) => { for (let i = 0; i < 6; i++) miniPhoto(sx + 4 + (i % 3) * (sw / 3), sy + 4 + Math.floor(i / 3) * (sh / 2), sw / 3 - 6, sh / 2 - 6, i, { stroke: false, r: 2 }); }); g.restore(); } });
    g.restore();
    if (t > 58.9) { g.fillStyle = `rgba(255,255,255,${seg(t, 58.9, 59.3)})`; g.fillRect(0, 0, W, H); }
    return;
  }
  // full iPad view
  g.fillStyle = vgrad(0, H, ['#f8e7d8', '#efd2bd']); g.fillRect(0, 0, W, H);
  for (let i = 0; i < 14; i++) { circle(hash(i) * W, hash(i + 9) * H, 40 + hash(i + 3) * 90); g.fillStyle = `rgba(255,${200 + hash(i) * 40 | 0},170,.25)`; g.fill(); }
  const iw = 1300, ih = 760, ix = W / 2 - iw / 2, iy = 250;
  const ent = easeOut(seg(t, 59.3, 59.9));
  g.save(); g.translate(W / 2, iy + ih / 2); g.scale(.9 + .1 * ent, .9 + .1 * ent); g.translate(-W / 2, -(iy + ih / 2));
  shadowOn(50, 24, .35); rr(ix - 30, iy - 30, iw + 60, ih + 60, 56); fs('#262932'); shadowOff();
  rr(ix - 30, iy - 30, iw + 60, ih + 60, 56); fs(null, C.ink, 6);
  ipadUI(t, ix, iy, iw, ih);
  g.restore();
  if (t < 59.6) { g.fillStyle = `rgba(255,255,255,${1 - seg(t, 59.3, 59.6)})`; g.fillRect(0, 0, W, H); }
  // finger(s)
  const [fx, fy] = fingerPath(t);
  const taps = [...SELECT_TAPS, 67.25];
  let press = 0; taps.forEach(tp => { if (t >= tp && t < tp + .4) press = 1 - (t - tp) / .4; });
  if (t > 63.6 && t < 64.6) {
    const sp = ease(seg(t, 63.9, 64.5)) * 120;
    finger(ix + iw * .58 - sp, iy + ih * .62 - sp * .3, 1, 0);
    finger(ix + iw * .66 + sp, iy + ih * .66 + sp * .3, 1, 0);
  } else finger(ix + iw * fx, iy + ih * fy, 1, press);
}

/* S6 – Printing (68.3 – 81.3) */
function printerBox(x, y, t, printing) {
  const vib = printing ? Math.sin(t * 60) * 1.5 : 0;
  g.save(); g.translate(x, y + vib);
  shadowOn(26, 12, .25); rr(-230, -190, 460, 190, 30); fs('#f1f3f7'); shadowOff();
  rr(-230, -190, 460, 190, 30); fs(null, C.ink, 6);
  rr(-200, -160, 150, 70, 12); fs('#1f2533', C.ink, 4);
  text(printing ? 'PRINTING' : 'READY', -125, -125, F(800, 20), '#7fe39a');
  rr(-170, -60, 340, 20, 10); fs('#2b2e38');
  circle(150, -125, 12); fs(printing && Math.floor(t * 4) % 2 ? '#58d26a' : '#2b8a3e', C.ink, 3);
  text('PHOTO PRINTER', 30, -126, F(800, 18), '#8a90a0');
  g.restore();
}
const PRINT_T0 = 71.6, PRINT_DT = 1.15;
function sceneHandover(t) {
  g.save(); cam(1.06, 1000, 560);
  receptionWorld(t, storyMinutes(t));
  const p = ease(seg(t, 68.9, 69.9));
  const ipX = lerp(1010, 1290, p), ipY = lerp(560, 520, p) - Math.sin(p * PI) * 60;
  owner({ x: 1420, y: 830, face: -1, t, aL: .35, aR: p > .9 ? 1.4 : .3, expr: t > 70.2 ? 'talk' : 'happy', blink: blinking(t, 10) });
  receptionCounterFront();
  customer({ x: 900, y: 900, s: 1.05, t, aR: lerp(1.6, .3, seg(t, 69.6, 70)), aL: .3, expr: t < 69.6 ? 'talk' : 'joy', blink: blinking(t, 11) });
  g.save(); g.translate(ipX, ipY); g.rotate(-.1 + p * .2); ipadProp(150, 104, (sx, sy, sw, sh) => { for (let i = 0; i < 5; i++) miniPhoto(sx + 4 + (i % 3) * (sw / 3), sy + 4 + Math.floor(i / 3) * (sh / 2), sw / 3 - 6, sh / 2 - 6, SELECT_IDS[i], { stroke: false, r: 2 }); }); g.restore();
  bubble(920, 500, 'These 5,\nplease!', seg(t, 68.6, 68.9) * (1 - seg(t, 70.0, 70.2)), { tail: 1 });
  bubble(1300, 360, 'Printing\nright away!', seg(t, 70.2, 70.5), { tail: -1 });
  g.restore();
}
function scenePrint(t) {
  if (t < 71.1) return sceneHandover(t);
  const checkP = ease(seg(t, 77.3, 78.3));
  const z = lerp(1.15, 1.0, checkP), fx = lerp(900, 960, checkP), fy = lerp(640, 600, checkP);
  g.save(); cam(z, fx, fy);
  room(780, ['#f5ede3', '#eadccb']);
  warmPool(800, 300, 600, .45); pendant(820, 60, 1);
  wallClock(1580, 200, 64, storyMinutes(t));
  merciSign(260, 220, .6);
  // counter top
  g.fillStyle = vgrad(700, 1080, ['#d8ab7d', '#b98a5e']); g.fillRect(-200, 720, 2400, 400);
  g.fillStyle = '#e5be93'; g.fillRect(-200, 700, 2400, 30);
  g.strokeStyle = C.ink; g.lineWidth = 6; line(-200, 700, 2200, 700);
  // owner behind counter
  const holding = t > 78.6;
  owner({ x: 1470, y: 880, face: -1, t, aL: holding ? 1.9 : .3, aR: holding ? 1.5 : .3, expr: t > 79.4 ? 'joy' : (holding ? 'wow' : 'happy'), lx: -4, ly: holding ? -4 : 6, blink: blinking(t, 12),
    holdR: holding ? () => { g.save(); g.rotate(-.5); g.strokeStyle = C.ink; g.lineWidth = 12; line(0, 0, 0, -40); g.strokeStyle = '#7a5a3a'; g.lineWidth = 7; line(0, 0, 0, -40); circle(0, -80, 44); fs('rgba(200,235,255,.45)', C.ink, 8); g.restore(); } : null });
  g.fillStyle = vgrad(700, 1080, ['#d8ab7d', '#b98a5e']); g.fillRect(1260, 760, 500, 400);
  g.strokeStyle = 'rgba(0,0,0,.15)'; g.lineWidth = 3; line(1260, 760, 1760, 760);
  const printing = t > PRINT_T0 && t < PRINT_T0 + PRINT_DT * 5 + .2;
  for (let i = 0; i < 5; i++) { const t0 = PRINT_T0 + i * PRINT_DT, out = seg(t, t0, t0 + .8); if (t >= t0 && out < 1) printPhoto(760, lerp(700, 470, out), 150, SELECT_IDS[i], 0, out); }
  printerBox(760, 760, t, printing);
  // prints
  for (let i = 0; i < 5; i++) {
    const t0 = PRINT_T0 + i * PRINT_DT;
    if (t < t0) continue;
    const out = seg(t, t0, t0 + .8);
    const slide = ease(seg(t, t0 + .8, t0 + 1.1));
    let x = 760, y = 470, rot = 0, w = 150;
    if (out >= 1) { x = lerp(760, 1120, slide); y = lerp(470, 780 - i * 6, slide); rot = lerp(0, -.08 + i * .04, slide); }
    const toRow = ease(seg(t, 77.3 + i * .08, 78.1 + i * .08));
    if (toRow > 0) { x = lerp(x, 330 + i * 200, toRow); y = lerp(y, 860, toRow); rot = lerp(rot, 0, toRow); w = lerp(150, 165, toRow); }
    if (out < 1) continue;
    if (slide < 1 || toRow > 0) { x = lerp(760, x, 1); }
    printPhoto(x, y, w, SELECT_IDS[i], rot, 1);
    if (t > 78.6 + i * .32) { const q = pop(t, 78.6 + i * .32); g.save(); g.translate(330 + i * 200 + 55, 790); g.scale(q, q); circle(0, 0, 28); fs(C.green, C.ink, 5); g.strokeStyle = '#fff'; g.lineWidth = 7; g.beginPath(); g.moveTo(-12, 0); g.lineTo(-3, 10); g.lineTo(14, -10); g.stroke(); g.restore(); }
  }
  // print count chip
  const done = clamp(Math.floor((t - PRINT_T0) / PRINT_DT + .3), 0, 5);
  if (t > PRINT_T0 - .3 && t < 77.4) { g.save(); g.translate(760, 470); rr(-110, -32, 220, 64, 32); fs('#fff', C.ink, 5); text(`${done} / 5 PRINTED`, 0, 2, F(900, 26), C.ink); g.restore(); }
  bubble(1420, 560, 'Perfect!', seg(t, 79.6, 79.9) * (1 - seg(t, 81.2, 81.4)), { tail: -1 });
  g.restore();
}

/* S7 – Delivery (81.3 – 92.3) */
function photoFan() {
  g.save(); g.translate(0, -40);
  [-1, 0, 1].forEach(k => printPhoto(k * 34, -10 + Math.abs(k) * 8, 92, SELECT_IDS[k + 1], k * .25)); g.restore();
}
function phoneUI(t, x, y, w, h) {
  g.save(); rr(x, y, w, h, 34); g.clip();
  g.fillStyle = '#f5f6fa'; g.fillRect(x, y, w, h);
  text('12:40', x + 46, y + 32, F(800, 20), C.ink, 'left');
  const msgP = pop(t, 85.8, .4);
  const open = ease(seg(t, 87.6, 88.3));
  if (open < 1) {
    g.save(); g.globalAlpha = 1 - open;
    text('Messages', x + w / 2, y + 90, F(800, 26), C.ink);
    g.save(); g.translate(x + 24, y + 140); g.scale(1, msgP);
    rr(0, 0, w - 48, 300, 26); fs('#ffffff', '#dfe3ea', 3);
    circle(46, 46, 26); fs(C.ink); text('M', 46, 47, F(900, 24), '#fff');
    text('Merci Studio', 86, 38, F(800, 22), C.ink, 'left'); text('just now', 86, 64, F(600, 16), '#8a90a0', 'left');
    text('Your softcopy is ready!', 24, 112, F(700, 21), C.ink, 'left');
    text('All 48 photos are in', 24, 142, F(600, 19), '#4b5163', 'left');
    text('your Google Drive folder:', 24, 168, F(600, 19), '#4b5163', 'left');
    rr(20, 196, w - 88, 76, 16); fs('#eef4ff', '#b9d0ff', 3);
    g.save(); g.translate(56, 234); rr(-22, -16, 18, 8, 3); fs('#ffb84d'); rr(-22, -12, 44, 30, 5); fs('#ffc85f', C.ink, 2.5); g.restore();
    text('Google Drive link', 94, 222, F(800, 19), '#2f6fe0', 'left');
    text('Merci Studio · Softcopy', 94, 248, F(600, 16), '#4b5163', 'left');
    g.restore();
    g.restore();
  }
  if (open > 0) {
    g.save(); g.globalAlpha = open;
    g.fillStyle = '#ffffff'; g.fillRect(x, y + 50, w, 90);
    g.save(); g.translate(x + 50, y + 96); rr(-22, -18, 18, 8, 3); fs('#ffb84d'); rr(-22, -14, 44, 32, 5); fs('#ffc85f', C.ink, 2.5); g.restore();
    text('Merci Studio · Softcopy', x + 86, y + 84, F(800, 21), C.ink, 'left');
    text('48 photos', x + 86, y + 110, F(600, 17), '#8a90a0', 'left');
    const cols = 3, gap = 8, tw = (w - gap * 4) / cols;
    const scroll = ease(seg(t, 89.2, 91.4)) * tw * 3;
    for (let i = 0; i < 30; i++) { const c = i % cols, r = Math.floor(i / cols); const py = y + 150 + r * (tw + gap) - scroll; if (py > y + h || py + tw < y + 140) continue; miniPhoto(x + gap + c * (tw + gap), py, tw, tw, i, { stroke: false, r: 4 }); }
    g.restore();
  }
  g.restore();
}
function sceneDeliver(t) {
  const m = storyMinutes(t);
  const split = ease(seg(t, 84.9, 85.8));
  g.save(); cam(lerp(1.04, 1.25, split), lerp(1000, 1220, split), lerp(560, 600, split));
  receptionWorld(t, m);
  const p = ease(seg(t, 81.8, 82.9));
  const got = t > 83.0;
  owner({ x: 1420, y: 830, face: -1, t, aL: .35, aR: !got ? lerp(.3, 1.6, seg(t, 81.6, 82.2)) : (t > 83.6 ? 2.5 + Math.sin(t * 8) * .2 : .3), expr: 'joy', blink: blinking(t, 13) });
  receptionCounterFront();
  const cx = 1010;
  customer({ x: cx, y: 900, s: 1.05, t, aR: got ? 2.2 : lerp(.3, 1.5, seg(t, 82.2, 82.8)), aL: t > 85.4 ? 1.5 : .3, expr: got ? 'joy' : 'grin', blink: blinking(t, 14), jump: got && t < 84.6 ? Math.abs(Math.sin(seg(t, 83, 84.6) * PI * 2)) * 60 : 0,
    holdR: got ? photoFan : null,
    holdL: t > 85.4 ? () => { g.save(); g.rotate(-.2); rr(-26, -48, 52, 92, 10); fs('#262932', C.ink, 4); rr(-20, -40, 40, 74, 6); fs('#dfeaff'); g.restore(); } : null });
  if (!got) { const x = lerp(1290, 1110, p), y = lerp(560, 560, p) - Math.sin(p * PI) * 60; g.save(); g.translate(x, y); rr(-80, -55, 160, 110, 10); fs('#f3dfc4', C.ink, 5); text('MERCI', 0, 2, F(800, 26), '#6b5644'); g.restore(); }
  if (got && t < 85.2) for (let i = 0; i < 5; i++) heart(cx - 120 + i * 60, 330 - ((t - 83 + i * .3) % 1.6) * 120, .9, C.coral);
  g.restore();
  if (split > 0) {
    // phone panel slides in on the right
    const px = lerp(W + 300, 1380, split), py = 560;
    const pw = 420, ph = 820;
    g.save(); g.translate(px, py);
    shadowOn(50, 24, .4); rr(-pw / 2 - 16, -ph / 2 - 16, pw + 32, ph + 32, 60); fs('#23262f'); shadowOff();
    rr(-pw / 2 - 16, -ph / 2 - 16, pw + 32, ph + 32, 60); fs(null, C.ink, 6);
    phoneUI(t, -pw / 2, -ph / 2, pw, ph);
    rr(-60, -ph / 2 + 10, 120, 28, 14); fs('#23262f');
    g.restore();
    if (t > 87.3 && t < 87.9) finger(px + 20, py - 80, .9, 1 - seg(t, 87.55, 87.9));
  }
}

/* S8 – Goodbye (92.3 – 98.3) */
function sceneGoodbye(t) {
  const m = storyMinutes(t);
  g.save(); cam(1.04, 960, 560);
  receptionWorld(t, m);
  owner({ x: 1420, y: 830, face: -1, t, aL: .35, aR: t > 94 ? 2.5 + Math.sin(t * 9) * .35 : .3, expr: t > 94.3 && t < 96.5 ? 'talk' : 'joy', blink: blinking(t, 15) });
  receptionCounterFront();
  const bow = Math.sin(seg(t, 92.6, 93.8) * PI) * .35;
  const p = ease(seg(t, 95.2, 98.2));
  const walking = p > 0 && p < 1;
  customer({ x: lerp(1010, 120, p), y: 900, s: 1.05, t, face: walking ? -1 : 1, tilt: bow, walk: walking ? t * 9 : null,
    aR: walking ? 2.5 + Math.sin(t * 10) * .4 : (t > 93.8 ? 2.4 + Math.sin(t * 10) * .3 : .3), aL: .4, expr: bow > .05 ? 'joy' : (walking ? 'grin' : 'talk'), lx: walking ? -14 : 0, blink: blinking(t, 16),
    holdL: photoFanSmall });
  bubble(1010, 450, 'Thank you\nso much!', seg(t, 92.8, 93.1) * (1 - seg(t, 94.8, 95.0)), { tail: 1 });
  bubble(1330, 330, 'Come again\nsoon!', seg(t, 94.4, 94.7) * (1 - seg(t, 97.6, 97.8)), { tail: -1 });
  for (let i = 0; i < 6; i++) { const hp = ((t - 92.4) * .7 + hash(i)) % 1; heart(300 + hash(i + 2) * 1300, 760 - hp * 600, .8 * Math.sin(hp * PI), C.coral); }
  g.restore();
}
function photoFanSmall() { g.save(); g.scale(.8, .8); photoFan(); g.restore(); }

/* End card (98.3 – 106) */
function sceneEnd(t) {
  const gr = g.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 1200);
  gr.addColorStop(0, '#fff6ea'); gr.addColorStop(1, '#f2d2bb'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 40; i++) {
    const y = ((hash(i) * H + (t - 98) * (60 + hash(i + 5) * 80)) % (H + 100)) - 50;
    g.save(); g.translate(hash(i + 7) * W, y); g.rotate(t * (hash(i + 1) - .5) * 4);
    g.fillStyle = [C.coral, C.yellow, '#8fd3ff', '#a9e6bd', '#cdb5ff'][i % 5]; g.fillRect(-9, -5, 18, 10); g.restore();
  }
  const a = seg(t, 98.3, 99.1);
  const la = easeOut(a);
  polaroid(IMG.store, lerp(-300, 330, la), 210, 560, -.07, 'OUR STUDIO', 1);
  polaroid(IMG.stairs, lerp(W + 300, 1600, la), 190, 600, .06, 'COME ON UP!', 1);
  const t1 = pop(t, 99.0, .5), t2 = pop(t, 99.7, .5), t3 = pop(t, 100.4, .5);
  g.save(); g.translate(W / 2, 360); g.scale(t1, t1);
  heart(0, 0, 2.4, C.coral); g.restore();
  g.save(); g.translate(W / 2, 520); g.scale(t2, t2);
  text('Thank You for', 0, -50, F(900, 80), '#ffffff', 'center', C.ink, 16);
  text('Choosing Us!', 0, 45, F(900, 92), C.yellow, 'center', C.ink, 16);
  g.restore();
  g.save(); g.translate(W / 2, 720); g.scale(t3, t3);
  rr(-470, -48, 940, 96, 48); fs(C.navy);
  text('Your Memories, Beautifully Captured.', 0, 2, F(800, 42), '#ffffff');
  g.restore();
  const t4 = seg(t, 101.2, 101.8);
  g.save(); g.globalAlpha = t4; text('MERCI STUDIO', W / 2, 850, F(900, 44), C.ink);
  text('Mirror Photobooth  ·  High Angle  ·  Self Photo', W / 2, 900, F(700, 26), '#6b5644');
  text('Arrive 12:00 PM   →   Prints + softcopy by 12:40 PM', W / 2, 950, F(700, 24), '#8a6f5a'); g.restore();
  for (let i = 0; i < 8; i++) sparkle(W / 2 + Math.cos(i * .8) * (560 + i * 10), 520 + Math.sin(i * 1.7) * 260, (0.6 + .4 * Math.sin(t * 3 + i)) * t2, C.yellow, t + i);
  if (t > 105.2) { g.fillStyle = `rgba(0,0,0,${seg(t, 105.2, 106)})`; g.fillRect(0, 0, W, H); }
}

/* ---------------- timeline + transitions ---------------- */
const SCENES = [
  { a: 0, b: 7.3, fn: sceneArrive },
  { a: 7.3, b: 13.0, fn: sceneStairs },
  { a: 13.0, b: 21.0, fn: sceneWelcome },
  { a: 21.0, b: 46.3, fn: sceneStudio },
  { a: 46.3, b: 56.3, fn: sceneDownload },
  { a: 56.3, b: 68.3, fn: sceneSelect },
  { a: 68.3, b: 81.3, fn: scenePrint },
  { a: 81.3, b: 92.3, fn: sceneDeliver },
  { a: 92.3, b: 98.3, fn: sceneGoodbye },
  { a: 98.3, b: 106.1, fn: sceneEnd },
];
const TRANS = { 7.3: ['whip', .7], 13.0: ['iris', .8], 21.0: ['whip', .7], 46.3: ['iris', .8], 56.3: ['whip', .7], 68.3: ['iris', .8], 81.3: ['whip', .7], 92.3: ['iris', .8], 98.3: ['fade', .8] };
const bufA = document.createElement('canvas'), bufB = document.createElement('canvas');
bufA.width = bufB.width = W; bufA.height = bufB.height = H;
const ctxA = bufA.getContext('2d'), ctxB = bufB.getContext('2d');

function drawScene(sc, t, ctx) { const prev = g; g = ctx; g.save(); g.clearRect(0, 0, W, H); sc.fn(t); g.restore(); vignette(); g = prev; }
function vignette() {
  const gr = g.createRadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250);
  gr.addColorStop(0, 'rgba(60,30,10,0)'); gr.addColorStop(1, 'rgba(60,30,10,0.28)');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
}
function render(t) {
  g = mainCtx;
  g.setTransform(1, 0, 0, 1, 0, 0);
  let done = false;
  for (let i = 1; i < SCENES.length; i++) {
    const b = SCENES[i].a; const tr = TRANS[b];
    if (!tr) continue;
    const [type, d] = tr;
    if (t >= b - d / 2 && t < b + d / 2) {
      const p = ease(seg(t, b - d / 2, b + d / 2));
      drawScene(SCENES[i - 1], t, ctxA); drawScene(SCENES[i], t, ctxB);
      g.clearRect(0, 0, W, H);
      if (type === 'whip') {
        const bl = Math.sin(p * PI) * 18;
        g.filter = `blur(${bl}px)`;
        g.drawImage(bufA, -p * W, 0); g.drawImage(bufB, (1 - p) * W, 0);
        g.filter = 'none';
      } else if (type === 'iris') {
        g.drawImage(bufA, 0, 0);
        g.save(); circle(W / 2, H / 2, p * 1200); g.clip(); g.drawImage(bufB, 0, 0); g.restore();
        if (p > 0 && p < 1) { circle(W / 2, H / 2, p * 1200); fs(null, '#ffffff', 18); }
      } else {
        g.drawImage(bufA, 0, 0); g.globalAlpha = p; g.drawImage(bufB, 0, 0); g.globalAlpha = 1;
      }
      done = true; break;
    }
  }
  if (!done) {
    const sc = SCENES.find(s => t >= s.a && t < s.b) || SCENES[SCENES.length - 1];
    g.save(); sc.fn(t); g.restore(); vignette();
  }
  drawHUD(t);
  drawCaption(t);
}

/* ---------------- sound cue sheet (read by the audio builder) ---------------- */
const SFX = (() => {
  const s = [];
  Object.keys(TRANS).forEach(k => s.push({ t: +k - .3, type: 'whoosh' }));
  FLASHES.forEach(t => s.push({ t, type: 'shutter' }));
  s.push({ t: 3.6, type: 'ding' }, { t: 38.9, type: 'tada' }, { t: 50.6, type: 'ding' }, { t: 67.25, type: 'tap' }, { t: 83.0, type: 'tada' }, { t: 99.0, type: 'chime' });
  [4.0, 14.3, 17.6, 68.6, 70.2, 79.6, 92.8, 94.4].forEach(t => s.push({ t, type: 'pop' }));
  SELECT_TAPS.forEach(t => s.push({ t, type: 'tap' }));
  [61.3, 87.55].forEach(t => s.push({ t, type: 'tap' }));
  for (let i = 0; i < 5; i++) s.push({ t: PRINT_T0 + i * PRINT_DT, type: 'print' });
  for (let i = 0; i < 5; i++) s.push({ t: 78.6 + i * .32, type: 'check' });
  s.push({ t: 85.8, type: 'notify' });
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
