"""Demo del 'videito' del challenge: 3 epocas de un punto -> GIF animado.

Uso:
    .venv/bin/python make_movie.py 232.66 -10.72 --detector 3 --size 0.25 --frames 3 -o movie.gif

1. Consulta SIA2 de IRSA por posicion.
2. Elige N epocas repartidas del detector pedido.
3. Descarga recortes (?center=&size=) y los renderiza con render.py.
4. Ensambla un GIF animado con PIL.
"""

import argparse
import io
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from render import load_image, max_pool, stretch_asinh

SIA_URL = "https://irsa.ipac.caltech.edu/SIA/spherex_qr3"
NS = "{http://www.ivoa.net/xml/VOTable/v1.3}"


def sia_query(ra, dec, radius, maxrec=500):
    qs = urllib.parse.urlencode(
        {"POS": f"CIRCLE {ra} {dec} {radius}", "MAXREC": maxrec}
    )
    with urllib.request.urlopen(f"{SIA_URL}?{qs}", timeout=60) as r:
        return r.read()


def pick_epochs(vot_bytes, detector, n):
    root = ET.fromstring(vot_bytes)
    fields = [f.get("name") for f in root.iter(NS + "FIELD")]
    seen = {}
    for row in root.iter(NS + "TR"):
        d = dict(zip(fields, [td.text for td in row.iter(NS + "TD")]))
        url = d.get("access_url") or ""
        if f"D{detector}_spx" not in url:
            continue
        oid = d.get("obs_id")
        if oid not in seen:
            seen[oid] = (float(d.get("t_min")), url)
    items = sorted(seen.items(), key=lambda kv: kv[1][0])
    if not items:
        raise SystemExit("Sin imagenes de ese detector en el punto")
    idx = np.linspace(0, len(items) - 1, min(n, len(items))).astype(int)
    return [items[i] for i in idx]


def cutout(url, ra, dec, size):
    q = urllib.parse.urlencode({"center": f"{ra},{dec}", "size": size})
    with urllib.request.urlopen(f"{url}?{q}", timeout=120) as r:
        return r.read()


def frame_png(fits_bytes, pool=2):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with open("/tmp/_frame.fits", "wb") as f:
        f.write(fits_bytes)
    img, _ = load_image("/tmp/_frame.fits")
    small = max_pool(img, pool)
    norm = stretch_asinh(small, 0.3, 0.5, 99.8)
    buf = io.BytesIO()
    plt.imsave(buf, norm, cmap="gray", origin="lower", format="png")
    return Image.open(buf).convert("L")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("ra", type=float)
    p.add_argument("dec", type=float)
    p.add_argument("--detector", type=int, default=3)
    p.add_argument("--size", type=float, default=0.25)
    p.add_argument("--radius", type=float, default=0.3)
    p.add_argument("--frames", type=int, default=3)
    p.add_argument("-o", "--output", default="movie.gif")
    a = p.parse_args()

    epochs = pick_epochs(sia_query(a.ra, a.dec, a.radius), a.detector, a.frames)
    imgs = []
    for oid, (tm, url) in epochs:
        print(f"epoca {oid} (MJD {tm:.2f}) ...", flush=True)
        try:
            imgs.append(frame_png(cutout(url, a.ra, a.dec, a.size)))
        except Exception as e:  # recorte fuera del footprint -> salta
            print(f"  salto ({e})")
    if len(imgs) < 2:
        raise SystemExit("Muy pocos cuadros validos")
    imgs[0].save(
        a.output, save_all=True, append_images=imgs[1:],
        duration=800, loop=0,
    )
    print(f"GIF guardado: {a.output} ({len(imgs)} cuadros)")


if __name__ == "__main__":
    main()
