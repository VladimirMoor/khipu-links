"""Цикл гипотез: каждая — функция hNN(), печатает итог против фона. Запуск: python3 khipu/hyp_tests.py 17 18 …
Данные — база OKR через khipu/hyp.py. Итоги записываются в docs/project_log_ru.md вручную.
"""
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hyp  # noqa: E402

R = random.Random(17)


def spearman(a, b):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = rk(a), rk(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else 0.0


def h17():
    """Cord length carries information: among intact cords with the same number of digit clusters, longer cords hold
    larger values (within khipu). Baseline: lengths shuffled among the same cords."""
    K = hyp.okr()
    reals, sims = [], defaultdict(list)
    for k, cs in K.items():
        by = defaultdict(list)
        for r in cs:
            if r["term"] == "K" and r["value"] > 0 and r["length"] > 0:
                by[len(r["clusters"])].append((r["length"], r["value"]))
        for nd, xs in by.items():
            if len(xs) >= 10 and len({v for _, v in xs}) >= 5:
                L, V = [x[0] for x in xs], [x[1] for x in xs]
                reals.append(spearman(L, V))
    print(f"H17: khipu × digit-count sets: {len(reals)}; mean Spearman(length, value) {statistics.mean(reals):.3f}; "
          f"positive in {sum(r > 0 for r in reals)} of {len(reals)} (sign test vs 50%)")


def h18():
    """A shared 'ruler': the distance between the units and tens clusters is alike within one find-place.
    Per khipu: median gap (cm) between the last two clusters of 2+ cluster cords; spread within places vs shuffled places."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    gaps = {}
    for k, cs in K.items():
        g = [r["clusters"][-1]["pos"] - r["clusters"][-2]["pos"] for r in cs if len(r["clusters"]) >= 2
             and r["clusters"][-1]["pos"] is not None and r["clusters"][-2]["pos"] is not None and r["clusters"][-1]["pos"] > r["clusters"][-2]["pos"] >= 0]
        if len(g) >= 10 and site.get(k):
            gaps[k] = statistics.median(g)
    ks = list(gaps)
    def within(lab):
        by = defaultdict(list)
        for k in ks:
            by[lab[k]].append(gaps[k])
        return statistics.mean(statistics.pstdev(v) for v in by.values() if len(v) >= 3)
    lab = {k: site[k] for k in ks}
    real = within(lab)
    labs = [lab[k] for k in ks]
    sims = []
    for _ in range(2000):
        R.shuffle(labs)
        sims.append(within(dict(zip(ks, labs))))
    p = (1 + sum(s <= real for s in sims)) / 2001
    by = defaultdict(list)
    for k in ks:
        by[lab[k]].append(gaps[k])
    print(f"H18: {len(ks)} khipus with a place; mean within-place SD of the units–tens gap {real:.2f} cm; shuffled {statistics.mean(sims):.2f}; p(≤) {p:.4f}")
    print("     median gap by place: " + ", ".join(f"{s} {statistics.median(v):.1f}" for s, v in sorted(by.items(), key=lambda x: -len(x[1])) if len(v) >= 5))


def all_values():
    K = hyp.okr()
    vals = Counter()
    for cs in K.values():
        for r in cs:
            vals[r["value"]] += 1
            for s in r["subs"]:
                vals[s["value"]] += 1
    return vals


def h19():
    """Calendar numbers (365, 360, 354, 328, 730, 260, 584, 30, 29) occur more often than neighbouring values."""
    vals = all_values()
    for v in (365, 360, 354, 355, 328, 730, 260, 584, 30, 29, 28, 12, 13):
        nb = [vals[v + d] for d in range(-5, 6) if d]
        print(f"H19: {v}: {vals[v]} times; neighbours ±1…±5 mean {statistics.mean(nb):.1f} (max {max(nb)})")


def h20():
    """Prime numbers are over-represented among values 11–999 compared with values shifted by ±1…±3."""
    vals = all_values()
    isp = lambda n: n > 1 and all(n % q for q in range(2, int(n ** 0.5) + 1))
    def frac(d):
        tot = sum(c for v, c in vals.items() if 11 <= v <= 999)
        return sum(c for v, c in vals.items() if 11 <= v <= 999 and isp(v + d)) / tot
    real = frac(0)
    sh = [frac(d) for d in (-3, -2, -1, 1, 2, 3)]
    print(f"H20: primes among values 11–999: {real:.3f}; shifted ±1…±3: {statistics.mean(sh):.3f} (min {min(sh):.3f}, max {max(sh):.3f})")
    # odd/even control: shifts by ±1/±3 change parity; compare only ±2
    print(f"     (shift ±2 keeps parity: {frac(-2):.3f}, {frac(2):.3f})")


def h21():
    """Knots of the minority direction mark negative values: a group total fits sum(majority) − sum(minority) where the
    plain sum does not. Baseline: the same number of cords marked negative at random."""
    K = hyp.okr()
    real_plain = real_signed = 0
    cases = []
    for k, cs in K.items():
        dirs = Counter(d for r in cs for c in r["clusters"] for d, n in c["dirs"].items() if d in ("S", "Z") for _ in range(n))
        if sum(dirs.values()) < 30 or min(dirs.values(), default=0) < 0.05 * sum(dirs.values()) or len(dirs) < 2:
            continue
        maj = dirs.most_common(1)[0][0]
        for g in hyp.groups(cs):
            if len(g) < 3:
                continue
            for t, tot in enumerate(g):
                if tot["value"] < 10:
                    continue
                rest = [r for i, r in enumerate(g) if i != t and r["value"] > 0]
                if len(rest) < 2:
                    continue
                neg = [any(c["dirs"].get(maj, 0) == 0 and sum(c["dirs"].values()) > 0 for c in r["clusters"]) for r in rest]
                plain = sum(r["value"] for r in rest) == tot["value"]
                signed = sum(-r["value"] if n else r["value"] for r, n in zip(rest, neg)) == tot["value"]
                real_plain += plain
                if any(neg):
                    cases.append(([r["value"] for r in rest], sum(neg), tot["value"]))
                    real_signed += signed and not plain
    sims = []
    for _ in range(500):
        s = 0
        for vals, nneg, tot in cases:
            idx = set(R.sample(range(len(vals)), nneg))
            s += sum(-v if i in idx else v for i, v in enumerate(vals)) == tot and sum(vals) != tot
        sims.append(s)
    print(f"H21: groups with minority-direction cords: {len(cases)}; total fits only with them negative: {real_signed} "
          f"(random cords negative: {statistics.mean(sims):.2f}, max {max(sims)}); plain sums anywhere {real_plain}")


def h22():
    """Groups are laid out by importance: group totals fall along the khipu. Per khipu Spearman(position, group total)."""
    K = hyp.okr()
    rs = []
    for k, cs in K.items():
        gs = [sum(r["value"] for r in g) for g in hyp.groups(cs)]
        if len(gs) >= 6 and len(set(gs)) >= 4:
            rs.append(spearman(list(range(len(gs))), gs))
    neg = sum(r < 0 for r in rs)
    print(f"H22: {len(rs)} khipus with ≥ 6 groups; mean Spearman(position, group total) {statistics.mean(rs):.3f}; "
          f"falling in {neg}, rising in {sum(r > 0 for r in rs)}")


def h23():
    """A colour 'header' names the place: the colour sequence of the first three pendants is shared by khipus of one place
    more often than by khipus of different places (places shuffled)."""
    K = hyp.okr()
    _, site, dup = hyp.atlas()
    head = {k: tuple("".join(r["colour"]) for r in cs[:3]) for k, cs in K.items() if len(cs) >= 3 and site.get(k) and all(r["colour"][0] for r in cs[:3])}
    ks = list(head)
    def rate(lab):
        n = s = 0
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                if head[a] == head[b] and (a, b) not in dup:
                    n += 1; s += lab[a] == lab[b]
        return s, n
    lab = {k: site[k] for k in ks}
    s, n = rate(lab)
    labs = [lab[k] for k in ks]
    sims = []
    for _ in range(1000):
        R.shuffle(labs)
        sims.append(rate(dict(zip(ks, labs)))[0])
    print(f"H23: {len(ks)} khipus; pairs with the same first-three colours: {n}; same place {s}; shuffled places {statistics.mean(sims):.1f}; "
          f"p {(1 + sum(x >= s for x in sims)) / 1001:.4f}")
    common = Counter(head.values()).most_common(5)
    print("     commonest headers: " + "; ".join(f"{'-'.join(h)} ×{c}" for h, c in common))


def h24():
    """Subsidiaries add up to their pendant (pendant = sum of its subsidiaries), more often than with subsidiaries shuffled
    between pendants of the same khipu."""
    K = hyp.okr()
    real = n = 0
    sims = [0] * 300
    for k, cs in K.items():
        ps = [r for r in cs if len(r["subs"]) >= 2 and r["value"] >= 10]
        if len(ps) < 3:
            continue
        sums = [sum(s["value"] for s in r["subs"]) for r in ps]
        vals = [r["value"] for r in ps]
        n += len(ps)
        real += sum(a == b for a, b in zip(vals, sums))
        for t in range(300):
            sh = sums[:]
            R.shuffle(sh)
            sims[t] += sum(a == b for a, b in zip(vals, sh))
    print(f"H24: pendants with ≥ 2 subsidiaries (value ≥ 10): {n}; pendant = sum of subsidiaries: {real}; shuffled {statistics.mean(sims):.1f}, max {max(sims)}")



def h19b():
    """260 against other round values: is 260 commoner than 240, 250, 270, 280 and other multiples of 10 near it?"""
    vals = all_values()
    nb = {v: vals[v] for v in range(200, 330, 10)}
    print("H19b: multiples of 10 from 200 to 320: " + ", ".join(f"{v}:{c}" for v, c in nb.items()))
    who = Counter()
    for k, cs in hyp.okr().items():
        for r in cs:
            if r["value"] == 260:
                who[k] += 1
    print("      khipus with 260: " + ", ".join(f"{k} {n}" for k, n in who.most_common()))


def h22b():
    """Group totals fall along the khipu even when only intact cords are counted (end knotted, not broken) and khipus
    whose first group is a summary of the rest are left out."""
    K = hyp.okr()
    rs = []
    for k, cs in K.items():
        gs = hyp.groups(cs)
        tot = [sum(r["value"] for r in g if r["term"] == "K") for g in gs]
        if len(tot) >= 6 and len(set(tot)) >= 4:
            if tot[0] > 0 and tot[0] * 2 >= sum(tot):   # first group holds half or more: summary-like
                continue
            rs.append(spearman(list(range(len(tot))), tot))
    print(f"H22b: {len(rs)} khipus; intact cords only, summary-first khipus left out: mean Spearman {statistics.mean(rs):.3f}; "
          f"falling {sum(r < 0 for r in rs)}, rising {sum(r > 0 for r in rs)}")
    # damage check: share of broken cords by position third
    br = Counter(); n = Counter()
    for k, cs in K.items():
        for i, r in enumerate(cs):
            t = min(2, 3 * i // max(1, len(cs)))
            n[t] += 1; br[t] += r["term"] == "B"
    print("      broken ends by third of the khipu: " + ", ".join(f"{t + 1}: {br[t] / n[t]:.1%}" for t in range(3)))


def h17b():
    """Why do larger values sit on shorter cords? Check: (a) within one group; (b) summary/top-of-group cords; (c) only
    cords whose value has no long knot (single knots only)."""
    K = hyp.okr()
    within, first_short = [], []
    for k, cs in K.items():
        for g in hyp.groups(cs):
            xs = [(r["length"], r["value"]) for r in g if r["term"] == "K" and r["value"] > 0 and r["length"] > 0]
            if len(xs) >= 6 and len({v for _, v in xs}) >= 4:
                within.append(spearman([x[0] for x in xs], [x[1] for x in xs]))
    print(f"H17b: within single groups (≥ 6 intact cords): mean Spearman(length, value) {statistics.mean(within):.3f}; "
          f"negative in {sum(r < 0 for r in within)} of {len(within)}")
    # lower knot position: is the last (units) cluster placed lower on longer cords? relation of length to the units-cluster position
    pos = []
    for k, cs in K.items():
        xs = [(r["length"], r["clusters"][-1]["pos"]) for r in cs if r["term"] == "K" and r["clusters"] and r["clusters"][-1]["pos"] and r["length"] > 0]
        if len(xs) >= 10:
            pos.append(spearman([x[0] for x in xs], [x[1] for x in xs]))
    print(f"      length vs position of the lowest cluster: mean Spearman {statistics.mean(pos):.3f} over {len(pos)} khipus")
    # do cords with more knots in total end up shorter? (knots take up cord length when tied)
    kn = []
    for k, cs in K.items():
        xs = [(r["length"], sum(len(c["knots"]) + sum(t for _, _, _, t in c["knots"]) for c in r["clusters"])) for r in cs if r["term"] == "K" and r["length"] > 0 and r["clusters"]]
        if len(xs) >= 10:
            kn.append(spearman([x[0] for x in xs], [x[1] for x in xs]))
    print(f"      length vs number of knots and turns: mean Spearman {statistics.mean(kn):.3f} over {len(kn)} khipus")



def h25():
    """Tying order shows in knot positions: the position of the units cluster drifts along the khipu (sign test)."""
    K = hyp.okr()
    rs = []
    for k, cs in K.items():
        xs = [(r["order"], r["clusters"][-1]["pos"]) for r in cs if r["clusters"] and r["clusters"][-1]["pos"] and r["clusters"][-1]["pos"] > 0]
        if len(xs) >= 20:
            rs.append(spearman([x[0] for x in xs], [x[1] for x in xs]))
    big = [r for r in rs if abs(r) >= 0.3]
    print(f"H25: {len(rs)} khipus; mean Spearman(order, units position) {statistics.mean(rs):.3f}; |rho| ≥ 0.3 in {len(big)} "
          f"({sum(r > 0 for r in big)} drifting down the cord, {sum(r < 0 for r in big)} up)")


def h26():
    """A copy was knotted lying beside its original: matched cords have their clusters at the same distances.
    Linked pairs (copy/excerpt/details/fold); per matched cord pair, |difference| of the units-cluster position, against
    the same cords paired at random within the pair of khipus."""
    import copies_losses as cl
    K = hyp.okr()
    D, _, _ = hyp.atlas()
    real, sims = [], []
    for e in D["edges"]:
        if e["type"] not in ("copy", "excerpt", "details", "fold"):
            continue
        A, B = K.get(e["from"]), K.get(e["to"])
        if not A or not B:
            continue
        al = cl.align([r["value"] for r in A], [r["value"] for r in B])
        pr = [(A[i], B[j]) for i, j in al if A[i]["value"] == B[j]["value"] and A[i]["value"] > 0 and A[i]["clusters"] and B[j]["clusters"]
              and A[i]["clusters"][-1]["pos"] and B[j]["clusters"][-1]["pos"]]
        if len(pr) < 5:
            continue
        pa = [a["clusters"][-1]["pos"] for a, _ in pr]
        pb = [b["clusters"][-1]["pos"] for _, b in pr]
        rho = spearman(pa, pb)
        sh = []
        for _ in range(500):
            q = pb[:]; R.shuffle(q); sh.append(spearman(pa, q))
        real.append((e["from"], e["to"], len(pr), rho, (1 + sum(x >= rho for x in sh)) / 501))
    for a, b, n, rho, p in real:
        print(f"H26: {a} ~ {b}: {n} matched cords; Spearman of units-cluster positions {rho:.2f}; p {p:.3f}")


def h27():
    """Two-colour cords (mottled ':' or barber-pole '-') hold larger values than one-colour cords of the same khipu."""
    K = hyp.okr()
    wins = losses = 0
    for k, cs in K.items():
        two = [r["value"] for r in cs if r["colour"][1] and r["value"] > 0]
        one = [r["value"] for r in cs if r["colour"][0] and not r["colour"][1] and r["value"] > 0]
        if len(two) >= 5 and len(one) >= 5:
            m2, m1 = statistics.median(two), statistics.median(one)
            wins += m2 > m1; losses += m2 < m1
    print(f"H27: khipus with ≥ 5 two-colour and ≥ 5 one-colour cords: two-colour median larger in {wins}, smaller in {losses}")


def h28():
    """Knotless (zero) pendants sit at particular places in their groups: first or last more often than with values
    shuffled within groups."""
    K = hyp.okr()
    cnt = Counter(); sims = Counter(); n = 0
    for k, cs in K.items():
        for g in hyp.groups(cs):
            if len(g) < 4:
                continue
            v = [r["value"] for r in g]
            if 0 < v.count(0) < len(v):
                n += 1
                cnt["first"] += v[0] == 0; cnt["last"] += v[-1] == 0
                for _ in range(20):
                    q = v[:]; R.shuffle(q)
                    sims["first"] += (q[0] == 0) / 20; sims["last"] += (q[-1] == 0) / 20
    print(f"H28: groups (≥ 4) with some zeros: {n}; zero first {cnt['first']} (shuffled {sims['first']:.1f}); zero last {cnt['last']} (shuffled {sims['last']:.1f})")


def h31():
    """Khipus as time series: totals of neighbouring groups are more alike than in shuffled order (lag-1 correlation)."""
    K = hyp.okr()
    real, null = [], []
    for k, cs in K.items():
        t = [sum(r["value"] for r in g) for g in hyp.groups(cs)]
        if len(t) >= 8 and len(set(t)) >= 5:
            lag = spearman(t[:-1], t[1:])
            real.append(lag)
            q = t[:]; sh = []
            for _ in range(100):
                R.shuffle(q); sh.append(spearman(q[:-1], q[1:]))
            null.append(statistics.mean(sh))
    print(f"H31: {len(real)} khipus; mean lag-1 Spearman of group totals {statistics.mean(real):.3f}; shuffled order {statistics.mean(null):.3f}; "
          f"above its shuffle in {sum(a > b for a, b in zip(real, null))}")


def h36():
    """Modern recorders also slip by one knot: where the KFG release and the OKR read the same khipu differently, the
    difference is mostly one knot — so some 'copy slips' may be modern."""
    import csv as _csv
    import copies_losses as cl
    K = hyp.okr()
    kfg = defaultdict(list)
    for r in _csv.DictReader(open(hyp.ROOT / "extracted/kfg2026_cords.csv")):
        if not r.get("parent_id"):
            kfg[r["inv_num"]].append((int(r["order"]), int(r["value"] or 0)))
    diffs = []; same = tot = 0
    for k, xs in kfg.items():
        if k not in K:
            continue
        A = [v for _, v in sorted(xs)]
        B = [r["value"] for r in K[k]]
        if abs(len(A) - len(B)) > 3:
            continue
        al = cl.align(A, B)
        eq = {(i, j) for i, j in al if A[i] == B[j]}
        tot += len(al); same += len(eq)
        for i, j in al:
            if A[i] != B[j] and A[i] > 0 and B[j] > 0 and ((i - 1, j - 1) in eq or (i + 1, j + 1) in eq):
                diffs.append((A[i], B[j]))
    c = Counter(cl.kind(x, y) for x, y in diffs)
    print(f"H36: KFG vs OKR, same khipus: aligned cords {tot}, equal {same} ({same / max(1, tot):.1%}); differing (both nonzero) {len(diffs)}: {dict(c)}")



def pos_resid(cs):
    """units-cluster position per cord, corrected for digit count, knots above the units and the local trend (None if absent)"""
    rows = [(i, len(r["clusters"]), sum(len(c["knots"]) for c in r["clusters"][:-1]), r["clusters"][-1]["pos"])
            for i, r in enumerate(cs) if r["clusters"] and r["clusters"][-1]["pos"]]
    if len(rows) < 10:
        return [None] * len(cs)
    by = defaultdict(list)
    for i, nc, ka, p in rows:
        by[nc].append((ka, p))
    fit = {}
    for nc, xs in by.items():
        if len(xs) >= 3 and len({a for a, _ in xs}) > 1:
            ma = statistics.mean(a for a, _ in xs); mp = statistics.mean(p for _, p in xs)
            fit[nc] = (ma, mp, sum((a - ma) * (p - mp) for a, p in xs) / sum((a - ma) ** 2 for a, _ in xs))
        else:
            fit[nc] = (0, statistics.mean(p for _, p in xs), 0)
    raw = [None] * len(cs)
    for i, nc, ka, p in rows:
        ma, mp, b = fit[nc]
        raw[i] = p - (mp + b * (ka - ma))
    out = []
    for i, x in enumerate(raw):
        if x is None:
            out.append(None); continue
        w = [y for y in raw[max(0, i - 5):i + 6] if y is not None]
        out.append(x - statistics.median(w))
    return out


def h37():
    """'Blank forms': pairs of khipus linked only by the layout of their knots — corrected knot positions correlate cord by
    cord although the values differ. Pairs with pendant counts within 5%; index-wise correlation; baseline circular shifts."""
    K = hyp.okr()
    _, site, dup = hyp.atlas()
    res = {k: pos_resid(cs) for k, cs in K.items() if len(cs) >= 20}
    ks = sorted(res, key=lambda k: len(K[k]))
    hits = []
    for a_i, a in enumerate(ks):
        for b in ks[a_i + 1:]:
            na, nb = len(K[a]), len(K[b])
            if nb > na * 1.05:
                break
            if (a, b) in dup:
                continue
            n = min(na, nb)
            xa, xb = res[a][:n], res[b][:n]
            pr = [(x, y) for x, y in zip(xa, xb) if x is not None and y is not None]
            if len(pr) < 20:
                continue
            rho = spearman([x for x, _ in pr], [y for _, y in pr])
            if rho < 0.4:
                continue
            sh = []
            for d in range(5, n - 5, max(1, (n - 10) // 40)):
                q = xb[d:] + xb[:d]
                pp = [(x, y) for x, y in zip(xa, q) if x is not None and y is not None]
                if len(pp) >= 20:
                    sh.append(spearman([x for x, _ in pp], [y for _, y in pp]))
            if sh and rho > max(sh):
                same = sum(K[a][i]["value"] == K[b][i]["value"] for i in range(n))
                hits.append((rho, a, b, len(pr), max(sh), same / n, site.get(a), site.get(b)))
    hits.sort(reverse=True)
    print(f"H37: pairs with corrected-position correlation ≥ 0.4 above all circular shifts: {len(hits)}")
    for rho, a, b, n, mx, same, sa, sb in hits[:25]:
        print(f"     {a:9} ~ {b:9} rho {rho:.2f} (shifts max {mx:.2f}), {n} cords, equal values {same:.0%} · {sa} / {sb}")


def h38():
    """A knotter's 'hand': the spread of corrected knot positions is a signature — linked pairs have more alike spreads
    than random pairs."""
    K = hyp.okr()
    D, _, _ = hyp.atlas()
    sd = {}
    for k, cs in K.items():
        r = [x for x in pos_resid(cs) if x is not None]
        if len(r) >= 15:
            sd[k] = statistics.pstdev(r)
    ks = list(sd)
    linked = [(e["from"], e["to"]) for e in D["edges"] if e["from"] in sd and e["to"] in sd]
    real = statistics.mean(abs(math.log(sd[a] / sd[b])) for a, b in linked)
    sims = [statistics.mean(abs(math.log(sd[a] / sd[b])) for a, b in (R.sample(ks, 2) for _ in linked)) for _ in range(2000)]
    print(f"H38: linked pairs {len(linked)}: mean |log ratio| of positional spread {real:.3f}; random pairs {statistics.mean(sims):.3f}; "
          f"p(≤) {(1 + sum(x <= real for x in sims)) / 2001:.4f}")


def h40():
    """Knot direction follows the cord's ply: within khipus that have both S- and Z-plied pendants, Z-plied cords carry the
    other knot direction more often (2×2 association, permutation of ply labels within khipu)."""
    K = hyp.okr()
    real = n = 0
    sims = [0] * 500
    for k, cs in K.items():
        rows = []
        for r in cs:
            d = Counter()
            for c in r["clusters"]:
                for dd, m in c["dirs"].items():
                    if dd in ("S", "Z"):
                        d[dd] += m
            if r["twist"] in ("S", "Z") and d:
                rows.append((r["twist"], d.most_common(1)[0][0]))
        tw = [t for t, _ in rows]
        if len(set(tw)) < 2 or len(rows) < 10 or min(Counter(tw).values()) < 3:
            continue
        n += len(rows)
        real += sum(t != d for t, d in rows)
        kd = [d for _, d in rows]
        for i in range(500):
            q = tw[:]; R.shuffle(q)
            sims[i] += sum(t != d for t, d in zip(q, kd))
    print(f"H40: cords in khipus with both plies: {n}; knot direction opposite to the ply: {real}; shuffled plies {statistics.mean(sims):.1f} "
          f"(min {min(sims)}, max {max(sims)})")


def h43():
    """Double entry: the two halves of a khipu (by groups) have equal totals more often than random splits."""
    K = hyp.okr()
    real = n = 0
    sims = 0.0
    for k, cs in K.items():
        t = [sum(r["value"] for r in g) for g in hyp.groups(cs)]
        if len(t) < 4 or len(t) % 2 or sum(t) < 100:
            continue
        n += 1
        h = len(t) // 2
        real += sum(t[:h]) == sum(t[h:])
        hits = 0
        for _ in range(200):
            q = t[:]; R.shuffle(q)
            hits += sum(q[:h]) == sum(q[h:])
        sims += hits / 200
    print(f"H43: khipus with an even number of groups: {n}; halves equal: {real}; random halves {sims:.1f}")


def h44():
    """Multiples of 9 (the Berlin ninths) are over-represented among non-round values 100–9999, against values shifted ±9
    (which keeps divisibility patterns by 3 the same) and ±1…±3."""
    vals = all_values()
    def frac(d):
        xs = [(v + d, c) for v, c in vals.items() if 100 <= v <= 9999 and v % 10]
        tot = sum(c for _, c in xs)
        return sum(c for v, c in xs if v % 9 == 0) / tot
    print(f"H44: share of multiples of 9: {frac(0):.4f}; shifted ±1…±3: " + ", ".join(f"{frac(d):.4f}" for d in (-3, -2, -1, 1, 2, 3))
          + f"; ±9: {frac(-9):.4f}, {frac(9):.4f} (1/9 = 0.1111)")


def kfg_groups():
    import csv
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(hyp.ROOT / "extracted/plus2026_cords.csv")):
        if not r["parent_id"]:
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"] or 0)))
    return {k: [[v for _, v in sorted(g)] for _, g in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}


def h46():
    """H45 replicates in the KFG khipus that are not in OKR (and not duplicates of OKR khipus)."""
    G, O = kfg_groups(), hyp.okr()
    _, _, dup = hyp.atlas()
    new = [k for k in G if k not in O and not any((k, o) in dup for o in O)]
    def scan(d):
        n = 0
        for k in new:
            for v in G[k]:
                for m in range(2, 7):
                    for i in range(len(v) - m + 1):
                        w = v[i:i + m]
                        if min(w) >= 10 and max(w) - min(w) == 1 and (sum(w) + d) % 10 == 0 and (sum(w) + d) % m:
                            n += 1
        return n
    sh = [scan(d) for d in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)]
    print(f"H46: KFG-only khipus {len(new)}; runs {scan(0)}; shifted mean {statistics.mean(sh):.1f}, max {max(sh)}")


def h47():
    """Tripartition: group sizes 3, 6, 9, 12 are local peaks of the size histogram (more common than both neighbours),
    more often than sizes 5, 10 (decimal) or 4, 8."""
    K = hyp.okr()
    c = Counter(len(g) for cs in K.values() for g in hyp.groups(cs))
    print("H47: group sizes " + ", ".join(f"{n}:{c[n]}" for n in range(1, 25)))
    for n in (3, 4, 5, 6, 8, 9, 10, 12, 15, 20):
        print(f"   size {n}: {c[n]} vs neighbours {c[n - 1]}, {c[n + 1]}; ratio {2 * c[n] / max(1, c[n - 1] + c[n + 1]):.2f}")


def h48():
    """Benford: first digits of khipu values ≥ 10 follow Benford's law (counted quantities); round-number planned
    quotas would not. Reported per site with chi-square against Benford."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    by = defaultdict(Counter)
    for k, cs in K.items():
        for r in cs:
            if r["value"] >= 10:
                by[site.get(k) or "?"][int(str(r["value"])[0])] += 1
                by["ALL"][int(str(r["value"])[0])] += 1
    ben = [math.log10(1 + 1 / d) for d in range(1, 10)]
    for s, c in sorted(by.items(), key=lambda kv: -sum(kv[1].values()))[:12]:
        n = sum(c.values())
        chi = sum((c[d] - n * ben[d - 1]) ** 2 / (n * ben[d - 1]) for d in range(1, 10))
        print(f"H48: {s:12} n={n:5} " + " ".join(f"{c[d] / n:.2f}" for d in range(1, 10)) + f"  chi2 {chi:.1f}")
    print("   Benford       " + " ".join(f"{b:.2f}" for b in ben))


def h49():
    """Heaping: share of values ending in 0 (among 10–999) differs by site — estimated vs counted quantities."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    by = defaultdict(lambda: [0, 0, 0])
    for k, cs in K.items():
        for r in cs:
            v = r["value"]
            if 10 <= v <= 999:
                b = by[site.get(k) or "?"]
                b[0] += 1; b[1] += v % 10 == 0; b[2] += v % 10 == 5
    for s, (n, z, f) in sorted(by.items(), key=lambda kv: -kv[1][0])[:15]:
        print(f"H49: {s:12} n={n:5} ends in 0: {z / n:.2f}; in 5: {f / n:.2f}")


def h50():
    """A length standard: spacing (cm) between adjacent place clusters on one cord is more alike among khipus of one
    site than among khipus overall (site labels shuffled)."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    med = {}
    for k, cs in K.items():
        d = []
        for r in cs:
            ps = [c["pos"] for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0]
            d += [b - a for a, b in zip(ps, ps[1:]) if b > a]
        if len(d) >= 10 and site.get(k):
            med[k] = statistics.median(d)
    ks = list(med)
    def within(lab):
        g = defaultdict(list)
        for k in ks:
            g[lab[k]].append(med[k])
        return sum(statistics.pvariance(v) * len(v) for v in g.values() if len(v) >= 3) / sum(len(v) for v in g.values() if len(v) >= 3)
    lab = {k: site[k] for k in ks}
    real = within(lab)
    labs = [lab[k] for k in ks]
    sims = []
    for _ in range(1000):
        R.shuffle(labs)
        sims.append(within(dict(zip(ks, labs))))
    print(f"H50: khipus {len(ks)}; median spacing overall {statistics.median(med.values()):.1f} cm; within-site variance "
          f"{real:.2f} vs shuffled {statistics.mean(sims):.2f}; p {(1 + sum(x <= real for x in sims)) / 1001:.4f}")
    h = Counter(round(v * 2) / 2 for v in med.values())
    print("   histogram (0.5 cm): " + ", ".join(f"{x}:{h[x]}" for x in sorted(h) if h[x] >= 3))


def h51():
    """Squares and triangular numbers are over-represented among values 100–9999 against shifted values."""
    vals = all_values()
    sq = {i * i for i in range(1, 101)}
    tri = {i * (i + 1) // 2 for i in range(1, 150)}
    for name, S in (("squares", sq), ("triangular", tri)):
        def cnt(d):
            return sum(c for v, c in vals.items() if 100 <= v <= 9999 and v % 10 and v + d in S)
        sh = [cnt(d) for d in (-3, -2, -1, 1, 2, 3)]
        print(f"H51: {name}: {cnt(0)}; shifted {sh}")


def h52():
    """Mirror copies: some khipus copy another read from the other end. Pairs sharing a run of 4 values (non-zero, two
    ≥ 10) forward vs reversed vs cords shuffled within khipu."""
    K = {k: [r["value"] for r in cs] for k, cs in hyp.okr().items()}
    _, _, dup = hyp.atlas()
    def grams(v):
        return {tuple(v[i:i + 4]) for i in range(len(v) - 3) if min(v[i:i + 4]) > 0 and sum(x >= 10 for x in v[i:i + 4]) >= 2}
    idx = defaultdict(set)
    for k, v in K.items():
        for g in grams(v):
            idx[g].add(k)
    def pairs(tr):
        out = set()
        for k, v in K.items():
            for g in grams(tr(v)):
                for o in idx.get(g, ()):
                    if o != k and (k, o) not in dup:
                        out.add(tuple(sorted((k, o))))
        return out
    fw = pairs(lambda v: v)
    rv = pairs(lambda v: v[::-1])
    sims = []
    for _ in range(5):
        sims.append(len(pairs(lambda v: R.sample(v, len(v)))))
    print(f"H52: pairs sharing a 4-run forward {len(fw)}; reversed {len(rv)}; shuffled {sims}")
    print("   reversed only: " + ", ".join(f"{a}~{b}" for a, b in sorted(rv - fw)[:30]))


def h52b():
    """H52 with informative runs only: 4 consecutive values, at least two of them ≥ 10 and not multiples of 10."""
    K = {k: [r["value"] for r in cs] for k, cs in hyp.okr().items()}
    _, _, dup = hyp.atlas()
    def grams(v):
        return {tuple(v[i:i + 4]) for i in range(len(v) - 3) if sum(x >= 10 and x % 10 for x in v[i:i + 4]) >= 2}
    idx = defaultdict(set)
    for k, v in K.items():
        for g in grams(v):
            idx[g].add(k)
    def pairs(tr):
        out = set()
        for k, v in K.items():
            for g in grams(tr(v)):
                for o in idx.get(g, ()):
                    if o != k and (k, o) not in dup:
                        out.add(tuple(sorted((k, o))))
        return out
    fw, rv = pairs(lambda v: v), pairs(lambda v: v[::-1])
    sims = [len(pairs(lambda v: R.sample(v, len(v)))) for _ in range(10)]
    print(f"H52b: pairs forward {len(fw)}; reversed {len(rv)}; shuffled mean {statistics.mean(sims):.1f}, max {max(sims)}")
    print("   reversed: " + ", ".join(f"{a}~{b}" for a, b in sorted(rv)))


def h50b():
    """H50 controlled for size: per-khipu median spacing regressed on median cord length and median number of clusters;
    residuals tested for site clustering."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    rows = {}
    for k, cs in K.items():
        d, L, nc = [], [], []
        for r in cs:
            ps = [c["pos"] for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0]
            d += [b - a for a, b in zip(ps, ps[1:]) if b > a]
            if r["length"] > 0:
                L.append(r["length"])
            nc.append(len(ps))
        if len(d) >= 10 and site.get(k) and L:
            rows[k] = (statistics.median(d), statistics.median(L), statistics.mean(nc))
    ks = list(rows)
    X = [[1.0, rows[k][1], rows[k][2]] for k in ks]
    y = [rows[k][0] for k in ks]
    # least squares via normal equations (3x3)
    A = [[sum(x[i] * x[j] for x in X) for j in range(3)] for i in range(3)]
    b = [sum(x[i] * t for x, t in zip(X, y)) for i in range(3)]
    for i in range(3):
        for j in range(i + 1, 3):
            f = A[j][i] / A[i][i]
            A[j] = [a - f * c for a, c in zip(A[j], A[i])]; b[j] -= f * b[i]
    w = [0.0] * 3
    for i in (2, 1, 0):
        w[i] = (b[i] - sum(A[i][j] * w[j] for j in range(i + 1, 3))) / A[i][i]
    res = {k: t - sum(wi * xi for wi, xi in zip(w, x)) for k, x, t in zip(ks, X, y)}
    def within(lab):
        g = defaultdict(list)
        for k in ks:
            g[lab[k]].append(res[k])
        v = [x for x in g.values() if len(x) >= 3]
        return sum(statistics.pvariance(x) * len(x) for x in v) / sum(len(x) for x in v)
    labs = [site[k] for k in ks]
    real = within(dict(zip(ks, labs)))
    sims = []
    for _ in range(1000):
        R.shuffle(labs)
        sims.append(within(dict(zip(ks, labs))))
    print(f"H50b: coefficients (const, length, clusters) {[round(x, 3) for x in w]}; residual within-site variance {real:.2f} "
          f"vs shuffled {statistics.mean(sims):.2f}; p {(1 + sum(x <= real for x in sims)) / 1001:.4f}")
    g = defaultdict(list)
    for k in ks:
        g[site[k]].append(rows[k][0])
    for s_, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
        if len(v) >= 4:
            print(f"   {s_:12} n={len(v):3} median spacing {statistics.median(v):.1f} cm, IQR {statistics.quantiles(v, n=4)[0]:.1f}–{statistics.quantiles(v, n=4)[2]:.1f}")


def h47b():
    """H47 counted once per khipu: in how many khipus is a size the most common group size."""
    K = hyp.okr()
    c, any_ = Counter(), Counter()
    for cs in K.values():
        sz = Counter(len(g) for g in hyp.groups(cs) if len(g) > 1)
        if sz:
            c[sz.most_common(1)[0][0]] += 1
            for n in sz:
                any_[n] += 1
    print("H47b: modal group size per khipu " + ", ".join(f"{n}:{c[n]}" for n in range(2, 25)))
    print("   khipus having a group of size " + ", ".join(f"{n}:{any_[n]}" for n in range(2, 25)))


def h49b():
    """Round values by region, one number per khipu (share of values 10–999 ending in 0); central coast (lima, huacho,
    armatambo, pachacamac) against the rest, Mann–Whitney via permutation."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    cc = {"lima", "huacho", "armatambo", "pachacamac", "huaquerones", "ancon", "chancay"}
    sh = {}
    for k, cs in K.items():
        v = [r["value"] for r in cs if 10 <= r["value"] <= 999]
        if len(v) >= 10 and site.get(k):
            sh[k] = sum(x % 10 == 0 for x in v) / len(v)
    a = [sh[k] for k in sh if site[k] in cc]
    b = [sh[k] for k in sh if site[k] not in cc]
    real = statistics.median(a) - statistics.median(b)
    pool, n = a + b, len(a)
    sims = []
    for _ in range(5000):
        R.shuffle(pool)
        sims.append(statistics.median(pool[:n]) - statistics.median(pool[n:]))
    print(f"H49b: central coast khipus {len(a)} median share round {statistics.median(a):.2f}; others {len(b)} {statistics.median(b):.2f}; "
          f"p {(1 + sum(x >= real for x in sims)) / 5001:.4f}")
    g = defaultdict(list)
    for k in sh:
        g[site[k]].append(sh[k])
    print("   " + "; ".join(f"{s_} {statistics.median(v):.2f} (n={len(v)})" for s_, v in sorted(g.items(), key=lambda kv: -statistics.median(kv[1])) if len(v) >= 4))


def h52c():
    """Mirror copies, strict: pairs sharing a run of 5 consecutive values with at least 3 of them ≥ 10 and not round,
    forward against reversed. Known copies should appear forward; mirror copies would appear reversed only."""
    K = {k: [r["value"] for r in cs] for k, cs in hyp.okr().items()}
    _, _, dup = hyp.atlas()
    def grams(v):
        return {tuple(v[i:i + 5]) for i in range(len(v) - 4) if sum(x >= 10 and x % 10 for x in v[i:i + 5]) >= 3}
    idx = defaultdict(set)
    for k, v in K.items():
        for g in grams(v):
            idx[g].add(k)
    def pairs(tr):
        out = Counter()
        for k, v in K.items():
            for g in grams(tr(v)):
                for o in idx.get(g, ()):
                    if o != k and (k, o) not in dup:
                        out[tuple(sorted((k, o)))] += 1
        return out
    fw, rv = pairs(lambda v: v), pairs(lambda v: v[::-1])
    print(f"H52c: pairs forward {len(fw)}; reversed {len(rv)}")
    print("   forward: " + ", ".join(f"{a}~{b}({n})" for (a, b), n in fw.most_common(40)))
    print("   reversed: " + ", ".join(f"{a}~{b}({n})" for (a, b), n in rv.most_common(40)))


def h50c():
    """H50 inside one recording team (UR khipus only), so the measuring protocol is the same."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    med = {}
    for k, cs in K.items():
        if not k.startswith("UR"):
            continue
        d = []
        for r in cs:
            ps = [c["pos"] for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0]
            d += [b - a for a, b in zip(ps, ps[1:]) if b > a]
        if len(d) >= 10 and site.get(k):
            med[k] = statistics.median(d)
    ks = list(med)
    def within(lab):
        g = defaultdict(list)
        for k in ks:
            g[lab[k]].append(med[k])
        v = [x for x in g.values() if len(x) >= 3]
        return sum(statistics.pvariance(x) * len(x) for x in v) / sum(len(x) for x in v)
    labs = [site[k] for k in ks]
    real = within(dict(zip(ks, labs)))
    sims = []
    for _ in range(1000):
        R.shuffle(labs)
        sims.append(within(dict(zip(ks, labs))))
    print(f"H50c: UR khipus {len(ks)}; within-site variance {real:.2f} vs shuffled {statistics.mean(sims):.2f}; "
          f"p {(1 + sum(x <= real for x in sims)) / 1001:.4f}")


def spacing(cs):
    d = []
    for r in cs:
        ps = [c["pos"] for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0]
        d += [b - a for a, b in zip(ps, ps[1:]) if b > a]
    return statistics.median(d) if len(d) >= 10 else None


def h53():
    """Linked khipus (atlas links) share the place spacing more closely than random pairs from the same site."""
    K = hyp.okr()
    D, site, _ = hyp.atlas()
    sp = {k: spacing(cs) for k, cs in K.items()}
    sp = {k: v for k, v in sp.items() if v is not None}
    pairs = {tuple(sorted((e["from"], e["to"]))) for e in D["edges"] if e["from"] in sp and e["to"] in sp}
    real = [abs(sp[a] - sp[b]) for a, b in pairs]
    by = defaultdict(list)
    for k in sp:
        by[site.get(k)].append(k)
    sims = []
    for _ in range(2000):
        x = []
        for a, b in pairs:
            pool = by[site.get(a)]
            o = R.choice(pool) if len(pool) > 1 else None
            while o == a and len(pool) > 1:
                o = R.choice(pool)
            if o:
                x.append(abs(sp[a] - sp[o]))
        sims.append(statistics.mean(x))
    m = statistics.mean(real)
    print(f"H53: linked pairs with spacing {len(pairs)}; mean |difference| {m:.2f} cm; same-site random {statistics.mean(sims):.2f}; "
          f"p {(1 + sum(x <= m for x in sims)) / 2001:.4f}; identical spacing in {sum(d == 0 for d in real)} pairs")


def h57():
    """Check digits: in groups with ≥ 4 cords the last cord equals the sum of the others mod 10 (or mod 9), excluding
    exact sums, more often than with the cords shuffled."""
    K = hyp.okr()
    G = [[r["value"] for r in g] for cs in K.values() for g in hyp.groups(cs) if len(g) >= 4]
    def cnt(gs, m, pos):
        n = 0
        for v in gs:
            i = 0 if pos == "first" else -1
            t, rest = v[i], (v[1:] if pos == "first" else v[:-1])
            if t != sum(rest) and t > 0 and t % m == sum(rest) % m:
                n += 1
        return n
    for m in (9, 10):
        for pos in ("first", "last"):
            real = cnt(G, m, pos)
            sims = []
            for _ in range(200):
                sims.append(cnt([R.sample(v, len(v)) for v in G], m, pos))
            print(f"H57: mod {m}, {pos} cord: {real}; shuffled {statistics.mean(sims):.1f}, max {max(sims)} (groups {len(G)})")


def h60():
    """Subsidiaries as adjustments: pendant ± its subsidiaries matches a group total / another cord of the khipu more
    often than the pendant alone (only pendants that have subsidiaries with values)."""
    K = hyp.okr()
    res = Counter()
    for cs in K.values():
        tot = {sum(r["value"] for r in g) for g in hyp.groups(cs)} | {r["value"] for r in cs}
        for r in cs:
            s = sum(x["value"] for x in r["subs"])
            if not s or r["value"] < 10:
                continue
            others = tot - {r["value"]}
            res["n"] += 1
            res["alone"] += r["value"] in others
            res["plus"] += r["value"] + s in others
            res["minus"] += r["value"] - s in others
            res["plus±1"] += (r["value"] + s + 1 in others) + (r["value"] + s - 1 in others)
    print(f"H60: pendants with valued subsidiaries {res['n']}; value found elsewhere: alone {res['alone']}, plus subs {res['plus']}, "
          f"minus subs {res['minus']}; plus subs ±1 (baseline, per side) {res['plus±1'] / 2:.1f}")


def h61():
    """Handedness: per-khipu share of S single knots is bimodal with a minority mode near 10% of khipus."""
    K = hyp.okr()
    sh = []
    for cs in K.values():
        c = Counter(k[1] for r in cs for cl in r["clusters"] for k in cl["knots"] if k[0] == "S" and k[1] in ("S", "Z"))
        if sum(c.values()) >= 30:
            sh.append(c["S"] / sum(c.values()))
    h = Counter(min(9, int(x * 10)) for x in sh)
    print(f"H61: khipus {len(sh)}; share of S-direction single knots, by tenths: " + " ".join(f"{i / 10:.1f}:{h[i]}" for i in range(10)))


def h62():
    """Colour and magnitude: within khipus, cords of dark colours (KB, MB, DB) hold larger values than white/light (W, AB)."""
    K = hyp.okr()
    dark, light = {"KB", "MB", "DB", "B"}, {"W", "AB", "YB"}
    real, n, sims = 0, 0, [0] * 500
    for cs in K.values():
        xs = [(r["colour"][0], r["value"]) for r in cs if r["value"] > 0 and not r["colour"][1]]
        d = [v for c, v in xs if c in dark]
        l_ = [v for c, v in xs if c in light]
        if len(d) < 3 or len(l_) < 3:
            continue
        n += 1
        real += statistics.median(d) > statistics.median(l_)
        vals = [v for c, v in xs if c in dark | light]
        for i in range(500):
            R.shuffle(vals)
            sims[i] += statistics.median(vals[:len(d)]) > statistics.median(vals[len(d):])
    print(f"H62: khipus {n}; dark median larger in {real}; shuffled mean {statistics.mean(sims):.1f}, "
          f"p {(1 + sum(x >= real for x in sims)) / 501:.4f}")


def h64():
    """Inca decimal units with halves: 50, 500, 5000 are over-represented against 40/60, 400/600, 4000/6000."""
    vals = all_values()
    for a, b, c in ((40, 50, 60), (400, 500, 600), (4000, 5000, 6000), (90, 100, 110), (900, 1000, 1100), (20, 30, 40), (200, 300, 400)):
        print(f"H64: {a}:{vals.get(a, 0)}  {b}:{vals.get(b, 0)}  {c}:{vals.get(c, 0)}")


def h60b():
    """H60 with a proper baseline: subsidiary sums shuffled among the pendants of the same khipu that have subsidiaries.
    Targets: other pendants' values and group totals of other groups."""
    K = hyp.okr()
    def run(shuffle):
        out = Counter()
        for cs in K.values():
            rs = [r for r in cs if r["value"] >= 10 and sum(x["value"] for x in r["subs"])]
            if not rs:
                continue
            ss = [sum(x["value"] for x in r["subs"]) for r in rs]
            if shuffle:
                R.shuffle(ss)
            gs = hyp.groups(cs)
            gid = {id(r): i for i, g in enumerate(gs) for r in g}
            gt = [sum(r["value"] for r in g) for g in gs]
            for r, s_ in zip(rs, ss):
                tgt = {x["value"] for x in cs if x is not r} | {t for i, t in enumerate(gt) if i != gid[id(r)]}
                out["plus"] += r["value"] + s_ in tgt
                out["minus"] += r["value"] - s_ in tgt
        return out
    real = run(False)
    sims = [run(True) for _ in range(100)]
    for k in ("plus", "minus"):
        v = [x[k] for x in sims]
        print(f"H60b: pendant {k} its subsidiaries found elsewhere: {real[k]}; shuffled {statistics.mean(v):.1f}, max {max(v)}")


def h62b():
    """H62 reversed: light cords (W, AB, YB) hold larger values than dark (KB, MB, DB, B); also with group totals removed
    (cords equal to the sum of the rest of their group or of another group)."""
    K = hyp.okr()
    dark, light = {"KB", "MB", "DB", "B"}, {"W", "AB", "YB"}
    for drop in (False, True):
        real, n, sims = 0, 0, [0] * 500
        for cs in K.values():
            tot = set()
            if drop:
                for g in hyp.groups(cs):
                    t = sum(r["value"] for r in g)
                    for r in g:
                        if r["value"] and r["value"] * 2 == t:
                            tot.add(id(r))
                gts = {sum(r["value"] for r in g) for g in hyp.groups(cs)}
                tot |= {id(r) for r in cs if r["value"] >= 10 and r["value"] in gts}
            xs = [(r["colour"][0], r["value"]) for r in cs if r["value"] > 0 and not r["colour"][1] and id(r) not in tot]
            d = [v for c, v in xs if c in dark]
            l_ = [v for c, v in xs if c in light]
            if len(d) < 3 or len(l_) < 3:
                continue
            n += 1
            real += statistics.median(l_) > statistics.median(d)
            vals = [v for c, v in xs if c in dark | light]
            for i in range(500):
                R.shuffle(vals)
                sims[i] += statistics.median(vals[len(d):]) > statistics.median(vals[:len(d)])
        print(f"H62b: totals removed {drop}: khipus {n}; light median larger in {real}; shuffled mean {statistics.mean(sims):.1f}, "
              f"p {(1 + sum(x >= real for x in sims)) / 501:.4f}")


def h61b():
    """H61: is the S-mode a recording artefact? Share of S-mode khipus by recording team (prefix) and by site."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    by_t, by_s = defaultdict(Counter), defaultdict(Counter)
    for k, cs in K.items():
        c = Counter(kk[1] for r in cs for cl in r["clusters"] for kk in cl["knots"] if kk[0] == "S" and kk[1] in ("S", "Z"))
        if sum(c.values()) >= 30:
            m = "S" if c["S"] / sum(c.values()) >= 0.5 else "Z"
            by_t[k[:2]][m] += 1
            by_s[site.get(k)][m] += 1
    print("H61b: by team " + "; ".join(f"{t} S {c['S']} / Z {c['Z']}" for t, c in sorted(by_t.items())))
    print("   by site " + "; ".join(f"{s_} S {c['S']} / Z {c['Z']}" for s_, c in sorted(by_s.items(), key=lambda kv: -sum(kv[1].values())) if sum(c.values()) >= 4))


def h67():
    """Self-reference: a group contains a cord whose value equals the number of cords in the group (or of its non-zero
    cords), more often than size ± 1…3. Groups of ≥ 4 cords; the counted size excludes nothing."""
    K = hyp.okr()
    G = [[r["value"] for r in g] for cs in K.values() for g in hyp.groups(cs) if len(g) >= 4]
    for name, f in (("all cords", len), ("non-zero cords", lambda v: sum(1 for x in v if x))):
        res = {d: sum(1 for v in G if f(v) + d in v) for d in range(-3, 4)}
        res2 = {d: sum(1 for v in G if f(v) + d in (v[0], v[-1])) for d in range(-3, 4)}
        print(f"H67: {name}: anywhere " + ", ".join(f"{d:+d}:{n}" for d, n in res.items()) + " | first/last " + ", ".join(f"{d:+d}:{n}" for d, n in res2.items()))
    T = []
    for cs in K.values():
        n = len(cs)
        T.append(sum(1 for r in cs if r["value"] == n))
    sh = {d: sum(1 for cs in K.values() if any(r["value"] == len(cs) + d for r in cs)) for d in range(-3, 4)}
    print("   khipu size on a cord: " + ", ".join(f"{d:+d}:{n}" for d, n in sh.items()))


def h69():
    """Numbering: runs of ≥ 4 adjacent pendants with consecutive values (v, v+1, v+2, v+3), v ≥ 1, against cords shuffled
    within group."""
    K = hyp.okr()
    G = [[r["value"] for r in g] for cs in K.values() for g in hyp.groups(cs) if len(g) >= 4]
    def cnt(gs, step):
        n = 0
        for v in gs:
            for i in range(len(v) - 3):
                if v[i] >= 1 and all(v[i + j + 1] - v[i + j] == step for j in range(3)):
                    n += 1
        return n
    for step in (1, -1):
        real = cnt(G, step)
        sims = [cnt([R.sample(v, len(v)) for v in G], step) for _ in range(200)]
        print(f"H69: step {step:+d}: runs {real}; shuffled mean {statistics.mean(sims):.1f}, max {max(sims)}")


def h70():
    """Progressions: runs of 4 adjacent cords with a constant non-zero difference (|d| ≥ 2), or doubling (x, 2x, 4x), against
    shuffled cords within group."""
    K = hyp.okr()
    G = [[r["value"] for r in g] for cs in K.values() for g in hyp.groups(cs) if len(g) >= 4]
    def ap(gs):
        n, ex = 0, []
        for v in gs:
            for i in range(len(v) - 3):
                d = v[i + 1] - v[i]
                if abs(d) >= 2 and v[i] > 0 and v[i + 2] - v[i + 1] == d and v[i + 3] - v[i + 2] == d:
                    n += 1; ex.append(v[i:i + 4])
        return n, ex
    def dbl(gs):
        n, ex = 0, []
        for v in gs:
            for i in range(len(v) - 2):
                if v[i] >= 2 and v[i + 1] == 2 * v[i] and v[i + 2] == 4 * v[i]:
                    n += 1; ex.append(v[i:i + 3])
                if v[i + 2] >= 2 and v[i + 1] == 2 * v[i + 2] and v[i] == 4 * v[i + 2]:
                    n += 1; ex.append(v[i:i + 3])
        return n, ex
    for name, f in (("arithmetic", ap), ("doubling", dbl)):
        real, ex = f(G)
        sims = [f([R.sample(v, len(v)) for v in G])[0] for _ in range(200)]
        print(f"H70: {name}: {real}; shuffled mean {statistics.mean(sims):.1f}, max {max(sims)}; e.g. {ex[:12]}")


def h73():
    """Internal copies: a khipu repeats a run of ≥ 5 informative values (≥ 10, not round) in another place of itself
    (non-overlapping), more often than with its cords shuffled."""
    K = hyp.okr()
    def longest(v):
        best, at = 0, None
        n = len(v)
        for sh in range(5, n):
            run = 0
            for i in range(n - sh):
                if v[i] == v[i + sh] and v[i] >= 10 and v[i] % 10:
                    run += 1
                    if run > best and run <= sh:
                        best, at = run, (i - run + 2, i + sh - run + 2)
                elif v[i] == v[i + sh] and v[i] > 0:
                    pass
                else:
                    run = 0
        return best, at
    real = {}
    for k, cs in K.items():
        v = [r["value"] for r in cs]
        b, at = longest(v)
        if b >= 3:
            real[k] = (b, at, len(v))
    sims = []
    for _ in range(5):
        c = 0
        for k, cs in K.items():
            v = [r["value"] for r in cs]
            R.shuffle(v)
            c += longest(v)[0] >= 3
        sims.append(c)
    print(f"H73: khipus with an internal repeat of ≥ 3 informative values: {len(real)}; shuffled {sims}")
    for k, (b, at, n) in sorted(real.items(), key=lambda kv: -kv[1][0])[:25]:
        print(f"   {k:10} run {b} at cords {at[0]} and {at[1]} of {n}")


def h73b():
    """H73 strict: a repeated run of ≥ 4 cords at a shift ≥ 2 (non-overlapping) with ≥ 3 distinct informative values."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    def reps(v):
        out, n = [], len(v)
        for sh in range(2, n):
            i = 0
            while i < n - sh:
                j = i
                while j < n - sh and v[j] == v[j + sh]:
                    j += 1
                run = v[i:j]
                if 4 <= j - i <= sh and len({x for x in run if x >= 10 and x % 10}) >= 3:
                    out.append((i + 1, i + sh + 1, j - i, run))
                i = max(j, i + 1)
        return out
    real = {k: reps([r["value"] for r in cs]) for k, cs in K.items()}
    real = {k: v for k, v in real.items() if v}
    sims = []
    for _ in range(10):
        c = 0
        for cs in K.values():
            v = [r["value"] for r in cs]
            R.shuffle(v)
            c += bool(reps(v))
        sims.append(c)
    print(f"H73b: khipus with an internal copy: {len(real)}; shuffled {sims}")
    for k, v in sorted(real.items()):
        a, b, n, run = max(v, key=lambda x: x[2])
        print(f"   {k:8} {site.get(k)} cords {a} and {b}, {n} long: {run[:10]}")


def copy_pairs():
    """Aligned cord pairs (pendants) of atlas copy-type links, OKR records: list of (a, b, [(ra, rb)]) with equal values."""
    sys.path.insert(0, str(hyp.ROOT / "khipu"))
    import copies_losses
    K = hyp.okr()
    D, _, _ = hyp.atlas()
    out = []
    for e in D["edges"]:
        if e["type"] not in ("copy", "excerpt", "details", "fold"):
            continue
        a, b = e["from"], e["to"]
        if a not in K or b not in K:
            continue
        A, B = K[a], K[b]
        pr = copies_losses.align([r["value"] for r in A], [r["value"] for r in B])
        out.append((a, b, [(A[i], B[j]) for i, j in pr if A[i]["value"] == B[j]["value"]]))
    return out


def h74():
    """Colour as a code: in copies, each colour of one khipu goes over to one colour of the other (consistent mapping).
    Consistency = share of matched cords whose colour pair is the most common pair for that source colour; baseline: colours
    of the target shuffled among matched cords of the pair."""
    P = copy_pairs()
    def cons(pairs):
        by = defaultdict(Counter)
        for ca, cb in pairs:
            by[ca][cb] += 1
        return sum(c.most_common(1)[0][1] for c in by.values()), len(pairs)
    tot_r, tot_s, n_all = 0, [0] * 300, 0
    lines = []
    for a, b, pr in P:
        cp = [(x["colour"][0], y["colour"][0]) for x, y in pr if x["colour"][0] and y["colour"][0]]
        if len(cp) < 8:
            continue
        r, n = cons(cp)
        same = sum(x == y for x, y in cp)
        tb = [y for _, y in cp]
        sims = []
        for i in range(300):
            R.shuffle(tb)
            s_ = cons(list(zip([x for x, _ in cp], tb)))[0]
            sims.append(s_); tot_s[i] += s_
        tot_r += r; n_all += n
        lines.append(f"   {a}~{b}: matched {n}, same colour {same}, consistent {r} vs {statistics.mean(sims):.1f} "
                     f"(p {(1 + sum(x >= r for x in sims)) / 301:.3f})")
    print(f"H74: pairs {len(lines)}; consistent {tot_r}/{n_all} vs shuffled {statistics.mean(tot_s):.1f}; "
          f"p {(1 + sum(x >= tot_r for x in tot_s)) / 301:.4f}")
    print("\n".join(lines))


def h75():
    """Totals are marked physically: cords equal to the sum of the other cords of their group (≥ 3 others, total ≥ 10)
    differ in termination, attachment or twist from the rest of the khipu."""
    K = hyp.okr()
    tot, rest = Counter(), Counter()
    nt = nr = 0
    for cs in K.values():
        for g in hyp.groups(cs):
            v = [r["value"] for r in g]
            s_ = sum(v)
            for r in g:
                is_t = len(g) >= 4 and r["value"] >= 10 and r["value"] * 2 == s_
                C = tot if is_t else rest
                C["term " + r["term"]] += 1; C["att " + r["att"]] += 1; C["twist " + r["twist"]] += 1
                if is_t:
                    nt += 1
                else:
                    nr += 1
    keys = sorted(set(tot) | set(rest))
    print(f"H75: totals {nt}, other cords {nr}")
    for k in keys:
        if tot[k] + rest[k] > 50:
            print(f"   {k:10} totals {tot[k] / nt:.3f}  others {rest[k] / nr:.3f}")


def h77():
    """Forms: in khipus with ≥ 3 groups of the same size, zero cords stand in the same slots across those groups more than
    with cords shuffled within each group."""
    K = hyp.okr()
    real = sims_t = 0
    sims = [0] * 200
    nk = 0
    for cs in K.values():
        by = defaultdict(list)
        for g in hyp.groups(cs):
            by[len(g)].append([r["value"] == 0 for r in g])
        for n, gs in by.items():
            if n < 4 or len(gs) < 3:
                continue
            z = sum(map(sum, gs))
            if z < 3 or z == n * len(gs):
                continue
            nk += 1
            def agree(gg):
                return sum(max(c, len(gg) - c) for c in (sum(col) for col in zip(*gg)))
            real += agree(gs)
            for i in range(200):
                sims[i] += agree([R.sample(g, len(g)) for g in gs])
    print(f"H77: sets of equal-size groups {nk}; slot agreement {real} vs shuffled {statistics.mean(sims):.1f}, max {max(sims)}")


def h78():
    """Ceque numbers: 328 (huacas), 41 (ceques), 365, 12, 30 more common than their neighbours."""
    vals = all_values()
    for x in (12, 30, 41, 328, 365, 354, 360):
        print(f"H78: {x}: {vals.get(x, 0)}; neighbours " + ", ".join(str(vals.get(x + d, 0)) for d in (-2, -1, 1, 2)))


def h79():
    """Round group totals: group sums exactly 100, 1000 (and multiples of 100) more often than sums shifted ±1…±5."""
    K = hyp.okr()
    T = [sum(r["value"] for r in g) for cs in K.values() for g in hyp.groups(cs) if len(g) >= 3]
    for base in (100, 1000):
        f = lambda d: sum(1 for t in T if t >= base and (t + d) % base == 0)
        print(f"H79: group sums ≥ {base} that are multiples of {base}: {f(0)}; shifted " + ", ".join(str(f(d)) for d in (-5, -3, -1, 1, 3, 5)))
    print(f"   exactly 100: {T.count(100)} (99: {T.count(99)}, 101: {T.count(101)}); 1000: {T.count(1000)} (999: {T.count(999)}, 1001: {T.count(1001)})")


def h74b():
    """H74 with block structure kept: target colours shifted circularly along the matched cords (all shifts ≥ 3)."""
    P = copy_pairs()
    def cons(pairs):
        by = defaultdict(Counter)
        for ca, cb in pairs:
            by[ca][cb] += 1
        return sum(c.most_common(1)[0][1] for c in by.values())
    for a, b, pr in P:
        cp = [(x["colour"][0], y["colour"][0]) for x, y in pr if x["colour"][0] and y["colour"][0]]
        if len(cp) < 8:
            continue
        xs, ys = [x for x, _ in cp], [y for _, y in cp]
        r = cons(cp)
        sims = [cons(list(zip(xs, ys[k:] + ys[:k]))) for k in range(3, len(ys) - 2)]
        print(f"H74b: {a}~{b}: consistent {r}/{len(cp)}; circular shifts mean {statistics.mean(sims):.1f}, max {max(sims)}; "
              f"p {(1 + sum(x >= r for x in sims)) / (1 + len(sims)):.3f}")


def h79b():
    """H79 controlled: only groups with ≥ 2 non-round cords (value not a multiple of 10), so a round sum is not automatic."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    T = []
    for k, cs in K.items():
        for g in hyp.groups(cs):
            v = [r["value"] for r in g]
            if len(v) >= 3 and sum(1 for x in v if x % 10) >= 2:
                T.append((sum(v), k, v))
    for base in (100, 1000):
        f = lambda d: sum(1 for t, _, _ in T if t >= base and (t + d) % base == 0)
        print(f"H79b: multiples of {base}: {f(0)}; shifted " + ", ".join(str(f(d)) for d in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)))
    ex = Counter(k for t, k, _ in T if t >= 100 and t % 100 == 0)
    print("   by khipu: " + ", ".join(f"{k} ({site.get(k)}) {n}" for k, n in ex.most_common(20)))
    for t, k, v in sorted(T, key=lambda x: -x[0]):
        if t >= 100 and t % 100 == 0:
            print(f"   {k:8} {t}: {v[:16]}")


def h82():
    """Colour as a category across khipus of one site: the order of colours by median value agrees between khipus of a site
    (mean pairwise Spearman over shared colours) more than with colour labels shuffled within each khipu."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    prof = defaultdict(dict)
    raw = {}
    for k, cs in K.items():
        xs = [(r["colour"][0], r["value"]) for r in cs if r["value"] > 0 and r["colour"][0] and not r["colour"][1]]
        if site.get(k) and len(xs) >= 20:
            raw[k] = xs
    def profile(xs):
        by = defaultdict(list)
        for c, v in xs:
            by[c].append(v)
        return {c: statistics.median(v) for c, v in by.items() if len(v) >= 3}
    def score(P):
        by = defaultdict(list)
        for k, p in P.items():
            by[site[k]].append(p)
        rs = []
        for ps in by.values():
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    sh = sorted(set(ps[i]) & set(ps[j]))
                    if len(sh) >= 3:
                        rs.append(spearman([ps[i][c] for c in sh], [ps[j][c] for c in sh]))
        return statistics.mean(rs), len(rs)
    real, n = score({k: profile(x) for k, x in raw.items()})
    sims = []
    for _ in range(200):
        P = {}
        for k, xs in raw.items():
            cs_ = [c for c, _ in xs]
            R.shuffle(cs_)
            P[k] = profile(list(zip(cs_, [v for _, v in xs])))
        sims.append(score(P)[0])
    print(f"H82: khipu pairs within sites sharing ≥ 3 colours: {n}; mean Spearman {real:.3f}; shuffled {statistics.mean(sims):.3f}, "
          f"max {max(sims):.3f}")


def h85():
    """Two columns: within a khipu the height (cm from the main cord) of the units cluster differs by cord colour more
    than with colours shuffled (variance explained by colour)."""
    K = hyp.okr()
    real_t = 0.0
    sims_t = [0.0] * 200
    n = 0
    for cs in K.values():
        xs = []
        for r in cs:
            ps = [c["pos"] for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0]
            if ps and r["colour"][0] and not r["colour"][1]:
                xs.append((r["colour"][0], max(ps)))
        cols = Counter(c for c, _ in xs)
        xs = [x for x in xs if cols[x[0]] >= 3]
        if len(xs) < 20 or len({c for c, _ in xs}) < 2:
            continue
        def r2(pairs):
            ys = [y for _, y in pairs]
            m = statistics.mean(ys)
            tot = sum((y - m) ** 2 for y in ys) or 1
            by = defaultdict(list)
            for c, y in pairs:
                by[c].append(y)
            return sum(len(v) * (statistics.mean(v) - m) ** 2 for v in by.values()) / tot
        n += 1
        real_t += r2(xs)
        cl = [c for c, _ in xs]
        ys = [y for _, y in xs]
        for i in range(200):
            R.shuffle(cl)
            sims_t[i] += r2(list(zip(cl, ys)))
    print(f"H85: khipus {n}; mean R² of units height on colour {real_t / n:.3f}; shuffled {statistics.mean(sims_t) / n:.3f}, max {max(sims_t) / n:.3f}")


def h86():
    """Calendar counts: numbers of groups per khipu peak at 12, 24, 30, 36 (and pendant counts at 360/365)."""
    K = hyp.okr()
    g = Counter(len(hyp.groups(cs)) for cs in K.values())
    print("H86: groups per khipu " + ", ".join(f"{n}:{g[n]}" for n in range(1, 41)))
    p = Counter(len(cs) for cs in K.values())
    print("   pendants per khipu: 12:%d 24:%d 30:%d 36:%d 360:%d 365:%d; multiples of 10: %d of %d" % (
        p[12], p[24], p[30], p[36], p[360], p[365], sum(c for n, c in p.items() if n % 10 == 0), sum(p.values())))


def h92():
    """A grand total: some cord equals the sum of all other pendants of the khipu (or the sum of all group totals but
    its own group), against the sum shifted ±1…±5."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    def cnt(d):
        n, ex = 0, []
        for k, cs in K.items():
            v = [r["value"] for r in cs]
            s_ = sum(v)
            if s_ < 20:
                continue
            for i, x in enumerate(v):
                if x and x * 2 + d == s_:
                    n += 1; ex.append((k, i + 1, x)); break
        return n, ex
    real, ex = cnt(0)
    sh = [cnt(d)[0] for d in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)]
    print(f"H92: khipus with a grand-total cord: {real}; shifted {sh}")
    for k, i, x in ex:
        print(f"   {k} ({site.get(k)}) cord {i} = {x} of {len(K[k])}")


def h85b():
    """H85 within groups: colours shuffled only inside each group (group heights kept); R² of units height on colour
    computed within groups (group means removed)."""
    K = hyp.okr()
    real_t, sims_t, n = 0.0, [0.0] * 200, 0
    for cs in K.values():
        rows = []
        for gi, g in enumerate(hyp.groups(cs)):
            ys = []
            for r in g:
                ps = [c["pos"] for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0]
                if ps and r["colour"][0] and not r["colour"][1]:
                    ys.append((r["colour"][0], max(ps)))
            if len(ys) >= 3 and len({c for c, _ in ys}) >= 2:
                m = statistics.mean(y for _, y in ys)
                rows.append([(c, y - m) for c, y in ys])
        flat = [x for g in rows for x in g]
        if len(flat) < 20:
            continue
        def r2(pairs):
            tot = sum(y * y for _, y in pairs) or 1
            by = defaultdict(list)
            for c, y in pairs:
                by[c].append(y)
            return sum(len(v) * statistics.mean(v) ** 2 for v in by.values()) / tot
        n += 1
        real_t += r2(flat)
        for i in range(200):
            sh = []
            for g in rows:
                cl = [c for c, _ in g]
                R.shuffle(cl)
                sh += list(zip(cl, [y for _, y in g]))
            sims_t[i] += r2(sh)
    print(f"H85b: khipus {n}; within-group R² {real_t / n:.3f}; shuffled within groups {statistics.mean(sims_t) / n:.3f}, max {max(sims_t) / n:.3f}")


def h96():
    """Golden ratio: adjacent cords (both ≥ 10) with ratio within 1% of 1.618 more often than ratios near 1.5 and 1.75."""
    K = hyp.okr()
    rs = []
    for cs in K.values():
        for g in hyp.groups(cs):
            v = [r["value"] for r in g]
            for a, b in zip(v, v[1:]):
                if a >= 10 and b >= 10:
                    rs.append(max(a, b) / min(a, b))
    for t in (1.5, 1.55, 1.6, 1.618, 1.65, 1.7, 1.75):
        print(f"H96: ratio {t}: {sum(1 for x in rs if abs(x - t) / t < 0.01)}")


def h98():
    """Lunar months: adjacent 29/30 pairs (alternating month lengths) against 28/29, 30/31 and 27/28."""
    K = hyp.okr()
    c = Counter()
    for cs in K.values():
        v = [r["value"] for r in cs]
        for a, b in zip(v, v[1:]):
            c[tuple(sorted((a, b)))] += 1
    for p_ in ((27, 28), (28, 29), (29, 30), (30, 31), (31, 32)):
        print(f"H98: adjacent {p_}: {c[p_]}")


def h101():
    """Change records: the difference between totals of adjacent groups (≥ 10, not round) is written on a cord of the
    khipu, more often than differences between non-adjacent group pairs at distance 2–4."""
    K = hyp.okr()
    hit = {1: [0, 0], 2: [0, 0], 3: [0, 0], 4: [0, 0]}
    for cs in K.values():
        vals = {r["value"] for r in cs}
        t = [sum(r["value"] for r in g) for g in hyp.groups(cs)]
        for gap in hit:
            for a, b in zip(t, t[gap:]):
                d = abs(a - b)
                if d >= 10 and d % 10:
                    hit[gap][0] += 1; hit[gap][1] += d in vals
    for gap, (n, h) in hit.items():
        print(f"H101: groups {gap} apart: differences {n}, written on a cord {h} ({h / max(1, n):.3f})")


def h102():
    """Running totals: a cord equals the sum of all preceding cords of its group (≥ 3 preceding, sum ≥ 10), against the
    same with cords shuffled within group."""
    K = hyp.okr()
    G = [[r["value"] for r in g] for cs in K.values() for g in hyp.groups(cs) if len(g) >= 4]
    def cnt(gs):
        n = 0
        for v in gs:
            run = 0
            for i, x in enumerate(v):
                if i >= 3 and run >= 10 and x == run and x % 10:
                    n += 1
                run += x
        return n
    real = cnt(G)
    sims = [cnt([R.sample(v, len(v)) for v in G]) for _ in range(200)]
    print(f"H102: running-total cords {real}; shuffled mean {statistics.mean(sims):.1f}, max {max(sims)}")


def h105():
    """Pairs: some khipus count pairs — almost all their non-round values ≥ 10 are even. Khipus with ≥ 15 such values and
    ≥ 80% even (or odd), against the binomial expectation from the overall even share."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    rows = []
    for k, cs in K.items():
        v = [r["value"] for r in cs if r["value"] >= 10 and r["value"] % 10]
        if len(v) >= 15:
            rows.append((k, len(v), sum(1 for x in v if x % 2 == 0)))
    p = sum(e for _, _, e in rows) / sum(n for _, n, _ in rows)
    def tail(n, k):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))
    exp_even = sum(tail(n, math.ceil(0.8 * n)) for _, n, _ in rows)
    obs_even = [(k, n, e) for k, n, e in rows if e >= 0.8 * n]
    q = 1 - p
    exp_odd = sum(sum(math.comb(n, i) * q ** i * p ** (n - i) for i in range(math.ceil(0.8 * n), n + 1)) for _, n, _ in rows)
    obs_odd = [(k, n, e) for k, n, e in rows if n - e >= 0.8 * n]
    print(f"H105: khipus {len(rows)}; overall even share {p:.3f}; ≥ 80% even: {len(obs_even)} (expected {exp_even:.1f}); "
          f"≥ 80% odd: {len(obs_odd)} (expected {exp_odd:.1f})")
    for k, n, e in obs_even:
        print(f"   even {k} ({site.get(k)}) {e}/{n}")
    for k, n, e in obs_odd:
        print(f"   odd {k} ({site.get(k)}) {n - e}/{n}")


