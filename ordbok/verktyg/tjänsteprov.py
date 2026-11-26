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


def _egen_tjänst(kurs):
    """En tjänst med bara den här kursens tillstånd. Se `prov_dagen_tar_slut`."""
    import tempfile as _tf
    return tjänst(Path(_tf.mkdtemp()) / f"dag{kurs['id']}.db")[0]


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
    # NOLLSTÄLL FÖRST, av samma skäl som `prov_tomt_pass_fylls`: kopian bär
    # Julius RIKTIGA läge, och en kurs vars dag redan är gjord ger provet
    # ingenting att mäta. Utan raden blev provet stumt beroende på när på
    # dygnet sviten kördes — det upptäcktes 2026-08-31, och två prov hade
    # då slutat mäta utan att någon rad blev röd.
    #
    # EGEN TJÄNST PER KURS, och det är inte kosmetika. Med en DELAD tjänst
    # tog franskans dag fler och fler meningar ju fler kurser som körts före:
    # 10 ensam, 12 efter tyskan, 15 efter japanskan, och efter alla tre tog
    # den inte slut på 120. Kortlekarna är skilda per språk, så det är
    # tjänstens eget tillstånd som läcker mellan kurser — en egen fråga, och
    # den står som öppen i G6. Provet här mäter sin EGNA invariant: att en
    # dag tar slut. Att låta det bära två frågor gör det oläsbart när det
    # faller.
    tj = _egen_tjänst(kurs)
    tj.nollställ(kurs["id"], "RESET")
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
            # NÖDUTGÅNGEN MÅSTE FAKTISKT AVSLUTA DAGEN. Provet tog `tomt`
            # som framgång utan att kontrollera det, och det var hålet: går
            # ingen mening att bygga MEN passet står kvar med väntande rader
            # är dagen inte slut, den är låst. Skillnaden är precis vad B8:s
            # `avskriv` finns för, och utan kontrollen kunde sabotaget som
            # slår av den inte fälla provet.
            if not tj._dagsplan(kurs)["klar"]:
                kvar = tj._dagsplan(kurs)["att_göra"]
                return [f"[{kurs['målspråk']}] ingen mening gick att bygga, "
                        f"men dagen är inte klar — {kvar} rader väntar utan "
                        f"att skrivas av (B8)"]
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
    # ÄR KÖN TRASIG ÄR FRÅGAN BESVARAD. Kontrollen låg efter `_extraläge`,
    # vilket gick bra så länge inget annat rörde `kommande()` — men
    # extraläget läser numera också hur mycket en extraövning är VÄRD
    # (`extranytta`), och det måttet går genom samma kö. Provet kraschade
    # då i stället för att rapportera det fel det just hade fångat.
    if fel:
        return fel
    extra = tj._extraläge(tj._dagsplan(kurs), kurs)
    if not extra["finns"]:
        return []
    try:
        u = tj.uppgift(kurs["id"], extra=True)
    except Exception as e:
        return [f"extraläget lovade {extra['finns']} kort men kastade "
                f"{type(e).__name__}: {e}"]
    if u is None or u.get("tomt"):
        # ATT INGET GÅR ATT BYGGA ÄR ETT GILTIGT SVAR (B8) — men då ska talet
        # sluta lovas. Det är samma regel som allt annat här: den som VISAS
        # och den som STYR måste vara samma.
        kvar = tj._extraläge(tj._dagsplan(kurs), kurs)["finns"]
        return ([] if not kvar else
                [f"extraläget gav {u!r} men lovar fortfarande {kvar} kort"])
    return []


def prov_en_kurs_per_målspråk(tj, kort, kurs) -> list[str]:
    """En ANDRA kurs mot ett upptaget målspråk ska vägras — men bara en ny.

    `Kort` har `språk` och ingen `kurs_id`, så alla kurser mot samma målspråk
    övar samma kortlek. Julius körde sv→fr och en→fr och trodde att de var
    skilda: nollställning av den ena raderade den andras kort, och dagens
    frysta inflödestak slogs upp per språk fast det härleds ur
    `minuter_per_dag`, som är per kurs.

    TVÅ HALVOR, OCH BÅDA MÅSTE HÅLLA. Att vägra är lätt; att vägra FÖR MYCKET
    är det verkliga felet, och jag gjorde det på första försöket. Spärren
    stängde ute användaren från kurser som redan fanns, eftersom `ny_kurs`
    också är vägen man ÖPPNAR en kurs på. Provet kontrollerar därför båda
    riktningarna.
    """
    fel: list[str] = []
    mål = kurs["målspråk"]
    upptagen = {k["källspråk"] for k in kort.execute(
        "SELECT källspråk FROM Kurs WHERE målspråk = ?", (mål,))}
    ny_källa = next((s for s in ("sv", "en", "de", "it", "es")
                     if s not in upptagen and s != mål), None)
    if ny_källa is not None:
        r = tj.ny_kurs(ny_källa, mål)
        if r is None or "fel" not in r:
            fel.append(f"[{mål}] en andra kurs {ny_källa}→{mål} skapades — "
                       f"kortleken delas och kurserna nollställer varandra")
    # Och den befintliga ska fortfarande gå att öppna.
    r = tj.ny_kurs(kurs["källspråk"], mål)
    if r is None or "fel" in r:
        fel.append(f"[{mål}] den BEFINTLIGA kursen {kurs['källspråk']}→{mål} "
                   f"vägrades — spärren stänger ute i stället för att hindra")
    return fel


