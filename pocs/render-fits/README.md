# render-fits — FITS Level 2 de SPHEREx a PNG

Prueba de renderizado de una exposición de ciencia (`IMAGE` 2040×2040 en MJy/sr)
del bucket público `nasa-irsa-spherex` a una imagen visible en el navegador.

## Preparar el entorno

```bash
cd pcos/render-fits
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Descargar un FITS de prueba (62,8 MB, acceso anónimo)

```bash
aws s3 cp --no-sign-request --region us-east-1 \
  s3://nasa-irsa-spherex/qr3/level2/2026W30_1B/l2b-v27-2026-222/1/level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits \
  ./level2_test_D1.fits
```

Es QR3, detector 1, observado el 2026-07-20, apuntando a RA 232,66°, Dec −10,72°.

## Renderizar

```bash
.venv/bin/python render.py level2_test_D1.fits -o preview.png
```

Opciones: `--pool 4` (max-pool para conservar fuentes puntuales),
`--scale 0.3` (escala del arcsinh en MJy/sr), `--lo/--hi` (percentiles de corte),
`--cmap gray`, `--ext IMAGE`.

## Por qué así y no de otra forma

* El rango dinámico va de ~0,3 (fondo) a ~4000 (estrellas): un estiramiento lineal
  sale negro. El `arcsinh` alrededor del fondo es el estándar en astronomía.
* Sin max-pool, las estrellas de 1 píxel desaparecen al reescalar a tamaño web.
* Ojo con `FLAGS`: el 49 % de píxeles viene marcado, pero el grueso es un solo bit
  (`0x200000`, presumiblemente benigno). No enmascarar todo `!= 0` sin leer el
  *Explanatory Supplement*.
