"""Экспорт данных сайта site/data.json из базы атласа atlas/atlas.db.

Источник правды — atlas/curated/*.csv|json (места, связи, находки, хронология, источники, поправки) и корпус;
база собирается khipu/atlas_db.py. Здесь — только выгрузка для сайта и сравнения шнуров для страниц находок
(build_compare: значения берутся из каталожного слоя базы).
Порядок: python3 khipu/atlas_db.py && python3 khipu/site_build.py && python3 khipu/site_knots.py
"""
import csv
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site/data.json"
KHIPU_URL = "https://github.com/VladimirMoor/khipu-links/blob/main/khipu/"


def inkawasi_diagram():
    """SVG of the Inkawasi archive on three levels (parts, ledgers, copies and totals). Text elements hold English
    strings that the page translates (listed in "labels")."""
    W, H, bw, bh = 1120, 440, 116, 62
    X = {k: 215 + 140 * i for i, k in enumerate(["UR275", "UR269", "UR268", "UR274B", "UR274A", "UR267A", "UR267B"])}
    Y = {"parts": 70, "ledgers": 205, "copies": 340}
    nodes = [  # id, x, row, role key, deduction, place, product key, sector C
        ("UR278", X["UR275"], "parts", "nine parts", "", "A 20N · UE 16", "peanut", False),
        ("UR270", X["UR274B"], "parts", "nine parts", "", "A 20N · UE 13", "", False),
        ("UR275", X["UR275"], "ledgers", "ledger", "− 47", "A 20N · UE 19", "peanut", False),
        ("UR269", X["UR269"], "ledgers", "rounds of five", "− 47·46·46·44·25", "A 20N · UE 11", "peanut", False),
        ("UR268", X["UR268"], "ledgers", "ledger", "− 208", "A 20N · UE 18", "peanut", False),
        ("UR274B", X["UR274B"], "ledgers", "ledger", "− 10, 17", "A 20N · UE 15", "", False),
        ("UR274A", X["UR274A"], "ledgers", "ledger", "− 30", "A 20N · UE 15", "", False),
        ("UR267A", X["UR267A"], "ledgers", "ledger", "− 15", "A 24-F · UE 16", "chili", False),
        ("UR267B", X["UR267B"], "ledgers", "ledger", "− 10", "A 24-F · UE 16", "chili", False),
        ("UR266", X["UR275"], "copies", "copy", "− 47", "A 20N · UE 12", "peanut", False),
        ("UR273B", X["UR274B"], "copies", "totals only", "", "A 20N · UE 14", "", False),
        ("UR273A", X["UR274A"], "copies", "totals only", "", "A 20N · UE 14", "", False),
        ("UR255", X["UR267A"], "copies", "copy", "− 15", "C 19K · UE 2", "chili", True),
        ("UR256", X["UR267B"], "copies", "copy", "− 10", "C 19K · UE 2", "chili", True),
    ]
    pos = {n[0]: (n[1], Y[n[2]]) for n in nodes}
    edges = [("UR278", "UR275", "totals"), ("UR278", "UR266", ""), ("UR270", "UR274B", "totals"), ("UR275", "UR266", "copy"),
             ("UR274B", "UR273B", "totals"), ("UR274A", "UR273A", "totals"), ("UR267A", "UR255", "copy"),
             ("UR267B", "UR256", "copy"), ("UR275", "UR269", "place 1"), ("UR269", "UR268", "208 = sum of the five deductions")]
    labels = {"Parts", "Ledgers", "Copies and totals", "The archive on three levels",
              "Outlined in red: stored in sector C (unit 19K); all others in sector A. Numbers after − are the fixed deductions; arrows point from the details to the totals and from a ledger to its copy."}
    out = [f'<svg viewBox="0 0 {W} {H}" class="dg" role="img" aria-label="The archive on three levels">',
           '<defs><marker id="dga" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0,0 L10,5 L0,10 z" class="dg-arrow"/></marker></defs>']
    for key, y in (("Parts", "parts"), ("Ledgers", "ledgers"), ("Copies and totals", "copies")):
        out.append(f'<text x="8" y="{Y[y] + 5}" class="dg-row">{key}</text>')
    for a, b, lab in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        if y1 == y2:      # same row: from right edge to left edge
            sx, sy, ex, ey = x1 + bw / 2, y1, x2 - bw / 2, y2
        else:
            sx, sy, ex, ey = x1, y1 + bh / 2, x2, y2 - bh / 2
            if a == "UR278" and b == "UR266":   # long arrow past UR275, on its left
                sx, ex = x1 - bw / 2 + 6, x2 - bw / 2 + 6
                out.append(f'<path d="M{sx},{sy} C{sx - 40},{sy + 80} {ex - 40},{ey - 80} {ex},{ey}" class="dg-edge" marker-end="url(#dga)"/>')
                continue
        out.append(f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" class="dg-edge" marker-end="url(#dga)"/>')
        if lab:
            labels.add(lab)
            if y1 == y2:      # under the boxes, below the place labels
                out.append(f'<text x="{(sx + ex) / 2}" y="{sy + bh / 2 + 28}" class="dg-elab" text-anchor="middle">{lab}</text>')
            else:
                out.append(f'<text x="{sx + 6}" y="{(sy + ey) / 2 + 4}" class="dg-elab">{lab}</text>')
    for k, x, row, role, ded, place, prod, secC in nodes:
        y = Y[row]
        out.append(f'<rect x="{x - bw / 2}" y="{y - bh / 2}" width="{bw}" height="{bh}" rx="7" class="dg-box{" dg-c" if secC else ""}"/>')
        out.append(f'<text x="{x}" y="{y - 14}" class="dg-id" text-anchor="middle">{k}</text>')
        out.append(f'<text x="{x}" y="{y + 3}" class="dg-role" text-anchor="middle">{role}</text>')
        labels.add(role)
        if ded:
            out.append(f'<text x="{x}" y="{y + 19}" class="dg-ded" text-anchor="middle">{ded}</text>')
        out.append(f'<text x="{x}" y="{y + bh / 2 + 13}" class="dg-place" text-anchor="middle">{place}</text>')
        if prod:
            labels.add(prod)
            out.append(f'<text x="{x - bw / 2 + 2}" y="{y - bh / 2 - 4}" class="dg-prod">{prod}</text>')
    out.append("</svg>")
    return {"kind": "svg", "title": "The archive on three levels", "svg": "".join(out), "labels": sorted(labels),
            "note": "Outlined in red: stored in sector C (unit 19K); all others in sector A. Numbers after − are the fixed deductions; arrows point from the details to the totals and from a ledger to its copy."}


def build_compare(pend, kids):
    val = {k: [int(r["value"]) for r in rs] for k, rs in pend.items()}
    grp = {k: [[int(r["value"]) for r in g] for _, g in itertools.groupby(rs, key=lambda r: r["group"])] for k, rs in pend.items()}
    subs = lambda k, i: [int(c["value"]) for c in sorted(kids.get(pend[k][i]["cord_id"], []), key=lambda c: int(c["order"]))]

    def pairs(title, a, b, mapping, note=""):
        rows = []
        for ia, ib in mapping:
            va = val[a][ia - 1] if ia else None
            vb = val[b][ib - 1] if ib else None
            flag = "na" if va is None or vb is None else ("eq" if va == vb else "ne")
            rows.append([ia or "", "" if va is None else va, ib or "", "" if vb is None else vb, flag])
        n_eq = sum(r[4] == "eq" for r in rows)
        return {"kind": "pairs", "title": title, "a": a, "b": b, "rows": rows, "note": note,
                "tally": f"{n_eq} of {sum(r[4] != 'na' for r in rows)} cords equal"}

    def window(title, a, b, width=40, note=""):
        import difflib
        A, B = val[a], val[b]
        rows = []
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
            if t == "equal":
                rows += [[i1 + d + 1, A[i1 + d], j1 + d + 1, B[j1 + d], "eq"] for d in range(i2 - i1)]
            elif t == "replace":
                for d in range(max(i2 - i1, j2 - j1)):
                    ia, ib = i1 + d, j1 + d
                    rows.append([ia + 1 if ia < i2 else "", A[ia] if ia < i2 else "", ib + 1 if ib < j2 else "", B[ib] if ib < j2 else "",
                                 "ne" if ia < i2 and ib < j2 else "na"])
            elif t == "delete":
                rows += [[i1 + d + 1, A[i1 + d], "", "", "na"] for d in range(i2 - i1)]
            else:
                rows += [["", "", j1 + d + 1, B[j1 + d], "na"] for d in range(j2 - j1)]
        best, bi = -1, 0
        for i in range(max(1, len(rows) - width + 1)):
            e = sum(r[4] == "eq" for r in rows[i:i + width])
            if e > best:
                best, bi = e, i
        rows = rows[bi:bi + width]
        return {"kind": "pairs", "title": title, "a": a, "b": b, "rows": rows, "note": note,
                "tally": f"{sum(r[4] == 'eq' for r in rows)} of {sum(r[4] != 'na' for r in rows)} aligned cords equal in this window"}

    C = defaultdict(list)
    C["basel"].append(pairs("MM015 (Basel) against UR212 unit 1 and AS131 unit 1", "MM015", "UR212",
                            [(i, 195 - i) for i in range(1, 14)] + [(14, 195)],
                            "Cords 1–13 run against UR212 in reverse; the knotless cord stays last on both."))
    C["basel"].append(pairs("MM015 cords 15–23 against AS131 cords 1–9", "MM015", "UR1131", [(14 + i, i) for i in range(1, 10)],
                            "Cord 21 is the colour-marked slot: knotless on AS131, 4 on the Basel copy."))
    C["basel"].append(pairs("MM008 (Basel) against AS131 unit 14", "MM008", "UR1131", [(i, 147 - i) for i in range(1, 11)],
                            "Cord 4 is the marked slot: knotless on AS131, 14 on the copy."))
    C["basel"].append(pairs("MM008 cords 11–25 against UR212 unit 14", "MM008", "UR212", [(10 + i, i) for i in range(1, 15)] + [(25, None)],
                            "UR212's first group; the Basel copy has one extra cord of 113 at the end."))
    C["basel"].append({"kind": "table", "title": "Each fragment pairs the same unit of both khipus",
                       "head": ["Fragment", "UR212 unit (counted from its end)", "AS131 unit"],
                       "rows": [["MM015", "1", "1"], ["MM016", "4", "4"], ["MM008", "14", "14"], ["MM009", "—", "13"], ["MM012", "7", "—"], ["MM014", "2", "—"]]})
    C["frame14"].append({"kind": "table", "title": "Khipus of the Gretzer batch with 14 units",
                         "head": ["Khipu", "Berlin number", "Cords per unit", "How the halves of 7 are marked", "Cord data"],
                         "rows": [["UR212", "VA 42508 (A)", "14", "a single knotless cord", "yes"], ["AS131 (UR1131)", "VA 42510", "10", "a larger space (Aschers)", "yes"],
                                  ["AS170", "VA 42554", "5–7", "a marker, after a two-group preamble (Aschers)", "yes"],
                                  ["UR199", "VA 42597 (A)", "5", "not recorded", "yes"], ["—", "VA 42513", "13", "museum record: 14 × 13", "no"],
                                  ["—", "VA 42537", "9", "museum record: 14 × 9", "no"], ["—", "VA 42532", "5 + 4", "museum record: 7 × A, 7 × B, 7 × A, 7 × B", "no"]]})
    g1, g2, g4 = grp["UR1149"][0], grp["UR1149"][1], grp["UR1143"][3]
    C["berlin"].append({"kind": "table", "title": "AS143 group 4 = AS149 group 1 + group 2",
                        "head": ["Position", "AS149 g1", "AS149 g2", "Sum", "AS143 g4", ""],
                        "rows": [[i + 1, g1[i], g2[i], g1[i] + g2[i], g4[i], "=" if g1[i] + g2[i] == g4[i] else "≠"] for i in range(5)]})
    C["huacho1"].append(window("AS175 (Pachacamac) against UR233 (Huacho), best-aligned window", "UR1175", "UR233", 44,
                               "Runs break at the knotless cord UR233 adds to each group and where AS175's totals (part 2) are left out."))
    st = len(grp["UR218"][0])   # UR218 group 2 starts after its first group
    C["as118"].append(pairs("UR218 groups 2–3 against AS118 groups 2–3", "UR218", "UR1118", [(st + i, 1 + i) for i in range(1, 15)],
                            "The knot counts agree as well; five cords are broken on AS118."))
    s1 = subs("UR1118", 0)
    t = [sum(g) for g in grp["AS125"]]
    C["as118"].append({"kind": "table", "title": "AS118's first-cord subsidiaries against the group totals of AS125",
                       "head": ["AS118 subsidiary", "AS125 group total", "Note"],
                       "rows": [[s1[1], t[0], "unexplained"], [s1[2], t[1], "exact"], [s1[3], t[2], "exact if a broken cord read 2220 was 2298"],
                                [s1[4], t[3], "exact if the cord the Aschers left unread is 3111"]]})
    try:
        sys_path = str(ROOT / "khipu")
        import sys
        sys.path.insert(0, sys_path)
        import slotded
        B = [b for b in slotded.blocks("UR269") if len(b) >= 4]
        rows = []
        for n, b in enumerate(B, 1):
            ds = [slotded.ded(g) for g in b][:5]
            rows.append([n] + [d if d is not None else "·" for d in ds] + [""] * (5 - len(ds)))
        C["ur269"].append({"kind": "table", "title": "UR269: deduction in each place of each block", "head": ["Block", "Place 1", "Place 2", "Place 3", "Place 4", "Place 5"],
                           "rows": rows, "note": "Modal values 47, 46, 46, 44, 25; · = no readable deduction."})
    except Exception:
        pass
    shared = [1200, 1249, 1332, 1575, 2142, 2300]
    find = lambda k, v: next((g for g in grp[k] if v in g), [])
    C["inkawasi_archive"].append(inkawasi_diagram())
    roles = list(csv.DictReader(open(ROOT / "atlas/curated/inkawasi_roles.csv")))
    C["inkawasi_archive"].append({"kind": "table", "title": "The Inkawasi khipus by place",
                                  "head": ["Khipu", "Place", "Product", "Role", "Deduction", "Linked to"],
                                  "rows": [[r["khipu"], r["place"], r["product"], r["role"], r["deduction"], r["link"]] for r in roles],
                                  "note": "Place: sector, excavation unit and layer (UE) from the excavators' notes in the OKR; the JC khipus were recorded in 2016. Products from the excavators' nicknames and from the copies."})
    C["inkawasi"].append({"kind": "table", "title": "UR273B keeps only the totals of UR274B", "head": ["Total", "UR274B group", "UR273B group"],
                          "rows": [[v, " ".join(map(str, find("UR274B", v))), " ".join(map(str, find("UR273B", v)))] for v in shared]})
    C["as003"].append({"kind": "table", "title": "AS003 repeats the summary part of AS215", "head": ["", "Summary cords", "Top cord"],
                       "rows": [["AS215 part II", " ".join(map(str, grp["AS215"][4])), grp["AS215"][5][0]],
                                ["AS003", " ".join(map(str, grp["AS003"][0])), grp["AS003"][1][0]]],
                       "note": "Same six values in reverse order; 4 + 14 + 7 + 37 + 10 + 4 = 76 on both."})
    C["known"].append(window("KH0049 (Lima) against UR122 (Gothenburg), best-aligned window", "KH0049", "UR122", 36))
    try:
        import do_check
        U = do_check.urton_notes()
        C["dumbarton"].append({"kind": "note", "title": "Check against Urton's own totals",
                               "text": f"On the last eight sheets of UR297 Urton wrote the total of each group and of its summary cord: {sum(len(v) for v in U.values())} totals in all. 74 of the 78 equal our transcription (do_check.py)."})
    except Exception:
        pass
    return C



def main():
    """Экспорт site/data.json из atlas/atlas.db (сначала: python3 khipu/atlas_db.py)."""
    import sqlite3
    db = sqlite3.connect(ROOT / "atlas/atlas.db")
    db.row_factory = sqlite3.Row
    q = lambda sql, *a: [dict(r) for r in db.execute(sql, a)]
    pend, kids = defaultdict(list), defaultdict(list)
    for r in q("select khipu as inv_num, cord_id, parent_id, ord as 'order', grp as 'group', value, color, level from cord"):
        r = {k: (str(v) if v is not None else "") for k, v in r.items()}
        (kids[r["parent_id"]].append(r) if r["parent_id"] else pend[r["inv_num"]].append(r))
    for k in pend:
        pend[k].sort(key=lambda r: int(r["order"]))
    findings = [json.loads(r["body"]) for r in q("select body from finding")]
    edges_all = q("select src, dst, type, finding, note from link")
    edge_k, find_k = defaultdict(list), defaultdict(list)
    for e in edges_all:
        edge_k[e["src"]].append(e["finding"])
        edge_k[e["dst"]].append(e["finding"])
    for f in findings:
        for k in f["khipus"]:
            find_k[k].append(f["id"])
    names = defaultdict(list)
    for r in q("select khipu, name from khipu_name order by name"):
        names[r["khipu"]].append(r["name"])
    import re
    norm = lambda x: re.sub(r"[^0-9A-Z]", "", str(x).upper())
    smb = {r["norm"]: r["url"] for r in q("select * from smb_object")}
    acq = q("select * from acquisition")
    brk = {r["khipu"]: r["n"] for r in q("select khipu, count(*) as n from cord where level = 1 and termination = 'B' group by khipu")}
    nsub = {r["khipu"]: r["n"] for r in q("select khipu, count(*) as n from cord where level > 1 group by khipu")}
    corr = defaultdict(list)
    for r in q("select * from correction"):
        corr[r["khipu"]].append(r)
    checks = q("select * from object_check")
    ktypes = defaultdict(dict)
    for r in q("select k.khipu, k.type, sum(k.n) as n from model_knot k join model_meta m on m.khipu = k.khipu where m.quality != 'recon' group by k.khipu, k.type"):
        ktypes[r["khipu"]][r["type"]] = r["n"]
    khipus = []
    for m in q("select * from khipu order by id"):
        k = m["id"]
        rs = pend.get(k, [])
        vals = [int(r["value"]) for r in rs]
        khipus.append({"id": k, "alias": m["alias"], "okr": m["okr"], "museum": m["museum"], "num": m["num"], "prov": m["prov"],
                       "site": m["site"], "collector": m["collector"], "names": names.get(k, []), "np": m["n_pendants"], "nc": m["n_cords"], "model": m["model"],
                       "groups": [len(list(g)) for _, g in itertools.groupby(rs, key=lambda r: r["group"])],
                       "v": vals, "c": [r["color"] for r in rs], "max": max(vals) if vals else 0, "sum": sum(vals),
                       "findings": sorted(set(find_k.get(k, []) + edge_k.get(k, []))),
                       "brk": brk.get(k, 0), "nsub": nsub.get(k, 0), "corr": corr.get(k, []), "kt": ktypes.get(k, {}),
                       "kfg": next((n for n in [k] + names.get(k, []) if re.fullmatch(r"KH\d{4}[A-Z]?", n)), ""),
                       "ascher": next((n for n in [m["alias"], k] + names.get(k, []) if n and re.fullmatch(r"AS\d{3}[A-Z]?", n)), ""),
                       "smb": next((u for kk, u in smb.items() if m["num"] and (norm(m["num"]) == kk or (norm(m["num"]).startswith(kk) and len(norm(m["num"])) - len(kk) <= 2))), ""),
                       "acq": next(({"via": a["via"], "year": a["year"], "note": a["note"]} for a in acq if norm(m["num"]).startswith(norm(a["num_prefix"]))), None)})
    ids = {x["id"] for x in khipus}
    site_counts = Counter(x["site"] for x in khipus if x["site"])
    sites = [dict(r, n=site_counts.get(r["id"], 0)) for r in q("select * from site") if site_counts.get(r["id"], 0)]
    comp = build_compare(pend, kids)
    for f in findings:
        f["compare"] = comp.get(f["id"], [])
    data = {"built": __import__("datetime").date.today().isoformat(), "khipus": khipus, "sites": sites,
            "edges": [{"from": e["src"], "to": e["dst"], "type": e["type"], "finding": e["finding"], "note": e["note"]} for e in edges_all if e["src"] in ids and e["dst"] in ids],
            "edgeTypes": {r["type"]: r["label"] for r in q("select * from link_type")},
            "duplicates": [r for r in q("select a, b, note from duplicate") if r["a"] in ids and r["b"] in ids],
            "findings": findings, "negatives": q("select title, text from negative"),
            "sources": [dict(r, url=r["url"] or None) for r in q("select title, url, use from source")],
            "undigitized": q("select inv, collector, groups, url from undigitized order by inv"),
            "context": q("select kind, label, lat, lon, note from context"),
            "roads": [{"kind": r["kind"], "pts": [[lo, la] for la, lo in json.loads(r["pts"])]} for r in q("select * from road")],
            "timeline": [{"when": r["whn"], "title": r["title"], "text": r["text"], "finding": r["finding"] or None} for r in q("select * from timeline order by ord")],
            "corrections": q("select * from correction"), "checks": checks, "scriptBase": KHIPU_URL}
    s = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(s)
    print(f"data.json: khipus {len(khipus)}; sites {len(sites)}; edges {len(data['edges'])}; {len(s) // 1024} KB")
    write_i18n(data)


def write_i18n(data):
    """Переводы интерфейса и содержимого: atlas/curated/i18n/<lang>.json → site/i18n/<lang>.json.

    content — по ключам английского текста (находки по id; хронология, отрицательные результаты, источники — по
    английскому заголовку), так что новая строка без перевода просто показывается по-английски.
    """
    import sys
    sys.path.insert(0, str(ROOT / "khipu"))
    from i18n_source import compare_strings
    src = ROOT / "atlas/curated/i18n"
    out = ROOT / "site/i18n"
    out.mkdir(exist_ok=True)
    want = {"findings": {f["id"] for f in data["findings"]}, "timeline": {t["title"] for t in data["timeline"]},
            "negatives": {n["title"] for n in data["negatives"]}, "sources": {x["title"] for x in data["sources"]},
            "linkTypes": set(data["edgeTypes"]), "compare": set(compare_strings(data))}
    for f in sorted(src.glob("*.json")):
        if f.stem == "en_source":
            continue
        t = json.load(open(f))
        miss = {k: len(v - set(t.get("content", {}).get(k, {}))) for k, v in want.items()}
        (out / f.name).write_text(json.dumps(t, ensure_ascii=False, separators=(",", ":")))
        print(f"i18n/{f.name}: ui {sum(len(v) for v in t['ui'].values())} strings; untranslated content "
              + ", ".join(f"{k} {n}" for k, n in miss.items() if n) if any(miss.values()) else
              f"i18n/{f.name}: ui {sum(len(v) for v in t['ui'].values())} strings; content complete")


if __name__ == "__main__":
    main()
