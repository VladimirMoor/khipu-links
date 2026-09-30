"""Данные для сайта-каталога (site/data.json): кипу, места, связи, находки, отрицательные результаты, источники.

Кипу — все с шнурами в extracted/plus_do_cords.csv (KFG + новые OKR + наши расшифровки UR297/UR298), подвесные
по порядку с группой, значением и цветом. Собиратели берлинских кипу — из карточек museum-digital (data/smb).
Берлинские кипу без оцифровки шнуров — отдельным списком (номер, собиратель, строка «Groups» карточки).
Координаты мест — приблизительные (уровень поселения/долины), заданы вручную ниже.
"""
import csv
import itertools
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site/data.json"

SITES = {  # key: (label, lat, lon, region)
    "pachacamac": ("Pachacamac", -12.256, -76.900, "Central coast"),
    "huacho": ("Huacho", -11.108, -77.610, "Central coast"),
    "huaura": ("Huaura valley (Santa Rosalía)", -11.080, -77.580, "Central coast"),
    "inkawasi": ("Inkawasi (Cañete)", -12.910, -76.130, "South-central coast"),
    "huacones": ("Huacones-Vilcahuasi (Cañete)", -13.050, -76.430, "South-central coast"),
    "ica": ("Ica", -14.070, -75.730, "South coast"),
    "icapisco": ("Between Ica and Pisco", -13.900, -75.950, "South coast"),
    "ocucaje": ("Ocucaje / Callango (Ica)", -14.370, -75.670, "South coast"),
    "nazca": ("Nazca", -14.830, -74.940, "South coast"),
    "atarco": ("Atarco (Nazca)", -14.930, -74.980, "South coast"),
    "paracas": ("Paracas / Pisco", -13.780, -76.230, "South coast"),
    "tambocolorado": ("Tambo Colorado", -13.460, -75.940, "South coast"),
    "acari": ("Acarí", -15.430, -74.620, "South coast"),
    "leymebamba": ("Leymebamba (Laguna de los Cóndores)", -6.710, -77.800, "Northern highlands"),
    "santa": ("Santa valley", -8.980, -78.630, "North coast"),
    "huaquerones": ("Puruchuco-Huaquerones (Lima)", -12.050, -76.930, "Central coast"),
    "armatambo": ("Armatambo (Lima)", -12.170, -77.020, "Central coast"),
    "lima": ("Lima", -12.050, -77.040, "Central coast"),
    "chuquitanta": ("El Paraíso / Chuquitanta", -11.950, -77.120, "Central coast"),
    "chancay": ("Chancay", -11.570, -77.270, "Central coast"),
    "cajamarquilla": ("Cajamarquilla", -11.990, -76.870, "Central coast"),
    "cieneguilla": ("Cieneguilla (Lurín)", -12.100, -76.800, "Central coast"),
    "arica": ("Arica / Lluta (Chile)", -18.450, -70.250, "Far south"),
    "quillagua": ("Quillagua (Loa, Chile)", -21.660, -69.540, "Far south"),
    "cuzco": ("Cuzco", -13.530, -71.970, "Southern highlands"),
    "huari": ("Huari (Ayacucho)", -13.060, -74.200, "Southern highlands"),
}
RULES = [("achacam", "pachacamac"), ("pachacmac", "pachacamac"), ("santa rosalia", "huaura"), ("huaura", "huaura"),
         ("huacho", "huacho"), ("incahuasi", "inkawasi"), ("huacones", "huacones"), ("between ica and pisco", "icapisco"),
         ("ica/pisco", "icapisco"), ("ocucaje", "ocucaje"), ("callang", "ocucaje"), ("ullujal", "ocucaje"),
         ("ullujay", "ocucaje"), ("atarco", "atarco"), ("nazca", "nazca"), ("copara", "nazca"), ("paracas", "paracas"),
         ("pisco", "paracas"), ("tambo colorado", "tambocolorado"), ("acari", "acari"), ("leymebamba", "leymebamba"),
         ("santa", "santa"), ("huaquerones", "huaquerones"), ("armatambo", "armatambo"), ("huaca san pedro", "armatambo"),
         ("chuquitanta", "chuquitanta"), ("chancay", "chancay"), ("huando", "chancay"), ("cajamarquilla", "cajamarquilla"),
         ("cieneguilla", "cieneguilla"), ("lluta", "arica"), ("arica", "arica"), ("mollepampa", "arica"),
         ("quillagua", "quillagua"), ("cuzco", "cuzco"), ("huari", "huari"), ("maranga", "lima"), ("pueblo libre", "lima"),
         ("huaca perez", "lima"), ("la molina", "lima"), ("rimac", "lima"), ("near lima", "lima"), ("lima", "lima"),
         ("ica", "ica")]