def h106():
    """Units digit 9 is avoided: among values ≥ 100 with a non-zero units digit, digits 7–9 are rarer than 1–6, by team
    prefix and by site (values relative to the mean share of 1–6). For values ≥ 100 the smooth fall of the value
    distribution cannot make the units digit uneven."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    by = defaultdict(Counter)
    for k, cs in K.items():
        for r in cs:
            v = r["value"]
            if v >= 100 and v % 10:
                by["ALL"][v % 10] += 1; by["team " + k[:2]][v % 10] += 1; by[str(site.get(k))][v % 10] += 1
    for g, c in sorted(by.items(), key=lambda kv: -sum(kv[1].values()))[:12]:
        n = sum(c.values())
        base = sum(c[d] for d in range(1, 7)) / 6
        print(f"H106: {g:14} n={n:5} " + " ".join(f"{d}:{c[d] / base:.2f}" for d in range(1, 10)))
    t = Counter(kk[3] for cs in K.values() for r in cs for cl in r["clusters"] for kk in cl["knots"] if kk[0] == "L")
    print("   long knots by turns: " + ", ".join(f"{n}:{t[n]}" for n in range(0, 13)))


def lk_rows(k):
    """Cords of khipu k on which every cluster is a single long knot: list of turn lists (by cord order)."""
    out = []
    for r in hyp.okr()[k]:
        cl = r["clusters"]
        if cl and all(c["type"] == "L" and len(c["knots"]) == 1 for c in cl):
            out.append([c["knots"][0][3] for c in cl])
    return out


def h107():
    """Long-knot-only khipus (every cluster one long knot): turn counts are not counted quantities but a knotter's habit —
    (a) far less spread than units digits of ordinary khipus (sd ≈ 2.6 for 1–9), (b) positions on one cord correlate,
    (c) neighbouring cords are more alike than distant ones (drift along the khipu), against cords shuffled."""
    K = hyp.okr()
    cand = []
    for k, cs in K.items():
        rows = lk_rows(k)
        if len(rows) >= 12 and statistics.mean(len(x) for x in rows) >= 2:
            cand.append((k, rows))
    for k, rows in cand:
        flat = [t for x in rows for t in x]
        m = [statistics.mean(x) for x in rows]
        def nb(v):
            return statistics.mean(abs(a - b) for a, b in zip(v, v[1:]))
        real = nb(m)
        sims = []
        for _ in range(1000):
            q = m[:]
            R.shuffle(q)
            sims.append(nb(q))
        print(f"H107: {k:11} cords {len(rows):3}, turns mean {statistics.mean(flat):.1f} sd {statistics.pstdev(flat):.2f}; "
              f"neighbour |Δ mean| {real:.2f} vs shuffled {statistics.mean(sims):.2f}, p {(1 + sum(x <= real for x in sims)) / 1001:.3f}")


def h109():
    """Rounding up: the sum of a group that ends in 7–9 appears elsewhere in the khipu as the next ten more often than a sum
    ending in 1–3 appears as the ten below (and than the cross controls)."""
    K = hyp.okr()
    hit = Counter()
    for cs in K.values():
        vals = Counter(r["value"] for r in cs)
        for g in hyp.groups(cs):
            S = sum(r["value"] for r in g)
            if S < 30 or S % 10 == 0 or len(g) < 2:
                continue
            up, down = (S // 10 + 1) * 10, S // 10 * 10
            inside = Counter(r["value"] for r in g)
            have = lambda x: vals[x] - inside[x] > 0
            e = S % 10
            if e >= 7:
                hit["7-9 n"] += 1; hit["7-9 up"] += have(up); hit["7-9 down"] += have(down); hit["7-9 exact"] += have(S)
            elif e <= 3:
                hit["1-3 n"] += 1; hit["1-3 up"] += have(up); hit["1-3 down"] += have(down); hit["1-3 exact"] += have(S)
    for e in ("7-9", "1-3"):
        n = hit[e + " n"]
        print(f"H109: sums ending {e}: {n}; next ten elsewhere {hit[e + ' up'] / n:.3f}; ten below {hit[e + ' down'] / n:.3f}; "
              f"exact sum elsewhere {hit[e + ' exact'] / n:.3f}")


def extra():
    """Pendant id → (fibre, thickness, attachment position on the main cord in cm) from OKR."""
    import sqlite3
    c = sqlite3.connect(hyp.DB)
    return {cid: ((f or "").strip(), float(t or 0), float(a) if a not in (None, "") else None)
            for cid, f, t, a in c.execute("select CORD_ID, FIBER, THICKNESS, ATTACH_POS from cord where CORD_LEVEL = 1")}


def within_compare(pairs_by_khipu, label_a, label_b, n_sims=500):
    """pairs_by_khipu: list of lists of (label, value). Counts khipus where median of a > median of b; baseline shuffles labels."""
    real, sims, n = 0, [0] * n_sims, 0
    for xs in pairs_by_khipu:
        a = [v for l, v in xs if l == label_a]
        b = [v for l, v in xs if l == label_b]
        if len(a) < 3 or len(b) < 3:
            continue
        n += 1
        real += statistics.median(a) > statistics.median(b)
        vals = [v for l, v in xs if l in (label_a, label_b)]
        for i in range(n_sims):
            R.shuffle(vals)
            sims[i] += statistics.median(vals[:len(a)]) > statistics.median(vals[len(a):])
    return n, real, statistics.mean(sims), (1 + sum(x >= real for x in sims)) / (n_sims + 1), (1 + sum(x <= real for x in sims)) / (n_sims + 1)


def h110():
    """Fibre: camelid (CL) cords carry different numbers from cotton (CN) cords of the same khipu."""
    K, X = hyp.okr(), extra()
    data = [[(X.get(r["id"], ("",))[0], r["value"]) for r in cs if r["value"] > 0] for cs in K.values()]
    n, real, m, p_hi, p_lo = within_compare(data, "CL", "CN")
    print(f"H110: khipus with ≥ 3 camelid and ≥ 3 cotton valued cords: {n}; camelid median larger in {real}; shuffled {m:.1f}; "
          f"p(≥) {p_hi:.4f}, p(≤) {p_lo:.4f}")
    col = Counter((X.get(r["id"], ("",))[0], r["colour"][0]) for cs in K.values() for r in cs)
    for f in ("CN", "CL"):
        tot = sum(v for (ff, _), v in col.items() if ff == f)
        print(f"   {f}: " + ", ".join(f"{c}:{v / tot:.2f}" for (ff, c), v in sorted(col.items(), key=lambda kv: -kv[1]) if ff == f and v / tot >= 0.04))


def h111():
    """Thickness: within khipus, thicker cords (above the khipu median) hold larger values."""
    K, X = hyp.okr(), extra()
    data = []
    for cs in K.values():
        th = [X.get(r["id"], ("", 0))[1] for r in cs]
        th = [t for t in th if t > 0]
        if len(set(th)) < 2:
            continue
        md = statistics.median(th)
        data.append([("thick" if X[r["id"]][1] > md else "thin", r["value"]) for r in cs if r["value"] > 0 and X.get(r["id"], ("", 0))[1] > 0 and X[r["id"]][1] != md])
    n, real, m, p_hi, p_lo = within_compare(data, "thick", "thin")
    print(f"H111: khipus {n}; thicker cords' median larger in {real}; shuffled {m:.1f}; p(≥) {p_hi:.4f}, p(≤) {p_lo:.4f}")


def h112():
    """Spacing on the main cord: within groups, the gap before a cord (attachment positions) correlates with its value;
    and gaps before cords that are group totals are wider."""
    K, X = hyp.okr(), extra()
    rs, sims, n = [], [], 0
    big, small = [], []
    for cs in K.values():
        pos = [X.get(r["id"], ("", 0, None))[2] for r in cs]
        if sum(p_ is not None for p_ in pos) < len(cs) * 0.8:
            continue
        for g in hyp.groups(cs):
            xs = []
            for r in g:
                i = cs.index(r)
                if i and pos[i] is not None and pos[i - 1] is not None and pos[i] > pos[i - 1]:
                    xs.append((pos[i] - pos[i - 1], r["value"]))
            if len(xs) >= 5 and len({v for _, v in xs}) > 2 and len({gp for gp, _ in xs}) > 2:
                rs.append(spearman([a for a, _ in xs], [b for _, b in xs]))
    print(f"H112: groups {len(rs)}; mean Spearman (gap before cord, value) {statistics.mean(rs):.3f}; positive in "
          f"{sum(r > 0 for r in rs)}, negative in {sum(r < 0 for r in rs)}")


def h116():
    """The sum of all pendants of a khipu is a round number (a set amount) more often than the sum shifted ±1…±10."""
    K = hyp.okr()
    S = [sum(r["value"] for r in cs) for cs in K.values()]
    S = [x for x in S if x >= 100]
    for base in (10, 100):
        f = lambda d: sum(1 for x in S if (x + d) % base == 0)
        sh = [f(d) for d in range(-10, 11) if d]
        print(f"H116: khipu sums ≥ 100 ({len(S)}) that are multiples of {base}: {f(0)}; shifted mean {statistics.mean(sh):.1f}, max {max(sh)}")


def h118():
    """Equal allotments: in khipus with ≥ 4 groups of the same size, group totals vary less than when the cords of those
    groups are dealt out at random among them (CV of totals)."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    real_lo, n, ex = 0, 0, []
    for k, cs in K.items():
        by = defaultdict(list)
        for g in hyp.groups(cs):
            by[len(g)].append([r["value"] for r in g])
        for sz, gs in by.items():
            if sz < 3 or len(gs) < 4:
                continue
            t = [sum(g) for g in gs]
            if statistics.mean(t) < 20:
                continue
            cv = statistics.pstdev(t) / statistics.mean(t)
            flat = [x for g in gs for x in g]
            sims = []
            for _ in range(300):
                R.shuffle(flat)
                tt = [sum(flat[i * sz:(i + 1) * sz]) for i in range(len(gs))]
                sims.append(statistics.pstdev(tt) / statistics.mean(tt))
            p_ = (1 + sum(x <= cv for x in sims)) / 301
            n += 1
            real_lo += p_ < 0.05
            if p_ < 0.01:
                ex.append((k, sz, len(gs), round(cv, 3), round(statistics.mean(sims), 3), t[:10]))
    print(f"H118: sets {n}; group totals more even than random (p < 0.05) in {real_lo} (expected {0.05 * n:.1f})")
    for e in ex[:20]:
        print(f"   {e[0]} ({site.get(e[0])}) {e[2]} groups of {e[1]}: CV {e[3]} vs {e[4]}; totals {e[5]}")


