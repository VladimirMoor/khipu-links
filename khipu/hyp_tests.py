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


# ---- runner (keep last) ----
if __name__ == "__main__":
    for a in sys.argv[1:]:
        globals()[f"h{a}"]()
