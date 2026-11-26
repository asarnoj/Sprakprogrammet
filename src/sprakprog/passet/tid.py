"""Tidsmodellen — hur många nya kort dygnet tål (KÄRNAN 5.5).

> **Dagens antal nya kort är det största jämna tempo som ryms varje dag till
> kursens slut:**
>
>     n = minsta värdet av (T − E(t)) / K(t − i dag), över dagarna t fram till
>     kursens slut

    T      den inställda tiden per dag
    E(t)   förväntad arbetstid dag t från de kort som redan är införda
    k(a)   förväntad arbetstid för ett nytt kort a dagar efter presentationen
    K(a)   k(0) + k(1) + … + k(a)

TRE SAKER SKILJER DEN FRÅN DET GAMLA SYSTEMETS `kort/arbetsborda.py`, och alla
tre står i 5.5.

**Arbetet räknas i MENINGAR, inte i kort.** En mening prövar flera kort på en
gång, så n kort kostar inte n repetitioners tid. Växelkursen är 6.3:s mätta
kostnad — `ordbok/verktyg/meningstidsmätning.py` ger `13,4 + 2,8 × kort`, alltså
en fast kostnad som är fem gånger kortets. Därför beror tiden per kort på hur
tätt meningarna packas, och tätheten kommer ur dagsplanen.

**Ingen vald horisont.** Den gamla modulen simulerar med slumptal och behöver
därför ett fönster på fjorton dygn: «bortom ett par veckor beror varje kort på
utfall som ännu inte skett, och simuleringen säger då mer om slumptalen än om
användaren». 5.5 räknar i stället VÄNTEVÄRDEN — «en summa per dag framåt, ingen
simulering» — och ett väntevärde har inget frötal att bli otillförlitligt av.
Horisonten är kursens slut, och slutet följer av tempot: räkningen görs om tills
de två stämmer överens.

**Ingen avräkning.** «Prognosen räknar för högt, och det rättas med en mätning.»
FSRS räknar med att varje förfallet kort kräver en egen repetition, men kort som
behövs i andra meningar möts och bokförs innan de förfaller (7.1). Hur stor del
som faller bort är inte mätt än, och tills det är mätt räknas ingen del bort —
det ger färre nya kort, aldrig fler.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fsrs import Card, Rating

from ..fsrslager import schemaläggare

#: Hur finmaskigt FSRS-tillstånden slås ihop: rutor per e-faldig ökning av
#: stabiliteten, och per svårighetssteg.
#:
#: TILLSTÅND SLÅS IHOP, DE GALLRAS INTE. Varje repetition grenar sig i två —
#: rätt med sannolikhet R, fel med 1 − R — så en exakt uppräkning växer som 2^n.
#: Att i stället kasta de minsta grenarna vore fel åt farligt håll: de grenar
#: som faller ofta är just de som ger MÅNGA repetitioner, så gallringen
#: underskattar arbetet, och underskattat arbete släpper in FLER nya kort. 5.5
#: säger uttryckligen motsatsen — «det ger färre nya kort, aldrig fler». Mätt:
#: med gallring vid 1e-6 gav året 7,88 repetitioner mot den gamla modulens
#: uppmätta 8,4, och att skärpa gränsen slutade konvergera innan den hann bli
#: rätt.
#:
#: Lösningen är att tillstånd som ligger nära varandra räknas som ett. Ett
#: FSRS-tillstånd är (stabilitet, svårighet), och efter ett fall hamnar kortet
#: på nästan samma ställe oavsett hur det kom dit — så tillstånden klumpar sig
#: av sig själva, de matchar bara inte på flyttalsnivå. Med ett rutnät blir
#: antalet levande tillstånd bundet av rutnätet, och kostnaden växer med
#: upplösningen i stället för med tiden.
#:
#: TALET ÄR MÄTT FRAM, inte valt. Summan över ett år, per upplösning:
#:
#:     upplösning   30 dagar   365 dagar   tillstånd   sekunder
#:              6      3,685       8,334          74        0,2
#:             12      3,685       8,365         147        0,4
#:             24      3,685       8,370         291        0,7
#:             48      3,685       8,374         728        1,8
#:             96      3,685       8,376        2080        5,4
#:
#: Första månaden är identisk vid varje upplösning, och året konvergerar mot
#: 8,376. Tjugofyra ligger 0,07 % under gränsvärdet och kostar 0,7 s — och 8,37
#: stämmer med den gamla modulens Monte Carlo-mätta 8,4, som har sitt eget
#: urvalsfel. Att gå finare köper tre decimaler för åtta gånger tiden.
UPPLÖSNING = 24


@dataclass(frozen=True, slots=True)
class Meningstid:
    """Vad en mening kostar i sekunder: `fast + per_kort × kort` (6.3).

    Formen är 6.3:s eget påstående — «den fasta kostnaden per mening dominerar»
    — och de två talen är mätta ur loggen av
    `ordbok/verktyg/meningstidsmätning.py`.
    """
    fast: float
    per_kort: float
    #: Hur många kort en mening bedömde i MEDIAN i loggen som mätte linjen.
    #: Reserven för en ny kurs: «innan användarens egen historik finns används
    #: FSRS standardparametrar och tiderna ur den gamla loggen» (5.5). Utan den
    #: kan en ny kurs inte grindas alls, eftersom tätheten är det enda mått som
    #: kräver att användaren redan övat.
    täthet: float

    @classmethod
    def ur_fil(cls, fil: str | Path) -> Meningstid | None:
        """Linjen anpassad ur mätpunkterna, eller None när de är för få.

        Utan talet finns ingen väg från minuter till kort, och då svarar
        modellen «vet inte» i stället för att gissa.
        """
        sökväg = Path(fil)
        if not sökväg.exists():
            return None
        with sökväg.open(encoding="utf-8") as f:
            rader = [{"kort": int(r["kort"]), "meningar": int(r["meningar"]),
                      "sekunder": float(r["sekunder"])} for r in csv.DictReader(f)]
        linje = _anpassa(rader)
        if linje is None:
            return None
        # Medianen över de loggade MENINGARNA, inte över grupperna: en grupp med
        # tjugonio meningar ska väga tjugonio gånger tyngre än en med en.
        vikter = sorted((r["kort"] for r in rader for _ in range(r["meningar"])))
        return cls(*linje, täthet=float(vikter[len(vikter) // 2]))

    def per_repetition(self, kort_per_mening: float) -> float:
        """Sekunder per BEDÖMT kort vid den tätheten.

        En mening med c kort kostar `fast + per_kort × c` och ger c
        bedömningar. Packas meningarna tätare sjunker priset per kort, och det
        är hela skälet att 5.5 räknar arbetet i meningar.
        """
        if kort_per_mening <= 0:
            raise ValueError("tätheten måste vara positiv")
        return (self.fast + self.per_kort * kort_per_mening) / kort_per_mening


#: Så många meningar krävs i en grupp innan dess median används. Samma tal och
#: samma skäl som i `meningstidsmätning`, som mäter punkterna.
MINSTA_I_GRUPP = 10


def _anpassa(rader: list[dict]) -> tuple[float, float] | None:
    """(fast, per_kort) med viktad minsta kvadrat över grupperna som är stora nog.

    Samma räkning som `meningstidsmätning.anpassa`. Den bor på två ställen av
    ett skäl: verktyget mäter och skriver punkterna, och kärnan läser dem —
    KÄRNAN 9 säger att verktygen inte är beroenden för koden.
    """
    säkra = [r for r in rader if r["meningar"] >= MINSTA_I_GRUPP]
    if len(säkra) < 2:
        return None
    v = [float(r["meningar"]) for r in säkra]
    x = [float(r["kort"]) for r in säkra]
    y = [float(r["sekunder"]) for r in säkra]
    sv = sum(v)
    mx = sum(a * b for a, b in zip(v, x)) / sv
    my = sum(a * b for a, b in zip(v, y)) / sv
    nämnare = sum(a * (b - mx) ** 2 for a, b in zip(v, x))
    if not nämnare:
        return None
    per_kort = sum(a * (b - mx) * (c - my) for a, b, c in zip(v, x, y)) / nämnare
    return my - per_kort * mx, per_kort


def arbetsprofil(retention: float, dagar: int,
                 upplösning: int = UPPLÖSNING) -> tuple[list[float], int]:
    """k(a) i REPETITIONER: väntevärdet dag 0..dagar från ett kort som införs i dag.

    Ger (profilen, största antalet samtidigt levande tillstånd).

    ETT VÄNTEVÄRDE, INTE EN SIMULERING. 5.5 föreskriver «en genomräkning av
    FSRS-tillståndens sannolikheter dag för dag», och skillnaden mot att dra
    slumptal är att svaret inte beror på ett frötal. Varje repetition grenar
    sig: rätt med sannolikhet R, fel med 1 − R, och båda grenarna följs med sin
    vikt. Tillstånd som hamnar i samma ruta räknas som ett (`UPPLÖSNING`), så
    ingen sannolikhetsmassa försvinner — den flyttas bara någon procent i
    stabilitet.

    Introduktionen räknas med i dag 0: att presentera kortet kostar också tid
    (5.4), och 5.5:s K(0) är det första dygnets arbete.
    """
    s = schemaläggare(retention)
    start = datetime(2000, 1, 1, tzinfo=UTC)
    per_dag = [0.0] * (dagar + 1)
    #: dag → ruta → (ett kort i rutan, sannolikhetsmassan i den)
    framtid: dict[int, dict[tuple, list]] = defaultdict(dict)
    störst = 0

    def lägg(c: Card, p: float) -> None:
        dag = (c.due - start).days
        if dag > dagar:
            return
        ruta = (round(math.log(max(c.stability or 1e-9, 1e-9)) * upplösning),
                round((c.difficulty or 0.0) * upplösning))
        post = framtid[dag].get(ruta)
        if post is None:
            framtid[dag][ruta] = [c, p]
        else:
            post[1] += p

    kort, _ = s.review_card(Card(), Rating.Good, start)
    per_dag[0] += 1.0
    lägg(kort, 1.0)
    for dag in range(dagar + 1):
        rutor = framtid.pop(dag, None)
        if not rutor:
            continue
        störst = max(störst, len(rutor))
        tid = start + timedelta(days=dag)
        for c, p in rutor.values():
            per_dag[dag] += p
            R = s.get_card_retrievability(c, current_datetime=tid)
            for betyg, andel in ((Rating.Good, R), (Rating.Again, 1 - R)):
                if andel <= 0:
                    continue
                nytt, _ = s.review_card(c, betyg, tid)
                lägg(nytt, p * andel)
    return per_dag, störst


@dataclass(frozen=True, slots=True)
class Tempo:
    """Svaret från tidsmodellen, med det som gör talet läsbart."""
    #: Hur många nya kort dagen tål. Noll är ett riktigt svar (5.5).
    nya: int
    #: Vilken framtida dag som var den bindande — den som gav minimum.
    trängsta_dagen: int
    #: Hur många dagar kursen tar i det tempot, eller None när n är noll.
    slutdagen: int | None
    #: Arbetstiden i sekunder den trängsta dagen, från de INFÖRDA korten.
    upptaget: float
    #: Sekunder per bedömt kort vid dagens täthet.
    per_repetition: float


class Tidsmodell:
    """5.5, räknad ur en arbetsprofil och en mätt meningskostnad.

    `åldrar` är hur många dagar sedan varje infört kort presenterades, och
    `kvar` hur många kort kursen har att införa. Båda kommer utifrån: modellen
    läser ingen databas.
    """

    def __init__(self, profil: list[float], meningstid: Meningstid,
                 kort_per_mening: float, introsekunder: float) -> None:
        self.profil = profil
        self.per_repetition = meningstid.per_repetition(kort_per_mening)
        #: Vad det kostar att INFÖRA kortet, utöver dess repetitioner.
        #:
        #: Introfasen bokför ingenting (5.4) men tar tid, och 5.5 räknar den:
        #: «tid per introövning, med omtag». Den ligger på dag 0 och bara där —
        #: ett redan infört kort har sin introduktion bakom sig, så `upptaget`
        #: räknar den inte.
        self.introsekunder = introsekunder
        #: K(a) = k(0) + … + k(a), i sekunder.
        #: K(a) = k(0) + … + k(a), i sekunder.
        self.K: list[float] = []
        #: Prefixsumman av profilen i REPETITIONER, för fönstersummor.
        self._prefix: list[float] = [0.0]
        summa = introsekunder
        for rep in profil:
            summa += rep * self.per_repetition
            self.K.append(summa)
            self._prefix.append(self._prefix[-1] + rep)

    def upptaget(self, dag: int, åldrar: list[int]) -> float:
        """E(t): arbetstiden dag `dag` från de kort som redan är införda.

        «Arbetsbördan är summan av varje korts arbetsprofil, förskjuten till den
        dag kortet presenterades» (5.5). Ett kort som presenterades för a dagar
        sedan är dag t i profilens läge a + t.
        """
        return self.per_repetition * sum(
            self.profil[a + dag] for a in åldrar if a + dag < len(self.profil))

    def tempo(self, minuter: float, åldrar: list[int], kvar: int) -> Tempo:
        """n enligt 5.5, med slutdagen och tempot i samklang.

        «Ingen vald horisont. Kursen slutar när alla kort är införda. När det
        sker beror på tempot, så räkningen görs om tills tempot och slutdagen
        stämmer överens; det tar några varv.»

        HORISONTEN GÅR FÖRBI SLUTDAGEN. «Över dagarna t fram till kursens slut»
        är inte hela villkoret: ett kort kostar arbete i över ett år, så
        arbetsbördan fortsätter efter sista införandet. Minimeringen sträcker
        sig därför till slutdagen PLUS arbetsprofilens längd, och efter
        slutdagen införs inga nya kort — bidraget per nytt kort är då inte
        längre K(t) utan ett FÖNSTER genom profilen: de kort som infördes dag
        t − slutdagen … t.

        MEN DEN BÄR INTE TALET, och det ska stå rätt. Mätt: den korta horisonten
        ger 30 kort vid tjugo minuter mot 27 med den hela, eftersom dagarna efter
        slutdagen aldrig binder — då är arbetet utspritt över året. Det som tämjer
        tempot är INTRODUKTIONSKOSTNADEN: utan den gav en timme om dagen 265 nya
        kort och en kurs på sex dagar. Horisonten är kvar för att den är den
        riktiga formeln, inte för att den räddade något.
        """
        T = minuter * 60
        n = max(kvar, 1)
        sedda: set[int] = set()
        while n > 0 and n not in sedda:
            sedda.add(n)
            nytt, _ = self._minimum(T, åldrar, self._slutdag(kvar, n))
            if nytt == n:
                break
            n = nytt
        slut = self._slutdag(kvar, n) if n > 0 else 0
        n, trängsta = self._minimum(T, åldrar, slut)
        return Tempo(nya=max(0, n), trängsta_dagen=trängsta,
                     slutdagen=self._slutdag(kvar, n) if n > 0 else None,
                     upptaget=self.upptaget(trängsta, åldrar),
                     per_repetition=self.per_repetition)

    @staticmethod
    def _slutdag(kvar: int, n: int) -> int:
        """Hur många dagar det tar att införa `kvar` kort i tempot n."""
        return max(1, -(-kvar // n)) if n > 0 else 0

    def _minimum(self, T: float, åldrar: list[int], slut: int) -> tuple[int, int]:
        """(n, den bindande dagen) — minimum av (T − E(t)) / bidrag(t) över hela
        horisonten, alltså slutdagen plus arbetsprofilens längd."""
        bäst: float | None = None
        trängsta = 0
        for t in range(slut + len(self.profil)):
            # Bidraget per nytt kort dag t: de kort som infördes dag
            # max(0, t − slut) … min(t, slut) är nu i profilens läge
            # t − dag, alltså ett fönster genom K.
            övre = min(t, slut)
            undre = max(0, t - len(self.profil) + 1)
            if övre < undre:
                continue
            bidrag = self._fönster(t - övre, t - undre) * self.per_repetition
            # Korten som införs I DAG bär också sin introduktion. Dag t gäller
            # det bara det kort som infördes dag t, alltså när fönstret når
            # profilens dag 0.
            if t <= slut:
                bidrag += self.introsekunder
            if bidrag <= 0:
                continue
            ryms = (T - self.upptaget(t, åldrar)) / bidrag
            if bäst is None or ryms < bäst:
                bäst, trängsta = ryms, t
        # Golvet, inte avrundning: ett halvt kort finns inte, och att runda upp
        # vore att lägga på arbete budgeten inte har.
        return (0 if bäst is None else int(bäst // 1)), trängsta

    def _fönster(self, från: int, till: int) -> float:
        """k(från) + … + k(till), ur prefixsumman."""
        if till < 0 or från >= len(self._prefix) - 1:
            return 0.0
        till = min(till, len(self._prefix) - 2)
        från = max(från, 0)
        return self._prefix[till + 1] - self._prefix[från]
