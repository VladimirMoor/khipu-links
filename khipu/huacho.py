"""AS175 (Пачакамак, VA42518) и сращённая пара UR233 + UR232 (Уачо, VA63038b).

Для каждой группы UR233 и UR232 ищем группу AS175 (45 групп × 5 подвесных), с которой она
совпадает лучше всего, выбрасывая у группы Уачо одну позицию (обычно третью, пустую).
Счёт — число позиций, равных точно; фон — лучший счёт по тем же группам AS175, но с
циклически сдвинутыми позициями группы Уачо. Вывод: extracted/huacho.txt.
"""
import csv
import itertools
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/huacho.txt"


def groups(k, rows):
    rs = sorted((r for r in rows[k] if r["parent_id"] == ""), key=lambda r: int(r["order"]))
    subs = defaultdict(list)
    for r in rows[k]:
        if r["parent_id"]:
            subs[r["parent_id"]].append(int(r["value"]))
    out = []
    for _, g in itertools.groupby(rs, key=lambda r: r["group"]):
        g = list(g)
        out.append(([int(r["value"]) for r in g], [sum(subs[r["cord_id"]]) for r in g],
                    [r["color"] for r in g]))
    return out


def score(a, b):
    """Лучшее число точных совпадений a (5 позиций) с b после выброса одной позиции b."""
    best = (0, -1)
    for i in range(len(b)) if len(b) == len(a) + 1 else [None]:
        bb = b if i is None else b[:i] + b[i + 1:]
        if len(bb) != len(a):
            continue
        s = sum(1 for x, y in zip(a, bb) if x == y and x > 0)
        best = max(best, (s, -1 if i is None else i + 1))
    return best


def main():
    rows = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/kfg_cords.csv")):
        if r["inv_num"] in ("UR1175", "UR233", "UR232"):
            rows[r["inv_num"]].append(r)
    A = groups("UR1175", rows)
    lines = [f"AS175: {len(A)} групп; части по Ашерам: 1 = г1–21, 2 = г22–24, 3 = г25–45", ""]
    for k in ("UR233", "UR232"):
        B = groups(k, rows)
        lines.append(f"{k}: {len(B)} групп")
        tot = bgtot = 0
        for j, (b, bs, bc) in enumerate(B, 1):
            res = sorted(((score(a, b), i) for i, (a, _, _) in enumerate(A, 1)), reverse=True)
            (s, drop), i = res[0]
            bg = max((score(a, b[r:] + b[:r])[0] for a, _, _ in A for r in range(1, len(b)) if len(b) > 1), default=0)
            tot += s
            bgtot += bg
            mark = "  <==" if s >= 3 and s > bg else ""
            lines.append(f"  г{j:<3} {str(b):32} дочерние {str(bs):22} ~ AS175 г{i:<3} {str(A[i-1][0]):28} "
                         f"точно {s} (выброшена поз. {drop}; фон {bg}){mark}")
        lines.append(f"  итого точных совпадений {tot}, фон {bgtot}")
        lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()


def diagonal(A, B, big=10):
    """Сумма точных совпадений значений ≥ big по «диагоналям» (группа Уачо j ~ группа AS175 j + c)."""
    def s(a, b):
        best = 0
        for i in range(len(b)) if len(b) == len(a) + 1 else [None]:
            bb = b if i is None else b[:i] + b[i + 1:]
            if len(bb) == len(a):
                best = max(best, sum(1 for x, y in zip(a, bb) if x == y and x >= big))
        return best
    return {c: sum(s(A[j + c][0], B[j][0]) for j in range(len(B)) if 0 <= j + c < len(A))
            for c in range(-len(B) + 1, len(A))}


def diag_report():
    rows = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/kfg_cords.csv")):
        if r["inv_num"] in ("UR1175", "UR233", "UR232"):
            rows[r["inv_num"]].append(r)
    A = groups("UR1175", rows)
    lines = ["Диагонали (совпадения значений ≥ 10; группа Уачо j ~ AS175 j + c):"]
    for k in ("UR233", "UR232"):
        d = diagonal(A, groups(k, rows))
        best = max(d, key=d.get)
        others = [v for c, v in d.items() if c != best]
        m = sum(others) / len(others)
        sd = (sum((v - m) ** 2 for v in others) / len(others)) ** 0.5
        lines.append(f"  {k}: лучший сдвиг c = {best:+d}, совпадений {d[best]}; прочие сдвиги "
                     f"{m:.1f} ± {sd:.1f}, максимум {max(others)}; z = {(d[best] - m) / sd:.1f}")
    return lines


if __name__ == "__main__":
    L = diag_report()
    with open(OUT, "a") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
