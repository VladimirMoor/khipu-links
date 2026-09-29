"""Одиночные шнуры между группами — итоги соседей? И устойчивость к разбивке на группы.

1. Для каждой «одиночной» группы (1 подвесной, значение ≥ MINV) в кипу проверяем: равно ли её
   значение сумме предыдущей группы, следующей, двух предыдущих, двух следующих, предыдущей +
   следующей (свои значения подвесных). Фон — значение ± d (d = 1…20). Вывод по видам.
2. Перегруппировка: одиночную группу присоединяем к следующей (как «заголовок») — и заново
   ищем точные векторные суммы между кипу (vecsum) — появляется ли что-то новое?
Вывод: extracted/singletons.txt.
"""
import itertools
from collections import Counter
from pathlib import Path

import vecsum

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extracted/singletons.txt"
MINV = 100


def kinds(gs, i):
    s = [sum(g) for g in gs]
    out = {}
    if i >= 1:
        out["пред."] = s[i - 1]
    if i + 1 < len(gs):
        out["след."] = s[i + 1]
    if i >= 2:
        out["2 пред."] = s[i - 1] + s[i - 2]
    if i + 2 < len(gs):
        out["2 след."] = s[i + 1] + s[i + 2]
    if 1 <= i < len(gs) - 1:
        out["пред.+след."] = s[i - 1] + s[i + 1]
    return out


def main():
    G = vecsum.load()
    real, null, n = Counter(), Counter(), 0
    hits = []
    for k, gs in G.items():
        for i, g in enumerate(gs):
            if len(g) != 1 or g[0] < MINV:
                continue
            n += 1
            for kind, v in kinds(gs, i).items():
                if len(gs[i - 1 if "пред" in kind else i + 1]) < 2:
                    continue
                if v == g[0]:
                    real[kind] += 1
                    hits.append((k, i + 1, g[0], kind))
                null[kind] += sum(1 for d in range(-20, 21) if d and v == g[0] + d) / 40
    lines = [f"одиночных групп со значением ≥ {MINV}: {n}", "вид: реально / фон (значение ± d, среднее на один d)"]
    for kind in ("пред.", "след.", "2 пред.", "2 след.", "пред.+след."):
        lines.append(f"  {kind:12} {real[kind]:4} / {null[kind]:5.2f}")
    lines += ["", "совпадения:"] + [f"  {k} г{i} = {v} = {kind}" for k, i, v, kind in hits]

    # 2. перегруппировка: одиночная группа присоединяется к следующей
    def regroup(gs):
        out, carry = [], []
        for g in gs:
            if len(g) == 1:
                carry += g
            else:
                out.append(carry + g)
                carry = []
        if carry:
            out.append(carry)
        return out

    vecsum.load = lambda G=G: {k: regroup(gs) for k, gs in G.items()}
    lines.append("")
    lines.append("перегруппировка (одиночные шнуры присоединены к следующей группе), vecsum:")
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        vecsum.OUT = ROOT / "extracted/vecsum_regroup.txt"
        vecsum.main()
    lines += ["  " + l for l in buf.getvalue().splitlines()[:6]]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
