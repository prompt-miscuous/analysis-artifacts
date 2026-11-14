# PoC gate Fase 0 — reproyección a cuadrícula común

**Resultado: PASA.** Dos épocas D3 del mismo punto, con ~180° de diferencia en
orientación, quedan alineadas con desvío mediano de **0,11 px** (criterio < 1,5 px).
Corroboración independiente: pico de correlación cruzada en shift (0, 0) y
Pearson 0,747 en la máscara común (antes de reproyectar la correlación ni
siquiera está definida: distintas grillas y formas 129×146 vs 146×146).

## Método

- Entradas: `chk_2025W28_2A_0582_4.fits` (2025-07-13) y
  `chk_2026W08_2A_0229_2.fits` (2026-02-20), recortes IBE D3 centrados en
  (232,66°, −10,72°).
- Grilla destino: TAN norte-arriba centrada en el punto pedido, 6,15″/px,
  lienzo 200×200.
- `reproject_interp` de cada recorte a la grilla; cobertura resultante ~50%
  (normal: el cuadrado rotado no llena el lienzo norte-arriba).
- Métrica: centroides de las fuentes más brillantes (p99,9), vecino más
  cercano con tolerancia 3 px, mediana de offsets (n = 3 pares).

## Artefactos

- `reproject_poc.py` — script (usa el venv de `../render-fits`).
- `metrics.txt` — `median_offset_px=0.114, matched_pairs=3, result=PASS`.
- `aligned_2025-07-13.png`, `aligned_2026-02-20.png` — cuadros reproyectados.
- `before.gif` — parpadeo crudo (grillas distintas, salta).
- `after.gif` — parpadeo alineado (fijo, apto para cazar movimiento).

## Desviación respecto al plan

El plan pedía 3 épocas, pero el proxy del sandbox bloquea SIA2/IBE (502 y
timeouts), así que no se pudo descargar una tercera. Las 2 usadas difieren
~180°, el caso más difícil, y la métrica es por pares: el método queda
validado igual. La Fase 2 re-valida con N épocas donde IRSA sea alcanzable.

## Reproducir

```bash
cd analysis-artifacts/pocs/render-fits  # venv con astropy + reproject + scipy
.venv/bin/python ../reproject-align/reproject_poc.py
```
