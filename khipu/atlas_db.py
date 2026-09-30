"""Сборка базы атласа atlas/atlas.db (SQLite) из корпуса и редактируемых таблиц atlas/curated/.

Слои:
  * каталог — khipu (метаданные), cord (все шнуры корпуса: значение, цвет, группа, родитель) — как в
    extracted/plus_do_cords.csv (KFG + новые OKR + наши расшифровки UR297/UR298);
  * модель — model_cord, model_knot: геометрия для 3D (позиция на основном шнуре или на родителе, длина, крепление,
    узлы с высотой и типом); источник модели: okr | sheet | recon (см. site_knots.py);
  * курируемое — site, site_rule, context, road, link, link_type, duplicate, finding, negative, source, timeline,
    correction (поправки к прочтениям; применяются к cord.value только при applied = yes), undigitized (берлинские
    карточки museum-digital без оцифровки).
Правка данных: меняем файлы в atlas/curated/ (или добавляем расшифровку в extracted/), затем
  python3 khipu/atlas_db.py && python3 khipu/site_build.py && python3 khipu/site_knots.py
"""
import csv
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
DBP = ROOT / "atlas/atlas.db"
CUR = ROOT / "atlas/curated"
OKR = ROOT / "data/open-khipu-repository/data/khipu.db"

SCHEMA = """
create table khipu(id text primary key, alias text, okr text, museum text, num text, prov text, site text, collector text,
  n_pendants int, n_cords int, model text);
create table cord(khipu text, cord_id text, parent_id text, level int, ord int, grp text, value int, color text,
  attachment text, length real, termination text);
create table model_cord(khipu text, idx int, label text, parent_idx int, level int, pos real, length real, attachment text,
  termination text, color1 text, op text, color2 text, value int);
create table model_knot(khipu text, cord_idx int, pos real, type text, n int, turns int, direction text);
create table model_meta(khipu text primary key, quality text, primary_length real, primary_color text);
create table site(id text primary key, label text, lat real, lon real, region text);
create table site_rule(keyword text, site text);
create table context(kind text, label text, lat real, lon real, note text);
create table road(kind text, pts text);
create table link(src text, dst text, type text, finding text, note text);
create table link_type(type text primary key, label text);
create table duplicate(a text, b text, note text);
create table finding(id text primary key, status text, title text, body text);
create table negative(title text, text text);
create table source(title text, url text, use text);
create table timeline(ord int, whn text, title text, text text, finding text);
create table correction(khipu text, cord text, field text, recorded text, corrected text, applied text, source text, note text);
create table undigitized(inv text, collector text, groups text, url text);
"""


def rows(name):
    return list(csv.DictReader(open(CUR / name)))


