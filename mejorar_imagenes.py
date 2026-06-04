#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KÜME Café — Enhancement de imágenes de producto
Pipeline: noise reduction → white balance → CLAHE → saturation → unsharp mask
Input:  fotos/menus desayunos/png_nobg/DSC_XXXX.png  (RGBA, canal alpha preservado)
Output: fotos/menus desayunos/png_enhanced/DSC_XXXX.png (RGBA mejorada)
"""

import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import numpy as np
from PIL import Image

BASE    = Path(r"C:\Users\EMILIANO JAVIER LOPE\Desktop\Kume cafeteria")
PNG_DIR = BASE / "fotos" / "menus desayunos" / "png_nobg"
OUT_DIR = BASE / "fotos" / "menus desayunos" / "png_enhanced"

MENU_FILES = [
    "DSC_0002", "DSC_0013", "DSC_0015", "DSC_0017",
    "DSC_0021", "DSC_0031", "DSC_0034", "DSC_0035",
]

# ── Parámetros de enhancement ──────────────────────────────────────
BILATERAL_SIGMA_COLOR   = 0.05
BILATERAL_SIGMA_SPATIAL = 3
WB_BLEND                = 0.70   # 70% corrección — preserva calidez de luz café
CLAHE_CLIP              = 0.02
SAT_FACTOR              = 1.12
SHARP_RADIUS            = 1.8
SHARP_AMOUNT            = 1.0


def check_dependencies():
    missing = []
    try:
        import skimage
    except ImportError:
        missing.append("scikit-image")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    if missing:
        print(f"ERROR: Faltan librerías: {', '.join(missing)}")
        print("Instala con: pip install scikit-image numpy")
        sys.exit(1)
    print("Dependencias OK")


def load_rgba(path):
    """Carga RGBA PNG, separa canal alpha. Devuelve (rgb float64 [0..1], alpha uint8)."""
    img = Image.open(str(path)).convert("RGBA")
    arr = np.array(img, dtype=np.float64)
    rgb   = arr[:, :, :3] / 255.0
    alpha = np.array(img)[:, :, 3]    # uint8
    return rgb, alpha


def denoise_rgb(rgb):
    """Bilateral: preserva bordes de alimentos. Fallback a wavelet si tarda mucho."""
    from skimage.restoration import denoise_bilateral, denoise_wavelet
    t0 = time.time()
    try:
        result = denoise_bilateral(
            rgb,
            sigma_color=BILATERAL_SIGMA_COLOR,
            sigma_spatial=BILATERAL_SIGMA_SPATIAL,
            channel_axis=-1,
        )
        elapsed = time.time() - t0
        if elapsed > 50:
            print(f"    (bilateral tardó {elapsed:.0f}s — considera wavelet en próximas ejecuciones)")
        return result
    except Exception as e:
        print(f"    Bilateral falló ({e}), usando wavelet...")
        return denoise_wavelet(rgb, method="BayesShrink", mode="soft", channel_axis=-1)


def white_balance_gray_world(rgb, blend=WB_BLEND):
    """Gray world correction mezclada con original para preservar calidez."""
    r_mean = rgb[:, :, 0].mean()
    g_mean = rgb[:, :, 1].mean()
    b_mean = rgb[:, :, 2].mean()
    gray   = (r_mean + g_mean + b_mean) / 3.0
    if r_mean < 1e-6 or g_mean < 1e-6 or b_mean < 1e-6:
        return rgb
    corrected = rgb.copy()
    corrected[:, :, 0] = np.clip(rgb[:, :, 0] * (gray / r_mean), 0, 1)
    corrected[:, :, 1] = np.clip(rgb[:, :, 1] * (gray / g_mean), 0, 1)
    corrected[:, :, 2] = np.clip(rgb[:, :, 2] * (gray / b_mean), 0, 1)
    return (1.0 - blend) * rgb + blend * corrected


def clahe_lab(rgb):
    """CLAHE sobre canal L del espacio LAB — mejora contraste sin alterar tono."""
    from skimage.color import rgb2lab, lab2rgb
    from skimage.exposure import equalize_adapthist
    lab = rgb2lab(rgb.astype(np.float64))
    L = lab[:, :, 0] / 100.0                         # normalizar a [0,1]
    L_clahe = equalize_adapthist(L, clip_limit=CLAHE_CLIP)
    lab_new = lab.copy()
    lab_new[:, :, 0] = L_clahe * 100.0
    result = lab2rgb(lab_new)
    return np.clip(result, 0, 1)


def saturation_boost(rgb, factor=SAT_FACTOR):
    """Aumenta saturación en HSV para colores más vivos."""
    from skimage.color import rgb2hsv, hsv2rgb
    hsv = rgb2hsv(rgb)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 1)
    return hsv2rgb(hsv)


def sharpen_unsharp(rgb, radius=SHARP_RADIUS, amount=SHARP_AMOUNT):
    """Unsharp mask — por canal (channel_axis=-1 produce resultados incorrectos en skimage 0.26)."""
    from skimage.filters import unsharp_mask
    result = np.stack([
        unsharp_mask(rgb[:, :, c], radius=radius, amount=amount)
        for c in range(3)
    ], axis=-1)
    return np.clip(result, 0, 1)


def save_rgba(rgb_float, alpha_uint8, out_path):
    """Recompone RGB mejorado + alpha original y guarda como PNG RGBA."""
    rgb_uint8 = (rgb_float * 255).clip(0, 255).astype(np.uint8)
    img_rgb = Image.fromarray(rgb_uint8, "RGB")
    img_rgb.putalpha(Image.fromarray(alpha_uint8, "L"))
    img_rgb.save(str(out_path), "PNG", optimize=False)


def enhance_single(src_path, dst_path):
    """Ejecuta el pipeline completo sobre una imagen. Retorna True si procesó."""
    if dst_path.exists():
        print("    [SKIP] ya existe")
        return False
    t0 = time.time()
    print("    Cargando...", end=" ", flush=True)
    rgb, alpha = load_rgba(src_path)

    print("denoise...", end=" ", flush=True)
    rgb = denoise_rgb(rgb)

    print("WB...", end=" ", flush=True)
    rgb = white_balance_gray_world(rgb)

    print("CLAHE...", end=" ", flush=True)
    rgb = clahe_lab(rgb)

    print("sat...", end=" ", flush=True)
    rgb = saturation_boost(rgb)

    print("sharpen...", end=" ", flush=True)
    rgb = sharpen_unsharp(rgb)

    print("guardando...", end=" ", flush=True)
    save_rgba(rgb, alpha, dst_path)

    elapsed = time.time() - t0
    size_kb = dst_path.stat().st_size // 1024
    print(f"OK ({elapsed:.1f}s, {size_kb}KB)")
    return True


def main():
    print("=== KÜME Image Enhancement ===\n")
    check_dependencies()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total = len(MENU_FILES)

    for i, stem in enumerate(MENU_FILES):
        src = PNG_DIR / f"{stem}.png"
        dst = OUT_DIR / f"{stem}.png"
        print(f"[{i+1}/{total}] {stem}.png")
        if not src.exists():
            print(f"    ERROR: no encontrado en {src}")
            continue
        enhance_single(src, dst)

    print(f"\n=== Completado — {total} imágenes procesadas en {OUT_DIR.name}/ ===")


if __name__ == "__main__":
    main()
