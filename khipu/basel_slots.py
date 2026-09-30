"""Пустые места берлинских кипу (UR212, AS131), заполненные на базельских фрагментах из Уачо.

Для трёх единиц, которые фрагменты несут целиком (MM015 — ед. 1 UR212 и AS131; MM008 — ед. 14 UR212 и AS131;
MM016 — ед. 4 UR212), группы выравниваются по месту (базельский участок приводится к направлению берлинской
группы). Считаем: берлинский 0 → базельский 0 / не 0; берлинское не 0 → базельский 0; отдельно — на
«помеченном» месте (шнур особого цвета: AS131 место 7, NB:KB; UR212 место 4 (ед. 14) и 3 (ед. 1), AB:CB; у MM015 пустой шнур остаётся последним, поэтому
разворачиваются только 13 шнуров с узлами). Вывод: extracted/basel_slots.txt.
"""
import csv
import itertools
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/basel_slots.txt"


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    for k in by:
        by[k].sort(key=lambda r: int(r["order"]))
    grp = lambda k: [list(g) for _, g in itertools.groupby(by[k], key=lambda r: r["group"])]
    U = [g for g in grp("UR212") if len(g) >= 10][::-1]      # unit 1 = last group
    A = [g for g in grp("UR1131") if len(g) >= 10]
    M = {k: by[k] for k in ("MM008", "MM015", "MM016")}
    v = lambda rs: [(int(r["value"]), r["color"]) for r in rs]
    # (label, Berlin group in its own order, Basel cords in Berlin order, marked slot index)
    cases = [("ед. 1 UR212", v(U[0]), v(M["MM015"][:13])[::-1] + v(M["MM015"][13:14]), 2),
             ("ед. 1 AS131", v(A[0])[:9], v(M["MM015"][14:23]), 6),
             ("ед. 14 AS131", v(A[13]), v(M["MM008"][:10])[::-1], 6),
             ("ед. 14 UR212", v(U[13]), v(M["MM008"][10:24]), 3),
             ("ед. 4 AS131", v(A[3])[:5], v(M["MM016"][14:19]), None)]
    lines, tally = [], defaultdict(int)
    for lab, b, s, mark in cases:
        row = []
        for i, ((bv, bc), (sv, sc)) in enumerate(zip(b, s)):
            key = ("помеч." if i == mark else "прочие", "0→0" if bv == 0 == sv else "0→n" if bv == 0 else
                   "n→0" if sv == 0 else "n=n" if bv == sv else "n≠n")
            tally[key] += 1
            if key[1] != "n=n":
                row.append(f"место {i + 1}: {bv} {bc} → {sv} {sc}")
        lines.append(f"{lab}: " + ("; ".join(row) if row else "все значения совпадают"))
    lines.append("итог: " + ", ".join(f"{a} {b}: {n}" for (a, b), n in sorted(tally.items())))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
