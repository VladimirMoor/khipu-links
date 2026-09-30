"""Все кипу из Уачо / Уауры против всех кипу Пачакамака: совпадающие подряд участки шнуров.

Участок — ≥ 4 шнуров подряд, прямо или обратно (difflib), из них ≥ 2 некруглых значения ≥ 10. Оценка пары —
сумма длин участков. Фон — те же кипу Уачо против кипу других мест (не Пачакамак, не Уачо) того же размера.
Базельские фрагменты IVc.366.03 (MM008–MM017) считаются кипу из Уачо (Medrano 2022).
Вывод: extracted/huacho_pach.txt.
"""
import csv
import difflib
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/huacho_pach.txt"


def score(q, w):
    best = 0
    for ww in (w, w[::-1]):
        s = sum(b.size for b in difflib.SequenceMatcher(None, q, ww, autojunk=False).get_matching_blocks()
                if b.size >= 4 and sum(x >= 10 and x % 10 > 0 for x in q[b.a:b.a + b.size]) >= 2)
        best = max(best, s)
    return best


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    val = {k: [int(r["value"]) for r in sorted(v, key=lambda r: int(r["order"]))] for k, v in by.items()}
    prov = lambda k: str(meta.get(k, {}).get("PROVENANCE", ""))
    huacho = [k for k in val if ("uacho" in prov(k) or "uaura" in prov(k)
                                  or (k.startswith("MM") and str(meta.get(k, {}).get("MUSEUM_NUM")) == "IVc.366.03"))]
    pach = [k for k in val if "achacamac" in prov(k)]
    other = [k for k in val if k not in huacho and k not in pach and len(val[k]) >= 20]
    lines = [f"кипу Уачо/Уауры: {len(huacho)}; Пачакамака: {len(pach)}; прочих (≥ 20 подв.): {len(other)}"]
    for h in sorted(huacho):
        sp = sorted(((score(val[h], val[p]), p) for p in pach), reverse=True)
        so = sorted(score(val[h], val[o]) for o in other)
        top = [x for x in sp if x[0] > 0][:3]
        lines.append(f"  {h} ({len(val[h])} подв., {meta.get(h, {}).get('MUSEUM_NUM')}): Пачакамак {top}; "
                     f"прочие: макс {so[-1]}, 99% {so[int(0.99 * len(so))]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
