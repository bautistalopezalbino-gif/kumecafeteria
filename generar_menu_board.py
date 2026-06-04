#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KÜME Café — Menú Digital estilo tablero (McDonald's / BK)
Formato 16:9 | 297×167 mm
Páginas: portada + desayunos normales (5) + desayunos especiales (3)
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import rawpy
from rembg import remove
from PIL import Image, ImageFilter
from fpdf import FPDF

BASE     = Path(r"C:\Users\EMILIANO JAVIER LOPE\Desktop\Kume cafeteria")
NEF_DIR  = BASE / "fotos" / "menus desayunos"
JPG_DIR  = NEF_DIR / "jpg"
PNG_DIR  = NEF_DIR / "png_nobg"
PDF_PATH = BASE / "Kume_Menu_Board.pdf"
FONTS    = Path(r"C:\Windows\Fonts")
PREVIEW  = BASE / "preview_board"

PW, PH = 297, 167   # mm — 16:9

# ── Paleta ─────────────────────────────────────────────────────────
BG       = (13, 22, 17)       # negro-verde profundo
HDR_NRM  = (46, 84, 56)       # verde KÜME — normales
HDR_SPC  = (115, 74, 20)      # ámbar oscuro — especiales
GOLD     = (200, 160, 90)     # dorado precios
WHITE_W  = (248, 244, 238)    # blanco cálido
MUTED    = (138, 126, 102)    # gris cálido
DIV      = (32, 56, 40)       # divisor columnas

# Franja de categoría
HEADER_H = 34    # mm
# Zona foto: y = HEADER_H → HEADER_H + PHOTO_H
PHOTO_H  = 82    # mm
TEXT_Y   = HEADER_H + PHOTO_H   # = 116 mm — inicio texto

# ── Menú ───────────────────────────────────────────────────────────
NORMAL_ITEMS = [
    {
        "photo": PNG_DIR / "DSC_0002.png",
        "name1": "Café + Croissant",
        "name2": "",
        "price": "3€",
        "note":  "+ zumo 1€",
    },
    {
        "photo": PNG_DIR / "DSC_0015.png",
        "name1": "Café + Tostada",
        "name2": "Tomate y Aceite",
        "price": "3€",
        "note":  "+ zumo 1€",
    },
    {
        "photo": PNG_DIR / "DSC_0017.png",
        "name1": "Café + Tostada",
        "name2": "Tomate y Jamón Serrano",
        "price": "3€",
        "note":  "+ zumo 1€",
    },
    {
        "photo": PNG_DIR / "DSC_0021.png",
        "name1": "Café + Tostada",
        "name2": "Mantequilla y Mermelada",
        "price": "3€",
        "note":  "+ zumo 1€",
    },
    {
        "photo": PNG_DIR / "DSC_0013.png",
        "name1": "Café + Dos Medialunas",
        "name2": "",
        "price": "3€",
        "note":  "+ zumo 1€",
    },
]

SPECIAL_ITEMS = [
    {
        "photo": PNG_DIR / "DSC_0034.png",
        "name1": "Tostada de Salmón,",
        "name2": "Aguacate y Queso",
        "price": "5,50€",
        "note":  "café + zumo incluidos",
    },
    {
        "photo": PNG_DIR / "DSC_0031.png",
        "name1": "Tostada de Huevo,",
        "name2": "Guacamole y Tomate",
        "price": "5€",
        "note":  "café + zumo incluidos",
    },
    {
        "photo": PNG_DIR / "DSC_0035.png",
        "name1": "Desayuno Completo",
        "name2": "Huevos, Bacon o Guacamole",
        "price": "5,50€",
        "note":  "café + zumo incluidos",
    },
]


# ── Procesado de imágenes ───────────────────────────────────────────

def nef_to_jpg(nef_dir, jpg_dir):
    jpg_dir.mkdir(parents=True, exist_ok=True)
    nefs = sorted(nef_dir.glob("*.NEF")) + sorted(nef_dir.glob("*.nef"))
    new = 0
    for nef in nefs:
        jpg = jpg_dir / (nef.stem + ".jpg")
        if jpg.exists():
            continue
        print(f"  Convirtiendo {nef.name}...")
        with rawpy.imread(str(nef)) as raw:
            rgb = raw.postprocess(use_camera_wb=True, output_bps=8, no_auto_bright=False)
        Image.fromarray(rgb).save(str(jpg), "JPEG", quality=95)
        new += 1
    print(f"  JPGs: {new} nuevos, {len(nefs) - new} ya existian.")
    return sorted(jpg_dir.glob("*.jpg"))


