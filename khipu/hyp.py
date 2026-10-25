"""Общий загрузчик для цикла гипотез (база OKR): кипу → подвесные по порядку с группой, значением, длиной, концом, цветом,
креплением, круткой, кластерами узлов (положение в см от основного шнура, тип, число узлов, направления) и дочерними.
Плюс место находки и повторные записи из атласа. Используется в khipu/hyp_tests.py.
"""
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/open-khipu-repository/data/khipu.db"


@lru_cache(maxsize=1)
def okr():
    c = sqlite3.connect(DB)
    inv = {k: (n or "").strip() for k, n in c.execute("select KHIPU_ID, INVESTIGATOR_NUM from khipu_main")}
    col = {}
    for cid, c1, op, c2 in c.execute("select CORD_ID, COLOR_CD_1, OPERATOR_1, COLOR_CD_2 from ascher_cord_color order by color_id"):
        col.setdefault(cid, ((c1 or "").strip(), (op or "").strip(), (c2 or "").strip()))
    kn = defaultdict(list)
    for cid, pos, clu, t, d, v, turns in c.execute(
            "select kc.CORD_ID, kc.START_POS, kc.CLUSTER_ID, k.TYPE_CODE, k.DIRECTION, k.knot_value_type, k.NUM_TURNS "
            "from knot_cluster kc join knot k on k.CLUSTER_ID = kc.CLUSTER_ID order by kc.CORD_ID, kc.START_POS, k.KNOT_ORDINAL"):
        kn[cid].append((pos, clu, (t or "").strip(), (d or "").strip().upper(), int(v or 0), int(turns or 0)))
    K = defaultdict(list)
    sub = defaultdict(list)
    for cid, kid, lvl, ordn, clu, pf, ln, term, att, tw in c.execute(
            "select CORD_ID, KHIPU_ID, CORD_LEVEL, CORD_ORDINAL, CLUSTER_ID, PENDANT_FROM, CORD_LENGTH, TERMINATION, ATTACHMENT_TYPE, TWIST "
            "from cord order by KHIPU_ID, CORD_LEVEL, CORD_ORDINAL"):
        clusters = defaultdict(list)
        for pos, cl, t, d, v, turns in kn.get(cid, []):
            clusters[(pos if pos is not None else -1, cl)].append((t, d, v, turns))
        cls = [{"pos": p, "knots": ks, "value": sum(k[2] for k in ks), "type": Counter(k[0] for k in ks).most_common(1)[0][0],
                "dirs": Counter(k[1] for k in ks)} for (p, _), ks in sorted(clusters.items())]
        rec = {"id": cid, "order": ordn or 0, "group": clu, "value": sum(x["value"] for x in cls), "length": float(ln or 0),
               "term": (term or "").strip(), "att": (att or "").strip().upper()[:1], "twist": (tw or "").strip().upper()[:1],
               "colour": col.get(cid, ("", "", "")), "clusters": cls, "subs": []}
        if (lvl or 1) == 1:
            K[inv.get(kid, "")].append(rec)
        else:
            sub[pf].append(rec)
    for k, cs in K.items():
        for r in cs:
            r["subs"] = sorted(sub.get(r["id"], []), key=lambda s: s["order"])
        cs.sort(key=lambda r: r["order"])
    return dict(K)


def groups(cords):
    out, cur, last = [], [], object()
    for r in cords:
        if r["group"] != last and cur:
            out.append(cur); cur = []
        cur.append(r); last = r["group"]
    if cur:
        out.append(cur)
    return out


@lru_cache(maxsize=1)
def atlas():
    D = json.load(open(ROOT / "site/data.json"))
    site = {k["id"]: k["site"] for k in D["khipus"]}
    dup = set()
    for r in csv.DictReader(open(ROOT / "atlas/curated/duplicates.csv")):
        dup |= {(r["a"], r["b"]), (r["b"], r["a"])}
    return D, site, dup
