"""Позиционное чтение кипу в стиле Уари: длинный узел = цифра, высота = разряд?

Для кипу с канутос/Уари (недесятичных) каждый подвесной читаем двумя способами:
  (a) «сумма узлов» — как в базе (длинный узел в n витков = n);
  (b) позиционно — кластеры сверху вниз = разряды от старшего к младшему; цифра кластера = число
      витков длинного узла, число простых узлов, 1 для восьмёрки; значение = Σ цифра · 10^разряд.
Проверка: сколько подвесных равны сумме 2–6 подряд идущих подвесных того же кипу (соседних слева
или справа) — «суммовые шнуры», как у инков. Фон — значение проверяемого шнура ± d (d = 1…10).
Контроль — инкские десятичные кипу тем же тестом. Вывод: extracted/wari.txt.
"""
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/open-khipu-repository/data/khipu.db"
OUT = ROOT / "extracted/wari.txt"
WARI = ["UR039", "UR050", "UR051", "UR052", "UR054", "UR055", "UR110", "UR112"]


def cords(db, inv):
    kid = db.execute("select KHIPU_ID from khipu_main where INVESTIGATOR_NUM = ?", (inv,)).fetchone()[0]
    rows = db.execute(
        "select c.CORD_ID, c.CORD_ORDINAL, kc.START_POS, k.TYPE_CODE, cast(k.NUM_TURNS as int), k.knot_value_type "
        "from cord c left join knot k on k.CORD_ID = c.CORD_ID left join knot_cluster kc on k.CLUSTER_ID = kc.CLUSTER_ID "
        "where c.KHIPU_ID = ? and c.CORD_LEVEL = 1 order by c.CORD_ORDINAL", (kid,)).fetchall()
    by = {}
    for cid, order, pos, t, n, v in rows:
        d = by.setdefault(cid, {"order": order, "cl": defaultdict(list)})
        if t:
            d["cl"][pos or 0].append((t, n or 0, v or 0))
    out = []
    for cid, d in sorted(by.items(), key=lambda kv: kv[1]["order"]):
        naive = sum(v for ks in d["cl"].values() for _, _, v in ks)
        digits = []
        for pos in sorted(d["cl"]):
            ks = d["cl"][pos]
            if any(t == "L" for t, _, _ in ks):
                digits.append(max(n for t, n, _ in ks if t == "L"))
            elif any(t == "E" for t, _, _ in ks):
                digits.append(1)
            else:
                digits.append(sum(1 for t, _, _ in ks if t == "S"))
        pos_val = sum(dg * 10 ** (len(digits) - 1 - i) for i, dg in enumerate(digits)) if digits else 0
        out.append((naive, pos_val, len(digits)))
    return out


def sums(vals, d=0):
    hits = 0
    for i, v in enumerate(vals):
        if v < 10:
            continue
        for k in range(2, 7):
            for lo, hi in ((i - k, i), (i + 1, i + 1 + k)):
                if lo >= 0 and hi <= len(vals) and sum(vals[lo:hi]) == v + d:
                    hits += 1
                    break
    return hits


def main():
    db = sqlite3.connect(DB)
    lines = ["кипу: суммовых шнуров (= сумме 2–6 соседних) при чтении «сумма узлов» / позиционном; фон ± d"]
    tot = {"a": [0, 0], "b": [0, 0]}
    for inv in WARI:
        cs = cords(db, inv)
        a = [c[0] for c in cs]
        b = [c[1] for c in cs]
        ra, rb = sums(a), sums(b)
        na = sum(sums(a, d) for d in range(-10, 11) if d) / 20
        nb = sum(sums(b, d) for d in range(-10, 11) if d) / 20
        tot["a"][0] += ra; tot["a"][1] += na
        tot["b"][0] += rb; tot["b"][1] += nb
        lines.append(f"  {inv:6} шнуров {len(cs):3}: сумма узлов {ra:3} (фон {na:5.2f}) | позиционно {rb:3} (фон {nb:5.2f})")
    lines.append(f"  всего Уари: сумма узлов {tot['a'][0]} (фон {tot['a'][1]:.1f}) | позиционно {tot['b'][0]} (фон {tot['b'][1]:.1f})")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
