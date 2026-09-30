# khipu-links

A corpus-wide search for arithmetic links **between** khipus — copies, extracts, sums and
hierarchies of accounts — in the open data of the Open Khipu Repository (OKR) and the
Khipu Field Guide (KFG), about 700 khipus. Every detector is first run on relations already
published, and every result is compared with structure-preserving baselines (targets offset
by ±d, shuffled group order), not only with shuffled values.

- **Preprint** (7 pages): [`docs/preprint/preprint.pdf`](docs/preprint/preprint.pdf)
- **Full report** with tables, methods and caveats: [`report/khipu_links_report.html`](report/khipu_links_report.html) (open in a browser)
- **Study log** (Russian, every step and negative result): [`docs/project_log_ru.md`](docs/project_log_ru.md)

## New results

These relations are, as far as we have checked (the Aschers' databook, Chirinos 2010,
Urton 2014 and 2017, Urton & Chu 2015, 2018, 2019, Medrano 2022, the Khipu-Biblio Cross-Reference), not described in the literature.

| # | Result | Evidence |
|---|---|---|
| 1 | **Berlin / Ica: one allocation on three khipus** (AS143, AS149, AS179; 1907 acquisition). AS143 group 4 = AS149 group 1 + group 2 in all five positions (17436 = 8653 + 8783; 8220 = 4049 + 4171; 41883 = 20640 + 21243; 1350 = 660 + 690; 9528 = 4741 + 4787). All shares have the same composition (22.4 : 10.4 : 54.4 : 12.8 %); in ninths of the AS143 total (180,345) the shares are 2 + 2 + 2 + 2 + 1. AS149 splits its shares into lots; the lot 1430, 670, 3410, 820 (×4) recurs on AS179 as 1430, 670, 3424, 820. | The only exact cross-khipu vector sum in the corpus (`vecsum.py`; offset baseline 0–2, small values only). |
| 2 | **Pachacamac → Huacho: a copy of the details without the totals.** The spliced Huacho khipus UR233 + UR232 (VA63038b) repeat parts 1 and 3 of AS175 (VA42518) group by group, leave out part 2 (the sums of part 3) and add one knotless pendant to every group. Their part-3 values reproduce AS175's own part-2 sums better than AS175 does (8 vs 5 of 15 exactly). | z = 6.4 and 19.5 against other offsets; group-order permutation p ≤ 0.003 (`diagscan.py`, `huacho.py`). Different objects: cords per group, lengths, subsidiaries. |
| 3 | **AS118 links two other Pachacamac khipus.** Groups 2–3 of AS118 (VA42601) repeat groups 2–3 of UR218 (VA42559) cord for cord, including knot counts (five cords broken on AS118, intact on UR218). The five subsidiaries of its first, knotless pendant (2696, 13182, 14658, 11522, 8565) follow the group totals of AS125 (VA42670): 14658 exact; 8565 if an AS125 cord recorded by the Aschers as “?” (knots 3 · 1 · 1 · 1) is 3111. | Among 696 khipus only AS125 matches more than one of the values; none on the offset baseline (`as118.py`). |
| 3a | **Pachacamac → Huacho again: two Berlin khipus joined on a Huacho khipu in Basel.** Six fragments on the cloth Basel IVc.366.03 (dug near Huacho, bought 1910; Medrano 2022) repeat runs of UR212 (VA42508(A); 37 of 195 pendants) and AS131 (VA42510; 25 of 146). UR212 and AS131 each have 14 main groups (14 and 10 cords); every fragment carrying both pairs the same unit (units 1, 4, 14), i.e. the Huacho khipu set the two halves of one 14-unit account side by side. | Other khipus ≥ 100 pendants: at most 4 matching cords (`basel_huacho.py`); same unit 3 of 3, p ≈ 0.005 (`ur212_as131_units.py`). Direction of the runs is not meaningful (two recorders, fragments sewn on in 1924). |
| 3b | **Inkawasi UR269: the deduction is set by the place of the record.** In blocks of five records the deduction is 47, 46, 46, 44, 25 by place, whatever the deposit size (1.9%–4.4% of the mean deposit). Urton & Chu (2015, 2018, 2019) list UR269 as having no repeating value. The five place deductions add up to 208, UR268's fixed deduction, but no record-level link was found. | 33 of 43 deductions equal their place value, 17 when records are shuffled within blocks (p ≈ 0.0005; `slotded.py`, `ur268_269.py`). |
| 4 | **Empty pendants.** 11 khipus with regular groups have an intact, knotless pendant at the same position in ≥ 80% of groups (3.0 expected). In the Inkawasi pair UR255 ~ UR267A the net-value pendant is empty on UR255 in the first 12 deposits and filled with the same values as UR267A in 5 of the last 6; the tied UR256 shows the same order. | `blanks.py`, `fillslot.py`; the pairs themselves are known (Urton & Chu 2015). |

## Known relations recovered or refined

