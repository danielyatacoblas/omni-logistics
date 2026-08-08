"""Carga de configuración desde .env — OMNI Logística (almacén / muelle)."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _f(key, default):
    return float(os.getenv(key, default))


def _i(key, default):
    return int(os.getenv(key, default))


def _b(key, default):
    return os.getenv(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Config:
    # ── modelos (se corren combinados en un mismo frame) ──
    pallet_model: str = os.getenv("PALLET_MODEL", "weights/pallet_n_640.pt")
    forklift_model: str = os.getenv("FORKLIFT_MODEL", "weights/forklift_kerem.pt")
    fire_model: str = os.getenv("FIRE_MODEL", "weights/fire_smoke.pt")
    fire_conf: float = _f("FIRE_CONF", 0.50)
    fire_realert_sec: float = _f("FIRE_REALERT_SEC", 6.0)
    ppe_model: str = os.getenv("PPE_MODEL", "weights/ppe_vest.pt")
    ppe_conf: float = _f("PPE_CONF", 0.40)
    ppe_realert_sec: float = _f("PPE_REALERT_SEC", 8.0)
    device: str = os.getenv("DEVICE", "cuda")
    half: bool = _b("HALF", True)          # FP16 en CUDA (~40% más rápido)
    fire_every: int = _i("FIRE_EVERY", 3)  # correr el modelo de fuego cada N frames
    work_res: int = _i("WORK_RES", 640)
    default_conf: float = _f("DEFAULT_CONF", 0.35)
    pallet_conf: float = _f("PALLET_CONF", 0.30)   # los pallets suelen puntuar más bajo
    nms_iou: float = _f("NMS_IOU", 0.6)

    # ── tracking (ByteTrack) ──
    track_activation: float = _f("TRACK_ACTIVATION", 0.25)
    track_lost_buffer: int = _i("TRACK_LOST_BUFFER", 60)
    track_min_match: float = _f("TRACK_MIN_MATCH", 0.80)

    # ── reglas por módulo ──
    # ocupación: umbrales de % de llenado de una zona de almacenaje
    occ_warning_pct: float = _f("OCC_WARNING_PCT", 85)
    occ_critical_pct: float = _f("OCC_CRITICAL_PCT", 100)
    zone_capacity: int = _i("ZONE_CAPACITY", 0)   # 0 = auto (máximo observado)
    # seguridad: distancia mínima forklift↔persona (fracción del ancho del frame)
    safe_dist_frac: float = _f("SAFE_DIST_FRAC", 0.07)
    safety_realert_sec: float = _f("SAFETY_REALERT_SEC", 4.0)
    # caída de persona: caja "acostada" (ancho > alto*ratio) sostenida N seg
    fall_ratio: float = _f("FALL_RATIO", 1.15)
    fall_sec: float = _f("FALL_SEC", 1.2)
    # velocidad de montacargas: fracción del ancho del frame por segundo
    speed_limit_frac: float = _f("SPEED_LIMIT_FRAC", 0.22)
    # obstrucción: pallet quieto en zona tipo "pasillo" más de N seg
    obstruct_sec: float = _f("OBSTRUCT_SEC", 8.0)
    # trazabilidad: permanencia excesiva de un montacargas en una zona
    dwell_alert_sec: float = _f("DWELL_ALERT_SEC", 120)

    # ── procesamiento ──
    # 0 = automático: procesa ~30 fps efectivos (videos 60fps → stride 2)
    frame_stride: int = _i("FRAME_STRIDE", 0)
    max_width: int = _i("MAX_WIDTH", 1280)
    jpeg_quality: int = _i("JPEG_QUALITY", 80)

    # ── servidor ──
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = _i("PORT", 8021)
    videos_dir: str = os.getenv("VIDEOS_DIR", "videos")
    data_dir: str = os.getenv("DATA_DIR", "data")

    @property
    def videos_abs(self) -> Path:
        p = Path(self.videos_dir)
        return p if p.is_absolute() else ROOT / p

    @property
    def data_abs(self) -> Path:
        p = Path(self.data_dir)
        return p if p.is_absolute() else ROOT / p


config = Config()
config.data_abs.mkdir(parents=True, exist_ok=True)
config.videos_abs.mkdir(parents=True, exist_ok=True)