def add_drop_shadow(img_rgba, offset=(20, 20), blur=24, opacity=110):
    pad = blur * 2
    cw = img_rgba.width  + abs(offset[0]) + pad
    ch = img_rgba.height + abs(offset[1]) + pad
    ox = pad + max(0, -offset[0])
    oy = pad + max(0, -offset[1])
    sx, sy = ox + offset[0], oy + offset[1]
    alpha_mask = img_rgba.split()[3].point(lambda p: min(p, opacity))
    shadow_src = Image.new("RGBA", img_rgba.size, (10, 5, 2, 0))
    shadow_src.putalpha(alpha_mask)
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    canvas.paste(shadow_src, (sx, sy), shadow_src)
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(img_rgba, (ox, oy), img_rgba)
    return canvas


def remove_backgrounds(jpg_files):
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    skip = 0
    for jpg in jpg_files:
        png = PNG_DIR / (jpg.stem + ".png")
        if png.exists():
            skip += 1
            continue
        print(f"  Removiendo fondo: {jpg.name}...")
        img = Image.open(str(jpg))
        result = remove(img).convert("RGBA")
        alpha = result.split()[3]
        bbox = alpha.getbbox()
        if bbox:
            result = result.crop(bbox)
        result = add_drop_shadow(result)
        result.save(str(png), "PNG")
    print(f"  PNGs: {skip} ya existian, {len(jpg_files) - skip} nuevos.")
    return sorted(PNG_DIR.glob("DSC_*.png"))


# ── PDF ────────────────────────────────────────────────────────────

class MenuPDF(FPDF):

    def __init__(self):
        super().__init__(orientation="L", unit="mm", format=(PH, PW))
        self.set_auto_page_break(False)
        self.add_font("Georgia", "",  str(FONTS / "georgia.ttf"),  uni=True)
        self.add_font("Georgia", "B", str(FONTS / "georgiab.ttf"), uni=True)
        self.add_font("Georgia", "I", str(FONTS / "georgiai.ttf"), uni=True)
        self.add_font("Segoe",   "",  str(FONTS / "segoeui.ttf"),  uni=True)
        self.add_font("Segoe",   "B", str(FONTS / "segoeuib.ttf"), uni=True)

    # ── helpers ───────────────────────────────────────────────────

    def _fill(self, color, x, y, w, h):
        self.set_fill_color(*color)
        self.rect(x, y, w, h, "F")

    def _place_photo(self, png_path, col_x, col_w):
        """Coloca la foto flotando (RGBA) centrada en la zona de foto."""
        if not png_path.exists():
            print(f"  AVISO: foto no encontrada: {png_path.name}")
            return
        img = Image.open(str(png_path)).convert("RGBA")
        alpha = img.split()[3]
        bbox = alpha.getbbox()
        if bbox:
            img = img.crop(bbox)
        iw, ih = img.size
        max_w = col_w - 10     # 5 mm padding cada lado
        max_h = PHOTO_H - 6   # 3 mm padding arriba/abajo
        scale = min(max_w / iw, max_h / ih)
        disp_w = iw * scale
        disp_h = ih * scale
        x = col_x + (col_w - disp_w) / 2
        y = HEADER_H + (PHOTO_H - disp_h) / 2
        tmp = PNG_DIR / f"_tmp_{png_path.stem}.png"
        img.save(str(tmp), "PNG")
        self.image(str(tmp), x=x, y=y, w=disp_w, h=disp_h)
        tmp.unlink(missing_ok=True)

    def _draw_col_text(self, cx, cw, item, name_pt, price_pt, note_pt):
        """Renderiza nombre, precio y nota centrados en la columna."""
        lh_name  = name_pt  * 0.352 + 2.0
        lh_price = price_pt * 0.352 + 2.5
        lh_note  = note_pt  * 0.352 + 1.5

        # — Nombre (1 ó 2 líneas) ——————————————————————————
        self.set_font("Segoe", "B", name_pt)
        self.set_text_color(*WHITE_W)
        self.set_xy(cx, TEXT_Y + 2)
        self.cell(cw, lh_name, item["name1"], align="C")
        if item["name2"]:
            self.set_xy(cx, TEXT_Y + 2 + lh_name + 1.2)
            self.cell(cw, lh_name, item["name2"], align="C")

        # — Precio (anclado desde posición fija) ———————————
        self.set_font("Georgia", "B", price_pt)
        self.set_text_color(*GOLD)
        self.set_xy(cx, 139)
        self.cell(cw, lh_price, item["price"], align="C")

        # — Nota ———————————————————————————————————————————
        self.set_font("Segoe", "", note_pt)
        self.set_text_color(*MUTED)
        self.set_xy(cx, 159)
        self.cell(cw, lh_note, item["note"], align="C")

    def _draw_header(self, title, subtitle, hdr_color):
        """Franja de categoría en la parte superior."""
        self._fill(hdr_color, 0, 0, PW, HEADER_H)

        # Línea dorada inferior del header
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(0, HEADER_H, PW, HEADER_H)

        # Título
        self.set_font("Georgia", "B", 24)
        self.set_text_color(*WHITE_W)
        self.set_xy(16, 7)
        self.cell(0, 0, title)

        # Subtítulo
        self.set_font("Segoe", "", 9.5)
        self.set_text_color(235, 220, 195)
        self.set_xy(16, 21)
        self.cell(0, 0, subtitle)

        # KÜME (derecha del header)
        self.set_font("Georgia", "B", 16)
        self.set_text_color(*WHITE_W)
        self.set_xy(PW - 72, 7)
        self.cell(64, 0, "KÜME", align="R")

        self.set_font("Segoe", "", 9)
        self.set_text_color(*MUTED)
        self.set_xy(PW - 72, 20)
        self.cell(64, 0, "café · Benimaclet", align="R")

    # ── páginas ───────────────────────────────────────────────────

    def page_cover(self):
        self.add_page()
        self._fill(BG, 0, 0, PW, PH)

        # Franja verde inferior
        self._fill(HDR_NRM, 0, PH - 18, PW, 18)

        # KÜME
        self.set_font("Georgia", "B", 78)
        self.set_text_color(*GOLD)
        self.set_xy(0, PH / 2 - 48)
        self.cell(PW, 0, "KÜME", align="C")

        # Línea dorada
        self.set_draw_color(*GOLD)
        self.set_line_width(0.6)
        self.line(PW / 2 - 55, PH / 2 - 8, PW / 2 + 55, PH / 2 - 8)

        # café
        self.set_font("Georgia", "I", 22)
        self.set_text_color(*WHITE_W)
        self.set_xy(0, PH / 2 - 2)
        self.cell(PW, 0, "café", align="C")

        # Ciudad
        self.set_font("Segoe", "", 11)
        self.set_text_color(*MUTED)
        self.set_xy(0, PH / 2 + 18)
        self.cell(PW, 0, "Benimaclet  ·  Valencia", align="C")

        # Texto franja inferior
        self.set_font("Segoe", "", 10)
        self.set_text_color(*WHITE_W)
        self.set_xy(0, PH - 14)
        self.cell(PW, 0, "CARTA DE DESAYUNOS", align="C")

    def page_normal(self):
        self.add_page()
        self._fill(BG, 0, 0, PW, PH)
        self._draw_header(
            "DESAYUNOS DEL DÍA",
            "Café cortado o con leche incluido  ·  Añade zumo natural por solo 1€",
            HDR_NRM,
        )
        n = len(NORMAL_ITEMS)
        col_w = PW / n

        # Divisores de columna
        self.set_draw_color(*DIV)
        self.set_line_width(0.25)
        for i in range(1, n):
            cx = i * col_w
            self.line(cx, HEADER_H + 6, cx, PH - 5)

        for i, item in enumerate(NORMAL_ITEMS):
            cx = i * col_w
            self._place_photo(item["photo"], cx, col_w)
            self._draw_col_text(cx, col_w, item, name_pt=8.5, price_pt=22, note_pt=8)

    def page_special(self):
        self.add_page()
        self._fill(BG, 0, 0, PW, PH)
        self._draw_header(
            "DESAYUNOS ESPECIALES",
            "Con café y zumo natural de naranja incluidos  ·  El mejor desayuno del día",
            HDR_SPC,
        )
        n = len(SPECIAL_ITEMS)
        col_w = PW / n

        self.set_draw_color(*DIV)
        self.set_line_width(0.25)
        for i in range(1, n):
            cx = i * col_w
            self.line(cx, HEADER_H + 6, cx, PH - 5)

        for i, item in enumerate(SPECIAL_ITEMS):
            cx = i * col_w
            self._place_photo(item["photo"], cx, col_w)
            self._draw_col_text(cx, col_w, item, name_pt=10.5, price_pt=28, note_pt=8.5)


