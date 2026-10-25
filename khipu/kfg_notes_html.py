"""Notes for the Khipu Field Guide, one HTML fragment per khipu, in the style of the KFG notes (KH0022, KH0097, KH0242).

Sources: atlas/curated/links.csv (links found or refined here), findings.json (findings that name the khipu), SPEC below
(khipu-specific results of the 2026 hypothesis series, docs/project_log_ru.md), object_checks.csv, and
extracted/place_suspects.csv (place readings that knot heights call into question). Each note starts with
"Note by Vladimir Muravev:". Earlier authors are named where a result was known before.
Output: report/kfg_notes/<KFG code>.html and report/kfg_notes/index.md (list with khipu numbers).
"""
import csv
import html
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/kfg_notes"
ATLAS = "https://khipu-links.vercel.app/"
REPO = "https://github.com/VladimirMoor/khipu-links"
TYPE = {"sum": "sum across khipus", "lot": "shared lot", "details": "details without totals", "excerpt": "excerpt",
        "totals": "totals only", "join": "two accounts joined", "copy": "copy", "fold": "folded copy"}
PRIOR = {("UR267A", "UR255"): "Urton & Chu 2015", ("UR267B", "UR256"): "Urton & Chu 2015", ("UR266", "UR275"): "Urton & Chu 2015",
         ("KH0049", "UR122"): "", ("HP055", "UR1084"): "", ("UR1114", "UR1123"): "Urton 2005", ("UR066", "UR067"): "Urton & Brezine, OKR notes"}
# findings whose summary is about the named khipus themselves (the first sentences are quoted); the rest are corpus-wide
SPECIFIC = {"basel", "frame14", "berlin", "ica109", "huacho1", "as118", "ur269", "inkawasi", "as003", "folded", "known", "dumbarton",
            "inkawasi_archive", "as104"}

CANUTO = ("This is one of the eight OKR khipus whose pendants are gathered in bundles wrapped with coloured thread (canutos); such khipus are "
          "usually assigned to the Wari tradition (Urton; Cherkinsky &amp; Urton 2014 radiocarbon-date three to AD 780–1024). In the OKR the "
          "canuto field marks exactly the khipus whose long knots keep nearly the same number of turns: among 120 khipus with at least 40 long "
          "knots the eight rank 1, 2, 3, 5, 6, 9, 17 and 18 by the spread of turns. On them almost every cluster is a single long knot of 4–7 turns, "
          "there are no subsidiaries and no knotless pendants, the long knots are all of one direction (S in the OKR records), and the knots of a "
          "bundle sit at similar heights, as if each bundle was knotted together. Reading these knots as decimal digits would be wrong.")
