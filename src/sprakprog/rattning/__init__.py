"""Rättningen — steg 8 i kärnans byggordning (KÄRNAN 7.2 och 7.3).

Svaret jämförs med facit ord för ord, och varje kort får sitt betyg av de ord
det bestämde. Ett kort som bestämde ett ord som stämmer är rätt; stämmer något
av dess ord inte är det fel. Stavfel och accentfel räknas som fel: rättningen
gissar aldrig vad användaren menade (7.2).

Enheten är renderarens positioner (7.3). Spåret säger vilka utskrivna ord varje
kort bestämde, och luckorna säger var ett kort hade lagt till ett ord som inte
står i svaret. Diffen säger vilka positioner som stämmer.

Ett uppslag är inte alltid ett skrivet ord: "how many" och "inte längre" är
ett uppslag och två ord. `_spann` översätter mellan de två räkningarna.

PREREKVISITSTEGEN (7.3 steg 1) gör att ett ordslarv inte fäller grammatiken:
ordkortet gäller lexemet och inte den ställda formen, ordföljdsregeln graderas
på platsen och inte på stavningen, och ett formkort ograderas när ett annat kort
bär felet — men bara då, för rättningen får aldrig tiga.

VAD SOM INTE ÄR BYGGT ÄN. Steg 2, minsta förklaring, kräver att meningen
renderas om (6.5). Steg 1:s tredje punkt stod här som ogörlig av samma skäl
ända till 2026-11-26, och det var fel: omrenderingarna fanns redan i spåret,
i `Beslut.alternativ`. Se `_förklarar`. Version ett jämför med
en variant: den mening som ställdes. Flera godtagna varianter (6.5) och omrättningen (7.2) kommer med
entydighetsfiltret respektive gränssnittet. Sammansmälta ord — franskans «du»,
där två uppslag blir ETT skrivet ord — går åt andra hållet än `_spann` och
görs när ett språk som smälter samman ord kommer in.
"""

from __future__ import annotations

import difflib
import sqlite3
from collections import Counter
from dataclasses import dataclass

from ..kortmodell import Formtabell, Kort, beslutskort, meningens_kort
from ..rendering.spec import RenderingsFel
from ..rendering.spår import Utskrift

#: Betygen som räknas fram ur diffen (7.2). `Hard` och `Easy` kommer bara från
#: användarens omrättning.
RÄTT, FEL = "good", "again"

#: Korten som gäller STRÄNGEN i ett ords böjning (3.4). De är ordkortets
#: prerekvisit i 7.3: kan man inte ordet kan man inte heller dess form.
FORMKORT = frozenset({"ändelse", "oregelbunden"})


#: Vad användaren skrev på ett uppslags plats, sett från KORTEN där (7.3).
KÄNT = "känt"              #: exakt den ställda formen
ANNAN_FORM = "annan form"  #: en annan form av rätt lexem — «stand» för «stands»
ANNAT_ORD = "annat ord"    #: ingen form av lexemet, eller inget ord alls
#: Namnet hette `ANNAT_ORD` till 2026-11-26 och lästes då som «ett ord utanför
#: kursen». Det är inte vad läget betyder: meningen innehåller bara ord som
#: introducerats, och läget beskriver vad ANVÄNDAREN skrev.


