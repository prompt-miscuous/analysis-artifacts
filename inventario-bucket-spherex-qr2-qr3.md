# Qué hay exactamente en el bucket de SPHEREx (QR2 vs QR3)

Inventario observado del bucket público `s3://nasa-irsa-spherex` (región `us-east-1`,
acceso anónimo con `--no-sign-request`, sin cuenta de AWS), levantado con AWS CLI
el 2026-10-29. Complementa el análisis arquitectónico de
[spikes/spherex-satellite-architecture.md](spikes/spherex-satellite-architecture.md).

## 1. Qué es «la ciencia» (`level2/`)

«La ciencia» son las **imágenes espectrales calibradas de Nivel 2**: cada archivo FITS
es la exposición de **un detector individual (2040 × 2040 píxeles activos)** ya
reducida por el pipeline (dark, flat, astrometría, luz zodiacal) y lista para análisis
astronómico. Es el único producto consultable por coordenadas (IVOA SIA2/TAP) y el que
permite recortes espaciales (*cutouts*).

Cada FITS de ciencia (~63–68 MB) trae 6 extensiones tras el HDU primario:

| Extensión | Nombre | Contenido |
| --- | --- | --- |
| 0 | `PRIMARY` | Cabecera global: apuntamiento, tiempos, telemetría |
| 1 | `IMAGE` | Imagen calibrada en brillo superficial (MJy/sr) + WCS espacial |
| 2 | `FLAGS` | Máscara de bits: rayos cósmicos, saturación, píxeles muertos, dicroico |
| 3 | `VARIANCE` | Incertidumbre σ² por píxel (Poisson + ruido de lectura) |
| 4 | `ZODI` | Modelo de luz zodiacal estimada por píxel |
| 5 | `PSF` / `EPSF` | PSF promediada por exposición (cambia entre QR2 y QR3, ver §4) |
| 6 | `WCS-WAVE` | Tabla que convierte (x, y) → longitud de onda y ancho de banda |

## 2. Estructura exacta de carpetas (verificada con `aws s3 ls`)

```text
s3://nasa-irsa-spherex/
├── index.html                  # visor web del bucket
├── qr2/                        # Quick Release 2 (2025W17 → 2026W29, ~130 semanas)
│   ├── level2/<semana>/<versión>/<detector>/*.fits
│   └── <13 carpetas de calibración>
└── qr3/                        # Quick Release 3 (2026W30 → 2026W38, 18 semanas)
    ├── level2/<semana>/<versión>/<detector>/*.fits
    └── <19 carpetas de calibración>
```

Ejemplo real de navegación en ciencia (QR3):

```text
qr3/level2/2026W30_1B/                                  # semana de planificación
└── l2b-v27-2026-222/                                    # versión del procesador
    ├── 1/ … 6/                                          # uno por detector
    │   └── level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits  (62,8 MB)
```

Ejemplo real en QR2 (nótese la versión de pipeline distinta):

```text
qr2/level2/2025W19_2B/l2b-v20-2025-247/3/
└── level2_2025W19_2B_0007_2D3_spx_l2b-v20-2025-247.fits  (68,3 MB)
```

### Cómo leer un nombre de archivo

Definición oficial ([IRSA Data Products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/)):
`level2_[Observation ID]D[Detector]_spx_l2b_v[Version]_[Processing Date].fits`, donde el
*Observation ID* incluye el periodo de planificación y los contadores de maniobra grande
y pequeña (ejemplo documentado: `2025W18_2B_0001_1` = periodo `2025W18_2B` + large slew
`0001` + small slew `1`; máximo 4 pequeñas por grande, algunas traen menos):

```text
level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits
         │        │    │  │ │   └── fecha de procesado (día 222 de 2026)
         │        │    │  │ └────── versión del pipeline (l2b-v27…)
         │        │    │  └──────── sufijo de misión/instrumento
         │        │    └─────────── detector (D1 … D6, coincide con la carpeta)
         │        └────────────── contadores: maniobra grande 0001, pequeña 1
         └────────────────────── periodo de planificación (semana ISO + plan)
```