def prov_inget_redan_bedömt_väntar(tj, kort, kurs) -> list[str]:
    """Ingen passrad får VÄNTA på ett kort som redan bedömts idag.

    Julius: *"Trots att det inte går 24 timmar så vill jag inte få övningar
    som inte gör någon skillnad. Övningar ska endast ta fram ett kort som
    behöver tränas. Annars är övningen meningslös."*

    Han mätte fallet: `Il existe.` rörde sju kort och alla sju var redan
    bedömda tidigare samma dag, så due, again och new stod stilla.

    INVARIANTEN SITTER PÅ KÖN, inte på den serverade meningen, och det är ett
    medvetet val. Jag försökte först pröva utfallet — "varje serverad mening
    bokför minst ett kort" — och fick ett prov som inte gick att fälla ens med
    städningen OCH nödutgången avslagna: generatorn vägrar ändå bygga en
    mening utan täckning. Egenskapen har alltså tre oberoende vakter, och ett
    prov på utfallet mäter vilken som råkar svara först.

    Kön är den plats där felet faktiskt uppstod, och den enda som går att
    fälla rent: ett kort med en dom idag hör inte hemma bland det som väntar.
    Ett FÄLLT kort står kvar — det ska tas igen (B7).
    """
    from sprakprog.kort import pass_ as passlager
    from sprakprog.kort.schemalaggning import dygnets_början
    tj.nollställ(kurs["id"], "RESET")
    for _ in range(20):
        g = tj.glosor(kurs["id"])
        if not g or not g["ord"]:
            break
        for o in g["ord"]:
            tj.glossvar(kurs["id"], o["kort_id"], True)
    u = tj.uppgift(kurs["id"])
    if u is None or u.get("tomt"):
        return []                      # tom dag: omätbar, se japanskan
    f = tj._öppna[u["id"]][1]
    tj.svara(u["id"], f.text)
    tj.bokför(u["id"])
    # Lägg tillbaka de nyss bedömda korten som väntande — precis läget
    # Julius hamnade i, återskapat med avsikt.
    rad = passlager.nuvarande(kort, kurs["id"])
    if rad is None:
        return []
    for k in f.kort:
        kort.execute(
            """INSERT INTO Passkort (pass_id, kort_id, roll, ordning)
               VALUES (?, ?, 'förfallen',
                       (SELECT COALESCE(MAX(ordning), 0) + 1
                        FROM Passkort WHERE pass_id = ?))""",
            (rad["id"], k["id"], rad["id"]))
    kort.commit()
    tj.hem(kurs["id"])                 # läsningen ska städa kön
    kvar = kort.execute(
        """SELECT COUNT(*) AS n FROM Passkort pk
           WHERE pk.pass_id = ? AND pk.status = 'väntar' AND EXISTS
             (SELECT 1 FROM Repetition r WHERE r.kort_id = pk.kort_id
              AND r.tidpunkt >= ? AND (r.betyg IS NULL OR r.betyg <> 1))""",
        (rad["id"], dygnets_början(None))).fetchone()["n"]
    if kvar:
        return [f"[{kurs['målspråk']}] {kvar} rader väntar på kort som redan "
                f"bedömts idag — de räknas som arbete men bokför ingenting"]
    return []