def h118b():
    """H118 with the table kept: values permuted across groups within each slot (column), so column sizes stay; row totals
    more even than that mean the rows were balanced (the columns compensate each other)."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    lo, hi, n, ex = 0, 0, 0, []
    for k, cs in K.items():
        by = defaultdict(list)
        for g in hyp.groups(cs):
            by[len(g)].append([r["value"] for r in g])
        for sz, gs in by.items():
            if sz < 3 or len(gs) < 4:
                continue
            t = [sum(g) for g in gs]
            if statistics.mean(t) < 20:
                continue
            cv = statistics.pstdev(t) / statistics.mean(t)
            cols = [list(c) for c in zip(*gs)]
            sims = []
            for _ in range(300):
                for c in cols:
                    R.shuffle(c)
                tt = [sum(row) for row in zip(*cols)]
                sims.append(statistics.pstdev(tt) / statistics.mean(tt))
            p_lo = (1 + sum(x <= cv for x in sims)) / 301
            p_hi = (1 + sum(x >= cv for x in sims)) / 301
            n += 1
            lo += p_lo < 0.05
            hi += p_hi < 0.05
            if p_lo < 0.01:
                ex.append((k, sz, len(gs), round(cv, 3), round(statistics.mean(sims), 3), t[:10]))
    print(f"H118b: sets {n}; rows more even than column-wise shuffles (p < 0.05) in {lo}, less even in {hi} (expected {0.05 * n:.1f} each)")
    for e in ex[:20]:
        print(f"   {e[0]} ({site.get(e[0])}) {e[2]} groups of {e[1]}: CV {e[3]} vs {e[4]}; totals {e[5]}")


def h120():
    """Age grades: in tables (≥ 4 groups of the same size ≥ 5), column means fall steadily from the first column to the
    last (as age grades of a census would); random column order gives a symmetric spread of Spearman around 0."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    rs, ex = [], []
    for k, cs in K.items():
        by = defaultdict(list)
        for g in hyp.groups(cs):
            by[len(g)].append([r["value"] for r in g])
        for sz, gs in by.items():
            if sz < 5 or len(gs) < 4:
                continue
            means = [statistics.mean(c) for c in zip(*gs)]
            if len(set(means)) < 3:
                continue
            r = spearman(list(range(sz)), means)
            rs.append(r)
            if abs(r) >= 0.8:
                ex.append((k, sz, len(gs), round(r, 2), [round(m) for m in means]))
    print(f"H120: tables {len(rs)}; mean Spearman (column index, column mean) {statistics.mean(rs):.3f}; ρ ≤ −0.8 in "
          f"{sum(r <= -0.8 for r in rs)}, ρ ≥ 0.8 in {sum(r >= 0.8 for r in rs)}; negative {sum(r < 0 for r in rs)}, positive {sum(r > 0 for r in rs)}")
    for e in ex[:25]:
        print(f"   {e[0]} ({site.get(e[0])}) {e[2]}×{e[1]} ρ {e[3]}: {e[4]}")


