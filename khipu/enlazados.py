"""«Khipus Enlazados» MNAAHP RT-16905 (OKR KH0638–KH0652; Chirinos, Ghezzi, Álvarez 2023):
15 физически связанных кипу. Разбор Excel-файлов OKR и поиск арифметических связей внутри
связки.
"""
import glob
import itertools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xlsx import read  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data/open-khipu-repository/data/KH0638_0652"

# что к чему привязано (по описанию набора)
LINKS = {
    "01": ["15", "13", "14", "02", "03", "04"],  # Hub B, D, E и петля Khipu15
    "04": ["05", "06", "07", "08", "09"],        # зона F и Hub G
    "hubA": ["11", "12", "13", "14"],
    "hubC": ["10", "11", "12"],
}


def num(s):
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return 0


def load():
    K = {}
    for f in sorted(glob.glob(str(DIR / "*.xlsx"))):
        k = re.search(r"\.(\d\d)\.xlsx$", f).group(1)
        sh = read(f)
        if "pendant_cords" not in sh:
            continue
        # группы: строки кластеров с числовым ORDINAL и BEG/END_CORD
        groups = []
        for r in sh["primary_cord"]:
            if r and r[0].strip().isdigit() and len(r) > 6 and r[5].strip().isdigit() and r[6].strip().isdigit():
                groups.append((int(r[0]), int(r[5]), int(r[6])))
        pend, subs = {}, {}
        for r in sh["pendant_cords"][1:]:
            if not r or not r[0].strip():
                continue
            name = r[0].strip()
            rec = {"name": name, "att": (r[1].split("/")[-1].strip() if len(r) > 1 and "/" in r[1] else ""),
                   "knots": r[2] if len(r) > 2 else "", "color": r[5] if len(r) > 5 else "",
                   "value": num(r[6]) if len(r) > 6 else 0}
            if name.isdigit():
                pend[int(name)] = rec
            elif re.fullmatch(r"\d+s\d+(s\d+)*", name):
                subs.setdefault(int(name.split("s")[0]), []).append(rec)
        cords = []
        for i in sorted(pend):
            p = pend[i]
            g = next((o for o, a, b in groups if a <= i <= b), None)
            sv = sum(s["value"] for s in subs.get(i, []))
            cords.append({**p, "idx": i, "group": g, "tree": p["value"] + sv, "nsub": len(subs.get(i, []))})
        K[k] = cords
    return K


def main():
    K = load()
    print("кипу:", {k: len(v) for k, v in K.items()})
    tot = {k: sum(c["tree"] for c in v) for k, v in K.items()}
    totown = {k: sum(c["value"] for c in v) for k, v in K.items()}
    gsum = {}
    for k, v in K.items():
        for g, it in itertools.groupby(v, key=lambda c: c["group"]):
            it = list(it)
            gsum[(k, g)] = (sum(c["tree"] for c in it), sum(c["value"] for c in it), [c["value"] for c in it])
    print("\nИтоги кипу (с дочерними / собственные):")
    for k in K:
        print(f"  {k}: {tot[k]:6} / {totown[k]:6}   группы: " +
              " ".join(f"{g}:{s[1]}" for (kk, g), s in gsum.items() if kk == k))
    # все «единицы»: шнуры, группы, кипу
    units = []
    for k, v in K.items():
        for c in v:
            units.append((c["value"], f"{k}.p{c['idx']}"))
            if c["tree"] != c["value"]:
                units.append((c["tree"], f"{k}.p{c['idx']}+дочерние"))
    for (k, g), (st, so, _) in gsum.items():
        units.append((so, f"{k}.группа{g}"))
    for k in K:
        units.append((totown[k], f"{k}.всего"))
    byval = {}
    for v, n in units:
        if v >= 20:
            byval.setdefault(v, []).append(n)
    print("\nОдинаковые числа (≥ 20) у разных кипу, где хотя бы одно — итог группы или кипу:")
    for v, names in sorted(byval.items()):
        ks = {n.split(".")[0] for n in names}
        if len(ks) >= 2 and any(("группа" in n or "всего" in n) for n in names):
            print(f"  {v:6}: {', '.join(names)}")
    print("\nГипотеза «узловая кипу хранит итоги привязанных»:")
    for hub, att in LINKS.items():
        if hub not in K:
            continue
        vals = {c["value"] for c in K[hub]} | {c["tree"] for c in K[hub]} | {s[1] for (kk, g), s in gsum.items() if kk == hub}
        for a in att:
            if a in totown:
                hit = [x for x in (totown[a], tot[a]) if x in vals]
                print(f"  {hub} ← {a}: итог {a} = {totown[a]} / {tot[a]}  → {'ЕСТЬ на ' + hub if hit else 'нет'}")
        s_all = sum(totown[a] for a in att if a in totown)
        print(f"  {hub}: сумма итогов привязанных = {s_all} → {'ЕСТЬ' if s_all in vals else 'нет'}")


if __name__ == "__main__":
    main()
