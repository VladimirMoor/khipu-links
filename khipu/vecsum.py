"""Группа одного кипу = поразрядная сумма нескольких групп другого (как AS143 г4 = AS149 г1 + г2).

Для кипу A берём группы одной длины L (3–12) и считаем суммы: подряд идущих (2–10 групп) и
«с шагом» t = 2…4 (2–8 групп: s, s + t, s + 2t …), как в части 2 AS175. Каждую группу B других
кипу (музейный номер другой) сравниваем с этими суммами той же длины: точное равенство во всех
позициях, либо во всех, кроме одной (допуск «одна ошибка»). Нужны ≥ 3 позиции со значением
≥ 10. Фон — те же суммы, сдвинутые на d в одной случайной позиции? Проще и строже: сдвиг всех
позиций B на +d (d = 1…5) — так сохраняется структура групп. Вывод: extracted/vecsum.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/vecsum.txt"


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


def sums(gs):
    """(вектор, описание) для сумм групп одной длины."""
    byL = defaultdict(list)
    for i, g in enumerate(gs):
        if 3 <= len(g) <= 12:
            byL[len(g)].append(i)
    out = []
    for L, idx in byL.items():
        n = len(idx)
        for a in range(n):
            for b in range(a + 2, min(n, a + 10) + 1):
                sel = idx[a:b]
                if sel[-1] - sel[0] == len(sel) - 1:
                    out.append((tuple(map(sum, zip(*(gs[i] for i in sel)))), f"г{sel[0] + 1}–г{sel[-1] + 1}"))
        for t in (2, 3, 4):
            for s in range(len(gs)):
                sel = []
                j = s
                while j < len(gs) and len(gs[j]) == L:
                    sel.append(j)
                    if 2 <= len(sel) <= 8 and len(sel) >= 2:
                        out.append((tuple(map(sum, zip(*(gs[i] for i in sel)))),
                                    "г" + ",".join(str(i + 1) for i in sel)))
                    j += t
    return out


def main():
    G = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    exact = defaultdict(list)
    loose = defaultdict(list)
    for k, gs in G.items():
        for v, lab in sums(gs):
            if sum(1 for x in v if x >= 10) < 3:
                continue
            exact[v].append((k, lab))
            for p in range(len(v)):
                loose[v[:p] + (None,) + v[p + 1:]].append((k, lab, v))

    def scan(d):
        hx, hl = [], []
        for y, gs in G.items():
            for j, g in enumerate(gs):
                if not 3 <= len(g) <= 12 or sum(1 for x in g if x >= 10) < 3:
                    continue
                w = tuple(x + d if x >= 10 else x for x in g)
                for k, lab in exact.get(w, []):
                    if k != y and mus(k) != mus(y):
                        hx.append((y, j + 1, g, k, lab))
                for p in range(len(w)):
                    for k, lab, v in loose.get(w[:p] + (None,) + w[p + 1:], []):
                        if k != y and mus(k) != mus(y) and v != w:
                            hl.append((y, j + 1, g, k, lab, v))
        return hx, hl

    rx, rl = scan(0)
    nulls = [scan(d) for d in (1, 2, 3, 5, 7)]
    lines = [f"точные: {len(rx)} (фон {[len(n[0]) for n in nulls]}); с одной ошибкой: {len(rl)} "
             f"(фон {[len(n[1]) for n in nulls]})", "", "точные:"]
    for y, j, g, k, lab in rx:
        lines.append(f"  {y} г{j} {g} = {k} сумма {lab}   | {meta.get(y, {}).get('PROVENANCE')} / {meta.get(k, {}).get('PROVENANCE')}")
    lines.append("с одной ошибкой:")
    for y, j, g, k, lab, v in rl[:80]:
        lines.append(f"  {y} г{j} {g} ≈ {k} сумма {lab} {list(v)}   | {meta.get(y, {}).get('PROVENANCE')} / {meta.get(k, {}).get('PROVENANCE')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:90]))


if __name__ == "__main__":
    main()
