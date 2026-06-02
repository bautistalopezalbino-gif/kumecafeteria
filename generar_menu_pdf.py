#!/usr/bin/env python3
"""
KÜME Café — Generador de PDF para pantallas (16:9)
Convierte fotos NEF a JPG y genera presentación visual para menús de desayuno.
"""

import os
import sys
import rawpy
from pathlib import Path
from fpdf import FPDF
from PIL import Image

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════
BASE      = Path(r"C:\Users\EMILIANO JAVIER LOPE\Desktop\Kume cafeteria")
NEF_DIR   = BASE / "fotos" / "menus desayunos"
JPG_DIR   = NEF_DIR / "jpg"
PDF_PATH  = BASE / "Kume_Menu_Desayunos.pdf"
WIN_FONTS = Path(r"C:\Windows\Fonts")

PW, PH = 297, 167   # mm — 16:9 landscape

# ── Colores de marca ──────────────────────────────────────────────────────────
CREAM      = (252, 249, 248)
CREAM_WARM = (245, 236, 215)
GREEN_DARK = (43,  83,  64)
GREEN      = (83,  99,  69)
BROWN      = (128, 85,  51)
CHARCOAL   = (28,  27,  27)
WHITE      = (255, 255, 255)
MUTED      = (110, 107, 104)
GOLD       = (192, 157, 106)
SAGE_LIGHT = (192, 220, 180)

# ══════════════════════════════════════════════════════════════════════════════
#  CONTENIDO DEL MENÚ
# ══════════════════════════════════════════════════════════════════════════════
NORMAL_ITEMS = [
    {
        "title":  ["Café + Croissant"],
        "desc":   "Café al gusto acompañado de\ncroissant artesanal recién horneado",
        "price":  "3€",
        "note":   "Añade zumo de naranja natural  +1€",
        "badge":  "CLÁSICO",
    },
    {
        "title":  ["Café + Tostada", "Tomate y Aceite"],
        "desc":   "Pan artesanal tostado con\ntomate natural y aceite de oliva\nvirgen extra",
        "price":  "3€",
        "note":   "Añade zumo de naranja natural  +1€",
        "badge":  "CLÁSICO",
    },
    {
        "title":  ["Café + Tostada con", "Tomate y Jamón Serrano"],
        "desc":   "Pan tostado con tomate natural\ny jamón serrano seleccionado",
        "price":  "3€",
        "note":   "Añade zumo de naranja natural  +1€",
        "badge":  "CLÁSICO",
    },
    {
        "title":  ["Café + Tostada con", "Mantequilla y Mermelada"],
        "desc":   "Pan tostado con mantequilla\ny mermelada artesanal de temporada",
        "price":  "3€",
        "note":   "Añade zumo de naranja natural  +1€",
        "badge":  "CLÁSICO",
    },
    {
        "title":  ["Café + Dos Medialunas"],
        "desc":   "Café al gusto acompañado de\ndos medialunas artesanales",
        "price":  "3€",
        "note":   "Añade zumo de naranja natural  +1€",
        "badge":  "CLÁSICO",
    },
]

