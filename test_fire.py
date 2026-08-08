"""Prueba rápida: alarma de incendio + sin falsos positivos en almacén."""
import time

from backend.processor import VideoProcessor


def run(video, usecase, secs=30):
    p = VideoProcessor()
    p.start(f"videos/{video}", video, 0.35, usecase)
    s = {}
    for i in range(secs // 3):
        time.sleep(3)
        s = p.status()
        f = s.get("fire")
        if f is not None:
            print(f"[{3*(i+1):>2}s] fps {s['proc_fps']:>5} | fuego {f['fire_now']} "
                  f"humo {f['smoke_now']} activo={f['active']} eventos={f['events']}")
            if f["events"] > 0:
                break
        else:
            print(f"[{3*(i+1):>2}s] cargando modelos...")
        if s.get("finished"):
            break
    alerts = [(a["modulo"], a["tipo"]) for a in s.get("alerts", [])]
    print("  alertas:", alerts[:4])
    p.stop()
    return s


print("=== FUEGO (fuego_test.mp4, modulo seguridad) ===")
s1 = run("fuego_test.mp4", "seguridad")

print("=== ALMACEN (forklift_almacen.mp4, trazabilidad+heatmap) ===")
s2 = run("forklift_almacen.mp4", "trazabilidad", secs=15)
f2 = s2.get("fire") or {}
print("falsas alarmas de fuego en almacén:", f2.get("events", "?"))