def h121():
    """Blank rows: groups of ≥ 4 cords with no knots at all whose colour sequence repeats that of a filled group of the same
    khipu (a prepared, unfilled row). They stand at the end of the khipu more often than at the start (filled in order)."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    rel, ex = [], []
    for k, cs in K.items():
        gs = hyp.groups(cs)
        if len(gs) < 4:
            continue
        pat = lambda g: tuple(r["colour"] for r in g)
        filled = {pat(g) for g in gs if sum(r["value"] for r in g) > 0}
        blanks = [i for i, g in enumerate(gs) if len(g) >= 4 and all(not r["clusters"] for r in g) and pat(g) in filled
                  and len({r["colour"] for r in g}) >= 2]
        if blanks:
            ex.append((k, len(gs), [i + 1 for i in blanks]))
            rel += [i / (len(gs) - 1) for i in blanks]
    print(f"H121: khipus with blank patterned rows: {len(ex)}; blank rows {len(rel)}; in the last third {sum(x > 2 / 3 for x in rel)}, "
          f"middle {sum(1 / 3 <= x <= 2 / 3 for x in rel)}, first third {sum(x < 1 / 3 for x in rel)}")
    for k, n, b in ex:
        print(f"   {k} ({site.get(k)}) groups {n}: blank rows {b}")


def tables(min_rows=4, min_cols=3):
    K = hyp.okr()
    out = []
    for k, cs in K.items():
        by = defaultdict(list)
        for g in hyp.groups(cs):
            by[len(g)].append(g)
        for sz, gs in by.items():
            if sz >= min_cols and len(gs) >= min_rows:
                out.append((k, gs))
    return out


def h123():
    """Red cords (colour code with R: RD, FR, …) hold smaller numbers than the other cords of their khipu (markers)."""
    K = hyp.okr()
    data = [[("red" if "R" in r["colour"][0] and r["colour"][0] not in ("BR",) else "other", r["value"]) for r in cs if r["value"] > 0] for cs in K.values()]
    n, real, m, p_hi, p_lo = within_compare(data, "red", "other")
    print(f"H123: khipus {n}; red median larger in {real}; shuffled {m:.1f}; p(≥) {p_hi:.4f}, p(≤) {p_lo:.4f}")


def h126():
    """Fixed rates: two columns of a table stand in an exact integer ratio k (2–12) in ≥ 3 rows (values ≥ 2), against the
    second column's rows shuffled."""
    T = tables()
    def cnt(shuffle):
        n, ex = 0, []
        for k, gs in T:
            rows = [[r["value"] for r in g] for g in gs]
            cols = [list(c) for c in zip(*rows)]
            for i in range(len(cols)):
                for j in range(len(cols)):
                    if i == j:
                        continue
                    a, b = cols[i], cols[j][:]
                    if shuffle:
                        R.shuffle(b)
                    best = Counter(y // x for x, y in zip(a, b) if x >= 2 and y > x and y % x == 0 and 2 <= y // x <= 12)
                    if best and best.most_common(1)[0][1] >= 3:
                        n += 1; ex.append((k, i + 1, j + 1, best.most_common(1)[0]))
        return n, ex
    real, ex = cnt(False)
    sims = [cnt(True)[0] for _ in range(20)]
    print(f"H126: column pairs with ≥ 3 rows in an exact ratio: {real}; shuffled mean {statistics.mean(sims):.1f}, max {max(sims)}")
    for e in ex[:20]:
        print("   ", e)


def h127():
    """Miscounted long knots: in groups where one cord equals the sum of the others ± 1 (a near-miss total), the parts carry
    units digits 7–9 more often than in groups where the total is exact."""
    K = hyp.okr()
    st = {"exact": [0, 0, 0], "off1": [0, 0, 0]}
    for cs in K.values():
        for g in hyp.groups(cs):
            v = [r["value"] for r in g]
            if len(v) < 4:
                continue
            S = sum(v)
            for i, t in enumerate(v):
                if t < 20:
                    continue
                rest = v[:i] + v[i + 1:]
                d = t - (S - t)
                kind = "exact" if d == 0 else "off1" if abs(d) == 1 else None
                if kind:
                    u = [x % 10 for x in rest if x % 10]
                    st[kind][0] += 1; st[kind][1] += sum(1 for x in u if x >= 7); st[kind][2] += len(u)
                    break
    for k, (n, hi, tot) in st.items():
        print(f"H127: {k} totals {n}; parts with units 7–9 {hi} of {tot} non-zero units ({hi / max(1, tot):.3f})")


def h132():
    """Long-knot-only khipus copy each other: per-cord turn sequences of UR050–UR055 and the other long-knot khipus align
    (best Spearman over shifts, overlap ≥ 15) better than with one sequence shuffled."""
    names = ["UR050", "UR051", "UR052", "UR054", "UR055", "UR193", "UR120", "AS090/N2"]
    S = {k: [statistics.mean(x) for x in lk_rows(k)] for k in names}
    S = {k: v for k, v in S.items() if len(v) >= 12}
    def best(a, b):
        out = -1
        for sh in range(-len(b) + 15, len(a) - 15 + 1):
            pa = [(a[i], b[i - sh]) for i in range(len(a)) if 0 <= i - sh < len(b)]
            if len(pa) >= 15:
                out = max(out, spearman([x for x, _ in pa], [y for _, y in pa]))
        return out
    ks = sorted(S)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a, b = S[ks[i]], S[ks[j]]
            r = best(a, b)
            sims = []
            for _ in range(100):
                q = b[:]
                R.shuffle(q)
                sims.append(best(a, q))
            print(f"H132: {ks[i]} ~ {ks[j]}: best ρ {r:.2f}; shuffled max-over-shifts mean {statistics.mean(sims):.2f}, "
                  f"p {(1 + sum(x >= r for x in sims)) / 101:.3f}")


def h134():
    """Headers: the first group of a khipu (its value sequence, ≥ 2 cords, not all zero) recurs as the first group of another
    khipu of the same site more often than groups at other positions recur at the same position."""
    K = hyp.okr()
    _, site, dup = hyp.atlas()
    G = {k: [tuple(r["value"] for r in g) for g in hyp.groups(cs)] for k, cs in K.items() if site.get(k)}
    def cnt(pos):
        seen = defaultdict(set)
        for k, gs in G.items():
            i = pos if pos >= 0 else len(gs) + pos
            if 0 <= i < len(gs) and len(gs) > 2 and len(gs[i]) >= 2 and sum(gs[i]) > 0:
                seen[(site[k], gs[i])].add(k)
        return sum(1 for v in seen.values() if len(v) >= 2 and not all((a, b) in dup for a in v for b in v if a != b))
    print("H134: shared sequences by group position (same site): " + ", ".join(f"{p_}:{cnt(p_)}" for p_ in (0, 1, 2, 3, -1)))


def h137():
    """Subsidiaries hang on larger numbers: within khipus, pendants with subsidiaries hold larger values than those without."""
    K = hyp.okr()
    data = [[("sub" if r["subs"] else "none", r["value"]) for r in cs if r["value"] > 0] for cs in K.values()]
    n, real, m, p_hi, p_lo = within_compare(data, "sub", "none")
    print(f"H137: khipus {n}; median with subsidiaries larger in {real}; shuffled {m:.1f}; p(≥) {p_hi:.4f}, p(≤) {p_lo:.4f}")


def h138():
    """Subsidiary colour: subsidiaries share their pendant's colour more often than a random pendant of the same khipu does;
    and their colours are less varied (one attribute colour per khipu)."""
    K = hyp.okr()
    same = rnd = n = 0
    ent_s, ent_p = [], []
    def H_(xs):
        c = Counter(xs)
        t = sum(c.values())
        return -sum(v / t * math.log2(v / t) for v in c.values())
    for cs in K.values():
        cols = [r["colour"][0] for r in cs if r["colour"][0]]
        subs = [(r["colour"][0], s_["colour"][0]) for r in cs for s_ in r["subs"] if r["colour"][0] and s_["colour"][0]]
        if len(subs) < 5:
            continue
        for pc, sc in subs:
            n += 1; same += pc == sc; rnd += R.choice(cols) == sc
        sc_ = [sc for _, sc in subs]
        ent_s.append(H_(sc_))
        ent_p.append(statistics.mean(H_(R.sample(cols, len(sc_))) for _ in range(50)) if len(cols) >= len(sc_) else H_(cols))
    print(f"H138: subsidiaries {n}; same colour as own pendant {same / n:.3f}; as a random pendant {rnd / n:.3f}")
    print(f"   colour entropy: subsidiaries {statistics.mean(ent_s):.2f} bits; random pendants of the same number {statistics.mean(ent_p):.2f}")


def h139():
    """Proportional subsidiaries: within khipus, the subsidiary sum grows with the pendant value (Spearman over pendants
    with both ≥ 1), beyond subsidiary sums shuffled among the same pendants."""
    K = hyp.okr()
    rs, ss = [], []
    for cs in K.values():
        xs = [(r["value"], sum(s_["value"] for s_ in r["subs"])) for r in cs if r["value"] >= 1 and r["subs"]]
        xs = [x for x in xs if x[1] >= 1]
        if len(xs) < 8:
            continue
        a, b = [x for x, _ in xs], [y for _, y in xs]
        rs.append(spearman(a, b))
        q = b[:]
        sims = []
        for _ in range(50):
            R.shuffle(q)
            sims.append(spearman(a, q))
        ss.append(statistics.mean(sims))
    print(f"H139: khipus {len(rs)}; mean Spearman (pendant, subsidiary sum) {statistics.mean(rs):.3f}; shuffled {statistics.mean(ss):.3f}; "
          f"positive in {sum(r > 0 for r in rs)}, negative in {sum(r < 0 for r in rs)}")


def h140():
    """Simple fractions in subsidiaries: the subsidiary sum is exactly 1/q of the pendant (q = 2…10) more often than 1/q of
    the pendant ± 1 (same q), pendants ≥ 10."""
    K = hyp.okr()
    ex, near = Counter(), Counter()
    for cs in K.values():
        for r in cs:
            s_ = sum(x["value"] for x in r["subs"])
            p_ = r["value"]
            if p_ < 10 or s_ < 1:
                continue
            for q in range(2, 11):
                ex[q] += s_ * q == p_
                near[q] += (s_ * q == p_ + 1) + (s_ * q == p_ - 1)
    print("H140: q: exact vs (±1)/2 — " + ", ".join(f"1/{q}: {ex[q]} vs {near[q] / 2:.1f}" for q in range(2, 11)))


def h141():
    """Counting, not arithmetic, avoids 9: cords that are sums of a group elsewhere in the khipu (computed totals) show no
    deficit of units digits 7–9, while the summed parts (counts) do. Values ≥ 20 with non-zero units."""
    K = hyp.okr()
    tot, parts = Counter(), Counter()
    for cs in K.values():
        gs = hyp.groups(cs)
        sums = {}
        for gi, g in enumerate(gs):
            v = [r["value"] for r in g]
            if len(v) >= 2 and sum(1 for x in v if x) >= 2:
                sums.setdefault(sum(v), []).append(gi)
        gid = {id(r): gi for gi, g in enumerate(gs) for r in g}
        used = set()
        for r in cs:
            v = r["value"]
            if v >= 20 and v % 10 and v in sums and any(gi != gid[id(r)] for gi in sums[v]):
                tot[v % 10] += 1
                used |= {gi for gi in sums[v] if gi != gid[id(r)]}
        for gi in used:
            for r in gs[gi]:
                if r["value"] >= 1 and r["value"] % 10:
                    parts[r["value"] % 10] += 1
    for name, c in (("computed totals", tot), ("their parts", parts)):
        n = sum(c.values())
        base = sum(c[d] for d in range(1, 7)) / 6
        print(f"H141: {name}: n={n}; " + " ".join(f"{d}:{c[d] / base:.2f}" for d in range(1, 10)))


def h144():
    """Hidden bases: some khipus never use a digit above k < 9 in any place although they have many digits (a base-(k+1)
    or quinary habit). Expected count of such khipus from the corpus digit distribution (digits 1–9, all places)."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    allc = Counter()
    per = {}
    for k, cs in K.items():
        c = Counter()
        for r in cs:
            for cl in r["clusters"]:
                if 1 <= cl["value"] // (10 ** int(math.log10(cl["value"]))) <= 9 if cl["value"] else False:
                    d = cl["value"] // (10 ** int(math.log10(cl["value"])))
                    c[d] += 1
        per[k] = c
        allc += c
    tot = sum(allc.values())
    pk = {d: allc[d] / tot for d in range(1, 10)}
    for kmax in (5, 6, 7):
        q = sum(pk[d] for d in range(1, kmax + 1))
        cand = [(k, sum(c.values())) for k, c in per.items() if sum(c.values()) >= 40 and max(c) <= kmax]
        exp = sum(q ** sum(c.values()) for c in per.values() if sum(c.values()) >= 40)
        print(f"H144: khipus with ≥ 40 digits, none above {kmax}: {len(cand)} (expected {exp:.2f}) " + ", ".join(f"{k} ({site.get(k)}, {n})" for k, n in cand))


def h145():
    """A second long-knot style: khipus whose long knots keep nearly the same number of turns (sd < 1.3) form a distinct
    group, not the tail of a continuum; listed with site and share of long knots among all clusters."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    rows = []
    for k, cs in K.items():
        t = [kk[3] for r in cs for cl in r["clusters"] for kk in cl["knots"] if kk[0] == "L" and kk[3] >= 2]
        ncl = sum(1 for r in cs for cl in r["clusters"])
        if len(t) >= 40:
            rows.append((statistics.pstdev(t), statistics.mean(t), len(t), len(t) / max(1, ncl), k))
    h = Counter(round(sd * 4) / 4 for sd, *_ in rows)
    print("H145: sd of long-knot turns per khipu (≥ 40 long knots), histogram: " + ", ".join(f"{x}:{h[x]}" for x in sorted(h)))
    for sd, m, n, sh, k in sorted(rows)[:20]:
        print(f"   {k:11} {site.get(k)} sd {sd:.2f} mean {m:.1f} long knots {n} ({sh:.0%} of clusters)")


GENRE = ["UR039", "UR112", "UR144", "UR050", "UR110", "UR054", "UR055", "UR052", "UR051", "AS090/N2", "UR193"]


def h146():
    """In the long-knot genre, turns depend on cord colour or on the cluster's position on the cord (a code), more than with
    colours / positions shuffled within the khipu."""
    K = hyp.okr()
    for k in GENRE:
        xs = []
        for r in K[k]:
            for i, cl in enumerate(r["clusters"]):
                if cl["type"] == "L" and len(cl["knots"]) == 1 and r["colour"][0]:
                    xs.append((r["colour"][0], i, cl["knots"][0][3]))
        if len(xs) < 30:
            continue
        def r2(pairs):
            ys = [y for _, y in pairs]
            m = statistics.mean(ys)
            tot = sum((y - m) ** 2 for y in ys) or 1
            by = defaultdict(list)
            for c, y in pairs:
                by[c].append(y)
            return sum(len(v) * (statistics.mean(v) - m) ** 2 for v in by.values()) / tot
        out = []
        for name, idx in (("colour", 0), ("position", 1)):
            pairs = [(x[idx], x[2]) for x in xs]
            if len({p_ for p_, _ in pairs}) < 2:
                out.append(f"{name} —"); continue
            real = r2(pairs)
            labs = [p_ for p_, _ in pairs]
            ys = [y for _, y in pairs]
            sims = []
            for _ in range(300):
                R.shuffle(labs)
                sims.append(r2(list(zip(labs, ys))))
            out.append(f"{name} R² {real:.3f} vs {statistics.mean(sims):.3f} (p {(1 + sum(x >= real for x in sims)) / 301:.3f})")
        print(f"H146: {k:9} clusters {len(xs)}: " + "; ".join(out))


def h147():
    """Space filling: in the long-knot genre, cords with more knots have fewer turns per knot (the knots share a fixed length
    of cord), and the lowest knot is shorter than the others."""
    K = hyp.okr()
    for k in GENRE:
        rows = lk_rows(k)
        if len(rows) < 20:
            continue
        n = [len(x) for x in rows]
        m = [statistics.mean(x) for x in rows]
        r = spearman(n, m) if len(set(n)) > 1 else float("nan")
        last = [x[-1] - statistics.mean(x[:-1]) for x in rows if len(x) >= 2]
        tot = [sum(x) for x in rows]
        print(f"H147: {k:9} cords {len(rows)}: Spearman (knots on cord, turns per knot) {r:.2f}; lowest knot minus the others "
              f"{statistics.mean(last):+.2f} turns (lower in {sum(d < 0 for d in last)}, higher in {sum(d > 0 for d in last)}); "
              f"Spearman (knots, total turns) {spearman(n, tot) if len(set(n)) > 1 else float('nan'):.2f}")


def h148():
    """Crowding or counting? Units digits by number of places (long-knot genre excluded): if crowded cords squeezed the units
    knot, the 7–9 deficit would grow with the number of places; if it comes from counting small amounts, it fades in large
    (aggregated) values."""
    K = hyp.okr()
    by = defaultdict(Counter)
    for k, cs in K.items():
        if k in GENRE:
            continue
        for r in cs:
            v = r["value"]
            if v >= 10 and v % 10:
                by[len(str(v))][v % 10] += 1
    for n, c in sorted(by.items()):
        t = sum(c.values())
        if t < 50:
            continue
        base = sum(c[d] for d in range(1, 7)) / 6
        print(f"H148: {n} places, n={t}: " + " ".join(f"{d}:{c[d] / base:.2f}" for d in range(1, 10)))


def h149():
    """Just above, not just below: values one or two above a round number are commoner than one or two below it, although the
    value distribution falls (which favours the values below)."""
    V = all_values()
    for d in list(range(20, 100, 10)) + [100, 200, 300, 400, 500, 1000]:
        b = V.get(d - 2, 0) + V.get(d - 1, 0)
        a = V.get(d + 1, 0) + V.get(d + 2, 0)
        print(f"H149: {d}: {d - 2}–{d - 1} {b}, {d}: {V.get(d, 0)}, {d + 1}–{d + 2} {a}")


def h150():
    """H149 by site: values ending in 8–9 against values ending in 1–2 (values 20–999, round tens excluded), per site;
    the falling distribution alone favours 8–9 of the decade below only slightly at these sizes."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    by = defaultdict(lambda: [0, 0])
    for k, cs in K.items():
        for r in cs:
            v = r["value"]
            if 20 <= v <= 999:
                if v % 10 in (8, 9):
                    by[site.get(k) or "?"][0] += 1; by["ALL"][0] += 1
                elif v % 10 in (1, 2):
                    by[site.get(k) or "?"][1] += 1; by["ALL"][1] += 1
    for s_, (b, a) in sorted(by.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:16]:
        print(f"H150: {s_:12} ending 8–9: {b:5}; ending 1–2: {a:5}; ratio {b / max(1, a):.2f}")


def h157():
    """The long-knot genre is the canuto khipus: khipus whose pendants are gathered in wrapped bundles (cord.CANUTO_ID) are
    the ones with nearly constant long knots. Rank of the canuto khipus among all khipus with ≥ 40 long knots by turn sd."""
    import sqlite3
    c = sqlite3.connect(hyp.DB)
    inv = {k: (n or "").strip() for k, n in c.execute("select KHIPU_ID, INVESTIGATOR_NUM from khipu_main")}
    can, tot = Counter(), Counter()
    for kid, cid in c.execute("select KHIPU_ID, CANUTO_ID from cord where CORD_LEVEL = 1"):
        tot[inv[kid]] += 1
        can[inv[kid]] += cid not in (None, "", 0, "0")
    K = hyp.okr()
    rows = []
    for k, cs in K.items():
        t = [kk[3] for r in cs for cl in r["clusters"] for kk in cl["knots"] if kk[0] == "L" and kk[3] >= 2]
        if len(t) >= 40:
            rows.append((statistics.pstdev(t), k, can[k] / max(1, tot[k])))
    rows.sort()
    ranks = [i + 1 for i, (_, k, f) in enumerate(rows) if f > 0]
    n, m = len(rows), len(ranks)
    # probability that m random khipus all fall within the top max(ranks)
    top = max(ranks)
    p_ = math.comb(top, m) / math.comb(n, m)
    print(f"H157: khipus with canutos {sum(1 for k in tot if can[k])}; among {n} khipus with ≥ 40 long knots their ranks by turn sd: {ranks}; "
          f"P(all {m} within the lowest {top}) = {p_:.2e}")
    print("   " + ", ".join(f"{k} sd {sd:.2f} canuto {f:.0%}" for sd, k, f in rows[:14]))


def h158():
    """Canuto bundles are units: cords of one bundle share a turn level (R² of turns on bundle, against bundles shuffled with
    sizes kept), and bundle sizes are fixed within a khipu."""
    import sqlite3
    c = sqlite3.connect(hyp.DB)
    inv = {k: (n or "").strip() for k, n in c.execute("select KHIPU_ID, INVESTIGATOR_NUM from khipu_main")}
    bun = {cid: can for cid, can in c.execute("select CORD_ID, CANUTO_ID from cord where CORD_LEVEL = 1") if can not in (None, "", 0, "0")}
    K = hyp.okr()
    for k in ("UR039", "UR050", "UR052", "UR054", "UR055", "UR110", "UR112", "UR144"):
        xs = []
        for r in K[k]:
            t = [kk[3] for cl in r["clusters"] for kk in cl["knots"] if kk[0] == "L"]
            if t and r["id"] in bun:
                xs.append((bun[r["id"]], statistics.mean(t)))
        if len(xs) < 20:
            continue
        sizes = Counter(Counter(b for b, _ in xs).values())
        def r2(pairs):
            ys = [y for _, y in pairs]
            m = statistics.mean(ys)
            tot = sum((y - m) ** 2 for y in ys) or 1
            by = defaultdict(list)
            for b, y in pairs:
                by[b].append(y)
            return sum(len(v) * (statistics.mean(v) - m) ** 2 for v in by.values()) / tot
        real = r2(xs)
        labs = [b for b, _ in xs]
        ys = [y for _, y in xs]
        sims = []
        for _ in range(300):
            R.shuffle(labs)
            sims.append(r2(list(zip(labs, ys))))
        print(f"H158: {k}: cords {len(xs)}, bundles {len(set(labs))}, bundle sizes {dict(sorted(sizes.items()))}; R² on bundle {real:.3f} "
              f"vs {statistics.mean(sims):.3f} (p {(1 + sum(x >= real for x in sims)) / 301:.3f})")


def h160():
    """Canuto bundles as multiple copies: cords of one bundle carry the same knot sequence (number of clusters and turns per
    cluster) more often than random pairs of cords of the same khipu; also how close the sequences are (mean |Δ turns|)."""
    import sqlite3
    c = sqlite3.connect(hyp.DB)
    bun = {cid: can for cid, can in c.execute("select CORD_ID, CANUTO_ID from cord where CORD_LEVEL = 1") if can not in (None, "", 0, "0")}
    K = hyp.okr()
    for k in ("UR039", "UR050", "UR052", "UR054", "UR055", "UR110", "UR112", "UR144"):
        seqs = defaultdict(list)
        allc = []
        for r in K[k]:
            if r["id"] in bun:
                sq = tuple(sum(kk[3] if kk[0] == "L" else 1 for kk in cl["knots"]) for cl in r["clusters"])
                seqs[bun[r["id"]]].append(sq)
                allc.append(sq)
        def stats(pairs):
            same = sum(a == b for a, b in pairs)
            close = [statistics.mean(abs(x - y) for x, y in zip(a, b)) for a, b in pairs if len(a) == len(b) and a]
            samelen = sum(len(a) == len(b) for a, b in pairs)
            return same / len(pairs), samelen / len(pairs), (statistics.mean(close) if close else float("nan"))
        within = [(a, b) for v in seqs.values() for i, a in enumerate(v) for b in v[i + 1:]]
        rnd = [tuple(R.sample(allc, 2)) for _ in range(5000)]
        w, r_ = stats(within), stats(rnd)
        print(f"H160: {k}: pairs in bundles {len(within)}; identical {w[0]:.3f} vs random {r_[0]:.3f}; same number of clusters {w[1]:.2f} vs {r_[1]:.2f}; "
              f"mean |Δ turns| (same length) {w[2]:.2f} vs {r_[2]:.2f}")


def h168():
    """Totals overshoot: where no cord equals a group's sum exactly but one equals the sum ± d (d = 1…5, cords outside the
    group, sums ≥ 50 and ≥ 3 non-zero parts), the near total is above the sum more often than below. The falling value
    distribution alone favours 'below'."""
    K = hyp.okr()
    up, dn = Counter(), Counter()
    for cs in K.values():
        gs = hyp.groups(cs)
        where = defaultdict(set)
        for gi, g in enumerate(gs):
            for r in g:
                where[r["value"]].add(gi)
        for gi, g in enumerate(gs):
            v = [r["value"] for r in g]
            S = sum(v)
            if S < 50 or sum(1 for x in v if x) < 3:
                continue
            has = lambda x: bool(where.get(x, set()) - {gi})
            if has(S):
                continue
            for d in range(1, 6):
                up[d] += has(S + d); dn[d] += has(S - d)
    print("H168: near totals above/below the group sum: " + ", ".join(f"±{d}: {up[d]}/{dn[d]}" for d in range(1, 6)))


def h169():
    """Wild: the khipu is read from the far end — the first cords (by OKR order) are the summaries. Within khipus with sum
    relations (a cord equal to the sum of another group), the total cords stand before their groups more often than after."""
    K = hyp.okr()
    before = after = 0
    for cs in K.values():
        gs = hyp.groups(cs)
        gid = {id(r): gi for gi, g in enumerate(gs) for r in g}
        sums = defaultdict(list)
        for gi, g in enumerate(gs):
            v = [r["value"] for r in g]
            if len(v) >= 3 and sum(1 for x in v if x) >= 3 and sum(v) >= 20 and sum(v) % 10:
                sums[sum(v)].append(gi)
        for r in cs:
            for gi in sums.get(r["value"], []):
                if gi != gid[id(r)]:
                    if gid[id(r)] < gi:
                        before += 1
                    else:
                        after += 1
    print(f"H169: total cords standing before the group they sum: {before}; after: {after}")


def h177():
    """Cords cut one after another: intact cord length (knot allowance added back) drifts along the khipu, and neighbouring
    cords are closer in length than distant ones (cut in sequence from one batch)."""
    K = hyp.okr()
    rs, nb_real, nb_sim, n = [], 0, 0, 0
    for cs in K.values():
        L = []
        for r in cs:
            if r["length"] > 0 and r["term"] != "B":
                turns = sum(kk[3] if kk[0] == "L" else 0 for cl in r["clusters"] for kk in cl["knots"])
                single = sum(1 for cl in r["clusters"] for kk in cl["knots"] if kk[0] != "L")
                L.append(r["length"] + 0.54 * single + 0.64 * turns)
        if len(L) < 20 or statistics.pstdev(L) == 0:
            continue
        n += 1
        rs.append(spearman(list(range(len(L))), L))
        d = statistics.mean(abs(a - b) for a, b in zip(L, L[1:]))
        q = L[:]
        sims = []
        for _ in range(100):
            R.shuffle(q)
            sims.append(statistics.mean(abs(a - b) for a, b in zip(q, q[1:])))
        nb_real += d < statistics.quantiles(sims, n=20)[0]
    print(f"H177: khipus {n}; Spearman (order, length) mean {statistics.mean(rs):.3f}, positive {sum(r > 0 for r in rs)}, negative {sum(r < 0 for r in rs)}; "
          f"neighbours closer than the 5% shuffle quantile in {nb_real} (expected {0.05 * n:.1f})")


def h178():
    """Planned cutting: groups that were going to carry more knots got longer cords. Between groups of one khipu, measured
    length falls with knot load less steeply than within groups (where length was fixed and knots only use it up)."""
    K = hyp.okr()
    def slope(xs, ys):
        mx, my = statistics.mean(xs), statistics.mean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else None
    within, between = [], []
    for cs in K.values():
        gx, gy = [], []
        for g in hyp.groups(cs):
            xs, ys = [], []
            for r in g:
                if r["length"] > 0 and r["term"] != "B":
                    load = sum(kk[3] * 0.64 / 0.54 if kk[0] == "L" else 1 for cl in r["clusters"] for kk in cl["knots"])
                    xs.append(load); ys.append(r["length"])
            if len(xs) >= 4:
                s_ = slope(xs, ys)
                if s_ is not None:
                    within.append(s_)
                gx.append(statistics.mean(xs)); gy.append(statistics.mean(ys))
        if len(gx) >= 5:
            s_ = slope(gx, gy)
            if s_ is not None:
                between.append(s_)
    print(f"H178: within-group slope of length on knot load (cm per single-knot equivalent): median {statistics.median(within):.2f} "
          f"({len(within)} groups); between groups of a khipu: median {statistics.median(between):.2f} ({len(between)} khipus)")


def h181():
    """Copies repeat cord lengths: matched equal cords (both intact) of copy pairs have correlated lengths beyond a
    permutation of lengths among the matched cords; group-level batches are kept by using circular shifts as well."""
    for a, b, pr in copy_pairs():
        xs = [(x["length"], y["length"]) for x, y in pr if x["length"] > 0 and y["length"] > 0 and x["term"] != "B" and y["term"] != "B"]
        if len(xs) < 10:
            continue
        A, B = [x for x, _ in xs], [y for _, y in xs]
        r = spearman(A, B)
        sims = [spearman(A, B[k:] + B[:k]) for k in range(3, len(B) - 2)]
        print(f"H181: {a}~{b}: cords {len(xs)}; length Spearman {r:.2f}; circular shifts mean {statistics.mean(sims):.2f}, "
              f"p {(1 + sum(x >= r for x in sims)) / (1 + len(sims)):.3f}")


def prep_len(r):
    """Cord length with the knot allowance added back (0.54 cm per single or figure-eight knot, 0.64 cm per long-knot turn)."""
    turns = sum(kk[3] for cl in r["clusters"] for kk in cl["knots"] if kk[0] == "L")
    single = sum(1 for cl in r["clusters"] for kk in cl["knots"] if kk[0] != "L")
    return r["length"] + 0.54 * single + 0.64 * turns


def h181b():
    """H181 with knot use removed (prepared length), so equal knots on matched cords cannot make the lengths agree."""
    tot = []
    for a, b, pr in copy_pairs():
        xs = [(prep_len(x), prep_len(y)) for x, y in pr if x["length"] > 0 and y["length"] > 0 and x["term"] != "B" and y["term"] != "B"]
        if len(xs) < 10:
            continue
        A, B = [x for x, _ in xs], [y for _, y in xs]
        r = spearman(A, B)
        sims = [spearman(A, B[k:] + B[:k]) for k in range(3, len(B) - 2)]
        p_ = (1 + sum(x >= r for x in sims)) / (1 + len(sims))
        tot.append(p_)
        print(f"H181b: {a}~{b}: cords {len(xs)}; prepared-length Spearman {r:.2f}; circular shifts mean {statistics.mean(sims):.2f}, p {p_:.3f}")


def h183():
    """Plans and counts: khipus split into 'planned' ones (nearly all values ≥ 10 round) and 'counted' ones; the per-khipu
    share of round values is bimodal, beyond a binomial spread around the corpus share."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    rows = []
    for k, cs in K.items():
        v = [r["value"] for r in cs if r["value"] >= 10]
        if len(v) >= 15:
            rows.append((sum(1 for x in v if x % 10 == 0) / len(v), len(v), k))
    p_ = sum(s_ * n for s_, n, _ in rows) / sum(n for _, n, _ in rows)
    h = Counter(min(9, int(s_ * 10)) for s_, _, _ in rows)
    sim = Counter()
    for _ in range(20):
        for _, n, _ in rows:
            x = sum(R.random() < p_ for _ in range(n)) / n
            sim[min(9, int(x * 10))] += 1 / 20
    print(f"H183: khipus {len(rows)}; corpus share of round values {p_:.2f}")
    print("   observed by tenths: " + " ".join(f"{i / 10:.1f}:{h[i]}" for i in range(10)))
    print("   binomial expectation: " + " ".join(f"{i / 10:.1f}:{sim[i]:.0f}" for i in range(10)))
    print("   ≥ 0.9 round: " + ", ".join(f"{k} ({site.get(k)}, {n})" for s_, n, k in rows if s_ >= 0.9))


