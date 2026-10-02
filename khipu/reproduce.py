"""Воспроизведение препринта: перезапускает скрипты и сверяет каждое приведённое в тексте число с их выводом.

  python3 khipu/reproduce.py          # все проверки; итог PASS/FAIL по каждой, код выхода 1 при любом FAIL
Для чисел, которые скрипты не печатают, проверка считается здесь же прямо по данным (раздел «по данным»).
В конце — список утверждений препринта, проверенных только вручную (по записям Ашеров, KFG и т. п.).
Отчёт: extracted/reproduce.txt.
"""
import csv
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/reproduce.txt"

# (section, claim in the preprint, script, regex on its output, expected groups as strings)
CHECKS = [
    ("3.1", "only exact cross-khipu vector sum; offset baseline 0–2", "vecsum", r"точные: (\d+) \(фон \[([\d, ]+)\]", lambda g: g[0] == "1" and max(map(int, g[1].split(","))) <= 2),
    ("3.1", "AS143 g4 = AS149 g1 + g2", "vecsum", r"UR1143 г4 \[17436, 8220, 41883, 1350, 9528\] = UR1149 сумма г1–г2", None),
    ("3.1", "composition 22.4 : 10.4 : 54.4 : 12.8 %", "composition", r"берлинский состав: \[0\.224, 0\.1038, 0\.5442, 0\.128\]", None),
    ("3.2", "UR233: 29 equal values, other offsets 3.2 ± 4.0, z = 6.4", "huacho", r"UR233: лучший сдвиг c = [-+]?\d+, совпадений 29; прочие сдвиги 3\.2 ± 4\.0, максимум \d+; z = 6\.4", None),
    ("3.2", "UR232: 40 equal values, other offsets 2.1 ± 1.9, z = 19.5", "huacho", r"UR232: лучший сдвиг c = [-+]?\d+, совпадений 40; прочие сдвиги 2\.1 ± 1\.9, максимум \d+; z = 19\.5", None),
    ("3.2", "part 2 from part 3: AS175 5/15, UR232 8/15 exact", "huacho", r"точно: по AS175 5/15, по UR232 8/15", None),
    ("3.2", "with one-knot tolerance 6/15 and 10/15", "huacho", r"точно или с разницей в один узел: по AS175 6/15, по UR232 10/15", None),
    ("3.2", "mixed version 10 of 15; baseline 1.5, max 5", "huacho", r"сходится 10/15; фон \(итог ± d\): 1\.5 в среднем, максимум 5", None),
    ("3.3", "only AS125 (and its duplicate UR247) matches > 1 subsidiary", "as118", r"допуск 1\.0%: .*верх \[\(3, 'AS125'\), \(2, 'UR247'\), \(1,", None),
    ("3.3", "no khipu matches 3 with values shifted ±100…±300", "as118", r"кипу со счётом ≥ 3 из 4 — \[([0, ]+)\]", lambda g: set(g[0].replace(" ", "").split(",")) == {"0"}),
    ("3.3", "8565 if AS125 g4 cord 1 = 3111; 11522 if g3 cord 1 = 2298", "as118", r"при 3111 сумма = 8565[\s\S]*первый шнур = 2298", None),
    ("3.4", "UR212 37 of 195, AS131 25 of 146; others ≤ 4", "basel_huacho", r"UR212: покрыто 37 из 195[\s\S]*UR1131: покрыто 25 из 146[\s\S]*максимум 4", None),
    ("3.4", "MM015 = UR212 182–194 (13 cords)", "basel_huacho", r"UR212 обратно: шнуры 1–13 = 182–194 \(13\)", None),
    ("3.4", "same unit in 3 of 3 fragments, p ≈ 0.005", "ur212_as131_units", r"фрагментов с участками обоих кипу: 3; из них одна и та же единица: 3; случайно \(после первого\) p ≈ 0\.005", None),
    ("3.4", "unit totals uncorrelated (ρ = 0.19)", "units14", r"UR212 ~ UR1131 обратно: ρ = 0\.19", None),
    ("3.4", "marked slots 3 filled; other empties stay 2; 41 agree, 5 differ", "basel_slots", r"помеч\. 0→n: 3, помеч\. n=n: 1, прочие 0→0: 2, прочие n=n: 41, прочие n≠n: 5", None),
    ("3.5", "14 groups: 4 of 23 in the batch, 1.6% elsewhere, P ≈ 0.0005", "units14", r"4 из 23; прочие 5 из 308 \(1\.6%\); биномиально P ≈ 0\.0005", None),
    ("3.5", "largest space in the middle 12.9 times, 13.0 expected (109 khipus)", "halves", r"109; наибольший промежуток посередине: 12\.9; ожидание 13\.0", None),
    ("3.6", "154 regular khipus; 11 with an empty intact position, 3.0 expected, max 6 in 200", "blanks", r"кипу с правильными группами: 154[\s\S]*: 11 \(фон 3\.0, макс 6 из 200\)", None),
    ("3.6", "UR255: 12 empty, then 5 of the last 6 filled", "fillslot", r"порядок по группам UR255[^:]*: ппппппппппппзззззпз", None),
    ("3.6", "UR256: 6 empty, then 12 filled", "fillslot", r"UR256, группы[^:]*: ппппппзззззззззззз", None),
    ("3.6", "split probabilities about 1 in 3,900 and 1 in 18,600", "paper_extra", r"UR255: [пз]+; .*P = 1 / 3 876[\s\S]*UR256: [пз]+; .*P = 1 / 18 564", None),
    ("3.6", "UR273B ~ UR274B six totals, 0.5 expected, p ≈ 10⁻⁵", "paper_extra", r"UR273B ~ UR274B: 6 против 0\.50; Пуассон p = 1\.\de-05", None),
    ("3.6", "UR273A ~ UR274A 891, 453, 448, 448 in order, 0.3 expected", "paper_extra", r"UR273A ~ UR274A, итоги групп ≥ 100: общих 4 против 0\.30 \(p = 2\.\de-04\); 891 .*453 .*448 .*448 .*порядок сохранён: True", None),
    ("3.6", "UR273B ~ UR274B totals in the same order", "paper_extra", r"UR273B ~ UR274B, итоги групп ≥ 100: общих 6 .*порядок сохранён: True", None),
    ("3.7", "UR269: 33 of 43 deductions equal their place value, 17 shuffled", "slotded", r"33 из 43; перестановка внутри блоков: среднее 17\.3", None),
    ("3.7", "UR269 place deductions 47, 46, 46, 44, 25", "slotded", r"место 1: \[[^\]]*\][\s\S]*место 5", "modes"),
    ("3.7", "UR269 place 1 on UR275: 5 of 10, 0.5 expected; places 2–4: 0, 1, 1", "ur269_streams", r"UR275: место 1: 5 из 10 \(фон 0\.50\); место 2: 0 из 12 \(фон 0\.35\); место 3: 1 из 9 \(фон 0\.25\); место 4: 1 из 7 \(фон 0\.10\)", None),
    ("3.7", "block b = UR275 entry b + 15; 5 hits, permutations at most 4, p ≈ 0.0002", "ur269_streams", r"блок b ~ группа b \+15 UR275: 5 совпадений; 5000 перестановок блоков: среднее [\d.]+, максимум 4, p = 0\.0002", None),
    ("3.7", "UR275 entry 19 [1825, 47, 1780] ~ UR269 block 4 [1827, 1780, 47]", "ur269_streams", r"блок 4 место 1 \[1827, 1780, 47\]  ~  UR275 г19 \[1825, 47, 1780\]", None),
    ("3.8", "summaries 384 against 415.6 (max 585)", "summaries", r"384; фон 415\.6 \(макс 585\)", None),
    ("3.9", "UR053C → UR053B: 35 fields, at most 18 in 2,000 shuffles", "paper_extra", r"совпавших полей 35; 2000 перемешиваний троек C: среднее [\d.]+, максимум 18", None),
    ("3.9", "run ends on group boundaries 38% against 46%", "unit_invariance", r"доля 38% против 46%", None),
    ("3.10", "74 of 78 of Urton's group totals equal ours", "do_check", r"итогов у Уртона: 78; совпадают с нашей расшифровкой: 74", None),
    ("3.11", "style: 22 of 29 = share of the larger class", "style_pach_huacho", r"22 из 29 \(доля большего класса 76%\)", None),
]

