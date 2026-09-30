"""Сводки между кипу: шнуры одного кипу X подряд = итоги групп или суммы столбцов другого кипу Y.

Для каждого Y (подвесные, собственные значения):
  T — итоги групп по порядку (все группы ≥ 2 шнуров);
  C — суммы по месту (столбцы) по каждому максимальному ряду ≥ 2 подряд идущих групп одной длины L ≥ 3,
      а также по всему кипу для групп этой длины.
Ищем в X (подвесные подряд и дочерние одного шнура подряд; прямо и обратно) окно длиной ≥ 3, совпадающее с
последовательным участком T или C; окно должно иметь ≥ 2 некруглых значения ≥ 10. X ≠ Y по музейному номеру.
Фон — цели Y + d (d = ±1…±5, только ненулевые). Вывод: extracted/summaries.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/summaries.txt"
K = 3


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    rows = list(csv.DictReader(open(ROOT / "extracted/plus_cords.csv")))
    kids = defaultdict(list)
    by = defaultdict(list)
    for r in rows:
        (kids[r["parent_id"]].append(r) if r["parent_id"] else by[r["inv_num"]].append(r))
    for k in by:
        by[k].sort(key=lambda r: int(r["order"]))
    # sequences in X to search: pendants in order, subsidiaries of each cord in order
    seqs = defaultdict(list)
    for k, rs in by.items():
        seqs[k].append(("подв.", [int(r["value"]) for r in rs]))
        for r in rs:
            ch = sorted(kids.get(r["cord_id"], []), key=lambda c: int(c["order"]))
            if len(ch) >= K:
                seqs[k].append((f"доч. шнура {r['order']}", [int(c["value"]) for c in ch]))
    idx = defaultdict(list)
    for k, ss in seqs.items():
        for lab, v in ss:
            for d, w in (("прямо", v), ("обратно", v[::-1])):
                for i in range(len(w) - K + 1):
                    t = tuple(w[i:i + K])
                    if sum(x >= 10 and x % 10 > 0 for x in t) >= 2:
                        idx[t].append((k, lab, d))

    def targets(k):
        gs = [[int(r["value"]) for r in g] for _, g in itertools.groupby(by[k], key=lambda r: r["group"])]
        out = []
        T = [sum(g) for g in gs if len(g) >= 2]
        out.append(("итоги групп", T))
        for L, run in itertools.groupby(enumerate(gs), key=lambda x: len(x[1])):
            run = list(run)
            if L >= 3 and len(run) >= 2:
                out.append((f"столбцы групп {run[0][0] + 1}–{run[-1][0] + 1} (L={L})",
                            [sum(g[i] for _, g in run) for i in range(L)]))
        for L in {len(g) for g in gs if len(g) >= 3}:
            same = [g for g in gs if len(g) == L]
            if len(same) >= 3:
                out.append((f"столбцы всех групп L={L}", [sum(g[i] for g in same) for i in range(L)]))
        return out

    def scan(dv):
        hits = {}
        for Y in by:
            for lab, t in targets(Y):
                tt = [x + dv if x else x for x in t]
                for i in range(len(tt) - K + 1):
                    w = tuple(tt[i:i + K])
                    for X, xl, d in idx.get(w, []):
                        if mus(X) != mus(Y):
                            hits.setdefault((X, Y, lab), set()).add((i, xl, d))
        return hits

    real = scan(0)
    null = [len(scan(d)) for d in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)]
    lines = [f"пар (X, Y, цель) с окном ≥ {K}: {len(real)}; фон {sum(null) / len(null):.1f} (макс {max(null)})"]
    for (X, Y, lab), s in sorted(real.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"  {X} ({meta.get(X, {}).get('PROVENANCE')}) ← {Y} ({meta.get(Y, {}).get('PROVENANCE')}) {lab}: "
                     f"{len(s)} окон, напр. {sorted(s)[:2]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:60]))


if __name__ == "__main__":
    main()
