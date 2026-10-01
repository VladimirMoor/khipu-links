"""Самостоятельная копия атласа для обычного хостинга (Vercel, GitHub Pages, любой статический сервер): dist/.

site/index.html написан как тело страницы-артефакта (оболочку <!doctype>/<head> добавляет claude.ai при публикации),
поэтому здесь страница оборачивается в полный документ, рядом кладутся data.json, land.json, terrain.json, kd/
и уведомления о лицензиях исходных данных. Заметки исследователей работают только внутри claude.ai; в этой копии
блок заметок скрыт.
  python3 khipu/site_export.py https://khipu-atlas.vercel.app
Затем: npx vercel deploy dist --prod
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DIST = ROOT / "dist"
ART = "https://claude.ai/artifact/6e97CVKAN6Xb1kQW5sFYno"

NOTICE = """Khipu Links Atlas: third-party data notices

The atlas derives its cord and knot data from:

1. Open Khipu Repository (https://github.com/khipulab/open-khipu-repository; Zenodo doi:10.5281/zenodo.18025748)
{okr}

2. Khipu Field Guide companion data (Khosla and Medrano 2023; Zenodo doi:10.5281/zenodo.8125718)
{kfg}

Relief of the 3D map: Terrain Tiles, AWS Open Data Registry (https://registry.opendata.aws/terrain-tiles/),
Mapzen; sources include SRTM, GMTED2010 and ETOPO1.
Coastlines: Natural Earth (public domain).
"""


def main():
    url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else ""
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    body = (SITE / "index.html").read_text()
    if url:
        body = body.replace(f"const ART='{ART}';", f"const ART='{url}/';")
    # notes need the claude.ai runtime: hide the block in the standalone copy
    body = body.replace("<style>", "<style>\n#notes,#ov-notes{display:none!important}", 1)
    i = body.index("<style>")
    head, body = body[:i], body[i:]   # <title>, <meta>, <link> go into <head>
    page = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
            + head + "</head><body>\n" + body + "\n</body></html>\n")
    (DIST / "index.html").write_text(page)
    for f in ("data.json", "land.json", "terrain.json"):
        shutil.copy(SITE / f, DIST / f)
    shutil.copytree(SITE / "kd", DIST / "kd")
    shutil.copytree(SITE / "i18n", DIST / "i18n")
    (DIST / "THIRD_PARTY_NOTICES.txt").write_text(NOTICE.format(
        okr=(ROOT / "data/open-khipu-repository/LICENSE").read_text().strip(),
        kfg=(ROOT / "data/kfg/kfg_article/LICENSE").read_text().strip()))
    (DIST / "vercel.json").write_text(json.dumps({"cleanUrls": True, "headers": [
        {"source": "/(.*)\\.json", "headers": [{"key": "Cache-Control", "value": "public, max-age=3600"}]}]}, indent=2))
    n = sum(1 for _ in DIST.rglob("*") if _.is_file())
    size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file()) // 1024
    print(f"dist/: {n} files, {size} KB" + (f", citation URL {url}/" if url else ""))


if __name__ == "__main__":
    main()
