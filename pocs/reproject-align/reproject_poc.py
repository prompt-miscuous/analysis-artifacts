"""PoC gate Fase 0: reproyectar recortes de distintas epocas a una cuadricula comun.

Criterio de exito (fijado antes de correr): tras reproyectar, las estrellas de
campo quedan alineadas con desvio mediano < 1.5 px y el GIF parpadeante no
muestra saltos de rotacion.

Uso:
    .venv/bin/python reproject_poc.py
    (usar el venv de ../render-fits, que ya trae astropy + reproject + scipy)
"""

import os

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_interp
from scipy.ndimage import center_of_mass, label

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_FITS = os.path.join(HERE, "..", "render-fits")

# Desviacion de este PoC respecto al plan: el sandbox bloquea las consultas
# SIA2/IBE (proxy 502/timeout), asi que no se pudo bajar una 3a epoca.
# Se usan las 2 epocas D3 disponibles en local, que difieren ~180 deg en
# orientacion: el caso mas dificil para la alineacion. La Fase 2 re-valida
# con N epocas donde IRSA sea alcanzable.
INPUTS = [
    ("2025-07-13", os.path.join(RENDER_FITS, "chk_2025W28_2A_0582_4.fits")),
    ("2026-02-20", os.path.join(RENDER_FITS, "chk_2026W08_2A_0229_2.fits")),
]

RA0, DEC0 = 232.66, -10.72          # centro pedido a IBE (grados)
PX_SCALE_DEG = 6.15 / 3600          # escala de pixel SPHEREx
SHAPE_OUT = (200, 200)              # lienzo comun (cubre el cuadrado rotado)
MAX_OFFSET_PX = 1.5                 # criterio de exito


def target_wcs():
    """Grilla comun: TAN, norte-arriba, centrada en el punto pedido."""
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [RA0, DEC0]
    w.wcs.crpix = [SHAPE_OUT[1] / 2 + 0.5, SHAPE_OUT[0] / 2 + 0.5]
    w.wcs.cd = [[-PX_SCALE_DEG, 0.0], [0.0, PX_SCALE_DEG]]
    return w


def load_cutout(path):
    with fits.open(path) as hdul:
        img = np.asarray(hdul["IMAGE"].data, dtype=np.float64)
        w = WCS(hdul["IMAGE"].header).celestial
    img[~np.isfinite(img)] = np.nan
    return img, w


def find_stars(img, n_max=60):
    """Centroides de las fuentes mas brillantes (ventana 7x7)."""
    thr = np.nanpercentile(img, 99.9)
    mask = np.isfinite(img) & (img > thr)
    lab, n = label(mask)
    if n == 0:
        return np.zeros((0, 2))
    fluxes = np.array([np.nansum(img[lab == i]) for i in range(1, n + 1)])
    order = np.argsort(fluxes)[::-1][:n_max]
    stars = []
    for i in order:
        ys, xs = np.nonzero(lab == i + 1)
        yc, xc = center_of_mass(img, lab, i + 1)
        y0, y1 = max(int(yc) - 3, 0), min(int(yc) + 4, img.shape[0])
        x0, x1 = max(int(xc) - 3, 0), min(int(xc) + 4, img.shape[1])
        cut = img[y0:y1, x0:x1]
        if cut.size == 0 or not np.isfinite(cut).any():
            continue
        cut = np.where(np.isfinite(cut), cut, 0.0)
        tot = cut.sum()
        if tot <= 0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        stars.append([(cut * xx).sum() / tot, (cut * yy).sum() / tot])
    return np.asarray(stars)


def match_offsets(a, b, tol=3.0):
    """Offset mediano entre estrellas vecinas mas cercanas (px)."""
    if len(a) == 0 or len(b) == 0:
        return np.nan, 0
    d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    j = d.argmin(1)
    offs = np.sqrt(((a - b[j]) ** 2).sum(1))
    good = offs[offs <= tol]
    if len(good) == 0:
        return np.nan, 0
    return float(np.median(good)), len(good)


def stretch(img):
    med = np.nanmedian(img)
    a = np.arcsinh((np.where(np.isfinite(img), img, med) - med) / 0.3)
    lo, hi = np.percentile(a, (0.5, 99.8))
    return np.clip((a - lo) / (hi - lo), 0, 1)


def to_pil(norm):
    return Image.fromarray((norm * 255).astype(np.uint8)).convert("L")


def main():
    twcs = target_wcs()
    raw_pngs, aligned_pngs, aligned = [], [], []
    print(f"lienzo comun: {SHAPE_OUT[1]}x{SHAPE_OUT[0]} norte-arriba "
          f"a {PX_SCALE_DEG * 3600:.2f}''/px")
    for date_obs, path in INPUTS:
        img, w = load_cutout(path)
        arr, footprint = reproject_interp((img, w), twcs, shape_out=SHAPE_OUT)
        arr[footprint < 0.5] = np.nan
        aligned.append(arr)
        raw_pngs.append(to_pil(stretch(img)))
        a_png = to_pil(stretch(arr))
        aligned_pngs.append(a_png)
        a_png.save(os.path.join(HERE, f"aligned_{date_obs}.png"))
        print(f"{date_obs}: {os.path.basename(path)} {img.shape} -> "
              f"cobertura {np.isfinite(arr).mean() * 100:.1f}%")

    stars = [find_stars(a) for a in aligned]
    print(f"estrellas detectadas: {[len(s) for s in stars]}")
    med, n = match_offsets(stars[0], stars[1])
    print(f"offset mediano entre epocas tras reproyectar: {med:.2f} px "
          f"(n={n} pares)")

    ok = np.isfinite(med) and med < MAX_OFFSET_PX
    print(f"CRITERIO (< {MAX_OFFSET_PX} px): {'PASA' if ok else 'FALLA'}")
    with open(os.path.join(HERE, "metrics.txt"), "w") as f:
        f.write(f"median_offset_px={med:.3f}\nmatched_pairs={n}\n"
                f"threshold_px={MAX_OFFSET_PX}\nresult={'PASS' if ok else 'FAIL'}\n")

    raw_pngs[0].save(os.path.join(HERE, "before.gif"), save_all=True,
                     append_images=raw_pngs[1:], duration=800, loop=0)
    aligned_pngs[0].save(os.path.join(HERE, "after.gif"), save_all=True,
                         append_images=aligned_pngs[1:], duration=800, loop=0)
    print("GIFs: before.gif (crudo, distintas grillas) / after.gif (alineado)")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
