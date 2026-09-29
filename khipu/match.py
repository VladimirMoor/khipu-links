"""Сверка последовательностей чисел из документов с кипу OKR.

Для каждой пары (документ, кипу) считаем:
  score    — log10-отношение правдоподобия «кипу — источник документа» против
             «случайная кипу» по различным числам документа (>= MIN_VALUE), найденным
             среди значений шнуров или сумм групп/поддеревьев. Учитывает и редкость
             числа, и размер кипу (у большой кипу случайных совпадений больше).
  lcs      — длина наибольшей общей подпоследовательности (порядок документа
             против порядка шнуров), только по числам >= MIN_VALUE.

Значимость: для каждого документа строим NULL_DOCS «подставных» документов той же
длины, где каждое число заменено случайным из того же десятичного разряда, и берём
лучший score по всем кипу. p-value = доля подставных, чей лучший score >= реального.
"""
import argparse
import csv
import glob
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import os
CORDS = Path(os.environ.get("KHIPU_CORDS", ROOT / "extracted/okr_cords.csv"))
MIN_VALUE = 2
NULL_DOCS = 200


def load_khipus(path=CORDS):
    by = defaultdict(list)
    meta = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            r["value"] = int(r["value"])
            by[r["khipu_id"]].append(r)
            meta[r["khipu_id"]] = (r["okr_num"], r["inv_num"])
    khipus = {}
    for kid, rows in by.items():
        rows.sort(key=lambda r: int(r["order"]))
        seq = [r["value"] for r in rows if r["n_knots"] != "0"]
        # суммы поддеревьев (шнур + все его потомки) и суммы верхних групп
        kids = defaultdict(list)
        for r in rows:
            kids[r["parent_id"]].append(r)
        sub = {}

        def subtotal(r):
            if r["cord_id"] in sub:
                return sub[r["cord_id"]]
            s = r["value"] + sum(subtotal(c) for c in kids.get(r["cord_id"], []))
            sub[r["cord_id"]] = s
            return s

        for r in rows:
            subtotal(r)
        groups = defaultdict(int)
        for r in rows:
            if r["parent_id"] == "" and r["group"] != "":
                groups[r["group"]] += r["value"]
        derived = set(sub.values()) | set(groups.values()) | {sum(r["value"] for r in rows)}
        khipus[kid] = {
            "okr": meta[kid][0], "inv": meta[kid][1],
            "seq": seq,
            "values": set(seq),
            "derived": derived - set(seq),
        }
    return khipus


Q_HIT = 0.5  # предполагаемая доля чисел документа, реально лежащих на «своей» кипу


class Model:
    """Вероятность случайно встретить число v среди целей кипу k.

    p(v) — частота v среди всех целей корпуса (значения шнуров + производные суммы),
    сглаженная: для невиданных значений используем среднюю частоту по разряду.
    pi(k, v) = 1 - (1 - p(v)) ** n_k, где n_k — число различных целей кипу.
    """

    def __init__(self, khipus):
        cnt = Counter()
        for k in khipus.values():
            k["targets"] = k["values"] | k["derived"]
            cnt.update(k["targets"])
        self.n = sum(cnt.values())
        self.cnt = cnt
        by_len = defaultdict(list)
        for v, c in cnt.items():
            by_len[len(str(v))].append(c)
        # средняя частота одного значения данного разряда (включая невиданные)
        self.len_p = {d: sum(cs) / self.n / (9 * 10 ** (d - 1)) for d, cs in by_len.items()}
        self.khipus = khipus

    def p(self, v):
        c = self.cnt.get(v)
        if c:
            return c / self.n
        return self.len_p.get(len(str(v)), 1e-7) / 2

    def pi(self, k, v):
        return 1 - (1 - self.p(v)) ** len(k["targets"])


def rarity(khipus):
    return Model(khipus)


def lcs(a, b):
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def score(doc_vals, k, m):
    """Лог-отношение правдоподобия: «эта кипу — источник» против «случайная кипу»."""
    s, hits = 0.0, []
    for v in set(doc_vals):
        pi = min(max(m.pi(k, v), 1e-9), 1 - 1e-9)
        if v in k["targets"]:
            hits.append(v)
            s += math.log10(max(Q_HIT, pi) / pi)
        else:
            s += math.log10((1 - Q_HIT) / (1 - pi)) if pi < Q_HIT else 0.0
    return s, sorted(hits)


def best(doc_vals, khipus, w, top=5):
    res = []
    for kid, k in khipus.items():
        s, hits = score(doc_vals, k, w)
        res.append((s, kid, hits))
    res.sort(reverse=True)
    return res[:top]


_pools = {}


