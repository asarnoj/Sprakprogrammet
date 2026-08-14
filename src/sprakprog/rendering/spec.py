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


class Grad(StrEnum):
    """Komparationsgrad på predikativet: "stor", "större", "störst".

    Realiseras syntetiskt eller perifrastiskt beroende på både SPRÅK och
    ORD. Tyskan är alltid syntetisk (größer). Franskan alltid perifrastisk
    (plus grand). Svenskan, engelskan, spanskan och italienskan blandar:
    "större" men "mer intressant", "bigger" men "more interesting".

    Renderaren avgör det på datan — finns komparativcellen används den,
    annars byggs frasen med komp_mer.
    """
    POSITIV = "positiv"
    KOMPARATIV = "komparativ"
    SUPERLATIV = "superlativ"


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


class Satsmodus(StrEnum):
    """Satsens modus. Imperativen är en uppmaning: "läs boken!".

    Imperativen har inget eget subjektsfält. Subjektet står kvar och namnger
    den TILLTALADE — det är därifrån person och numerus kommer, precis som i
    alla andra satser, och det är därför validatorn kan pröva tilltalet mot
    verbets subjektskrav utan att veta något om imperativ. Renderaren tiger
    om subjektet i stället för att specen ska tappa det.

    Bara tyskan säger ändå ut pronomenet, och bara i två av sina fyra
    former: "Lesen Sie!" och "Lesen wir!" — 2sg och 2pl står nakna som i de
    andra språken.

    Modus är en axel som kommer att växa. Konjunktiv och konditionalis
    ligger som ifyllda celler i fr/es/it och är det största onådda blocket
    efter tyskans attributiva komparation; de blir egna värden här när
    bisatserna finns. Därför en enum och inte ett `imperativ: bool`.
    """
    INDIKATIV = "indikativ"
    IMPERATIV = "imperativ"


#: Subjektskonceptet i en imperativsats → tilltalsform. Fyra tilltal räcker:
#: imperativens paradigm är som störst fem celler (es), och den femte —
#: ustedes — är samma tilltal som `artig` i plural, vilket numerus redan
#: säger. Ett subjekt utanför tabellen är inget tilltal, och att uppmana
#: någon frånvarande är inte en imperativ utan en önskan.
TILLTAL = {
    "pronomen_2sg": "2sg",
    "pronomen_2pl": "2pl",
    "pronomen_2sg_formal": "artig",
    "pronomen_1pl": "1pl",
}


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
    frågedeterminant: str | None = None
    """Frågande bestämning: "vilken bok", "hur många böcker".

    Tar artikelns plats precis som en possessiv gör, och styr adjektivet
    likadant. Skilt från `Mening.fråga_om` som ersätter HELA ledet med vem
    eller vad — här står huvudordet kvar och det är valet mellan exemplar
    som efterfrågas. Meningen måste ändå säga vilken SLOT frågan gäller,
    så att renderaren vet vad som ska flyttas först.
    """
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
class Bisats:
    """Subjunktion plus en hel sats: "att han kom", "när hon läste boken".

    Den första konstruktionen där `Mening` innehåller en `Mening`. Allt som
    går att säga i en huvudsats går därmed att säga i en bisats — tempus,
    negation, passiv, perfekt — utan att något behöver läggas till.

    Bisatsen fyller två helt olika roller, och skillnaden ligger i
    subjunktionen, inte i strukturen:

      ARGUMENT    "hon vet ATT han kom" — satsen ÄR objektet. Bara de 22
                  verb vars MönsterKrav har frastyp & 32 tar en sådan.

      ADVERBIAL   "hon läste NÄR han kom" — satsen är en omständighet, och
                  vilket verb som helst tar den. Ligger därför i
                  `adverbial` bredvid Prepositionsfras, inte i `bisats`.

    Ordföljden i bisatsen är INTE densamma som i huvudsatsen i två av sju
    språk: tyskan flyttar det finita verbet sist, svenskan flyttar
    satsadverbialet före det. Japanskan byter dessutom register — bisatsen
    står alltid i enkel form, aldrig artig, och det är grammatik och inte
    stil.
    """
    subjunktion: str
    sats: "Mening"


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
    adverbial: "tuple[str | Prepositionsfras | Bisats, ...]" = field(default=())
    komplement: str | None = None
    """Infinitivkomplement: "hon vill läsa", "hon börjar att läsa".

    Ett verbkoncept som styrs av huvudverbet och står i infinitiv. Första
    gången en mening innehåller ett andra verb.

    Markören framför infinitiven — att, to, zu, à, di — är LEXIKAL per verb
    och per språk, och ligger i MönsterKrav.preposition_koncept_id på det
    språkspecifika mönstret. Ingen rad = ren infinitiv, vilket är fallet för
    de flesta modalverb.
    """
    grad: Grad = Grad.POSITIV
    jämförelse: "Nominalfras | None" = None
    """Jämförelseled: "boken är större ÄN huset". Kräver grad=KOMPARATIV."""
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
    bisats: "Bisats | None" = None
    """Argumentbisats: "hon vet att han kom".

    Satsen fyller verbets objekt- eller kommunikatslot — vilken av dem
    avgörs av verbets MönsterKrav och spelar ingen roll för ordföljden, så
    renderaren behöver inte veta vilken. Validatorn gör det.
    """
    fråga_om: str | None = None
    """Vad frågan gäller — gör meningen till en wh-fråga.

    Två sorters värden, och skillnaden är grammatisk och inte godtycklig:

      "subjekt" / "objekt" / "io"   ett ARGUMENT efterfrågas. Slotten står
                                    kvar i specen med svaret i sig ("vem
                                    läser boken?" byggs ur "flickan läser
                                    boken"), och renderaren byter ut ordet
                                    mot vem eller vad. Vilketdera avgörs på
                                    MÄNSKLIG-biten hos det som efterfrågas,
                                    inte på slotten.

      "frågadverb_tid" m.fl.        en OMSTÄNDIGHET efterfrågas. Inget
                                    argument tas bort; adverbet läggs till.

    Att svaret ligger kvar i specen är inte en tillfällighet: en fråga och
    dess svar är samma mening, och en inlärningsapp behöver båda.

    Sex av sju språk flyttar frågeordet först. Japanskan flyttar det inte
    alls — 何 står kvar där objektet stod. Och SUBJEKTSfrågan inverterar
    inte i något språk, eftersom frågeordet redan står på subjektets plats:
    "vem läser boken?" mot "vad läser hon?".
    """
    modus: Satsmodus = Satsmodus.INDIKATIV
    """Satsmodus. IMPERATIV gör meningen till en uppmaning: "läs boken!".

    Imperativen har inget tempus — en uppmaning gäller framåt per definition
    — så `tid` och `aspekt` ignoreras när modus är IMPERATIV i stället för
    att tyst producera en form som inte finns.
    """


