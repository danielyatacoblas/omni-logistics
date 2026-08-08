# 🎬 Prompts para generar videos de prueba con IA — OMNI Logística

Prompts listos para Sora / Veo / Kling / Runway / Pika. Cada uno está diseñado
para que **los detectores del MVP funcionen** sobre el video generado.

## ⚠️ Reglas de oro (aplican a TODOS los prompts)

1. **Cámara FIJA** (tipo CCTV/vigilancia). Sin cortes, sin zoom, sin paneo —
   ByteTrack pierde los IDs si la cámara se mueve.
2. **Un solo plano continuo** de 8–10 segundos (genera 2-3 clips y los unes si
   quieres más duración).
3. **Iluminación industrial pareja** (luz blanca de nave), sin contraluz fuerte.
4. **Objetos a escala media**: ni primerísimos planos ni tomas aéreas lejanas.
5. Estilo **realista** (photorealistic), NO cartoon ni render 3D estilizado.
6. En inglés funcionan mejor casi todos los generadores — cada caso tiene su
   versión EN y ES.

---

## 01 · OCUPACIÓN POR ZONA (contar pallets por área)

**Qué necesita el detector:** pallets de madera con carga, bien visibles en el
piso, algunos entran/salen de la escena durante el clip.

**Prompt EN:**
> Static security camera footage of a warehouse storage area, fixed wide shot
> from 4 meters high in a corner. Six wooden pallets loaded with stacked
> cardboard boxes sit on the concrete floor in two rows. A worker with a manual
> pallet jack slowly brings one more loaded pallet into the area, places it,
> and leaves. Even white industrial lighting, photorealistic, CCTV style, no
> camera movement, single continuous 10 second shot.

**Prompt ES:**
> Video de cámara de seguridad fija en esquina alta (4 m) de una zona de
> almacenaje. Seis pallets de madera cargados con cajas de cartón apiladas en
> dos filas sobre piso de concreto. Un trabajador con transpaleta manual trae
> lentamente un pallet más, lo deja y se va. Luz industrial blanca pareja,
> fotorrealista, estilo CCTV, cámara sin movimiento, plano único de 10 s.

**Para la demo:** dibuja 2 zonas ("Rack A" sobre una fila, "Rack B" sobre la
otra) y verás el % de llenado subir cuando entra el pallet nuevo.

---

## 02 · MUELLE CARGA/DESCARGA (piezas que cruzan la línea)

**Qué necesita el detector:** pallets/carga que CRUZAN claramente de un lado a
otro de la escena (para la LineZone). Esto es lo que pediste: perspectiva de
cámara apuntando y paquetes pasando.

**Prompt EN:**
> Fixed security camera at a warehouse loading dock, wide shot facing the open
> truck door. Workers with manual pallet jacks repeatedly move wooden pallets
> loaded with cardboard boxes from the right side (warehouse) to the left side
> (into the truck), one pallet crossing the frame every 2 seconds, 4 pallets
> total. Even industrial lighting, photorealistic, CCTV style, camera does not
> move, single continuous 10 second take.

**Prompt ES:**
> Cámara de seguridad fija en un muelle de carga, plano abierto mirando a la
> puerta abierta del camión. Trabajadores con transpaletas mueven pallets de
> madera cargados con cajas desde la derecha (almacén) hacia la izquierda
> (al camión), un pallet cruza el cuadro cada 2 segundos, 4 en total. Luz
> industrial pareja, fotorrealista, estilo CCTV, cámara inmóvil, plano único
> de 10 s.

**Variante "faja/rodillos" (como tu ejemplo):**
> Fixed camera pointing at an industrial roller conveyor in a warehouse,
> medium shot. Cardboard boxes travel along the conveyor from left to right,
> one box every 1.5 seconds, evenly spaced, nothing else happens. Photoreal,
> even lighting, static camera, continuous 10 second shot.
*(OJO: el MVP cuenta PALLETS en la línea; cajas sueltas se detectan menos —
úsala solo si luego agregamos el modelo de cajas.)*

**Para la demo:** dibuja la línea vertical en medio del recorrido → IN/OUT y
piezas/min en vivo.

---

## 03 · SEGURIDAD MONTACARGAS ↔ PERSONA (proximidad peligrosa)

**Qué necesita el detector:** un montacargas EN MOVIMIENTO y un peatón que se
le acerca demasiado (que sus recuadros casi se toquen en algún momento).

