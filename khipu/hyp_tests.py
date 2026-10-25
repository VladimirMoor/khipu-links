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


# ---- runner (keep last) ----
if __name__ == "__main__":
    for a in sys.argv[1:]:
        globals()[f"h{a}"]()
