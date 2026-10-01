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

Standalone copy for Vercel or any static host (wraps the page, adds data files and licence notices to dist/):

```
python3 khipu/site_export.py https://<project>.vercel.app && npx vercel deploy dist --prod
```

The site (`site/index.html`) reads only the exported `site/data.json` and `site/kd/*.json`.