def main():
    import site_knots as SK
    if DBP.exists():
        DBP.unlink()
    DBP.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DBP)
    db.executescript(SCHEMA)
    # curated
    for r in rows("sites.csv"):
        db.execute("insert into site values(?,?,?,?,?)", (r["id"], r["label"], float(r["lat"]), float(r["lon"]), r["region"]))
    rules = [(r["keyword"], r["site"]) for r in rows("site_rules.csv")]
    db.executemany("insert into site_rule values(?,?)", rules)
    db.executemany("insert into context values(?,?,?,?,?)", [(r["kind"], r["label"], float(r["lat"]), float(r["lon"]), r["note"]) for r in rows("context.csv")])
    db.executemany("insert into road values(?,?)", [(r["kind"], json.dumps(r["pts"])) for r in json.load(open(CUR / "roads.json"))])
    db.executemany("insert into link values(?,?,?,?,?)", [(r["from"], r["to"], r["type"], r["finding"], r["note"]) for r in rows("links.csv")])
    db.executemany("insert into link_type values(?,?)", [(r["type"], r["label"]) for r in rows("link_types.csv")])
    db.executemany("insert into duplicate values(?,?,?)", [(r["a"], r["b"], r["note"]) for r in rows("duplicates.csv")])
    db.executemany("insert into finding values(?,?,?,?)", [(f["id"], f["status"], f["title"], json.dumps(f, ensure_ascii=False))
                                                          for f in json.load(open(CUR / "findings.json"))])
    db.executemany("insert into negative values(?,?)", [(r["title"], r["text"]) for r in rows("negatives.csv")])
    db.executemany("insert into source values(?,?,?)", [(r["title"], r["url"], r["use"]) for r in rows("sources.csv")])
    db.executemany("insert into timeline values(?,?,?,?,?)", [(i, r["when"], r["title"], r["text"], r["finding"]) for i, r in enumerate(rows("timeline.csv"))])
    corr = rows("corrections.csv")
    db.executemany("insert into correction values(?,?,?,?,?,?,?,?)", [tuple(r[k] for k in ("khipu", "cord", "field", "recorded", "corrected", "applied", "source", "note")) for r in corr])
    # catalogue
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    meta.setdefault("UR297", {"MUSEUM_NAME": "Dumbarton Oaks, Washington DC", "MUSEUM_NUM": "PC.WBC.2016.072", "PROVENANCE": "Unknown", "OKR_NUM": "KH0675"})
    meta.setdefault("UR298", {"MUSEUM_NAME": "Dumbarton Oaks, Washington DC", "MUSEUM_NUM": "PC.WBC.2016.071", "PROVENANCE": "Unknown", "OKR_NUM": "KH0674"})
    norm = lambda s: re.sub(r"[^0-9A-Z]", "", str(s).upper())
    coll = {norm(inv): c for inv, c, _, _ in json.load(open(ROOT / "data/smb/khipu_collectors.json"))}
    apply = {(r["khipu"], r["cord"]): int(r["corrected"]) for r in corr if r["applied"].strip().lower() == "yes" and r["field"] == "value"}
    allc = list(csv.DictReader(open(ROOT / "extracted/plus_do_cords.csv")))
    pend = defaultdict(list)
    for r in allc:
        if r["parent_id"] == "":
            pend[r["inv_num"]].append(r)
    ordmap = {}
    for k, rs in pend.items():
        rs.sort(key=lambda r: int(r["order"]))
        for i, r in enumerate(rs, 1):
            ordmap[r["cord_id"]] = i
    ncount = Counter(r["inv_num"] for r in allc)
    for r in allc:
        v = int(r["value"])
        if r["parent_id"] == "" and (r["inv_num"], str(ordmap.get(r["cord_id"]))) in apply:
            v = apply[(r["inv_num"], str(ordmap[r["cord_id"]]))]
        db.execute("insert into cord values(?,?,?,?,?,?,?,?,?,?,?)", (r["inv_num"], r["cord_id"], r["parent_id"], int(r["level"] or 1),
                   int(r["order"]), r["group"], v, r["color"], r["attachment"], float(r["length"] or 0) if re.match(r"^[\d.]+$", r["length"] or "") else None, r["termination"]))

    def site_of(k, prov, mnum):
        if k.startswith("MM") and mnum == "IVc.366.03":
            return "huacho"
        p = prov.lower()
        return next((s for kw, s in rules if kw in p), None)

    # models
    con = sqlite3.connect(OKR)
    okr = dict(con.execute("select INVESTIGATOR_NUM, KHIPU_ID from khipu_main"))
    kids = defaultdict(list)
    for r in allc:
        if r["parent_id"]:
            kids[r["parent_id"]].append(r)
    for k, rs in pend.items():
        m = None
        if k in ("UR297", "UR298"):
            m = SK.from_sheets(k)
        elif k in okr:
            m = SK.from_okr(con, okr[k], None)
            if m and not any(c[11] for c in m["c"]):
                m = None
        if m is None:
            m = SK.reconstruct(k, rs, kids)
        db.execute("insert into model_meta values(?,?,?,?)", (k, m["q"], m["pl"], m["pc"]))
        for i, c in enumerate(m["c"]):
            db.execute("insert into model_cord values(?,?,?,?,?,?,?,?,?,?,?,?,?)", (k, i, c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10]))
            db.executemany("insert into model_knot values(?,?,?,?,?,?,?)", [(k, i, kn[0], kn[1], kn[2], kn[3], kn[4]) for kn in c[11]])
        mm = meta.get(k, {})
        prov = str(mm.get("PROVENANCE") or "").strip('" ')
        mnum = str(mm.get("MUSEUM_NUM") or "").strip('" ')
        c = coll.get(norm(mnum)) or next((v for kk, v in coll.items() if norm(mnum).startswith(kk) and len(norm(mnum)) - len(kk) <= 2), "")
        if not c and "Gaffron" in prov:
            c = "Gaffron, Eduard"
        db.execute("insert into khipu values(?,?,?,?,?,?,?,?,?,?,?)", (k, ("AS" + k[3:]) if re.fullmatch(r"UR1\d{3}", k) else "",
                   mm.get("OKR_NUM") or "", str(mm.get("MUSEUM_NAME") or "").strip('" '), mnum, prov, site_of(k, prov, mnum), c,
                   len(rs), ncount[k], m["q"]))
    # undigitized Berlin records
    have = {norm(x[0]) for x in db.execute("select num from khipu") if x[0]}
    for f in os.listdir(ROOT / "data/smb/obj"):
        d = json.load(open(ROOT / "data/smb/obj" / f))
        inv = d["object_inventory_number"]
        if any(norm(inv) == h or h.startswith(norm(inv)) for h in have):
            continue
        desc = d.get("object_description") or ""
        g = re.search(r"Groups?:\s*([^\n]+)", desc)
        cc = re.search(r"Sammler:\s*([^\n]+)", desc)
        db.execute("insert into undigitized values(?,?,?,?)", (inv, cc.group(1).strip() if cc else "", (g.group(1).strip() if g else "")[:140],
                   f"https://smb.museum-digital.de/object/{d['object_id']}"))
    db.commit()
    q = lambda s: db.execute(s).fetchone()[0]
    print(f"atlas.db: khipu {q('select count(*) from khipu')}, cord {q('select count(*) from cord')}, model_cord {q('select count(*) from model_cord')}, "
          f"model_knot {q('select count(*) from model_knot')}, link {q('select count(*) from link')}, finding {q('select count(*) from finding')}, "
          f"correction {q('select count(*) from correction')} (applied {len(apply)}), undigitized {q('select count(*) from undigitized')}; "
          f"{DBP.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