# ── Previews ────────────────────────────────────────────────────────

def generate_previews(pdf_path, preview_dir):
    try:
        import fitz
        preview_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(str(pdf_path))
        paths = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            out = preview_dir / f"slide_{i+1:02d}.png"
            pix.save(str(out))
            paths.append(out)
            print(f"  Preview: {out.name}")
        doc.close()
        return paths
    except ImportError:
        print("  PyMuPDF no disponible — instala con: pip install pymupdf")
        return []


# ── Main ────────────────────────────────────────────────────────────

def main():
    print("=== KÜME Menu Board Generator ===")

    print("\n[1/3] Convirtiendo NEFs a JPG...")
    jpg_files = nef_to_jpg(NEF_DIR, JPG_DIR)

    print("\n[2/3] Removiendo fondos (rembg)...")
    remove_backgrounds(jpg_files)

    print("\n[3/3] Generando PDF...")
    pdf = MenuPDF()
    pdf.page_cover()
    pdf.page_normal()
    pdf.page_special()
    pdf.output(str(PDF_PATH))

    size_mb = PDF_PATH.stat().st_size / 1e6
    print(f"\n  PDF guardado: {PDF_PATH}")
    print(f"  Tamaño: {size_mb:.1f} MB")

    print("\n[+] Generando previews...")
    generate_previews(PDF_PATH, PREVIEW)

    print("\nListo!")


if __name__ == "__main__":
    main()
