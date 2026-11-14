# ADR-0003: Backend Python como proxy/procesador frente a IRSA

- **Estado:** Aceptado
- **Fecha:** 2026-11-14
- **Skills consulted:** [software-architecture] (sin dominios Android/LAN/audio involucrados)

## Contexto

Requisitos del visor (MVP del hackatón): dado RA/Dec/tamaño/banda, mostrar una
animación de épocas SPHEREx alineadas. IRSA expone los datos vía SIA2 (tabla
VOTable/XML) y recortes IBE (FITS multi-extensión de ~MB), sin cuadros
alineados ni video (ver `validacion-api-irsa-sia2-ibe.md` §5). El frontend es
un sitio estático React (ADR-0001) desplegado en S3+CloudFront (ADR-0002).
El PoC `pocs/render-fits/` demuestra en Python el pipeline buscar → recortar →
renderizar con `astropy`/`numpy`/`matplotlib`, y los tutoriales oficiales de
recortes de IRSA están en Python.

## Decisión

El navegador nunca habla con IRSA. Un backend Python intermedio expone
`GET /frames` (contrato en `docs/contrato-frames-v1.md`), traduce parámetros,
consulta SIA2, agrupa épocas por `obs_id`, descarga recortes IBE, reproyecta a
una cuadrícula norte-arriba común, renderiza PNG con asinh + max-pool, cachea
por (ra, dec, size, band, frames) y sirve manifiesto + imágenes.

## Alternativas consideradas

| Opción | Por qué se rechazó |
| --- | --- |
| Frontend directo a IRSA | El navegador tendría que parsear VOTable/FITS, descargar MB por frame, sufrir CORS y carece del ecosistema WCS/reproyección; además expone al usuario a la API profesional sin mediación |
| Ingerir el bucket S3 propio | Costo de ingesta masiva (~670 GB por semana-versión QR3) y reproceso frente a un reto que se resuelve con caché por demanda; se pierde la frescura semanal automática |
| Reutilizar la Spectrophotometry Tool de IRSA | Devuelve espectros por punto, no cuadros; trabajos asíncronos de minutos a horas sin API pública simple; resuelve el problema inverso (colapsa tiempo, necesitamos colapsar espectro) |
| Backend en Node | Duplicaría el PoC validado y carece de `astropy`/WCS/`reproject`; Python es además el lenguaje de los tutoriales oficiales |

## Consecuencias

- A favor: reutiliza el PoC tal cual como núcleo, caché propia, control de
  timeouts/reintentos, contrato simple para el frontend, frescura semanal heredada.
- En contra: un servicio más que desplegar y operar; dependencia de
  disponibilidad y límites no publicados de IRSA; el framework HTTP y el
  despliegue quedan como decisiones separadas (ver Validation).

## Reversal cost

Medio-bajo: el contrato `/frames` aísla al frontend de la implementación; el
núcleo (búsqueda/recorte/reproyección/render) es código Python puro
reutilizable aunque cambie el framework o el hosting. Revertir a ingesta
propia sí sería caro, pero nada de esta decisión lo impide después.

## Evidence

- `validacion-api-irsa-sia2-ibe.md`: SIA2 + IBE probados de punta a punta
  (`make_movie.py`, `movie_d3_demo.gif`, §6).
- PoC de reproyección de Fase 0 (gate): 3 épocas reales alineadas a grilla
  común sin saltos de rotación (ver `pocs/reproject-align/`).
- Tutoriales oficiales: `https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/`.

## Validation

Sería errónea si IRSA publicara cuadros ya alineados + video (haría el backend
innecesario), o si los límites de uso impidieran servir el demo (forzaría
ingesta propia o pre-render). El framework HTTP y el hosting del backend se
deciden en ADR separados y no invalidan esta decisión.
