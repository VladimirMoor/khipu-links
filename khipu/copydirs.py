"""Сохраняют ли копии направления узлов (S/Z), крутку шнура, крепление и цвет?

Пары: связи атласа (копии, выписки, части одного счёта и т. д.) и, для сравнения, повторные записи одного предмета
(показывают, насколько согласно разные исследователи записывают сами признаки). Данные — база OKR (узлы с
направлением есть только там).

Шнуры пары выравниваются по значениям подвесных (глобальное выравнивание с пропусками, прямо и обратно); дальше —
только сопоставленные шнуры с равными ненулевыми значениями. Для них:
- узлы: кластеры сверху вниз (разряды), пара кластеров с тем же типом и числом узлов; направление кластера —
  преобладающее S или Z среди его узлов (U и пустые не считаются);
- крутка шнура (S/Z), крепление (R/V), цвет (код цвета целиком).
Согласие против перестановки: признак перемешивается внутри каждого кипу среди сопоставленных шнуров (для узлов —
внутри одного типа узла и одного разряда), 2000 раз. Вывод: extracted/copydirs.txt.
"""
import json
import random
import sqlite3
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/open-khipu-repository/data/khipu.db"
OUT = ROOT / "extracted/copydirs.txt"
NPERM = 2000
# second recordings of one object found in the global scan (globalweb.py), with OKR data on both sides
EXTRA_SAME = [("AS056", "UR163"), ("AS068", "UR281"), ("AS125", "UR247"), ("AS181", "UR236")]


def load():
    c = sqlite3.connect(DB)
    inv = {k: (n or "").strip() for k, n in c.execute("select KHIPU_ID, INVESTIGATOR_NUM from khipu_main")}
    col = {}
    for cid, c1, op, c2 in c.execute("select CORD_ID, COLOR_CD_1, OPERATOR_1, COLOR_CD_2 from ascher_cord_color order by color_id"):
        col.setdefault(cid, (c1 or "") + (op or "") + (c2 or ""))
    val = dict(c.execute("select CORD_ID, sum(knot_value_type) from knot group by CORD_ID"))
    clus = defaultdict(list)
    q = ("select kc.CORD_ID, kc.START_POS, kc.CLUSTER_ID, k.TYPE_CODE, k.DIRECTION from knot_cluster kc "
         "join knot k on k.CLUSTER_ID = kc.CLUSTER_ID order by kc.CORD_ID, kc.START_POS, k.KNOT_ORDINAL")
    tmp = defaultdict(lambda: defaultdict(list))
    for cid, pos, cl, t, d in c.execute(q):
        tmp[cid][(pos or 0, cl)].append(((t or "").strip(), (d or "").strip().upper()))
    for cid, cs in tmp.items():
        for key in sorted(cs):
            ks = cs[key]
            t = Counter(x[0] for x in ks).most_common(1)[0][0]
            dirs = Counter(x[1] for x in ks if x[1] in ("S", "Z"))
            d = dirs.most_common(1)[0][0] if dirs and (len(dirs) == 1 or dirs.most_common(2)[0][1] > dirs.most_common(2)[1][1]) else ""
            clus[cid].append((t, len(ks), d))
    K = defaultdict(list)
    for cid, kid, lvl, ordn, tw, att in c.execute("select CORD_ID, KHIPU_ID, CORD_LEVEL, CORD_ORDINAL, TWIST, ATTACHMENT_TYPE from cord "
                                                    "where CORD_LEVEL = 1 order by KHIPU_ID, CORD_ORDINAL"):
        K[inv.get(kid, "")].append({"v": int(val.get(cid) or 0), "tw": (tw or "").strip().upper(), "att": (att or "").strip().upper()[:1],
                                    "col": col.get(cid, ""), "k": clus.get(cid, [])})
    return K


def align(X, Y):
    n, m, G = len(X), len(Y), 2
    sc = lambda x, y: (5 if x >= 100 else 4 if x >= 10 else 1 if x else 0.5) if x == y else -1
    H = [[0.0] * (m + 1) for _ in range(n + 1)]
    P = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        H[i][0], P[i][0] = -G * i, 1
    for j in range(1, m + 1):
        H[0][j], P[0][j] = -G * j, 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d, u, l = H[i - 1][j - 1] + sc(X[i - 1], Y[j - 1]), H[i - 1][j] - G, H[i][j - 1] - G
            H[i][j], P[i][j] = (d, 0) if d >= u and d >= l else (u, 1) if u >= l else (l, 2)
    out, i, j = [], n, m
    while i > 0 and j > 0:
        if P[i][j] == 0:
            out.append((i - 1, j - 1)); i -= 1; j -= 1
        elif P[i][j] == 1:
            i -= 1
        else:
            j -= 1
    return out[::-1], H[n][m]


