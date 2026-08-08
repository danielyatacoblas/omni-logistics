# OMNI Logistics — MVP de visión para almacén y muelle (ApexCorp)

> **Visión computacional · YOLO + ByteTrack · FastAPI · CPU o GPU**

Estado: **v0.1.0 · prototipo funcional sobre video real de almacén.**

Dashboard que mira el video de las cámaras de un almacén y responde cuatro
preguntas que hoy se contestan a ojo o no se contestan:

| Módulo | Qué responde | Con qué |
|---|---|---|
| **Ocupación** | ¿Cuánto de cada zona está ocupado y desde cuándo? | Pallets detectados dentro de polígonos dibujados |
| **Muelle** | ¿Cuánto tarda una carga o descarga? | Montacargas y pallets entrando y saliendo del área de muelle |
| **Seguridad** | ¿Hay fuego, humo o gente sin EPP cerca de un montacargas? | Fuego/humo con filtro de brillo, y chaleco/casco |
| **Trazabilidad** | ¿Por dónde pasó cada montacargas y cuánto tardó? | Seguimiento con ByteTrack y cruce de líneas |

Las cifras salen del procesamiento real del video, no de datos simulados.

## Probarlo

```bash
pip install -r requirements.txt
python download_models.py          # dice qué pesos faltan y descarga los públicos
./arrancar.bat                     # o: python -m uvicorn backend.main:app --port 8010
```

Abre <http://localhost:8010>, elige un video, dibuja las zonas sobre el primer
fotograma y pulsa iniciar.

**Los pesos y los videos no están en el repositorio.** No son código: son
entrada del sistema, y varios pasan del límite de 100 MB de GitHub.
`download_models.py` trae los públicos y dice exactamente cuáles faltan y qué
son — de los cinco modelos, cuatro están afinados para este caso y no tienen
URL pública.

Sin esos pesos el sistema **arranca igual**: los módulos que dependen de ellos
aparecen desactivados en la interfaz en lugar de reventar a media ejecución.

## Cómo está montado

```
backend/
├── config.py      rutas de modelos y umbrales, todo por variable de entorno
├── detector.py    carga perezosa de los cinco modelos; informa de cuáles hay
├── processor.py   el bucle de video: detectar, seguir, anotar y emitir
├── analytics.py   lo que convierte detecciones en cifras: ocupación, tiempos,
│                  eventos de seguridad y rutas
├── zones.py       polígonos y líneas dibujados sobre el primer fotograma
└── main.py        API y streaming MJPEG
frontend/          interfaz sin framework: HTML, CSS y un solo app.js
data/zones/        zonas ya dibujadas para los videos de ejemplo
```

Decisiones que vale la pena conocer:

- **Los modelos se cargan cuando se usan**, no al arrancar. Cargar cinco de
  golpe tarda y ocupa memoria aunque la sesión solo necesite uno.
- **El fuego se confirma con brillo.** Un detector de fuego solo marca muchos
  reflejos de foco como incendio; exigir además brillo alto en la caja quita
  casi todos los falsos positivos.
- **Las zonas se guardan por video**, en `data/zones/`, así que dibujarlas es
  cosa de una vez.
- **El seguimiento va a pocos fps a propósito.** ByteTrack no necesita todos
  los fotogramas para mantener la identidad, y bajarlo deja margen de CPU para
  el resto.

## Pruebas

```bash
python -m pytest -q          # 8 pruebas, sin video ni modelos ni GPU
```

`test_eventos.py` fabrica detecciones a mano y las pasa por `Analytics`: una
persona que se cae, un montacargas que corre de más y un pallet en mitad de la
ruta de evacuación. Comprueba que cada uno dispara su evento **una sola vez** —
cuatro segundos en el suelo son una caída, no cien alarmas seguidas.

Aparte, `comprobar_fuego.py` es una comprobación **manual** que sí necesita
pesos, videos y GPU. Mide lo único que no se puede fabricar sintéticamente: que
el filtro de brillo distinga un incendio de los focos del almacén. Pasa dos
videos, uno con fuego y otro sin él, y los dos tienen que salir bien — un
detector que solo acierta el primero estaría sonando todo el día.

```bash
python comprobar_fuego.py
```

## Licencia

Uso interno de ApexCorp.

<sub>OMNI Logistics · ApexCorp — desarrollado por
<a href="https://github.com/danielyatacoblas">Daniel Yataco Blas</a></sub>
