#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KÜME café — Reel promocional de la carta de Brunch
==================================================
Genera un vídeo vertical 1080×1920 (9:16) para Instagram Reels / TikTok con
TODOS los menús de brunch.html que tienen imagen.

· Paleta y tipografías tomadas de la propia web (brunch.html / DESIGN.md):
    verdes salvia/bosque + crema, Noto Serif + Inter.
· Estructura: intro → (tarjeta de sección → ítems)… → cierre con CTA.
· Animaciones: entrada con escala+fade, Ken Burns suave y salida en fade.

Salida: Kume_Reel_Brunch.mp4
"""

import sys, io, re, html, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE   = Path(__file__).resolve().parent
FONTS  = BASE / ".reel_assets" / "fonts"
SOURCE = BASE / "brunch.html"
OUTPUT = BASE / "Kume_Reel_Brunch.mp4"

# ── Vídeo ───────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS  = 30

# Frames por bloque
INTRO_F   = 78     # 2.6 s
SECTION_F = 42     # 1.4 s
ITEM_F    = 57     # 1.9 s
OUTRO_F   = 96     # 3.2 s

ITEM_IN, ITEM_OUT = 9, 8          # fade in / out del ítem
ZOOM_MAX = 1.035                  # Ken Burns suave (el fondo ya aporta movimiento)

# ── Paleta KÜME (brunch.html :root) ─────────────────────────────────
G950 = (26,  50,  40)    # #1A3228  fondo más oscuro
G900 = (20,  40,  32)    # tono inventado un pelín más oscuro para gradiente
G800 = (43,  83,  64)    # #2B5340  primary
G700 = (61, 107,  80)    # #3D6B50
G400 = (138, 156, 96)    # #8A9C60  salvia/oliva
G200 = (196, 212, 160)   # #C4D4A0  salvia claro (acento precio)
G100 = (224, 235, 208)   # #E0EBD0
G50  = (234, 240, 220)   # #EAF0DC
G10  = (248, 246, 242)   # #F8F6F2  crema
ON_DARK        = (245, 240, 232)        # #F5F0E8
ON_DARK_MUTED  = (200, 200, 185)        # crema atenuada
ON_DARK_SUBTLE = (150, 158, 138)        # verde-crema sutil

# ── Datos de contacto (de brunch.html) ──────────────────────────────
BRAND    = "KÜME café"
WEB      = "kumepasteleria.com"
ADDRESS  = "Benimaclet · C/ Guardia Civil, 20 · Valencia"
TAGLINE  = "Pastelería Argentina · Cafetería de Especialidad"


# ════════════════════════════════════════════════════════════════════
#  Parseo de brunch.html → ítems con imagen
# ════════════════════════════════════════════════════════════════════

def clean(t):
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def parse_menu():
    src = SOURCE.read_text(encoding="utf-8")
    sec_re = re.compile(r'<section class="menu-sec" id="([^"]+)">(.*?)</section>', re.S)
    h2_re  = re.compile(r"<h2>(.*?)</h2>", re.S)
    intro_re = re.compile(r'<div class="section-head">.*?<p>(.*?)</p>', re.S)

    sections = []
    for m in sec_re.finditer(src):
        body = m.group(2)
        h2m  = h2_re.search(body)
        title = clean(h2m.group(1)) if h2m else m.group(1)
        intro = ""
        im = intro_re.search(body)
        if im:
            intro = clean(im.group(1))
        items = []
        for cm in re.finditer(r'<div class="menu-card">(.*?)(?=<div class="menu-card">|$)', body, re.S):
            card = cm.group(1)
            img  = re.search(r'menu-card-img"><img src="([^"]+)"', card)
            name = re.search(r'menu-card-name">(.*?)</div>', card, re.S)
            if not img or not name:
                continue
            desc  = re.search(r'menu-card-desc">(.*?)</div>', card, re.S)
            price = re.search(r'menu-card-price">(.*?)</div>', card, re.S)
            incl  = re.search(r'menu-card-incl">(.*?)</div>', card, re.S)
            p = (BASE / img.group(1))
            if not p.exists():
                continue
            items.append({
                "img":   p,
                "name":  clean(name.group(1)),
                "desc":  clean(desc.group(1)) if desc else "",
                "price": clean(price.group(1)) if price else "",
                "incl":  clean(incl.group(1)) if incl else "",
            })
        if items:
            sections.append({"title": title, "intro": intro, "items": items})
    return sections


# ════════════════════════════════════════════════════════════════════
#  Tipografías
# ════════════════════════════════════════════════════════════════════

def serif(size, weight=700):
    f = ImageFont.truetype(str(FONTS / "NotoSerif.ttf"), size)
    try:
        f.set_variation_by_axes([weight, 100])
    except Exception:
        pass
    return f

def sans(size, w="Regular"):
    return ImageFont.truetype(str(FONTS / f"Inter-{w}.ttf"), size)

FONTS_CACHE = {}
def F(kind):
    if kind in FONTS_CACHE:
        return FONTS_CACHE[kind]
    fn = {
        "brand":     lambda: serif(46, 600),
        "intro_big": lambda: serif(132, 700),
        "intro_sub": lambda: sans(34, "Medium"),
        "sec_big":   lambda: serif(96, 700),
        "sec_intro": lambda: sans(31, "Regular"),
        "eyebrow":   lambda: sans(27, "SemiBold"),
        "name":      lambda: serif(62, 700),
        "desc":      lambda: sans(30, "Regular"),
        "price":     lambda: serif(112, 700),
        "incl":      lambda: sans(29, "SemiBold"),
        "foot":      lambda: sans(25, "Medium"),
        "count":     lambda: sans(27, "SemiBold"),
        "outro_big": lambda: serif(104, 700),
        "outro_web": lambda: sans(40, "Bold"),
        "outro_sub": lambda: sans(30, "Regular"),
    }[kind]()
    FONTS_CACHE[kind] = fn
    return fn


# ════════════════════════════════════════════════════════════════════
#  Utilidades de dibujo
# ════════════════════════════════════════════════════════════════════

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def ease_out(t):
    return 1 - (1 - min(max(t, 0), 1)) ** 3

def ease_in_out(t):
    t = min(max(t, 0), 1)
    return 3 * t * t - 2 * t * t * t

def text_tracking(draw, xy, text, font, fill, tracking=0, anchor_center=True):
    """Dibuja texto con letter-spacing (tracking en px). Centrado en x si anchor_center."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = xy[0] - total / 2 if anchor_center else xy[0]
    y = xy[1]
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill, anchor="lm")
        x += wch + tracking

def wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines

def draw_block(draw, lines, font, cy, fill, max_w, line_gap=10):
    """Dibuja líneas centradas verticalmente alrededor de cy. Devuelve (top, bottom)."""
    asc, desc = font.getmetrics()
    lh = asc + desc + line_gap
    total = lh * len(lines) - line_gap
    y = cy - total / 2
    top = y
    for ln in lines:
        draw.text((W // 2, y + asc), ln, font=font, fill=fill, anchor="ms")
        y += lh
    return top, y - line_gap

def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return m

def cover_fit(img, box_w, box_h):
    """Escala+recorta la imagen para cubrir box (object-fit: cover)."""
    img = img.convert("RGB")
    w, h = img.size
    scale = max(box_w / w, box_h / h)
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    x0 = (nw - box_w) // 2
    y0 = (nh - box_h) // 2
    return img.crop((x0, y0, x0 + box_w, y0 + box_h))


# ════════════════════════════════════════════════════════════════════
#  Fondo ANIMADO (gradiente verde + aurora salvia a la deriva + bokeh)
#  · "Slow rituals": movimiento lento y orgánico, nunca distrae.
#  · Se precalculan sprites una vez; cada frame solo pega y compone.
# ════════════════════════════════════════════════════════════════════

import math

GRAD_RGBA = None     # gradiente base RGBA
VIG_MASK  = None     # máscara de viñeta (L)
DARK_RGB  = Image.new("RGB", (W, H), (7, 16, 11))
BLOBS     = []       # auroras grandes a la deriva
BOKEH     = []       # partículas flotantes
TAU = math.tau


def radial_sprite(d, color, max_alpha, soft=0.16):
    """Círculo radial suave (RGBA) con caída gaussiana."""
    m = Image.new("L", (d, d), 0)
    ImageDraw.Draw(m).ellipse([d * 0.16, d * 0.16, d * 0.84, d * 0.84], fill=max_alpha)
    m = m.filter(ImageFilter.GaussianBlur(d * soft))
    s = Image.new("RGBA", (d, d), color + (0,))
    s.putalpha(m)
    return s


def init_background():
    global GRAD_RGBA, VIG_MASK, BLOBS, BOKEH
    # gradiente vertical G950 → G900
    col = Image.new("RGB", (1, H))
    for y in range(H):
        col.putpixel((0, y), lerp(G950, G900, y / H))
    GRAD_RGBA = col.resize((W, H)).convert("RGBA")

    # viñeta (oscurece bordes, foca el centro)
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-300, -340, W + 300, H + 340], fill=255)
    VIG_MASK = vig.filter(ImageFilter.GaussianBlur(240))

    # auroras: sprite, centro base, amplitud (ax,ay), periodo s, fase, alpha base/var
    blob_defs = [
        (820, G700, (300, 360), (150, 120), 13.0, 0.0,  96, 28),
        (760, G400, (760, 300), (170, 140), 17.0, 1.7,  62, 22),
        (900, G800, (520, 1500),(140, 130), 15.5, 3.2, 104, 26),
        (640, G400, (180, 1150),(130, 160), 11.0, 4.6,  54, 20),
    ]
    for d, color, (cx, cy), (ax, ay), per, ph, a0, av in blob_defs:
        BLOBS.append({"spr": radial_sprite(d, color, 255), "d": d, "cx": cx, "cy": cy,
                      "ax": ax, "ay": ay, "per": per * FPS, "ph": ph, "a0": a0, "av": av})

    # bokeh: partículas flotando hacia arriba con leve vaivén
    rng = np.random.default_rng(7)
    sprites = {s: radial_sprite(s, G200, 255, soft=0.20) for s in (44, 64, 90, 120)}
    for _ in range(16):
        size = int(rng.choice([44, 64, 90, 120]))
        BOKEH.append({
            "spr": sprites[size], "d": size,
            "x0": float(rng.uniform(0, W)),
            "y0": float(rng.uniform(0, H + 200)),
            "speed": float(rng.uniform(7, 18)) / FPS,    # px por frame, hacia arriba
            "amp": float(rng.uniform(20, 70)),
            "per": float(rng.uniform(6, 12)) * FPS,
            "ph": float(rng.uniform(0, TAU)),
            "a0": int(rng.uniform(26, 56)),
            "av": int(rng.uniform(8, 20)),
            "aper": float(rng.uniform(4, 8)) * FPS,
        })


