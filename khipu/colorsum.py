"""Цвет как категория: складываются ли дочерние шнуры «цвет к цвету» внутри сводок?

1. Сводки: подвесной T (собственное значение ≥ 100) = сумма собственных значений целой
   группы (кластера) других подвесных G (точно).
2. Для сводок, где у T и у слагаемых есть дочерние: для каждого цвета c, встречающегося
   среди дочерних T, сравниваем D_T(c) = сумма дочерних T цвета c и
   D_G(c) = сумма дочерних цвета c у всех подвесных группы G. Совпадение — D_T(c) = D_G(c) > 0.
3. Контроль: цвета дочерних перемешаны случайно среди всех дочерних этой кипу
   (NPERM раз); p — доля перестановок с числом совпадений ≥ реального.
Дополнительно: то же для «без учёта цвета» (сумма всех дочерних T = сумма всех дочерних G).
"""
import random
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/kfg/kfg.db"
MIN_T, NPERM = 100, 300


def load():
    con = sqlite3.connect(DB)
    pcs = dict(con.execute("select khipu_id, pcord_id from primary_cord"))
    inv = dict(con.execute("select khipu_id, investigator_num from khipu_main"))
    kids, clus = defaultdict(list), {}
    for cid, par, o, cl in con.execute("select cord_id, pendant_from, cord_ordinal, cluster_id from cord"):
        kids[par].append((o or 0, cid))
        clus[cid] = cl
    val = defaultdict(int)
    for cid, v in con.execute("select cord_id, knot_value_type from knot"):
        val[cid] += int(v or 0)
    color = {}
    for cid, col in con.execute("select cord_id, full_color from ascher_cord_color where pcord_flag=0 order by color_id"):
        color.setdefault(cid, col)
    memo = {}

    def tree(c):
        if c not in memo:
            memo[c] = val.get(c, 0) + sum(tree(k) for _, k in kids.get(c, []))
        return memo[c]
    K = {}
    for kid, pc in pcs.items():
        top = [c for _, c in sorted(kids.get(pc, []))]
        rows = []
        for c in top:
            subs = [(color.get(k) or "?", tree(k)) for _, k in kids.get(c, [])]
            rows.append({"own": val.get(c, 0), "grp": clus.get(c), "subs": subs})
        if any(r["subs"] for r in rows):
            K[inv.get(kid, kid)] = rows
    return K


def relations(rows):
    """(t, [индексы группы]) — сводки по собственным значениям."""
    totals = defaultdict(list)
    for i, r in enumerate(rows):
        if r["own"] >= MIN_T:
            totals[r["own"]].append(i)
    out = []
    start = 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or rows[i]["grp"] != rows[start]["grp"]:
            if i - start >= 2:
                s = sum(rows[k]["own"] for k in range(start, i))
                for t in totals.get(s, ()):
                    if not (start <= t < i):
                        out.append((t, list(range(start, i))))
            start = i
    return out


def color_matches(rows, rels, subs_of):
    m = allm = tried = 0
    for t, g in rels:
        st = subs_of[t]
        sg = [x for k in g for x in subs_of[k]]
        if not st or not sg:
            continue
        tried += 1
        if sum(v for _, v in st) > 0 and sum(v for _, v in st) == sum(v for _, v in sg):
            allm += 1
        dt, dg = defaultdict(int), defaultdict(int)
        for c, v in st:
            dt[c] += v
        for c, v in sg:
            dg[c] += v
        m += sum(1 for c in dt if dt[c] > 0 and dt[c] == dg.get(c, 0))
    return m, allm, tried


def main():
    K = load()
    rng = random.Random(3)
    real = allr = tried = 0
    perms = [0] * NPERM
    per_khipu = []
    for inv, rows in K.items():
        rels = relations(rows)
        if not rels:
            continue
        subs_of = [r["subs"] for r in rows]
        m, a, tr = color_matches(rows, rels, subs_of)
        if not tr:
            continue
        real += m
        allr += a
        tried += tr
        per_khipu.append((m, inv, tr))
        flat_colors = [c for s in subs_of for c, _ in s]
        for p in range(NPERM):
            cols = flat_colors[:]
            rng.shuffle(cols)
            it = iter(cols)
            sh = [[(next(it), v) for _, v in s] for s in subs_of]
            perms[p] += color_matches(rows, rels, sh)[0]
    mean = sum(perms) / NPERM
    pval = (sum(1 for x in perms if x >= real) + 1) / (NPERM + 1)
    print(f"сводок с дочерними у итога и слагаемых: {tried}")
    print(f"сумма всех дочерних итога = сумме всех дочерних группы: {allr} из {tried}")
    print(f"совпадений «цвет к цвету»: реальных {real}; при перемешанных цветах в среднем {mean:.1f} "
          f"(макс {max(perms)}) → p = {pval:.4f}")
    print("кипу с наибольшим числом совпадений:", sorted(per_khipu, reverse=True)[:12])


if __name__ == "__main__":
    main()
