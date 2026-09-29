"""Гипотеза «знака»: есть ли у кипу отрицательные шнуры, отмеченные осязаемым или видимым
признаком (направление узлов, сторона крепления, цвет)?

Для каждой кипу: подвесные в порядке (значение = шнур + дочерние). «Итог» — любой подвесной
со значением ≥ MIN_T; «отрезок» — 2..MAXRUN подряд идущих подвесных, не содержащий итога.
Знаковая сумма отрезка: шнуры с признаком X берутся со знаком минус. Считаем
  N = число пар (итог, отрезок), где знаковая сумма = итог, а обычная (все +) — нет,
при реальной раскладке признака и при 200 случайных циклических сдвигах разметки вдоль кипу
(блоки признака и доля «минусов» сохраняются; простое перемешивание дробит блоки и завышает фон). Суммируем по корпусу; p = доля перестановок с N ≥ реального.
"""
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/kfg/kfg.db"
MIN_T, MAXRUN, NPERM = 20, 15, 200


def load():
    con = sqlite3.connect(DB)
    pcs = dict(con.execute("select khipu_id, pcord_id from primary_cord"))
    inv = dict(con.execute("select khipu_id, investigator_num from khipu_main"))
    cords = defaultdict(list)
    parent = {}
    for cid, kid, par, o, att in con.execute("select cord_id, khipu_id, pendant_from, cord_ordinal, attachment_type from cord"):
        cords[kid].append((cid, par, o or 0, att))
        parent[cid] = par
    val = defaultdict(int)
    dirs = defaultdict(Counter)
    for cid, v, d in con.execute("select cord_id, knot_value_type, direction from knot"):
        val[cid] += int(v or 0)
        if d in ("S", "Z"):
            dirs[cid][d] += 1
    color = {}
    for cid, col in con.execute("select cord_id, full_color from ascher_cord_color where pcord_flag=0 order by color_id"):
        color.setdefault(cid, col)
    K = {}
    for kid, cs in cords.items():
        if kid not in pcs:
            continue
        kids = defaultdict(list)
        for cid, par, o, att in cs:
            kids[par].append((o, cid, att))

        def tree(c):
            return val.get(c, 0) + sum(tree(k) for _, k, _ in kids.get(c, []))
        top = sorted(kids.get(pcs[kid], []))
        rows = []
        for o, cid, att in top:
            dmaj = dirs[cid].most_common(1)[0][0] if dirs[cid] else None
            rows.append({"v": tree(cid), "dir": dmaj, "att": att if att in ("R", "V") else None,
                         "col": color.get(cid)})
        if len(rows) >= 6:
            K[inv.get(kid, kid)] = rows
    return K


def count(vals, neg):
    """N пар (итог, отрезок), где знаковая сумма = итог, а обычная — нет."""
    n = len(vals)
    totals = defaultdict(list)
    for i, v in enumerate(vals):
        if v >= MIN_T:
            totals[v].append(i)
    N = 0
    for i in range(n):
        plain = signed = 0
        has_neg = False
        for j in range(i, min(n, i + MAXRUN)):
            plain += vals[j]
            signed += -vals[j] if neg[j] else vals[j]
            has_neg |= neg[j] and vals[j] > 0
            if j == i or not has_neg or signed == plain:
                continue
            for t in totals.get(signed, ()):
                if not (i <= t <= j):
                    N += 1
    return N


def test(K, attr, pick):
    """attr: ключ признака; pick(rows) → значение признака, считаемое «минусом» (или None)."""
    data = []
    for inv, rows in K.items():
        labels = [r[attr] for r in rows]
        known = [l for l in labels if l is not None]
        if len(set(known)) < 2:
            continue
        m = pick(rows)
        if m is None:
            continue
        neg = [l == m for l in labels]
        if not (0 < sum(neg) < len(neg)):
            continue
        data.append(([r["v"] for r in rows], neg))
    real = sum(count(v, n) for v, n in data)
    rng = random.Random(5)
    perms = []
    for _ in range(NPERM):
        tot = 0
        for v, n in data:
            k = rng.randrange(1, len(n))  # циклический сдвиг: блоки признака сохраняются
            q = n[k:] + n[:k]
            tot += count(v, q)
        perms.append(tot)
    p = (sum(1 for x in perms if x >= real) + 1) / (NPERM + 1)
    return len(data), real, sum(perms) / len(perms), max(perms), p


def main():
    K = load()
    print(f"кипу: {len(K)}")
    tests = {
        "узлы Z = минус": ("dir", lambda rows: "Z"),
        "узлы S = минус": ("dir", lambda rows: "S"),
        "крепление V = минус": ("att", lambda rows: "V"),
        "крепление R = минус": ("att", lambda rows: "R"),
        "редкий цвет кипу = минус": ("col", lambda rows: (lambda c: c[-1][0] if len(c) >= 2 else None)(
            Counter(r["col"] for r in rows if r["col"]).most_common(3))),
        "2-й по частоте цвет = минус": ("col", lambda rows: (lambda c: c[1][0] if len(c) >= 2 else None)(
            Counter(r["col"] for r in rows if r["col"]).most_common(2))),
    }
    for name, (attr, pick) in tests.items():
        n, real, mean, mx, p = test(K, attr, pick)
        print(f"{name:28} кипу={n:3}  знаковых сумм: реальных {real:5}, в перестановках в среднем {mean:7.1f} "
              f"(макс {mx}) → p={p:.3f}")


if __name__ == "__main__":
    main()
