#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from PIL import Image

BASE     = Path(r"C:\Users\EMILIANO JAVIER LOPE\Desktop\Kume cafeteria")
DESAYUNO = BASE / "fotos" / "menus desayunos"

SOURCES = [
    (DESAYUNO / "png_enhanced",  DESAYUNO / "jpg_enhanced"),
    (DESAYUNO / "fotos estudio", DESAYUNO / "fotos estudio" / "jpg"),
]

BG = (255, 255, 255)   # blanco
QUALITY = 95


def png_to_jpg(src: Path, dst: Path):
    img = Image.open(src)
    if img.mode in ("RGBA", "LA", "P"):
        base = Image.new("RGB", img.size, BG)
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):
            base.paste(img, mask=img.split()[-1])
        else:
            base.paste(img)
        img = base
    else:
        img = img.convert("RGB")
    img.save(str(dst), "JPEG", quality=QUALITY, optimize=True)
    kb = dst.stat().st_size // 1024
    print(f"  OK  {src.name}  →  {dst.name}  ({kb} KB)")


def main():
    print("=== Conversión PNG → JPG ===\n")
    total = 0
    for src_dir, dst_dir in SOURCES:
        pngs = sorted(src_dir.glob("*.png"))
        if not pngs:
            print(f"[SKIP] Sin PNGs en {src_dir.name}/")
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        print(f"[{src_dir.name}]  →  {dst_dir.relative_to(DESAYUNO)}/")
        for p in pngs:
            dst = dst_dir / (p.stem + ".jpg")
            png_to_jpg(p, dst)
            total += 1
        print()
    print(f"=== {total} imágenes convertidas ===")


if __name__ == "__main__":
    main()