BY_HAND = [
    "3.1 Chirinos Rivera's proportions (11.0, 22.7, 43.6, 22.7%) and the AS143/AS149 discussion in Ascher & Ascher 1981 — from the books",
    "3.1 'Among 16 corpus khipus … only AS143 is as uniform' and the AS179 colour breakdown (p ≈ 0.06) — composition.py / coloursum.py, ranked lists",
    "3.2 85 of 100 and 73 of 105 comparable values equal; extra pendants, lengths, subsidiaries — from the OKR/KFG cord records (huacho.py lists them group by group)",
    "3.2 group-order permutation p ≤ 0.003 — diagscan.perm_p (slow; run on demand)",
    "3.3 the Aschers' notes on AS118 and AS125 (Databook pp. 791–793) — from the Databook",
    "3.4 provenance and collectors (Medrano 2022, museum-digital) — from the sources",
    "3.6 red tassels (2 of 4 against 0 of 25) and product labels — from the OKR records and Urton & Chu",
]


def run(name, cache={}):
    if name not in cache:
        t = time.time()
        p = subprocess.run([sys.executable, str(ROOT / f"khipu/{name}.py")], capture_output=True, text=True, cwd=ROOT)
        cache[name] = (p.stdout + p.stderr, time.time() - t, p.returncode)
    return cache[name]


