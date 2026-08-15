"""Håller `sprak.db` och `ordbok/former.tsv` ense — och larmar när de inte är det.

VARFÖR DEN HÄR FINNS. `sprak.db` är gitignorerad och `ordbok/former.tsv` är
sanningen: databasen ska när som helst kunna byggas om ur filen. Men
rättelser landar i DATABASEN — en LLM-granskning, en migrering, en handpåläggning
— och exporten tillbaka är ett eget steg som går att glömma. Glöms den lever
rättelsen bara i en fil som git inte ser, och nästa ombyggnad backar den tyst.

Det hade hänt, upptäckt 2026-08-15: nio svenska verb hade fått imperativen
åtskild från infinitiven i databasen (`äg` tempus=16, `äga` tempus=1) medan
filen fortfarande hade en enda rad som påstod sig vara båda (`äg` tempus=17).
Arton rader fanns bara i databasen, nio bara i filen, och ingenting sa ifrån.

Vad som skiljer den från `ögonblicksbild.py`: den jämför två TIDPUNKTER av
samma källa för att se vad en åtgärd gjorde. Den här jämför två KÄLLOR vid
samma tidpunkt för att se om de säger samma sak.

Kör:  python ordbok/verktyg/synk.py
"""
from __future__ import annotations

import collections
import csv
import sqlite3
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
TSV = ROT / "ordbok" / "former.tsv"
DB = ROT / "sprak.db"

#: Axelkolumnerna, i filens ordning. Formen ensam räcker inte som identitet —
#: samma sträng står ofta i flera celler, och det är precis de fallen som blir
#: fel när en rad påstår sig vara två celler.
AXLAR = ("numerus", "species", "kasus", "genus", "tempus", "grad", "person",
         "diates")


def ur_databasen(conn: sqlite3.Connection) -> collections.Counter:
    kol = ", ".join(f"f.{a}" for a in AXLAR)
    return collections.Counter(
        (r["nyckel"], r["språk"], r["lemma"], r["form"])
        + tuple(str(r[a] or "") for a in AXLAR)
        for r in conn.execute(
            f"""SELECT k.nyckel, l.språk, l.lemma, f.form, {kol}
                FROM Former f
                JOIN Lexem l ON l.id = f.lexem_id
                JOIN Koncept k ON k.id = l.koncept_id"""))


def ur_filen(sökväg: Path) -> collections.Counter:
    with sökväg.open(encoding="utf-8") as f:
        rader = list(csv.reader(f, delimiter="\t"))
    return collections.Counter(tuple(r[:4]) + tuple(r[4:12]) for r in rader[1:])


def main() -> int:
    if not DB.exists():
        print(f"{DB.name} finns inte — bygg den först.")
        return 1
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    db, fil = ur_databasen(conn), ur_filen(TSV)
    bara_db, bara_fil = db - fil, fil - db
    n_db, n_fil = sum(bara_db.values()), sum(bara_fil.values())

    print(f"sprak.db {sum(db.values())} rader, former.tsv {sum(fil.values())}")
    if not n_db and not n_fil:
        print("✓ Ense, rad för rad.")
        return 0

    print(f"\n{n_db} rader finns BARA i databasen, {n_fil} BARA i filen.\n"
          f"Filen är sanningen och databasen kan byggas om ur den — så det som\n"
          f"bara finns i databasen är en rättelse som aldrig exporterades, och\n"
          f"nästa ombyggnad backar den. Kör `ordbok exportera-former`.\n")
    for märke, rader in (("bara i db ", bara_db), ("bara i fil", bara_fil)):
        for rad in list(rader)[:8]:
            axlar = " ".join(f"{a}={v}" for a, v in zip(AXLAR, rad[4:]) if v)
            print(f"  {märke}  {rad[1]}/{rad[2]:14} {rad[3]:14} {axlar}")
        if len(rader) > 8:
            print(f"  {märke}  … och {len(rader) - 8} till")
    return 1


if __name__ == "__main__":
    sys.exit(main())
