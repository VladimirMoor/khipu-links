"""Экспорт данных сайта site/data.json из базы атласа atlas/atlas.db.

Источник правды — atlas/curated/*.csv|json (места, связи, находки, хронология, источники, поправки) и корпус;
база собирается khipu/atlas_db.py. Здесь — только выгрузка для сайта и сравнения шнуров для страниц находок
(build_compare: значения берутся из каталожного слоя базы).
Порядок: python3 khipu/atlas_db.py && python3 khipu/site_build.py && python3 khipu/site_knots.py
"""
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site/data.json"
KHIPU_URL = "https://github.com/VladimirMoor/khipu-links/blob/main/khipu/"


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
    khipus = []
    for m in q("select * from khipu order by id"):
        k = m["id"]
        rs = pend.get(k, [])
        vals = [int(r["value"]) for r in rs]
        khipus.append({"id": k, "alias": m["alias"], "okr": m["okr"], "museum": m["museum"], "num": m["num"], "prov": m["prov"],
                       "site": m["site"], "collector": m["collector"], "np": m["n_pendants"], "nc": m["n_cords"], "model": m["model"],
                       "groups": [len(list(g)) for _, g in itertools.groupby(rs, key=lambda r: r["group"])],
                       "v": vals, "c": [r["color"] for r in rs], "max": max(vals) if vals else 0, "sum": sum(vals),
                       "findings": sorted(set(find_k.get(k, []) + edge_k.get(k, [])))})
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
            "corrections": q("select * from correction"), "scriptBase": KHIPU_URL}
    s = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(s)
    print(f"data.json: khipus {len(khipus)}; sites {len(sites)}; edges {len(data['edges'])}; {len(s) // 1024} KB")


if __name__ == "__main__":
    main()
