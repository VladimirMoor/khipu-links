"""Одна и та же группа («лот») на двух разных кипу — как AS149 г4 = AS179 г1.

Группа (кластер) подвесных длиной 3–8, сумма ≥ MINSUM, ≥ 3 позиций со значением ≥ 10.
Две группы совпадают, если у них одна длина (или одна длиннее на одну позицию, которую
выбрасываем), все позиции равны с допуском max(1, 2%) и не меньше половины позиций равны
точно. Кипу с одинаковым музейным номером пропускаем (это дубли одной записи).
Фон — то же для группы B, позиции которой циклически сдвинуты на 1..L−1.
Вес совпадения — сумма log10 совпавших значений ≥ 10 (сколько «цифр» совпало).
"""
import csv
import itertools
import json
import math
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))
MINSUM, OUT = 100, ROOT / "extracted/lotmatch.txt"


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        out = []
        for gi, (_, g) in enumerate(itertools.groupby(rs, key=lambda r: r["group"]), 1):
            v = [int(r["value"]) for r in g]
            if 3 <= len(v) <= 8 and sum(v) >= MINSUM and sum(1 for x in v if x >= 10) >= 3:
                out.append((gi, v))
        if out:
            G[k] = out
    return G


def close(a, b):
    return abs(a - b) <= max(1, 0.02 * max(a, b))


def eq(u, v):
    if len(u) != len(v) or not all(close(a, b) for a, b in zip(u, v)):
        return None
    if 2 * sum(1 for a, b in zip(u, v) if a == b) < len(u):
        return None
    return sum(math.log10(a) for a, b in zip(u, v) if a >= 10)


def match(u, v):
    """Вес лучшего совпадения u и v (с выбросом одной позиции у более длинной) или None."""
    if len(u) == len(v):
        return eq(u, v)
    if abs(len(u) - len(v)) != 1:
        return None
    lo, hi = (u, v) if len(u) < len(v) else (v, u)
    ws = [eq(lo, hi[:i] + hi[i + 1:]) for i in range(len(hi))]
    ws = [w for w in ws if w is not None]
    return max(ws) if ws else None


def rot(v, r):
    return v[r:] + v[:r]


def main():
    G = load()
    meta = {k["INVESTIGATOR_NUM"]: k for k in json.load(open(ROOT / "extracted/kfg_khipus.json"))}
    museum = {k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "") for k in G}
    keys = sorted(G)
    hits, bg = [], defaultdict(int)
    for x, y in itertools.combinations(keys, 2):
        if museum[x] == museum[y]:
            continue
        for (gi, u), (gj, v) in itertools.product(G[x], G[y]):
            w = match(u, v)
            if w is not None:
                hits.append((w, x, gi, u, y, gj, v))
            for r in range(1, len(v)):
                wb = match(u, rot(v, r))
                if wb is not None:
                    bg[int(wb)] += 1.0 / (len(v) - 1)
    hits.sort(key=lambda t: -t[0])
    lines = [f"кипу: {len(keys)}, групп: {sum(len(v) for v in G.values())}, совпадений: {len(hits)}",
             "вес (сумма log10 совпавших значений): реальные / фон (сдвиг позиций, среднее)"]
    for t in range(0, 12):
        real = sum(1 for h in hits if int(h[0]) == t)
        if real or bg[t]:
            lines.append(f"  вес {t:2}–{t + 1:<2}: {real:5} / {bg[t]:7.1f}")
    lines.append("")
    pairs = defaultdict(list)
    for h in hits:
        pairs[(h[1], h[4])].append(h)
    lines.append("лучшие совпадения (вес ≥ 6):")
    for w, x, gi, u, y, gj, v in hits:
        if w < 6:
            break
        mx, my = meta.get(x, {}), meta.get(y, {})
        lines.append(f"{w:5.1f}  {x} г{gi} {u}  ~  {y} г{gj} {v}   | "
                     f"{mx.get('PROVENANCE')} #{mx.get('MUSEUM_NUM')} / {my.get('PROVENANCE')} #{my.get('MUSEUM_NUM')}"
                     f"   [групп в паре: {len(pairs[(x, y)])}]")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:80]))


if __name__ == "__main__":
    main()
