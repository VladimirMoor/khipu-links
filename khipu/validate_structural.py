"""Посадка: берём настоящий табличный участок кипу, шумим (±25%), выбрасываем 20%
клеток, перемешиваем столбцы — проверяем, находит ли поиск ту же кипу и значимо ли."""
import math
import random
from itertools import permutations

from structural import candidates, load_tables, run


def plant(tables, rng, m, k):
    while True:
        kid = rng.choice(list(tables))
        cands = [(key, mat) for key, mat in candidates(tables[kid], m, k)
                 if key[0] == "A" and key[2] == 1 and key[3] is None
                 and sum(1 for r in mat for x in r if x > 0) >= m * k * 0.8]
        if cands:
            key, mat = rng.choice(cands)
            break
    perm = list(range(k))
    rng.shuffle(perm)
    doc = []
    for r in mat:
        row = [max(1, round(r[perm[j]] * math.exp(rng.gauss(0, 0.25)))) if rng.random() > 0.2 else None
               for j in range(k)]
        doc.append(row)
    return kid, doc


if __name__ == "__main__":
    rng = random.Random(5)
    tables = load_tables()
    for m, k in [(12, 5), (8, 4), (6, 4)]:
        hits, sig = 0, 0
        T = 8
        for _ in range(T):
            kid, doc = plant(tables, rng, m, k)
            top, p, _ = run("plant", doc, tables, 30, rng)
            hits += bool(top) and top[0][1] == kid
            sig += p <= 0.05
        print(f"{m}x{k}: найдена та же кипу {hits}/{T}, p<=0.05 в {sig}/{T}")
