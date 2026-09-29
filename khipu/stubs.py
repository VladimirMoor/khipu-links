"""Обрывы шнуров: «корешки» (нарочно, в одной позиции группы) или порча (случайно/пятнами)?

Кипу с правильными группами (≥ 4 групп одной длины L ≥ 3). Для оборванных подвесных
(termination B) считаем: (1) концентрацию по позиции в группе — max по столбцам доли
оборванных (статистика: хи-квадрат по столбцам); (2) пятнистость — число соседних пар
оборванных шнуров подряд. Фон — случайная перестановка тех же обрывов по шнурам кипу.
Вывод: extracted/stubs.txt.
"""
import csv
import itertools
import os
import random
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/plus_cords.csv"))
OUT = ROOT / "extracted/stubs.txt"


def chi(broken, L):
    n = len(broken) // L
    cols = [sum(broken[g * L + p] for g in range(n)) for p in range(L)]
    e = sum(cols) / L
    return sum((c - e) ** 2 / e for c in cols) if e else 0.0


def runs(broken):
    return sum(1 for a, b in zip(broken, broken[1:]) if a and b)


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    rnd = random.Random(1)
    res = []
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        gs = [list(g) for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
        L = Counter(len(g) for g in gs).most_common(1)[0][0]
        gs = [g for g in gs if len(g) == L]
        if L < 3 or len(gs) < 4:
            continue
        b = [1 if r["termination"] == "B" else 0 for g in gs for r in g]
        nb = sum(b)
        if nb < 5 or nb > len(b) - 5:
            continue
        c0, r0 = chi(b, L), runs(b)
        cn, rn = [], []
        for _ in range(500):
            p = b[:]
            rnd.shuffle(p)
            cn.append(chi(p, L))
            rn.append(runs(p))
        res.append((k, L, len(gs), nb, c0, sum(x >= c0 for x in cn) / 500, r0, sum(rn) / 500,
                    sum(x >= r0 for x in rn) / 500))
    lines = [f"кипу с правильными группами и ≥ 5 обрывами: {len(res)}"]
    for name, idx in (("столбцы (корешки)", 5), ("пятна (порча)", 8)):
        ps = [r[idx] for r in res]
        lines.append(f"{name}: p < 0.01 у {sum(p < 0.01 for p in ps)}, p < 0.05 у {sum(p < 0.05 for p in ps)} "
                     f"(ожидание при случайности {0.05 * len(ps):.1f})")
    lines.append("\nкипу с концентрацией по столбцу (p < 0.01):")
    for r in sorted(res, key=lambda r: r[5]):
        if r[5] >= 0.01:
            break
        lines.append(f"  {r[0]}: L={r[1]} групп={r[2]} обрывов={r[3]} хи2={r[4]:.1f} p={r[5]:.3f}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