def _läget(tabell: Formtabell, o, sträcka: range, lika: set[int],
           motpart: dict) -> str:
    """Vilket av de tre lägena svaret är i på ett uppslags plats.

    Skillnaden mellan ANNAN_FORM och ANNAT_ORD är hela prerekvisitstegen: skrev
    användaren en annan form av rätt lexem KAN hen ordet, och det är cellvalet
    som brast. Skrev hen något annat vet vi ingenting om formen.

    UPPSLAGET FÅR INTE SVARA «ANNAT ORD» PÅ ETT PROGRAMFEL (lagat 2026-11-26).
    Förut låg de två raderna i ett `try` som fångade allt och svarade
    ANNAT_ORD. Ett trasigt lexem eller en databas som inte svarar blev då
    utsagan «användaren kan inte ordet», och ordkortet fick ett underkänt för
    något användaren inte gjort — exakt den falska raden i inlärarloggen som
    `Rättningsfel` finns för att förhindra.

    Att det aldrig syntes beror på att felet är ONÅBART i normal drift:
    `meningens_kort` slår upp varje uppslags lexem och varje cells kort INNAN
    rättningen kommer hit, utan att fånga något, och `Formtabell` cachar
    resultatet. Når vi den här raden har alltså samma uppslag redan lyckats en
    gång. Smäller det ändå har datan ändrats under oss, och då är det rätt att
    vägra.
    """
    if all(i in lika for i in sträcka):
        return KÄNT
    skrivet = [motpart.get(i) for i in sträcka]
    if any(x is None for x in skrivet):
        return ANNAT_ORD
    try:
        lexem = tabell.u.lexem(o.koncept, o.variant)
        former = {f.lower() for f in tabell.u._celler(lexem).values() if f}
    except (RenderingsFel, sqlite3.Error) as e:
        raise Rättningsfel(
            f"formerna för {o.koncept!r} gick inte att slå upp: {e}. "
            f"Rättningen vägrar hellre än skriver «annat ord» på ett "
            f"programfel — det hade gett ordkortet ett underkänt användaren "
            f"inte förtjänat") from e
    return ANNAN_FORM if " ".join(skrivet).lower() in former else ANNAT_ORD


def _är_ordföljd(kort: Kort) -> bool:
    """En regel som PLACERAR ord, till skillnad från en som väljer form.

    Samma skillnad som prerekvisitstegen i 7.3 vilar på, och samma som
    `Passet._åtskilda` gör: «ett ordföljdsbeslut placerar ordet, det väljer
    inte dess form».
    """
    return kort.typ == "regel" and kort.nyckel[0] == "ordning"


class Rättningsfel(Exception):
    """Rättningen kan inte säga vilket kort som bär vilket ord.

    Kastas hellre än att betygsätta på en gissning: en falsk rad i loggen ger
    ett kort en repetition det inte förtjänat, och det som brast får ingen.
    """


@dataclass(frozen=True, slots=True)
class Rättning:
    """Vad diffen säger om svaret."""
    rätt: bool
    #: kort → again · good, räknat ur diffen
    betyg: dict[Kort, str]
    #: (facit, svar) per position: None när ordet saknas på sin sida
    diff: tuple[tuple[str | None, str | None], ...]

    @property
    def fel(self) -> list[Kort]:
        return sorted((k for k, b in self.betyg.items() if b == FEL), key=str)


@dataclass(frozen=True, slots=True)
class Jämförelse:
    """Hur svaret skiljer sig från facit, per position i FACIT.

    `ersatt` och `saknad` skiljer två fall som båda är «inte lika» men betyder
    olika saker för attributionen (7.3): ett ERSATT ord står på sin plats med
    fel form, ett SAKNAT ord finns inte i svaret alls. Ordföljdsregeln bryr sig
    bara om det andra — «för ett ord på fel plats den regel som placerade det».
    """
    lika: set[int]
    ersatt: set[int]
    saknad: set[int]
    tillagda: set[int]
    diff: list
    #: facits position → det ord användaren skrev där, eller None när inget
    #: ord i svaret hamnade på platsen. Utan det går «fel lexem» inte att
    #: skilja från «rätt lexem i fel form» (7.3 steg 1).
    motpart: dict


