"""Meningsspecifikationen — den språkoberoende beskrivningen av en mening.

Det här är objektet hela projektet vilar på: en mening definieras EN gång,
språkoberoende, och renderas sedan till valfritt språk. Specifikationen får
därför bara innehålla sådant som är sant om meningen oavsett språk.

Gränsdragningen i praktiken:

  HÖR HEMMA HÄR    vilket koncept som fyller vilken roll, bestämdhet,
                   numerus, tidsreferens, aspekt, vem som är koreferent
                   med vem.

  HÖR INTE HEMMA   kasus (tyska geben styr dativ, svenskan har inget kasus),
                   hjälpverbsval (fr être/avoir), ordföljd, genus på
                   adjektiv. Allt sådant följer av språket + databasen och
                   räknas ut av renderaren.

Testet är: skulle fältet kunna ha olika värde i två språk för samma mening?
Då hör det inte hemma här.

Tidsreferens och aspekt hålls isär eftersom språken delar upp dem olika.
"Förfluten + perfektiv" blir svenskt preteritum (gav), franskt passé
composé (a donné) och italienskt passato prossimo (ha dato) — samma
specifikation, tre olika celler. Mappningen ligger per språk i renderaren.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Bestämdhet(StrEnum):
    OBESTÄMD = "obestämd"
    BESTÄMD = "bestämd"


class Numerus(StrEnum):
    SG = "sg"
    PL = "pl"


class Tidsreferens(StrEnum):
    NUTID = "nutid"
    FÖRFLUTEN = "förfluten"
    FRAMTID = "framtid"


class Diates(StrEnum):
    """Aktiv eller passiv — och svenskan har två passiver.

    I en passiv sats står PATIENTEN som subjekt: "boken lästes". Specen
    behöver inget nytt fält för det; den som bygger meningen sätter helt
    enkelt patienten i subjektsslotten. Men validatorn måste veta det, så
    att den prövar subjektet mot verbets OBJEKTskrav i stället.

    PASSIV_HÄNDELSE finns för att svenskan skiljer "boken lästes" från
    "boken blev läst" — den senare betonar händelsen. Sex av sju språk har
    bara en passiv och renderar båda värdena likadant.
    """
    AKTIV = "aktiv"
    PASSIV = "passiv"
    PASSIV_HÄNDELSE = "passiv_händelse"


class Referentgenus(StrEnum):
    """Naturligt genus hos den som åsyftas — inte grammatiskt genus.

    Behövs när ett språk har könsskilda pronomen där svenskan inte har det:
    fr ils/elles, es ellos/ellas, es nosotros/nosotras. Vilket som väljs är
    en egenskap hos MENINGEN (vilka personer talar vi om?), inte hos
    språket, och hör därför hemma i specifikationen.

    Värdena matchar `Lexem.variant` så att renderaren kan skicka dem rakt
    igenom. Övriga variantetiketter hör INTE hemma här: familjär/artig är
    register och ligger utanför projektets scope, och reflexiv uttrycks
    redan med Nominalfras.possessiv_koreferent.
    """
    MASKULIN = "mask"
    FEMININ = "fem"


class Aspekt(StrEnum):
    """Perfektiv = avslutad händelse, imperfektiv = pågående eller vanemässig,
    perfekt = avslutad med relevans nu.

    Perfekt kombineras med tidsreferensen: nutid + perfekt ger "har läst",
    förfluten + perfekt ger "hade läst". Det är alltså inte ett tempus utan
    en aspekt som lägger sig ovanpå tempus.

    I franskan och italienskan sammanfaller nutid + perfekt med förfluten +
    perfektiv — passé composé och passato prossimo är samma form. Spanskan
    skiljer dem: "ha leído" mot "leyó".

    Svenskan och tyskan saknar morfologisk aspekt och ignorerar axeln.
    De romanska språken behöver den: "il donnait" (imperfekt) mot
    "il a donné" (passé composé) skiljer sig bara på aspekt.
    """
    PERFEKTIV = "perfektiv"
    PERFEKT = "perfekt"
    IMPERFEKTIV = "imperfektiv"


@dataclass(frozen=True, slots=True)
class Nominalfras:
    """En nominalfras: ett huvudord med eventuella bestämningar.

    `possessiv_koreferent` säger att ägaren är samma som satsens subjekt.
    Det är en egenskap hos MENINGEN, inte hos språket, och därför hör den
    hemma här — men bara svenskan realiserar den morfologiskt, med sin/hans.
    """
    koncept: str
    bestämdhet: Bestämdhet = Bestämdhet.OBESTÄMD
    numerus: Numerus = Numerus.SG
    attribut: tuple[str, ...] = ()
    possessiv: str | None = None
    possessiv_koreferent: bool = False
    referent: Referentgenus | None = None
    ägare: "Nominalfras | None" = None
    """Genitivattribut: "flickans bok". Ägaren är en egen nominalfras.

    Skilt från `possessiv`, som är ett pronomen (sin, hennes). Här är
    ägaren ett substantiv med egen bestämdhet och eget numerus, och den
    realiseras olika i de sju språken: morfologisk genitiv före huvudordet
    i sv/en, efter i de, preposition i fr/es/it, partikel i ja.
    """


@dataclass(frozen=True, slots=True)
class Prepositionsfras:
    """Preposition plus nominalfras: "i skolan", "med sin bror".

    Tyskan styr kasus på komplementet per preposition — "mit dem Buch" men
    "für das Buch" — och det ligger i MönsterKrav på prepositionens eget
    koncept. Övriga sex språk saknar kasus och behöver ingen rektion.
    """
    preposition: str
    komplement: Nominalfras


@dataclass(frozen=True, slots=True)
class Mening:
    """En hel sats. Slotnamnen matchar MönsterKrav.slot."""
    verb: str
    subjekt: Nominalfras
    objekt: Nominalfras | None = None
    io: Nominalfras | None = None
    predikativ: "str | Nominalfras | None" = None
    """Predikativ till kopulaverb: "hon är glad", "hon är läkare".

    En sträng är ett adjektivkoncept (Adjektivfras), en Nominalfras är en
    substantivfras. Bara fyra verbmönster tar predikativ — men två av dem
    är `vara` och `bli`, de mest frekventa verben i vilket språk som helst.

    Predikativa adjektiv böjs INTE som attributiva: svenskan använder den
    obestämda formen och kongruerar med subjektet ("hon är glad", "de är
    glada"), tyskan böjer inte alls ("sie ist glücklich").

    Ett predikativt substantiv står utan artikel i sv/de/fr/es/it — "hon är
    läkare", inte "hon är en läkare" — men med artikel i engelskan.
    """
    adverbial: "tuple[str | Prepositionsfras, ...]" = field(default=())
    komplement: str | None = None
    """Infinitivkomplement: "hon vill läsa", "hon börjar att läsa".

    Ett verbkoncept som styrs av huvudverbet och står i infinitiv. Första
    gången en mening innehåller ett andra verb.

    Markören framför infinitiven — att, to, zu, à, di — är LEXIKAL per verb
    och per språk, och ligger i MönsterKrav.preposition_koncept_id på det
    språkspecifika mönstret. Ingen rad = ren infinitiv, vilket är fallet för
    de flesta modalverb.
    """
    diates: Diates = Diates.AKTIV
    fråga: bool = False
    """Ja/nej-fråga: "läser flickan boken?"

    Låser upp noll nya ordformer men är den utökning som ställer störst krav
    på ORDFÖLJDEN — det är första gången satsens led byter plats i stället
    för att något läggs till.

    Sex olika strategier: verbet först i sv och de, do-omskrivning plus
    inversion i en, est-ce que i fr, enbart intonation och skiljetecken i
    es och it, och partikeln か sist i ja.
    """
    negerad: bool = False
    """Nekande sats: "flickan läser inte boken".

    Låser upp noll nya ordformer men mångdubblar antalet meningar som går
    att bygga av samma ord. Realiseras helt olika i de sju språken: ett
    satsadverbial i sv och de, do-omskrivning i en, en tvådelad klammer i
    fr, en preverbal partikel i es och it, och ren verbböjning i ja.
    """
    tid: Tidsreferens = Tidsreferens.NUTID
    aspekt: Aspekt = Aspekt.PERFEKTIV


class RenderingsFel(Exception):
    """Renderaren kan inte producera meningen.

    Kastas hellre än att gissa. En tyst felaktig mening är värre än ett
    stopp — hela poängen med det här projektet är att det renderade
    resultatet ska gå att lita på.
    """
