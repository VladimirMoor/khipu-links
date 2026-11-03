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
# Old-corpus records of khipus that KFG 2026 holds under another name: KFG 2025 codes (KH0049 = AS038 …), second OKR
# records merged by KFG (UR043 = AS030, UR083 = AS208 reversed, UR176 = LL01 reversed …) and QU016/QU017/QU019, split into parts.
SAME = {"AS046", "AS067/MA29", "AS070", "AS086", "BM1", "BM2", "BM3", "HP036", "KH0001", "KH0032", "KH0033", "KH0049", "KH0057",
        "KH0067", "KH0080", "KH0081", "KH0083", "KH0197", "KH0227", "KH0267", "KH0350", "QU016", "QU017", "QU019", "R4303", "UR043",
        "UR044", "UR083", "UR126", "UR133", "UR163", "UR176", "UR236", "UR247", "UR281"}
keep = [r for r in old if r["inv_num"] not in have and r["inv_num"] not in SAME]
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
