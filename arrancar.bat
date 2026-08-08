@echo off
REM ── OMNI Logística — ApexCorp ──
REM Doble clic para arrancar el dashboard. Se abre en http://localhost:8021
cd /d "%~dp0"
set PYTHONUTF8=1
start "" http://localhost:8021
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8021
pause
