"""Kandidatgenerering — meningar att poängsätta.

Sökningen är sampla-och-poängsätt, inte constraint-lösning (GENERATOR.md,
"Sökningen"). Den här modulen gör samplingen, och två val avgör att den
räcker till.

FYLLNADEN VÄLJS SÅ ATT KRAVET UPPFYLLS, i stället för att slumpas och
förkastas efteråt. Ett slumpmässigt svep hade 89 % avvisade av
restriktionerna; med ett index från krav till koncept blir nästan varje
kandidat giltig, och budgeten av kandidater räcker mycket längre.

MÅLORDEN PLACERAS FÖRST. Ska ett förfallet kort prövas läggs dess ord i en
slot som verbet faktiskt öppnar, och resten fylls runt. Att hoppas på att en
slumpmässig mening råkar innehålla rätt ord vore hopplöst — beståndet är
24 000 kort.

Vad modulen INTE gör är att räkna ut vilken böjning ett visst kort kräver.
Cellen `pret_3sg` kommer ur förfluten tid och tredje person, `akk_sg` ur en
objektsslot — men den bakvägen finns inte, och behöver inte finnas: kandidaten
renderas och beroendekartan säger i efterhand exakt vilka kort den rörde.
"""

from __future__ import annotations

import collections
import random
from dataclasses import replace
import sqlite3

from ..rendering import (
    Aspekt, Attribut, Bestämdhet, Bisats, Diates, Grad, Mening, Nominalfras,
    Numerus, Prepositionsfras, Satsmodus, Tidsreferens,
)

#: CEFR-nivåerna i stigande ordning. Ett tak på A2 släpper in A1 också.
#:
#: Ortogonal mot komplexitetsstegen nedan, och båda behövs: den ena säger
#: vilka ORD en nybörjare möter, den andra vilka KONSTRUKTIONER. Att blanda
#: ihop dem vore att påstå att den som lärt sig bisatser också kan alla ord.
CEFR = ("A1", "A2", "B1", "B2", "C1", "C2")


#: Vad varje nivå på komplexitetsstegen låser upp. Nycklarna är egenskaper
#: hos specen, inte konstruktioner i språket — det är specen samplaren rör.
#: Se GENERATOR.md, "Komplexitetsstegen".
NIVÅ = {
    2: "objekt", 3: "bestämdhet", 4: "numerus", 5: "attribut", 6: "possessiv",
    7: "io", 8: "adverbial", 9: "tempus", 10: "genitiv", 11: "predikativ",
    12: "negation", 13: "komplement", 14: "perfekt", 15: "prepositionsfras",
    16: "fråga", 17: "passiv", 18: "komparation", 19: "imperativ",
    20: "bisats", 21: "whfråga",
}

TILLTALADE = ("pronomen_2sg", "pronomen_2pl", "pronomen_1pl")

#: Subjunktioner som inleder en ARGUMENTBISATS — satsen som ÄR verbets objekt.
#: De adverbiella (när, eftersom, medan, tills, trots att) inleder en
#: omständighet och hör hemma i `adverbial`, inte i `bisats`. Skillnaden är
#: spec.Bisats egen: "hon vet ATT han kom" mot "hon läste NÄR han kom".
#: Utan listan valde samplaren fritt och byggde "han menade INTE, NÄR hennes
#: mus öppnade" — grammatiskt men inte en argumentbisats.
ARGUMENTSUBJUNKTIONER = ("subj_att", "subj_om_huruvida")


def upplåst(nivå: int) -> set[str]:
    return {namn for n, namn in NIVÅ.items() if n <= nivå}


def _någon_fras(m):
    """Meningens nominalfraser, inklusive bisatsens."""
    for nf in (m.subjekt, m.objekt, m.io, m.predikativ):
        if nf is not None and not isinstance(nf, str):
            yield nf
    if m.bisats is not None:
        yield from _någon_fras(m.bisats.sats)


