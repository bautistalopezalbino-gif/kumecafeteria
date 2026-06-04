#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import rawpy
import numpy as np
from PIL import Image

NEF_DIR = Path(r"C:\Users\EMILIANO JAVIER LOPE\Desktop\Kume cafeteria\fotos\menus desayunos")
OUT_DIR = NEF_DIR / "jpg"
QUALITY = 95

def convert_nef(src: Path, dst: Path):
    with rawpy.imread(str(src)) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=False,
            no_auto_bright=False,
            output_bps=8,
        )
    img = Image.fromarray(rgb)
    img.save(str(dst), "JPEG", quality=QUALITY, optimize=True)
    kb = dst.stat().st_size // 1024
    print(f"  OK  {src.name}  →  {dst.name}  ({kb} KB)")

def main():
    print("=== Conversión NEF → JPG ===\n")
    OUT_DIR.mkdir(exist_ok=True)

    nefs = sorted(NEF_DIR.glob("*.NEF")) + sorted(NEF_DIR.glob("*.nef"))
    if not nefs:
        print("No se encontraron archivos NEF.")
        return

    total, skip, error = 0, 0, 0
    for nef in nefs:
        dst = OUT_DIR / (nef.stem + ".jpg")
        if dst.exists():
            print(f"  [SKIP]  {nef.name}  (ya existe)")
            skip += 1
            continue
        try:
            convert_nef(nef, dst)
            total += 1
        except Exception as e:
            print(f"  [ERROR] {nef.name}: {e}")
            error += 1

    print(f"\n=== Convertidos: {total}  |  Saltados: {skip}  |  Errores: {error} ===")
    print(f"JPGs guardados en: {OUT_DIR}")

if __name__ == "__main__":
    main()
