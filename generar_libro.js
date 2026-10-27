// generar_libro.js — carta-print.html → carta-kume.pdf (A4, 12 págs.)
// Después: python3 generar_libro.py  (maqueta el libro a partir de ese PDF)
// Si Chrome no está en la caché de puppeteer: PUPPETEER_EXECUTABLE_PATH=/ruta/a/chrome
const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.emulateMediaType('print');
  await page.goto('file://' + path.resolve(__dirname, 'carta-print.html'), { waitUntil: 'networkidle0', timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);

  // Comprobación: nada se sale de la página y ninguna foto de relleno queda diminuta
  const avisos = await page.evaluate(() => {
    const mm = 96 / 25.4, out = [];
    document.querySelectorAll('.page.pg').forEach((pg, i) => {
      const box = pg.getBoundingClientRect();
      const limite = box.bottom - parseFloat(getComputedStyle(pg).paddingBottom) + 0.5;
      let fondo = 0;
      pg.querySelectorAll('*').forEach(el => {
        if (el.closest('.pf')) return;
        const r = el.getBoundingClientRect();
        if (r.height > 0) fondo = Math.max(fondo, r.bottom);
      });
      const tag = pg.querySelector('.ph-tag')?.textContent || '';
      if (fondo > limite) out.push(`pág. ${i + 2} (${tag}): se sale ${((fondo - limite) / mm).toFixed(1)} mm`);
      pg.querySelectorAll('.photo, .card-grid.fill .card img').forEach(el => {
        const h = el.getBoundingClientRect().height / mm;
        if (h < 18) out.push(`pág. ${i + 2} (${tag}): foto de solo ${h.toFixed(1)} mm de alto`);
      });
    });
    return out;
  });
  avisos.forEach(a => console.warn('AVISO', a));

  await page.pdf({
    path: path.resolve(__dirname, 'carta-kume.pdf'),
    preferCSSPageSize: true,
    printBackground: true,
  });
  await browser.close();
  console.log('OK carta-kume.pdf' + (avisos.length ? ` (${avisos.length} avisos)` : ''));
})();