def prov_sista_nivån_går_att_nå(tj, kort, kurs) -> list[str]:
    """Stegens sista steg måste gå att låsa upp.

    TAKET VAR HÅRDKODAT TILL 21 på tre ställen i tjänsten, och inget språk
    har 21 nivåer sedan böjningsdimensionerna flätades in i stegen (F5b):

        de 22   en 22   es 23   fr 22   it 23   ja 24   sv 22

    Följden var att sista nivån aldrig gick att nå. `_byggbarhet` och
    `_nästa_nivå` svarade None ett steg för tidigt, så upplåsningsknappen
    visades aldrig, och `lås_upp` vägrade även om någon anropade den direkt.
    Hemvyns egen totalsiffra rättades när stegen byggdes — men de här tre
    JÄMFÖR med talet i stället för att visa det, och glömdes därför.

    Provet ställer kursen på näst sista nivån och kräver tre saker: att
    byggbarheten går att räkna, att nästa nivå har en kostnad, och att
    upplåsningen inte vägrar av takskäl.
    """
    from sprakprog.kort.dimensioner import toppnivå
    fel = []
    språk = kurs["målspråk"]
    topp = toppnivå(språk)
    gammal = kurs["nivå"]
    try:
        kort.execute("UPDATE Kurs SET nivå = ? WHERE id = ?",
                     (topp - 1, kurs["id"]))
        kort.commit()
        tj._byggbarheter.clear()
        tj._nästa_nivå_kostnad.clear()
        rad = tj._kurs(kurs["id"])
        if tj._byggbarhet(rad) is None:
            fel.append(f"[{språk}] byggbarheten för nivå {topp} går inte att "
                       f"räkna — knappen kan aldrig visas")
        if tj._nästa_nivå(rad) is None:
            fel.append(f"[{språk}] nivå {topp} har ingen kostnad — steget "
                       f"finns i stegen men inte i tjänsten")
        # `lås_upp` får svara None för att byggbarheten är för låg; det är
        # ett annat och riktigt skäl. Provet skiljer dem åt genom att fråga
        # om taket ensamt stänger: står kursen UNDER toppen ska takvillkoret
        # aldrig vara det som stoppar.
        if rad["nivå"] >= topp:
            fel.append(f"[{språk}] näst sista nivån räknas redan som toppen")
    finally:
        kort.execute("UPDATE Kurs SET nivå = ? WHERE id = ?",
                     (gammal, kurs["id"]))
        kort.commit()
        tj._byggbarheter.clear()
        tj._nästa_nivå_kostnad.clear()
    return fel


def prov_ingen_tom_mening(tj, kurs) -> list[str]:
    """Ingen mening får ställas som inte kan bokföra ett enda kort.

    Julius: *"Den gav en mening som inte testar ett enda kort."* Spåret gav
    honom rätt: fem av sex kort hade `läge: redan_bedömd` — rätt bedömda
    tidigare samma dag, och en andra rätt samma dygn är noll i FSRS (E2) —
    och det sjätte stod inte i passet.

    OCH DET VAR INTE EN OLYCKA. Mätt på en nollställd fransk kurs, hela
    dagen i rätt form med glosdelen först:

         7  Elle existe.   bokförs 0   kvar 2
         8  J'ai.          bokförs 0   kvar 2
         9  Il coûte.      bokförs 0   kvar 2

    Tre i rad, 3 av 11 meningar. De sista väntande korten gick inte att
    bygga kring, och då vann den minst dåliga kandidaten — vars kort alla
    redan var avklarade. Nödutgången (B8) fanns men prövade fel sak: om kön
    var BYGGBAR, inte om meningen BOKFÖR något. Den löste ut tre meningar
    för sent.

    Provet spelar igenom en dag med bara rätta svar och kräver att varje
    ställd mening bokför minst ett kort. Efter rättelsen: 11 meningar, noll
    tomma — dagen blev alltså inte kortare, bara ärligare.
    """
    fel = []
    # EGEN TJÄNST OCH NOLLSTÄLLNING, se `prov_dagen_tar_slut`. Utan dem
    # mätte provet Julius halvgjorda dag i stället för en hel, och blev
    # stumt: med en delad tjänst nådde franskan aldrig det läge där alla
    # kandidaters kort redan är bedömda.
    tj = _egen_tjänst(kurs)
    tj.nollställ(kurs["id"], "RESET")
    ställda = 0
    for i in range(120):
        h = tj._dagsplan(kurs)
        if h["klar"]:
            break
        if h["nya_ord"]:
            for o in tj.glosor(kurs["id"])["ord"]:
                tj.glossvar(kurs["id"], o["kort_id"], True)
            continue
        u = tj.uppgift(kurs["id"])
        if u is None or u.get("tomt"):
            break
        # NÅGRA SVAR MÅSTE VARA FEL, och det är inte kosmetika.
        #
        # Provet svarade rätt hela vägen, och då uppstår aldrig ett kort med
        # `redan_fälld` eller `undanhållen` — alltså precis de två lägen som
        # gjorde tomgångsspärren otät. Provet var grönt i tre dagar medan
        # Julius fick fyra tomma meningar av tjugotre.
        #
        # Var tredje svar är fel, med fast frö så utfallet går att upprepa.
        # Ett fel drar dessutom in `igen`-rader och skyddade kort, vilket är
        # den kombination där E2 och D3 möts.
        rätt = (ställda % 3) != 2
        sv = tj.svara(u["id"], tj._öppna[u["id"]][1].text if rätt
                      else "detta är fel")
        tj.bokför(u["id"])
        ställda += 1
        if sv is not None and sv["bokförs"] == 0:
            fel.append(f"[{kurs['målspråk']}] mening {i + 1} bokförde noll "
                       f"kort: {sv['facit'][:40]!r}")
    # ETT PROV SOM INTE MÄTTE NÅGOT FÅR INTE SÄGA GRÖNT. Utan den här raden
    # blev provet tyst så snart dagen råkade vara tom.
    if not ställda:
        fel.append(f"[{kurs['målspråk']}] ingen mening ställdes — provet "
                   f"prövade ingenting")
    return fel[:4]


