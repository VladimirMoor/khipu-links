"""Как читать дочерние шнуры: прибавлять, вычитать или не учитывать?

Для каждой кипу значение подвесного по трём правилам:
  own — только узлы самого подвесного;
  add — подвесной + все дочерние (всё поддерево);
  sub — подвесной − поддеревья его дочерних (если результат < 0 — шнур не участвует).
Считаем «суммы»: подвесной T (≥ MIN_T = 100) = сумма целой группы (кластера) подвесных,
не включающей T (так устроены суммы у Ашеров; «любые подряд идущие» дают море случайных). Учитываем только суммы, где хотя бы у одного участника есть дочерние (у
остальных правила совпадают). Фон: тот же подсчёт при перемешанном порядке подвесных в кипу
(NPERM раз); результат правила = реальные − средний фон (превышение), и z-оценка.
Отдельно — по кипу: какое правило даёт наибольшее превышение.
"""
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/kfg/kfg.db"
MIN_T, MAXRUN, NPERM = 100, 12, 30


def load():
    con = sqlite3.connect(DB)
    pcs = dict(con.execute("select khipu_id, pcord_id from primary_cord"))
    inv = dict(con.execute("select khipu_id, investigator_num from khipu_main"))
    kids = defaultdict(list)
    by_khipu = defaultdict(list)
    clus = {}
    for cid, kid, par, o, cl in con.execute("select cord_id, khipu_id, pendant_from, cord_ordinal, cluster_id from cord"):
        kids[par].append((o or 0, cid))
        by_khipu[kid].append(cid)
        clus[cid] = cl
    val = defaultdict(int)
    for cid, v in con.execute("select cord_id, knot_value_type from knot"):
        val[cid] += int(v or 0)
    memo = {}

    def tree(c):
        if c not in memo:
            memo[c] = val.get(c, 0) + sum(tree(k) for _, k in kids.get(c, []))
        return memo[c]
    K = {}
    for kid, pc in pcs.items():
        top = [c for _, c in sorted(kids.get(pc, []))]
        if len(top) < 6:
            continue
        rows = []
        for c in top:
            subs = [k for _, k in kids.get(c, [])]
            s = sum(tree(k) for k in subs)
            own = val.get(c, 0)
            rows.append({"own": own, "add": own + s, "sub": own - s if own - s >= 0 else None,
                         "hasub": bool(subs) and s > 0, "grp": clus.get(c)})
        if any(r["hasub"] for r in rows):
            K[inv.get(kid, kid)] = rows
    return K


def count(vals, hasub, grp=None):
    """Суммы: итог (≥ MIN_T) = сумма целой группы (кластера) других подвесных."""
    if grp is not None:
        totals = defaultdict(list)
        for i, v in enumerate(vals):
            if v is not None and v >= MIN_T:
                totals[v].append(i)
        N = 0
        bounds = []
        start = 0
        for i in range(1, len(vals) + 1):
            if i == len(vals) or grp[i] != grp[start]:
                bounds.append((start, i))
                start = i
        for a, b in bounds:
            if b - a < 2 or any(vals[k] is None for k in range(a, b)):
                continue
            s = sum(vals[a:b])
            touched = any(hasub[a:b])
            for t in totals.get(s, ()):
                if not (a <= t < b) and (touched or hasub[t]):
                    N += 1
        return N
    n = len(vals)
    totals = defaultdict(list)
    for i, v in enumerate(vals):
        if v is not None and v >= MIN_T:
            totals[v].append(i)
    N = 0
    for i in range(n):
        if vals[i] is None:
            continue
        s, touched = 0, False
        for j in range(i, min(n, i + MAXRUN)):
            if vals[j] is None:
                break
            s += vals[j]
            touched |= hasub[j]
            if j == i:
                continue
            for t in totals.get(s, ()):
                if not (i <= t <= j) and (touched or hasub[t]):
                    N += 1
    return N


def main():
    K = load()
    print(f"кипу с дочерними шнурами: {len(K)}")
    rng = random.Random(1)
    rules = ["own", "add", "sub"]
    tot = {r: [0, 0.0, 0.0] for r in rules}  # реальные, сумма фона, сумма квадратов разброса
    wins = Counter()
    for inv, rows in K.items():
        per = {}
        for r in rules:
            vals = [x[r] for x in rows]
            hs = [x["hasub"] for x in rows]
            gp = [x["grp"] for x in rows]
            real = count(vals, hs, gp)
            bg = []
            idx = list(range(len(rows)))
            for _ in range(NPERM):
                rng.shuffle(idx)  # значения перемешиваются, границы групп остаются на месте
                bg.append(count([vals[i] for i in idx], [hs[i] for i in idx], gp))
            m = sum(bg) / len(bg)
            var = sum((b - m) ** 2 for b in bg) / len(bg)
            tot[r][0] += real
            tot[r][1] += m
            tot[r][2] += var
            per[r] = real - m
        best = max(per, key=per.get)
        if per[best] > 0.5:
            wins[best] += 1
    print(f"{'правило':6} {'реальных':>9} {'фон':>9} {'превышение':>11} {'z':>7}")
    for r in rules:
        real, m, var = tot[r]
        z = (real - m) / (var ** 0.5) if var > 0 else float("nan")
        print(f"{r:6} {real:9} {m:9.1f} {real - m:11.1f} {z:7.1f}")
    print("по кипу — какое правило даёт наибольшее превышение:", dict(wins))


if __name__ == "__main__":
    main()
