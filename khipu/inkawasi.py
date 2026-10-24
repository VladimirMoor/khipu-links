"""Инкавази: бухгалтерия склада — опись, форматы записей, связи внутри архива.

1. Форматы: в каждом кипу группы из 3 подвесных, где одно значение равно сумме двух других (брутто = нетто + вычет);
   доля таких групп, положение брутто/нетто/вычета в группе, повторяющиеся вычеты. Фон: та же проверка, где значения
   троек перемешаны между группами кипу (сохраняет величины, ломает тройки).
2. Связи внутри архива: для каждой пары кипу Инкавази — общие значения шнуров (≥ 20, не кратные 10), итог группы одного
   на шнуре другого, общие тройки целиком; фон — значения второго кипу, сдвинутые на ±1…±10.
Вывод: extracted/inkawasi.txt.
"""
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus2026_cords.csv"
OUT = ROOT / "extracted/inkawasi.txt"


def load(ids):
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(CORDS)):
        if r["inv_num"] in ids and not r["parent_id"]:
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"] or 0)))
    return {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}


def triple_role(g):
    """for a group of 3 with one value = sum of the other two (all > 0): (index of the total, deduction value) else None"""
    if len(g) != 3 or min(g) <= 0:
        return None
    for t in range(3):
        o = [g[i] for i in range(3) if i != t]
        if g[t] == sum(o):
            return t, min(o)
    return None


def main():
    D = json.load(open(ROOT / "site/data.json"))
    meta = {k["id"]: k for k in D["khipus"] if k["site"] == "inkawasi"}
    K = load(set(meta))
    rnd = random.Random(2)
    lines = ["1. Record format: groups of three where one value is the sum of the other two (gross = net + deduction)"]
    lines.append(f"   {'khipu':7} {'groups':>6} {'of 3':>5} {'sums':>5} {'chance':>6}  total at  deductions (most common)")
    formats = {}
    for k in sorted(K):
        gs = K[k]
        tri = [g for g in gs if len(g) == 3]
        if len(tri) < 3:
            continue
        roles = [triple_role(g) for g in tri]
        hit = [r for r in roles if r]
        vals = [v for g in tri for v in g]
        sims = []
        for _ in range(300):
            rnd.shuffle(vals)
            sims.append(sum(1 for i in range(0, len(vals), 3) if triple_role(vals[i:i + 3])))
        chance = sum(sims) / len(sims)
        pos = Counter(t for t, _ in hit)
        ded = Counter(d for _, d in hit)
        formats[k] = (len(hit), len(tri), ded)
        lines.append(f"   {k:7} {len(gs):6} {len(tri):5} {len(hit):5} {chance:6.1f}  {dict(pos)}  {ded.most_common(6)}")
    # 2. relations between khipus of the archive
    rare = lambda v: v >= 20 and v % 10
    vals = {k: {v for g in gs for v in g if rare(v)} for k, gs in K.items()}
    tots = {k: {sum(g) for g in gs if len(g) > 1 and rare(sum(g))} for k, gs in K.items()}
    trip = {k: {tuple(g) for g in gs if len(g) == 3 and min(g) > 0 and max(g) >= 20} for k, gs in K.items()}
    def score(a, b, d):
        vb = {v + d for v in vals[b]}
        tb = {v + d for v in tots[b]}
        s = len(vals[a] & vb) + len(tots[a] & vb) + len(vals[a] & tb)
        s3 = len(trip[a] & {tuple(x + d for x in t) for t in trip[b]})
        return s, s3
    lines.append("\n2. Pairs within the archive: shared rare values (cords ≥ 20 not round; group total = cord), whole triples; "
                 "shifted ±1…±10")
    rows = []
    ids = sorted(K)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            s, s3 = score(a, b, 0)
            if s < 3 and not s3:
                continue
            ns = [score(a, b, d) for d in range(-10, 11) if d]
            e = sum(x for x, _ in ns) / len(ns)
            e3 = sum(y for _, y in ns) / len(ns)
            mx = max(x for x, _ in ns)
            rows.append((s - e, a, b, s, e, mx, s3, e3))
    rows.sort(reverse=True)
    for ex, a, b, s, e, mx, s3, e3 in rows[:40]:
        flag = "**" if s > mx and s >= 2 * e + 3 else "  "
        la, lb = meta[a], meta[b]
        lines.append(f"   {flag} {a:7} ~ {b:7} values {s:3} (shifted {e:5.1f}, max {mx:3}) triples {s3} ({e3:.1f}) · cords {la['np']}/{lb['np']}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