def _jämför(facit: list[str], svar: list[str]) -> Jämförelse:
    """Vilka av facits ord som stämmer, hur de övriga avviker, och diffen.

    De tillagda orden räknas per lucka: lucka `i` ligger före facits ord `i`,
    och lucka `len(facit)` sist, som i spåret.
    """
    lika: set[int] = set()
    ersatt: set[int] = set()
    saknad: set[int] = set()
    tillagda: set[int] = set()
    motpart: dict[int, str | None] = {}
    diff: list[tuple[str | None, str | None]] = []
    for tagg, i1, i2, j1, j2 in difflib.SequenceMatcher(
            a=facit, b=svar, autojunk=False).get_opcodes():
        if tagg == "equal":
            lika.update(range(i1, i2))
            motpart.update(zip(range(i1, i2), (svar[j] for j in range(j1, j2))))
            diff.extend((facit[i], svar[j]) for i, j in zip(range(i1, i2), range(j1, j2)))
        elif tagg == "insert":
            tillagda.add(i1)
            diff.extend((None, svar[j]) for j in range(j1, j2))
        elif tagg == "delete":
            saknad.update(range(i1, i2))
            motpart.update({i: None for i in range(i1, i2)})
            diff.extend((facit[i], None) for i in range(i1, i2))
        else:
            # Ett utbytt stycke kan också ha fler ord i svaret än i facit, och de
            # orden är tillagda i styckets båda ändar.
            if j2 - j1 > i2 - i1:
                tillagda.update({i1, i2})
            # De facitord som har en motpart i stycket är ERSATTA; blir stycket
            # kortare i svaret saknar resten motpart.
            par = min(i2 - i1, j2 - j1)
            ersatt.update(range(i1, i1 + par))
            saknad.update(range(i1 + par, i2))
            motpart.update(zip(range(i1, i1 + par), (svar[j] for j in range(j1, j1 + par))))
            motpart.update({i: None for i in range(i1 + par, i2)})
            diff.extend((facit[i] if i < i2 else None, svar[j] if j < j2 else None)
                        for i, j in zip(range(i1, max(i2, i1 + j2 - j1)),
                                        range(j1, max(j2, j1 + i2 - i1))))
    return Jämförelse(lika, ersatt, saknad, tillagda, diff, motpart)


#: Tecken som MENINGEN får av `spec.slutar` och av versaliseringen i
#: renderarens `rendera`, inte av något kort: punkt, frågetecken, utropstecken
#: och spanskans inledande ¿ och ¡.
SATSENS_FORM = ".!?¿¡…"


def _avskalad(ord_: list[str]) -> list[str]:
    """Orden utan det ingen bestämde: sluttecknet och den inledande versalen.

    Ett korts positioner är de utskrivna ord vars FORM kortet bestämde (6.2).
    Punkten i slutet bestämmer inget kort — den kommer ur `spec.slutar`, som
    läser meningens modus — och den inledande versalen kommer ur
    renderarens sista rad. Ändå satt de på samma tokens som orden, så ett
    svar utan punkt fällde varje kort som stod på sista ordet.

    Det hände direkt i den första riktiga körningen: «Time exists» i stället
    för «Time exists.» underkände fem kort, däribland ordet, ändelsen,
    kongruensen och ordföljden. Inget av dem hade gjort något.

    Skillnaden försvinner alltså ur ATTRIBUTIONEN. Den syns fortfarande för
    användaren, eftersom facit skrivs ut som det är.
    """
    if not ord_:
        return ord_
    ut = list(ord_)
    ut[-1] = ut[-1].rstrip(SATSENS_FORM)
    ut[0] = ut[0].lstrip(SATSENS_FORM)
    if ut[0][:1].isupper():
        ut[0] = ut[0][:1].lower() + ut[0][1:]
    return ut


def _spann(ut: Utskrift, facit: list[str]) -> list[range]:
    """Var varje uppslag står i den skrivna texten.

    Spåret räknar UPPSLAG och texten räknar SKRIVNA ORD, och det är inte
    samma sak. Ett uppslag är ett ord för spåret men kan vara flera på
    pappret: "how many", "inte längre", "den här". Läses spårets index som
    ett ordindex glider allt efter det första flerordiga uppslaget ett steg,
    och rättningen skyller på grannen i stället för på den skyldige.

    Felet var inte teoretiskt. Med facit "How many books does the girl
    read?" gav svaret "How many book does the girl read?" — fel numerus på
    substantivet — godkänt substantiv och underkänt do, kongruens och
    inversion, sex kort som inte hade gjort något. Och svaret "...the girl
    reads?" gick igenom helt, fast det var fel.

    Motsatsen — flera uppslag som smälter ihop till ETT skrivet ord, som
    franskans «du» — får samma svar när den dagen kommer: spannet är tomt
    eller delat i stället för ett ord långt (KÄRNAN 7.3).
    """
    spann: list[range] = []
    nästa = 0
    for o in ut.ord:
        antal = len(str(o).split())
        spann.append(range(nästa, nästa + antal))
        nästa += antal
    if nästa != len(facit):
        raise Rättningsfel(
            f"uppslagen är {nästa} skrivna ord men meningen har {len(facit)}: "
            f"{ut.text!r}. Rättningen kan inte säga vilket kort som bär vilket "
            f"ord, och vägrar hellre än gissar")
    return spann