def h185():
    """Plan and fact: a rounded khipu (≥ 50% round values) repeats, in order, another khipu's non-round values rounded to the
    nearest ten. Aligned matches (round value on A = rounded non-round value on B) against B's cords shuffled."""
    sys.path.insert(0, str(hyp.ROOT / "khipu"))
    import copies_losses
    K = {k: [r["value"] for r in cs] for k, cs in hyp.okr().items()}
    _, site, dup = hyp.atlas()
    rnd = {k for k, v in K.items() if len([x for x in v if x >= 10]) >= 10 and sum(1 for x in v if x >= 10 and x % 10 == 0) / len([x for x in v if x >= 10]) >= 0.5}
    def r10(x):
        return int(round(x / 10.0)) * 10 if x % 10 and x >= 10 else -1 - x
    def score(A, B):
        Y = [r10(b) for b in B]
        pr = copies_losses.align(A, Y)
        return sum(1 for i, j in pr if A[i] == Y[j] and A[i] >= 20)
    out = []
    for a in rnd:
        A = K[a]
        setA = {x for x in A if x >= 20 and x % 10 == 0}
        for b, B in K.items():
            if b == a or (a, b) in dup:
                continue
            if len(setA & {r10(x) for x in B}) < 4:
                continue
            sc = score(A, B)
            if sc >= 4:
                sims = []
                for _ in range(20):
                    q = B[:]
                    R.shuffle(q)
                    sims.append(score(A, q))
                out.append((sc, max(sims), a, b))
    out.sort(reverse=True)
    print(f"H185: rounded khipus {len(rnd)}; pairs with ≥ 4 aligned rounded matches {len(out)}; above all 20 shuffles: {sum(1 for sc, mx, _, _ in out if sc > mx)}")
    for sc, mx, a, b in out[:15]:
        print(f"   {a} ({site.get(a)}) ← {b} ({site.get(b)}): {sc} vs shuffled max {mx}")


