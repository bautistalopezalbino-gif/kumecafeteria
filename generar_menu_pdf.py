#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KUME Cafe -- Generador de PDF para pantallas (16:9)
Pasos: NEF -> JPG -> PNG transparente con sombra -> PDF presentacion
"""

import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import rawpy
from rembg import remove
from PIL import Image, ImageFilter
from fpdf import FPDF

# =============================================================================
#  CONFIGURACION
# =============================================================================
BASE    = Path(r"C:\Users\EMILIANO JAVIER LOPE\Desktop\Kume cafeteria")
NEF_DIR = BASE / "fotos" / "menus desayunos"
JPG_DIR = NEF_DIR / "jpg"
PNG_DIR = NEF_DIR / "png_nobg"
PDF_PATH = BASE / "Kume_Menu_Desayunos.pdf"
FONTS   = Path(r"C:\Windows\Fonts")

PW, PH = 297, 167   # mm — 16:9

# -- Colores ------------------------------------------------------------------
CREAM      = (252, 249, 248)
CREAM_WARM = (245, 236, 215)
GREEN_DARK = ( 43,  83,  64)
GREEN      = ( 83,  99,  69)
BROWN      = (128,  85,  51)
CHARCOAL   = ( 28,  27,  27)
WHITE      = (255, 255, 255)
MUTED      = (110, 107, 104)
GOLD       = (192, 157, 106)
SAGE_LIGHT = (192, 220, 180)

# =============================================================================
#  CONTENIDO DEL MENU  (con tildes y caracteres correctos)
# =============================================================================
NORMAL_ITEMS = [
    {
        "photo": PNG_DIR / "DSC_0002.png",
        "title": ["Café + Croissant"],
        "desc":  "Café al gusto acompañado de\ncroissant artesanal",
        "price": "3",
        "note":  "Añade zumo de naranja natural  +1€",
    },
    {
        "photo": PNG_DIR / "DSC_0015.png",
        "title": ["Café + Tostada", "Tomate y Aceite"],
        "desc":  "Pan artesanal tostado con tomate\nnatural y aceite de oliva virgen extra",
        "price": "3",
        "note":  "Añade zumo de naranja natural  +1€",
    },
    {
        "photo": PNG_DIR / "DSC_0017.png",
        "title": ["Café + Tostada con", "Tomate y Jamón Serrano"],
        "desc":  "Pan tostado con tomate natural\ny jamón serrano seleccionado",
        "price": "3",
        "note":  "Añade zumo de naranja natural  +1€",
    },
    {
        "photo": PNG_DIR / "DSC_0021.png",
        "title": ["Café + Tostada con", "Mantequilla y Mermelada"],
        "desc":  "Pan tostado con mantequilla\ny mermelada artesanal de temporada",
        "price": "3",
        "note":  "Añade zumo de naranja natural  +1€",
    },
    {
        "photo": PNG_DIR / "DSC_0013.png",
        "title": ["Café + Dos Medialunas"],
        "desc":  "Café al gusto con dos\nmedialunas artesanales",
        "price": "3",
        "note":  "Añade zumo de naranja natural  +1€",
    },
]

SPECIAL_ITEMS = [
    {
        "photo": PNG_DIR / "DSC_0034.png",
        "title": ["Tostada de Salmón,", "Aguacate y Queso"],
        "desc":  "Salmón ahumado, aguacate fresco\ny queso crema sobre pan artesanal",
        "price": "5,50",
        "note":  "Zumo de naranja natural incluido",
    },
    {
        "photo": PNG_DIR / "DSC_0031.png",
        "title": ["Tostada de Huevo,", "Guacamole y Tomate"],
        "desc":  "Huevo, guacamole casero y tomate\nnatural sobre pan artesanal tostado",
        "price": "5",
        "note":  "Zumo de naranja natural incluido",
    },
    {
        "photo": PNG_DIR / "DSC_0035.png",
        "title": ["Desayuno Completo"],
        "desc":  "Tostada o croissant\n+ tortilla francesa o huevos\n+ guacamole o bacon",
        "price": "5,50",
        "note":  "Zumo de naranja natural incluido",
    },
]

# =============================================================================
#  PASO 1: NEF -> JPG
# =============================================================================
def convert_nef():
    JPG_DIR.mkdir(exist_ok=True)
    nefs = sorted(NEF_DIR.glob("*.NEF"))
    out  = []
    print(f"[1/3] Convirtiendo {len(nefs)} archivos NEF a JPG ...")
    for nef in nefs:
        jpg = JPG_DIR / (nef.stem + ".jpg")
        if not jpg.exists():
            try:
                with rawpy.imread(str(nef)) as raw:
                    rgb = raw.postprocess(use_camera_wb=True, output_bps=8)
                img = Image.fromarray(rgb)
                if img.width > 2400:
                    r = 2400 / img.width
                    img = img.resize((2400, int(img.height * r)), Image.LANCZOS)
                img.save(str(jpg), "JPEG", quality=90, optimize=True)
                print(f"    OK  {nef.name}")
            except Exception as e:
                print(f"    ERR {nef.name}: {e}")
                continue
        out.append(jpg)
    print(f"    {len(out)} imagenes JPG listas.\n")
    return out


# =============================================================================
#  PASO 2: Sombra suave sobre RGBA transparente
# =============================================================================
def add_drop_shadow(img_rgba, offset=(20, 20), blur=24, opacity=115):
    """Añade sombra suave al producto. Devuelve imagen RGBA más grande."""
    pad      = blur * 2
    canvas_w = img_rgba.width  + abs(offset[0]) + pad
    canvas_h = img_rgba.height + abs(offset[1]) + pad

    ox = pad + max(0, -offset[0])
    oy = pad + max(0, -offset[1])
    sx = ox + offset[0]
    sy = oy + offset[1]

    alpha_mask = img_rgba.split()[3].point(lambda p: min(p, opacity))
    shadow_src = Image.new("RGBA", img_rgba.size, (15, 10, 5, 0))
    shadow_src.putalpha(alpha_mask)

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.paste(shadow_src, (sx, sy), shadow_src)
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(img_rgba, (ox, oy), img_rgba)
    return canvas


# =============================================================================
#  PASO 2: JPG -> PNG transparente con sombra (rembg)
# =============================================================================
def remove_backgrounds(jpg_files):
    PNG_DIR.mkdir(exist_ok=True)
    out = []
    print(f"[2/3] Eliminando fondos de {len(jpg_files)} imagenes ...")
    for jpg in jpg_files:
        png = PNG_DIR / (jpg.stem + ".png")
        if not png.exists():
            try:
                img    = Image.open(str(jpg))
                result = remove(img).convert("RGBA")

                alpha = result.split()[3]
                bbox  = alpha.getbbox()
                if bbox:
                    result = result.crop(bbox)

                result = add_drop_shadow(result)
                result.save(str(png), "PNG")
                print(f"    OK  {jpg.name} -> {png.name}")
            except Exception as e:
                print(f"    ERR {jpg.name}: {e}")
                png = jpg
        out.append(png)
    print(f"\n    {len(out)} imagenes listas.\n")
    return out


# =============================================================================
#  PASO 3: GENERACION DEL PDF
# =============================================================================

def c(pdf, color):   pdf.set_fill_color(*color)
def tc(pdf, color):  pdf.set_text_color(*color)
def dc(pdf, color):  pdf.set_draw_color(*color)


class MenuPDF(FPDF):

    def setup_fonts(self):
        self.add_font("Serif", style="",  fname=str(FONTS / "georgia.ttf"))
        self.add_font("Serif", style="B", fname=str(FONTS / "georgiab.ttf"))
        self.add_font("Serif", style="I", fname=str(FONTS / "georgiai.ttf"))
        self.add_font("Sans",  style="",  fname=str(FONTS / "segoeui.ttf"))
        self.add_font("Sans",  style="B", fname=str(FONTS / "segoeuib.ttf"))

    # -------------------------------------------------------------------------
    def slide_cover(self):
        self.add_page()
        c(self, GREEN_DARK);  self.rect(0, 0, PW, PH, "F")
        c(self, BROWN);       self.rect(0, 0, PW, 2, "F")
        c(self, BROWN);       self.rect(0, PH - 2, PW, 2, "F")

        tc(self, CREAM)
        self.set_font("Serif", "B", 82)
        self.set_xy(0, 24); self.cell(PW, 0, "KÜME", align="C")

        dc(self, GOLD); self.set_line_width(0.6)
        self.line(PW/2 - 38, 76, PW/2 + 38, 76)

        tc(self, SAGE_LIGHT)
        self.set_font("Serif", "I", 30)
        self.set_xy(0, 79); self.cell(PW, 0, "café", align="C")

        tc(self, (175, 190, 175))
        self.set_font("Sans", "", 11)
        self.set_xy(0, 104); self.cell(PW, 0, "CARTA DE DESAYUNOS", align="C")

        tc(self, (120, 140, 120))
        self.set_font("Sans", "", 8)
        self.set_xy(0, PH - 13); self.cell(PW, 0, "Benimaclet · Valencia", align="C")

    # -------------------------------------------------------------------------
    def slide_section(self, title, subtitle, bg):
        self.add_page()
        c(self, bg);    self.rect(0, 0, PW, PH, "F")
        c(self, BROWN); self.rect(0, 0, PW, 2, "F")
        c(self, BROWN); self.rect(0, PH - 2, PW, 2, "F")

        tc(self, (200, 220, 200))
        self.set_font("Sans", "", 8.5)
        self.set_xy(0, PH/2 - 36); self.cell(PW, 0, "--  SECCIÓN  --", align="C")

        tc(self, WHITE)
        self.set_font("Serif", "B", 52)
        self.set_xy(0, PH/2 - 26); self.cell(PW, 0, title, align="C")

        dc(self, GOLD); self.set_line_width(0.4)
        self.line(PW/2 - 30, PH/2 + 6, PW/2 + 30, PH/2 + 6)

        tc(self, CREAM_WARM)
        self.set_font("Sans", "", 13)
        self.set_xy(0, PH/2 + 11); self.cell(PW, 0, subtitle, align="C")

    # -------------------------------------------------------------------------
    def _place_product(self, png_path, panel_x, panel_w, panel_h):
        """Coloca el PNG transparente centrado en el panel de color."""
        try:
            img = Image.open(str(png_path)).convert("RGBA")
            alpha = img.split()[3]
            bbox  = alpha.getbbox()
            if bbox:
                img = img.crop(bbox)

            iw, ih = img.size
            max_w  = panel_w * 0.88
            max_h  = panel_h * 0.84
            scale  = min(max_w / iw, max_h / ih)

            disp_w = iw * scale
            disp_h = ih * scale
            x = panel_x + (panel_w - disp_w) / 2
            y = (panel_h - disp_h) / 2

            tmp = PNG_DIR / f"_tmp_{png_path.stem}.png"
            img.save(str(tmp), "PNG")
            self.image(str(tmp), x=x, y=y, w=disp_w, h=disp_h)
            tmp.unlink(missing_ok=True)
        except Exception as e:
            print(f"    WARN imagen no colocada ({png_path.name}): {e}")

    # -------------------------------------------------------------------------
    def slide_item(self, item, number, is_special=False):
        self.add_page()

        panel_bg = GREEN_DARK if is_special else GREEN
        accent   = BROWN

        # Panel izquierdo
        photo_w = PW * 0.56
        c(self, panel_bg)
        self.rect(0, 0, photo_w, PH, "F")

        # Borde sutil en el límite foto/texto
        shade = tuple(max(0, v - 22) for v in panel_bg)
        c(self, shade)
        self.rect(photo_w - 4, 0, 4, PH, "F")

        # Producto PNG transparente
        self._place_product(item["photo"], 0, photo_w, PH)

        # Panel derecho
        c(self, CREAM)
        self.rect(photo_w, 0, PW - photo_w, PH, "F")

        # Franja inferior del panel texto
        c(self, accent)
        self.rect(photo_w, PH - 5, PW - photo_w, 5, "F")

        px = photo_w + 12
        pw = PW - photo_w - 16

        # Número de ítem
        num_str = f"0{number}" if number < 10 else str(number)
        tc(self, accent)
        self.set_font("Serif", "B", 12)
        self.set_xy(px, 14); self.cell(pw, 0, num_str)

        # Etiqueta de categoría
        category = "DESAYUNO ESPECIAL" if is_special else "DESAYUNO DEL DÍA"
        tc(self, MUTED)
        self.set_font("Sans", "", 7.5)
        self.set_xy(px, 23); self.cell(pw, 0, category)

        # Línea divisoria
        dc(self, accent); self.set_line_width(0.35)
        self.line(px, 32, px + pw, 32)

        # Título
        tc(self, CHARCOAL)
        lines = item["title"]
        if len(lines) == 1:
            self.set_font("Serif", "B", 24)
            self.set_xy(px, 37); self.cell(pw, 11, lines[0])
            title_end = 49
        else:
            self.set_font("Serif", "B", 20)
            y = 36
            for line in lines:
                self.set_xy(px, y); self.cell(pw, 9, line)
                y += 9
            title_end = y + 1

        # Descripción
        tc(self, MUTED)
        self.set_font("Sans", "", 10)
        self.set_xy(px, title_end + 5)
        self.multi_cell(pw, 5.5, item["desc"])

        # Precio — máximo impacto visual
        tc(self, panel_bg)
        self.set_font("Serif", "B", 48)
        self.set_xy(px, PH - 55)
        self.cell(pw, 0, item["price"] + "€")

        # Nota
        tc(self, MUTED)
        self.set_font("Sans", "", 8.5)
        self.set_xy(px, PH - 28)
        self.multi_cell(pw, 4.8, item["note"])

        # Logo KÜME pequeño
        tc(self, (205, 202, 200))
        self.set_font("Serif", "I", 7)
        self.set_xy(photo_w, PH - 14)
        self.cell(PW - photo_w - 5, 0, "KÜME café", align="R")


# =============================================================================
def generate_pdf():
    print("[3/3] Generando PDF ...")
    pdf = MenuPDF(unit="mm", format=(PW, PH))
    pdf.set_auto_page_break(False)
    pdf.setup_fonts()

    pdf.slide_cover()

    pdf.slide_section("Desayunos del Día", "Café y algo más — desde 3€", GREEN)
    for i, item in enumerate(NORMAL_ITEMS):
        pdf.slide_item(item, i + 1, is_special=False)

    pdf.slide_section("Desayunos Especiales", "Para empezar el día con todo — desde 5€", GREEN_DARK)
    for i, item in enumerate(SPECIAL_ITEMS):
        pdf.slide_item(item, i + 1, is_special=True)

    pdf.output(str(PDF_PATH))
    total = 2 + len(NORMAL_ITEMS) + len(SPECIAL_ITEMS) + 2
    print(f"\nOK PDF generado: {PDF_PATH}")
    print(f"   {total} paginas en total")


# =============================================================================
if __name__ == "__main__":
    jpg_files = convert_nef()
    if not jpg_files:
        print("ERROR: No hay imagenes JPG. Abortando.")
        sys.exit(1)
    remove_backgrounds(jpg_files)
    generate_pdf()
