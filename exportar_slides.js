// exportar_slides.js — captura cada slide de Desayunos Küme.html como PNG
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const HTML_PATH = path.resolve(__dirname, 'Kume menus', 'Desayunos Küme.html');
const OUT_DIR   = path.resolve(__dirname, 'menus televicion');

(async () => {
  console.log('Abriendo navegador…');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-web-security', '--allow-file-access-from-files'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  const fileURL = 'file:///' + HTML_PATH.replace(/\\/g, '/');
  console.log('Cargando:', fileURL);
  await page.goto(fileURL, { waitUntil: 'networkidle0', timeout: 30000 });

  // Esperar a que deck-stage esté definido y cargado
  await page.waitForFunction(
    () => customElements.get('deck-stage') !== undefined,
    { timeout: 10000 }
  );

  await page.setCacheEnabled(false);

  // Ocultar rail y overlay; noscale = render 1:1 sin transform
  await page.evaluate(() => {
    const stage = document.querySelector('deck-stage');
    stage.setAttribute('no-rail', '');
    stage.setAttribute('noscale', '');
    const shadow = stage.shadowRoot;
    if (shadow) {
      const overlay = shadow.querySelector('.overlay');
      if (overlay) overlay.style.display = 'none';
      const rail    = shadow.querySelector('.rail');
      if (rail)    rail.style.display = 'none';
      const resize  = shadow.querySelector('.rail-resize');
      if (resize)  resize.style.display = 'none';
    }
  });

  await new Promise(r => setTimeout(r, 1500)); // QR + fuentes

  // Obtener info de slides desde el DOM
  const slides = await page.evaluate(() => {
    const stage = document.querySelector('deck-stage');
    const sections = Array.from(stage.querySelectorAll('section'));
    return sections.map((s, i) => ({
      index: i,
      label: s.dataset.label || `Slide ${i + 1}`,
    }));
  });

  console.log(`\nTotal slides encontrados: ${slides.length}\n`);

  // Ir a slide 0 por si acaso
  await page.evaluate(() => {
    document.querySelector('deck-stage').goTo(0);
  });
  await new Promise(r => setTimeout(r, 600));

  for (let i = 0; i < slides.length; i++) {
    const { label } = slides[i];

    // Navegar al slide i
    await page.evaluate((idx) => {
      document.querySelector('deck-stage').goTo(idx);
    }, i);
    await new Promise(r => setTimeout(r, 800)); // animaciones + QR

    // Capturar solo el canvas de deck-stage (inner div escalado a 1920×1080)
    const clip = { x: 0, y: 0, width: 1920, height: 1080 };

    const num = String(i + 1).padStart(2, '0');
    const safeName = label.replace(/[<>:"/\\|?*]/g, '');
    const filename = `${num} - ${safeName}.png`;
    const outPath  = path.join(OUT_DIR, filename);

    await page.screenshot({ path: outPath, clip, type: 'png' });
    console.log(`  ✓ ${filename}`);
  }

  await browser.close();
  console.log(`\nExportación completa → ${OUT_DIR}`);
})();
