"""Flytta en kurs ett dygn framåt. ETT PROVVERKTYG, inte en del av kursen.

En dag i kursen är ett dygn på klockan (5.1), och grinden öppnar nya nivåer en
gång per dygn (4.4). Att se vad dag fem gör skulle därför kräva att man väntade
till dag fem. Den här modulen flyttar kursen i stället.

VARFÖR DEN LIGGER I PAKETET. Logiken fanns först bara i `nästa_dag.py`, och
dagspasset behövde samma sak. Två kopior av en tidsflytt är värre än en: den
ena hade hunnit glömma en tabell. Modulen heter `simulering` för att ingen ska
kunna importera den av misstag och tro att det är en vanlig kursoperation.

DEN ÄR SPÄRRAD I BÅDA ANROPEN. `nästa_dag.py` är ett eget kommando man måste
skriva, och dagspasset visar valet bara när det startats med `--simulera`. Det
var skälet till att tiden först hölls utanför passet: en tidsmaskin man kan
råka trycka på i en riktig kurs är ett sätt att fuska utan att mena det. Att ha
valet bakom en flagga uppfyller samma skäl, och en kopia tas alltid först.

VARJE TIDSSTÄMPEL FLYTTAS BAKÅT, lika mycket. De två billigare varianterna är
båda fel: att bara ändra vilket datum som räknas som i dag är inte samma sak,
och att bara åldra införandena är sämre — FSRS räknar nästa repetition ur
MÖTETS tid (7.1), så lämnas mötena kvar i dag blir ingen repetition förfallen
och dagen får ingenting att göra. Flyttas allt lika mycket bevaras varje
intervall exakt, och kursen ser ut precis som den hade gjort om dygnet gått.

Det följer av samma flytt att dagens förbrukade källmeningar (villkor 8 i 6.1)
och dagens presenterade kort (5.2) hamnar i går, vilket är riktigt: en ny dag
har varken ställt eller presenterat något.
"""

from __future__ import annotations

import shutil
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
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
#: STÄMPLAR stannar flytten: en kurs där hälften av tiderna flyttats är värre
#: än en kurs som inte flyttats alls.
TIDSNAMN = {"tid", "dag", "öppnad", "skapad", "när", "tidpunkt"}


class OkändaStämplar(Exception):
    """Schemat bär en tidskolumn som STÄMPLAR inte känner till."""

    def __init__(self, kolumner: list[str]) -> None:
        self.kolumner = kolumner
        super().__init__(
            "kursens schema har tidskolumner som flytten inte känner till: "
            + ", ".join(kolumner)
            + ".\nLägg dem i STÄMPLAR (sprakprog/kurs/simulering.py) — en kurs "
              "där bara hälften av tiderna flyttats är värre än en oflyttad.")


def _bakåt(värde: str, dagar: int, sort: str) -> str:
    """Samma format, N dygn tidigare. SQLites `datetime()` duger inte — den
    tappar tidszonen och skriver om formatet."""
    if sort == "dygn":
        return (date.fromisoformat(värde) - timedelta(days=dagar)).isoformat()
    t = datetime.fromisoformat(värde) - timedelta(days=dagar)
    return t.isoformat(timespec="seconds")


def okända_stämplar(conn: sqlite3.Connection) -> list[str]:
    """Tidskolumner i schemat som flytten inte känner till."""
    kända = {(t, k) for t, k, _ in STÄMPLAR}
    ut = []
    for (tabell,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
        for rad in conn.execute(f'PRAGMA table_info("{tabell}")'):
            if rad[1] in TIDSNAMN and (tabell, rad[1]) not in kända:
                ut.append(f"{tabell}.{rad[1]}")
    return ut


def flytta_framåt(kurs: str | Path, dagar: int = 1,
                  rapport=None) -> tuple[int, Path]:
    """Flytta kursen `dagar` dygn framåt. Ger (antal stämplar, kopians väg).

    Tar en kopia av kursfilen först, och vägrar flytta en kurs vars schema har
    en tidskolumn som STÄMPLAR inte känner till (`OkändaStämplar`).
    """
    if dagar < 1:
        raise ValueError("dagar måste vara minst 1")
    fil = Path(kurs)
    if not fil.exists():
        raise FileNotFoundError(f"{fil} finns inte — starta passet en gång först")

    conn = sqlite3.connect(fil)
    okända = okända_stämplar(conn)
    if okända:
        raise OkändaStämplar(okända)

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
                         (_bakåt(värde, dagar, sort), rowid))
        if värden and rapport is not None:
            rapport(f"  {tabell}.{kolumn}: {len(värden)} rader")
        rader += len(värden)
    conn.commit()
    conn.close()
    return rader, kopia