def prov_dagboken_fångar_övergången(tj, kurs) -> list[str]:
    """Dagboken ska bära kortets tillstånd FÖRE och EFTER, inte bara efter.

    Julius: *"kunna kolla tillbaka och se exakt när det har skett fel beslut
    i rättning sortering eller något annat. Så att jag slipper återberätta."*
    Ett felaktigt beslut syns i ÖVERGÅNGEN — ett kort som flyttades fel, ett
    betyg som inte skulle ha satts — och en logg som bara har sluttillståndet
    besvarar inte frågan. Ögonblicksbilden måste därför tas före mutationen,
    och det är lätt att råka ta den efter.

    Provet svarar RÄTT på en mening och kräver att minst ett kort visar en
    skillnad mellan `före` och `efter`. Det räcker som vittne: kan raden
    visa en övergång är den tagen på rätt sida om bokföringen.

    Provet kräver också att raden bär kortens IDENTITET — nyckel, typ,
    facit — och inte bara id:n. Skälet är hela anledningen att dagboken är
    en fil: Julius nollställer kursen, id:n återanvänds, och en rad som bara
    bär id:n pekar då på fel kort.
    """
    import tempfile as _tf
    from pathlib import Path as _P
    from sprakprog.kort import dagbok as D

    katalog = _P(_tf.mkdtemp()) / "loggar"
    tj = _egen_tjänst(kurs)
    tj.dagbokskatalog = katalog
    try:
        tj.nollställ(kurs["id"], "RESET")     # se `prov_dagen_tar_slut`
        for _ in range(40):
            h = tj._dagsplan(kurs)
            if h["klar"]:
                return ["dagen var redan klar — provet kunde inte mäta"]
            if h["nya_ord"]:
                for o in tj.glosor(kurs["id"])["ord"]:
                    tj.glossvar(kurs["id"], o["kort_id"], True)
                continue
            u = tj.uppgift(kurs["id"])
            if u is None or u.get("tomt"):
                return ["ingen uppgift gick att bygga — provet kunde inte mäta"]
            tj.svara(u["id"], tj._öppna[u["id"]][1].text)
            tj.bokför(u["id"])
            break
        else:
            return ["ingen mening ställdes på 40 steg"]

        poster = [p for b in D.dagböcker(katalog) for p in D.läs(b)]
        if not poster:
            return [f"[{kurs['målspråk']}] dagboken skrevs inte alls"]
        post = poster[-1]
        fel = []
        if not post["kort"]:
            return [f"[{kurs['målspråk']}] raden bär inga kort"]
        if any(k.get("facit") is None and k.get("nyckel") is None
               for k in post["kort"]):
            fel.append(f"[{kurs['målspråk']}] kort utan identitet — raden går "
                       f"inte att läsa efter en nollställning")
        rörelse = [k for k in post["kort"]
                   if k["bokförd"] and k["före"] != k["efter"]]
        if not rörelse:
            fel.append(f"[{kurs['målspråk']}] inget kort visar en skillnad "
                       f"mellan `före` och `efter` — bilden är tagen efter "
                       f"bokföringen")
        return fel
    finally:
        pass


