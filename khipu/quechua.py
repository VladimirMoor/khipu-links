"""Похожи ли «знаки» кипу Уари на слоги кечуа? Грубое статистическое сравнение.

Кечуа: Википедия на кечуа (dumps.wikimedia.org, CC BY-SA; data/quechua/, не в git). Слова
статей только из букв алфавита кечуа и только с гласными a, i, u (отсекает испанские слова),
делим на графемы (ch, chh, ch', kh, k', ll, ph, p', qh, q', sh, th, t' …) и слоги (C)V(C):
одиночный согласный между гласными отходит к следующему слогу.
Уари: недесятичные шнуры кипу UR039, UR050–UR055, UR110, UR112 (signs.py) — «слог» = узел
(L5 …), «слово» = шнур (последовательность узлов).
Контроль: десятичные инкские шнуры — «слово» = значение шнура, «слог» = цифра разряда.
Сравнение при равном числе единиц N (подвыборки, 200 раз): число типов, энтропия (бит), доля 10
самых частых; и распределение длины «слова».
Вывод: extracted/quechua.txt.
"""
import bz2
import math
import random
import re
from collections import Counter
from pathlib import Path

import signs

ROOT = Path(__file__).resolve().parents[1]
DUMP = ROOT / "data/quechua/quwiki-latest-pages-articles.xml.bz2"
OUT = ROOT / "extracted/quechua.txt"
WARI = {"UR039", "UR050", "UR051", "UR052", "UR054", "UR055", "UR110", "UR112"}

CONS = ["chh", "ch'", "ch", "kh", "k'", "ph", "p'", "qh", "q'", "th", "t'", "ll", "sh",
        "h", "k", "l", "m", "n", "ñ", "p", "q", "r", "s", "t", "w", "y"]
VOW = "aiu"
WORD = re.compile(r"^[aiuchklmnñpqrstwy']+$")


def graphemes(w):
    out, i = [], 0
    while i < len(w):
        if w[i] in VOW:
            out.append(w[i])
            i += 1
            continue
        for c in CONS:
            if w.startswith(c, i):
                out.append(c)
                i += len(c)
                break
        else:
            return None
    return out


def syllables(w):
    g = graphemes(w)
    if not g or not any(x in VOW for x in g):
        return None
    syl, cur = [], []
    i = 0
    while i < len(g):
        cur.append(g[i])
        if g[i] in VOW:
            # согласные до следующей гласной: все, кроме последнего, остаются в этом слоге
            j = i + 1
            cons = []
            while j < len(g) and g[j] not in VOW:
                cons.append(g[j])
                j += 1
            if j == len(g):
                cur += cons
                syl.append("".join(cur))
                return syl
            cur += cons[:-1]
            syl.append("".join(cur))
            cur = [cons[-1]] if cons else []
            i = j
            continue
        i += 1
    if cur:
        syl.append("".join(cur))
    return syl


def quechua_words(limit=400000):
    text = bz2.open(DUMP, "rt", encoding="utf-8").read()
    body = re.findall(r"<ns>0</ns>.*?<text[^>]*>(.*?)</text>", text, flags=re.S)
    words = []
    for b in body:
        b = re.sub(r"\{\{.*?\}\}|\[\[[^\]|]*\||<[^>]+>|&[a-z]+;|https?://\S+", " ", b, flags=re.S)
        for w in re.findall(r"[A-Za-zÑñ']+", b):
            w = w.lower()
            if len(w) >= 2 and WORD.match(w) and not w.startswith("'"):
                s = syllables(w)
                if s:
                    words.append(s)
        if len(words) >= limit:
            break
    return words


def stats(units, N, rnd, reps=200):
    t = e = top = 0.0
    for _ in range(reps):
        s = rnd.sample(units, N) if len(units) > N else units
        c = Counter(s)
        t += len(c)
        e += -sum(v / len(s) * math.log2(v / len(s)) for v in c.values())
        top += sum(v for _, v in c.most_common(10)) / len(s)
    return t / reps, e / reps, top / reps


def main():
    rnd = random.Random(1)
    qw = quechua_words()
    q_syl = [s for w in qw for s in w]
    meta, cords = signs.load()
    inv = {k: i for k, (i, _) in meta.items()}
    wari_cords, dec_cords = [], []
    for cid, (kid, order, toks) in cords.items():
        k = signs.kind(toks)
        tt = [t for _, t in toks]
        if k == "недесятичный" and inv[kid] in WARI:
            wari_cords.append(tt)
        elif k == "десятичный" and inv[kid] not in WARI:
            dec_cords.append(tt)
    w_syl = [t for c in wari_cords for t in c]
    d_syl = [t for c in dec_cords for t in c]
    N = min(len(w_syl), 2000)
    lines = [f"кечуа: слов {len(qw)}, слогов {len(q_syl)}, разных слогов {len(set(q_syl))}; "
             f"Уари: шнуров {len(wari_cords)}, узлов {len(w_syl)}; десятичные инкские: шнуров {len(dec_cords)}",
             "", f"«слоги» (N = {N} в каждой подвыборке): типов / энтропия, бит / доля 10 частых"]
    for name, u in (("кечуа, слоги", q_syl), ("Уари, узлы", w_syl), ("инки, кластеры узлов (числа)", d_syl)):
        t, e, top = stats(u, N, rnd)
        lines.append(f"  {name:30} {t:6.1f} / {e:4.2f} / {top:.0%}")
    lines.append("  10 самых частых слогов кечуа: " + ", ".join(f"{s} {v}" for s, v in Counter(q_syl).most_common(10)))
    lines.append("  10 самых частых узлов Уари:   " + ", ".join(f"{s} {v}" for s, v in Counter(w_syl).most_common(10)))
    M = min(len(wari_cords), 800)
    lines += ["", f"«слова» (N = {M}): типов / энтропия / доля 10 частых"]
    for name, u in (("кечуа, слова", ["-".join(w) for w in qw]), ("Уари, шнуры", ["-".join(c) for c in wari_cords]),
                    ("инки, шнуры (числа)", ["-".join(c) for c in dec_cords])):
        t, e, top = stats(u, M, rnd)
        lines.append(f"  {name:30} {t:6.1f} / {e:4.2f} / {top:.0%}")
    lines += ["", "длина «слова» (слогов / узлов): доли 1, 2, 3, 4, 5+"]
    for name, u in (("кечуа", [len(w) for w in qw]), ("Уари", [len(c) for c in wari_cords]),
                    ("инки (числа)", [len(c) for c in dec_cords])):
        c = Counter(min(x, 5) for x in u)
        n = len(u)
        lines.append(f"  {name:14} " + "  ".join(f"{c[i] / n:.0%}" for i in range(1, 6)))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
