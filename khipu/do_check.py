"""Проверка расшифровки UR297 по заметкам самого Уртона (бланк, с. 40–47): для каждой группы он выписал
«итог группы из 10 шнуров» и «итог сводного шнура». Сводный — обведённый шнур группы; итоги — со всеми дочерними.
Сравниваем с нашей расшифровкой. Вывод: extracted/do_check.txt.
"""
import csv
import glob
import itertools
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/do_check.txt"


def urton_notes():
    lines = [l.split(":", 1)[1].strip() for l in open(ROOT / "extracted/do_UR297_p39-47_meta.txt")
             if re.match(r"p(4[0-7])", l)]
    out, cur = {}, None
    for l in lines:
        m = re.match(r"^(?:cords\s*)?(\d+)\s*(?:-|->|–)\s*(\d+)$", l)
        if m:
            cur = int(m.group(1))
            out[cur] = {}
            continue
        m = re.match(r"^([\d,]+)\s*(?:\(broken\))?\s*[-=]\s*(.*)$", l)
        if m and cur is not None:
            v = int(m.group(1).replace(",", ""))
            out[cur]["S" if "summary" in m.group(2) else "T"] = v
    return out


def main():
    raw = {}
    for f in glob.glob(str(ROOT / "extracted/do_UR297_p*.csv")):
        for r in csv.DictReader(open(f)):
            raw[r["cord"].strip()] = r
    rows = [r for r in csv.DictReader(open(ROOT / "extracted/do_cords.csv")) if r["inv_num"] == "UR297"]
    kids = defaultdict(list)
    pend = []
    for r in rows:
        (kids[r["parent_id"]].append(r) if r["parent_id"] else pend.append(r))
    tree = lambda r: int(r["value"]) + sum(tree(c) for c in kids.get(r["cord_id"], []))
    pend.sort(key=lambda r: int(r["order"]))
    ours = {}
    for _, rr in itertools.groupby(pend, key=lambda r: r["group"]):
        rr = list(rr)
        circ = [r for r in rr if "ircle" in raw.get(r["cord_id"].split("_")[1], {}).get("notes", "")]
        if len(circ) == 1:
            ours[int(rr[0]["order"])] = {"S": tree(circ[0]), "T": sum(tree(r) for r in rr if r is not circ[0])}
    U = urton_notes()
    agree = n = 0
    lines = []
    for g in sorted(U):
        for key in ("T", "S"):
            if key in U[g] and g in ours:
                n += 1
                agree += U[g][key] == ours[g][key]
                if U[g][key] != ours[g][key]:
                    lines.append(f"  группа с {g}: {'итог группы' if key == 'T' else 'сводный'} — Уртон {U[g][key]}, мы {ours[g][key]}")
    eq = sum(1 for g in U if U[g].get("S") is not None and U[g].get("S") == U[g].get("T"))
    lines.insert(0, f"итогов у Уртона: {n}; совпадают с нашей расшифровкой: {agree}; групп, где сводный = итогу "
                    f"(по Уртону): {eq} из {len(U)}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