def h187():
    """Odd colour = special entry: within groups (≥ 4 cords with a majority colour), a cord of another colour holds a larger
    number than its group-mates more often than chance (labels shuffled within khipu)."""
    K = hyp.okr()
    data = []
    pos = Counter()
    for cs in K.values():
        xs = []
        for g in hyp.groups(cs):
            if len(g) < 4:
                continue
            c = Counter(r["colour"] for r in g).most_common(1)[0]
            if c[1] < len(g) / 2 or c[1] == len(g):
                continue
            for i, r in enumerate(g):
                if r["value"] > 0:
                    lab = "odd" if r["colour"] != c[0] else "major"
                    xs.append((lab, r["value"]))
                    if lab == "odd":
                        pos["first" if i == 0 else "last" if i == len(g) - 1 else "middle"] += 1
        data.append(xs)
    n, real, m, p_hi, p_lo = within_compare(data, "odd", "major")
    print(f"H187: khipus {n}; odd-coloured cords' median larger in {real}; shuffled {m:.1f}; p(≥) {p_hi:.4f}, p(≤) {p_lo:.4f}; "
          f"odd cords at first {pos['first']}, middle {pos['middle']}, last {pos['last']}")


def h189():
    """Moieties: groups come in pairs (1–2, 3–4, …) — totals within a pair are closer than across pair boundaries (2–3, 4–5),
    in khipus with ≥ 6 groups. Both phases tested (pairs starting at group 1 or at group 2)."""
    K = hyp.okr()
    res = Counter()
    for cs in K.values():
        t = [sum(r["value"] for r in g) for g in hyp.groups(cs)]
        if len(t) < 6 or sum(t) == 0:
            continue
        d = [abs(math.log1p(a) - math.log1p(b)) for a, b in zip(t, t[1:])]
        odd = statistics.mean(d[0::2])
        even = statistics.mean(d[1::2])
        res["n"] += 1
        res["pairs from 1 tighter"] += odd < even
        res["pairs from 2 tighter"] += even < odd
        sz = [len(g) for g in hyp.groups(cs)]
        res["same size within pair from 1"] += sum(a == b for a, b in zip(sz[0::2], sz[1::2]))
        res["same size across"] += sum(a == b for a, b in zip(sz[1::2], sz[2::2]))
    print("H189: " + "; ".join(f"{k} {v}" for k, v in res.items()))


