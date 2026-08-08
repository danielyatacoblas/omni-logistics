"""Detector combinado de logística → detecciones Supervision unificadas.

Cada APARTADO (caso de uso) activa SOLO los modelos que necesita:

  apartado       modelos activos por defecto
  ─────────────  ─────────────────────────────────────────────
  ocupacion      pallet
  muelle         pallet + forklift
  seguridad      forklift + fire + ppe (chaleco/casco)
  trazabilidad   forklift

El usuario puede sobreescribir la selección desde la UI (config ⚙).

Clases unificadas:
  0=person · 1=forklift · 2=pallet · 3=fire · 4=smoke ·
  5=no_vest (sin chaleco) · 6=no_helmet (sin casco)
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import supervision as sv

from .config import config

if config.device.lower() == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

ROOT = Path(__file__).resolve().parent.parent

# clase unificada -> id / nombre
PERSON, FORKLIFT, PALLET, FIRE, SMOKE, NO_VEST, NO_HELMET = 0, 1, 2, 3, 4, 5, 6
NAMES = {PERSON: "person", FORKLIFT: "forklift", PALLET: "pallet",
         FIRE: "fire", SMOKE: "smoke",
         NO_VEST: "no_vest", NO_HELMET: "no_helmet"}
ES = {"person": "Persona", "forklift": "Montacargas", "pallet": "Pallet",
      "fire": "FUEGO", "smoke": "HUMO",
      "no_vest": "SIN CHALECO", "no_helmet": "SIN CASCO"}

# modelos disponibles (clave -> descripción para la UI)
MODEL_INFO = {
    "pallet":   {"label": "Pallets", "desc": "YOLO11n · pallets de madera"},
    "forklift": {"label": "Montacargas + Personas", "desc": "YOLOv8m keremberke"},
    "fire":     {"label": "Fuego / Humo", "desc": "YOLOv8n + filtro de brillo"},
    "ppe":      {"label": "EPP: chaleco y casco", "desc": "CSS · detecta infracciones"},
}

# modelos por defecto de cada apartado
MODULE_MODELS = {
    "ocupacion":    ["pallet"],
    "muelle":       ["pallet", "forklift"],
    "seguridad":    ["forklift", "fire", "ppe"],
    "trazabilidad": ["forklift"],
}


def _canon(name: str) -> int:
    n = name.lower()
    if "pallet" in n:
        return PALLET
    if "fork" in n or "lift" in n or "montac" in n:
        return FORKLIFT
    if n in ("person", "people", "human"):
        return PERSON
    if "fire" in n or "flame" in n or "fuego" in n:
        return FIRE
    if "smoke" in n or "humo" in n:
        return SMOKE
    return -1


def _canon_ppe(name: str) -> int:
    """Del modelo EPP solo interesan las INFRACCIONES (NO-...)."""
    n = name.lower()
    if "no-safety vest" in n or "no-vest" in n or n == "no_vest":
        return NO_VEST
    if "no-hardhat" in n or "no-helmet" in n or n == "no_helmet":
        return NO_HELMET
    return -1


def _dev():
    import torch
    return 0 if (config.device.lower().startswith("cuda")
                 and torch.cuda.is_available()) else "cpu"


def _round_res(x: int, base: int = 32) -> int:
    return int(round(max(base * 7, int(x)) / base) * base)


class LogiDetector:
    """Corre SOLO los modelos activos y fusiona a clases unificadas."""

    def __init__(self):
        from ultralytics import YOLO
        self.device = _dev()
        self.half = bool(config.half) and self.device != "cpu"
        self.resolution = _round_res(config.work_res)
        self._paths = {
            "pallet": self._path(config.pallet_model),
            "forklift": self._path(config.forklift_model),
            "fire": self._path(config.fire_model),
            "ppe": self._path(config.ppe_model),
        }
        self._yolo = YOLO
        self._models: dict[str, object] = {}     # carga perezosa por clave
        self.object_mode = False
        self._fire_cache = None
        self._fire_tick = 0

    @staticmethod
    def _path(rel: str) -> str:
        p = Path(rel)
        if not p.is_absolute():
            p = ROOT / rel
        return str(p) if p.exists() else rel

    def _model(self, key: str):
        if key not in self._models:
            self._models[key] = self._yolo(self._paths[key])
        return self._models[key]

    def available(self) -> dict:
        """Qué modelos tienen pesos en disco (para la UI)."""
        return {k: Path(v).exists() for k, v in self._paths.items()}

    def _run(self, key: str, frame, conf, canon=_canon):
        r = self._model(key).predict(frame, conf=conf, device=self.device,
                                     imgsz=self.resolution, half=self.half,
                                     verbose=False)[0]
        d = sv.Detections.from_ultralytics(r)
        if d is None or len(d) == 0:
            return None
        model_names = r.names
        uni = np.array([canon(model_names[int(c)]) for c in d.class_id])
        keep = uni >= 0
        d = d[keep]
        if len(d) == 0:
            return None
        uni = uni[keep]
        d.class_id = uni
        d.data["class_name"] = np.array([NAMES[int(u)] for u in uni])
        return d

    def infer(self, frame, conf: float, active=None) -> sv.Detections:
        """active = iterable de claves de MODEL_INFO; None = todos."""
        act = set(active) if active else set(MODEL_INFO)
        parts = []
        if "pallet" in act:
            d = self._run("pallet", frame, min(conf, config.pallet_conf))
            if d is not None:
                parts.append(d)
        if "forklift" in act:
            d = self._run("forklift", frame, conf)
            if d is not None:
                parts.append(d)
        if "fire" in act:
            # el fuego cambia lento: cada FIRE_EVERY frames, cacheado
            if self._fire_tick % max(1, config.fire_every) == 0:
                self._fire_cache = self._run("fire", frame, config.fire_conf)
            self._fire_tick += 1
            if self._fire_cache is not None:
                parts.append(self._fire_cache)
        else:
            self._fire_cache = None
        if "ppe" in act:
            d = self._run("ppe", frame, config.ppe_conf, canon=_canon_ppe)
            if d is not None:
                parts.append(d)
        if not parts:
            return sv.Detections.empty()
        merged = sv.Detections.merge(parts) if len(parts) > 1 else parts[0]
        try:
            merged = merged.with_nms(threshold=config.nms_iou, class_agnostic=False)
        except Exception:
            pass
        return merged


# ── caché + estado "warmed" ──
_instance: LogiDetector | None = None
_warmed = False


def get_detector() -> LogiDetector:
    global _instance
    if _instance is None:
        _instance = LogiDetector()
    return _instance


def mark_warmed():
    global _warmed
    _warmed = True


def is_warmed() -> bool:
    return _warmed
