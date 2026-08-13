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
    """Perfektiv = avslutad händelse, imperfektiv = pågående eller vanemässig.

    Svenskan och tyskan saknar morfologisk aspekt och ignorerar axeln.
    De romanska språken behöver den: "il donnait" (imperfekt) mot
    "il a donné" (passé composé) skiljer sig bara på aspekt.
    """
    PERFEKTIV = "perfektiv"
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
class Mening:
    """En hel sats. Slotnamnen matchar MönsterKrav.slot."""
    verb: str
    subjekt: Nominalfras
    objekt: Nominalfras | None = None
    io: Nominalfras | None = None
    adverbial: tuple[str, ...] = field(default=())
    tid: Tidsreferens = Tidsreferens.NUTID
    aspekt: Aspekt = Aspekt.PERFEKTIV


class RenderingsFel(Exception):
    """Renderaren kan inte producera meningen.

    Kastas hellre än att gissa. En tyst felaktig mening är värre än ett
    stopp — hela poängen med det här projektet är att det renderade
    resultatet ska gå att lita på.
    """