def bg_frame(gt):
    """Fotograma de fondo animado para el frame global gt."""
    base = GRAD_RGBA.copy()
    # auroras
    for b in BLOBS:
        t = gt / b["per"]
        x = b["cx"] + b["ax"] * math.sin(TAU * t + b["ph"])
        y = b["cy"] + b["ay"] * math.cos(TAU * t * 0.83 + b["ph"])
        op = b["a0"] + b["av"] * math.sin(TAU * t * 0.6 + b["ph"] * 1.4)
        spr = b["spr"].copy()
        spr.putalpha(b["spr"].split()[3].point(lambda v, o=op: int(v * o / 255)))
        base.paste(spr, (int(x - b["d"] / 2), int(y - b["d"] / 2)), spr)
    # bokeh
    span = H + 220
    for p in BOKEH:
        y = p["y0"] - p["speed"] * gt
        y = ((y + 110) % span) - 110
        x = p["x0"] + p["amp"] * math.sin(TAU * gt / p["per"] + p["ph"])
        op = max(0, p["a0"] + p["av"] * math.sin(TAU * gt / p["aper"] + p["ph"]))
        spr = p["spr"].copy()
        spr.putalpha(p["spr"].split()[3].point(lambda v, o=op: int(v * o / 255)))
        base.paste(spr, (int(x - p["d"] / 2), int(y - p["d"] / 2)), spr)
    # viñeta
    out = Image.composite(base.convert("RGB"), DARK_RGB, VIG_MASK)
    return out