SPECIAL_ITEMS = [
    {
        "title":  ["Tostada de Salmón,", "Aguacate y Queso"],
        "desc":   "Salmón ahumado, aguacate fresco\ny queso crema sobre pan artesanal\ntostado",
        "price":  "5,50€",
        "note":   "Zumo de naranja natural incluido",
        "badge":  "ESPECIAL",
    },
    {
        "title":  ["Tostada de Huevo,", "Guacamole y Tomate"],
        "desc":   "Huevo, guacamole casero y tomate\nnatural sobre pan artesanal\ntostado",
        "price":  "5€",
        "note":   "Zumo de naranja natural incluido",
        "badge":  "ESPECIAL",
    },
    {
        "title":  ["Desayuno Completo"],
        "desc":   "Tostada o croissant\n+ tortilla francesa o huevos revueltos\n+ guacamole o bacon",
        "price":  "5,50€",
        "note":   "Zumo de naranja natural incluido",
        "badge":  "ESPECIAL",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  CONVERSIÓN NEF → JPG
# ══════════════════════════════════════════════════════════════════════════════
def convert_nef_to_jpg():
    JPG_DIR.mkdir(exist_ok=True)
    nef_files = sorted(NEF_DIR.glob("*.NEF"))
    jpg_files = []

    if not nef_files:
        print("ERROR: No se encontraron archivos .NEF en", NEF_DIR)
        return []

    print(f"Convirtiendo {len(nef_files)} archivos NEF …")
    for nef in nef_files:
        jpg = JPG_DIR / (nef.stem + ".jpg")
        if not jpg.exists():
            try:
                with rawpy.imread(str(nef)) as raw:
                    rgb = raw.postprocess(
                        use_camera_wb=True,
                        no_auto_bright=False,
                        output_bps=8,
                    )
                img = Image.fromarray(rgb)
                if img.width > 2400:
                    r = 2400 / img.width
                    img = img.resize((2400, int(img.height * r)), Image.LANCZOS)
                img.save(str(jpg), "JPEG", quality=90, optimize=True)
                print(f"  OK  {nef.name}")
            except Exception as exc:
                print(f"  ERR {nef.name}: {exc}")
                continue
        jpg_files.append(jpg)

    print(f"\n{len(jpg_files)} imagenes listas.\n")
    return jpg_files


# ══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════
_tmp_counter = 0

def fill_image(pdf, img_path, x, y, w, h):
    """Coloca imagen recortada para rellenar exactamente el rectángulo."""
    global _tmp_counter
    img = Image.open(str(img_path))
    iw, ih = img.size
    target_ratio = w / h
    img_ratio = iw / ih

    if img_ratio > target_ratio:
        new_w = int(ih * target_ratio)
        left = (iw - new_w) // 2
        img = img.crop((left, 0, left + new_w, ih))
    else:
        new_h = int(iw / target_ratio)
        top = int((ih - new_h) * 0.30)
        img = img.crop((0, top, iw, top + new_h))

    _tmp_counter += 1
    tmp = JPG_DIR / f"_tmp_{_tmp_counter}.jpg"
    img.save(str(tmp), "JPEG", quality=88)
    pdf.image(str(tmp), x=x, y=y, w=w, h=h)
    tmp.unlink(missing_ok=True)


def c(pdf, color):
    pdf.set_fill_color(*color)

def tc(pdf, color):
    pdf.set_text_color(*color)

def dc(pdf, color):
    pdf.set_draw_color(*color)


# ══════════════════════════════════════════════════════════════════════════════
#  CLASE PDF
# ══════════════════════════════════════════════════════════════════════════════
class MenuPDF(FPDF):

    def setup_fonts(self):
        self.add_font("Serif", style="",  fname=str(WIN_FONTS / "georgia.ttf"))
        self.add_font("Serif", style="B", fname=str(WIN_FONTS / "georgiab.ttf"))
        self.add_font("Serif", style="I", fname=str(WIN_FONTS / "georgiai.ttf"))
        self.add_font("Sans",  style="",  fname=str(WIN_FONTS / "segoeui.ttf"))
        self.add_font("Sans",  style="B", fname=str(WIN_FONTS / "segoeuib.ttf"))

    # ── Portada ───────────────────────────────────────────────────────────────
    def slide_cover(self):
        self.add_page()

        # Fondo verde oscuro
        c(self, GREEN_DARK)
        self.rect(0, 0, PW, PH, "F")

        # Franja dorada superior
        c(self, BROWN)
        self.rect(0, 0, PW, 1.8, "F")

        # Franja dorada inferior
        self.rect(0, PH - 1.8, PW, 1.8, "F")

        # Nombre KÜME — grande
        tc(self, CREAM)
        self.set_font("Serif", "B", 80)
        self.set_xy(0, 28)
        self.cell(PW, 0, "KÜME", align="C")

        # Línea decorativa
        dc(self, GOLD)
        self.set_line_width(0.5)
        cx = PW / 2
        self.line(cx - 35, 76, cx + 35, 76)

        # "café"
        tc(self, SAGE_LIGHT)
        self.set_font("Serif", "I", 28)
        self.set_xy(0, 79)
        self.cell(PW, 0, "café", align="C")

        # Subtítulo
        tc(self, (175, 190, 175))
        self.set_font("Sans", "", 11)
        self.set_xy(0, 102)
        self.cell(PW, 0, "CARTA DE DESAYUNOS", align="C")

        # Ciudad
        tc(self, (120, 140, 120))
        self.set_font("Sans", "", 8)
        self.set_xy(0, PH - 12)
        self.cell(PW, 0, "Benimaclet · Valencia", align="C")

    # ── Slide separador de sección ────────────────────────────────────────────
    def slide_section(self, title, subtitle, bg, accent):
        self.add_page()

        c(self, bg)
        self.rect(0, 0, PW, PH, "F")

        # Franjas decorativas
        c(self, accent)
        self.rect(0, 0, PW, 1.8, "F")
        self.rect(0, PH - 1.8, PW, 1.8, "F")

        # Número de sección pequeño
        tc(self, (*accent, 100) if False else (200, 220, 200))
        self.set_font("Sans", "", 9)
        self.set_xy(0, PH / 2 - 30)
        self.cell(PW, 0, "──  SECCIÓN  ──", align="C")

        # Título principal
        tc(self, WHITE)
        self.set_font("Serif", "B", 52)
        self.set_xy(0, PH / 2 - 22)
        self.cell(PW, 0, title, align="C")

        # Línea
        dc(self, GOLD)
        self.set_line_width(0.4)
        self.line(cx := PW / 2, PH / 2 + 5, cx, PH / 2 + 5)  # dummy; below is real
        self.line(PW / 2 - 28, PH / 2 + 5, PW / 2 + 28, PH / 2 + 5)

        # Subtítulo
        tc(self, CREAM_WARM)
        self.set_font("Sans", "", 13)
        self.set_xy(0, PH / 2 + 10)
        self.cell(PW, 0, subtitle, align="C")

    # ── Slide de ítem (foto izquierda + texto derecha) ────────────────────────
    def slide_item(self, item, photo_path, number, is_special=False):
        self.add_page()

        # Fondo crema
        c(self, CREAM)
        self.rect(0, 0, PW, PH, "F")

        # Foto rellena el 60% izquierdo
        photo_w = PW * 0.60
        fill_image(self, photo_path, 0, 0, photo_w, PH)

        # Sombra sutil entre foto y panel (línea)
        dc(self, (200, 195, 190))
        self.set_line_width(0.1)
        self.line(photo_w, 0, photo_w, PH)

        # Panel derecho
        px = photo_w + 10   # x inicio texto (con margen interior)
        pw = PW - photo_w   # ancho del panel
        tw = pw - 18        # ancho disponible para texto

        # Número
        num_str = f"0{number}" if number < 10 else str(number)
        accent = BROWN if is_special else GREEN
        tc(self, accent)
        self.set_font("Sans", "B", 10)
        self.set_xy(px, 15)
        self.cell(tw, 0, num_str)

        # Badge / etiqueta
        tc(self, MUTED)
        self.set_font("Sans", "", 7.5)
        self.set_xy(px, 23)
        self.cell(tw, 0, item["badge"])

        # Línea divisoria
        dc(self, accent)
        self.set_line_width(0.35)
        self.line(px, 31, px + tw, 31)

        # Título (1 o 2 líneas)
        tc(self, CHARCOAL)
        title_lines = item["title"]
        if len(title_lines) == 1:
            self.set_font("Serif", "B", 22)
            self.set_xy(px, 35)
            self.cell(tw, 11, title_lines[0])
            title_end_y = 46
        else:
            self.set_font("Serif", "B", 19)
            y = 34
            for line in title_lines:
                self.set_xy(px, y)
                self.cell(tw, 9, line)
                y += 9
            title_end_y = y + 1

        # Descripción
        tc(self, MUTED)
        self.set_font("Sans", "", 9.5)
        self.set_xy(px, title_end_y + 4)
        self.multi_cell(tw, 5.2, item["desc"])

        # Precio — grande, en la parte baja
        price_y = PH - 48
        tc(self, BROWN if not is_special else GREEN_DARK)
        self.set_font("Serif", "B", 42)
        self.set_xy(px, price_y)
        self.cell(tw, 0, item["price"])

        # Nota (zumo)
        tc(self, MUTED)
        self.set_font("Sans", "", 8)
        self.set_xy(px, price_y + 20)
        self.multi_cell(tw, 4.5, item["note"])

        # Franja de color inferior
        c(self, accent)
        self.rect(photo_w, PH - 4, pw, 4, "F")

        # Logo KÜME pequeño
        tc(self, (210, 207, 204))
        self.set_font("Serif", "I", 7.5)
        self.set_xy(photo_w, PH - 14)
        self.cell(pw - 4, 0, "KÜME café", align="R")


# ══════════════════════════════════════════════════════════════════════════════
#  GENERACIÓN DEL PDF
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(jpg_files):
    print("Generando PDF …")
    pdf = MenuPDF(unit="mm", format=(PW, PH))
    pdf.set_auto_page_break(False)
    pdf.setup_fonts()

    # Portada
    pdf.slide_cover()

    # ── Sección 1: Desayunos del Día ──────────────────────────────────────────
    pdf.slide_section(
        "Desayunos del Día",
        "Café y algo más — desde 3 €",
        GREEN,
        BROWN,
    )

    for i, item in enumerate(NORMAL_ITEMS):
        photo = jpg_files[i % len(jpg_files)]
        pdf.slide_item(item, photo, i + 1, is_special=False)

    # ── Sección 2: Desayunos Especiales ──────────────────────────────────────
    pdf.slide_section(
        "Desayunos Especiales",
        "Para empezar el día con todo — desde 5 €",
        GREEN_DARK,
        BROWN,
    )

    for i, item in enumerate(SPECIAL_ITEMS):
        photo = jpg_files[(len(NORMAL_ITEMS) + i) % len(jpg_files)]
        pdf.slide_item(item, photo, i + 1, is_special=True)

    pdf.output(str(PDF_PATH))
    print(f"\nOK PDF generado: {PDF_PATH}")
    print(f"  {len(NORMAL_ITEMS) + len(SPECIAL_ITEMS) + 4} paginas en total")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    jpg_files = convert_nef_to_jpg()
    if not jpg_files:
        print("No hay imágenes disponibles. Abortando.")
        sys.exit(1)
    generate_pdf(jpg_files)
