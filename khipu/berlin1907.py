"""Берлинская партия 1907 г. (Ascher & Ascher 1978: список при AS100 + AS147–149):
поиск связей между кипу внутри партии.

(1) Векторный поиск слагаемых для групп AS143 (UR1143): 4-шнуровые группы выравниваются
    на 5 позиций с пустой 4-й (как у Ашеров). Кандидаты — любая группа или сумма 2–3 групп
    (из любых кипу партии, кроме самой AS143), совпадение позиций с допуском в 1 узел.
(2) Скалярный поиск: шнур (свой / с дочерними) одной кипу = итог группы, итог 2–8 подряд
    идущих групп или итог всей другой кипу партии (значения ≥ MINV). Фон — перемешивание
    значений подвесных внутри партии (структура групп сохраняется).
"""
import csv
import itertools
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH_AS = {100, 103, 105, 109, 115, 116, 117, 120, 123, 126, 129, 135, 138, 141, 142, 143, 146,
            150, 152, 161, 162, 164, 166, 171, 179, 180, 147, 148, 149}
MINV = 100


def batch_names():
    out = {}
    for r in csv.DictReader(open(ROOT / "data/kfg/kfg_article/data/khipu_summary.csv")):
        m = re.match(r"AS(\d+)", r["original_name"] or "")
        if m and int(m.group(1)) in BATCH_AS and r["provenance"] in ("Ica", "Ocucaje"):
            out[r["kfg_name"]] = "AS" + m.group(1)
    return out


def load(names):
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/kfg_cords.csv")):
        if r["inv_num"] in names:
            by[r["inv_num"]].append(r)
    K = {}
    for inv, rows in by.items():
        kids = defaultdict(list)
        for r in rows:
            kids[r["parent_id"]].append(r)
        memo = {}

        def tree(r):
            if r["cord_id"] not in memo:
                memo[r["cord_id"]] = int(r["value"]) + sum(tree(c) for c in kids.get(r["cord_id"], []))
            return memo[r["cord_id"]]
        top = sorted(kids.get("", []), key=lambda r: int(r["order"]))
        groups = [[(int(r["value"]), tree(r)) for r in g] for _, g in itertools.groupby(top, key=lambda r: r["group"])]
        K[inv] = groups
    return K


def one_knot(a, b):
    if a == b:
        return True
    if a == 0 or b == 0:
        return False
    da, db = str(a).zfill(6), str(b).zfill(6)
    diff = [(x, y) for x, y in zip(da, db) if x != y]
    return len(diff) == 1 and abs(int(diff[0][0]) - int(diff[0][1])) == 1


def to5(g):
    v = [x for x, _ in g]
    if len(v) == 5:
        return v
    if len(v) == 4:
        return v[:3] + [None] + v[3:]
    return None


def vector_search(K, names):
    T = next(k for k in K if names[k] == "AS143")
    tg = [to5(g) for g in K[T]]
    print("AS143 группы (5 позиций):", tg[:5])
    cand = []
    for k, gs in K.items():
        if k == T:
            continue
        for gi, g in enumerate(gs):
            v = to5(g)
            if v:
                cand.append(((names[k], gi + 1), v))
    print(f"групп-кандидатов в партии (4–5 шнуров): {len(cand)}")
    for ti in (1, 2, 4):  # группы 2, 3, 5
        target = tg[ti]
        best = []
        for r in (1, 2, 3):
            for combo in itertools.combinations(cand, r):
                s = []
                for p in range(5):
                    if target[p] is None:
                        s.append(None)
                        continue
                    xs = [c[1][p] for c in combo]
                    s.append(None if any(x is None for x in xs) else sum(xs))
                hits = sum(1 for p in range(5) if target[p] and s[p] is not None and one_knot(s[p], target[p]))
                nz = sum(1 for p in range(5) if target[p])
                if hits >= 2:
                    best.append((hits, nz, [c[0] for c in combo], s))
        best.sort(key=lambda x: -x[0])
        print(f"\nAS143 группа {ti+1} = {target}: лучшие кандидаты")
        for b in best[:5]:
            print(f"   {b[0]}/{b[1]} позиций  {b[2]}  сумма {b[3]}")


def scalar_units(K, names):
    """Единицы-«итоги»: группы, серии групп, кипу; и «шнуры»."""
    totals, cords = [], []
    for k, gs in K.items():
        n = names[k]
        for gi, g in enumerate(gs):
            for ci, (o, t) in enumerate(g):
                cords.append((o, n, f"g{gi+1}c{ci+1}"))
                if t != o:
                    cords.append((t, n, f"g{gi+1}c{ci+1}+sub"))
        gsum = [sum(o for o, _ in g) for g in gs]
        for i in range(len(gs)):
            if len(gs[i]) >= 2:
                totals.append((gsum[i], n, f"группа {i+1}"))
            for j in range(i + 1, min(len(gs), i + 8)):
                totals.append((sum(gsum[i:j + 1]), n, f"группы {i+1}–{j+1}"))
        totals.append((sum(gsum), n, "вся кипу"))
    return totals, cords


def scalar_hits(K, names):
    totals, cords = scalar_units(K, names)
    idx = defaultdict(list)
    for v, n, w in cords:
        if v >= MINV:
            idx[v].append((n, w))
    H = set()
    for v, n, w in totals:
        if v >= MINV:
            for n2, w2 in idx.get(v, ()):
                if n2 != n:
                    H.add((v, n, w, n2, w2))
    return H


def main():
    names = batch_names()
    K = load(set(names))
    print(f"кипу партии в корпусе: {len(K)}")
    vector_search(K, names)
    H = scalar_hits(K, names)
    print(f"\nСкалярные связи «итог одной кипу = шнур другой» (≥{MINV}): {len(H)}")
    for h in sorted(H, key=lambda x: -x[0])[:40]:
        print(f"   {h[0]:6}  {h[1]} {h[2]}  =  {h[3]} {h[4]}")
    rng = random.Random(7)
    null = []
    allv = [c for gs in K.values() for g in gs for c in g]
    for _ in range(300):
        s = allv[:]
        rng.shuffle(s)
        it = iter(s)
        Ks = {k: [[next(it) for _ in g] for g in gs] for k, gs in K.items()}
        null.append(len(scalar_hits(Ks, names)))
    null.sort()
    p = (sum(1 for x in null if x >= len(H)) + 1) / 301
    print(f"фон: среднее {sum(null)/len(null):.1f}, 95% {null[284]}, макс {null[-1]} → p = {p:.3f}")


if __name__ == "__main__":
    main()
