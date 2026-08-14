"""Anslutning till inlärardatabasen.

Egen fil, eget schema, ingen delad anslutning med sprak.db. Att hålla dem
isär är hela poängen — se kort.sql.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

PROJEKTROT = Path(__file__).resolve().parents[3]
KORTSCHEMA = PROJEKTROT / "kort.sql"
STANDARD_KORT_DB = PROJEKTROT / "kort.db"


#: Kolumner som tillkommit efter att schemat först skrevs, som (tabell, namn,
#: definition). Inlärardatabasen kan aldrig byggas om — den innehåller
#: repetitionshistoriken — så schemaändringar måste vara ADDITIVA och gå att
#: köra om. Därför bara nya kolumner med förvalt värde, aldrig ändrade eller
#: borttagna. Behövs något annat är det en riktig migrering med datakopiering,
#: och den ska skrivas för hand och köras medvetet.
TILLÄGG = (
    ("Kurs", "meningar_per_dag", "INTEGER NOT NULL DEFAULT 20"),
    ("Repetition", "r_före", "REAL"),
    ("Mening", "sedda", "INTEGER"),
    ("Mening", "nya", "INTEGER"),
    ("Kurs", "cefr", "TEXT NOT NULL DEFAULT 'C2'"),
)


def _migrera(conn: sqlite3.Connection) -> None:
    for tabell, kolumn, definition in TILLÄGG:
        if not conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (tabell,)).fetchone():
            continue
        finns = {r["name"] for r in conn.execute(f"PRAGMA table_info({tabell})")}
        if kolumn not in finns:
            conn.execute(f"ALTER TABLE {tabell} ADD COLUMN {kolumn} {definition}")
            conn.commit()


def anslut_kort(sökväg: Path | None = None, *,
                delad_mellan_trådar: bool = False) -> sqlite3.Connection:
    """Se `sprakprog.db.anslut` för vad `delad_mellan_trådar` innebär."""
    conn = sqlite3.connect(sökväg or STANDARD_KORT_DB, timeout=60,
                           check_same_thread=not delad_mellan_trådar)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 60000")
    _migrera(conn)
    return conn


def skapa_kortdatabas(sökväg: Path | None = None) -> sqlite3.Connection:
    """Ny, tom inlärardatabas. Raderar en befintlig fil.

    Anroparen ansvarar för att fråga användaren först — det här kastar bort
    repetitionshistorik, det enda i systemet som inte går att återskapa.
    """
    mål = sökväg or STANDARD_KORT_DB
    mål.unlink(missing_ok=True)
    Path(str(mål) + "-wal").unlink(missing_ok=True)
    Path(str(mål) + "-shm").unlink(missing_ok=True)
    conn = anslut_kort(mål)
    conn.executescript(KORTSCHEMA.read_text(encoding="utf-8"))
    conn.commit()
    return conn
