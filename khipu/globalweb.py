"""Все кипу сразу: нет ли между ними, кроме найденных связей, общей сети слабых связей?

Для каждой пары кипу (корпус KFG 2026, extracted/plus2026_cords.csv) — общие «редкие» числа: значения шнуров ≥ 100,
не кратные 10, и итоги групп (подвесные) с тем же условием. Счёт пары = общие значения шнуров + итог группы одного,
стоящий на шнуре другого (в обе стороны). Фон: все значения и итоги второго кипу сдвинуты на d = ±1…±10 — та же
структура, те же величины, но совпадения случайные. Второй фон — сдвиги на ±10, ±20, … ±100: последняя цифра та же
(в записях есть любимые последние цифры, и сдвиг на 1–9 их ломает, занижая фон).

Вывод (extracted/globalweb.txt):
1. общий счёт по всем парам против фона — отдельно для пар внутри одного места находки, между разными местами,
   и с кипу без места; без пар известных связей и повторных записей одного предмета;
2. отдельные пары с избытком: p по Пуассону с ожиданием из фона, порог Бонферрони по числу пар;
3. сеть значимых пар: связывает ли она известные группы связей между собой.
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORDS = ROOT / "extracted/plus2026_cords.csv"
OUT = ROOT / "extracted/globalweb.txt"
SHIFTS = [d for d in range(-10, 11) if d]
SHIFTS10 = [10 * d for d in range(-10, 11) if d]
rare = lambda v: v >= 100 and v % 10


def load():
    vals, groups = defaultdict(list), defaultdict(lambda: defaultdict(int))
    for r in csv.DictReader(open(CORDS)):
        k, v = r["inv_num"], int(r["value"] or 0)
        vals[k].append(v)
        if not r["parent_id"]:
            groups[k][r["group"]] += v
    C = {k: {v for v in vs if rare(v)} for k, vs in vals.items()}
    G = {k: {s for s in groups[k].values() if rare(s)} for k in vals}
    return C, G, {k: len(vs) for k, vs in vals.items()}


def pair_counts(C, G, d):
    """score[(a, b)] for a < b, with b's values and totals shifted by d (d = 0: real)."""
    idxC, idxG = defaultdict(set), defaultdict(set)
    for k, s in C.items():
        for v in s:
            idxC[v + d].add(k)
    for k, s in G.items():
        for v in s:
            idxG[v + d].add(k)
    score = defaultdict(int)
    for a in C:
        for v in C[a]:
            for b in idxC.get(v, ()):            # cord of a = cord of b (shifted)
                if b != a:
                    score[(a, b)] += 1
            for b in idxG.get(v, ()):            # cord of a = group total of b (shifted)
                if b != a:
                    score[(a, b)] += 1
        for v in G[a]:
            for b in idxC.get(v, ()):            # group total of a = cord of b (shifted)
                if b != a:
                    score[(a, b)] += 1
    # unordered pair: a's real values against b's shifted, summed over both directions, halved
    out = defaultdict(float)
    for (a, b), n in score.items():
        out[tuple(sorted((a, b)))] += n / 2
    return out


def poisson_sf(k, lam):
    if k <= 0:
        return 1.0
    lam = max(lam, 1e-6)
    term, cdf = math.exp(-lam), 0.0
    for i in range(int(k)):
        cdf += term
        term *= lam / (i + 1)
    return max(0.0, 1 - cdf)


def summary(lines, label, ps, real, nulls):
    r = sum(real.get(p, 0) for p in ps)
    per = [sum(n.get(p, 0) for p in ps) for n in nulls]
    m = sum(per) / len(per)
    sd = (sum((x - m) ** 2 for x in per) / (len(per) - 1)) ** 0.5
    lines.append(f"   {label}: real {r:.0f}, shifted {m:.1f} ± {sd:.1f} (min {min(per):.0f}, max {max(per):.0f})"
                 + (f"; ratio {r / m:.2f}" if m else ""))


