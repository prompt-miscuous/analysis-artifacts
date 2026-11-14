# ADR-0005: Hosting del backend (PROPUESTA)

- **Estado:** proposed
- **Fecha:** 2026-11-14
- **Skills consulted:** [software-architecture] (sin dominios Android/LAN/audio involucrados)

## Contexto

El backend (`GET /frames`, uvicorn) está implementado y probado, pero sin
decisión de hosting. Requisitos del demo: una URL pública estable durante el
hackatón, salida a `irsa.ipac.caltech.edu`, tráfico bajo, costo mínimo.
El frontend ya está en S3+CloudFront (ADR-0002) y acepta `VITE_BACKEND_URL`.

## Decisión (propuesta, pendiente del equipo)

Desplegar en una **EC2 pequeña con systemd** (instancia free-tier, uvicorn en
puerto local + reverse proxy o puerto directo con security group mínimo),
añadiendo un módulo Terraform `live/backend/` que siga las convenciones del
repo `infra`.

## Alternativas consideradas

| Opción | Evaluación |
| --- | --- |
| EC2 + systemd (propuesta) | Free-tier, control total, ~1 h de trabajo; en contra: SSH + parches a mano |
| Portátil del equipo para el demo | Costo cero y cero trabajo; en contra: frágil (sueño, red, IP cambiante) |
| AWS App Runner / ECS | Cero ops SSH; en contra: cuesta dinero fuera del free tier y suma piezas |
| Co-ubicar en el bucket S3 | Imposible: S3 solo sirve estáticos, el backend es cómputo |

## Consecuencias

- A favor: URL estable, IRSA alcanzable (egreso directo, sin proxy de sandbox),
  permite la validación en vivo de Fase 4 contra el backend real.
- En contra: una pieza con estado (caché en disco efímero; aceptable: la caché
  se reconstruye sola).

## Reversal cost

Bajo: el servicio es un solo proceso uvicorn sin datos persistentes; moverlo
es levantar el mismo comando en otro host y cambiar `VITE_BACKEND_URL`.

## Evidence

Pendiente de aceptación del equipo (costo/ops). Ninguna medición bloquea:
el servicio arranca con un comando y su salud es `GET /health`.

## Validation

Sería errónea si el costo superara el free tier o si el equipo prefiriera
cero-ops aunque pague (entonces App Runner). Al aceptar, fijar instancia,
región y playbook de deploy en este ADR.
