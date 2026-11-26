"""Kursdata — steg 3b i kärnans byggordning (KÄRNAN 5.2 och punkt 9).

Inlärardatan ligger skild från språkdatabasen, i en egen fil per maskin: en
ombyggd `sprak.db` ska kunna mötas av en orörd kursdatabas.

VAD SOM LAGRAS är det mätta och det valda (5.2): mötena med diffens och
användarens betyg, meningarna och svaren, vilka kort som presenterats och
införts, öppnade nivåer och vilken nivå som öppnade varje kort, dagens
tilldelning av nya kort, sparat tempo, bevisen (3.10), karantänen,
felrapporterna och inställningarna.

VAD SOM RÄKNAS FRAM och därför inte lagras: förfallodagar, R, FSRS-tillstånd och
fönstren (5.2, 7.6). De följer av mötena, och mötena är det enda som mäts. Ett
lagrat tillstånd hade kunnat glida isär från loggen, och loggen är facit.

DYGNET börjar 04:00 i användarens lokala tid (5.1), vilket är en inställning.
Tiderna lagras som de mättes, i UTC; vilken dag ett möte hör till räknas fram med
gränsen, så att en ändrad gräns inte skriver om historien.

Paketet hör till den nya kärnan och importerar inget ur den gamla (`kort`,
`generator`).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from ..kortmodell import Kort

#: Förvalen (R6): varje tal användaren kan välja står här, inget i koden.
FÖRVAL = {
    "dygnsgräns": "04:00",      # när ett nytt dygn börjar, lokal tid (5.1)
    "tid_per_dag": "20",        # minuter, tidsratten (5.5, 5.7)
    "svårighet": "0.10",        # τ i budgeten, svårighetsratten (5.7)
    "retention": "0.90",        # retentionsmålet i FSRS, som ger fönstret (7.6)
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS kurs (
    id          INTEGER PRIMARY KEY,
    källspråk   TEXT NOT NULL,
    målspråk    TEXT NOT NULL,
    skapad      TEXT NOT NULL,
    UNIQUE (källspråk, målspråk)
);

CREATE TABLE IF NOT EXISTS inställning (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    namn        TEXT NOT NULL,
    värde       TEXT NOT NULL,
    PRIMARY KEY (kurs_id, namn)
);

-- En ställd uppgift: meningen som visades och svaret som gavs. `spec` är
-- meningsspecifikationen, så att meningen går att rendera om (7.2).
CREATE TABLE IF NOT EXISTS mening (
    id          INTEGER PRIMARY KEY,
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    tid         TEXT NOT NULL,
    fas         TEXT NOT NULL,          -- intro · mening · ensam (5.1, 6.3)
    spec        TEXT NOT NULL,
    källtext    TEXT NOT NULL,
    facit       TEXT NOT NULL,          -- de godtagna varianterna, JSON (6.5)
    svar        TEXT,
    sekunder    REAL                    -- svarstiden, för tidsmodellen (5.5)
);

-- Varje möte bokförs (7.1). Introfasen bokför ingenting (5.4).
CREATE TABLE IF NOT EXISTS möte (
    id          INTEGER PRIMARY KEY,
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    mening_id   INTEGER REFERENCES mening(id),
    tid         TEXT NOT NULL,
    språk       TEXT NOT NULL,
    typ         TEXT NOT NULL,
    nyckel      TEXT NOT NULL,
    mål         INTEGER NOT NULL,       -- var kortet ett av meningens mål?
    betyg_diff  TEXT NOT NULL,          -- again · good, räknat ur diffen (7.2)
    betyg       TEXT NOT NULL           -- det användaren lämnade till FSRS (7.2)
);

CREATE TABLE IF NOT EXISTS presenterat (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    språk       TEXT NOT NULL, typ TEXT NOT NULL, nyckel TEXT NOT NULL,
    tid         TEXT NOT NULL,
    PRIMARY KEY (kurs_id, språk, typ, nyckel, tid)
);

CREATE TABLE IF NOT EXISTS infört (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    språk       TEXT NOT NULL, typ TEXT NOT NULL, nyckel TEXT NOT NULL,
    tid         TEXT NOT NULL,
    mening_id   INTEGER REFERENCES mening(id),
    PRIMARY KEY (kurs_id, språk, typ, nyckel)
);

CREATE TABLE IF NOT EXISTS nivå (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    nummer      INTEGER NOT NULL,
    öppnad      TEXT NOT NULL,
    PRIMARY KEY (kurs_id, nummer)
);

-- Vilken nivå som låste upp kortet (4.5): upplåst är inte infört.
CREATE TABLE IF NOT EXISTS kortnivå (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    språk       TEXT NOT NULL, typ TEXT NOT NULL, nyckel TEXT NOT NULL,
    nummer      INTEGER NOT NULL,
    PRIMARY KEY (kurs_id, språk, typ, nyckel)
);

-- Dagens nya kort, valda innan passet börjar (5.1).
CREATE TABLE IF NOT EXISTS tilldelning (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    dag         TEXT NOT NULL,
    språk       TEXT NOT NULL, typ TEXT NOT NULL, nyckel TEXT NOT NULL,
    PRIMARY KEY (kurs_id, dag, språk, typ, nyckel)
);

-- Tempot (5.5): dagens antal nya kort och det som inte användes.
CREATE TABLE IF NOT EXISTS tempo (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    dag         TEXT NOT NULL,
    nya         INTEGER NOT NULL,
    sparat      REAL NOT NULL,
    PRIMARY KEY (kurs_id, dag)
);

-- Bevismeningen för ett prövbart kort (3.10), så att kontrollen inte görs om.
CREATE TABLE IF NOT EXISTS bevis (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    språk       TEXT NOT NULL, typ TEXT NOT NULL, nyckel TEXT NOT NULL,
    spec        TEXT NOT NULL,
    tid         TEXT NOT NULL,
    PRIMARY KEY (kurs_id, språk, typ, nyckel)
);

CREATE TABLE IF NOT EXISTS karantän (
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    språk       TEXT NOT NULL, typ TEXT NOT NULL, nyckel TEXT NOT NULL,
    orsak       TEXT NOT NULL,
    tid         TEXT NOT NULL,
    PRIMARY KEY (kurs_id, språk, typ, nyckel)
);

-- Användarens flagga på facit (7.2), till granskningen av datan (3.4).
CREATE TABLE IF NOT EXISTS felrapport (
    id          INTEGER PRIMARY KEY,
    kurs_id     INTEGER NOT NULL REFERENCES kurs(id),
    mening_id   INTEGER REFERENCES mening(id),
    språk       TEXT, typ TEXT, nyckel TEXT,
    text        TEXT NOT NULL,
    tid         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS möte_kort ON möte (kurs_id, språk, typ, nyckel, tid);
CREATE INDEX IF NOT EXISTS möte_tid ON möte (kurs_id, tid);
"""


