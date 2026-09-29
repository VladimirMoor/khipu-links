"""Детектор «свёрнутых» копий по записям (ролям цветов).

1. Для каждой кипу ищем период цвета подвесных p ∈ {2, 3, 4}: доля позиций i, где цвет[i] =
   цвет[i−p], ≥ REG. Если периода нет — p = 1 (запись = подвесной с дочерними).
2. Для каждой фазы φ ∈ [0, p) режем подвесные на записи по p подряд, начиная с φ.
   Итог записи = сумма всех значений в записи (подвесные + всё поддерево дочерних).
3. Для каждой пары кипу и каждой пары фаз ищем лучшую диагональ (сдвиг) — серию записей
   с равными итогами (≥ MINV), допускаются разрывы ≤ GAP; счёт = Σ −log2 частоты итога.
4. Порог — максимум счёта по корпусу, где порядок записей в каждой кипу перемешан.
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
REG, MINV, GAP = 0.7, 5, 2


def load():
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

        def tree(r):
            if r["cord_id"] not in memo:
                memo[r["cord_id"]] = int(r["value"]) + sum(tree(c) for c in kids.get(r["cord_id"], []))
            return memo[r["cord_id"]]
        top = sorted(kids.get("", []), key=lambda r: int(r["order"]))
        K[inv] = [(r["color"], tree(r)) for r in top]
    return K


def period(cols):
    best = 1
    for p in (2, 3, 4):
        n = len(cols) - p
        if n < 3 * p:
            continue
        same = sum(1 for i in range(p, len(cols)) if cols[i] == cols[i - p]) / n
        # период должен быть «настоящим»: внутри цикла цвета различаются
        distinct = len(set(cols[:p])) > 1
        if same >= REG and distinct:
            return p
    return best


def record_seqs(K):
    """inv → список (p, φ, [итоги записей])."""
    R = {}
    for inv, cords in K.items():
        cols = [c for c, _ in cords]
        p = period(cols)
        out = []
        for ph in range(p):
            tot = [sum(v for _, v in cords[i:i + p]) for i in range(ph, len(cords) - p + 1, p)]
            out.append((p, ph, tot))
        R[inv] = out
    return R


def best_diag(a, b, w):
    idx = defaultdict(list)
    for j, v in enumerate(b):
        if v >= MINV:
            idx[v].append(j)
    diag = defaultdict(list)
    for i, v in enumerate(a):
        if v >= MINV:
            for j in idx.get(v, ()):
                diag[j - i].append((i, w.get(v, 15.0)))
    best = (0.0, None, 0)
    for off, hits in diag.items():
        hits.sort()
        cur, prev, cnt = 0.0, None, 0
        for i, wt in hits:
            if prev is not None and i - prev > GAP + 1:
                cur, cnt = 0.0, 0
            cur += wt
            cnt += 1
            prev = i
            if cur > best[0]:
                best = (cur, off, cnt)
    return best


def scan(R, w, pairs=None):
    invs = sorted(R)
    res = []
    for x in range(len(invs)):
        for y in range(x + 1, len(invs)):
            A, B = invs[x], invs[y]
            if pairs and (A, B) not in pairs and (B, A) not in pairs:
                continue
            top = (0.0,)
            for pa, fa, ta in R[A]:
                for pb, fb, tb in R[B]:
                    if pa == 1 and pb == 1 and not pairs:
                        pass
                    sc, off, cnt = best_diag(ta, tb, w)
                    if sc > top[0]:
                        top = (sc, pa, fa, pb, fb, off, cnt)
            if top[0] > 0:
                res.append((top, A, B))
    res.sort(key=lambda x: -x[0][0])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=2)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    K = load()
    R = record_seqs(K)
    allt = Counter(v for seqs in R.values() for _, _, t in seqs for v in t if v >= MINV)
    n = sum(allt.values())
    w = {v: -math.log2(c / n) for v, c in allt.items()}
    print("периоды:", Counter(seqs[0][0] for seqs in R.values()))
    for inv in ("UR053B", "UR053C", "UR270", "UR278"):
        print(f"  {inv}: период {R[inv][0][0]}" if inv in R else f"  {inv}: нет")
    res = scan(R, w)
    rng = random.Random(4)
    thr = 0.0
    for _ in range(a.null):
        Rs = {}
        for inv, seqs in R.items():
            new = []
            for p, ph, t in seqs:
                t2 = t[:]
                rng.shuffle(t2)
                new.append((p, ph, t2))
            Rs[inv] = new
        r2 = scan(Rs, w)
        thr = max(thr, r2[0][0][0] if r2 else 0)
    meta = {k["INVESTIGATOR_NUM"]: k for fn in ("kfg_khipus.json", "plus_khipus.json")
            if (ROOT / "extracted" / fn).exists() for k in json.load(open(ROOT / "extracted" / fn))}
    print(f"порог (перемешанный порядок записей, {a.null} раз): {thr:.1f} бит")
    for k, (top, A, B) in enumerate(res[:a.top]):
        sc, pa, fa, pb, fb, off, cnt = top
        mA, mB = meta.get(A, {}), meta.get(B, {})
        same = mA.get("MUSEUM_NUM") and str(mA.get("MUSEUM_NUM")).replace(" ", "") == str(mB.get("MUSEUM_NUM")).replace(" ", "")
        flag = "**" if sc > thr else "  "
        print(f"{flag} {sc:6.1f} бит {cnt:3} зап.  {A:>12}(p{pa},φ{fa}) ~ {B:<12}(p{pb},φ{fb}) сдвиг {off:+d}  "
              f"{'тот же №' if same else '        '} {(mA.get('MUSEUM_NAME') or '')[:20]} || {(mB.get('MUSEUM_NAME') or '')[:20]}")


if __name__ == "__main__":
    main()
