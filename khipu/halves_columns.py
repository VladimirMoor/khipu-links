"""UR212 и AS131 = UR1131: деление на две части по 7 единиц и суммы по столбцам.

1) Где у каждого кипу граница частей: AS131 — больший промежуток после 7-й группы (Ашеры, Databook с. 852, 866);
   UR212 — одиночная группа [0] между основными группами (единицы считаются с конца UR212).
2) Проверка равенств Ашеров внутри AS131 (Σ ч.1 поз. 3 = Σ ч.1 поз. 4; Σ ч.1 поз. 2 = Σ ч.2 поз. 4;
   Σ ч.1 поз. 6 = Σ ч.2 поз. 2) на данных OKR.
3) Суммы столбцов по частям: UR212 (14 мест, в порядке единиц; группы развёрнуты) против AS131 (10 мест) —
   число равных пар (сумма ≥ 20) против фона (суммы AS131 + d, d = ±1…±10).
Вывод: extracted/halves_columns.txt.
"""
import csv
import itertools
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/halves_columns.txt"


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    grp = lambda k: [[int(r["value"]) for r in g] for _, g in
                     itertools.groupby(sorted(by[k], key=lambda r: int(r["order"])), key=lambda r: r["group"])]
    U = grp("UR212")[::-1]
    lines = ["UR212, группы с конца (размеры): " + str([len(g) for g in U])]
    sep = [i for i, g in enumerate(U) if len(g) < 10]
    main_before = [sum(1 for g in U[:i] if len(g) >= 10) for i in sep]
    lines.append(f"  короткие группы UR212 после единиц № {main_before} (с конца)")
    Uu = [g[::-1] for g in U if len(g) >= 10]
    A = [g for g in grp("UR1131") if len(g) >= 10]
    col = lambda G, part, i: sum(g[i] for g in G[7 * part:7 * part + 7] if len(g) > i)
    for (p1, i1), (p2, i2) in (((0, 2), (0, 3)), ((0, 1), (1, 3)), ((0, 5), (1, 1))):
        lines.append(f"  AS131 Σ ч.{p1 + 1} поз.{i1 + 1} = {col(A, p1, i1)}; Σ ч.{p2 + 1} поз.{i2 + 1} = {col(A, p2, i2)}")
    SU = {(p, i): col(Uu, p, i) for p in (0, 1) for i in range(14)}
    SA = {(p, j): col(A, p, j) for p in (0, 1) for j in range(10)}

    def eq(d):
        return [(u, a, SU[u]) for u in SU for a in SA if SU[u] >= 20 and SU[u] == SA[a] + d]
    real = eq(0)
    null = [len(eq(d)) for d in range(-10, 11) if d]
    lines.append(f"равных сумм столбцов UR212 ~ AS131 (≥ 20): {len(real)} {real}; фон {sum(null) / len(null):.2f} (макс {max(null)})")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
