"""Analítica de logística por video — 4 módulos calculados a la vez.

Todo se mide sobre el *tiempo del video* (frame/fps) para ser correcto aunque el
procesamiento sea más lento/rápido que tiempo real.

  1. Ocupación por zona : cuenta pallets dentro de cada zona → % de llenado.
  2. Muelle carga/descarga: LineZone sobre pallets que cruzan → piezas/min.
  3. Seguridad forklift↔persona: proximidad peligrosa entre cajas → alertas.
  4. Trazabilidad de montacargas: tracking, estelas, heatmap, permanencia.
  +. Incendio (transversal): fuego/humo detectado en cualquier módulo →
     alarma crítica con zona afectada.
"""
from __future__ import annotations

import math

import cv2
import numpy as np
import supervision as sv

# Antes que nada: sin esto LineZone mata el hilo de procesamiento en
# cuanto alguien cruza la línea. Ver backend/compat.py.
from . import compat  # noqa: F401

from .config import config
from .detector import (ES, FIRE, FORKLIFT, NAMES, NO_HELMET, NO_VEST, PALLET,
                       PERSON, SMOKE)
from .zones import line_to_px, zone_to_px


class Analytics:
    def __init__(self, cfg_data: dict, w: int, h: int, fps: float):
        self.w, self.h, self.fps = w, h, max(1.0, fps)
        self.cur_t = 0.0

        # ── línea de muelle (conteo de pallets que cruzan) ──
        self.line_zone = None
        lp = line_to_px(cfg_data.get("line"), w, h)
        if lp:
            (ax, ay), (bx, by) = lp
            try:
                self.line_zone = sv.LineZone(
                    start=sv.Point(ax, ay), end=sv.Point(bx, by),
                    triggering_anchors=[sv.Position.CENTER])
            except TypeError:
                self.line_zone = sv.LineZone(start=sv.Point(ax, ay),
                                             end=sv.Point(bx, by))
        self.dock_in = 0
        self.dock_out = 0

        # ── zonas: almacenaje (ocupación) y pasillos (obstrucción) ──
        self.zones = []     # tipo 'ocupacion'
        self.aisles = []    # tipo 'pasillo' → ruta que debe estar LIBRE
        for z in cfg_data.get("zones", []):
            poly = zone_to_px(z, w, h)
            if len(poly) < 3:
                continue
            entry = {
                "id": z.get("id"), "name": z.get("name", "Zona"),
                "color": z.get("color", "#129A6B"), "poly": poly,
                "count": 0,                     # pallets ahora (suavizado)
                "capacity": config.zone_capacity,  # 0 = auto
                "expected": max(1, config.zone_capacity),
                "dwell": {},                    # tid(montacargas) -> segundos
                "present": set(),               # tids dentro ahora
            }
            if z.get("type") == "pasillo":
                entry["pallet_dwell"] = {}      # tid pallet -> seg quieto dentro
                entry["blocked"] = False
                entry["blockers"] = []          # cajas de pallets obstruyendo
                self.aisles.append(entry)
            else:
                self.zones.append(entry)

        # ── tracking / trazabilidad ──
        self.objects = {}          # tid -> {first,last,cls}
        self.object_zone = {}      # tid -> (zona, seg)  temporizador en pantalla

        # ── seguridad ──
        self.safety_incidents = 0
        self.safety_pairs = []     # pares peligrosos ahora
        self._pair_alerted = {}    # (fid,pid) -> último t alertado
        self.min_gap_frac = 1.0

        # ── caída de persona (man down) ──
        self._fall_time = {}       # tid -> seg acumulados "acostado"
        self._fall_alerted = set() # tids con alerta activa (hasta reincorporarse)
        self.fallen_now = []       # [(tid, box)] caídos ahora
        self.falls_total = 0

        # ── exceso de velocidad de montacargas ──
        self._last_pos = {}        # tid -> (cx, cy, t)
        self._speed = {}           # tid -> velocidad EMA (frac ancho/seg)
        self._speed_alerted = {}   # tid -> último t alertado
        self.speeding_now = []     # [(tid, vel)] rápidos ahora
        self.speed_events = 0

        # ── obstrucción de pasillos ──
        self.obstructions = 0
        self._obstruct_alerted = set()   # (zone_id, tid)

        # ── EPP: infracciones (sin chaleco / sin casco) ──
        self.ppe_boxes = []              # [(box, cls)] infracciones ahora
        self.ppe_events = 0
        self._ppe_last_alert = -1e9

        # ── incendio (transversal a todos los módulos) ──
        self.fire_now = 0            # detecciones de fuego en el frame
        self.smoke_now = 0
        self.fire_boxes = []         # cajas actuales para dibujar
        self.fire_active = False     # con histéresis (frames consecutivos)
        self._fire_streak = 0
        self.fire_events = 0         # alarmas emitidas
        self._fire_last_alert = -1e9
        self.fire_zone = None        # zona donde se ve el fuego

        # ── heatmap de rutas (montacargas) ──
        self.heat_scale = 8
        self.heat = np.zeros((max(1, h // self.heat_scale),
                              max(1, w // self.heat_scale)), dtype=np.float32)

        # ── conteos instantáneos ──
        self.pallets_now = self.forklifts_now = self.persons_now = 0

        # ── timeline + alertas ──
        self.timeline = []
        self._last_sample = -1
        self.alerts = []
        self._zone_state = {}      # id -> estado ocupación
        self._dwell_alerted = set()

    # ── helpers ──
    def _add_alert(self, t, modulo, tipo, detalle, severity):
        self.alerts.append({"t": round(t, 1), "video_time": _fmt(t),
                            "modulo": modulo, "tipo": tipo,
                            "detalle": detalle, "severity": severity})

    @staticmethod
    def _center(box):
        return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)

    def _split(self, dets):
        """Devuelve dict cls -> lista de (box, tid) de un sv.Detections."""
        out = {PERSON: [], FORKLIFT: [], PALLET: [], FIRE: [], SMOKE: [],
               NO_VEST: [], NO_HELMET: []}
        if dets is None or len(dets) == 0:
            return out
        tids = dets.tracker_id if dets.tracker_id is not None else [None] * len(dets)
        for box, cid, tid in zip(dets.xyxy, dets.class_id, tids):
            c = int(cid)
            if c in out:
                out[c].append((box, None if tid is None else int(tid)))
        return out

    # ── actualización por frame ──
    def update(self, raw, tracked, frame_bgr, video_t: float, dt: float):
        self.cur_t = video_t
        rsplit = self._split(raw)
        tsplit = self._split(tracked)

        self.pallets_now = len(rsplit[PALLET])
        self.forklifts_now = len(rsplit[FORKLIFT])
        self.persons_now = len(rsplit[PERSON])

        # ── INCENDIO (siempre activo, en todos los módulos) ──
        # doble validación anti-falsos: el fuego real tiene núcleo BRILLANTE
        # (objetos naranjas mate — máquinas, chalecos — no pasan el filtro)
        fire_ok = [(box, tid) for box, tid in rsplit[FIRE]
                   if _fire_brightness_ok(frame_bgr, box)]
        self.fire_now = len(fire_ok)
        self.smoke_now = len(rsplit[SMOKE])
        self.fire_boxes = [(box, FIRE) for box, _ in fire_ok] + \
                          [(box, SMOKE) for box, _ in rsplit[SMOKE]]
        if self.fire_now or self.smoke_now:
            self._fire_streak += 1
        else:
            self._fire_streak = max(0, self._fire_streak - 2)
        # histéresis: 3 frames seguidos encienden la alarma (evita falsos por 1 frame)
        self.fire_active = self._fire_streak >= 3
        if self.fire_active:
            # ¿en qué zona está el fuego?
            self.fire_zone = None
            for box, _c in self.fire_boxes:
                cen = self._center(box)
                for z in self.zones:
                    if cv2.pointPolygonTest(z["poly"], cen, False) >= 0:
                        self.fire_zone = z["name"]
                        break
                if self.fire_zone:
                    break
            if video_t - self._fire_last_alert >= config.fire_realert_sec:
                self._fire_last_alert = video_t
                self.fire_events += 1
                donde = f" en {self.fire_zone}" if self.fire_zone else ""
                tipo = "FUEGO detectado" if self.fire_now else "HUMO detectado"
                self._add_alert(video_t, "Incendio", tipo,
                                f"{tipo}{donde} — evacuar y verificar",
                                "critical")
        else:
            self.fire_zone = None

        # ── HEATMAP de rutas (montacargas; decae lento) ──
        self.heat *= 0.999
        hs = self.heat_scale
        for box, _tid in tsplit[FORKLIFT]:
            cx = int(((box[0] + box[2]) / 2) // hs)
            cy = int(((box[1] + box[3]) / 2) // hs)
            if 0 <= cy < self.heat.shape[0] and 0 <= cx < self.heat.shape[1]:
                y0, y1 = max(0, cy - 1), min(self.heat.shape[0], cy + 2)
                x0, x1 = max(0, cx - 1), min(self.heat.shape[1], cx + 2)
                self.heat[y0:y1, x0:x1] += 0.35
                self.heat[cy, cx] += 0.9

        # ── TRAZABILIDAD: registrar tracks ──
        if tracked is not None and len(tracked) and tracked.tracker_id is not None:
            for box, cid, tid in zip(tracked.xyxy, tracked.class_id, tracked.tracker_id):
                if tid is None:
                    continue
                tid = int(tid)
                o = self.objects.get(tid)
                if o is None:
                    self.objects[tid] = {"first": video_t, "last": video_t,
                                         "cls": int(cid)}
                else:
                    o["last"] = video_t
                    o["cls"] = int(cid)

        # ── OCUPACIÓN + permanencia por zona ──
        self.object_zone = {}
        for z in self.zones:
            # pallets dentro (conteo suavizado para evitar parpadeo)
            cnt = sum(1 for box, _ in rsplit[PALLET]
                      if cv2.pointPolygonTest(z["poly"], self._center(box), False) >= 0)
            z["count"] = int(round(0.5 * z["count"] + 0.5 * cnt))
            if config.zone_capacity <= 0:
                z["expected"] = max(z["expected"], z["count"], 1)
            cap = z["expected"] if config.zone_capacity <= 0 else config.zone_capacity
            z["capacity"] = cap
            z["pct"] = max(0.0, min(100.0, 100.0 * z["count"] / max(1, cap)))
            self._eval_zone(z, video_t)

            # permanencia de montacargas en la zona (trazabilidad)
            present = set()
            for box, tid in tsplit[FORKLIFT]:
                if tid is not None and cv2.pointPolygonTest(
                        z["poly"], self._center(box), False) >= 0:
                    present.add(tid)
                    z["dwell"][tid] = z["dwell"].get(tid, 0.0) + dt
                    self.object_zone[tid] = (z["name"], z["dwell"][tid])
                    if (z["dwell"][tid] >= config.dwell_alert_sec
                            and (z["id"], tid) not in self._dwell_alerted):
                        self._dwell_alerted.add((z["id"], tid))
                        self._add_alert(video_t, "Trazabilidad",
                                        "Permanencia excesiva",
                                        f"Montacargas ID {tid} lleva "
                                        f"{_fmt(z['dwell'][tid])} en {z['name']}",
                                        "warning")
            z["present"] = present

        # ── MUELLE: pallets Y montacargas que cruzan la línea ──
        # (se cuentan ambos: la carga suele cruzar montada en el montacargas
        #  y el pallet solo a veces se detecta durante el cruce)
        if self.line_zone is not None and tracked is not None and len(tracked) \
                and tracked.tracker_id is not None:
            idx = [i for i, (c, t) in enumerate(zip(tracked.class_id,
                                                    tracked.tracker_id))
                   if int(c) in (PALLET, FORKLIFT) and t is not None]
            if idx:
                try:
                    self.line_zone.trigger(tracked[idx])
                except Exception:
                    pass
                self.dock_in = int(self.line_zone.in_count)
                self.dock_out = int(self.line_zone.out_count)

        # ── SEGURIDAD: proximidad forklift ↔ persona ──
        self.safety_pairs = []
        self.min_gap_frac = 1.0
        danger = config.safe_dist_frac
        for fbox, ftid in tsplit[FORKLIFT]:
            for pbox, ptid in tsplit[PERSON]:
                gap = _box_gap(fbox, pbox) / self.w
                self.min_gap_frac = min(self.min_gap_frac, gap)
                if gap <= danger:
                    crit = gap <= 0.0
                    self.safety_pairs.append({
                        "f": ftid, "p": ptid,
                        "fc": self._center(fbox), "pc": self._center(pbox),
                        "gap": round(gap * 100, 1), "critical": crit})
                    key = (ftid, ptid)
                    last = self._pair_alerted.get(key, -1e9)
                    if video_t - last >= config.safety_realert_sec:
                        self._pair_alerted[key] = video_t
                        self.safety_incidents += 1
                        self._add_alert(
                            video_t, "Seguridad",
                            "Contacto crítico" if crit else "Proximidad peligrosa",
                            f"Montacargas ID {ftid} y Persona ID {ptid} "
                            f"a {gap*100:.0f}% de distancia",
                            "critical" if crit else "warning")

        # ── CAÍDA DE PERSONA (man down): caja "acostada" sostenida ──
        self.fallen_now = []
        seen_p = set()
        for box, tid in tsplit[PERSON]:
            if tid is None:
                continue
            seen_p.add(tid)
            bw, bh = box[2] - box[0], box[3] - box[1]
            if bh > 0 and bw / bh >= config.fall_ratio:
                self._fall_time[tid] = self._fall_time.get(tid, 0.0) + dt
                if self._fall_time[tid] >= config.fall_sec:
                    self.fallen_now.append((tid, box))
                    if tid not in self._fall_alerted:
                        self._fall_alerted.add(tid)
                        self.falls_total += 1
                        self._add_alert(video_t, "Seguridad", "PERSONA CAÍDA",
                                        f"Persona ID {tid} en el piso — "
                                        "verificar de inmediato", "critical")
            else:
                self._fall_time[tid] = 0.0
                self._fall_alerted.discard(tid)   # se reincorporó
        for tid in list(self._fall_time):
            if tid not in seen_p:
                self._fall_time.pop(tid, None)

        # ── EXCESO DE VELOCIDAD de montacargas ──
        self.speeding_now = []
        for box, tid in tsplit[FORKLIFT]:
            if tid is None:
                continue
            cx, cy = self._center(box)
            prev = self._last_pos.get(tid)
            self._last_pos[tid] = (cx, cy, video_t)
            if prev is None:
                continue
            pdt = video_t - prev[2]
            if pdt <= 0:
                continue
            v = math.hypot(cx - prev[0], cy - prev[1]) / pdt / self.w
            ema = self._speed.get(tid, v)
            ema = 0.7 * ema + 0.3 * v
            self._speed[tid] = ema
            if ema >= config.speed_limit_frac:
                self.speeding_now.append((tid, ema))
                last = self._speed_alerted.get(tid, -1e9)
                if video_t - last >= config.safety_realert_sec:
                    self._speed_alerted[tid] = video_t
                    self.speed_events += 1
                    self._add_alert(video_t, "Seguridad", "Velocidad excesiva",
                                    f"Montacargas ID {tid} a "
                                    f"{ema/config.speed_limit_frac:.1f}x el límite",
                                    "warning")

        # ── OBSTRUCCIÓN de pasillos (pallet quieto en ruta que debe estar libre) ──
        for ai in self.aisles:
            blockers = []
            inside_now = set()
            for box, tid in tsplit[PALLET]:
                if tid is None:
                    continue
                if cv2.pointPolygonTest(ai["poly"], self._center(box), False) >= 0:
                    inside_now.add(tid)
                    ai["pallet_dwell"][tid] = ai["pallet_dwell"].get(tid, 0.0) + dt
                    if ai["pallet_dwell"][tid] >= config.obstruct_sec:
                        blockers.append(box)
                        if (ai["id"], tid) not in self._obstruct_alerted:
                            self._obstruct_alerted.add((ai["id"], tid))
                            self.obstructions += 1
                            self._add_alert(
                                video_t, "Seguridad", "Pasillo obstruido",
                                f"Pallet ID {tid} bloquea {ai['name']} hace "
                                f"{_fmt(ai['pallet_dwell'][tid])}", "critical")
            # limpiar pallets que ya no están en el pasillo
            for tid in list(ai["pallet_dwell"]):
                if tid not in inside_now:
                    ai["pallet_dwell"].pop(tid, None)
                    self._obstruct_alerted.discard((ai["id"], tid))
            ai["blockers"] = blockers
            ai["blocked"] = bool(blockers)

        # ── EPP: infracciones sin chaleco / sin casco ──
        self.ppe_boxes = [(box, NO_VEST) for box, _ in rsplit[NO_VEST]] + \
                         [(box, NO_HELMET) for box, _ in rsplit[NO_HELMET]]
        if self.ppe_boxes and video_t - self._ppe_last_alert >= config.ppe_realert_sec:
            self._ppe_last_alert = video_t
            self.ppe_events += 1
            nv, nh = len(rsplit[NO_VEST]), len(rsplit[NO_HELMET])
            det = " y ".join(x for x in [f"{nv} sin chaleco" if nv else "",
                                         f"{nh} sin casco" if nh else ""] if x)
            self._add_alert(video_t, "Seguridad", "EPP incompleto",
                            f"Personal {det} en la escena", "warning")

        # ── timeline (1 muestra/seg de video) ──
        sec = int(video_t)
        if sec != self._last_sample:
            self._last_sample = sec
            self.timeline.append({"t": sec, "pallets": self.pallets_now,
                                  "forklifts": self.forklifts_now,
                                  "persons": self.persons_now,
                                  "in": self.dock_in, "out": self.dock_out,
                                  "events": len(self.alerts)})

    def _eval_zone(self, z, video_t):
        pct = z["pct"]
        if pct >= config.occ_critical_pct:
            state = "critical"
        elif pct >= config.occ_warning_pct:
            state = "warning"
        else:
            state = "ok"
        prev = self._zone_state.get(z["id"])
        if state != prev and state in ("warning", "critical"):
            self._add_alert(
                video_t, "Ocupación",
                "Zona llena" if state == "critical" else "Zona casi llena",
                f"{z['name']} al {pct:.0f}% ({z['count']}/{z['capacity']} pallets)",
                state)
        self._zone_state[z["id"]] = state

    # ── snapshot para el dashboard ──
    def snapshot(self) -> dict:
        zones_out = [{
            "id": z["id"], "name": z["name"], "color": z["color"],
            "count": z["count"], "capacity": z["capacity"],
            "free": max(0, z["capacity"] - z["count"]),
            "pct": round(z.get("pct", 0.0), 1),
            "status": self._zone_state.get(z["id"], "ok"),
            "forklifts_now": len(z["present"]),
            "dwell_avg": _fmt(sum(z["dwell"].values()) / len(z["dwell"]))
            if z["dwell"] else "0s",
        } for z in self.zones]

        video_min = max(1e-6, self.cur_t / 60.0)
        total_cross = self.dock_in + self.dock_out
        dock = {"in": self.dock_in, "out": self.dock_out,
                "net": self.dock_in - self.dock_out,
                "total": total_cross,
                "throughput": round(total_cross / video_min, 1),
                "enabled": self.line_zone is not None}

        if self.fallen_now or any(a["blocked"] for a in self.aisles):
            risk = "critical"
        elif self.safety_pairs:
            risk = "critical" if any(p["critical"] for p in self.safety_pairs) else "warning"
        elif self.speeding_now:
            risk = "warning"
        else:
            risk = "ok"
        safety = {"incidents": self.safety_incidents, "risk": risk,
                  "pairs_now": len(self.safety_pairs),
                  "min_gap": round(self.min_gap_frac * 100, 1),
                  "danger_pct": round(config.safe_dist_frac * 100, 1),
                  "falls_total": self.falls_total,
                  "fallen_now": len(self.fallen_now),
                  "speeding_now": len(self.speeding_now),
                  "speed_events": self.speed_events,
                  "obstructions": self.obstructions,
                  "aisles_blocked": sum(1 for a in self.aisles if a["blocked"]),
                  "ppe_now": len(self.ppe_boxes),
                  "ppe_events": self.ppe_events}
        aisles_out = [{"id": a["id"], "name": a["name"], "color": a["color"],
                       "blocked": a["blocked"],
                       "blockers": len(a["blockers"])} for a in self.aisles]

        # objetos activos (vistos en el último ~segundo)
        active = []
        for tid, o in self.objects.items():
            if self.cur_t - o["last"] > 1.0:
                continue
            name = NAMES.get(o["cls"], "?")
            zname = next((z["name"] for z in self.zones if tid in z["present"]), None)
            dwell = sum(z["dwell"].get(tid, 0.0) for z in self.zones)
            active.append({"id": tid, "cls": name, "cls_es": ES.get(name, name),
                           "zone": zname, "dwell_sec": round(dwell, 1),
                           "dwell": _fmt(dwell),
                           "seen": _fmt(o["last"] - o["first"])})
        active.sort(key=lambda x: (x["cls"] != "forklift", -x["dwell_sec"]))

        uniq_f = sum(1 for o in self.objects.values() if o["cls"] == FORKLIFT)
        uniq_p = sum(1 for o in self.objects.values() if o["cls"] == PERSON)

        return {
            "pallets_now": self.pallets_now,
            "forklifts_now": self.forklifts_now,
            "persons_now": self.persons_now,
            "fire": {"active": self.fire_active, "fire_now": self.fire_now,
                     "smoke_now": self.smoke_now, "events": self.fire_events,
                     "zone": self.fire_zone},
            "unique_forklifts": uniq_f,
            "unique_persons": uniq_p,
            "zones": zones_out,
            "aisles": aisles_out,
            "dock": dock,
            "safety": safety,
            "active_objects": active[:40],
            "active_count": len(active),
            "timeline": self.timeline[-600:],
            "alerts": self.alerts[-100:],
        }


def _fire_brightness_ok(frame_bgr, box, min_bright=210, min_frac=0.10) -> bool:
    """Fuego real = núcleo brillante (píxeles casi blancos/amarillos).

    Rechaza objetos naranjas mate (máquinas, conos, chalecos) que el modelo
    confunde: exige que ≥6% del recorte tenga brillo ≥210.
    """
    x1, y1, x2, y2 = (int(v) for v in box)
    h, w = frame_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 - x1 < 4 or y2 - y1 < 4:
        return False
    roi = frame_bgr[y1:y2, x1:x2]
    v = roi.max(axis=2)          # brillo aprox (canal máximo)
    return float((v >= min_bright).mean()) >= min_frac


def _box_gap(a, b) -> float:
    """Distancia euclídea entre dos cajas (0 si se solapan)."""
    dx = max(0.0, max(a[0] - b[2], b[0] - a[2]))
    dy = max(0.0, max(a[1] - b[3], b[1] - a[3]))
    return math.hypot(dx, dy)


def _fmt(sec: float) -> str:
    sec = int(round(sec))
    m, s = divmod(sec, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s" if m else f"{s}s"
