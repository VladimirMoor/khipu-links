"""Разбор связи AS069 ↔ AS070 (Thompson 2024) на данных KFG.

AS069: разделы, открываемые красным шнуром (SR); внутри — строки по 7 шнуров,
каждой предшествует одиночный цветной шнур-метка; строка с меткой HB — особая.
AS070: группы, открываемые SR; внутри — по 10 шнуров с дочерними.
Проверка: числа (>= MIN) из дерева шнура s группы g в AS070 против чисел раздела s
в AS069 (ячейки, суммы столбцов, суммы строк, частичные суммы столбцов). Сравниваем
совпадения при s ↔ s (выравнивание) с s ↔ s' (сдвиг), как контроль.
"""
import csv
import itertools
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN = 10


def load():
    rows = [r for r in csv.DictReader(open(ROOT / "extracted/kfg_cords.csv"))
            if r["inv_num"] in ("AS069", "AS070")]
    kids = defaultdict(list)
    for r in rows:
        kids[r["parent_id"]].append(r)
    for k in kids:
        kids[k].sort(key=lambda r: int(r["order"]))
    return rows, kids


def sub(r, kids):
    return int(r["value"]) + sum(sub(c, kids) for c in kids.get(r["cord_id"], []))


def tree_numbers(r, kids, out):
    out.add(int(r["value"]))
    out.add(sub(r, kids))
    for c in kids.get(r["cord_id"], []):
        tree_numbers(c, kids, out)
    return out


def as069_sections(rows, kids):
    A = [r for r in sorted([r for r in rows if r["inv_num"] == "AS069"], key=lambda r: int(r["order"]))
         if r["parent_id"] == ""]
    secs, cur, last = [], None, None
    for _, it in itertools.groupby(A, key=lambda r: r["group"]):
        g = list(it)
        if len(g) == 1 and g[0]["color"] == "SR":
            cur = {"rows": [], "hb": None}
            secs.append(cur)
            last = None
        elif cur is None:
            continue
        elif len(g) == 1:
            last = g[0]["color"]
        elif len(g) == 7:
            vals = [sub(r, kids) for r in g]
            if last == "HB":
                cur["hb"] = vals
            else:
                cur["rows"].append((last, vals))
            last = None
    return [s for s in secs if s["rows"]]


def section_numbers(s):
    nums = set()
    rows = [v for _, v in s["rows"]] + ([s["hb"]] if s["hb"] else [])
    for v in rows:
        nums.update(v)
        nums.add(sum(v))
    for c in range(7):
        col = [v[c] for _, v in s["rows"]]
        nums.add(sum(col))
        acc = 0
        for x in col:  # частичные (нарастающие) суммы столбца
            acc += x
            nums.add(acc)
    return {x for x in nums if x >= MIN}


def as070_groups(rows, kids):
    B = [r for r in sorted([r for r in rows if r["inv_num"] == "AS070"], key=lambda r: int(r["order"]))
         if r["parent_id"] == ""]
    groups = []
    for _, it in itertools.groupby(B, key=lambda r: r["group"]):
        g = [r for r in it if r["color"] == "W"]
        groups.append(g)
    return groups


if __name__ == "__main__":
    rows, kids = load()
    secs = as069_sections(rows, kids)
    S = [section_numbers(s) for s in secs]
    groups = as070_groups(rows, kids)
    print(f"AS069: {len(secs)} разделов; AS070: группы {[len(g) for g in groups]}")
    for gi, g in enumerate(groups):
        if len(g) < 8:
            continue
        T = [{x for x in tree_numbers(r, kids, set()) if x >= MIN} for r in g]
        n = min(len(T), len(S))
        M = [[len(T[i] & S[j]) for j in range(len(S))] for i in range(n)]
        diag = sum(M[i][i] for i in range(n))
        off = [sum(M[i][(i + k) % len(S)] for i in range(n)) for k in range(1, len(S))]
        print(f"группа {gi+1}: совпадений на диагонали {diag}; при сдвигах: {off}")
        for i in range(n):
            common = sorted(T[i] & S[i])
            print(f"   шнур {i+1} ↔ раздел {i+1}: {common}")
