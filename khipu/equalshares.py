"""Равные по итогу группы внутри кипу (обобщение AS143 г3 = 41062, г5 = 41061).

Пары групп одной длины (3–12 шнуров, ≥ 3 шнуров ≥ 10, итог ≥ 500), не совпадающие поразрядно.
Считаем |Σa − Σb| = 0 или 1 и сравниваем с локальным фоном — средним числом пар на единицу
разности в диапазоне 2…40. Вариант «некруглые»: в каждой группе ≥ 2 некруглых значений.
Вывод: extracted/equalshares.txt.
"""
import csv
import itertools
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/equalshares.txt"


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    lines = []
    for mode in ("все", "некруглые"):
        D = Counter()
        for k, rs in by.items():
            rs.sort(key=lambda r: int(r["order"]))
            gs = [tuple(int(r["value"]) for r in g) for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
            gs = [g for g in gs if 3 <= len(g) <= 12 and sum(1 for x in g if x >= 10) >= 3 and sum(g) >= 500]
            if mode == "некруглые":
                gs = [g for g in gs if sum(1 for x in g if x % 10) >= 2]
            seen = set()
            for a, b in itertools.combinations(gs, 2):
                if len(a) != len(b) or a == b or (a, b) in seen:
                    continue
                seen.add((a, b))
                d = abs(sum(a) - sum(b))
                if d <= 40:
                    D[d] += 1
        exp = 2 * sum(D[d] for d in range(2, 41)) / 39
        obs = D[0] + D[1]
        p = 1 - sum(math.exp(-exp) * exp ** i / math.factorial(i) for i in range(obs))
        lines.append(f"{mode}: |разность| ≤ 1 — {obs} пар, ожидание {exp:.1f}, p ≈ {p:.2f}; "
                     f"профиль d = 0…15: {[D[d] for d in range(16)]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
