// node render.mjs  -> ../NyayaSetu-System-Architecture-Report.pdf   (needs playwright-core and a Chromium; set CHROME=/path/to/chrome)
import { chromium } from 'playwright-core';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const chrome = process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const browser = await chromium.launch({ executablePath: chrome, args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.goto('file://' + path.join(here, 'report.html'), { waitUntil: 'networkidle' });
await page.emulateMedia({ media: 'print' });
await page.pdf({
  path: path.join(here, '..', 'NyayaSetu-System-Architecture-Report.pdf'),
  format: 'A4', printBackground: true, displayHeaderFooter: true,
  margin: { top: '20mm', bottom: '20mm', left: '17mm', right: '17mm' },
  headerTemplate: '<span></span>',
  footerTemplate: '<div style="font-family:Inter,sans-serif;font-size:7.5px;width:100%;padding:0 17mm;display:flex;justify-content:space-between;color:#7a859c"><span>NyayaSetu · System Architecture &amp; Interview Guide</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
});
await browser.close();
