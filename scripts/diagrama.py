# -*- coding: utf-8 -*-
"""Dibuja `docs/flujo.svg`: qué pasa desde el video hasta la decisión.

    python scripts/medir_modelos.py     # primero, deja docs/modelos.json
    python scripts/diagrama.py

El diagrama **lee las cifras medidas** de `docs/modelos.json` y las escribe en
las tarjetas de los modelos. Así no puede quedarse contando una versión del
sistema que ya no existe: si cambia el modelo o la máquina, se vuelve a correr
y el dibujo cambia solo.

Se genera en SVG y no en Mermaid porque hace falta controlar el tamaño de cada
tarjeta para meter cuatro cifras dentro, y porque un SVG se abre a pantalla
completa sin depender de que GitHub decida renderizar.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"

W, H = 2000, 1180
COL = ["#e2e8f0", "#dbeafe", "#ede9fe", "#dcfce7", "#fef3c7"]

TITULO = "OMNI Logistics · de la cámara del almacén a la operación"
BAJADA = ("Cuatro modelos, cada uno con su trabajo, cargados solo cuando "
          "hacen falta. Las cifras de velocidad están medidas en esta "
          "máquina; las de acierto vienen de la validación de cada uno.")
PIE = ("Un detector de fuego a secas marca como incendio cada foco del "
          "almacén. La comprobación de brillo es la diferencia entre una "
          "alarma que se atiende y una que en una semana nadie mira.")

CARRILES = [
    ("Entrada", "Las cámaras que ya hay"),
    ("Detección", "Cuatro modelos, uno por trabajo"),
    ("Identidad", "Qué es el mismo objeto"),
    ("Analítica", "Qué significa para la operación"),
    ("Decisión", "Qué se hace con eso"),
]


def _t(x, y, txt, size=12, peso="400", color="#0f172a", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{peso}" '
            f'fill="{color}" text-anchor="{anchor}">{escape(txt)}</text>')


def tarjeta(x, y, w, h, titulo, lineas, etiqueta, color, cifras=None):
    """La etiqueta va ARRIBA del título, no a su derecha.

    A la derecha se solapaban en cuanto el título pasaba de tres palabras, y
    eso no se ve hasta que se renderiza — pasó con «Cuánta gente entró y no
    compró».
    """
    p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" '
         f'fill="#ffffff" stroke="#94a3b8" stroke-width="2" '
         f'filter="url(#shadow)"/>']
    yy = y + 26
    if etiqueta:
        ew = 12 + len(etiqueta) * 6.4
        p.append(f'<rect x="{x + 16}" y="{y + 12}" width="{ew}" '
                 f'height="20" rx="10" fill="{color}"/>')
        p.append(_t(x + 16 + ew / 2, y + 26, etiqueta, 9.5, "700",
                    "#0f172a", "middle"))
        yy = y + 54
    for ln in _partir(titulo, int((w - 32) / 8.1)):
        p.append(_t(x + 16, yy, ln, 14.5, "700"))
        yy += 19
    yy += 6
    for ln in lineas:
        p.append(_t(x + 16, yy, ln, 11, "400", "#475569"))
        yy += 16
    if cifras:
        yy += 4
        p.append(f'<line x1="{x + 16}" y1="{yy - 12}" x2="{x + w - 16}" '
                 f'y2="{yy - 12}" stroke="#e2e8f0" stroke-width="1.5"/>')
        for et, val, tono in cifras:
            p.append(_t(x + 16, yy + 4, et, 9.5, "600", "#64748b"))
            p.append(_t(x + w - 16, yy + 4, val, 12, "700", tono, "end"))
            yy += 19
    return "".join(p)


def flecha(x1, y1, x2, y2, texto="", punteada=False):
    mx = (x1 + x2) / 2
    d = f"M {x1} {y1} H {mx} V {y2} H {x2}"
    guion = ' stroke-dasharray="8 7"' if punteada else ""
    s = (f'<path d="{d}" fill="none" stroke="#334155" stroke-width="2.2"'
         f'{guion} marker-end="url(#arrow)"/>')
    if texto:
        s += (f'<text x="{mx}" y="{min(y1, y2) - 10}" font-size="11" '
              f'font-weight="600" fill="#334155" text-anchor="middle" '
              f'stroke="#ffffff" stroke-width="5" paint-order="stroke">'
              f'{escape(texto)}</text>')
    return s


def medidas() -> dict:
    f = DOCS / "modelos.json"
    if not f.exists():
        return {}
    return {m["archivo"]: m for m in json.loads(f.read_text(encoding="utf-8"))}


def pct(m, k):
    v = (m.get("metricas") or {}).get(k)
    return f"{v * 100:.1f} %" if isinstance(v, (int, float)) else "—"


def main() -> int:
    med = medidas()
    y1 = med.get("pallet_n_640.pt", {})
    y2 = med.get("fire_smoke.pt", {})

    cx = [60, 460, 860, 1240, 1620]
    cw = [360, 360, 340, 340, 320]

    piezas = ['<rect width="100%" height="100%" fill="#f8fafc"/>']
    piezas.append(_t(48, 52, TITULO, 30, "700"))
    for i, ln in enumerate(_partir(BAJADA, 118)):
        piezas.append(_t(48, 82 + i * 20, ln, 14, "400", "#475569"))

    top, alto = 150, 900
    for i, (nombre, sub) in enumerate(CARRILES):
        piezas.append(f'<rect x="{cx[i]}" y="{top}" width="{cw[i]}" '
                      f'height="{alto}" rx="18" fill="{COL[i]}" '
                      f'fill-opacity="0.5" stroke="#94a3b8" '
                      f'stroke-width="1.5"/>')
        piezas.append(_t(cx[i] + 16, top + 28, nombre.upper(), 13, "700",
                         "#334155"))
        piezas.append(_t(cx[i] + 16, top + 46, sub, 10.5, "400", "#64748b"))

    # ── flechas primero, para que las tarjetas queden encima ──────────────
    piezas.append(flecha(cx[0] + cw[0] - 20, 330, cx[1] + 20, 330, "fotogramas"))
    # Esta va de la primera columna a la cuarta: si se traza recto atraviesa
    # dos tarjetas. Se baja por debajo de todo y se sube al llegar.
    piezas.append(
        f'<path d="M {cx[0] + cw[0] - 20} 700 V 1010 H {cx[3] + 150} V 960" '
        f'fill="none" stroke="#334155" stroke-width="2.2" '
        f'marker-end="url(#arrow)"/>'
        + _t((cx[0] + cw[0] + cx[3]) / 2, 1002,
             "las zonas entran en la analítica, no en el detector", 11.5,
             "600", "#334155", "middle"))
    piezas.append(flecha(cx[1] + cw[1] - 20, 330, cx[2] + 20, 400, "cajas"))
    piezas.append(flecha(cx[1] + cw[1] - 20, 660, cx[3] + 20, 880, "sin seguimiento",
                         punteada=True))
    piezas.append(flecha(cx[2] + cw[2] - 20, 400, cx[3] + 20, 400, "ID estable"))
    piezas.append(flecha(cx[3] + cw[3] - 20, 400, cx[4] + 20, 330, ""))
    piezas.append(flecha(cx[3] + cw[3] - 20, 700, cx[4] + 20, 560, ""))
    piezas.append(flecha(cx[3] + cw[3] - 20, 880, cx[4] + 20, 790, ""))

    # ── entrada ──────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[0] + 20, 250, cw[0] - 40, 175,
        "Cámara de almacén o muelle",
        ["Un .mp4 de la cámara de siempre.",
         "Los videos van por módulo, y el",
         "listado filtra según el elegido."],
        "EXISTENTE", "#e2e8f0"
        ))
    piezas.append(tarjeta(
        cx[0] + 20, 560, cw[0] - 40, 190,
        "Zonas, pasillos y línea",
        ["Un polígono por zona, otro por",
         "ruta de evacuación, y una línea",
         "en el muelle. Guardados de 0 a 1",
         "por video."],
        "UNA VEZ", "#dbeafe"
        ))

    # ── detección ────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[1] + 20, 230, cw[1] - 40, 250,
        "pallet_n_640 · pallets",
        ["YOLO11n afinado con pallets de",
         "madera. Es el que sostiene la",
         "cifra de ocupación."],
        "DETECTOR", "#dcfce7"
        , [
         ("mAP@50", pct(y1, "mAP50"), "#166534"),
         ("mAP@50-95", pct(y1, "mAP50-95"), "#166534"),
         ("velocidad medida", f"{y1.get('fps', '—')} fps", "#1e40af"),
         ("latencia", f"{y1.get('ms', '—')} ms", "#1e40af")]
        ))
    piezas.append(tarjeta(
        cx[1] + 20, 580, cw[1] - 40, 250,
        "fire_smoke + brillo",
        ["El detector solo marca cada",
         "reflejo de foco como incendio.",
         "Se exige además brillo alto",
         "dentro de la caja."],
        "CON FILTRO", "#fee2e2"
        , [
         ("mAP@50", pct(y2, "mAP50"), "#166534"),
         ("velocidad medida", f"{y2.get('fps', '—')} fps", "#1e40af"),
         ("sin el filtro", "suena todo el día", "#b91c1c")]
        ))

    # ── identidad ────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[2] + 20, 300, cw[2] - 40, 250,
        "ByteTrack",
        ["El mismo ID entre fotogramas,",
         "para pallets y montacargas.",
         "",
         "Los cuatro modelos se cargan",
         "solo al usarse: cargarlos todos",
         "de golpe tarda y ocupa memoria."],
        "SEGUIMIENTO", "#ede9fe"
        , [
         ("si falta un peso", "el módulo sale apagado", "#92400e"),
         ("no", "revienta a media faena", "#166534")]
        ))

    # ── analítica ────────────────────────────────────────────
    for y, tit, ls, cif in (
        (300, "Ocupación por zona", ["Cuántos pallets dentro de cada", "polígono, y desde cuándo."], [("hoy se sabe", "de ayer, si alguien apuntó", "#92400e")]),
        (610, "Muelle: piezas por minuto", ["Cruces de línea de pallets y", "montacargas."], [("es", "el tiempo real de descarga", "#166534")]),
        (790, "Caída · velocidad · obstrucción", ["Cada uno dispara UNA vez. Cuatro", "segundos en el suelo son una", "caída, no cien alarmas."], [("fijado por", "test_eventos.py", "#166534")]),
    ):
        piezas.append(tarjeta(cx[3] + 20, y, cw[3] - 40, 165, tit, ls,
                              "", "", cif))

    # ── decisión ─────────────────────────────────────────────
    for y, tit, ls in (
        (250, "Cuánto queda libre ahora", ["No cuánto quedaba ayer cuando", "alguien pasó a apuntarlo."]),
        (480, "Cuánto tarda de verdad", ["Una descarga, con datos y no", "con la impresión del turno."]),
        (710, "Aviso antes del humo", ["Y un pasillo de evacuación que", "no lleva diez minutos tapado."]),
    ):
        piezas.append(tarjeta(cx[4] + 20, y, cw[4] - 40, 175, tit, ls,
                              "VALOR", "#dcfce7"))

    piezas.append(f'<rect x="48" y="1090" width="{W - 96}" height="52" '
                  f'rx="12" fill="#e2e8f0"/>')
    piezas.append(_t(70, 1122, PIE, 13.5, "700"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d" '
           f'font-family="Segoe UI, Arial, sans-serif">'
           f'<title id="t">{escape(TITULO)}</title>'
           f'<desc id="d">{escape(BAJADA)}</desc>'
           '<defs>'
           '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">'
           '<feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0f172a" '
           'flood-opacity="0.14"/></filter>'
           '<marker id="arrow" markerWidth="9" markerHeight="9" refX="7" '
           'refY="4.5" orient="auto"><path d="M0,0 L0,9 L8,4.5 z" '
           'fill="#334155"/></marker>'
           '</defs>' + "".join(piezas) + '</svg>')

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "flujo.svg").write_text(svg, encoding="utf-8", newline="\n")
    print(f"  docs/flujo.svg  {len(svg) // 1024} KB · "
          f"{'con' if med else 'SIN'} cifras medidas")
    return 0


def _partir(texto: str, ancho: int) -> list:
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + 1 > ancho:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}".strip()
    if actual:
        lineas.append(actual)
    return lineas


if __name__ == "__main__":
    sys.exit(main())
