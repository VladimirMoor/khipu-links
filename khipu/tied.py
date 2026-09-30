"""Физически связанные кипу: связаны ли и числами?

Пары из заметок OKR («tied», «attached», «spliced», «joined», «bundle» …). Для каждой пары —
общие величины (подвесные, дочерние, суммы групп, окна 2–3 групп, итог; не круглые, ≥ MINV;
pachanet.quantities) — реально и при сдвиге одной стороны на d = ±1…±20. Сравнение со случайными
несвязанными парами кипу (того же общего числа шнуров ±30%). Вывод: extracted/tied.txt.
"""
import csv
import random
from collections import defaultdict
from pathlib import Path

import pachanet

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/tied.txt"
MINV = 100
PAIRS = [("UR200", "UR201"), ("UR232", "UR233"), ("AS026A", "AS026B"), ("UR267A", "UR267B"),
         ("UR255", "UR256"), ("UR273A", "UR273B"), ("UR274A", "UR274B"), ("UR264", "UR265"),
         ("UR259", "UR260"), ("JC002", "JC003"), ("JC004", "JC005"), ("JC011", "JC012"),
         ("JC011", "JC013"), ("JC012", "JC013"), ("UR213", "UR214"), ("UR214", "UR215"),
         ("UR227", "UR228"), ("UR243", "UR244"), ("UR282", "UR283"), ("UR210", "UR211"),
         ("UR116A", "UR116B"), ("UR117A", "UR117B"), ("UR117B", "UR117C"), ("UR117C", "UR117D"),
         ("UR056A", "UR056B"), ("UR056B", "UR056C"), ("UR131A", "UR131B"), ("UR131B", "UR131C"),
         ("UR023", "UR024"), ("UR024", "UR029"), ("UR023", "UR057"), ("UR027", "UR028"),
         ("UR032", "UR033"), ("AS093", "AS094"), ("AS127", "AS128"), ("AS207A", "AS207B"),
         ("AS207A", "AS207C"), ("AS101 - Part 1", "AS101 - Part 2"), ("AS35A", "AS35B"),
         ("AS35B", "AS035C"), ("AS035C", "AS035D"), ("AS35B", "AS035D"), ("UR053A", "UR053B"),
         ("UR053B", "UR053C"), ("UR053C", "UR053D"), ("UR053D", "UR053E"), ("UR106", "UR107"),
         ("UR1106", "UR1107")]


def main():
    rows = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        rows[r["inv_num"]].append(r)
    pachanet.MINV = MINV
    Q, idx = {}, {}
    for k, R in rows.items():
        q = [(v, l) for v, l in pachanet.quantities(R) if v % 10]
        Q[k] = q
        idx[k] = defaultdict(list)
        for v, l in q:
            idx[k][v].append(l)
    size = {k: sum(1 for r in R if r["parent_id"] == "") for k, R in rows.items()}

    def common(x, y, d=0):
        return sorted({v for v in idx[x] if v + d in idx[y]})

    lines = [f"пара: общих величин (не круглых, ≥ {MINV}) / фон (сдвиг ±1…±20, среднее) / примеры"]
    tot_r = tot_n = 0
    pairs = [(x, y) for x, y in PAIRS if x in idx and y in idx]
    for x, y in pairs:
        r = common(x, y)
        n = sum(len(common(x, y, d)) for d in range(-20, 21) if d) / 40
        tot_r += len(r)
        tot_n += n
        mark = "  <==" if len(r) >= 3 and len(r) > 3 * max(n, 0.3) else ""
        ex = [(v, idx[x][v][:1], idx[y][v][:1]) for v in r[-4:]]
        lines.append(f"  {x:>14} ~ {y:<14} {len(r):3} / {n:5.2f}  {ex}{mark}")
    lines.append(f"итого по {len(pairs)} связанным парам: {tot_r} против фона {tot_n:.1f}")
    # случайные несвязанные пары того же размера
    rnd = random.Random(1)
    keys = [k for k in idx if size.get(k)]
    tied = {frozenset(p) for p in pairs}
    rs = []
    for _ in range(20):
        t = 0
        for x, y in pairs:
            cand = [k for k in keys if abs(size[k] - size[y]) <= 0.3 * size[y] and k not in (x, y)
                    and frozenset((x, k)) not in tied]
            t += len(common(x, rnd.choice(cand))) if cand else 0
        rs.append(t)
    lines.append(f"случайные несвязанные пары (тот же первый кипу, второй того же размера): "
                 f"{sum(rs) / len(rs):.1f} (макс {max(rs)})")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