**Prompt EN:**
> Static warehouse security camera, wide shot of a main aisle between tall
> pallet racks. A yellow forklift drives slowly from left to right carrying a
> pallet. A worker in a high-visibility vest walks distracted looking at a
> clipboard and crosses the aisle, passing dangerously close in front of the
> moving forklift, less than one meter away; the forklift brakes. Even
> industrial lighting, photorealistic, CCTV style, fixed camera, single
> continuous 10 second shot.

**Prompt ES:**
> Cámara de seguridad fija, plano abierto de un pasillo principal entre racks
> altos. Un montacargas amarillo avanza lento de izquierda a derecha cargando
> un pallet. Un trabajador con chaleco reflectante camina distraído mirando
> una tabla y cruza el pasillo pasando peligrosamente cerca (menos de 1 metro)
> por delante del montacargas, que frena. Luz industrial pareja,
> fotorrealista, estilo CCTV, cámara fija, plano único de 10 s.

**Para la demo:** módulo 03 sin dibujar nada → línea roja "PELIGRO" + alerta
crítica cuando se cruzan.

---

## 04 · TRAZABILIDAD / RUTAS (heatmap del montacargas)

**Qué necesita el detector:** un (o dos) montacargas recorriendo VARIAS partes
de la escena durante el clip, con recorrido variado (el heatmap pinta por
dónde pasa más).

**Prompt EN:**
> Static overhead-ish security camera, high wide shot covering a large
> warehouse floor with several aisles. A yellow forklift drives around
> continuously: goes up the left aisle, turns, comes back down the center
> aisle, pauses 2 seconds near a stack of pallets, then exits right. A second
> forklift crosses the back area once. Even lighting, photorealistic, CCTV
> style, fixed camera, single continuous 10 second shot.

**Prompt ES:**
> Cámara de seguridad fija en alto, plano muy abierto que cubre gran parte del
> piso del almacén con varios pasillos. Un montacargas amarillo circula todo
> el clip: sube por el pasillo izquierdo, gira, baja por el central, se
> detiene 2 segundos junto a unos pallets y sale por la derecha. Un segundo
> montacargas cruza el fondo una vez. Luz pareja, fotorrealista, estilo CCTV,
> cámara fija, plano único de 10 s.

**Para la demo:** módulo 04 → estelas + heatmap TURBO marcando el pasillo más
usado; dibuja una zona sobre los pallets para ver la permanencia de 2 s.

---

## 🔥 INCENDIO (alarma transversal)

**Qué necesita el detector:** llamas REALES visibles (naranjas brillantes con
núcleo claro) y/o humo gris; que empiece pequeño y crezca — así se ve la
alarma dispararse en vivo. El filtro anti-falsos exige núcleo brillante: pide
llamas luminosas, no brasas apagadas.

**Prompt EN:**
> Static warehouse security camera, wide shot of a storage corner with wooden
> pallets and cardboard boxes. At second 2, a small bright orange flame starts
> at the base of a cardboard box on a pallet; over the next 6 seconds the fire
> grows visibly with bright yellow-white core and gray smoke rising toward the
> ceiling. No people. Even industrial lighting, photorealistic, CCTV style,
> fixed camera, single continuous 10 second shot.

**Prompt ES:**
> Cámara de seguridad fija, plano abierto de una esquina de almacenaje con
> pallets de madera y cajas de cartón. En el segundo 2 aparece una llama
> naranja pequeña y brillante en la base de una caja sobre un pallet; durante
> los siguientes 6 segundos el fuego crece visiblemente, con núcleo
> amarillo-blanco luminoso y humo gris subiendo al techo. Sin personas. Luz
> industrial pareja, fotorrealista, estilo CCTV, cámara fija, plano único de
> 10 s.

**Combo estrella para vender (incendio + seguridad):**
> Same warehouse security camera shot: a forklift works moving a pallet in the
> background while a small bright fire starts on a cardboard box in the
> foreground corner and grows with gray smoke. A worker walks in, notices the
> fire and hurries away. Fixed camera, photorealistic, CCTV style, continuous
> 10 seconds.

**Para la demo:** cualquier módulo → banner rojo + sirena + tarjeta "¡FUEGO
ACTIVO!" a los ~2-3 s de aparecer la llama.

---

## 🧍⬇️ PERSONA CAÍDA (man down) — módulo Seguridad

**Qué necesita el detector:** una persona de pie que cae y QUEDA EN EL PISO
varios segundos (la caja pasa de vertical a horizontal ≥1.2 s → alarma).