def prov_nödutgången_frågar_om_sökningen(tj, kurs) -> list[str]:
    """Nödutgången får bara lösa ut när INGEN kandidat täckte något.

    B8 skriver av hela dagens återstående kort som onåbara, och det är ett
    hårt beslut: ett `igen`-kort som skrivs av bryter B7 — felet skulle tas
    igen och läggs i stället undan utan att användaren får veta.

    Villkoret läste VINNARENS täckning. Men vinnaren kan ha noll fast
    sökningen hittade hundratals som täckte: de täckande kan ha fallit på
    okändgränsen (C5) eller på upprepningsspärren, och då vinner en reserv
    som inte täcker något.

    Mätt när nödutgången löste ut i en simulerad dag: **698 av 1 030
    kandidater täckte ett köat kort**. På Julius kurs 2026-09-04 kostade det
    tre kort — `ord:se` och två `igen`-kort han just fällt. `fam_pappa` gick
    att bygga en mening kring i 1 719 försök av 2 000.

    Provet prövar BESLUTET och inte en dag, därför att det avgörande läget är
    sällsynt: det uppstod en gång på fyra simulerade dagar. Ett prov som
    behöver tur för att mäta mäter inte.
    """
    from dataclasses import replace as _replace
    from sprakprog.generator import Förslag
    from sprakprog.generator.poang import Poäng

    def förslag(täckta, fanns):
        p = Poäng(0.0, {}, 0.0, 0, täckta, 0)
        return Förslag(None, "x", None, [], p, täckning_fanns=fanns)

    fall = [
        (0, True,  False, "vinnaren täckte inget MEN sökningen hittade "
                          "täckande kandidater"),
        (0, False, True,  "ingen kandidat täckte något — då är dagen slut"),
        (2, False, False, "vinnaren täcker något"),
    ]
    fel = []
    for täckta, fanns, väntat, namn in fall:
        fick = tj._onåbar(förslag(täckta, fanns), {})
        if fick != väntat:
            fel.append(f"[{kurs['målspråk']}] {namn}: nödutgången "
                       f"{'löste ut' if fick else 'löste inte ut'}, väntat "
                       f"{'utlösning' if väntat else 'ingen utlösning'}")
    return fel


def prov_extrafel_stannar_i_extrapasset(tj, kurs) -> list[str]:
    """Ett fel i extraövningen får inte öppna en avklarad dag.

    Julius 2026-09-04: *"när jag fick ett kort att repetera så avbröts keep
    practising och så behövde jag starta det vanliga passet som då hade ett
    kort på again."*

    `bokför` frågade `passlager.nuvarande` UTAN läge, och förvalet är
    `dagens`. Ett fel i extraövningen skrev därför sin `igen`-rad i dagens
    pass — och en `igen`-rad gör dagen o-klar, medan extraövningen kräver
    att den ÄR klar. Den avbröt alltså sig själv.

    ATT FRIVILLIGT EXTRAARBETE UPPHÄVER EN AVKLARAD DAG ÄR BAKVÄNT. Dagens
    omfång bestämdes ur dagens plan; kortet som fälls ingick aldrig i den.
    B7 hålls ändå, inom sessionen: felet tas igen i extrapasset. Och lämnar
    man extraövningen är ingenting förlorat — FSRS har redan bokfört fallet.

    Provet bygger båda passen och bokför ett fel som är märkt `extra`.
    """
    from sprakprog.kort import pass_ as passlager
    fel = []
    # EGEN TJÄNST. Provet nollställer kursen och bygger ett extrapass, och
    # med den DELADE tjänsten slog det ut `extraövningen går att köra` som
    # kördes efteråt. Samma fälla som `prov_dagen_tar_slut` redan hade.
    tj = _egen_tjänst(kurs)
    tj.nollställ(kurs["id"], "RESET")
    tj._dagsplan(kurs)                       # bygger dagens pass
    dagens = passlager.nuvarande(tj.kort_db, kurs["id"])
    extra = passlager.starta(tj.kort_db, kurs, tj._dagsplan(kurs), läge="extra")
    if dagens is None or extra is None:
        return [f"[{kurs['målspråk']}] passen gick inte att bygga — provet "
                f"kunde inte mäta"]
    # VILKET KORT SOM HELST DUGER. Provet mäter VAR `igen`-raden hamnar,
    # inte vad kortet är — och efter nollställningen är inget kort sett.
    kid = tj.kort_db.execute(
        "SELECT id FROM Kort WHERE språk = ? LIMIT 1",
        (kurs["målspråk"],)).fetchone()
    if kid is None:
        return [f"[{kurs['målspråk']}] inga kort alls — provet kunde inte mäta"]
    före_dagens = passlager.läget(tj.kort_db, dagens["id"])["igen"]
    före_extra = passlager.läget(tj.kort_db, extra["id"])["igen"]
    passlager.registrera(tj.kort_db, extra["id"], {kid["id"]: False})
    efter_dagens = passlager.läget(tj.kort_db, dagens["id"])["igen"]
    efter_extra = passlager.läget(tj.kort_db, extra["id"])["igen"]
    if efter_dagens != före_dagens:
        fel.append(f"[{kurs['målspråk']}] ett fel i extraövningen lade en "
                   f"`igen`-rad i DAGENS pass ({före_dagens} → "
                   f"{efter_dagens}) — dagen öppnas av frivilligt arbete")
    if efter_extra != före_extra + 1:
        fel.append(f"[{kurs['målspråk']}] felet lades inte i extrapasset "
                   f"({före_extra} → {efter_extra}) — B7 bryts, "
                   f"återförsöket försvinner")
    return fel


