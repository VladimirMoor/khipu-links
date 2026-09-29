"""Фиксированный вычет («налог») вне Инкауаси.

В каждом кипу берём «суммовые» группы: ≥ 3 подвесных, крупнейший = сумме остальных (свои
значения; нули не считаем слагаемыми). Среди слагаемых ищем значение c > 0, которое входит в
≥ MINFRAC суммовых групп кипу и хотя бы в MINN из них. Фон: в каждой группе крупнейший шнур
сдвигаем на d (d = ±1…±10) и заново ищем «суммовые» группы с тем же правилом «крупнейший =
сумма остальных + d» — это сохраняет состав значений кипу, но разрушает точные суммы.
Вывод: extracted/taxscan.txt.
"""
import csv
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/taxscan.txt"
MINFRAC, MINN = 0.5, 4


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        G[k] = [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    return G


def taxes(gs, d=0):
    sumg = []
    for g in gs:
        parts = sorted((x for x in g if x), reverse=True)
        if len(parts) >= 3 and parts[0] == sum(parts[1:]) + d:
            sumg.append(set(parts[1:]))
    if len(sumg) < MINN:
        return len(sumg), []
    c = Counter(x for s in sumg for x in s)
    return len(sumg), [(v, n) for v, n in c.most_common() if n >= MINN and n >= MINFRAC * len(sumg)]


def main():
    G = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    real = {k: taxes(gs) for k, gs in G.items()}
    hits = {k: v for k, v in real.items() if v[1]}
    null = []
    for d in [x for x in range(-10, 11) if x]:
        null.append(sum(1 for gs in G.values() if taxes(gs, d)[1]))
    lines = [f"кипу с «налогом» (одно слагаемое в ≥ {MINFRAC:.0%} суммовых групп, ≥ {MINN}): {len(hits)}; "
             f"фон (общее ± d): {sum(null) / len(null):.1f}, макс {max(null)}", ""]
    for k, (n, t) in sorted(hits.items(), key=lambda kv: -kv[1][0]):
        lines.append(f"  {k:10} суммовых групп {n:3}  повторяющиеся слагаемые {t[:4]}  | "
                     f"{meta.get(k, {}).get('PROVENANCE')} #{meta.get(k, {}).get('MUSEUM_NUM')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
