"""Инкавази UR269 («Khipu del Maní», 20N): постоянный вычет по месту записи в блоке.

Блоки — группы между одиночными нулевыми шнурами; одиночная группа [d] сразу после записи
считается её отделённым шнуром вычета. Вычет записи — третий шнур (если 9…60), иначе
брутто − нетто (если 9…60). Статистика — число записей, чей вычет равен моде своего места
(моды пересчитываются в каждой перестановке); фон — перестановка записей внутри блоков.
Вывод: extracted/slotded.txt.
"""
import csv
import itertools
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/slotded.txt"


def blocks(K):
    rs = sorted((r for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv"))
                 if r["inv_num"] == K and r["parent_id"] == ""), key=lambda r: int(r["order"]))
    gs = [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    out, cur = [], []
    for g in gs:
        if g == [0]:
            if cur:
                out.append(cur)
            cur = []
        elif len(g) == 1 and 9 <= g[0] <= 60 and cur:
            cur[-1] = cur[-1][:2] + [g[0]]
        else:
            cur.append(g)
    if cur:
        out.append(cur)
    return out


def ded(g):
    if len(g) > 2 and 9 <= g[2] <= 60:
        return g[2]
    if len(g) > 1 and g[0] and g[1] and 9 <= g[0] - g[1] <= 60:
        return g[0] - g[1]
    return None


def stat(B):
    by = defaultdict(list)
    for b in B:
        for i, d in enumerate(b):
            if d is not None:
                by[i].append(d)
    return sum(Counter(v).most_common(1)[0][1] for v in by.values()), by


def main():
    B = [[ded(g) for g in b] for b in blocks("UR269") if len(b) >= 4]
    s, by = stat(B)
    rnd = random.Random(1)
    null = []
    for _ in range(10000):
        null.append(stat([rnd.sample(b, len(b)) for b in B])[0])
    p = (1 + sum(x >= s for x in null)) / (1 + len(null))
    lines = [f"UR269: блоков ≥ 4 записей {len(B)}; вычеты по месту записи:"]
    for i in sorted(by):
        lines.append(f"  место {i + 1}: {by[i]}")
    lines.append(f"записей с вычетом = моде места: {s} из {sum(len(v) for v in by.values())}; "
                 f"перестановка внутри блоков: среднее {sum(null) / len(null):.1f}, p = {p:.4f}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
