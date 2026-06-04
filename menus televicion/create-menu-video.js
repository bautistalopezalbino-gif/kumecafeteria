const { execFileSync } = require('child_process');
const fs   = require('fs');
const path = require('path');

const dir    = path.resolve(__dirname);
const FADE   = 0.8;   // segundos de cross-fade entre diapositivas
const HOLD   = 10;    // segundos que se muestra cada diapositiva
const W      = 1920;
const H      = 1080;
const OUT    = path.join(dir, 'Menu Küme.mp4');

// ── 1. Recoger los PNGs numerados, ordenados ──────────────────────────────────
const slides = fs.readdirSync(dir)
  .filter(f => /^\d{2} - .+\.png$/.test(f))
  .sort();

if (slides.length === 0) {
  console.error('No se encontraron diapositivas (01 - *.png)');
  process.exit(1);
}

console.log(`▸ ${slides.length} diapositivas encontradas:`);
slides.forEach((f, i) => console.log(`   ${String(i + 1).padStart(2, '0')}. ${f}`));

// ── 2. Construir argumentos de FFmpeg ─────────────────────────────────────────
//   Cada imagen se carga con -loop 1 -t HOLD
//   luego encadenamos con xfade (fade/dissolve)
const args = [];

for (const f of slides) {
  args.push('-loop', '1', '-t', String(HOLD), '-i', path.join(dir, f));
}

// filter_complex: escalar cada input a 1920x1080 y encadenar con xfade
let fc = '';
const n = slides.length;

// Primero escalar todos los inputs
for (let i = 0; i < n; i++) {
  fc += `[${i}:v]scale=${W}:${H}:flags=lanczos,format=yuv420p[s${i}];`;
}

// Encadenar con xfade
// offset = i * (HOLD - FADE)  para cada transición i (0-indexed por par)
if (n === 1) {
  fc += `[s0]copy[vout]`;
} else {
  // primera transición: s0 + s1 → x0
  fc += `[s0][s1]xfade=transition=fade:duration=${FADE}:offset=${HOLD - FADE}[x0];`;
  for (let i = 2; i < n; i++) {
    const offset = i * (HOLD - FADE);
    const prev   = i === 2 ? 'x0' : `x${i - 2}`;
    const cur    = i < n - 1 ? `x${i - 1}` : 'vout';
    fc += `[${prev}][s${i}]xfade=transition=fade:duration=${FADE}:offset=${offset.toFixed(3)}[${cur}];`;
  }
  // Si solo hay 2 slides, renombrar x0 → vout
  if (n === 2) {
    fc = fc.replace('[x0]', '[vout]');
  }
}

args.push(
  '-filter_complex', fc,
  '-map', '[vout]',
  '-c:v', 'libx264',
  '-crf', '18',
  '-r', '30',
  '-pix_fmt', 'yuv420p',
  '-movflags', '+faststart',
  '-y',
  OUT
);

// ── 3. Ejecutar FFmpeg ────────────────────────────────────────────────────────
const total  = slides.length * HOLD - (slides.length - 1) * FADE;
console.log(`\n▸ Generando vídeo: ${total.toFixed(1)}s · ${W}x${H} · cross-fade ${FADE}s`);
console.log(`  Destino: ${OUT}\n`);

try {
  execFileSync('ffmpeg', args, { stdio: 'inherit' });
  console.log(`\n✓ Vídeo creado: Menu Küme.mp4`);
} catch (e) {
  console.error('Error al ejecutar FFmpeg:', e.message);
  process.exit(1);
}