def data_checks():
    """§3.1 shares in ninths and the two equal 2/9 shares, straight from the cord data."""
    g = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(ROOT / "extracted/plus_cords.csv")):
        if r["parent_id"] == "" and r["inv_num"] in ("UR1143", "UR1149"):
            g[r["inv_num"]][r["group"]].append((int(r["order"]), int(r["value"])))
    grp = {k: [[v for _, v in sorted(x)] for _, x in sorted(d.items(), key=lambda kv: min(o for o, _ in kv[1]))] for k, d in g.items()}
    a, b = grp["UR1143"], grp["UR1149"]
    total = sum(a[0])
    ninth = total / 9
    sh = [sum(a[1]) / ninth, sum(a[2]) / ninth, sum(a[4]) / ninth, sum(b[0]) / ninth, sum(b[1]) / ninth]
    out = [("3.1", "AS143 total 180,345", total == 180345, f"{total}"),
           ("3.1", "shares in ninths 0.99, 2.05, 2.05, 1.93, 1.98", [round(x, 2) for x in sh] == [0.99, 2.05, 2.05, 1.93, 1.98], ", ".join(f"{x:.2f}" for x in sh)),
           ("3.1", "AS143 g3 and g5 total 41,062 and 41,061", (sum(a[2]), sum(a[4])) == (41062, 41061), f"{sum(a[2])}, {sum(a[4])}"),
           ("3.1", "g4 = g1 + g2 of AS149 position by position", a[3] == [x + y for x, y in zip(b[0], b[1])], f"{a[3]}")]
    return out


def main():
    lines, fails = [], 0
    for sec, claim, script, pat, test in CHECKS:
        out, dt, rc = run(script)
        m = re.search(pat, out)
        ok = bool(m) and rc == 0
        if ok and test == "modes":
            from collections import Counter
            modes = [Counter(map(int, re.search(rf"место {p}: \[([^\]]*)\]", out).group(1).split(","))).most_common(1)[0][0] for p in range(1, 6)]
            ok = modes == [47, 46, 46, 44, 25]
        elif ok and test:
            ok = test(m.groups())
        fails += not ok
        lines.append(f"{'PASS' if ok else 'FAIL'}  §{sec:<4} {claim}   [{script}.py]")
    for sec, claim, ok, val in data_checks():
        fails += not ok
        lines.append(f"{'PASS' if ok else 'FAIL'}  §{sec:<4} {claim}   [по данным: {val}]")
    n = len(lines)
    lines.append(f"\n{n - fails} of {n} checks pass; scripts run: {len(run.__defaults__[0])}, "
                 f"{sum(v[1] for v in run.__defaults__[0].values()):.0f} s")
    lines.append("\nChecked by hand only (not scripted):")
    lines += [f"  - {x}" for x in BY_HAND]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