KHIPU_URL = "https://github.com/VladimirMoor/khipu-links/blob/main/khipu/"

# Relations between khipus: (from, to, type, finding id, note)
EDGES = [
    ("UR1149", "UR1143", "sum", "berlin", "AS143 group 4 = AS149 groups 1 + 2 in all five positions"),
    ("UR1149", "UR1179", "lot", "berlin", "The lot 1430, 670, 3410, 820 recurs as 1430, 670, 3424, 820"),
    ("UR1175", "UR233", "details", "huacho1", "Parts 1 and 3 of AS175 copied group by group, totals left out"),
    ("UR1175", "UR232", "details", "huacho1", "Part 3 of AS175 continued on the spliced second khipu"),
    ("UR218", "UR1118", "excerpt", "as118", "Groups 2–3 of AS118 repeat groups 2–3 of UR218, knot counts included"),
    ("AS125", "UR1118", "totals", "as118", "The five subsidiaries of AS118's first cord follow the group totals of AS125"),
    ("UR212", "MM008", "join", "basel", "UR212 unit 14 (cords 1–12)"),
    ("UR212", "MM012", "join", "basel", "UR212 cords 97–100"),
    ("UR212", "MM014", "join", "basel", "UR212 cords 167–169"),
    ("UR212", "MM015", "join", "basel", "UR212 unit 1 (cords 182–194), 13 of 13"),
    ("UR212", "MM016", "join", "basel", "UR212 unit 4 (cords 139–148)"),
    ("UR1131", "MM008", "join", "basel", "AS131 unit 14 (cords 137–146)"),
    ("UR1131", "MM009", "join", "basel", "AS131 cords 127–132"),
    ("UR1131", "MM015", "join", "basel", "AS131 unit 1 (cords 1–9), marked slot filled"),
    ("UR1131", "MM016", "join", "basel", "AS131 unit 4 (cords 35–39)"),
    ("UR274B", "UR273B", "totals", "inkawasi", "UR273B records only the deposit totals of UR274B"),
    ("UR267A", "UR255", "copy", "inkawasi", "Matched pair (Urton & Chu 2015); net slots empty then filled on UR255"),
    ("UR267B", "UR256", "copy", "inkawasi", "Matched pair (Urton & Chu 2015)"),
    ("UR266", "UR275", "copy", "inkawasi", "Shared deposits with deduction 47 (Urton & Chu 2015)"),
    ("UR278", "UR270", "fold", "folded", "A separate cord in one copy is a subsidiary in the other"),
    ("UR053C", "UR053B", "fold", "folded", "Waterfall set: triples in C packed into pairs in B"),
    ("KH0049", "UR122", "excerpt", "known", "Lima → Gothenburg: one branch of the account (Chirinos 2010)"),
    ("HP055", "UR1084", "copy", "known", "Lima ↔ Paris copy (Chirinos 2010)"),
    ("UR1114", "UR1123", "excerpt", "known", "AS123 group 5 = one block of AS114 (Urton 2005)"),
    ("AS215", "AS003", "totals", "as003", "AS003 records only the summary part of AS215, with its total 76"),
    ("UR066", "UR067", "copy", "known", "Puruchuco matching pair"),
    ("AS069", "AS070", "sum", "known", "Thompson 2024"),
]
EDGE_TYPES = {
    "sum": "Sum across khipus", "lot": "Shared lot", "details": "Details without totals", "excerpt": "Excerpt",
    "totals": "Totals only", "join": "Two accounts joined", "copy": "Matching copy", "fold": "Folded copy",
}
DUPLICATES = [("AS208", "UR083", "one khipu, recorded twice and read from opposite ends"),
              ("UR1107", "UR237", "one khipu, recorded twice, read from opposite ends"),
              ("AS046", "HP041", "one khipu, recorded twice"), ("AS086", "MM1086", "one khipu, recorded twice"),
              ("AS038", "HP036", "one khipu, recorded twice"), ("AS070", "UR035", "one khipu, recorded twice")]

