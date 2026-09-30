"""Расшифровка бланков UR297 и UR298 (Думбартон-Окс; OKR data/KH0674_0675) → формат extracted/*_cords.csv.

Источники: extracted/do_UR29x_p*.csv (строки шнуров) и do_UR29x_p*_meta.txt (строки «group of N pendants (a-b)»).
Группа подвесного — по диапазону (a-b) из мета-файлов; иначе — одна общая группа. Дочерние — по метке (1s1 → 1).
Выход: extracted/do_cords.csv (только эти два кипу) и extracted/plus_do_cords.csv (корпус plus + они).
"""
import csv
import glob
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["khipu_id", "okr_num", "inv_num", "cord_id", "parent_id", "level", "order", "sib_ordinal",
          "group", "value", "n_knots", "color", "attachment", "twist", "length", "termination"]
META = {"UR297": ("KH0675", 9000297), "UR298": ("KH0674", 9000298)}


def ranges(k):
    out = []
    for f in sorted(glob.glob(str(ROOT / f"extracted/do_{k}_p*_meta.txt"))):
        for line in open(f):
            if "cm" not in line:
                continue
            for a, b in re.findall(r"\((\d+)\s*[-–]\s*(\d+)\)", line):   # целые диапазоны; «(0.0-27.0 cm)» не подходит
                out.append((int(a), int(b)))
    return sorted(set(out))


def main():
    rows_out = []
    for k, (okr, kid) in META.items():
        rs = []
        for f in sorted(glob.glob(str(ROOT / f"extracted/do_{k}_p*.csv"))):
            if f.endswith("_meta.txt"):
                continue
            rs += list(csv.DictReader(open(f)))
        R = ranges(k)
        grp = lambda n: next((i + 1 for i, (a, b) in enumerate(R) if a <= n <= b), 0)
        seen = {}
        for r in rs:
            lab = r["cord"].strip().replace(" ", "")
            m = re.match(r"^[Tt]?(\d+)", lab)
            if not m:
                continue
            pend = int(m.group(1))
            level = lab.lower().count("s") + 1
            parent = r["parent"].strip().replace(" ", "")
            raw = r["value"].strip().replace(",", "")
            try:
                v = sum(int(float(x)) for x in raw.split("+")) if raw not in ("", "-") else 0   # «2+10» → 12
            except ValueError:
                v = 0
            cid = f"{kid}_{lab}"
            if cid in seen:
                continue
            seen[cid] = 1
            att = (r["spin_ply_attach"].split("/") + ["", "", ""])[2].strip().upper()[:1] or "U"
            rows_out.append({"khipu_id": kid, "okr_num": okr, "inv_num": k, "cord_id": cid,
                             "parent_id": f"{kid}_{parent}" if level > 1 and parent else "",
                             "level": level, "order": pend * 1000 + len(seen) if level > 1 else pend,
                             "sib_ordinal": "", "group": grp(pend) if level == 1 else "",
                             "value": v, "n_knots": "", "color": r["color"].strip(), "attachment": att,
                             "twist": "", "length": r["length_cm"].strip().rstrip("kKbBuU"),
                             "termination": (re.findall(r"[kKbBuU]$", r["length_cm"].strip()) or [""])[0].upper()})
        print(k, "строк", len([x for x in rows_out if x["inv_num"] == k]), "групп по мета", len(R))
    w = csv.DictWriter(open(ROOT / "extracted/do_cords.csv", "w"), fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows_out)
    base = list(csv.DictReader(open(ROOT / "extracted/plus_cords.csv")))
    w = csv.DictWriter(open(ROOT / "extracted/plus_do_cords.csv", "w"), fieldnames=FIELDS)
    w.writeheader()
    w.writerows(base + rows_out)


if __name__ == "__main__":
    main()
