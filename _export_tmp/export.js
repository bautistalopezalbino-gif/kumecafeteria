const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const HTML_FILE = 'C:\\Users\\EMILIANO JAVIER LOPE\\Desktop\\Kume cafeteria\\Kume menus\\Desayunos Küme.html';
const OUTPUT_DIR = 'C:\\Users\\EMILIANO JAVIER LOPE\\Desktop\\Kume cafeteria\\menus televicion';
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const SLIDES = [
  'Portada',
  'Desayunos clasicos',
  'Especiales',
  'Cafes especiales',
  'Brunch tortitas',
  'Brunch crepes',
  'Brunch gofres',
  'Smoothies',
  'Milkshakes',
  'Merienda',
  'Tardeo',
];

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-web-security',
      '--allow-file-access-from-files',
      '--window-size=1920,1080',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  const fileUrl = 'file:///' + HTML_FILE.replace(/\\/g, '/').replace(/ü/g, '%C3%BC').replace(/ /g, '%20');

  console.log('Cargando presentacion...');
  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

  // Hide the thumbnail rail
  await page.evaluate(() => {
    const stage = document.querySelector('deck-stage');
    if (stage) stage.setAttribute('no-rail', '');
  });

  // Wait for fonts to load
  await page.waitForFunction(() => {
    const stage = document.querySelector('deck-stage');
    return stage && !stage.hasAttribute('data-fonts-pending');
  }, { timeout: 5000 }).catch(() => {});

  // Hide navigation overlay and rail chrome
  await page.evaluate(() => {
    const stage = document.querySelector('deck-stage');
    if (stage && stage.shadowRoot) {
      stage.shadowRoot.querySelectorAll('.overlay, .rail, .rail-resize').forEach(el => {
        el.style.display = 'none';
      });
    }
  });

  // Wait for images
  await new Promise(r => setTimeout(r, 1500));

  const total = await page.evaluate(() => {
    const stage = document.querySelector('deck-stage');
    return stage ? stage.length : 0;
  });
  console.log(`Diapositivas detectadas: ${total}`);

  for (let i = 0; i < SLIDES.length; i++) {
    console.log(`Capturando diapositiva ${i + 1}: ${SLIDES[i]} ...`);

    // Navigate to the slide using the public API
    await page.evaluate((idx) => {
      const stage = document.querySelector('deck-stage');
      if (stage) stage.goTo(idx);
    }, i);

    // Wait for the slide to become active
    await page.waitForFunction((idx) => {
      const sections = document.querySelectorAll('deck-stage > section');
      const target = sections[idx];
      return target && target.hasAttribute('data-deck-active');
    }, { timeout: 3000 }, i).catch(() => {});

    // Short wait for any CSS transitions
    await new Promise(r => setTimeout(r, 400));

    const num = String(i + 1).padStart(2, '0');
    const filename = `${num} - ${SLIDES[i]}.png`;
    const outputPath = path.join(OUTPUT_DIR, filename);

    await page.screenshot({
      path: outputPath,
      type: 'png',
      clip: { x: 0, y: 0, width: 1920, height: 1080 },
    });

    console.log(`  -> Guardado: ${filename}`);
  }

  await browser.close();
  console.log('\nExportacion completada. Archivos en:');
  console.log(OUTPUT_DIR);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
