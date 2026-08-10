"""Databasanslutning och schemainitialisering.

Allt SQL-arbete går genom anslutningar härifrån. Övriga moduler
ska aldrig importera sqlite3 direkt.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

PROJEKTROT = Path(__file__).resolve().parents[2]
SCHEMA_FIL = PROJEKTROT / "setup.sql"
STANDARD_DB = PROJEKTROT / "sprak.db"


def anslut(db_sökväg: Path | None = None) -> sqlite3.Connection:
    """Returnerar en anslutning med foreign keys aktiverade."""
    sökväg = db_sökväg if db_sökväg is not None else STANDARD_DB
    conn = sqlite3.connect(sökväg, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Genereringen kan köras som ett jobb per språk samtidigt. Skrivningarna
    # är korta, men två jobb kan råka committa i samma ögonblick — vänta ut
    # låset i stället för att dö på "database is locked".
    conn.execute("PRAGMA busy_timeout = 60000")
    return conn


def initiera_schema(conn: sqlite3.Connection) -> None:
    """Kör setup.sql mot anslutningen. Antar tom databas."""
    sql = SCHEMA_FIL.read_text(encoding="utf-8")
    conn.executescript(sql)


def skapa_tom_databas(db_sökväg: Path | None = None) -> sqlite3.Connection:
    """Skapar en ny databas vid sökvägen och initialiserar schemat.

    Om filen redan finns raderas den först. Anropare ansvarar för
    att fråga användaren innan denna funktion anropas.
    """
    sökväg = db_sökväg if db_sökväg is not None else STANDARD_DB
    if sökväg.exists():
        sökväg.unlink()
    conn = anslut(sökväg)
    initiera_schema(conn)
    return conn
