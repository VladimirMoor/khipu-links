"""Детектор связи «сводка с транспонированием» между двумя кипу (тип Thompson 2024).

Кипу A: последовательность кластеров v_1..v_T (у каждого до k подвесных; значение
шнура = шнур + все дочерние). Кипу B: таблица k×n (k групп по n подвесных, значение с
дочерними). Гипотеза: A делится на n подряд идущих отрезков, и сумма кластеров отрезка s
по позиции p ≈ B[p][s].

Поиск: динамическое программирование по границам отрезков, максимизирующее число
«попаданий» — клеток, где |сумма − B| ≤ tol·max(1, B) (tol=0 — только точные), без учёта
пар 0↔0. Значимость: то же для A с перемешанным порядком кластеров (перестановка ломает
связь отрезков, но сохраняет состав), максимум по перестановкам → p-value.
"""
import argparse
import csv
import itertools
import os
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/kfg_cords.csv"))


def load_all():
    by = defaultdict(list)
    with open(CORDS) as f:
        for r in csv.DictReader(f):
            by[r["inv_num"]].append(r)
    return by


def tree_values(rows):
    kids = defaultdict(list)
    for r in rows:
        kids[r["parent_id"]].append(r)
    memo = {}

    def sub(r):
        if r["cord_id"] not in memo:
            memo[r["cord_id"]] = int(r["value"]) + sum(sub(c) for c in kids.get(r["cord_id"], []))
        return memo[r["cord_id"]]
    top = sorted([r for r in rows if r["parent_id"] == ""], key=lambda r: int(r["order"]))
    return top, sub


def clusters_of(rows, min_size=5, max_size=7, split_big=True):
    """Кластеры подвесных (группы KFG размера min..max; большие делим пополам;
    одиночные шнуры-маркеры и мелкие группы пропускаем)."""
    top, sub = tree_values(rows)
    out = []
    for _, it in itertools.groupby(top, key=lambda r: r["group"]):
        c = [sub(r) for r in it]
        n = len(c)
        if split_big and n >= 2 * min_size:
            h = n // 2
            out += [c[:h], c[h:]]
        elif min_size <= n <= max_size:
            out.append(c)
    return out


def table_of(rows, n_min=8):
    """Таблица B: группы KFG, у которых ≥ n_min подвесных, без первого шнура-маркера
    (если он пуст); строки = группы, столбцы = позиции."""
    top, sub = tree_values(rows)
    T = []
    for _, it in itertools.groupby(top, key=lambda r: r["group"]):
        g = list(it)
        if g and int(g[0]["value"]) == 0 and sub(g[0]) == 0 and g[0]["color"] != "W":
            g = g[1:]
        if len(g) >= n_min:
            T.append([sub(r) for r in g])
    return T


def table_by_markers(rows, prefix="SR"):
    """Таблица B по шнурам-маркерам: делим подвесные по шнурам, чей цвет начинается
    с prefix (красный/красно-белый), строка = шнуры после маркера до следующего."""
    top, sub = tree_values(rows)
    T, cur = [], None
    for r in top:
        if r["color"].startswith(prefix):
            if cur:
                T.append(cur)
            cur = []
        elif cur is not None:
            cur.append(sub(r))
    if cur:
        T.append(cur)
    return T


def hit(a, b, tol):
    if a == 0 and b == 0:
        return 0
    return 1 if abs(a - b) <= tol * max(1, b) else 0


def cell_err(a, b):
    """Относительная ошибка клетки, ограниченная сверху 1 (грубый промах = 1)."""
    return min(1.0, abs(a - b) / (abs(b) + 5))


def best_segmentation(C, B, tol=0.0, min_len=1, mode="err"):
    """C: список кластеров (векторы длины ≤k); B: k×n. mode="err": минимизируем сумму
    относительных ошибок (возвращаем −ошибку); mode="hits": максимизируем попадания."""
    k, n, T = len(B), len(B[0]), len(C)
    # префиксные суммы по позициям
    pref = [[0] * k]
    for c in C:
        pref.append([pref[-1][p] + (c[p] if p < len(c) else 0) for p in range(k)])

    def seg_score(i, j, s):
        if mode == "hits":
            return sum(hit(pref[j][p] - pref[i][p], B[p][s], tol) for p in range(k))
        return -sum(cell_err(pref[j][p] - pref[i][p], B[p][s]) for p in range(k))
    NEG = -10 ** 9
    dp = [[NEG] * (T + 1) for _ in range(n + 1)]
    back = [[0] * (T + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for s in range(1, n + 1):
        for j in range(s * min_len, T + 1):
            best, arg = NEG, 0
            for i in range((s - 1) * min_len, j - min_len + 1):
                if dp[s - 1][i] == NEG:
                    continue
                v = dp[s - 1][i] + seg_score(i, j, s - 1)
                if v > best:
                    best, arg = v, i
            dp[s][j], back[s][j] = best, arg
    bounds, j = [T], T
    for s in range(n, 0, -1):
        j = back[s][j]
        bounds.append(j)
    return dp[n][T], bounds[::-1]


def seg_matrix(C, B, bounds):
    k, n = len(B), len(B[0])
    return [[sum(c[p] for c in C[bounds[s]:bounds[s + 1]] if p < len(c)) for s in range(n)] for p in range(k)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="AS069")
    ap.add_argument("--b", default="AS070")
    ap.add_argument("--k", type=int, default=6, help="сколько групп B (строк) брать")
    ap.add_argument("--n", type=int, default=10, help="сколько позиций в группе B (столбцов)")
    ap.add_argument("--tol", type=float, default=0.0)
    ap.add_argument("--null", type=int, default=50)
    a = ap.parse_args()
    by = load_all()
    C = clusters_of(by[a.a])
    B = [row[:a.n] + [0] * (a.n - len(row[:a.n])) for row in table_by_markers(by[a.b])[:a.k]]
    k = len(B)
    C = [c[:k] for c in C]
    print(f"{a.a}: {len(C)} кластеров; {a.b}: таблица {k}×{a.n}")
    for r in B:
        print("   B", r)
    h, bounds = best_segmentation(C, B, a.tol)
    M = seg_matrix(C, B, bounds)
    exact = sum(1 for p in range(k) for s in range(a.n) if M[p][s] == B[p][s] and B[p][s])
    near = sum(1 for p in range(k) for s in range(a.n) if B[p][s] and abs(M[p][s] - B[p][s]) <= 0.05 * B[p][s])
    print(f"суммарная ошибка {-h:.2f}; точных {exact}, в пределах 5%: {near} из {k * a.n}; границы: {bounds}")
    print(f"длины отрезков: {[bounds[i+1]-bounds[i] for i in range(len(bounds)-1)]}")
    for p in range(k):
        print("   A", M[p])
    rng = random.Random(1)
    nulls = []
    for _ in range(a.null):
        D = C[:]
        rng.shuffle(D)
        nulls.append(best_segmentation(D, B, a.tol)[0])
    nulls.sort()
    p = (sum(1 for x in nulls if x >= h) + 1) / (a.null + 1)
    print(f"перестановки кластеров: лучшая ошибка {-nulls[-1]:.2f}, медиана {-nulls[len(nulls)//2]:.2f} → p={p:.3f}")


if __name__ == "__main__":
    main()
