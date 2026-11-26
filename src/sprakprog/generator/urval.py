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

    #: Hur ofta samplaren FÖRSÖKER med en konstruktion. Det här är inga
    #: inställningar och inga trösklar: sökningen tar bästa av tusen
    #: kandidater, så en frekvens behöver bara vara stor nog att
    #: konstruktionen dyker upp bland kandidaterna. Poängfunktionen avgör
    #: sedan vad som faktiskt visas. Att sätta någon av dem till noll är
    #: däremot att stänga av en hel nivå — vilket var precis vad som hade
    #: hänt för possessiv, adverbial, genitiv, prepositionsfras och bisats.
    FÖRSÖK = {"possessiv": 0.15, "genitiv": 0.10, "adverbial": 0.15,
              "prepositionsfras": 0.20, "bisats": 0.25}

    def _nf(self, koncept: str, *, attributkandidater: list[str],
            djup: int = 0) -> Nominalfras:
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
            attribut = (Attribut(r.choice(attributkandidater), grad),)

        # Possessiv och genitivägare tar ARTIKELNS plats — "mitt hus", inte
        # "det mitt hus". Frasen är bestämd ändå (spec.bestämd_fras), så
        # bestämdheten sätts tillbaka till obestämd för att inte be
        # renderaren om både artikel och ägare.
        possessiv = ägare = None
        possessiva = self.o.per_ordklass.get("Possessiv", [])
        if ("possessiv" in self.tillåtet and possessiva
                and r.random() < self.FÖRSÖK["possessiv"]):
            possessiv, best = r.choice(possessiva), Bestämdhet.OBESTÄMD
        elif ("genitiv" in self.tillåtet and djup == 0
                and r.random() < self.FÖRSÖK["genitiv"]):
            # Ägaren är en egen nominalfras, och den byggs på DJUP 1 så att
            # den inte i sin tur får en ägare. "Kattens hunds ben" är
            # grammatiskt men ingen övningsmening.
            möjliga = self.o.uppfyller([], "Substantiv")
            if möjliga:
                ägare = self._nf(r.choice(möjliga), attributkandidater=[],
                                 djup=1)
                ägare = replace(ägare, bestämdhet=Bestämdhet.BESTÄMD)
                best = Bestämdhet.OBESTÄMD
        return Nominalfras(koncept, best, num, attribut,
                           possessiv=possessiv, ägare=ägare)

    def kandidat(self, *, kring: str | None = None) -> Mening | None:
        """En kandidatmening, byggd runt `kring` om det går."""
        r = self.rng
        adjektiv = self.o.per_ordklass.get("Adjektiv", [])

        # Verbet: det som ska prövas, eller ett som tar målordet
        if kring and self.o.ordklass.get(kring) == "Verb" and kring in self.o.verb:
            verb = kring
        elif kring and self.o.ordklass.get(kring) in self.o.FRASHUVUD:
            möjliga = self.o.verb_för(kring)
            verb = r.choice(möjliga) if möjliga else None
        else:
            verb = r.choice(list(self.o.verb)) if self.o.verb else None
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
            return self._nf(r.choice(val), attributkandidater=adjektiv)

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
            komplement = r.choice(list(self.o.verb))

        # Samma sak för kopulan: "Sie ist." är ingen mening. Ett verb med
        # predikativslot MÅSTE få ett predikativ, och det får vara adjektiv
        # eller substantiv — mönstret säger vilket.
        predikativ = None
        if "predikativ" in slotkrav:
            if "predikativ" not in self.tillåtet:
                return None
            if adjektiv and r.random() < 0.7:
                predikativ = r.choice(adjektiv)
            else:
                val = self.o.uppfyller([], "Substantiv")
                if not val:
                    return None
                predikativ = Nominalfras(r.choice(val))
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
        adverbial: list = []
        adverb = self.o.per_ordklass.get("Adverb", [])
        if ("adverbial" in self.tillåtet and adverb
                and r.random() < self.FÖRSÖK["adverbial"]):
            adverbial.append(r.choice(adverb))
        prepositioner = self.o.per_ordklass.get("Preposition", [])
        if ("prepositionsfras" in self.tillåtet and prepositioner
                and r.random() < self.FÖRSÖK["prepositionsfras"]):
            möjliga = self.o.uppfyller([], "Substantiv")
            if möjliga:
                adverbial.append(Prepositionsfras(
                    r.choice(prepositioner),
                    self._nf(r.choice(möjliga), attributkandidater=[], djup=1)))
        if adverbial:
            m = _med(m, adverbial=tuple(adverbial))

        # ── argumentbisats ────────────────────────────────────────────
        # Bara de verb vars mönster har Bisatsfras i frastypen. Bisatsen
        # byggs som en egen enkel sats — utan bisats i sin tur, och utan
        # fråga eller imperativ, som inte är argument.
        if ("bisats" in self.tillåtet and m.verb in self.o.bisatsverb
                and not m.fråga and m.modus is Satsmodus.INDIKATIV
                and m.fråga_om is None
                and r.random() < self.FÖRSÖK["bisats"]):
            inre_verb = r.choice(list(self.o.verb))
            inre_krav = self.o.verb[inre_verb]
            if "komplement" not in inre_krav and "predikativ" not in inre_krav:
                inre_subjekt = None
                val = self.o.uppfyller(inre_krav.get("subjekt", []))
                if val:
                    inre_subjekt = self._nf(r.choice(val),
                                            attributkandidater=[], djup=1)
                if inre_subjekt is not None:
                    inre = Mening(inre_verb, inre_subjekt)
                    if "tempus" in self.tillåtet:
                        inre = _med(inre, tid=r.choice(list(Tidsreferens)))
                    m = _med(m, bisats=Bisats(r.choice(ARGUMENTSUBJUNKTIONER),
                                              inre))
        return m


def _med(m: Mening, **fält) -> Mening:
    from dataclasses import replace
    return replace(m, **fält)
