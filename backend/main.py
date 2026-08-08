"""Servidor FastAPI — OMNI Logística (ocupación, muelle, seguridad, trazabilidad).

Rutas:
  GET  /                       -> dashboard
  GET  /api/videos             -> lista de videos + config
  GET  /api/video/{n}/meta     -> metadatos
  GET  /api/video/{n}/frame    -> primer frame JPEG (editor de zonas)
  GET  /api/video/{n}/zones    -> zonas/línea guardadas
  POST /api/video/{n}/zones    -> guarda zonas/línea
  POST /api/start              -> inicia {video, conf, usecase}
  POST /api/stop               -> detiene
  GET  /stream                 -> MJPEG anotado
  GET  /api/status             -> snapshot de estadísticas reales
  GET  /api/export             -> descarga CSV
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import (FileResponse, JSONResponse, Response,
                               StreamingResponse)
from fastapi.staticfiles import StaticFiles

from .config import config
from .processor import processor
from .zones import load_config, save_config

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
VIDEO_EXT = (".mp4", ".avi", ".mov", ".mkv", ".webm")

app = FastAPI(title="OMNI Logística — MVP")


@app.on_event("startup")
def _warmup():
    """Precarga el detector combinado en segundo plano (evita arranque en frío)."""
    import threading

    def _load():
        import numpy as np
        from .detector import get_detector, mark_warmed
        dummy = np.zeros((720, 1280, 3), dtype=np.uint8)
        try:
            d = get_detector()
            d.infer(dummy, config.default_conf)
            d.infer(dummy, config.default_conf)
            mark_warmed()
            print("[warmup] detector combinado precargado y listo")
        except Exception as e:
            print(f"[warmup] no se pudo precargar: {e}")

    threading.Thread(target=_load, daemon=True).start()


# carpeta de videos por apartado (caso de uso)
UC_DIR = {"ocupacion": "01_ocupacion", "muelle": "02_muelle",
          "seguridad": "03_seguridad", "trazabilidad": "04_trazabilidad"}


@app.get("/api/videos")
def list_videos(usecase: str = ""):
    """Videos del apartado (su carpeta) + los sueltos en videos/."""
    dirs = [config.videos_abs]
    sub = UC_DIR.get(usecase)
    if sub and (config.videos_abs / sub).exists():
        dirs.insert(0, config.videos_abs / sub)
    vids = []
    for d in dirs:
        for f in sorted(d.iterdir()):
            if f.is_file() and f.suffix.lower() in VIDEO_EXT:
                rel = str(f.relative_to(config.videos_abs)).replace("\\", "/")
                vids.append(rel)
    return {"videos": vids, "default_conf": config.default_conf,
            "device": config.device,
            "safe_dist_pct": round(config.safe_dist_frac * 100, 1)}


@app.get("/api/models")
def list_models():
    """Modelos disponibles + activos por defecto en cada apartado."""
    from .detector import MODEL_INFO, MODULE_MODELS, get_detector
    avail = get_detector().available()
    return {"models": [{"key": k, **v, "available": avail.get(k, False)}
                       for k, v in MODEL_INFO.items()],
            "defaults": MODULE_MODELS}


def _vpath(name: str) -> Path:
    p = (config.videos_abs / name).resolve()
    # el nombre puede incluir subcarpeta (01_ocupacion/x.mp4); nunca salir de videos/
    if config.videos_abs.resolve() not in p.parents and p != config.videos_abs.resolve():
        return config.videos_abs / "_invalido_"
    return p


@app.get("/api/video/{name:path}/meta")
def video_meta(name: str):
    p = _vpath(name)
    if not p.exists():
        return JSONResponse({"error": "video no encontrado"}, status_code=404)
    return processor.video_meta(str(p))


@app.get("/api/video/{name:path}/frame")
def video_frame(name: str):
    p = _vpath(name)
    if not p.exists():
        return JSONResponse({"error": "video no encontrado"}, status_code=404)
    jpg = processor.first_frame_jpeg(str(p))
    if jpg is None:
        return JSONResponse({"error": "no se pudo leer el frame"}, status_code=400)
    return Response(content=jpg, media_type="image/jpeg")


@app.get("/api/video/{name:path}/zones")
def get_zones(name: str):
    return load_config(name)


@app.post("/api/video/{name:path}/zones")
async def set_zones(name: str, request: Request):
    data = await request.json()
    return save_config(name, data)


@app.post("/api/start")
async def start(request: Request):
    body = await request.json()
    name = body.get("video")
    conf = float(body.get("conf", config.default_conf))
    usecase = body.get("usecase") or "ocupacion"
    models = body.get("models") or None   # selección de la UI (config ⚙)
    p = _vpath(name) if name else None
    if not p or not p.exists():
        return JSONResponse({"error": "video no encontrado"}, status_code=404)
    try:
        processor.start(str(p), name, conf, usecase, models)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return {"ok": True, "video": name, "usecase": usecase,
            "models": sorted(processor.active_models)}


@app.post("/api/stop")
def stop():
    processor.stop()
    return {"ok": True}


@app.get("/stream")
def stream():
    return StreamingResponse(
        processor.mjpeg_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/status")
def status():
    return processor.status()


@app.get("/api/export")
def export():
    try:
        out = processor.export_csv()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return FileResponse(str(out), media_type="text/csv", filename=out.name)


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
