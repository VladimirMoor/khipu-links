"""Структурная сверка: матрица документа (строки × категории) против «табличных»
участков кипу.

Кандидаты на кипу:
  A (groups): подряд идущие верхние группы шнуров; группа = строка, подвесные
     шнуры внутри группы = категории. Длина группы k или k+1 (тогда одна позиция —
     одна и та же во всех строках — лишняя, напр. итог или маркер).
  B (subs):   подряд идущие подвесные шнуры, у каждого k-1..k дочерних; строка =
     [сам шнур] + дочерние (подвесной шнур может быть итогом строки).

Сопоставление столбцов: перебираем все k! соответствий «категория ↔ позиция».
Оба направления чтения кипу.

Мера: после стандартизации каждого столбца (log1p, z-оценка по строкам) —
корреляция Пирсона по всем парным клеткам. Стандартизация убирает общий профиль
столбцов («коки больше, чем тканей»); остаётся согласованность строк:
у кого из касиков больше/меньше. Итог: z = atanh(r)·sqrt(n−3).

Значимость: документ с целиком переставленными строками (связь категорий внутри
строки и «эффект размера строки» сохранены, соответствие порядку строк на кипу
разрушено), тот же полный поиск, максимум z по корпусу; p = доля подставных с
max z ≥ реального. Перемешивать клетки по столбцам нельзя: тогда любая кипу, где
группы бывают «все крупные»/«все мелкие», выглядит совпадением.
"""
import argparse
import math
import random
from collections import defaultdict
from itertools import permutations

from match import load_khipus  # noqa: F401  (для совместимости импорта)
from templates import TEMPLATES

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import os
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/okr_cords.csv"))
MIN_CELLS = 10


def load_tables():
    by = defaultdict(list)
    with open(CORDS) as f:
        for r in csv.DictReader(f):
            r["value"] = int(r["value"])
            by[r["khipu_id"]].append(r)
    out = {}
    for kid, rows in by.items():
        rows.sort(key=lambda r: int(r["order"]))
        top = [r for r in rows if r["parent_id"] == ""]
        kids = defaultdict(list)
        for r in rows:
            kids[r["parent_id"]].append(r)
        groups, cur, g = [], [], None
        for r in top:
            if r["group"] != g and cur:
                groups.append(cur)
                cur = []
            g = r["group"]
            cur.append(r["value"])
        if cur:
            groups.append(cur)
        subs = [[r["value"]] + [c["value"] for c in kids.get(r["cord_id"], [])] for r in top]
        out[kid] = {"okr": rows[0]["okr_num"], "inv": rows[0]["inv_num"],
                    "groups": groups, "subs": subs}
    return out


def zcols(mat):
    """log1p + z-оценка по столбцу (None остаётся None)."""
    m, k = len(mat), len(mat[0])
    out = [[None] * k for _ in range(m)]
    for j in range(k):
        col = [(i, math.log1p(mat[i][j])) for i in range(m) if mat[i][j] is not None]
        if len(col) < 3:
            continue
        mu = sum(v for _, v in col) / len(col)
        sd = math.sqrt(sum((v - mu) ** 2 for _, v in col) / len(col))
        if sd < 1e-9:
            continue
        for i, v in col:
            out[i][j] = (v - mu) / sd
    return out


def candidates(tab, m, k):
    """Все кандидатные матрицы m×k (в виде списков строк) для одной кипу."""
    for layout, rows, lens in (("A", tab["groups"], (k, k + 1)), ("B", tab["subs"], (k, k + 1))):
        ok = [len(r) in lens for r in rows]
        for start in range(0, len(rows) - m + 1):
            if not all(ok[start:start + m]):
                continue
            win = rows[start:start + m]
            for direction in (1, -1):
                w = win[::direction]
                L = min(len(r) for r in w)
                drops = [None] if all(len(r) == k for r in w) else range(k + 1)
                for d in drops:
                    mat = []
                    for r in w:
                        rr = list(r)
                        if len(rr) == k + 1:
                            rr.pop(d if d is not None else k)
                        mat.append(rr[:k])
                    yield (layout, start, direction, d), mat
                    if L < k:
                        break


def best_for(doc_z, tab, m, k, perms):
    best = (-1e9, None)
    for key, mat in candidates(tab, m, k):
        kz = zcols(mat)
        # C[j][l] — сумма произведений по строкам, где есть и doc[:,j], и kip[:,l]
        C = [[0.0] * k for _ in range(k)]
        N = [[0] * k for _ in range(k)]
        for i in range(m):
            di, ki = doc_z[i], kz[i]
            for j in range(k):
                a = di[j]
                if a is None:
                    continue
                for l in range(k):
                    b = ki[l]
                    if b is not None:
                        C[j][l] += a * b
                        N[j][l] += 1
        for p in perms:
            n = sum(N[j][p[j]] for j in range(k))
            if n < MIN_CELLS:
                continue
            r = sum(C[j][p[j]] for j in range(k)) / n
            r = max(min(r, 0.999999), -0.999999)
            z = math.atanh(r) * math.sqrt(n - 3)
            if z > best[0]:
                best = (z, (key, p, round(r, 3), n))
    return best


def search(doc, tables, perms):
    m, k = len(doc), len(doc[0])
    dz = zcols(doc)
    res = []
    for kid, tab in tables.items():
        z, info = best_for(dz, tab, m, k, perms)
        if info:
            res.append((z, kid, info))
    res.sort(reverse=True)
    return res


def shuffle_rows(doc, rng):
    rows = [list(r) for r in doc]
    rng.shuffle(rows)
    return rows


def run(name, doc, tables, null_n, rng):
    m, k = len(doc), len(doc[0])
    perms = list(permutations(range(k)))
    res = search(doc, tables, perms)
    real = res[0][0] if res else float("-inf")
    nulls = []
    for _ in range(null_n):
        r = search(shuffle_rows(doc, rng), tables, perms)
        nulls.append(r[0][0] if r else float("-inf"))
    p = (sum(1 for s in nulls if s >= real) + 1) / (null_n + 1)
    return res[:5], p, sorted(nulls)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=50)
    ap.add_argument("--only", default="")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--place", default="", help="regex по месту находки кипу")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    from provenance import subset
    tables = subset(load_tables(), CORDS, a.place)
    print(f"кипу в поиске: {len(tables)}")
    for name, f in TEMPLATES.items():
        if a.only and a.only not in name:
            continue
        cats, doc, labels = f()
        if len(cats) < 3:
            print(f"-- {name}: пропуск (меньше 3 категорий)")
            continue
        top, p, nulls = run(name, doc, tables, a.null, rng)
        q95 = nulls[int(0.95 * len(nulls)) - 1] if nulls else float("nan")
        print(f"== {name}: {len(doc)}×{len(cats)}  p={p:.3f}  (null z95={q95:.2f})")
        for z, kid, (key, perm, r, n) in top:
            t = tables[kid]
            mapping = ", ".join(f"{cats[j]}→{perm[j]+1}" for j in range(len(cats)))
            print(f"   z={z:5.2f} r={r:5.2f} n={n:2} {t['okr']}/{t['inv']} layout={key[0]} "
                  f"start={key[1]} dir={key[2]} drop={key[3]} [{mapping}]")


if __name__ == "__main__":
    main()
