"""Итоги разделов одного кипу на другом, по всему корпусу 2026 (обобщение KH0697 ~ AS109).

Цель — группа кипу X с ≥ 4 позициями ≥ 100. Источник — сумма 2–15 подряд идущих групп кипу Y ≠ X. Совпадение — равенство
≥ 4 позиций со значением ≥ 100 (одна позиция может расходиться, как на один узел). Пары с тем же музейным номером
(повторные записи одного предмета) пропускаются. Фон: те же поиски с целями, сдвинутыми на ±1…±10.
Вход: extracted/plus2026_cords.csv (run_2026.sh), extracted/kfg2026_meta.json, site/data.json. Вывод: extracted/section_totals.txt.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/section_totals.txt"


def main():
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(ROOT / "extracted/plus2026_cords.csv")):
        if r["parent_id"] == "":
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"])))
    gr = {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}
    norm = lambda s: re.sub(r"[^0-9A-Z]", "", str(s or "").upper())
    mus = {}
    for k in json.load(open(ROOT / "site/data.json"))["khipus"]:
        mus[k["id"]] = norm(k["num"])
    for k, v in json.load(open(ROOT / "extracted/kfg2026_meta.json")).items():
        mus.setdefault(k, norm(v.get("museum_num")))
    same = lambda a, b: bool(mus.get(a)) and mus.get(a) == mus.get(b) or (mus.get(a, "")[:8] and mus.get(a, "")[:8] == mus.get(b, "")[:8] and len(mus.get(a, "")) >= 8)
    index = defaultdict(list)          # (position, value) -> [(khipu, i, j)]
    for k, gs in gr.items():
        for i in range(len(gs)):
            acc = []
            for j in range(i, min(len(gs), i + 15)):
                g = gs[j]
                acc = [a + b for a, b in zip(acc + [0] * (len(g) - len(acc)), g + [0] * (len(acc) - len(g)))] if acc else list(g)
                if j > i:
                    for p, v in enumerate(acc):
                        if v >= 100:
                            index[(p, v)].append((k, i, j))
    targets = [(k, gi, g) for k, gs in gr.items() for gi, g in enumerate(gs) if sum(1 for v in g if v >= 100) >= 4]

    def run(d):
        found = []
        for k, gi, g in targets:
            cand = Counter()
            for p, v in enumerate(g):
                if v >= 100:
                    for s in index.get((p, v + d), []):
                        if s[0] != k:
                            cand[s] += 1
            best = {}
            for s, n in cand.items():
                if n >= 4 and not same(k, s[0]):
                    key = (k, gi, s[0])
                    if n > best.get(key, (0,))[0]:
                        best[key] = (n, s)
            found += [(n, k, gi, s) for (k_, gi_, y), (n, s) in best.items()]
        return found
    real = run(0)
    null = [len(run(d)) for d in list(range(-10, 0)) + list(range(1, 11))]
    pairs = Counter((k, s[0]) for n, k, gi, s in real)
    lines = [f"целей (группы с ≥ 4 значениями ≥ 100): {len(targets)}; совпадений (цель, кипу-источник): {len(real)}; "
             f"фон: в среднем {sum(null) / len(null):.1f}, максимум {max(null)}",
             "пары кипу (цель ← источник): число групп-целей"]
    for (a, b), n in pairs.most_common(40):
        ex = next((x for x in real if x[1] == a and x[3][0] == b), None)
        lines.append(f"  {a} ← {b}: {n};  напр. г{ex[2] + 1} {gr[a][ex[2]]} = {b} г{ex[3][1] + 1}–г{ex[3][2] + 1} ({ex[0]} поз.)")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
