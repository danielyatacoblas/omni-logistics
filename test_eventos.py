"""Prueba sintética de los 3 eventos nuevos: caída, velocidad, obstrucción.

Fabrica detecciones (sin video ni modelos) y las pasa por Analytics.
"""
import numpy as np
import supervision as sv

from backend.analytics import Analytics

W, H, FPS = 1280, 720, 25.0
DT = 1.0 / FPS
frame = np.zeros((H, W, 3), dtype=np.uint8)


def dets(rows):
    """rows = [(x1,y1,x2,y2, cls, tid)]"""
    if not rows:
        return sv.Detections.empty()
    xyxy = np.array([r[:4] for r in rows], dtype=np.float32)
    cid = np.array([r[4] for r in rows])
    tid = np.array([r[5] for r in rows])
    d = sv.Detections(xyxy=xyxy, class_id=cid, confidence=np.ones(len(rows)))
    d.tracker_id = tid
    return d


cfg = {"line": None, "zones": [
    {"id": "p1", "name": "Ruta evacuación", "type": "pasillo", "color": "#E19100",
     "points": [[0.0, 0.5], [0.5, 0.5], [0.5, 1.0], [0.0, 1.0]]},
]}
a = Analytics(cfg, W, H, FPS)

t = 0.0
# 1) persona de pie (100x220) que a los 2s "cae" (caja 220x90) y queda 2s
# 2) forklift que se mueve 100 px/frame (=2500 px/s ≈ 2.0 ancho/s >> límite)
# 3) pallet quieto DENTRO del pasillo todo el rato (10s > OBSTRUCT_SEC=8)
for f in range(int(11 * FPS)):
    t = f * DT
    rows = []
    # persona: de pie hasta t=2, caída de t=2 a t=6, de pie después
    if t < 2.0 or t > 6.0:
        rows.append((900, 200, 1000, 420, 0, 1))       # de pie (w100 h220)
    else:
        rows.append((850, 350, 1070, 440, 0, 1))       # acostada (w220 h90)
    # forklift veloz (avanza 40px/frame = 1000px/s ≈ 0.78 ancho/s)
    x = 50 + (f * 40) % 1000
    rows.append((x, 100, x + 160, 220, 1, 2))
    # pallet quieto dentro del pasillo (centro ~(300,650))
    rows.append((250, 600, 350, 700, 2, 3))
    d = dets(rows)
    a.update(d, d, frame, t, DT)

s = a.snapshot()
sf = s["safety"]
print("caídas:", sf["falls_total"], "| caído ahora:", sf["fallen_now"])
print("excesos velocidad:", sf["speed_events"], "| rápidos ahora:", sf["speeding_now"])
print("obstrucciones:", sf["obstructions"], "| pasillos bloqueados:", sf["aisles_blocked"])
print("aisles:", s["aisles"])
print("alertas:", [(x["t"], x["tipo"]) for x in s["alerts"]])

ok = (sf["falls_total"] == 1 and sf["speed_events"] >= 1
      and sf["obstructions"] == 1 and s["aisles"][0]["blocked"])
print("\nRESULTADO:", "TODO OK ✓" if ok else "FALLO ✗")
