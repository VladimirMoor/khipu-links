"""Сводки «S = G_i + G_{i+1} + … + G_j»: участок S равен поэлементной сумме подряд идущих
групп одного размера (2..MAXK групп) из другой кипу (--mode cross) или той же (--mode within,
S не перекрывается со слагаемыми).

Информативные позиции: сумма ≥ 100 и хотя бы два слагаемых в этой позиции ненулевые.
Допуск 0.2%. Порог — максимум по перемешанному корпусу. Использует функции sumscan.py.
"""
import argparse
import itertools
import random
from collections import defaultdict

from sumscan import MINV, candidates, index, load, match_at, shuffled

MINW, MINHIT, MAXK = 4, 4, 30


def runs_of(P, groups):
    for i in range(len(groups)):
        st, w = groups[i]
        if w < MINW:
            continue
        acc = P[st:st + w]
        nz = [1 if v > 0 else 0 for v in acc]
        for j in range(i + 1, min(len(groups), i + MAXK)):
            s2, w2 = groups[j]
            if w2 != w:
                break
            acc = [acc[k] + P[s2 + k] for k in range(w)]
            nz = [nz[k] + (1 if P[s2 + k] > 0 else 0) for k in range(w)]
            inf = [k for k in range(w) if acc[k] >= MINV and nz[k] >= 2]
            if len(inf) >= MINHIT:
                yield i, j, st, groups[j][0] + w, w, acc, inf


def scan(K, mode):
    idxs = {inv: index(P) for inv, (P, _) in K.items()}
    res = []
    for x, (P, groups) in K.items():
        for i, j, a0, a1, w, V, inf in runs_of(P, groups):
            targets = [x] if mode == "within" else [y for y in K if y != x]
            for y in targets:
                S = K[y][0]
                for s0 in candidates(idxs[y], S, V, inf):
                    if y == x and not (s0 + w <= a0 or s0 >= a1):
                        continue
                    hits, n = match_at(S, s0, V, inf)
                    if hits >= MINHIT and hits >= 0.6 * n:
                        res.append((hits, n, x, i + 1, j + 1, w, y, s0))
    res.sort(reverse=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["within", "cross"], default="cross")
    ap.add_argument("--own", action="store_true")
    ap.add_argument("--null", type=int, default=2)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    K = load(own=a.own)
    res = scan(K, a.mode)
    rng = random.Random(12)
    thr = 0
    for _ in range(a.null):
        r = scan(shuffled(K, rng), a.mode)
        thr = max(thr, r[0][0] if r else 0)
    print(f"[{a.mode}{' own' if a.own else ''}] находок: {len(res)}; порог (перемешанный корпус, {a.null} раз): {thr}")
    seen = set()
    for hits, n, x, gi, gj, w, y, s0 in res:
        key = (x, y, s0)
        if key in seen:
            continue
        seen.add(key)
        flag = "**" if hits > thr else "  "
        print(f"{flag} {hits:2}/{n:2}  S={y}[{s0}:{s0+w}] = Σ групп {gi}–{gj} кипу {x} (по {w} шнуров)  S:{K[y][0][s0:s0+min(w,6)]}")
        if len(seen) >= a.top:
            break


if __name__ == "__main__":
    main()
