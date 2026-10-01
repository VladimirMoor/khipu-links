# Khipu Links Atlas — data

The atlas keeps its data apart from the web page.

- `curated/` — hand-edited tables, the only place to change what the atlas says:
  `sites.csv`, `site_rules.csv` (provenance text → place), `context.csv` (centres, valleys, cities, quarters),
  `roads.json`, `links.csv` + `link_types.csv`, `duplicates.csv`, `findings.json`, `negatives.csv`,
  `sources.csv`, `timeline.csv`, `corrections.csv` (readings we propose; applied to cord values only when `applied` = yes).
- `atlas.db` — SQLite database built from the corpus (OKR, KFG, our transcriptions) and `curated/`
  (not in git: it contains KFG cord data). Tables: `khipu`, `cord` (catalogue layer), `model_cord`, `model_knot`,
  `model_meta` (3D layer: okr / sheet / recon), plus one table per curated file and `undigitized` (Berlin records).

Rebuild after any change:

```
python3 khipu/atlas_db.py && python3 khipu/site_build.py && python3 khipu/site_knots.py && python3 khipu/terrain.py
```

Standalone copy for Vercel or any static host (wraps the page, adds data files and licence notices to dist/). The branch `site` of this repository holds only that copy; Vercel deploys it from GitHub (Production Branch = site, Framework = Other, no build command). Update it with `sh khipu/site_publish.sh https://khipu-links.vercel.app`. By hand:

```
python3 khipu/site_export.py https://<project>.vercel.app && npx vercel deploy dist --prod
```

The site (`site/index.html`) reads only the exported `site/data.json`, `site/kd/*.json` and `site/i18n/<lang>.json`.

## Languages

The page is written in English. Translations live in `curated/i18n/<lang>.json` (now `es`, `ru`, `de`), keyed by the
English text: `ui.static` (short strings in the markup), `ui.mixed` (HTML blocks marked `data-i18n-html`, such as the
*Start here* page), `ui.dyn` (strings passed to `tr()` in the code) and `content` (findings by id; timeline, negative
results and sources by their English title; link types). `site_build.py` copies them to `site/i18n/`, and the page
loads one only when a reader picks that language. Anything without a translation is shown in English.

`python3 khipu/i18n_source.py` writes `curated/i18n/en_source.json`, the full list of English strings to translate,
and reports what each language still lacks. To add a language: translate `en_source.json` into `curated/i18n/<lang>.json`,
add the code to `LANGS` and a button in `.lang` in `site/index.html`, and rebuild.
