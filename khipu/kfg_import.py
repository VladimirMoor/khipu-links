"""KFG_DB.SQL (MySQL-дамп Khipu Field Guide, Zenodo 10.5281/zenodo.8125718) → data/kfg/kfg.db (SQLite)."""
import os
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/kfg/kfg_article/data/KFG_DB.SQL"
DST = ROOT / "data/kfg/kfg.db"


def mysql_to_sqlite_values(s):
    out, i, n, inq = [], 0, len(s), False
    while i < n:
        c = s[i]
        if inq:
            if c == "\\" and i + 1 < n:
                nx = s[i + 1]
                out.append({"'": "''", "n": "\n", "r": "\r", "t": "\t", "0": ""}.get(nx, nx))
                i += 2
                continue
            if c == "'":
                inq = False
        elif c == "'":
            inq = True
        out.append(c)
        i += 1
    return "".join(out)


def main():
    if DST.exists():
        os.remove(DST)
    con = sqlite3.connect(DST)
    sql = SRC.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"CREATE TABLE `(\w+)` \((.*?)\n\) ENGINE", sql, re.S):
        cols = []
        for name, typ in re.findall(r"`([^`]+)` (\w+)", m.group(2)):
            t = "INTEGER" if "int" in typ else "REAL" if typ in ("float", "double") else "TEXT"
            cols.append(f'"{name}" {t}')
        con.execute(f'CREATE TABLE "{m.group(1)}" ({", ".join(cols)})')
    for m in re.finditer(r"^INSERT INTO `(\w+)` VALUES (.*);$", sql, re.M):
        con.execute(f'INSERT INTO "{m.group(1)}" VALUES {mysql_to_sqlite_values(m.group(2))}')
    con.commit()
    for (t,) in con.execute("select name from sqlite_master where type='table'"):
        print(t, con.execute(f'select count(*) from "{t}"').fetchone()[0])


if __name__ == "__main__":
    main()
