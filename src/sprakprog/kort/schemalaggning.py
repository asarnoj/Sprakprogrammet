"""FSRS-schemaläggning ovanpå kortlagret.

Algoritmen kommer från paketet `fsrs` (6.3.2) och skrivs inte om här. Skälet
är projektets eget: en tyst felaktig implementation av en minnesmodell märks
inte på månader, och det är precis den sortens fel som har kostat mest i det
här projektet. Ett testat bibliotek är billigare än en egen härledning.

Vad som DÄREMOT är vårt är hur systemet används, och där finns tre beslut
ur GENERATOR.md som alla syns i koden nedan.

INGA INLÄRNINGSSTEG. `Scheduler` startar normalt varje kort i en kedja om
en och tio minuter, och lägger tillbaka fallerade kort i en tiominutersloop.
Vi kör med tomma steglistor: att se SAMMA kort om och om igen är precis det
som gör att man fastnar, och genereringen kan i stället ge kortet i en ny
mening med andra ord runt sig.

Men den ersättningen sker INTE här, och det påstod den här texten tidigare
att den gjorde. FSRS minsta intervall är ett dygn, så ett fallerat kort
schemaläggs i morgon och kan inte komma tillbaka i dagens kö hur kön än
sorteras. Återförsöket ligger i generatorns PASSKÖ (`generator/__init__.py`),
som är per pass och lever i minnet. Schemaläggningen här rörs inte av den —
återförsöket blir en tidig repetition, med den mindre stabilitetsökning
FSRS ger sådana.

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
        # Nollmodellen, sparad före prövningen. Se kort.sql, Repetition.
        r_före = self.retention(rad, nu) if rad["sedd"] else None
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
               (kort_id, mening_id, tidpunkt, betyg, förfluten, r_före,
                stabilitet, svårighet)
               VALUES (?,?,?,?,?,?,?,?)""",
            (kort_id, mening_id, nu.isoformat(), int(RÄTT if rätt else FEL),
             förfluten, r_före, efter.stability, efter.difficulty))
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
        # NOLLMODELLEN RÄKNAS BARA ÖVER SEDDA KORT. Ett osett kort har R = 0,
        # och att summera det in i `förväntat` vore att påstå att FSRS
        # förutsäger ett säkert fel — men modellen förutsäger ingenting alls
        # om ett kort den aldrig sett. Talet blev då två storheter adderade,
        # förväntade fel plus antalet nya ord, och därmed oanvändbart som
        # nollmodell. Poängsättaren gjorde redan den här uppdelningen; loggen
        # gjorde det inte, så samma namn betydde olika saker på två ställen.
        rader = self._rader(utfall)
        sedda = [r for r in rader if r["sedd"] is not None]
        förväntat = sum(1 - self.retention(r, nu) for r in sedda)
        markör = self.db.execute(
            """INSERT INTO Mening (tidpunkt, språk, källspråk, spec, text,
                                   budget, förväntat, sedda, nya, fel)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nu.isoformat(), språk, källspråk, spec, text, budget, förväntat,
             len(sedda), len(rader) - len(sedda),
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


#: Förval för hur mycket användaren vill öva, när kursen inte säger något.
#: DET ENDA VALDA TALET I UPPLÅSNINGEN — och det är användarens val och inte
#: vårt: en uppgift om hens dygn, som ingen mätning kan ersätta. Allt annat
#: räknas fram (se `upplåsningsläge`).
STANDARD_MENINGAR_PER_DAG = 20


def belastning(kort_db: sqlite3.Connection, språk: str) -> tuple[float, float | None]:
    """(repetitioner per dag för det lärda, per osett kort) — i jämvikt.

    Ett kort med stabilitet S ska enligt FSRS ses var I(S):e dag, alltså
    1/I(S) gånger per dag. Summan över de SEDDA korten är kursens dagliga
    arbetsmängd i jämvikt. Intervallet är schemaläggarens eget.

    ETT OSETT KORT KAN INTE RÄKNAS SÅ. Frestelsen är att sätta in stabiliteten
    efter första rätta svaret, men det ger kortets kostnad DEN DAG det lärs in,
    och beskriver därmed en topp som aldrig inträffar: generatorn introducerar
    nya kort i den takt användaren övar, inte alla på en gång, och intervallen
    växer med varje repetition. Måttet skulle säga att 262 nya kort kostar
    22 meningar om dagen för alltid, när sanningen är att de kostar det en dag
    var och sedan allt mindre.

    Vad ett osett kort kostar när det väl SITTER går däremot att mäta, och
    inte på användare i allmänhet utan på just den här: medelbelastningen över
    hens egna sedda kort i samma kurs. Det är en mätning av hens minne, inte
    ett antagande om det. None när kursen är oövad och mätningen saknas.

    Bara SCHEMALAGDA kort räknas. De mätta står aldrig i kön och belastar inte.
    """
    f = _skapa_schemaläggare()
    takter = [1 / f._next_interval(stability=r["stabilitet"])
              for r in kort_db.execute(
                  """SELECT stabilitet FROM Kort
                     WHERE språk = ? AND schemalagt = 1 AND sedd IS NOT NULL
                       AND stabilitet IS NOT NULL""", (språk,))]
    return sum(takter), (sum(takter) / len(takter) if takter else None)


def kort_per_mening(kort_db: sqlite3.Connection, språk: str) -> float | None:
    """Hur många kort en mening rör. MÄTT ur användarens egen historik.

    Bron mellan det användaren väljer (meningar per dag) och det systemet
    räknar i (repetitioner per dag). Storheten är stram — 5,3 till 6,7 över
    språk och nivåer, med sd omkring 1 — så medelvärdet konvergerar på tio
    meningar. Därför ingen spärr för minsta historik.

    None när kursen är oövad. Då finns heller ingen upplåsningsfråga: man kan
    inte lämna en nivå man inte börjat på, och att öva den skapar mätningen.
    """
    rad = kort_db.execute(
        """SELECT COUNT(*) AS rep, COUNT(DISTINCT r.mening_id) AS meningar
           FROM Repetition r
           JOIN Kort k ON k.id = r.kort_id
           WHERE k.språk = ? AND r.mening_id IS NOT NULL""", (språk,)).fetchone()
    return rad["rep"] / rad["meningar"] if rad["meningar"] else None


def upplåsningsläge(kort_db: sqlite3.Connection, språk: str,
                    meningar_per_dag: int | None = None) -> dict:
    """Finns det plats för mer material?

    UPPLÅSNING ÄR EN KAPACITETSFRÅGA OCH INTE EN BEHÄRSKNINGSFRÅGA. Att mäta
    om användaren "kan" nivån vore att implementera om FSRS garanti: håller
    man repetitionerna minns man per konstruktion 90 % av sina kort, hela
    tiden. Det finns ingen behärskning kvar att pröva. Det som däremot är en
    verklig gräns är arbetsmängden — nya kort kostar repetitioner, och dygnet
    är ändligt.

    Alltså: nivån öppnas när belastningen den skulle ge ryms i det användaren
    valt att öva. Tre tal, varav bara ett är valt:

        belastning        Σ 1/intervall          — FSRS egna intervall
        kort per mening   mätt ur historiken     — användarens egen logg
        meningar per dag  användarens val        — en uppgift om hens liv

    Måttet blandar inte ihop "kan inte" med "repeterade nyss", vilket varje
    mått byggt på R gör: R faller med tiden sedan repetitionen, stabiliteten
    gör det inte.
    """
    if meningar_per_dag is None:
        rad = kort_db.execute(
            "SELECT meningar_per_dag FROM Kurs WHERE målspråk = ?", (språk,)).fetchone()
        meningar_per_dag = rad["meningar_per_dag"] if rad else STANDARD_MENINGAR_PER_DAG

    rad = kort_db.execute(
        """SELECT COUNT(*) AS totalt,
                  SUM(CASE WHEN sedd IS NULL THEN 1 ELSE 0 END) AS osedda
           FROM Kort WHERE språk = ? AND schemalagt = 1""", (språk,)).fetchone()
    lärt, per_kort = belastning(kort_db, språk)
    k = kort_per_mening(kort_db, språk)
    rep_per_dag = (lärt + (rad["osedda"] or 0) * per_kort
                   if per_kort is not None else None)
    krävs = rep_per_dag / k if (k and rep_per_dag is not None) else None
    return {"totalt": rad["totalt"], "osedda": rad["osedda"] or 0,
            "rep_per_dag": rep_per_dag, "kort_per_mening": k, "per_kort": per_kort,
            "krävs": krävs, "kapacitet": meningar_per_dag,
            "klar": krävs is not None and krävs <= meningar_per_dag}


def kostnad(kort_db: sqlite3.Connection, språk_db: sqlite3.Connection, språk: str,
            nivå: int, cefr: str, meningar_per_dag: int | None = None) -> dict:
    """Vad nivån `nivå` skulle kosta, utan att låsa upp den.

    Befolkningen är additiv och idempotent men skriver, så frågan ställs i en
    kopia av inlärardatabasen. Att fråga vad något kostar får inte vara att
    köpa det.
    """
    import tempfile
    from pathlib import Path

    from .befolka import befolka
    from .db import anslut_kort

    läge = upplåsningsläge(kort_db, språk, meningar_per_dag)
    with tempfile.TemporaryDirectory() as d:
        kopia = Path(d) / "prov.db"
        kort_db.commit()
        with sqlite3.connect(kopia) as mål:
            kort_db.backup(mål)
        prov = anslut_kort(kopia)
        befolka(prov, språk_db, {språk}, nivå=nivå, cefr=cefr)
        efter = upplåsningsläge(prov, språk, läge["kapacitet"])
        prov.close()
    return {"nivå": nivå, "före": läge, "efter": efter,
            "nya_kort": efter["totalt"] - läge["totalt"],
            "ryms": efter["klar"]}


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
