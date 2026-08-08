"""Procesa un video en hilo: detector combinado + ByteTrack + analítica logística.

Lee el archivo de principio a fin, corre pallet+forklift+person, los sigue con
ByteTrack, dibuja los overlays del módulo activo y publica el JPEG anotado (MJPEG)
+ un snapshot de estadísticas reales.
"""
from __future__ import annotations

import csv
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import supervision as sv

from .analytics import Analytics, _fmt
from .config import config
from .detector import (ES, FIRE, FORKLIFT, MODULE_MODELS, NAMES, NO_HELMET,
                       NO_VEST, PALLET, PERSON, SMOKE, get_detector,
                       mark_warmed)
from .zones import line_to_px, load_config

# colores BGR por clase
COL = {PERSON: (40, 190, 235), FORKLIFT: (235, 160, 40), PALLET: (90, 200, 90),
       FIRE: (0, 80, 255), SMOKE: (160, 160, 160)}
RED = (60, 60, 235)
AMBER = (40, 190, 235)
WHITE = (240, 240, 240)
DARK = (30, 30, 30)


def _resize_max(frame, max_w):
    if max_w and frame.shape[1] > max_w:
        h, w = frame.shape[:2]
        return cv2.resize(frame, (max_w, int(h * max_w / w)))
    return frame


def _hex(h):
    h = h.lstrip("#")
    return int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)