FINDINGS = [
    {"id": "basel", "status": "new", "title": "Two Pachacamac accounts joined on a Huacho khipu",
     "place": ["pachacamac", "huacho"],
     "summary": "Six fragments sewn on the Basel cloth IVc.366.03 (dug near Huacho, bought 1910) repeat runs of two Berlin khipus labelled Pachacamac: UR212 (37 of 195 pendants) and AS131 (25 of 146). UR212 and AS131 each have 14 main groups, divided 7 + 7 at the same point. Every fragment that carries both khipus pairs the same unit (units 1, 4 and 14), so the Huacho khipu set the two halves of one 14-unit account side by side, 14 + 10 cords per unit.",
     "evidence": ["Other khipus with ≥ 100 pendants match at most 4 cords (median 0).",
                  "Same unit in 3 of 3 fragments: p ≈ (1/14)² ≈ 0.005.",
                  "Where Berlin leaves a colour-marked cord knotless, the Basel copy carries a value (3 of 3); other knotless cords stay knotless.",
                  "Unit totals of UR212 and AS131 are not correlated (ρ = 0.19): different categories of the same units."],
     "khipus": ["UR212", "UR1131", "MM008", "MM009", "MM012", "MM014", "MM015", "MM016"],
     "scripts": ["basel_huacho.py", "ur212_as131_units.py", "basel_slots.py", "halves_columns.py"]},
    {"id": "frame14", "status": "suggestive", "title": "A 14-unit frame in Gretzer's Berlin batch",
     "place": ["pachacamac"],
     "summary": "Fourteen main groups are rare (1.6% of khipus outside the Berlin 'Pachacamac' batch) but occur on 4 of 23 khipus of that batch: UR212, AS131, AS170 and UR199. Berlin catalogue records describe three more that are not digitized: VA 42513 (14 × 13 pendants), VA 42537 (14 × 9) and VA 42532 (7 × A, 7 × B, 7 × A, 7 × B). AS131, UR212 and AS170 split their units 7 + 7 at the same place, each marked differently: a larger space, a single knotless cord, a marker.",
     "evidence": ["Binomial P ≈ 0.0005 with all four; P ≈ 0.04 without the two khipus that prompted the question.",
                  "Across 109 OKR khipus with an even number of main groups, the largest space falls in the middle 12.9 times (13.0 expected): equal halves are not a general habit."],
     "khipus": ["UR212", "UR1131", "AS170", "UR199"], "scripts": ["units14.py", "halves.py"]},
    {"id": "berlin", "status": "new", "title": "One allocation on three Ica khipus (Berlin, 1907)",
     "place": ["ica"],
     "summary": "AS143 group 4 equals AS149 groups 1 + 2 in all five positions (17436 = 8653 + 8783, 41883 = 20640 + 21243, …). All shares have the same composition (22.4 : 10.4 : 54.4 : 12.8 %); in ninths of the AS143 total the shares are 2 + 2 + 2 + 2 + 1. The lot 1430, 670, 3410, 820 recurs on AS179.",
     "evidence": ["The only exact cross-khipu vector sum in the corpus (offset baseline 0–2, small values only).",
                  "Two 2/9 shares of AS143 are equal within 1 (41062 and 41061) with a substitution between goods (p ≈ 0.005)."],
     "khipus": ["UR1143", "UR1149", "UR1179"], "scripts": ["vecsum.py", "lotmatch.py"]},
    {"id": "huacho1", "status": "new", "title": "Pachacamac → Huacho: the details without the totals",
     "place": ["pachacamac", "huacho"],
     "summary": "The spliced Huacho khipus UR233 + UR232 (Berlin VA 63038b, Gaffron) repeat parts 1 and 3 of AS175 (VA 42518, Gretzer) group by group, leave out part 2 (the sums of part 3) and add one knotless pendant to every group.",
     "evidence": ["z = 6.4 and 19.5 against other offsets; group-order permutation p ≤ 0.003.",
                  "Different objects: cords per group, lengths and subsidiaries differ."],
     "khipus": ["UR1175", "UR233", "UR232"], "scripts": ["diagscan.py", "huacho.py"]},
    {"id": "as118", "status": "new", "title": "AS118 links two other Pachacamac khipus",
     "place": ["pachacamac"],
     "summary": "Groups 2–3 of AS118 repeat groups 2–3 of UR218 cord for cord, knot counts included. The five subsidiaries of its first, knotless pendant follow the group totals of AS125: 14658 exact, 8565 if one cord the Aschers left unread is 3111.",
     "evidence": ["Among 696 khipus only AS125 matches more than one of the five values; none on the offset baseline."],
     "khipus": ["UR1118", "UR218", "AS125"], "scripts": ["as118.py"]},
    {"id": "ur269", "status": "new", "title": "Inkawasi UR269: the deduction is set by the place of the record",
     "place": ["inkawasi"],
     "summary": "In blocks of five records [gross, net, deduction] the deduction is 47, 46, 46, 44, 25 by place, whatever the deposit size (1.9% in places 2–4, 3.0% in place 1, 4.4% in place 5). Urton & Chu (2015, 2018, 2019) list UR269 as having no repeating value. The five place deductions add up to 208, the fixed deduction of UR268 from the same room, but no record-level link was found.",
     "evidence": ["33 of 43 deductions equal their place value; 17 when records are shuffled within blocks (p ≈ 0.0005).",
                  "No other Inkawasi khipu shows a place dependence (all p > 0.8)."],
     "khipus": ["UR269", "UR268"], "scripts": ["slotded.py", "ur268_269.py"]},
    {"id": "inkawasi", "status": "new", "title": "Inkawasi: empty slots, totals-only copies, product labels",
     "place": ["inkawasi"],
     "summary": "On UR255 the net pendant is empty in the first 12 deposits and filled with the values of UR267A in 5 of the last 6. UR273B records only the deposit totals of UR274B (6 shared totals, 0.45 expected). Copies lie in a different bundle from their counterparts. A red tassel at the start of the primary cord occurs only on peanut khipus (2 of 4 against 0 of 25).",
     "evidence": ["Split this clean under random placement: about 1 in 3,000.", "UR273B ~ UR274B: Poisson p ≈ 10⁻⁵."],
     "khipus": ["UR255", "UR267A", "UR256", "UR267B", "UR273B", "UR274B", "UR266", "UR275"],
     "scripts": ["fillslot.py", "blanks.py"]},
    {"id": "as003", "status": "new", "title": "AS003: a record of the totals only",
     "place": ["nazca"],
     "summary": "AS003 (Heye 17/8827) repeats the summary part of AS215 (Hood Museum, Nazca): six values that are sums over the four groups of its other part, and the top cord 76 that totals them. It is a second totals-only record, after UR273B at Inkawasi.",
     "evidence": ["The Aschers' AS215 entry (Databook pp. 127–132) describes the summary but does not mention AS003."],
     "khipus": ["AS003", "AS215"], "scripts": ["mirror.py"]},
    {"id": "folded", "status": "known-refined", "title": "Folded copies",
     "place": ["inkawasi"],
     "summary": "In two independent cases a separate cord in one copy is a subsidiary in the other: UR270 → UR278 at Inkawasi and UR053C → UR053B in the Waterfall set. The packing rule is ours; the near-duplication of B and C was noted by Chirinos.",
     "evidence": ["UR053B/C: 35 fields match against at most 19 in 2,000 shuffles."],
     "khipus": ["UR270", "UR278", "UR053B", "UR053C"], "scripts": ["records.py", "bagscan.py"]},
    {"id": "known", "status": "known-refined", "title": "Known copies recovered",
     "place": [],
     "summary": "The detectors find, without being told, the copies already published: Lima → Gothenburg (KH0049 → UR122, one branch of the account), Lima ↔ Paris (HP055 ~ AS084), AS114/AS123 (Urton 2005), Puruchuco UR066 ~ UR067, AS069/AS070 (Thompson 2024), and duplicate recordings of one object.",
     "evidence": [], "khipus": ["KH0049", "UR122", "HP055", "UR1084", "UR1114", "UR1123", "UR066", "UR067"],
     "scripts": ["excerpts.py", "segsum.py"]},
    {"id": "dumbarton", "status": "data", "title": "Two Dumbarton Oaks khipus transcribed",
     "place": [],
     "summary": "UR297 (438 pendants, 623 cords) and UR298 (203 pendants, 285 cords), given by Bill Conklin, exist in the OKR only as scans of Urton's handwritten sheets. We transcribed all 65 pages. 74 of the 78 group totals Urton noted on the sheets equal ours. UR297 has 41 groups, mostly ten cords plus one summary cord pulled up like a top cord. Neither khipu is linked to any other.",
     "evidence": [], "khipus": ["UR297", "UR298"], "scripts": ["do_ingest.py", "do_check.py"]},
]