# ════════════════════════════════════════════════════════════════════
#  Construcción de frames base (PIL) por bloque
# ════════════════════════════════════════════════════════════════════

def brand_header(draw, y=78):
    text_tracking(draw, (W // 2, y), "KÜME café", F("brand"), ON_DARK, tracking=2)
    # subrayado salvia corto
    draw.rectangle([W//2 - 46, y + 40, W//2 + 46, y + 43], fill=G400)


def pill(draw, text, cy, font, fg, bg, pad_x=30, pad_y=14):
    tw = draw.textlength(text, font=font)
    asc, desc = font.getmetrics()
    th = asc + desc
    w = tw + pad_x * 2
    h = th + pad_y * 2
    x0 = W // 2 - w / 2
    y0 = cy - h / 2
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=h / 2, fill=bg)
    draw.text((W // 2, cy), text, font=font, fill=fg, anchor="mm")


def build_item(item, section_title, idx, total):
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)

    brand_header(draw)

    # eyebrow sección
    pill(draw, section_title.upper(), 188, F("eyebrow"), ON_DARK, G800, pad_x=34, pad_y=15)

    # ── Foto (cover, esquinas redondeadas, borde salvia tenue) ──
    PX0, PY0, PW, PH, RAD = 80, 250, W - 160, 940, 52
    photo = cover_fit(Image.open(item["img"]), PW, PH)
    mask = rounded_mask((PW, PH), RAD)
    # sombra suave
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(sh)
    shd.rounded_rectangle([PX0, PY0 + 16, PX0 + PW, PY0 + PH + 16], radius=RAD, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(34))
    bg.paste(sh, (0, 0), sh)
    bg.paste(photo, (PX0, PY0), mask)
    # borde fino
    draw.rounded_rectangle([PX0, PY0, PX0 + PW, PY0 + PH], radius=RAD, outline=(255, 255, 255, 60), width=2)

    # contador
    text_tracking(draw, (W // 2, 1248), f"{idx} / {total}", F("count"), ON_DARK_SUBTLE, tracking=5)

    # ── Bloque de texto (nombre / desc / precio / incl) centrado ──
    name_lines = wrap(draw, item["name"], F("name"), W - 150)
    desc_lines = wrap(draw, item["desc"], F("desc"), W - 180) if item["desc"] else []

    # medir alturas
    def block_h(lines, font, gap):
        asc, desc = font.getmetrics()
        lh = asc + desc + gap
        return lh * len(lines) - gap if lines else 0

    nh = block_h(name_lines, F("name"), 6)
    dh = block_h(desc_lines, F("desc"), 6)
    pasc, pdesc = F("price").getmetrics()
    ph = int((pasc + pdesc) * 0.78)
    ih = block_h([item["incl"]], F("incl"), 0) if item["incl"] else 0

    gap1, gap2, gap3 = 22, 34, 18
    total_h = nh + (gap1 + dh if desc_lines else 0) + gap2 + ph + (gap3 + ih if item["incl"] else 0)

    area_top, area_bot = 1300, 1820
    y = area_top + ((area_bot - area_top) - total_h) / 2

    # nombre
    asc, _ = F("name").getmetrics()
    draw_block(draw, name_lines, F("name"), y + nh / 2, ON_DARK, W - 150, line_gap=6)
    y += nh
    # desc
    if desc_lines:
        y += gap1
        draw_block(draw, desc_lines, F("desc"), y + dh / 2, ON_DARK_MUTED, W - 180, line_gap=6)
        y += dh
    # precio
    y += gap2
    draw.text((W // 2, y + ph / 2), item["price"], font=F("price"), fill=G200, anchor="mm")
    y += ph
    # incl
    if item["incl"]:
        y += gap3
        pill(draw, item["incl"].upper(), y + ih / 2, F("incl"), G950, G200, pad_x=26, pad_y=12)

    # footer
    draw.rectangle([W//2 - 70, 1858, W//2 + 70, 1860], fill=G700)
    text_tracking(draw, (W // 2, 1888), WEB, F("foot"), ON_DARK_SUBTLE, tracking=3)
    return bg


def build_section(sec, idx_food):
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)
    brand_header(draw, y=140)

    # número decorativo
    text_tracking(draw, (W // 2, 760), f"0{idx_food}" if idx_food < 10 else str(idx_food),
                  serif(72, 700), G700, tracking=8)

    # título grande (puede ir en 2 líneas)
    title_lines = wrap(draw, sec["title"], F("sec_big"), W - 160)
    top, bot = draw_block(draw, title_lines, F("sec_big"), 920, ON_DARK, W - 160, line_gap=4)

    # divisor salvia
    draw.rectangle([W//2 - 70, bot + 46, W//2 + 70, bot + 50], fill=G400)

    # intro
    if sec["intro"]:
        intro_lines = wrap(draw, sec["intro"], F("sec_intro"), W - 260)
        draw_block(draw, intro_lines[:3], F("sec_intro"), bot + 150, ON_DARK_MUTED, W - 260, line_gap=8)

    # nº de platos
    n = len(sec["items"])
    pill(draw, f"{n} OPCIONES" if n != 1 else "1 OPCIÓN", 1120, F("count"), G950, G200, pad_x=30, pad_y=13)

    text_tracking(draw, (W // 2, 1820), WEB, F("foot"), ON_DARK_SUBTLE, tracking=3)
    return bg


def build_intro():
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)

    pill(draw, "CARTA DE BRUNCH & DESAYUNOS", 690, F("eyebrow"), ON_DARK, G800, pad_x=34, pad_y=16)

    text_tracking(draw, (W // 2, 880), "KÜME", F("intro_big"), ON_DARK, tracking=10)
    draw.text((W // 2, 1010), "café", font=serif(96, 700), fill=G200, anchor="mm")

    draw.rectangle([W//2 - 90, 1110, W//2 + 90, 1114], fill=G400)

    sub = wrap(draw, "Desayunos, tortitas, crepes, gofres, smoothies, batidos, meriendas y tardeos — todo al momento en Benimaclet.",
               F("intro_sub"), W - 220)
    draw_block(draw, sub, F("intro_sub"), 1260, ON_DARK_MUTED, W - 220, line_gap=10)

    text_tracking(draw, (W // 2, 1500), TAGLINE.upper(), F("foot"), ON_DARK_SUBTLE, tracking=2)
    text_tracking(draw, (W // 2, 1838), WEB, F("outro_sub"), G200, tracking=3)
    return bg


def build_outro():
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)
    brand_header(draw, y=140)

    pill(draw, "TE ESPERAMOS", 700, F("eyebrow"), ON_DARK, G800, pad_x=34, pad_y=16)

    lines = ["Reserva tu", "mesa o pídelo ya."]
    draw_block(draw, lines, F("outro_big"), 920, ON_DARK, W - 140, line_gap=8)

    draw.rectangle([W//2 - 70, 1090, W//2 + 70, 1094], fill=G400)

    text_tracking(draw, (W // 2, 1210), "WHATSAPP · 621 498 315", F("outro_sub"), ON_DARK_MUTED, tracking=2)

    sub = wrap(draw, ADDRESS, F("outro_sub"), W - 200)
    draw_block(draw, sub, F("outro_sub"), 1330, ON_DARK_MUTED, W - 200, line_gap=8)

    pill(draw, WEB, 1560, F("outro_web"), G950, G200, pad_x=40, pad_y=18)
    text_tracking(draw, (W // 2, 1838), TAGLINE.upper(), F("foot"), ON_DARK_SUBTLE, tracking=2)
    return bg


# ════════════════════════════════════════════════════════════════════
#  Animación → frames numpy
# ════════════════════════════════════════════════════════════════════

def transform_layer(content, scale=1.0, yoff=0.0, alpha_mult=1.0):
    """Devuelve una capa RGBA W×H con el contenido escalado/desplazado/atenuado."""
    if scale != 1.0:
        nw, nh = int(round(W * scale)), int(round(H * scale))
        c = content.resize((nw, nh), Image.LANCZOS)
    else:
        nw, nh, c = W, H, content
    if nw == W and nh == H and yoff == 0:
        canvas = c.copy()
    else:
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(c, ((W - nw) // 2, (H - nh) // 2 + int(round(yoff))))
    if alpha_mult < 1.0:
        canvas.putalpha(canvas.split()[3].point(lambda v: int(v * alpha_mult)))
    return canvas


def compose(layer, gt):
    """Compone la capa de contenido sobre el fondo animado del frame global gt."""
    frame = bg_frame(gt)            # RGB
    frame.paste(layer, (0, 0), layer)
    return np.asarray(frame, dtype=np.uint8)


def write_block(writer, content, nframes, fin, fout, gt, kb=True):
    """Escribe nframes del bloque; el fondo animado avanza con gt. Devuelve gt."""
    last = nframes - 1
    for f in range(nframes):
        if f < fin:                                    # entrada: escala + subida + fade
            e = ease_out(f / fin)
            layer = transform_layer(content, 0.94 + 0.06 * e, (1 - e) * 42, min(1.0, e * 1.06))
        elif f >= nframes - fout:                      # salida: fade revelando el fondo
            scale = 1.0 + (ZOOM_MAX - 1.0) * (f / last) if kb else 1.0
            a = (last - f) / fout
            layer = transform_layer(content, scale, 0.0, a)
        else:                                          # sostén: Ken Burns suave (o fijo)
            scale = 1.0 + (ZOOM_MAX - 1.0) * (f / last) if kb else 1.0
            layer = transform_layer(content, scale)
        writer.append_data(compose(layer, gt))
        gt += 1
    return gt


# ════════════════════════════════════════════════════════════════════
#  Main
# ════════════════════════════════════════════════════════════════════

def main():
    import imageio

    print("=== KÜME · Reel Brunch ===")
    sections = parse_menu()
    total_items = sum(len(s["items"]) for s in sections)
    print(f"Secciones: {len(sections)}  |  Ítems con imagen: {total_items}")

    print("Preparando fondo animado…")
    init_background()

    nframes_total = INTRO_F + len(sections) * SECTION_F + total_items * ITEM_F + OUTRO_F
    print(f"Duración estimada: {nframes_total / FPS:.1f}s\n")

    t0 = time.time()
    gt = 0
    with imageio.get_writer(str(OUTPUT), format="ffmpeg", mode="I", fps=FPS,
                            codec="libx264", quality=8, macro_block_size=1,
                            ffmpeg_params=["-pix_fmt", "yuv420p"]) as writer:
        print("[intro]")
        gt = write_block(writer, build_intro(), INTRO_F, 16, 12, gt, kb=True)

        idx = 0
        for si, sec in enumerate(sections, 1):
            print(f"[sección {si}/{len(sections)}] {sec['title']} ({len(sec['items'])})")
            gt = write_block(writer, build_section(sec, si), SECTION_F, 10, 9, gt, kb=False)
            for item in sec["items"]:
                idx += 1
                base = build_item(item, sec["title"], idx, total_items)
                gt = write_block(writer, base, ITEM_F, ITEM_IN, ITEM_OUT, gt, kb=True)

        print("[cierre]")
        gt = write_block(writer, build_outro(), OUTRO_F, 16, 14, gt, kb=True)

    dt = time.time() - t0
    mb = OUTPUT.stat().st_size / 1e6
    print(f"\n✓ {OUTPUT.name}  |  {mb:.1f} MB  |  {nframes_total/FPS:.1f}s  |  render {dt/60:.1f} min")


if __name__ == "__main__":
    main()
