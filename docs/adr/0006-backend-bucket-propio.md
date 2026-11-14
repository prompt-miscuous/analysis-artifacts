# ADR-0006: Backend propio sobre el bucket S3 (supersede la fuente de ADR-0003)

- **Estado:** Aceptado
- **Fecha:** 2026-11-14
- **Skills consulted:** [software-architecture] (sin dominios Android/LAN/audio involucrados)

## Contexto

ADR-0003 eligió SIA2+IBE de IRSA como fuente. En la práctica, la búsqueda
SIA con radio 0,3° tarda >90 s y muere en timeouts/502 tras proxies (medido
2026-11-14: radio 0,05 responde en 1,3 s; radio 0,30 no responde), dejando el
demo a merced de un servicio pensado para consultas interactivas chicas.
El bucket público `s3://nasa-irsa-spherex` (us-east-1, acceso anónimo)
contiene los mismos FITS de Nivel 2 (`dr1/`, `qr2/`, `qr3/`), pero organizado
por semana/versión/detector, sin índice espacial.

Medición gate (PoC `pocs/bucket-headers/`): leer la cabecera IMAGE de un
FITS por rango S3 cuesta 64 KB y mediana 1,09 s secuencial; paralelizable.

## Decisión

Construir índice espacial propio (SQLite: footprint WCS por archivo, leído
por rangos) y servir `/frames` desde el bucket: buscar en el índice, bajar
FITS de S3, recortar local y reutilizar reproyección/render/caché actuales.
La fuente se elige con `FRAMES_PROVIDER=bucket|irsa` (default `bucket`);
SIA queda como fallback comparable. El contrato v1 no cambia.

## Alternativas consideradas

| Opción | Por qué se rechazó |
| --- | --- |
| Seguir con SIA como principal | Consultas pesadas >90 s / 502 tras proxies; sin control de latencia ni caché de búsqueda |
| TAP como principal | Mismo destino tras proxies en las pruebas; queda como ruta oficial documentada, no implementada |
| Ingerir y re-publicar los FITS | Duplicar ~670 GB/semana no aporta: basta índice + descarga por demanda con caché |
| Índice en servicio externo (Athena, etc.) | Piezas nuevas sin necesidad: SQLite local alcanza para bounding-box + punto-en-polígono |

## Consecuencias

- A favor: latencia de búsqueda local y predecible, sin límites de IRSA, mismo
  contrato y frontend intactos, descarga S3 rápida desde AWS us-east-1.
- En contra: hay que construir y refrescar el índice (semanal, incremental);
  la cobertura es solo la indexada (alcance inicial: semanas DR1 del set
  dorado; se amplía por semanas); petición fría baja FITS de ~65 MB por época.

## Reversal cost

Bajo: el flag de proveedor vuelve a SIA sin tocar frontend ni contrato; el
índice es un archivo SQLite desechable y reconstruible.

## Evidence

- `pocs/bucket-headers/poc_headers.py`: 20/20 cabeceras OK, 64 KB/archivo.
- Inventario vivo 2026-11-14: prefijos `dr1/` (110 semanas), `qr2/` (129),
  `qr3/` (41); ~1.812 FITS por detector-semana.
- Set dorado SIA (radio 0,05, 1,3 s): WISE 0855/D3 incluye
  `2025W19_1B_0116_1` y `2025W46_1A_0075_4` (DR1).

## Validation

Sería errónea si IRSA estabilizara SIA para consultas pesadas (el flag
permite volver sin costo) o si el costo de indexar/refrescar superara el
beneficio frente a SIA con radio chico (medido en el gate: no, con workers).
