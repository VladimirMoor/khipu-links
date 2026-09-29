"""Детектор сводок «S = A + B»: участок шнуров S равен поэлементной сумме двух групп A и B
(как в KH0049, где первые 18 шнуров = сумма двух следующих групп по 18).

A, B — верхние группы (кластеры) одинакового размера w ≥ MINW в кипу X; S — любой участок из
w подряд идущих подвесных (не обязательно одна группа: у KH0049 сводка разбита на 9+9) в той
же кипу (--mode within) или в другой кипу (--mode cross). Значение шнура — вместе с
дочерними. Совпадение позиции: |S − (A+B)| ≤ TOL·max(1, A+B), только позиции, где A+B ≥ 10.
Считаются только «информативные» позиции: A>0, B>0, A+B ≥ 100 (иначе S=A при B=0 или
узоры из десяток дают ложные «суммы»). Допуск 0.2% (ошибка записи узла в крупном числе).
Счёт = число совпавших информативных позиций; требуется ≥ MINHIT и доля ≥ 0.5.

Значимость: тот же поиск по корпусу с перемешанными внутри каждой кипу значениями
(состав и размеры групп сохранены); порог — максимум счёта по перемешанному корпусу.
"""
import argparse
import csv
import itertools
import os
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))
MINW, MINHIT, TOL = 4, 4, 0.002
MINV = 100


def load(own=False):
    by = defaultdict(list)
    with open(CORDS) as f:
        for r in csv.DictReader(f):
            by[r["inv_num"]].append(r)
    K = {}
    for inv, rows in by.items():
        kids = defaultdict(list)
        for r in rows:
            kids[r["parent_id"]].append(r)
        memo = {}

        def sub(r):
            if r["cord_id"] not in memo:
                memo[r["cord_id"]] = int(r["value"]) + sum(sub(c) for c in kids.get(r["cord_id"], []))
            return memo[r["cord_id"]]
        top = sorted([r for r in rows if r["parent_id"] == ""], key=lambda r: int(r["order"]))
        P = [int(r["value"]) if own else sub(r) for r in top]
        groups, i = [], 0
        for _, it in itertools.groupby(top, key=lambda r: r["group"]):
            n = len(list(it))
            groups.append((i, n))
            i += n
        K[inv] = (P, groups)
    return K


def ok(s, t):
    return abs(s - t) <= TOL * max(1, t)


def informative(A, B):
    """Позиции, где обе группы вносят вклад и сумма достаточно велика."""
    return [k for k in range(len(A)) if A[k] > 0 and B[k] > 0 and A[k] + B[k] >= MINV]


def pairs_of(P, groups):
    """Пары групп одинакового размера (A раньше B)."""
    bysize = defaultdict(list)
    for st, n in groups:
        if n >= MINW:
            bysize[n].append(st)
    for n, starts in bysize.items():
        if len(starts) > 60:
            starts = starts[:60]
        for a, b in itertools.combinations(starts, 2):
            A, B = P[a:a + n], P[b:b + n]
            inf = informative(A, B)
            if len(inf) >= MINHIT:
                yield a, b, n, [A[k] + B[k] for k in range(n)], inf


import math
STEP = math.log(1.004)


def index(P):
    idx = defaultdict(list)
    for i, v in enumerate(P):
        if v >= MINV:
            idx[int(math.log(v) / STEP)].append(i)
    return idx


def candidates(idx, S, V, inf):
    votes = defaultdict(int)
    for k in inf:
        b0 = int(math.log(V[k]) / STEP)
        for d in (-1, 0, 1):
            for s in idx.get(b0 + d, ()):
                if ok(S[s], V[k]):
                    votes[s - k] += 1
    return [s0 for s0, c in votes.items() if c >= MINHIT]


def match_at(S, s0, V, inf):
    n = len(V)
    if s0 < 0 or s0 + n > len(S):
        return 0, 0
    hits = sum(1 for k in inf if ok(S[s0 + k], V[k]))
    return hits, len(inf)


def scan(K, mode):
    res = []
    idxs = {inv: index(P) for inv, (P, _) in K.items()}
    for x, (P, groups) in K.items():
        for a, b, n, V, inf in pairs_of(P, groups):
            targets = [x] if mode == "within" else [y for y in K if y != x]
            for y in targets:
                S = K[y][0]
                for s0 in candidates(idxs[y], S, V, inf):
                    if y == x and (abs(s0 - a) < n or abs(s0 - b) < n):
                        continue  # S не должна перекрываться с A или B
                    hits, nz = match_at(S, s0, V, inf)
                    if hits >= MINHIT and hits >= 0.5 * nz:
                        res.append((hits, nz, x, a, b, n, y, s0))
    res.sort(reverse=True)
    return res


def shuffled(K, rng):
    out = {}
    for inv, (P, g) in K.items():
        Q = P[:]
        rng.shuffle(Q)
        out[inv] = (Q, g)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["within", "cross"], default="within")
    ap.add_argument("--null", type=int, default=3)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--own", action="store_true", help="значение подвесного без дочерних")
    a = ap.parse_args()
    K = load(own=a.own)
    res = scan(K, a.mode)
    rng = random.Random(6)
    thr = 0
    for _ in range(a.null):
        r = scan(shuffled(K, rng), a.mode)
        thr = max(thr, r[0][0] if r else 0)
    print(f"[{a.mode}] находок: {len(res)}; порог (макс. по перемешанному корпусу, {a.null} раз): {thr}")
    seen = set()
    for hits, nz, x, s_a, s_b, n, y, s0 in res:
        key = (x, y, s0)
        if key in seen:
            continue
        seen.add(key)
        P = K[x][0]
        flag = "**" if hits > thr else "  "
        print(f"{flag} {hits:2}/{nz:2}  S={y}[{s0}:{s0+n}]  = A {x}[{s_a}:{s_a+n}] + B {x}[{s_b}:{s_b+n}]   "
              f"S:{K[y][0][s0:s0+min(n,6)]} A:{P[s_a:s_a+min(n,6)]} B:{P[s_b:s_b+min(n,6)]}")
        if len(seen) >= a.top:
            break


if __name__ == "__main__":
    main()
