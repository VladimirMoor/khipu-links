"""UR269: место 1 каждого блока — поставки, записанные и на UR275 (вычет 47 везде) и его копии UR266.

1) По местам блока: сколько записей UR269 (брутто или нетто, некруглые ≥ 100) находятся среди значений UR275 / UR266;
   фон — те же значения UR275 / UR266, сдвинутые на ±1…±10.
2) Выравнивание: блок b UR269 (запись места 1) ~ группа b + c UR275; число совпадений при лучшем c против 5000
   перестановок порядка блоков.
3) Записи мест 2–5 по всем остальным кипу Инкавази.
Вывод: extracted/ur269_streams.txt.
"""
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
import slotded  # noqa: E402

OUT = ROOT / "extracted/ur269_streams.txt"
nr = lambda v: v >= 100 and v % 100 != 0


def main():
    B = slotded.blocks("UR269")
    D = json.load(open(ROOT / "site/data.json"))
    ink = [k["id"] for k in D["khipus"] if k["site"] == "inkawasi" and k["id"] != "UR269"]
    G = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["inv_num"] in ink and r["parent_id"] == "":
            G[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"])))
    gr = {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in G.items()}
    vals = lambda k, d=0: {v + d for g in gr[k] for v in g if nr(v)}
    lines = []
    for k in ("UR275", "UR266"):
        parts = []
        for p in range(1, 6):
            recs = [b[p - 1] for b in B if len(b) >= p and b[p - 1] and nr(b[p - 1][0])]
            hit = sum(1 for r in recs if any(nr(v) and v in vals(k) for v in r[:2]))
            null = [sum(1 for r in recs if any(nr(v) and v in vals(k, d) for v in r[:2])) for d in list(range(-10, 0)) + list(range(1, 11))]
            parts.append(f"место {p}: {hit} из {len(recs)} (фон {sum(null) / len(null):.2f})")
        lines.append(f"{k}: " + "; ".join(parts))
    A = gr["UR275"]

    def best(Bs):
        S = {}
        for c in range(-40, 40):
            S[c] = sum(1 for bi, b in enumerate(Bs, 1) if b and b[0] and 0 <= bi + c - 1 < len(A)
                       and any(nr(v) and v in A[bi + c - 1] for v in b[0][:2]))
        c = max(S, key=S.get)
        return S[c], c
    real, c = best(B)
    rnd = random.Random(1)
    null = []
    for _ in range(5000):
        Bs = B[:]
        rnd.shuffle(Bs)
        null.append(best(Bs)[0])
    p = (1 + sum(x >= real for x in null)) / 5001
    lines.append(f"выравнивание: блок b ~ группа b {c:+d} UR275: {real} совпадений; 5000 перестановок блоков: "
                 f"среднее {sum(null) / len(null):.2f}, максимум {max(null)}, p = {p:.4f}")
    for bi, b in enumerate(B, 1):
        j = bi + c - 1
        if b and b[0] and 0 <= j < len(A) and any(nr(v) and v in A[j] for v in b[0][:2]):
            lines.append(f"  блок {bi} место 1 {b[0][:3]}  ~  UR275 г{j + 1} {A[j][:3]}")
    for p in range(2, 6):
        recs = [b[p - 1] for b in B if len(b) >= p and b[p - 1] and nr(b[p - 1][0])]
        found = defaultdict(int)
        for r in recs:
            for k in gr:
                if any(nr(v) and v in vals(k) for v in r[:2]):
                    found[k] += 1
        lines.append(f"место {p} ({len(recs)} записей) по другим кипу архива: "
                     + (", ".join(f"{k} {n}" for k, n in sorted(found.items(), key=lambda x: -x[1])) or "нигде"))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
