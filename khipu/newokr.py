"""Кипу, добавленные в OKR после 2017 г. (папки data/KH*), → строки формата extracted/*_cords.csv.
Результат: extracted/plus_cords.csv (+ plus_khipus.json) = KFG (678 кипу) + новые кипу OKR.

Форматы: шаблон OKR (лист pendant_cords: cord «1», «1s1», …; кластеры в primary_cord) и
шаблон KFG (лист Cords: p1, p1s1, …; кластеры текстом «group of N pendants (a-b)»).
"""
import csv
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xlsx import read  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/open-khipu-repository/data"
FIELDS = ["khipu_id", "okr_num", "inv_num", "cord_id", "parent_id", "level", "order", "sib_ordinal",
          "group", "value", "n_knots", "color", "attachment", "twist", "length", "termination"]


def num(s):
    try:
        return int(round(float(s)))
    except (TypeError, ValueError):
        return 0


def parse_okr_template(sh):
    groups = []
    for r in sh["primary_cord"]:
        if r and r[0].strip().isdigit() and len(r) > 6 and r[5].strip().isdigit() and r[6].strip().isdigit():
            groups.append((int(r[0]), int(r[5]), int(r[6])))
    cords = []
    for r in sh["pendant_cords"][1:]:
        if not r or not r[0].strip():
            continue
        name = r[0].strip()
        if not re.fullmatch(r"\d+(s\d+)*", name):
            continue
        parts = (r[1] if len(r) > 1 else "").split("/")
        cords.append({"name": name, "value": num(r[6]) if len(r) > 6 else 0,
                      "color": r[5] if len(r) > 5 else "", "att": parts[-1] if len(parts) >= 3 else "",
                      "twist": parts[1] if len(parts) >= 2 else "", "length": re.sub(r"[A-Z]+$", "", r[3]) if len(r) > 3 else "",
                      "term": (re.findall(r"[A-Z]+$", r[3]) or [""])[0] if len(r) > 3 else "",
                      "knots": r[2] if len(r) > 2 else ""})
    return cords, groups


def parse_kfg_template(sh):
    groups = []
    for i, r in enumerate(sh.get("Clusters", [])):
        m = re.search(r"group of (\d+) pendants \((\d+)-(\d+)\)", " ".join(r))
        if m:
            groups.append((len(groups) + 1, int(m.group(2)), int(m.group(3))))
    rows = sh["Cords"]
    hdr = rows[0]
    ix = {h: i for i, h in enumerate(hdr)}
    cords = []
    for r in rows[1:]:
        if not r or not r[0].strip().startswith("p"):
            continue
        name = r[0].strip()[1:]
        if not re.fullmatch(r"\d+(s\d+)*", name):
            continue
        g = lambda k: r[ix[k]] if k in ix and ix[k] < len(r) else ""
        cords.append({"name": name, "value": num(g("Value")), "color": g("Color"), "att": g("Attachment"),
                      "twist": g("Twist"), "length": g("Length"), "term": g("Termination"), "knots": g("Knots")})
    return cords, groups


def to_rows(khipu_id, okr, inv, cords, groups):
    out, order = [], 0
    ids = {}
    for c in cords:
        parts = c["name"].split("s")
        cid = f"{khipu_id}-{c['name']}"
        ids[c["name"]] = cid
        parent = "" if len(parts) == 1 else f"{khipu_id}-{'s'.join(parts[:-1])}"
        top = int(parts[0])
        grp = next((o for o, a, b in groups if a <= top <= b), "")
        order += 1
        out.append({"khipu_id": khipu_id, "okr_num": okr, "inv_num": inv, "cord_id": cid, "parent_id": parent,
                    "level": len(parts), "order": order, "sib_ordinal": parts[-1], "group": grp if len(parts) == 1 else "",
                    "value": c["value"], "n_knots": 1 if c["knots"].strip() else 0, "color": c["color"],
                    "attachment": c["att"], "twist": c["twist"], "length": c["length"], "termination": c["term"]})
    return out


def main():
    base = list(csv.DictReader(open(ROOT / "extracted/kfg_cords.csv")))
    meta = json.load(open(ROOT / "extracted/kfg_khipus.json"))
    known = {r["okr_num"] for r in base if r["okr_num"]}
    new_rows, new_meta = [], []
    for f in sorted(glob.glob(str(DATA / "KH*/*.xlsx"))):
        try:
            sh = read(f)
        except Exception as e:
            print("пропуск", f, e)
            continue
        if "pendant_cords" in sh:
            cords, groups = parse_okr_template(sh)
        elif "Cords" in sh:
            cords, groups = parse_kfg_template(sh)
        else:
            print("иной формат:", Path(f).name)
            continue
        if not cords:
            continue
        stem = Path(f).stem
        m = re.search(r"MNAAHP\.(\d\d)", stem) or re.search(r"khipu_(\d)", stem)
        folder = Path(f).parent.name
        inv = f"ENL{m.group(1)}" if "ENLAZADO" in stem else (f"BM{m.group(1)}" if "Am_1937" in stem else stem)
        kid = f"new-{folder}-{inv}"
        new_rows += to_rows(kid, "", inv, cords, groups)
        prov = {"ENL": "Khipus Enlazados MNAAHP RT-16905 (decomiso)", "BM": "British Museum Am1937,0213.84 (tied set)"}
        new_meta.append({"KHIPU_ID": kid, "OKR_NUM": "", "INVESTIGATOR_NUM": inv, "MUSEUM_NAME": folder,
                         "PROVENANCE": next((v for k, v in prov.items() if inv.startswith(k)), "OKR " + folder), "REGION": ""})
        print(f"{inv:22} {folder:12} подвесных {sum(1 for c in cords if 's' not in c['name']):3}, всего шнуров {len(cords):3}, групп {len(groups)}")
    with open(ROOT / "extracted/plus_cords.csv", "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=FIELDS)
        w.writeheader()
        for r in base:
            w.writerow({k: r.get(k, "") for k in FIELDS})
        for r in new_rows:
            w.writerow(r)
    json.dump(meta + new_meta, open(ROOT / "extracted/plus_khipus.json", "w"), ensure_ascii=False, indent=1)
    print(f"добавлено кипу: {len(new_meta)}, шнуров: {len(new_rows)}")


if __name__ == "__main__":
    main()