def _shape(v):
    """(число цифр, число нулей на конце) — «форма» числа: 400 → (3, 2), 437 → (3, 0)."""
    t = str(v)
    return len(t), len(t) - len(t.rstrip("0"))


def null_doc(vals, rng, m=None):
    """Подставной документ: каждое число заменяем случайным значением той же формы
    (разряд и круглость), взятым из распределения чисел корпуса кипу. Так документ
    из одних круглых чисел (тасы: 100, 200, 400) сравнивается с такими же круглыми,
    а не с произвольными трёхзначными."""
    if m is not None and not _pools:
        for v, c in m.cnt.items():
            if v >= MIN_VALUE:
                _pools.setdefault(_shape(v), ([], []))
                _pools[_shape(v)][0].append(v)
                _pools[_shape(v)][1].append(c)
    out = []
    for v in vals:
        sh = _shape(v)
        if sh in _pools:
            vs, cs = _pools[sh]
            out.append(rng.choices(vs, cs)[0])
        else:
            d = sh[0]
            out.append(rng.randint(10 ** (d - 1), 10 ** d - 1))
    return out


NOISE = ("precio", "edad", "año", "anos", "mes", "día", "dia", "tiempo", "semana",
         "pena", "multa", "costas", "derechos", "folio", "foja", "hoja", "azote", "latigazo",
         "tercio", "vez", "veces")


def is_noise(r):
    s = " ".join(r.get(k, "") for k in ("item", "unit")).lower()
    return any(w in s for w in NOISE)


def load_docs(pattern, quipu_only=True):
    docs = defaultdict(list)
    titles = {}
    for fn in sorted(glob.glob(pattern)):
        with open(fn) as f:
            for r in csv.DictReader(f):
                if quipu_only and r.get("quipu_based") not in ("yes", "probable"):
                    continue
                if is_noise(r):
                    continue
                try:
                    q = float(r["quantity"])
                except (ValueError, TypeError, KeyError):
                    continue
                if q != int(q) or q < MIN_VALUE:
                    continue
                if r.get("confidence", "") == "low":
                    continue
                docs[r["doc_id"]].append(int(q))
                titles.setdefault(r["doc_id"], r.get("doc_title", ""))
    return docs, titles


def evaluate(name, vals, khipus, w, rng, null_n=NULL_DOCS, top=5):
    ranking = best(vals, khipus, w, top)
    real = ranking[0][0]
    nulls = [best(null_doc(vals, rng, w), khipus, w, 1)[0][0] for _ in range(null_n)]
    p = (sum(1 for s in nulls if s >= real) + 1) / (null_n + 1)
    out = []
    for s, kid, hits in ranking:
        k = khipus[kid]
        big = [v for v in vals if v >= 10]
        out.append({
            "doc": name, "khipu_id": kid, "okr": k["okr"], "inv": k["inv"],
            "score": round(s, 2), "n_hits": len(hits),
            "lcs_ge10": lcs(big, [v for v in k["seq"] if v >= 10]),
            "hits": " ".join(map(str, hits[:40])),
        })
    return out, p, sorted(nulls)[int(0.95 * len(nulls))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=str(ROOT / "extracted/[JC]*.csv"))
    ap.add_argument("--null", type=int, default=NULL_DOCS)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=str(ROOT / "extracted/match_results.csv"))
    ap.add_argument("--place", default="", help="regex по месту находки кипу (Leymebamba|Chachapoyas)")
    ap.add_argument("--doc", default="", help="regex по doc_id")
    ap.add_argument("--all-docs", action="store_true", help="брать и документы без пометки quipu_based")
    a = ap.parse_args()

    from provenance import subset
    khipus = load_khipus()
    w = rarity(khipus)  # частоты чисел — по всему корпусу
    khipus = subset(khipus, CORDS, a.place)
    print(f"кипу в поиске: {len(khipus)}")
    rng = random.Random(a.seed)
    docs, titles = load_docs(a.docs, quipu_only=not a.all_docs)
    rows = []
    import re as _re
    for name, vals in docs.items():
        if a.doc and not _re.search(a.doc, name):
            continue
        res, p, q95 = evaluate(name, vals, khipus, w, rng, a.null)
        for r in res:
            r.update({"p_best": round(p, 4), "null_q95": round(q95, 2),
                      "n_doc_values": len(vals), "n_distinct": len(set(vals)),
                      "title": titles[name][:80]})
            rows.append(r)
        b = res[0]
        print(f"{name:8} n={len(vals):3} best={b['okr']}/{b['inv']} score={b['score']:.1f} "
              f"(null95={q95:.1f}) p={p:.3f} hits={b['hits'][:60]}")
    if rows:
        with open(a.out, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(rows)


if __name__ == "__main__":
    main()
