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


CONTEXT = [  # (kind, label, lat, lon, note) — approximate positions for orientation
    ("centre", "Chan Chan", -8.105, -79.075, "Chimu capital"), ("centre", "Farfán", -7.25, -79.47, "Chimu–Inka centre; floor yupana"),
    ("centre", "Manchán", -9.47, -78.30, "Chimu–Inka centre; floor yupana"), ("centre", "Paramonga", -10.67, -77.83, "Fortress"),
    ("centre", "Caral", -10.89, -77.52, "Supe valley"), ("centre", "Huarco / Cerro Azul", -13.02, -76.48, "Guarco capital"),
    ("centre", "Huánuco Pampa", -9.87, -76.94, "Inka administrative centre"), ("centre", "Hatun Xauxa (Jauja)", -11.77, -75.50, "Huanca khipu accounts, 1533–1561"),
    ("centre", "Vilcashuamán", -13.65, -73.95, "Inka provincial centre"), ("centre", "Chucuito", -15.89, -69.89, "Lupaqa accounts, 1567"),
    ("centre", "Cajamarca", -7.16, -78.51, "Inka centre; 1532"), ("centre", "Chincha", -13.42, -76.13, "Coastal lordship"),
    ("valley", "Jequetepeque", -7.35, -79.60, ""), ("valley", "Moche", -8.15, -78.98, ""), ("valley", "Casma", -9.47, -78.40, ""),
    ("valley", "Supe", -10.80, -77.72, ""), ("valley", "Huaura", -11.12, -77.52, ""), ("valley", "Chancay", -11.52, -77.20, ""),
    ("valley", "Chillón", -11.90, -77.08, ""), ("valley", "Rímac", -12.02, -77.00, ""), ("valley", "Lurín", -12.22, -76.82, ""),
    ("valley", "Cañete", -13.05, -76.30, ""), ("valley", "Pisco", -13.65, -76.10, ""), ("valley", "Ica", -14.25, -75.70, ""),
    ("valley", "Río Grande (Nazca)", -14.75, -75.15, ""), ("valley", "Acarí", -15.35, -74.55, ""), ("valley", "Lluta", -18.35, -70.20, ""),
    ("valley", "Loa", -21.45, -70.00, ""),
    ("city", "Lima", -12.046, -77.043, ""), ("city", "Trujillo", -8.11, -79.03, ""), ("city", "Arequipa", -16.40, -71.54, ""),
    ("city", "Cusco", -13.53, -71.97, ""), ("city", "Arica", -18.48, -70.31, ""), ("city", "Tumbes", -3.57, -80.45, ""),
    ("suyu", "Chinchaysuyu", -9.3, -76.4, "North-western quarter"), ("suyu", "Antisuyu", -12.6, -71.2, "Eastern quarter"),
    ("suyu", "Collasuyu", -18.2, -68.9, "South-eastern quarter"), ("suyu", "Contisuyu", -15.6, -73.4, "South-western quarter"),
]
ROADS = [  # schematic trunk routes of the Inka road, approximate
    ("coastal", [(-3.57, -80.45), (-5.2, -80.6), (-7.25, -79.47), (-8.1, -79.0), (-8.98, -78.63), (-9.47, -78.3), (-10.67, -77.83),
                 (-11.1, -77.6), (-11.57, -77.27), (-12.05, -77.04), (-12.256, -76.9), (-13.02, -76.48), (-13.42, -76.13),
                 (-14.07, -75.73), (-14.83, -74.94), (-15.43, -74.62)]),
    ("highland", [(-3.99, -79.2), (-7.16, -78.51), (-9.87, -76.94), (-11.77, -75.5), (-13.65, -73.95), (-13.53, -71.97),
                  (-15.89, -69.89), (-18.0, -67.8)]),
]
TIMELINE = [
    ("c. 1400–1532", "Inka period", "Most khipus of the corpus date to the Inka period; radiocarbon dates, where tested, fall here.", None),
    ("1533–1548", "Huanca lords record what they gave the Spaniards", "Their khipus, read out in court, keep the shares of the valley's three parts, 4 : 2 : 3 (Chirinos 2010).", None),
    ("1558 / 1561", "A summary khipu equals twelve detail khipus", "Hatun Xauxa's summary of 1558 is the sum of the detail khipus shown in 1561 (Chirinos 2010). No such pair survives in the corpus.", None),
    ("1583", "Third Council of Lima", "The council orders khipus to be destroyed; the court record of khipu readings ends soon after.", None),
    ("1872", "Wilhelm Gretzer arrives in Peru", "A textile merchant from Hanover, he builds the largest collection of its time, mostly from grave robbers.", None),
    ("1882", "Macedo collection to Berlin", "Berlin buys about 2,400 objects from José Mariano Macedo of Lima.", None),
    ("1882–1923", "Eduard Gaffron practises medicine in Lima", "His collection later reaches Berlin (the Huacho khipus VA 63038–63044), Detmold and other museums.", "huacho1"),
    ("1896", "Max Uhle excavates at Pachacamac", "The first systematic excavation of the sanctuary.", None),
    ("1899", "Baessler gift", "Arthur Baessler gives Berlin about 11,690 objects.", None),
    ("1904", "Khipus 'between Ica and Pisco' reach Berlin", "Among them AS114, whose block recurs on AS123.", "known"),
    ("1906–1907", "Berlin buys Gretzer's collection", "About 40,000 objects, most labelled Pachacamac, among them UR212, AS131, AS170 and AS175.", "frame14"),
    ("1907", "The Ica khipus AS143, AS149, AS179 enter Berlin", "One allocation spread over three khipus of the same batch.", "berlin"),
    ("1909", "Gaffron khipus in Detmold", "Entered with other objects from his collection.", None),
    ("1910", "Basel buys khipus dug near Huacho", "The ship's doctor Arnold Masarey sells a cache of cords; the museum's report calls them calendar records.", "basel"),
    ("1924", "Nordenskiöld mounts the Huacho khipus", "Ten fragments and loose cords are sewn onto a cloth, IVc.366.03, and pieces face both ways.", "basel"),
    ("1925", "Nordenskiöld's calendar reading", "He publishes the calendar hypothesis but not the Basel khipus.", None),
    ("1978, 1988", "The Aschers' Databooks", "Cord-by-cord records of more than 200 khipus, with observations such as the 7 + 7 parts of AS131 and AS170.", "frame14"),
    ("2013–2014", "Inkawasi storehouse excavated", "Alejandro Chu recovers 34 khipus, some under chili peppers, peanuts and black beans.", "inkawasi"),
    ("2015, 2019", "Urton & Chu on Inkawasi", "Matched pairs and fixed deductions 10, 15, 47, 208.", "ur269"),
    ("2016", "Conklin khipus at Dumbarton Oaks", "UR297 and UR298 enter the collection.", "dumbarton"),
    ("2017", "Huacones-Vilcahuasi", "Eleven khipus found rolled together near a chili storeroom and a floor yupana.", None),
    ("2022", "Medrano traces the Basel khipus to Huacho", "The museum archive names the burial ground near Huacho and the 1924 mounting.", "basel"),
    ("2026", "This atlas", "Corpus-wide search: every link between surviving khipus is a copy of one account.", None),
]


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
    kids = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_do_cords.csv")):
        if r["parent_id"]:
            kids[r["parent_id"]].append(r)
    comp = build_compare({k: v for k, v in pend.items()}, kids)
    for f in FINDINGS:
        f["compare"] = comp.get(f["id"], [])
    edges = [{"from": a, "to": b, "type": t, "finding": f, "note": n} for a, b, t, f, n in EDGES if a in ids and b in ids]
    dups = [{"a": a, "b": b, "note": n} for a, b, n in DUPLICATES if a in ids and b in ids]
    data = {"built": "2026-09-30", "khipus": khipus, "sites": sites, "edges": edges, "edgeTypes": EDGE_TYPES,
            "duplicates": dups, "findings": FINDINGS, "negatives": [{"title": a, "text": b} for a, b in NEGATIVES],
            "sources": [{"title": a, "url": u, "use": w} for a, u, w in SOURCES], "undigitized": undig,
            "context": [{"kind": a, "label": b, "lat": c, "lon": d, "note": e} for a, b, c, d, e in CONTEXT],
            "roads": [{"kind": a, "pts": [[lo, la] for la, lo in pts]} for a, pts in ROADS],
            "timeline": [{"when": a, "title": b, "text": c, "finding": d} for a, b, c, d in TIMELINE],
            "scriptBase": KHIPU_URL}
    s = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(s)
    print(f"khipus {len(khipus)}; sites {len(sites)}; edges {len(edges)}; dups {len(dups)}; undigitized {len(undig)}; "
          f"{len(s) // 1024} KB; unplaced {sum(1 for x in khipus if not x['site'])}")


if __name__ == "__main__":
    main()
