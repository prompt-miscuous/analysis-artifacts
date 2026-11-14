# Validación profunda: API de IRSA (SIA2 + recortes IBE) como backend de datos

Documento de trabajo para decidir **usar la API de IRSA tal cual vs construir un
backend propio**. Todo lo marcado `[PROBADO]` se ejecutó de verdad en esta sesión
(octubre 2026); lo marcado `[DOC]` viene de la documentación oficial sin ejecutar.

## 1. Resumen ejecutivo

- IRSA expone **SIA2** (búsqueda por posición, tiempo y longitud de onda, sin clave)
  y un **servicio de recortes IBE** (`?center=…&size=…`) que devuelve FITS pequeños
  con la misma estructura de 7 extensiones `[PROBADO]`.
- Con esos dos servicios se puede armar el pipeline del challenge sin tocar el
  bucket S3: buscar → recortar → renderizar → animar `[PROBADO]` (ver
  `pocs/render-fits/make_movie.py` y `movie_d3_demo.gif`).
- Lo que la API **no** da: imágenes a longitud de onda exacta (solo granularidad
  de banda/detector), cubos cielo×color (Nivel 3, aún no público), cuadros
  alineados entre épocas (cada uno trae su rotación) ni video ensamblado.
- Va al día: devuelve datos hasta la semana 2026W36; el bucket va por la W38
  (días de diferencia) `[PROBADO]`.

## 2. SIA2: búsqueda de imágenes

### 2.1 Endpoint y parámetros probados

```text
GET https://irsa.ipac.caltech.edu/SIA/spherex_qr3?POS=CIRCLE <ra> <dec> <radio>&...
```

| Parámetro | Formato probado | Efecto verificado |
| --- | --- | --- |
| `POS` | `CIRCLE 232.66 -10.72 0.3` (grados) | Devuelve imágenes cuyo footprint toca el círculo `[PROBADO]` |
| `BAND` | `2.0e-6` o `1.63e-6 2.44e-6` (metros) | Filtra por longitud de onda `[PROBADO]` (ver §2.2) |
| `TIME` | `61290 61330` (MJD) | Filtra por época `[PROBADO]` |
| `MAXREC` | entero | Tope de filas; **trunca en silencio** si hay más `[PROBADO]` |

Respuesta: tabla VOTable/XML, una fila por imagen. Sin autenticación.

### 2.2 El filtro `BAND` funciona (probado)

Consultas al mismo punto con distinto `BAND` devuelven solo el detector
correspondiente:

| `BAND=` | Detectores devueltos |
| --- | --- |
| `9.0e-7` (0,9 µm) | Solo D1 (67 filas) |
| `2.0e-6` (2,0 µm) | Solo D3 (67 filas) |
| `3.0e-6` (3,0 µm) | Solo D4 (67 filas) |
| `4.7e-6` (4,7 µm) | Solo D6 (48 filas) |

`[PROBADO]`. Conclusión: "todas las épocas de este punto a esta longitud de onda"
**sí se puede pedir** — con granularidad de banda (ver §5.1).

### 2.3 Anatomía de una fila (ejemplo real)

```text
obs_id       = 2025W28_2A_0582_4
em_min       = 1.63010e-06        (metros)
em_max       = 2.43460e-06
t_min/t_max  = 60869.721842 / …   (MJD ≈ jul-2025)
access_url   = https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/level2/…_4D3_spx_….fits
s_region     = polígono del footprint (RA/Dec de las esquinas)
```

Campos útiles además: `dataproduct_type/subtype`, `obs_collection`,
`obs_release_date`, `access_format`. El `obs_id` codifica
semana_plan_maniobra-grande_maniobra-pequeña (sin detector) `[PROBADO]`.

### 2.4 Trampas comprobadas

1. **Respuesta federada:** sin filtrar, la consulta mezcló 202 mapas de **AKARI**
   (otro telescopio) con los de SPHEREx. Filtrar siempre por
   `obs_collection` SPHEREx `[PROBADO]`.
2. **`MAXREC` silencioso:** con tope bajo devuelve las primeras N filas sin avisar
   (una vez se vio estado `OVERFLOW`). Paginar o subir el tope y verificar
   conteos `[PROBADO]`.
3. **Mismo `obs_id`, varios detectores:** cada par co-apuntado (D1&D4, D2&D5, D3&D6)
   aparece como filas separadas del mismo `obs_id` `[PROBADO]`. No confundir
   "filas" con "épocas": agrupar por `obs_id`.

## 3. Recortes IBE: el pedacito en vez del FITS de 63 MB

### 3.1 Sintaxis (probada, coincide con el ejemplo oficial)

```bash
curl -o cut.fits "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W30_1B/l2b-v27-2026-222/1/level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits?center=232.66,-10.72&size=0.25"
```

- `center=RA,Dec` en grados, `size=` en grados (la doc genérica de IBE muestra
  variantes con unidades `deg`/`arcmin`; para SPHEREx el ejemplo oficial usa
  números pelados y así se probó) `[PROBADO]`.
