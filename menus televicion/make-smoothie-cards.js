const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const url = require('url');

const dir = path.resolve(__dirname);
const imgRelPath = 'pomelli_photoshoot_image_1_1_0602 (1).png';
const outDir = path.join(dir, 'images', 'drinks');

const smoothies = [
  // Fila 1
  { name: 'Sunny Mango',  ingr: 'Mango, papaya y piña',          col: 0, row: 0 },
  { name: 'Tropical',     ingr: 'Piña, coco y mango',            col: 1, row: 0 },
  { name: 'Dragon Fruit', ingr: 'Pitahaya, fresa y mango',       col: 2, row: 0 },
  // Fila 2 — rojo oscuro → Red Berries, rosa → Red Bliss, amarillo con lima → Piña Colada
  { name: 'Red Berries',  ingr: 'Fresas, frambuesas y açaí',     col: 0, row: 1 },
  { name: 'Red Bliss',    ingr: 'Sandía, fresa y limón',         col: 1, row: 1 },
  { name: 'Piña Colada',  ingr: 'Piña, coco y lima',             col: 2, row: 1 },
  // Fila 3 — amarillo tropical → Caribbean, naranja/amarillo → Vitality, verde → Green Detox
  { name: 'Caribbean',    ingr: 'Mango, maracuyá y lima',        col: 0, row: 2 },
  { name: 'Vitality',     ingr: 'Naranja, zanahoria y cúrcuma',  col: 1, row: 2 },
  { name: 'Green Detox',  ingr: 'Manzana, espinaca y jengibre',  col: 2, row: 2 },
];

function bgPos(col, row) {
  const x = col === 0 ? '0%' : col === 1 ? '50%' : '100%';
  const y = row === 0 ? '0%' : row === 1 ? '50%' : '100%';
  return `${x} ${y}`;
}

function buildHTML(sm) {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,600;1,400&family=Inter:wght@400;600&display=swap" rel="stylesheet"/>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { width: 360px; height: 480px; background: #fff; display: flex; flex-direction: column; overflow: hidden; font-family: 'Inter', sans-serif; }
  .photo {
    width: 360px; height: 340px; flex-shrink: 0;
    background-image: url('${imgRelPath}');
    background-size: 300% 300%;
    background-position: ${bgPos(sm.col, sm.row)};
    background-repeat: no-repeat;
  }
  .info {
    flex: 1;
    background: #fff;
    border-top: 1px solid #e8e4da;
    padding: 18px 22px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .name {
    font-family: 'Noto Serif', serif;
    font-size: 26px;
    font-weight: 600;
    color: #2d4018;
    line-height: 1.15;
  }
  .ingr {
    font-size: 15px;
    color: #4d6230;
    margin-top: 4px;
  }
  .bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 12px;
  }
  .price {
    font-family: 'Noto Serif', serif;
    font-size: 32px;
    font-weight: 600;
    color: #2e3a25;
    line-height: 1;
  }
  .price span { font-size: 0.6em; }
</style>
</head>
<body>
  <div class="photo" id="photo"></div>
  <div class="info">
    <div>
      <p class="name">${sm.name}</p>
      <p class="ingr">${sm.ingr}</p>
    </div>
    <div class="bottom">
      <span></span>
      <span class="price">5<span> €</span></span>
    </div>
  </div>
</body>
</html>`;
}

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  for (const sm of smoothies) {
    // Guardar HTML temporal junto al archivo de imagen (mismo directorio)
    const slug = sm.name.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-');
    const tmpHtml = path.join(dir, `_tmp_${slug}.html`);
    fs.writeFileSync(tmpHtml, buildHTML(sm), 'utf8');

    const page = await browser.newPage();
    await page.setViewport({ width: 360, height: 480 });

    const fileUrl = url.pathToFileURL(tmpHtml).href;
    await page.goto(fileUrl, { waitUntil: 'load', timeout: 30000 });

    // Forzar decode de la imagen de fondo
    await page.evaluate(async () => {
      const div = document.getElementById('photo');
      const style = getComputedStyle(div);
      const bgUrl = style.backgroundImage.match(/url\("?([^")\s]+)"?\)/);
      if (!bgUrl) return;
      const img = new Image();
      img.src = bgUrl[1];
      await new Promise(r => {
        img.onload = r;
        img.onerror = r;
        setTimeout(r, 5000);
      });
      if (img.decode) await img.decode().catch(() => {});
    });

    await new Promise(r => setTimeout(r, 600));

    const outFile = path.join(outDir, `sm-${slug}-card.png`);
    await page.screenshot({ path: outFile, clip: { x: 0, y: 0, width: 360, height: 480 } });
    await page.close();

    fs.unlinkSync(tmpHtml);
    console.log('Guardado:', path.basename(outFile));
  }

  await browser.close();
  console.log('¡Listo!');
})();
