"""Связан ли UR268 (вычет 208) с блоками UR269 (вычеты по местам 47+46+46+44+25 = 208)?

1) Поставки UR268 (брутто, нетто = брутто − 208) против сумм любых k подряд идущих записей UR269
   (k = 4…6, брутто и нетто), точное совпадение и в пределах 0.5%; фон — те же суммы, умноженные на
   случайный множитель 0.9…1.1 (1000 раз).
2) Размер: поставки UR268 против полных блоков UR269 (все пять мест заполнены) — средние и разброс.
Вывод: extracted/ur268_269.txt.
"""
import csv
import itertools
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
import slotded  # noqa: E402

OUT = ROOT / "extracted/ur268_269.txt"


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "" and r["inv_num"] == "UR268":
            by[r["group"]].append(r)
    dep = []
    for g in sorted(by.values(), key=lambda g: int(g[0]["order"])):
        v = [int(r["value"]) for r in sorted(g, key=lambda r: int(r["order"]))]
        if len(v) >= 3 and v[0] >= 1000:
            dep.append(v[0])
    recs = [g for b in slotded.blocks("UR269") for g in b if g and g[0] >= 100]
    gross = [g[0] for g in recs]
    net = [g[1] if len(g) > 1 else 0 for g in recs]
    sums = set()
    for seq in (gross, net):
        for k in (4, 5, 6):
            for i in range(len(seq) - k + 1):
                sums.add(sum(seq[i:i + k]))
    targets = dep + [d - 208 for d in dep]

    def hits(S, tol):
        return sum(any(abs(t - s) <= tol * t for s in S) for t in targets)

    real0, real5 = hits(sums, 0), hits(sums, 0.005)
    rnd = random.Random(1)
    null5 = [hits({round(s * rnd.uniform(0.9, 1.1)) for s in sums}, 0.005) for _ in range(1000)]
    p = (1 + sum(x >= real5 for x in null5)) / 1001
    full = [sum(g[0] for g in b) for b in slotded.blocks("UR269")
            if len(b) == 5 and all(g and g[0] >= 100 for g in b)]
    lines = [f"поставок UR268: {len(dep)}; записей UR269: {len(recs)}; сумм окон k = 4…6: {len(sums)}",
             f"точных совпадений (брутто или нетто UR268 = сумма окна): {real0}",
             f"в пределах 0.5%: {real5}; фон {st.mean(null5):.1f} (p = {p:.2f})",
             f"поставка UR268: среднее {st.mean(dep):.0f}, SD {st.pstdev(dep):.0f}; "
             f"полный блок UR269 (n = {len(full)}): среднее {st.mean(full):.0f}, SD {st.pstdev(full):.0f}"]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
