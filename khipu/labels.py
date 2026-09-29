"""Шнуры-ярлыки: «подпись» в начале кипу и постоянные графы.

1. Подпись. Для каждой пары кипу одной provenance: совпадают ли первые K подвесных (как
   последовательность значений, K = 1..3, не все нули)? Сравниваем долю совпадений у пар одной
   provenance с парами разных provenance и с тем же тестом на случайном окне из K подвесных
   (фон «место в кипу не важно»). Проверка на известном: Пуручуко (Urton & Brezine 2005).
2. Постоянная графа. Кипу с ≥ 5 группами одной длины L ≥ 3: позиция, где одно ненулевое
   значение стоит в ≥ 80% групп, тогда как в группе есть и другие значения. Фон — значения
   перемешаны между группами внутри каждой позиции? Нет: такое перемешивание сохраняет
   столбец. Фон — перемешивание значений внутри каждой группы (позиции разрушены).
Вывод: extracted/labels.txt.
"""
import csv
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/labels.txt"


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    P, G = {}, {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        P[k] = [int(r["value"]) for r in rs]
        G[k] = [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    return P, G


def signature(P, prov, K, rnd, random_window=False):
    same = diff = hs = hd = 0
    keys = [k for k in P if len(P[k]) >= K + 5]
    start = {k: (rnd.randrange(0, len(P[k]) - K) if random_window else 0) for k in keys}
    win = {k: tuple(P[k][start[k]:start[k] + K]) for k in keys}
    for x, y in itertools.combinations(keys, 2):
        if not any(win[x]):
            continue
        h = win[x] == win[y]
        if prov[x] and prov[x] == prov[y]:
            same += 1
            hs += h
        else:
            diff += 1
            hd += h
    return hs, same, hd, diff


def const_col(G, frac=0.8):
    out = []
    for k, gs in G.items():
        L = Counter(len(g) for g in gs).most_common(1)[0][0]
        gs = [g for g in gs if len(g) == L]
        if L < 3 or len(gs) < 5:
            continue
        cols = []
        for p in range(L):
            c = Counter(g[p] for g in gs)
            v, n = c.most_common(1)[0]
            if v and n >= frac * len(gs):
                cols.append((p + 1, v, n))
        out.append((k, L, len(gs), cols))
    return out


def main():
    P, G = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    prov = {k: str(meta.get(k, {}).get("PROVENANCE") or "").strip().lower() for k in P}
    for k in prov:
        if prov[k] in ("unknown", "none", "", "peru"):
            prov[k] = ""
    rnd = random.Random(1)
    lines = ["1. Подпись: совпадение первых K подвесных (пары одного места / разных мест)"]
    for K in (1, 2, 3):
        hs, s, hd, d = signature(P, prov, K, rnd)
        rs = [signature(P, prov, K, rnd, True) for _ in range(20)]
        rs_same = sum(r[0] for r in rs) / 20
        lines.append(f"  K={K}: одно место {hs}/{s} ({hs / s:.3%}), разные {hd}/{d} ({hd / d:.3%}); "
                     f"случайное окно, одно место: {rs_same:.1f}/{s}")
    lines.append("  совпадения первых 3 у пар одного места:")
    keys = [k for k in P if len(P[k]) >= 8]
    byp = defaultdict(list)
    for k in keys:
        if prov[k] and any(P[k][:3]):
            byp[(prov[k], tuple(P[k][:3]))].append(k)
    for (pv, sig), ks in sorted(byp.items(), key=lambda t: -len(t[1])):
        if len(ks) >= 2:
            lines.append(f"    {pv[:30]:30} {sig}: {ks}")
    lines.append("")
    real = const_col(G)
    n_real = sum(1 for r in real if r[3])
    nulls = []
    for i in range(50):
        G2 = {k: [rnd.sample(g, len(g)) for g in gs] for k, gs in G.items()}
        nulls.append(sum(1 for r in const_col(G2) if r[3]))
    lines.append(f"2. Постоянная графа (одно ненулевое значение в ≥ 80% групп): у {n_real} из {len(real)} кипу; "
                 f"фон (позиции внутри групп перемешаны): {sum(nulls) / len(nulls):.1f}, макс {max(nulls)}")
    vals = Counter(v for r in real for _, v, _ in r[3])
    lines.append(f"  значения постоянных граф: {vals.most_common(15)}")
    for k, L, n, cols in real:
        if cols:
            lines.append(f"  {k:10} L={L:2} групп={n:3} графы {cols}  | {prov[k][:30]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:80]))


if __name__ == "__main__":
    main()
