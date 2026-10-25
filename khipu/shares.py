"""Деление круглой величины на равные доли с распределением остатка (100/3 → 33, 33, 34; 2000/3 → 666, 667, 667).

Подряд идущие подвесные (2–6) одной группы, значения ≥ 10, различаются ровно на 1, сумма — кратна 10 (100) и не делится нацело
на число долей. Фон: то же условие для суммы, сдвинутой на ±1…±5. База OKR (khipu/hyp.py). Вывод: extracted/shares.txt.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hyp  # noqa: E402

OUT = hyp.ROOT / "extracted/shares.txt"


def scan(K, d, base):
    hits = []
    for k, cs in K.items():
        for gi, g in enumerate(hyp.groups(cs)):
            v = [r["value"] for r in g]
            for n in range(2, 7):
                for i in range(len(v) - n + 1):
                    w = v[i:i + n]
                    if min(w) < 10 or max(w) - min(w) != 1:
                        continue
                    s = sum(w) + d
                    if s % base == 0 and s % n:
                        hits.append((k, gi + 1, i + 1, n, tuple(w), sum(w)))
    return hits


def main():
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    lines = []
    for base in (10, 100):
        real = scan(K, 0, base)
        sh = [len(scan(K, d, base)) for d in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)]
        lines.append(f"sum a multiple of {base}: {len(real)} runs; sum shifted ±1…±5: mean {statistics.mean(sh):.1f}, max {max(sh)}")
    for k, g, i, n, w, s in sorted(set(scan(K, 0, 10)), key=lambda x: (-x[5], x[0])):
        lines.append(f"  {k:9} g{g} cords {i}–{i + n - 1}: {list(w)} = {s} ({s}/{n} = {s / n:.2f}) · {site.get(k)}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
