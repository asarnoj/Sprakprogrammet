"""Prov för D3: får en mening innehålla ett ord användaren aldrig mött?

Nej. Ordkort införs i glosläget och ingen annanstans (C2/D3) — en mening kan
inte lära ut ett ord, bara använda det. Ändå gjorde den det, tre gånger om, av
tre olika skäl som alla såg ut som varandras motsats.

VAD SOM FAKTISKT HÄNDE, 2026-08-24. Sex ord introducerades i drillen 14:19.
Passet gav sedan `Un frère existe.` — och `un` var inte ett av de sex. Loggen
visar ordkortet för `artikel_obestamd` betygsatt 14:21:41 med mening 130, alltså
infört av meningen. I andra körningar var det `coûter` och `avoir`.

DE TRE VÄGARNA IN:

  1. `osedda(uteslut=("ord",))` höll ordKORTET borta men inte ordet. Egenskaps-
     och stamkorten för samma koncept kom in i kön, blev MÅLORD, och samplaren
     byggde meningen kring dem. Målordet går förbi `Samplare.begränsa`, som
     bara styr fyllnaden. Mätt: tio meningar i rad införde vart och ett ett ord
     som inte var något av dagens — `homme`, `fille`, `famille`, `frère cadet`.

  2. `okända <= 1` i `Generator._sök`. En nykvot från tiden då meningen FICK
     införa ord. Den regeln försvann; kvoten blev kvar och var då den sista
     vägen in — för strukturorden, som renderaren skjuter in på egen hand.
     Artikeln i `Un frère existe.` väljs aldrig av `_välj`.

  3. `schemalagt = 1` i `osedda`. Flaggan betyder "möts för ofta för att
     spacing ska betyda något" — inte "kan redan". Att låta den gälla
     INTRODUKTIONEN gjorde vanliga ord till ord som aldrig lärs ut. De tre
     franska ordkort som var `schemalagt = 0` var exakt de tre som dök upp
     oannonserade: `un`, `avoir`, `coûter`.

Provet nollställer ett språk, låter drillen införa N ord, kör ett pass och
frågar en enda sak: rörde någon mening ett ordkort som inte var infört?

ALDRIG MOT DEN RIKTIGA DATABASEN — kopia via SQLites backup, som allt annat
som skriver. Kör:  python ordbok/verktyg/introduktionsprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut                      # noqa: E402
from sprakprog.generator import Generator            # noqa: E402
from sprakprog.kort import schemalaggning            # noqa: E402
from sprakprog.kort.schemalaggning import Schemaläggare  # noqa: E402
from sprakprog.kort.db import anslut_kort           # noqa: E402
from sprakprog.webb import Övningstjänst            # noqa: E402

#: Hur många ord drillen får införa innan passet körs. Tre lägen, för att de
#: tre vägarna in visar sig vid olika ordförrådsstorlek: strukturorden redan
#: vid sex, målordsläckan först när det finns böjningskort att köa.
DRILLADE = (6, 12, 25)

#: Meningar per läge. Läckan var inte sällsynt — den träffade var tredje
#: mening — så tolv räcker gott för att den ska synas.
MENINGAR = 12

#: Dagens tak på nya kort. Måste vara > 0, annars fylls kön aldrig på med
#: osedda kort och provet mäter ingenting.
NYA_TILLÅTNA = 19


def _kopia(mål: Path) -> sqlite3.Connection:
    # Anslutningarna stängs — se `tjänsteprov.tjänst` för vad som händer
    # annars: `with` avslutar transaktionen, inte anslutningen.
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(mål)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    return anslut_kort(mål, delad_mellan_trådar=True)


def _kallstart(kort: sqlite3.Connection, språk: str, n: int) -> set[str]:
    """Nollställ språket och låt drillen införa `n` ord. Ger de sedda koncepten.

    Drillen simuleras med `oglosade`, alltså exakt den kö glosläget delar ut —
    inte en egen ordning. Ett prov som väljer sina egna ord skulle inte kunna
    upptäcka att drillen aldrig når fram till ett ord.
    """
    kort.execute("""UPDATE Kort SET sedd = NULL, förfaller = NULL, tillstånd = 1,
                        steg = NULL, stabilitet = NULL, svårighet = NULL,
                        antal = 0, fall = 0
                    WHERE språk = ?""", (språk,))
    drill = Schemaläggare(kort).oglosade(språk, n)
    kort.executemany(
        """UPDATE Kort SET sedd = '2026-01-01T10:00:00+00:00',
               förfaller = '2026-01-03T10:00:00+00:00', tillstånd = 1,
               stabilitet = 2.0, svårighet = 5.0, antal = 1 WHERE id = ?""",
        [(r["id"],) for r in drill])
    kort.commit()
    return {r["koncept"] for r in kort.execute(
        "SELECT DISTINCT koncept FROM Kort WHERE språk = ? AND sedd IS NOT NULL "
        "AND koncept IS NOT NULL", (språk,))}


# ── invarianterna ────────────────────────────────────────────────────
#
# TRE FIXAR, TRE INVARIANTER. Att pröva alla tre genom MENINGEN gick inte:
# var och en räcker för att stoppa läckan, så att ta bort en åt gången syns
# inte i utfallet. Det är djupförsvar och inte tre halva lösningar — men ett
# prov som bara kan se den yttersta av dem bevisar ingenting om de andra två.
# Därför mäts varje fix där den arbetar.


def prov_kön(kort: sqlite3.Connection, kurs: sqlite3.Row, n: int) -> list[str]:
    """`osedda` får inte lämna ut ett kort vars ORD ännu inte är infört.

    Det var väg 1: `uteslut=("ord",)` höll ordkortet borta men inte ordet.
    Egenskapskortet för `coûter` kom in i kön, blev målord, och samplaren
    byggde meningen kring det — förbi `begränsa`, som bara styr fyllnaden.
    """
    språk = kurs["målspråk"]
    _kallstart(kort, språk, n)
    osedda_ord = {r["koncept"] for r in kort.execute(
        """SELECT koncept FROM Kort WHERE språk = ? AND typ = 'ord'
           AND sedd IS NULL AND koncept IS NOT NULL""", (språk,))}
    fel = []
    for r in Schemaläggare(kort).osedda(språk, 40, uteslut=("ord",)):
        if r["koncept"] in osedda_ord:
            fel.append(f"{n} drillade: kön bjuder ut {r['typ']}-kortet för "
                       f"{r['koncept']!r}, vars ord inte är infört")
    return fel[:3]


def prov_drillen(kort: sqlite3.Connection, kurs: sqlite3.Row, n: int) -> list[str]:
    """Varje ordkort måste gå att NÅ genom glosläget.

    Det var väg 3: `schemalagt = 0` betyder "möts för ofta för att spacing ska
    betyda något" — inte "kan redan". Som grind på introduktionen gjorde den
    vanliga ord till ord som aldrig lärs ut, och sedan lät meningarna
    presentera dem ändå. `un`, `avoir` och `coûter` var exakt de tre franska
    ordkort som hade flaggan.

    Provet drar drillen tom och ser efter vad som blev kvar. `n` används inte
    — invarianten gäller hela ordförrådet — så det körs bara en gång.
    """
    if n != DRILLADE[0]:
        return []
    språk = kurs["målspråk"]
    _kallstart(kort, språk, 0)
    s = Schemaläggare(kort)
    nådda: set[int] = set()
    while (parti := [r for r in s.oglosade(språk, 50) if r["id"] not in nådda]):
        nådda.update(r["id"] for r in parti)
        kort.executemany(
            "UPDATE Kort SET sedd = '2026-01-01T10:00:00+00:00' WHERE id = ?",
            [(r["id"],) for r in parti])
    kort.commit()
    kvar = kort.execute(
        """SELECT COUNT(*) FROM Kort WHERE språk = ? AND typ = 'ord'
           AND sedd IS NULL""", (språk,)).fetchone()[0]
    return ([] if not kvar else
            [f"{kvar} ordkort går inte att nå genom glosläget"])


def prov_meningen(kort: sqlite3.Connection, kurs: sqlite3.Row,
                  n: int) -> list[str]:
    """Ingen mening får införa ett ordkort på egen hand.

    Det var väg 2: `okända <= 1`, en nykvot från tiden då meningen FICK införa
    ord. Den släppte in STRUKTURORDEN — artikeln i `Un frère existe.` väljs
    aldrig av `_välj` utan följer av `Bestämdhet.OBESTÄMD`, så `begränsa` ser
    den aldrig.

    Provet ställer upp just det läget: drillen körs, och sedan tas artiklarna
    tillbaka. Det är ett ÄKTA tillstånd — dag ett, innan drillen nått dit —
    och det är enda sättet att pröva den innersta grinden, eftersom de två
    yttre annars hinner först.
    """
    språk = kurs["målspråk"]
    sedda = _kallstart(kort, språk, n)
    strukturord = {r["koncept"] for r in kort.execute(
        """SELECT DISTINCT koncept FROM Kort WHERE språk = ? AND typ = 'ord'
           AND ordklass = 'Artikel'""", (språk,))}
    if strukturord:
        kort.execute(
            f"""UPDATE Kort SET sedd = NULL, antal = 0 WHERE språk = ? AND koncept IN
                ({','.join('?' * len(strukturord))})""", (språk, *strukturord))
        kort.commit()
        sedda -= strukturord
    if not sedda:
        return []
    g = Generator(anslut(), kort, språk, källspråk=kurs["källspråk"],
                  nivå=kurs["nivå"], cefr=kurs["cefr"],
                  budget=kurs["budget"], frö=7)
    läckta: dict[str, str] = {}
    for _ in range(MENINGAR):
        f = g.föreslå(kandidater=300, nya_tillåtna=NYA_TILLÅTNA, oövade=[])
        if f is None:
            continue
        for k in f.kort:
            if (k["typ"] == "ord" and k["sedd"] is None
                    and k["koncept"] not in sedda):
                läckta.setdefault(k["koncept"], f.text)
    return [f"{n} drillade: meningen införde {k!r} själv — {t!r}"
            for k, t in sorted(läckta.items())]


def prov_tjänsten(kort: sqlite3.Connection, kurs: sqlite3.Row,
                  n: int) -> list[str]:
    """Samma invariant, men hela vägen genom ÖVNINGSTJÄNSTEN.

    G6:S LÄRDOM. Att motorn har rätt gör inte att skärmen har det. Fem fel av
    precis den sorten hittades vid ett enda testpass — alla i sömmen mellan
    generator och vy, inget av dem i generatorn. Provet ovan anropar
    `Generator.föreslå` direkt och skulle inte se ett enda av dem.

    Här nollställs kursen, glosläget drillar `n` ord, och passet körs med FEL
    svar hela vägen — så passkön hålls full, vilket är när målorden styrs om
    och läckan var som störst.

    OMGÅNGENS STORLEK MÅSTE VARA PROVETS OCH INTE DAGSPLANENS. Utan `n` bestäms
    den av kursens minuter och den uppmätta takten i den RIKTIGA databasen, så
    provet ändrade sig när Julius övade: med en stor omgång hann drillen dela
    ut artikeln själv, och sabotaget hade inget kvar att läcka. Provet
    rapporterade STUMT av en orsak som inte hade med koden att göra.
    """
    if n != DRILLADE[0]:
        return []
    tj = _frödd_tjänst(kort)
    tj.nollställ(kurs["id"], "RESET")
    kurs = kort.execute("SELECT * FROM Kurs WHERE id = ?", (kurs["id"],)).fetchone()
    for o in tj.glosor(kurs["id"], n)["ord"]:
        tj.glossvar(kurs["id"], o["kort_id"], True)
    efter_drill = _sedda_ord(kort, kurs["målspråk"])
    for _ in range(MENINGAR):
        u = tj.uppgift(kurs["id"])
        if u is None or u.get("tomt"):
            break
        tj.svara(u["id"], "")           # fel svar: passkön hålls full
        tj.bokför(u["id"])
    läckta = _sedda_ord(kort, kurs["målspråk"]) - efter_drill
    return [f"passet införde {k!r} utan att drillen gjort det"
            for k in sorted(läckta)]


def _frödd_tjänst(kort: sqlite3.Connection) -> Övningstjänst:
    """Övningstjänsten med FAST FRÖ i generatorn.

    I drift ska samplingen vara slumpmässig. Ett prov som samplar olika varje
    körning är däremot FLAKIGT, och ett flakigt prov är sämre än inget — man
    slutar tro på det. Mätt här: samma sabotage gav 0, 3, 0, 3 fynd i fyra
    körningar, av ingen annan orsak än att substantivmeningen ibland inte
    råkade komma inom tolv försök. Samma lärdom som `tjänsteprov.py`.
    """
    tj = Övningstjänst(kort, anslut())
    äkta = tj._generator

    def frödd(kurs):
        g = äkta(kurs)
        g.rng.seed(0)
        return g
    tj._generator = frödd
    return tj


def _sedda_ord(kort: sqlite3.Connection, språk: str) -> set[str]:
    return {r["koncept"] for r in kort.execute(
        """SELECT koncept FROM Kort WHERE språk = ? AND typ = 'ord'
           AND sedd IS NOT NULL""", (språk,))}


PROV = [("kön — inget böjningskort före sitt ord", prov_kön),
        ("drillen — varje ordkort går att nå", prov_drillen),
        ("meningen — inget ord införs av en mening", prov_meningen),
        ("tjänsten — samma sak hela vägen genom vyerna", prov_tjänsten)]


# ── falsifiering: varje gammal väg in ska fälla sitt prov ────────────

def _sabotage_målord():
    """Väg 1: ta bort ordningsregeln, så böjningskort för okända ord köas."""
    orig = Schemaläggare.osedda

    def utan(self, språk, gräns=100, uteslut=()):
        ordning = " ".join(f"WHEN '{t}' THEN {i}" for i, t
                           in enumerate(self.INTRODUKTIONSORDNING))
        filter = ("AND typ NOT IN (" + ",".join("?" * len(uteslut)) + ")"
                  if uteslut else "")
        rader = self.db.execute(
            f"""SELECT * FROM Kort
                WHERE språk = ? AND sedd IS NULL {filter}
                  AND (schemalagt = 1 OR typ = 'ord')
                ORDER BY CASE typ {ordning} ELSE 99 END,
                         rang, räckvidd DESC, id LIMIT ?""",
            (språk, *uteslut, gräns * 4)).fetchall()
        return schemalaggning._fläta(rader, gräns)

    Schemaläggare.osedda = utan
    return lambda: setattr(Schemaläggare, "osedda", orig)


def _sabotage_schemalagt():
    """Väg 3: låt `schemalagt` grinda introduktionen igen.

    SABOTAGET MÅSTE LIGGA I FRÅGAN, inte som ett filter på svaret. En första
    version filtrerade bort de oschemalagda EFTER `osedda` och tog ett bredare
    fönster för att kompensera — och fick då en annan omflätning: drillen gav
    sex pronomen i stället för den historiska blandningen med två substantiv.
    Utan substantiv behövs ingen artikel, och läckan uppstod aldrig. Provet
    rapporterade STUMT fast felet var återinfört.
    """
    orig = Schemaläggare.osedda

    def bara_schemalagda(self, språk, gräns=100, uteslut=()):
        ordning = " ".join(f"WHEN '{t}' THEN {i}" for i, t
                           in enumerate(self.INTRODUKTIONSORDNING))
        filter = ("AND typ NOT IN (" + ",".join("?" * len(uteslut)) + ")"
                  if uteslut else "")
        rader = self.db.execute(
            f"""SELECT * FROM Kort
                WHERE språk = ? AND schemalagt = 1 AND sedd IS NULL {filter}
                  AND NOT EXISTS (SELECT 1 FROM Kort o
                                  WHERE o.språk = Kort.språk
                                    AND o.koncept = Kort.koncept
                                    AND o.typ = 'ord' AND o.sedd IS NULL
                                    AND o.id <> Kort.id)
                ORDER BY CASE typ {ordning} ELSE 99 END,
                         rang, räckvidd DESC, id LIMIT ?""",
            (språk, *uteslut, gräns * 4)).fetchall()
        return schemalaggning._fläta(rader, gräns)

    Schemaläggare.osedda = bara_schemalagda
    return lambda: setattr(Schemaläggare, "osedda", orig)


def _sabotage_nykvot():
    """Väg 2: återinför `okända <= 1` i sökningen.

    Regeln patchas som METOD och inte genom att skriva i källfilen. Den vägen
    fanns här först och var en tyst fälla: `.pyc`-cachen jämför källans mtime i
    hela sekunder, så när sabotaget skrevs, ångrades och skrevs igen inom samma
    sekund läste omladdningen gammal bytekod. Provet sa STUMT om ett sabotage
    som fällde det när det kördes ensamt — alltså precis den sortens fel som
    får en att sluta tro på provet.
    """
    orig = Generator._duglig
    Generator._duglig = (
        lambda själv, okända, text: okända <= 1
        and text not in själv._förra_texter)
    return lambda: setattr(Generator, "_duglig", orig)


def _sabotage_kallstart():
    """Väg 2 OCH 3 tillsammans — läget som faktiskt inträffade 14:21:41.

    Ingen av dem ensam läcker genom tjänsten, och det är inte en svaghet hos
    provet utan hur djupförsvar ser ut: utan `schemalagt`-grinden drillas `un`
    ändå, och utan nykvoten hoppar passet bara över artikeln. Först när
    drillen inte når ordet OCH sökningen släpper igenom ett okänt står
    `Un frère existe.` på skärmen med `un` osett — vilket är exakt vad loggen
    visar för mening 130.

    Ett sabotage som återskapar ETT av felen skulle vara stumt här och därmed
    ljuga om att provet inte fångar något. Det här återskapar TILLSTÅNDET.
    """
    a, b = _sabotage_schemalagt(), _sabotage_nykvot()

    def ångra():
        b()
        a()
    return ångra


#: Vilket sabotage som ska fälla vilket prov, som index i `PROV`.
SABOTAGE = [(_sabotage_målord, 0), (_sabotage_schemalagt, 1),
            (_sabotage_nykvot, 2), (_sabotage_kallstart, 3)]


def _kör(kort, prov_f) -> list[str]:
    """Kör ett prov för varje kurs och läge.

    `fetchall` OCH INTE EN LAT MARKÖR. Proven skriver i samma anslutning —
    `nollställ` raderar och befolkar om — och en markör man itererar över
    medan man skriver i den tar tyst slut. Provet gick igenom alla kurser
    när loopen skrevs för hand och bara den första när den var en
    list-comprehension över markören, alltså rapporterade STUMT för ett
    sabotage som fällde det direkt. Ett prov som tystnar när det skrivs i
    databasen är värre än inget.
    """
    kurser = kort.execute("SELECT * FROM Kurs ORDER BY målspråk").fetchall()
    return [f"[{kurs['målspråk']}] {b}" for kurs in kurser
            for n in DRILLADE for b in prov_f(kort, kurs, n)]


def main() -> int:
    fel = stumma = 0
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        print(f"{len(PROV)} invarianter, {len(DRILLADE)} lägen per kurs "
              f"({', '.join(str(n) for n in DRILLADE)} drillade ord)\n")
        for i, (namn, prov_f) in enumerate(PROV):
            # EGEN KOPIA PER PROV. Proven nollställer språk och inför kort;
            # delade de databas skulle de ärva varandras tillstånd.
            kort = _kopia(d / f"ren{i}.db")
            brister = _kör(kort, prov_f)
            kort.close()
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister[:6]:
                print(f"      {b}")
            if len(brister) > 6:
                print(f"      … och {len(brister) - 6} till")

        print("\nfalsifiering — varje gammal väg in ska fälla sitt prov:")
        for i, (sab, mål) in enumerate(SABOTAGE):
            namn, prov_f = PROV[mål]
            ångra = sab()
            try:
                kort = _kopia(d / f"sab{i}.db")
                brister = _kör(kort, prov_f)
                kort.close()
            finally:
                ångra()
            if not brister:
                stumma += 1
            print(f"  {'✓ föll' if brister else '✗ STUMT'}  {namn}"
                  + (f"  ({len(brister)} fynd)" if brister else ""))

    print(f"\n{len(PROV)} invarianter, {fel} brott." if fel
          else f"\n{len(PROV)} invarianter, alla håller.")
    if stumma:
        print(f"{stumma} sabotage fällde inte sitt prov. Ett prov som inte "
              f"kan falla bevisar ingenting.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
