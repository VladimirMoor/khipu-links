"""Зеркальные копии: группа одного кипу = группа другого в обратном порядке шнуров.

1) Группы ≥ 4 шнуров (≥ 2 некруглых значений ≥ 10), совпадающие как мультимножества у кипу с
   разными музейными номерами: тот же порядок / обратный / иная перестановка.
2) Выравнивание целых кипу (difflib) в прямом и обратном порядке для найденных пар.
3) MM015 (Базель): каждая группа против всех окон корпуса той же длины в обоих направлениях.
Вывод: extracted/mirror.txt.
"""
import csv
import difflib
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/mirror.txt"


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        G[k] = [tuple(int(r["value"]) for r in g) for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    ms = defaultdict(list)
    for k, gs in G.items():
        for i, v in enumerate(gs):
            if len(v) >= 4 and sum(1 for x in v if x >= 10 and x % 10) >= 2:
                ms[tuple(sorted(v))].append((k, i + 1, v))
    kinds = defaultdict(list)
    for L in ms.values():
        for (k1, i1, a), (k2, i2, b) in itertools.combinations(L, 2):
            if mus(k1) == mus(k2):
                continue
            kind = "тот же" if a == b else "обратный" if a == b[::-1] else "перестановка"
            kinds[kind].append((k1, i1, k2, i2, a, b))
    lines = ["группы-мультимножества у разных музейных номеров: " +
             ", ".join(f"{k} {len(v)}" for k, v in kinds.items())]
    pairs = sorted({(x[0], x[2]) for k in ("обратный", "перестановка") for x in kinds[k]})
    for a, b in pairs:
        A = [v for g in G[a] for v in g]
        B = [v for g in G[b] for v in g]
        f = sum(m.size for m in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks())
        r = sum(m.size for m in difflib.SequenceMatcher(None, A[::-1], B, autojunk=False).get_matching_blocks())
        lines.append(f"  {a} ({meta[a]['MUSEUM_NUM']}, {len(A)} шн.) ~ {b} ({meta[b]['MUSEUM_NUM']}, {len(B)} шн.): "
                     f"совпало подряд — прямо {f}, обратно {r}")
    flat = {k: [v for g in gs for v in g] for k, gs in G.items()}
    lines.append("MM015 (Базель) — лучшие окна корпуса для каждой группы:")
    for gi, g in enumerate(G["MM015"]):
        if len(g) < 4:
            continue
        best = []
        for k, v in flat.items():
            if mus(k) == mus("MM015"):
                continue
            for i in range(len(v) - len(g) + 1):
                w = v[i:i + len(g)]
                for d, ww in (("прямо", w), ("обратно", w[::-1])):
                    s = sum(x == y for x, y in zip(g, ww))
                    if s >= len(g) - 2:
                        best.append((s, k, i + 1, d))
        best.sort(reverse=True)
        lines.append(f"  г{gi + 1} {list(g)}: {best[:4]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
