# Contrato compartido v1 — frontend ↔ backend (`GET /frames`)

Fuente única de verdad para unidades, bandas, límites y formato de intercambio.
Congelado en Fase 0. Cualquier cambio posterior a estos valores exige actualizar
este documento y los tests de ambos lados.

## 1. Glosario de dominio (valores canónicos)

### 1.1 Bandas espectrales SPHEREx

El selector de banda ofrece los 6 detectores. `W1`/`W2` son bandas de WISE y
**no existen** en este proyecto. Rangos según la Guía IRSA 2026 (ver
[spikes/spherex-satellite-architecture.md](spikes/spherex-satellite-architecture.md)):

| Banda | Detector | Rango (µm) | `BAND` SIA2 (m) |
| --- | --- | --- | --- |
| D1 | 1 | 0,75 – 1,09 | `9.0e-7` |
| D2 | 2 | 1,10 – 1,62 | `1.3e-6` |
| D3 | 3 | 1,63 – 2,41 | `2.0e-6` |
| D4 | 4 | 2,42 – 3,82 | `3.0e-6` |
| D5 | 5 | 3,83 – 4,41 | `4.1e-6` |
| D6 | 6 | 4,42 – 5,00 | `4.7e-6` |

El backend traduce `band=Dn` al valor `BAND` de la tabla. SIA2 filtra a
granularidad de detector, no de canal exacto (ver
[validacion-api-irsa-sia2-ibe.md](validacion-api-irsa-sia2-ibe.md) §5.1).

### 1.2 Tamaño de región

- **Unidad: grados decimales.** Es la unidad que consume IBE (`size=`) y la que
  viaja en la URL y en la API. No hay conversión de unidades en el MVP.
- **Presets:** `0.10` / `0.25` / `0.50` / `1.00` (grados).
- **Rango permitido:** mínimo `0.05`, máximo `1.00`, siempre `> 0`.
- **Default:** `0.25` (= 900″ ≈ 146×146 px a 6,15″/px, [PROBADO]).
- El máximo existe por cortesía con IRSA: recortes mayores multiplican peso y
  tiempo de descarga por cada época.

### 1.3 Coordenadas y objeto default

- RA en grados `[0, 360]`, Dec en grados `[-90, +90]`.
- Default: **WISE 0855** con coordenadas de catálogo J2000 convertidas:
  - `ra = 133.7951`, `dec = -7.2451`
  - Derivación: AR 08h 55m 10,83s → 133,795125°; Dec −07° 14′ 42,5″ → −7,245139°.
  - Nota: el brief original del frontend usaba `133.98`, valor erróneo que deja
    al objeto fuera de un recorte de 0,25° (desvío de 665″ frente a un
    semilado de 450″). El enlace de WiseView usa 133,7897 (posición propagada
    por movimiento propio); se elige el valor de catálogo por ser el
    documentado, y el radio de búsqueda 0,3° cubre el desplazamiento igual.
- Radio de búsqueda SIA2 fijo en backend: `0.3` grados (no expuesto al usuario
  en el MVP).

### 1.4 Cuadros (frames)

- **Default:** `5` épocas. **Mínimo:** `2`. **Máximo:** `12`.
- El backend elige N épocas repartidas en el tiempo disponible; si hay menos
  épocas válidas que las pedidas, devuelve las que haya y lo declara en el
  manifiesto (no falla salvo que haya < 2).

### 1.5 Constantes físicas de referencia

- Escala de píxel: **6,15 ″/px**. Campo por detector: 3,5° × 3,5°.
- Detectores co-apuntados: D1&D4, D2&D5, D3&D6 (mismo `obs_id`, filas separadas).

## 2. API del backend v1

### 2.1 `GET /frames`

```text
GET /frames?ra=133.7951&dec=-7.2451&size=0.25&band=D3&frames=5
```

| Parámetro | Tipo | Validación espejo del frontend |
| --- | --- | --- |
| `ra` | número | 0 – 360, obligatorio |
| `dec` | número | −90 – +90, obligatorio |
| `size` | número | 0,05 – 1,00, obligatorio |
| `band` | texto | uno de `D1`…`D6`, obligatorio |
| `frames` | entero | 2 – 12, opcional (default 5) |

### 2.2 Manifiesto de respuesta (200)

```json
{
  "params": {"ra": 133.7951, "dec": -7.2451, "size": 0.25, "band": "D3", "frames": 5},
  "grid": {"crs": "north-up", "pixel_scale_arcsec": 6.15, "width": 146, "height": 146},
  "epochs_available": 9,
  "frames": [
    {"obs_id": "2025W28_2A_0582_4", "mjd": 60869.72, "date_obs": "2025-07-13T17:19:27",
     "detector": 3, "png_url": "/frames/abc123/00.png", "width": 146, "height": 146,
     "warning": null}
  ],
  "warnings": ["epoch 2025W28_2A_0582_4: cutout truncated at detector edge"]
}
```

- `frames` ordenados por `mjd` ascendente. Todos comparten la cuadrícula `grid`.
- `png_url` puede ser ruta relativa al backend o URL firmada; el frontend no
  construye URLs de imágenes por su cuenta.

### 2.3 Catálogo de errores

| HTTP | `code` | Cuándo |
| --- | --- | --- |
| 400 | `invalid_params` | parámetro fuera de rango o banda inválida (incl. `W1`) |
| 404 | `no_coverage` | IRSA no tiene imágenes de esa banda en ese punto |
| 422 | `few_epochs` | hay cobertura pero < 2 épocas válidas |
| 502 | `irsa_unavailable` | IRSA no responde o tarda más que el timeout |
| 504 | `irsa_timeout` | descarga/render excede el presupuesto de tiempo |

Cuerpo de error: `{"code": "...", "message": "...legible..."}`.

## 3. Parámetros de URL del navegador

La UI refleja su estado en la URL con los **mismos nombres y unidades**:

```text
?ra=133.7951&dec=-7.2451&size=0.25&band=D3
```

(`frames` no viaja en la URL en el MVP; es ajuste de sesión del visor.)
Reglas: sincronizar con `history.replaceState` sin recargar; al cargar,
validar antes de aplicar; si faltan o son inválidos, usar defaults y avisar.
