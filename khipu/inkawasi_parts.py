"""Инкавази: разбивки поставок. Итоги групп одного кипу (по порядку) против первых шнуров групп другого («брутто»
записей, по порядку) — как UR278 → UR275 и UR270 → UR274B.

Для каждой упорядоченной пары кипу архива (T — группы ≥ 3 шнуров с итогом ≥ 100; L — первые шнуры групп ≥ 2 шнуров,
значение ≥ 100): глобальное выравнивание с пропусками двух последовательностей; счёт — число равных пар (и «на один
узел» отдельно). Фон: значения L сдвинуты на d = ±1…±10 (то же выравнивание). Отбор: равных ≥ 3 и больше максимума фона.
Вывод: extracted/inkawasi_parts.txt.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
import inkawasi  # noqa: E402

OUT = ROOT / "extracted/inkawasi_parts.txt"
knot = lambda x, y: x != y and abs(x - y) in (1, 10, 100, 1000, 10000)


def align(X, Y):
    n, m, G = len(X), len(Y), 2
    sc = lambda x, y: 5 if x == y else 2 if knot(x, y) else -1
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
    eq = nr = 0
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        if P[i][j] == 0:
            if X[i - 1] == Y[j - 1]:
                eq += 1; pairs.append((i - 1, j - 1, "="))
            elif knot(X[i - 1], Y[j - 1]):
                nr += 1; pairs.append((i - 1, j - 1, "≈"))
            i -= 1; j -= 1
        elif P[i][j] == 1:
            i -= 1
        else:
            j -= 1
    return eq, nr, pairs[::-1]


def main():
    D = json.load(open(ROOT / "site/data.json"))
    ids = {k["id"] for k in D["khipus"] if k["site"] == "inkawasi"}
    K = inkawasi.load(ids)
    T = {k: [(gi + 1, sum(g)) for gi, g in enumerate(gs) if len(g) >= 3 and sum(g) >= 100] for k, gs in K.items()}
    L = {k: [(gi + 1, g[0]) for gi, g in enumerate(gs) if len(g) >= 2 and g[0] >= 100] for k, gs in K.items()}
    rows = []
    for t, ts in T.items():
        if len(ts) < 3:
            continue
        for l, ls in L.items():
            if l == t or len(ls) < 3:
                continue
            X, Y = [s for _, s in ts], [v for _, v in ls]
            eq, nr, pairs = align(X, Y)
            if eq < 3:
                continue
            null = [align(X, [y + d for y in Y])[0] for d in range(-10, 11) if d]
            if eq > max(null):
                rows.append((eq - sum(null) / len(null), t, l, eq, nr, sum(null) / len(null), max(null),
                             [(ts[i][0], ls[j][0], f) for i, j, f in pairs]))
    rows.sort(reverse=True)
    lines = [f"Group totals of T (in order) = first cords of L's groups (in order); shifted ±1…±10. Pairs above the maximum of the shifts: {len(rows)}"]
    for _, t, l, eq, nr, m, mx, pr in rows:
        lines.append(f"  {t:7} -> {l:7}: equal {eq}, one knot apart {nr}; shifted mean {m:.1f}, max {mx}")
        lines.append("      " + ", ".join(f"g{a}{f}g{b}" for a, b, f in pr))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