NEGATIVES = [
    ("Summary khipus", "No khipu records the group totals or column sums of another beyond chance (384 pairs against 415.6 on the offset baseline)."),
    ("Compilations", "Apart from the Basel fragments, no khipu combines runs from two or more other khipus."),
    ("Colonial documents", "About 2,300 numbers from roughly 70 open transcriptions match no digitized khipu."),
    ("Huacones-Vilcahuasi hierarchy", "Totals of one khipu on the next are at the level of chance (offset baseline)."),
    ("Opposite attachment in copies", "Recto on one copy and verso on the other in 7 of 10 pairs, against 50% at random (p ≈ 0.17)."),
    ("Same suppliers in the same order", "Deposit sizes of different Inkawasi khipus do not correlate by position."),
    ("Copies respect group boundaries", "Run endpoints fall on group boundaries in 38% of cases against 46% expected."),
    ("Broken cords as lower bounds", "Sums with a broken part are exact half as often (35% vs 68%), but the sign shows no loss of knots."),
    ("Equal-share convention", "Pairs of equal-total groups are not over-represented corpus-wide (p ≈ 0.1)."),
    ("Pachacamac style vs Huacho style", "Simple numeric features do not separate site-museum Pachacamac khipus from Huacho khipus."),
    ("Sign convention", "Neither attachment side nor colour marks negative cords."),
    ("Syllables in non-decimal khipus", "The non-decimal signs of Wari-style khipus have far too small an alphabet for syllables."),
    ("Calendar reading", "Group and cord counts give no calendar numbers beyond chance."),
    ("Colour of the product", "Colour is not carried into copies and does not mark the product at Inkawasi."),
]

