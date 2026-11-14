# PoC gate — cabeceras FITS por rango S3

**Resultado: VIABLE.** Leer la cabecera `IMAGE` de un FITS por rango S3
cuesta 64 KB y mediana 1,09 s secuencial (latencia pura). Con 24 workers,
una semana completa (~10.900 archivos) indexa en minutos, no horas.

## Medición (2026-11-14)

- Muestra: 20 archivos de `dr1/level2/2025W19_1B/l2b-v27-2026-197/3/` y
  `dr1/level2/2025W46_1A/l2b-v27-2026-206/3/`.
- 20/20 OK: centro WCS, esquinas y MJD (`DATE-OBS`) extraídos de un solo
  `Range: bytes=0-65535`.
- La cabecera `IMAGE` termina ~29 KB (primaria 2.880 B + ~26 KB), así que
  64 KB sobra en todos los casos observados.

## Reproducir

```bash
cd backend  # venv del backend (astropy + httpx)
.venv/bin/python ../analysis-artifacts/pocs/bucket-headers/poc_headers.py 20
```
