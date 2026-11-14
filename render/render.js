// Usage:
//   node render/render.js stills 5 23 50 ...      -> out/stills/t_<sec>.png
//   node render/render.js video [workers]          -> out/video_noaudio.mp4 + out/sfx.json
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'out');
const FPS = 30;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };

function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p)) { rsp.writeHead(404); return rsp.end(); }
      rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(rsp);
    }).listen(0, () => res(srv));
  });
}

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e));
  await page.goto(`http://127.0.0.1:${port}/src/index.html`);
  await page.evaluate(() => boot());
  return page;
}

async function grab(page, t, type = 'image/jpeg') {
  const b64 = await page.evaluate(([t, type]) => { render(t); return document.getElementById('c').toDataURL(type, 0.96).split(',')[1]; }, [t, type]);
  return Buffer.from(b64, 'base64');
}

async function main() {
  const [mode, ...args] = process.argv.slice(2);
  const srv = await serve();
  const port = srv.address().port;
  const browser = await chromium.launch();
  fs.mkdirSync(OUT, { recursive: true });
  try {
    if (mode === 'stills') {
      const dir = path.join(OUT, 'stills'); fs.mkdirSync(dir, { recursive: true });
      const page = await openPage(browser, port);
      for (const a of args) fs.writeFileSync(path.join(dir, `t_${a}.png`), await grab(page, parseFloat(a), 'image/png'));
    } else if (mode === 'video') {
      const workers = parseInt(args[0] || '4', 10);
      const probe = await openPage(browser, port);
      const { dur, sfx } = await probe.evaluate(() => ({ dur: DURATION, sfx: SFX }));
      fs.writeFileSync(path.join(OUT, 'sfx.json'), JSON.stringify(sfx, null, 1));
      await probe.close();
      const total = Math.round(dur * FPS);
      const per = Math.ceil(total / workers);
      const t0 = Date.now();
      await Promise.all([...Array(workers).keys()].map(async w => {
        const a = w * per, b = Math.min(total, a + per);
        const page = await openPage(browser, port);
        const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(OUT, `part${w}.mp4`)], { stdio: ['pipe', 'inherit', 'inherit'] });
        for (let f = a; f < b; f++) {
          const buf = await grab(page, f / FPS);
          if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
          if (w === 0 && (f - a) % 150 === 0) console.log(`worker0 ${f - a}/${b - a}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
        }
        ff.stdin.end();
        await new Promise(r => ff.on('close', r));
      }));
      fs.writeFileSync(path.join(OUT, 'parts.txt'), [...Array(workers).keys()].map(w => `file 'part${w}.mp4'`).join('\n'));
      await new Promise(r => spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(OUT, 'parts.txt'), '-c', 'copy', path.join(OUT, 'video_noaudio.mp4')], { stdio: 'inherit' }).on('close', r));
      console.log('done in', ((Date.now() - t0) / 1000).toFixed(0), 's');
    }
  } finally { await browser.close(); srv.close(); }
}
main().catch(e => { console.error(e); process.exit(1); });
