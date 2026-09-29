"""Сеть связей внутри архива Пачакамака (+ Уачо): точные равенства крупных величин между кипу.

Для каждого кипу: значения подвесных (свои и с дочерними), значения дочерних, суммы групп,
суммы 2–3 соседних групп, итог кипу. Берём величины ≥ MINV. Равенство между разными кипу
(музейные номера разные, известные дубли исключены) — точное. Фон: величины одного кипу пары
сдвинуты на d = ±1…±30; сколько равенств тогда. Вывод: extracted/pachanet.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/pachanet.txt"
MINV = 1000
SAME = {frozenset(p) for p in [("AS125", "UR247"), ("UR1175", "UR1175")]}


def quantities(R):
    kids = defaultdict(list)
    for r in R:
        if r["parent_id"]:
            kids[r["parent_id"]].append(r)
    memo = {}

    def tree(r):
        if r["cord_id"] not in memo:
            memo[r["cord_id"]] = int(r["value"]) + sum(tree(c) for c in kids[r["cord_id"]])
        return memo[r["cord_id"]]

    top = sorted((r for r in R if not r["parent_id"]), key=lambda r: int(r["order"]))
    q = []
    for r in top:
        q.append((int(r["value"]), f"шнур {r['order']}"))
        if kids[r["cord_id"]]:
            q.append((tree(r), f"шнур {r['order']}+доч."))
    for r in R:
        if r["parent_id"]:
            q.append((int(r["value"]), f"доч. {r['order']}"))
    gs = [(g, sum(int(r["value"]) for r in grp)) for g, grp in
          ((g, list(grp)) for g, grp in itertools.groupby(top, key=lambda r: r["group"]))]
    for i, (g, s) in enumerate(gs):
        q.append((s, f"г{g}"))
        for w in (2, 3):
            if i + w <= len(gs):
                q.append((sum(x for _, x in gs[i:i + w]), f"г{g}–г{gs[i + w - 1][0]}"))
    q.append((sum(s for _, s in gs), "итог"))
    return [(v, lab) for v, lab in q if v >= MINV]


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for k in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(k["INVESTIGATOR_NUM"], k)
    keep = {k for k, m in meta.items() if any(s in str(m.get("PROVENANCE", "")).lower() for s in ("pachac", "huacho"))}
    rows = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["inv_num"] in keep:
            rows[r["inv_num"]].append(r)
    Q = {k: quantities(R) for k, R in rows.items()}
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    idx = {k: defaultdict(list) for k in Q}
    for k, q in Q.items():
        for v, lab in q:
            idx[k][v].append(lab)

    def count(d):
        hits = []
        for x, y in itertools.combinations(sorted(Q), 2):
            if mus(x) == mus(y) or frozenset((x, y)) in SAME:
                continue
            for v in set(idx[x]):
                if v + d in idx[y]:
                    hits.append((v, x, idx[x][v], y, idx[y][v + d]))
        return hits

    real = count(0)
    null = [len(count(d)) for d in list(range(-30, 0)) + list(range(1, 31))]
    m = sum(null) / len(null)
    sd = (sum((n - m) ** 2 for n in null) / len(null)) ** 0.5
    lines = [f"кипу: {len(Q)}; равенств величин ≥ {MINV} между разными кипу: {len(real)}; "
             f"фон (сдвиг ±1…±30): {m:.1f} ± {sd:.1f}, максимум {max(null)}; z = {(len(real) - m) / sd:.1f}"]
    for lo in (2000, 5000, 10000):
        r = sum(1 for h in real if h[0] >= lo)
        n = [sum(1 for h in count(d) if h[0] >= lo) for d in (-20, -10, -5, -3, -1, 1, 3, 5, 10, 20)]
        lines.append(f"  ≥ {lo}: реально {r}, фон {sum(n) / len(n):.1f} (макс {max(n)})")
    lines.append("")
    for v, x, lx, y, ly in sorted(real, key=lambda h: -h[0]):
        lines.append(f"{v:7}  {x} {lx[:3]}  =  {y} {ly[:3]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:70]))


if __name__ == "__main__":
    main()
