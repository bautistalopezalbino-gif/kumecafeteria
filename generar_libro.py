#!/usr/bin/env python3
"""generar_libro.py — carta-kume.pdf (A4) → carta de Küme en formato libro.

Requiere: pip install pypdf pymupdf. Antes, node generar_libro.js
(carta-print.html → carta-kume.pdf); este script lo recomprime y maqueta.

Genera dos PDFs en hojas A3 apaisadas (2 páginas A4 por cara):
  carta-kume-libro.pdf            doble página en orden de lectura (para ver / enviar):
                                  1.ª hoja = exterior (contraportada | portada)
  carta-kume-libro-imprimir.pdf   cuadernillo grapado, listo para imprimir
                                  (a doble cara, voltear por el lado corto) y doblar

El libro necesita un múltiplo de 4 páginas. carta-print.html tiene 12 y no
queda ninguna en blanco; si algún día no cuadra, se añade una página en
blanco antes de la contraportada y el script avisa.
"""
import os
import pymupdf
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

SRC = "carta-kume.pdf"
A4_W, A4_H = 595.0, 842.0          # pt
SHEET_W, SHEET_H = A4_W * 2, A4_H  # A3 apaisado

# Chrome incrusta las fotos a resolución original (~27 MB): se reducen a 300 ppp
doc = pymupdf.open(SRC)
doc.rewrite_images(dpi_threshold=330, dpi_target=300, quality=80)
doc.save(SRC + ".tmp", garbage=4, deflate=True)
doc.close()
os.replace(SRC + ".tmp", SRC)

src = PdfReader(SRC)
pages = list(src.pages)
cover, inner, back = pages[0], pages[1:-1], pages[-1]

# Relleno hasta múltiplo de 4 (blanco = interior de contraportada)
blank = PageObject.create_blank_page(width=A4_W, height=A4_H)
book = [cover] + inner
while (len(book) + 1) % 4:
    book.append(blank)
    print("AVISO: añadida una página en blanco para completar el cuadernillo")
book.append(back)
n = len(book)


def sheet(left, right):
    out = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
    if left is not None:
        out.merge_page(left)
    if right is not None:
        out.merge_transformed_page(right, Transformation().translate(A4_W, 0))
    return out


# 1) Doble página en orden de lectura. La primera hoja es el exterior del
#    libro (contraportada | portada), así ninguna hoja queda a medias.
w = PdfWriter()
w.add_page(sheet(book[-1], book[0]))
for i in range(1, n - 1, 2):
    w.add_page(sheet(book[i], book[i + 1]))
w.add_metadata({"/Title": "KÜME café — La Carta (libro)"})
w.write("carta-kume-libro.pdf")

# 2) Imposición para cuadernillo grapado: 12,1 · 2,11 · 10,3 · 4,9 · 8,5 · 6,7
w = PdfWriter()
for k in range(n // 4):
    w.add_page(sheet(book[n - 1 - 2 * k], book[2 * k]))      # cara
    w.add_page(sheet(book[2 * k + 1], book[n - 2 - 2 * k]))  # dorso
w.add_metadata({"/Title": "KÜME café — La Carta (libro, para imprimir)"})
w.write("carta-kume-libro-imprimir.pdf")

print(f"OK · {n} páginas de libro · {n // 4} hojas A3 a doble cara")
