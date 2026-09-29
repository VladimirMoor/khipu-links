"""Поиск пар кипу со связью «сводка с транспонированием» по всему корпусу KFG.

B-кандидаты: (1) подряд идущие группы KFG одинакового размера n (5..12), не меньше 4
групп, в каждой ≥ 3 непустых шнура; (2) строки между красными маркерами (SR…), ≥ 4 строк
длиной ≥ 5 → таблица k×n (k = число строк, до 10).
A-кандидаты: кипу, у которых ≥ 2n кластеров размера k−1..k+1 (позиции 1..k).
Для каждой пары — DP из segsum (минимум относительной ошибки), затем для лучших пар
перестановочная проверка.
"""
import itertools
import random
import sys

from segsum import best_segmentation, load_all, seg_matrix, table_by_markers, tree_values

MAX_T = 400


def b_tables(rows):
    top, sub = tree_values(rows)
    groups = [[sub(r) for r in it] for _, it in itertools.groupby(top, key=lambda r: r["group"])]
    out = []
    i = 0
    while i < len(groups):
        n = len(groups[i])
        j = i
        while j < len(groups) and len(groups[j]) == n:
            j += 1
        run = [g for g in groups[i:j] if sum(1 for x in g if x) >= 3]
        if 5 <= n <= 12 and len(run) >= 4:
            out.append(run[:10])
        i = max(j, i + 1)
    # второй способ: строки, разделённые красными маркерами (цвет начинается с SR)
    mt = [r for r in table_by_markers(rows) if len(r) >= 5 and sum(1 for x in r if x) >= 3]
    if len(mt) >= 4:
        n = min(12, sorted(len(r) for r in mt)[len(mt) // 2])  # медианная длина строки
        mt = [r for r in mt if n - 1 <= len(r) <= n + 1]
        if len(mt) >= 4:
            out.append([(r + [0] * n)[:n] for r in mt[:10]])
    return out


def a_clusters(rows, k):
    top, sub = tree_values(rows)
    C = []
    for _, it in itertools.groupby(top, key=lambda r: r["group"]):
        c = [sub(r) for r in it]
        if k - 1 <= len(c) <= k + 1:
            C.append(c[:k])
    return C


def main():
    by = load_all()
    Bs = [(inv, t) for inv, rows in by.items() for t in b_tables(rows)]
    print(f"таблиц-кандидатов B: {len(Bs)}", flush=True)
    res = []
    for bi, (binv, B) in enumerate(Bs):
        k, n = len(B), len(B[0])
        for ainv, rows in by.items():
            if ainv == binv:
                continue
            C = a_clusters(rows, k)
            if len(C) < 2 * n or len(C) > MAX_T:
                continue
            err, bounds = best_segmentation(C, B)
            res.append((-err / (k * n), binv, ainv, k, n, len(C), bounds))
        print(f"  {bi+1}/{len(Bs)} {binv} {k}×{n}", flush=True)
    res.sort()
    known = [x for x in res if {x[1], x[2]} == {"AS069", "AS070"}]
    rank = next((i + 1 for i, x in enumerate(res) if {x[1], x[2]} == {"AS069", "AS070"}), None)
    print(f"контроль: пара AS069/AS070 на месте {rank} из {len(res)}; {known[:1]}")
    print("\nлучшие пары (средняя ошибка на клетку):")
    for e, binv, ainv, k, n, T, bounds in res[:15]:
        print(f"  {e:.3f}  B={binv} ({k}×{n})  A={ainv} ({T} кластеров)")
    rng = random.Random(2)
    print("\nперестановочная проверка для 8 лучших:")
    for e, binv, ainv, k, n, T, bounds in res[:8]:
        B = next(t for inv, t in Bs if inv == binv and len(t) == k and len(t[0]) == n)
        C = a_clusters(by[ainv], k)
        nulls = []
        for _ in range(30):
            D = C[:]
            rng.shuffle(D)
            nulls.append(-best_segmentation(D, B)[0] / (k * n))
        better = sum(1 for x in nulls if x <= e)
        print(f"  B={binv} A={ainv}: ошибка {e:.3f}, перестановки min {min(nulls):.3f} med {sorted(nulls)[15]:.3f} → p={(better+1)/31:.3f}", flush=True)


if __name__ == "__main__":
    main()
