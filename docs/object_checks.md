# Checks on the objects (Ethnologisches Museum, Berlin)

A short list of cords whose reading decides the results in the preprint
(`docs/preprint/preprint.pdf`). Cord numbers follow the Aschers' databook
(pendants numbered along the main cord; subsidiaries as `1s1`, `1s2` …). Values in brackets
are the published readings (Aschers / KFG / Urton). Every check is useful whatever the outcome.

## 1. AS125 (VA42670, Pachacamac) — totals carried on AS118

| Cord | Published | What to check | If … |
|---|---|---|---|
| 13 (group 4, first cord) | Aschers “?”, knots 3s(10.0); 1s(18.0); 1s(26.0); 1s(37.0); 1s(39.0); KFG 3130; Urton 31111; Chirinos 2010 3112 | Knot types and clusters in the lower (units) zone: one or two single knots? any long or figure-eight knot? | **3111** → group 4 = 8565 = AS118 subsidiary 1s5 exactly; 3112 → 8566; 3130 → 8584 (no match). |
| 8 (group 3, first cord) | Aschers “222?” (Chirinos 2010: 2222), knots 2s(9.5); 2s(18.0); 2s(27.5), broken at 29.5 cm | Is the tens cluster cut by the break? traces of further tens knots or of units below 29.5 cm? | tens cut → the value may have been 2298, and group 3 = 11522 = AS118 1s4. |
| 16 (single YB pendant, “group 5”) | no knots, 8.5 cm, broken | Any knot remains? | knots → a candidate for AS118 1s1 (2696). |

## 2. AS118 (VA42601, Pachacamac)

| Cord | Published | What to check |
|---|---|---|
| 1 and subsidiaries 1s1–1s5 | Aschers: cord 1 linked through the strands of the main cord; subsidiaries 2696, 13182, 14658, 11522, 8565 | Order of the subsidiaries (which is nearest the main cord); reading of 1s2 (13182; AS125 group 1 sums to 13676). |
| 2–8 (group 2) | Urton: “on a subsidiary main cord” | How the group is attached (tied-on piece?). |

## 3. AS175 (VA42518, Pachacamac) against the Huacho copy UR232

Part 3 of AS175 (groups 25–45, cords 120–224). Where AS175 and UR232 differ, the part-2 sums
of AS175 side with UR232 in five totals and with AS175 in one. Priority cords:

| Cord | Group, position | AS175 | UR232 | Why it matters |
|---|---|---|---|---|
| 132 | g27, 3 | 108 | 18 | total 335 (g24, pos. 3) needs 18 |
| 167 | g34, 3 | 30 (broken) | 32 | total 268 (g22, pos. 3) needs 32 |
| 125, 170 | g26, g35, 1 | 5, 6 | 3, 7 | total 108 (g23, pos. 1) needs 3 and 7 |
| 121, 126, 136, 141, 146, 151, 156, 171, 176, 186, 196, 201, 211, 216 | position 2 (LB pendants) | 4, 2, 7, 6, 7, 5, 10, 3, 4, 12, 10, 5, 40, 40 | 0, 1, 2, 1, 17, 0, 3, 0, 14, 11, 1, 0, 20, 20 | the part-2 totals 35 and 36 match only the UR232 column |
| 179, 224 | g36, g45, 5 | 18, 11 | 28, 21 | total 192 (g24, pos. 5) needs the AS175 values |

The full list of the 32 differing cords is produced by `khipu/huacho.py` and the snippet in
`docs/project_log_ru.md` (30.09.2026).

## 4. UR232 and UR233 (VA63038b, Huacho)

- The sixth (extra) pendant of each group: position 3 on UR233 (reported intact, knotless),
  position 4 on UR232 (dark MB:KB, 18 of 20 broken). Knot traces on the broken ones?
- The black (KB) subsidiaries on the first pendant of each group: 22 are stubs of 0.5–2.5 cm.
  Any knot traces? The intact ones read 25, 6, 7, 6, 0, as on AS175.
- The splice between the two primary cords: which ends are joined, and in which order the two
  khipus were joined (UR233 = part 1, UR232 = part 3).
- Radiocarbon: Cherkinsky and Urton (2014, p. 34) list VA63038 among the dated khipus. The
  date would show whether the Huacho copy is Inka or colonial.

## 5. AS149 / AS179 (VA44866C, VA47123)

No check needed: the Aschers' record of AS179 cord 3 is unambiguous, 3s(5.5); 4s(11.5); 2s(17.5);
4L(22.5) = 3424, and cord 2 (670) is broken at 28.0 cm, below its units zone. The AS179 lot
therefore differs from the four AS149 lots (3410) by 14 in position 3.

## Basel, Museum der Kulturen: IVc.366.03 (Huacho, Masarey 1910) against Berlin UR212 (VA42508(A)) and AS131 (VA42510)

- Six fragments on the cloth (OKR MM008, MM009, MM012, MM014, MM015, MM016) repeat runs of UR212 and AS131 (`khipu/basel_huacho.py`). Longest: MM015 cords 1–13 = UR212 cords 182–194 (reversed); MM016 cords 5–14 = UR212 139–148 (reversed); MM008 cords 16–22 = UR212 6–12.
- For each fragment: which end is the start of the primary cord (knotted loop or end knot), so that the fragment's orientation on the cloth can be fixed.
- Berlin: which end of UR212 and of AS131 is the start, as recorded by Urton and by the Aschers.
- MM015 cord 21 (4, W:GL) against AS131's seventh cord (knotless, NB:KB); MM008's 103 against UR212's 102; MM015's 212 with a subsidiary (88) against UR212's 212 without one.
- Were the Basel fragments cut from larger khipus (cut ends) or broken?
