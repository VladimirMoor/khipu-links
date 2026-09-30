"""Умножение в кипу: группа B = k · группа A (поразрядно), k = 2…20.

Пары групп одной длины (3–12) внутри одного кипу и между разными кипу (музейные номера разные).
Совпадение: ≥ 3 позиций, где A > 0 и B = k·A точно, и ≥ 2 разных ненулевых значения A среди них
(чтобы не считать повторы вроде [10, 10, 10]); B ≥ 10 в этих позициях. Фон: то же для
B = k·A + d (d = ±1…±3 — «почти кратно»), что сохраняет распределение значений.
Вывод: extracted/multiply.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/multiply.txt"


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        G[k] = [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    return G


def score(a, b, k, d=0):
    pos = [(x, y) for x, y in zip(a, b) if x > 0 and y >= 10 and y == k * x + d]
    if len(pos) >= 3 and len({x for x, _ in pos}) >= 2:
        return len(pos)
    return 0


def scan(G, mus, d=0, cross=False):
    hits = []
    items = [(k, i, g) for k, gs in G.items() for i, g in enumerate(gs) if 3 <= len(g) <= 12]
    byL = defaultdict(list)
    for it in items:
        byL[len(it[2])].append(it)
    for L, its in byL.items():
        for (ka, ia, a), (kb, ib, b) in itertools.permutations(its, 2):
            same = ka == kb
            if cross == same or (cross and mus[ka] == mus[kb]):
                continue
            for k in range(2, 21):
                s = score(a, b, k, d)
                if s:
                    hits.append((s, k, ka, ia + 1, a, kb, ib + 1, b))
    return hits


def main():
    G = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    mus = {k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper() for k in G}
    lines = []
    for cross in (False, True):
        real = scan(G, mus, 0, cross)
        null = [len(scan(G, mus, d, cross)) for d in (-3, -2, -1, 1, 2, 3)]
        lines.append(f"{'между кипу' if cross else 'внутри кипу'}: совпадений {len(real)}; фон (k·A ± d) {null}")
        for h in sorted(real, key=lambda h: (-h[0], h[1]))[:25]:
            s, k, ka, ia, a, kb, ib, b = h
            lines.append(f"   {s} ×{k:<2} {ka} г{ia} {a} → {kb} г{ib} {b}   | {meta.get(ka, {}).get('PROVENANCE')}")
        lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