#: ANVÄNDER MENINGEN FAKTISKT NIVÅNS KONSTRUKTION?
#:
#: `upplåst(nivå)` säger vad som är TILLÅTET. Det här säger vad en färdig spec
#: faktiskt GJORDE, och skillnaden är hela skälet till att upplåsningsgrinden
#: inte fungerade: `byggbarhet` samplade meningar på nivån och frågade bara om
#: de hade högst ett okänt ord. På nivå 2 är en vanlig subjekt-verb-mening
#: fortfarande giltig, så måttet mätte nivå 1 och släppte igenom nivå 2.
#:
#: Mätt 2026-08-26: efter EN dags franska gick tjugo nivåer att låsa upp i
#: följd, 632 kort, utan att öva emellan. Byggbarheten låg på 0,006–0,067 och
#: tröskeln är 0,00125, så varje nivå passerade — mätt på meningar som inte
#: innehöll det nivån handlade om.
#:
#: Predikaten är fält på `Mening` och inget annat. En konstruktion som inte
#: går att se i specen hör inte hemma på komplexitetsstegen.
ANVÄNDER = {
    "objekt":           lambda m: m.objekt is not None,
    "bestämdhet":       lambda m: any(f.bestämdhet is not Bestämdhet.OBESTÄMD
                                      for f in _någon_fras(m)),
    "numerus":          lambda m: any(f.numerus is Numerus.PL
                                      for f in _någon_fras(m)),
    "attribut":         lambda m: any(f.attribut for f in _någon_fras(m)),
    "possessiv":        lambda m: any(f.possessiv for f in _någon_fras(m)),
    "io":               lambda m: m.io is not None,
    "adverbial":        lambda m: any(isinstance(a, str) for a in m.adverbial),
    "tempus":           lambda m: m.tid is not Tidsreferens.NUTID,
    "genitiv":          lambda m: any(f.ägare for f in _någon_fras(m)),
    "predikativ":       lambda m: m.predikativ is not None,
    "negation":         lambda m: m.negerad,
    "komplement":       lambda m: m.komplement is not None,
    "perfekt":          lambda m: m.aspekt is Aspekt.PERFEKT,
    "prepositionsfras": lambda m: any(isinstance(a, Prepositionsfras)
                                      for a in m.adverbial),
    "fråga":            lambda m: m.fråga,
    "passiv":           lambda m: m.diates is not Diates.AKTIV,
    "komparation":      lambda m: any(a.grad is not Grad.POSITIV
                                      for f in _någon_fras(m) for a in f.attribut),
    "imperativ":        lambda m: m.modus is Satsmodus.IMPERATIV,
    "bisats":           lambda m: m.bisats is not None,
    "whfråga":          lambda m: m.fråga_om is not None,
}


def använder_nivån(m, nivå: int) -> bool:
    """Använder specen den konstruktion `nivå` låser upp?

    Nivå 1 har ingen egen konstruktion — den ÄR grundsatsen — så varje mening
    räknas där.
    """
    namn = NIVÅ.get(nivå)
    return True if namn is None else ANVÄNDER[namn](m)