SOURCES = [
    ("Ascher & Ascher, Code of the Quipu Databook I–II (1978, 1988)", "https://courses.cit.cornell.edu/quipu/", "Cord records and observations for AS khipus; the 7 + 7 parts of AS131 and AS170; AS215's summary part."),
    ("Open Khipu Repository (OKR)", "https://github.com/khipulab/open-khipu-repository", "SQLite database (MIT licence), cord positions, record-sheet scans of UR297/UR298 and Huacones-Vilcahuasi."),
    ("Khipu Field Guide (KFG)", "https://www.khipufieldguide.com/", "Cleaned cord data for about 680 khipus; the 2026 catalogue lists 711."),
    ("Staatliche Museen zu Berlin, museum-digital", "https://smb.museum-digital.de/", "305 khipu records: collectors (Gretzer, Gaffron…) and group descriptions of undigitized khipus."),
    ("Chirinos Rivera, Quipus del Tahuantinsuyo (2010)", None, "Colonial allocations in ninths, summary = sum of details, copies in three exemplars."),
    ("Urton & Chu, Accounting in the King's Storehouse (LAA 2015) and supplements", "https://doi.org/10.7183/1045-6635.26.4.512", "Inkawasi inventory; matched pairs; UR269 listed without a repeating value."),
    ("Urton & Chu, The Invention of Taxation in the Inka Empire (LAA 2019)", "https://doi.org/10.1017/laq.2018.64", "Fixed deductions 10, 15, 47, 208; the 2% proportionality we test on UR269."),
    ("Chu & Urton, El archivo khipu de Incawasi (2018)", None, "Spanish version; table of khipus found with produce."),
    ("Urton, Quipus de Pachacamac (2014)", None, "Inventory of the Berlin Pachacamac khipus."),
    ("Medrano, The promise of Andean khipu transcriptions (MPhil thesis, St Andrews 2022)", "https://research-repository.st-andrews.ac.uk/", "Provenance of Basel IVc.366.03: dug near Huacho, bought 1910; mounted under Nordenskiöld in 1924."),
    ("Barraza Lescano et al., By Stones and by Knots (Andean Past 2022)", None, "Huacones-Vilcahuasi context and Table 3, which checks our transcription."),
    ("Thompson, A Numerical Connection Between Two Khipus (2024)", None, "AS069/AS070, used to validate the detectors."),
    ("Pereyra, Dos quipus excepcionales (1996)", None, "Detailed khipu descriptions."),
    ("Nordenskiöld, Calculations with Years and Months in the Peruvian Quipus (1925)", "https://archive.org/details/b30624642", "Calendar hypothesis; context of the Basel mounting."),
    ("Locke, A Peruvian Quipu (1927)", "https://archive.org/details/peruvianquipu00lock", "A Heye khipu with summary top cords."),
    ("Eeckhout, La sombra de Ychsma (BIFEA 2004)", "https://journals.openedition.org/bifea/5047", "Ychsma organization; no 7 + 7 unit match."),
    ("Lambayeque-style textiles in the Ethnologisches Museum, Berlin (Nuevo Mundo Mundos Nuevos)", "https://journals.openedition.org/nuevomundo/69290", "How Gretzer collected: grave robbers, 'Pachacamac' labels."),
    ("Curatola & de la Puente (eds.), El quipu colonial (2013)", None, "Colonial transcriptions used in the document match."),
    ("Contreras, Structural pattern mining in Inka khipus (arXiv 2026)", "https://arxiv.org/abs/2607.00185", "Santa Valley recto/verso validation."),
]


