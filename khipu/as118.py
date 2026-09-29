"""AS118 (Пачакамак, VA42601) как связующее кипу: итоги групп AS125 и копия групп UR218.

Первая группа AS118 — пустой подвесной W:RG с пятью дочерними [2696, 13182, 14658, 11522,
8565]. Сравниваем их с цепочкой сумм групп каждого кипу корпуса (лучший сдвиг, допуск 1% и
0.5%); фон — те же числа, сдвинутые на d = ±100…±300. Вывод: extracted/as118.txt.
"""
import csv
import itertools
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus_cords.csv"
OUT = ROOT / "extracted/as118.txt"
SUBS = [2696, 13182, 14658, 11522, 8565]


def chains():
    by = defaultdict(list)
    for r in csv.DictReader(open(CORDS)):
        if r["parent_id"] == "":
            by[r["inv_num"]].append(r)
    S = {}
    for k, rs in by.items():
        rs.sort(key=lambda r: int(r["order"]))
        S[k] = [sum(int(r["value"]) for r in g) for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
    return S


def score(t, seq, tol):
    return max((sum(1 for i, x in enumerate(t) if 0 <= i + sh < len(seq) and abs(seq[i + sh] - x) <= tol * x)
                for sh in range(-len(t) + 1, len(seq))), default=0)


def main():
    S = chains()
    del S["UR1118"]
    lines = [f"дочерние AS118 г1: {SUBS}", f"AS125 суммы групп: {S['AS125']}; UR247 (та же вещь): {S['UR247']}"]
    for tol in (0.01, 0.005):
        res = Counter(score(SUBS, v, tol) for v in S.values())
        top = sorted(((score(SUBS, v, tol), k) for k, v in S.items()), reverse=True)[:4]
        lines.append(f"допуск {tol:.1%}: распределение лучших счетов по {len(S)} кипу {sorted(res.items())}; верх {top}")
    null = [sum(1 for v in S.values() if score([x + d for x in SUBS[1:]], v, 0.01) >= 3)
            for d in list(range(-300, -99, 20)) + list(range(100, 301, 20))]
    lines.append(f"фон (дочерние 2–5 + d, |d| ≥ 100): кипу со счётом ≥ 3 из 4 — {null}")
    lines.append("AS125 г4 = [3130, 3332, 2122] (Ашеры) / [31111, 3332, 2122] (Уртон); при 3111 сумма = "
                 f"{3111 + 3332 + 2122}")
    lines.append(f"AS125 г3 = [2220 (оборван), 4377, 1292, 1162, 2393]; для 11522 первый шнур = {11522 - 4377 - 1292 - 1162 - 2393}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