class Ordförråd:
    """Index från semantiskt krav till de koncept som uppfyller det.

    Byggs en gång per språk. Utan det skulle samplaren kasta nio kandidater
    av tio, vilket är precis vad den första mätningen visade.
    """

    def __init__(self, conn: sqlite3.Connection, språk: str,
                 cefr: str = "C2") -> None:
        self.conn = conn
        self.språk = språk
        self.cefr = cefr
        self.semantik: dict[str, int] = {}
        self.ordklass: dict[str, str] = {}
        self.räknebar: dict[str, bool] = {}
        tillåtna = CEFR[:CEFR.index(cefr) + 1] if cefr in CEFR else CEFR
        platser = ",".join("?" * len(tillåtna))
        for r in conn.execute(
                f"""SELECT k.nyckel, k.ordklass, k.semantik, k.räknebar
                    FROM Koncept k JOIN Lexem l ON l.koncept_id = k.id
                    WHERE l.språk = ?
                      AND (k.nivå IS NULL OR k.nivå IN ({platser}))
                      AND EXISTS (SELECT 1 FROM Former f WHERE f.lexem_id = l.id)
                    GROUP BY k.id""", (språk, *tillåtna)):
            self.ordklass[r["nyckel"]] = r["ordklass"]
            self.räknebar[r["nyckel"]] = bool(r["räknebar"])
            if r["semantik"] is not None:
                self.semantik[r["nyckel"]] = r["semantik"]

        self.per_ordklass: dict[str, list[str]] = collections.defaultdict(list)
        for nyckel, ordklass in self.ordklass.items():
            self.per_ordklass[ordklass].append(nyckel)

        # Verb med ett universellt mönster — de som går att bygga en sats av.
        self.verb: dict[str, dict[str, list[int]]] = {}
        for r in conn.execute(
                """SELECT k.nyckel, mk.slot, mk.tagg FROM Mönster m
                   JOIN Koncept k ON k.id = m.koncept_id
                   JOIN MönsterKrav mk ON mk.mönster_id = m.id
                   WHERE m.språk IS NULL AND k.ordklass = 'Verb'"""):
            if r["nyckel"] in self.ordklass:
                slotkrav = self.verb.setdefault(r["nyckel"], {})
                if r["tagg"] is not None:
                    slotkrav.setdefault(r["slot"], []).append(r["tagg"])
                else:
                    slotkrav.setdefault(r["slot"], [])

        # Verb som tar en ARGUMENTBISATS. Kravet står som en bit i
        # MönsterKrav.frastyp (Bisatsfras = 32) och inte som en egen slot, så
        # det syns inte i `self.verb` ovan. Utan den här frågan kan samplaren
        # inte bygga nivå 20 alls — vilket den inte kunde förrän 2026-08-15.
        self.bisatsverb: dict[str, str] = {}
        for r in conn.execute(
                """SELECT k.nyckel, mk.slot FROM Mönster m
                   JOIN Koncept k ON k.id = m.koncept_id
                   JOIN MönsterKrav mk ON mk.mönster_id = m.id
                   WHERE mk.frastyp & 32 AND k.ordklass = 'Verb'
                     AND (m.språk IS NULL OR m.språk = ?)""", (språk,)):
            if r["nyckel"] in self.ordklass:
                self.bisatsverb[r["nyckel"]] = r["slot"]

        self._cache: dict[tuple, list[str]] = {}

    #: Ordklasser som kan fylla en nominalfrasslot. Pronomen hör hit — utan
    #: dem går personböjningen aldrig att pröva, och de är dessutom de
    #: första orden en nybörjare möter.
    FRASHUVUD = ("Substantiv", "Pronomen")

    def uppfyller(self, alternativ: list[int], ordklass: str = "*") -> list[str]:
        """Koncept som klarar minst ett av kraven. Tom lista = inget krav."""
        nyckel = (tuple(sorted(alternativ)), ordklass)
        if nyckel not in self._cache:
            if ordklass == "*":
                kandidater = [k for o in self.FRASHUVUD
                              for k in self.per_ordklass.get(o, [])]
            else:
                kandidater = self.per_ordklass.get(ordklass, [])
            if not alternativ:
                träffar = [k for k in kandidater if k in self.semantik]
            else:
                träffar = [k for k in kandidater
                           if any(self.semantik.get(k, 0) & a == a for a in alternativ)]
            self._cache[nyckel] = träffar or kandidater
        return self._cache[nyckel]

    def verb_för(self, koncept: str) -> list[str]:
        """Verb vars mönster har en slot som `koncept` kan fylla."""
        ut = []
        for verb, slotkrav in self.verb.items():
            for slot, alternativ in slotkrav.items():
                if slot in ("subjekt", "objekt", "io") and (
                        not alternativ
                        or any(self.semantik.get(koncept, 0) & a == a
                               for a in alternativ)):
                    ut.append(verb)
                    break
        return ut


