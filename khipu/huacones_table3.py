"""Сверка нашей расшифровки бланков Уаконес-Вилькауаси (JC024–JC034) с таблицей 3 статьи
Barraza Lescano et al. 2022 (число подвесных, дочерних, узлов = кластеров, верхних шнуров и их узлов).

Соглашение таблицы: подвесные и узлы — без верхних шнуров; «узел» = кластер. Верхние шнуры в нашей
расшифровке помечены (T); у JC028 шнуры 1–2 (отдельная группа, крепление V) проверяются как верхние.
Вывод: extracted/huacones_table3.txt.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/huacones_table3.txt"
TABLE3 = {1: (4, 3, 9, 0, 0), 2: (5, 0, 5, 0, 0), 3: (7, 0, 4, 1, 1), 4: (7, 7, 14, 1, 3), 5: (5, 2, 16, 1, 2),
          6: (6, 4, 22, 2, 7), 7: (4, 6, 18, 0, 0), 8: (9, 3, 24, 0, 0), 9: (9, 2, 11, 0, 0),
          10: (5, 4, 11, 1, 0), 11: (2, 0, 0, 0, 0)}
EXTRA_TOP = {"JC028": {"1", "2"}}


def counts(R, k):
    cl = lambda r: len(re.findall(r"\d+\s*[sLE]", r["knots_raw"] or ""))
    top = {r["cord"] for r in R if not r["parent"] and "(T)" in r["cord"]} | EXTRA_TOP.get(k, set())
    intop = lambda r: r["cord"] in top or r["parent"] in top
    pend = [r for r in R if not r["parent"] and r["cord"] not in top]
    sub = [r for r in R if r["parent"] and r["parent"] not in top]
    return (len(pend), len(sub), sum(cl(r) for r in R if not intop(r)), len(top), sum(cl(r) for r in R if intop(r)))


def main():
    meta, rows = {}, []
    for f in ("A", "B"):
        meta.update({r["khipu"]: r for r in csv.DictReader(open(ROOT / f"extracted/huacones_{f}_meta.csv"))})
        rows += list(csv.DictReader(open(ROOT / f"extracted/huacones_{f}.csv")))
    C = {k: counts([r for r in rows if r["khipu"] == k], k) for k in meta}
    lines = ["бланк (инв.): наша расшифровка (подв., доч., узлы, верхн., узлы верхн.) → совпадающие строки таблицы 3"]
    for k in sorted(meta, key=lambda k: int(re.sub(r"\D", "", meta[k]["local_quipu_no"]))):
        q = int(re.sub(r"\D", "", meta[k]["local_quipu_no"]))
        near = [n for n, t in TABLE3.items() if sum(abs(a - b) for a, b in zip(C[k], t)) <= 1]
        lines.append(f"  Quipu {q} {k} ({meta[k]['inventory_no']}): {C[k]}; таблица №{q} {TABLE3[q]}; "
                     f"совпадает (±1) со строками {near}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