def nu() -> str:
    """Tiden som den mäts: UTC med tidszon."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dygnet(tid: str, gräns: str) -> str:
    """Vilket dygn en tidpunkt hör till, med dygnsgränsen i lokal tid (5.1)."""
    t, h = datetime.fromisoformat(tid).astimezone(), time.fromisoformat(gräns)
    return (t - timedelta(hours=h.hour, minutes=h.minute)).date().isoformat()


@dataclass(frozen=True, slots=True)
class Möte:
    """Ett bokfört möte med ett kort (7.1)."""
    kort: Kort
    tid: str
    mål: bool
    betyg_diff: str
    betyg: str
    mening_id: int | None


def _kolumner(kort: Kort) -> tuple:
    return kort.språk, kort.typ, json.dumps(list(kort.nyckel), ensure_ascii=False)


def _kort(rad) -> Kort:
    return Kort(rad["språk"], rad["typ"], tuple(json.loads(rad["nyckel"])))


class Kursdata:
    """En kurs inlärardata: ett språkpar och allt som mätts och valts i den."""

    def __init__(self, conn: sqlite3.Connection, källspråk: str, målspråk: str) -> None:
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        self.conn = conn
        rad = conn.execute(
            "SELECT id FROM kurs WHERE källspråk = ? AND målspråk = ?",
            (källspråk, målspråk)).fetchone()
        if rad is None:
            conn.execute("INSERT INTO kurs (källspråk, målspråk, skapad) VALUES (?, ?, ?)",
                         (källspråk, målspråk, nu()))
            conn.commit()
            rad = conn.execute("SELECT id FROM kurs WHERE källspråk = ? AND målspråk = ?",
                               (källspråk, målspråk)).fetchone()
        self.id, self.källspråk, self.målspråk = rad["id"], källspråk, målspråk

    # ── inställningarna (R6) ──

    def inställning(self, namn: str) -> str:
        rad = self.conn.execute(
            "SELECT värde FROM inställning WHERE kurs_id = ? AND namn = ?",
            (self.id, namn)).fetchone()
        return rad["värde"] if rad else FÖRVAL[namn]

    def ställ_in(self, namn: str, värde: str) -> None:
        if namn not in FÖRVAL:
            raise KeyError(f"okänd inställning: {namn!r}")
        self.conn.execute(
            "INSERT INTO inställning (kurs_id, namn, värde) VALUES (?, ?, ?) "
            "ON CONFLICT (kurs_id, namn) DO UPDATE SET värde = excluded.värde",
            (self.id, namn, värde))
        self.conn.commit()

    def dag(self, tid: str | None = None) -> str:
        """Dygnet en tidpunkt hör till; utan tid: dygnet just nu."""
        return dygnet(tid or nu(), self.inställning("dygnsgräns"))

    # ── meningarna och mötena ──

    def ny_mening(self, fas: str, spec: str, källtext: str, facit: list[str]) -> int:
        """Uppgiften som ställdes. Ger meningens id, som mötena hänger på."""
        rad = self.conn.execute(
            "INSERT INTO mening (kurs_id, tid, fas, spec, källtext, facit) "
            "VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
            (self.id, nu(), fas, spec, källtext,
             json.dumps(facit, ensure_ascii=False))).fetchone()
        self.conn.commit()
        return rad["id"]

    def dagens_källtexter(self) -> set[str]:
        """Källmeningarna som redan ställts i dag (KÄRNAN 6.1 punkt 8).

        Efter ett fel har användaren sett facit, och samma fråga igen mäter
        minnet av facit i stället för kortet. En annan dag gäller inte
        villkoret, så frågan är avgränsad till dygnet (5.1).
        """
        dag = self.dag()
        return {r["källtext"] for r in self.conn.execute(
            "SELECT tid, källtext FROM mening WHERE kurs_id = ?", (self.id,))
            if self.dag(r["tid"]) == dag}

    def svara(self, mening_id: int, svar: str, sekunder: float) -> None:
        self.conn.execute("UPDATE mening SET svar = ?, sekunder = ? WHERE id = ?",
                          (svar, sekunder, mening_id))
        self.conn.commit()

    def bokför(self, kort: Kort, *, mål: bool, betyg_diff: str, betyg: str,
               mening_id: int | None = None) -> None:
        """Ett möte (7.1). `betyg_diff` är mätt ur diffen, `betyg` är användarens
        efter omrättningen — båda sparas, och FSRS får användarens (7.2)."""
        self.conn.execute(
            "INSERT INTO möte (kurs_id, mening_id, tid, språk, typ, nyckel, mål, "
            "betyg_diff, betyg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.id, mening_id, nu(), *_kolumner(kort), int(mål), betyg_diff, betyg))
        self.conn.commit()

    def möten(self, kort: Kort | None = None) -> list[Möte]:
        """Mötena i tidsordning, för ett kort eller för hela kursen."""
        villkor, argument = "kurs_id = ?", [self.id]
        if kort is not None:
            villkor += " AND språk = ? AND typ = ? AND nyckel = ?"
            argument += list(_kolumner(kort))
        return [Möte(_kort(r), r["tid"], bool(r["mål"]), r["betyg_diff"], r["betyg"],
                     r["mening_id"])
                for r in self.conn.execute(
                    f"SELECT * FROM möte WHERE {villkor} ORDER BY tid, id", argument)]

    # ── kortens läge i kursen ──

    def presentera(self, kort: Kort) -> None:
        """Kortet har klarat introövningen och får användas i dagens meningar (5.1)."""
        self.conn.execute(
            "INSERT OR IGNORE INTO presenterat (kurs_id, språk, typ, nyckel, tid) "
            "VALUES (?, ?, ?, ?, ?)", (self.id, *_kolumner(kort), nu()))
        self.conn.commit()

    def presenterade(self, dag: str | None = None) -> set[Kort]:
        dag = dag or self.dag()
        gräns = self.inställning("dygnsgräns")
        return {_kort(r) for r in self.conn.execute(
            "SELECT * FROM presenterat WHERE kurs_id = ?", (self.id,))
            if dygnet(r["tid"], gräns) == dag}

    def inför(self, kort: Kort, mening_id: int | None = None) -> None:
        """Kortet gick rätt i en mening och är inne i systemet (5.1)."""
        self.conn.execute(
            "INSERT OR IGNORE INTO infört (kurs_id, språk, typ, nyckel, tid, mening_id) "
            "VALUES (?, ?, ?, ?, ?, ?)", (self.id, *_kolumner(kort), nu(), mening_id))
        self.conn.commit()

    def införda(self) -> set[Kort]:
        return {_kort(r) for r in self.conn.execute(
            "SELECT * FROM infört WHERE kurs_id = ?", (self.id,))}

    def tillåtna(self, dag: str | None = None) -> set[Kort]:
        """Vad en mening får använda i dag: införda plus dagens presenterade (5.2)."""
        return self.införda() | self.presenterade(dag)

    # ── nivåerna ──

    def öppna_nivå(self, nummer: int, kort: list[Kort]) -> None:
        """Nivån öppnas och dess kort blir upplåsta, inte införda (4.5)."""
        self.conn.execute("INSERT OR IGNORE INTO nivå (kurs_id, nummer, öppnad) "
                          "VALUES (?, ?, ?)", (self.id, nummer, nu()))
        self.conn.executemany(
            "INSERT OR IGNORE INTO kortnivå (kurs_id, språk, typ, nyckel, nummer) "
            "VALUES (?, ?, ?, ?, ?)", [(self.id, *_kolumner(k), nummer) for k in kort])
        self.conn.commit()

    def öppnade_nivåer(self) -> list[int]:
        return [r["nummer"] for r in self.conn.execute(
            "SELECT nummer FROM nivå WHERE kurs_id = ? ORDER BY nummer", (self.id,))]

    def upplåsta(self) -> set[Kort]:
        return {_kort(r) for r in self.conn.execute(
            "SELECT * FROM kortnivå WHERE kurs_id = ?", (self.id,))}

    # ── dagens plan ──

    def tilldela(self, kort: list[Kort], dag: str | None = None) -> None:
        """Dagens nya kort, valda innan passet börjar (5.1)."""
        dag = dag or self.dag()
        self.conn.executemany(
            "INSERT OR IGNORE INTO tilldelning (kurs_id, dag, språk, typ, nyckel) "
            "VALUES (?, ?, ?, ?, ?)", [(self.id, dag, *_kolumner(k)) for k in kort])
        self.conn.commit()

    def tilldelning(self, dag: str | None = None) -> set[Kort]:
        return {_kort(r) for r in self.conn.execute(
            "SELECT * FROM tilldelning WHERE kurs_id = ? AND dag = ?",
            (self.id, dag or self.dag()))}

    def spara_tempo(self, nya: int, sparat: float, dag: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO tempo (kurs_id, dag, nya, sparat) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (kurs_id, dag) DO UPDATE SET nya = excluded.nya, "
            "sparat = excluded.sparat", (self.id, dag or self.dag(), nya, sparat))
        self.conn.commit()

    def tempo(self, dag: str | None = None) -> tuple[int, float] | None:
        rad = self.conn.execute("SELECT nya, sparat FROM tempo WHERE kurs_id = ? AND dag = ?",
                                (self.id, dag or self.dag())).fetchone()
        return None if rad is None else (rad["nya"], rad["sparat"])

    # ── bevis, karantän och felrapporter (3.10, 7.2) ──

    def spara_bevis(self, kort: Kort, spec: str) -> None:
        self.conn.execute(
            "INSERT INTO bevis (kurs_id, språk, typ, nyckel, spec, tid) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (kurs_id, språk, typ, nyckel) "
            "DO UPDATE SET spec = excluded.spec, tid = excluded.tid",
            (self.id, *_kolumner(kort), spec, nu()))
        self.conn.commit()

    def bevis(self, kort: Kort) -> str | None:
        rad = self.conn.execute(
            "SELECT spec FROM bevis WHERE kurs_id = ? AND språk = ? AND typ = ? "
            "AND nyckel = ?", (self.id, *_kolumner(kort))).fetchone()
        return rad["spec"] if rad else None

    def sätt_i_karantän(self, kort: Kort, orsak: str) -> None:
        """Kortet var i dagsplanen men gick inte att pröva (3.10)."""
        self.conn.execute(
            "INSERT OR REPLACE INTO karantän (kurs_id, språk, typ, nyckel, orsak, tid) "
            "VALUES (?, ?, ?, ?, ?, ?)", (self.id, *_kolumner(kort), orsak, nu()))
        self.conn.commit()

    def karantän(self) -> dict[Kort, str]:
        return {_kort(r): r["orsak"] for r in self.conn.execute(
            "SELECT * FROM karantän WHERE kurs_id = ?", (self.id,))}

    def rapportera_fel(self, text: str, kort: Kort | None = None,
                       mening_id: int | None = None) -> None:
        self.conn.execute(
            "INSERT INTO felrapport (kurs_id, mening_id, språk, typ, nyckel, text, tid) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.id, mening_id, *(_kolumner(kort) if kort else (None, None, None)),
             text, nu()))
        self.conn.commit()