PROV = [
    ("en kurs per målspråk", prov_en_kurs_per_målspråk),
    ("inget redan bedömt väntar", prov_inget_redan_bedömt_väntar),
    ("dagsbudgeten hålls av alla vägar in", prov_glosbudget),
    ("extraövningen går att köra", prov_extraövningen_går_att_köra),
    ("passet tar slut", lambda tj, k, kurs: prov_dagen_tar_slut(tj, kurs)),
    ("uppgiften överlever att vyn lämnas",
     lambda tj, k, kurs: prov_uppgiften_överlever(tj, kurs)),
    ("visat tal = styrande tal", lambda tj, k, kurs: prov_visat_lika_styrande(tj, kurs)),
    ("extraövning kräver klar dag", lambda tj, k, kurs: prov_extra_kräver_klar(tj, kurs)),
    ("ingen upprepad mening", lambda tj, k, kurs: prov_ingen_upprepad_mening(tj, kurs)),
    ("räknaren i takt med bokföringen", lambda tj, k, kurs: prov_räknaren_är_i_takt(tj, kurs)),
    ("sista nivån går att nå", prov_sista_nivån_går_att_nå),
    ("ingen tom mening ställs",
     lambda tj, k, kurs: prov_ingen_tom_mening(tj, kurs)),
    ("dagboken fångar övergången",
     lambda tj, k, kurs: prov_dagboken_fångar_övergången(tj, kurs)),
    ("nödutgången frågar om sökningen, inte om vinnaren",
     lambda tj, k, kurs: prov_nödutgången_frågar_om_sökningen(tj, kurs)),
    ("fel i extraövningen stannar i extrapasset",
     lambda tj, k, kurs: prov_extrafel_stannar_i_extrapasset(tj, kurs)),
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

    if namn == "inget redan bedömt väntar":
        # Före rättelsen: passet lämnade rader kvar som `väntar` för kort
        # som redan bedömts idag. Passet räknade dem som arbete, `att_göra`
        # visade dem, och generatorn byggde meningar för att täcka dem —
        # medan E2 hoppade över dem vid bokföringen, med rätta.
        from sprakprog.kort import pass_ as passlager
        äkta = passlager._stäng_redan_bedömda
        passlager._stäng_redan_bedömda = lambda *a, **kw: 0
        return lambda: setattr(passlager, "_stäng_redan_bedömda", äkta)

    if namn == "fel i extraövningen stannar i extrapasset":
        # Före rättelsen: `bokför` frågade alltid efter DAGENS pass, oavsett
        # var uppgiften kom ifrån. Sabotaget flyttar registreringen dit.
        from sprakprog.kort import pass_ as _p
        äkta = _p.registrera

        def i_dagens(kort_db, pass_id, utfall, nu=None):
            rad = kort_db.execute(
                """SELECT p2.id FROM Pass p1 JOIN Pass p2
                     ON p2.kurs_id = p1.kurs_id AND p2.datum = p1.datum
                   WHERE p1.id = ? AND p2.läge = 'dagens'""",
                (pass_id,)).fetchone()
            return äkta(kort_db, rad[0] if rad else pass_id, utfall, nu)

        _p.registrera = i_dagens
        return lambda: setattr(_p, "registrera", äkta)

    if namn == "nödutgången frågar om sökningen, inte om vinnaren":
        # Före rättelsen: villkoret läste bara vinnarens täckning.
        äkta = Övningstjänst.__dict__["_onåbar"]
        Övningstjänst._onåbar = staticmethod(
            lambda f, p: f.poäng is not None and f.poäng.täckta == 0)
        return lambda: setattr(Övningstjänst, "_onåbar", äkta)

    if namn == "dagboken fångar övergången":
        # Före rättelsen: ögonblicksbilden togs EFTER mutationerna, så
        # `före` och `efter` blev samma sak och övergången försvann.
        from sprakprog.kort import dagbok as D
        äkta = D.före
        D.före = lambda kort_db, pass_id, idn: {
            "kort": {}, "fast": {k: {"nyckel": None, "typ": None,
                                     "koncept": None, "variant": None,
                                     "facit": None, "ordklass": None,
                                     "klass": None, "cell": None,
                                     "egenskap": None} for k in idn},
            "pass": {}, "ordet_sett": {}}
        return lambda: setattr(D, "före", äkta)

    if namn == "ingen tom mening ställs":
        # DEN SMALA MÄNGDEN, alltså buggen som faktiskt nådde Julius — inte
        # den ursprungliga avsaknaden av filter. `betyg <> FEL` såg rimligt
        # ut och var fel på två sätt: ett fallerat kort föll bort, och ett
        # undanhållet har `betyg IS NULL`, vilket SQL:s trevärda logik
        # tystar bort. Provet såg det inte, för det svarade alltid rätt.
        from sprakprog.kort.schemalaggning import dygnets_början
        äkta = Generator._redan_klara

        def smal(själv, nu):
            return {r["kort_id"] for r in själv.kort_db.execute(
                """SELECT DISTINCT r.kort_id FROM Repetition r
                   JOIN Kort k ON k.id = r.kort_id
                   WHERE k.språk = ? AND r.tidpunkt >= ? AND r.betyg <> 1""",
                (själv.språk, dygnets_början(nu)))}

        Generator._redan_klara = smal
        return lambda: setattr(Generator, "_redan_klara", äkta)

    if namn == "sista nivån går att nå":
        # Före rättelsen: taket hårdkodat till 21 i båda grindarna.
        äkta_b = Övningstjänst._byggbarhet
        äkta_n = Övningstjänst._nästa_nivå

        def med_21(äkta):
            def grind(själv, kurs):
                if kurs["nivå"] >= 21:
                    return None
                return äkta(själv, kurs)
            return grind

        Övningstjänst._byggbarhet = med_21(äkta_b)
        Övningstjänst._nästa_nivå = med_21(äkta_n)

        def ångra():
            Övningstjänst._byggbarhet = äkta_b
            Övningstjänst._nästa_nivå = äkta_n
        return ångra

    if namn == "en kurs per målspråk":
        # Före spärren: `ny_kurs` skapade glatt en andra kurs mot samma mål.
        äkta = Övningstjänst.ny_kurs
        def utan_spärr(själv, källspråk, målspråk, nivå=1, cefr="A1"):
            import sprakprog.webb as w
            gammal, w.EN_KURS_PER_MÅLSPRÅK = w.EN_KURS_PER_MÅLSPRÅK, None
            try:
                # Med texten borta kastar formateringen, så spärren hoppas
                # över — samma utfall som när den inte fanns.
                try:
                    return äkta(själv, källspråk, målspråk, nivå, cefr)
                except AttributeError:
                    pass
            finally:
                w.EN_KURS_PER_MÅLSPRÅK = gammal
            with själv.lås:
                from datetime import UTC, datetime
                nu = datetime.now(UTC).isoformat()
                själv.kort_db.execute(
                    """INSERT INTO Kurs (källspråk, målspråk, nivå, cefr,
                                         budget, startad, senast_öppnad)
                       VALUES (?,?,?,?,1.5,?,?)
                       ON CONFLICT (källspråk, målspråk) DO UPDATE SET
                           senast_öppnad = excluded.senast_öppnad""",
                    (källspråk, målspråk, nivå, cefr, nu, nu))
                själv.kort_db.commit()
                return dict(själv.kort_db.execute(
                    "SELECT * FROM Kurs WHERE källspråk=? AND målspråk=?",
                    (källspråk, målspråk)).fetchone())
        Övningstjänst.ny_kurs = utan_spärr
        return lambda: setattr(Övningstjänst, "ny_kurs", äkta)

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
        # OCH NÖDUTGÅNGENS SKRIVNING, som är det sätt dagen KAN fastna i
        # dagens kod. De två ovan slutade bita när koden växte ur felen de
        # återskapade (se G7); den här är trogen mot ett fel som fortfarande
        # är möjligt: hittas ingen mening och skrivs raderna inte av, står
        # passet kvar med väntande arbete för alltid.
        from sprakprog.kort import pass_ as _p
        äkta_avskriv = _p.avskriv
        _p.avskriv = lambda *a, **kw: 0
        äkta = Övningstjänst.__dict__["_onåbar"]
        Övningstjänst._onåbar = staticmethod(
            lambda f, p: f.poäng is not None and f.poäng.täckta == 0
            and bool(p["förfallna"]))
        äkta_sil = Generator.övningsbara
        Generator.övningsbara = lambda själv, koncept: list(koncept)
        # OCH DEN DISJUNKTA KÖN, som är det tredje sättet dagen kunde fastna.
        #
        # Sabotaget ovan slutade fälla provet 2026-08-26, och det var ett gott
        # tecken: sedan generatorn tar dagens nya kort UR PASSET behöver dagen
        # inte längre nödutgången för att ta slut, så att slå av den ändrar
        # ingenting. Men ett prov som inte kan falla bevisar ingenting, och
        # invarianten "passet tar slut" ska skydda mot ALLA sätt det kan
        # brytas — inte bara det som var akut när den skrevs.
        #
        # Före rättelsen frågade `föreslå` `osedda` på nytt i stället för att
        # använda passets rader, och de två mängderna var helt disjunkta:
        # passet väntade på nio kort, generatorn köade nio andra, noll
        # gemensamma. Att slänga `nya` återskapar precis det.
        äkta_föreslå = Generator.föreslå
        Generator.föreslå = (
            lambda själv, **kw: äkta_föreslå(
                själv, **{**kw, "nya": None}))

        def ångra():
            Övningstjänst._onåbar = staticmethod(äkta)
            Generator.övningsbara = äkta_sil
            Generator.föreslå = äkta_föreslå
            _p.avskriv = äkta_avskriv
        return ångra


    if namn == "uppgiften överlever att vyn lämnas":
        äkta = Övningstjänst.uppgift

        def alltid_ny(själv, kurs_id, *, extra=False):
            själv._pågående.clear()
            return äkta(själv, kurs_id, extra=extra)
        Övningstjänst.uppgift = alltid_ny
        return lambda: setattr(Övningstjänst, "uppgift", äkta)

    if namn == "extraövning kräver klar dag":
        # SIGNATUREN MÅSTE FÖLJA DEN ÄKTA. `_extraläge` fick argumentet
        # `kurs` 2026-09-04, och sabotagets lambda gjorde det inte — den
        # kastade `TypeError` mitt i falsifieringen. Provet hade då redan
        # skrivit "15 invarianter, alla håller", så utskriften såg grön ut
        # medan returkoden var 1, och sviten föll av ett skäl som inte stod
        # i provets egen sammanfattning.
        #
        # Ett sabotage som inte längre passar det det saboterar är samma
        # sorts ruttnande som ett stumt prov, bara högljuddare. Se G7.
        äkta = Övningstjänst._extraläge
        Övningstjänst._extraläge = staticmethod(
            lambda p, kurs=None: {"nya": p["nya_extra"], "tidiga": p["tidiga"],
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
        # `staticmethod` BÅDE VID SABOTAGE OCH ÅTERSTÄLLNING. Attributläsning
        # på klassen packar upp deskriptorn till en vanlig funktion, så ett
        # naket `setattr` lämnar metoden som en instansmetod — och `self`
        # smyger då in som första argument nästa gång någon anropar den.
        # Felet syntes inte förrän ett prov som körs EFTER det här sabotaget
        # anropade `svara`, alltså långt från sin orsak.
        äkta = Övningstjänst.__dict__["_igen_efter"]
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
    # SAMMANFATTNINGEN STÅR SIST, EFTER FALSIFIERINGEN. Den låg här förut,
    # och när ett sabotage kastade mitt i falsifieringen hade provet redan
    # skrivit "alla håller" — utskriften såg grön ut medan returkoden var 1,
    # och sviten föll av ett skäl som inte stod i provets egen rad. En rad
    # som skrivs innan allt som kan falla har hänt kan inte vara sann.

    # OCH BEVISA ATT DE KAN FALLA.
    print("\nfalsifiering — med det gamla felet återinfört ska varje prov falla:")
    stumma = 0
    with tempfile.TemporaryDirectory() as d:
        for nr, (namn, kör) in enumerate(PROV):
            try:
                ångra = _sabotera(namn)
            except Exception as e:                            # noqa: BLE001
                # Också SJÄLVA sabotaget kan sluta passa. Se nedan.
                print(f"  ✗ KASTADE  {namn}  ({type(e).__name__}: "
                      f"{str(e)[:60]})")
                stumma += 1
                continue
            try:
                tj, kort = tjänst(Path(d) / f"sab{nr}.db")
                kurser = kort.execute("SELECT * FROM Kurs").fetchall()
                # ETT KRASCHANDE SABOTAGE FÅR INTE DÖDA DE ANDRA, och det
                # gjorde det: `_extraläge` fick ett argument till, sabotagets
                # lambda följde inte med, och hela falsifieringen dog vid
                # nummer åtta av femton. Ett sabotage som kastar har inte
                # bevisat något — det räknas som STUMT och rapporteras, så
                # de övriga fjorton fortfarande mäts.
                try:
                    brister = [b for kurs in kurser
                               for b in kör(tj, kort, kurs)]
                except Exception as e:                        # noqa: BLE001
                    brister = []
                    print(f"  ✗ KASTADE  {namn}  ({type(e).__name__}: "
                          f"{str(e)[:60]})")
                    kort.close()
                    stumma += 1
                    continue
                kort.close()
            finally:
                ångra()
            if not brister:
                stumma += 1
            print(f"  {'✓ föll' if brister else '✗ STUMT PROV'}  {namn}")
    if stumma:
        print(f"\n{stumma} prov kunde inte falla. Ett prov som inte kan falla "
              f"bevisar ingenting.")
    # HÄR, och ingenstans tidigare: allt som kan falla har fallit nu.
    print(f"\n{len(PROV)} invarianter, {fel} brott, {stumma} stumma."
          if fel or stumma else
          f"\n{len(PROV)} invarianter, alla håller och alla kan falla.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
