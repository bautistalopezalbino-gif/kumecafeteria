#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepara el vaso de matcha para el post: limpia el fondo a blanco puro,
recorta y lo deja tumbado (volcado) con canal alfa.

Entrada:  Kume menus/images/cafe-matcha-latte.png
Salida:   assets/vaso-volcado.png
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

BASE = Path(__file__).resolve().parent
SRC = BASE.parent.parent / "Kume menus" / "images" / "cafe-matcha-latte.png"
OUT = BASE / "assets" / "vaso-volcado.png"

WHITE_POINT = 231.0   # todo lo mas claro que esto pasa a blanco puro
ANGLE = 118           # grados antihorario: deja el vaso tumbado boca abajo-izq


def main():
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(np.float32)

    # 1. Normaliza el fondo gris del estudio a blanco puro
    a = np.clip(a * (255.0 / WHITE_POINT), 0, 255)

    # 2. Alfa a partir de la luminancia: el blanco desaparece, el vaso queda
    lum = a.max(axis=2)
    alpha = np.clip((252.0 - lum) / 14.0, 0, 1) ** 0.85
    rgba = np.dstack([a, alpha * 255.0]).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA")

    # 3. Recorte ajustado al vaso
    bbox = im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    im = im.crop(bbox)

    # 4. Vuelca el vaso
    im = im.rotate(ANGLE, resample=Image.BICUBIC, expand=True)
    im = im.crop(im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox())

    # 5. Suaviza el borde del recorte
    a = np.asarray(im).astype(np.float32)
    edge = Image.fromarray(a[:, :, 3].astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.6))
    a[:, :, 3] = np.asarray(edge, dtype=np.float32)
    im = Image.fromarray(a.astype(np.uint8), "RGBA")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT)
    print("OK", OUT, im.size)


if __name__ == "__main__":
    main()
