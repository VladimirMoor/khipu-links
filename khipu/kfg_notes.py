"""Заметки для Khipu Field Guide: одна строка на пару (кипу, связь), с кодом KFG, текстом и ссылкой.

Источник — atlas/curated/links.csv и findings.json; только связи, найденные в этой работе (finding ≠ known);
для пар, известных раньше (Urton & Chu 2015 и др.), заметка говорит, что добавлено здесь, и называет первоисточник.
Вывод: report/kfg_notes.csv (kfg_code, khipu, other_khipu, kfg_other, note, reference).
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/kfg_notes.csv"
SEC = {"berlin": "3.1", "huacho1": "3.2", "as118": "3.3", "basel": "3.4", "frame14": "3.5", "inkawasi": "3.6",
       "ur269": "3.7", "as003": "3.8", "folded": "3.9", "dumbarton": "3.10", "ica109": "3.11"}
PRIOR = {("UR267A", "UR255"): "pairing: Urton & Chu 2015", ("UR267B", "UR256"): "pairing: Urton & Chu 2015",
         ("UR266", "UR275"): "pairing: Urton & Chu 2015"}
ATLAS = "https://khipu-links.vercel.app/#finding-"
PAPER = "Muravev 2026, Accounts across khipus (preprint v4, https://github.com/VladimirMoor/khipu-links)"


def main():
    D = json.load(open(ROOT / "site/data.json"))
    K = {k["id"]: k for k in D["khipus"]}
    kfg = {}
    for r in csv.DictReader(open(ROOT / "atlas/curated/kfg_names.csv")):
        if r["khipu"]:
            kfg[r["khipu"]] = r["kfg"]
    for k in K.values():
        if k.get("okr") and k["id"] not in kfg:
            kfg[k["id"]] = k["okr"]
    nm = lambda x: K[x]["alias"] if x in K and K[x].get("alias") else x
    rows = []
    for r in csv.DictReader(open(ROOT / "atlas/curated/links.csv")):
        if r["finding"] == "known":
            continue
        a, b, f = r["from"], r["to"], r["finding"]
        ref = f"{PAPER}, §{SEC.get(f, '')}; {ATLAS}{f}"
        prior = PRIOR.get((a, b))
        note = r["note"] + (f" ({prior}; added here: {'empty net slots on UR255 in the first 12 deposits, filled in 5 of the last 6' if b == 'UR255' else 'order and arithmetic of the shared records'})" if prior else "")
        for x, y in ((a, b), (b, a)):
            rows.append({"kfg_code": kfg.get(x, ""), "khipu": nm(x), "other_khipu": nm(y), "kfg_other": kfg.get(y, ""),
                         "note": f"Linked to {nm(y)} ({r['type']}): {note}.", "reference": ref})
    for k, n in (("UR212", "14 main groups divided 7 + 7 by a single knotless cord"), ("UR1131", "14 main groups divided 7 + 7 by a larger space"),
                 ("AS170", "14 main groups divided 7 + 7 by a marker"), ("UR199", "14 main groups")):
        rows.append({"kfg_code": kfg.get(k, ""), "khipu": nm(k), "other_khipu": "", "kfg_other": "",
                     "note": f"{n}; one of four fourteen-unit khipus in Gretzer's Berlin 'Pachacamac' batch (suggestive).",
                     "reference": f"{PAPER}, §3.5; {ATLAS}frame14"})
    for k in ("UR297", "UR298"):
        rows.append({"kfg_code": kfg.get(k, ""), "khipu": k, "other_khipu": "", "kfg_other": "",
                     "note": "Transcribed from Urton's record sheets (OKR scans); 74 of Urton's 78 group totals agree with the transcription.",
                     "reference": f"{PAPER}, §3.10; {ATLAS}dumbarton"})
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    miss = sorted({r["khipu"] for r in rows if not r["kfg_code"]})
    print(f"kfg_notes.csv: {len(rows)} rows, {len({r['khipu'] for r in rows})} khipus; without KFG code: {miss}")


if __name__ == "__main__":
    main()
