"""Календарные следы в кипу: числа и устройство.

1. Числа. Как часто «календарные» числа (365, 360, 354, 355, 328, 730, 720, 29, 30) встречаются
   как итог кипу, сумма группы или значение подвесного — по сравнению с соседями той же
   «круглости» (t ± 10k для k = 1…5, без кратных 100, если само t не кратно 100). Отношение
   «реально / среднее соседей» > 1 означает избыток. Контроль: 260, 584 (майяские циклы) и
   случайные 347, 373, 412.
2. Устройство. Распределение числа «крупных» групп (≥ 10 подвесных) по кипу: есть ли пик на
   12 или 24 по сравнению с соседними числами групп.
Вывод: extracted/calendar.txt.
"""
import csv
import itertools
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/calendar.txt"
TARGETS = [365, 360, 354, 355, 328, 730, 720, 29, 30, 260, 584, 347, 373, 412]


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    tot, grp, cord, big = Counter(), Counter(), Counter(), Counter()
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        gs = [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
        tot[sum(map(sum, gs))] += 1
        for g in gs:
            grp[sum(g)] += 1
            for v in g:
                cord[v] += 1
        big[sum(1 for g in gs if len(g) >= 10)] += 1
    return tot, grp, cord, big


def neighbours(t):
    step = 10 if t >= 100 else 1
    out = []
    for k in range(1, 6):
        for s in (-1, 1):
            n = t + s * k * step
            if n > 0 and (t % 100 == 0 or n % 100 != 0):
                out.append(n)
    return out


def main():
    tot, grp, cord, big = load()
    lines = ["1. Календарные числа: реально / среднее у соседей той же круглости (отношение)"]
    for name, C in (("итог кипу", tot), ("сумма группы", grp), ("значение подвесного", cord)):
        lines.append(f"  {name}:")
        for t in TARGETS:
            nb = neighbours(t)
            m = sum(C[n] for n in nb) / len(nb)
            lines.append(f"    {t:4}: {C[t]:4} / {m:6.2f}" + (f"  ({C[t] / m:.2f})" if m else ""))
    lines += ["", "2. Число крупных групп (≥ 10 подвесных) на кипу:"]
    lines.append("   " + ", ".join(f"{n}: {big[n]}" for n in range(6, 31)))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
