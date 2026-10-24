"""Шнуры «не той стороны»: в кипу, где ≥ 80% подвесных прикреплены одинаково (recto или verso), подвесные другой
стороны. Метки ли это?

Для таких шнуров (база OKR) против перестановки — те же шнуры, случайно переставленные внутри своего кипу (2000 раз):
1. положение в группе: первый, последний, одиночная группа;
2. скопления: соседний подвесной тоже «не той стороны»; целые группы такими шнурами;
3. значение: без узлов (0); равно итогу остальных шнуров своей группы; равно итогу предыдущей или следующей группы;
4. цвет: отличается от преобладающего цвета своей группы;
5. копии: у сопоставленных шнуров связанной пары (как в copydirs.py) «не та сторона» на одном месте у обоих.
Вывод: extracted/oddside.txt.
"""
import json
import random
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
import copydirs  # noqa: E402

DB = ROOT / "data/open-khipu-repository/data/khipu.db"
OUT = ROOT / "extracted/oddside.txt"
NPERM = 2000
MAJ = 0.8


def load():
    c = sqlite3.connect(DB)
    inv = {k: (n or "").strip() for k, n in c.execute("select KHIPU_ID, INVESTIGATOR_NUM from khipu_main")}
    col = {}
    for cid, c1, op, c2 in c.execute("select CORD_ID, COLOR_CD_1, OPERATOR_1, COLOR_CD_2 from ascher_cord_color order by color_id"):
        col.setdefault(cid, (c1 or "") + (op or "") + (c2 or ""))
    val = dict(c.execute("select CORD_ID, sum(knot_value_type) from knot group by CORD_ID"))
    K = defaultdict(list)
    for cid, kid, ordn, clu, att in c.execute("select CORD_ID, KHIPU_ID, CORD_ORDINAL, CLUSTER_ID, ATTACHMENT_TYPE from cord "
                                               "where CORD_LEVEL = 1 order by KHIPU_ID, CORD_ORDINAL"):
        K[inv.get(kid, "")].append({"v": int(val.get(cid) or 0), "att": (att or "").strip().upper()[:1], "col": col.get(cid, ""), "g": clu})
    return K


def features(cords, odd):
    """counts over the odd cords (indices in `odd`) of each feature"""
    n = len(cords)
    gi = [c["g"] for c in cords]
    groups = defaultdict(list)
    for i, g in enumerate(gi):
        groups[g].append(i)
    gorder = []
    for g in gi:
        if not gorder or gorder[-1] != g:
            gorder.append(g)
    gsum = {g: sum(cords[i]["v"] for i in groups[g]) for g in groups}
    gcol = {g: Counter(cords[i]["col"] for i in groups[g]).most_common(1)[0][0] for g in groups}
    pos = {g: k for k, g in enumerate(gorder)}
    S = set(odd)
    f = Counter()
    for i in odd:
        g, mem = gi[i], groups[gi[i]]
        if len(mem) == 1:
            f["single-cord group"] += 1
        else:
            f["first in group"] += i == mem[0]
            f["last in group"] += i == mem[-1]
        f["neighbour also odd"] += (i - 1 in S) or (i + 1 in S)
        v = cords[i]["v"]
        f["knotless (0)"] += v == 0
        rest = gsum[g] - v
        f["= total of rest of its group"] += v >= 10 and v == rest and len(mem) >= 3
        k = pos.get(g, -1)
        nb = [gsum[gorder[k + d]] for d in (-1, 1) if 0 <= k + d < len(gorder)]
        f["= total of a neighbouring group"] += v >= 10 and v in nb
        f["colour differs from its group"] += bool(cords[i]["col"]) and cords[i]["col"] != gcol[g]
    for g, mem in groups.items():
        if len(mem) >= 2 and all(i in S for i in mem):
            f["cords in whole odd groups"] += len(mem)
    return f


def main():
    K = load()
    rnd = random.Random(5)
    real, sims = Counter(), [Counter() for _ in range(NPERM)]
    nk = nodd = 0
    oddsets = {}
    for k, cords in K.items():
        sides = [c["att"] for c in cords if c["att"] in ("R", "V")]
        if len(sides) < 10:
            continue
        cnt = Counter(sides)
        major, m = cnt.most_common(1)[0]
        if m / len(sides) < MAJ or m == len(sides):
            continue
        odd = [i for i, c in enumerate(cords) if c["att"] in ("R", "V") and c["att"] != major]
        eligible = [i for i, c in enumerate(cords) if c["att"] in ("R", "V")]
        oddsets[k] = (set(odd), major)
        nk += 1; nodd += len(odd)
        real += features(cords, odd)
        for s in range(NPERM):
            sims[s] += features(cords, rnd.sample(eligible, len(odd)))
    lines = [f"khipus with ≥ {MAJ:.0%} of pendants on one side and some on the other: {nk}; odd-side pendants: {nodd}", ""]
    for feat in ["first in group", "last in group", "single-cord group", "neighbour also odd", "cords in whole odd groups",
                 "knotless (0)", "= total of rest of its group", "= total of a neighbouring group", "colour differs from its group"]:
        xs = [s[feat] for s in sims]
        m = sum(xs) / len(xs)
        p = (1 + sum(x >= real[feat] for x in xs)) / (1 + NPERM)
        lines.append(f"{feat:32} real {real[feat]:5}  shuffled {m:7.1f}  ratio {real[feat] / m if m else float('nan'):5.2f}  p(≥) {p:.4f}")
    # 5. copies: is an odd-side cord at the same place on both members of a linked pair?
    D = json.load(open(ROOT / "site/data.json"))
    KC = copydirs.load()
    lines.append("\nLinked pairs: odd-side pendants at matched positions")
    agree = tot_a = tot_b = 0
    for e in D["edges"]:
        a, b = e["from"], e["to"]
        if a not in oddsets and b not in oddsets:
            continue
        if not KC.get(a) or not KC.get(b):
            continue
        M, rev = copydirs.matched(KC[a], KC[b])
        oa, ob = oddsets.get(a, (set(), ""))[0], oddsets.get(b, (set(), ""))[0]
        ina = [(i, j) for i, j in M if i in oa]
        inb = [(i, j) for i, j in M if j in ob]
        both = [(i, j) for i, j in M if i in oa and j in ob]
        agree += len(both); tot_a += len(ina); tot_b += len(inb)
        lines.append(f"   {a} ~ {b} ({e['type']}): matched {len(M)}; odd on {a} {len(ina)}, on {b} {len(inb)}, on both {len(both)}")
    lines.append(f"   total: odd on the first {tot_a}, on the second {tot_b}, at the same matched place on both {agree}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
