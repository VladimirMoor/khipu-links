"""Английский исходник для переводчиков: atlas/curated/i18n/en_source.json.

ui.static — короткие строки разметки (ключи испанской таблицы + новые строки из NEW_STATIC);
ui.mixed — HTML-блоки с data-i18n-html (внутренний HTML из site/index.html);
ui.dyn — строки из вызовов tr()/trf() в коде страницы и ключи испанской таблицы;
content — находки, хронология, отрицательные результаты, источники, типы связей (из site/data.json).
Перевод на новый язык: файл atlas/curated/i18n/<lang>.json той же формы, ключи — английские строки.
Сводка: какие строки ещё не переведены в каждом языке.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "atlas/curated/i18n"
NEW_STATIC = ["Start here", "For readers new to the subject", "All places", "No recorded find-place", "All collectors",
              "Sections", "Language", "Find a khipu by number", "Map view", "Zoom in", "Zoom out", "Vertical exaggeration",
              "Map of khipu find-places on the Peruvian and Chilean coast", "Network diagram of linked khipus",
              "Search khipus", "Diagram of a khipu", "New to khipus? Start here"]


def mixed_blocks(html):
    out = {}
    for m in re.finditer(r'<(\w+)([^>]*)\sdata-i18n-html="([^"]+)"([^>]*)>', html):
        tag, key, i = m.group(1), m.group(3), m.end()
        depth, pos = 1, i
        for t in re.finditer(rf"<(/?){tag}\b[^>]*>", html[i:]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                pos = i + t.start()
                break
        out[key] = html[i:pos].strip()
    return out


def main():
    html = (ROOT / "site/index.html").read_text()
    es = json.load(open(I18N / "es.json"))
    js = html[html.rindex("<script>"):]
    dyn = set(es["ui"]["dyn"])
    for m in re.finditer(r"\btrf?\(\s*'((?:[^'\\]|\\.)*)'", js):
        dyn.add(m.group(1).replace("\\'", "'"))
    for m in re.finditer(r'\btrf?\(\s*"((?:[^"\\]|\\.)*)"', js):
        dyn.add(m.group(1))
    D = json.load(open(ROOT / "site/data.json"))
    src = {"ui": {"static": sorted(set(es["ui"]["static"]) | set(NEW_STATIC)), "mixed": mixed_blocks(html), "dyn": sorted(dyn)},
           "content": {"findings": {f["id"]: {"title": f["title"], "summary": f["summary"], "evidence": f.get("evidence", [])} for f in D["findings"]},
                       "timeline": {t["title"]: {"title": t["title"], "text": t["text"]} for t in D["timeline"]},
                       "negatives": {n["title"]: {"title": n["title"], "text": n["text"]} for n in D["negatives"]},
                       "sources": {s["title"]: s["use"] for s in D["sources"]},
                       "linkTypes": D["edgeTypes"]}}
    (I18N / "en_source.json").write_text(json.dumps(src, ensure_ascii=False, indent=1))
    n = sum(len(v) for v in src["ui"].values())
    print(f"en_source.json: ui {n} strings ({', '.join(f'{k} {len(v)}' for k, v in src['ui'].items())})")
    for f in sorted(I18N.glob("*.json")):
        if f.stem == "en_source":
            continue
        t = json.load(open(f))
        miss = {k: [x for x in src["ui"][k] if x not in t["ui"].get(k, {})] for k in src["ui"]}
        cm = {k: [x for x in src["content"][k] if x not in t["content"].get(k, {})] for k in src["content"]}
        print(f"{f.stem}: missing ui " + ", ".join(f"{k} {len(v)}" for k, v in miss.items()) +
              "; content " + ", ".join(f"{k} {len(v)}" for k, v in cm.items() if v))


if __name__ == "__main__":
    main()
