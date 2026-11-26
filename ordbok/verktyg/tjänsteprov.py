"""Prov för G6: gör alla vägar in i systemet samma sak?

VARFÖR DET HÄR PROVET FINNS. `dagsplan` räknar dagens arbete och är systemets
enda auktoritet på hur mycket nytt som får införas, vad som är förfallet och
om dagen är klar. Den räknar rätt. Men ingenting TVINGAR ändpunkterna att
fråga den, och gör de olika saker säger inget ifrån — båda svaren är i sig
giltiga, de är bara inte samma.

Fem fel av precis den sorten hittades vid ett enda testpass 2026-08-24, alla
för hand. Glosläget delade ut tio nya ord varje gång vyn öppnades utan att
läsa dagsbudgeten (44 införda kort mot ett tak på 34). Räknaren för
återförsök låg alltid en mening efter. Extraknappen var öppen innan dagens
kort var gjorda. Generatorn gav samma mening åtta gånger i rad till passkön.

VAD PROVET INTE ÄR. Det prövar inte om reglerna är RIKTIGA — det är vad
PROBLEM.md är till för. Det prövar bara att alla vägar in lyder samma regel.
`omkastningsprov.py` gör motsvarande för en ren funktion; det här gör det för
tjänsten.

ALDRIG MOT DEN RIKTIGA DATABASEN. Provet övar, svarar fel och inför kort. Det
arbetar därför alltid i en kopia, tagen med SQLites backup så att WAL följer
med — se `kort/db.py`.

Kör:  python ordbok/verktyg/tjänsteprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kort.schemalaggning import Schemaläggare  # noqa: E402
from sprakprog.kort.db import anslut_kort           # noqa: E402
from sprakprog.webb import Övningstjänst  # noqa: E402

#: Så många meningar varje prov kör. Nog för att en tvåtakt (A, B, A, B) ska
#: hinna visa sig, och nog för att dagsbudgeten ska hinna ta slut i de kurser
#: som har ett litet tak.
MENINGAR = 10


def tjänst(kopia: Path):
    """Övningstjänsten mot en kopia av inlärardatabasen.

    GENERATORN FÅR ETT FAST FRÖ. I drift ska samplingen vara slumpmässig, men
    ett prov som samplar olika varje körning är FLAKIGT — och ett flakigt prov
    är sämre än inget, eftersom man slutar tro på det. Mätt: en körning av
    fyra rapporterade "ingen upprepad mening" som stumt, av ingen annan orsak
    än att just den sekvensen råkade variera ändå.
    """
    # BÅDA ANSLUTNINGARNA STÄNGS. `with sqlite3.connect(...)` avslutar en
    # TRANSAKTION, inte anslutningen — den lämnades öppen mot den riktiga
    # kortdatabasen, en per prov. Med sexton prov (åtta plus falsifieringen)
    # låg sexton läsare kvar och varje ny `backup` fick vänta ut dem: mätt
    # 47 minuter väggtid mot 112 sekunder processortid, alltså fyra procents
    # last. Var fas för sig tog under en minut, vilket var det som gjorde
    # felet svårt att se.
    käll = sqlite3.connect(ROT / "kort.db")
    mål = sqlite3.connect(kopia)
    try:
        käll.backup(mål)
    finally:
        mål.close()
        käll.close()
    # `anslut_kort` OCH INTE `sqlite3.connect`: migrationerna körs där, och
    # en kopia som öppnas förbi dem saknar de tabeller appen förutsätter.
    # Mätt när `Pass` infördes: tre prov föll på "no such table" utan att
    # något var fel i koden de skulle pröva.
    kort = anslut_kort(kopia, delad_mellan_trådar=True)
    språk = sqlite3.connect(ROT / "sprak.db", check_same_thread=False)
    språk.row_factory = sqlite3.Row
    # FÄRRE KANDIDATER PER MENING. Proven mäter KONTROLLFLÖDE — att dagen tar
    # slut, att taket håller, att kön töms — och inte hur bra meningen blev.
    # Med driftens 800 kandidater tog en körning 39 minuter när dygnet väl
    # rullat över och kurserna hade riktiga högar, eftersom `dagen tar slut`
    # kan behöva spela igenom hundra steg per kurs. Ett prov som är för dyrt
    # att köra körs inte, och då finns det inte.
    tj = Övningstjänst(kort, språk, kandidater=60)
    äkta = tj._generator

    def frödd(kurs):
        g = äkta(kurs)
        g.rng.seed(0)
        return g

    tj._generator = frödd
    return tj, kort


# ── invarianterna ────────────────────────────────────────────────────

def infört_idag(tj, kurs) -> int:
    return tj._dagsplan(kurs)["infört_idag"]


def prov_glosbudget(tj, kort, kurs) -> list[str]:
    """Ingen ändpunkt får införa fler nya kort än `dagsplan` medger.

    DET HÄR ÄR FELET SOM FAKTISKT HÄNDE. Vyn öppnades om och om igen och gav
    tio ord varje gång; hemskärmen visade rätt tal men ändpunkten frågade
    aldrig. Provet mäter DELTAT det själv orsakar, så det är oberoende av vad
    databasen råkade innehålla innan.
    """
    fel = []
    p = tj._dagsplan(kurs)
    # TAKET FÖR DRILLEN ÄR GLOSRADERNA. Sedan passlagret skiljer dagen på
    # glosor (som möts i drillen) och böjningskort (som möts i en mening) —
    # två potter, inte en. `nya` är den andra potten och säger ingenting om
    # hur många ord drillen får dela ut.
    tak, före = p["glosor"], infört_idag(tj, kurs)
    for _ in range(6):                       # sex besök i glosvyn
        g = tj.glosor(kurs["id"])
        for o in g["ord"]:
            tj.glossvar(kurs["id"], o["kort_id"], True)
    infört = infört_idag(tj, kurs) - före
    if infört > tak:
        fel.append(f"glosläget införde {infört} kort, dagsbudgeten sa {tak}")
    return fel


def prov_visat_lika_styrande(tj, kurs) -> list[str]:
    """Talet en vy VISAR ska komma ur samma anrop som styr handlingen.

    Hemskärmen säger hur många glosor som väntar. Öppnar man vyn ska man få
    just så många — inte fler, inte färre. Två tal om samma sak är hur felet
    ovan kunde uppstå utan att någon märkte det.

    JÄMFÖRELSEN VAR `min(visat, GLOSPORTION)` och det var fel. `GLOSPORTION`
    var ett dagstak när provet skrevs, men är sedan "en lektion per dag" en
    SIDBRYTNING — hur många ord listan visar åt gången, inte hur många dagen
    innehåller. Provet mätte alltså en regel som inte längre gällde, och
    rapporterade brott mot den i kurser som bara hade en stor omgång kvar.
    """
    h = tj.hem(kurs["id"])
    visat = h["idag"]["glosor"]
    ordrad = next((r["nya"] for r in h["typer"] if r["typ"] == "ord"), 0)
    fick = len(tj.glosor(kurs["id"])["ord"])
    fel = []
    if fick != visat:
        fel.append(f"hemskärmen sa {visat} glosor, vyn gav {fick}")
    # OCH UPPDELNINGEN RÄKNAS MED. `ord` står först i introduktionsordningen
    # och tog därför hela dagstaket, medan drillen styrs av `nya_ord` — så
    # rutan sa "Words 7" på en dag där glosläget hade noll att dela ut.
    if ordrad != visat:
        fel.append(f"uppdelningen sa {ordrad} nya ordkort, glosraden sa {visat}")
    return fel


def prov_extra_kräver_klar(tj, kurs) -> list[str]:
    """Extraövning förutsätter att dagens kort är gjorda.

    Att öva extra före de förfallna korten är att välja bort det FSRS garanti
    vilar på — rätt kort i tid — till förmån för tidiga repetitioner, som ger
    mindre (B6).
    """
    h = tj.hem(kurs["id"])
    if not h["idag"]["klar"] and h["extra"]["finns"]:
        return [f"dagen är inte klar men extraövningen erbjuder "
                f"{h['extra']['finns']} kort"]
    return []


def prov_ingen_upprepad_mening(tj, kurs) -> list[str]:
    """En mening får inte upprepas inom minnets fönster.

    B7 säger att ett fallerat kort ska tillbaka i en ANNAN mening, just för
    att se samma sak om och om igen är det som gör att man fastnar. Provet
    svarar avsiktligt fel varje gång, så passkön hålls full — det är då felet
    uppstår.

    FÖNSTRET OCH INTE BARA GRANNPARET. Villkoret var "två gånger i RAD", och
    det var för svagt: med minnet borttaget gav engelskan
    `He sleeps. / She has. / He sleeps. / She has.` — en tvåtakt, som är
    precis den pathologi ett tre djupt minne finns för att bryta, och som
    provet inte såg. Sabotaget rapporterades som STUMT fast felet var
    återinfört.

    Djupet är `Generator._förra_texter`, alltså tre.

    OCH NÖDFALLET ÄR UNDANTAGET, som systemet numera säger ut. Har sökningen
    inget annat än en upprepning tas den — en liten kortlek har inte fler
    meningar än den har, och en upprepning är ärligare än ett oanmält ord
    (C5). Utan flaggan gick de två fallen inte att skilja på, och provet föll
    på franskan med fyra drillade ord där upprepningen var enda utvägen.

    Villkoret är alltså det systemet faktiskt lovar: *en upprepning inom
    fönstret får bara ske när sökningen sa att den inte hade något val.*
    """
    fel, texter = [], []
    fönster = 3       # samma djup som `Generator._förra_texter`
    for _ in range(MENINGAR):
        u = tj.uppgift(kurs["id"])
        if u is None or u.get("tomt"):
            break
        texter.append((u["uppgift"], u.get("nödfall", False)))
        tj.svara(u["id"], "avsiktligt fel svar")
        tj.bokför(u["id"])
    for i, (t, nöd) in enumerate(texter):
        if nöd:
            continue
        if t in [x for x, _ in texter[max(0, i - fönster):i]]:
            fel.append(f"samma mening igen inom {fönster} meningar utan att "
                       f"sökningen sa att den saknade alternativ: {t!r}")
            break
    return fel


def prov_räknaren_är_i_takt(tj, kurs) -> list[str]:
    """Det `svara` rapporterar ska gälla EFTER den här meningen.

    `svara` körs före `bokför`, som är där passkön uppdateras. Att läsa den
    råa kön gav ett tal som alltid låg en mening efter, vilket såg ut som att
    fel "ibland" inte hamnade i återförsöken.
    """
    u = tj.uppgift(kurs["id"])
    if u is None or u.get("tomt"):
        return []
    r = tj.svara(u["id"], "avsiktligt fel svar")
    fällda = {a["kort_id"] for a in r["anmärkningar"] if a["kort_id"]}
    tj.bokför(u["id"])
    if fällda and r["igen"] < len(fällda):
        return [f"{len(fällda)} kort fälldes men räknaren sa {r['igen']}"]
    return []


def prov_dagen_tar_slut(tj, kurs) -> list[str]:
    """Ett pass måste kunna TA SLUT. Rätta svar ska tömma dagen.

    DET HÄR FELET LÅSTE EN HEL KURS. Med sex ord införda och sju böjningskort
    kvar av dagens tilldelning krävde vartenda ett något ordförrådet inte hade
    — `pres_2sg` utan `tu`, `sg` utan substantiv, hjälpverbet för en tempus
    nivån inte öppnat. Passet gav fyra meningar i evig rundgång med täckning
    NOLL, och hemskärmen stod kvar på "7 new" dygnet ut. Mätt: 330 meningar,
    inget kort infört, ingen dag avslutad.

    Nödutgången fanns men krävde FÖRFALLNA kort. Onåbarheten gäller hela kön,
    och kön är förfallna plus passkön plus dagens nya.

    Provet svarar RÄTT hela vägen, så ingenting hamnar i passkön: då ska dagen
    ta slut. Taket är generöst — det prövar terminering, inte längd.
    """
    # `_dagsplan` OCH INTE `hem`. Hemskärmen räknar också NÄSTA NIVÅS
    # byggbarhet — tvåhundra renderingar i en kopia av kortleken — och cachen
    # töms vid varje bokförd mening. Mätt: 7,0 s per `hem` efter en bokföring
    # mot 0,007 s för `_dagsplan`, alltså tusen gånger. Provet spelar igenom
    # hundra steg per kurs, så skillnaden var 39 minuter mot en dryg minut.
    # Övningsskärmen gör redan samma sak av samma skäl (`dagsläge`).
    tak = 120
    for i in range(tak):
        h = tj._dagsplan(kurs)
        if h["klar"]:
            return []
        if h["nya_ord"]:
            for o in tj.glosor(kurs["id"])["ord"]:
                tj.glossvar(kurs["id"], o["kort_id"], True)
            continue
        u = tj.uppgift(kurs["id"])
        if u is None or u.get("tomt"):
            return []
        tj.svara(u["id"], tj._öppna[u["id"]][1].text)
        tj.bokför(u["id"])
    return [f"dagen tog inte slut på {tak} steg med bara rätta svar"]


def prov_uppgiften_överlever(tj, kurs) -> list[str]:
    """Lämnar man vyn och kommer tillbaka ska det vara SAMMA mening.

    En ny mening vid varje återkomst är inte bara onödigt arbete: den mening
    som byggdes valdes för att den täckte något bestämt, och att kasta den och
    bygga en ny gör vilket kort som övas till en funktion av hur man klickar.
    """
    a = tj.uppgift(kurs["id"])
    if a is None or a.get("tomt"):
        return []
    tj.hem(kurs["id"])                       # ut ur passvyn
    b = tj.uppgift(kurs["id"])
    if b is None or b.get("id") != a["id"] or b.get("uppgift") != a["uppgift"]:
        return [f"uppgiften byttes ut när vyn lämnades: "
                f"{a['uppgift']!r} → {(b or {}).get('uppgift')!r}"]
    # Och efter ett svar ska nästa vara en NY.
    tj.svara(a["id"], ""); tj.bokför(a["id"])
    c = tj.uppgift(kurs["id"])
    if c is not None and not c.get("tomt") and c.get("id") == a["id"]:
        return ["samma uppgift kom tillbaka efter att den besvarats"]
    return []


def prov_extraövningen_går_att_köra(tj, kort, kurs) -> list[str]:
    """Lovar extraläget kort ska de gå att få ut.

    `kommande()` — extraövningens kö — hade fyra platshållare och tre
    bindningar, så varje anrop som faktiskt nådde frågan kastade
    `ProgrammingError`. Felet syntes aldrig i bruk: `finns_extra` var noll i
    alla kurser som testats för hand, så knappen var låst och frågan ställdes
    inte. En trasig SQL-sats kan ligga tyst hur länge som helst bakom en
    grind som råkar vara stängd.

    KÖN PRÖVAS DIREKT, DAGEN SPELAS INTE IGENOM. Första versionen övade hela
    dagen klar för varje kurs, eftersom extraläget är låst dessförinnan (B6) —
    och den tog 39 minuter när dygnet väl rullat över och kurserna hade
    riktiga högar. Ett prov som är för dyrt att köra körs inte, och då finns
    det inte.

    Frågan är ändå den enda som behöver ställas till KÖN: den var trasig i
    sig, oavsett hur man kom fram till den. Samstämmigheten mellan det som
    visas och det som ges prövas sedan bara när dagen RÅKAR vara klar.
    """
    fel = []
    try:
        Schemaläggare(kort).kommande(kurs["målspråk"], 30)
    except Exception as e:
        fel.append(f"extraövningens kö kastade {type(e).__name__}: {e}")
    extra = tj._extraläge(tj._dagsplan(kurs))
    if fel or not extra["finns"]:
        return fel
    try:
        u = tj.uppgift(kurs["id"], extra=True)
    except Exception as e:
        return [f"extraläget lovade {extra['finns']} kort men kastade "
                f"{type(e).__name__}: {e}"]
    if u is None or u.get("tomt"):
        # ATT INGET GÅR ATT BYGGA ÄR ETT GILTIGT SVAR (B8) — men då ska talet
        # sluta lovas. Det är samma regel som allt annat här: den som VISAS
        # och den som STYR måste vara samma.
        kvar = tj._extraläge(tj._dagsplan(kurs))["finns"]
        return ([] if not kvar else
                [f"extraläget gav {u!r} men lovar fortfarande {kvar} kort"])
    return []


PROV = [
    ("dagsbudgeten hålls av alla vägar in", prov_glosbudget),
    ("extraövningen går att köra", prov_extraövningen_går_att_köra),
    ("passet tar slut", lambda tj, k, kurs: prov_dagen_tar_slut(tj, kurs)),
    ("uppgiften överlever att vyn lämnas",
     lambda tj, k, kurs: prov_uppgiften_överlever(tj, kurs)),
    ("visat tal = styrande tal", lambda tj, k, kurs: prov_visat_lika_styrande(tj, kurs)),
    ("extraövning kräver klar dag", lambda tj, k, kurs: prov_extra_kräver_klar(tj, kurs)),
    ("ingen upprepad mening", lambda tj, k, kurs: prov_ingen_upprepad_mening(tj, kurs)),
    ("räknaren i takt med bokföringen", lambda tj, k, kurs: prov_räknaren_är_i_takt(tj, kurs)),
]


# ── falsifieringen ───────────────────────────────────────────────────
#
# ETT PROV SOM INTE KAN FALLA BEVISAR INGENTING. Varje invariant har därför
# ett SABOTAGE: den gamla, trasiga varianten av regeln. Kör man provet med
# sabotaget påslaget SKA det falla, och gör det inte det är det provet som är
# fel — inte koden.
#
# Det här är samma lärdom som omkastningsprovet gav: den första invarianten
# jag skrev där var tom och kunde inte falla, och den andra var för stark.

def _sabotera(namn: str):
    """Återställ det gamla felet. Returnerar en funktion som ångrar det."""
    from sprakprog.webb import Övningstjänst
    from sprakprog.generator import Generator

    if namn in ("dagsbudgeten hålls av alla vägar in", "visat tal = styrande tal"):
        # Före fixen läste glosläget aldrig dagsbudgeten.
        äkta = Övningstjänst.glosor
        def utan_budget(själv, kurs_id, antal=None):
            with själv.lås:
                kurs = själv._kurs(kurs_id)
                rader = Schemaläggare(själv.kort_db).oglosade(
                    kurs["målspråk"], antal or själv.GLOSPORTION)
                return {"ord": [{"kort_id": r["id"], "mål": r["facit"],
                                 "källa": None} for r in rader], "kvar": 0}
        Övningstjänst.glosor = utan_budget
        return lambda: setattr(Övningstjänst, "glosor", äkta)

    if namn == "extraövningen går att köra":
        # Den trasiga frågan, återinförd: fyra platshållare, tre bindningar.
        äkta = Schemaläggare.kommande

        def trasig(själv, språk, gräns=30, nu=None):
            from datetime import UTC, datetime
            tid = (nu or datetime.now(UTC)).isoformat()
            return själv.db.execute(
                """SELECT * FROM Kort
                   WHERE språk = ? AND schemalagt = 1 AND sedd IS NOT NULL
                     AND sedd < ?
                     AND förfaller IS NOT NULL AND förfaller > ?
                   ORDER BY förfaller LIMIT ?""",
                (språk, tid, gräns)).fetchall()
        Schemaläggare.kommande = trasig
        return lambda: setattr(Schemaläggare, "kommande", äkta)

    if namn == "passet tar slut":
        # Före rättelsen krävde nödutgången FÖRFALLNA kort, så en kö som bara
        # innehöll onåbara NYA kort tog aldrig slut. Och `oövade` silades inte,
        # så ett ord man inte kan bygga en mening kring låg i kön och räknades
        # som TÄCKT av varje mening — vilket höll `täckta` över noll.
        # `staticmethod` BÅDA VÄGARNA. Att läsa ut den ger den nakna
        # funktionen, och skriver man tillbaka den rakt av blir den en vanlig
        # metod som får `self` som första argument. Sabotaget lämnade då
        # klassen trasig för de prov som kom efter.
        äkta = Övningstjänst.__dict__["_onåbar"]
        Övningstjänst._onåbar = staticmethod(
            lambda f, p: f.poäng is not None and f.poäng.täckta == 0
            and bool(p["förfallna"]))
        äkta_sil = Generator.övningsbara
        Generator.övningsbara = lambda själv, koncept: list(koncept)

        def ångra():
            Övningstjänst._onåbar = äkta
            Generator.övningsbara = äkta_sil
        return ångra


    if namn == "uppgiften överlever att vyn lämnas":
        äkta = Övningstjänst.uppgift

        def alltid_ny(själv, kurs_id, *, extra=False):
            själv._pågående.clear()
            return äkta(själv, kurs_id, extra=extra)
        Övningstjänst.uppgift = alltid_ny
        return lambda: setattr(Övningstjänst, "uppgift", äkta)

    if namn == "extraövning kräver klar dag":
        äkta = Övningstjänst._extraläge
        Övningstjänst._extraläge = staticmethod(
            lambda p: {"nya": p["nya_extra"], "tidiga": p["tidiga"],
                       "finns": p["finns_extra"], "låst": False})
        return lambda: setattr(Övningstjänst, "_extraläge", äkta)

    if namn == "ingen upprepad mening":
        # SABOTAGET MÅSTE ÅTERSKAPA HELA DET GAMLA LÄGET, inte bara den ena
        # raden. Att enbart tömma meningsminnet räckte inte längre: sedan de
        # oövade orden lades i kön (F4) roterar målorden ändå, så meningarna
        # varierar av en annan orsak och provet blev STUMT.
        #
        # Att provet upptäckte det är hela poängen med falsifieringen — en
        # kontroll som slutat kunna falla ser likadan ut som en som håller.
        äkta = Generator._sök
        äkta_uppg = Övningstjänst.uppgift

        def utan_minne(själv, *a, **kw):
            själv._förra_texter = []
            return äkta(själv, *a, **kw)

        def utan_oövade(själv, kurs_id, *, extra=False):
            # Smal kö och full passkö — precis läget där felet uppstod.
            import sprakprog.webb as webb
            spara = webb.oövade_koncept
            webb.oövade_koncept = lambda *a, **kw: []
            try:
                return äkta_uppg(själv, kurs_id, extra=extra)
            finally:
                webb.oövade_koncept = spara

        Generator._sök = utan_minne
        Övningstjänst.uppgift = utan_oövade

        def ångra():
            Generator._sök = äkta
            Övningstjänst.uppgift = äkta_uppg
        return ångra

    if namn == "räknaren i takt med bokföringen":
        # Före fixen lästes den RÅA kön, alltså läget före den här meningen.
        äkta = Övningstjänst._igen_efter
        Övningstjänst._igen_efter = staticmethod(lambda g, utfall: g.passkö())
        return lambda: setattr(Övningstjänst, "_igen_efter", äkta)

    raise KeyError(namn)


def main() -> int:
    fel = 0
    with tempfile.TemporaryDirectory() as d:
        for nr, (namn, kör) in enumerate(PROV):
            # EGEN KOPIA PER PROV. Proven inför kort och svarar fel, så de
            # skulle annars ärva varandras tillstånd och bli beroende av
            # ordningen — och ett prov som bara faller ibland är värre än
            # inget.
            tj, kort = tjänst(Path(d) / f"prov{nr}.db")
            brister: list[str] = []
            # fetchall: proven skriver i samma anslutning, och en lat
            # markör tar då tyst slut. Se introduktionsprov._kör.
            for kurs in kort.execute(
                    "SELECT * FROM Kurs ORDER BY målspråk").fetchall():
                for b in kör(tj, kort, kurs):
                    brister.append(f"[{kurs['målspråk']}] {b}")
            kort.close()
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister:
                print(f"      {b}")
    print(f"\n{len(PROV)} invarianter, {fel} brott." if fel
          else f"\n{len(PROV)} invarianter, alla håller.")

    # OCH BEVISA ATT DE KAN FALLA.
    print("\nfalsifiering — med det gamla felet återinfört ska varje prov falla:")
    stumma = 0
    with tempfile.TemporaryDirectory() as d:
        for nr, (namn, kör) in enumerate(PROV):
            ångra = _sabotera(namn)
            try:
                tj, kort = tjänst(Path(d) / f"sab{nr}.db")
                kurser = kort.execute("SELECT * FROM Kurs").fetchall()
                brister = [b for kurs in kurser
                           for b in kör(tj, kort, kurs)]
                kort.close()
            finally:
                ångra()
            if not brister:
                stumma += 1
            print(f"  {'✓ föll' if brister else '✗ STUMT PROV'}  {namn}")
    if stumma:
        print(f"\n{stumma} prov kunde inte falla. Ett prov som inte kan falla "
              f"bevisar ingenting.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
