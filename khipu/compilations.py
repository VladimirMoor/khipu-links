"""Кипу-«сборники»: кипу X, в котором есть участки из двух и более других кипу (разные музейные номера).

Участок — 4 подряд идущих шнура (прямо или обратно), из них ≥ 2 некруглых значения ≥ 10 и ≥ 1 значение ≥ 20.
Индекс по таким четвёркам. Для каждого X — источники, с которыми он делит ≥ 2 разные четвёрки. Повторные записи
одного предмета (≥ 50% шнуров X в общих четвёрках с одним кипу при совпадающем числе шнуров ±10%) отмечаются.
Фон — те же значения X, сдвинутые на +1 (общих четвёрок должно почти не быть). Вывод: extracted/compilations.txt.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/compilations.txt"


def grams(v):
    out = set()
    for seq in (v, v[::-1]):
        for i in range(len(seq) - 3):
            w = tuple(seq[i:i + 4])
            if sum(x >= 10 and x % 10 > 0 for x in w) >= 2 and max(w) >= 20:
                out.add(w)
    return out


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper()
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    val = {k: [int(r["value"]) for r in sorted(v, key=lambda r: int(r["order"]))] for k, v in by.items()}
    G = {k: grams(v) for k, v in val.items()}
    idx = defaultdict(set)
    for k, g in G.items():
        for w in g:
            idx[w].add(k)
    lines = []
    for X in sorted(val):
        src = defaultdict(set)
        for w in G[X]:
            for Y in idx[w]:
                if Y != X and mus(Y) != mus(X):
                    src[Y].add(w)
        src = {Y: s for Y, s in src.items() if len(s) >= 2}
        dup = {Y for Y, s in src.items() if len(s) >= 0.5 * max(1, len(G[X])) and abs(len(val[Y]) - len(val[X])) <= 0.1 * len(val[X])}
        real = {Y: s for Y, s in src.items() if Y not in dup}
        if len(real) >= 2:
            shifted = grams([x + 1 if x else x for x in val[X]])
            null = sum(1 for w in shifted for Y in idx[w] if Y != X)
            lines.append(f"{X} ({len(val[X])} подв., {meta.get(X, {}).get('MUSEUM_NUM')}, {meta.get(X, {}).get('PROVENANCE')}): "
                         + "; ".join(f"{Y} {len(s)}" for Y, s in sorted(real.items(), key=lambda t: -len(t[1])))
                         + (f" | повторные записи: {sorted(dup)}" if dup else "") + f" | фон {null}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
