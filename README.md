# khipu-links

A corpus-wide search for arithmetic links **between** khipus — copies, summaries and
hierarchies — in the Open Khipu Repository (OKR) and the Khipu Field Guide (KFG) data.
Every detector is checked on relations already known in the literature and every result
is compared with shuffled-corpus baselines.

Preprint (6 pages): [`docs/preprint/preprint.pdf`](docs/preprint/preprint.pdf).
Full write-up with tables, methods and caveats: [`report/khipu_links_report.html`](report/khipu_links_report.html)
(open the file in a browser). A running log of the whole study, in Russian, is in
[`docs/project_log_ru.md`](docs/project_log_ru.md).

## Main results

| # | Result | Status |
|---|---|---|
| 1 | **Berlin AS149 → AS143.** AS149 (KH0165) groups 1 + 2 = AS143 (KH0159) group 4, exactly in 5 of 5 positions (17436 = 8653 + 8783; 41883 = 20640 + 21243 …). With the Aschers' internal sums: five levels across two khipus. Chirinos 2010 reads this group as a fraction of the total; AS149 is not in his book. AS179 (KH0196, same 1907 batch) carries one more parcel of the same allocation (1430, 670, 3424, 820 vs 1430, 670, 3410, 820 ×4 on AS149). | new, as far as checked |
| 2 | **Lima → Gothenburg.** KH0362 (UR122, Museum of World Culture 1938.45.0228, Nasca; Nordenskiöld 1924) copies one branch of KH0049 (AS038/HP036, MNAAHP 3550): the subtotal group and its three addends. 27 of 31 intact pendants equal. | copy known (Chirinos 2010, pp. 233, 339–341); branch mapping and breakage analysis added |
| 3 | **Folded copies.** A separate cord in one copy is a subsidiary in the other: UR270 → UR278 (Incahuasi), UR053C → UR053B (Waterfall set). | new rule; B ≈ C noted by Chirinos 2026 |
| 4 | **Subsidiaries do not enter pendant sums** (422 khipus; pendant-only reading z = 4.4 on an offset baseline; adding them z = 2.5, subtracting z = 0.8). | tested |
| 5 | **Huacones-Vilcahuasi** JC024–JC034 transcribed from the OKR record-sheet photos (tables in `extracted/`). An apparent chain of totals does not survive an offset baseline (z = 1.1). | transcription; link withdrawn |
| 6 | Validations (AS069/AS070, Santa Valley structure, known duplicates) and negative results (colonial documents, sign convention, Waterfall E → B sums, no further links in the Berlin 1907 batch). | checks |
| 7 | **Pachacamac → Huacho.** Two spliced Huacho khipus (UR233 + UR232, VA63038b) repeat parts 1 and 3 of AS175 (VA42518, Pachacamac) group by group, without its summary part 2 and with one empty cord added to every group (z = 6.4 and 19.5). AS118 (VA42601) repeats groups 2–3 of UR218 (VA42559) cord for cord, and the subsidiaries of its first cord follow the group totals of AS125 (VA42670; 14658 exact). | new, as far as checked |

## Repository layout

- `khipu/` — detectors and loaders (Python 3, standard library only).
- `extracted/` — our own tables: numbers transcribed from colonial documents
  (`J1`, `C1`–`C6`, `S1*`, `A1`, `H1`; schema in `SCHEMA.md`), the Huacones transcriptions
  (`huacones_*.csv`), and the outputs of every scan (`*.txt`, `match_*.csv`).
- `report/` — the HTML report.
- `docs/` — study log (Russian).

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

# 4. Examples
KHIPU_CORDS=extracted/kfg_cords.csv python3 khipu/sumscan.py --mode cross --own   # result 1
python3 khipu/pair_lg.py                                                          # result 2
KHIPU_CORDS=extracted/plus_cords.csv python3 khipu/records.py                     # result 3
python3 khipu/subsrule.py                                                         # result 4
python3 khipu/segsum.py --k 6 --n 10                                              # AS069/AS070 check
```

## Data sources and credits

- Open Khipu Repository, https://github.com/khipulab/open-khipu-repository (DOI 10.5281/zenodo.18025748).
- Khipu Field Guide, A. Khosla and M. Medrano, https://www.khipufieldguide.com, companion data Zenodo 10.5281/zenodo.8125718.
- M. Ascher and R. Ascher, *Code of the Quipu: Databook* (1978) and *Code of the Quipu* (1981).
- K. M. Thompson, “A Numerical Connection Between Two Khipus”, *Ñawpa Pacha* 45(1), 2024.
- Colonial transcriptions from open-access publications listed in `docs/project_log_ru.md`.

Code: MIT licence (see `LICENSE`). Tables in `extracted/` derived from published sources remain subject to those sources' terms.
