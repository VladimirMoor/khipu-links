"""Сохраняют ли копии единицу счёта — группу? Для известных пар копий разных предметов: совпадающие участки
(difflib, ≥ 3 шнуров подряд, ≥ 2 значений ≥ 10; прямо или обратно) и их концы. Конец участка «на границе», если
он совпадает с началом/концом группы (допуск 1 шнур — пустые пограничные шнуры). Считаем долю концов на границе
в источнике и в копии и сравниваем с ожиданием при случайном положении участка той же длины внутри кипу
(перебор всех сдвигов). Вывод: extracted/unit_invariance.txt.
"""
import csv
import difflib
import itertools
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/unit_invariance.txt"
PAIRS = [("UR267A", "UR255"), ("UR267B", "UR256"), ("UR266", "UR275"), ("UR274B", "UR273B"), ("UR278", "UR270"),
         ("UR053C", "UR053B"), ("UR1175", "UR233"), ("UR1175", "UR232"), ("UR218", "UR1118"), ("KH0049", "UR122"),
         ("HP055", "UR1084"), ("UR066", "UR067"), ("UR1114", "UR1123"), ("AS215", "AS003"),
         ("UR212", "MM008"), ("UR212", "MM015"), ("UR212", "MM016"), ("UR1131", "MM008"), ("UR1131", "MM009"),
         ("UR1131", "MM015"), ("UR1131", "MM016")]


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    for k in by:
        by[k].sort(key=lambda r: int(r["order"]))

    def info(k):
        v = [int(r["value"]) for r in by[k]]
        b = set()
        i = 0
        for _, g in itertools.groupby(by[k], key=lambda r: r["group"]):
            n = len(list(g))
            b.update({i, i + n})          # boundaries as cut positions 0..len
            i += n
        return v, b

    def near(p, B):
        return any(abs(p - x) <= 1 for x in B)

    tot = obs = exp = 0.0
    lines = []
    for S, C in PAIRS:
        if S not in by or C not in by:
            continue
        vs, bs = info(S)
        vc, bc = info(C)
        o = e = n = 0
        for d, w in (("f", vs), ("r", vs[::-1])):
            B = bs if d == "f" else {len(vs) - x for x in bs}
            for m in difflib.SequenceMatcher(None, vc, w, autojunk=False).get_matching_blocks():
                if m.size < 3 or sum(x >= 10 for x in vc[m.a:m.a + m.size]) < 2:
                    continue
                for pos, Bset, L in ((m.a, bc, len(vc)), (m.a + m.size, bc, len(vc)),
                                     (m.b, B, len(w)), (m.b + m.size, B, len(w))):
                    n += 1
                    o += near(pos, Bset)
                    # expectation: fraction of cut positions near a boundary
                    e += sum(near(p, Bset) for p in range(L + 1)) / (L + 1)
        if n:
            lines.append(f"  {S} → {C}: концов {n}, на границе {o} (ожидание {e:.1f})")
            tot += n
            obs += o
            exp += e
    lines.insert(0, f"всего концов участков {tot:.0f}: на границе групп {obs:.0f}, ожидание {exp:.1f} "
                    f"(доля {obs / tot:.0%} против {exp / tot:.0%})")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
