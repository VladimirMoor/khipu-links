"""Пустые графы («бланк, который заполнят потом»): позиция группы, где шнур цел и без узлов.

Кипу с ≥ 5 группами одной длины L ≥ 3. Графа пустая, если в ≥ 80% групп на этой позиции
значение 0, а шнур цел (termination не B, длина ≥ половины медианной длины шнуров кипу).
Для сравнения — «оборванные пустые»: то же, но шнуры оборваны (порча, а не бланк).
Фон — значения и концы перемешаны внутри каждой группы (позиции разрушены, та же доля нулей).
Вывод: extracted/blanks.txt.
"""
import csv
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/blanks.txt"
FRAC = 0.8


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    K = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        L = [float(r["length"]) for r in rs if r["length"]]
        med = sorted(L)[len(L) // 2] if L else 0
        gs = []
        for _, g in itertools.groupby(rs, key=lambda r: r["group"]):
            gs.append([(int(r["value"]), r["termination"] == "B",
                        bool(r["length"]) and float(r["length"]) >= 0.5 * med, r["color"]) for r in g])
        n = Counter(len(g) for g in gs).most_common(1)[0][0]
        gs = [g for g in gs if len(g) == n]
        if n >= 3 and len(gs) >= 5:
            K[k] = gs
    return K


def blank_cols(gs):
    out = []
    for p in range(len(gs[0])):
        col = [g[p] for g in gs]
        intact = sum(1 for v, b, long_, _ in col if v == 0 and not b and long_)
        broken = sum(1 for v, b, _, _ in col if v == 0 and b)
        if intact >= FRAC * len(col):
            out.append(("цел", p + 1, intact, len(col), Counter(c for *_, c in col).most_common(1)[0][0]))
        elif intact + broken >= FRAC * len(col) and broken:
            out.append(("оборв", p + 1, intact + broken, len(col), Counter(c for *_, c in col).most_common(1)[0][0]))
    return out


def main():
    K = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    real = {k: blank_cols(gs) for k, gs in K.items()}
    count = lambda R, t: sum(1 for cols in R.values() if any(c[0] == t for c in cols))
    rnd = random.Random(1)
    nulls = []
    for _ in range(50):
        R = {k: blank_cols([rnd.sample(g, len(g)) for g in gs]) for k, gs in K.items()}
        nulls.append((count(R, "цел"), count(R, "оборв")))
    lines = [f"кипу с правильными группами: {len(K)}",
             f"с пустой целой графой: {count(real, 'цел')} (фон {sum(n[0] for n in nulls) / 50:.1f}, "
             f"макс {max(n[0] for n in nulls)})",
             f"с пустой графой из оборванных шнуров: {count(real, 'оборв')} (фон {sum(n[1] for n in nulls) / 50:.1f})",
             ""]
    full = {k for k, gs in K.items() if all(v == 0 for g in gs for v, *_ in g)}
    K2 = {k: gs for k, gs in K.items() if k not in full}
    part = sum(1 for k in K2 if any(c[0] == "цел" for c in real[k]))
    rnd2 = random.Random(2)
    pn = [sum(1 for gs in K2.values() if any(c[0] == "цел" for c in blank_cols([rnd2.sample(g, len(g)) for g in gs])))
          for _ in range(200)]
    lines.insert(3, f"без полностью пустых кипу ({', '.join(sorted(full))}): {part} "
                    f"(фон {sum(pn) / len(pn):.1f}, макс {max(pn)} из 200)")
    for k, cols in sorted(real.items()):
        if cols:
            lines.append(f"  {k:10} L={len(K[k][0])} групп={len(K[k])} {cols}  | {meta.get(k, {}).get('PROVENANCE')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
