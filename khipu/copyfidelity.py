"""Что переносит копия? Верность копии по отдельным признакам шнура.

Для пар кипу, где найден общий участок (копия счёта), выравниваем подвесные со сдвигом off
и для каждого признака считаем долю совпадений на выровненных парах — против той же доли
при всех остальных сдвигах (фон: признак совпадает «сам по себе» из-за частот).
Признаки:
  value      — значение подвесного (контроль: по нему пары и найдены);
  knotdir    — направления узлов по разрядам: строка вида «1000:S 100:Z 10:Z 1:S»
               (для каждого разряда — преобладающее направление узлов этого разряда);
  knotdir_any— совпадает ли преобладающее направление узлов шнура в целом;
  knottypes  — типы узлов по разрядам (S/L/E) — входит в значение, осязаем;
  attach     — крепление к основному шнуру (R/V);
  color      — цвет (визуальный признак);
  nsub       — число дочерних шнуров;
  length     — длина с точностью 20%.
Сравниваются только пары, где признак известен у обеих сторон (не '' и не 'U').
"""
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/kfg/kfg.db"

PAIRS = [  # (A, B, сдвиг: индекс в B = индекс в A + off), найдено links/nearlinks
    ("UR270", "UR278", 178),
    ("UR267A", "UR255", 5),
    ("UR1118", "UR218", 5),
    ("UR1114", "UR1123", 1),
    ("UR122", "KH0049", 36),
    ("UR122", "HP036", 36),
]


def load(con, inv):
    kid = con.execute("select khipu_id from khipu_main where investigator_num=?", (inv,)).fetchone()[0]
    pc = con.execute("select pcord_id from primary_cord where khipu_id=?", (kid,)).fetchone()[0]
    rows = con.execute("select cord_id, pendant_from, cord_ordinal, attachment_type, cord_length "
                       "from cord where khipu_id=?", (kid,)).fetchall()
    kids = defaultdict(list)
    info = {}
    for cid, par, o, att, ln in rows:
        kids[par].append((o or 0, cid))
        info[cid] = (att, ln)
    color = {}
    for cid, col in con.execute("select cord_id, full_color from ascher_cord_color where khipu_id=? "
                                "and pcord_flag=0 order by color_id", (kid,)):
        color.setdefault(cid, col)
    knots = defaultdict(list)
    for cid, t, v, d in con.execute("select k.cord_id, k.type_code, k.knot_value_type, k.direction "
                                    "from knot k join cord c on c.cord_id=k.cord_id where c.khipu_id=?", (kid,)):
        knots[cid].append((t or "", int(v or 0), d or ""))
    top = [cid for _, cid in sorted(kids[pc])]
    ownv = {cid: sum(v for _, v, _ in knots.get(cid, [])) for cid in info}

    def tree(c):
        return ownv.get(c, 0) + sum(tree(k) for _, k in kids.get(c, []))
    out = []
    for cid in top:
        ks = knots.get(cid, [])
        reg = defaultdict(list)
        for t, v, d in ks:
            if v <= 0:
                continue
            place = 10 ** (len(str(v)) - 1) if t == "S" else 1
            reg[place].append((t, d))
        kd = {p: Counter(d for _, d in lst if d in ("S", "Z")).most_common(1) for p, lst in reg.items()}
        kd = {p: c[0][0] for p, c in kd.items() if c}
        kt = {p: "".join(sorted(set(t for t, _ in lst))) for p, lst in reg.items()}
        dirs = Counter(d for _, _, d in ks if d in ("S", "Z"))
        att, ln = info[cid]
        out.append({
            "value": sum(v for _, v, _ in ks), "tree": tree(cid),
            "knotdir": kd, "knotdir_any": dirs.most_common(1)[0][0] if dirs else None,
            "knottypes": kt, "attach": att if att in ("R", "V") else None,
            "color": color.get(cid) or None, "nsub": len(kids.get(cid, [])), "length": ln or None,
        })
    return out


def agree(f, a, b):
    x, y = a[f], b[f]
    if f == "value":
        return None if not x or not y else x == y
    if f in ("knotdir", "knottypes"):
        common = set(x) & set(y)
        if not common:
            return None
        return all(x[p] == y[p] for p in common)
    if f == "length":
        if not x or not y:
            return None
        return abs(x - y) <= 0.2 * max(x, y)
    if x is None or y is None:
        return None
    return x == y


FEATURES = ["value", "knotdir", "knotdir_any", "knottypes", "attach", "color", "nsub", "length"]


def rate(A, B, off, f, window=None):
    ok = n = 0
    for i, a in enumerate(A):
        j = i + off
        if not (0 <= j < len(B)):
            continue
        if window and not (window[0] <= i < window[1]):
            continue
        r = agree(f, a, B[j])
        if r is None:
            continue
        n += 1
        ok += r
    return ok, n


def main():
    con = sqlite3.connect(DB)
    for x, y, off in PAIRS:
        A, B = load(con, x), load(con, y)
        # участок копии: позиции A, где значения совпадают на своём сдвиге
        match = [i for i in range(len(A)) if 0 <= i + off < len(B) and
                 ((A[i]["value"] and A[i]["value"] == B[i + off]["value"]) or (A[i]["tree"] >= 10 and A[i]["tree"] == B[i + off]["tree"]))]
        if not match:
            continue
        win = (min(match), max(match) + 1)
        print(f"\n== {x} ↔ {y}, сдвиг {off:+d}; участок копии {x}[{win[0]}:{win[1]}], точных значений {len(match)}")
        print(f"   {'признак':12} {'на сдвиге':>14} {'фон (др. сдвиги)':>18}   вывод")
        for f in FEATURES:
            ok, n = rate(A, B, off, f, win)
            bo = bn = 0
            for o in range(-len(A) + 1, len(B)):
                if o == off:
                    continue
                k, m = rate(A, B, o, f)
                bo += k
                bn += m
            r = ok / n if n else float("nan")
            br = bo / bn if bn else float("nan")
            verdict = ""
            if n >= 5 and bn:
                verdict = "КОПИРУЕТСЯ" if r - br > 0.2 else ("≈ фон" if abs(r - br) <= 0.2 else "реже фона")
            print(f"   {f:12} {ok:4}/{n:<4} {r:5.2f}   {bo:6}/{bn:<6} {br:5.2f}   {verdict}")


if __name__ == "__main__":
    main()