Comprobado en el bucket: la exposición `0001` trae las 4 pequeñas (`1D1`–`4D1`), la
`0005` solo `1D1`, la `0007` trae 3. Por cada apuntamiento hay 6 MEFs (uno por detector),
aunque algunas observaciones no incluyen las 6 bandas por control de calidad.

Algunas semanas traen **dos versiones del procesador** (p. ej. `l2b-v27-2026-222/` y
`l2b_retry-v27-2026-223/`): son reprocesados de la misma semana; ante la duda usa la más
reciente (`retry` o día juliano mayor).

## 3. Qué es QR2 y QR3 (y qué fue QR1)

**QR = Quick Release**: publicaciones rápidas semanales de datos de Nivel 2 con
calibraciones preliminares, para que la comunidad los use cuanto antes. No son el archivo
definitivo de la misión.

| | QR1 | QR2 | QR3 |
| --- | --- | --- | --- |
| Periodo | jul-2025 → ene-2026 | oct-2025 → ~sep-2026 | sep-2026 → vigente |
| Semanas en bucket | ninguna (purgado) | `2025W17` → `2026W29` (~130) | `2026W30` → `2026W38` (18 y creciendo) |
| Pipeline visto | — | `l2b-v20-*` | `l2b-v27-*` |
| Tamaño por FITS | — | ~68 MB | ~63 MB |
| Estado | retirado feb-2026 | vigente (histórico) | vigente (actual) |

En la práctica: **QR3 es la versión a usar** (calibraciones más nuevas); QR2 sirve como
histórico y para comparar épocas separadas por ~1 año, que es justo lo que necesita el
challenge (detectar movimiento entre imágenes de distintas épocas).

## 4. Diferencias concretas QR2 vs QR3

1. **Cobertura temporal**: QR2 cubre el primer año de sondeo (may-2025 → ~jul-2026);
   QR3 empieza en la semana 30 de 2026 y sigue publicándose cada semana.
2. **PSF (extensión 5 del FITS)**: QR2 trae `average_psf/` (cubo 101 × 101 × 121,
   sobremuestreo 10×); QR3 la reemplaza por `epsf/` (modelos ePSF de 33 × 33 píxeles,
   sobremuestreo 5×, en rejilla espacial por zonas del detector).
3. **Carpetas de calibración nuevas solo en QR3** (verificadas en el listado):
   `aurora_template/`, `he_template/`, `shuttle_glow_template/`
   (plantillas de emisión atmosférica), `l3_flux_corrections/` (homogeneiza QR2 con QR3
   para mosaicos de Nivel 3), `xtalk_class1/`, `xtalk_class2/`, `zodi_scaling_v2/`
   (tablas `.ecsv`) y `nonfunc_v2/` (reemplaza a `nonfunc/` de QR2).
4. **Versiones de calibración distintas**: p. ej. PSF `cal-psf-v5-*` (QR2) frente a
   ePSF `cal-epsf-v1/v2-2026-191` (QR3); cada versión vive en su propia subcarpeta con
   fecha juliana (`-2026-191` = día 191 de 2026).

## 5. Las carpetas de calibración, una por una (con ejemplos reales)

Son los ingredientes que usó el pipeline para cocinar el Nivel 2. Estructura típica:
`<producto>/<versión-cal>/<detector 1-6>/<archivo>.fits`.

* **`dark/`** → `cal-drk-v6-2026-191/`: corriente oscura por píxel.
* **`dichroic/`**: mapa binario de píxeles atenuados ≥50 % por el filtro dicroico
  (solo afecta a bandas 3 y 4).
* **`epsf/` (QR3)** → `cal-epsf-v2-2026-191/3/epsf_D3_spx_cal-epsf-v2-2026-191.fits`
  (7,7 MB): ePSF del detector 3.
* **`average_psf/` (QR2)** → versiones `cal-psf-v5-2025-206/`, `cal-psf-v5-2026-082/`.
* **`gain_factors/`** → `base-2026-191/gain_factors_spx_base-2026-191.yaml` (5,4 KB):
  32 ganancias electrón/ADU por amplificador para cada detector, con números de serie
  de detector y electrónica (p. ej. DETSER 21903, entorno de prueba KASI).
