"""Сравнение берлинского состава (AS143/AS149/AS179: 22.4 : 10.4 : 54.4 : 12.8 %) с составами
из колониальных источников. Для каждого источника — наилучшее сопоставление позиций
(перебор перестановок), мера — максимальное отклонение доли. Фон — случайные составы
(Дирихле(1,1,1,1)), чтобы понять, насколько «близко» вообще что-то значит.
"""
import csv
import itertools
import random
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = [0.224, 0.1038, 0.5442, 0.128]
CATS = ["tributarios", "viejos", "muchachos", "mujeres"]


def census():
    data = OrderedDict()
    for r in csv.DictReader(open(ROOT / "extracted/A1.csv")):
        it = next((c for c in CATS if r["item"].startswith(c)), None)
        if r["doc_id"] == "A1.m" and r["section"].startswith("padrón 1570") and it:
            data.setdefault(r["context"], {})[it] = float(r["quantity"])
    out = [(f"Толедо 1570: {k}", [v[c] for c in CATS]) for k, v in data.items() if len(v) == 4]
    out.append(("Сисикая 1588 (сводка документа)", [153, 39, 184, 263]))
    return out


def best(p, q):
    q = [x / sum(q) for x in q]
    return min((max(abs(a - q[k]) for a, k in zip(p, perm)), perm) for perm in itertools.permutations(range(len(q))))


def null(n=20000, seed=1):
    rng = random.Random(seed)
    d = sorted(best(K, [rng.gammavariate(1, 1) for _ in range(4)])[0] for _ in range(n))
    return d


def report(title, items, labels):
    d0 = null()
    print(f"\n{title}\nберлинский состав: {K}; случайные составы: медиана {d0[len(d0)//2]:.3f}, "
          f"5% {d0[len(d0)//20]:.3f}, 1% {d0[len(d0)//100]:.3f}")
    for name, q in items:
        d, perm = best(K, q)
        qn = [round(x / sum(q), 3) for x in q]
        rank = sum(1 for x in d0 if x <= d) / len(d0)
        print(f"  {name[:34]:34} {qn}  откл. {d:.3f} (доля случайных не хуже: {rank:.1%})  "
              f"позиции кипу → {[labels[k] for k in perm]}")


if __name__ == "__main__":
    report("Демография (переписи)", census(), CATS)
