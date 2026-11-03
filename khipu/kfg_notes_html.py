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
import re
import sqlite3
import statistics
from collections import defaultdict
from pathlib import Path

from xlsx_read import sheets

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
              "gross (Spearman 0.68 over 9 rounds); places 2–4 run about 1.4 times place 1, place 5 about 0.4.",
              "Many values of UR269 are lower bounds: 55 of its 75 values ending in 0 sit on cords broken above the units zone (units knots at "
              "about 22 cm), so their units are lost. This explains two of the small discrepancies above: round 3 includes 2700 and 2810 on cords "
              "broken at 20 and 15 cm, so its total lies between 10,379 and 10,397 and holds UR268's 10,385; round 8 (2000 and 2100 on broken cords) "
              "gives 8515–8533 and holds 8527. The cords p154 and p166 are discussed under readings below."],
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
    "CM009": ["Probably the same object as UR068 (KH0305, Puruchuco Museum), recorded by Carol Mackey: aligned with UR068, 47 of 65 values and 57 of 61 colours agree "
              "(8, 1, 3, 1, 56, 5, 4, 1, 1213, 43, 64, 17 …), and Urton &amp; Brezine's note on UR068 says it 'matches Mackey's #2'. The cord lengths here are all 45.0 "
              "(not measured). Real copies in the corpus usually change colours, so this is more likely a second recording than the third copy of the UR064 ~ UR068 account."],
    "UR090": ["Place reading: the OKR gives 105, 102, 202, 302, 401 … where the KFG 2026 file gives 15, 12, 22, 32, 41 (51 of 53 such cords). On this khipu the "
              "single knots of two-cluster cords all stand about 8 cm from the main cord and the long knots 16–20 cm, a gap like that between tens and units on other "
              "khipus, so the KFG reading (no empty tens place) is the likely one."],
    "UR235": ["Place reading: the OKR gives 505, 109, 203, 207 … where the KFG 2026 file gives 55, 19, 23, 27 (22 of 22). Cords 1–3 put hundreds, tens and units at "
              "6.5, 15 and 28 cm; the disputed cords have their upper knots at 7.5 cm and units at 20–22 cm, a gap of about 13.5 cm, the tens-to-units distance: the "
              "whole cord is simply knotted higher, and the KFG reading is supported."],
    "UR085": ["Place readings: OKR and KFG 2026 differ by an empty tens place on 14 cords; by knot spacing the KFG reading is supported on 10 of the judgeable ones.", "A run 1498, 19, 73, 27 on cords 29–32 is repeated on cords 142–145 on cords of other colours, with 101 → 100 on the fifth cord: "
              "an internal copy."],
    "UR211": ["Its values look like marks rather than numbers: each place holds either one tufted knot (TF) or none (1111, 110, 1001, 1101, "
              "11 ...). Of its values of 10 and more, 18 of 20 are written with the digits 0 and 1 only (not counting 10, 100, 1000), against a "
              "median of 3% over the corpus. The Alt_Value reading (the lowest cluster read as tens: 1120, 1010 ...) keeps the same pattern. "
              "Reading: a table of presence and absence by position, or some count that is not decimal; its values should not be compared "
              "with numbers on other khipus."],
    "UR1084": ["It repeats a part of itself (12, 100, 40, 0, 22, 32, 0 at cords 124 and 135), and so does its copy HP055 (KH0586).",
               "It is longer than HP055: cords 1 to about 185 follow the whole of HP055 (189 pendants; HP055's primary cord ends in a knot, so "
               "nothing of it is lost), and cords 181–319 (about 135 pendants, all verso) are not on HP055 but continue with ten or so further "
               "records of the same form (a large number of 950–1600, then 10–14, 100 or 200, and small values 6–45). The knots change "
               "hand too: simple knots are Z on cords 1–140 (as on HP055) and S from about cord 145 to the end, the switch falling on a group "
               "boundary, and the median gap between places drops there from 8.5 to 6.5 cm. Reading: the Paris khipu is "
               "the Lima storehouse record copied and then continued, by a second knotter, with later entries.",
               "Lost cords can be restored from HP055. The cords Ascher listed as missing (existence implied by colour and spacing) at "
               "p31, p43, p56, p92, p127 and p138 all fall where every record of HP055 has 222, and broken stubs nearby (e.g. p29, p30, value "
               "0 on 6–7 cm) where HP055 has 100 and 40. On UR1084 these positions are dark brown (MB, BY), on HP055 white: the copy lost "
               "them to the dark dye, which is known to weaken the fibre."],
    "HP055": ["It repeats a part of itself (12, 0, 100, 40, 222, 22, 32, 76, 0 at cords 115 and 127), and so does its copy UR1084 (KH0097).",
              "UR1084 (KH0097) copies all of HP055 and then goes on with about 135 more pendants (ten or so records of the same form) that are "
              "not on HP055, tied by another hand (S knots, verso): HP055 looks like the earlier state of a record that was later continued.",
              "Reading to check, cord p114: OKR and KFG read 187, but its knots sit at 3, 12.5 and 21 cm, the heights of cord p126 (1087: 3, 12 "
              "and 20.5 cm), where the top cluster is thousands; with the hundreds left empty the value is 1087, which is what the copy UR1084 "
              "has at this place (its cord 112). Cord p102 reads 78 (knots at 13.5 and 22 cm, no top cluster) where UR1084 has 1078 (cord 100, "
              "a thousands knot at 2 cm): either the knot is lost on HP055 or the copyist added it."],
    "QU011": ["Two knotters. Cords 1–37 (with their subsidiaries) are tied all in Z, with units at 20–22 cm and few hundreds (values up to 132); "
              "cords 38–118 are all S (figure-eights stay Z), with hundreds at 1–4 cm and units at 11–14 cm (values up to 2388). The switch falls "
              "between p37 and p38, one cord before the end of the group 34–38, after the largest gap of the first half (10.5 cm). Such switches "
              "fall on group boundaries in most khipus where they occur (5 of 8 on the KFG records), and the height of the places changes with "
              "the hand, as here. No other khipu in the corpus repeats either part."],
    "AS214": ["The five old untied knots noted by Ascher (p5 1S, p9 2L, p13 2L, p14 1E, p15 3L) were, in four cases, the units knot of a "
              "two-cluster cord, so that 12, 12, 11 and 13 became exactly 10; on p5 the tens knot was removed (14 → 4). This looks like a deliberate "
              "change of the record (dropping the units) rather than damage; the group sums before or after the change do not give p1 = 30 or p2 = 13."],
    "AS170": ["The short colour segments at the top of the cords (above all knots) are labels of columns: in the seven-cord groups the tops G0, MB "
              "and 0D stand on the 4th, 5th and 6th cords in 11 of 12 groups, whatever the values (67, 33, 133; 150, 50, 50; 0, 0, 0 ...), and "
              "never on cords 1–3 or 7. Over the corpus such coloured tops are usually not tied to a place in the group (a band of darkening "
              "along the main cord would look the same); here they are."],
    "AS071": ["A form marked out in colour and filled only here and there: almost all cords are blank, yet each place of a group carries its own "
              "short colour segment at the top (W, BS:DB, W:HB, HB, then W ...; in later groups all BS, DB or W), and the few values (2, 3, 4; "
              "8, 4 ...) fall into a few of these columns. Compare the partly filled blank forms KT004 and UR1121."],
    "HP039": ["A table with a summary row. After the markers the cords form rows of seven: two head rows (cords 8–14 and 16–22), then five "
              "white rows (25–63) and five light-brown rows (65–100). The row 16–22 (873 292 353 601 400 458 225) is the column sum of the ten "
              "rows below it: 873, 292, 353 and 400 exactly, if the 3rd and 4th columns are added together (in the brown rows the value sits "
              "either in the 3rd or in the 4th place, the other one being empty); the 6th column gives 413 against 458 with p99 broken, and the "
              "7th 229 against 225. The 4th value of the summary row (601), the row 8–14 and cord 1 (4147) remain unexplained. Automatic searches "
              "for sums missed this because of the floating 3rd/4th column."],
    "KH0699": ["Three sections of the same plan: two head groups of six cords, then six detail groups. In the third section the head 139–144 "
               "(204 183 174 173 153 119) holds the sums of the six detail groups 153–206 in order (184 183 174 172 153 119): four exact, one "
               "off by 1, and the first 20 short with no broken cord in that group. In the first two sections the heads look like round "
               "set amounts next to the actual sums: groups 77* 86 86 86 73* 70 against heads with 86, 86 and 84 84 84 84; groups 195* 99* 121 "
               "127 40 71 against 200 128 120 120 100 100 (* = group with broken cords). The second head of section 3 (204 178 160 150 145 134 "
               "36) is a falling series that we could not explain."],
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


