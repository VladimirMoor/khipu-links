"""Векторные суммы между кипу с учётом обрывов (продолжение vecsum.py).

Группа B (3–12 шнуров) = поразрядная сумма нескольких групп A другого кипу (подряд 2–10 или с
шагом 2–4), если: во всех позициях, где ни шнур B, ни одно из слагаемых не оборваны, значения
равны точно; таких позиций ≥ 3 со значением ≥ 10; позиции с обрывом могут расходиться, но
значение оборванного шнура не больше «правильного» (обрыв отнимает, а не прибавляет).
Фон: все значения B сдвинуты на +d (d = 1, 2, 3, 5, 7) в целых позициях. Вывод:
extracted/vecsum_broken.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/vecsum_broken.txt"


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        G[k] = [[(int(r["value"]), r["termination"] == "B") for r in g]
                for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    return G


def sums(gs):
    byL = defaultdict(list)
    for i, g in enumerate(gs):
        if 3 <= len(g) <= 12:
            byL[len(g)].append(i)
    out = []
    for L, idx in byL.items():
        sels = []
        for a in range(len(idx)):
            for b in range(a + 2, min(len(idx), a + 10) + 1):
                sel = idx[a:b]
                if sel[-1] - sel[0] == len(sel) - 1:
                    sels.append(sel)
        for t in (2, 3, 4):
            for s in range(len(gs)):
                sel, j = [], s
                while j < len(gs) and len(gs[j]) == L and len(sel) < 8:
                    sel.append(j)
                    if len(sel) >= 2:
                        sels.append(list(sel))
                    j += t
        for sel in sels:
            v = tuple(sum(gs[i][p][0] for i in sel) for p in range(L))
            br = tuple(any(gs[i][p][1] for i in sel) for p in range(L))
            out.append((v, br, sel))
    return out


def match(b, v, br, d=0):
    exact = 0
    for (x, xb), y, yb in zip(b, v, br):
        if xb or yb:
            if xb and x + (d if not xb else 0) > y:
                return 0
            continue
        if x + d != y:
            return 0
        if x >= 10:
            exact += 1
    return exact


def main():
    G = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    # индекс сумм по длине и первой целой позиции для скорости
    S = defaultdict(list)          # (длина, позиция, значение) -> суммы
    for k, gs in G.items():
        for v, br, sel in sums(gs):
            for p in range(len(v)):
                if not br[p] and v[p] >= 10:
                    S[(len(v), p, v[p])].append((k, v, br, sel))

    def scan(d):
        hits = []
        for y, gs in G.items():
            for j, b in enumerate(gs):
                if not 3 <= len(b) <= 12 or sum(1 for x, xb in b if x >= 10 and not xb) < 3:
                    continue
                keys = [p for p, (x, xb) in enumerate(b) if x >= 10 and not xb][:2]
                cand = {}
                for p in keys:
                    for c in S.get((len(b), p, b[p][0] + d), []):
                        cand[(c[0], tuple(c[3]))] = c
                for k, v, br, sel in cand.values():
                    if k == y or mus(k) == mus(y):
                        continue
                    e = match(b, v, br, d)
                    if e >= 3 and (any(xb for _, xb in b) or any(br)):
                        hits.append((e, y, j + 1, [x for x, _ in b], k, [i + 1 for i in sel], list(v)))
        return hits

    real = scan(0)
    nulls = [len(scan(d)) for d in (1, 2, 3, 5, 7)]
    lines = [f"совпадений с обрывами (≥ 3 точных целых позиций ≥ 10, остальные — оборванные): {len(real)}; "
             f"фон {nulls}"]
    for e, y, j, b, k, sel, v in sorted(real, reverse=True)[:40]:
        lines.append(f"  {e}  {y} г{j} {b}  ~  {k} г{sel} {v}   | {meta.get(y, {}).get('PROVENANCE')} / {meta.get(k, {}).get('PROVENANCE')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