- Resultado verificado: FITS de ~4–5 MB, 146×146 px para `size=0.25`
  (0,25° = 900″ / 6,15″/px ≈ 146 px ✓), con las **7 extensiones intactas**
  (`IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `EPSF`, `WCS-WAVE`) `[PROBADO]`.

### 3.2 Cómo verificar que el recorte está bien centrado (lección aprendida)

El `CRVAL` de la cabecera del recorte **conserva la referencia del archivo padre**:
mirarlo solo lleva a concluir (mal) que el centro fue ignorado. La verificación
correcta es evaluar el WCS completo en el píxel central:

```python
from astropy.wcs import WCS
w = WCS(header)
ra, dec = w.all_pix2world([[nx/2, ny/2]], 0)[0]
```

Con ese método, tres recortes pedidos en (232,66°, −10,72°) dieron centros reales
de (232,6643°, −10,7063°), (232,6600°, −10,7190°) y equivalente: acuerdo a
~50″ `[PROBADO]`. Los tres cuadros del demo **sí son el mismo punto**.

### 3.3 Casos borde observados

- **Truncado:** un recorte volvió de 129×146 en vez de 146×146: el punto estaba
  cerca del borde real de datos (el polígono `s_region` es aproximado).
  El backend debe tolerar tamaños distintos `[PROBADO]`.
- **Rotación:** cada época trae su propia orientación (el satélite barre en
  direcciones distintas). Mismo centro ≠ misma cuadrícula de píxeles: correlación
  directa ≈ 0. Animar exige **reproyectar a una cuadrícula común** (pendiente;
  librería candidata: `reproject`) `[PROBADO]`.
- **Canal intra-banda:** dentro de un detector, el punto cae en filas distintas
  según la época (gradiente LVF), o sea en sub-canales distintos. Misma banda ≠
  mismo color exacto: comparar brillos sin corrección espectral es aproximado
  `[PROBADO conceptualmente; corrección pendiente]`.

## 4. Cobertura y frescura

- Misma zona, banda D3: **49 épocas** entre jul-2025 y jul-2026, en ~4 racimos
  de visitas (cadencia típica fuera de los polos: 3–4 pasadas/año) `[PROBADO]`.
- Dato más reciente visto en API: semana **2026W36** (día de proceso 254);
  bucket: **2026W38**. Van a la par `[PROBADO]`.
- Consultar `spherex_qr3` devolvió también filas con URLs `qr2/`: la colección
  parece incluir histórico reprocesado (observar, no documentado) `[PROBADO]`.

## 5. Lo que la API NO hace (límites para la decisión)

1. **Sin longitud de onda exacta:** `BAND` filtra a nivel detector (rango de
   ~0,4–1,4 µm). El canal exacto de un píxel vive dentro del archivo
   (`WCS-WAVE` + calibración `spectral_wcs`) `[PROBADO]`.
2. **Sin cubos Nivel 3:** la "imagen a λ exacta" reconstruida no existe como
   producto consultable (prevista a futuro). La Spectrophotometry Tool da
   **espectros en puntos**, no imágenes `[DOC]`.
3. **Sin alineación ni video:** entrega metadatos + FITS sueltos; bajar, alinear,
   estirar y animar es trabajo nuestro `[PROBADO]`.
4. **Sin interfaz pública simple:** es API de archivo profesional; el producto
   amable del challenge hay que construirlo igual.

## 6. Receta backend verificada (la que usó el demo)

```text
1. SIA2 por (RA, Dec, radio, BAND, TIME, MAXREC alto) → tabla VOTable
2. Filtrar obs_collection SPHEREx + detector/banda deseados
3. Agrupar por obs_id (= época real), ordenar por t_min, elegir N repartidas
4. Por época: GET access_url?center=RA,Dec&size=grados → FITS ~MB
5. Render: asinh alrededor del fondo + max-pool → PNG (pocs/render-fits/render.py)
6. [PENDIENTE] Reproyectar a cuadrícula común antes de animar
7. Servir PNGs ordenados o GIF/MP4 ensamblado
```

Probado de punta a punta en `pocs/render-fits/make_movie.py`
(`movie_d3_demo.gif`: mismo punto, banda D3, 3 épocas) `[PROBADO]`.

## 7. Insumos para la decisión build-vs-reusa

| Si reusamos IRSA… | Si construimos backend propio… |
| --- | --- |
| Cero ingesta: sin S3 ni 63 MB por cuadro | Control total de caché, colas y reintentos |
| Frescura automática (semanal) | Funciona offline / sin depender de IRSA |
| Búsqueda por punto/banda/tiempo ya resuelta | Podríamos pre-alinear y pre-renderizar mosaicos |
| Riesgo: límites de uso no publicados, caídas ajenas | Costo: ingesta masiva, almacenamiento, reproceso |

Recomendación de este análisis: **reusar IRSA como fuente** (SIA2 + recortes) y
construir solo la capa fina que falta: caché de recortes, reproyección,
render y API `/frames` para el frontend. Decisión formal pendiente del equipo.

## 8. Referencias

- Guía de acceso (oficial): [spherex-data-access](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/)
- Formatos y productos (oficial): [spherex-data-products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/)
- Sintaxis de recortes IBE: [ibe/cutouts.html](https://irsa.ipac.caltech.edu/ibe/cutouts.html)
- Ayuda SPHEREx en IRSA (PDF, 19 MB): `https://irsa.ipac.caltech.edu/onlinehelp/spherex/help.pdf`
- Tutoriales Python (no ejecutados): `https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/`
- Evidencia local: `pocs/render-fits/` (scripts, GIFs, FITS de prueba)