def site_of(k, prov, museum_num):
    if k.startswith("MM") and str(museum_num) == "IVc.366.03":
        return "huacho"
    p = prov.lower()
    for kw, s in RULES:
        if kw in p:
            return s
    return None


def main():
    meta = {}
    for fn in ("plus_khipus.json", "kfg_khipus.json"):
        for m in json.load(open(ROOT / "extracted" / fn)):
            meta.setdefault(m["INVESTIGATOR_NUM"], m)
    meta.setdefault("UR297", {"MUSEUM_NAME": "Dumbarton Oaks, Washington DC", "MUSEUM_NUM": "PC.WBC.2016.072",
                              "PROVENANCE": "Unknown", "OKR_NUM": "KH0675"})
    meta.setdefault("UR298", {"MUSEUM_NAME": "Dumbarton Oaks, Washington DC", "MUSEUM_NUM": "PC.WBC.2016.071",
                              "PROVENANCE": "Unknown", "OKR_NUM": "KH0674"})
    norm = lambda s: re.sub(r"[^0-9A-Z]", "", str(s).upper())
    coll = {}
    for inv, c, _, _ in json.load(open(ROOT / "data/smb/khipu_collectors.json")):
        coll[norm(inv)] = c
    pend, nall = defaultdict(list), Counter()
    for r in csv.DictReader(open(ROOT / "extracted/plus_do_cords.csv")):
        nall[r["inv_num"]] += 1
        if r["parent_id"] == "":
            pend[r["inv_num"]].append(r)
    edge_k = defaultdict(list)
    for a, b, t, f, _ in EDGES:
        edge_k[a].append(f)
        edge_k[b].append(f)
    find_k = defaultdict(list)
    for f in FINDINGS:
        for k in f["khipus"]:
            find_k[k].append(f["id"])
    khipus = []
    for k, rs in pend.items():
        rs.sort(key=lambda r: int(r["order"]))
        m = meta.get(k, {})
        prov = str(m.get("PROVENANCE") or "").strip('" ')
        mus = str(m.get("MUSEUM_NAME") or "").strip('" ')
        mnum = str(m.get("MUSEUM_NUM") or "").strip('" ')
        groups = [len(list(g)) for _, g in itertools.groupby(rs, key=lambda r: r["group"])]
        vals = [int(r["value"]) for r in rs]
        cols = [r["color"] for r in rs]
        c = coll.get(norm(mnum)) or next((v for kk, v in coll.items() if norm(mnum).startswith(kk) and len(norm(mnum)) - len(kk) <= 2), "")
        if not c and "Gaffron" in prov:
            c = "Gaffron, Eduard"
        alias = ("AS" + k[3:]) if re.fullmatch(r"UR1\d{3}", k) else ""
        khipus.append({"id": k, "alias": alias, "okr": m.get("OKR_NUM") or "", "museum": mus, "num": mnum, "prov": prov,
                       "site": site_of(k, prov, mnum), "collector": c, "np": len(rs), "nc": nall[k],
                       "groups": groups, "v": vals, "c": cols,
                       "max": max(vals) if vals else 0, "sum": sum(vals),
                       "findings": sorted(set(find_k.get(k, []) + edge_k.get(k, [])))})
    khipus.sort(key=lambda x: x["id"])
    ids = {x["id"] for x in khipus}
    site_counts = Counter(x["site"] for x in khipus if x["site"])
    sites = [{"id": s, "label": v[0], "lat": v[1], "lon": v[2], "region": v[3], "n": site_counts.get(s, 0)}
             for s, v in SITES.items() if site_counts.get(s, 0)]
    undig = []
    for f in os.listdir(ROOT / "data/smb/obj"):
        d = json.load(open(ROOT / "data/smb/obj" / f))
        inv = d["object_inventory_number"]
        if any(norm(inv) == norm(x["num"]) or norm(x["num"]).startswith(norm(inv)) for x in khipus if x["num"]):
            continue
        desc = d.get("object_description") or ""
        g = re.search(r"Groups?:\s*([^\n]+)", desc)
        cc = re.search(r"Sammler:\s*([^\n]+)", desc)
        undig.append({"inv": inv, "collector": cc.group(1).strip() if cc else "", "groups": (g.group(1).strip() if g else "")[:140],
                      "url": f"https://smb.museum-digital.de/object/{d['object_id']}"})
    undig.sort(key=lambda x: x["inv"])
    edges = [{"from": a, "to": b, "type": t, "finding": f, "note": n} for a, b, t, f, n in EDGES if a in ids and b in ids]
    dups = [{"a": a, "b": b, "note": n} for a, b, n in DUPLICATES if a in ids and b in ids]
    data = {"built": "2026-09-30", "khipus": khipus, "sites": sites, "edges": edges, "edgeTypes": EDGE_TYPES,
            "duplicates": dups, "findings": FINDINGS, "negatives": [{"title": a, "text": b} for a, b in NEGATIVES],
            "sources": [{"title": a, "url": u, "use": w} for a, u, w in SOURCES], "undigitized": undig,
            "scriptBase": KHIPU_URL}
    s = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(s)
    print(f"khipus {len(khipus)}; sites {len(sites)}; edges {len(edges)}; dups {len(dups)}; undigitized {len(undig)}; "
          f"{len(s) // 1024} KB; unplaced {sum(1 for x in khipus if not x['site'])}")


if __name__ == "__main__":
    main()
