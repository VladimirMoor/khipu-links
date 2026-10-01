"""Итоги групп одного кипу, повторённые в том же порядке на другом (обобщение UR273A/B ~ UR274A/B), по всему корпусу.

Итог группы — её наибольшее значение, если оно некруглое и ≥ 100. Для пары (X, Y) — длина наибольшей общей
подпоследовательности итогов (порядок сохранён). Фон — та же длина с итогами Y, сдвинутыми на ±1…±10.
Пары с тем же музейным номером (повторные записи одного предмета) пропускаем. Вывод: extracted/ordered_totals.txt.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/ordered_totals.txt"
nr = lambda v: v >= 100 and v % 100 != 0


def lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def main():
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"])))
    T = {}
    for k, d in G.items():
        gs = [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))]
        t = [max(g) for g in gs if nr(max(g))]
        if len(t) >= 3:
            T[k] = t
    D = json.load(open(ROOT / "site/data.json"))
    meta = {k["id"]: k for k in D["khipus"]}
    norm = lambda s: "".join(ch for ch in str(s or "").upper() if ch.isalnum())
    mus = {k: norm(meta.get(k, {}).get("num")) for k in T}
    dup = {(d["a"], d["b"]) for d in D["duplicates"]} | {(d["b"], d["a"]) for d in D["duplicates"]}
    ks = sorted(T)
    sets = {k: set(T[k]) for k in ks}
    res = []
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            if len(sets[a] & sets[b]) < 3 or (mus[a] and mus[a] == mus[b]) or (a, b) in dup:
                continue
            real = lcs(T[a], T[b])
            if real < 3:
                continue
            null = [lcs(T[a], [v + d for v in T[b]]) for d in list(range(-10, 0)) + list(range(1, 11))]
            m = sum(null) / len(null)
            res.append((real - m, real, m, max(null), a, b))
    res.sort(reverse=True)
    lines = [f"кипу с ≥ 3 итогами: {len(ks)}; пар с общей упорядоченной цепочкой ≥ 3: {len(res)}",
             f"{'изб.':>5} {'LCS':>4} {'фон':>5} {'макс':>4}  пара"]
    for ex, real, m, mx, a, b in res[:40]:
        lines.append(f"{ex:5.1f} {real:4} {m:5.2f} {mx:4}  {a} ~ {b}   | {meta.get(a, {}).get('site') or meta.get(a, {}).get('prov', '')} / "
                     f"{meta.get(b, {}).get('site') or meta.get(b, {}).get('prov', '')} | {meta.get(a, {}).get('num')} / {meta.get(b, {}).get('num')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
