"""Делятся ли кипу на две равные половины? По OKR (cord_cluster: промежуток после группы).

Основные группы — кластеры уровня 1 с ≥ 3 шнурами (соседние мелкие кластеры считаются разделителями и в число
групп не входят, но их промежутки прибавляются к промежутку). Для кипу с чётным числом основных групп 2k (k ≥ 3):
приходится ли наибольший промежуток между группами на середину (после k-й). Ожидание при случайном месте — сумма
1/(2k − 1) (с долями при равных максимумах). Отдельно: наибольший промежуток vs второй по величине — насколько он
выделяется. Вывод: extracted/halves.txt.
"""
import sqlite3
from collections import defaultdict
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/open-khipu-repository/data/khipu.db"
OUT = ROOT / "extracted/halves.txt"


def main():
    con = sqlite3.connect(DB)
    names = dict(con.execute("select KHIPU_ID, INVESTIGATOR_NUM from khipu_main"))
    rows = con.execute("select KHIPU_ID, ORDINAL, START_POSITION, END_POSITION, NUM_CORDS from cord_cluster "
                       "where CLUSTER_LEVEL = 1 order by KHIPU_ID, ORDINAL").fetchall()
    by = defaultdict(list)
    for k, o, s, e, n in rows:
        if s is not None and e is not None:
            by[k].append((float(s), float(e), n or 0))
    obs = exp = 0.0
    n = 0
    hits = []
    for k, cl in by.items():
        cl.sort()
        main = [c for c in cl if c[2] >= 3]
        if len(main) < 6 or len(main) % 2:
            continue
        gaps = [main[i + 1][0] - main[i][1] for i in range(len(main) - 1)]
        if any(g < 0 for g in gaps) or max(gaps) <= 0:
            continue
        mx = max(gaps)
        top = [i for i, g in enumerate(gaps) if g == mx]
        mid = len(main) // 2 - 1
        n += 1
        obs += (mid in top) / len(top)
        exp += 1 / len(gaps)
        if mid in top and len(top) == 1:
            second = sorted(gaps)[-2]
            hits.append((names.get(k), len(main), round(mx, 1), round(second, 1)))
    # Poisson-binomial tail approx by normal
    lines = [f"кипу с чётным числом основных групп (≥ 6): {n}; наибольший промежуток посередине: {obs:.1f}; "
             f"ожидание {exp:.1f}"]
    lines += [f"  {h}" for h in sorted(hits, key=lambda h: -h[2] / max(h[3], 0.1))]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