def matched(A, B):
    va, vb = [c["v"] for c in A], [c["v"] for c in B]
    f, sf = align(va, vb)
    r, sr = align(va, vb[::-1])
    pairs, rev = (f, False) if sf >= sr else ([(i, len(B) - 1 - j) for i, j in r], True)
    return [(i, j) for i, j in pairs if va[i] == vb[j] and va[i] > 0], rev


def items(A, B, M):
    """comparable observations: (feature, stratum, value on A, value on B)"""
    out = []
    for i, j in M:
        a, b = A[i], B[j]
        if a["tw"] in ("S", "Z") and b["tw"] in ("S", "Z"):
            out.append(("ply", "", a["tw"], b["tw"]))
        if a["att"] in ("R", "V") and b["att"] in ("R", "V"):
            out.append(("attachment", "", a["att"], b["att"]))
        if a["col"] and b["col"]:
            out.append(("colour", "", a["col"], b["col"]))
        ka, kb = a["k"], b["k"]
        if len(ka) == len(kb):
            for lvl, (x, y) in enumerate(zip(ka[::-1], kb[::-1])):     # from the units up
                if x[0] == y[0] and x[1] == y[1] and x[2] and y[2]:
                    out.append(("knot direction", f"{x[0]}{min(lvl, 3)}", x[2], y[2]))
    return out


def perm_test(obs, rnd):
    real = sum(a == b for _, _, a, b in obs)
    strata = defaultdict(list)
    for n, (_, s, a, b) in enumerate(obs):
        strata[s].append(n)
    A = [o[2] for o in obs]
    B = [o[3] for o in obs]
    ge, sims = 0, []
    for _ in range(NPERM):
        Bp = B[:]
        for idx in strata.values():
            vals = [B[n] for n in idx]; rnd.shuffle(vals)
            for n, v in zip(idx, vals):
                Bp[n] = v
        s = sum(x == y for x, y in zip(A, Bp))
        sims.append(s); ge += s >= real
    return real, sum(sims) / len(sims), (ge + 1) / (NPERM + 1)


def main():
    D = json.load(open(ROOT / "site/data.json"))
    K = load()
    pairs = [(e["from"], e["to"], e["type"]) for e in D["edges"]] + [(d["a"], d["b"], "same object") for d in D["duplicates"]] \
        + [(a, b, "same object") for a, b in EXTRA_SAME]
    rnd = random.Random(3)
    pooled = defaultdict(lambda: defaultdict(list))
    lines = []
    for a, b, t in pairs:
        if not K.get(a) or not K.get(b):
            lines.append(f"{a} ~ {b} ({t}): not both in the OKR, skipped")
            continue
        M, rev = matched(K[a], K[b])
        obs = items(K[a], K[b], M)
        grp = "same object" if t == "same object" else "link"
        parts = []
        for feat in ("knot direction", "ply", "attachment", "colour"):
            o = [x for x in obs if x[0] == feat]
            pooled[grp][feat] += [(f"{a}~{b}:{s}", s, x, y) for _, s, x, y in o]
            if o:
                r, e, p = perm_test(o, rnd)
                parts.append(f"{feat} {r}/{len(o)} (chance {e:.1f}, p {p:.3f})")
        lines.append(f"{a} ~ {b} ({t}{', reversed' if rev else ''}): {len(M)} matched cords; " + ("; ".join(parts) or "nothing comparable"))
    lines.append("")
    for grp in ("link", "same object"):
        lines.append(f"Pooled, {grp}s (permutations within each pair and stratum):")
        for feat in ("knot direction", "ply", "attachment", "colour"):
            o = pooled[grp][feat]
            if o:
                # stratum includes the pair, so shuffles stay inside one pair
                r, e, p = perm_test([(feat, s, x, y) for s, _, x, y in o], rnd)
                dist = Counter(x for _, _, x, _ in o) + Counter(y for _, _, _, y in o)
                lines.append(f"   {feat}: agree {r} of {len(o)} ({r / len(o):.0%}); by chance {e:.1f} ({e / len(o):.0%}); p {p:.4f} · values {dict(dist.most_common(4))}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
