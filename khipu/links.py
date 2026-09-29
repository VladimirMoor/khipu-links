"""Граф связей между кипу корпуса: систематический поиск по всем парам.

Для каждой кипу две последовательности:
  P — значения подвесных шнуров (шнур + дочерние) в порядке на основном шнуре;
  G — суммы верхних групп (кластеров) в порядке.
Ищем «диагонали» — пары участков, где числа совпадают подряд со сдвигом off:
  копия:     P(B)[j] = P(A)[j+off]
  иерархия:  P(B)[j] = G(A)[j+off]   (шнуры B — итоги групп A, как в Пуручуко)
Вес совпадения = −log2 частоты числа в корпусе (числа < MIN не считаются: 1–9 и
круглые повсюду). Счёт диагонали = сумма весов совпадений в лучшем окне, где между
соседними совпадениями не больше GAP позиций.

Значимость: тот же поиск по корпусу, где у каждой кипу перемешаны значения P и G
(состав сохранён, порядок разрушен). Порог = максимум счёта по «перемешанному» корпусу:
всё, что выше, — не случайность при данном числе сравнений.
"""
import argparse
import csv
import itertools
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))
MIN = 10
GAP = 3


def load_seqs():
    by = defaultdict(list)
    with open(CORDS) as f:
        for r in csv.DictReader(f):
            by[r["inv_num"]].append(r)
    P, G = {}, {}
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
        P[inv] = [sub(r) for r in top]
        G[inv] = []
        for _, it in itertools.groupby(top, key=lambda r: r["group"]):
            vals = [sub(r) for r in it]
            # тривиальная группа (меньше двух непустых шнуров) — её «итог» равен шнуру; не индексируем
            G[inv].append(sum(vals) if sum(1 for v in vals if v > 0) >= 2 else -1)
    return P, G


def weights(P):
    c = Counter(v for s in P.values() for v in s if v >= MIN)
    n = sum(c.values())
    return {v: -math.log2(k / n) for v, k in c.items()}


def index(seqs):
    idx = defaultdict(list)
    for inv, s in seqs.items():
        for i, v in enumerate(s):
            if v >= MIN:
                idx[v].append((inv, i))
    return idx


def diagonals(Bseqs, Aidx, w, same_ok=False):
    """(A, B, off) → список (j, weight) совпадений P(B)[j] = X(A)[j+off]."""
    diag = defaultdict(list)
    for b, s in Bseqs.items():
        for j, v in enumerate(s):
            if v < MIN:
                continue
            for a, i in Aidx.get(v, ()):
                if a == b and not same_ok:
                    continue
                if a == b and i == j:
                    continue
                diag[(a, b, i - j)].append((j, w.get(v, 20.0), v))
    return diag


def best_window(hits):
    """Лучшая серия совпадений на диагонали с разрывами ≤ GAP."""
    hits.sort()
    best, cur, start, prev = (0.0, 0, None, None), 0.0, None, None
    cnt = 0
    for j, wt, v in hits:
        if prev is None or j - prev > GAP + 1:
            cur, cnt, start = 0.0, 0, j
        cur += wt
        cnt += 1
        prev = j
        if cur > best[0]:
            best = (cur, cnt, start, j)
    return best


def scan(P, G, w, kind):
    Bseqs = P
    Aidx = index(P if kind == "copy" else G)
    res = []
    for (a, b, off), hits in diagonals(Bseqs, Aidx, w, same_ok=(kind == "hier")).items():
        if len(hits) < 3:
            continue
        sc, cnt, j0, j1 = best_window(hits)
        if cnt >= 3:
            res.append((sc, cnt, a, b, off, j0, j1))
    res.sort(reverse=True)
    return res


def shuffled(seqs, rng):
    out = {}
    for k, s in seqs.items():
        t = s[:]
        rng.shuffle(t)
        out[k] = t
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["copy", "hier"], default="copy")
    ap.add_argument("--null", type=int, default=3)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    P, G = load_seqs()
    w = weights(P)
    res = scan(P, G, w, a.kind)
    rng = random.Random(4)
    thr = []
    for _ in range(a.null):
        r = scan(shuffled(P, rng), shuffled(G, rng), w, a.kind)
        thr.append(r[0][0] if r else 0)
    t = max(thr)
    print(f"[{a.kind}] диагоналей с ≥3 совпадениями: {len(res)}; порог (макс. по перемешанному корпусу, {a.null} раз): {t:.1f} бит")
    seen = set()
    for sc, cnt, ai, bi, off, j0, j1 in res:
        key = tuple(sorted((ai, bi))) if a.kind == "copy" else (ai, bi)
        if key in seen:
            continue
        seen.add(key)
        flag = "**" if sc > t else "  "
        seq = P[bi][j0:j1 + 1]
        src = (P if a.kind == "copy" else G)[ai][j0 + off:j1 + off + 1]
        print(f"{flag} {sc:6.1f} бит  {cnt:2} совп.  B={bi} [{j0}:{j1}]  A={ai} сдвиг {off:+d}   B:{seq[:10]}  A:{src[:10]}")
        if len(seen) >= a.top:
            break


if __name__ == "__main__":
    main()
