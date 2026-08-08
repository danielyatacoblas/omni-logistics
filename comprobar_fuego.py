# -*- coding: utf-8 -*-
"""Comprobación manual del detector de fuego sobre video real.

    python comprobar_fuego.py

No es una prueba automática y por eso no se llama `test_`: necesita los pesos,
los videos y varios minutos de GPU. Lo que mide es lo único que no se puede
fabricar con detecciones sintéticas — que el filtro de brillo distinga un fuego
de verdad de los focos de un almacén.

Dos pasadas, y las dos tienen que salir bien:

  1. `fuego_test.mp4`      → debe dar la alarma
  2. `forklift_almacen.mp4` → NO debe darla (aquí es donde saltaban los focos)

Un detector que solo pasa la primera es inútil: en un almacén real estaría
sonando todo el día y en una semana nadie le haría caso.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from backend.processor import VideoProcessor

RAIZ = Path(__file__).resolve().parent


def pasada(video: str, modulo: str, segundos: int = 30) -> dict:
    ruta = RAIZ / "videos" / video
    if not ruta.exists():
        print(f"  falta videos/{video} — se salta")
        return {}

    p = VideoProcessor()
    p.start(str(ruta), video, 0.35, modulo)
    s = {}
    for i in range(segundos // 3):
        time.sleep(3)
        s = p.status()
        f = s.get("fire")
        if f is None:
            print(f"  [{3 * (i + 1):>2}s] cargando modelos…")
        else:
            print(f"  [{3 * (i + 1):>2}s] fps {s['proc_fps']:>5} | "
                  f"fuego {f['fire_now']} humo {f['smoke_now']} "
                  f"activo={f['active']} eventos={f['events']}")
            if f["events"] > 0:
                break
        if s.get("finished"):
            break
    print("  alertas:", [(a["modulo"], a["tipo"]) for a in s.get("alerts", [])][:4])
    p.stop()
    return s


def main() -> int:
    print("1 · fuego real — debe dar la alarma")
    con_fuego = pasada("fuego_test.mp4", "seguridad")

    print("\n2 · almacén normal — NO debe darla")
    sin_fuego = pasada("forklift_almacen.mp4", "trazabilidad", segundos=15)

    if not con_fuego or not sin_fuego:
        print("\nNo se pudo comprobar: faltan videos.")
        return 2

    detecta = (con_fuego.get("fire") or {}).get("events", 0)
    falsas = (sin_fuego.get("fire") or {}).get("events", 0)
    print(f"\ndetecciones en el video con fuego: {detecta}")
    print(f"falsas alarmas en el almacén:      {falsas}")

    ok = detecta > 0 and falsas == 0
    print("BIEN" if ok else "MAL — revisar el umbral de brillo en config.py")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
