"""Поиск повреждённых копий: совместимость значений с учётом обрывов шнуров.

Кандидаты: пары кипу, у которых на одном сдвиге ≥ ANCH точно равных подвесных (≥ 100).
Для сдвига считаем по перекрытию:
  exact  — равны (оба ≥ 10);
  trunc  — одно = другое с обнулёнными младшими разрядами (обрыв: 4130 → 4000), меньшее > 0;
  zero   — одно 0, у другого число, и шнур с нулём оборван (termination B);
  miss   — оба ≠ 0 и несовместимы.
Счёт = (exact + trunc) − miss по позициям, где хотя бы одно число ≥ 10. Фон — тот же счёт на
всех прочих сдвигах пары: z = (счёт − среднее) / sd.
"""
import csv
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))
ANCH, MINV = 2, 100


def load():
    by = defaultdict(list)
    with open(CORDS) as f:
        for r in csv.DictReader(f):
            if r["parent_id"] == "":
                by[r["inv_num"]].append(r)
    return {k: [(int(r["value"]), r["termination"]) for r in sorted(v, key=lambda r: int(r["order"]))]
            for k, v in by.items()}


def trunc_of(big, small):
    if small <= 0 or small >= big:
        return False
    p = 10
    while p <= big:
        if (big // p) * p == small:
            return True
        p *= 10
    return False


def score(A, B, off):
    ex = tr = ze = mi = 0
    for i, (a, ta) in enumerate(A):
        j = i + off
        if not (0 <= j < len(B)):
            continue
        b, tb = B[j]
        if max(a, b) < 10:
            continue
        if a == b:
            ex += 1
        elif trunc_of(a, b) or trunc_of(b, a):
            tr += 1
        elif (a == 0 and ta == "B") or (b == 0 and tb == "B"):
            ze += 1
        elif a == 0 or b == 0:
            continue
        else:
            mi += 1
    return ex + tr - mi, ex, tr, ze, mi


def main():
    K = load()
    idx = defaultdict(list)
    for k, s in K.items():
        for i, (v, _) in enumerate(s):
            if v >= MINV:
                idx[v].append((k, i))
    diag = defaultdict(int)
    for v, lst in idx.items():
        if len(lst) > 60:
            continue
        for x in range(len(lst)):
            for y in range(x + 1, len(lst)):
                (a, i), (b, j) = lst[x], lst[y]
                if a == b:
                    continue
                if a > b:
                    a, b, i, j = b, a, j, i
                diag[(a, b, j - i)] += 1
    cands = [(a, b, off) for (a, b, off), n in diag.items() if n >= ANCH]
    print(f"кандидатов (пара, сдвиг): {len(cands)}")
    res = []
    for a, b, off in cands:
        A, B = K[a], K[b]
        sc = score(A, B, off)
        bg = [score(A, B, o)[0] for o in range(-len(A) + 1, len(B)) if o != off]
        if len(bg) < 5:
            continue
        m = sum(bg) / len(bg)
        sd = (sum((x - m) ** 2 for x in bg) / len(bg)) ** 0.5 or 1.0
        res.append(((sc[0] - m) / sd, sc, a, b, off))
    res.sort(key=lambda x: -x[0])
    print(f"{'z':>6}  {'точно':>5} {'обрыв':>5} {'ноль/B':>6} {'промах':>6}  пара")
    seen = set()
    for z, (s, ex, tr, ze, mi), a, b, off in res:
        if (a, b) in seen:
            continue
        seen.add((a, b))
        print(f"{z:6.1f}  {ex:5} {tr:5} {ze:6} {mi:6}  {a} ~ {b} сдвиг {off:+d}")
        if len(seen) >= 45:
            break


if __name__ == "__main__":
    main()
