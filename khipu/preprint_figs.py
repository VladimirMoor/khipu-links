"""Рисунки препринта (SVG): docs/preprint/fig1_map.svg … fig4_ur269.svg.

fig*_es.svg — те же рисунки с испанскими подписями.
fig1 — места находок и связи между кипу (site/data.json, береговая линия Natural Earth из site/land.json);
fig2 — доли распределения AS143 / AS149 в девятых (числа из §3.1);
fig3 — счёт диагонали для AS175 против UR233 и UR232 (huacho.diagonal, те же числа, что z = 6.4 и 19.5);
fig4 — вычет UR269 по месту записи в блоке (slotded.py).
"""
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/preprint"
sys.path.insert(0, str(ROOT / "khipu"))
FONT = 'font-family="Charter, Georgia, serif"'
INK, MUTED, ACC, CORD, LAND = "#1d1b19", "#6b665e", "#a3283d", "#8a6a4f", "#e9e8e1"
LANG = "en"
ES = {"Pacific Ocean": "Océano Pacífico", "ninths of the AS143 total (group 1 = 180,345)": "novenos del total de AS143 (grupo 1 = 180 345)",
      "vs": "frente a", "offset c (group of AS175 − group of {o})": "desfase c (grupo de AS175 − grupo de {o})", "place": "lugar",
      "deduction": "deducción", "sum of the": "suma de los", "five places:": "cinco lugares:"}
T = lambda x: ES.get(x, x) if LANG == "es" else x
SUF = lambda: "_es" if LANG == "es" else ""


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" {FONT} font-size="10">'
            + "".join(body) + "</svg>\n")


def fig1():
    D = json.load(open(ROOT / "site/data.json"))
    land = json.load(open(ROOT / "site/land.json"))
    lon0, lon1, lat0, lat1 = -78.6, -74.4, -10.75, -15.1
    W = 330
    k = W / ((lon1 - lon0) * math.cos(math.radians(12.5)))
    H = round((lat0 - lat1) * k)
    P = lambda lon, lat: ((lon - lon0) * math.cos(math.radians(12.5)) * k, (lat0 - lat) * k)
    b = [f'<defs><clipPath id="c"><rect width="{W}" height="{H}"/></clipPath></defs><rect width="{W}" height="{H}" fill="#f4f7f8"/><g clip-path="url(#c)">']
    for f in land["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly[:1]:
                d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in (P(*pt) for pt in ring)) + "Z"
                b.append(f'<path d="{d}" fill="{LAND}" stroke="#b9b6ac" stroke-width=".5"/>')
    site = {k["id"]: k["site"] for k in D["khipus"]}
    pair, inner = Counter(), Counter()
    for e in D["edges"]:
        a, c = site.get(e["from"]), site.get(e["to"])
        if a and c:
            if a == c:
                inner[a] += 1
            else:
                pair[tuple(sorted((a, c)))] += 1
    pos = {s["id"]: P(s["lon"], s["lat"]) for s in D["sites"]}
    for (a, c), n in pair.items():
        (x1, y1), (x2, y2) = pos[a], pos[c]
        mx, my = (x1 + x2) / 2 + (y2 - y1) * .3, (y1 + y2) / 2 - (x2 - x1) * .3
        b.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{ACC}" '
                 f'stroke-opacity=".8" stroke-width="{1 + math.sqrt(n):.1f}"/>')
    mx_n = max(s["n"] for s in D["sites"])
    lab = {"pachacamac": (6, 8), "huacho": (6, -2), "chancay": (6, 4), "lima": (-28, -2), "inkawasi": (6, 4), "huacones": (-60, 10),
           "paracas": (-54, 4), "ica": (6, 4), "ocucaje": (6, 6), "nazca": (6, 4), "tambocolorado": (6, 0)}
    for s in sorted(D["sites"], key=lambda s: -s["n"]):
        x, y = pos[s["id"]]
        r = 2 + 9 * math.sqrt(s["n"] / mx_n)
        b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{CORD}" fill-opacity=".8" stroke="#fff" stroke-width=".7"/>')
        if inner[s["id"]]:
            b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 2:.1f}" fill="none" stroke="{ACC}" stroke-width="1.2"/>')
        if s["id"] in lab:
            dx, dy = lab[s["id"]]
            b.append(f'<text x="{x + r + dx - 6 if dx > 0 else x + dx:.1f}" y="{y + dy:.1f}" fill="{INK}" '
                     f'stroke="#fff" stroke-width="2.5" paint-order="stroke">{s["label"].split(" (")[0]}</text>')
    b.append(f'<text x="24" y="{H * .8:.0f}" fill="{MUTED}" font-style="italic">{T("Pacific Ocean")}</text></g>')
    km = 100 / 111 * k
    b.append(f'<path d="M20,{H - 14} h{km:.1f}" stroke="{INK}" stroke-width="1.5"/><text x="{20 + km / 2:.1f}" y="{H - 18}" text-anchor="middle" font-size="9">100 km</text>')
    (OUT / f"fig1_map{SUF()}.svg").write_text(svg(W, H, b))