def h195():
    """Ply direction as a sign: within khipus that mix S- and Z-plied pendants, the Z-plied cords (the minority) carry
    different numbers, or are zero more often."""
    K = hyp.okr()
    data = [[(r["twist"], r["value"]) for r in cs if r["value"] > 0 and r["twist"] in ("S", "Z")] for cs in K.values()]
    n, real, m, p_hi, p_lo = within_compare(data, "Z", "S")
    print(f"H195: khipus {n}; Z-plied median larger in {real}; shuffled {m:.1f}; p(≥) {p_hi:.4f}, p(≤) {p_lo:.4f}")
    zz = Counter()
    for cs in K.values():
        z = [r for r in cs if r["twist"] == "Z"]
        s_ = [r for r in cs if r["twist"] == "S"]
        if len(z) >= 3 and len(s_) >= 3:
            a = sum(1 for r in z if not r["clusters"]) / len(z)
            b = sum(1 for r in s_ if not r["clusters"]) / len(s_)
            zz["Z emptier" if a > b else "S emptier" if b > a else "equal"] += 1
    print("   empty cords: " + ", ".join(f"{k} {v}" for k, v in zz.items()))


def h196():
    """Copies were made from counts, not re-counted: the 'just above round' habit (8–9 endings rarer than 1–2) is as strong
    on the copy side as on the original side of copy pairs — compared on matched cords that differ between the two."""
    P = copy_pairs()
    sys.path.insert(0, str(hyp.ROOT / "khipu"))
    import copies_losses
    K = hyp.okr()
    D, _, _ = hyp.atlas()
    diff = []
    for e in D["edges"]:
        if e["type"] not in ("copy", "excerpt", "details", "fold"):
            continue
        a, b = e["from"], e["to"]
        if a not in K or b not in K:
            continue
        A, B = [r["value"] for r in K[a]], [r["value"] for r in K[b]]
        for i, j in copies_losses.align(A, B):
            if A[i] != B[j] and A[i] >= 10 and B[j] >= 10:
                diff.append((A[i], B[j]))
    end = lambda x: x % 10
    print(f"H196: differing matched values {len(diff)}; endings of side A: 8–9 {sum(end(a) in (8, 9) for a, _ in diff)}, 1–2 {sum(end(a) in (1, 2) for a, _ in diff)}, 0 {sum(end(a) == 0 for a, _ in diff)}; "
          f"side B: 8–9 {sum(end(b) in (8, 9) for _, b in diff)}, 1–2 {sum(end(b) in (1, 2) for _, b in diff)}, 0 {sum(end(b) == 0 for _, b in diff)}")
    rd = sum(1 for a, b in diff if (a % 10 == 0) != (b % 10 == 0) and abs(a - b) <= 5)
    print(f"   pairs where one side is the other rounded to a ten (|Δ| ≤ 5): {rd}")


