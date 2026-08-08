#!/usr/bin/env python3
"""Comprueba y descarga lo que el repositorio NO versiona: pesos y videos.

Uso:
    python download_models.py              # comprueba qué falta
    python download_models.py --videos     # además descarga videos de muestra

Los pesos y los videos no están en el repositorio porque no son código: son
entrada del sistema. Varios pasan del límite de 100 MB de GitHub, y clonar el
proyecto pasaría de segundos a minutos.

De los cinco modelos que usa este MVP, **solo uno es descargable sin más**:
`yolo11n.pt`, que publica Ultralytics. Los otros cuatro están afinados para
este caso —pallets, montacargas, fuego/humo y EPP— y no tienen una URL pública
estable. Este script lo dice claramente en vez de fallar a mitad: saber qué
falta y de dónde sacarlo es más útil que una descarga que se rompe.
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
WEIGHTS = ROOT / "weights"
VIDEOS = ROOT / "videos"

# Los que sí se pueden traer solos.
DESCARGABLES = {
    "yolo11n.pt":
        "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt",
}

# Los afinados para este caso. No hay URL pública: se dice de dónde salieron.
PROPIOS = {
    "pallet_n_640.pt":
        "YOLO11n afinado con un conjunto de pallets de madera a 640 px",
    "forklift_kerem.pt":
        "YOLOv8m de keremberke (montacargas y personas)",
    "fire_smoke.pt":
        "YOLOv8n de fuego y humo, con filtro de brillo encima para "
        "descartar reflejos",
    "ppe_vest.pt":
        "detector de chaleco y casco, usado para marcar infracciones",
}

VIDEOS_MUESTRA = {
    "almacen_racks.mp4":
        "https://videos.pexels.com/video-files/4480994/4480994-hd_1920_1080_25fps.mp4",
    "carga_muelle.mp4":
        "https://videos.pexels.com/video-files/4489739/4489739-hd_1920_1080_25fps.mp4",
}


def _bajar(url: str, destino: Path) -> None:
    if destino.exists() and destino.stat().st_size > 1e5:
        print(f"  · {destino.name} ya está — se omite")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"  ↓ {destino.name} …", end="", flush=True)
    try:
        urllib.request.urlretrieve(url, destino)
        print(f" {destino.stat().st_size // 1024 // 1024} MB")
    except Exception as e:
        print(f" falló: {e}")
        # Un archivo a medias es peor que ninguno: el modelo cargaría y
        # daría un error incomprensible mucho más adelante.
        destino.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", action="store_true",
                    help="descarga también videos de muestra")
    args = ap.parse_args()

    WEIGHTS.mkdir(exist_ok=True)
    print("Pesos descargables:")
    for nombre, url in DESCARGABLES.items():
        _bajar(url, WEIGHTS / nombre)

    print("\nPesos afinados para este caso:")
    faltan = []
    for nombre, que_es in PROPIOS.items():
        if (WEIGHTS / nombre).exists():
            print(f"  · {nombre} — presente")
        else:
            faltan.append(nombre)
            print(f"  ✗ {nombre} — FALTA · {que_es}")

    if args.videos:
        print("\nVideos de muestra:")
        VIDEOS.mkdir(exist_ok=True)
        for nombre, url in VIDEOS_MUESTRA.items():
            _bajar(url, VIDEOS / nombre)

    if faltan:
        print(f"\nFaltan {len(faltan)} pesos afinados. Sin ellos el "
              "detector arranca, pero los módulos que los usan aparecen "
              "desactivados en la interfaz en lugar de reventar.")
        print("Colócalos en weights/ con esos nombres exactos, o cambia la "
              "ruta con las variables PALLET_MODEL, FORKLIFT_MODEL, "
              "FIRE_MODEL y PPE_MODEL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
