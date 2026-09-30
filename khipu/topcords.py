"""Верхние шнуры (attachment T): равны ли сумме соседней группы; группы по шесть.

Проверка утверждения Ашеров (пересказано у Chirinos 2010, гл. 15). Для каждого ненулевого верхнего
шнура — сумма подвесных предыдущей и следующей группы; фон — значение шнура, сдвинутое на d = ±1…±10.
Доля групп из 6 подвесных — в кипу с верхними шнурами и в остальных. Вывод: extracted/topcords.txt.
"""
import csv
import itertools
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/topcords.txt"


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["level"] == "1":
            by[r["inv_num"]].append(r)
    tk = sorted(k for k, rs in by.items() if any(r["attachment"] == "T" for r in rs))
    side, null, n, kh = Counter(), 0, 0, set()
    sizes = {True: Counter(), False: Counter()}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        gs = [list(rr) for _, rr in itertools.groupby(rs, key=lambda r: r["group"])]
        gsum = [sum(int(r["value"]) for r in g if r["attachment"] != "T") for g in gs]
        for g in gs:
            m = sum(1 for r in g if r["attachment"] != "T")
            if m:
                sizes[k in tk][m] += 1
        if k not in tk:
            continue
        for i, g in enumerate(gs):
            for t in (r for r in g if r["attachment"] == "T"):
                v = int(t["value"])
                if v <= 0:
                    continue
                n += 1
                P = gsum[i - 1] if i > 0 else None
                N = gsum[i + 1] if i + 1 < len(gs) else None
                side["предыдущей" if v == P else "следующей" if v == N else "нет"] += 1
                if v in (P, N):
                    kh.add(k)
                null += sum(v + d in (P, N) for d in range(-10, 11) if d)
    six = {f: sizes[f][6] / sum(sizes[f].values()) for f in sizes}
    lines = [f"кипу с верхними шнурами: {len(tk)}; хотя бы один верхний = сумме соседней группы: {len(kh)}",
             f"ненулевых верхних шнуров {n}; равен сумме группы: {dict(side)}; фон на один сдвиг {null / 20:.2f}",
             f"группы из 6 подвесных: {six[True]:.0%} в кипу с верхними шнурами, {six[False]:.0%} в остальных"]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
