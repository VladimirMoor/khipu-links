"""Базельские фрагменты IVc.366.03 (MM008–MM017; по Medrano 2023 — раскопаны у Уачо, куплены у A. Masarey в
1910 г., нашиты на полотно под руководством Норденшёльда в 1924 г.) против берлинских кипу Пачакамака UR212
(VA42508(A), запись Уртона) и UR1131 = AS131 (VA42510, запись Ашеров).

Для каждого фрагмента — совпадающие подряд участки (difflib, ≥ 3 шнуров, из них ≥ 2 значений ≥ 10) с UR212 и
UR1131 в прямом и обратном порядке; покрытие берлинских кипу; направление участков внутри фрагмента.
Фон — те же фрагменты против всех остальных кипу корпуса того же размера (≥ 100 подвесных).
Вывод: extracted/basel_huacho.txt.
"""
import csv
import difflib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/basel_huacho.txt"
FRAG = [f"MM{i:03d}" for i in range(8, 18)]
TARGETS = ("UR212", "UR1131")


def runs(q, w):
    out = []
    for d, ww in (("прямо", w), ("обратно", w[::-1])):
        for b in difflib.SequenceMatcher(None, q, ww, autojunk=False).get_matching_blocks():
            if b.size >= 3 and sum(x >= 10 for x in q[b.a:b.a + b.size]) >= 2:
                start = b.b if d == "прямо" else len(w) - b.b - b.size
                out.append((d, b.a + 1, start + 1, b.size))
    return out


def main():
    by = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    val = {k: [int(r["value"]) for r in sorted(v, key=lambda r: int(r["order"]))] for k, v in by.items()}
    lines, cov = [], {t: set() for t in TARGETS}
    for K in FRAG:
        parts = []
        for T in TARGETS:
            for d, a, s, n in runs(val[K], val[T]):
                parts.append(f"{T} {d}: шнуры {a}–{a + n - 1} = {s}–{s + n - 1} ({n})")
                cov[T].update(range(s, s + n))
        lines.append(f"{K} ({len(val[K])} подв.): " + ("; ".join(parts) if parts else "—"))
    for T in TARGETS:
        lines.append(f"{T}: покрыто {len(cov[T])} из {len(val[T])} подвесных")
    others = [k for k in val if len(val[k]) >= 100 and k not in TARGETS and not k.startswith("MM")]
    tot = lambda T: sum(n for K in FRAG for _, _, _, n in runs(val[K], val[T]))
    real = {T: tot(T) for T in TARGETS}
    null = sorted(tot(T) for T in others)
    lines.append(f"сумма совпавших шнуров: UR212 {real['UR212']}, UR1131 {real['UR1131']}; "
                 f"у {len(others)} других кипу ≥ 100 подв.: медиана {null[len(null) // 2]}, максимум {null[-1]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
