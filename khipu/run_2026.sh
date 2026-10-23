#!/bin/sh
# Прогон основных детекторов на корпусе с данными KFG 2026 (extracted/plus2026_cords.csv).
# Скрипты читают extracted/plus_cords.csv; на время прогона он подменяется и потом всегда восстанавливается.
# Выводы — в extracted/run2026/<script>.out. Числа препринта (reproduce.py) остаются на прежнем корпусе.
set -e
cd "$(dirname "$0")/.."
python3 - <<'PY'
import csv
new = list(csv.DictReader(open("extracted/kfg2026_cords.csv")))
have = {r["inv_num"] for r in new}
old = list(csv.DictReader(open("extracted/plus_do_cords.csv")))
keep = [r for r in old if r["inv_num"] not in have]
fields = list(old[0].keys())
with open("extracted/plus2026_cords.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
    w.writeheader(); w.writerows(keep); w.writerows(new)
print(f"plus2026_cords.csv: {len({r['inv_num'] for r in keep})} khipus kept from the old corpus + {len(have)} from KFG 2026")
PY
mkdir -p extracted/run2026
cp extracted/plus_cords.csv extracted/plus_cords_2023.bak
cp extracted/plus_do_cords.csv extracted/plus_do_cords_2023.bak
trap 'cp extracted/plus_cords_2023.bak extracted/plus_cords.csv; cp extracted/plus_do_cords_2023.bak extracted/plus_do_cords.csv; rm -f extracted/plus_cords_2023.bak extracted/plus_do_cords_2023.bak; git checkout -q -- extracted; echo restored' EXIT
cp extracted/plus2026_cords.csv extracted/plus_cords.csv
cp extracted/plus2026_cords.csv extracted/plus_do_cords.csv
for s in vecsum diagscan lotmatch excerpts compilations summaries ordered_totals small_lots place_constants records; do
  KHIPU_CORDS=extracted/plus_cords.csv timeout 1800 python3 khipu/$s.py > extracted/run2026/$s.out 2>&1 || echo "$s failed"
  echo "$s: $(wc -l < extracted/run2026/$s.out) lines"
done