def fig2():
    W, H, x0, w = 460, 150, 92, 340
    b = []
    rows = [("AS143", [("g2", 1), ("g3", 2), ("g4 = AS149 g1 + g2", 4), ("g5", 2)], 18),
            ("AS149", [(None, 1), (None, 2), ("g1", 2), ("g2", 2), (None, 2)], 74)]
    for name, parts, y in rows:
        b.append(f'<text x="{x0 - 8}" y="{y + 17}" text-anchor="end" font-weight="bold">{name}</text>')
        x = x0
        for lab, n in parts:
            ww = w * n / 9
            if lab:
                b.append(f'<rect x="{x:.1f}" y="{y}" width="{ww - 2:.1f}" height="26" fill="{CORD}" fill-opacity="{.35 if "=" not in lab else .6}" stroke="{INK}" stroke-width=".6"/>')
                b.append(f'<text x="{x + ww / 2 - 1:.1f}" y="{y + 17}" text-anchor="middle">{lab}</text>')
            x += ww
    for i in range(10):
        xx = x0 + w * i / 9
        b.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="110" y2="114" stroke="{MUTED}"/>')
        b.append(f'<text x="{xx:.1f}" y="126" text-anchor="middle" fill="{MUTED}" font-size="9">{i}</text>')
    b.append(f'<line x1="{x0}" x2="{x0 + w}" y1="110" y2="110" stroke="{MUTED}"/>')
    b.append(f'<text x="{x0 + w / 2}" y="142" text-anchor="middle" fill="{MUTED}">{T("ninths of the AS143 total (group 1 = 180,345)")}</text>')
    x4 = x0 + w * 3 / 9
    b.append(f'<path d="M{x4:.1f},46 L{x4:.1f},72 M{x0 + w * 7 / 9 - 2:.1f},46 L{x0 + w * 7 / 9 - 2:.1f},72" stroke="{ACC}" stroke-dasharray="3 2"/>')
    (OUT / f"fig2_berlin{SUF()}.svg").write_text(svg(W, H, b))


