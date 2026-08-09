/**
 * Renderiza post.html a PNG 1080x1350 (formato vertical de Instagram).
 * Se dibuja a 2x y se reduce con Pillow para bordes limpios.
 */
const path = require('path');
const puppeteer = require(path.join(__dirname, '..', '..', 'node_modules', 'puppeteer'));

const W = 1080, H = 1350, SCALE = 2;

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: process.env.CHROME_BIN || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: SCALE });
  await page.goto('file://' + path.join(__dirname, 'post.html'), { waitUntil: 'networkidle0' });
  await page.evaluateHandle('document.fonts.ready');
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({
    path: path.join(__dirname, 'post-matcha-benimaclet@2x.png'),
    clip: { x: 0, y: 0, width: W, height: H },
  });
  await browser.close();
  console.log('OK render 2x');
})();
