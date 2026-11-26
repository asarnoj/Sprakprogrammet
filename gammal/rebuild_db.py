"""
River och återbygger databasen från setup.sql + queries.sql.

Kör med:  python rebuild_db.py

Regel: ändra ALDRIG databasen direkt. Alla ändringar görs i
setup.sql (schema) och queries.sql (data), sedan körs detta script.
"""

import sqlite3
import os

DB  = "ordbok/sprak.db"
SQL = ["setup.sql", "queries.sql"]

if os.path.exists(DB):
    os.remove(DB)
    print(f"  Tog bort {DB}")

db = sqlite3.connect(DB)

for fil in SQL:
    with open(fil, encoding="utf-8") as f:
        db.executescript(f.read())
    print(f"  Körde {fil}")

version = db.execute("PRAGMA user_version").fetchone()[0]
db.close()

print(f"\n  Databasen återbyggd (version {version}).")