def fig3():
    import csv
    import huacho as HU
    rows = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/kfg_cords.csv")):
        if r["inv_num"] in ("UR1175", "UR233", "UR232"):
            rows[r["inv_num"]].append(r)
    A = HU.groups("UR1175", rows)
    W, H = 460, 230
    b = []
    for row, other in enumerate(("UR233", "UR232")):
        D = HU.diagonal(A, HU.groups(other, rows))   # the same scores as huacho.py (z = 6.4 and 19.5)
        cs = sorted(D)
        y0, hh = 18 + row * 105, 70
        mx = max(D.values())
        x0, w = 50, 400
        bw = w / len(cs)
        best = max(cs, key=D.get)
        for i, c in enumerate(cs):
            v = D[c]
            h = hh * v / mx
            b.append(f'<rect x="{x0 + i * bw:.2f}" y="{y0 + hh - h:.1f}" width="{max(bw - .6, .5):.2f}" height="{h:.1f}" fill="{ACC if c == best else CORD}"/>')
        b.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{y0 + hh}" y2="{y0 + hh}" stroke="{MUTED}"/>')
        b.append(f'<text x="{x0 - 6}" y="{y0 + 8}" text-anchor="end" fill="{MUTED}" font-size="9">{mx}</text>')
        b.append(f'<text x="{x0 - 6}" y="{y0 + hh}" text-anchor="end" fill="{MUTED}" font-size="9">0</text>')
        b.append(f'<text x="{x0 + 4}" y="{y0 + 4}" font-weight="bold">AS175 {T("vs")} {other}</text>')
        b.append(f'<text x="{x0 + w / 2}" y="{y0 + hh + 14}" text-anchor="middle" fill="{MUTED}" font-size="9">{T("offset c (group of AS175 − group of {o})").format(o=other)}</text>')
    (OUT / f"fig3_huacho{SUF()}.svg").write_text(svg(W, H, b))


def fig4():
    out = subprocess.run([sys.executable, str(ROOT / "khipu/slotded.py")], capture_output=True, text=True).stdout
    place = {}
    for m in re.finditer(r"место (\d+): \[([^\]]*)\]", out):
        place[int(m.group(1))] = [int(x) for x in m.group(2).split(",")]
    W, H, x0, y0, hh = 520, 170, 50, 14, 120
    b = []
    ymax = 50
    Y = lambda v: y0 + hh - hh * v / ymax
    for v in (0, 10, 20, 30, 40, 50):
        b.append(f'<line x1="{x0}" x2="{x0 + 380}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#ddd"/>')
        b.append(f'<text x="{x0 - 6}" y="{Y(v) + 3:.1f}" text-anchor="end" fill="{MUTED}" font-size="9">{v}</text>')
    mode = {1: 47, 2: 46, 3: 46, 4: 44, 5: 25}
    for p in range(1, 6):
        cx = x0 + 40 + (p - 1) * 75
        cnt = Counter(place.get(p, []))
        for v, n in cnt.items():
            for j in range(n):
                xx = cx + (j - (n - 1) / 2) * 5
                b.append(f'<circle cx="{xx:.1f}" cy="{Y(v):.1f}" r="2.2" fill="{ACC if v == mode[p] else CORD}"/>')
        b.append(f'<text x="{cx}" y="{y0 + hh + 14}" text-anchor="middle">{T("place")} {p}</text>')
        b.append(f'<text x="{cx + 24}" y="{Y(mode[p]) + 3:.1f}" fill="{ACC}" font-size="9">{mode[p]}</text>')
    b.append(f'<text x="{x0 - 36}" y="{y0 + hh / 2}" transform="rotate(-90 {x0 - 36} {y0 + hh / 2})" text-anchor="middle" fill="{MUTED}">{T("deduction")}</text>')
    b.append(f'<text x="{x0 + 400}" y="{y0 + 40}" fill="{MUTED}" font-size="9">{T("sum of the")}</text>')
    b.append(f'<text x="{x0 + 400}" y="{y0 + 52}" fill="{MUTED}" font-size="9">{T("five places:")}</text>')
    b.append(f'<text x="{x0 + 400}" y="{y0 + 64}" fill="{ACC}" font-size="9">208</text>')
    (OUT / f"fig4_ur269{SUF()}.svg").write_text(svg(W, H, b))


if __name__ == "__main__":
    for LANG in ("en", "es"):
        fig1(); fig2(); fig3(); fig4()
    print("figures:", ", ".join(sorted(p.name for p in OUT.glob("fig*.svg"))))
