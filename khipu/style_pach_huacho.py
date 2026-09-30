"""Похожи ли «пачакамакские» кипу Гретцера (Берлин) больше на кипу из Уачо, чем на кипу из музея святилища
Пачакамака (серия HP)?

Признаки кипу (≥ 15 подвесных, по возможности не зависящие от записывающего): lg медианы ненулевых значений,
доля нулей, ln средней длины группы, доля подвесных с дочерними, ln числа подвесных, доля значений ≥ 100.
Из набора Уачо исключены копии пачакамакских кипу (UR232, UR233, фрагменты IVc.366.03) и повторная запись UR083/KH0227.
1) Различимы ли HP и Уачо (скользящий контроль, ближайший центроид) против доли большего класса.
2) Для кипу Гретцера — ближе ли к центроиду Уачо, чем к HP. Вывод: extracted/style_pach_huacho.txt.
"""
import csv
import itertools
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/style_pach_huacho.txt"
COPIES = {"UR232", "UR233", "UR083", "KH0227"} | {f"MM{i:03d}" for i in range(8, 18)}


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    kids, by = defaultdict(int), defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        (kids.__setitem__(r["parent_id"], kids[r["parent_id"]] + 1) if r["parent_id"] else by[r["inv_num"]].append(r))

    def feats(k):
        rs = sorted(by[k], key=lambda r: int(r["order"]))
        v = [int(r["value"]) for r in rs]
        if len(v) < 15:
            return None
        gs = [len(list(g)) for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
        nz = [x for x in v if x > 0] or [1]
        return [math.log10(st.median(nz) + 1), sum(x == 0 for x in v) / len(v), math.log(st.mean(gs)),
                sum(1 for r in rs if kids[r["cord_id"]]) / len(v), math.log(len(v)), sum(x >= 100 for x in v) / len(v)]

    prov = lambda k: str(meta.get(k, {}).get("PROVENANCE", ""))
    mus = lambda k: str(meta.get(k, {}).get("MUSEUM_NAME", ""))
    F = {k: f for k in by if (f := feats(k))}
    HP = [k for k in F if k.startswith("HP") and "achacamac" in prov(k)]
    HU = [k for k in F if ("uacho" in prov(k) or "uaura" in prov(k)) and k not in COPIES]
    GR = [k for k in F if "achacamac" in prov(k) and "Berlin" in mus(k)]
    pool = [F[k] for k in HP + HU + GR]
    mu = [st.mean(c) for c in zip(*pool)]
    sd = [st.pstdev(c) or 1 for c in zip(*pool)]
    Z = {k: [(x - m) / s for x, m, s in zip(F[k], mu, sd)] for k in HP + HU + GR}
    cen = lambda ks: [st.mean(c) for c in zip(*[Z[k] for k in ks])]
    ok = sum(("HP" if math.dist(Z[k], cen([x for x in HP if x != k])) < math.dist(Z[k], cen([x for x in HU if x != k]))
              else "HU") == ("HP" if k in HP else "HU") for k in HP + HU)
    base = max(len(HP), len(HU)) / (len(HP) + len(HU))
    cHP, cHU = cen(HP), cen(HU)
    lines = [f"HP (святилище): {len(HP)}; Уачо без копий: {len(HU)} {sorted(HU)}; Гретцер (Берлин): {len(GR)}",
             f"скользящий контроль HP vs Уачо: {ok} из {len(HP) + len(HU)} (доля большего класса {base:.0%})"]
    for k in ("UR212", "UR1131", "UR1175"):
        lines.append(f"  {k}: до HP {math.dist(Z[k], cHP):.2f}, до Уачо {math.dist(Z[k], cHU):.2f}")
    lines.append(f"кипу Гретцера ближе к Уачо: {sum(math.dist(Z[k], cHU) < math.dist(Z[k], cHP) for k in GR)} из {len(GR)}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
