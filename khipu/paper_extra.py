"""Числа препринта, которые раньше считались вручную (по журналу), — теперь скриптом.

1) Пустая графа и заполненная копия (§3.6): вероятность того, что при случайном расположении заполненных групп
   первые E групп окажутся пустыми, — C(n − E, f) / C(n, f); последовательности берём из вывода fillslot.py.
2) Карта копий архива Инкавази (§3.6): общие «итоги» (максимумы групп ≥ 30) у каждой пары кипу архива против фона —
   те же максимумы второго кипу, сдвинутые на ±1…±10; Пуассоновская p для UR273B ~ UR274B.
3) «Свёрнутая» копия UR053C → UR053B (§3.8): запись B = (W, R с дочерним AB) = (W, R) тройки C и AB следующей тройки;
   число совпавших полей при лучшем сдвиге против 2000 перемешиваний троек C.
Вывод: extracted/paper_extra.txt.
"""
import csv
import json
import math
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/paper_extra.txt"


def split_p(seq):
    n, f = len(seq), seq.count("з")
    e = seq.index("з")
    return math.comb(n - e, f) / math.comb(n, f), n, f, e


def cords(keys):
    rows = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["inv_num"] in keys:
            rows[r["inv_num"]].append(r)
    return rows


def group_max(rs):
    g = defaultdict(list)
    for r in rs:
        if r["parent_id"] == "":
            g[r["group"]].append(int(r["value"]))
    return Counter(max(v) for v in g.values() if max(v) >= 30)


def main():
    lines = []
    out = subprocess.run([sys.executable, str(ROOT / "khipu/fillslot.py")], capture_output=True, text=True).stdout
    for label, pat in (("UR255", r"порядок по группам UR255[^:]*: ([пз]+)"), ("UR256", r"UR256, группы[^:]*: ([пз]+)")):
        seq = re.search(pat, out).group(1)
        p, n, f, e = split_p(seq)
        lines.append(f"{label}: {seq}; групп {n}, заполнено {f}, первых пустых {e}; P = 1 / {1 / p:,.0f}".replace(",", " "))
    # Inkawasi copy map
    D = json.load(open(ROOT / "site/data.json"))
    ink = sorted(k["id"] for k in D["khipus"] if k["site"] == "inkawasi")
    rows = cords(set(ink))
    inkrows = rows
    mx = {k: group_max(rows[k]) for k in ink}
    res = []
    for i, a in enumerate(ink):
        for b in ink[i + 1:]:
            real = sum((mx[a] & mx[b]).values())
            if real < 3:
                continue
            null = [sum((mx[a] & Counter({v + d: c for v, c in mx[b].items()})).values()) for d in list(range(-10, 0)) + list(range(1, 11))]
            res.append((real, sum(null) / len(null), a, b))
    res.sort(key=lambda x: -(x[0] - x[1]))
    lines.append(f"Инкавази: {len(ink)} кипу; пары с ≥ 3 общими итогами групп (фон — сдвиг ±1…±10):")
    for real, m, a, b in res[:8]:
        pp = 1 - sum(math.exp(-m) * m ** j / math.factorial(j) for j in range(real))
        lines.append(f"  {a} ~ {b}: {real} против {m:.2f}; Пуассон p = {pp:.1e}")
    # the two UR273 ~ UR274 pairs in detail: shared group totals (≥ 100, so the deductions 10/17/30 do not count) and their order
    for a, b in (("UR273A", "UR274A"), ("UR273B", "UR274B")):
        def tot(k):
            g = defaultdict(list)
            for r in sorted((r for r in rows[k] if r["parent_id"] == ""), key=lambda r: int(r["order"])):
                g[r["group"]].append(int(r["value"]))
            return [(i + 1, max(v)) for i, v in enumerate(g.values()) if max(v) >= 100]
        ta, tb = tot(a), tot(b)
        sb = Counter(v for _, v in tb)
        sh = [(i, v) for i, v in ta if sb[v]]
        used, pairs = Counter(), []
        for i, v in sh:
            js = [j for j, w in tb if w == v]
            pairs.append((i, js[used[v]] if used[v] < len(js) else None, v)); used[v] += 1
        order = [j for _, j, _ in pairs if j is not None]
        null = []
        for d in list(range(-10, 0)) + list(range(1, 11)):
            sd = Counter(v + d for _, v in tb)
            null.append(sum(min(c, sd[v]) for v, c in Counter(v for _, v in ta).items()))
        m = sum(null) / len(null)
        pp = 1 - sum(math.exp(-m) * m ** j / math.factorial(j) for j in range(len(sh)))
        lines.append(f"  {a} ~ {b}, итоги групп ≥ 100: общих {len(sh)} против {m:.2f} (p = {pp:.1e}); "
                     + ", ".join(f"{v} (г{i} ~ г{j})" for i, j, v in pairs) + f"; порядок сохранён: {order == sorted(order)}")
    # UR053C -> UR053B
    rows = cords({"UR053B", "UR053C"})
    def pend(k):
        rs = rows[k]
        kids = defaultdict(list)
        for r in rs:
            if r["parent_id"]:
                kids[r["parent_id"]].append(int(r["value"]))
        return [(r["color"].split(":")[0], int(r["value"]), kids[r["cord_id"]]) for r in sorted((r for r in rs if r["parent_id"] == ""), key=lambda r: int(r["order"]))]
    B = [(w[1], r[1], (r[2] or [None])[0]) for w, r in zip(pend("UR053B")[0::2], pend("UR053B")[1::2])]
    pc = pend("UR053C")
    C = [(pc[i][1], pc[i + 1][1], pc[i + 2][1]) for i in range(0, len(pc) - 2, 3)]   # (AB, W, R)

    def score(Cs):
        best = 0
        for s in range(-len(B), len(Cs)):
            m = 0
            for i, (w, r, ab) in enumerate(B):
                j = i + s
                if 0 <= j < len(Cs):
                    m += (w == Cs[j][1]) + (r == Cs[j][2])
                if 0 <= j + 1 < len(Cs):
                    m += ab == Cs[j + 1][0]
            best = max(best, m)
        return best
    real = score(C)
    rnd = random.Random(1)
    null = []
    for _ in range(2000):
        Cs = C[:]
        rnd.shuffle(Cs)
        null.append(score(Cs))
    lines.append(f"UR053C → UR053B: записей B {len(B)}, троек C {len(C)}; совпавших полей {real}; "
                 f"2000 перемешиваний троек C: среднее {sum(null) / len(null):.1f}, максимум {max(null)}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
