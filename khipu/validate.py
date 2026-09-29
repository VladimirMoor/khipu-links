"""Проверка сверщика на случаях с известным ответом.

1. Пара Томпсон (2024): KH0082 (AS69) и KH0083 (AS70) из Арики хранят одни данные.
   Берём числа одной кипу как «документ» и ищем среди остальных 608.
2. Синтетика: из случайной кипу берём часть чисел, портим часть из них и
   перемешиваем порядок (как в пересказе писца) — должна найтись та же кипу.
"""
import random

from match import MIN_VALUE, best, evaluate, load_khipus, rarity


def by_okr(khipus, okr):
    return next(k for k, v in khipus.items() if v["okr"] == okr or v["inv"] == okr)


def thompson(khipus, w, rng):
    for src, dst in [("KH0082", "KH0083"), ("KH0083", "KH0082")]:
        sid, did = by_okr(khipus, src), by_okr(khipus, dst)
        vals = [v for v in khipus[sid]["seq"] if v >= MIN_VALUE]
        others = {k: v for k, v in khipus.items() if k != sid}
        res, p, q95 = evaluate(src, vals, others, w, rng, null_n=100)
        rank = next((i for i, r in enumerate(best(vals, others, w, 609)) if r[1] == did), None)
        print(f"{src} -> top={res[0]['okr']} score={res[0]['score']} "
              f"rank_of_{dst}={rank + 1 if rank is not None else '-'} p={p:.3f} null95={q95:.1f}")


def synthetic(khipus, w, rng, trials=40, keep=0.3, corrupt=0.2, max_len=40):
    ranks = []
    pool = [k for k, v in khipus.items() if sum(1 for x in v["seq"] if x >= 10) >= 15]
    for _ in range(trials):
        kid = rng.choice(pool)
        vals = [v for v in khipus[kid]["seq"] if v >= MIN_VALUE]
        rng.shuffle(vals)
        vals = vals[:max(5, min(max_len, int(len(vals) * keep)))]
        vals = [v + rng.choice([-1, 1]) * max(1, v // 10) if rng.random() < corrupt else v
                for v in vals]
        ranking = best(vals, khipus, w, len(khipus))
        ranks.append(next(i for i, r in enumerate(ranking) if r[1] == kid) + 1)
    top1 = sum(1 for r in ranks if r == 1) / len(ranks)
    top5 = sum(1 for r in ranks if r <= 5) / len(ranks)
    print(f"synthetic keep={keep} corrupt={corrupt} max_len={max_len}: "
          f"top1={top1:.0%} top5={top5:.0%} median_rank={sorted(ranks)[len(ranks)//2]}")


if __name__ == "__main__":
    rng = random.Random(7)
    khipus = load_khipus()
    w = rarity(khipus)
    thompson(khipus, w, rng)
    for keep, corrupt, ml in [(0.3, 0.2, 40), (0.2, 0.3, 20), (0.1, 0.3, 10)]:
        synthetic(khipus, w, rng, keep=keep, corrupt=corrupt, max_len=ml)