# group arithmetic as a judge between OKR and KFG 2026 readings (log, hypothesis 506)
SUMS = [
    ("UR128", "p2", 15, 105, "OKR: with 15 the group reads 23 = 15 + 8."),
    ("UR034", "p24", 5, 15, "OKR: with 5 the group reads 20 = 5 + 15."),
    ("UR269", "p166", 46, 406, "OKR: gross 2362 minus net 2316 is 46, the deduction of this place (KFG also gives 46 as Alt_Value)."),
    ("UR268", "p36", 1331, 1335, "KFG: with 1335 the row reads 11,954 = 208 + 1335 + 2620 + 7791."),
]

def lower_bounds(code):
    """Pendants broken above the units zone of their khipu (KFG 2026 file): their units are lost, so the values are lower bounds
    (hypotheses 493, 507, 642: 92% of such cords end in 0 against 27% of intact ones)."""
    try:
        S = sheets(ROOT / "data/kfg_2026/xlsx" / f"{code}.xlsx")
    except Exception:
        return None
    hdr = S["Cords"][0]
    col = {h: i for i, h in enumerate(hdr)}
    get = lambda r, h: r[col[h]] if col.get(h) is not None and col[h] < len(r) else ""
    rows, units = [], []
    for r in S["Cords"][1:]:
        if not r or not re.fullmatch(r"p\d+", r[0] or ""):
            continue
        try:
            v, ln = int(float(get(r, "Value") or 0)), float(get(r, "Length") or 0)
        except ValueError:
            continue
        cl = sorted((float(p), int(x)) for p, x in re.findall(r"\d+[A-Z]+\(([\d.]+),[SZU]\),(\d+)", get(r, "Knots") or "") if int(x))
        if cl and v % 10 and cl[-1][1] == v % 10:
            units.append(cl[-1][0])
        rows.append((r[0], v, ln, str(get(r, "Termination")).strip().upper()))
    if len(units) < 5:
        return None
    u = statistics.median(units)
    cut = [(c, v) for c, v, ln, t in rows if t == "B" and v >= 10 and 0 < ln < u - 1]
    return (u, cut) if len(cut) >= 2 else None


