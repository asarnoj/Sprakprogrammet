"""Prov för E6: kort som mäts men inte schemaläggs.

VARFÖR DET HÄR PROVET FINNS. `schemalagt = 0` var en NEGATION. Ett kort som
möts oftare än en gång om dagen kan inte spacas — FSRS kortaste meningsfulla
intervall är ett dygn (`exponeringsgräns`) — så flaggan lyfte kortet ur kön
och lämnade det utan mått. Det betygsattes ändå, men ingenting läste betygen.
Franskans `form:une` gick fel fyra gånger av sex och systemet hade ingen väg
att märka det: kortet stod inte i `förfallna` (frågan kräver `schemalagt = 1`)
och kunde därför aldrig bli mål.

`Schemaläggare.i_larm` är avläsningen, och `övervakad` är rollen den får i
passet. Kedjan har sju led och vart och ett kan gå sönder tyst:

  1. LARMET FÅNGAR       ett kort med fler fel än slumpen bär ska larma
  2. LARMET TIGER        ett kort på normal takt ska INTE larma
  3. BETYGLÖST RÄKNAS EJ ett undanhållet möte är ingen mätning
  4. PASSET TAR IN       ett larmat kort ska bli mål i dagens pass
  5. INGEN LÅSNING       ett kort som redan rörts idag får inte larma, för
                         då kan raden aldrig klareras och passet aldrig bli
                         klart (E2: en bedömning per kort och dygn)
  6. GENERATORN SER      passet och generatorn ska fråga SAMMA funktion
  7. SUMMAN STÄMMER      rollerna summerar till `att_göra`

TRÖSKELN ÄR MÄTT OCH INTE VALD, och provet vaktar just det. Första utkastet
larmade på "mer än ett fel i fönstret", rakt ur definitionen. Mätningen sa att
övervakade kort går rätt 88,4 % av gångerna — alltså under målet 0,9 — så den
tröskeln hade larmat på en tredjedel av beståndet. Invariant 2 är det
påståendet, och sabotaget som fäller den är exakt det förkastade måttet.

ALDRIG MOT DEN RIKTIGA DATABASEN — kopia via SQLites backup.

Kör:  python ordbok/verktyg/övervakningsprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut                                   # noqa: E402
from sprakprog.generator import Generator                         # noqa: E402
from sprakprog.kort import pass_ as passlager                     # noqa: E402
from sprakprog.kort.befolka import sätt_schemalagt                # noqa: E402
from sprakprog.kort.db import anslut_kort                         # noqa: E402
from sprakprog.kort import schemalaggning as sch                  # noqa: E402
from sprakprog.kort.schemalaggning import (                       # noqa: E402
    FEL, LARMFÖNSTER, RÄTT, Schemaläggare, dagsplan,
)

#: Modulen `befolka`, hämtad ur `sys.modules` och inte med `import ... as`.
#: `sprakprog.kort.__init__` gör `from .befolka import befolka`, vilket binder
#: OM paketets attribut `befolka` från modulen till funktionen — så
#: `import sprakprog.kort.befolka as bef` ger funktionen. Sabotaget behöver
#: modulen för att kunna byta ut `exponeringsgräns` i den.
bef = sys.modules[sätt_schemalagt.__module__]

#: Språket proven körs mot. Franskan är den enda kursen med en verklig
#: repetitionslogg, och proven skriver sin egen logg ändå — men beståndet av
#: ÖVERVAKADE kort måste finnas på riktigt, och det gör det bara där
#: exponeringen är mätt.
SPRÅK = "fr"


def _kopia(mål: Path) -> sqlite3.Connection:
    """Kopia av den riktiga basen, ansluten SOM PROGRAMMET ANSLUTER.

    `anslut_kort` och inte `sqlite3.connect`, och det är inte en
    bekvämlighet: migrationerna körs vid anslutningen, och rollen
    `övervakad` finns bara i `Passkort` efter att `passkort_overvakad.sql`
    byggt om tabellen. Med en rå anslutning provades ett schema ingen
    användare har.
    """
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(mål)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    return anslut_kort(mål)


def _övervakat(kort: sqlite3.Connection, *, flitigast: bool = True):
    """Ett verkligt övervakat kort ur beståndet.

    `flitigast` väljer det med högst exponering, alltså det som säkert går
    att bygga en mening kring. Det spelar roll för invariant 6 och för
    ingenting annat: ett larm på ett onåbart kort vore ett larm ingen kan
    svara på, och då mäter provet sökningen i stället för larmet.
    """
    return kort.execute(
        "SELECT * FROM Kort WHERE språk = ? AND schemalagt = 0 "
        "AND sedd IS NOT NULL ORDER BY exponering "
        + ("DESC" if flitigast else "ASC") + " LIMIT 1", (SPRÅK,)).fetchone()


def _sätt_logg(kort: sqlite3.Connection, kort_id: int,
               betyg: list[int | None], *, dagar_bak: int = 2) -> None:
    """Skriv om kortets repetitionslogg. Sista i listan är det senaste mötet.

    DATERAS BAKÅT, alltid. Ett möte idag gör kortet skyddat resten av dygnet
    (`_redan_idag`), och då står det utanför larmet av rätt skäl — vilket är
    invariant 5 och inte något de övriga ska råka mäta.
    """
    kort.execute("DELETE FROM Repetition WHERE kort_id = ?", (kort_id,))
    bas = datetime.now(UTC) - timedelta(days=dagar_bak)
    for i, b in enumerate(betyg):
        # EN BETYGLÖS RAD MÅSTE SÄGA VARFÖR — schemat kräver det, och det är
        # samma sak provet påstår: raden finns, men den är ingen mätning.
        kort.execute(
            "INSERT INTO Repetition (kort_id, tidpunkt, betyg, skäl) "
            "VALUES (?,?,?,?)",
            (kort_id, (bas + timedelta(seconds=i)).isoformat(), b,
             None if b is not None else "undanhållen"))
    kort.commit()


def _sätt_meningslogg(kort: sqlite3.Connection, per_dag: list[int]) -> None:
    """Skriv om meningsloggen: en post per element, i lika många dygn.

    Det är den här loggen `meningstakt` mäter, och därmed det enda som numera
    avgör var gränsen mellan schemalagt och övervakat går.
    """
    kort.execute("DELETE FROM Mening WHERE språk = ?", (SPRÅK,))
    for dag, antal in enumerate(per_dag):
        stund = (datetime(2026, 1, 1, 12, tzinfo=UTC)
                 + timedelta(days=dag)).isoformat()
        for _ in range(antal):
            kort.execute(
                "INSERT INTO Mening (tidpunkt, språk, spec, text) "
                "VALUES (?,?,'{}','x')", (stund, SPRÅK))
    kort.commit()


def _övervakade(kort: sqlite3.Connection) -> int:
    return kort.execute(
        "SELECT COUNT(*) FROM Kort WHERE språk = ? AND schemalagt = 0",
        (SPRÅK,)).fetchone()[0]


def _kurs(kort: sqlite3.Connection) -> sqlite3.Row:
    return kort.execute("SELECT * FROM Kurs WHERE målspråk = ? LIMIT 1",
                        (SPRÅK,)).fetchone()


# ── invarianterna ────────────────────────────────────────────────────

def prov_larmet_fångar(kort) -> list[str]:
    """Ett kort med fler fel än slumpen bär ska larma."""
    k = _övervakat(kort)
    _sätt_logg(kort, k["id"], [int(FEL)] * 3 + [int(RÄTT)] * 7)
    larm = {r["id"] for r in Schemaläggare(kort).i_larm(SPRÅK)}
    if k["id"] not in larm:
        return [f"{k['typ']}:{k['facit']} har 3 fel av {LARMFÖNSTER} "
                f"och larmar inte"]
    return []


def prov_larmet_tiger(kort) -> list[str]:
    """Ett kort på beståndets egen takt ska INTE larma.

    ETT FEL AV TIO ÄR MÅLET, inte en avvikelse. Provet är det förkastade
    måttets gravsten: "mer än ett fel i fönstret" hade fällt precis det här.
    """
    k = _övervakat(kort)
    _sätt_logg(kort, k["id"], [int(FEL)] + [int(RÄTT)] * 9)
    larm = {r["id"] for r in Schemaläggare(kort).i_larm(SPRÅK)}
    if k["id"] in larm:
        return [f"{k['typ']}:{k['facit']} larmar på 1 fel av {LARMFÖNSTER}, "
                f"vilket ÄR retentionsmålet"]
    return []


def prov_betyglöst_räknas_ej(kort) -> list[str]:
    """Ett undanhållet möte är ingen mätning och får inte spä ut larmet."""
    k = _övervakat(kort)
    _sätt_logg(kort, k["id"], [int(FEL)] * 3 + [int(RÄTT)] * 7 + [None] * 10)
    larm = {r["id"] for r in Schemaläggare(kort).i_larm(SPRÅK)}
    if k["id"] not in larm:
        return [f"{LARMFÖNSTER} betyglösa rader tystade larmet på "
                f"{k['typ']}:{k['facit']} — ett undanhållet kort prövades "
                f"aldrig och får inte räknas som rätt"]
    return []


def prov_passet_tar_in(kort) -> list[str]:
    """Ett larmat kort ska bli mål i dagens pass, med sin egen roll."""
    k = _övervakat(kort)
    _sätt_logg(kort, k["id"], [int(FEL)] * 3 + [int(RÄTT)] * 7)
    kurs = _kurs(kort)
    kort.execute("DELETE FROM Passkort"); kort.execute("DELETE FROM Pass")
    kort.commit()
    plan = dagsplan(kort, SPRÅK, minuter_per_dag=kurs["minuter_per_dag"])
    p = passlager.starta(kort, kurs, plan)
    roller = {r["kort_id"]: r["roll"] for r in kort.execute(
        "SELECT kort_id, roll FROM Passkort WHERE pass_id = ?", (p["id"],))}
    if roller.get(k["id"]) != "övervakad":
        return [f"{k['typ']}:{k['facit']} larmar men fick rollen "
                f"{roller.get(k['id'])!r} i passet"]
    return []


def prov_ingen_låsning(kort) -> list[str]:
    """Ett kort som redan rörts idag får inte larma — raden vore olåsbar.

    E2 ger en bedömning per kort och dygn, och bara ett FEL får registreras
    en gång till. En `övervakad`-rad på ett redan mött kort går alltså inte
    att klarera genom att svara RÄTT: den står kvar som `väntar`, och passet
    säger att arbete återstår utan att det finns någon väg att göra det.
    """
    k = _övervakat(kort)
    # FYRA FEL OCH INTE TRE. Dagens möte lägger en elfte rad, och fönstret
    # tappar då sin äldsta — som är ett fel. Med tre föll kortet ur larmet
    # av den anledningen i stället för av spärren, och sabotaget blev stumt:
    # provet mätte sin egen uppsättning i stället för regeln.
    _sätt_logg(kort, k["id"], [int(FEL)] * 4 + [int(RÄTT)] * 6)
    kort.execute(
        "INSERT INTO Repetition (kort_id, tidpunkt, betyg) VALUES (?,?,?)",
        (k["id"], datetime.now(UTC).isoformat(), int(RÄTT)))
    kort.commit()
    larm = {r["id"] for r in Schemaläggare(kort).i_larm(SPRÅK)}
    if k["id"] in larm:
        return [f"{k['typ']}:{k['facit']} rördes idag men larmar ändå — "
                f"passraden skulle aldrig gå att klarera"]
    return []


def prov_generatorn_ser(kort, språk_db) -> list[str]:
    """Generatorn ska ha samma larm som passet, annars är raden olåsbar.

    KÖN TÖMS FÖRST. Allt schemalagt får en förfallodag långt fram och inget
    nytt tillåts, så det larmade kortet är det ENDA i kön. Då är svaret
    entydigt: bygger generatorn en mening som rör kortet, eller bygger den
    ingenting alls?
    """
    k = _övervakat(kort)
    _sätt_logg(kort, k["id"], [int(FEL)] * 3 + [int(RÄTT)] * 7)
    kort.execute(
        "UPDATE Kort SET förfaller = ? WHERE språk = ? AND schemalagt = 1",
        ((datetime.now(UTC) + timedelta(days=365)).isoformat(), SPRÅK))
    kort.commit()
    kurs = _kurs(kort)
    from sprakprog.kort.dimensioner import toppnivå
    g = Generator(språk_db, kort, SPRÅK, källspråk=kurs["källspråk"],
                  nivå=toppnivå(SPRÅK), cefr="C2", budget=kurs["budget"],
                  frö=11)
    f = g.föreslå(kandidater=300, nya_tillåtna=0)
    if f is None:
        return [f"generatorn byggde ingenting med {k['typ']}:{k['facit']} "
                f"som enda köade kort — larmet nådde den aldrig"]
    if k["id"] not in {c["id"] for c in (f.kort or [])}:
        return [f"meningen rörde inte {k['typ']}:{k['facit']}, "
                f"trots att det var det enda i kön"]
    return []


def prov_summan_stämmer(kort) -> list[str]:
    """Uppdelningen ska summera till `att_göra`, roll för roll.

    EN RAD AV VARJE ROLL, tagen ur `ROLLORDNING` och inte ur en lista här.
    En sjätte roll som läggs till utan att komma med i `DELAR` faller
    därmed på det här provet i stället för på en skärm hos Julius.
    """
    kurs = _kurs(kort)
    kort.execute("DELETE FROM Passkort"); kort.execute("DELETE FROM Pass")
    kort.execute(
        "INSERT INTO Pass (kurs_id, datum, läge, startad) VALUES (?,?,?,?)",
        (kurs["id"], "2026-01-01", "dagens", datetime.now(UTC).isoformat()))
    pid = kort.execute("SELECT MAX(id) FROM Pass").fetchone()[0]
    idn = [r["id"] for r in kort.execute(
        "SELECT id FROM Kort WHERE språk = ? LIMIT ?",
        (SPRÅK, len(passlager.ROLLORDNING)))]
    for i, (kid, roll) in enumerate(zip(idn, passlager.ROLLORDNING)):
        kort.execute("INSERT INTO Passkort (pass_id, kort_id, roll, ordning) "
                     "VALUES (?,?,?,?)", (pid, kid, roll, i))
    kort.commit()
    läge = passlager.läget(kort, pid)
    summa = sum(d["antal"] for d in läge["delar"])
    if summa != läge["att_göra"]:
        saknas = set(passlager.ROLLORDNING) - {r for r, _ in passlager.DELAR}
        return [f"delarna summerar till {summa}, att_göra är "
                f"{läge['att_göra']} — roller utan nyckel: "
                f"{sorted(saknas) or 'inga'}"]
    return []


def prov_oövad_lyfter_inget(kort) -> list[str]:
    """En kurs som aldrig övats får inga kort lyfta ur schemat.

    GRÄNSEN ÄR EN MÄTNING OCH INTE ETT TAL, och det här är den skarpaste
    formen av påståendet. Förut kom antalet meningar per dag ur
    `Kurs.meningar_per_dag`, som svarade 20 även för en kurs där användaren
    aldrig gjort en enda mening — och 20 lyfte kort ur schemat på ett
    antagande om en dag som inte inträffat. Japanskan hade sex sådana kort.

    Att lämna kortet schemalagt är dessutom den ofarliga sidan: ett
    allestädes närvarande kort som schemaläggs växer bara i stabilitet och
    förfaller aldrig, medan ett sällsynt kort utan schema förlorar spacing.
    """
    _sätt_meningslogg(kort, [])
    sätt_schemalagt(kort, språk=SPRÅK)
    n = _övervakade(kort)
    if n:
        return [f"{n} kort lyftes ur schemat trots att kursen aldrig övats — "
                f"gränsen kom från något annat än en mätning"]
    return []


def prov_gränsen_följer_takten(kort) -> list[str]:
    """Övar man mer möts korten oftare, och fler faller ur schemat.

    Riktningen är hela innehållet: gränsen är 1/takt, så en högre takt ger en
    LÄGRE gräns och därmed fler övervakade kort. Ett fast tal — vilket som
    helst — ger samma svar på båda loggarna.
    """
    _sätt_meningslogg(kort, [5, 5, 5])
    sätt_schemalagt(kort, språk=SPRÅK)
    lugnt = _övervakade(kort)
    _sätt_meningslogg(kort, [40, 40, 40])
    sätt_schemalagt(kort, språk=SPRÅK)
    flitigt = _övervakade(kort)
    if not lugnt < flitigt:
        return [f"5 meningar/dag gav {lugnt} övervakade kort och 40 gav "
                f"{flitigt} — takten styr inte gränsen"]
    return []


def prov_passet_räknar_om(kort) -> list[str]:
    """Gränsen räknas om när dagen byggs, inte bara när `befolka` körs.

    Talet ändrar sig medan användaren övar. Förut behövde det aldrig räknas
    om — det stod stilla på 20 — så flaggan kunde vara satt vid en körning av
    `ordbok kort` för veckor sedan och ändå styra dagens kö.
    """
    _sätt_meningslogg(kort, [40, 40, 40])
    sätt_schemalagt(kort, språk=SPRÅK)
    flitigt = _övervakade(kort)
    # Takten faller, men ingen rör flaggan — bara dagen byggs.
    _sätt_meningslogg(kort, [5, 5, 5])
    kurs = _kurs(kort)
    kort.execute("DELETE FROM Passkort"); kort.execute("DELETE FROM Pass")
    kort.commit()
    plan = dagsplan(kort, SPRÅK, minuter_per_dag=kurs["minuter_per_dag"])
    passlager.starta(kort, kurs, plan)
    efter = _övervakade(kort)
    if not efter < flitigt:
        return [f"takten föll från 40 till 5 meningar/dag men antalet "
                f"övervakade kort stod kvar på {efter} (var {flitigt}) — "
                f"gränsen räknades inte om när passet byggdes"]
    return []


PROV = [
    ("larmet fångar ett trasigt kort",      prov_larmet_fångar),
    ("larmet tiger om ett friskt kort",     prov_larmet_tiger),
    ("betyglösa möten räknas inte",         prov_betyglöst_räknas_ej),
    ("passet tar in det larmade kortet",    prov_passet_tar_in),
    ("redan mött idag låser inte passet",   prov_ingen_låsning),
    ("generatorn ser samma larm",           prov_generatorn_ser),
    ("uppdelningen summerar till att_göra", prov_summan_stämmer),
    ("oövad kurs lyfter inget ur schemat",  prov_oövad_lyfter_inget),
    ("gränsen följer den mätta takten",     prov_gränsen_följer_takten),
    ("passet räknar om gränsen",            prov_passet_räknar_om),
]


# ── sabotagen ────────────────────────────────────────────────────────

def _sabotage_tröskeln_av():
    """larmet stängs av — inget antal fel räcker"""
    gammal = sch._osannolikt_många_fel
    sch._osannolikt_många_fel = lambda fel, möten: False
    return lambda: setattr(sch, "_osannolikt_många_fel", gammal)


def _sabotage_tröskeln_rå():
    """det FÖRKASTADE måttet: fler fel än väntat, utan sannolikhet"""
    gammal = sch._osannolikt_många_fel
    sch._osannolikt_många_fel = (
        lambda fel, möten: fel > möten * sch.FELTOLERANS)
    return lambda: setattr(sch, "_osannolikt_många_fel", gammal)


def _sabotage_betyglöst_räknas():
    """betyglösa rader får räknas med i fönstret"""
    gammal = Schemaläggare.övervakade

    def utan_filter(self, språk):
        return self.db.execute(
            f"""WITH senaste AS (
                    SELECT r.kort_id AS kid, r.betyg AS betyg,
                           ROW_NUMBER() OVER (PARTITION BY r.kort_id
                                              ORDER BY r.tidpunkt DESC) AS n
                    FROM Repetition r JOIN Kort k ON k.id = r.kort_id
                    WHERE k.språk = ? AND k.schemalagt = 0
                )
                SELECT k.*, COUNT(*) AS möten,
                       COALESCE(SUM(s.betyg = {int(FEL)}), 0) AS fel
                FROM Kort k JOIN senaste s ON s.kid = k.id
                WHERE s.n <= ? GROUP BY k.id""", (språk, LARMFÖNSTER)).fetchall()

    Schemaläggare.övervakade = utan_filter
    return lambda: setattr(Schemaläggare, "övervakade", gammal)


def _sabotage_dagens_rörda_med():
    """dagens redan mötta kort får larma igen"""
    gammal = Schemaläggare.i_larm

    def utan_spärr(self, språk, nu=None):
        rader = [r for r in self.övervakade(språk)
                 if sch._osannolikt_många_fel(r["fel"], r["möten"])]
        return sorted(rader, key=lambda r: (-r["fel"] / r["möten"], -r["möten"]))

    Schemaläggare.i_larm = utan_spärr
    return lambda: setattr(Schemaläggare, "i_larm", gammal)


def _sabotage_passet_utan_larm():
    """passet slutar ta in larmade kort"""
    gammal = passlager._rader

    def utan(kort_db, kurs, plan, läge, nu, nåbara=None):
        return [(i, r) for i, r in gammal(kort_db, kurs, plan, läge, nu, nåbara)
                if r != "övervakad"]

    passlager._rader = utan
    return lambda: setattr(passlager, "_rader", gammal)


def _sabotage_generatorn_utan_larm():
    """generatorn frågar inte efter larmet"""
    gammal = Schemaläggare.i_larm
    # PATCHEN SITTER PÅ KLASSEN och tystar därmed båda sidorna. Det duger
    # här, och skälet är att provet den fäller inte bygger något pass: det
    # tömmer kön och kräver att generatorn ändå hittar det larmade kortet.
    # Sabotaget visar alltså att det provet KAN falla — att invarianten inte
    # är tom — medan den faktiska regressionen det vaktar är en annan: tas
    # raden `kö += … i_larm(…)` bort ur `föreslå` returnerar sökningen None
    # på en tom kö, och provet faller på exakt samma sätt.
    Schemaläggare.i_larm = lambda self, språk, nu=None: []
    return lambda: setattr(Schemaläggare, "i_larm", gammal)


def _sabotage_delar_utan_övervakad():
    """uppdelningen glömmer den femte rollen"""
    gammal = passlager.DELAR
    passlager.DELAR = tuple((r, n) for r, n in gammal if r != "övervakad")
    return lambda: setattr(passlager, "DELAR", gammal)


def _sabotage_takten_är_ett_tal():
    """det gamla läget: takten är 20, mätt eller ej"""
    gammal = sch.meningstakt
    sch.meningstakt = lambda kort_db, språk: 20.0
    return lambda: setattr(sch, "meningstakt", gammal)


def _sabotage_gränsen_är_fast():
    """gränsen slutar följa takten"""
    gammal = bef.exponeringsgräns
    bef.exponeringsgräns = lambda takt: 0.05
    return lambda: setattr(bef, "exponeringsgräns", gammal)


def _sabotage_passet_räknar_inte_om():
    """dagen byggs på flaggan som råkar stå där"""
    gammal = passlager.sätt_schemalagt
    passlager.sätt_schemalagt = lambda kort_db, takt=None, *, språk=None: 0
    return lambda: setattr(passlager, "sätt_schemalagt", gammal)


#: (sabotage, vilket prov det ska fälla)
SABOTAGE = [
    (_sabotage_tröskeln_av,           0),
    (_sabotage_tröskeln_rå,           1),
    (_sabotage_betyglöst_räknas,      2),
    (_sabotage_passet_utan_larm,      3),
    (_sabotage_dagens_rörda_med,      4),
    (_sabotage_generatorn_utan_larm,  5),
    (_sabotage_delar_utan_övervakad,  6),
    (_sabotage_takten_är_ett_tal,     7),
    (_sabotage_gränsen_är_fast,       8),
    (_sabotage_passet_räknar_inte_om, 9),
]


def _kör(d: Path, märke: str, prov_f, språk_db) -> list[str]:
    kort = _kopia(d / f"{märke}.db")
    try:
        if prov_f is prov_generatorn_ser:
            return prov_f(kort, språk_db)
        return prov_f(kort)
    finally:
        kort.close()


def main() -> int:
    språk_db = anslut()
    if sqlite3.sqlite_version_info < (3, 25):
        print(f"SQLite {sqlite3.sqlite_version} saknar fönsterfunktioner; "
              f"`övervakade` kan inte köras.")
        return 1
    fel = stumma = 0
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        print(f"{len(PROV)} invarianter, språk {SPRÅK}, "
              f"fönster {LARMFÖNSTER} möten\n")
        for i, (namn, prov_f) in enumerate(PROV):
            brister = _kör(d, f"ren{i}", prov_f, språk_db)
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister[:5]:
                print(f"      {b}")

        print("\nfalsifiering — varje gammalt läge ska fälla sitt prov:")
        for i, (sab, mål) in enumerate(SABOTAGE):
            ångra = sab()
            try:
                brister = _kör(d, f"sab{i}", PROV[mål][1], språk_db)
            except Exception as e:                             # noqa: BLE001
                # ETT SABOTAGE SOM KRASCHAR HAR INTE FÄLLT NÅGOT. Att låta
                # undantaget döda körningen hade dessutom dolt de sabotage
                # som kommer efter — samma fel `tjänsteprov` en gång hade.
                brister = []
                print(f"      (sabotaget kraschade: {type(e).__name__}: {e})")
            finally:
                ångra()
            if not brister:
                stumma += 1
            namn = sab.__doc__.splitlines()[0] if sab.__doc__ else str(i)
            print(f"  {'✓ föll' if brister else '✗ STUMT'}  {namn}"
                  + (f"  ({len(brister)} fynd)" if brister else ""))

    print(f"\n{len(PROV)} invarianter, {fel} brott." if fel
          else f"\n{len(PROV)} invarianter, alla håller.")
    if stumma:
        print(f"{stumma} sabotage fällde inte sitt prov.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
