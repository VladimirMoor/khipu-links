"""UR212 (VA42508(A), Уртон) и AS131 = UR1131 (VA42510, Ашеры) — две половины одного счёта из 14 единиц,
которые базельские фрагменты из Уачо (IVc.366.03, MM008–MM017) сводят вместе.

Единица k: k-я основная группа (≥ 10 шнуров) UR212, считая с конца, и k-я основная группа AS131, считая
с начала. Для каждого фрагмента находим, каким единицам принадлежат его совпадающие участки с UR212 и с AS131
(difflib, ≥ 3 шнуров, ≥ 2 значений ≥ 10); единица участка — по большинству его шнуров с узлами
(пустые шнуры на границах групп не учитываются). Если фрагмент несёт участки обоих кипу, проверяем, одна ли это
единица. Вероятность совпадения номера единицы случайно — 1/14 на каждый фрагмент после первого.
Вывод: extracted/ur212_as131_units.txt.
"""
import csv
import difflib
import itertools
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/ur212_as131_units.txt"
FRAG = [f"MM{i:03d}" for i in range(8, 18)]


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    for k in by:
        by[k].sort(key=lambda r: int(r["order"]))
    val = lambda k: [int(r["value"]) for r in by[k]]

    def unit_of(K, from_end):
        gs = [list(g) for _, g in itertools.groupby(range(len(by[K])), key=lambda i: by[K][i]["group"])]
        main = [g for g in gs if len(g) >= 10]
        if from_end:
            main = main[::-1]
        u = {}
        for n, g in enumerate(main, 1):
            for i in g:
                u[i + 1] = n
        return u, len(main)

    uU, nU = unit_of("UR212", True)
    uA, nA = unit_of("UR1131", False)
    lines = [f"основных групп: UR212 {nU}, AS131 {nA}"]
    paired, hits = 0, 0
    for K in FRAG:
        q = val(K)
        units = {"UR212": [], "AS131": []}
        for T, tag, um in (("UR212", "UR212", uU), ("UR1131", "AS131", uA)):
            w = val(T)
            for d, ww in (("f", w), ("r", w[::-1])):
                for b in difflib.SequenceMatcher(None, q, ww, autojunk=False).get_matching_blocks():
                    if b.size >= 3 and sum(x >= 10 for x in q[b.a:b.a + b.size]) >= 2:
                        for i in range(b.size):
                            pos = b.b + i + 1 if d == "f" else len(w) - (b.b + i)
                            if pos in um and q[b.a + i] > 0:
                                units[tag].append(um[pos])
        units = {t: ({max(set(v), key=v.count)} if v else set()) for t, v in units.items()}
        if units["UR212"] or units["AS131"]:
            both = units["UR212"] and units["AS131"]
            same = both and units["UR212"] == units["AS131"]
            paired += bool(both)
            hits += bool(same)
            lines.append(f"  {K}: единицы UR212 {sorted(units['UR212'])}, AS131 {sorted(units['AS131'])}"
                         + ("  ← одна единица" if same else ""))
    p = (1 / 14) ** (hits - 1) if hits >= 2 else 1.0
    lines.append(f"фрагментов с участками обоих кипу: {paired}; из них одна и та же единица: {hits}; "
                 f"случайно (после первого) p ≈ {p:.4f}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
