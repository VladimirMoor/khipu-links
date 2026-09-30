"""Подробные данные для 3D-модели кипу на сайте (site/kd/*.json).

Для кипу из OKR — записанное: длина основного шнура; положение каждого подвесного вдоль основного (по началу и
концу его группы в cord_cluster, равномерно внутри группы); длина шнура, крепление (R/V), окончание; цвета
(ascher_cord_color, первый код, оператор, второй код); кластеры узлов с высотой от верха шнура, типом (S, L, E …),
числом узлов и витков; дочерние — от родителя на записанной высоте (ATTACH_POS).
Для UR297/UR298 — из нашей расшифровки бланков (knots_raw «5s(9.5/z) 4L(12.0/s)»; группы — из строк списка групп).
Для прочих кипу (только KFG) — реконструкция по значению: узлы на типовых высотах (помечено 'recon').
Формат шнура: [метка, индекс родителя (-1), уровень, позиция (см; для подвесного — вдоль основного, для дочернего — на
родителе), длина, крепление, окончание, цвет1, оператор, цвет2, значение, [[высота, тип, число, витки, направление]…]].
"""
import csv
import glob
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/open-khipu-repository/data/khipu.db"
OUT = ROOT / "site/kd"
PER = 30


def num(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def from_okr(con, kid, cat_vals):
    pc = con.execute("select PCORD_ID, PCORD_LENGTH from primary_cord where KHIPU_ID=?", (kid,)).fetchone()
    pcol = con.execute("select COLOR_CD_1 from ascher_cord_color where KHIPU_ID=? and PCORD_FLAG=1 limit 1", (kid,)).fetchone()
    cords = con.execute("select CORD_ID, PENDANT_FROM, CORD_LEVEL, CORD_ORDINAL, CLUSTER_ID, ATTACH_POS, CORD_LENGTH, "
                        "ATTACHMENT_TYPE, TERMINATION from cord where KHIPU_ID=? order by CORD_LEVEL, CORD_ORDINAL", (kid,)).fetchall()
    if not cords:
        return None
    cl = {r[0]: (num(r[1]), num(r[2]), r[3] or 0) for r in
          con.execute("select CLUSTER_ID, START_POSITION, END_POSITION, NUM_CORDS from cord_cluster where KHIPU_ID=?", (kid,))}
    col = {}
    for cid, c1, op, c2 in con.execute("select CORD_ID, COLOR_CD_1, OPERATOR_1, COLOR_CD_2 from ascher_cord_color where KHIPU_ID=? "
                                       "order by color_id", (kid,)):
        col.setdefault(cid, (c1 or "", op or "", c2 or ""))
    knots = defaultdict(list)
    q = ("select kc.CORD_ID, kc.CLUSTER_ID, kc.START_POS, k.TYPE_CODE, k.NUM_TURNS, k.DIRECTION from knot_cluster kc "
         "join knot k on k.CLUSTER_ID = kc.CLUSTER_ID join cord c on c.CORD_ID = kc.CORD_ID where c.KHIPU_ID=? "
         "order by kc.CORD_ID, kc.START_POS, k.KNOT_ORDINAL")
    agg = defaultdict(lambda: [0.0, "", 0, 0, ""])
    order = []
    for cid, clu, pos, t, turns, d in con.execute(q, (kid,)):
        key = (cid, clu, t)
        if key not in agg:
            order.append(key)
        a = agg[key]
        a[0], a[1], a[2], a[3], a[4] = num(pos), t or "S", a[2] + 1, max(a[3], int(num(turns))), d or ""
    for key in order:
        knots[key[0]].append([round(agg[key][0], 1), agg[key][1], agg[key][2], agg[key][3], agg[key][4]])
    by_parent = defaultdict(list)
    pend = []
    for r in cords:
        if (r[2] or 1) == 1:
            pend.append(r)
        else:
            by_parent[r[1]].append(r)
    # x-position of pendants: evenly inside their cluster
    per_cl = defaultdict(list)
    for r in pend:
        per_cl[r[4]].append(r)
    xpos = {}
    for c, rs in per_cl.items():
        s, e, _ = cl.get(c, (0.0, 0.0, 0))
        rs.sort(key=lambda r: r[3] or 0)
        if e <= s:
            e = s + 0.6 * len(rs)
        for i, r in enumerate(rs):
            xpos[r[0]] = s + (e - s) * (i + 0.5) / len(rs)
    out, idx = [], {}

    def add(r, label, parent_i, x):
        c1, op, c2 = col.get(r[0], ("", "", ""))
        idx[r[0]] = len(out)
        kn = knots.get(r[0], [])
        val = 0
        out.append([label, parent_i, r[2] or 1, round(x, 2), round(num(r[6]), 1), r[7] or "", r[8] or "", c1, op, c2, val, kn])
        for j, s in enumerate(sorted(by_parent.get(r[0], []), key=lambda z: z[3] or 0), 1):
            pos = num(s[5]) if num(s[5]) > 0 else 1.0 + 0.8 * j
            add(s, f"{label}s{j}", idx[r[0]], pos)

    pend.sort(key=lambda r: (xpos.get(r[0], 0), r[3] or 0))
    for i, r in enumerate(pend, 1):
        add(r, str(i), -1, xpos.get(r[0], i * 0.6))
    # values: sum of knot_value_type per cord (as in the corpus), fallback — from knot digits
    vals = dict(con.execute("select c.CORD_ID, sum(k.knot_value_type) from cord c join knot k on k.CORD_ID = c.CORD_ID "
                            "where c.KHIPU_ID=? group by c.CORD_ID", (kid,)))
    back = {i: cid for cid, i in idx.items()}
    for i, c in enumerate(out):
        v = vals.get(back.get(i))
        c[10] = int(v) if v is not None else value_from_knots(c[11])
    return {"q": "okr", "pl": round(num(pc[1]) if pc else max(c[3] for c in out) + 2, 1), "pc": (pcol[0] if pcol else "") or "", "c": out}


def value_from_knots(kn):
    if not kn:
        return 0
    # clusters from top to bottom = descending places; long/E knots are units
    kn = sorted(kn, key=lambda k: k[0])
    digits = []
    for pos, t, n, turns, d in kn:
        if t in ("L", "SP", "BL", "LL"):
            digits.append(max(turns, 2) if t == "L" else 3)
        elif t in ("E", "EE", "TF"):
            digits.append(1 if t != "EE" else 2)
        else:
            digits.append(n)
    v = 0
    for d in digits:
        v = v * 10 + d
    return v


KRE = re.compile(r"(\d+)\s*([sSLE])\s*\(\s*(\d+(?:\.\d+)?)\s*(?:[/,]\s*([sSzZ]))?")


def from_sheets(k):
    rows = []
    for f in sorted(glob.glob(str(ROOT / f"extracted/do_{k}_p*.csv"))):
        rows += list(csv.DictReader(open(f)))
    if not rows:
        return None
    groups = []
    for f in sorted(glob.glob(str(ROOT / f"extracted/do_{k}_p*_meta.txt"))):
        for line in open(f):
            m = re.search(r"(\d+(?:\.\d+)?)\s*cm\.?,?\s.*?\((\d+)\s*[-–]\s*(\d+)\)", line)
            if m:
                groups.append((float(m.group(1)), int(m.group(2)), int(m.group(3))))
    groups.sort()
    xpos = {}
    for gi, (s, a, b) in enumerate(groups):
        e = groups[gi + 1][0] - 0.8 if gi + 1 < len(groups) else s + 0.35 * (b - a + 1)
        e = max(e, s + 0.2 * (b - a + 1))
        for n in range(a, b + 1):
            xpos[n] = s + (e - s) * (n - a + 0.5) / (b - a + 1)
    out, idx = [], {}
    subs_pos = defaultdict(list)
    seen = set()
    for r in rows:
        lab = r["cord"].strip().replace(" ", "")
        if lab in seen or not re.match(r"^\d", lab):
            continue
        seen.add(lab)
        kn = [[float(p), ("S" if t in "sS" else t), int(n) if t in "sS" else 1, int(n) if t == "L" else 0, (d or "").upper()]
              for n, t, p, d in KRE.findall(r["knots_raw"] or "")]
        par = r["parent"].strip().replace(" ", "")
        lvl = lab.count("s") + 1
        try:
            val = int(sum(int(float(x)) for x in str(r["value"]).replace(",", "").split("+"))) if str(r["value"]).strip() not in ("", "-") else 0
        except ValueError:
            val = 0
        length = num(re.sub(r"[^\d.]", "", r["length_cm"] or "") or 0)
        att = (r["spin_ply_attach"].split("/") + ["", "", ""])[2].strip().upper()[:1]
        pi = idx.get(par, -1)
        if lvl == 1:
            x = xpos.get(int(re.match(r"\d+", lab).group(0)), 0.6 * len(out))
        else:
            sp = [float(v) for v in re.findall(r":\s*(\d+(?:\.\d+)?)", rows_by(rows, par).get("subsidiaries_raw", "") or "")]
            j = len(subs_pos[par])
            x = sp[j] if j < len(sp) else 1.0 + 0.8 * j
            subs_pos[par].append(x)
        idx[lab] = len(out)
        colr = (r["color"] or "").strip()
        m = re.match(r"([A-Z]+)(?:\s*([:\-/])\s*([A-Z]+))?", colr)
        c1, op, c2 = (m.group(1), m.group(2) or "", m.group(3) or "") if m else ("", "", "")
        out.append([lab, pi, lvl, round(x, 2), round(length, 1), att, "", c1, op, c2, val, kn])
    pl = max((c[3] for c in out if c[2] == 1), default=10) + 1
    return {"q": "sheet", "pl": round(pl, 1), "pc": "", "c": out}


_rb = {}


def rows_by(rows, lab):
    if id(rows) not in _rb:
        _rb[id(rows)] = {r["cord"].strip().replace(" ", ""): r for r in rows}
    return _rb[id(rows)].get(lab, {})


def reconstruct(k, rs, kids):
    out = []
    x = 1.0
    last_g = None

    def knots_for(v, length):
        if v <= 0:
            return []
        L = length if length > 5 else 40.0
        ds = [int(c) for c in str(v)]
        kn = []
        for i, d in enumerate(ds):
            place = len(ds) - 1 - i
            pos = round(L * (0.78 - 0.2 * place), 1) if place < 4 else round(L * 0.1, 1)
            if d == 0:
                continue
            if place == 0:
                kn.append([pos, "E", 1, 0, ""] if d == 1 else [pos, "L", 1, d, ""])
            else:
                kn.append([pos, "S", d, 0, ""])
        return kn

    def add(r, label, pi, pos):
        v = int(r["value"])
        length = num(r["length"])
        m = re.match(r"([A-Z]+)(?:\s*([:\-/])\s*([A-Z]+))?", r["color"] or "")
        c1, op, c2 = (m.group(1), m.group(2) or "", m.group(3) or "") if m else ("", "", "")
        i = len(out)
        out.append([label, pi, int(r["level"] or 1), round(pos, 2), round(length or 30.0, 1), (r["attachment"] or "")[:1],
                    r["termination"] or "", c1, op, c2, v, knots_for(v, length or 30.0)])
        for j, s in enumerate(sorted(kids.get(r["cord_id"], []), key=lambda z: int(z["order"])), 1):
            add(s, f"{label}s{j}", i, 1.0 + 0.8 * j)

    for n, r in enumerate(rs, 1):
        if last_g is not None and r["group"] != last_g:
            x += 1.2
        last_g = r["group"]
        add(r, str(n), -1, x)
        x += 0.6
    return {"q": "recon", "pl": round(x + 1, 1), "pc": "", "c": out}


def main():
    """Экспорт site/kd/*.json (модели для 3D) из atlas/atlas.db."""
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.json"):
        f.unlink()
    db = sqlite3.connect(ROOT / "atlas/atlas.db")
    knots = defaultdict(list)
    for k, ci, pos, t, n, turns, d in db.execute("select khipu, cord_idx, pos, type, n, turns, direction from model_knot"):
        knots[(k, ci)].append([pos, t, n, turns, d])
    cords = defaultdict(list)
    for r in db.execute("select khipu, idx, label, parent_idx, level, pos, length, attachment, termination, color1, op, color2, value "
                        "from model_cord order by khipu, idx"):
        cords[r[0]].append(list(r[2:]) + [knots.get((r[0], r[1]), [])])
    models = {k: {"q": q, "pl": pl, "pc": pc or "", "c": cords[k]} for k, q, pl, pc in db.execute("select * from model_meta")}
    ids = sorted(models)
    index = {}
    for b in range(0, len(ids), PER):
        chunk = {k: models[k] for k in ids[b:b + PER]}
        name = f"b{b // PER:02d}.json"
        (OUT / name).write_text(json.dumps(chunk, separators=(",", ":")))
        for k in chunk:
            index[k] = name
    (OUT / "index.json").write_text(json.dumps(index, separators=(",", ":")))
    print(f"kd: models {len(models)}; files {len(list(OUT.glob('*.json')))}; {sum(f.stat().st_size for f in OUT.glob('*.json')) // 1024} KB")


if __name__ == "__main__":
    main()
