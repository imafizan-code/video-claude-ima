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

