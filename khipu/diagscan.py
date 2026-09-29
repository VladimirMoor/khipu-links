"""Копии по «диагонали групп» (обобщение AS175 → UR233 + UR232).

Для пары кипу A, B и групп a ∈ A, b ∈ B: s(a, b) — число позиций с равными значениями ≥ BIG
(если длины различаются на 1, у длинной выбрасывается одна позиция — «лишний пустой шнур»).
Диагональ c: D(c) = Σ_j s(A[j + c], B[j]). Копия группа-в-группу даёт одну диагональ,
далеко выше прочих. Счёт пары — лучшая D(c) и z против всех прочих сдвигов этой же пары
(тот же набор групп и значений, разрушен только порядок). Разрыв группы надвое сдвигает
диагональ на 1, поэтому берём лучшую сумму двух соседних диагоналей (c, c + 1).
Пропускаем пары с одинаковым музейным номером и пары, у которых мало общих значений.
"""
import csv
import itertools
import json
import os
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/plus_cords.csv"))
OUT = ROOT / "extracted/diagscan.txt"
BIG, MINCOMMON, MIND = 10, 8, 8


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        gs = [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
        if len(gs) >= 3:
            G[k] = gs
    return G


def s(a, b):
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b) if x == y and x >= BIG)
    if abs(len(a) - len(b)) != 1:
        return 0
    lo, hi = (a, b) if len(a) < len(b) else (b, a)
    return max(sum(1 for x, y in zip(lo, hi[:i] + hi[i + 1:]) if x == y and x >= BIG) for i in range(len(hi)))


def diag(A, B):
    D = defaultdict(int)
    vb = [set(v for v in b if v >= BIG) for b in B]
    for i, a in enumerate(A):
        va = set(v for v in a if v >= BIG)
        for j, b in enumerate(B):
            if va & vb[j]:
                D[i - j] += s(a, b)
    return D


def main():
    G = load()
    meta = {}
    for fn in ("kfg_khipus.json", "okr_khipus.json"):
        p = ROOT / "extracted" / fn
        if p.exists():
            for k in json.load(open(p)):
                meta.setdefault(k["INVESTIGATOR_NUM"], k)
    museum = {k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper() for k in G}
    bag = {k: Counter(v for g in G[k] for v in g if v >= BIG) for k in G}
    keys = sorted(G)
    res = []
    for x, y in itertools.combinations(keys, 2):
        if museum[x] == museum[y] or sum((bag[x] & bag[y]).values()) < MINCOMMON:
            continue
        D = diag(G[x], G[y])
        cs = range(-len(G[y]) + 1, len(G[x]))
        pair = {c: D.get(c, 0) + D.get(c + 1, 0) for c in cs}
        best = max(pair, key=pair.get)
        if pair[best] < MIND:
            continue
        others = [D.get(c, 0) for c in cs if c not in (best, best + 1)]
        m = sum(others) / len(others)
        sd = max((sum((v - m) ** 2 for v in others) / len(others)) ** 0.5, 0.5)
        res.append(((pair[best] - m) / sd, pair[best], best, x, y, max(others)))
    res.sort(reverse=True)
    lines = [f"кипу: {len(keys)}; пар с диагональю ≥ {MIND}: {len(res)}",
             f"{'z':>6} {'D':>4} {'c':>4} {'макс. проч.':>11}  пара"]
    for z, d, c, x, y, mo in res[:60]:
        mx, my = meta.get(x, {}), meta.get(y, {})
        lines.append(f"{z:6.1f} {d:4} {c:+4} {mo:11}  {x} ~ {y}   | {mx.get('PROVENANCE')} #{mx.get('MUSEUM_NUM')} "
                     f"/ {my.get('PROVENANCE')} #{my.get('MUSEUM_NUM')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()


def perm_p(A, B, n=300, seed=1):
    """Доля перестановок порядка групп B, где лучшая пара диагоналей ≥ реальной."""
    import random
    rnd = random.Random(seed)
    def best(A, B):
        D = diag(A, B)
        return max((D.get(c, 0) + D.get(c + 1, 0) for c in range(-len(B) + 1, len(A))), default=0)
    real = best(A, B)
    hit = 0
    for _ in range(n):
        Bp = B[:]
        rnd.shuffle(Bp)
        hit += best(A, Bp) >= real
    return real, (hit + 1) / (n + 1)


def check(pairs):
    G = load()
    lines = ["Перестановочный тест (порядок групп второго кипу, 300 раз):"]
    for x, y in pairs:
        real, p = perm_p(G[x], G[y])
        lines.append(f"  {x} ~ {y}: D = {real}, p = {p:.3f}")
    with open(OUT, "a") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