| Result | Status |
|---|---|
| **Lima → Gothenburg.** KH0362 (UR122, Gothenburg 1938.45.0228) copies one branch of KH0049 (AS038/HP036, Lima): a subtotal group and its three addends; 27 of 31 intact pendants equal. | Copy known (Chirinos 2010, pp. 233–234, 339–341); branch mapping and breakage analysis added. |
| **Folded copies.** A separate cord in one copy is a subsidiary in the other: UR270 → UR278 (Inkawasi), UR053C → UR053B (Waterfall set). | Packing rule new; B ≈ C noted by Chirinos (2026). |
| **Subsidiaries do not enter pendant sums** (422 khipus; own values z = 4.4 on an offset baseline; adding subsidiaries z = 2.5, subtracting z = 0.8). | Tested. |
| **Validations:** AS069/AS070 (Thompson 2024), Santa Valley structure, Inkawasi fixed deductions 10/15/47 (Urton & Chu 2015; found nowhere else in the corpus), duplicate recordings, single pendants = sums of neighbouring groups. | Recovered by the detectors. |
| **Published tables reproduced:** Urton & Chu 2019 supplementary table (all OKR values of UR267A/B, UR275, UR268 in order; one difference), Barraza Lescano et al. 2022 Table 3 (our transcription of JC024–JC034, 9 of 11 exact; rows 4 and 8 of the paper swapped). Duplicate recordings read from opposite ends: AS208 = UR083, UR1107 = UR237. | `sup2019.py`, `huacones_table3.py`, `excerpts.py`. |

## Negative results

Huacones-Vilcahuasi chain of totals (JC024–JC034, our transcription) — not above an offset
baseline; no further links in the Berlin 1907 batch; no colonial transcription matches a
digitized khipu; the Berlin composition matches neither colonial censuses nor the Chincha
tasa; colour is not carried into copies and does not mark the product at Inkawasi; knot
direction is not carried into the Waterfall copy; cord twist does not separate larger and
smaller values; Urton's (2014) six “similar” Pachacamac pairs do not share values; the
non-decimal “signs” of Wari-style khipus recur across khipus but have far too small an
alphabet for syllables (compared with Quechua syllable statistics); opposite recto/verso attachment is not a general rule of copies (7 of 10 pairs, p ≈ 0.17); no fixed supplier order across Inkawasi khipus; values on broken cords are uncertain, not simply too small (exact sums 35% vs 68%, no directional bias).

## Repository layout

- `khipu/` — loaders and detectors (Python 3, standard library only).
- `extracted/` — our own tables and the output of every scan (`*.txt`): numbers transcribed
  from colonial documents (`J1`, `C1`–`C6`, `S1*`, `A1`, `H1`; schema in `SCHEMA.md`) and the
  Huacones transcriptions (`huacones_*.csv`).
- `report/` — the HTML report. `docs/` — preprint and study log.

Third-party data and publications are **not** included; download them as below.

## Reproducing

```bash
# 1. Open Khipu Repository (MIT licence)
git clone https://github.com/khipulab/open-khipu-repository data/open-khipu-repository

# 2. KFG companion data (Khosla & Medrano, Zenodo 10.5281/zenodo.8125718)
mkdir -p data/kfg && curl -L -o data/kfg/kfg_article_v2.zip \
  "https://zenodo.org/api/records/8125718/files/khipufieldguide/data-science-khipu-article-v2.0.0.zip/content"
unzip data/kfg/kfg_article_v2.zip -d data/kfg/zen && \
  mv data/kfg/zen/khipufieldguide-data-science-khipu-article-* data/kfg/kfg_article

# 3. Build the corpora
python3 khipu/kfg_import.py          # KFG MySQL dump -> data/kfg/kfg.db
python3 khipu/okr.py okr             # -> extracted/okr_cords.csv
python3 khipu/okr.py kfg             # -> extracted/kfg_cords.csv
python3 khipu/newokr.py              # + post-2017 OKR khipus -> extracted/plus_cords.csv

# 4. Main results
python3 khipu/vecsum.py              # result 1: cross-khipu vector sums
python3 khipu/berlin1907.py          # result 1: the Berlin 1907 batch
python3 khipu/diagscan.py            # result 2 and known copies: group-diagonal alignment
python3 khipu/huacho.py              # result 2: AS175 vs UR233 / UR232, part-2 sums
python3 khipu/as118.py               # result 3
python3 khipu/blanks.py              # result 4: empty pendants
python3 khipu/fillslot.py            # result 4: UR255 ~ UR267A
python3 khipu/pair_lg.py             # Lima -> Gothenburg
python3 khipu/subsrule.py            # subsidiaries in sums
python3 khipu/taxscan.py             # fixed deductions (Inkawasi only)

# Optional: Quechua comparison (Quechua Wikipedia dump, CC BY-SA, ~13 MB)
mkdir -p data/quechua && curl -L -o data/quechua/quwiki-latest-pages-articles.xml.bz2 \
  https://dumps.wikimedia.org/quwiki/latest/quwiki-latest-pages-articles.xml.bz2
python3 khipu/signs.py && python3 khipu/quechua.py
```

## Sources and credits

- Open Khipu Repository, https://github.com/khipulab/open-khipu-repository (doi:10.5281/zenodo.18025748).
- Khipu Field Guide, A. Khosla and M. Medrano, https://www.khipufieldguide.com; companion data doi:10.5281/zenodo.8125718.
- K. M. Thompson, Khipu-Biblio Cross-Reference (KBCR) v9, doi:10.26188/25661322; “A Numerical Connection Between Two Khipus”, *Ñawpa Pacha* 45(1), 2024.
- M. Ascher and R. Ascher, *Code of the Quipu: Databook* (1978; online edition, Cornell) and *Code of the Quipu* (1981).
- A. Chirinos Rivera, *Quipus del Tahuantinsuyo* (2010); G. Urton, *Quipus de Pachacamac* (2014); G. Urton and A. Chu (2015, 2019) on Inkawasi.
- Colonial transcriptions from open-access publications listed in `docs/project_log_ru.md`.

The code and analyses were developed with the assistance of an AI model (Claude, Anthropic);
all results were checked against the source records.

Code: MIT licence (see `LICENSE`). Tables in `extracted/` derived from published sources remain
subject to those sources' terms. Contact: Vladimir Muravev, aderby3d@gmail.com.
