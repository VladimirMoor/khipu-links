"""Гипотеза: «таблицы с постоянными столбцами» — в группах одного размера каждая позиция означает одного и того же
поставщика или одну категорию — есть по всему корпусу, как в таблицах Инкавази (UR278, UR270).

Для каждого кипу и размера группы k = 4…12, если групп размера k ≥ 4 и в каждой ≥ k − 1 ненулевых шнуров: средняя
ранговая корреляция (Спирмен) всех пар строк против перемешивания значений внутри строк (1000 раз). Порог: p < 0,01.
Вывод: extracted/columns.txt (и список таблиц для сравнения профилей между кипу).
"""
import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus2026_cords.csv"
OUT = ROOT / "extracted/columns.txt"


def load():
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(CORDS)):
        if not r["parent_id"]:
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"] or 0)))
    return {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: (v[i], i))
    r = [0] * len(v)
    for k, i in enumerate(o):
        r[i] = k
    return r


def mean_spear(rows):
    R = [ranks(r) for r in rows]
    n = len(rows[0])
    s = [1 - 6 * sum((x - y) ** 2 for x, y in zip(R[i], R[j])) / (n * (n * n - 1)) for i in range(len(R)) for j in range(i + 1, len(R))]
    return statistics.mean(s)


def tables(K, rnd, nperm=1000):
    out = []
    for k, gs in K.items():
        for size in range(4, 13):
            rows = [g for g in gs if len(g) == size and sum(1 for v in g if v > 0) >= size - 1]
            if len(rows) < 4 or len({tuple(r) for r in rows}) < 3:
                continue
            real = mean_spear(rows)
            sims = [mean_spear([rnd.sample(r, size) for r in rows]) for _ in range(nperm)]
            p = (1 + sum(x >= real for x in sims)) / (1 + nperm)
            prof = [statistics.mean(r[c] / sum(r) for r in rows) for c in range(size)]
            out.append((p, k, size, len(rows), real, statistics.mean(sims), prof))
    return out


def main():
    K = load()
    D = json.load(open(ROOT / "site/data.json"))
    site = {k["id"]: k["site"] for k in D["khipus"]}
    res = tables(K, random.Random(7))
    sig = sorted(x for x in res if x[0] < 0.01)
    lines = [f"khipu/size combinations tested: {len(res)}; with stable columns (p < 0.01): {len(sig)} (expected by chance ≈ {0.01 * len(res):.1f})"]
    for p, k, size, n, real, null, prof in sig:
        lines.append(f"  {k:9} groups of {size:2} × {n:3}  Spearman {real:.2f} (shuffled {null:.2f}) p {p:.4f}  {site.get(k)}  profile "
                     + " ".join(f"{x:.2f}" for x in prof))
    by = defaultdict(int)
    for x in sig:
        by[site.get(x[1])] += 1
    lines.append("by place: " + ", ".join(f"{s} {n}" for s, n in sorted(by.items(), key=lambda z: -z[1])))
    OUT.write_text("\n".join(lines) + "\n")
    json.dump([{"khipu": k, "size": size, "rows": n, "p": p, "profile": prof} for p, k, size, n, real, null, prof in sig],
              open(ROOT / "extracted/columns.json", "w"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
