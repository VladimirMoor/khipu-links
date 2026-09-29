"""«Раздаточные» кипу: таблица групп × позиций, близкая к мультипликативной (ранг 1):
x[g][p] ≈ share[g] · comp[p]. Это обобщение «постоянных пропорций» Ашеров.

Для каждой кипу берём подряд идущие группы одной длины L (3–10), все значения > 0 в ≥ 3 столбцах,
≥ 3 группы, сумма группы ≥ 100. Мера: доля «объяснённой» суммы квадратов логарифмов первой
компонентой после центрирования по строкам и столбцам — эквивалентно: остаток log x − (a_g + b_p).
RMS остатка (в log, ≈ относительная ошибка). Фон: перемешивание значений внутри каждого столбца
между группами (распределения столбцов сохранены), 200 раз; p = доля перемешиваний с RMS ≤ реального.
Для значимых — доли групп в «простых дробях»: отношения сумм групп к наименьшей и ближайшие к ним
кратные 1/2.
"""
import csv
import itertools
import math
import os
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))


def tables():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    out = []
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        gs = [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
        i = 0
        while i < len(gs):
            L = len(gs[i])
            j = i
            while j < len(gs) and len(gs[j]) == L:
                j += 1
            run = [g for g in gs[i:j] if sum(g) >= 100]
            if 3 <= L <= 10 and len(run) >= 3:
                cols = [c for c in range(L) if all(g[c] > 0 for g in run)]
                if len(cols) >= 3:
                    out.append((k, i, [[g[c] for c in cols] for g in run]))
            i = max(j, i + 1)
    return out


def rms(M):
    Y = [[math.log(x) for x in row] for row in M]
    n, m = len(Y), len(Y[0])
    rm = [sum(r) / m for r in Y]
    cm = [sum(Y[i][j] for i in range(n)) / n for j in range(m)]
    gm = sum(rm) / n
    res = [Y[i][j] - rm[i] - cm[j] + gm for i in range(n) for j in range(m)]
    return math.sqrt(sum(e * e for e in res) / len(res))


def shuffle_cols(M, rng):
    n, m = len(M), len(M[0])
    cols = [[M[i][j] for i in range(n)] for j in range(m)]
    for c in cols:
        rng.shuffle(c)
    return [[cols[j][i] for j in range(m)] for i in range(n)]


def main():
    rng = random.Random(5)
    res = []
    for k, start, M in tables():
        r = rms(M)
        null = [rms(shuffle_cols(M, rng)) for _ in range(200)]
        p = (sum(1 for x in null if x <= r) + 1) / 201
        res.append((p, r, sorted(null)[100], k, start, M))
    res.sort(key=lambda t: (t[0], t[1]))
    print(f"таблиц: {len(res)}")
    print(f"{'p':>6} {'RMS':>6} {'фон':>6}  кипу  (групп × столбцов)  доли групп (к наименьшей)")
    for p, r, med, k, start, M in res[:30]:
        tot = [sum(g) for g in M]
        mn = min(tot)
        print(f"{p:6.3f} {r:6.3f} {med:6.3f}  {k:<8} ({len(M)}×{len(M[0])})  {[round(t/mn, 2) for t in tot][:12]}")


if __name__ == "__main__":
    main()
