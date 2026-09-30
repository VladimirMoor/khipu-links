"""Сводка из двух разных кипу: группа Z = группа X + группа Y поразрядно (X, Y, Z — три разных кипу).

По образцу Хатун-Хаухи (Chirinos 2010, гл. 2: сводка 1558 = сумма детальных кипу 1561). Все группы
3–10 шнуров. Для группы-цели b и каждой группы a той же длины из другого кипу ищем группу c = b − a в
таблице всех групп (третий кипу). Требования: ≥ 3 позиций, где b ≥ 10; a и c имеют ≥ 2 ненулевых
позиций каждая и не совпадают с b. Музейные номера трёх кипу разные. Фон: b + d (d = ±1, ±2, ±3)
в позициях b ≥ 10. Вывод: extracted/twosource.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/twosource.txt"


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    G = []
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        for i, (_, g) in enumerate(itertools.groupby(rs, key=lambda r: r["group"]), 1):
            v = tuple(int(r["value"]) for r in g)
            if 3 <= len(v) <= 10 and sum(1 for x in v if x > 0) >= 2:
                G.append((k, i, v))
    return G


def main():
    G = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    table = defaultdict(list)
    byL = defaultdict(list)
    for k, i, v in G:
        table[v].append((k, i))
        byL[len(v)].append((k, i, v))
    targets = [(k, i, v) for k, i, v in G if sum(1 for x in v if x >= 10) >= 3]

    def scan(d):
        hits = []
        for kb, ib, b0 in targets:
            b = tuple(x + d if x >= 10 else x for x in b0)
            for ka, ia, a in byL[len(b)]:
                if mus(ka) == mus(kb) or a == b:
                    continue
                c = tuple(x - y for x, y in zip(b, a))
                if min(c) < 0 or sum(1 for x in c if x > 0) < 2:
                    continue
                for kc, ic in table.get(c, []):
                    if mus(kc) not in (mus(ka), mus(kb)) and ka < kc:
                        hits.append((kb, ib, b0, ka, ia, a, kc, ic, c))
        return hits

    real = scan(0)
    nulls = [len(scan(d)) for d in (-3, -2, -1, 1, 2, 3)]
    lines = [f"групп-целей: {len(targets)}; совпадений Z = X + Y: {len(real)}; фон {nulls}"]
    big = sorted(real, key=lambda h: -max(h[2]))
    for kb, ib, b, ka, ia, a, kc, ic, c in big[:30]:
        lines.append(f"  {kb} г{ib} {list(b)} = {ka} г{ia} {list(a)} + {kc} г{ic} {list(c)}   | "
                     f"{meta.get(kb, {}).get('PROVENANCE')} / {meta.get(ka, {}).get('PROVENANCE')} / {meta.get(kc, {}).get('PROVENANCE')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
