"""Benchmark del detector combinado: mide ms por modelo y fps del pipeline.

Uso:  python bench.py [video] [segundos]
"""
import sys
import time

import cv2

from backend.config import config
from backend.detector import get_detector


def main(video="videos/forklift_almacen.mp4", secs=12):
    d = get_detector()
    cap = cv2.VideoCapture(video)
    ok, fr = cap.read()
    assert ok, "no abre el video"
    if fr.shape[1] > config.max_width:
        h, w = fr.shape[:2]
        fr = cv2.resize(fr, (config.max_width, int(h * config.max_width / w)))

    # warmup
    for _ in range(3):
        d.infer(fr, 0.35)

    # por-modelo (mismo frame repetido: mide SOLO inferencia)
    for name, model, conf in (("pallet", d.pallet, config.pallet_conf),
                              ("forklift", d.forklift, 0.35),
                              ("fire", d.fire, config.fire_conf)):
        t0 = time.time()
        n = 20
        for _ in range(n):
            model.predict(fr, conf=conf, device=d.device, imgsz=d.resolution,
                          half=getattr(d, "half", False), verbose=False)
        print(f"  {name:9} {1000*(time.time()-t0)/n:6.1f} ms/frame")

    # pipeline completo con lectura de video real (decode incluido)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    t0 = time.time()
    n = 0
    while time.time() - t0 < secs:
        ok, fr = cap.read()
        if not ok:
            break
        if fr.shape[1] > config.max_width:
            h, w = fr.shape[:2]
            fr = cv2.resize(fr, (config.max_width, int(h * config.max_width / w)))
        d.infer(fr, 0.35)
        n += 1
    dt = time.time() - t0
    cap.release()
    print(f"  pipeline  {n/dt:6.1f} fps  (decode+resize+3 modelos, {n} frames)")


if __name__ == "__main__":
    v = sys.argv[1] if len(sys.argv) > 1 else "videos/forklift_almacen.mp4"
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    print(f"video={v}  half={getattr(get_detector(), 'half', 'n/a')}  "
          f"res={config.work_res}  device={config.device}")
    main(v, s)