def _stegen(betyg: dict, formkort: dict, korten: list) -> None:
    """Prerekvisitstegen som efterpass: ta bort formkortens betyg där ett annat
    kort redan bär felet (7.3 steg 1).

    Villkoret «ett annat kort bär det» är inte pynt. Stegen förutsätter att det
    finns ett beslut att lägga skulden på, och ibland finns det inte: «How many
    books» blir plural av frågedeterminantens krav, inte av något `val`-kort.
    Ograderades pluraländelsen ändå föll ingenting alls, och «How many book …»
    blev ett perfekt svar. Rättningen får aldrig tiga.
    """
    for k, formens in formkort.items():
        andra = [kort for kort, platser in korten
                 if kort.typ not in FORMKORT and betyg.get(kort) == FEL
                 and ("ord", k) in platser]
        if andra:
            for kort in formens:
                betyg.pop(kort, None)


def _förklarar(b, avvikande: set[str]) -> bool:
    """Ger något ANNAT utfall av beslutet ett ord användaren faktiskt skrev?

    Det här är steg 1:s tredje punkt i 7.3 — «förklarar ett beslut som väljer
    cell avvikelsen, har beslutet fallit». Punkten stod länge som ogörlig med
    skälet att den kräver att meningen renderas om. Den kräver det, men
    omrenderingarna FINNS REDAN: spåret räknar ut ett besluts positioner genom
    att tvinga beslutet till vart och ett av sina andra utfall och rendera om,
    och behåller orden i `Beslut.alternativ`. `spår.py` säger det självt —
    «omrenderingarna är också de alternativ rättningen jämför svaret med när
    den avgör om ett kort förklarar en avvikelse (7.3)». Rättningen läste dem
    bara aldrig (mätt 2026-11-26: `alternativ` förekom inte i filen).

    Mätt på «How many books does the girl read?»:

        svaret «... the girl write?»   inget utfall av tempusform eller
                                      do_omskrivning ger «write» → inget av
                                      dem förklarar avvikelsen
        svaret «... the girl reads?»   `utan_do` ger «how many books READS the
                                      girl» → do_omskrivning förklarar den,
                                      tempusform gör det inte
        svaret «... does a girl read?» `obestämd_artikel` ger «does A girl
                                      read» → bestämningen förklarar den

    Det sista fallet är varför ingen handskriven lista över «beslut som väljer
    ord» behövs: att artikelbeslutet brast syns på att ett annat utfall skriver
    just det ord användaren skrev. En lista kunde glömma en familj, och då
    skulle korrekta svar underkännas utan att något märker det.
    """
    if not avvikande:
        return False
    for ord_ in (b.alternativ or {}).values():
        if {str(o).lower() for o in ord_} & avvikande:
            return True
    return False


def _punkt3(betyg: dict, avvikelser: dict, beslut_för: dict, korten: list) -> None:
    """Håll de cellbeslut som inte förklarar sin avvikelse (7.3 steg 1 punkt 3).

    HÅLLET, inte godkänt: kortet tas ur betygen och får ingen rad i loggen.
    Betyget skrivs inte om till `good` — beslutet prövades inte, och att säga
    att det gick rätt vore lika påhittat som att säga att det gick fel. Planen
    i `paradigm/BEDÖMNING.md` §4 kallar det det tredje betygstillståndet.

    MEN BARA NÄR NÅGON ANNAN TAR SKULDEN, av samma skäl som `_stegen`:
    rättningen får aldrig tiga. Bär inget annat kort felet på platsen är
    beslutet det enda kort som kan göra det, och då gör det det.
    """
    for kort, avvikande in avvikelser.items():
        b = beslut_för.get(kort)
        if b is None or _förklarar(b, avvikande):
            continue
        platser = {p for k, p in korten if k == kort for p in p}
        andra = [k for k, p in korten
                 if k != kort and betyg.get(k) == FEL and p & platser]
        if andra:
            betyg.pop(kort, None)


