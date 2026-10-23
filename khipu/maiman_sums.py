"""Кипу бывшего собрания Маймана (KFG 2026: KH0665 = BA001, KH0696 = AK001, KH0697 = AK002, KH0698 = AK003) против сумм
подряд идущих групп (1–15) всех кипу корпуса plus2026; совпадение — равенство ≥ 4 позиций со значением ≥ 100.
Фон: тот же поиск с целевыми группами, сдвинутыми на ±1…±20 (все позиции на d). Вывод: extracted/maiman_sums.txt.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/maiman_sums.txt"
TARGETS = ["KH0665", "KH0696", "KH0697", "KH0698"]


def main():
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(ROOT / "extracted/plus2026_cords.csv")):
        if r["parent_id"] == "":
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"])))
    gr = {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}
    sums = []   # (khipu, i, j, vector)
    for k, gs in gr.items():
        if k in TARGETS:
            continue
        for i in range(len(gs)):
            acc = []
            for j in range(i, min(len(gs), i + 15)):
                g = gs[j]
                acc = [a + b for a, b in zip(acc + [0] * (len(g) - len(acc)), g + [0] * (len(acc) - len(g)))] if acc else list(g)
                sums.append((k, i, j, tuple(acc)))
    index = defaultdict(list)
    for s in sums:
        for p, v in enumerate(s[3]):
            if v >= 100:
                index[(p, v)].append(s)

    def hits(tg, d=0):
        out = []
        t = [v + d if v else 0 for v in tg]
        cand = defaultdict(int)
        for p, v in enumerate(t):
            if v >= 100:
                for s in index.get((p, v), []):
                    cand[(s[0], s[1], s[2])] += 1
        for key, n in cand.items():
            if n >= 4:
                out.append((n, key))
        return out
    lines = []
    for k in TARGETS:
        real = []
        for gi, tg in enumerate(gr.get(k, [])):
            for n, key in hits(tg):
                real.append((n, gi + 1, key))
        null = []
        for d in [x for x in range(-20, 21) if x]:
            null.append(sum(len(hits(tg, d)) for tg in gr.get(k, [])))
        lines.append(f"{k}: групп {len(gr.get(k, []))}; совпадений (≥ 4 позиций) {len(real)}; фон в среднем {sum(null) / len(null):.2f}, максимум {max(null)}")
        for n, gi, (kk, i, j) in sorted(real, reverse=True)[:12]:
            lines.append(f"  г{gi} {gr[k][gi - 1]} = {kk} сумма г{i + 1}–г{j + 1} {list(next(s[3] for s in sums if s[0] == kk and s[1] == i and s[2] == j))}  ({n} позиций)")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
