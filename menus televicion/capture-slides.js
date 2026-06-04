const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const url = require('url');

const dir = path.resolve(__dirname);
const htmlFile = path.join(dir, 'Desayunos Küme.html');

async function decodeAllImages(page) {
  await page.evaluate(async () => {
    const imgs = Array.from(document.querySelectorAll('img'));
    await Promise.all(imgs.map(async img => {
      try {
        // Force decode (ensures Chrome renders even deferred images)
        if (img.decode) await img.decode();
      } catch (e) {
        // Reload image if decode failed
        if (img.src) {
          const src = img.src;
          img.src = '';
          img.src = src;
          await new Promise(r => {
            img.addEventListener('load', r, { once: true });
            img.addEventListener('error', r, { once: true });
            setTimeout(r, 5000);
          });
        }
      }
    }));
  });
}

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--font-render-hinting=none',
      '--force-color-profile=srgb'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  const fileUrl = url.pathToFileURL(htmlFile).href;
  console.log('Abriendo:', fileUrl);

  await page.goto(fileUrl, { waitUntil: 'load', timeout: 60000 });

  await page.waitForFunction(
    () => customElements.get('deck-stage') !== undefined,
    { timeout: 15000 }
  );

  // Esperar fuentes y decodificar todas las imágenes
  await new Promise(r => setTimeout(r, 2000));
  await decodeAllImages(page);

  // Ocultar barra lateral del deck-stage
  await page.evaluate(() => {
    const ds = document.querySelector('deck-stage');
    if (!ds || !ds.shadowRoot) return;
    const sr = ds.shadowRoot;
    ['rail', 'rail-resize', 'overlay', 'ctxmenu', 'confirm-backdrop'].forEach(cls => {
      const el = sr.querySelector('.' + cls);
      if (el) el.style.display = 'none';
    });
  });
  await new Promise(r => setTimeout(r, 300));

  // Medir el área real del slide (sección activa) después de ocultar el rail
  const slideClip = await page.evaluate(() => {
    const ds = document.querySelector('deck-stage');
    const section = ds ? ds.querySelector('section') : null;
    if (!section) return { x: 0, y: 0, width: 1920, height: 1080 };
    const r = section.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) };
  });
  console.log('Clip area:', JSON.stringify(slideClip));
  await new Promise(r => setTimeout(r, 500));

  const slides = await page.evaluate(() => {
    const ds = document.querySelector('deck-stage');
    const sections = Array.from(ds.children).filter(el => el.tagName === 'SECTION');
    return sections.map((s, i) => ({
      index: i,
      label: s.getAttribute('data-label') || `Slide ${i + 1}`
    }));
  });

  console.log(`Encontradas ${slides.length} diapositivas`);

  // Eliminar PNGs numerados antiguos
  const oldFiles = fs.readdirSync(dir).filter(f => /^\d{2} - .+\.png$/.test(f));
  for (const f of oldFiles) {
    fs.unlinkSync(path.join(dir, f));
    console.log(`Eliminado: ${f}`);
  }

  // Capturar cada diapositiva
  for (const slide of slides) {
    await page.evaluate((idx) => {
      document.querySelector('deck-stage').goTo(idx);
    }, slide.index);

    await new Promise(r => setTimeout(r, 800));
    await decodeAllImages(page);
    await new Promise(r => setTimeout(r, 400));

    const filename = `${String(slide.index + 1).padStart(2, '0')} - ${slide.label}.png`;
    const filepath = path.join(dir, filename);

    await page.screenshot({
      path: filepath,
      clip: slideClip
    });
    console.log(`Guardado: ${filename}`);
  }

  await browser.close();
  console.log('¡Listo!');
})();
