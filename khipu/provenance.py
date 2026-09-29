"""Фильтр кипу по месту находки (provenance/region из *_khipus.json рядом с *_cords.csv)."""
import json
import re
from pathlib import Path


def place_map(cords_path):
    p = Path(cords_path)
    js = p.with_name(p.name.replace("_cords.csv", "_khipus.json"))
    with open(js) as f:
        return {str(k["KHIPU_ID"]): f"{k.get('PROVENANCE') or ''} | {k.get('REGION') or ''}" for k in json.load(f)}


def subset(items, cords_path, pattern):
    """items: dict khipu_id → что угодно. Оставляет кипу, чьё место совпадает с regex."""
    if not pattern:
        return items
    places = place_map(cords_path)
    rx = re.compile(pattern, re.I)
    return {k: v for k, v in items.items() if rx.search(places.get(str(k), ""))}