class VideoProcessor:
    def __init__(self):
        self.lock = threading.Lock()
        self.thread = None
        self.running = False
        self.finished = False
        self.latest_jpeg = None
        self.analytics: Analytics | None = None
        self.video = None
        self.usecase = "ocupacion"
        self.conf = config.default_conf
        self.progress = 0.0
        self.video_t = 0.0
        self.duration = 0.0
        self.proc_fps = 0.0
        self._line_px = None
        self._trace = None

    # ── frame inicial / metadatos para el editor ──
    def first_frame_jpeg(self, video_path: str) -> bytes | None:
        cap = cv2.VideoCapture(video_path)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return None
        frame = _resize_max(frame, config.max_width)
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return buf.tobytes() if ok else None

    def video_meta(self, video_path: str) -> dict:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return {"fps": round(fps, 2), "frames": n, "width": w, "height": h,
                "duration_sec": round(n / max(1.0, fps), 1)}

    # ── control ──
    def start(self, video_path: str, video_name: str, conf: float, usecase: str,
              models=None):
        self.stop()
        self.cfg_data = load_config(video_name)
        self.conf = float(conf)
        self.video = video_name
        self.usecase = usecase or "ocupacion"
        # modelos activos: los del apartado, o la selección del usuario
        self.active_models = set(models) if models \
            else set(MODULE_MODELS.get(self.usecase, ["pallet", "forklift"]))
        # limpiar la analítica del apartado ANTERIOR: el status no debe
        # mostrar alertas/contadores viejos mientras cargan los modelos
        self.analytics = None
        self.finished = False
        self.progress = 0.0
        self.video_t = 0.0
        with self.lock:
            self.latest_jpeg = None
        self.running = True
        self.thread = threading.Thread(target=self._loop, args=(video_path,),
                                       daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.thread = None

    def _loop(self, video_path: str):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.running = False
            self.finished = True
            return
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self.duration = total / src_fps if total else 0.0

        ok, frame = cap.read()
        if not ok:
            cap.release(); self.running = False; self.finished = True; return
        frame = _resize_max(frame, config.max_width)
        h, w = frame.shape[:2]

        detector = get_detector()
        tracker = sv.ByteTrack(
            track_activation_threshold=config.track_activation,
            lost_track_buffer=config.track_lost_buffer,
            minimum_matching_threshold=config.track_min_match,
            frame_rate=int(round(src_fps)))
        try:
            self._trace = sv.TraceAnnotator(trace_length=30, thickness=2,
                                            color_lookup=sv.ColorLookup.TRACK)
        except Exception:
            self._trace = None
        self.analytics = Analytics(self.cfg_data, w, h, src_fps)
        self._line_px = line_to_px(self.cfg_data.get("line"), w, h)

        # stride automático (FRAME_STRIDE=0): apunta a ~30 fps efectivos,
        # p.ej. video 60fps → procesa 1 de cada 2 (el decode 4K es lo caro)
        stride = config.frame_stride if config.frame_stride > 0 \
            else max(1, int(round(src_fps / 30.0)))
        dt = stride / src_fps
        frame_idx = 0
        t_wall = time.time()
        proc_count = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        while self.running:
            ok = cap.grab()
            if not ok:
                break
            if frame_idx % stride != 0:
                frame_idx += 1
                continue
            ok, frame = cap.retrieve()
            if not ok:
                break
            frame = _resize_max(frame, config.max_width)

            raw = detector.infer(frame, self.conf, self.active_models)
            tracked = tracker.update_with_detections(raw)

            self.video_t = frame_idx / src_fps
            self.analytics.update(raw, tracked, frame, self.video_t, dt)
            self._draw(frame, raw, tracked)
            mark_warmed()

            proc_count += 1
            elapsed = time.time() - t_wall
            self.proc_fps = proc_count / elapsed if elapsed > 0 else 0.0
            self.progress = (frame_idx / total) if total else 0.0

            ok, buf = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, config.jpeg_quality])
            if ok:
                with self.lock:
                    self.latest_jpeg = buf.tobytes()
            frame_idx += 1

        cap.release()
        self.running = False
        self.finished = True
        self.progress = 1.0
        try:
            self.export_csv()
        except Exception as e:
            print(f"[processor] export CSV falló: {e}")

    # ── dibujo ──
    def _draw(self, frame, raw, tracked):
        uc = self.usecase
        a = self.analytics
        # heatmap de rutas (trazabilidad): se pinta debajo de todo
        if uc == "trazabilidad" and a.heat.max() > 0.5:
            hm = a.heat / max(1e-6, float(a.heat.max()))
            hm8 = (np.clip(hm, 0, 1) * 255).astype(np.uint8)
            hm8 = cv2.resize(hm8, (frame.shape[1], frame.shape[0]),
                             interpolation=cv2.INTER_LINEAR)
            colored = cv2.applyColorMap(hm8, cv2.COLORMAP_TURBO)
            mask = hm8 > 26   # solo donde hay calor real
            blend = cv2.addWeighted(frame, 0.55, colored, 0.45, 0)
            frame[mask] = blend[mask]
        # zonas (ocupación / trazabilidad)
        if uc in ("ocupacion", "trazabilidad"):
            for z in a.zones:
                col = _hex(z["color"])
                status = a._zone_state.get(z["id"], "ok")
                edge = RED if status == "critical" else (
                    (40, 190, 235) if status == "warning" else col)
                overlay = frame.copy()
                cv2.fillPoly(overlay, [z["poly"]], col)
                cv2.addWeighted(overlay, 0.16, frame, 0.84, 0, frame)
                cv2.polylines(frame, [z["poly"]], True, edge, 2)
                p0 = z["poly"][0]
                lbl = f"{z['name']}  {z['count']}/{z['capacity']} ({z.get('pct',0):.0f}%)"
                cv2.putText(frame, lbl, (int(p0[0]), int(p0[1]) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, edge, 2, cv2.LINE_AA)
        # línea de muelle
        if uc == "muelle" and self._line_px:
            (ax, ay), (bx, by) = self._line_px
            cv2.line(frame, (int(ax), int(ay)), (int(bx), int(by)), RED, 3)
            cv2.putText(frame, f"IN {a.dock_in}  OUT {a.dock_out}",
                        (int(ax), int(ay) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        RED, 2, cv2.LINE_AA)
        # estelas (trazabilidad)
        if uc == "trazabilidad" and self._trace is not None and tracked is not None \
                and len(tracked) and tracked.tracker_id is not None:
            try:
                self._trace.annotate(frame, tracked)
            except Exception:
                pass

        # cajas de detección (clases relevantes según módulo)
        show = {"ocupacion": {PALLET}, "muelle": {PALLET, FORKLIFT},
                "seguridad": {FORKLIFT, PERSON},
                "trazabilidad": {FORKLIFT, PERSON, PALLET}}[uc]
        src = tracked if (tracked is not None and len(tracked)) else raw
        if src is not None and len(src):
            tids = src.tracker_id if src.tracker_id is not None else [None] * len(src)
            for box, cid, tid in zip(src.xyxy, src.class_id, tids):
                c = int(cid)
                if c not in show:
                    continue
                x1, y1, x2, y2 = map(int, box)
                col = COL[c]
                cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)
                name = ES.get(NAMES[c], NAMES[c])
                lbl = f"{name}" + (f" #{int(tid)}" if tid is not None else "")
                (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 6, y1), col, -1)
                cv2.putText(frame, lbl, (x1 + 3, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1, cv2.LINE_AA)
                # temporizador de permanencia (trazabilidad)
                if uc == "trazabilidad" and tid is not None:
                    pz = a.object_zone.get(int(tid))
                    if pz:
                        ztxt = f"{pz[0]}: {_fmt(pz[1])}"
                        cv2.putText(frame, ztxt, (x1, y2 + 16),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 235, 120),
                                    2, cv2.LINE_AA)

        # líneas de peligro (seguridad)
        if uc == "seguridad":
            for pr in a.safety_pairs:
                fc = tuple(map(int, pr["fc"]))
                pc = tuple(map(int, pr["pc"]))
                col = RED if pr["critical"] else (40, 190, 235)
                cv2.line(frame, fc, pc, col, 2)
                mid = ((fc[0] + pc[0]) // 2, (fc[1] + pc[1]) // 2)
                txt = "PELIGRO" if pr["critical"] else f"{pr['gap']:.0f}%"
                cv2.putText(frame, txt, mid, cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            col, 2, cv2.LINE_AA)
            # pasillos que deben estar libres + pallets que los bloquean
            for ai in a.aisles:
                col = RED if ai["blocked"] else (40, 190, 235)
                cv2.polylines(frame, [ai["poly"]], True, col, 2)
                p0 = ai["poly"][0]
                estado = "OBSTRUIDO" if ai["blocked"] else "libre"
                cv2.putText(frame, f"{ai['name']}: {estado}",
                            (int(p0[0]), int(p0[1]) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2, cv2.LINE_AA)
                for bb in ai["blockers"]:
                    x1, y1, x2, y2 = map(int, bb)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), RED, 3)
                    cv2.putText(frame, "OBSTRUYE", (x1, y1 - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, RED, 2, cv2.LINE_AA)

        # EPP: infracciones sin chaleco / sin casco (módulo seguridad)
        for box, c in a.ppe_boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), RED, 2)
            tag = ES[NAMES[c]]
            (tw, th2), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th2 - 6), (x1 + tw + 6, y1), RED, -1)
            cv2.putText(frame, tag, (x1 + 3, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1, cv2.LINE_AA)

        # PERSONA CAÍDA (se dibuja en todos los módulos: es crítico)
        flash = int(self.video_t * 4) % 2 == 0
        for tid, box in a.fallen_now:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), RED, 4 if flash else 2)
            cv2.putText(frame, f"CAIDA #{tid}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2, cv2.LINE_AA)

        # MONTACARGAS RÁPIDO (etiqueta ámbar sobre la caja)
        if uc in ("seguridad", "trazabilidad") and a.speeding_now \
                and tracked is not None and len(tracked) \
                and tracked.tracker_id is not None:
            fast = {tid for tid, _v in a.speeding_now}
            for box, tid in zip(tracked.xyxy, tracked.tracker_id):
                if tid is not None and int(tid) in fast:
                    cv2.putText(frame, ">> RAPIDO", (int(box[0]), int(box[1]) - 24),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, AMBER, 2, cv2.LINE_AA)

        # INCENDIO: cajas de fuego/humo SIEMPRE (en cualquier módulo)
        flash_on = int(self.video_t * 4) % 2 == 0   # parpadeo ~2 Hz
        for box, c in a.fire_boxes:
            x1, y1, x2, y2 = map(int, box)
            col = COL[c]
            th = 4 if (c == FIRE and flash_on) else 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), col, th)
            tag = ES[NAMES[c]]
            (tw, thh), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - thh - 8), (x1 + tw + 8, y1), col, -1)
            cv2.putText(frame, tag, (x1 + 4, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2, cv2.LINE_AA)

        # HUD
        hud = (f"t {_fmt(self.video_t)} / {_fmt(self.duration)}   "
               f"pallets {a.pallets_now}  forklifts {a.forklifts_now}  "
               f"personas {a.persons_now}   {self.proc_fps:.1f} fps")
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 26), DARK, -1)
        cv2.putText(frame, hud, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (120, 230, 120), 1, cv2.LINE_AA)

        # BANNER de alarma de incendio (encima de todo, parpadea)
        if a.fire_active:
            h, w = frame.shape[:2]
            if flash_on:
                cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 60, 255), 10)
            band = frame[26:78, 0:w]
            red = np.full_like(band, (30, 30, 200))
            frame[26:78, 0:w] = cv2.addWeighted(band, 0.25, red, 0.75, 0)
            donde = f"  ·  {a.fire_zone}" if a.fire_zone else ""
            msg = f"!! ALERTA DE INCENDIO{donde}  ·  fuego {a.fire_now}  humo {a.smoke_now}"
            cv2.putText(frame, msg, (14, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.85, WHITE, 2, cv2.LINE_AA)

    # ── salidas ──
    def mjpeg_frames(self):
        while True:
            with self.lock:
                data = self.latest_jpeg
            if data is None:
                time.sleep(0.03)
                continue
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n")
            time.sleep(0.04)

    def status(self) -> dict:
        from . import detector as _det
        base = {
            "running": self.running, "finished": self.finished,
            "video": self.video, "usecase": self.usecase,
            "progress": round(self.progress, 4),
            "video_time": _fmt(self.video_t), "duration": _fmt(self.duration),
            "proc_fps": round(self.proc_fps, 1),
            "has_frame": self.latest_jpeg is not None,
            "model_ready": _det.is_warmed(),
            "active_models": sorted(getattr(self, "active_models", [])),
        }
        if self.analytics:
            base.update(self.analytics.snapshot())
        return base

    def export_csv(self) -> Path:
        if not self.analytics:
            raise RuntimeError("no hay analítica para exportar")
        snap = self.analytics.snapshot()
        out = config.data_abs / f"reporte_{Path(self.video).stem}.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["OMNI Logística — Reporte", self.video])
            wr.writerow([])
            wr.writerow(["RESUMEN"])
            wr.writerow(["Pallets (final)", snap["pallets_now"]])
            wr.writerow(["Montacargas únicos", snap["unique_forklifts"]])
            wr.writerow(["Personas únicas", snap["unique_persons"]])
            wr.writerow([])
            wr.writerow(["OCUPACIÓN POR ZONA"])
            wr.writerow(["Zona", "Pallets", "Capacidad", "%", "Estado"])
            for z in snap["zones"]:
                wr.writerow([z["name"], z["count"], z["capacity"], f"{z['pct']:.0f}",
                             z["status"]])
            wr.writerow([])
            wr.writerow(["MUELLE"])
            d = snap["dock"]
            wr.writerow(["Entradas (IN)", d["in"]])
            wr.writerow(["Salidas (OUT)", d["out"]])
            wr.writerow(["Piezas/min", d["throughput"]])
            wr.writerow([])
            wr.writerow(["SEGURIDAD"])
            wr.writerow(["Incidentes de proximidad", snap["safety"]["incidents"]])
            wr.writerow(["Personas caídas", snap["safety"]["falls_total"]])
            wr.writerow(["Excesos de velocidad", snap["safety"]["speed_events"]])
            wr.writerow(["Obstrucciones de pasillo", snap["safety"]["obstructions"]])
            wr.writerow(["Alarmas de incendio", snap["fire"]["events"]])
            wr.writerow([])
            wr.writerow(["ALERTAS"])
            wr.writerow(["Tiempo video", "Módulo", "Tipo", "Detalle", "Severidad"])
            for al in snap["alerts"]:
                wr.writerow([al["video_time"], al["modulo"], al["tipo"],
                             al["detalle"], al["severity"]])
        return out


processor = VideoProcessor()