class RenderingsFel(Exception):
    """Renderaren kan inte producera meningen.

    Kastas hellre än att gissa. En tyst felaktig mening är värre än ett
    stopp — hela poängen med det här projektet är att det renderade
    resultatet ska gå att lita på.
    """


#: De argumentslottar en wh-fråga kan efterfråga. Adverbialfrågor namnger
#: i stället frågadverbets koncept, som ju inte har någon slot att peka på.
FRÅGESLOTTAR = ("subjekt", "objekt", "io")


def slutar(m: "Mening") -> str:
    """Satsens skiljetecken. Frågan vinner över uppmaningen.

    En imperativ kan inte samtidigt vara en ja/nej-fråga — "läser boken!?"
    är ingen sats — men specen kan bära båda flaggorna, och då är frågan den
    som syns i ordföljden. Spanskans inledande ¡ och ¿ hanteras i sin egen
    renderare; det här är tecknet på slutet.
    """
    if m.fråga or m.fråga_om is not None:
        return "?"
    return "!" if m.modus is Satsmodus.IMPERATIV else "."


def tilltal(m: "Mening", språk: str, stöds: tuple[str, ...]) -> str:
    """Vem imperativen riktar sig till, läst ur subjektet.

    `stöds` är de tilltal språket har en form för. Svenskan och engelskan
    saknar 1pl-imperativ helt — "låt oss läsa", "let's read" är omskrivningar
    med ett verb databasen inte har — och ska säga det i stället för att
    tyst rendera något annat.
    """
    if m.subjekt.koncept not in TILLTAL:
        raise RenderingsFel(
            f"{språk}: imperativens subjekt måste vara den tilltalade "
            f"({', '.join(TILLTAL)}), inte {m.subjekt.koncept!r}")
    tal = TILLTAL[m.subjekt.koncept]
    if tal not in stöds:
        raise RenderingsFel(
            f"{språk}: saknar imperativform för {tal} — språket har bara "
            f"{', '.join(stöds)} och uttrycker resten med en omskrivning")
    return tal
