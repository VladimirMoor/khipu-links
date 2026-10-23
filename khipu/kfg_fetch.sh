#!/bin/sh
# Скачивает Excel-файлы Khipu Field Guide (обновление 10.10.2026) в data/kfg_2026/xlsx/ с паузой 10 с (robots.txt: Crawl-delay 10).
# Список файлов: data/kfg_2026/xlsx_list.txt (листинг https://www.khipufieldguide.com/databook/excel_khipus/). Уже скачанные пропускает.
cd "$(dirname "$0")/.."
while read -r f; do
  [ -s "data/kfg_2026/xlsx/$f" ] && continue
  curl -s -f -o "data/kfg_2026/xlsx/$f" "https://www.khipufieldguide.com/databook/excel_khipus/$f" || echo "fail $f"
  sleep 10
done < data/kfg_2026/xlsx_list.txt
echo "done: $(ls data/kfg_2026/xlsx | wc -l) files"
