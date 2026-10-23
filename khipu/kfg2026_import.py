"""KFG, обновление 10.10.2026 (Excel, data/kfg_2026/xlsx/) → extracted/kfg2026_cords.csv в формате plus_cords.csv,
и сравнение с прежним корпусом (extracted/plus_cords.csv): новые кипу, изменённые значения подвесных.

Имя шнура: pN — подвесной номер N, pNsM… — дочерний; группа подвесного — из листа CordGroups («group of k pendants (a-b)»
или одиночный «(n)»). Код кипу в нашем корпусе — по atlas/curated/kfg_names.csv (KFG → наш номер), иначе код KFG.
Вывод: extracted/kfg2026_cords.csv, extracted/kfg2026_meta.json, extracted/kfg2026_diff.txt.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
from xlsx_read import sheets  # noqa: E402

SRC = ROOT / "data/kfg_2026/xlsx"
OUT = ROOT / "extracted/kfg2026_cords.csv"
FIELDS = ["khipu_id", "okr_num", "inv_num", "cord_id", "parent_id", "level", "order", "sib_ordinal", "group", "value",
          "n_knots", "color", "attachment", "twist", "length", "termination"]


def kv(rows):
    d = {}
    for r in rows:
        if r and ":" in r[0]:
            k, v = r[0].split(":", 1)
            d[k.strip()] = v.strip()
    return d


def main():
    ours = {}
    for r in csv.DictReader(open(ROOT / "atlas/curated/kfg_names.csv")):
        if r["khipu"]:
            ours[r["kfg"]] = r["khipu"]
    okr2inv, have = {}, set()
    for r in csv.DictReader(open(ROOT / "extracted/plus_do_cords.csv")):
        have.add(r["inv_num"])
        if r["okr_num"]:
            okr2inv.setdefault(r["okr_num"], r["inv_num"])
    norm = lambda x: re.sub(r"[^0-9A-Z]", "", x.upper())
    hn = {norm(h): h for h in have}
    rows, meta, bad = [], {}, []
    for f in sorted(SRC.glob("*.xlsx")):
        try:
            S = sheets(f)
        except Exception as e:
            bad.append(f"{f.name}: {e}")
            continue
        info = kv(S.get("Khipu", []))
        name = info.get("Name", f.stem)
        al = [norm(x) for x in re.split(r"[,;]", info.get("Aliases", "")) if x.strip()]
        # investigator numbers (UR, AS…) first: KH numbers of khipus added after 2017 may differ between sources
        # investigator numbers (UR, AS…) listed by the KFG itself come first: the KFG renumbered some khipus in 2026
        # (KH0197 is now AS180), so the old catalogue mapping by KH code can point at the wrong object
        inv = next((hn[x] for x in al if x in hn and not x.startswith("KH")), None) or ours.get(name) or okr2inv.get(name) or name
        gr = {}
        gi = 0
        for r in S.get("CordGroups", [])[1:]:
            if not r or not r[0]:
                continue
            m = re.search(r"\((\d+)(?:-(\d+))?\)", r[0])
            if not m:
                continue
            gi += 1
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
            for n in range(a, b + 1):
                gr[n] = gi
        hdr = S["Cords"][0]
        col = {h: i for i, h in enumerate(hdr)}
        sib = defaultdict(int)
        for r in S["Cords"][1:]:
            if not r or not r[0] or not re.fullmatch(r"p\d+(s\d+)*", r[0]):
                continue
            get = lambda h: r[col[h]] if col.get(h) is not None and col[h] < len(r) else ""
            cname = r[0]
            parts = re.findall(r"[ps](\d+)", cname)
            pn = int(parts[0])
            parent = "" if len(parts) == 1 else f"{name}:{cname[:cname.rindex('s')]}"
            sib[parent] += 1
            try:
                val = int(float(get("Value") or 0))
            except ValueError:
                val = 0
            knots = get("Knots")
            rows.append({"khipu_id": "", "okr_num": name, "inv_num": inv, "cord_id": f"{name}:{cname}", "parent_id": parent,
                         "level": len(parts), "order": pn, "sib_ordinal": sib[parent], "group": gr.get(pn, 0), "value": val,
                         "n_knots": len([k for k in knots.split(";") if k.strip()]) if knots else 0,
                         "color": get("Color"), "attachment": get("Attachment"), "twist": get("Twist"),
                         "length": get("Length"), "termination": get("Termination")})
        meta[inv] = {"kfg": name, "aliases": info.get("Aliases", ""), "museum": info.get("Museum Name", ""),
                     "museum_num": info.get("Museum Number", ""), "provenance": info.get("Provenance", ""),
                     "excel_date": info.get("Excel Write Date", ""), "changes": max(0, len(S.get("ChangeLog", [])) - 1)}
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    json.dump(meta, open(ROOT / "extracted/kfg2026_meta.json", "w"), ensure_ascii=False, indent=1)
    # compare with the corpus used so far
    old = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "":
            old[r["inv_num"]].append((int(r["order"]), int(r["value"])))
    new = defaultdict(list)
    for r in rows:
        if r["parent_id"] == "":
            new[r["inv_num"]].append((r["order"], r["value"]))
    lines = [f"файлов: {len(list(SRC.glob('*.xlsx')))}; кипу прочитано: {len(meta)}; шнуров: {len(rows)}; ошибок чтения: {len(bad)}"]
    lines += [f"  ошибка: {b}" for b in bad]
    fresh = sorted(k for k in new if k not in old)
    lines.append(f"новые кипу (нет в прежнем корпусе): {len(fresh)}: " + ", ".join(f"{k} ({len(new[k])} подв.)" for k in fresh))
    ch = []
    for k in sorted(set(new) & set(old)):
        a = [v for _, v in sorted(old[k])]
        b = [v for _, v in sorted(new[k])]
        if a != b and a[::-1] != b:
            d1 = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            d2 = sum(1 for x, y in zip(a[::-1], b) if x != y) + abs(len(a) - len(b))
            ch.append((min(d1, d2), k, len(a), len(b), meta[k]["changes"], "обратный порядок" if d2 < d1 else ""))
    ch.sort(reverse=True)
    lines.append(f"кипу с изменёнными значениями подвесных: {len(ch)} из {len(set(new) & set(old))}")
    rev = sum(1 for k in set(new) & set(old) if [v for _, v in sorted(old[k])][::-1] == [v for _, v in sorted(new[k])] != [v for _, v in sorted(old[k])])
    lines.append(f"  (из них просто развёрнуты без других изменений: {rev})")
    lines += [f"  {k}: подвесных {la} → {lb}, различий {d}{' (' + r + ')' if r else ''}, записей в ChangeLog {c}" for d, k, la, lb, c, r in ch[:60]]
    (ROOT / "extracted/kfg2026_diff.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:25]))


if __name__ == "__main__":
    main()
