"""Постоянные, зависящие от места записи в блоке (обобщение UR269), по всему корпусу.

Запись = группа подвесных; блоки — серии записей между «разделителями» (группа из одних нулей или один шнур).
Для каждой позиции шнура j в записи: сколько записей несут на позиции j «моду своего места» (значение ≥ 2,
самое частое для этого места в блоке, встречающееся ≥ 2 раз). Требуем ≥ 2 разных мод у разных мест, иначе это
одна общая константа, а не зависимость от места. Фон — перестановка записей внутри каждого блока (1000 раз).
Вывод: extracted/place_constants.txt.
"""
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/place_constants.txt"


def blocks_of(groups):
    out, cur = [], []
    for g in groups:
        if all(v == 0 for v in g) or len(g) == 1:
            if len(cur) >= 3:
                out.append(cur)
            cur = []
        else:
            cur.append(g)
    if len(cur) >= 3:
        out.append(cur)
    return out


def stat(B, j):
    by = defaultdict(list)
    for b in B:
        for p, g in enumerate(b):
            if j < len(g):
                by[p].append(g[j])
    modes = {}
    for p, vs in by.items():
        c = Counter(v for v in vs if v >= 2)
        if c:
            v, n = c.most_common(1)[0]
            if n >= 2:
                modes[p] = v
    if len(set(modes.values())) < 2:
        return 0, modes
    hits = sum(1 for b in B for p, g in enumerate(b) if j < len(g) and p in modes and g[j] == modes[p])
    return hits, modes


def main():
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"])))
    rnd = random.Random(1)
    res = []
    for k, d in G.items():
        groups = [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))]
        B = blocks_of(groups)
        if sum(len(b) for b in B) < 12 or len(B) < 3:
            continue
        for j in range(max(len(g) for b in B for g in b)):
            real, modes = stat(B, j)
            if real < 8:
                continue
            null = []
            for _ in range(300):
                Bs = [rnd.sample(b, len(b)) for b in B]
                null.append(stat(Bs, j)[0])
            p = (1 + sum(x >= real for x in null)) / 301
            res.append((p, -real, k, j, real, sum(null) / len(null), len(B), sum(len(b) for b in B), modes))
    res.sort()
    lines = [f"кипу × позиций с ≥ 8 записями на моде своего места: {len(res)}"]
    for p, _, k, j, real, m, nb, nr, modes in res[:30]:
        lines.append(f"p = {p:.4f}  {k} позиция {j + 1}: {real} записей на моде места (фон {m:.1f}); блоков {nb}, записей {nr}; "
                     f"моды по местам {dict(sorted(modes.items()))}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
