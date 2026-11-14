# ADR-0001: Stack del frontend

- **Estado:** Aceptado
- **Fecha:** 2026-10-30
- **Skills consulted:** [software-architecture] (sin dominios Android/LAN/audio involucrados)
- **Issue:** [frontend#1](https://github.com/prompt-miscuous/frontend/issues/1)
- **Ubicación anterior:** `frontend/docs/adr-001-stack.md` (movido aquí: todos los ADR viven en este repo)

## Contexto

Requisitos del visor (MVP del hackatón): formulario de coordenadas (RA/Dec, tamaño,
banda), animación de cuadros PNG en orden temporal, consumo de `GET /frames` y un
deploy rápido para el demo. Restricciones: equipo pequeño, iteración en días, sin
necesidad de SSR ni estado distribuido.

## Decisión

React + Vite + Vitest (+ Testing Library) con npm como gestor de paquetes.

## Alternativas consideradas

| Opción | Por qué se descartó |
| --- | --- |
| Next.js (SSR) | Sin requisito de SSR; suma servidor y complejidad de deploy para un MVP estático |
| SvelteKit | Ecosistema menos conocido por el equipo; mayor riesgo en tiempo de hackatón |
| Vanilla JS + Vite | Viable, pero React da componentes testeables para formulario + visor con poco costo |

## Consecuencias

- A favor: HMR rápido, build estático simple de desplegar, un solo `vite.config.js`
  para app y tests, `package-lock.json` versionado como fuente de verdad.
- En contra: ninguna relevante para el MVP; toolchain de Node requerida en CI.

## Reversal cost

Bajo: el MVP son dos pantallas sin estado persistente; reescribir en otro stack
cuesta días, no semanas. Sin migración de datos.

## Evidence

Decisión dirigida por el stakeholder (dueño del producto) el 2026-10-30 con los
criterios de velocidad de iteración y ecosistema conocido. Sin PoC: todas las
alternativas tienen factibilidad documentada y sobrada para el alcance.

## Validation

Esta decisión sería errónea si apareciera un requisito de SSR/SEO o de tiempo real
colaborativo; en ese caso se re-evalúa (ver ADR futuro).
