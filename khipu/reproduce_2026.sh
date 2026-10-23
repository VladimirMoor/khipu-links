#!/bin/sh
# Те же 42 проверки reproduce.py, но на корпусе с данными KFG 2026 (extracted/plus2026_cords.csv из run_2026.sh):
# насколько числа препринта держатся на исправленных чтениях. Корпус подменяется на время прогона и восстанавливается.
# Вывод: extracted/reproduce_2026.txt и выводы скриптов в extracted/run2026/repro/.
set -e
cd "$(dirname "$0")/.."
[ -s extracted/plus2026_cords.csv ] || { echo "run khipu/run_2026.sh first"; exit 1; }
cp extracted/plus_cords.csv extracted/plus_cords_2023.bak
cp extracted/plus_do_cords.csv extracted/plus_do_cords_2023.bak
cp extracted/kfg_cords.csv extracted/kfg_cords_2023.bak
trap 'cp extracted/plus_cords_2023.bak extracted/plus_cords.csv; cp extracted/plus_do_cords_2023.bak extracted/plus_do_cords.csv; cp extracted/kfg_cords_2023.bak extracted/kfg_cords.csv; rm -f extracted/*_2023.bak; git checkout -q -- extracted; echo restored' EXIT
cp extracted/plus2026_cords.csv extracted/plus_cords.csv
cp extracted/plus2026_cords.csv extracted/plus_do_cords.csv
cp extracted/plus2026_cords.csv extracted/kfg_cords.csv
python3 khipu/reproduce.py > extracted/reproduce_2026.out 2>&1 || true
mkdir -p extracted/run2026/repro
for s in vecsum huacho as118 basel_huacho ur212_as131_units basel_slots units14 halves blanks fillslot slotded summaries paper_extra ur269_streams unit_invariance do_check style_pach_huacho; do
  python3 khipu/$s.py > extracted/run2026/repro/$s.out 2>&1 || true
done
cp extracted/reproduce_2026.out extracted/run2026/reproduce_2026.txt