**Prompt EN:**
> Static warehouse security camera, wide shot of an open floor area next to
> pallet racks. A worker in a high-visibility vest walks across the floor,
> trips on a pallet corner, falls to the ground and remains lying on the floor
> motionless for 5 seconds. No one else in the scene. Even industrial
> lighting, photorealistic, CCTV style, fixed camera, single continuous 10
> second shot.

**Prompt ES:**
> Cámara de seguridad fija, plano abierto de una zona despejada junto a racks.
> Un trabajador con chaleco reflectante camina, se tropieza con la esquina de
> un pallet, cae al piso y queda tendido inmóvil 5 segundos. Nadie más en
> escena. Luz industrial pareja, fotorrealista, estilo CCTV, cámara fija,
> plano único de 10 s.

**Para la demo:** módulo 03 → caja roja parpadeante "CAÍDA #id" + alerta
crítica "PERSONA CAÍDA" ~1.2 s después de tocar el piso.

---

## 🚧 PASILLO OBSTRUIDO (ruta de evacuación) — módulo Seguridad

**Qué necesita el detector:** un pallet que alguien DEJA en medio de un
pasillo y queda ahí quieto (>8 s → alarma). Dibuja el pasillo en la UI antes.

**Prompt EN:**
> Static warehouse security camera, wide shot of a long clear aisle between
> tall pallet racks, marked with yellow floor lines. A worker with a manual
> pallet jack brings a wooden pallet loaded with boxes, leaves it in the
> middle of the aisle and walks away. The pallet remains there blocking the
> aisle for the rest of the clip. Even lighting, photorealistic, CCTV style,
> fixed camera, single continuous 12 second shot.

**Prompt ES:**
> Cámara de seguridad fija, plano abierto de un pasillo largo y despejado
> entre racks altos, con líneas amarillas en el piso. Un trabajador con
> transpaleta trae un pallet cargado con cajas, lo deja en MEDIO del pasillo
> y se va. El pallet queda ahí bloqueando el pasillo el resto del clip. Luz
> pareja, fotorrealista, estilo CCTV, cámara fija, plano único de 12 s.

**Para la demo:** módulo 03 → botón "Marcar pasillo" → dibuja el pasillo →
a los 8 s del pallet quieto: zona en rojo "OBSTRUIDO" + caja roja "OBSTRUYE"
+ alerta crítica.

---

## ⚡ EXCESO DE VELOCIDAD de montacargas — módulo Seguridad

**Qué necesita el detector:** un montacargas cruzando el cuadro NOTORIAMENTE
rápido (recorre >1/5 del ancho por segundo).

**Prompt EN:**
> Static warehouse security camera, wide shot of a long main corridor. A
> yellow forklift speeds through the corridor from left to right much faster
> than normal, crossing the entire frame in about 3 seconds, then a second
> slower forklift crosses calmly taking 8 seconds. Even industrial lighting,
> photorealistic, CCTV style, fixed camera, single continuous 12 second shot.

**Prompt ES:**
> Cámara de seguridad fija, plano abierto de un corredor principal largo. Un
> montacargas amarillo lo cruza de izquierda a derecha MUY rápido (todo el
> cuadro en ~3 segundos); luego un segundo montacargas cruza lento tomando 8
> segundos. Luz industrial pareja, fotorrealista, estilo CCTV, cámara fija,
> plano único de 12 s.

**Para la demo:** módulo 03 → al rápido le aparece ">> RAPIDO" en ámbar +
alerta "Velocidad excesiva (1.8x el límite)"; el lento no dispara nada
(contraste perfecto para la demo).

---

## 📋 Negative prompt (agregar si el generador lo soporta)

> camera movement, camera shake, cuts, scene change, zoom, pan, cartoon, 3d
> render, animation style, motion blur, fisheye, dark scene, night, text
> overlay, watermark, slow motion

## 💡 Tips finales

- Genera **1080p si se puede** (o 720p); evita 4K vertical.
- Si el generador limita a 5 s, genera 2 clips con el MISMO prompt y únelos
  (`ffmpeg -f concat`); al ser cámara fija casi no se nota el corte.
- Guarda los resultados en `videos/` con nombres tipo `ia_muelle.mp4`,
  `ia_incendio.mp4` — aparecen solos en el selector.
- Si un clip generado no detecta bien, el problema #1 suele ser: cámara en
  movimiento o estética "render" — refuerza "static CCTV camera,
  photorealistic".