def main():
    D = json.load(open(ROOT / "site/data.json"))
    site = {k["id"]: k["site"] for k in D["khipus"]}
    known = {tuple(sorted((e["from"], e["to"]))) for e in D["edges"]} | {tuple(sorted((x["a"], x["b"]))) for x in D["duplicates"]}
    C, G, size = load()
    real = pair_counts(C, G, 0)
    npairs = len(C) * (len(C) - 1) // 2
    alpha = 0.05 / npairs
    lines = [f"khipus {len(C)}; pairs sharing any rare value: {len(real)}; known links and duplicates {len(known)}"]

    def cls(p):
        a, b = (site.get(x) for x in p)
        return "same place" if a and a == b else "different places" if a and b else "place unknown"
    for name, sh in (("shifts ±1…±10", SHIFTS), ("shifts ±10…±100, same last digit", SHIFTS10)):
        nulls = [pair_counts(C, G, d) for d in sh]
        pairs = set(real) | {p for n in nulls for p in n}
        exp = {p: sum(n.get(p, 0) for n in nulls) / len(nulls) for p in pairs}
        lines.append(f"\n== Baseline: {name}")
        sig = []
        for p, s_ in real.items():
            pv = poisson_sf(math.ceil(s_), exp.get(p, 0) + 0.05)
            if pv < alpha:
                sig.append((pv, p, s_, exp.get(p, 0)))
        sig.sort()
        # one object under two numbers (KFG and OKR records not merged): same number of cords (±10%), many shared values
        same = {p for p, s_ in real.items() if s_ >= 5 and s_ >= 3 * (exp.get(p, 0) + 0.2)
                and min(size[p[0]], size[p[1]]) >= 0.9 * max(size[p[0]], size[p[1]])}
        lines.append(f"2. Pairs above chance (Poisson, expected from the shifts + 0.05; Bonferroni over {npairs} pairs, "
                     f"p < {alpha:.1e}): {len(sig)}, of them known {sum(1 for x in sig if x[1] in known)}, "
                     f"one object under two numbers {sum(1 for x in sig if x[1] in same and x[1] not in known)}")
        for pv, p, s_, e in sig:
            tag = "known" if p in known else "same" if p in same else "NEW"
            lines.append(f"   {tag:5} {p[0]:8} {p[1]:8} score {s_:4.0f} expected {e:5.2f} p {pv:.1e} · "
                         f"{site.get(p[0])} / {site.get(p[1])} · cords {size[p[0]]}/{size[p[1]]}")
        excl = known | same | {x[1] for x in sig}
        lines.append(f"1. Everything else — shared rare values over all other pairs (without known links, the significant pairs "
                     f"and {len(same)} pairs that look like one object under two numbers):")
        for c in ("same place", "different places", "place unknown"):
            summary(lines, c, [p for p in pairs if p not in excl and cls(p) == c], real, nulls)
        lines.append("   within each place with ≥ 5 khipus:")
        by = defaultdict(list)
        for p in pairs:
            if p not in excl and cls(p) == "same place":
                by[site[p[0]]].append(p)
        for s_, ps in sorted(by.items(), key=lambda x: -len(x[1])):
            n = sum(1 for k in site if site[k] == s_ and k in C)
            if n >= 5:
                summary(lines, f"  {s_} ({n} khipus)", ps, real, nulls)
        # is the remaining excess spread over many pairs (a web) or held by a few?
        ex = sorted(((real.get(p, 0) - exp.get(p, 0), p) for p in pairs if p not in excl), reverse=True)
        tot = sum(e for e, _ in ex)
        pos = [e for e, _ in ex if e > 0]
        cum, k50 = 0, 0
        for e in pos:
            cum += e; k50 += 1
            if cum >= tot / 2:
                break
        lines.append(f"   remaining excess {tot:.0f} over {len(ex)} pairs; the top 10 pairs hold {sum(e for e, _ in ex[:10]):.0f}, "
                     f"the top 100 {sum(e for e, _ in ex[:100]):.0f}; half of it needs the top {k50} pairs")
        lines.append("   top pairs: " + "; ".join(f"{p[0]}~{p[1]} {real.get(p, 0):.0f}/{exp.get(p, 0):.1f}" for e, p in ex[:12]))
    # 4. do khipus from one place share more rare values than random khipus of the same size? (controls for popular
    #    values: the pair scores are the real ones, only the place labels are shuffled, within size deciles)
    import random
    rnd = random.Random(7)
    placed = sorted(k for k in C if site.get(k))
    order = sorted(placed, key=lambda k: size[k])
    dec = {k: i * 10 // len(order) for i, k in enumerate(order)}
    sc = {p: v for p, v in real.items() if p not in excl and p[0] in dec and p[1] in dec}
    def stat(lab):
        tot, per = 0.0, defaultdict(float)
        for (a, b), v in sc.items():
            if lab[a] == lab[b]:
                tot += v; per[lab[a]] += v
        return tot, per
    lab0 = {k: site[k] for k in placed}
    T0, per0 = stat(lab0)
    sims, persims = [], defaultdict(list)
    bins = defaultdict(list)
    for k in placed:
        bins[dec[k]].append(k)
    for _ in range(2000):
        lab = {}
        for ks in bins.values():
            ls = [lab0[k] for k in ks]; rnd.shuffle(ls)
            lab.update(zip(ks, ls))
        t, per = stat(lab)
        sims.append(t)
        for s_ in per0:
            persims[s_].append(per.get(s_, 0.0))
    m = sum(sims) / len(sims); sd = (sum((x - m) ** 2 for x in sims) / (len(sims) - 1)) ** 0.5
    pv = (1 + sum(x >= T0 for x in sims)) / (1 + len(sims))
    lines.append(f"\n4. Same-place sharing against shuffled place labels (within size deciles, 2000 shuffles; pairs as in 1.): "
                 f"real {T0:.0f}, shuffled {m:.0f} ± {sd:.0f}, p = {pv:.4f}")
    for s_, v in sorted(per0.items(), key=lambda x: -x[1]):
        xs = persims[s_]; mm = sum(xs) / len(xs); p_ = (1 + sum(x >= v for x in xs)) / (1 + len(xs))
        n = sum(1 for k in placed if site[k] == s_)
        if n >= 5:
            lines.append(f"   {s_} ({n}): real {v:.0f}, shuffled {mm:.1f}, p = {p_:.4f}")

    # 3. does the network of significant pairs (last baseline) join the known groups?
    adj = defaultdict(set)
    for _, (a, b), _, _ in sig:
        adj[a].add(b); adj[b].add(a)
    for a, b in known:
        adj[a].add(b); adj[b].add(a)
    seen, comps = set(), []
    for v in adj:
        if v in seen:
            continue
        st, c = [v], set()
        while st:
            u = st.pop()
            if u not in c:
                c.add(u); st += list(adj[u] - c)
        seen |= c; comps.append(sorted(c))
    comps.sort(key=len, reverse=True)
    lines.append(f"\n3. Known links + significant pairs: {len(comps)} groups; sizes " + ", ".join(str(len(c)) for c in comps))
    for c in comps[:10]:
        lines.append("   " + " ".join(c))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
