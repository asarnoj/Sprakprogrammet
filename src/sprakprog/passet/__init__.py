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
- Reservsteg 1 i 6.3, ensamövningen, saknas. Reservsteg 2 — den minst riskabla
  meningen — finns, och behövs redan dag ett, då varje kort är nytt.
- Entydighetsfiltret (6.5) ger flera godtagna varianter; här är facit den mening
  som ställdes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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


class Passet:
    """Dagens pass för en kurs."""

    def __init__(self, data: Kursdata, sammansättare: Sammansättare, lager: Lager,
                 krav: dict[Kort, frozenset], nivåer: list[frozenset]) -> None:
        self.data, self.s, self.lager = data, sammansättare, lager
        self.krav, self.nivåer = krav, nivåer
        self.τ = 1 - lager.retention
        self._tillstånd: dict = {}
        self._i_dag: dict = {}
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
        """
        ställda = self.data.dagens_källtexter()
        bäst: tuple[float, Uppgift] | None = None
        längd: int | None = None
        for träff in self.s.meningar(kort, tillåten, högst_ord=LÄNGSTA, per_mall=1,
                                     grupperat=True):
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
                continue
            if källtext in ställda:
                # 6.1 punkt 8: källmeningen har redan ställts i dag. Den mäter
                # då minnet av facit i stället för kortet. Risken räknas ändå,
                # så en utesluten kandidat inte får avsluta sökningen.
                continue
            if not self._åtskilda(ut, mål):
                continue
            uppgift = Uppgift(träff, ut, källtext, frozenset(mål),
                              frozenset(träff.kort - mål))
            if risk <= self.τ:
                return uppgift
            bäst = (risk, uppgift)
        # Reservsteg 2 tas bara när den som frågar tillåter det. Ordningen i
        # 6.3 är ensamövningen FÖRST, och den ordningen går förlorad om
        # budgeten släpps redan här.
        return bäst[1] if bäst and släpp_budget else None

    def uppgift(self, kort: Kort) -> Uppgift | None:
        """En mening som prövar kortet, byggd av tillåtna kort (R1).

        Kortet självt är alltid ett mål, och övriga svaga kort i meningen blir
        också mål (6.2).
        """
        tillåtna, svaga = self.tillåtna() | {kort}, self.svaga()

        def mål_av(träff):
            return (träff.kort & svaga) | {kort}

        # 6.3, i ordning: en mening som ryms i budgeten, annars ensamövningen,
        # annars den minst riskabla meningen.
        uppgift = self._välj(kort, lambda k: k in tillåtna, mål_av,
                             släpp_budget=False)
        if uppgift is not None:
            return uppgift
        ensam = self.ensamövning(kort)
        if ensam is not None:
            return ensam
        return self._välj(kort, lambda k: k in tillåtna, mål_av)

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
        """Den första nivå som inte är införd och vars krav är införda (4.4).

        Korten i en nivå kräver varandra (4.1), så ett enskilt kort går inte att
        införa först. Nivån öppnas i sin helhet, och dess kort införs sedan i
        paket (3.10) — ett eller flera, allt efter vad budgeten rymmer.
        """
        införda = self.data.införda()
        for nivå in self.nivåer:
            if nivå <= införda:
                continue
            krav = frozenset().union(*(self.krav.get(k, frozenset()) for k in nivå))
            if krav - nivå <= införda:
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
        """
        if kort.familj != "ord" or self.s.par is None:
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

    def _ensamt_mål(self, kort: Kort, paket: frozenset) -> Uppgift | None:
        """En övning med kortet som ENDA mål, byggd utan gränsvärde (5.4).

        Lånekorten hålls inte mot budgeten: bara det nya kortet är mål, och
        övningen finns för att just det ska prövas. Samma bygge används av
        introfasen och av ensamövningen — «samma bygge tre gånger» (6.4).
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
        # nya ord komma med. De lärs ut som glosor innan övningen (`introsteg`).
        return self._välj(kort, lambda k: k in tillåtna or k.familj == "ord",
                          lambda t: {kort})

    def ensamövning(self, kort: Kort) -> Uppgift | None:
        """Reservsteg 1 i 6.3: kortet prövas ensamt när ingen mening når det.

        Samma form som introövningen (5.4), men utan att kortet visas först —
        övningen är provet, ingen förberedelse — och svaret bokförs som en
        vanlig repetition.

        Den behövs redan dag ett, och det är villkor 5 som gör den nödvändig:
        när de få korten presenterades samma dag är varje kort svagt, och i
        «Time stands.» styr alla fem samma två ord. Ingen mening med flera mål
        är då giltig, och utan ensamövningen fanns ingen uppgift alls — dagen
        gick inte att komma igenom. Budgeten kan aldrig göra ett kort onåbart.
        """
        return self._ensamt_mål(kort, frozenset())

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

    def introsteg(self, kort: Kort,
                  paket: frozenset = frozenset()) -> tuple[list, Uppgift] | None:
        """Vad som ska presenteras för att lära ut `kort`, i kravordning (5.4).

        «Ordningen inom dagen följer kraven. Ett kort presenteras efter de
        kort det kräver, så att lånekorten redan är införda eller
        presenterade.» Glosorna kommer alltså före övningen, och regeln hör
        hemma HÄR och inte i ett gränssnitt: ett annat gränssnitt skulle
        annars behöva komma ihåg att införa den på nytt.

        Ger (glosor, övning), eller None när ingen övning går att bygga.
        """
        uppgift = self.presentera(kort, paket, markera=False)
        if uppgift is None:
            return None
        kända = self.data.införda() | self.data.presenterade()
        glosor = [g for k in sorted(uppgift.träff.kort - kända - {kort}, key=str)
                  if (g := self.glosa(k)) is not None]
        return glosor, uppgift

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
                "kandidater": len(self.kandidater())}