def main():
    c = sqlite3.connect(ROOT / "data/open-khipu-repository/data/khipu.db")
    kfg = {(n or "").strip(): (o or "").strip() for n, o in c.execute("select INVESTIGATOR_NUM, OKR_NUM from khipu_main") if o}
    for r in csv.DictReader(open(ROOT / "atlas/curated/kfg_names.csv")):
        for i in [r["khipu"]] + [a.strip() for a in r["aliases"].split(";") if a.strip()]:
            if i and r["kfg"]:
                kfg.setdefault(i, r["kfg"])
        kfg.setdefault(r["kfg"], r["kfg"])
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
    for k, cord, okr_v, kfg_v, rel in SUMS:
        notes[k]["reading"].append(f"Cord {cord}: the OKR value is {okr_v}, the KFG 2026 value {kfg_v}. Group arithmetic supports the "
                                   f"{'OKR' if 'OKR' in rel.split(':')[0] else 'KFG'} reading: {rel.split(':', 1)[1].strip()}")
    alt = ROOT / "extracted/alt_supported.txt"
    if alt.exists():
        for line in alt.read_text().splitlines():
            k, _, cord, v, a, gap, verdict = line.split("\t")
            long_, short = (a, v) if len(a) > len(v) else (v, a)
            if verdict != "alt" or long_.rstrip("0") == short.rstrip("0"):
                continue  # a trailing zero: the gap between clusters cannot decide it
            why = ("about two place steps, as an empty place in between would give" if float(gap) > 1.6
                   else "about one place step, so no empty place lies in between")
            notes[k]["reading"].append(
                f"Cord {cord}: Value {v}, Alt_Value {a}. The widest gap between its knot clusters is {gap} times the usual gap "
                f"between neighbouring places on this khipu, {why}; this supports the Alt_Value {a}.")
    OUT.mkdir(parents=True, exist_ok=True)
    for k in [k for k in notes if any(notes[k].values())]:
        lb = lower_bounds(kfg.get(k, "")) if kfg.get(k) else None
        if lb:
            u, cut = lb
            shown = ", ".join(f"{c} ({v})" for c, v in cut[:15]) + (f" and {len(cut) - 15} more" if len(cut) > 15 else "")
            notes[k]["reading"].append(
                f"Broken above the units zone: {shown}. These pendants end in a break (B) shorter than the usual height of the units knots "
                f"on this khipu ({u:g} cm), so their units knots are lost and the values are lower bounds. Over the corpus 92% of such cords "
                f"end in 0, against 27% of intact ones; the rule holds for subsidiaries too.")
    bycode = defaultdict(list)
    for k in sorted(notes):
        code = kfg.get(k, "")
        if code and (ROOT / "data/kfg_2026/xlsx" / f"{code}.xlsx").exists() and any(notes[k].values()):
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
