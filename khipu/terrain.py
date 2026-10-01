"""Сетка высот для 3D-карты атласа: site/terrain.json.

Источник: открытые Terrain Tiles (AWS Open Data, формат terrarium; Mapzen; данные SRTM, GMTED2010, ETOPO1 и др.),
https://registry.opendata.aws/terrain-tiles/ . Тайлы кешируются в data/terrain/ (не в git).
Сетка: равные шаги по долготе и широте (STEP градусов), значение = средняя высота в метрах по пикселям тайла,
попавшим в ячейку (океан — отрицательные глубины). Файл: {lon0, lat0, step, w, h, z: base64 int16 little-endian},
строки с севера на юг, столбцы с запада на восток.
"""
import base64
import json
import math
import struct
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/terrain"
OUT = ROOT / "site/terrain.json"
Z = 7
LON0, LON1, LAT0, LAT1 = -81.6, -68.0, -3.2, -22.2   # запад, восток, север, юг
STEP = 0.03
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def tile_xy(lon, lat):
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    la = math.radians(lat)
    y = (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n
    return x, y


def tile(x, y):
    p = CACHE / f"{Z}_{x}_{y}.png"
    if not p.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL.format(z=Z, x=x, y=y), p)
    im = Image.open(p).convert("RGB")
    return im.load()


def main():
    w = round((LON1 - LON0) / STEP)
    h = round((LAT0 - LAT1) / STEP)
    tiles = {}
    out = []
    S = 3  # подвыборка 3×3 точек на ячейку
    for j in range(h):
        row = []
        for i in range(w):
            acc = 0
            for a in range(S):
                for b in range(S):
                    lon = LON0 + (i + (b + .5) / S) * STEP
                    lat = LAT0 - (j + (a + .5) / S) * STEP
                    fx, fy = tile_xy(lon, lat)
                    tx, ty = int(fx), int(fy)
                    if (tx, ty) not in tiles:
                        tiles[(tx, ty)] = tile(tx, ty)
                    r, g, bl = tiles[(tx, ty)][min(255, int((fx - tx) * 256)), min(255, int((fy - ty) * 256))]
                    acc += r * 256 + g + bl / 256 - 32768
            row.append(max(-32000, min(32000, round(acc / S / S))))
        out.extend(row)
    raw = struct.pack(f"<{len(out)}h", *out)
    OUT.write_text(json.dumps({"lon0": LON0, "lat0": LAT0, "step": STEP, "w": w, "h": h,
                               "source": "Terrain Tiles (AWS Open Data; Mapzen; SRTM, GMTED2010, ETOPO1)",
                               "z": base64.b64encode(raw).decode()}))
    print(f"terrain {w}×{h}, {len(tiles)} tiles, max {max(out)} m, min {min(out)} m, {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
