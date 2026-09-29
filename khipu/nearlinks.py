"""Скан «почти-копий»: подряд идущие шнуры двух кипу, чьи значения совпадают с точностью
±2% (только числа ≥ 100: мелкие и круглые совпадают слишком легко). Такие пары могут
быть разными записями одного предмета, копиями счёта или связанными отчётами, где часть
чисел расходится (ошибки записи, поправки).

Счёт диагонали (A, B, сдвиг) = число почти-совпадений в лучшем окне (разрывы ≤ GAP).
Значимость: тот же скан по корпусу, где у каждой кипу перемешан порядок шнуров;
порог = максимум по перемешанному корпусу.
"""
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from links import load_seqs, shuffled

ROOT = Path(__file__).resolve().parents[1]
MINV = 100
TOL = 0.02
GAP = 4
STEP = math.log(1 + TOL)


def bins(v):
    return int(math.log(v) / STEP)


def near(a, b):
    return abs(a - b) <= TOL * max(a, b)


def scan(P):
    idx = defaultdict(list)
    for inv, s in P.items():
        for i, v in enumerate(s):
            if v >= MINV:
                idx[bins(v)].append((inv, i, v))
    diag = defaultdict(list)
    for b, s in P.items():
        for j, v in enumerate(s):
            if v < MINV:
                continue
            bb = bins(v)
            for d in (-1, 0, 1):
                for a, i, u in idx.get(bb + d, ()):
                    if a == b or not near(u, v):
                        continue
                    diag[(a, b, i - j)].append(j)
    res = []
    for (a, b, off), js in diag.items():
        if len(js) < 4 or a > b:  # каждую неупорядоченную пару один раз
            continue
        js = sorted(set(js))
        best, cur, prev, start, bs = 0, 0, None, None, None
        for j in js:
            if prev is None or j - prev > GAP + 1:
                cur, start = 0, j
            cur += 1
            prev = j
            if cur > best:
                best, bs = cur, (start, j)
        res.append((best, a, b, off, bs))
    res.sort(reverse=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=3)
    ap.add_argument("--top", type=int, default=45)
    a = ap.parse_args()
    P, _ = load_seqs()
    meta = {k["INVESTIGATOR_NUM"]: k for k in json.load(open(ROOT / "extracted/kfg_khipus.json"))}
    res = scan(P)
    rng = random.Random(8)
    thr = max((scan(shuffled(P, rng)) or [(0,)])[0][0] for _ in range(a.null))
    print(f"порог (макс. по перемешанному корпусу, {a.null} раз): {thr} почти-совпадений")
    seen = set()
    for best, x, y, off, (j0, j1) in res:
        if (x, y) in seen:
            continue
        seen.add((x, y))
        mx, my = meta.get(x, {}), meta.get(y, {})
        same = mx.get("MUSEUM_NUM") and str(mx.get("MUSEUM_NUM")).replace(" ", "") == str(my.get("MUSEUM_NUM")).replace(" ", "")
        f = lambda m: f"{(m.get('MUSEUM_NAME') or '')[:26]} #{m.get('MUSEUM_NUM')} | {(m.get('PROVENANCE') or '')[:18]}"
        flag = "**" if best > thr else "  "
        print(f"{flag} {best:3}  {y:>12} [{j0}:{j1}] ~ {x:<12} сдвиг {off:+4d}  {'тот же №' if same else '        '}  {f(my)} || {f(mx)}")
        if len(seen) >= a.top:
            break


if __name__ == "__main__":
    main()