def h197():
    """Ranked lists: within groups (≥ 5 non-zero cords) values are in descending (or ascending) order more often than with the
    cords shuffled; also the mean within-group Spearman between position and value."""
    K = hyp.okr()
    G = [[r["value"] for r in g if r["value"] > 0] for cs in K.values() for g in hyp.groups(cs)]
    G = [v for v in G if len(v) >= 5 and len(set(v)) >= 3]
    desc = lambda v: all(a >= b for a, b in zip(v, v[1:]))
    asc = lambda v: all(a <= b for a, b in zip(v, v[1:]))
    rd, ra = sum(desc(v) for v in G), sum(asc(v) for v in G)
    sd, sa = [], []
    for _ in range(200):
        q = [R.sample(v, len(v)) for v in G]
        sd.append(sum(desc(v) for v in q)); sa.append(sum(asc(v) for v in q))
    rho = [spearman(list(range(len(v))), v) for v in G]
    print(f"H197: groups {len(G)}; descending {rd} (shuffled {statistics.mean(sd):.1f}, max {max(sd)}); ascending {ra} "
          f"(shuffled {statistics.mean(sa):.1f}, max {max(sa)}); mean ρ(position, value) {statistics.mean(rho):.3f}; "
          f"ρ ≤ −0.5 {sum(r <= -0.5 for r in rho)}, ρ ≥ 0.5 {sum(r >= 0.5 for r in rho)}")


def h198():
    """Head cords: the first cord of a group (≥ 4 cords, ≥ 3 non-zero) is its largest more often than 1/n; compared with the
    last cord, and split into heads that are the sum of the rest and those that are not."""
    K = hyp.okr()
    first = last = exp = tot_heads = 0
    n = 0
    for cs in K.values():
        for g in hyp.groups(cs):
            v = [r["value"] for r in g]
            if len(v) < 4 or sum(1 for x in v if x) < 3:
                continue
            m = max(v)
            if v.count(m) > 1:
                continue
            n += 1
            exp += 1 / len(v)
            first += v[0] == m
            last += v[-1] == m
            tot_heads += v[0] == m and v[0] == sum(v[1:])
    print(f"H198: groups {n}; first cord largest {first}, last cord largest {last}, expected {exp:.0f}; heads equal to the sum of the rest {tot_heads}")


def h199():
    """The head is marked: the first cord of a group has a colour different from the rest of its group more often than the
    other positions do (each position compared with the colours of the remaining cords of its group)."""
    K = hyp.okr()
    by_pos = Counter()
    n_pos = Counter()
    big_odd = big_same = 0
    for cs in K.values():
        for g in hyp.groups(cs):
            if len(g) < 4:
                continue
            for i, r in enumerate(g):
                others = [x["colour"] for j, x in enumerate(g) if j != i]
                odd = r["colour"] not in others
                key = "first" if i == 0 else "last" if i == len(g) - 1 else "middle"
                by_pos[key] += odd
                n_pos[key] += 1
            v = [r["value"] for r in g]
            if v[0] == max(v) and v.count(max(v)) == 1:
                if g[0]["colour"] not in [x["colour"] for x in g[1:]]:
                    big_odd += 1
                else:
                    big_same += 1
    print("H199: colour unique within the group — " + ", ".join(f"{k} {by_pos[k] / n_pos[k]:.3f} ({n_pos[k]})" for k in ("first", "middle", "last")))
    print(f"   largest-first groups: head colour unique {big_odd}, shared {big_same}")


def h201():
    """Canuto khipus are made of camelid fibre or human hair, unlike the cotton corpus: fibre of pendants on the 8 canuto
    khipus against all others."""
    import sqlite3
    c = sqlite3.connect(hyp.DB)
    inv = {k: (n or "").strip() for k, n in c.execute("select KHIPU_ID, INVESTIGATOR_NUM from khipu_main")}
    can = {"UR039", "UR050", "UR052", "UR054", "UR055", "UR110", "UR112", "UR144"}
    a, b = Counter(), Counter()
    hair = Counter()
    for kid, fib in c.execute("select KHIPU_ID, FIBER from cord where CORD_LEVEL = 1"):
        f = (fib or "").strip()
        (a if inv[kid] in can else b)[f] += 1
        if f == "H":
            hair[inv[kid]] += 1
    ta, tb = sum(a.values()), sum(b.values())
    print("H201: canuto khipus — " + ", ".join(f"{k or '?'} {v / ta:.2f}" for k, v in a.most_common()))
    print("   all other khipus — " + ", ".join(f"{k or '?'} {v / tb:.3f}" for k, v in b.most_common(6)))
    print("   human-hair pendants by khipu: " + ", ".join(f"{k} {v}" for k, v in hair.most_common()))


def h202():
    """Fibre as a marker: in cotton khipus (≥ 90% of pendants cotton), the few non-cotton pendants (hair, wool, camelid) are
    knotless and stand first in their group more often than the cotton pendants of the same khipus."""
    import sqlite3
    c = sqlite3.connect(hyp.DB)
    fib = {cid: (f or "").strip() for cid, f in c.execute("select CORD_ID, FIBER from cord where CORD_LEVEL = 1")}
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    st = {"odd": [0, 0, 0], "cotton": [0, 0, 0]}
    ks = Counter()
    for k, cs in K.items():
        f = [fib.get(r["id"], "") for r in cs]
        cn = sum(1 for x in f if x == "CN")
        odd = [x for x in f if x and x != "CN"]
        if not cs or cn / len(cs) < 0.9 or not odd:
            continue
        for g in hyp.groups(cs):
            for i, r in enumerate(g):
                fr = fib.get(r["id"], "")
                if not fr:
                    continue
                key = "cotton" if fr == "CN" else "odd"
                st[key][0] += 1; st[key][1] += not r["clusters"]; st[key][2] += i == 0 and len(g) > 1
                if key == "odd":
                    ks[k] += 1
    for key, (n, z, f0) in st.items():
        print(f"H202: {key} pendants {n}: knotless {z / n:.3f}, first in group {f0 / n:.3f}")
    print("   khipus: " + ", ".join(f"{k} ({site.get(k)}) {v}" for k, v in ks.most_common(12)))


def h206():
    """Separators are totals: a single-cord group standing between two larger groups equals the sum of the group before, the
    group after, or both — against the same check with the sums shifted by ±1…±3."""
    K = hyp.okr()
    _, site, _ = hyp.atlas()
    def cnt(d):
        res = Counter()
        for cs in K.values():
            gs = hyp.groups(cs)
            for i in range(1, len(gs) - 1):
                if len(gs[i]) != 1 or len(gs[i - 1]) < 3 or len(gs[i + 1]) < 3:
                    continue
                x = gs[i][0]["value"]
                if x < 10:
                    continue
                pv, nx = sum(r["value"] for r in gs[i - 1]), sum(r["value"] for r in gs[i + 1])
                res["n"] += 1
                res["prev"] += x == pv + d
                res["next"] += x == nx + d
                res["both"] += x == pv + nx + d
        return res
    real = cnt(0)
    sims = [cnt(d) for d in (-3, -2, -1, 1, 2, 3)]
    print(f"H206: separators {real['n']}; = sum of group before {real['prev']} (shifted {statistics.mean(s_['prev'] for s_ in sims):.1f}), "
          f"after {real['next']} ({statistics.mean(s_['next'] for s_ in sims):.1f}), both {real['both']} ({statistics.mean(s_['both'] for s_ in sims):.1f})")


def h210():
    """Male–female pairs: within groups, cords at positions (1,2), (3,4), … are closer in value than pairs (2,3), (4,5), and
    than random pairs of the group (|log ratio|, values ≥ 1)."""
    K = hyp.okr()
    a, b, c = [], [], []
    for cs in K.values():
        for g in hyp.groups(cs):
            v = [r["value"] for r in g]
            if len(v) < 6 or min(v) < 1:
                continue
            L = [math.log(x) for x in v]
            a += [abs(L[i] - L[i + 1]) for i in range(0, len(L) - 1, 2)]
            b += [abs(L[i] - L[i + 1]) for i in range(1, len(L) - 1, 2)]
            for _ in range(len(L) // 2):
                x, y = R.sample(L, 2)
                c.append(abs(x - y))
    print(f"H210: |log ratio| pairs (1,2),(3,4)…: {statistics.mean(a):.3f} (n {len(a)}); (2,3),(4,5)…: {statistics.mean(b):.3f}; random pairs {statistics.mean(c):.3f}")


def h212():
    """H198 replicated on the KFG khipus that are not in OKR: the first cord of a group is its largest more often than 1/n."""
    G, O = kfg_groups(), hyp.okr()
    _, _, dup = hyp.atlas()
    new = [k for k in G if k not in O and not any((k, o) in dup for o in O)]
    first = last = exp = n = 0
    for k in new:
        for v in G[k]:
            if len(v) < 4 or sum(1 for x in v if x) < 3:
                continue
            m = max(v)
            if v.count(m) > 1:
                continue
            n += 1; exp += 1 / len(v); first += v[0] == m; last += v[-1] == m
    print(f"H212: KFG-only khipus {len(new)}; groups {n}; first largest {first}, last largest {last}, expected {exp:.0f}")


def h213():
    """Replication on KFG-only khipus (not in OKR): 8–9 vs 1–2 endings (H149/150), units digit 9 by places (H148), length of
    neighbours within vs across groups (H177, raw length), subsidiaries scaling with their pendant (H139)."""
    import csv
    O = hyp.okr()
    _, _, dup = hyp.atlas()
    rows = defaultdict(list)
    subs = defaultdict(int)
    for r in csv.DictReader(open(hyp.ROOT / "extracted/plus2026_cords.csv")):
        k = r["inv_num"]
        if k in O or any((k, o) in dup for o in O):
            continue
        if r["parent_id"]:
            subs[r["parent_id"]] += int(r["value"] or 0)
        else:
            rows[k].append((int(r["order"]), int(r["value"] or 0), r["group"], float(r["length"] or 0), r["termination"], r["cord_id"]))
    V = [v for cs in rows.values() for _, v, *_ in cs]
    b = sum(1 for v in V if 20 <= v <= 999 and v % 10 in (8, 9))
    a = sum(1 for v in V if 20 <= v <= 999 and v % 10 in (1, 2))
    print(f"H213: KFG-only khipus {len(rows)}; endings 8–9 {b}, 1–2 {a} (ratio {b / max(1, a):.2f})")
    for n in (2, 3, 4):
        c = Counter(v % 10 for v in V if len(str(v)) == n and v % 10)
        base = sum(c[d] for d in range(1, 7)) / 6 or 1
        print(f"   {n} places: 7 {c[7] / base:.2f}, 8 {c[8] / base:.2f}, 9 {c[9] / base:.2f} (n {sum(c.values())})")
    win, acr, rnd = [], [], []
    for cs in rows.values():
        cs.sort()
        L = [(g, l) for _, _, g, l, t, _ in cs if l > 0 and t != "B"]
        if len(L) < 20:
            continue
        m = statistics.median(l for _, l in L)
        for (g1, l1), (g2, l2) in zip(L, L[1:]):
            (win if g1 == g2 else acr).append(abs(l1 - l2) / m)
        for _ in range(len(L)):
            (x, y) = R.sample(L, 2)
            rnd.append(abs(x[1] - y[1]) / m)
    if win:
        print(f"   lengths: within-group neighbours {statistics.median(win):.3f}, across boundary {statistics.median(acr):.3f}, random {statistics.median(rnd):.3f}")
    rs = []
    for cs in rows.values():
        xs = [(v, subs[cid]) for _, v, _, _, _, cid in cs if v >= 1 and subs.get(cid, 0) >= 1]
        if len(xs) >= 8:
            rs.append(spearman([x for x, _ in xs], [y for _, y in xs]))
    if rs:
        print(f"   subsidiaries: khipus {len(rs)}, mean Spearman (pendant, subsidiary sum) {statistics.mean(rs):.3f}, positive {sum(r > 0 for r in rs)}")


def h214():
    """Replication on KFG-only khipus: light cords hold larger values than dark ones (H62); zero cords align across equal-size
    groups (H77); group sums are round hundreds above baseline (H79)."""
    import csv
    O = hyp.okr()
    _, _, dup = hyp.atlas()
    rows = defaultdict(list)
    for r in csv.DictReader(open(hyp.ROOT / "extracted/plus2026_cords.csv")):
        k = r["inv_num"]
        if r["parent_id"] or k in O or any((k, o) in dup for o in O):
            continue
        rows[k].append((int(r["order"]), int(r["value"] or 0), r["group"], (r["color"] or "").split(":")[0] if ":" not in (r["color"] or "")[:3] else "", r["color"]))
    dark, light = {"KB", "MB", "DB", "B"}, {"W", "AB", "YB"}
    data = [[("light" if c in light else "dark" if c in dark else "x", v) for _, v, _, c, full in sorted(cs) if v > 0 and "-" not in full and ":" not in full]
            for cs in rows.values()]
    n, real, m, p_hi, p_lo = within_compare(data, "light", "dark")
    print(f"H214: KFG-only: khipus with both {n}; light median larger in {real}; shuffled {m:.1f}; p(≥) {p_hi:.4f}")
    real_a, sims, nk = 0, [0] * 200, 0
    allT = []
    for cs in rows.values():
        cs.sort()
        G = defaultdict(list)
        order = []
        for _, v, g, _, _ in cs:
            if g not in G:
                order.append(g)
            G[g].append(v)
        gs = [G[g] for g in order]
        allT += [sum(g) for g in gs if len(g) >= 3 and sum(1 for x in g if x % 10) >= 2]
        by = defaultdict(list)
        for g in gs:
            by[len(g)].append([x == 0 for x in g])
        for sz, gg in by.items():
            if sz < 4 or len(gg) < 3:
                continue
            z = sum(map(sum, gg))
            if z < 3 or z == sz * len(gg):
                continue
            nk += 1
            agree = lambda q: sum(max(c, len(q) - c) for c in (sum(col) for col in zip(*q)))
            real_a += agree(gg)
            for i in range(200):
                sims[i] += agree([R.sample(g, len(g)) for g in gg])
    print(f"   zero-slot agreement: sets {nk}; {real_a} vs shuffled {statistics.mean(sims):.1f}, max {max(sims)}")
    f = lambda d: sum(1 for t in allT if t >= 100 and (t + d) % 100 == 0)
    print(f"   round-hundred group sums (≥ 2 non-round parts): {f(0)}; shifted " + ", ".join(str(f(d)) for d in (-5, -3, -1, 1, 3, 5)))


def h215():
    """The head cord is longer: within groups (≥ 4 intact cords), the first cord's prepared length (knot allowance added back)
    exceeds the group median more often than other positions'."""
    K = hyp.okr()
    st = Counter()
    for cs in K.values():
        for g in hyp.groups(cs):
            L = [prep_len(r) if r["length"] > 0 and r["term"] != "B" else None for r in g]
            ok = [x for x in L if x is not None]
            if len(g) < 4 or len(ok) < 4:
                continue
            md = statistics.median(ok)
            for i, x in enumerate(L):
                if x is None or x == md:
                    continue
                key = "first" if i == 0 else "last" if i == len(g) - 1 else "middle"
                st[key + " n"] += 1
                st[key + " longer"] += x > md
    print("H215: share longer than the group median — " + ", ".join(f"{k} {st[k + ' longer'] / st[k + ' n']:.3f} ({st[k + ' n']})" for k in ("first", "middle", "last")))


def h217():
    """The head is a share of the group: head × k equals the sum of the rest (k = 2…10, a tithe-like share) more often than
    head × k = sum ± 1; groups where the head is the largest cord."""
    K = hyp.okr()
    ex, near = Counter(), Counter()
    for cs in K.values():
        for g in hyp.groups(cs):
            v = [r["value"] for r in g]
            if len(v) < 4 or v[0] != max(v) or v[0] < 5:
                continue
            rest = sum(v[1:])
            for k in range(2, 11):
                ex[k] += v[0] * k == rest
                near[k] += (v[0] * k == rest + 1) + (v[0] * k == rest - 1)
    print("H217: k: exact vs (±1)/2 — " + ", ".join(f"{k}: {ex[k]} vs {near[k] / 2:.1f}" for k in range(2, 11)))


def h218():
    """Heads carry the row scale: across groups of one khipu, the head value tracks the sum of the rest of its group more
    closely than any other single position does (mean within-khipu Spearman, groups of equal size ≥ 4, ≥ 4 groups)."""
    K = hyp.okr()
    res = defaultdict(list)
    for cs in K.values():
        by = defaultdict(list)
        for g in hyp.groups(cs):
            by[len(g)].append([r["value"] for r in g])
        for sz, gs in by.items():
            if sz < 4 or len(gs) < 4:
                continue
            for pos in range(sz):
                a = [g[pos] for g in gs]
                b = [sum(g) - g[pos] for g in gs]
                if len(set(a)) > 1 and len(set(b)) > 1:
                    res["first" if pos == 0 else "last" if pos == sz - 1 else "middle"].append(spearman(a, b))
    print("H218: Spearman (cord at a position, rest of its group) across groups — " + ", ".join(f"{k} {statistics.mean(v):.3f} ({len(v)})" for k, v in res.items()))


def h230():
    """Colonial dozens: multiples of 12 (and of 8, the real's pieces) are over-represented among non-round values 24–9999
    against values shifted ±1…±3 (and ±12/±8, which keep divisibility patterns)."""
    vals = all_values()
    for m in (12, 8, 6):
        def frac(d):
            xs = [(v + d, c) for v, c in vals.items() if 24 <= v <= 9999 and v % 10]
            tot = sum(c for _, c in xs)
            return sum(c for v, c in xs if v % m == 0) / tot
        print(f"H230: multiples of {m}: {frac(0):.4f}; shifted ±1…±3: " + ", ".join(f"{frac(d):.4f}" for d in (-3, -2, -1, 1, 2, 3))
              + f"; ±{m}: {frac(-m):.4f}, {frac(m):.4f} (1/{m} = {1 / m:.4f})")


# ---- runner (keep last) ----
if __name__ == "__main__":
    for a in sys.argv[1:]:
        globals()[f"h{a}"]()
