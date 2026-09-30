"""Крепление (recto/verso) в парах копий: противоположное ли оно, как отмечают Urton & Chu 2015 для Инкавази?

Сторона кипу — преобладающая (≥ 80% шнуров с известной стороной R/V). Пары — известные копии разных
предметов (не повторные записи). Фон — доля противоположных сторон у случайной пары однородных кипу корпуса.
Вывод: extracted/attach_copies.txt.
"""
import csv
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/attach_copies.txt"
PAIRS = [("UR267A", "UR255"), ("UR267B", "UR256"), ("UR266", "UR275"), ("UR273B", "UR274B"),
         ("UR270", "UR278"), ("UR053B", "UR053C"), ("MM015", "UR212"), ("UR1084", "HP055"),
         ("UR066", "UR067"), ("KH0049", "UR122")]


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)

    def side(k):
        c = Counter(r["attachment"] for r in by[k] if r["attachment"] in ("R", "V"))
        n = sum(c.values())
        if n < 5 or n < 0.6 * len(by[k]):
            return None
        s, m = c.most_common(1)[0]
        return s if m >= 0.8 * n else "смеш."

    S = Counter(side(k) for k in by)
    p0 = 2 * S["R"] * S["V"] / (S["R"] + S["V"]) ** 2
    lines, opp, n = [], 0, 0
    for a, b in PAIRS:
        sa, sb = side(a), side(b)
        if sa in ("R", "V") and sb in ("R", "V"):
            n += 1
            opp += sa != sb
        lines.append(f"  {a} {sa} ~ {b} {sb}")
    p = sum(comb(n, k) * p0 ** k * (1 - p0) ** (n - k) for k in range(opp, n + 1))
    lines.insert(0, f"противоположная сторона: {opp} из {n} пар копий; у случайной пары {p0:.2f}; "
                    f"односторонний p = {p:.2f}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