SPEC = {
    "UR268": ["Its 16 four-cord rows [gross, deduction 208, two parts] follow the 16 four-cord rows of UR275 (KH0514) in the same order "
              "(Spearman 0.83, permutation p &lt; 0.0001; other offsets ≤ 0.39). They are 2.8–5.9 times larger, median 4.45, which is the ratio of "
              "the two fixed deductions, 208 / 47 = 4.43; and 208 = 47 + 46 + 46 + 44 + 25, the five place deductions of UR269 (KH0506). The final "
              "block of [gross, 208, net] triples holds round totals of UR269: group 20 = 10,385 (UR269 round 3: 10,379), group 28 = 9332 (round 1: "
              "9335), group 29 = 8527 (round 8: 8515), group 31 has net 8345 = 8553 − 208 (round 9: 8553), group 33 has net 7475 (round 10: 7478). Reading: UR268 keeps whole "
              "delivery rounds of five streams, UR275 the first stream alone. The similar column profile of UR268 and UR275 was noted earlier in this "
              "work; the row-by-row link is the new part."],
    "UR275": ["Its 16 four-cord rows are followed, row by row, by the four-cord rows of UR268 (KH0505), 4.45 times larger on the median — the "
              "ratio of the fixed deductions 208 / 47. Its three-cord rows [gross, 47, net] (1653 = 47 + 1606, 1737 = 47 + 1690, 1825 = 47 + 1780, …) "
              "are the place-1 records of the rounds of UR269 (KH0506).",
              "Group heads: in 100% of its groups the first cord is the largest (gross first), as in the other detail ledgers of the storehouse, "
              "while the summary khipus UR278 and UR270 do not show this rule.",
              "Rows of four cords do not always balance: gross − (deduction + parts) is 11, 34, 10, 10, 2002, 12, 0, 0 — a recurring remainder of "
              "about 10 that we could not explain."],
    "UR269": ["Round totals of its blocks of five records (gross summed over the five places) reappear in the final block of UR268 (KH0505), "
              "4 of 11 rounds within 3–12 (about 1.5 expected) and one more exactly as gross minus 208: round 3 → UR268 group 20 (10,379 / 10,385), "
              "round 1 → group 28 (9335 / 9332), rounds 8–10 → groups 29, 31, 33 in order. Within a round the place-2 gross follows the place-1 "
              "gross (Spearman 0.68 over 9 rounds); places 2–4 run about 1.4 times place 1, place 5 about 0.4."],
    "UR274B": ["Candidate link (not proven): its group heads follow those of the chili ledger UR267B (KH0504) at an offset of one row "
               "(Spearman 0.76, p = 0.002 among offsets ±5), 1.5–4.4 times larger; both keep a deduction of 10 in the same slot. It does not follow "
               "UR267A, UR275 or UR268, and the copy UR256 follows it weakly at the same offset. About 1,200 Inkawasi pairs were screened, so this "
               "needs confirmation."],
    "UR267B": ["Candidate link: the group heads of UR274B (KH0513) follow its rows at an offset of one (Spearman 0.76, p = 0.002); see that note."],
    "UR255": ["Its rows are laid out in a form of its own: every row has an empty cord between the gross amount and the fixed deduction 15 "
              "(106, 0, 15; 206, 0, 15, 0; 238, 0, 15, 0 …), where UR267A goes straight on (106, 15, 91). Gross values of UR267A reappear on UR255 in "
              "17 of 23 cases, net values in 9 of 22. Of 47 cords matched with UR267A only 1 is white, against 38 on UR267A. Its group heads follow "
              "UR267A row by row (Spearman 0.96)."],
    "UR256": ["Like UR255, every row has an empty cord between the gross amount and the fixed deduction 10 (1055, 0, 10, …; 672, 0, 10, …; "
              "1411, 0, 10, …), where UR267B goes straight on (660, 10, 74). None of its 44 cords matched with UR267B is white, against 36 on UR267B."],
    "UR267A": ["Its copy UR255 (KH0491) inserts an empty cord after every gross value and keeps almost no white cords (1 of 47 matched cords, "
               "against 38 here)."],
    "UR1120": ["Four rows of eight cords with totals 146,087, 49,783, 62,850 and 33,455 are divided by the same shares, about 17.6 / 0.7 / 29.3 / "
               "1.3 / 13.2 / 3.8 / 4.5 / 29.7 % (rows 1 and 2 proportional within 1–2%: 25,691 / 8,731 = 2.94, 43,372 / 14,701 = 2.95). This "
               "proportionality is Ascher &amp; Ascher's example 7.5 (Code of the Quipu, 1981) and is discussed by Chirinos (2010). A search of the "
               "whole corpus for proportional groups finds only this khipu, AS143 (KH0159) and the Inkawasi nine-part tables; the eight shares do "
               "not combine into those of AS143, and the row totals occur on no other digitized khipu."],
    "UR190": ["Groups 15–20 repeat the same slots with equal shares of round amounts, the remainder spread by ones: 100 as 33, 33, 34; 140 as "
              "46, 47, 47; 70 as 23, 23, 24. Corpus-wide, runs of cords that differ by exactly one and add up to a round number not divisible by "
              "their count are three times commoner than chance (24 against 8.3), and UR190 holds 8 of them."],
    "UR1161": ["Group 1 is 16, 16, 17, 17, 17, 17, 50, 50: one hundred divided into six shares with the remainder spread by ones, then 50 + 50 "
               "(sum 200)."],
    "HP037": ["Thirds of round amounts with the remainder spread by ones: 666, 667, 667 (2000), 134, 133 and 1334 (thirds of 400 and 4000), "
              "266 / 267 (800)."],
    "UR015": ["Group sum 5500 = 500 + 1782 + 1796 + 1422: a round total made of non-round parts (corpus-wide such sums are about 2.4 times "
              "commoner than chance)."],
    "UR187": ["Group sum 12,600 from non-round parts (6152, 478, 741, …)."],
    "HP030": ["Group sum 7200 from non-round parts (2691, 249, 364, …)."],
    "UR1113": ["After six filled rows of 11–12 cords come four rows of eleven cords with the same colour pattern (W W W W FR MB W W W W W) and "
               "no knots at all: a table prepared in advance and not filled. Column means fall from the first to the last column "
               "(209, 84, 70, 48, 44, 38, 54, 43, 40, 37, 16, 14). 12 khipus in the OKR have such blank rows."],
    "AS074": ["Eleven of its rows have cords in the colour pattern of the filled rows but no knots (blank rows of a prepared table) — the "
              "largest number in the OKR."],
    "UR1057": ["Five rows with the colour pattern of the filled rows and no knots (prepared, unfilled rows)."],
    "AS075": ["Four rows with the colour pattern of the filled rows and no knots (prepared, unfilled rows)."],
    "UR093": ["90 pendants carry exactly eight subsidiaries each (the sixth and seventh of another colour); the pendant equals the sum of its eight "
              "subsidiaries 19 times. HP038 (KH0568) has the same eight-subsidiary layout on 24 pendants but no shared values."],
    "HP038": ["24 pendants carry exactly eight subsidiaries each, the layout of UR093 (KH0329); no values are shared."],
    "UR1097": ["Many white pendants have a short coloured top (4–9 cm, then white). The colour of that top predicts the value: G0 and BB tags "
               "carry 1 (or 0), BG, VB and 0D tags carry 5 (or 0), and cords 14–47 alternate 5 / 1 in pairs (colour explains 94% of the variance "
               "of log values, 11% when shuffled)."],
    "UR004": ["Its few non-cotton pendants are blank markers: nine of human hair (colour LK) and seven of wool (AB) are knotless in 12 of 16 "
              "cases, and they open groups 14, 23, 37, 51 (hair) and 39, 41, 45 (wool). In this khipu the largest entry of a group tends to come "
              "last, often on a white or green cord (the Leymebamba rule, the mirror of the Inkawasi heads)."],
    "UR051": ["It is knotted like the canuto khipus — every upper cluster a long knot, knots about 12.5 cm apart, some long knots of 10+ turns, "
              "part camelid fibre — but its OKR record lists no canutos and the spread of turns is wider (sd 2.06). Worth checking on the object."],
    "AS068": ["Recorded twice, by Ascher (AS068) and by Urton (UR281): colour agrees on only 61 of 181 matched cords, mainly because Ascher's YB "
              "is Urton's AB (56 cases). Colour comparisons between the two sets of records need a translation table."],
    "UR085": ["A run 1498, 19, 73, 27 on cords 29–32 is repeated on cords 142–145 on cords of other colours, with 101 → 100 on the fifth cord: "
              "an internal copy."],
    "UR1084": ["It repeats a part of itself (12, 100, 40, 0, 22, 32, 0 at cords 124 and 135), and so does its copy HP055 (KH0586)."],
    "HP055": ["It repeats a part of itself (12, 0, 100, 40, 222, 22, 32, 76, 0 at cords 115 and 127), and so does its copy UR1084 (KH0097)."],
}
FIB = {"UR055": "Its pendants are human hair (178 of 180 recorded); 167 have ends wrapped with coloured thread. Bundles mostly of four cords "
                "(29 of 41); knots about 13.5 cm apart; turns per long knot sd 1.43.",
       "UR052": "Pendants of camelid fibre (59) and human hair (39); 52 wrapped ends; bundles mostly of four (18 of 27); knots about 17 cm apart; "
                "turns sd 1.46.",
       "UR050": "Camelid pendants; 85 wrapped ends; bundles of six (24 of 29); knots about 19 cm apart; turns sd 0.87; 90% of cords carry "
                "exactly three long knots.",
       "UR054": "Camelid pendants (115); bundles of mixed size; knots about 19 cm apart; turns sd 1.14.",
       "UR110": "Camelid pendants; bundles mostly of four (13 of 22); knots about 14 cm apart; turns sd 0.99; bundle-level turn sharing "
                "(R² 0.56 against 0.25).",
       "UR112": "Camelid pendants; 54 wrapped ends; bundles mostly of four (15 of 20); knots about 13 cm apart; turns sd 0.77.",
       "UR144": "Camelid pendants; bundles of four (23 of 24); knots about 11.5 cm apart; turns sd 0.80; the lowest knot is shorter on 38 of 42 cords.",
       "UR039": "From Huari; the only cotton khipu of the group; bundles of two (41 of 45); knots about 12.5 cm apart; turns sd 0.73, the "
                "narrowest of the corpus."}
