"""Связи между кипу через общий «рецепт» состава групп (как AS143 ~ AS149).

Группа (кластер) из 4–6 подвесных, сумма ≥ MINSUM, профиль p = значения / сумма; нужна
«непростая» форма: ≥ 3 позиции с долей ≥ 5%. Две группы из разных кипу (разные музейные
номера) одной длины совпадают, если max|p − q| ≤ TOL. Счёт пары кипу = число групп первой,
у которых есть совпадающая группа во второй, плюс наоборот. Фон — то же, но позиции групп
второй кипу циклически сдвинуты на 1..L−1 (статистика профилей та же, позиции разрушены).
"""
import csv
import itertools
import json
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))
MINSUM, TOL = 200, 0.01


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        out = []
        for _, g in itertools.groupby(rs, key=lambda r: r["group"]):
            v = [int(r["value"]) for r in g]
            s = sum(v)
            if 4 <= len(v) <= 6 and s >= MINSUM:
                p = [x / s for x in v]
                if sum(1 for x in p if x >= 0.05) >= 3:
                    out.append(p)
        if out:
            G[k] = out
    return G


def match(p, q):
    return len(p) == len(q) and max(abs(a - b) for a, b in zip(p, q)) <= TOL


def pair_score(A, B, rot=0):
    Bq = [q[rot % len(q):] + q[:rot % len(q)] for q in B] if rot else B
    a = sum(1 for p in A if any(match(p, q) for q in Bq))
    b = sum(1 for q in Bq if any(match(q, p) for p in A))
    return a + b


def main():
    G = load()
    meta = {}
    for fn in ("kfg_khipus.json",):
        for k in json.load(open(ROOT / "extracted" / fn)):
            meta[k["INVESTIGATOR_NUM"]] = k
    museum = {k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "") for k in G}
    keys = sorted(G)
    print(f"кипу с подходящими группами: {len(keys)}, групп: {sum(len(v) for v in G.values())}")
    res = []
    for x, y in itertools.combinations(keys, 2):
        if museum[x] == museum[y]:
            continue
        s = pair_score(G[x], G[y])
        if s >= 2:
            L = max(len(p) for p in G[y])
            bg = [pair_score(G[x], G[y], r) for r in range(1, L)]
            res.append((s, max(bg), x, y))
    res.sort(key=lambda t: (-(t[0] - t[1]), -t[0]))
    tot_real = sum(s for s, _, _, _ in res)
    print(f"пар кипу со счётом ≥ 2: {len(res)}")
    print(f"{'счёт':>4} {'фон':>4}  пара")
    for s, b, x, y in res[:30]:
        mx, my = meta.get(x, {}), meta.get(y, {})
        print(f"{s:4} {b:4}  {x:>10} ~ {y:<10} {(mx.get('MUSEUM_NAME') or '')[:24]} #{mx.get('MUSEUM_NUM')} | "
              f"{(my.get('MUSEUM_NAME') or '')[:24]} #{my.get('MUSEUM_NUM')} | {mx.get('PROVENANCE')} / {my.get('PROVENANCE')}")


if __name__ == "__main__":
    main()
