"""«Почерк архива»: сходство кипу по цветовым узорам групп.

Узор группы — кортеж цветов её подвесных (группы ≥ 3 шнуров). Сходство двух кипу — доля общих
узоров (Жаккар по множествам). Проверка: пары кипу одного места (provenance известна) против
пар разных мест — AUC; отдельно внутри записей одного исследователя (UR/AS/HP), чтобы не мерить
только привычки записи цвета. Затем для кипу наших систем — ближайшие по почерку кипу.
Дубли одной вещи (один музейный номер) исключены. Вывод: extracted/housestyle.txt.
"""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/housestyle.txt"
KEY = ["UR1143", "UR1149", "UR1179", "UR1175", "UR233", "UR232", "UR1118", "UR218", "AS125", "AS038", "UR122"]


def load():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    P = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        pats = set()
        for _, g in itertools.groupby(rs, key=lambda r: r["group"]):
            cols = tuple(r["color"] for r in g)
            if len(cols) >= 3 and all(cols) and len(set(cols)) >= 2:
                pats.add(cols)
        if pats:
            P[k] = pats
    return P


def jac(a, b):
    return len(a & b) / len(a | b)


def auc(pos, neg):
    s = 0.0
    for x in pos:
        for y in neg:
            s += (x > y) + 0.5 * (x == y)
    return s / (len(pos) * len(neg))


def main():
    P = load()
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    prov = {}
    for k in P:
        p = str(meta.get(k, {}).get("PROVENANCE") or "").strip().strip('"').lower()
        prov[k] = "" if p in ("", "unknown", "none", "peru", "unknown provenance") else p
    mus = {k: str(meta.get(k, {}).get("MUSEUM_NUM") or k).replace(" ", "").upper() for k in P}
    rec = {k: k[:2] for k in P}
    keys = sorted(P)
    same, diff, same_r, diff_r = [], [], [], []
    for x, y in itertools.combinations(keys, 2):
        if mus[x] == mus[y] or not prov[x] or not prov[y]:
            continue
        s = jac(P[x], P[y])
        (same if prov[x] == prov[y] else diff).append(s)
        if rec[x] == rec[y]:
            (same_r if prov[x] == prov[y] else diff_r).append(s)
    lines = [f"кипу с узорами: {len(P)}; пар одного места {len(same)}, разных {len(diff)}",
             f"AUC (одно место > разные места): {auc(same, diff):.3f}; средние {sum(same) / len(same):.4f} против {sum(diff) / len(diff):.4f}",
             f"внутри одного исследователя: AUC {auc(same_r, diff_r):.3f} (пар {len(same_r)} / {len(diff_r)})",
             f"доля пар с общим узором: одно место {sum(1 for s in same if s > 0) / len(same):.1%}, разные {sum(1 for s in diff if s > 0) / len(diff):.1%}",
             "", "ближайшие по почерку к кипу наших систем:"]
    for k in KEY:
        if k not in P:
            continue
        near = sorted(((jac(P[k], P[y]), y) for y in keys if y != k and mus[y] != mus[k]), reverse=True)[:6]
        lines.append(f"  {k:8} ({prov[k] or '?'}): " + ", ".join(f"{y} {s:.2f} [{prov[y][:14] or '?'}]" for s, y in near if s > 0))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