* **`nonfunc/` (QR2) / `nonfunc_v2/` (QR3)**: máscara de píxeles muertos o calientes.
* **`nonlinear_pars/`** (~79 MB/archivo): coeficientes `Q_nl, b1, b2, b3, Qmax` de
  corrección de no-linealidad del pozo de píxel.
* **`readnoise_pars/`** (~48 MB/archivo): mapas `READNOISE-1/2` en electrones.
* **`solid_angle_pixel_map/`** → `cal-sapm-v3-2026-191/<1-6>/`: área de cielo por píxel
  (arcsec²); sirve para pasar de brillo superficial a flujo.
* **`spectral_wcs/`** → `cal-swcs-v5-2026-191/1/spectral_wcs_D1_spx_cal-swcs-v5-2026-191.fits`
  (31,8 MB): capas `CWAVE` (λ central por píxel) y `CBAND` (ancho de banda por píxel).
* **`spectral_channels/`**: los 17 canales espectrales por banda según posición focal.
* **`sip/`**: coeficientes polinómicos de distorsión astrométrica.
* **`abs_gain_matrix/`**: flat-field píxel a píxel entre y dentro de canales.
* **Solo QR3**: `aurora_template/`, `he_template/`, `shuttle_glow_template/`,
  `l3_flux_corrections/`, `xtalk_class1/2/`, `zodi_scaling_v2/` (p. ej.
  `cal-zodi-v2-2026-254/<1-6>/`, un ECSV de factores de escala del modelo de Kelsall
  por detector).

## 6. Qué NO hay en el bucket

Solo hay **Quick Releases de Nivel 2**. No están: Nivel 0/1 crudo (rampas, telemetría),
mosaicos de Nivel 3, ni catálogos de Nivel 4 (redshifts, hielos). Tampoco hay PNG/JPG
listos para web: el frontend tendrá que convertir los FITS (ver §7).

## 7. Para el challenge: qué descargar

* **Mínimo viable**: un FITS de `level2/` de QR3 + su `spectral_wcs` del mismo detector
  (para saber qué longitud de onda ve cada píxel). La extensión útil es `IMAGE`;
  `FLAGS` dice qué píxeles desconfiar y `ZODI` permite restar el fondo.
* **El «videíto» del challenge**: el mismo trozo de cielo en QR2 (2025) y en QR3 (2026):
  con ~1 año de separación, una estrella como Barnard ya se habrá movido varios
  píxeles (6,15″/píxel). Para localizarla, la vía oficial es la API SIA2/TAP de IRSA
  por coordenadas; el bucket solo se navega por semana/detector.
* **Cita obligatoria en publicaciones**: DOI `10.26131/IRSA652` (QR2);
  el DOI de QR3 aún estaba pendiente de asignación.

### Comandos de referencia

```bash
# Estructura sin descargar nada
aws s3 ls --no-sign-request s3://nasa-irsa-spherex/qr3/ --region us-east-1
aws s3 ls --no-sign-request s3://nasa-irsa-spherex/qr3/level2/2026W30_1B/l2b-v27-2026-222/ --region us-east-1

# Un FITS de ciencia (~63 MB)
aws s3 cp --no-sign-request --region us-east-1 \
  s3://nasa-irsa-spherex/qr3/level2/2026W30_1B/l2b-v27-2026-222/1/level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits .

# Su mapa espectral del detector 1 (~32 MB)
aws s3 cp --no-sign-request --region us-east-1 \
  s3://nasa-irsa-spherex/qr3/spectral_wcs/cal-swcs-v5-2026-191/1/spectral_wcs_D1_spx_cal-swcs-v5-2026-191.fits .
```

## Fuente

* Listados directos del bucket con AWS CLI el 2026-10-29 (carpetas, nombres y tamaños
  de este archivo son observados, no citados).
* Definiciones de productos y extensiones FITS:
  [spikes/spherex-satellite-architecture.md](spikes/spherex-satellite-architecture.md)
  (§2.3–2.4), [IRSA Data Products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/)
  y [IRSA Data Access](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/).
