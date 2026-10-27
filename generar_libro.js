// generar_libro.js — carta-print.html → carta-kume.pdf (A4, 11 págs.)
// Después: python3 generar_libro.py  (maqueta el libro a partir de ese PDF)
const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(__dirname, 'carta-print.html'), { waitUntil: 'networkidle0', timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: path.resolve(__dirname, 'carta-kume.pdf'),
    preferCSSPageSize: true,
    printBackground: true,
  });
  await browser.close();
  console.log('OK carta-kume.pdf');
})();
