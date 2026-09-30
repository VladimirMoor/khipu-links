"""Выписки: группа одного кипу (≥ 5 шнуров) = окно шнуров другого кипу, прямо или обратно, ≤ 1 расхождение.

Кипу с одинаковым музейным номером (повторные записи) и известные повторные записи исключены.
Требование к группе: ≥ 3 значений ≥ 10, из них ≥ 2 некруглых. Индекс по парам соседних значений
(при ≤ 1 расхождении в первых четырёх позициях одна из пар (1,2) или (3,4) цела). Фон: к ненулевым
значениям группы прибавлено d = ±1, ±2. Вывод: extracted/excerpts.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/excerpts.txt"
SAME = [{"AS208", "UR083", "KH0227"}]


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
    flat, groups = {}, []
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        flat[k] = [int(r["value"]) for r in rs]
        for i, (_, g) in enumerate(itertools.groupby(rs, key=lambda r: r["group"])):
            v = tuple(int(r["value"]) for r in g)
            if len(v) >= 5 and sum(x >= 10 for x in v) >= 3 and sum(x >= 10 and x % 10 > 0 for x in v) >= 2:
                groups.append((k, i + 1, v))
    idx = defaultdict(list)
    for k, v in flat.items():
        for d, seq in (("прямо", v), ("обратно", v[::-1])):
            for i in range(len(seq) - 1):
                idx[(seq[i], seq[i + 1])].append((k, d, i))
    same = lambda a, b: mus(a) == mus(b) or any(a in s and b in s for s in SAME)

    def scan(shift):
        hits = {}
        for k, gi, v0 in groups:
            v = tuple(x + shift if x else x for x in v0)
            L = len(v)
            for off in (0, 2):
                for k2, d, i in idx.get((v[off], v[off + 1]), []):
                    if same(k, k2):
                        continue
                    s = i - off
                    seq = flat[k2] if d == "прямо" else flat[k2][::-1]
                    if s < 0 or s + L > len(seq):
                        continue
                    w = seq[s:s + L]
                    mis = sum(a != b for a, b in zip(v, w))
                    if mis <= 1:
                        hits[(k, gi, k2, d)] = (L - mis, L, v0, s + 1)
        return hits

    real = scan(0)
    null = [len(scan(d)) for d in (-2, -1, 1, 2)]
    lines = [f"групп: {len(groups)}; выписок (≤ 1 расхождение): {len(real)}; фон (d = ±1, ±2): {null}"]
    for (k, gi, k2, d), (m, L, v, s) in sorted(real.items(), key=lambda x: -x[1][1]):
        lines.append(f"  {k} г{gi} ({meta.get(k, {}).get('MUSEUM_NUM')}, {meta.get(k, {}).get('PROVENANCE')}) → "
                     f"{k2} {d} с шнура {s} ({meta.get(k2, {}).get('MUSEUM_NUM')}, {meta.get(k2, {}).get('PROVENANCE')}): "
                     f"{m}/{L} {list(v)}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
