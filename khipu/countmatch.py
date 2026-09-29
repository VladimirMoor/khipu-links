"""Детектор «число людей = число групп шнуров» (перепись, где группа шнуров = человек/двор).

Документ: числа по категориям (пачаки, айлью) c_1..c_m. Кипу: последовательности «единиц»
(напр. шестишнуровые группы) по каждой кипу набора; кипу выстраиваются в цепочку (все
порядки перебираются), граница кипу — тоже разрез, категория может переходить на следующую кипу. Разрезы разрешены только на видимых
границах (смена кластера по расстоянию, цвета первого шнура единицы, стороны крепления,
значения первого шнура — выбирается набором BREAKS). Ищем раскладку: каждая категория —
один непрерывный участок внутри одной кипу между разрезами, размер участка = c_i; участки не
пересекаются; нераспределённых единиц суммарно не больше SLACK. Порядок категорий свободный.

Значимость: доля случайных наборов чисел (та же сумма, то же m, случайное разбиение), для
которых раскладка тоже существует. Если настоящие числа укладываются, а случайные — редко,
совпадение неслучайно.
"""
import argparse
import collections
import csv
import itertools
import random
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def breakpoints(units, kinds):
    """Индексы 0..n, между которыми разрешён разрез (0 и n — всегда)."""
    b = {0, len(units)}
    for i in range(1, len(units)):
        a, c = units[i - 1], units[i]
        if ("cluster" in kinds and a["cluster"] != c["cluster"]) or \
           ("color" in kinds and a["color"] != c["color"]) or \
           ("attach" in kinds and a["attach"] != c["attach"]) or \
           ("value" in kinds and a["first"] != c["first"]):
            b.add(i)
    return sorted(b)


def feasible(khipu_breaks, counts, slack):
    """khipu_breaks: для каждой кипу — отсортированные точки разреза (0..n)."""
    m = len(counts)
    full = (1 << m) - 1
    per = []
    for bps in khipu_breaks:
        idx = {p: k for k, p in enumerate(bps)}

        @lru_cache(maxsize=None)
        def go(k, mask):
            """Из точки bps[k] до конца кипу: множество (mask_использованных, пропущено)."""
            if k == len(bps) - 1:
                return frozenset({(mask, 0)})
            out = set()
            p = bps[k]
            for k2 in range(k + 1, len(bps)):
                size = bps[k2] - p
                if size > slack and size > max(counts):
                    break
                # пропустить участок
                if size <= slack:
                    for mk, sk in go(k2, mask):
                        if sk + size <= slack:
                            out.add((mk, sk + size))
                # назначить категорию
                for i, c in enumerate(counts):
                    if c == size and not mask >> i & 1:
                        out |= go(k2, mask | 1 << i)
            return frozenset(out)
        per.append(go(0, 0))
    # объединяем кипу: маски не пересекаются, пропуски суммируются
    states = {(0, 0)}
    for st in per:
        new = set()
        for mask, sk in states:
            for mk, s2 in st:
                # go() стартует с mask=0, поэтому mk — ровно маска этой кипу
                if mask & mk == 0 and sk + s2 <= slack:
                    new.add((mask | mk, sk + s2))
        states = new
    return any(mask == full for mask, _ in states)


def random_counts(total, m, rng, lo=1):
    cuts = sorted(rng.sample(range(1, total), m - 1))
    parts = [b - a for a, b in zip([0] + cuts, cuts + [total])]
    return parts if min(parts) >= lo else random_counts(total, m, rng, lo)


def chain_feasible(khipu_units, counts, kinds, slack, orders):
    """Кипу выстроены в цепочку (перебор порядков); граница кипу — тоже разрез;
    категория может переходить через границу кипу."""
    for order in orders:
        seq, bps, off = [], {0}, 0
        for k in order:
            u = khipu_units[k]
            for p in breakpoints(u, kinds):
                bps.add(off + p)
            off += len(u)
            seq += u
        if feasible([sorted(bps)], tuple(counts), slack):
            return True, order
    return False, None


def evaluate(khipu_units, counts, kinds, slack, n_null=500, seed=1, chain=True):
    if chain:
        orders = list(itertools.permutations(range(len(khipu_units))))
        real, order = chain_feasible(khipu_units, counts, kinds, slack, orders)
        rng = random.Random(seed)
        hits = sum(chain_feasible(khipu_units, random_counts(sum(counts), len(counts), rng), kinds, slack, orders)[0]
                   for _ in range(n_null))
        nb = sum(len(breakpoints(u, kinds)) - 2 for u in khipu_units) + len(khipu_units) - 1
        return real, hits / n_null, nb
    kb = [breakpoints(u, kinds) for u in khipu_units]
    real = feasible(kb, tuple(counts), slack)
    rng = random.Random(seed)
    hits = sum(feasible(kb, tuple(random_counts(sum(counts), len(counts), rng)), slack) for _ in range(n_null))
    return real, hits / n_null, sum(len(b) - 2 for b in kb)


# ---------- Санта: шестишнуровые группы ----------
def santa_units():
    rows = [r for r in csv.DictReader(open(ROOT / "extracted/okr_cords.csv"))
            if r["okr_num"] in ("KH0323", "KH0324", "KH0325", "KH0326", "KH0327", "KH0328")]
    by = collections.defaultdict(list)
    for r in rows:
        by[r["okr_num"]].append(r)
    out = {}
    for k in sorted(by):
        top = [r for r in sorted(by[k], key=lambda r: int(r["order"])) if r["parent_id"] == ""]
        units = []
        for cl, g in itertools.groupby(top, key=lambda r: r["group"]):
            g = list(g)
            for i in range(0, len(g) - len(g) % 6, 6):
                ch = g[i:i + 6]
                units.append({"cluster": cl, "color": ch[0]["color"], "first": int(ch[0]["value"]),
                              "attach": collections.Counter(r["attachment"] for r in ch).most_common(1)[0][0]})
        out[k] = units
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slack", type=int, default=4)
    ap.add_argument("--null", type=int, default=500)
    a = ap.parse_args()
    S = santa_units()
    print("Санта, единиц (шестёрок) по кипу:", {k: len(v) for k, v in S.items()})
    PACH = {"Намус": 18, "Коронго": 23, "Куючин": 9, "Куска": 7, "Гуауян": 41, "Укоре": 32}
    V, R = [18, 9, 41], [23, 7, 32]
    tests = [
        ("все 6 пачак, все кипу", list(S.values()), list(PACH.values())),
        ("V-половина (Намус, Куючин, Гуауян) на V-единицах",
         [[u for u in v if u["attach"] == "V"] for v in S.values()], V),
        ("R-половина (Коронго, Куска, Укоре) на R-единицах",
         [[u for u in v if u["attach"] == "R"] for v in S.values()], R),
    ]
    for kinds in (["cluster"], ["cluster", "attach"], ["cluster", "attach", "value"],
                  ["cluster", "attach", "color"], ["cluster", "attach", "value", "color"]):
        print(f"\nразрезы: {'+'.join(kinds)}")
        for name, units, counts in tests:
            real, frac, nb = evaluate([u for u in units if u], counts, kinds, a.slack, a.null)
            print(f"  {name:48} укладывается: {'ДА ' if real else 'нет'}  "
                  f"случайные числа укладываются в {frac:5.1%}  (разрезов {nb})")


if __name__ == "__main__":
    main()
