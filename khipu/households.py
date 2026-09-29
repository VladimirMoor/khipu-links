"""Подворная перепись Сисикаи 1588 против кипу: ищем участок кипу, где подряд идущие
шнуры повторяют размеры дворов (или число податных/детей) в порядке реестра.

Мера: для каждого сдвига (диагонали) между последовательностью дворов и
последовательностью подвесных шнуров кипу — серия точных совпадений подряд
(до GAPS несовпадений), где каждое совпадение весит -log2 частоты значения в корпусе.
Совпадения нулей не считаются: пустой шнур против двора без податных тривиален,
а в реестре дворы идут по категориям, так что длинные серии 0/1 — артефакт. Значимость: те же дворы, переставленные случайно внутри блока «айлью × раздел
реестра» (женатые / вдовцы-холостые / вдовы-незамужние), порядок блоков сохранён —
так сохраняются серии одиноких дворов, идущих в реестре подряд.
"""
import argparse
import csv
import os
import random
from collections import defaultdict
from pathlib import Path

from provenance import subset

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))
GAPS = 2


def households(field):
    rows = []
    with open(ROOT / "extracted/S1_households.csv") as f:
        for r in csv.DictReader(f):
            if "sin recaudo" in (r["notes"] or "").lower():
                continue
            if r["ayllu"].startswith("("):
                continue
            if field == "tot":
                v = int(float(r["total_personas"] or 0))
            else:
                v = int(float(r[field] or 0))
            sec = (r["notes"] or "").split("]")[0].strip("[ ") if (r["notes"] or "").startswith("[") else ""
            rows.append((r["ayllu"] + "|" + sec, v))
    return rows


def pendant_seqs():
    by = defaultdict(list)
    with open(CORDS) as f:
        for r in csv.DictReader(f):
            if r["parent_id"] == "":
                by[r["khipu_id"]].append((int(r["order"]), int(r["value"]), r["inv_num"]))
    return {k: ([v for _, v, _ in sorted(x)], x[0][2]) for k, x in by.items()}


W = {}


def set_weights(khipus):
    """w(v) = -log2 доли подвесных шнуров корпуса со значением v; нулям вес 0
    (пустой шнур и двор без податных «совпадают» тривиально)."""
    import math
    from collections import Counter
    c = Counter(v for ks, _ in khipus.values() for v in ks)
    n = sum(c.values())
    W.clear()
    W.update({v: (-math.log2(k / n) if v > 0 else 0.0) for v, k in c.items()})


def best_run(a, b, gaps=GAPS):
    """Лучшая серия на одной диагонали с не более чем gaps несовпадениями;
    счёт = сумма весов совпавших значений (совпадения нулей не считаются, но и не рвут серию)."""
    best = (0, None)
    n, m = len(a), len(b)
    for off in range(-n + 1, m):
        i0, j0 = max(0, -off), max(0, off)
        L = min(n - i0, m - j0)
        # скользящее окно: максимум совпадений при <= gaps несовпадений
        lo, miss, hits = 0, 0, 0.0
        eq = [a[i0 + t] == b[j0 + t] for t in range(L)]
        wt = [W.get(a[i0 + t], 10.0) if eq[t] else 0.0 for t in range(L)]
        for hi in range(L):
            if eq[hi]:
                hits += wt[hi]
            else:
                miss += 1
            while miss > gaps:
                if eq[lo]:
                    hits -= wt[lo]
                else:
                    miss -= 1
                lo += 1
            if hits > best[0]:
                best = (hits, (off, i0 + lo, j0 + lo, hi - lo + 1))
    return best


def search(seq, khipus):
    res = []
    for kid, (ks, inv) in khipus.items():
        h, info = best_run(seq, ks)
        res.append((h, inv, info))
    res.sort(reverse=True)
    return res


def shuffled(hh, rng):
    by = defaultdict(list)
    order = []
    for a, v in hh:
        if a not in by:
            order.append(a)
        by[a].append(v)
    out = []
    for a in order:
        vs = by[a][:]
        rng.shuffle(vs)
        out += vs
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--place", default="Pachacam|Lur[ií]n|Cieneguilla")
    ap.add_argument("--null", type=int, default=200)
    a = ap.parse_args()
    rng = random.Random(3)
    allk = pendant_seqs()
    set_weights(allk)
    khipus = subset(allk, CORDS, a.place)
    print(f"кипу в поиске: {len(khipus)}")
    for field in ["tot", "tributarios", "muchachos"]:
        hh = households(field)
        seq = [v for _, v in hh]
        res = search(seq, khipus)
        real = res[0][0]
        nulls = sorted(search(shuffled(hh, rng), khipus)[0][0] for _ in range(a.null))
        p = (sum(1 for x in nulls if x >= real) + 1) / (a.null + 1)
        print(f"{field:12} дворов={len(seq)} лучший={res[0][1]} вес={real:.1f} бит "
              f"(окно {res[0][2][3]}) p={p:.3f} null95={nulls[int(.95 * len(nulls)) - 1]:.1f}")
        for h, inv, info in res[1:4]:
            print(f"             {inv} {h:.1f}")


if __name__ == "__main__":
    main()
