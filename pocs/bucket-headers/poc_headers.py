"""PoC gate Fase 0 (backend bucket): leer solo cabeceras FITS por rango S3.

Mide bytes/tiempo por archivo para extrapolar el costo de indexar el bucket.
La cabecera IMAGE termina ~29 KB; se pide un rango de 64 KB.

Uso: .venv/bin/python poc_headers.py [n_archivos]
"""

import io
import sys
import time

import httpx
import numpy as np
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS

BUCKET = "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com"
WEEKS = [
    "dr1/level2/2025W19_1B/l2b-v27-2026-197/3/",
    "dr1/level2/2025W46_1A/l2b-v27-2026-206/3/",
]
RANGE_BYTES = 65536


def list_keys(prefix, limit):
    """Lista claves .fits del prefijo vía ListObjectsV2 anónimo."""
    keys, token = [], None
    while len(keys) < limit:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "100"}
        if token:
            params["continuation-token"] = token
        r = httpx.get(f"{BUCKET}/", params=params, timeout=60)
        r.raise_for_status()
        import xml.etree.ElementTree as ET

        root = ET.fromstring(r.content)
        ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
        batch = [el.text for el in root.iter(ns + "Key")
                 if el.text.endswith(".fits")]
        keys.extend(batch)
        truncated = root.findtext(ns + "IsTruncated") == "true"
        token = root.findtext(ns + "NextContinuationToken")
        if not truncated:
            break
    return keys[:limit]


def read_image_header(key):
    r = httpx.get(f"{BUCKET}/{key}",
                  headers={"Range": f"bytes=0-{RANGE_BYTES - 1}"},
                  timeout=60)
    r.raise_for_status()
    return r.content


def footprint(header_bytes):
    with fits.open(io.BytesIO(header_bytes)) as hdul:
        hdr = hdul["IMAGE"].header
        w = WCS(hdr).celestial
        nx, ny = hdr["NAXIS1"], hdr["NAXIS2"]
        corners = w.all_pix2world(
            [[0, 0], [nx - 1, 0], [nx - 1, ny - 1], [0, ny - 1]], 0)
        center = w.all_pix2world([[nx / 2, ny / 2]], 0)[0]
        mjd = Time(hdr["DATE-OBS"]).mjd
    return center, corners, mjd


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    keys = []
    for prefix in WEEKS:
        keys.extend(list_keys(prefix, n // 2 + 1))
    keys = keys[:n]
    print(f"muestra: {len(keys)} archivos (rango {RANGE_BYTES} B c/u)")
    times, sizes = [], []
    ok = 0
    for key in keys:
        t0 = time.monotonic()
        try:
            data = read_image_header(key)
            center, corners, mjd = footprint(data)
            dt = time.monotonic() - t0
            times.append(dt)
            sizes.append(len(data))
            ok += 1
            print(f"  ok {dt:5.2f}s centro=({center[0]:.3f},{center[1]:.3f}) "
                  f"mjd={mjd:.2f} {key.split('/')[-1][:32]}")
        except Exception as exc:
            print(f"  FALLO {key.split('/')[-1][:32]}: {exc}")
    if times:
        med = float(np.median(times))
        print(f"\nOK {ok}/{len(keys)} | mediana {med:.2f}s/archivo | "
              f"{np.mean(sizes)/1024:.0f} KB/archivo")
        print(f"extrapolacion: 10.900 arch/semana -> "
              f"{10900 * med / 60:.1f} min/semana (secuencial)")


if __name__ == "__main__":
    main()