class Samplare:
    """Bygger kandidatmeningar, gärna runt ett givet ord."""

    def __init__(self, ordförråd: Ordförråd, nivå: int,
                 rng: random.Random | None = None) -> None:
        self.o = ordförråd
        self.tillåtet = upplåst(nivå)
        self.rng = rng or random.Random()
        #: Koncept som fyllnaden ska hålla sig till, eller None för alla.
        #: Sätts av `begränsa` när dagens utrymme för nytt är slut.
        self.känt: set[str] | None = None

    def begränsa(self, koncept: set[str] | None) -> None:
        """Håll FYLLNADEN till de här koncepten. None släpper begränsningen.

        DET HÄR ÄR VAD SOM GÖR DAGSPLANENS TAK BINDANDE. Taket räknades först
        bara mot generatorns KÖ, alltså mot vilka kort en mening byggs runt —
        men en mening består inte bara av sitt målord. Resten av orden väljs
        fritt här, och varje osett ord som råkar hamna i en mening blir sett,
        betygsatt och infört.

        Mätt: sextio meningar med taket satt till NOLL nya kort införde ändå
        35 stycken, som lade 17,5 repetitioner per dygn på belastningen. De
        tidiga repetitionerna samma pass frigjorde 6,1. Taket var alltså inte
        bara otätt utan överröstat, och kapacitetsmodellen kunde beskriva
        arbetsbördan utan att kunna styra den.

        Målordet går fri: det väljs av kön och inte här, och att bygga en
        mening runt ett nytt kort är hela poängen med att införa det.
        """
        self.känt = koncept

    def _välj(self, kandidater):
        """Ett koncept ur `kandidater`, helst ett användaren redan mött.

        GER UPP HELLRE ÄN FALLER TILLBAKA. Tidigare togs ett OSETT ord när
        begränsningen tömde sloten, och det skedde tyst och per slot — så ett
        ord användaren aldrig mött kunde stå i meningen trots att dagens tak
        var noll. Mätt i bruk: `kostar` dök upp i en fransk mening samma dag
        som sex ord introducerats, och `kostar` var inte ett av dem.

        Reservutgången finns kvar, men på SÖKNINGENS nivå (`Generator._sök`):
        hittar hela sökningen ingenting med bara kända ord körs den om utan
        begränsning. Skillnaden är att undantaget då är ett undantag — ett
        beslut för hela meningen — i stället för något som smyger in ett ord
        i taget.

        `None` ÄR ETT SVAR OCH MÅSTE HANTERAS AV ANROPAREN. Det var det inte:
        tolv av fjorton anropsställen tog emot `None` och byggde specen ändå.
        Mätt på 3 000 kandidater med begränsat ordförråd, per nivå:

            nivå  5   attribut       4–24 % fick `Attribut(None)`
            nivå  5   objekt          0–10 % fick `Nominalfras(None)`
            nivå  8   adverbial      15 %   fick ett naket `None` i tupeln
            nivå 15   prepositions-  20 %   fick `Prepositionsfras(None, …)`
            nivå 20   bisats                `self.o.verb[None]` → KeyError

        De två första gav `RenderingsFel`, alltså tyst kastade kandidater —
        27 % av engelskans sökning på nivå 5, utan att något mätte det. De
        två sista gav `AttributeError` respektive `KeyError` UTANFÖR det
        `_rendera` fångar, alltså en krasch rakt ut ur `föreslå`.

        REGELN ÄR ATT KONSTRUKTIONEN FALLER, INTE ATT DEN BYGGS MED ETT HÅL,
        och vilken sorts fall beror på slotten:

            utsmyckning     attribut, adverbial, prepositionsfras, possessiv,
                            genitiv — HOPPAS ÖVER. Meningen är hel utan den.
            obligatorisk    subjekt, objekt, io, komplement, predikativ,
                            bisatsens verb — KANDIDATEN KASTAS, samma svar
                            som verbslotten redan gav.

        Att skilja på dem är inte en detalj: en utsmyckning som kastar hela
        kandidaten skulle tömma sökningen vid kallstart, och en obligatorisk
        slot som hoppas över ger en mening utan subjekt.
        """
        if not kandidater:
            return None
        if self.känt is not None:
            kända = [k for k in kandidater if k in self.känt]
            return self.rng.choice(kända) if kända else None
        return self.rng.choice(list(kandidater))

    #: Hur ofta samplaren FÖRSÖKER med en konstruktion. Det här är inga
    #: inställningar och inga trösklar: sökningen tar bästa av tusen
    #: kandidater, så en frekvens behöver bara vara stor nog att
    #: konstruktionen dyker upp bland kandidaterna. Poängfunktionen avgör
    #: sedan vad som faktiskt visas. Att sätta någon av dem till noll är
    #: däremot att stänga av en hel nivå — vilket var precis vad som hade
    #: hänt för possessiv, adverbial, genitiv, prepositionsfras och bisats.
    FÖRSÖK = {"possessiv": 0.15, "genitiv": 0.10, "adverbial": 0.15,
              "prepositionsfras": 0.20, "bisats": 0.25}

    def _nf(self, koncept: str | None, *, attributkandidater: list[str],
            djup: int = 0) -> Nominalfras | None:
        """Nominalfrasen, eller None när `koncept` är None.

        Att ta emot None och lämna vidare None är hela poängen: varje anropare
        väljer sitt koncept med `_välj`, som ger upp när begränsningen tömt
        sloten. Utan den här grinden byggdes `Nominalfras(None)` i stället,
        och renderaren svarade med `RenderingsFel` — en tyst kastad kandidat
        som ingen räknade.
        """
        if koncept is None:
            return None
        r = self.rng
        # Ett pronomen ÄR hela frasen — det tar varken artikel, numerus
        # eller attribut, och renderarna vägrar om man försöker.
        if self.o.ordklass.get(koncept) == "Pronomen":
            return Nominalfras(koncept)
        best = Bestämdhet.OBESTÄMD
        if "bestämdhet" in self.tillåtet:
            best = r.choice([Bestämdhet.OBESTÄMD, Bestämdhet.BESTÄMD])
        num = Numerus.SG
        if "numerus" in self.tillåtet and self.o.räknebar.get(koncept, True):
            num = r.choice([Numerus.SG, Numerus.PL])
        attribut: tuple = ()
        if "attribut" in self.tillåtet and attributkandidater and r.random() < 0.4:
            grad = Grad.POSITIV
            if "komparation" in self.tillåtet and r.random() < 0.3:
                grad = r.choice([Grad.KOMPARATIV, Grad.SUPERLATIV])
            if grad is Grad.SUPERLATIV and best is not Bestämdhet.BESTÄMD:
                grad = Grad.KOMPARATIV
            # UTSMYCKNING: tömde begränsningen adjektiven blir frasen naken,
            # inte trasig. `Attribut(None)` gav RenderingsFel — 24 % av
            # engelskans kandidater på nivå 5.
            valt = self._välj(attributkandidater)
            if valt is not None:
                attribut = (Attribut(valt, grad),)

        # Possessiv och genitivägare tar ARTIKELNS plats — "mitt hus", inte
        # "det mitt hus". Frasen är bestämd ändå (spec.bestämd_fras), så
        # bestämdheten sätts tillbaka till obestämd för att inte be
        # renderaren om både artikel och ägare.
        possessiv = ägare = None
        possessiva = self.o.per_ordklass.get("Possessiv", [])
        if ("possessiv" in self.tillåtet and possessiva
                and r.random() < self.FÖRSÖK["possessiv"]):
            # UTSMYCKNING. Bestämdheten flyttas bara när ägaren faktiskt
            # blev av — annars vore frasen obestämd utan att något tagit
            # artikelns plats.
            valt = self._välj(possessiva)
            if valt is not None:
                possessiv, best = valt, Bestämdhet.OBESTÄMD
        elif ("genitiv" in self.tillåtet and djup == 0
                and r.random() < self.FÖRSÖK["genitiv"]):
            # Ägaren är en egen nominalfras, och den byggs på DJUP 1 så att
            # den inte i sin tur får en ägare. "Kattens hunds ben" är
            # grammatiskt men ingen övningsmening.
            möjliga = self.o.uppfyller([], "Substantiv")
            if möjliga:
                # UTSMYCKNING, och `_nf` ger None när begränsningen tömt
                # substantiven. Utan grinden gick `None` in i `replace`.
                ägare = self._nf(self._välj(möjliga), attributkandidater=[],
                                 djup=1)
                if ägare is not None:
                    ägare = replace(ägare, bestämdhet=Bestämdhet.BESTÄMD)
                    best = Bestämdhet.OBESTÄMD
        return Nominalfras(koncept, best, num, attribut,
                           possessiv=possessiv, ägare=ägare)

    def duger_som_mål(self, koncept: str) -> bool:
        """Skulle `kandidat(kring=koncept)` faktiskt placera ordet?

        SAMMA VILLKOR SOM `kandidat` SJÄLV använder, läst ur den och inte
        gissat: verbet blir målordet om det är ett verb i mönstret, och en
        nominalfras byggs kring det om ordklassen är ett frashuvud som något
        verb tar. Allt annat — artiklar, adverb, systemord — går rakt igenom
        `else`-grenen och får ett SLUMPMÄSSIGT verb i stället. Målordet
        ignoreras alltså tyst.

        Det tysta ignorerandet var en riktig låsning. `un` drillades som ord,
        blev därmed "infört men inte övat", och stod först i målordslistan —
        men en artikel går inte att bygga en mening KRING, bara att få med på
        köpet i en nominalfras. Eftersom listan ERSATTE kön i stället för att
        gå före den blev varje mening byggd kring ett ignorerat mål, alltså
        kring ett slumpvis verb, och kön rördes aldrig. Mätt: fyra meningar i
        rundgång, täckning noll, 330 gånger.

        Regeln är alltså inte "artiklar duger inte" utan "fråga samplaren vad
        den kan bygga kring". Skulle `kandidat` lära sig fler frashuvuden
        följer det här med av sig självt.
        """
        ordklass = self.o.ordklass.get(koncept)
        if ordklass == "Verb":
            return koncept in self.o.verb
        return ordklass in self.o.FRASHUVUD and bool(self.o.verb_för(koncept))

    def kandidat(self, *, kring: str | None = None) -> Mening | None:
        """En kandidatmening, byggd runt `kring` om det går."""
        r = self.rng
        adjektiv = self.o.per_ordklass.get("Adjektiv", [])

        # Verbet: det som ska prövas, eller ett som tar målordet
        if kring and self.o.ordklass.get(kring) == "Verb" and kring in self.o.verb:
            verb = kring
        elif kring and self.o.ordklass.get(kring) in self.o.FRASHUVUD:
            möjliga = self.o.verb_för(kring)
            verb = self._välj(möjliga)
        else:
            verb = self._välj(list(self.o.verb))
        if verb is None:
            return None
        slotkrav = self.o.verb[verb]

        def fyll(slot: str) -> Nominalfras | None:
            if slot not in slotkrav:
                return None
            val = self.o.uppfyller(slotkrav[slot])
            if not val:
                return None
            # målordet placeras i den slot det passar
            if (kring and self.o.ordklass.get(kring) in self.o.FRASHUVUD
                    and kring in val):
                return self._nf(kring, attributkandidater=adjektiv)
            return self._nf(self._välj(val), attributkandidater=adjektiv)

        subjekt = fyll("subjekt")
        if subjekt is None:
            return None
        objekt = fyll("objekt") if "objekt" in self.tillåtet else None
        io = fyll("io") if "io" in self.tillåtet else None

        # Ett verb med komplementslot är ett modalverb — "He will." utan
        # huvudverb är ingen mening. Kan slotten inte fyllas duger inte
        # verbet, och kandidaten kastas hellre än renderas halv.
        komplement = None
        if "komplement" in slotkrav:
            if "komplement" not in self.tillåtet:
                return None
            # OBLIGATORISK SLOT: tömde begränsningen verben finns inget
            # huvudverb, och "He will." är ingen mening. Samma svar som
            # verbslotten ovan ger — kandidaten kastas, den byggs inte halv.
            komplement = self._välj(list(self.o.verb))
            if komplement is None:
                return None

        # Samma sak för kopulan: "Sie ist." är ingen mening. Ett verb med
        # predikativslot MÅSTE få ett predikativ, och det får vara adjektiv
        # eller substantiv — mönstret säger vilket.
        predikativ = None
        if "predikativ" in slotkrav:
            if "predikativ" not in self.tillåtet:
                return None
            # OBLIGATORISK SLOT, av samma skäl: "Sie ist." är ingen mening.
            if adjektiv and r.random() < 0.7:
                predikativ = self._välj(adjektiv)
            else:
                val = self.o.uppfyller([], "Substantiv")
                if not val:
                    return None
                valt = self._välj(val)
                predikativ = None if valt is None else Nominalfras(valt)
            if predikativ is None:
                return None
        m = Mening(verb, subjekt, objekt=objekt, io=io, komplement=komplement,
                   predikativ=predikativ)
        if "tempus" in self.tillåtet:
            m = _med(m, tid=r.choice(list(Tidsreferens)))
        if "perfekt" in self.tillåtet and r.random() < 0.2:
            m = _med(m, aspekt=Aspekt.PERFEKT)
        if "negation" in self.tillåtet and r.random() < 0.2:
            m = _med(m, negerad=True)
        if "fråga" in self.tillåtet and r.random() < 0.15:
            m = _med(m, fråga=True)
        if "passiv" in self.tillåtet and objekt is not None and r.random() < 0.15:
            m = _med(m, subjekt=objekt, objekt=None, diates=Diates.PASSIV)
        # Imperativen byter ut SUBJEKTET, så den får inte tillämpas när
        # målordet står där — då kastas hela skälet att bygga meningen.
        # Och en naken imperativ ("Seht!") är två kort och prövar nästan
        # ingenting; den kräver ett objekt för att vara värd att visa.
        if ("imperativ" in self.tillåtet and objekt is not None
                and kring != subjekt.koncept and r.random() < 0.1):
            m = _med(m, subjekt=Nominalfras(r.choice(TILLTALADE)),
                     modus=Satsmodus.IMPERATIV, fråga=False)
        # En uppmaning kan inte samtidigt vara en wh-fråga — "Seht wer sie?"
        # är ingen sats. Samplaren råkade bygga den innan villkoret fanns.
        if ("whfråga" in self.tillåtet and objekt is not None
                and not m.fråga and m.modus is Satsmodus.INDIKATIV
                and r.random() < 0.1):
            m = _med(m, fråga_om=r.choice(["subjekt", "objekt"]))

        # ── adverbial: nakna adverb och prepositionsfraser ────────────
        # De ligger i samma tuple men är två olika nivåer, och den ena får
        # inte smyga in den andra: ett naket adverb är nivå 8, en
        # prepositionsfras nivå 15.
        # BÅDA ÄR UTSMYCKNINGAR och hoppas därför över när begränsningen
        # tömt dem. Det var här den enda HÅRDA kraschen satt: ett naket
        # `None` i tupeln träffar renderarens `else`-gren, som läser
        # `.preposition` — en AttributeError utanför det `_rendera` fångar,
        # alltså rakt ut ur `föreslå`. Mätt: 176 av 1 500 tyska kandidater
        # på nivå 8, och varje anrop till `ordbok öva` föll på den.
        adverbial: list = []
        adverb = self.o.per_ordklass.get("Adverb", [])
        if ("adverbial" in self.tillåtet and adverb
                and r.random() < self.FÖRSÖK["adverbial"]):
            valt = self._välj(adverb)
            if valt is not None:
                adverbial.append(valt)
        prepositioner = self.o.per_ordklass.get("Preposition", [])
        if ("prepositionsfras" in self.tillåtet and prepositioner
                and r.random() < self.FÖRSÖK["prepositionsfras"]):
            möjliga = self.o.uppfyller([], "Substantiv")
            if möjliga:
                prep = self._välj(prepositioner)
                komplement_nf = self._nf(self._välj(möjliga),
                                         attributkandidater=[], djup=1)
                # BÅDA DELARNA KRÄVS. En prepositionsfras utan preposition
                # eller utan komplement är inte en halv fras, den är ingen.
                if prep is not None and komplement_nf is not None:
                    adverbial.append(Prepositionsfras(prep, komplement_nf))
        if adverbial:
            m = _med(m, adverbial=tuple(adverbial))

        # ── argumentbisats ────────────────────────────────────────────
        # Bara de verb vars mönster har Bisatsfras i frastypen. Bisatsen
        # byggs som en egen enkel sats — utan bisats i sin tur, och utan
        # fråga eller imperativ, som inte är argument.
        #
        # SATSEN ÄR OBJEKTET, den står inte bredvid det. Slotten den fyller
        # måste därför tömmas: "hon vet att han kom", inte "hon vet en typ
        # att han kom". Utan tömningen byggde samplaren just det.
        if ("bisats" in self.tillåtet and m.verb in self.o.bisatsverb
                and not m.fråga and m.modus is Satsmodus.INDIKATIV
                and m.fråga_om is None
                and r.random() < self.FÖRSÖK["bisats"]):
            # Bisatsen är en UTSMYCKNING på huvudsatsen men har en
            # obligatorisk slot inuti sig: utan verb finns ingen sats att
            # bygga. `self.o.verb[None]` gav KeyError — i `kandidat`, alltså
            # utanför det `_rendera` fångar.
            inre_verb = self._välj(list(self.o.verb))
            inre_krav = {} if inre_verb is None else self.o.verb[inre_verb]
            if (inre_verb is not None and "komplement" not in inre_krav
                    and "predikativ" not in inre_krav):
                inre_subjekt = None
                val = self.o.uppfyller(inre_krav.get("subjekt", []))
                if val:
                    inre_subjekt = self._nf(self._välj(val),
                                            attributkandidater=[], djup=1)
                if inre_subjekt is not None:
                    inre = Mening(inre_verb, inre_subjekt)
                    if "tempus" in self.tillåtet:
                        inre = _med(inre, tid=r.choice(list(Tidsreferens)))
                    slot = self.o.bisatsverb[m.verb]
                    m = _med(m, bisats=Bisats(r.choice(ARGUMENTSUBJUNKTIONER),
                                              inre),
                             **({slot: None} if slot in ("objekt", "io") else {}))
        return m


def _med(m: Mening, **fält) -> Mening:
    from dataclasses import replace
    return replace(m, **fält)
