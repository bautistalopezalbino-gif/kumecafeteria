#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KÜME Café — Generador de vídeo animado para Reels/TikTok
Formato: 1080×1920 (9:16 vertical) | 30fps | H.264
Duración: ~52s (8 ítems × 6.5s)
Animaciones: popup spring → Ken Burns hold → fade out
"""

import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE         = Path(r"C:\Users\EMILIANO JAVIER LOPE\Desktop\Kume cafeteria")
PNG_ENHANCED = BASE / "fotos" / "menus desayunos" / "png_enhanced"
PNG_NOBG     = BASE / "fotos" / "menus desayunos" / "png_nobg"
OUTPUT_PATH  = BASE / "Kume_Menu_Reels.mp4"
FONTS_DIR    = Path(r"C:\Windows\Fonts")

# ── Dimensiones vídeo ──────────────────────────────────────────────
W, H  = 1080, 1920
FPS   = 30

# ── Frames por fase ────────────────────────────────────────────────
POPUP_F = 21    # 0.7s
HOLD_F  = 150   # 5.0s
FADE_F  = 24    # 0.8s
TOTAL_F = POPUP_F + HOLD_F + FADE_F   # 195 frames = 6.5s por ítem

# ── Zoom Ken Burns ─────────────────────────────────────────────────
ZOOM_MAX = 1.03

# ── Paleta KÜME ────────────────────────────────────────────────────
BG       = (13,  22,  17)
HDR_NRM  = (46,  84,  56)
HDR_SPC  = (115, 74,  20)
GOLD     = (200, 160, 90)
WHITE_W  = (248, 244, 238)
MUTED    = (138, 126, 102)

# ── Layout zonas Y ────────────────────────────────────────────────
Y_HDR_END  = 160   # Barra KÜME: 0→160
Y_CAT_END  = 350   # Categoría: 160→350
Y_PHOTO_END= 1200  # Foto: 350→1200
Y_NAME_END = 1480  # Nombre: 1200→1480
Y_PRICE_END= 1720  # Precio: 1480→1720
Y_NOTE_END = 1860  # Nota: 1720→1860
               # Banda inferior: 1860→1920

# ── Datos del menú ─────────────────────────────────────────────────
MENU_ITEMS = [
    {"file": "DSC_0002", "name1": "Café + Croissant",       "name2": "",                       "price": "3€",    "note": "+ zumo 1€",             "category": "DESAYUNOS DEL DÍA", "hdr": HDR_NRM},
    {"file": "DSC_0015", "name1": "Café + Tostada",         "name2": "Tomate y Aceite",         "price": "3€",    "note": "+ zumo 1€",             "category": "DESAYUNOS DEL DÍA", "hdr": HDR_NRM},
    {"file": "DSC_0017", "name1": "Café + Tostada",         "name2": "Tomate y Jamón Serrano",  "price": "3€",    "note": "+ zumo 1€",             "category": "DESAYUNOS DEL DÍA", "hdr": HDR_NRM},
    {"file": "DSC_0021", "name1": "Café + Tostada",         "name2": "Mantequilla y Mermelada", "price": "3€",    "note": "+ zumo 1€",             "category": "DESAYUNOS DEL DÍA", "hdr": HDR_NRM},
    {"file": "DSC_0013", "name1": "Café + Dos Medialunas",  "name2": "",                       "price": "3€",    "note": "+ zumo 1€",             "category": "DESAYUNOS DEL DÍA", "hdr": HDR_NRM},
    {"file": "DSC_0034", "name1": "Tostada de Salmón,",     "name2": "Aguacate y Queso",        "price": "5,50€", "note": "café + zumo incluidos", "category": "ESPECIALES",         "hdr": HDR_SPC},
    {"file": "DSC_0031", "name1": "Tostada de Huevo,",      "name2": "Guacamole y Tomate",      "price": "5€",    "note": "café + zumo incluidos", "category": "ESPECIALES",         "hdr": HDR_SPC},
    {"file": "DSC_0035", "name1": "Desayuno Completo",      "name2": "Huevos, Bacon o Guacamole","price": "5,50€","note": "café + zumo incluidos", "category": "ESPECIALES",         "hdr": HDR_SPC},
]


# ── Dependencias ────────────────────────────────────────────────────

def check_dependencies():
    try:
        import imageio_ffmpeg
    except ImportError:
        print("ERROR: imageio-ffmpeg no instalado.")
        print("  Ejecuta: pip install imageio-ffmpeg")
        sys.exit(1)
    try:
        import imageio
        import numpy
        from PIL import Image
    except ImportError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    print("Dependencias OK")


# ── Utilidades ──────────────────────────────────────────────────────

def darken(color, factor):
    return tuple(max(0, int(c * factor)) for c in color)

def ease_out_cubic(t):
    return 1.0 - (1.0 - min(t, 1.0)) ** 3

def resolve_photo_path(stem):
    enhanced = PNG_ENHANCED / f"{stem}.png"
    nobg     = PNG_NOBG     / f"{stem}.png"
    if enhanced.exists():
        return enhanced
    elif nobg.exists():
        return nobg
    raise FileNotFoundError(f"Foto no encontrada: {stem}.png (buscando en png_enhanced/ y png_nobg/)")


# ── Fuentes ─────────────────────────────────────────────────────────

def load_fonts():
    def font(name, size):
        path = FONTS_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"Fuente no encontrada: {path}")
        return ImageFont.truetype(str(path), size)

    return {
        "brand":    font("georgiab.ttf", 52),
        "category": font("segoeui.ttf",  34),
        "name":     font("georgiab.ttf", 66),
        "price":    font("georgiab.ttf", 130),
        "note":     font("segoeui.ttf",  36),
    }


# ── Foto del producto ────────────────────────────────────────────────

def prepare_product_image(stem):
    """Carga RGBA, escala a max 900×800px. Llamar UNA SOLA VEZ por ítem."""
    path = resolve_photo_path(stem)
    img  = Image.open(str(path)).convert("RGBA")
    # Recortar a bbox de alpha para eliminar padding transparente
    alpha = img.split()[3]
    bbox  = alpha.getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h  = img.size
    max_w, max_h = 920, 820
    scale = min(max_w / w, max_h / h, 1.0)   # nunca upscale
    new_w = int(w * scale)
    new_h = int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


# ── Construcción del frame base ──────────────────────────────────────

def build_base_frame(item, fonts, product_img):
    """Frame estático sin animación. Se llama UNA VEZ por ítem."""
    canvas = Image.new("RGB", (W, H), BG)
    draw   = ImageDraw.Draw(canvas)
    hdr    = item["hdr"]

    # Barra KÜME (0→160px)
    draw.rectangle([(0, 0), (W, Y_HDR_END)], fill=hdr)
    draw.text((W // 2, Y_HDR_END // 2), "KÜME café",
              fill=WHITE_W, font=fonts["brand"], anchor="mm")

    # Decorative separator line below KÜME
    line_color = tuple(min(255, c + 30) for c in hdr)
    draw.rectangle([(0, Y_HDR_END), (W, Y_HDR_END + 3)], fill=GOLD)

    # Categoría (160→350px)
    cat_bg = darken(hdr, 0.78)
    draw.rectangle([(0, Y_HDR_END + 3), (W, Y_CAT_END)], fill=cat_bg)
    cat_y = Y_HDR_END + 3 + (Y_CAT_END - Y_HDR_END - 3) // 2
    draw.text((W // 2, cat_y), item["category"],
              fill=WHITE_W, font=fonts["category"], anchor="mm")

    # Foto producto (350→1200px, zona 850px) — sobre BG oscuro
    photo_zone_h = Y_PHOTO_END - Y_CAT_END   # 850px
    pw, ph = product_img.size
    px = (W - pw) // 2
    py = Y_CAT_END + (photo_zone_h - ph) // 2
    canvas.paste(product_img, (px, py), product_img)

    # Línea separadora sutil entre foto y texto
    draw.rectangle([(0, Y_PHOTO_END), (W, Y_PHOTO_END + 2)], fill=darken(hdr, 0.5))

    # Nombre (1200→1480px)
    name_zone_h = Y_NAME_END - Y_PHOTO_END   # 280px
    if item["name2"]:
        # 2 líneas
        y1 = Y_PHOTO_END + name_zone_h // 2 - 54
        y2 = Y_PHOTO_END + name_zone_h // 2 + 10
        draw.text((W // 2, y1), item["name1"], fill=WHITE_W, font=fonts["name"], anchor="mm")
        draw.text((W // 2, y2), item["name2"], fill=WHITE_W, font=fonts["name"], anchor="mm")
    else:
        # 1 línea centrada
        y1 = Y_PHOTO_END + name_zone_h // 2 - 22
        draw.text((W // 2, y1), item["name1"], fill=WHITE_W, font=fonts["name"], anchor="mm")

    # Precio (1480→1720px)
    price_center_y = Y_NAME_END + (Y_PRICE_END - Y_NAME_END) // 2
    draw.text((W // 2, price_center_y), item["price"],
              fill=GOLD, font=fonts["price"], anchor="mm")

    # Nota (1720→1860px)
    note_center_y = Y_PRICE_END + (Y_NOTE_END - Y_PRICE_END) // 2
    draw.text((W // 2, note_center_y), item["note"],
              fill=MUTED, font=fonts["note"], anchor="mm")

    # Banda inferior (1860→1920px)
    draw.rectangle([(0, Y_NOTE_END), (W, H)], fill=hdr)

    return canvas


# ── Funciones de animación ───────────────────────────────────────────

def apply_popup(base_frame, frame_idx):
    """Scale 0.82→1.0 ease-out-cubic, anclado al borde inferior."""
    t     = frame_idx / POPUP_F
    ease  = ease_out_cubic(t)
    scale = 0.82 + 0.18 * ease
    new_w = max(1, int(W * scale))
    new_h = max(1, int(H * scale))
    scaled = base_frame.resize((new_w, new_h), Image.BILINEAR)
    canvas = Image.new("RGB", (W, H), BG)
    x = (W - new_w) // 2   # centrado horizontal
    y = H - new_h           # anclado al borde inferior
    canvas.paste(scaled, (x, y))
    return np.array(canvas, dtype=np.uint8)


def apply_ken_burns(base_frame, frame_idx):
    """Zoom suave 1.0→1.03 durante la fase hold."""
    t     = frame_idx / max(HOLD_F - 1, 1)
    scale = 1.0 + (ZOOM_MAX - 1.0) * t
    new_w = max(W, int(W * scale))
    new_h = max(H, int(H * scale))
    zoomed = base_frame.resize((new_w, new_h), Image.BILINEAR)
    x0 = (new_w - W) // 2
    y0 = (new_h - H) // 2
    cropped = zoomed.crop((x0, y0, x0 + W, y0 + H))
    return np.array(cropped, dtype=np.uint8)


def apply_fade(frame_np, alpha_factor):
    """Multiplica todos los píxeles por alpha_factor (0..1)."""
    return (frame_np * alpha_factor).astype(np.uint8)


# ── Render de un ítem ────────────────────────────────────────────────

def render_item_frames(item, fonts, writer):
    """Genera y escribe los 195 frames de un ítem al writer."""
    product_img = prepare_product_image(item["file"])
    base_frame  = build_base_frame(item, fonts, product_img)

    # Fase 1: POPUP (frames 0..POPUP_F-1)
    for f in range(POPUP_F):
        writer.append_data(apply_popup(base_frame, f))

    # Fase 2: HOLD / Ken Burns (frames POPUP_F..POPUP_F+HOLD_F-1)
    for f in range(HOLD_F):
        writer.append_data(apply_ken_burns(base_frame, f))

    # Calcular último frame Ken Burns una sola vez para el fade
    last_kb = apply_ken_burns(base_frame, HOLD_F - 1)

    # Fase 3: FADE OUT (frames POPUP_F+HOLD_F..TOTAL_F-1)
    for f in range(FADE_F):
        alpha = 1.0 - (f / FADE_F)
        writer.append_data(apply_fade(last_kb, alpha))


# ── Main ────────────────────────────────────────────────────────────

def main():
    print("=== KÜME Menu Reels Generator ===\n")
    check_dependencies()

    if OUTPUT_PATH.exists():
        print(f"[INFO] {OUTPUT_PATH.name} ya existe.")
        print("  Borra el archivo y vuelve a ejecutar para regenerar.")
        sys.exit(0)

    import imageio

    print("Cargando fuentes...")
    fonts = load_fonts()

    total = len(MENU_ITEMS)
    duration_s = total * TOTAL_F / FPS
    print(f"Ítems: {total}  |  Frames: {total * TOTAL_F}  |  Duración: {duration_s:.1f}s\n")

    t_start = time.time()

    with imageio.get_writer(
        str(OUTPUT_PATH),
        format="ffmpeg",
        mode="I",
        fps=FPS,
        codec="libx264",
        quality=9,
        macro_block_size=1,
    ) as writer:
        for i, item in enumerate(MENU_ITEMS):
            print(f"[{i+1}/{total}] {item['name1']} ({item['file']}.png)")
            t0 = time.time()
            render_item_frames(item, fonts, writer)
            elapsed = time.time() - t0
            remaining = (total - i - 1) * elapsed
            print(f"  {TOTAL_F} frames en {elapsed:.1f}s  (restante estimado: {remaining/60:.1f} min)")

    total_elapsed = time.time() - t_start
    size_mb = OUTPUT_PATH.stat().st_size / 1e6
    print(f"\nVideo guardado: {OUTPUT_PATH}")
    print(f"Tamaño: {size_mb:.1f} MB  |  Tiempo total: {total_elapsed/60:.1f} min")
    print(f"Duración: {duration_s:.1f}s  |  Resolución: {W}×{H}  |  {FPS}fps")


if __name__ == "__main__":
    main()
