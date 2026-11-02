// node render.mjs <out.pdf>   -- prints report.html to PDF with the Chrome / Edge installed on this machine.
// Needs `npm install` in this folder (playwright-core only; no browser download). Set CHROME=<path to chrome/msedge> to override.
import { chromium } from 'playwright-core';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const out = process.argv[2];

async function launch() {
  const attempts = [];
  if (process.env.CHROME) attempts.push({ executablePath: process.env.CHROME });
  for (const p of ['/opt/pw-browsers/chromium-1194/chrome-linux/chrome']) if (fs.existsSync(p)) attempts.push({ executablePath: p });
  attempts.push({ channel: 'chrome' }, { channel: 'msedge' });   // installed Google Chrome, then Microsoft Edge (present on every Windows 10/11)
  let last;
  for (const a of attempts) {
    try { return await chromium.launch({ ...a, args: ['--no-sandbox'] }); } catch (e) { last = e; }
  }
  throw new Error('No Chrome/Edge found. Install Google Chrome or set CHROME to the browser path.\n' + last);
}

const browser = await launch();
const page = await browser.newPage();
await page.goto('file://' + path.join(here, 'report.html').replace(/\\/g, '/').replace(/^([A-Za-z]):/, '/$1:'), { waitUntil: 'networkidle' });
await page.emulateMedia({ media: 'print' });
await page.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
await browser.close();
