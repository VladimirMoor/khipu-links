"""Оборванные шнуры (termination B) как нижняя граница: объясняют ли они недостачи в суммах?

Группы ≥ 3 подвесных, где первый или последний шнур T ≈ сумма остальных S (|T − S| ≤ 3% от T, T ≥ 30).
Если оборвана часть, записанная сумма частей должна быть меньше (S < T); если оборван итог — T < S.
Сравниваем знак расхождения с тем, где оборванный шнур; фон — те же группы без оборванных шнуров
(знак случаен). Отдельно — доля точных сумм (T = S) у групп с/без оборванных шнуров.
Вывод: extracted/broken.txt.
"""
import csv
import itertools
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/broken.txt"


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    C = Counter()
    ex = []
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        for _, g in itertools.groupby(rs, key=lambda r: r["group"]):
            g = list(g)
            if len(g) < 3:
                continue
            for pos in (0, -1):
                t = g[pos]
                parts = g[1:] if pos == 0 else g[:-1]
                T = int(t["value"])
                S = sum(int(r["value"]) for r in parts)
                if T < 30 or abs(T - S) > 0.03 * T or sum(int(r["value"]) > 0 for r in parts) < 2:
                    continue
                tb = t["termination"] == "B"
                pb = any(r["termination"] == "B" for r in parts)
                cls = "итог оборван" if tb and not pb else "часть оборвана" if pb and not tb else \
                    "оба" if tb and pb else "нет обрывов"
                sign = "T=S" if T == S else "S<T" if S < T else "T<S"
                C[(cls, sign)] += 1
                if cls != "нет обрывов" and sign != "T=S":
                    ex.append((k, T, S, cls))
                break
    lines = ["класс: T=S / S<T (не хватает в частях) / T<S (не хватает в итоге)"]
    for cls in ("нет обрывов", "часть оборвана", "итог оборван", "оба"):
        a, b, c = C[(cls, "T=S")], C[(cls, "S<T")], C[(cls, "T<S")]
        n = a + b + c
        lines.append(f"  {cls}: {a} / {b} / {c}; точных {a / n:.0%}" if n else f"  {cls}: 0")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return C, ex


if __name__ == "__main__":
    main()
