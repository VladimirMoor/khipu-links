"""Загрузка Open Khipu Repository в плоские структуры для сверки с документами.

Значение шнура = сумма knot.knot_value_type по его узлам (поле уже содержит
вклад узла с учётом разряда). knot_cluster.TOTAL_VALUE в OKR не заполнен.

Порядок шнуров: обход в глубину от основного шнура; среди братьев — по CORD_ORDINAL.
"""
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/open-khipu-repository/data/khipu.db"
OUT = ROOT / "extracted"


class _Con:
    """Обёртка: строки как dict с ключами в верхнем регистре (в OKR столбцы
    заглавными, в KFG строчными; SQLite сам регистронезависим в запросах)."""

    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row

    def execute(self, q):
        for r in self.con.execute(q):
            yield {k.upper(): r[k] for k in r.keys()}


def load(db_path=DB):
    con = _Con(db_path)
    cols = {r["NAME"].upper() for r in con.execute("pragma table_info(khipu_main)")}
    okr_col = "OKR_NUM" if "OKR_NUM" in cols else "'' as OKR_NUM"

    khipus = {r["KHIPU_ID"]: dict(r) for r in con.execute(
        f"select KHIPU_ID, {okr_col}, INVESTIGATOR_NUM, MUSEUM_NAME, MUSEUM_NUM, "
        "PROVENANCE, REGION, NICKNAME, DUPLICATE_FLAG, DUPLICATE_ID from khipu_main")}
    pcord = {r["KHIPU_ID"]: r["PCORD_ID"] for r in con.execute(
        "select KHIPU_ID, PCORD_ID from primary_cord")}

    values = defaultdict(int)
    nknots = defaultdict(int)
    for r in con.execute("select CORD_ID, knot_value_type v from knot"):
        nknots[r["CORD_ID"]] += 1
        try:
            values[r["CORD_ID"]] += int(r["V"] or 0)
        except (TypeError, ValueError):
            pass

    colors = {}
    for r in con.execute(
            "select CORD_ID, FULL_COLOR from ascher_cord_color where PCORD_FLAG=0 "
            "order by color_id"):
        colors.setdefault(r["CORD_ID"], r["FULL_COLOR"])

    cluster_ord = {r["CLUSTER_ID"]: r["ORDINAL"] for r in con.execute(
        "select CLUSTER_ID, ORDINAL from cord_cluster")}

    children = defaultdict(list)
    cords = {}
    for r in con.execute(
            "select CORD_ID, KHIPU_ID, PENDANT_FROM, CORD_LEVEL, CORD_ORDINAL, "
            "CLUSTER_ID, ATTACHMENT_TYPE, TWIST, CORD_LENGTH, TERMINATION from cord"):
        c = dict(r)
        cords[c["CORD_ID"]] = c
        children[c["PENDANT_FROM"]].append(c["CORD_ID"])
    for kids in children.values():
        kids.sort(key=lambda cid: (cords[cid]["CORD_ORDINAL"] or 0, cid))

    rows = []
    for kid, meta in khipus.items():
        root = pcord.get(kid)
        if root is None:
            continue
        order = 0
        # стек: (cord_id, parent_id, top-level group ordinal, path)
        stack = [(cid, None, None) for cid in reversed(children.get(root, []))]
        while stack:
            cid, parent, top_group = stack.pop()
            c = cords[cid]
            if parent is None:
                top_group = cluster_ord.get(c["CLUSTER_ID"])
            order += 1
            rows.append({
                "khipu_id": kid,
                "okr_num": meta["OKR_NUM"],
                "inv_num": meta["INVESTIGATOR_NUM"],
                "cord_id": cid,
                "parent_id": parent or "",
                "level": c["CORD_LEVEL"],
                "order": order,
                "sib_ordinal": c["CORD_ORDINAL"],
                "group": top_group if top_group is not None else "",
                "value": values.get(cid, 0),
                "n_knots": nknots.get(cid, 0),
                "color": colors.get(cid, ""),
                "attachment": c["ATTACHMENT_TYPE"] or "",
                "twist": c["TWIST"] or "",
                "length": c["CORD_LENGTH"] or "",
                "termination": c["TERMINATION"] or "",
            })
            for ch in reversed(children.get(cid, [])):
                stack.append((ch, cid, top_group))
    return khipus, rows


KFG_DB = ROOT / "data/kfg/kfg.db"
KFG_SUMMARY = ROOT / "data/kfg/kfg_article/data/khipu_summary.csv"


def main():
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "okr"
    OUT.mkdir(exist_ok=True)
    khipus, rows = load(KFG_DB if which == "kfg" else DB)
    if which == "kfg":
        # номера KH (OKR) из сводной таблицы KFG
        with open(KFG_SUMMARY) as f:
            okr = {int(r["khipu_id"]): r["okr_name"] for r in csv.DictReader(f)}
        for r in rows:
            r["okr_num"] = okr.get(r["khipu_id"], "")
        for k in khipus.values():
            k["OKR_NUM"] = okr.get(k["KHIPU_ID"], "")
    with open(OUT / f"{which}_cords.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / f"{which}_khipus.json", "w") as f:
        json.dump(list(khipus.values()), f, ensure_ascii=False, indent=1)
    n_k = len({r["khipu_id"] for r in rows})
    print(f"{len(rows)} cords from {n_k} khipus -> {OUT / (which + '_cords.csv')}")


if __name__ == "__main__":
    main()
