"""Place readings judged by knot heights, all places (units to ten-thousands).

For each khipu the height of each place is the median position of clusters whose place is certain (cords whose value
has no empty place). A cord is flagged when its top cluster sits clearly nearer the height of a higher place than of the
place it was read in (nearer by at least 30% of the local step between places), while its lower clusters sit at their own
heights: the reading then gains or loses an
empty place. Output: extracted/place_heights.csv with the OKR value, the height reading and the KFG 2026 value.
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "khipu"))
import hyp  # noqa: E402

NONDEC = {"UR1087"}


def main():
    K = hyp.okr()
    kfg = {}
    for r in csv.DictReader(open(ROOT / "extracted/kfg2026_cords.csv")):
        if r["level"] == "1":
            kfg[(r["inv_num"], int(r["order"]))] = int(r["value"] or 0)
    out = []
    for k, cs in K.items():
        if k in NONDEC:
            continue
        pos = defaultdict(list)
        for r in cs:
            cl = [c for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0 and c["value"]]
            s = str(r["value"])
            if len(cl) != len(s) or "0" in s[:-1] or r["value"] < 10:
                continue
            for i, c in enumerate(sorted(cl, key=lambda c: c["pos"])):
                pos[len(s) - 1 - i].append(c["pos"])
        h = {p: statistics.median(v) for p, v in pos.items() if len(v) >= 3}
        if len(h) < 2:
            continue
        ps = sorted(h)
        step = statistics.median(h[b] - h[a] for a, b in zip(ps[1:], ps) if a == b + 1) if len(ps) > 1 else None
        if not step or step <= 0:
            continue
        for r in cs:
            cl = sorted((c for c in r["clusters"] if c["pos"] is not None and c["pos"] >= 0 and c["value"]), key=lambda c: c["pos"])
            if len(cl) < 2:
                continue
            places = [len(str(c["value"])) - 1 for c in cl]
            if any(a <= b for a, b in zip(places, places[1:])) or places[0] < 1:
                continue  # clusters must read as distinct places, top cluster tens or higher
            if any(p not in h or abs(h[p] - c["pos"]) > 0.35 * step for p, c in zip(places[1:], cl[1:])):
                continue  # the lower clusters must sit at their own heights: only the top one is in question
            top = cl[0]
            p_read = places[0]
            if p_read not in h:
                continue
            # height of a place not seen on this khipu: extrapolate one step up from the highest seen
            cand = dict(h)
            top_seen = max(h)
            cand[top_seen + 1] = h[top_seen] - step
            p_h = min(cand, key=lambda p: abs(cand[p] - top["pos"]))
            if p_h == p_read or abs(cand[p_read] - top["pos"]) - abs(cand[p_h] - top["pos"]) < 0.3 * step:
                continue
            shift = p_h - p_read
            alt = r["value"] - (r["value"] - r["value"] % 10 ** p_read) + (r["value"] - r["value"] % 10 ** p_read) * 10 ** shift \
                if shift > 0 else None
            if alt is None:
                continue  # only "an empty place was missed" is judged here
            out.append({"khipu": k, "cord": r["order"], "okr_value": r["value"], "height_reading": alt,
                        "kfg_value": kfg.get((k, r["order"]), ""), "top_pos": top["pos"], "read_place": p_read,
                        "height_place": p_h, "place_heights": " ".join(f"{p}:{h[p]:.1f}" for p in sorted(h))})
    with open(ROOT / "extracted/place_heights.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    agree = sum(1 for o in out if str(o["kfg_value"]) == str(o["height_reading"]))
    same = sum(1 for o in out if str(o["kfg_value"]) == str(o["okr_value"]))
    print(f"flagged {len(out)} cords in {len(set(o['khipu'] for o in out))} khipus; KFG agrees with the height reading {agree}, "
          f"with OKR {same}; read place → height place: "
          + ", ".join(f"{a}→{b}: {n}" for (a, b), n in sorted(__import__('collections').Counter((o['read_place'], o['height_place']) for o in out).items())))


if __name__ == "__main__":
    main()
