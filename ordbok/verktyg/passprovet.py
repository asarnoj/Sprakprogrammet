"""Nät för dagspassets invarianter — KÄRNAN 5.1, 5.4 och 6.1.

VARFÖR DET HÄR NÄTET FINNS. Tre fel i passet hittades samma dag, och alla tre
hade samma form: koden räknade upp något för hand och KÄRNAN sa något annat.

    villkor 8 i 6.1   källmeningen fick ställas om samma dag. Fyra av fjorton
                      meningar i den första riktiga körningen var upprepningar,
                      och andra gången mätte de minnet av facit i stället för
                      kortet.

    villkor 5 och 7   ingenting kontrollerade att två svaga kort inte styr
                      samma ställe. Budgeten gjorde felen FÅ, aldrig
                      ÅTSKILJBARA — KÄRNAN 6.2 kallar dem samma tal sett från
                      två håll, och bara det ena hölls.

    5.4               introfasen bokförde. `Passet.presentera` gjorde rätt sak
                      och anropades aldrig; gränssnittet ställde i stället en
                      mening med hela paketet som mål och skrev betygen till
                      FSRS.

Inget prov hade fångat något av dem. `passprov` prövar tjänsterna runt passet,
inte reglerna i det.

VAD PROVET GÖR. Bygger en färsk kurs, kör introfasen och några meningar, och
prövar invarianterna på det som faktiskt ställs. Sedan FALSIFIERAS varje
invariant: det gamla beteendet återinförs, och en invariant som inte faller då
är ingen invariant utan en förhoppning. Det är samma uppställning som
`övervakningsprov`.

VILAR INTE PÅ INLÄRARHISTORIKEN. Kursen byggs från noll i en temporärfil.

Kör:  python ordbok/verktyg/passprovet.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.fsrslager import Lager                             # noqa: E402
from sprakprog.kortmodell import Kort, meningens_kort             # noqa: E402
from sprakprog.kurs import Kursdata                               # noqa: E402
from sprakprog.passet import Passet                               # noqa: E402
from sprakprog.rendering.karta import ladda                       # noqa: E402
from sprakprog.sammansattning import Sammansättare                # noqa: E402

KARTA = ROT / "kartor" / "en.pkl"
NIVÅER = ROT / "kartor" / "nivaer_en.json"

#: Taket för hur länge det får ta att VÄLJA en uppgift. Mätt i KÄRNAN 6.3:
#: att svara på den kortaste meningen tar 16,2 s i median, och att välja den
#: får inte kosta mer än att besvara den. Frysningen som gav upphov till det
#: här provet höll sig långt över taket — kortet gav aldrig någon mening alls.
TAK_SEKUNDER = 16.2


def _nivåfil() -> tuple[dict, list]:
    data = json.loads(NIVÅER.read_text(encoding="utf-8"))

    def kort(rad) -> Kort:
        return Kort(rad[0], rad[1], tuple(rad[2]))

    return ({kort(k): frozenset(map(kort, m)) for k, m in data["krav"]},
            [frozenset(map(kort, n)) for n in data["nivåer"]])


def _passet(fil: Path) -> tuple[Passet, Kursdata]:
    s = Sammansättare(sqlite3.connect(ROT / "sprak.db"), ladda(KARTA), "sv")
    data = Kursdata(sqlite3.connect(fil), "sv", "en")
    krav, nivåer = _nivåfil()
    return Passet(data, s, Lager(data), krav, nivåer), data


@contextmanager
def _utan(objekt, namn: str, ersättning):
    """Återinför ett gammalt beteende, för falsifieringen."""
    gammalt = getattr(type(objekt), namn)
    setattr(type(objekt), namn, ersättning)
    try:
        yield
    finally:
        setattr(type(objekt), namn, gammalt)


# ── invarianterna ────────────────────────────────────────────────────


def introfasen_bokför_ingenting(p: Passet, data: Kursdata) -> list[str]:
    """5.4. Övningen finns för att användaren inte ska möta ny kunskap
    oförberedd, inte för FSRS."""
    före = len(data.möten())
    kort = p.kandidater()[0]
    uppgift = p.presentera(kort, paket=p.nästa_nivå())
    if uppgift is None:
        return ["ingen introövning gick att bygga för det första kortet"]
    uppgift = p.ställ(uppgift, "intro")
    p.rätta(uppgift, "struntprat", 1.0)
    efter = len(data.möten())
    return ([f"introfasen bokförde {efter - före} möten"] if efter != före else [])


def introövningen_har_ett_mål(p: Passet) -> list[str]:
    """5.4. Bara det nya kortet är mål; resten är lånekort.

    Prövas på BÅDA vägarna: `presentera`, och dagsplanens tilldelning. Planen
    bygger uppgiften när källmeningen först dyker upp och märker den med det
    kort som råkade samla in den; matchningen ger den sedan till ett annat.
    Följer märkningen inte med läser bedömningen i 5.4 fel korts betyg.
    """
    brister = []
    for kort in p.kandidater()[:3]:
        uppgift = p.presentera(kort, paket=p.nästa_nivå())
        if uppgift is None:
            continue
        if uppgift.mål != frozenset({kort}):
            brister.append(f"{kort}: introövningen hade målen "
                           f"{sorted(map(str, uppgift.mål))}")
    plan = p.dagsplan()
    for kort, uppgift in plan.introövningar:
        if uppgift.mål != frozenset({kort}):
            brister.append(f"{kort}: planens introövning «{uppgift.källtext}» "
                           f"är märkt {sorted(map(str, uppgift.mål))}")
    for kort, uppgift in plan.lektioner.items():
        if uppgift.mål != frozenset({kort}):
            brister.append(f"{kort}: planens lektion «{uppgift.källtext}» "
                           f"är märkt {sorted(map(str, uppgift.mål))}")
    return brister


def källmeningen_ställs_en_gång(p: Passet, data: Kursdata) -> list[str]:
    """6.1 punkt 8. Efter ett fel har användaren sett facit."""
    ställda: list[str] = []
    for kort in p.kandidater():
        uppgift = p.presentera(kort, paket=p.nästa_nivå())
        if uppgift is None:
            continue
        p.ställ(uppgift, "intro")
        ställda.append(uppgift.källtext)
    dubbletter = {t for t in ställda if ställda.count(t) > 1}
    return ([f"samma källmening ställdes flera gånger: {sorted(dubbletter)}"]
            if dubbletter else [])


def målen_är_åtskilda(p: Passet) -> list[str]:
    """6.1 punkt 5 och 7. Två mål får inte styra samma ställe."""
    brister = []
    for kort in p.kandidater()[:3]:
        uppgift = p.presentera(kort, paket=p.nästa_nivå())
        if uppgift is None:
            continue
        if not p._åtskilda(uppgift.ut, set(uppgift.mål)):
            brister.append(f"{kort}: målen delar ställe i «{uppgift.facit}»")
    return brister


def uppgiften_väljs_i_tid(p: Passet) -> list[str]:
    """Frysningen. Att välja en uppgift får inte kosta mer än att besvara den."""
    brister = []
    for kort in p.kandidater()[:3]:
        t = time.perf_counter()
        p.presentera(kort, paket=p.nästa_nivå())
        gick = time.perf_counter() - t
        if gick > TAK_SEKUNDER:
            brister.append(f"{kort}: att välja uppgiften tog {gick:.0f} s "
                           f"(taket är {TAK_SEKUNDER} s)")
    return brister


def paketet_införs_helt(p: Passet, data: Kursdata) -> list[str]:
    """5.1. Annars kunde ett verb vara infört utan det pronomen det kräver."""
    nivån = p.nästa_nivå()
    kort = p.kandidater()[0]
    uppgift = p.presentera(kort, paket=nivån)
    if uppgift is None:
        return ["ingen övning gick att bygga"]
    uppgift = p.ställ(uppgift)
    # Ett svar där ETT ord är fel. Då klarar sig de flesta korten och ett
    # faller — och först då skiljer sig «helt eller inte alls» från det gamla
    # «kort för kort». Ett svar som gör allt fel gör lägena omöjliga att
    # skilja åt, eftersom inget kort införs i någotdera.
    orden = uppgift.facit.split()
    svar = " ".join(orden[:-1] + ["xyzzy"])
    rättning = p.rätta(uppgift, svar, 1.0)
    if all(b == "again" for b in rättning.betyg.values()):
        return ["provet kunde inte få något kort att klara sig — fallet "
                "skiljer inte lägena åt"]
    p.bokför(uppgift, rättning, paket=nivån)
    infört = data.införda() & nivån
    return ([f"{len(infört)} av {len(nivån)} kort i paketet infördes trots att "
             f"paketet föll: {sorted(map(str, infört))}"] if infört else [])


def _introfasen(p: Passet, plan) -> None:
    """Gå igenom introfasen som passet gör den (`passet/__main__._introfas`).

    Proven körde förut en introfas som inte längre finns: de presenterade
    mönsterkorten men aldrig ORDEN. Då var ingenting tillåtet att bygga av,
    och ensamövningen — som inte längre hittar på ord — kunde inte svara.
    Vägen genom dagen ska prövas som den går.
    """
    for kort, övning in plan.introövningar:
        lektion = plan.lektioner.get(kort)
        for glosa in p.glosorna(*[u for u in (lektion, övning) if u is not None]):
            p.data.presentera(glosa.kort)
        if lektion is not None:
            p.ställ(lektion, "lektion")
        p.ställ(övning, "intro")
        p.klarat_introövningen(kort)
    for glosa in p.glosorna(*plan.meningsfasen):
        p.data.presentera(glosa.kort)
    p.uppdatera()


def dag_ett_går_att_komma_igenom(p: Passet, data: Kursdata) -> list[str]:
    """6.3: budgeten kan aldrig göra ett kort onåbart.

    Dag ett är alla kort svaga och står på samma få ord, så villkor 5 gör
    varje mening med flera mål ogiltig. Utan ensamövningen (reservsteg 1)
    fanns då ingen uppgift alls, och passet gick inte att komma igenom.
    """
    plan = p.dagsplan()
    _introfasen(p, plan)
    utan = [k for k in sorted(p.svaga(), key=str) if p.uppgift(k, plan) is None]
    return ([f"{len(utan)} svaga kort utan uppgift efter introfasen: "
             f"{sorted(map(str, utan))}"] if utan else [])


def slutna_ordklasser_är_grindade(p: Passet, data: Kursdata) -> list[str]:
    """4.5 och 3.10. Bara ord ur ÖPPNA ordklasser får fylla ut en övning.

    När ingen övning går att bygga av kända kort får nya ord komma med — de
    lärs ut som glosor först. Men `familj == "ord"` rymmer också artiklar,
    pronomen, kvantifikatorer och räkneord, och de är NIVÅKORT, grindade av
    sin nivå. Utan gränsen lärdes «man» ut i första lektionen fast det hör
    till nivå 81, och «någon» fast det hör till nivå 28.

    Grinden prövas direkt i stället för genom en övning. Att nå fram till
    läckan den vägen krävde tre introrundor — villkor 8 måste först ha
    förbrukat varje mening som går att bygga av de kända orden — och ett
    prov som tar tretton minuter körs inte.
    """
    fall = [("pronomen_impersonal", False), ("kvant_någon", False),
            ("artikel_bestamd", False), ("räkn_2", False),
            ("tid_tid", True), ("pos_stå", True), ("pers_flicka", True)]
    brister = []
    for nyckel, väntat in fall:
        fick = p._fritt_ord(Kort(p.s.språk, "ord", (nyckel, "")))
        if fick != väntat:
            brister.append(
                f"{nyckel}: {'släpps in' if fick else 'stängs ute'} men skulle "
                f"{'släppas in' if väntat else 'stängas ute'}")
    return brister


def korten_införs_när_de_går_rätt(p: Passet, data: Kursdata) -> list[str]:
    """5.1. Ett nytt kort blir infört när det går rätt i en mening.

    I den första riktiga körningen infördes noll kort på 32 ställda meningar.
    Passet kom aldrig ur introfasen — som inför ingenting — eftersom
    gränssnittet lät den köras om, och räknaren stod stilla eftersom den
    räknade oinförda kort. Provet går hela vägen: presentera, svara RÄTT,
    och kräv att korten är inne.
    """
    plan = p.dagsplan()
    _introfasen(p, plan)
    if p.att_presentera():
        return [f"{len(p.att_presentera())} kort kvar att presentera efter "
                f"introfasen — den tar aldrig slut"]
    # Dagen tar slut när högarna är tomma (5.3). Ett varv per kort i planen
    # räcker när varje svar är rätt; behövs fler är något fel.
    for _ in range(len(plan.kort)):
        svaga = sorted(p.svaga(), key=str)
        if not svaga:
            break
        uppgift = p.uppgift(svaga[0], plan)
        if uppgift is None:
            break
        uppgift = p.ställ(uppgift)
        rättning = p.rätta(uppgift, uppgift.facit, 1.0)   # svarar rätt
        if not rättning.rätt:
            return [f"ett svar lika med facit underkändes: «{uppgift.facit}» "
                    f"fällde {sorted(map(str, rättning.fel))}"]
        p.bokför(uppgift, rättning, paket=p.paket())
    # Dagen slutar när högarna är tomma (5.3), och med bara rätta svar ska
    # varje kort i planen vara inne.
    kvar = plan.kort - data.införda()
    return ([f"{len(kvar)} av planens {len(plan.kort)} kort infördes inte "
             f"trots att varje svar var lika med facit: "
             f"{sorted(map(str, kvar))[:6]}"] if kvar else [])


def orden_lärs_ut_före_mönstret(p: Passet, data: Kursdata) -> list[str]:
    """5.4. «Ett kort presenteras efter de kort det kräver.»

    Introövningen för SVO byggdes med «Tid står.», där varken `tid` eller
    `står` någonsin visats: tre okända saker prövades och en av dem kallades
    mål. Innehållsorden ska ha sin glosa först.

    Prövas på den väg passet FAKTISKT går: dagsplanens lektion och övning,
    och `glosorna` som introfasen läser dem ur.
    """
    plan = p.dagsplan()
    if not plan.introövningar:
        return ["dagsplanen är tom"]
    brister = []
    kända = data.införda() | data.presenterade()
    for kort, uppgift in plan.introövningar:
        lektion = plan.lektioner.get(kort)
        glosor = p.glosorna(*[u for u in (lektion, uppgift) if u is not None])
        lärda = {g.kort for g in glosor}
        orden = set(uppgift.träff.kort) | (set(lektion.träff.kort) if lektion else set())
        okända = [k for k in orden - kända - lärda - {kort}
                  if p.glosa(k) is not None]
        if okända:
            brister.append(f"{kort}: övningen har {len(okända)} olärda "
                           f"innehållsord {sorted(map(str, okända))} "
                           "som ingen glosa täcker")
    return brister


def presenterat_betyder_klarat(p: Passet, data: Kursdata) -> list[str]:
    """5.1. «presenterat = har klarat introövningen i dag.»

    Förut räknades kortet som presenterat så snart övningen BYGGDES, alltså
    innan användaren svarat, och fick då användas i dagens meningar utan att
    ha klarats.
    """
    kort = p.att_presentera()[0]
    p.presentera(kort, paket=p.nästa_nivå(), markera=False)
    return ([f"{kort} räknades som presenterat utan att ha klarat övningen"]
            if kort in data.presenterade() else [])


def dagsplanen_är_genomförbar(p: Passet, data: Kursdata) -> list[str]:
    """5.1 och 3.10. Planen läggs innan passet börjar, och den ska hålla.

    Villkor 8 i 6.1 gör att material FÖRBRUKAS medan dagen går: en källmening
    får ställas en gång. Utan en plan tog det slut mitt i — fyra presenterade
    ord gick inte att pröva alls, ett nivåkort blev presenterat utan övning,
    och dagen förklarades klar med fulla högar.

    Planen ska därför ge varje kort sin EGEN introövning, reservera meningar
    åt huvuddelen, och inte använda samma källmening två gånger.
    """
    plan = p.dagsplan()
    brister = []
    if not plan.introövningar:
        return ["dagsplanen är tom"]

    texter = [u.källtext for _, u in plan.introövningar]
    if len(set(texter)) != len(texter):
        brister.append("två introövningar delar källmening")
    delade = set(texter) & {u.källtext for u in plan.meningsfasen}
    if delade:
        brister.append(f"samma mening i båda faserna: {sorted(delade)}")

    # Lektionen VISAR facit. Ställs samma mening sedan mäter den minnet av
    # facit och inte kortet — samma skäl som villkor 8 i 6.1 ger.
    lästa = {u.källtext for u in plan.lektioner.values()}
    ställda = set(texter) | {u.källtext for u in plan.meningsfasen}
    if lästa & ställda:
        brister.append(f"en läst lektionsmening ställs: {sorted(lästa & ställda)}")

    # ORDEN RÄKNAS MED, inte bara mönsterkorten. Ett presenterat ord ligger
    # kvar i högen tills det gått rätt i en mening (5.1), så ett ord som
    # ingen mening i huvuddelen bär gör att dagen aldrig tar slut (5.3).
    planerade = plan.kort
    i_karantän = {k for k, _ in plan.karantän}
    utan = [k for k in p.kandidater()
            if k not in planerade and k not in i_karantän
            and k not in data.presenterade()]
    if utan:
        brister.append(f"{len(utan)} kort varken planerade eller i karantän: "
                       f"{sorted(map(str, utan))}")

    if plan.meningsfasen:
        täckta: set = set()
        for u in plan.meningsfasen:
            täckta |= set(u.träff.kort)
        otäckta = planerade - täckta
        if otäckta:
            brister.append(f"{len(otäckta)} kort kan inte införas i huvuddelen: "
                           f"{sorted(map(str, otäckta))}")
    elif planerade:
        brister.append("inga meningar reserverade åt huvuddelen")

    # Orden planen behöver ska räknas med i dagens kortmängd — det var det
    # Julius frågade om när räknaren sa fem och passet lärde ut tolv.
    if not plan.orden or not (plan.orden <= plan.kort):
        brister.append("ordförrådet ingår inte i dagens kortmängd")

    # DAG ETT FÅR INGEN KARANTÄN. «Karantänen är felhantering, inte
    # förlåtelse» (3.10): ett kort där är en felrapport som ska leda till en
    # rättelse, inte ett läge planen får nöja sig med. På dag ett betyder den
    # dessutom att kursen inte går att börja. Kursen här är ny, så mängden
    # ska vara tom.
    if plan.karantän:
        brister.append("karantän redan dag ett: " + ", ".join(
            f"{k} ({orsak})" for k, orsak in plan.karantän))
    return brister


def meningen_använder_bara_tillåtet(p: Passet, data: Kursdata) -> list[str]:
    """6.1 punkt 1 och 5.1. En mening får bara använda infört eller presenterat.

    Introfasen KAN pausa: ett kort som inte går rätt blir inte presenterat.
    Dagsplanens meningar är byggda i förväg, av det planen TÄNKTE presentera,
    och gick därför förbi villkoret helt — en körning införde 13 kort men hade
    presenterat 12, alltså ett kort användaren aldrig fått se.

    Provet presenterar bara HALVA planen, som en pausad introfas, och kräver
    att ingen uppgift då använder resten.
    """
    plan = p.dagsplan()
    if not plan.introövningar:
        return ["dagsplanen är tom"]
    halva = sorted(plan.kort, key=str)[:len(plan.kort) // 2]
    for k in halva:
        data.presentera(k)
    p.uppdatera()
    tillåtna = data.tillåtna()
    brister = []
    for kortet in sorted(p.svaga(), key=str):
        uppgift = p.uppgift(kortet, plan)
        if uppgift is None:
            continue
        otillåtna = uppgift.träff.kort - tillåtna - {kortet}
        if otillåtna:
            brister.append(f"«{uppgift.källtext}» använder {len(otillåtna)} "
                           f"opresenterade kort: {sorted(map(str, otillåtna))}")
    return brister


def _nästa_dygn(data: Kursdata) -> None:
    """Flytta kursen ett dygn framåt: införandena hamnar i går.

    Grinden i 4.4 öppnar en nivå först när föregångarens kort infördes en
    TIDIGARE dag, så ett prov som behöver två nivåer måste passera ett dygn.
    Dagens presenterade och ställda meningar hör till dygnet och rensas.
    """
    data.conn.execute(
        "UPDATE infört SET tid = datetime(tid, '-1 day') WHERE kurs_id = ?",
        (data.id,))
    data.conn.execute("DELETE FROM presenterat WHERE kurs_id = ?", (data.id,))
    data.conn.execute("DELETE FROM mening WHERE kurs_id = ?", (data.id,))
    data.conn.commit()


def _oinförda_lån(plan, införda, nivå) -> int:
    """Hur många lånekort i planens introövningar användaren INTE kan.

    Nivåns egna kort räknas inte: de kräver varandra (4.1) och införs som
    paket (3.10), så de går inte att välja bort.
    """
    return sum(1 for k, u in plan.introövningar for x in u.träff.kort - {k}
               if x not in införda and x not in nivå)


def lånekorten_är_de_kända(p, data) -> list[str]:
    """5.4. «Lånekorten väljs så att sannolikheten att alla blir rätt är så hög
    som möjligt — ett mönsterkort presenteras med ett ord användaren kan väl, så
    att bara mönstret är nytt.»

    SATSEN ÄR JÄMFÖRANDE, inte ett golv, och det är mätt fram. «Så hög som
    möjligt» är ett maximum: finns inget infört ord som duger är ett nytt det
    bästa som finns. Nivå 2 är just så — den kräver ett RÄKNEBART substantiv,
    och dag ett lär bara ut oräknebara, eftersom nivå 1 kräver naken fras. Ett
    prov som krävde noll okända lånekort där fällde alltså koden för att
    verkligheten inte erbjöd något bättre.

    Kravet är därför: vikten får aldrig göra det sämre, och där det finns något
    att välja på ska den göra det bättre. Mätt över åtta nivåer: 15 okända
    lånekort med vikten mot 18 utan, och hela skillnaden ligger på nivå 2
    (4 mot 7). Dag ett är noll mot noll — då finns ingenting att låna av, och
    då har regeln ingenting att säga.

    Prövas på första och andra nivån, för det är där skillnaden finns.
    """
    from sprakprog.passet import Passet as P

    def två_nivåer() -> list[int]:
        # Egen färsk kurs: jämförelsen ska börja från samma läge båda gångerna.
        #
        # DYGNET MÅSTE PASSERA MELLAN NIVÅERNA. Grinden i 4.4 kräver att
        # föregångarens kort infördes en TIDIGARE dag, så två nivåer längs en
        # kedja går inte att ta samma dag. Provet tog dem i följd och fick bara
        # en mätpunkt när dagsvillkoret kom på plats.
        with tempfile.TemporaryDirectory() as mapp:
            q, d = _passet(Path(mapp) / "lån.db")
            ut = []
            for varv in range(2):
                nivå, införda = q.nästa_nivå(), set(d.införda())
                plan = q.dagsplan()
                if not plan.introövningar:
                    break
                ut.append(_oinförda_lån(plan, införda, nivå))
                for k in plan.kort:
                    d.presentera(k)
                q.uppdatera()
                for u in plan.meningsfasen:
                    u2 = q.ställ(u)
                    q.bokför(u2, q.rätta(u2, u2.facit, 1.0), paket=q.paket())
                q.uppdatera()
                if varv == 0:
                    _nästa_dygn(d)
                    q.uppdatera()
            return ut

    med = två_nivåer()
    gammal = P.lånevikt
    P.lånevikt = lambda self, per_text: (lambda text, kort: ())
    try:
        utan = två_nivåer()
    finally:
        P.lånevikt = gammal

    if len(med) != len(utan) or not med:
        return [f"kunde inte jämföra: {med} mot {utan}"]
    brister = [f"nivå {i + 1}: vikten gav {a} okända lånekort, utan den {b}"
               for i, (a, b) in enumerate(zip(med, utan)) if a > b]
    if not brister and med == utan:
        brister.append(f"vikten ändrade ingenting: {med} i båda fallen — "
                       "regeln är inte i bruk")
    return brister


def grinden_kräver_en_tidigare_dag(p, data) -> list[str]:
    """4.4. «En nivå kan öppnas när föregångarnas kort infördes en TIDIGARE dag.»

    Följden står i samma stycke: «längs en kedja öppnas högst en nivå per dygn».
    Ingen egen regel om antal nivåer per dag behövs — den ligger i dagsvillkoret.

    Utan det öppnade nivå 2 en minut efter att nivå 1:s kort införts, och fyra
    nivåer gick igenom på fem minuter. Provet tar nivå 1 helt och kräver att
    ingen nivå som BEROR på den öppnar samma dag; en oberoende nivå får öppna,
    och ska göra det — «nivåer som inte beror på varandra behöver inte vänta».
    """
    nivå = p.nästa_nivå()
    if not nivå:
        return ["ingen nivå att börja med"]
    plan = p.dagsplan()
    if not plan.introövningar:
        return ["dagsplanen är tom"]
    _introfasen(p, plan)
    for u in plan.meningsfasen:
        u2 = p.ställ(u)
        p.bokför(u2, p.rätta(u2, u2.facit, 1.0), paket=p.paket())
    p.uppdatera()
    if not (nivå <= data.införda()):
        return ["nivån blev inte införd — provet kan inte pröva grinden"]

    nästa = p.nästa_nivå()
    if not nästa:
        return []
    kraven = frozenset().union(*(p.krav.get(k, frozenset()) for k in nästa))
    beroende = (kraven - nästa) & nivå
    return ([f"{sorted(map(str, nästa))} öppnade samma dag fast den kräver "
             f"{sorted(map(str, beroende))}, som infördes i dag"]
            if beroende else [])


INVARIANTER = [
    ("introfasen bokför ingenting", introfasen_bokför_ingenting, True),
    ("introövningen har ett enda mål", introövningen_har_ett_mål, False),
    ("källmeningen ställs en gång per dag", källmeningen_ställs_en_gång, True),
    ("målen är åtskilda", målen_är_åtskilda, False),
    ("uppgiften väljs i tid", uppgiften_väljs_i_tid, False),
    ("paketet införs helt eller inte alls", paketet_införs_helt, True),
    ("dag ett går att komma igenom", dag_ett_går_att_komma_igenom, True),
    ("slutna ordklasser är grindade", slutna_ordklasser_är_grindade, True),
    ("korten införs när de går rätt", korten_införs_när_de_går_rätt, True),
    ("orden lärs ut före mönstret", orden_lärs_ut_före_mönstret, True),
    ("presenterat betyder klarat", presenterat_betyder_klarat, True),
    ("dagsplanen är genomförbar", dagsplanen_är_genomförbar, True),
    ("meningen använder bara tillåtet", meningen_använder_bara_tillåtet, True),
    ("lånekorten är de kända", lånekorten_är_de_kända, True),
    ("grinden kräver en tidigare dag", grinden_kräver_en_tidigare_dag, True),
]


def _kör(namn, fn, med_data, mapp: Path, n: int) -> list[str]:
    p, data = _passet(mapp / f"kurs{n}.db")
    return fn(p, data) if med_data else fn(p)


# ── falsifieringen ───────────────────────────────────────────────────


def _falsifiera(mapp: Path) -> list[str]:
    """Varje gammalt beteende ska fälla sin invariant."""
    brister = []
    fall = [
        ("källmeningen fick ställas om samma dag",
         "källmeningen ställs en gång per dag", källmeningen_ställs_en_gång, True,
         (Kursdata, "dagens_källtexter", lambda self: set())),
        ("paketet infördes kort för kort",
         "paketet införs helt eller inte alls", paketet_införs_helt, True,
         (Passet, "bokför", None)),
        ("reservtillåtelsen släppte in varje ordkort",
         "slutna ordklasser är grindade", slutna_ordklasser_är_grindade, True,
         (Passet, "_fritt_ord", lambda self, kort: kort.familj == "ord")),
        ("ensamövningen fanns inte",
         "dag ett går att komma igenom", dag_ett_går_att_komma_igenom, True,
         (Passet, "ensamövning", lambda self, kort, plan=None: None)),
        # Ordförrådet var paketets egna ord och inget mer. Då finns en enda
        # källmening — «Tid står.» — och fyra av fem nivåkort hamnade i
        # karantän redan dag ett.
        # Planens meningar är färdigbyggda; utan omprövningen av villkor 1
        # släpps kort som introfasen aldrig hann presentera.
        ("planens meningar prövades inte mot villkor 1",
         "meningen använder bara tillåtet", meningen_använder_bara_tillåtet, True,
         (Passet, "tillåten_mening", lambda self, uppgift, mål: True)),
        # Märkningen följde inte med matchningen: uppgiften bar det kort som
        # råkade samla in källmeningen.
        ("planens uppgifter bar fel kort som mål",
         "introövningen har ett enda mål", introövningen_har_ett_mål, False,
         (Passet, "märk", lambda self, uppgift, kort: uppgift)),
        # Grinden såg bara MÄNGDEN införda kort, inte vilken dag de infördes.
        ("grinden saknade sitt dagsvillkor",
         "grinden kräver en tidigare dag", grinden_kräver_en_tidigare_dag, True,
         (Kursdata, "införda_dagar", lambda self: {k: "0000-00-00"
                                                  for k in self.införda()})),
        ("ordförrådet räckte inte till fler meningar",
         "dagsplanen är genomförbar", dagsplanen_är_genomförbar, True,
         (Passet, "_ordförråd", lambda self, korten, tillåtna: frozenset(
             k for k in self.paket() if k.familj == "ord"))),
    ]
    for i, (gammalt, invariant, fn, med_data, (klass, namn, ers)) in enumerate(fall):
        p, data = _passet(mapp / f"fals{i}.db")
        objekt = data if klass is Kursdata else p
        if ers is None:
            # Det gamla `bokför`: inför varje kort som inte föll, oavsett paket.
            def ers(self, uppgift, rättning, godkända=frozenset(), höjt=None,
                    flagga=None, paket=frozenset()):
                from sprakprog.rattning import FEL, RÄTT
                for kort, mätt in rättning.betyg.items():
                    betyg = RÄTT if kort in godkända else mätt
                    self.data.bokför(kort, mål=kort in uppgift.mål, betyg_diff=mätt,
                                     betyg=betyg, mening_id=uppgift.mening_id)
                    if betyg != FEL:
                        self.data.inför(kort, uppgift.mening_id)
                self.uppdatera()
        with _utan(objekt, namn, ers):
            fel = fn(p, data) if med_data else fn(p)
        status = "✓ föll" if fel else "✗ HÖLL ÄNDÅ"
        print(f"  {status}  {gammalt}")
        if not fel:
            brister.append(f"invarianten «{invariant}» fångar inte «{gammalt}»")
    return brister


def main() -> int:
    if not KARTA.exists() or not NIVÅER.exists():
        print(f"saknar {KARTA.name} eller {NIVÅER.name} — bygg dem först")
        return 0
    brister: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        mapp = Path(t)
        print("── invarianterna ──")
        for n, (namn, fn, med_data) in enumerate(INVARIANTER):
            start = time.perf_counter()
            fel = _kör(namn, fn, med_data, mapp, n)
            print(f"  {'✓' if not fel else '✗'} {namn}"
                  f"   ({time.perf_counter() - start:.1f} s)")
            for b in fel:
                print(f"      {b}")
            brister += fel

        print("\n── falsifiering: varje gammalt läge ska fälla sitt prov ──")
        brister += _falsifiera(mapp)

    antal = len(INVARIANTER) + 2
    print(f"\n{antal} kontroller, {len(brister)} brister." if brister
          else f"\n{antal} kontroller, alla håller.")
    return 1 if brister else 0


if __name__ == "__main__":
    raise SystemExit(main())
