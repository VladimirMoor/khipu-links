"""Гипотеза: разбивки, как в Инкавази (UR278 → UR275), есть и в других местах — итоги групп одного кипу по порядку
равны первым шнурам групп другого кипу по порядку.

Весь корпус KFG 2026 (extracted/plus2026_cords.csv), подвесные. T: итоги групп ≥ 3 шнуров, итог ≥ 100 и не кратен 10.
L: первые шнуры групп ≥ 2 шнуров, ≥ 100. Пары-кандидаты: ≥ 3 общих значения (индекс); для них — выравнивание с
пропусками (inkawasi_parts.align), счёт — равные пары по порядку. Фон: значения L сдвинуты на d = ±1…±10, тот же отбор и
выравнивание; сравниваем число пар со счётом ≥ 3 и ≥ 4 и максимум. Повторные записи одного предмета (duplicates.csv) и
пары с одним музейным номером исключены. Вывод: extracted/ordered_parts.txt.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
import inkawasi_parts  # noqa: E402

CORDS = ROOT / "extracted/plus2026_cords.csv"
OUT = ROOT / "extracted/ordered_parts.txt"


def load():
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(CORDS)):
        if not r["parent_id"]:
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"] or 0)))
    return {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}


def scan(T, L, d, skip):
    idx = defaultdict(set)
    for l, ls in L.items():
        for _, v in ls:
            idx[v + d].add(l)
    out = []
    for t, ts in T.items():
        cnt = defaultdict(int)
        for _, s in ts:
            for l in idx.get(s, ()):
                if l != t:
                    cnt[l] += 1
        for l, c in cnt.items():
            if c < 3 or (t, l) in skip:
                continue
            eq, nr, pairs = inkawasi_parts.align([s for _, s in ts], [v + d for _, v in L[l]])
            if eq >= 3:
                out.append((eq, nr, t, l, pairs))
    return out


def main():
    K = load()
    D = json.load(open(ROOT / "site/data.json"))
    meta = {k["id"]: k for k in D["khipus"]}
    skip = set()
    for r in csv.DictReader(open(ROOT / "atlas/curated/duplicates.csv")):
        skip |= {(r["a"], r["b"]), (r["b"], r["a"])}
    num = lambda k: (meta.get(k, {}).get("num") or "").replace(" ", "").upper()
    for a in K:
        for b in K:
            if a != b and num(a) and num(a) == num(b):
                skip.add((a, b))
    T = {k: [(gi + 1, sum(g)) for gi, g in enumerate(gs) if len(g) >= 3 and sum(g) >= 100 and sum(g) % 10] for k, gs in K.items()}
    T = {k: v for k, v in T.items() if len(v) >= 3}
    L = {k: [(gi + 1, g[0]) for gi, g in enumerate(gs) if len(g) >= 2 and g[0] >= 100] for k, gs in K.items()}
    L = {k: v for k, v in L.items() if len(v) >= 3}
    real = scan(T, L, 0, skip)
    nulls = {d: scan(T, L, d, skip) for d in range(-10, 11) if d}
    lines = [f"T khipus {len(T)}, L khipus {len(L)}"]
    for th in (3, 4, 5):
        r = sum(1 for x in real if x[0] >= th)
        ns = [sum(1 for x in v if x[0] >= th) for v in nulls.values()]
        lines.append(f"pairs with ≥ {th} equal totals in order: real {r}; shifted mean {sum(ns) / len(ns):.1f}, max {max(ns)}")
    mx = max((x[0] for v in nulls.values() for x in v), default=0)
    lines.append(f"highest count among the shifts: {mx}")
    links = {(e["from"], e["to"]) for e in D["edges"]} | {(e["to"], e["from"]) for e in D["edges"]}
    for eq, nr, t, l, pairs in sorted(real, reverse=True)[:40]:
        tag = "known" if (t, l) in links else ("NEW" if eq > mx else "")
        lines.append(f"  {tag:5} {t:8} -> {l:8} equal {eq}, one knot apart {nr} · {meta.get(t, {}).get('site')} / {meta.get(l, {}).get('site')}"
                     f" · " + ", ".join(f"g{T[t][i][0]}{f}g{L[l][j][0]}" for i, j, f in pairs[:12]))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
