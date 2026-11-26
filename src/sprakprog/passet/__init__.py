"""Dagspasset — steg 6 i kärnans byggordning (KÄRNAN 5.1–5.3, 6.2, 6.3).

Passet har två faser (5.1). I INTROFASEN presenteras dagens nya kort, en övning i
taget, och ingenting bokförs. I MENINGSFASEN översätts meningar, och varje möte
bokförs (7.1). Ett nytt kort blir infört när det går rätt i en mening.

DET SVAGA ÄR MÅLEN (6.2). Ett kort är svagt när det hör till dagens mål och inte
klarats i dag: de förfallna korten, dagens nya och det som fallit i dag. Meningen
byggs av så många svaga kort som budgeten tillåter.

BUDGETEN (6.3): sannolikheten för två fel i samma mening är högst τ = 1 −
retentionsmålet. Med ett fel syns det i diffen var det sitter, med två gör det
inte.

VAD SOM INTE ÄR BYGGT ÄN, och som därför är enkelt här:
- Värdet per mening (6.6) väljer bland de meningar som ryms; version ett tar den
  kortaste som ryms.
- Tidsmodellen (5.5) säger hur många nya kort dagen ska ha; här väljer användaren
  själv när ett nytt kort ska tas.
- Entydighetsfiltret (6.5) ger flera godtagna varianter; här är facit den mening
  som ställdes, och villkor 3 och 7 i 6.1 prövas bara till den del som går utan
  omrenderingarna.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..fsrslager import Lager
from ..kortmodell import Kort, meningens_kort
from ..kurs import Kursdata
from ..rattning import FEL, RÄTT, Rättning, rätta
from ..nivaer import SLUTNA_ORDKLASSER
from ..rendering import RenderingsFel, spåra
from ..rendering.spår import Utskrift
from ..sammansattning import Sammansättare, Träff

#: Längsta mening sökningen letar efter, i ord. Följer av budgeten (6.3): taket
#: är fem mål och fem övriga kort, och varje ord i en mening bär minst ett eget
#: kort, så en mening som ryms har högst tio ord.
LÄNGSTA = 10


@dataclass(frozen=True, slots=True)
class Uppgift:
    """En ställd mening: källtexten, facit och vilka kort den prövar."""
    träff: Träff
    ut: Utskrift
    källtext: str
    mål: frozenset
    övriga: frozenset
    mening_id: int | None = None

    @property
    def facit(self) -> str:
        return self.ut.text


@dataclass(frozen=True, slots=True)
class Glosa:
    """Introövningen för ett innehållsord: betydelse → form (5.4).

    Funktionsord får INTE en glosa utan en mening med ordet som enda mål —
    «en glosa vore sällan entydig: engelskans *a* är både en och ett» (5.4).
    Därför gäller den här bara de öppna ordklasserna.
    """
    kort: Kort
    källtext: str
    facit: str
    #: Varje form av lexemet godtas: kortet klaras om användaren skriver en
    #: form reglerna kan bygga av rätt lexem (3.3).
    former: frozenset


def _minst_ett_fel(p: list[float]) -> float:
    """P(≥2 fel) för oberoende kort med sannolikheterna `p` att bli rätt (6.3)."""
    inga = 1.0
    for x in p:
        inga *= x
    ett = sum((1 - x) * inga / x if x else 0.0 for x in p)
    return max(0.0, 1 - inga - ett)


@dataclass(frozen=True, slots=True)
class Dagsplan:
    """Dagens kort, och VILKEN MENING som bär vilket (5.1, 3.10).

    «Vilka nya kort dagen har är bestämt innan passet börjar» (5.1). Att
    bestämma korten räcker inte: villkor 8 i 6.1 säger att en källmening
    bara får ställas en gång per dag, så MATERIALET FÖRBRUKAS medan dagen
    går. Ett kort som var prövbart på morgonen kan vara oåtkomligt på
    eftermiddagen, och det var precis vad som hände — fyra presenterade ord
    gick inte att pröva alls, och dagen förklarades klar med fulla högar.

    Planen är därför en TILLDELNING: varje nytt kort får sin egen
    introövning, och huvuddelen får egna meningar reserverade. Alla olika.
    Ordförrådet är det planen kräver, inte det som råkar dyka upp.
    """
    lektioner: dict
    introövningar: tuple[tuple[Kort, Uppgift], ...]
    meningsfasen: tuple[Uppgift, ...]
    karantän: tuple[tuple[Kort, str], ...]

    @property
    def orden(self) -> frozenset:
        """Ordförrådet planens meningar behöver."""
        ut: set = set()
        for u in ([u for _, u in self.introövningar]
                  + list(self.lektioner.values()) + list(self.meningsfasen)):
            ut |= {k for k in u.träff.kort if k.familj == "ord"}
        return frozenset(ut)

    @property
    def kort(self) -> frozenset:
        """Allt dagen lär ut: mönsterkorten och orden de behöver."""
        return frozenset(k for k, _ in self.introövningar) | self.orden


def _i_går() -> str:
    """Gårdagens tidsstämpel, för att läsa upp det sparade tempot."""
    return (datetime.now().astimezone() - timedelta(days=1)).isoformat()


def _matcha(kandidater: dict, orden=None, vikt=None) -> dict:
    """Ge varje kort en EGEN mening, om det går (en matchning).

    Girigt räcker inte: tar det första kortet den enda mening som passar det
    andra, blir det andra utan. Augmenterande stigar löser det, och grafen
    är liten — några kort mot några meningar.

    `orden` ger en menings ord, och används för att SPRIDA valet. En
    matchning är fri att välja vilken av flera lika goda meningar som helst,
    och den fria tog den första varje gång: tre av fem introövningar hamnade
    på `passa`, som då hade en ENDA mening kvar i huvuddelen medan `sitta`
    hade fyra. Föll `passa` fanns ingen mening att ta om det med, och dagen
    slutade med kortet oinfört och ett påstående om att högarna var tomma.

    Spridningen är också dagens enda reserv mot fel. Hur många omtag en dag
    behöver går inte att veta i förväg — det beror på användaren — men ett
    ord vars meningar alla är förbrukade har garanterat noll.

    `vikt(mening, kort)` går FÖRE spridningen och är 5.4:s lånekortsregel:
    «generatorn väljer lånekort så att sannolikheten att alla blir rätt är så
    hög som möjligt». Spridningen är bara en tiebreak bland lika goda meningar.
    """
    par: dict = {}
    använt: Counter[str] = Counter()

    def kostnad(text: str) -> tuple:
        mängd = orden(text)
        return (max((använt[o] for o in mängd), default=0),
                sum(använt[o] for o in mängd))

    def stig(kort, sedda: set) -> bool:
        val = kandidater[kort]
        if orden is not None or vikt is not None:
            val = sorted(val, key=lambda t: (
                vikt(t, kort) if vikt is not None else (),
                kostnad(t) if orden is not None else (),
                val.index(t)))
        for mening in val:
            if mening in sedda:
                continue
            sedda.add(mening)
            if mening not in par or stig(par[mening], sedda):
                par[mening] = kort
                return True
        return False

    for kort in kandidater:
        if stig(kort, set()) and orden is not None:
            # Räknas om ur `par`: en augmenterande stig kan ha flyttat på
            # meningar som redan var tilldelade.
            använt.clear()
            for text in par:
                använt.update(orden(text))
    return {kort: mening for mening, kort in par.items()}


class Passet:
    """Dagens pass för en kurs."""

    def __init__(self, data: Kursdata, sammansättare: Sammansättare, lager: Lager,
                 krav: dict[Kort, frozenset], nivåer: list[frozenset],
                 tidsmodell=None, kort_i_kursen: int | None = None) -> None:
        self.data, self.s, self.lager = data, sammansättare, lager
        self.krav, self.nivåer = krav, nivåer
        #: `tid.Tidsmodell`, eller None. Injiceras som kraven och nivåerna:
        #: passet läser inga filer. Utan den finns ingen gräns för hur mycket
        #: nytt en dag tar, och `n` är användarens tangenttryckning.
        self.tidsmodell = tidsmodell
        #: Hur många kort kursen har i allt — horisonten i 5.5.
        self.kort_i_kursen = kort_i_kursen
        self.τ = 1 - lager.retention
        self._tillstånd: dict = {}
        self._i_dag: dict = {}
        self._öppen: dict[str, bool] = {}
        self._paket: dict[frozenset, frozenset] = {}
        self.uppdatera()

    # ── läget ──

    def uppdatera(self) -> None:
        """Läs om det som mötena säger: tillstånden och dagens senaste betyg."""
        self._tillstånd = self.lager.tillstånd()
        dag = self.data.dag()
        self._i_dag = {m.kort: m.betyg for m in self.data.möten()
                       if self.data.dag(m.tid) == dag}

    def tillåtna(self) -> set[Kort]:
        """Vad en mening får använda: införda kort och dagens presenterade (5.2)."""
        return self.data.tillåtna()

    def p(self, kort: Kort) -> float:
        """Sannolikheten att kortet blir rätt (6.2).

        Direkt efter ett möte ger FSRS R ≈ 1 oavsett svar, och ett nytt kort har
        inget tillstånd alls. För ett kort som presenterats i dag utan att ha
        mötts, och för ett kort som fallit i dag, gäller därför retentionsmålet
        tills andelarna är mätta ur loggen.
        """
        t = self._tillstånd.get(kort)
        if t is None or self._i_dag.get(kort) == FEL:
            return self.lager.retention
        return self.lager.r(t)

    def svaga(self) -> set[Kort]:
        """Dagens mål som inte klarats i dag, plus det som fallit i dag: F i 6.2."""
        införda = self.data.införda()
        nya = {k for k in self.data.presenterade() if k not in införda}
        klarade = {k for k, betyg in self._i_dag.items() if betyg == RÄTT}
        fallna = {k for k, betyg in self._i_dag.items() if betyg == FEL}
        return ((self.lager.förfallna() | nya) - klarade) | fallna

    # ── meningsfasen ──

    def _åtskilda(self, ut, mål: set) -> bool:
        """6.1 punkt 5: inga två svaga kort styr samma ställe i meningen.

        Budgeten (6.3) ser till att felen blir FÅ; det här ser till att de blir
        ÅTSKILJBARA. KÄRNAN 6.2 kallar dem samma tal sett från två håll, och
        bara det ena höll förut: passet räknade sannolikheten för två fel men
        aldrig om två mål stod på samma ord.

        Exemplet i 6.2: när genuskortet för `hus` är målet duger «ett hus», där
        genuset syns på ett ställe. «ett stort hus» duger inte — där styr
        genuset både artikeln och adjektivet, och ett fel går inte att knyta
        till ett enda kort.

        UNDANTAGET är ETT ORDS PREREKVISITSTEGE (6.2, 7.3): ordet självt, det
        beslut som valde dess cell, och den cellens formkort. De delar alltid
        position, men 7.3 skiljer dem åt utan att behöva positionerna — föll
        ordet är formen ograderad; förklarar beslutet avvikelsen har beslutet
        fallit; är svaret en form som inte finns har formkortet fallit. Därför
        får ett mönster prövas på ett nytt ord (6.4).

        Ett ORDFÖLJDSbeslut hör inte till stegen: det placerar ordet, det
        väljer inte dess form, och 7.3 har ingen prerekvisit som skiljer det
        från formkortet. Två mål som delar en LUCKA är aldrig åtskilda — där
        finns inget ord att hänga en stege på.
        """
        platser: dict = {}
        for kort, ps in meningens_kort(self.s.tabell, ut):
            if kort in mål:
                platser.setdefault(kort, set()).update(ps)

        stegar: list[set] = []
        for o in ut.ord:
            stegar.append(set(self.s.tabell.kort(
                self.s.u.lexem(o.koncept, o.variant), o.cell)))
        for kort, ps in meningens_kort(self.s.tabell, ut):
            if kort.typ == "regel" and kort.nyckel[0] == "val":
                for sort, i in ps:
                    if sort == "ord":
                        stegar[i].add(kort)

        lista = sorted(platser, key=str)
        for i, a in enumerate(lista):
            for b in lista[i + 1:]:
                delat = platser[a] & platser[b]
                if not delat:
                    continue
                if all(sort == "ord" and a in stegar[j] and b in stegar[j]
                       for sort, j in delat):
                    continue
                return False

        # 6.1 punkt 7, den del som går att avgöra utan varianterna: har ett
        # ANNAT kort exakt samma positioner som ett mål, finns ingen avvikelse
        # som skiljer dem åt, och skulden går inte att lägga rätt. Hela
        # villkoret kräver de omrenderingar entydighetsfiltret (6.5) ger och
        # kan inte prövas förrän det finns.
        alla: dict = {}
        for kort, ps in meningens_kort(self.s.tabell, ut):
            alla.setdefault(kort, set()).update(ps)
        for a in platser:
            for b, ps in alla.items():
                if b == a or ps != platser[a]:
                    continue
                if any(a in stege and b in stege for stege in stegar):
                    continue
                return False
        return True

    def ryms(self, mål: set, övriga: set) -> bool:
        """Håller budgeten: P(≥2 fel) ≤ τ (6.3)?"""
        return _minst_ett_fel([self.p(k) for k in mål | övriga]) <= self.τ

    def _välj(self, kort: Kort, tillåten, mål_av,
              släpp_budget: bool = True) -> Uppgift | None:
        """Den kortaste mening som prövar kortet och ryms i budgeten.

        Ryms ingen tas den minst riskabla av dem — reservsteg 2 i 6.3. Det
        behövs tidigt i kursen, när alla kort är nya och ingen mening kan vara
        säker; budgeten släpps bara här, och bara för att det annars inte blir
        någon övning alls. Bland de kortaste meningarna väljs den säkraste: en
        längre mening bär fler kort och är därför inte säkrare.

        SÖKNINGEN SLUTAR NÄR RISKEN SLUTAR SJUNKA. Reservsteg 2 vill ha den
        minst riskabla meningen, och att veta vilken det är kräver att alla
        räknas upp. Tidigt i kursen är det förödande och meningslöst på en
        gång: varje kort är nytt, alla har samma p, alltså har varje mening
        av samma längd SAMMA risk, och uppräkningen kan aldrig hitta något
        bättre. Kortet `regel:ordning/frågeord_först` gav sin första mening
        på 6 s och fortsatte sedan genom 104 likvärdiga fyraordsmeningar på
        två minuter utan att passet kom vidare.

        Därför: en kandidat som inte förbättrar den bästa risken avslutar
        sökningen. Ingen gräns är satt i förväg — det är datan som säger när
        det är klart. Den dag reservsteg 1 (ensamövningen, 6.3) finns
        behöver reservsteg 2 sällan tas alls.

        EN MENING PER MALL RÄCKER INTE, och det var nästan osynligt. `per_mall`
        fanns för farten: hundra likvärdiga meningar ur samma mall är slöseri.
        Men villkor 8 i 6.1 gallrar på KÄLLTEXT, och med en enda representant
        per mall blev sökningen blind så fort den representanten var ställd —
        «Kärlek står.» var ställd, och då fanns «Kärlek sitter.» inte, fast
        den stod oställd i dagens plan. Tidigt i kursen finns bara en mall,
        så `_välj` slutade hitta meningar efter den första.

        Taket är därför antalet ställda meningar plus en: fler än så kan inte
        vara uteslutna, så minst en av dem är ny.

        GRUPPERINGEN HAR SAMMA FEL, och den är värre. `grupperat` prövar ETT
        ord per kortsignatur, och `stå`, `sitta`, `passa` och `falla` är alla
        regelbundna verb med samma signatur: generatorn prövade aldrig något
        annat än `stå`. Var «Kärlek står.» ställd fanns ingen mening alls för
        `kärlek` — sökningen tog fem sekunder på att svara att dagens material
        var slut, med fyra oställda meningar kvar i planen. Grupperingen är
        rätt så länge man bara behöver EN mening per korttäckning, och fel så
        fort just den är förbrukad.

        Därför två svep: det grupperade först, för farten, och det ogrupperade
        BARA NÄR DET FÖRSTA UTESLÖT NÅGOT. Samma signatur ger samma kort, och
        samma kort ger samma risk och samma åtskillnad — det ogrupperade
        svepet kan alltså inte hitta en bättre mening, bara en annan
        KÄLLTEXT. Uteslöt det grupperade svepet ingenting på källtexten (eller
        på ett renderingsfel) finns det ingenting att gå tillbaka efter, och
        då körs det dyra svepet inte alls.
        """
        bäst, uteslutna = self._svep(kort, tillåten, mål_av, grupperat=True)
        if uteslutna and (bäst is None or bäst[0] > self.τ):
            andra, _ = self._svep(kort, tillåten, mål_av, grupperat=False)
            if andra is not None and (bäst is None or andra[0] < bäst[0]):
                bäst = andra
        if bäst is None:
            return None
        # Reservsteg 2 tas bara när den som frågar tillåter det. Ordningen i
        # 6.3 är ensamövningen FÖRST, och den ordningen går förlorad om
        # budgeten släpps redan här.
        return bäst[1] if bäst[0] <= self.τ or släpp_budget else None

    def _svep(self, kort: Kort, tillåten, mål_av,
              grupperat: bool) -> tuple[tuple[float, Uppgift] | None, int]:
        """Ett svep i `_välj`: (bästa kandidaten med sin risk, antal uteslutna).

        «Uteslutna» är de kandidater som föll på KÄLLTEXTEN — villkor 8 i 6.1
        — eller på ett renderingsfel. Bara de kan ett ogrupperat svep rädda.
        """
        ställda = self.data.dagens_källtexter()
        bäst: tuple[float, Uppgift] | None = None
        uteslutna = 0
        längd: int | None = None
        for träff in self.s.meningar(kort, tillåten, högst_ord=LÄNGSTA,
                                     per_mall=len(ställda) + 1,
                                     grupperat=grupperat):
            if längd is None:
                längd = träff.ord
            elif träff.ord > längd:
                break
            risk = _minst_ett_fel([self.p(k) for k in träff.kort])
            if bäst is not None and risk >= bäst[0]:
                # Ingen förbättring: ur reservsteg 2:s synvinkel är resten av
                # längdgruppen lika bra som den bästa vi redan har.
                break
            mål = mål_av(träff)
            try:
                ut = spåra(self.s.renderare, träff.mening)
                källtext = self.s.par.rendera(träff.mening)
            except RenderingsFel:
                uteslutna += 1
                continue
            if källtext in ställda:
                # 6.1 punkt 8: källmeningen har redan ställts i dag. Den mäter
                # då minnet av facit i stället för kortet. Risken räknas ändå,
                # så en utesluten kandidat inte får avsluta sökningen.
                uteslutna += 1
                continue
            if not self._åtskilda(ut, mål):
                continue
            uppgift = Uppgift(träff, ut, källtext, frozenset(mål),
                              frozenset(träff.kort - mål))
            if risk <= self.τ:
                return (risk, uppgift), uteslutna
            bäst = (risk, uppgift)
        return bäst, uteslutna

    def _ur_planen(self, plan: Dagsplan, kort: Kort,
                   mål_av) -> tuple[Uppgift | None, Uppgift | None]:
        """Dagens reserverade meningar för kortet: (ryms i budgeten, minst risk).

        MÅLEN RÄKNAS OM HÄR och kommer inte ur planen. Vad som är svagt beror
        på hur dagen har gått (6.2), och planen lades innan den började — där
        är varje mening bara märkt med det kort den reserverades för.

        OCH TILLÅTLIGHETEN PRÖVAS OM. Planen bygger sina meningar av det den
        TÄNKER presentera, men introfasen kan pausa — ett kort som inte gick
        rätt blir inte presenterat (5.1). Meningarna är färdigbyggda och gick
        förbi villkor 1 i 6.1 helt: en körning införde 13 kort men hade bara
        presenterat 12, alltså ett kort som användaren aldrig fick se.
        """
        bäst: Uppgift | None = None
        risk = 1.0
        ställda = self.data.dagens_källtexter()
        for u in plan.meningsfasen:
            if u.källtext in ställda or kort not in u.träff.kort:
                continue
            if not self.tillåten_mening(u, kort):
                continue
            mål = mål_av(u.träff)
            if not self._åtskilda(u.ut, mål):
                continue
            övriga = u.träff.kort - mål
            klar = Uppgift(u.träff, u.ut, u.källtext, frozenset(mål),
                           frozenset(övriga))
            if self.ryms(mål, övriga):
                return klar, None
            r = _minst_ett_fel([self.p(k) for k in u.träff.kort])
            if r < risk:
                bäst, risk = klar, r
        return None, bäst

    def tillåten_mening(self, uppgift: Uppgift, mål: Kort) -> bool:
        """Villkor 1 i 6.1: varje kort meningen kräver är infört eller
        presenterat i dag (R1, 5.2)."""
        return uppgift.träff.kort <= (self.tillåtna() | {mål})

    def uppgift(self, kort: Kort, plan: Dagsplan | None = None) -> Uppgift | None:
        """En mening som prövar kortet, byggd av tillåtna kort (R1).

        Kortet självt är alltid ett mål, och övriga svaga kort i meningen blir
        också mål (6.2).

        PLANENS MENINGAR GÅR FÖRE SÖKNINGEN. Planen bevisade före passet att
        varje kort i dagens mängd går att införa (5.1), och beviset är värt
        något bara om meningsfasen faktiskt tar de meningarna: söker den fritt
        tar den lika gärna en mening huvuddelen behövde till ett annat kort,
        och villkor 8 i 6.1 gör den förbrukad. Det var så fyra presenterade
        ord blev oprövbara mitt i dagen.
        """
        tillåtna, svaga = self.tillåtna() | {kort}, self.svaga()

        def mål_av(träff):
            return (träff.kort & svaga) | {kort}

        # 6.3, i ordning: en mening som ryms i budgeten, annars ensamövningen,
        # annars den minst riskabla meningen.
        #
        # HELA STEGEN TAS FÖRST INOM PLANEN. Planen räknade redan upp dagens
        # meningar; att gå till generatorn för samma meningar kostar 18 s per
        # val, och efter ETT felsvar faller fem kort på en gång och ska alla
        # ha var sin ny mening. Passet kröp då i minuter mellan övningarna.
        # Sökningen finns kvar för det planen inte hann samla in.
        minst_risk = None
        if plan is not None:
            i_budget, minst_risk = self._ur_planen(plan, kort, mål_av)
            if i_budget is not None:
                return i_budget
        else:
            uppgift = self._välj(kort, lambda k: k in tillåtna, mål_av,
                                 släpp_budget=False)
            if uppgift is not None:
                return uppgift

        ensam = self.ensamövning(kort, plan)
        if ensam is not None:
            return ensam
        if minst_risk is not None:
            return minst_risk
        # Planen samlade in med ett tak och är inte garanterat uttömmande, så
        # sökningen får sista ordet. Den kostar och ger oftast ingenting —
        # men den körs en gång per kort och dag, sist på dagen, och svaret
        # «det finns inget» ska vara sant och inte bara troligt.
        return self._välj(kort, lambda k: k in tillåtna, mål_av)

    def glosorna(self, *uppgifter: Uppgift) -> list[Glosa]:
        """Glosorna för de ord uppgifterna använder och användaren inte mött.

        «Ordningen inom dagen följer kraven. Ett kort presenteras efter de
        kort det kräver, så att lånekorten redan är införda eller
        presenterade» (5.4).

        DET VANLIGASTE ORDET FÖRST (5.6). Glosorna kräver ingenting och är
        därför fria att ordna; friheten var förut upplöst av `sorted(key=str)`,
        alltså bokstavsordning efter svensk konceptnyckel. Det är samma slump
        som en gång lade `he` på nivå 79.
        """
        kända = self.data.införda() | self.data.presenterade()
        nya: set[Kort] = set()
        for u in uppgifter:
            nya |= {k for k in u.träff.kort - kända if k.familj == "ord"}
        return [g for k in sorted(nya, key=lambda k: self.s._ordvikt(k.nyckel[0]))
                if (g := self.glosa(k)) is not None]

    def ställ(self, uppgift: Uppgift, fas: str = "mening") -> Uppgift:
        """Skriv ner uppgiften som ställdes, och ge den med sitt id."""
        mening_id = self.data.ny_mening(fas, repr(uppgift.träff.mening),
                                        uppgift.källtext, [uppgift.facit])
        return Uppgift(uppgift.träff, uppgift.ut, uppgift.källtext, uppgift.mål,
                       uppgift.övriga, mening_id)

    def rätta(self, uppgift: Uppgift, svar: str, sekunder: float) -> Rättning:
        """Diffens betyg per kort. Bokför ingenting — det gör `bokför` (7.2)."""
        if uppgift.mening_id is not None:
            self.data.svara(uppgift.mening_id, svar, sekunder)
        return rätta(self.s.tabell, uppgift.ut, svar)

    def bokför(self, uppgift: Uppgift, rättning: Rättning,
               godkända: frozenset = frozenset(), höjt: dict | None = None,
               flagga: str | None = None, paket: frozenset = frozenset()) -> None:
        """Betygen går till FSRS när användaren går vidare, inte när diffen
        räknats fram (7.2). Korten som gick rätt införs (5.1).

        `godkända` är de kort användaren markerat om från underkänt till
        godkänt: ett stavfel, eller ett korrekt svar som facit inte hade.
        `höjt` ger `hard` eller `easy` på ett godkänt kort — de räknas aldrig
        fram, varken ur diffen eller ur svarstiden. `flagga` är anmärkningen på
        facit, som går till granskningen av datan (3.4).

        Loggen sparar båda betygen: diffens, som är mätt, och användarens, som
        FSRS får. Renderaren fångar inte varje nyans av ett språk, och
        omrättningen är det som gör att den inte behöver det.
        """
        höjt = höjt or {}
        if flagga is not None:
            self.data.rapportera_fel(flagga, mening_id=uppgift.mening_id)
        betygen = {}
        for kort, mätt in rättning.betyg.items():
            betyg = RÄTT if kort in godkända else mätt
            if betyg == RÄTT:
                betyg = höjt.get(kort, RÄTT)
            betygen[kort] = (mätt, betyg)
            self.data.bokför(kort, mål=kort in uppgift.mål, betyg_diff=mätt,
                             betyg=betyg, mening_id=uppgift.mening_id)
        # ETT PAKET BLIR INFÖRT HELT ELLER INTE ALLS (5.1). Annars kunde ett
        # verb stå som infört utan det pronomen det kräver, och nästa mening
        # bygga på ett kort användaren aldrig klarat.
        föll = {k for k, (_, betyg) in betygen.items() if betyg == FEL}
        helt = not (paket & föll) if paket else True
        for kort, (_, betyg) in betygen.items():
            if betyg == FEL:
                continue
            if kort in paket and not helt:
                continue
            self.data.inför(kort, uppgift.mening_id)
        self.uppdatera()

    # ── introfasen ──

    def nästa_nivå(self) -> frozenset:
        """Den första nivå vars grind är uppfylld (4.4).

        > En nivå kan öppnas när föregångarnas kort infördes en TIDIGARE dag.

        DAGSVILLKORET ÄR GRINDEN, och det saknades. Utan det öppnade nivå 2 en
        minut efter att nivå 1:s kort införts, och en användare kunde ta fyra
        nivåer på fem minuter. Med det gäller 4.4:s följd av sig själv: «längs en
        kedja öppnas högst en nivå per dygn». Ingen ny regel behövdes — den låg
        i att införandet måste ha skett en tidigare dag.

        Korten i en nivå kräver varandra (4.1), så ett enskilt kort går inte att
        införa först. Nivån öppnas i sin helhet, och dess kort införs sedan i
        paket (3.10).

        ARBETSBÖRDAN PRÖVAS INTE HÄR. 4.4: «Att öppna en nivå lägger inga kort i
        passet, bara kandidater… En grind som prövade arbetsbördan vid
        upplåsningen skulle aldrig spärra.» Taket sätter tidsmodellen när dagens
        kort väljs (5.5), inte grinden.
        """
        införda = self.data.införda()
        i_dag = self.data.dag()
        tidigare = {k for k, dag in self.data.införda_dagar().items() if dag < i_dag}
        for nivå in self.nivåer:
            if nivå <= införda:
                continue
            krav = frozenset().union(*(self.krav.get(k, frozenset()) for k in nivå))
            if krav - nivå <= tidigare:
                return nivå
        return frozenset()

    def kandidater(self) -> list[Kort]:
        """Korten i nästa nivå som inte är införda (4.5), mönsterkorten först.

        DET HÄR ÄR INTE 5.6. Där är kandidaterna «upplåsta, inte införda och
        prövbara», vilket med nivåerna som grindar (4.5) betyder VARJE ordkort
        från dag ett — orden är upplåsta (3.1). Ordningen som ska sålla dem är
        täckningen, och den är inte räknad.

        Öppnas mängden innan täckningen finns väljer kursen på frekvens
        ensamt, och kan lära ut femtio substantiv innan den rör grammatiken.
        Därför den avsmalnade mängden, med mönsterkorten före orden: ett
        mönsterkort behövs av varje mening och har hög ny täckning, vilket är
        ett grovt närmevärde för det 5.6 vill mäta.

        Orden kommer ändå med, som lånekort till mönstren, och lärs ut som
        glosor innan kortet som kräver dem (5.4). Priset är att ett mycket
        vanligt ord kan komma senare än ett sällsynt mönster.

        När täckningen finns ersätter den både mängden och ordningen
        (KÄRNAN 5.6, noteringen om version 1).
        """
        return sorted(self.nästa_nivå() - self.data.införda(),
                      key=lambda k: ((0, *self.s._ordvikt(k.nyckel[0])) if k.familj == "ord"
                                     else (-1, 0.0, 0, str(k))))

    def tempo(self, minuter: float):
        """5.5: hur många nya kort dagen tål, och budgeten med sparat inräknat.

        Ger `(tid.Tempo, budget)`, eller None när något mått saknas. «Utan talet
        finns ingen väg från minuter till kort», och då svarar modellen inte alls
        i stället för att gissa.

        DET HÄR ÄR INGEN GRIND VID UPPLÅSNINGEN. 4.4 förbjuder en sådan: «att
        öppna en nivå lägger inga kort i passet, bara kandidater… en grind som
        prövade arbetsbördan vid upplåsningen skulle aldrig spärra.» Talet är ett
        TAK FÖR DAGENS KORTMÄNGD, alltså för införandet, och det hör till 5.6:s
        fråga «vad borde läras nu» — inte till 4.4:s «vad går att lära nu» (4.5).

        Jag byggde först den förbjudna grinden, och den prövade dessutom mot
        `paket()` — sju kort för nivå 1 — medan dagen lärde ut tretton. Budgeten
        debiterade sju och levererade tretton, och eftersom den lästes ur GÅRDAGENS
        rad förbrukades den aldrig inom dagen: fyra nivåer gick igenom på fem
        minuter.

        SPARAT. «Ett paket tas med helt, så en dag kan ge färre kort än n. Det
        som inte används sparas till nästa dag» (5.5).
        """
        if self.tidsmodell is None or self.kort_i_kursen is None:
            return None
        kvar = max(0, self.kort_i_kursen - len(self.data.införda()))
        if not kvar:
            return None
        t = self.tidsmodell.tempo(minuter, self.data.införda_åldrar(), kvar)
        i_går = self.data.tempo(self.data.dag(_i_går()))
        sparat = i_går[1] if i_går else 0.0
        return t, t.nya + sparat

    def paket(self) -> frozenset[Kort]:
        """Nivåns kort OCH de ord de behöver — dagens kortmängd (3.10).

        «Paketet är de oinförda korten i en minsta mening för kortet», räknat
        över alla kort, ord inräknade. En minsta mening för nivå 1 är «Time
        stands.», och dess oinförda kort är nivåns fem plus `tid` och `stå`:
        sju kort, inte fem. Räknaren sa förut fem och lärde sedan ut tolv.

        En sökning räcker, eftersom nivåns kort kräver varandra (4.1) och
        därför står i samma mening.
        """
        nivå = self.nästa_nivå()
        if not nivå:
            return frozenset()
        if nivå not in self._paket:
            införda = self.data.införda()
            uppgift = None
            for kort in self.kandidater():
                uppgift = self._ensamt_mål(kort, nivå)
                if uppgift is not None:
                    break
            self._paket[nivå] = (frozenset(uppgift.träff.kort) - införda
                                 if uppgift is not None else nivå)
        return self._paket[nivå]

    def lånevikt(self, per_text: dict):
        """5.4:s lånekortsregel som en sorteringsnyckel: minst först är bäst.

        > Lånekorten — övningens övriga kort — väljs utan gränsvärde.
        > Generatorn bygger övningen med det nya kortet som enda mål och väljer
        > lånekort så att sannolikheten att alla blir rätt är så hög som
        > möjligt. Ett mönsterkort presenteras alltså med ett ord användaren kan
        > väl, så att bara mönstret är nytt.

        TVÅ TAL, och det första är viktigast. Ett lånekort som bara är
        PRESENTERAT i dag har inget FSRS-tillstånd, och `p` ger då
        retentionsmålet som platshållare (5.1) — alltså samma tal som ett kort
        användaren drillat i en vecka, och ofta ett HÖGRE, eftersom det drillade
        kortets R har hunnit sjunka sedan sist. Sorteras det bara på `p` vinner
        därför de ord som glosades för tre minuter sedan, och övningen prövar
        två nya saker i stället för en. Antalet OINFÖRDA lånekort är det som
        skiljer, och det är ett mått vi har: infört betyder att kortet gått rätt
        i en mening (5.1).

        Sedan `p`, för de införda. Det är FSRS:s retrievability, alltså precis
        «repeterat länge, ofta rätt, nyligen genomgått» — måttet behöver inte
        hittas på, bara användas.

        DAG ETT är ingenting infört, så båda talen är lika för varje mening och
        spridningen avgör. Det är riktigt: då finns inget bättre än det som just
        gicks igenom.
        """
        införda = self.data.införda()

        def vikt(text: str, kort: Kort | None) -> tuple:
            lån = per_text[text].träff.kort - ({kort} if kort else set())
            oinförda = sum(1 for k in lån if k not in införda)
            säkert = 1.0
            for k in lån:
                säkert *= self.p(k)
            return (oinförda, -säkert)

        return vikt

    def märk(self, uppgift: Uppgift, kort: Kort) -> Uppgift:
        """Uppgiften märkt med det kort den TILLDELATS som enda mål (5.4).

        Dagsplanen bygger varje uppgift när källmeningen först dyker upp, och
        sätter då `mål` till det kort som råkade samla in den. Matchningen ger
        sedan meningen till ett ANNAT kort, och märkningen följde inte med:
        introövningen för `ord:artikel_obestamd` var märkt
        `regel:ordning/bestämning_före_huvudord`. Bedömningen i 5.4 — «en
        övning görs om tills det nya kortet blir rätt» — läste alltså ett annat
        korts betyg, och kunde godkänna en övning vars eget kort hade fallit.
        """
        return Uppgift(uppgift.träff, uppgift.ut, uppgift.källtext,
                       frozenset({kort}), frozenset(uppgift.träff.kort - {kort}))

    def _övas_med_mening(self, kort: Kort) -> bool:
        """Övas kortet med en MENING i stället för en glosa (5.4)?

        Tabellen i 5.4 delar korten efter övningsform, inte efter familj: ett
        innehållsord får en glosa, som inte kräver någon mening, medan regler,
        ändelser, oregelbundna former OCH FUNKTIONSORD får en mening — «en
        glosa vore sällan entydig: engelskans *a* är både `en` och `ett`».

        Räkningen som styr hur mycket material dagen behöver använde
        `familj != "ord"`, och ett funktionsord har familjen «ord». Nivån
        `ord:demonstrativ_fjärran` fick därför noll mönsterkort, taket ett, en
        enda kandidatmening — som gick till lektionen — och sedan karantän för
        att ingen övning fanns. Kursen stannade där.
        """
        return not (kort.typ == "ord" and self._fritt_ord(kort))

    def _ordklass(self, kort: Kort) -> str:
        rad = self.s.u.conn.execute(
            "SELECT ordklass FROM Koncept WHERE nyckel = ?",
            (kort.nyckel[0],)).fetchone()
        return rad["ordklass"] if rad else ""

    def _användbara(self, korten: list[Kort], tillåtna: set,
                    klasser: dict, m: int) -> dict[str, list[Kort]]:
        """De ord som FAKTISKT går att bygga en mening av, m per ordklass.

        Att nominera orden på frekvens ensamt räcker inte: nivå 1 har
        `val/bestämning/naken`, alltså inget bestämningsled, och då duger bara
        oräknebara substantiv. De vanligaste substantiven är räknebara, och
        ordförrådet gav en enda mening — «Tid står.» — och fyra kort i
        karantän. Vilka ord som duger avgörs av byggvillkoren, inte av en
        tabell, så frågan ställs till generatorn.

        Sökningen slutar när varje öppen ordklass har m ord, eller när
        generatorn tar slut. Meningen behöver inte renderas: bara vilka ord
        den bär är intressant, och renderingen är det dyra.
        """
        funna: dict[str, dict[Kort, None]] = {ok: {} for ok in klasser}

        def klart() -> bool:
            return all(len(v) >= m for v in funna.values())

        def tillåten(k: Kort) -> bool:
            return k in tillåtna or self._fritt_ord(k)

        for kort in korten:
            if klart():
                break
            for träff in self.s.meningar(kort, tillåten, högst_ord=LÄNGSTA,
                                         per_mall=None, grupperat=False):
                for k in träff.kort:
                    if k.familj == "ord" and (ok := self._ordklass(k)) in funna:
                        funna[ok][k] = None
                if klart():
                    break
        return {ok: sorted(v, key=lambda k: self.s._ordvikt(k.nyckel[0]))
                for ok, v in funna.items()}

    def _ordförråd(self, korten: list[Kort], tillåtna: set) -> frozenset[Kort]:
        """Dagens ORD — planens dyraste val, och därför ett eget (5.6).

        Varje ord en mening använder och användaren inte kan är ett KORT som
        dagen måste betala för: det lärs ut som en glosa före kortet som
        kräver det (5.4), och «ett ords egna kort är en kostnad, inte en
        vinst» (5.6). Planen behöver många OLIKA källmeningar — villkor 8 i
        6.1 låter varje mening ställas en gång per dag — men den ska köpa
        dem så billigt som möjligt.

        UTAN DET HÄR VALET tog planen de meningar generatorn råkade räkna upp
        först, och de kommer substantiv för substantiv: «Tid står», «Väder
        står», «Vatten står» … Femton meningar blev femton substantiv och ETT
        verb, alltså tjugoen kort på dag ett — och «Makt står», «Hälsa står»,
        «Kött står». Ett ÅTERKOMBINERANDE ordförråd ger lika många meningar
        för en bråkdel: fyra substantiv och fyra verb ger sexton.

        HUR MÅNGA ORD PER ORDKLASS är inte valt utan följer av vad planen ska
        räcka till. Med c ordklasser i meningen och m ord i varje finns m^c
        källmeningar. Planen behöver en lektion och en övning per mönsterkort
        (2P), och huvuddelen minst en mening per ord, eftersom varje mening
        bär ett ord ur varje klass och ett ord införs genom att stå rätt i en
        mening (5.1). Alltså det minsta m där

            m^c − m ≥ 2P

        Nivå 1 har fem mönsterkort och två ordklasser — substantiv och verb —
        och får m = 4: sexton möjliga meningar mot fjorton som behövs.

        VILKA ord det blir: paketets egna först, eftersom 3.10 redan valt dem
        med en minsta mening, och sedan de vanligaste av dem som FAKTISKT
        går att bygga en mening av (`_användbara`, 5.6). En SLUTEN ordklass
        fylls inte på — dess ord är nivåkort och grindade (4.5) — så den
        bidrar med paketets egna och inget mer.
        """
        klasser: dict[str, set[Kort]] = {}
        for k in self.paket():
            if k.familj == "ord":
                klasser.setdefault(self._ordklass(k), set()).add(k)
        öppna = {ok: frön for ok, frön in klasser.items()
                 if ok and ok not in SLUTNA_ORDKLASSER}
        ut: set[Kort] = {k for frön in klasser.values() for k in frön}
        if not öppna:
            return frozenset(ut)

        # DE INFÖRDA ORDEN FÖRST, och de kostar ingenting. 5.4: «lånekorten
        # väljs så att sannolikheten att alla blir rätt är så hög som möjligt
        # — ett mönsterkort presenteras med ett ord användaren kan väl, så att
        # bara mönstret är nytt». Ett infört ord är alltså både BÄTTRE material
        # och gratis, medan ett nytt är ett kort dagen måste betala för (5.6).
        #
        # Utan det här byggdes dagens ordförråd av nya ord fast tjugofem kort
        # redan var införda: nivå 2 lärde ut fem nya ord som introövningarna
        # sedan använde som lånekort, alltså tre okända saker i en övning som
        # skulle visa en.
        # MEN ETT INFÖRT ORD ÄR MATERIAL BARA OM DET GÅR ATT ANVÄNDA HÄR.
        # Först räknades de bara, och då blev materialet inbillat: nivå 2
        # kräver artikel, alltså ett RÄKNEBART substantiv, och dag ett lärde
        # bara ut oräknebara (`tid`, `vatten`, `väder`, `kärlek`) eftersom nivå
        # 1 kräver naken fras. Fyra substantiv fanns, m var fyra, och ändå
        # fanns bara fem meningar i hela nivån. Vilka ord som duger avgör
        # byggvillkoren, och det är `_användbara` som frågar dem.
        införda = self.data.införda()

        c = len(öppna)
        p = sum(1 for k in korten if self._övas_med_mening(k))
        m = max(len(frön) for frön in öppna.values())
        # Med c ordklasser och m ord i varje finns m^c källmeningar, och planen
        # behöver 2P åt lektionerna och övningarna plus m åt huvuddelen.
        #
        # FORMELN GÄLLER BARA c ≥ 2. Med en enda ordklass ger varje ord exakt
        # EN mening, så m^c − m är noll för varje m och olikheten kan aldrig
        # uppfyllas: loopen räknade upp m i evighet och passet hängde på nivån
        # `val/tempusform/preteritum`, vars paket bara har ett verb. Där finns
        # ingen kombinatorik att köpa material med — materialet måste komma
        # ur de införda orden, och det gör det nu.
        if c >= 2:
            while m ** c - m < 2 * p:
                m += 1
        användbara = self._användbara(korten, tillåtna, öppna, m)
        for ordklass, frön in öppna.items():
            valda = set(frön)
            # De INFÖRDA först, och inom varje grupp det vanligaste (5.6).
            # Sorteringen är stabil, så `_användbara`:s frekvensordning håller.
            for kort in sorted(användbara[ordklass], key=lambda k: k not in införda):
                if len(valda) >= m:
                    break
                valda.add(kort)
            ut |= valda
        return frozenset(ut)

    def dagsplan(self, rapport=None) -> Dagsplan:
        """Dagens tilldelning: vilken mening som bär vilket kort (5.1).

        Kandidatmeningar samlas per kort — en genomgång ger flera, så det
        kostar en sökning per kort och inte en per mening. Sedan matchas de,
        och det som blir över reserveras åt huvuddelen, där ett kort blir
        infört genom att gå rätt i en mening.

        ORDFÖRRÅDET VÄLJS FÖRST (`_ordförråd`), och sökningen får bara använda
        det. Annars bestämmer generatorns uppräkningsordning dagens ord, och
        den räknar upp substantiv för substantiv.

        Finns färre meningar än planen vill ha tar generatorn slut och planen
        blir så stor den kan bli — utan lektion får kortet bara sin övning,
        och det är sämre men inte trasigt.

        Kort som inte får någon mening hamnar i KARANTÄN (3.10) i stället för
        att presenteras och sedan visa sig oåtkomliga.
        """
        nivå = self.nästa_nivå()
        korten = [k for k in self.kandidater() if k not in self.data.presenterade()]
        if not korten:
            return Dagsplan({}, (), (), ())
        tillåtna = self.data.tillåtna() | nivå
        ställda = self.data.dagens_källtexter()
        ordförråd = self._ordförråd(korten, tillåtna)
        # De kort som övas med en MENING (5.4) — funktionsorden inräknade.
        mönster = sum(1 for k in korten if self._övas_med_mening(k))
        # Mer än så kan planen inte förbruka: en lektion och en övning per
        # sådant kort, och i värsta fall en egen mening åt varje kort som
        # ska införas i huvuddelen.
        tak = 2 * mönster + mönster + len(ordförråd)

        def tillåten(k: Kort) -> bool:
            return k in tillåtna or k in ordförråd

        kandidater: dict[Kort, list[str]] = {}
        per_text: dict[str, Uppgift] = {}
        for kort in korten:
            if rapport:
                rapport(f"    planerar {kort}")
            texter: list[str] = []
            # OGRUPPERAT, till skillnad från urvalet i `_välj`. `grupperat`
            # slår ihop ord med samma kortsignatur — «Jord står» och «Luft
            # står» ger samma kort — och det är rätt när man bara behöver EN
            # mening per korttäckning. Planen behöver tvärtom olika ORD:
            # lektionen, övningen och huvuddelens meningar ska vara skilda
            # källmeningar. Grupperat gav nivå 1 nio meningar, och
            # lektionerna plus övningarna åt upp alla nio — noll kvar åt
            # huvuddelen, alltså inget kort infört.
            for träff in self.s.meningar(kort, tillåten, högst_ord=LÄNGSTA,
                                         per_mall=None, grupperat=False):
                try:
                    ut = spåra(self.s.renderare, träff.mening)
                    källtext = self.s.par.rendera(träff.mening)
                except RenderingsFel:
                    continue
                if källtext in ställda or källtext in texter:
                    continue
                per_text.setdefault(källtext, Uppgift(
                    träff, ut, källtext, frozenset({kort}),
                    frozenset(träff.kort - {kort})))
                texter.append(källtext)
                if len(texter) >= tak:
                    break
            if texter:
                kandidater[kort] = texter

        # LEKTIONEN VÄLJS FÖRST, och flera kort får dela mening. Villkor 8 i
        # 6.1 gäller meningar som STÄLLS — «efter ett fel har användaren sett
        # facit, och samma fråga igen mäter minnet av facit» — och lektionen
        # ställer ingenting, den visar. Därför får samma mening gås igenom en
        # gång per kort, med olika kort markerat varje gång, och det är
        # dessutom den introduktion som bygger upp steg för steg: här är
        # meningen, det här är ordföljden, det här är ändelsen.
        #
        # Att i stället ge varje kort en EGEN lektionsmening kostade lika
        # många källmeningar som övningarna. Tio av tretton gick åt, och fyra
        # av dagens tretton kort blev presenterade utan att kunna införas.
        def åt(text: str, kort: Kort) -> Uppgift:
            return self.märk(per_text[text], kort)

        vikt = self.lånevikt(per_text)
        # Den delade lektionsmeningen: bland dem alla kort kan använda tas den
        # med de mest kända lånekorten (5.4).
        gemensamma = [t for t in per_text if all(t in v for v in kandidater.values())]
        delad = min(gemensamma, key=lambda t: vikt(t, None), default=None)
        lektioner: dict[Kort, Uppgift] = {}
        lästa: set[str] = set()
        for kort, texter in kandidater.items():
            text = (delad if delad in texter else
                    min(texter, key=lambda t: vikt(t, kort), default=None))
            if text is not None:
                lektioner[kort] = åt(text, kort)
                lästa.add(text)

        # HUVUDDELEN RESERVERAS FÖRE ÖVNINGARNA. Den är det hårda kravet:
        # introfasen bokför ingenting (5.4), så ett kort blir infört först
        # genom att gå rätt i en mening i huvuddelen, och dagen tar slut när
        # högarna är tomma (5.3). Övningarna har många meningar att välja på;
        # täckningen måste ha just de meningar som bär de kort ingen annan
        # mening bär. Matchades övningarna först åt de upp `stå` och `falla`,
        # och de två orden presenterades utan att kunna införas.
        #
        # Täckningen gäller HELA planens kortmängd, inte bara de kort som
        # råkar stå i de valda meningarna: dagens kort är bestämda innan
        # passet börjar (5.1), och det är ordförrådet plus mönsterkorten.
        # Bara det som ska INFÖRAS i dag, och bara det som någon insamlad
        # mening faktiskt bär. Ordförrådet är en NOMINERING: `_användbara`
        # säger att ordet går att bygga en mening av, men insamlingen har ett
        # tak och kan ha slutat innan just den meningen kom. Krävdes hela
        # nomineringen hamnade `ord:per_se` i karantän nivå efter nivå, utan
        # att någon mening i planen ens innehöll ordet — ett kort straffades
        # för att planen hade nämnt det.
        i_meningarna = {k for u in per_text.values() for k in u.träff.kort}
        behövs = ((set(korten) | (set(ordförråd) & i_meningarna))
                  - self.data.införda())
        kvar = [per_text[t] for t in per_text if t not in lästa]
        meningsfasen: list[Uppgift] = []
        while behövs and kvar:
            bäst = max(kvar, key=lambda u: len(behövs & u.träff.kort))
            if not (behövs & bäst.träff.kort):
                break
            meningsfasen.append(bäst)
            behövs -= bäst.träff.kort
            kvar.remove(bäst)

        # Övningen ställs, och får därför varken vara en läst mening — då vore
        # den en avskrift — eller någon annans övning, eller en mening
        # huvuddelen redan räknar med.
        reserverat = lästa | {u.källtext for u in meningsfasen}
        def orden_i(text: str) -> list[str]:
            return [k.nyckel[0] for k in per_text[text].träff.kort
                    if k.familj == "ord"]

        par = _matcha({k: [t for t in v if t not in reserverat]
                       for k, v in kandidater.items()},
                      orden=orden_i, vikt=self.lånevikt(per_text))
        intro = tuple((k, åt(par[k], k)) for k in korten if k in par)
        lektioner = {k: u for k, u in lektioner.items() if k in par}
        karantän = tuple(
            [(k, "ingen egen mening att öva på i dag")
             for k in korten if k not in par]
            + [(k, "ingen mening i huvuddelen för in kortet") for k in behövs])

        # Det som blir över följer med. Täckningen räcker för att INFÖRA varje
        # kort en gång, men varje fel ger mer arbete (5.3) och då behövs en
        # mening till. Det som blir över kostar ingenting att ha kvar, och
        # utan det står dagen still vid första felet.
        meningsfasen += [u for u in kvar if u.källtext not in set(par.values())]
        return Dagsplan(lektioner, intro, tuple(meningsfasen), karantän)

    def att_presentera(self) -> list[Kort]:
        """Nästa nivås kort som inte är införda OCH inte presenterade i dag.

        Skilt från `kandidater`, som bara drar bort de införda. Introfasen
        inför ingenting (5.4), så `kandidater` står stilla över hela
        introfasen — och gränssnittet lät då användaren köra om den i
        oändlighet, med samma fem kort tre varv i rad. Dagens nya kort
        presenteras en gång (5.1); sedan prövas de i meningar.
        """
        presenterade = self.data.presenterade()
        return [k for k in self.kandidater() if k not in presenterade]

    def glosa(self, kort: Kort) -> Glosa | None:
        """Innehållsordets introövning, eller None när den inte går att ställa.

        Är källordet tvetydigt — två koncept med samma lemma OCH samma
        ordklass, som «fisk» — skulle glosan bryta mot R2, och då ställs den
        inte (5.4). Mätt: 16 av 719 svenska lemman bärs av flera koncept, och
        bara två av dem är innehållsord.

        BARA `typ == "ord"`, inte hela FAMILJEN «ord». Familjen rymmer också
        `oregelbunden`, `egenskap` och `rektion`, och de gäller en FORM eller en
        egenskap hos ordet — inte ordet. Glosan byggdes ur lemmat, så kortet
        `oregelbunden:pos_stå/pret`, som gäller «stood», lärdes ut som
        «stå = stand». Svaret «stand» var rätt, kortet räknades som presenterat,
        och preteritumformen hade aldrig visats. 5.4 ger dem andra
        övningsformer: en ruta i paradigmtabellen, och formen där egenskapen
        eller kravet syns.
        """
        if kort.typ != "ord" or self.s.par is None:
            return None
        nyckel = kort.nyckel[0]
        källa, mål = self.s.par.u, self.s.u
        try:
            hit = källa.lexem(nyckel)
            dit = mål.lexem(nyckel)
        except RenderingsFel:
            return None
        ordklass = källa.ordklass(hit).split("/")[0]
        if ordklass in SLUTNA_ORDKLASSER:
            return None
        lemma = källa.lemma(hit)
        syskon = källa.conn.execute(
            """SELECT count(*) FROM Koncept k JOIN Lexem l ON l.koncept_id = k.id
               WHERE l.språk = ? AND l.lemma = ? AND k.ordklass = ?""",
            (källa.språk, lemma, ordklass)).fetchone()[0]
        if syskon > 1:
            return None
        former = {f for f in mål._celler(dit).values() if f}
        if not former:
            return None
        return Glosa(kort, f"{lemma}  ({ordklass.lower()})",
                     mål.lemma(dit), frozenset(former))

    def rätta_glosa(self, glosa: Glosa, svar: str) -> bool:
        """Klarat om svaret är en form reglerna kan bygga av rätt lexem (3.3)."""
        return svar.strip().lower() in {f.lower() for f in glosa.former}

    def _ensamt_mål(self, kort: Kort, paket: frozenset,
                    fritt: bool = True) -> Uppgift | None:
        """En övning med kortet som ENDA mål, byggd utan gränsvärde (5.4).

        Lånekorten hålls inte mot budgeten: bara det nya kortet är mål, och
        övningen finns för att just det ska prövas. Samma bygge används av
        introfasen och av ensamövningen — «samma bygge tre gånger» (6.4).

        `fritt` styr om oinförda ord får fylla ut. Introfasen får det: den lär
        ut dem som glosor först (5.4). MENINGSFASEN FÅR INTE — där är
        glosorna över, och ett nytt ord blir ett kort dagen aldrig planerade
        för. Det syntes som «Kärlek ligger.» mitt i huvuddelen, med `ligga`
        aldrig utlärt.
        """
        tillåtna = self.data.tillåtna() | paket | {kort}

        # 5.4: «lånekorten väljs så att sannolikheten att alla blir rätt är så
        # hög som möjligt — ett mönsterkort presenteras med ett ord användaren
        # kan väl, så att bara mönstret är nytt».
        #
        # Första försöket bygger därför av KÄNDA kort: infört eller
        # presenterat i dag, vilket också är det 6.1 punkt 1 kräver. Upplåst
        # är inte samma sak som tillåtet — orden är upplåsta från början
        # (3.1), men ett ord användaren aldrig sett gör övningen till ett prov
        # på tre okända saker samtidigt.
        uppgift = self._välj(kort, lambda k: k in tillåtna, lambda t: {kort})
        if uppgift is not None:
            return uppgift

        # Går det inte — och dag ett gör det aldrig, då inget är känt — får
        # nya ord komma med. De lärs ut som glosor innan övningen (`glosorna`).
        #
        # BARA ÖPPNA ORDKLASSER. `familj == "ord"` rymmer också artiklar,
        # pronomen och kvantifikatorer, och de är NIVÅKORT — grindade av
        # sin nivå (4.5). Utan den här gränsen lärdes «man» ut i första
        # lektionen fast det hör till nivå 81, och «någon» fast det hör till
        # nivå 28. 3.10 säger vad som får fylla ut: «alla kort i de öppna
        # nivåerna och hela ordförrådet».
        if not fritt:
            return None
        return self._välj(kort, lambda k: k in tillåtna or self._fritt_ord(k),
                          lambda t: {kort})

    def _fritt_ord(self, kort: Kort) -> bool:
        """Ett ord ur en öppen ordklass, alltså upplåst från början (3.1)."""
        if kort.familj != "ord":
            return False
        if kort.nyckel[0] not in self._öppen:
            rad = self.s.u.conn.execute(
                "SELECT ordklass FROM Koncept WHERE nyckel = ?",
                (kort.nyckel[0],)).fetchone()
            self._öppen[kort.nyckel[0]] = bool(
                rad and rad["ordklass"] not in SLUTNA_ORDKLASSER)
        return self._öppen[kort.nyckel[0]]

    def ensamövning(self, kort: Kort,
                    plan: Dagsplan | None = None) -> Uppgift | None:
        """Reservsteg 1 i 6.3: kortet prövas ensamt när ingen mening når det.

        Samma form som introövningen (5.4), men utan att kortet visas först —
        övningen är provet, ingen förberedelse — och svaret bokförs som en
        vanlig repetition.

        Den behövs redan dag ett, och det är villkor 5 som gör den nödvändig:
        när de få korten presenterades samma dag är varje kort svagt, och i
        «Time stands.» styr alla fem samma två ord. Ingen mening med flera mål
        är då giltig, och utan ensamövningen fanns ingen uppgift alls — dagen
        gick inte att komma igenom. Budgeten kan aldrig göra ett kort onåbart.

        Byggs bara av KÄNDA kort. Reservsteget finns för att budgeten inte
        ska göra ett kort onåbart, inte för att lära ut nya ord — det gör
        introfasen, med glosor först (5.4).

        TAS UR DAGENS PLAN när det finns en, och ur en sökning först när
        planen är slut. Steget hade annars två vägar, och då går det inte att
        stänga av: falsifieringen som ska visa att dagen inte går att komma
        igenom UTAN reservsteg 1 höll ändå, eftersom planen tyst gav samma
        sak. Ett begrepp ur 6.3 ska ha ett ställe.
        """
        if plan is not None:
            i_budget, minst_risk = self._ur_planen(plan, kort, lambda t: {kort})
            if i_budget is not None or minst_risk is not None:
                return i_budget or minst_risk
        return self._ensamt_mål(kort, frozenset(), fritt=False)

    def presentera(self, kort: Kort, paket: frozenset = frozenset(),
                   markera: bool = True) -> Uppgift | None:
        """Introövningen: en mening med kortet som ENDA mål (5.4).

        Bokför ingenting. Kortet räknas som presenterat, och får därför användas
        i dagens meningar (5.1).

        `paket` är de andra oinförda korten i samma nivå. De får vara lånekort
        trots att de inte är införda, eftersom korten i en nivå kräver varandra
        (4.1) — annars gick det första kortet i nivån inte att presentera alls.
        Lånekorten väljs utan gränsvärde (5.4): bara det nya kortet är mål, och
        budgeten gäller därför inte här.
        """
        uppgift = self._ensamt_mål(kort, paket)
        if uppgift is None:
            return None
        if markera:
            self.klarat_introövningen(kort)
        return uppgift

    def klarat_introövningen(self, kort: Kort) -> None:
        """Kortet är presenterat — det har KLARAT introövningen (5.1).

        Förut räknades kortet som presenterat så snart övningen byggdes, alltså
        innan användaren svarat. Då fick ett kort användas i dagens meningar
        utan att ha klarats, och «en övning görs om tills det nya kortet blir
        rätt» (5.4) saknade verkan.
        """
        self.data.presentera(kort)
        self.uppdatera()

    # ── dagens läge, för gränssnittet ──

    def läge(self) -> dict:
        nu = datetime.now().astimezone()
        return {"dag": self.data.dag(), "tid": nu.strftime("%H:%M"),
                "införda": len(self.data.införda()),
                "presenterade": len(self.data.presenterade()),
                "svaga": len(self.svaga()),
                "att_presentera": len(self.att_presentera()),
                "i_paketet": len(self.paket() - self.data.presenterade()
                                 - self.data.införda()),
                "kandidater": len(self.kandidater())}
