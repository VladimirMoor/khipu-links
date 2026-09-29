"""Документы с повторяющейся структурой → матрицы «строки × категории».

None — категория в строке отсутствует (в документе не названа).
Каждый шаблон собирается из extracted/*.csv по явным правилам ниже; правила
подобраны вручную под конкретный документ (см. комментарии).
"""
import csv
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "extracted"


def rows_of(fname, doc_id):
    with open(EX / fname) as f:
        return [r for r in csv.DictReader(f) if r["doc_id"] == doc_id]


def num(r):
    try:
        return float(r["quantity"])
    except ValueError:
        return None


def j1j():
    """Хауха 1570, партии расходов 12 принсипалов (J1.j).
    Категории: партии коки, корзины коки, партии одежды, партии скота, головы скота.
    Куски одежды не берём: половинные значения (9½) на кипу неочевидны."""
    cats = ["coca_partidas", "coca_cestos", "ropa_partidas", "ganado_partidas", "ganado"]
    rows = OrderedDict()
    for r in rows_of("J1.csv", "J1.j"):
        if r["level"] == "total":
            continue
        it = r["item"].lower()
        if "partidas" in it:
            c = ("coca_partidas" if "coca" in it else "ropa_partidas" if "ropa" in it
                 else "ganado_partidas")
        elif "coca" in it:
            c = "coca_cestos"
        elif any(w in it for w in ("carnero", "oveja", "ganado")):
            c = "ganado"
        else:
            continue
        rows.setdefault(r["section"], {})[c] = num(r)
    return cats, [[d.get(c) for c in cats] for d in rows.values()], list(rows)


def c4a():
    """Гуанчак 1606–1613, по годам (C4.a): урожай маиса, десятина(+примисии), соль,
    и урожай Учуйгуанчака того же года."""
    cats = ["maiz", "diezmo", "sal", "uchuy"]
    years = OrderedDict((i, {}) for i in range(1, 9))
    order = ["1er", "2º", "3er", "4º", "5º", "6º", "7º", "8º"]
    for r in rows_of("C4.csv", "C4.a"):
        sec, it = r["section"], r["item"].lower()
        if sec.startswith("Guanchac"):
            y = next((i + 1 for i, t in enumerate(order) if t in sec), None)
            if y is None:
                continue
            if "cogido" in it:
                years[y]["maiz"] = num(r)
            elif "diezmo" in it:
                years[y]["diezmo"] = (years[y].get("diezmo") or 0) + num(r)
            elif "primicia" in it:
                years[y]["diezmo"] = (years[y].get("diezmo") or 0) + num(r)
            elif it.startswith("sal"):
                years[y]["sal"] = num(r)
        elif sec.startswith("Uchuyguanchac — año"):
            years[int(sec.split()[-1])]["uchuy"] = num(r)
    return cats, [[d.get(c) for c in cats] for d in years.values()], [f"año {y}" for y in years]


def herds(fname, doc_id):
    """Тульпо 1611 (C6.j): стадо = строка, закрывается строкой «cabezas de la manada».
    Категории: матки, производители, приплод, итог стада. Сводные строки («resumen»,
    общий итог) и не-овечьи блоки пропускаем. Прочие таблицы Тульпо (C6.k–o) не берём:
    границы стад в них не размечены, а наборы категорий от стада к стаду разные."""
    cats = ["madres", "padres", "crias", "total"]
    out, cur = [], {}
    for r in rows_of(fname, doc_id):
        sec, it = r["section"].lower(), r["item"].lower()
        if "ovejuno" not in sec or "resumen" in sec or r["level"] == "total":
            continue
        v = num(r)
        if v is None:
            continue
        if r["level"] == "subtotal" and "manada" in it:
            cur["total"] = v
            out.append(cur)
            cur = {}
        elif "madres" in it or "de vientre" in it:
            cur["madres"] = v
        elif "padres" in it:
            cur["padres"] = cur.get("padres", 0) + v
        elif any(w in it for w in ("corder", "borreg")):
            cur["crias"] = cur.get("crias", 0) + v
    return cats, [[d.get(c) for c in cats] for d in out], [f"стадо {i+1}" for i in range(len(out))]


def c1b():
    """Лукана 1581, карнеро по третям (C1.b): натурой и серебром; 6 третей."""
    cats = ["especie", "plata"]
    names = ["primer", "segundo", "tercer", "cuarto", "quinto", "sexto"]
    t = OrderedDict((n, {}) for n in names)
    for r in rows_of("C1.csv", "C1.b"):
        it = r["item"].lower()
        n = next((x for x in names if x in it), None)
        if not n:
            continue
        if "espec" in it:
            t[n]["especie"] = num(r)
        elif "plata" in it:
            t[n]["plata"] = num(r)
        elif "pagados" in it and "sexto" not in it:
            t[n]["plata"] = num(r)
        elif "pagados" in it:
            t[n]["plata"] = num(r)
    return cats, [[d.get(c) for c in cats] for d in t.values()], names


def s1_ayllus():
    """Сисикая 1588 (S1): 10 айлью × податные, старики/освобождённые, мальчики,
    женщины (взрослые + вдовы), девочки. Дом касика не берём (одна семья)."""
    cats = ["tributarios", "viejos", "muchachos", "mujeres", "muchachas"]
    out, labels = [], []
    with open(EX / "S1_ayllus.csv") as f:
        for r in csv.DictReader(f):
            a = r["ayllu"]
            if a.startswith("(") or a.upper() == "TOTAL":
                continue
            g = lambda k: float(r[k] or 0)
            out.append([g("tributarios"), g("viejos_reservados"), g("muchachos"),
                        g("mujeres_adultas") + g("viudas"), g("muchachas")])
            labels.append(a)
    return cats, out, labels


TEMPLATES = {
    "S1 Сисикая 1588: 10 айлью": s1_ayllus,
    "J1.j Хауха 1570: 12 принсипалов": j1j,
    "C4.a Гуанчак 8 лет": c4a,
    "C6.j Тульпо 1611 стада": lambda: herds("C6.csv", "C6.j"),
    "C1.b Лукана 1581 трети": c1b,
}

if __name__ == "__main__":
    for name, f in TEMPLATES.items():
        cats, m, labels = f()
        filled = sum(1 for row in m for x in row if x is not None)
        print(f"== {name}: {len(m)}×{len(cats)} ({filled} клеток) {cats}")
        for lab, row in zip(labels, m):
            print(f"   {lab[:28]:28} " + " ".join(f"{x:>7g}" if x is not None else "      ·" for x in row))
