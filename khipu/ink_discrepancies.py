"""Расхождения между копиями Инкавази и какая версия держит арифметику записи (брутто = вычет + части).

Пары копий: UR255 ~ UR267A, UR256 ~ UR267B, UR266 ~ UR275, UR273A ~ UR274A, UR273B ~ UR274B, UR269 ~ UR275.
Запись = группа. Записи двух кипу сопоставляем по общему брутто (наибольшее значение группы, ≥ 100) или, если брутто
расходится, по общему нетто и вычету. Запись «сходится», если наибольшее значение = сумме остальных (пустые шнуры
не мешают). Для каждой сопоставленной пары с разными значениями: обе версии и какая сходится.
Вывод: extracted/ink_discrepancies.txt.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/ink_discrepancies.txt"
PAIRS = [("UR255", "UR267A"), ("UR256", "UR267B"), ("UR266", "UR275"), ("UR273A", "UR274A"), ("UR273B", "UR274B"), ("UR269", "UR275")]


def groups():
    G = defaultdict(lambda: defaultdict(list))
    keys = {k for p in PAIRS for k in p}
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["inv_num"] in keys and r["parent_id"] == "":
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"])))
    return {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}


def ok(g):
    nz = [v for v in g if v]
    return len(nz) >= 3 and max(nz) == sum(nz) - max(nz)


def main():
    gr = groups()
    lines, stats = [], defaultdict(lambda: defaultdict(int))
    for a, b in PAIRS:
        used = set()
        rows = []
        for i, ga in enumerate(gr[a]):
            if max(ga) < 100:
                continue
            cand = [j for j, gb in enumerate(gr[b]) if j not in used and max(gb) == max(ga)]
            if not cand:   # gross differs: match by the net value and one more shared value ≥ 10
                sa = {v for v in ga if v >= 10}
                cand = [j for j, gb in enumerate(gr[b]) if j not in used and max(gb) >= 100 and len(sa & {v for v in gb if v >= 10}) >= 2]
            if len(cand) != 1:
                continue
            j = cand[0]
            used.add(j)
            gb = gr[b][j]
            same = sorted(v for v in ga if v) == sorted(v for v in gb if v)
            stats[(a, b)]["matched"] += 1
            if same:
                stats[(a, b)]["identical"] += 1
                continue
            oa, ob = ok(ga), ok(gb)
            kind = "both" if oa and ob else a if oa else b if ob else "neither"
            stats[(a, b)][kind] += 1
            rows.append(f"  {a} г{i + 1} {ga}  {'✓' if oa else '✗'}   |   {b} г{j + 1} {gb}  {'✓' if ob else '✗'}")
        s = stats[(a, b)]
        lines.append(f"{a} ~ {b}: сопоставлено {s['matched']}, совпадают полностью {s['identical']}; различаются — "
                     f"сходится только {a}: {s[a]}, только {b}: {s[b]}, обе: {s['both']}, ни одна: {s['neither']}")
        lines += rows
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
