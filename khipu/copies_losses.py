"""Копии: утраченное и описки.

Связи атласа типа copy/excerpt/details/fold; подвесные двух кипу выравниваются по значениям (с пропусками).
1. Нули внутри участков, где оба соседа равны и ненулевые: оборванный шнур (конец B или длина < 10 см) против целого —
   есть ли у партнёра число (точный тест Фишера). Список восстановлений — extracted/restored_from_copies.csv.
2. Расхождения на сопоставленных местах рядом с совпадениями (оба шнура целые и ненулевые): на один узел, одна цифра в
   одном разряде, сдвиг ×10, перестановка цифр, другое; фон — расходящиеся значения перемешаны между местами (3000 раз).
Вывод: extracted/copies_losses.txt.
"""
import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus2026_cords.csv"
OUT = ROOT / "extracted/copies_losses.txt"


def align(X, Y):
    n, m, G = len(X), len(Y), 2
    sc = lambda x, y: (5 if x >= 10 else 1) if x == y else -1
    H = [[0.0] * (m + 1) for _ in range(n + 1)]
    P = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        H[i][0], P[i][0] = -G * i, 1
    for j in range(1, m + 1):
        H[0][j], P[0][j] = -G * j, 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d, u, l = H[i - 1][j - 1] + sc(X[i - 1], Y[j - 1]), H[i - 1][j] - G, H[i][j - 1] - G
            H[i][j], P[i][j] = (d, 0) if d >= u and d >= l else (u, 1) if u >= l else (l, 2)
    out, i, j = [], n, m
    while i > 0 and j > 0:
        if P[i][j] == 0:
            out.append((i - 1, j - 1)); i -= 1; j -= 1
        elif P[i][j] == 1:
            i -= 1
        else:
            j -= 1
    return out[::-1]


def kind(x, y):
    d, sx, sy = abs(x - y), str(x), str(y)
    if d in (1, 10, 100, 1000, 10000):
        return "one knot"
    if len(sx) == len(sy) and sorted(sx) == sorted(sy):
        return "digits swapped"
    if x * 10 == y or y * 10 == x:
        return "place shifted (×10)"
    if len(sx) == len(sy) and sum(a != b for a, b in zip(sx, sy)) == 1:
        return "one digit changed"
    return "other"


def main():
    D = json.load(open(ROOT / "site/data.json"))
    C = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if not r["parent_id"]:
            C[r["inv_num"]].append((int(r["order"]), int(r["value"] or 0), r["termination"], float(r["length"] or 0), r["group"]))
    for k in C:
        C[k].sort()
    broken = lambda c: c[2] == "B" or (c[3] and c[3] < 10)
    zeros = {"broken": [0, 0], "intact": [0, 0]}
    restored, diffs = [], []
    for e in D["edges"]:
        if e["type"] not in ("copy", "excerpt", "details", "fold"):
            continue
        a, b = e["from"], e["to"]
        if a not in C or b not in C:
            continue
        A, B = [c[1] for c in C[a]], [c[1] for c in C[b]]
        pairs = align(A, B)
        eq = {(i, j) for i, j in pairs if A[i] == B[j] and A[i] > 0}
        for i, j in pairs:
            inside = (i - 1, j - 1) in eq and (i + 1, j + 1) in eq
            if inside:
                for (X, Y, ii, jj, K1, K2, n1, n2) in ((A, B, i, j, C[a], C[b], a, b), (B, A, j, i, C[b], C[a], b, a)):
                    if X[ii] == 0:
                        cls = "broken" if broken(K1[ii]) else "intact"
                        zeros[cls][0] += 1; zeros[cls][1] += Y[jj] > 0
                        if cls == "broken" and Y[jj] > 0:
                            restored.append([n1, K1[ii][0], K1[ii][4], K1[ii][3], Y[jj], n2, K2[jj][0]])
            if ((i - 1, j - 1) in eq or (i + 1, j + 1) in eq) and A[i] != B[j] and A[i] > 0 and B[j] > 0 \
                    and not broken(C[a][i]) and not broken(C[b][j]):
                diffs.append((A[i], B[j]))
    (nb, fb), (ni, fi) = zeros["broken"], zeros["intact"]
    n, r1, c1 = nb + ni, nb, fb + fi
    p = sum(comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1) for x in range(fb, min(r1, c1) + 1))
    lines = [f"1. Zero cords inside runs of equal neighbours: broken {nb}, partner has a value on {fb}; intact {ni}, on {fi}; "
             f"one-sided Fisher p = {p:.4f}"]
    real = Counter(kind(x, y) for x, y in diffs)
    xs, ys = [x for x, _ in diffs], [y for _, y in diffs]
    rnd, sims = random.Random(10), defaultdict(list)
    for _ in range(3000):
        rnd.shuffle(ys)
        c = Counter(kind(x, y) for x, y in zip(xs, ys))
        for k in ("one knot", "one digit changed", "place shifted (×10)", "digits swapped", "other"):
            sims[k].append(c[k])
    lines.append(f"2. Differing matched values next to equal ones (cords intact, both nonzero): {len(diffs)}")
    for k in ("one knot", "one digit changed", "place shifted (×10)", "digits swapped", "other"):
        pk = (1 + sum(s >= real[k] for s in sims[k])) / 3001
        lines.append(f"   {k}: {real[k]}; shuffled {statistics.mean(sims[k]):.1f}; p(≥) {pk:.4f}")
    with open(ROOT / "extracted/restored_from_copies.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["khipu", "cord", "group", "length_cm", "value_on_partner", "partner", "partner_cord"])
        w.writerows(restored)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
