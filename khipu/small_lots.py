"""Одинаковые группы с малыми значениями в разных кипу (копии среди «мелких» кипу).

Группа ≥ 6 подвесных, ≥ 4 ненулевых значения, все значения < 100 (крупные покрыты lotmatch.py). Ищем группы с тем же
вектором значений (прямо или обратно) в кипу с другим музейным номером. Редкость вектора: −Σ log10 частоты значения
в корпусе (по всем подвесным). Фон: та же процедура с векторами, у которых значения перемешаны внутри группы
(сохраняет набор значений группы, разрушает порядок). Вывод: extracted/small_lots.txt.
"""
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/small_lots.txt"


def main():
    G = defaultdict(lambda: defaultdict(list))
    freq = Counter()
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            v = int(r["value"])
            G[r["inv_num"]][r["group"]].append((int(r["order"]), v))
            freq[v] += 1
    tot = sum(freq.values())
    D = json.load(open(ROOT / "site/data.json"))
    norm = lambda s: "".join(ch for ch in str(s or "").upper() if ch.isalnum())
    mus = {k["id"]: norm(k["num"]) for k in D["khipus"]}
    dup = {(d["a"], d["b"]) for d in D["duplicates"]} | {(d["b"], d["a"]) for d in D["duplicates"]}
    groups = []
    for k, d in G.items():
        for gid, x in d.items():
            g = tuple(v for _, v in sorted(x))
            if len(g) >= 6 and sum(1 for v in g if v) >= 4 and max(g) < 100:
                groups.append((k, gid, g))
    rar = lambda g: -sum(math.log10(freq[v] / tot) for v in g)

    def matches(gs):
        idx = defaultdict(list)
        for k, gid, g in gs:
            idx[g].append((k, gid))
        out = []
        for k, gid, g in gs:
            for key in (g, g[::-1]):
                for k2, gid2 in idx.get(key, []):
                    if k2 > k and mus.get(k) != mus.get(k2) and (k, k2) not in dup and (mus.get(k) or mus.get(k2)):
                        out.append((rar(g), k, gid, k2, gid2, g, key is not g))
        return out
    real = matches(groups)
    rnd = random.Random(1)
    null_counts = []
    for _ in range(20):
        sh = [(k, gid, tuple(rnd.sample(g, len(g)))) for k, gid, g in groups]
        null_counts.append(sorted((m[0] for m in matches(sh)), reverse=True))
    real.sort(reverse=True)
    lines = [f"групп с малыми значениями: {len(groups)}; совпадений между кипу: {len(real)}; "
             f"фон (перемешано внутри групп, 20 раз): в среднем {sum(len(n) for n in null_counts) / 20:.1f}"]
    for thr in (6, 8, 10, 12):
        lines.append(f"  редкость ≥ {thr}: реальных {sum(1 for m in real if m[0] >= thr)}, фон {sum(sum(1 for x in n if x >= thr) for n in null_counts) / 20:.2f}")
    seen = set()
    for r_, k, gid, k2, gid2, g, rev in real:
        if (k, k2) in seen:
            continue
        seen.add((k, k2))
        lines.append(f"{r_:5.1f}  {k} ~ {k2}{' (обратно)' if rev else ''}  {list(g)}")
        if len(seen) >= 30:
            break
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
