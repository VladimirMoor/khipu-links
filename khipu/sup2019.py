"""Сверка OKR с приложением Urton & Chu 2019 (Supplemental Table 1: значения по шнурам на четырёх кипу).

Колонки приложения: UR267B, UR267A, UR275, UR268 (значение — второй столбец каждой тройки). Последовательность
значений каждого кипу выравниваем (difflib) с последовательностью подвесных OKR; считаем совпавшие значения
и перечисляем расхождения внутри выровненных участков. Вывод: extracted/sup2019.txt.
"""
import csv
import difflib
import re
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "sources/related/UrtonChu2019_sup001.docx"
OUT = ROOT / "extracted/sup2019.txt"
COLS = {"UR267B": 1, "UR267A": 4, "UR275": 7, "UR268": 10}


def table():
    x = zipfile.ZipFile(DOCX).read("word/document.xml").decode()
    rows = []
    for tr in re.findall(r"<w:tr[ >].*?</w:tr>", x, flags=re.S):
        rows.append(["".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", tc)).strip()
                     for tc in re.findall(r"<w:tc>.*?</w:tc>", tr, flags=re.S)])
    seq = defaultdict(list)
    for r in rows:
        if len(r) != 13 or not r[0].isdigit() and not any(r[c - 1].isdigit() for c in COLS.values()):
            continue
        for k, c in COLS.items():
            v = r[c].replace("[", "").replace("]", "").replace(",", "")
            if r[c - 1].isdigit() and re.fullmatch(r"\d+", v):
                seq[k].append(int(v))
    return seq


def main():
    sup = table()
    okr = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "" and r["inv_num"] in COLS:
            okr[r["inv_num"]].append(r)
    lines = []
    for k in COLS:
        o = [int(r["value"]) for r in sorted(okr[k], key=lambda r: int(r["order"]))]
        s = sup[k]
        sm = difflib.SequenceMatcher(None, s, o, autojunk=False)
        m = sum(b.size for b in sm.get_matching_blocks())
        diffs = [(s[i1:i2], o[j1:j2]) for t, i1, i2, j1, j2 in sm.get_opcodes() if t == "replace" and i2 - i1 <= 2]
        lines.append(f"{k}: в приложении {len(s)} значений, в OKR {len(o)} подвесных; совпало подряд {m} "
                     f"({m / len(s):.0%} приложения); замены: {diffs[:12]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
