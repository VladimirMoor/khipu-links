"""Графа пустая в одной копии и заполнена в другой: Инкауаси UR255 ~ UR267A.

Группы сопоставляются по первому шнуру (общее). В UR267A группа = [общее, 15, остаток], в
UR255 — [общее, остаток, 15]. Для каждой пары групп, где остаток в UR267A > 0, смотрим шнур
остатка в UR255: заполнен тем же числом / пуст и цел (конец не B) / пуст и оборван.
Вывод: extracted/fillslot.txt.
"""
import csv
import itertools
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/fillslot.txt"


def groups(rows, k):
    rs = sorted(rows[k], key=lambda r: int(r["order"]))
    return [list(g) for _, g in itertools.groupby(rs, key=lambda r: r["group"])]


def main():
    rows = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["inv_num"] in ("UR255", "UR267A") and r["parent_id"] == "":
            rows[r["inv_num"]].append(r)
    A, B = groups(rows, "UR255"), groups(rows, "UR267A")
    first = {}
    for j, g in enumerate(B):
        first.setdefault(int(g[0]["value"]), j)
    lines = ["UR255 группа | остаток в UR255 (значение, конец, длина) | UR267A группа, остаток", ""]
    stat = Counter()
    order = []
    for i, g in enumerate(A, 1):
        v0 = int(g[0]["value"])
        if len(g) < 3 or v0 == 0 or v0 not in first:
            continue
        h = B[first[v0]]
        net_b = [int(r["value"]) for r in h if r["value"] not in ("15", "16")][1:]
        net_b = next((x for x in net_b if x), 0)
        if net_b == 0:
            continue
        slot = g[1]
        v = int(slot["value"])
        kind = ("заполнен" + ("" if v == net_b else f" иначе ({v})")) if v else \
               ("пуст, цел" if slot["termination"] != "B" else "пуст, оборван")
        stat[kind.split(" (")[0]] += 1
        order.append((i, kind[0]))
        lines.append(f"  г{i:<3} {v:4} {slot['termination']:1} {slot['length']:>5} см | UR267A г{first[v0] + 1}: {net_b:4}   {kind}")
    lines.append("")
    lines.append(f"итого: {dict(stat)}")
    lines.append("порядок по группам UR255 (з — заполнен, п — пуст): " + "".join(k for _, k in order))
    # UR256 (привязан к UR255, постоянное 10): группы вида [общее, графа, 10, …]
    rows2 = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["inv_num"] == "UR256" and r["parent_id"] == "":
            rows2["UR256"].append(r)
    seq, ok, tot = [], 0, 0
    for g in groups(rows2, "UR256"):
        v = [int(r["value"]) for r in g]
        if len(v) >= 3 and v[0] and 10 in v and v.index(10) == 2:
            seq.append("п" if v[1] == 0 else "з")
            if v[1]:
                tot += 1
                ok += v[0] == v[1] + 10 + sum(v[3:])
    lines.append(f"UR256, группы [общее, графа, 10, …]: {''.join(seq)}; общее = остаток + 10 (+ прочие) в {ok} из {tot}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
