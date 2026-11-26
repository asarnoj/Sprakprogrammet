"""Flytta en kurs ett dygn framåt, för att kunna prova flera dagar i rad.

    python ordbok/verktyg/nästa_dag.py [--kurs FIL] [--dagar N]

En dag i kursen är ett dygn på klockan (5.1), och grinden öppnar nya nivåer en
gång per dygn (4.4). Att prova fem dagar tar därför fem dagar — om man inte
flyttar kursen.

VARJE TIDSSTÄMPEL FLYTTAS BAKÅT, lika mycket. Att i stället bara ändra vilket
datum som räknas som i dag vore inte samma sak, och att bara åldra införandena
vore sämre: FSRS räknar nästa repetition ur MÖTETS tid (7.1), så lämnas mötena
kvar i dag blir ingen repetition förfallen och dagen får inget att göra.
Flyttas allt lika mycket bevaras varje intervall exakt, och kursen ser ut precis
som den hade gjort om dygnet hade gått.

Det följer av samma flytt att dagens förbrukade källmeningar (villkor 8 i 6.1)
och dagens presenterade kort (5.2) hamnar i går, vilket är riktigt: en ny dag
har varken ställt något eller presenterat något.

VERKTYGET ÄR TILL FÖR ATT PROVA, och det skriver i kursen. Därför tas en kopia
först. Ingenting i passet självt kan flytta tiden — en tidsmaskin i programmet
vore ett sätt att råka fuska i en riktig kurs.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
SÄKERHETSKOPIOR = ROT / "säkerhetskopior"

#: (tabell, kolumn, sort). Hela mängden tidsstämplar i kursens schema.
#: «stund» är ISO-8601 med tidszon, «dygn» ett datum.
STÄMPLAR = [
    ("kurs", "skapad", "stund"),
    ("mening", "tid", "stund"),
    ("möte", "tid", "stund"),
    ("presenterat", "tid", "stund"),
    ("infört", "tid", "stund"),
    ("nivå", "öppnad", "stund"),
    ("tilldelning", "dag", "dygn"),
    ("tempo", "dag", "dygn"),
    ("bevis", "tid", "stund"),
    ("karantän", "tid", "stund"),
    ("felrapport", "tid", "stund"),
]

#: Kolumnnamn som bär en tidpunkt. Finns ett sådant i schemat som inte står i
#: STÄMPLAR stannar verktyget: en kurs där hälften av tiderna flyttats är värre
#: än en kurs som inte flyttats alls.
TIDSNAMN = {"tid", "dag", "öppnad", "skapad", "när", "tidpunkt"}


def _bakåt(värde: str, dagar: int, sort: str) -> str:
    """Samma format, N dygn tidigare. SQLites `datetime()` duger inte — den
    tappar tidszonen och skriver om formatet."""
    if sort == "dygn":
        return (date.fromisoformat(värde) - timedelta(days=dagar)).isoformat()
    t = datetime.fromisoformat(värde) - timedelta(days=dagar)
    return t.isoformat(timespec="seconds")


def _okända(conn: sqlite3.Connection) -> list[str]:
    """Tidskolumner i schemat som verktyget inte känner till."""
    kända = {(t, k) for t, k, _ in STÄMPLAR}
    ut = []
    for (tabell,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
        for rad in conn.execute(f'PRAGMA table_info("{tabell}")'):
            if rad[1] in TIDSNAMN and (tabell, rad[1]) not in kända:
                ut.append(f"{tabell}.{rad[1]}")
    return ut


def main() -> int:
    p = argparse.ArgumentParser(description="Flytta kursen ett dygn framåt.")
    p.add_argument("--kurs", default=str(ROT / "kurs.db"))
    p.add_argument("--dagar", type=int, default=1,
                   help="hur många dygn kursen ska flyttas framåt (1)")
    a = p.parse_args()
    if a.dagar < 1:
        p.error("--dagar måste vara minst 1")
    fil = Path(a.kurs)
    if not fil.exists():
        p.error(f"{fil} finns inte — starta passet en gång först")

    conn = sqlite3.connect(fil)
    okända = _okända(conn)
    if okända:
        print(f"{fil}: schemat har tidskolumner verktyget inte känner till: "
              f"{', '.join(okända)}.\nLägg dem i STÄMPLAR — en kurs där bara "
              f"hälften av tiderna flyttats är värre än en oflyttad.",
              file=sys.stderr)
        return 1

    SÄKERHETSKOPIOR.mkdir(exist_ok=True)
    kopia = SÄKERHETSKOPIOR / f"{fil.name}.{datetime.now():%Y-%m-%dT%H%M%S}.före-flytt"
    shutil.copy2(fil, kopia)

    rader = 0
    for tabell, kolumn, sort in STÄMPLAR:
        värden = conn.execute(
            f'SELECT rowid, "{kolumn}" FROM "{tabell}" '
            f'WHERE "{kolumn}" IS NOT NULL').fetchall()
        for rowid, värde in värden:
            conn.execute(f'UPDATE "{tabell}" SET "{kolumn}" = ? WHERE rowid = ?',
                         (_bakåt(värde, a.dagar, sort), rowid))
        if värden:
            print(f"  {tabell}.{kolumn}: {len(värden)} rader")
        rader += len(värden)
    conn.commit()

    print(f"\n{fil.name} flyttad {a.dagar} dygn framåt ({rader} tidsstämplar).")
    print(f"Kopia före flytten: {kopia.relative_to(ROT)}")
    print("Starta passet och tryck n — nya nivåer är öppna.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
