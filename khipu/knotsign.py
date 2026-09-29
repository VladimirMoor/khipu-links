"""Довязанный узел («выдано», «оплачено»)? Знак расхождений на один узел между копиями.

Идея (Владимир): получатель или учётчик отмечал событие новым узлом. Тогда в паре
«оригинал — копия» расхождения на один узел (±1, ±10, ±100 … в одном разряде) шли бы в одну
сторону. Фон — две независимые записи одного и того же предмета (там расхождения — ошибки
чтения, знак ~50/50). Шнуры, оборванные хотя бы в одной записи, не считаем.
Выравнивание: лучшая диагональ групп (diagscan), у более длинной группы выбрасываем позицию,
дающую больше точных совпадений. Вывод: extracted/knotsign.txt.
"""
import csv
import itertools
import math
from collections import defaultdict
from pathlib import Path

import diagscan

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/knotsign.txt"

COPIES = [("UR1175", "UR233"), ("UR1175", "UR232"), ("AS038", "UR122"), ("UR218", "UR1118"),
          ("UR267A", "UR255")]
SAME = [("AS038", "HP036"), ("AS068", "UR281"), ("AS047", "KH0058"), ("AS125", "UR247"),
        ("AS181", "UR236")]


def cords():
    by = defaultdict(list)
    for r in csv.DictReader(open(diagscan.CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        G[k] = [[(int(r["value"]), r["termination"] == "B") for r in g]
                for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    return G


def one_knot(a, b):
    """+1 / −1, если b отличается от a ровно одним узлом в одном разряде, иначе 0."""
    d = b - a
    if d == 0:
        return 0
    k = int(round(math.log10(abs(d)))) if abs(d) > 0 else 0
    if abs(d) != 10 ** k:
        return 0
    return 1 if d > 0 else -1


def align(A, B):
    vals = lambda X: [[v for v, _ in g] for g in X]
    D = diagscan.diag(vals(A), vals(B))
    c = max(D, key=lambda c: D[c] + D.get(c + 1, 0))
    pairs = []
    for j, b in enumerate(B):
        best = None
        for cc in (c, c + 1):
            i = j + cc
            if not 0 <= i < len(A):
                continue
            a = A[i]
            opts = [(a, b)]
            if len(b) == len(a) + 1:
                opts = [(a, b[:t] + b[t + 1:]) for t in range(len(b))]
            elif len(a) == len(b) + 1:
                opts = [(a[:t] + a[t + 1:], b) for t in range(len(a))]
            for x, y in opts:
                if len(x) == len(y):
                    sc = sum(1 for (u, _), (w, _) in zip(x, y) if u == w and u >= 10)
                    if best is None or sc > best[0]:
                        best = (sc, list(zip(x, y)))
        if best and best[0] >= 2:
            pairs += best[1]
    return pairs


def count(G, x, y):
    up = down = eq = other = 0
    for (a, ba), (b, bb) in align(G[x], G[y]):
        if ba or bb:
            continue
        s = one_knot(a, b)
        if a == b:
            eq += 1
        elif s > 0:
            up += 1
        elif s < 0:
            down += 1
        else:
            other += 1
    return eq, up, down, other


def main():
    G = cords()
    lines = ["пара (первая → вторая): равны / +1 узел у второй / −1 узел / прочие расхождения"]
    tot = {}
    for name, L in (("копии", COPIES), ("одна вещь, две записи", SAME)):
        U = Dn = 0
        lines.append(name + ":")
        for x, y in L:
            eq, up, down, other = count(G, x, y)
            U += up
            Dn += down
            lines.append(f"  {x} → {y}: {eq} / +{up} / −{down} / {other}")
        n = U + Dn
        p = sum(math.comb(n, k) for k in range(max(U, Dn), n + 1)) / 2 ** n * 2 if n else 1
        lines.append(f"  итого +{U} / −{Dn}; двусторонний биномиальный p = {min(p, 1):.3f}")
        tot[name] = (U, Dn)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