for k, t in FIB.items():
    SPEC.setdefault(k, []).extend([CANUTO, t])


def main():
    c = sqlite3.connect(ROOT / "data/open-khipu-repository/data/khipu.db")
    kfg = {(n or "").strip(): (o or "").strip() for n, o in c.execute("select INVESTIGATOR_NUM, OKR_NUM from khipu_main") if o}
    for r in csv.DictReader(open(ROOT / "atlas/curated/kfg_names.csv")):
        for i in [r["khipu"]] + [a.strip() for a in r["aliases"].split(";") if a.strip()]:
            if i and r["kfg"].startswith("KH"):
                kfg.setdefault(i, r["kfg"])
    kfg.update({"AS068": "KH0081", "UR281": "KH0081", "KH0049": "KH0049", "KH0697": "KH0697"})
    D = json.load(open(ROOT / "site/data.json"))
    card = {}
    for k in D["khipus"]:
        for a in [k["id"]] + k["id"].split("/") + ([k["alias"]] if k.get("alias") else []):
            card.setdefault(a, k["id"])
    F = json.load(open(ROOT / "atlas/curated/findings.json"))
    notes = defaultdict(lambda: {"links": [], "findings": [], "spec": [], "checks": [], "reading": []})
    for r in csv.DictReader(open(ROOT / "atlas/curated/links.csv")):
        a, b = r["from"], r["to"]
        for x, y in ((a, b), (b, a)):
            prior = PRIOR.get((a, b))
            txt = f"<b>{html.escape(y)}</b>{' (' + kfg[y] + ')' if y in kfg and kfg[y] != y else ''} — {TYPE.get(r['type'], r['type'])}: {html.escape(r['note'])}."
            if prior is not None:
                txt += f" <i>The pairing was published before{(' (' + prior + ')') if prior else ''}; what is added here is the record-by-record comparison.</i>"
            elif r["finding"] == "known":
                txt += " <i>Known before this work.</i>"
            notes[x]["links"].append(txt)
    for f in F:
        for k in f.get("khipus", []):
            first = f["summary"].split(". ")
            body = ". ".join(first[:2]).rstrip(".") + "." if f["id"] in SPECIFIC else ""
            notes[k]["findings"].append((f["id"], f["title"], body))
    for k, lines in SPEC.items():
        notes[k]["spec"].extend(lines)
    for r in csv.DictReader(open(ROOT / "atlas/curated/object_checks.csv")):
        notes[r["khipu"]]["checks"].append(f"Cord {html.escape(r['cord'])}: {html.escape(r['check'])} <i>Why: {html.escape(r['why'])}</i>")
    ps = ROOT / "extracted/place_suspects.csv"
    if ps.exists():
        nondec = {"UR1087"}
        for r in csv.DictReader(open(ps)):
            if r["khipu"] in nondec:
                continue
            if r["kfg_value"] == r["height_reading"]:
                s = (f"Cord {r['cord']}: the OKR value is {r['okr_value']}, the KFG 2026 value {r['kfg_value']}. Knot heights support the KFG "
                     f"reading: the upper cluster sits at the hundreds height of its group ({r['top_pos']} cm against {r['group_hundreds_pos']} cm "
                     f"for hundreds and {r['group_tens_pos']} cm for tens).")
            elif r["kfg_value"] == r["okr_value"]:
                s = (f"Cord {r['cord']}: OKR and KFG both read {r['okr_value']}, but the upper cluster sits at the hundreds height of its group "
                     f"({r['top_pos']} cm; hundreds {r['group_hundreds_pos']} cm, tens {r['group_tens_pos']} cm), so the value may be "
                     f"{r['height_reading']} (empty tens place). Worth checking.")
            else:
                continue
            notes[r["khipu"]]["reading"].append(s)
    OUT.mkdir(parents=True, exist_ok=True)
    bycode = defaultdict(list)
    for k in sorted(notes):
        code = kfg.get(k, "")
        if code.startswith("KH") and any(notes[k].values()):
            bycode[code].append(k)
    index = []
    for code, ks in sorted(bycode.items()):
        n = {f: [x for k in ks for x in notes[k][f]] for f in ("links", "findings", "spec", "checks", "reading")}
        n["findings"] = list(dict.fromkeys(n["findings"]))
        n["spec"] = list(dict.fromkeys(n["spec"]))
        k = " / ".join(ks)
        if len(ks) > 1:
            n["spec"].insert(0, f"Recorded under {' and '.join(ks)} (one object).")
        parts = ["<br/><br/><b>Note by Vladimir Muravev:</b><br/><br/>"]
        if n["spec"]:
            parts += [f"{s}<br/><br/>" for s in n["spec"]]
        if n["links"]:
            parts.append("<b>Links to other khipus</b><ul>" + "".join(f"<li>{t}</li>" for t in n["links"]) + "</ul>")
        if n["findings"]:
            items = []
            for fid, title, body in n["findings"]:
                items.append(f'<li><a href="{ATLAS}#finding-{fid}">{html.escape(title)}</a>' + (f": {html.escape(body)}" if body else "") + "</li>")
            parts.append("<b>Findings that use this khipu</b> (Khipu Links Atlas)<ul>" + "".join(items) + "</ul>")
        if n["reading"]:
            parts.append("<b>Readings to check</b><ul>" + "".join(f"<li>{t}</li>" for t in n["reading"]) + "</ul>")
        if n["checks"]:
            parts.append("<b>Questions for the object</b><ul>" + "".join(f"<li>{t}</li>" for t in n["checks"]) + "</ul>")
        ref = f'Details, tests and baselines: <a href="{ATLAS}">Khipu Links Atlas</a>'
        if ks[0] in card:
            ref += f' (<a href="{ATLAS}#khipu-{html.escape(card[ks[0]])}">this khipu</a>)'
        ref += f', code and data <a href="{REPO}">{REPO}</a>. Contact: aderby3d@gmail.com.<br/>'
        parts.append(f"<i>{ref}</i>")
        (OUT / f"{code}.html").write_text("\n".join(parts) + "\n")
        index.append((code, k, len(n["spec"]), len(n["links"]), len(n["findings"]), len(n["reading"]), len(n["checks"])))
    with open(OUT / "index.md", "w") as fh:
        fh.write("| KFG | khipu | specific | links | findings | readings | object checks |\n|---|---|---|---|---|---|---|\n")
        for row in index:
            fh.write("| " + " | ".join(str(x) for x in row) + " |\n")
    print(f"{len(index)} notes in {OUT}")


if __name__ == "__main__":
    main()
