"""Копии с перестановкой шнуров («свёрнутые» копии, тройки ↔ пары, подвесной ↔ дочерний).

Каждая кипу → плоская последовательность значений: подвесной, затем его дочерние (в глубину).
Окна по W значений с шагом STEP. Окно = мультимножество значений ≥ MINV. Сходство двух окон
разных кипу = сумма весов общих значений (с учётом кратности), вес = −log2 частоты значения
в корпусе. Для каждой пары кипу берём лучшую пару окон. Порог — максимум по корпусу, где
значения каждой кипу перемешаны (состав сохранён, соседство разрушено).
"""
import argparse
import csv
import json
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))
W, STEP, MINV, CAP = 16, 4, 3, 400


def flat_seqs():
    by = defaultdict(list)
    with open(CORDS) as f:
        for r in csv.DictReader(f):
            by[r["inv_num"]].append(r)
    S = {}
    for inv, rows in by.items():
        kids = defaultdict(list)
        for r in rows:
            kids[r["parent_id"]].append(r)
        for k in kids:
            kids[k].sort(key=lambda r: int(r["order"]))
        out = []

        def walk(r):
            out.append(int(r["value"]))
            for c in kids.get(r["cord_id"], []):
                walk(c)
        for r in kids.get("", []):
            walk(r)
        S[inv] = out
    return S


def windows(S):
    win = []
    for inv, s in S.items():
        for st in range(0, max(1, len(s) - W + 1), STEP):
            bag = Counter(v for v in s[st:st + W] if v >= MINV)
            if sum(bag.values()) >= 5:
                win.append((inv, st, bag))
    return win


def scan(S, wts):
    win = windows(S)
    post = defaultdict(list)
    for wi, (inv, st, bag) in enumerate(win):
        for v in bag:
            post[v].append(wi)
    best = {}
    for wi, (inv, st, bag) in enumerate(win):
        acc = defaultdict(float)
        for v, c in bag.items():
            lst = post[v]
            if len(lst) > CAP:
                continue
            for wj in lst:
                if wj <= wi:
                    continue
                inv2, st2, bag2 = win[wj]
                if inv2 == inv:
                    continue
                acc[wj] += min(c, bag2[v]) * wts.get(v, 15.0)
        for wj, sc in acc.items():
            inv2, st2, _ = win[wj]
            key = tuple(sorted((inv, inv2)))
            if sc > best.get(key, (0,))[0]:
                best[key] = (sc, inv, st, inv2, st2)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=2)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    S = flat_seqs()
    cnt = Counter(v for s in S.values() for v in s if v >= MINV)
    n = sum(cnt.values())
    wts = {v: -math.log2(c / n) for v, c in cnt.items()}
    best = scan(S, wts)
    rng = random.Random(3)
    thr = 0.0
    for _ in range(a.null):
        Sh = {}
        for k, s in S.items():
            t = s[:]
            rng.shuffle(t)
            Sh[k] = t
        b = scan(Sh, wts)
        thr = max(thr, max(x[0] for x in b.values()))
    meta = {}
    for fn in ("kfg_khipus.json", "plus_khipus.json"):
        p = ROOT / "extracted" / fn
        if p.exists():
            for k in json.load(open(p)):
                meta[k["INVESTIGATOR_NUM"]] = k
    print(f"пар кипу: {len(best)}; порог (перемешанный корпус, {a.null} раз): {thr:.1f} бит")
    for key, (sc, i1, s1, i2, s2) in sorted(best.items(), key=lambda x: -x[1][0])[:a.top]:
        m1, m2 = meta.get(i1, {}), meta.get(i2, {})
        same = m1.get("MUSEUM_NUM") and str(m1.get("MUSEUM_NUM")).replace(" ", "") == str(m2.get("MUSEUM_NUM")).replace(" ", "")
        flag = "**" if sc > thr else "  "
        print(f"{flag} {sc:6.1f}  {i1:>12}[{s1}] ~ {i2:<12}[{s2}] {'тот же №' if same else '        '} "
              f"{(m1.get('MUSEUM_NAME') or '')[:22]} #{m1.get('MUSEUM_NUM')} || {(m2.get('MUSEUM_NAME') or '')[:22]} #{m2.get('MUSEUM_NUM')}")


if __name__ == "__main__":
    main()
