# OMNI Logistics — visión para almacén y muelle

> **Visión computacional · YOLO11 + YOLOv8 + ByteTrack · FastAPI · CUDA o CPU**
>
> ![estado](https://img.shields.io/badge/estado-MVP%20funcional-2D6CDF)
> ![version](https://img.shields.io/badge/versión-v0.3.0-129A6B)
> ![pruebas](https://img.shields.io/badge/pruebas-8%20pasando-129A6B)
> ![licencia](https://img.shields.io/badge/uso-interno%20ApexCorp-E19100)

![OMNI Logistics en marcha](docs/capturas/01-ocupacion.png)

## El problema

Un almacén no sabe cuánto de cada zona está ocupado ahora mismo. Sabe cuánto
había ayer, cuando alguien lo apuntó. No sabe cuánto tarda de verdad una
descarga, ni por dónde pasan los montacargas, ni se entera de un conato de
incendio hasta que hay humo en el pasillo.

Todo eso está en las cámaras que ya hay. OMNI Logistics lo saca.

| Módulo | Qué responde | Con qué |
|---|---|---|
| **Ocupación** | ¿Cuánto de cada zona está ocupado y desde cuándo? | Pallets detectados dentro de polígonos |
| **Muelle** | ¿Cuánto tarda una carga o descarga? ¿Cuántas piezas por minuto? | Cruces de línea de pallets y montacargas |
| **Seguridad** | ¿Hay fuego o humo? ¿Alguien sin EPP cerca de un montacargas? | Fuego/humo con filtro de brillo, y chaleco/casco |
| **Rutas** | ¿Por dónde pasó cada montacargas? ¿Hay un pasillo bloqueado? | Seguimiento, mapa de calor y detección de obstrucción |

## Qué se ve

| | |
|---|---|
| **Ocupación por zona**<br><img src="docs/capturas/01-ocupacion.png" width="100%"><br><sub>pallets dentro de cada polígono, y desde cuándo</sub> | **Muelle: carga y descarga**<br><img src="docs/capturas/02-muelle.png" width="100%"><br><sub>cruces de línea → piezas por minuto</sub> |
| **Fuego y humo**<br><img src="docs/capturas/03-seguridad-fuego.png" width="100%"><br><sub>detección confirmada con brillo, para no marcar cada foco</sub> | **Rutas y trazabilidad**<br><img src="docs/capturas/04-trazabilidad.png" width="100%"><br><sub>recorrido de cada montacargas y mapa de calor</sub> |
| **Editor de zonas**<br><img src="docs/capturas/05-editor-de-zonas.png" width="100%"><br><sub>polígonos y líneas sobre el primer fotograma</sub> |  |

## Cómo funciona

<a href="docs/flujo.svg">
  <img src="docs/flujo.svg" alt="De la cámara del almacén a la operación" width="100%">
</a>

<sub>Ábrelo en grande: <a href="docs/flujo.svg"><code>docs/flujo.svg</code></a>.
Las cifras de las tarjetas no están escritas a mano — las pone
<a href="scripts/diagrama.py"><code>scripts/diagrama.py</code></a> leyendo
<code>docs/modelos.json</code>, que a su vez genera
<a href="scripts/medir_modelos.py"><code>scripts/medir_modelos.py</code></a>
midiendo los modelos de verdad. Si mañana se cambia un modelo, se corren los
dos y el dibujo se corrige solo.</sub>

### El mismo recorrido, en corto

```mermaid
flowchart LR
  V["Video de almacén"] --> P["Lector de fotogramas"]
  P --> D1["Pallets<br/>YOLO11n afinado"]
  P --> D2["Montacargas y personas<br/>YOLOv8m"]
  P --> D3["Fuego y humo<br/>YOLOv8n + brillo"]
  P --> D4["EPP<br/>chaleco y casco"]
  D1 --> T["ByteTrack"]
  D2 --> T
  T --> A["Analítica"]
  D3 --> A
  D4 --> A
  A --> E1["Ocupación por zona"]
  A --> E2["Piezas/min del muelle"]
  A --> E3["Caída · velocidad · obstrucción"]
  A --> E4["Rutas y mapa de calor"]
  A --> M["Anotado + MJPEG"]
```

**Los modelos se cargan cuando se usan**, no al arrancar. Son cuatro; cargarlos
todos de golpe tarda y ocupa memoria aunque la sesión solo necesite uno. Si
falta alguno, el módulo que lo usa aparece **desactivado en la interfaz** en
lugar de reventar a media ejecución.

**El fuego se confirma con brillo.** Un detector de fuego a secas marca como
incendio cualquier reflejo de foco, y en un almacén hay focos por todas partes.
Exigir además brillo alto dentro de la caja quita casi todos los falsos
positivos. Es la diferencia entre una alarma que se atiende y una que en una
semana nadie mira.

<!-- MODELOS:inicio -->

### Los modelos, medidos

| Modelo | Para qué | Entrada | Precisión | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|---|---|
| **`pallet_n_640.pt`** | Pallets | 640² | 65.8 % | 61.4 % | 67.4 % | 57.1 % |
| **`forklift_kerem.pt`** | Montacargas y personas | 640² | — | — | — | — |
| **`fire_smoke.pt`** | Fuego y humo | 640² | 77.5 % | 69.5 % | 76.5 % | 44.5 % |
| **`ppe_vest.pt`** | Chaleco y casco | 640² | — | — | — | — |
| **`yolo11n.pt`** | Base genérica | 640² | 65.6 % | 50.2 % | 55.1 % | 39.4 % |

<sub>Estas cuatro columnas **no** se calculan aquí: salen del propio archivo `.pt`, donde Ultralytics guarda la validación del entrenamiento que produjo esos pesos. Son el acierto sobre el conjunto de validación de quien lo entrenó, **no** sobre los videos de este proyecto. Medir eso exigiría etiquetar a mano esta operación concreta, que es trabajo que un MVP todavía no ha hecho; dar un porcentaje inventado sería peor que no darlo. Comprobación de que la lectura es correcta: `yolo11n` sale con mAP@50-95 = 39,4 % y Ultralytics publica 39,5 % para ese modelo en COCO.</sub>

### De dónde sale cada modelo

| Modelo | Entrenado sobre | Épocas | Resolución | Origen |
|---|---|---|---|---|
| **`pallet_n_640.pt`** | `data` | 100 | 640×640 | YOLO11n afinado con pallets de madera |
| **`forklift_kerem.pt`** | `data` | 40 | 640×640 | [keremberke · forklift](https://huggingface.co/keremberke/yolov8m-forklift-detection) |
| **`fire_smoke.pt`** | `data` | 50 | 640×640 | YOLOv8n afinado con fuego y humo |
| **`ppe_vest.pt`** | `ppe_data` | 100 | 640×640 | Detector de EPP de terceros |
| **`yolo11n.pt`** | `coco` | 600 | 640×640 | [Ultralytics · COCO 2017](https://docs.ultralytics.com/models/yolo11/) |

<sub>El conjunto, las épocas y la resolución salen de `train_args`, que Ultralytics guarda dentro del propio `.pt`. Es decir: no es lo que dice la documentación del modelo, es lo que quedó grabado en el archivo que este repositorio usa de verdad. Los nombres de conjunto son los del disco de quien entrenó —`retrain_data`, `safe_human`— porque es literalmente lo que hay dentro.</sub>

| Modelo | Parámetros | Clases | Latencia (mejor) | Latencia (mediana) | Det./fotograma | Confianza media |
|---|---|---|---|---|---|---|
| **`pallet_n_640.pt`** | 2.6 M | 1 | 14.8 ms · 68 fps | 17.6 ms · 56.7 fps | 0.3 | 0.453 |
| **`forklift_kerem.pt`** | 25.9 M | 2 | 16.5 ms · 61 fps | 19.7 ms · 50.7 fps | 4.5 | 0.681 |
| **`fire_smoke.pt`** | 3.0 M | 2 | 27.9 ms · 36 fps | 40.1 ms · 24.9 fps | 1.2 | 0.54 |
| **`ppe_vest.pt`** | 3.0 M | 10 | 24.8 ms · 40 fps | 37.5 ms · 26.6 fps | 1.4 | 0.585 |
| **`yolo11n.pt`** | 2.6 M | 80 | 15.7 ms · 64 fps | 18.5 ms · 54.2 fps | 0.9 | 0.482 |

<sub>Esto sí se mide aquí, con <a href="scripts/medir_modelos.py"><code>scripts/medir_modelos.py</code></a>, sobre fotogramas reales de los videos del repositorio, en una RTX 3060 Laptop y a la resolución que usa la aplicación. Sesenta fotogramas, descartando los veinte primeros.<br>Se dan <b>dos</b> latencias a propósito. Esta GPU está a 210 MHz en reposo y tarda segundos en subir de reloj, así que la mediana se mueve bastante entre pasadas —el mismo <code>yolo11n</code> ha dado 20 y 48 fps— mientras que el mejor caso es estable y representa lo que la máquina puede sostener. Dar solo la cifra buena sería vender de más; dar solo la mediana, castigar al modelo por la gestión de energía del portátil.</sub>

<!-- MODELOS:fin -->

## Probarlo

```bash
pip install -r requirements.txt
python download_models.py
python -m uvicorn backend.main:app --port 8021    # o arrancar.bat
```

Abre <http://localhost:8021>, elige el módulo, elige el video, dibuja las zonas
sobre el primer fotograma y pulsa procesar.

> Cada MVP de la familia tiene su propio puerto —8000 PPE, 8010 Retail,
> 8020 Agro, 8021 Logistics, 8030 Guard— para poder tener varios levantados a
> la vez. Antes Agro y Logistics compartían el 8020 y el segundo no arrancaba.

### Por qué los pesos y los videos no están aquí

No son código: son la entrada y la salida del sistema. Varios pasan de los
100 MB que GitHub rechaza de plano, y clonar el proyecto pasaría de segundos a
minutos para traerse archivos que se regeneran o se descargan.

```bash
python download_models.py          # los recupera y dice cuáles faltan
```

De los cinco modelos, **solo `yolo11n` tiene URL pública**. Los otros cuatro
están afinados para este caso. El script los nombra y dice qué son, en vez de
fallar a mitad de descarga y dejar un archivo truncado que carga bien y revienta
mucho después.

## Cómo está montado

```
backend/
├── config.py     rutas de modelos y umbrales, por variable de entorno
├── detector.py   los cuatro modelos, cargados solo cuando se usan
├── processor.py  el bucle: leer, detectar, seguir, anotar, emitir
├── analytics.py  detecciones → ocupación, tiempos, eventos y rutas
├── zones.py      polígonos y líneas sobre el primer fotograma
├── compat.py     el parche de NumPy 2 para el conteo de línea
└── main.py       API y streaming MJPEG
frontend/         interfaz sin framework
scripts/          generadores de las capturas y del diagrama de ramas
data/zones/       zonas ya dibujadas para los videos de ejemplo
```

Los videos van en subcarpetas por módulo (`videos/01_ocupacion/`, …) y el
listado se filtra según el módulo elegido: cada apartado enseña solo lo suyo.

## Pruebas

```bash
python -m pytest -q          # 8, sin video ni modelos ni GPU
```

`test_eventos.py` fabrica detecciones a mano y las pasa por `Analytics`: una
persona que se cae, un montacargas que corre de más y un pallet en mitad de la
ruta de evacuación. Lo que fija es que cada evento salte **una sola vez** —
cuatro segundos en el suelo son una caída, no cien alarmas seguidas.

Antes esto no era una prueba: imprimía números y calculaba un booleano que
nadie comprobaba, así que pytest no recogía nada.

```bash
python comprobar_fuego.py    # necesita pesos, videos y GPU
```

Comprobación **manual**, aparte, porque mide lo único que no se puede fabricar
sintéticamente: que el filtro de brillo distinga un incendio de los focos del
almacén. Pasa dos videos, uno con fuego y otro sin él, y **los dos** tienen que
salir bien.

<!-- GITFLOW:inicio -->

## Cómo se trabajó

**15 commits**, **9 fusiones** y **3 etiquetas** (`v0.1.0`, `v0.2.0`, `v0.3.0`). al generar este bloque. Cada rama entra con `--no-ff`: un merge aplastado ahorra una línea y borra la única prueba de que aquello fue una tarea con principio y final.

```mermaid
gitGraph
   commit id: "import"
   branch develop
   checkout develop
   branch feature/repository-hygiene
   checkout feature/repository-hygiene
   commit
   checkout develop
   merge feature/repository-hygiene
   checkout main
   merge develop tag: "v0.1.0"
   checkout develop
   branch feature/project-setup-and-tests
   checkout feature/project-setup-and-tests
   commit
   checkout develop
   merge feature/project-setup-and-tests
   checkout main
   merge develop tag: "v0.2.0"
   checkout develop
   branch feature/documentation-and-own-port
   checkout feature/documentation-and-own-port
   commit
   checkout develop
   merge feature/documentation-and-own-port
   checkout main
   merge develop tag: "v0.3.0"
   checkout main
   merge develop
   checkout develop
   branch feature/pipeline-diagram-and-model-metrics
   checkout feature/pipeline-diagram-and-model-metrics
   commit
   checkout develop
   merge feature/pipeline-diagram-and-model-metrics
   checkout main
   merge develop
```

| Prefijo | Para qué | Ramas |
|---|---|---|
| `develop/` | rama de integración | 5 |
| `feature/` | trabajo acotado, se integra en develop | 4 |

| Rama | Responsabilidad | Regla de salida |
|---|---|---|
| `main` | Lo que ve primero quien llega al repositorio | Solo recibe trabajo terminado y con las pruebas en verde |
| `develop` | Integración: aquí se junta todo antes de subir | Merge `--no-ff` desde una rama `feature/*` |
| `feature/*` | Un trabajo acotado, nombrado por lo que hace | Merge `--no-ff` a `develop` con sus pruebas escritas |

Los mensajes siguen *Conventional Commits* y están en inglés. Explican **por qué**, no qué: el *qué* ya está en el diff. Varios cuentan el fallo que arreglan y cómo se descubrió, que es lo que sirve dentro de seis meses.

<sub>El diagrama lo genera <a href="scripts/gitflow.py"><code>scripts/gitflow.py</code></a> leyendo <code>git log --merges</code>.</sub>

<!-- GITFLOW:fin -->

---

## Licencia

Uso interno de ApexCorp S.A.C.

<sub>OMNI Logistics · ApexCorp S.A.C. — desarrollado por
<a href="https://github.com/danielyatacoblas">Daniel Yataco Blas</a></sub>
