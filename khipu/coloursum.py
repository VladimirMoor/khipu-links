"""Суммы по цвету между кипу (закрывает пробел детекторов: несмежные шнуры, выбранные по цвету).

Для кипу Y: суммы подвесных одного цвета — по всему кипу, по каждой группе, и по каждой позиции
во всех группах одной длины (столбец). Цели в кипу X: значения подвесных, суммы групп, итог.
Совпадение — точное, значение ≥ MINV, не круглое. Фон — цели X сдвинуты на d (±1…±10).
Режимы: архив (список кипу) или весь корпус. Вывод: extracted/coloursum.txt.
"""
import csv
import itertools
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/coloursum.txt"
MINV = 20


def load(keep=None):
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "" and (keep is None or r["inv_num"] in keep):
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        G[k] = [[(int(r["value"]), r["color"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    return G


def colour_sums(gs):
    out = {}
    whole = defaultdict(int)
    for gi, g in enumerate(gs):
        per = defaultdict(int)
        for v, c in g:
            per[c] += v
            whole[c] += v
        for c, s in per.items():
            if sum(1 for _, cc in g if cc == c) >= 2:
                out.setdefault(s, f"г{gi + 1}:{c}")
    for c, s in whole.items():
        out.setdefault(s, f"весь:{c}")
    byL = defaultdict(list)
    for g in gs:
        byL[len(g)].append(g)
    for L, grp in byL.items():
        if len(grp) >= 2:
            for p in range(L):
                cols = {g[p][1] for g in grp}
                if len(cols) == 1:
                    out.setdefault(sum(g[p][0] for g in grp), f"столбец{p + 1}:{cols.pop()}")
    return {s: l for s, l in out.items() if s >= MINV and s % 10}


def targets(gs):
    t = {}
    for gi, g in enumerate(gs):
        for i, (v, _) in enumerate(g):
            if v >= MINV and v % 10:
                t.setdefault(v, f"г{gi + 1}.{i + 1}")
        s = sum(v for v, _ in g)
        if s >= MINV and s % 10:
            t.setdefault(s, f"г{gi + 1}")
    s = sum(v for g in gs for v, _ in g)
    if s >= MINV and s % 10:
        t.setdefault(s, "итог")
    return t


def run(G, mus=None):
    CS = {k: colour_sums(gs) for k, gs in G.items()}
    TT = {k: targets(gs) for k, gs in G.items()}

    def count(d):
        hits = []
        for x, t in TT.items():
            for y, cs in CS.items():
                if x == y or (mus and mus.get(x) == mus.get(y)):
                    continue
                for v, lab in t.items():
                    if v + d in cs:
                        hits.append((v, x, lab, y, cs[v + d]))
        return hits
    real = count(0)
    null = [len(count(d)) for d in list(range(-10, 0)) + list(range(1, 11))]
    return real, null


def main():
    arch = {f"UR{n:03d}" for n in range(60, 84)}
    G = load(arch)
    real, null = run(G)
    lines = [f"Пуручуко (UR060–UR083): совпадений «цель X = сумма по цвету в Y» {len(real)}; "
             f"фон {sum(null) / len(null):.1f} (макс {max(null)})"]
    for h in sorted(real, reverse=True)[:20]:
        lines.append(f"   {h}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
