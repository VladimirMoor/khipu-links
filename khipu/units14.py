"""«Архив из 14 единиц» в берлинской партии Гретцера («Пачакамак»).

1) Доля кипу с ровно 14 основными группами (≥ 5 шнуров) — берлинские пачакамакские против остального корпуса;
   биномиальная вероятность.
2) Для четырёх таких кипу корпуса (UR212, AS131 = UR1131, AS170, UR199) — ранговая корреляция итогов 14 единиц
   попарно, в обоих направлениях чтения второго кипу (направление неизвестно); фон — перестановки.
Вывод: extracted/units14.txt.
"""
import csv
import itertools
import json
import random
from collections import defaultdict
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/units14.txt"
KEYS = ["UR212", "UR1131", "AS170", "UR199"]


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    groups = {k: [[int(r["value"]) for r in g] for _, g in
                  itertools.groupby(sorted(v, key=lambda r: int(r["order"])), key=lambda r: r["group"])] for k, v in by.items()}
    main = {k: [g for g in gs if len(g) >= 5] for k, gs in groups.items()}
    elig = [k for k in main if len(main[k]) >= 3]
    isP = lambda k: "achacamac" in str(meta.get(k, {}).get("PROVENANCE")) and "Berlin" in str(meta.get(k, {}).get("MUSEUM_NAME"))
    P = [k for k in elig if isP(k)]
    O = [k for k in elig if not isP(k)]
    p14 = sum(len(main[k]) == 14 for k in P)
    o14 = sum(len(main[k]) == 14 for k in O)
    q = o14 / len(O)
    pb = sum(comb(len(P), i) * q ** i * (1 - q) ** (len(P) - i) for i in range(p14, len(P) + 1))
    lines = [f"14 основных групп: берлинские «Пачакамак» {p14} из {len(P)}; прочие {o14} из {len(O)} ({q:.1%}); "
             f"биномиально P ≈ {pb:.4f}",
             "  " + ", ".join(f"{k} ({meta[k]['MUSEUM_NUM']}, {len(main[k][0])}…)" for k in P if len(main[k]) == 14)]

    def rank(x):
        s = sorted(range(len(x)), key=lambda i: x[i])
        r = [0] * len(x)
        for j, i in enumerate(s):
            r[i] = j
        return r

    def rho(a, b):
        a, b = rank(a), rank(b)
        m = (len(a) - 1) / 2
        return sum((x - m) * (y - m) for x, y in zip(a, b)) / sum((x - m) ** 2 for x in a)
    rnd = random.Random(1)
    tot = {k: [sum(g) for g in main[k]] for k in KEYS}
    for a, b in itertools.combinations(KEYS, 2):
        for d, tb in (("прямо", tot[b]), ("обратно", tot[b][::-1])):
            r = rho(tot[a], tb)
            null = [rho(tot[a], rnd.sample(tb, len(tb))) for _ in range(5000)]
            p = (1 + sum(abs(x) >= abs(r) for x in null)) / 5001
            lines.append(f"  {a} ~ {b} {d}: ρ = {r:.2f}, p = {p:.3f}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
