"""Нечисловые шнуры как «знаки»: доля и повторяемость между кипу.

1. Доля. Каждый подвесной шнур (OKR): без узлов / десятичная раскладка (не более одного
   кластера единиц L/E, он ниже всех S-кластеров) / недесятичная. Итог по корпусу и по
   «культурам» (канутос/Уари — по списку ниже).
2. Знаки. Недесятичный шнур → строка кластеров сверху вниз: S3 (три простых), L10 (длинный в
   10 витков), E (восьмёрка) … Считаем знаки из ≥ 3 кластеров, встречающиеся в ≥ 2 разных кипу
   (музейные номера разные), и пары соседних знаков (биграммы) в ≥ 2 кипу. Фон: кластеры всех
   недесятичных шнуров перемешаны между шнурами (число кластеров на шнуре сохранено) — сколько
   тогда общих знаков. Вывод: extracted/signs.txt.
"""
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/open-khipu-repository/data/khipu.db"
OUT = ROOT / "extracted/signs.txt"
WARI = {"UR050", "UR051", "UR052", "UR054", "UR055", "UR039", "UR110", "UR112"}


def load():
    db = sqlite3.connect(DB)
    meta = {k: (inv, str(mus or inv).replace(" ", "").upper())
            for k, inv, mus in db.execute("select KHIPU_ID, INVESTIGATOR_NUM, MUSEUM_NUM from khipu_main")}
    cords = {}
    for kid, cid, lvl, order in db.execute("select KHIPU_ID, CORD_ID, CORD_LEVEL, CORD_ORDINAL from cord"):
        if lvl == 1:
            cords[cid] = (kid, order, [])
    cl = defaultdict(lambda: defaultdict(list))
    for cid, pos, t, turns in db.execute(
            "select k.CORD_ID, kc.START_POS, k.TYPE_CODE, cast(k.NUM_TURNS as int) "
            "from knot k join knot_cluster kc on k.CLUSTER_ID = kc.CLUSTER_ID"):
        if cid in cords:
            cl[cid][pos or 0].append((t, turns or 0))
    for cid, byp in cl.items():
        for pos in sorted(byp):
            ks = byp[pos]
            types = Counter(t for t, _ in ks)
            if "L" in types:
                tok = f"L{max(n for t, n in ks if t == 'L')}"
            elif "E" in types:
                tok = "E"
            elif "S" in types:
                tok = f"S{types['S']}"
            else:
                tok = "?" + "".join(sorted(types))
            cords[cid][2].append((pos, tok))
    return meta, cords


def kind(toks):
    if not toks:
        return "пусто"
    unit = [i for i, (_, t) in enumerate(toks) if t[0] in "LE"]
    s = [i for i, (_, t) in enumerate(toks) if t[0] == "S"]
    if len(unit) > 1 or (unit and s and max(s) > min(unit)):
        return "недесятичный"
    if any(t[0] == "L" and int(t[1:] or 0) >= 10 for _, t in toks):
        return "недесятичный"
    return "десятичный"


def shared(signs_by_khipu, mus):
    where = defaultdict(set)
    for k, ss in signs_by_khipu.items():
        for s in ss:
            where[s].add(mus[k])
    return {s: w for s, w in where.items() if len(w) >= 2}


def main():
    meta, cords = load()
    mus = {k: m for k, (_, m) in meta.items()}
    tot = Counter()
    by_group = defaultdict(Counter)
    nd = defaultdict(list)          # khipu -> [(order, sign)]
    for cid, (kid, order, toks) in cords.items():
        k = kind(toks)
        tot[k] += 1
        by_group["Уари/канутос" if meta[kid][0] in WARI else "прочие"][k] += 1
        if k == "недесятичный":
            nd[kid].append((order, tuple(t for _, t in toks)))
    lines = ["1. Подвесные шнуры корпуса OKR:"]
    n = sum(tot.values())
    for k, v in tot.most_common():
        lines.append(f"   {k:14} {v:6} ({v / n:.1%})")
    for g, c in by_group.items():
        m = sum(c.values())
        lines.append(f"   {g}: " + ", ".join(f"{k} {v} ({v / m:.0%})" for k, v in c.most_common()))

    signs = {k: {s for _, s in v if len(s) >= 3} for k, v in nd.items()}
    bigr = {}
    for k, v in nd.items():
        v = [s for _, s in sorted(v)]
        bigr[k] = {(a, b) for a, b in zip(v, v[1:])}
    real_s, real_b = shared(signs, mus), shared(bigr, mus)
    # фон
    rnd = random.Random(1)
    pool = [t for v in nd.values() for _, s in v for t in s]
    null_s, null_b = [], []
    for _ in range(30):
        rnd.shuffle(pool)
        it = iter(pool)
        fake = {k: [(o, tuple(next(it) for _ in s)) for o, s in v] for k, v in nd.items()}
        null_s.append(len(shared({k: {s for _, s in v if len(s) >= 3} for k, v in fake.items()}, mus)))
        fb = {}
        for k, v in fake.items():
            v = [s for _, s in sorted(v)]
            fb[k] = {(a, b) for a, b in zip(v, v[1:])}
        null_b.append(len(shared(fb, mus)))
    lines += ["", f"2. Недесятичных шнуров: {sum(len(v) for v in nd.values())} в {len(nd)} кипу; "
                  f"разных знаков (≥ 3 кластеров): {len({s for v in signs.values() for s in v})}",
              f"   знаков в ≥ 2 кипу: {len(real_s)} (фон {sum(null_s) / 30:.1f}, макс {max(null_s)})",
              f"   пар соседних знаков в ≥ 2 кипу: {len(real_b)} (фон {sum(null_b) / 30:.1f}, макс {max(null_b)})",
              "   самые распространённые общие знаки:"]
    inv = {k: i for k, (i, _) in meta.items()}
    kh_of = defaultdict(set)
    for k, ss in signs.items():
        for s in ss:
            kh_of[s].add(inv[k])
    for s, w in sorted(real_s.items(), key=lambda t: -len(t[1]))[:15]:
        lines.append(f"     {'-'.join(s):28} в {len(w)} кипу: {sorted(kh_of[s])[:8]}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
