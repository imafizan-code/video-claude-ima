// Renders scene.html frame by frame: node render.js <scene.html> <timeline.json> <outDir> <fps> <seconds> [onlyT,...]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [html, tlFile, outDir, fps, secs, only] = process.argv.slice(2);
  const timeline = JSON.parse(fs.readFileSync(tlFile, 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 }, deviceScaleFactor: 1.5 });
  await page.goto('file://' + path.resolve(html));
  await page.evaluate(tl => init(tl), timeline);
  await page.evaluate(() => document.fonts.ready);

  const times = only
    ? only.split(',').map(Number)
    : Array.from({ length: Math.ceil(+secs * +fps) }, (_, i) => i / +fps);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => seek(t), times[i]);
    const name = only ? `t${times[i].toFixed(1)}.jpg` : String(i).padStart(5, '0') + '.jpg';
    await page.screenshot({ path: path.join(outDir, name), type: 'jpeg', quality: 90 });
    if (!only && i % 300 === 0) console.log(`frame ${i}/${times.length}`);
  }
  await browser.close();
})();
