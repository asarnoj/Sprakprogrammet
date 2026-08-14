"""FSRS-schemaläggning ovanpå kortlagret.

Algoritmen kommer från paketet `fsrs` (6.3.2) och skrivs inte om här. Skälet
är projektets eget: en tyst felaktig implementation av en minnesmodell märks
inte på månader, och det är precis den sortens fel som har kostat mest i det
här projektet. Ett testat bibliotek är billigare än en egen härledning.

Vad som DÄREMOT är vårt är hur systemet används, och där finns tre beslut
ur GENERATOR.md som alla syns i koden nedan.

INGA INLÄRNINGSSTEG. `Scheduler` startar normalt varje kort i en kedja om
en och tio minuter, och lägger tillbaka fallerade kort i en tiominutersloop.
Vi kör med tomma steglistor. Ett kort som fallerat får hög prioritet i nästa
generering och dyker upp igen inom några meningar — i en ANNAN mening, vilket
är bättre än att se samma kort igen. Genereringen ersätter mekaniken.

OAVSIKTLIGA REPETITIONER RÄKNAS. En mening rör sju till tio kort men valdes
för ett av dem. Alla får betyg. FSRS räknar på faktisk förfluten tid och ger
en repetition före förfallodatum en MINDRE stabilitetsökning — spacing-
effekten är modellerad, inte kringgången.

ETT FALLERAT ORDKORT SKYDDAR SINA FORMER. Kan man inte hämta fram ordet alls
testades formen aldrig, och den ska inte straffas för det. Utan den regeln
skulle ett enda ordglapp fälla trettio formkort på en gång.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from fsrs import Card, Rating, Scheduler, State

#: Betyg. FSRS har fyra steg, men en diff mot facit ger bara två signaler:
#: formen stod där eller inte. HARD och EASY lämnas oanvända hellre än att
#: härledas ur något som inte mäter dem — svarstid är en kandidat senare.
FEL, RÄTT = Rating.Again, Rating.Good


def _skapa_schemaläggare() -> Scheduler:
    return Scheduler(learning_steps=(), relearning_steps=())


def _till_card(rad: sqlite3.Row) -> Card:
    """Databasrad → fsrs.Card, utan översättningsförlust."""
    return Card(
        card_id=rad["id"],
        state=State(rad["tillstånd"]),
        step=rad["steg"],
        stability=rad["stabilitet"],
        difficulty=rad["svårighet"],
        due=datetime.fromisoformat(rad["förfaller"]) if rad["förfaller"]
        else datetime.now(UTC),
        last_review=datetime.fromisoformat(rad["sedd"]) if rad["sedd"] else None,
    )


class Schemaläggare:
    """Läser och skriver FSRS-tillstånd för kort i inlärardatabasen."""

    def __init__(self, kort_db: sqlite3.Connection) -> None:
        self.db = kort_db
        self.fsrs = _skapa_schemaläggare()

    # ── läsa ─────────────────────────────────────────────────────────

    def retention(self, rad: sqlite3.Row, nu: datetime | None = None) -> float:
        """R — sannolikheten att kortet minns just nu.

        Det är den här siffran svårighetsbudgeten summerar: förväntat antal
        fel i en mening är Σ(1−R) över dess kort. Ett osett kort har inget
        minne att mäta och räknas som 0.
        """
        if rad["sedd"] is None:
            return 0.0
        return self.fsrs.get_card_retrievability(_till_card(rad), nu or datetime.now(UTC))

    def förfallna(self, språk: str, gräns: int = 100,
                  nu: datetime | None = None) -> list[sqlite3.Row]:
        """Schemalagda kort som är förfallna, svagast först.

        Bara `schemalagt = 1`. Ett kort som möts i nästan varje mening går
        inte att schemalägga och står inte i kön — se kort.sql.
        """
        tid = (nu or datetime.now(UTC)).isoformat()
        return self.db.execute(
            """SELECT * FROM Kort
               WHERE språk = ? AND schemalagt = 1
                 AND förfaller IS NOT NULL AND förfaller <= ?
               ORDER BY förfaller LIMIT ?""", (språk, tid, gräns)).fetchall()

    #: Ordningen nya kort introduceras i. Ordet först, alltid: man kan inte
    #: lära sig att svag maskulin dativ tar -en innan man har ett ord att
    #: sätta ändelsen på. Inom en typ går det mest räckviddiga först — den
    #: stam som täcker fyrtionio celler är mer värd än den som täcker en.
    #:
    #: Det här är schemaläggarens FÖRVAL. Vilket kort en viss mening ska
    #: byggas kring är generatorns beslut, och den kan välja annorlunda.
    INTRODUKTIONSORDNING = ("ord", "egenskap", "stam", "form", "system",
                            "rektion", "ordföljd")

    def osedda(self, språk: str, gräns: int = 100) -> list[sqlite3.Row]:
        """Kort som aldrig prövats. Det är här nya ord kommer in."""
        ordning = " ".join(
            f"WHEN '{t}' THEN {i}" for i, t in enumerate(self.INTRODUKTIONSORDNING))
        return self.db.execute(
            f"""SELECT * FROM Kort
                WHERE språk = ? AND schemalagt = 1 AND sedd IS NULL
                ORDER BY CASE typ {ordning} ELSE 99 END,
                         räckvidd DESC, id LIMIT ?""", (språk, gräns)).fetchall()

    # ── skriva ───────────────────────────────────────────────────────

    def repetera(self, kort_id: int, rätt: bool, *, mening_id: int | None = None,
                 nu: datetime | None = None) -> sqlite3.Row:
        """Registrera EN prövning och skriv tillbaka det nya tillståndet."""
        nu = nu or datetime.now(UTC)
        rad = self.db.execute("SELECT * FROM Kort WHERE id = ?", (kort_id,)).fetchone()
        if rad is None:
            raise KeyError(f"kort {kort_id} finns inte")
        före = _till_card(rad)
        förfluten = ((nu - före.last_review).total_seconds() / 86400
                     if före.last_review else None)
        efter, _ = self.fsrs.review_card(före, RÄTT if rätt else FEL, nu)

        self.db.execute(
            """UPDATE Kort SET tillstånd = ?, steg = ?, stabilitet = ?,
                   svårighet = ?, förfaller = ?, sedd = ?,
                   antal = antal + 1, fall = fall + ?
               WHERE id = ?""",
            (int(efter.state), efter.step, efter.stability, efter.difficulty,
             efter.due.isoformat(), nu.isoformat(), 0 if rätt else 1, kort_id))
        self.db.execute(
            """INSERT INTO Repetition
               (kort_id, mening_id, tidpunkt, betyg, förfluten, stabilitet, svårighet)
               VALUES (?,?,?,?,?,?,?)""",
            (kort_id, mening_id, nu.isoformat(), int(RÄTT if rätt else FEL),
             förfluten, efter.stability, efter.difficulty))
        return self.db.execute("SELECT * FROM Kort WHERE id = ?", (kort_id,)).fetchone()

    def registrera_mening(self, språk: str, spec: str, text: str,
                          utfall: dict[int, bool], *, källspråk: str | None = None,
                          budget: float | None = None,
                          nu: datetime | None = None) -> int:
        """Logga en hel mening och betygsätt varje kort den rörde.

        `utfall` är kort_id → klarade det. Ett fallerat ORDKORT skyddar sina
        egna form- och stamkort: de tas ur betygsättningen helt och behåller
        sitt passerade förfallodatum, eftersom de aldrig prövades.
        """
        nu = nu or datetime.now(UTC)
        förväntat = sum(
            1 - self.retention(r, nu)
            for r in self._rader(utfall)) if utfall else 0.0
        markör = self.db.execute(
            """INSERT INTO Mening (tidpunkt, språk, källspråk, spec, text,
                                   budget, förväntat, fel)
               VALUES (?,?,?,?,?,?,?,?)""",
            (nu.isoformat(), språk, källspråk, spec, text, budget, förväntat,
             sum(1 for v in utfall.values() if not v)))
        mening_id = markör.lastrowid

        skyddade = self._skyddade(utfall)
        for kort_id, rätt in utfall.items():
            if kort_id in skyddade:
                continue
            self.repetera(kort_id, rätt, mening_id=mening_id, nu=nu)
        self.db.commit()
        return mening_id

    # ── hjälp ────────────────────────────────────────────────────────

    def _rader(self, utfall: dict[int, bool]) -> list[sqlite3.Row]:
        if not utfall:
            return []
        platser = ",".join("?" * len(utfall))
        return self.db.execute(
            f"SELECT * FROM Kort WHERE id IN ({platser})", tuple(utfall)).fetchall()

    def _skyddade(self, utfall: dict[int, bool]) -> set[int]:
        """Form- och stamkort vars ordkort fallerade i samma mening."""
        fallna_ord = {r["koncept"] for r in self._rader(utfall)
                      if r["typ"] == "ord" and not utfall[r["id"]]}
        if not fallna_ord:
            return set()
        return {r["id"] for r in self._rader(utfall)
                if r["typ"] in ("form", "stam") and r["koncept"] in fallna_ord}


#: Nivån öppnas när så här stor del av dess schemalagda kort har en
#: stabilitet över UPPLÅSNINGSDAGAR. Stabilitet är det FSRS faktiskt
#: modellerar; sju dagar betyder "överlevt minst en riktig glömskekurva";
#: nittio procent lämnar plats för de svåraste korten att släpa efter utan
#: att blockera.
#:
#: Två tal, båda första gissningar av samma sort som vikterna i poang.py —
#: men till skillnad från dem är de lätta att ändra och lätta att förstå.
UPPLÅSNINGSANDEL = 0.9
UPPLÅSNINGSDAGAR = 7.0


def upplåsningsläge(kort_db: sqlite3.Connection, språk: str) -> dict:
    """Hur nära nästa nivå kursen står.

    Räknar bara SCHEMALAGDA kort. De mätta står aldrig i kön och kan därför
    aldrig bli mogna på kösidan — att kräva det av dem vore att kräva något
    systemet med flit inte gör.
    """
    rad = kort_db.execute(
        """SELECT COUNT(*) AS totalt,
                  SUM(CASE WHEN stabilitet >= ? THEN 1 ELSE 0 END) AS mogna
           FROM Kort WHERE språk = ? AND schemalagt = 1""",
        (UPPLÅSNINGSDAGAR, språk)).fetchone()
    totalt = rad["totalt"] or 0
    mogna = rad["mogna"] or 0
    andel = mogna / totalt if totalt else 0.0
    return {"totalt": totalt, "mogna": mogna, "andel": andel,
            "klar": andel >= UPPLÅSNINGSANDEL}


def kö(kort_db: sqlite3.Connection, språk: str, antal: int = 20) -> list[sqlite3.Row]:
    """Dagens kort: förfallna först, sedan osedda om det finns plats."""
    s = Schemaläggare(kort_db)
    förfallna = s.förfallna(språk, antal)
    if len(förfallna) >= antal:
        return förfallna
    return förfallna + s.osedda(språk, antal - len(förfallna))


def spec_json(spec) -> str:
    """Meningsspecifikationen som text, för att kunna återskapa meningen."""
    from dataclasses import asdict, is_dataclass

    def rensa(v):
        if is_dataclass(v):
            return {k: rensa(x) for k, x in asdict(v).items() if x not in (None, (), False)}
        if isinstance(v, (list, tuple)):
            return [rensa(x) for x in v]
        return str(v) if hasattr(v, "value") else v

    return json.dumps(rensa(spec), ensure_ascii=False, sort_keys=True)
