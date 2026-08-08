# -*- coding: utf-8 -*-
"""Pruebas de los eventos de seguridad: caída, exceso de velocidad, obstrucción.

    python -m pytest test_eventos.py -q

Fabrica detecciones a mano y las pasa por `Analytics`: sin video, sin modelos y
sin GPU. Esa es la gracia — la parte que decide si suena una alarma se puede
comprobar en medio segundo, y no depende de que el detector acierte ese día.

El guion es siempre el mismo, 11 segundos:

  · una persona de pie que se cae a los 2 s y se levanta a los 6 s
  · un montacargas cruzando el almacén más rápido de lo permitido
  · un pallet quieto en mitad de la ruta de evacuación, los 11 segundos
"""
from __future__ import annotations

import numpy as np
import pytest
import supervision as sv

from backend.analytics import Analytics
from backend.detector import FORKLIFT, PALLET, PERSON

W, H, FPS = 1280, 720, 25.0
DT = 1.0 / FPS


def _dets(filas):
    """filas = [(x1, y1, x2, y2, clase, id_de_seguimiento)]"""
    if not filas:
        return sv.Detections.empty()
    d = sv.Detections(
        xyxy=np.array([f[:4] for f in filas], dtype=np.float32),
        class_id=np.array([f[4] for f in filas]),
        confidence=np.ones(len(filas)),
    )
    d.tracker_id = np.array([f[5] for f in filas])
    return d


CONFIG = {"line": None, "zones": [
    {"id": "p1", "name": "Ruta evacuación", "type": "pasillo", "color": "#E19100",
     "points": [[0.0, 0.5], [0.5, 0.5], [0.5, 1.0], [0.0, 1.0]]},
]}


@pytest.fixture(scope="module")
def resumen():
    a = Analytics(CONFIG, W, H, FPS)
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    for f in range(int(11 * FPS)):
        t = f * DT
        filas = []
        # La persona: de pie (100×220) salvo entre t=2 y t=6, donde la caja se
        # vuelve ancha y baja (220×90) — que es como se ve alguien tumbado.
        if t < 2.0 or t > 6.0:
            filas.append((900, 200, 1000, 420, PERSON, 1))
        else:
            filas.append((850, 350, 1070, 440, PERSON, 1))
        # El montacargas: 40 px por fotograma = 1000 px/s ≈ 0,78 anchos/s.
        x = 50 + (f * 40) % 1000
        filas.append((x, 100, x + 160, 220, FORKLIFT, 2))
        # El pallet: quieto dentro del pasillo, centro en ~(300, 650).
        filas.append((250, 600, 350, 700, PALLET, 3))
        d = _dets(filas)
        a.update(d, d, frame, t, DT)
    return a.snapshot()


# ── los tres eventos ────────────────────────────────────────────────────────

def test_la_caida_se_cuenta_una_sola_vez(resumen):
    """Cuatro segundos en el suelo son UNA caída, no cien alarmas seguidas."""
    assert resumen["safety"]["falls_total"] == 1


def test_al_levantarse_deja_de_estar_caida(resumen):
    assert resumen["safety"]["fallen_now"] == 0


def test_el_montacargas_rapido_dispara_el_evento(resumen):
    assert resumen["safety"]["speed_events"] >= 1


def test_el_pallet_en_el_pasillo_es_una_obstruccion(resumen):
    assert resumen["safety"]["obstructions"] == 1


def test_el_pasillo_queda_marcado_como_bloqueado(resumen):
    assert resumen["aisles"][0]["blocked"] is True
    assert resumen["aisles"][0]["name"] == "Ruta evacuación"


# ── lo que llega a la interfaz ──────────────────────────────────────────────

def test_cada_evento_deja_su_alerta_con_hora_y_tipo(resumen):
    alertas = resumen["alerts"]
    assert alertas, "ningún evento llegó al panel de alertas"
    for a in alertas:
        assert a["t"] is not None
        assert a["tipo"]
    assert any("CAÍDA" in a["tipo"].upper() for a in alertas)


def test_se_cuentan_los_tres_objetos_del_guion(resumen):
    assert resumen["pallets_now"] == 1
    assert resumen["forklifts_now"] == 1
    assert resumen["persons_now"] == 1


# ── el caso vacío, que es el que rompe las cosas ────────────────────────────

def test_sin_detecciones_no_inventa_eventos():
    a = Analytics(CONFIG, W, H, FPS)
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    for f in range(int(3 * FPS)):
        vacio = sv.Detections.empty()
        a.update(vacio, vacio, frame, f * DT, DT)
    s = a.snapshot()
    assert s["safety"]["falls_total"] == 0
    assert s["safety"]["obstructions"] == 0
    assert s["aisles"][0]["blocked"] is False
