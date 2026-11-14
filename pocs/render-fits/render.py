"""Renderiza la extension IMAGE de un FITS Level 2 de SPHEREx a PNG.

Receta: max-pool para conservar fuentes puntuales + estiramiento arcsinh
alrededor del fondo (el rango dinamico ~0.3 -> 4000 aplasta el lineal).

Uso:
    python render.py level2_test_D1.fits -o preview.png
"""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits


def load_image(path, ext="IMAGE"):
    with fits.open(path) as f:
        hdu = f[ext]
        img = np.asarray(hdu.data, dtype=np.float64)
        header = dict(hdu.header)
    img[~np.isfinite(img)] = 0.0
    return img, header


def max_pool(img, factor):
    h, w = img.shape
    h, w = h // factor * factor, w // factor * factor
    return img[:h, :w].reshape(h // factor, factor, w // factor, factor).max(axis=(1, 3))


def stretch_asinh(img, scale, lo_p, hi_p):
    med = np.median(img)
    a = np.arcsinh((img - med) / scale)
    lo, hi = np.percentile(a, (lo_p, hi_p))
    return np.clip((a - lo) / (hi - lo), 0, 1)


def main():
    p = argparse.ArgumentParser(description="FITS SPHEREx Level 2 -> PNG")
    p.add_argument("fits", help="Archivo .fits de entrada")
    p.add_argument("-o", "--output", default="preview.png", help="PNG de salida")
    p.add_argument("--ext", default="IMAGE", help="Extension a renderizar")
    p.add_argument("--pool", type=int, default=4, help="Factor de max-pool")
    p.add_argument("--scale", type=float, default=0.3, help="Escala del arcsinh (MJy/sr)")
    p.add_argument("--lo", type=float, default=0.5, help="Percentil bajo del corte")
    p.add_argument("--hi", type=float, default=99.8, help="Percentil alto del corte")
    p.add_argument("--cmap", default="gray", help="Mapa de color de matplotlib")
    args = p.parse_args()

    img, header = load_image(args.fits, args.ext)
    for k in ("CRVAL1", "CRVAL2", "DATE-OBS", "DETECTOR"):
        if k in header:
            print(f"{k} = {header[k]}")
    print(f"shape={img.shape} fondo~{np.median(img):.3f} "
          f"p99={np.percentile(img, 99):.3f} max={img.max():.1f}")

    small = max_pool(img, args.pool)
    norm = stretch_asinh(small, args.scale, args.lo, args.hi)
    plt.imsave(args.output, norm, cmap=args.cmap, origin="lower")
    print(f"PNG guardado: {args.output} ({small.shape[0]}x{small.shape[1]})")


if __name__ == "__main__":
    main()
