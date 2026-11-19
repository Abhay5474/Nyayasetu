// node render_svgs.mjs <svgs.html> <outdir>  : screenshots every <svg> (id s0, s1, ...) to PNG at 3x
import { chromium } from 'playwright-core';
import fs from 'node:fs';
const [,, html, outdir] = process.argv;
async function launch() {
  const tries = [];
  if (process.env.CHROME) tries.push({ executablePath: process.env.CHROME });
  for (const p of ['/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome']) if (fs.existsSync(p)) tries.push({ executablePath: p });
  tries.push({ channel: 'chrome' }, { channel: 'msedge' });
  let last; for (const t of tries) { try { return await chromium.launch({ ...t, args: ['--no-sandbox'] }); } catch (e) { last = e; } }
  throw last;
}
const b = await launch();
const p = await b.newPage({ viewport: { width: 900, height: 900 }, deviceScaleFactor: 3 });
await p.goto('file://' + html.replace(/\\/g, '/').replace(/^([A-Za-z]):/, '/$1:'));
const n = await p.locator('svg.fig').count();
for (let i = 0; i < n; i++) await p.locator('svg.fig').nth(i).screenshot({ path: `${outdir}/svg_${i}.png` });
await b.close();
console.log(n + ' svgs');