def rätta(tabell: Formtabell, ut: Utskrift, svar: str) -> Rättning:
    """Betyget per kort, räknat ur diffen mellan facit och svaret (7.3).

    PREREKVISITSTEGEN är steg 1 i 7.3: «Kan man inte ordet kan man inte heller
    dess form.» Utan den var rättningen rent positionell — varje kort som
    bestämde ett avvikande ord föll — och ett ordslarv skrev falska betyg på
    grammatiken. Mätt på «Time suits.» besvarad «Time fits.»: fem kort föll,
    men fyra av dem hade gjort allt rätt. Ordföljden var riktig, kongruensen
    riktig, tempus riktigt, ändelsen riktig; bara lexemet var fel.

    Stegets tre punkter:

    1. **Föll `ord` är formkorten ograderade.** Ändelsen och den oregelbundna
       formen gäller strängen i ordets böjning, och den böjningen prövades
       aldrig — användaren skrev ett annat ord.
    2. **Ordföljdsregeln graderas på PLATSEN, inte på formen.** 7.3 säger vilka
       kort en avvikande position har: «formens kort, och FÖR ETT ORD PÅ FEL
       PLATS den regel som placerade det». Ett ord som står rätt men är
       felstavat säger ingenting om ordföljden, och regeln ska inte falla för
       det. Ett ord är på fel plats när dess sträng finns i svaret men inte där
       den skulle, eller när den inte finns alls.

    3. **Ett cellbeslut som inte förklarar avvikelsen HÅLLS.** «Förklarar ett
       beslut som väljer cell avvikelsen, har beslutet fallit» — och gör det
       inte det, prövades beslutet inte. Se `_förklarar` och `_punkt3`.
       Punkten stod som ogörlig till 2026-11-26 med skälet att den kräver
       omrenderingar; de fanns redan i spåret. Förut föll cellbesluten med sin
       position, och konsekvensen stod i 7.3 själv: «Har användaren i själva
       verket valt rätt men glömt ändelsen får valet skulden; det kommer
       tillbaka snart och klaras.» Mätt vad den konsekvensen kostade: på
       «How many books does the girl write?» föll tre kort och ett hade gjort
       fel, och på «... the girl reads?» två kort och ett. Efter punkt 3 faller
       ett kort i båda fallen.
    """
    facit = ut.text.split()
    spann = _spann(ut, facit)
    # Attributionen jämför utan satsens form; diffen som visas behåller den.
    skalat_facit, skalat_svar = _avskalad(facit), _avskalad(svar.split())
    j = _jämför(skalat_facit, skalat_svar)
    lika, tillagda = j.lika, j.tillagda
    diff = _jämför(facit, svar.split()).diff

    # PÅ FEL PLATS: strängen finns i svaret men inte här, eller inte alls.
    # «Time fits» rör inte ordföljden — «suits» finns inte i svaret, så ordet
    # står kvar på sin plats med fel form. «Stands time» gör det: «time» finns,
    # fast någon annanstans.
    kvar_i_svaret = Counter(skalat_svar)
    for i in lika:
        kvar_i_svaret[skalat_facit[i]] -= 1
    fel_plats = {i for i in j.ersatt if kvar_i_svaret[skalat_facit[i]] > 0} | j.saknad

    korten = meningens_kort(tabell, ut)

    def positionerna(platser) -> set[int]:
        return {i for sort, k in platser if sort == "ord" for i in spann[k]}

    läget = {k: _läget(tabell, o, spann[k], lika, j.motpart)
             for k, o in enumerate(ut.ord)}

    beslut_för = {beslutskort(tabell.språk, b): b for b in ut.beslut if b.syns}

    betyg: dict[Kort, str] = {}
    formkort: dict[int, list[Kort]] = {}
    #: kort → de ord användaren skrev där kortet föll, för punkt 3
    avvikelser: dict[Kort, set[str]] = {}
    for kort, platser in korten:
        uppslagen = {k for sort, k in platser if sort == "ord"}
        lägen = {läget[k] for k in uppslagen}
        if kort.typ in FORMKORT and lägen - {KÄNT}:
            for k in uppslagen:
                formkort.setdefault(k, []).append(kort)
        ord_ = positionerna(platser)
        # Lucka `j` ligger före uppslag `j`, alltså vid spannets början, och
        # lucka `len(ord)` sist av allt.
        luckor = {spann[k].start if k < len(spann) else len(facit)
                  for sort, k in platser if sort == "lucka"}
        if kort.typ == "ord":
            # Ordkortet gäller LEXEMET: klarat om svaret är en form reglerna
            # kan bygga av rätt lexem (3.3), som glosan. Krävdes exakt den
            # ställda formen föll ordet för en glömd ändelse — och då blev
            # ändelsekortet ograderat av stegen ovan, alltså föll ingen för
            # felet.
            prövad = ANNAT_ORD not in lägen
        elif _är_ordföljd(kort):
            prövad = not (ord_ & fel_plats)
        else:
            prövad = ord_ <= lika
        # En lucka är prövad bara när svaret varken lade till ett ord där eller
        # ändrade orden runt den: annars säger den ingenting om kortet.
        rätt = prövad and all(
            i not in tillagda and (i == 0 or i - 1 in lika) and (i == len(facit) or i in lika)
            for i in luckor)
        # Ett kort kan stå på flera platser i samma mening; faller en faller kortet.
        if betyg.get(kort) != FEL:
            betyg[kort] = RÄTT if rätt else FEL
        # Punkt 3 behöver de ord användaren skrev där kortet föll — och bara
        # när felet satt på ett ORD. Ett kort som föll för en LUCKA har ingen
        # avvikande sträng att leta efter bland utfallen, och ska falla:
        # användaren utelämnade ordet beslutet satte in.
        if not prövad and kort.typ == "regel" and not _är_ordföljd(kort):
            skrivna = {j.motpart[i].lower() for i in ord_ - lika
                       if j.motpart.get(i)}
            if skrivna:
                avvikelser.setdefault(kort, set()).update(skrivna)

    # 7.3 STEG 1, prerekvisitstegen, som ett efterpass: «Föll `ord` är
    # formkorten ograderade», och skrev användaren en annan form av rätt lexem
    # var det cellvalet som brast — «har användaren i själva verket valt rätt
    # men glömt ändelsen får valet skulden; det kommer tillbaka snart och
    # klaras, och formkortet mäts en annan gång».
    #
    # MEN BARA NÄR NÅGON ANNAN TAR SKULDEN. Stegen förutsätter att det finns ett
    # beslut att lägga den på, och ibland finns det inte: «How many books» blir
    # plural av frågedeterminantens krav, inte av något `val`-kort. Ograderades
    # pluraländelsen ändå föll ingenting alls, och «How many book …» blev ett
    # perfekt svar. Då är formkortet det enda kort som kan bära felet, och det
    # gör det. Rättningen får aldrig tiga.
    #
    # Att ogradera BESLUTEN med `_stegen` vore dessutom att läsa stegen bredare
    # än den är: `val/bestämning/bestämd_artikel` väljer inte ordets cell utan
    # vilket ord som skrivs, och skrev användaren «a» för «the» syns det att
    # beslutet brast. Besluten har sin egen regel i `_punkt3`, och den skiljer
    # de två fallen utan att någon lista över kortfamiljer skrivs för hand:
    # artikelbeslutet faller för att ett annat av DESS utfall skriver just «a».
    _stegen(betyg, formkort, korten)
    _punkt3(betyg, avvikelser, beslut_för, korten)
    return Rättning(len(lika) == len(facit) and not tillagda, betyg, tuple(diff))
