"""Дочерние одного шнура = итоги групп (или подряд идущие шнуры) другого кипу — как AS118 → AS125.

Цели: для каждого подвесного с ≥ 3 дочерними — список значений дочерних (по порядку).
Источники в каждом другом кипу: (а) цепочка сумм групп подвесных, (б) цепочка значений
подвесных подряд. Счёт — лучший сдвиг, число позиций со значением ≥ MINV, совпавших с
допуском max(1, TOL·x). Фон — те же цели, сдвинутые на d (|d| = 10…100 с шагом 10), —
сколько пар (цель, кипу) набирают тот же счёт. Кипу с тем же музейным номером пропускаем.
Вывод: extracted/subsum.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/subsum.txt"
MINV, TOL, MINS = 100, 0.005, 2


def load():
    rows = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        rows[r["inv_num"]].append(r)
    targets, chains = [], {}
    for k, R in rows.items():
        kids = defaultdict(list)
        for r in R:
            if r["parent_id"]:
                kids[r["parent_id"]].append(r)
        top = sorted((r for r in R if not r["parent_id"]), key=lambda r: int(r["order"]))
        for r in top:
            ks = sorted(kids[r["cord_id"]], key=lambda c: int(c["sib_ordinal"] or 0))
            v = [int(c["value"]) for c in ks]
            if len(v) >= 3 and sum(1 for x in v if x >= MINV) >= MINS:
                targets.append((k, r["order"], v))
        gsum = [sum(int(r["value"]) for r in g) for _, g in itertools.groupby(top, key=lambda r: r["group"])]
        chains[k] = {"группы": gsum, "шнуры": [int(r["value"]) for r in top]}
    return targets, chains


def score(t, seq):
    best, at = 0, None
    for sh in range(-len(t) + 1, len(seq)):
        c = sum(1 for i, x in enumerate(t) if x >= MINV and 0 <= i + sh < len(seq)
                and abs(seq[i + sh] - x) <= max(1, TOL * x))
        if c > best:
            best, at = c, sh
    return best, at


def main():
    targets, chains = load()
    meta = {}
    for fn in ("kfg_khipus.json", "okr_khipus.json"):
        for k in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(k["INVESTIGATOR_NUM"], k)
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    lines = [f"целей (подвесных с ≥ 3 дочерними, ≥ {MINS} значений ≥ {MINV}): {len(targets)}"]
    for kind in ("группы", "шнуры"):
        def run(d):
            out = []
            for k, o, v in targets:
                vv = [x + d if x >= MINV else x for x in v]
                for y, ch in chains.items():
                    if y == k or mus(y) == mus(k):
                        continue
                    s, at = score(vv, ch[kind])
                    if s >= MINS:
                        out.append((s, k, o, v, y, at))
            return out
        real = run(0)
        nulls = [run(d) for d in (-100, -70, -40, -20, -10, 10, 20, 40, 70, 100)]
        for s in range(MINS, 6):
            r = sum(1 for x in real if x[0] >= s)
            n = [sum(1 for x in nl if x[0] >= s) for nl in nulls]
            lines.append(f"[{kind}] счёт ≥ {s}: реально {r}, фон {sum(n) / len(n):.1f} (макс {max(n)})")
        for s, k, o, v, y, at in sorted(real, key=lambda x: -x[0])[:25]:
            seq = chains[y][kind]
            al = [seq[i + at] if 0 <= i + at < len(seq) else None for i in range(len(v))]
            lines.append(f"   {s}  {k} шнур {o} дочерние {v}  ~  {y} {kind} {al}  | "
                         f"{meta.get(k, {}).get('PROVENANCE')} / {meta.get(y, {}).get('PROVENANCE')}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
