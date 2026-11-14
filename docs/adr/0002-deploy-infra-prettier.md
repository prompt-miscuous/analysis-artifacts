# ADR-0002: Deploy del frontend y repo de infraestructura

- **Estado:** Aceptado
- **Fecha:** 2026-10-30
- **Skills consulted:** [software-architecture] (sin dominios Android/LAN/audio involucrados)
- **Issue:** [frontend#2](https://github.com/prompt-miscuous/frontend/issues/2) (criterio deploy preview)

## Contexto

El MVP necesita una URL pública del visor para el demo del hackatón: sitio
estático (build de Vite), tráfico bajo, costo mínimo y deploy repetible. Además
hay que decidir dónde vive el código de infraestructura (Terraform) y con qué se
formatea el frontend.

## Decisión

1. **Hosting:** S3 + CloudFront en AWS (tier gratuito), via Terraform.
2. **Infra como código:** repo nuevo `prompt-miscuous/infra`, con módulos
   reutilizables (el primero: sitio estático S3+CloudFront).
3. **Formato:** Prettier como formateador del frontend (oxlint sigue como linter).

## Alternativas consideradas

| Opción | Por qué se descartó |
| --- | --- |
| Vercel/Netlify/GitHub Pages | Deploy más simple, pero el equipo eligió AWS para alinear con el resto del stack y practicar IaC |
| Infra por servicio (`frontend/infra/`) | Duplica config y parte el estado de Terraform; un repo único da un solo estado y módulos compartidos |
| Biome como formatter | Viable, pero el equipo pidió Prettier explícitamente (estándar conocido) |

## Consecuencias

- A favor: costo ~0 en tier gratuito, CDN global, deploys repetibles con Terraform,
  formato consistente con Prettier.
- En contra: primer deploy exige bootstrap (bucket de estado, `terraform apply`
  manual); más piezas que un hosting zero-config.

## Reversal cost

Bajo: el build es estático; moverlo a otro hosting es cambiar el destino del
`dist/` y borrar el stack. El repo `infra` se archiva sin afectar código.

## Evidence

Decisión dirigida por el stakeholder el 2026-10-30. Free tier de AWS cubre el
tráfico esperado del demo. Terraform v1.15 disponible y credenciales verificadas
(`sts:get-caller-identity` OK).

## Validation

Sería errónea si el costo superara el tier gratuito o si el equipo necesitara
previews por PR sin fricción; entonces se re-evalúa con hosting zero-config.
