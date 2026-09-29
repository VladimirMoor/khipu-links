"""Разбор пары KH0049 (Лима, MNAAHP 3550; записи AS038, HP036, KH0049) ↔ UR122
(Гётеборг, 1938.45.0228).

Выравнивание: верхние группы по 18 подвесных — KH0049 группы 4–7 ↔ UR122 группы 1–4
(для AS038/HP036 — те же позиции подвесных, 36..107). Для каждой позиции:
значение подвесного (только его узлы), значение с дочерними, число дочерних, цвет,
разряды (тысячи/сотни/десятки/единицы) по узлам.

Классы расхождений между Лимой и Гётеборгом (по значению подвесного без дочерних):
  equal       — равны;
  one_digit   — отличаются ровно в одном разряде (пропущенный/лишний узел, иное число
                оборотов длинного узла) — типичная ошибка записи;
  multi_digit — отличаются в нескольких разрядах;
  zero_side   — у одной стороны 0 (пустой шнур/утрата).
Базовый уровень «шума записи»: те же классы между AS038, HP036 и KH0049 (три записи
одного предмета).
"""
import sqlite3
from collections import Counter, defaultdict
from itertools import groupby
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/kfg/kfg.db"


def load(inv):
    con = sqlite3.connect(DB)
    kid = con.execute("select khipu_id from khipu_main where investigator_num=?", (inv,)).fetchone()[0]
    pc = con.execute("select pcord_id from primary_cord where khipu_id=?", (kid,)).fetchone()[0]
    cords = {r[0]: dict(zip(("id", "parent", "ordinal", "cluster", "level", "length", "term"), r))
             for r in con.execute("select cord_id, pendant_from, cord_ordinal, cluster_id, cord_level, "
                                  "cord_length, termination from cord where khipu_id=?", (kid,))}
    color = {}
    for cid, col in con.execute("select cord_id, full_color from ascher_cord_color where khipu_id=? "
                                "and pcord_flag=0 order by color_id", (kid,)):
        color.setdefault(cid, col)
    knots = defaultdict(list)
    for cid, t, v, turns, o in con.execute(
            "select k.cord_id, k.type_code, k.knot_value_type, k.num_turns, k.knot_ordinal from knot k "
            "join cord c on c.cord_id=k.cord_id where c.khipu_id=?", (kid,)):
        knots[cid].append((o or 0, t, int(v or 0), turns))
    clus = {r[0]: r[1] for r in con.execute("select cluster_id, ordinal from cord_cluster where khipu_id=?", (kid,))}
    kids = defaultdict(list)
    for c in cords.values():
        kids[c["parent"]].append(c["id"])
    for k in kids:
        kids[k].sort(key=lambda i: (cords[i]["ordinal"] or 0, i))

    def own(i):
        return sum(v for _, _, v, _ in knots.get(i, []))

    def tree(i):
        return own(i) + sum(tree(c) for c in kids.get(i, []))

    top = []
    for i in kids.get(pc, []):
        c = cords[i]
        top.append({
            "id": i, "group": clus.get(c["cluster"]), "own": own(i), "tree": tree(i),
            "subs": [own(s) for s in kids.get(i, [])], "nsub": len(kids.get(i, [])),
            "color": color.get(i, ""), "length": c["length"], "term": c["term"],
            "knots": sorted(knots.get(i, [])),
        })
    return top


def digits(v):
    return {10 ** p: (v // 10 ** p) % 10 for p in range(5)}


def classify(a, b):
    if a == b:
        return "equal"
    if a == 0 or b == 0:
        return "zero_side"
    da, db = digits(a), digits(b)
    diff = [p for p in da if da[p] != db[p]]
    return "one_digit" if len(diff) == 1 else "multi_digit"


def groups18(top):
    gs = [list(g) for _, g in groupby(top, key=lambda c: c["group"])]
    return [g for g in gs if len(g) == 18]


def main():
    L = {inv: load(inv) for inv in ("KH0049", "HP036", "AS038")}
    G = load("UR122")
    print("Подвесных:", {k: len(v) for k, v in L.items()}, "UR122:", len(G))
    print("Группы по 18:", {k: len(groups18(v)) for k, v in L.items()}, "UR122:", len(groups18(G)))
    lg = groups18(L["KH0049"])[-4:]
    gg = groups18(G)
    print("\n# Лима (KH0049) ↔ Гётеборг (UR122): значение подвесного без дочерних / с дочерними")
    stats = Counter()
    rows = []
    for gi, (a, b) in enumerate(zip(lg, gg)):
        for pos, (x, y) in enumerate(zip(a, b)):
            cls = classify(x["own"], y["own"])
            stats[cls] += 1
            dt = y["tree"] - x["tree"]
            rows.append((gi + 1, pos + 1, x, y, cls))
            print(f"г{gi+1} п{pos+1:2}  Л {x['own']:5} ({x['tree']:5}, {x['nsub']}s, {x['color']:>5})   "
                  f"Г {y['own']:5} ({y['tree']:5}, {y['nsub']}s, {y['color']:>5})   Δ={y['own']-x['own']:+5}  Δдер={dt:+6}  {cls}")
    print("\nЛима↔Гётеборг, классы:", dict(stats))
    # шум записи: AS038 / HP036 / KH0049 на тех же позициях
    print("\n# Базовый шум записи одного предмета (Лима, три записи), те же 72 позиции:")
    for x_inv, y_inv in (("AS038", "HP036"), ("AS038", "KH0049"), ("HP036", "KH0049")):
        xs = [c for g in groups18(L[x_inv])[-4:] for c in g]
        ys = [c for g in groups18(L[y_inv])[-4:] for c in g]
        st = Counter(classify(a["own"], b["own"]) for a, b in zip(xs, ys))
        print(f"  {x_inv} ↔ {y_inv}: {dict(st)}")
    # суммы групп
    print("\n# Суммы групп (с дочерними): Лима / Гётеборг")
    for gi, (a, b) in enumerate(zip(lg, gg)):
        print(f"  группа {gi+1}: {sum(c['tree'] for c in a):6} / {sum(c['tree'] for c in b):6}")
    # цвета: соответствие по позициям
    print("\n# Цвета по позициям (все 4 группы): Лима → Гётеборг")
    cm = Counter((x["color"], y["color"]) for _, _, x, y, _ in rows)
    for (cx, cy), n in cm.most_common(12):
        print(f"  {cx:>6} → {cy:<6} {n}")
    # дочерние: число совпадает?
    same_nsub = sum(1 for _, _, x, y, _ in rows if x["nsub"] == y["nsub"])
    print(f"\nЧисло дочерних совпадает в {same_nsub} из {len(rows)} позиций")
    # выпишем расхождения в одном разряде: какой разряд и на сколько
    od = Counter()
    for _, _, x, y, cls in rows:
        if cls == "one_digit":
            da, db = digits(x["own"]), digits(y["own"])
            p = next(p for p in da if da[p] != db[p])
            od[(p, db[p] - da[p])] += 1
    print("Расхождения в одном разряде (разряд, Гётеборг−Лима в цифрах):", dict(od))


if __name__ == "__main__":
    main()
