# ADR-0004: Stack del backend (FastAPI + reproject)

- **Estado:** Aceptado
- **Fecha:** 2026-11-14
- **Skills consulted:** [software-architecture] (sin dominios Android/LAN/audio involucrados)

## Contexto

ADR-0003 decidió un backend Python intermedio con `GET /frames` pero difirió
el framework HTTP y la librería de reproyección a después del PoC gate, hoy
superado (`pocs/reproject-align/`: desvío 0,11 px < 1,5 px con `reproject`).
El backend debe validar parámetros espejo del frontend, descargar recortes en
paralelo (I/O-bound, MB por época), reproyectar, renderizar PNG, cachear en
disco y mapear errores al catálogo del contrato
(`docs/contrato-frames-v1.md` §2.3).

## Decisión

1. **HTTP: FastAPI + uvicorn**, endpoints síncronos (`def`) con
   `ThreadPoolExecutor` para descargas paralelas y `FileResponse` para PNGs.
2. **Reproyección: `reproject`** (`reproject_interp` sobre WCS astropy),
   validada en el gate.
3. **Render sin matplotlib en el servidor:** asinh + percentiles del PoC con
   codificación PNG vía PIL (más rápido, sin backend Agg).
4. **Tests herméticos con pytest:** fixtures sintéticos (VOTable escrito a
   mano, FITS generados); el pipeline acepta funciones de búsqueda/descarga
   inyectables para probarse de punta a punta sin IRSA.

## Alternativas consideradas

| Opción | Por qué se rechazó |
| --- | --- |
| Flask | Viable, pero sin validación ni docs automáticas; FastAPI da OpenAPI gratis al equipo frontend |
| Django / Django REST | Exceso para dos rutas sin modelos ni usuarios |
| `http.server` stdlib | Ahorra una dependencia a cambio de reescribir validación, routing y docs a mano |
| Reproyección afín manual | El WCS trae distorsión SIP; `reproject` la maneja vía astropy y ya pasó el gate |
| Render con matplotlib | Más lento y frágil en servidor; PIL basta para PNG en escala de grises |

## Consecuencias

- A favor: validación espejo centralizada, docs interactivas, descargas
  paralelas simples, tests sin red.
- En contra: dependencias nuevas (`fastapi`, `uvicorn`, `httpx`, `pytest`);
  los endpoints síncronos bloquean workers ante IRSA lento (aceptable para el
  tráfico del demo; timeouts + 504 acotan el daño).

## Reversal cost

Bajo: el núcleo (`irsa.py`, `reproject_align.py`, `render.py`, `pipeline.py`)
es Python puro sin importar FastAPI; cambiar de framework toca solo `main.py`.

## Evidence

- Gate Fase 0: `pocs/reproject-align/metrics.txt` (`result=PASS`).
- `pip install` de toda la pila verificado en este entorno.

## Validation

Sería errónea si la concurrencia del demo saturara los workers (pasar a
endpoints async) o si el peso de las dependencias impidiera el deploy elegido
(ADR de hosting pendiente, separado).
