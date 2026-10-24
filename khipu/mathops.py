"""Есть ли в кипу операции сложнее сложения: дроби (умножение на p/q с округлением), произведения (площадь),
степени, «площадь круга»?

Корпус KFG 2026 (extracted/plus2026_cords.csv), подвесные внутри групп.
1. Дроби: пары групп одной длины (3–12) в одном кипу; B_i = A_i · p/q с округлением (вниз, к ближайшему или вверх)
   во всех позициях, где A_i > 0; ≥ 3 таких позиций и ≥ 2 разных A; B ≥ 10 хотя бы в двух; p/q несократимая, q = 2…12,
   0 < p/q < 12, не целое. Отдельно записываем, каким округлением получается каждое совпадение.
2. Произведение: три шнура одной группы a, b, c (c — не a и не b), a, b ≥ 2, c ≥ 20, c = a · b.
3. Степени: два шнура одной группы, b = a² (a ≥ 4) или b = a³ (a ≥ 3).
4. Круг: два шнура одной группы, b = round(π a²) или b = 3 a² (a ≥ 3) — «площадь круга радиуса a».
Фон: те же поиски, где проверяемое (B, c, b) заменено на значение ± d, d = 1…5 (то же распределение величин).
Вывод: extracted/mathops.txt.
"""
import csv
import math
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus2026_cords.csv"
OUT = ROOT / "extracted/mathops.txt"
DS = [d for d in range(-5, 6) if d]
FRACS = sorted({Fraction(p, q) for q in range(2, 13) for p in range(1, 12 * q) if Fraction(p, q).denominator > 1})
ROUND = {"floor": math.floor, "nearest": lambda x: math.floor(x + 0.5), "ceil": math.ceil}


def load():
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"]:
            continue
        G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"] or 0)))
    return {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}


def frac_hits(A, B, d=0):
    """fractions f such that B (shifted by d) = round(A·f) in all positions where A > 0, with the rounding names"""
    pos = [(a, b + d) for a, b in zip(A, B) if a > 0]
    if len(pos) < 3 or len({a for a, _ in pos}) < 2 or sum(b >= 10 for _, b in pos) < 2:
        return []
    out = []
    a0, b0 = pos[0]
    for f in FRACS:
        x0 = a0 * f
        if not (math.floor(x0) <= b0 <= math.ceil(x0)):
            continue
        rs = [name for name, fn in ROUND.items() if all(fn(a * f) == b for a, b in pos)]
        if rs:
            out.append((f, rs))
    return out


def main():
    K = load()
    lines = []
    # 1. fractions between groups of one khipu
    real, null, hits, rounding = 0, Counter(), [], Counter()
    for k, gs in K.items():
        for i, A in enumerate(gs):
            for j, B in enumerate(gs):
                if i == j or len(A) != len(B) or not 3 <= len(A) <= 12:
                    continue
                h = frac_hits(A, B)
                if h:
                    real += 1
                    hits.append((k, i + 1, j + 1, A, B, h))
                    for f, rs in h:
                        exact = all((a * f).denominator == 1 for a in A if a > 0)
                        rounding["exact" if exact else "/".join(rs)] += 1
                for d in DS:
                    null[d] += bool(frac_hits(A, B, d))
    m = sum(null.values()) / len(DS)
    lines.append(f"1. Fractions B = round(A · p/q) between groups of one khipu: {real} group pairs; shifted ±1…±5: {m:.1f} "
                 f"(min {min(null.values())}, max {max(null.values())})")
    lines.append(f"   rounding that fits: {dict(rounding)}")
    for k, i, j, A, B, h in hits[:60]:
        lines.append(f"   {k} g{i} {A} -> g{j} {B}: " + ", ".join(f"{f} ({'/'.join(rs)})" for f, rs in h[:4]))
    # 2-4. within one group
    def scan(test, d):
        n, ex = 0, []
        for k, gs in K.items():
            for gi, g in enumerate(gs):
                for e in test(g, d):
                    n += 1
                    if d == 0 and len(ex) < 40:
                        ex.append((k, gi + 1, g, e))
        return n, ex

    def prod(g, d):
        out = []
        for ia, a in enumerate(g):
            for ib, b in enumerate(g):
                if ib <= ia or a < 2 or b < 2:
                    continue
                for ic, c in enumerate(g):
                    if ic in (ia, ib):
                        continue
                    if c + d >= 20 and c + d == a * b:
                        out.append(f"{a} × {b} = {c} (cords {ia + 1}, {ib + 1} -> {ic + 1})")
        return out

    def power(g, d):
        out = []
        for ia, a in enumerate(g):
            for ib, b in enumerate(g):
                if ia == ib:
                    continue
                if a >= 4 and b + d == a * a:
                    out.append(f"{a}² = {b}")
                if a >= 3 and b + d == a ** 3:
                    out.append(f"{a}³ = {b}")
        return out

    def circle(g, d):
        out = []
        for ia, a in enumerate(g):
            for ib, b in enumerate(g):
                if ia == ib or a < 3:
                    continue
                if b + d == round(math.pi * a * a):
                    out.append(f"π·{a}² ≈ {b}")
                if b + d == 3 * a * a:
                    out.append(f"3·{a}² = {b}")
        return out

    for name, test in (("2. Products c = a·b inside a group", prod), ("3. Powers b = a² or a³ inside a group", power),
                       ("4. Circle b = π·a² or 3·a² inside a group", circle)):
        r, ex = scan(test, 0)
        ns = [scan(test, d)[0] for d in DS]
        lines.append(f"\n{name}: real {r}; shifted ±1…±5: {sum(ns) / len(ns):.1f} (min {min(ns)}, max {max(ns)})")
        for k, gi, g, e in ex[:25]:
            lines.append(f"   {k} g{gi} {g[:12]}{' …' if len(g) > 12 else ''}: {e}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
