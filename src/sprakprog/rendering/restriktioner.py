"""Semantisk validering av en meningsspecifikation.

Renderaren kontrollerar ingenting — den bygger den mening den får. Det är
rätt arbetsdelning: renderaren svarar för att formen blir korrekt, den här
modulen för att innehållet är välformat.

Validering sker på SPECEN, inte på den renderade strängen, och därför en
enda gång för alla sju språk. `MönsterKrav` hänger på det universella
mönstret (`Mönster.språk IS NULL`), som är språkoberoende per definition.

Matchningen är disjunktiv normalform:

    bitar inom EN rad  =  OCH   (konceptet måste ha alla)
    flera RADER        =  ELLER (minst en rad måste uppfyllas)

OCH-delen var odefinierad fram till 2026-08-12 — BITMASK.md §11 sade att
masken används för att matcha, men aldrig hur. ELLER-delen tillkom när tre
krav i rad visade sig omöjliga att uttrycka med enbart OCH: "bryta" tar
KONSTRUERAD eller KROPPSDEL, "blanda" ÄTBAR eller DRICKBAR, "snabb"
RÖRELSE eller ANIMAT. Ingen av dem har en gemensam bit, och att välja en
bredare bit i stället släppte igenom för mycket.

Vad den här modulen INTE gör: bedömer rimlighet. `Flickan köpte en dörr`
passerar, och ska göra det enligt scope-beslutet. Kategorifel stoppas,
osannolikhet inte.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .spec import (
    Bestämdhet, Bisats, Diates, Mening, Nominalfras, Numerus, Tidsreferens,
    attribut_med_grad,
)

# docs/BITMASK.md §11. Bara för läsbara felmeddelanden.
BITNAMN = {
    1: "ANIMAT", 2: "KONKRET", 4: "ABSTRAKT", 8: "ÄTBAR", 16: "PLATS",
    32: "MÄNSKLIG", 64: "RÖRELSE", 128: "RIKTNING", 256: "HÄNDELSE",
    512: "TID", 1024: "INSTRUMENT", 2048: "KOMMUNIKAT", 4096: "DRICKBAR",
    8192: "KROPPSDEL", 16384: "KLÄDESPLAGG", 32768: "INREDNING",
    65536: "NATURFENOMEN",
    # Tillagda 2026-08-12, se paradigm/RESTRIKTIONER.md
    131072: "ÖVERLÅTBAR", 262144: "HANTERBAR", 524288: "ÖPPNINGSBAR",
}


def _slå_ihop(alternativ: list[int]) -> int:
    """Bara för felmeddelandet: visa alla alternativ i en mask."""
    mask = 0
    for a in alternativ:
        mask |= a
    return mask


def _etiketter(mask: int | None) -> str:
    if not mask:
        return "—"
    return "+".join(namn for bit, namn in BITNAMN.items() if mask & bit)


# Tidsreferens → tempusbit ur _legend.yaml. Adverbets tempuskrav är en
# mängd tillåtna värden, så matchningen är medlemskap och inte OCH.
TIDSBIT = {
    Tidsreferens.NUTID: 2,
    Tidsreferens.FÖRFLUTEN: 4,
    Tidsreferens.FRAMTID: 64,
}
TIDSNAMN = {2: "nutid", 4: "förfluten", 64: "framtid"}

# MönsterKrav.frastyp, docs/BITMASK.md: Bisatsfras är bit 32.
BISATSFRAS = 32


@dataclass(frozen=True, slots=True)
class Brott:
    """Ett krav som specen inte uppfyller."""
    slot: str
    koncept: str
    krav: int
    faktisk: int | None

    def __str__(self) -> str:
        if self.slot == "valens":
            return (f"verb={self.koncept}: fyller ingen av verbets ramar "
                    f"(valens {self.krav}, docs/BITMASK.md §8)")
        if self.slot == "bisats":
            return (f"verb={self.koncept}: tar ingen bisats — inget av "
                    f"verbets mönsterkrav har frastyp Bisatsfras")
        if self.slot == "deixis":
            return (f"{self.koncept} står i både subjekt och objekt: "
                    f"{self.krav}:a person syftar på talsituationen, så de "
                    f"två leden kan inte vara olika — och koreferens kräver "
                    f"ett reflexivt verb som specen inte bad om")
        if self.slot == "oräknebar":
            return (f"oräknebar={self.koncept}: ordet räknas inte, så det tar "
                    f"varken obestämd artikel, plural eller räkneord — «en "
                    f"tid», «two airs» och «varje vin» finns inte")
        if self.slot == "självständig":
            return (f"självständig={self.koncept}: huvudordet skrivs inte ut "
                    f"och står ingen annanstans i satsen — «min» utan «min "
                    f"bok» någonstans gör konceptet omöjligt att återskapa, "
                    f"och specen bär då ett val som ingenting hänger på")
        if self.slot == "ägare":
            return (f"ägare={self.koncept}: en självständig possessiv kan inte "
                    f"äga en annan fras — engelskans «yours older sister» finns "
                    f"inte, och ägarens eget huvudord skrivs aldrig ut, så "
                    f"specen bär ett led som ingenting hänger på")
        if self.slot == "tempus":
            tillåtna = "/".join(n for b, n in TIDSNAMN.items() if self.krav & b)
            return (f"adverbial={self.koncept}: kräver {tillåtna}, "
                    f"meningen är {TIDSNAMN.get(self.faktisk, '?')}")
        if self.faktisk is None:
            return (f"{self.slot}={self.koncept}: saknar semantik helt, "
                    f"kravet {_etiketter(self.krav)} går inte att pröva")
        saknas = self.krav & ~self.faktisk
        return (f"{self.slot}={self.koncept}: kräver {_etiketter(self.krav)}, "
                f"har {_etiketter(self.faktisk)} — saknar {_etiketter(saknas)}")


class Validator:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self._krav: dict[str, dict[str, int]] = {}
        self._semantik: dict[str, int | None] = {}
        self._attributkrav: dict[str, list[int]] = {}
        self._tempuskrav: dict[str, int | None] = {}
        self._person: dict[str, int | None] = {}
        self._bisatsverb: dict[str, bool] = {}

    def krav_för(self, verb: str) -> dict[str, list[int]]:
        """Slot → lista av alternativa bitmasker. Flera = ELLER."""
        if verb not in self._krav:
            rader = self.conn.execute(
                """SELECT mk.slot, mk.tagg FROM Mönster m
                   JOIN Koncept k ON k.id = m.koncept_id
                   JOIN MönsterKrav mk ON mk.mönster_id = m.id
                   WHERE k.nyckel = ? AND m.språk IS NULL
                     AND mk.tagg IS NOT NULL""", (verb,)).fetchall()
            ut: dict[str, list[int]] = {}
            for r in rader:
                ut.setdefault(r["slot"], []).append(r["tagg"])
            self._krav[verb] = ut
        return self._krav[verb]

    @staticmethod
    def _uppfyller(faktisk: int | None, alternativ: list[int]) -> bool:
        """Minst ETT alternativ måste vara helt uppfyllt."""
        if faktisk is None:
            return False
        return any(faktisk & krav == krav for krav in alternativ)

    def semantik(self, koncept: str) -> int | None:
        if koncept not in self._semantik:
            rad = self.conn.execute(
                "SELECT semantik FROM Koncept WHERE nyckel = ?", (koncept,)).fetchone()
            self._semantik[koncept] = rad["semantik"] if rad else None
        return self._semantik[koncept]

    def person(self, koncept: str) -> int | None:
        """Grammatisk person, eller None för allt som inte har någon."""
        if koncept not in self._person:
            rad = self.conn.execute(
                "SELECT person FROM Koncept WHERE nyckel = ?",
                (koncept,)).fetchone()
            self._person[koncept] = rad["person"] if rad else None
        return self._person[koncept]

    def _deixisbrott(self, m: Mening) -> list[Brott]:
        """Samma 1:a eller 2:a person i två argumentled är inte språk.

        DET HÄR ÄR ETT KATEGORIFEL OCH INTE EN OSANNOLIKHET, vilket är
        skälet att det hör hemma i den här modulen alls. `Flickan köpte en
        dörr` passerar och ska göra det. `Je m'ai` passerar inte, för det är
        inte franska.

        Skälet är deixis. Första och andra person är förankrade i
        talsituationen: talaren är talaren, oavsett var i satsen ledet står.
        Två sådana led kan alltså inte syfta på olika personer, och den
        påtvingade koreferensen kräver ett reflexivt verb — en annan spec än
        den som ställdes.

        OCH RENDERAREN BEKRÄFTAR DET. Franskans objektsklitikum och
        reflexivklitikum är SAMMA STRÄNG i första och andra person — se
        `REFLEXIVKLITIKA` i `romansk.py`: *"Första och andra lånar det
        vanliga objektsklitikat — `je me lave` är samma `me` som i `il me
        voit`"*. `Tu te remercies` går alltså inte att skilja från "du
        tackar dig själv", fast specen bad om ett vanligt objekt. Meningen
        är inte underlig utan OUTTRYCKBAR.

        Det avsedda sättet att få en reflexiv är ett annat: verbets lemma är
        lexikalt reflexivt (`se réveiller`), och `reflexivklitikum` sätter
        tillbaka pronomenet. Kollisionen här är ingen designad reflexiv utan
        en strängsammanträffande.

        TREDJE PERSON OCH SUBSTANTIV ÄR FRIA och släpps igenom, av exakt
        samma skäl sett från andra hållet: tredje person HAR egna former, så
        `Il l'a` får `le` och inte `se` och läses som icke-koreferent — "han
        har den", fullgod franska och det specen menade. `Un enfant coûte un
        enfant` handlar om två olika barn: korrekt men underligt, och
        underligt ligger utanför modulens uppdrag.

        Regeln är språkoberoende, vilket den måste vara: validatorn körs en
        gång på specen för alla sju språken. Deixis fungerar likadant i dem
        alla — `jag har mig`, `I have me`, `ich habe mich` kräver alla ett
        reflexivt verb.

        MÄTT, OCH URVALET ÄR DET SOM GÖR DET STORT. I råa kandidater är
        kollisionen försvinnande: 4 av 15 800 på nivå 6, som mest 0,08 %.
        Men generatorn väljer bland kandidaterna efter vilka kort som
        förfaller, och på en färsk kurs är den mängden några få pronomen —
        då blir kollisionen det bästa draget om och om igen. Mätt genom hela
        valvägen på en nollställd fransk kurs, nivå 3:

            regeln av    21 av 42 valda meningar bröt mot deixis
            regeln på     0 av 42

        Halva dagen. Exemplen var `Tu te remercies` och `Nous nous
        remerciions`. Julius logg visade samma sak från andra hållet: 6 av
        42 flaggade som `subjekt = objekt`, varav fyra av den här sorten —
        `Je m'ai`, `Tu t'as`, `Vous vous coûtez`, `On nous coûte`. De två
        övriga var `Il l'a` och `Elle la coûte`, alltså tredje person, och
        de ska inte stoppas.

        Dagen svälter inte, och regeln kostar ingenting: 20 meningar på
        nivå 3 tog 3,6 s utan regeln och 2,7 s med, båda byggde alla 20 och
        ingen gav upp. Att avvisa en spec är billigare än att rendera den.
        """
        ut = []
        led = [(namn, nf) for namn, nf in
               (("subjekt", m.subjekt), ("objekt", m.objekt), ("io", m.io))
               if nf is not None]
        for i, (namn_a, a) in enumerate(led):
            for namn_b, b in led[i + 1:]:
                if a.koncept != b.koncept:
                    continue
                p = self.person(a.koncept)
                if p in (1, 2):
                    ut.append(Brott("deixis", a.koncept, p, None))
        return ut

    def attributkrav(self, koncept: str) -> list[int]:
        """Adjektivets alternativa krav på huvudordet. Tom lista = inget krav."""
        if koncept not in self._attributkrav:
            self._attributkrav[koncept] = [
                r["tagg"] for r in self.conn.execute(
                    """SELECT a.tagg FROM Attributkrav a
                       JOIN Koncept k ON k.id = a.koncept_id
                       WHERE k.nyckel = ?""", (koncept,))]
        return self._attributkrav[koncept]

    def tempuskrav(self, koncept: str) -> int | None:
        if koncept not in self._tempuskrav:
            rad = self.conn.execute(
                "SELECT tempuskrav FROM Koncept WHERE nyckel = ?",
                (koncept,)).fetchone()
            self._tempuskrav[koncept] = rad["tempuskrav"] if rad else None
        return self._tempuskrav[koncept]

    def _attributbrott(self, slot: str, nf: Nominalfras) -> list[Brott]:
        """Får adjektiven beskriva huvudordet?

        Kravet går åt motsatt håll mot verbets: adjektivet begränsar vad det
        får fästa på, i stället för att öppna en plats.
        """
        huvud = self.semantik(nf.koncept)
        ut = []
        for a in nf.attribut:
            # `attribut` blev en union när graden tillkom. Att glömma det här
            # var samma fel som med Prepositionsfras i adverbial-slotten:
            # validatorn skickade dataklassen till ett uppslag som väntar sig
            # en sträng, och kraschade först när någon validerade en mening
            # som faktiskt hade en.
            attribut = attribut_med_grad(a).koncept
            alternativ = self.attributkrav(attribut)
            if alternativ and not self._uppfyller(huvud, alternativ):
                ut.append(Brott(f"{slot}.attribut={attribut}", nf.koncept,
                                alternativ[0] if len(alternativ) == 1
                                else _slå_ihop(alternativ), huvud))
        return ut

    @staticmethod
    def _nominalfraser(m: Mening):
        """Varje nominalfras i satsen, också i bisatser och i ägarled."""
        att_gå = [m.subjekt, m.objekt, m.io, m.jämförelse]
        if isinstance(m.predikativ, Nominalfras):
            att_gå.append(m.predikativ)
        for a in m.adverbial:
            if not isinstance(a, str):
                att_gå.append(getattr(a, "komplement", None))
        while att_gå:
            nf = att_gå.pop()
            if nf is None:
                continue
            yield nf
            att_gå.append(nf.ägare)
        for b in (m.bisats, *(a for a in m.adverbial if isinstance(a, Bisats))):
            if b is not None:
                yield from Validator._nominalfraser(b.sats)

    def räknebar(self, koncept: str) -> int | None:
        if ("räknebar", koncept) not in self._semantik:
            rad = self.conn.execute(
                "SELECT räknebar FROM Koncept WHERE nyckel = ?",
                (koncept,)).fetchone()
            self._semantik[("räknebar", koncept)] = rad["räknebar"] if rad else None
        return self._semantik[("räknebar", koncept)]

    def _oräknebart_exemplar(self, m: Mening) -> list[Brott]:
        """Ett oräknebart ord räknas inte: «en tid», «two airs», «varje vin».

        `kontrollera_naken` i uppslaget prövar det omvända — att en NAKEN
        singular kräver ett oräknebart ord — men ingenting hindrade att ett
        oräknebart ord fick obestämd artikel, plural eller räkneord. «A time
        stands.» kom ur introfasen så snart lånekorten började återanvändas,
        och den är fel i båda språken.

        Bestämd form går bra: «tiden», «the time» pekar ut en bestämd mängd
        och räknar inte exemplar.
        """
        brott = []
        for nf in self._nominalfraser(m):
            if self.räknebar(nf.koncept) != 0:
                continue
            räknat = (nf.räkneord is not None
                      or nf.numerus is not Numerus.SG
                      or (nf.bestämdhet is Bestämdhet.OBESTÄMD
                          and nf.possessiv is None and nf.demonstrativ is None
                          and nf.kvantifikator is None and nf.ägare is None))
            if räknat:
                brott.append(Brott("oräknebar", nf.koncept, 0, None))
        return brott

    def _utan_antecedent(self, m: Mening) -> list[Brott]:
        """En självständig possessiv måste ha sitt huvudord i samma sats.

        `självständig` skriver inte ut huvudordet: «boken är min» säger
        `min`, inte `min bok`. Står konceptet ingen annanstans i satsen
        försvinner det ur meningen helt — och då är det ett FRITT VÄRDE UTAN
        VERKAN. «Min ser.» byggd av hund och byggd av katt ger samma
        källmening, samma målmening och samma kort; specen bär ett val som
        ingenting hänger på.

        Det är samma sorts redundans som kartan annars vaktar mot, och den
        kostar dubbelt: sökningen går igenom likvärdiga specar, och
        användaren får en mening vars innehåll ingen kan återskapa.

        «Boken är min» duger, för där står boken. «Min ser» gör det inte.
        """
        fraser = list(self._nominalfraser(m))
        brott = []
        for i, nf in enumerate(fraser):
            if not nf.självständig:
                continue
            if not any(a.koncept == nf.koncept and not a.självständig
                       for j, a in enumerate(fraser) if j != i):
                brott.append(Brott("självständig", nf.koncept, 0, None))
        return brott

    def _självständig_ägare(self, m: Mening) -> list[Brott]:
        """En självständig possessiv kan inte vara ägare åt en annan fras.

        `självständig` betyder att possessiven ÄR frasen: «boken är min» säger
        `min`, inte `min bok`, och huvudordet skrivs inte ut. Står den i ett
        ÄGARLED blir nästlingen osynlig, för ägarens huvudord renderas aldrig —
        och det som skrivs ut har ett led för lite:

            subjekt = storasyster, ägare = (självständig, poss_2sg_formal)
            svenskan   «Er storasyster ser.»          ett storasyster, specen har två
            engelskan  «Yours older sister sees.»     fel form

        Engelskan skiljer formerna: `your` framför ett substantiv, `yours`
        fristående (species 1 och 2 i `Former`). Genitiv av `yours` finns inte —
        ägandet sägs med den attributiva formen, «your older sister». Svenskan
        renderar rätt av en slump, eftersom `er` är båda formerna.

        DET ÄR SAMMA FRIA VÄRDE UTAN VERKAN som `_utan_antecedent` vaktar mot,
        och den regeln räcker inte: där är ägarens koncept samma som
        huvudordets, så antecedenten finns och kravet uppfylls degenererat.

        Kortet blir inte oprövbart. `oregelbunden:poss_2sg_formal/best` prövas
        predikativt i stället — «Luft är er.» → «Air is yours.» — och det är den
        enda ställning den självständiga formen har. Mätt 2026-10-06: tio av tio
        meningar för kortet gick genom ägarledet, alla med fel engelsk form.
        """
        brott = []
        for nf in self._nominalfraser(m):
            ägare = getattr(nf, "ägare", None)
            if ägare is not None and ägare.självständig:
                brott.append(Brott("ägare", ägare.koncept, 0, None))
        return brott

    def validera(self, m: Mening) -> list[Brott]:
        """Alla krav specen bryter mot. Tom lista = välformad."""
        krav = self.krav_för(m.verb)
        brott: list[Brott] = []

        # I passiv sats är subjektet semantiskt objekt, så det ska prövas
        # mot objektskravet. Annars skulle "boken lästes" avvisas för att
        # böcker inte är animata — läsa kräver animat SUBJEKT, men här är
        # subjektet det lästa.
        if m.diates is not Diates.AKTIV and "objekt" in krav:
            krav = {**krav, "subjekt": krav["objekt"]}

        for slot, nf in (("subjekt", m.subjekt), ("objekt", m.objekt),
                         ("io", m.io)):
            if nf is None or slot not in krav:
                continue
            alternativ = krav[slot]
            faktisk = self.semantik(nf.koncept)
            if not self._uppfyller(faktisk, alternativ):
                brott.append(Brott(
                    slot, nf.koncept,
                    alternativ[0] if len(alternativ) == 1
                    else _slå_ihop(alternativ), faktisk))

        for slot, nf in (("subjekt", m.subjekt), ("objekt", m.objekt),
                         ("io", m.io)):
            if nf is not None:
                brott += self._attributbrott(slot, nf)

        brott += self._utan_antecedent(m)
        brott += self._självständig_ägare(m)
        brott += self._oräknebart_exemplar(m)

        brott += self._deixisbrott(m)

        # Adverbial mot meningens tidsreferens. Medlemskap, inte OCH.
        # Bara ADVERB har tempuskrav — "igår" kräver förfluten tid. En
        # prepositionsfras eller bisats har inget, och slås inte upp: att
        # skicka dataklassen till uppslaget kraschade tyst i valideringen
        # ända sedan prepositionsfraserna byggdes, eftersom ingen validerade
        # en mening som hade en.
        tidsbit = TIDSBIT[m.tid]
        for adverbial in m.adverbial:
            if isinstance(adverbial, Bisats):
                brott += self._bisatsbrott(m, adverbial, argument=False)
                continue
            if not isinstance(adverbial, str):
                continue
            tillåtna = self.tempuskrav(adverbial)
            if tillåtna is not None and not tillåtna & tidsbit:
                brott.append(Brott("tempus", adverbial, tillåtna, tidsbit))

        if m.bisats is not None:
            brott += self._bisatsbrott(m, m.bisats, argument=True)

        return brott

    def _bisatsbrott(self, m: Mening, b: Bisats, argument: bool) -> list[Brott]:
        """Bisatsen prövas som en egen mening — den ÄR en.

        En argumentbisats kräver dessutom att verbet öppnar en plats för
        den: `MönsterKrav.frastyp & 32`. En adverbialbisats gör inte det,
        eftersom vilket verb som helst kan ha en omständighet.
        """
        brott: list[Brott] = []
        if argument and not self.tillåter_bisats(m.verb):
            brott.append(Brott("bisats", m.verb, BISATSFRAS, None))
        return brott + self.validera(b.sats)

    def tillåter_bisats(self, verb: str) -> bool:
        """Har verbet en slot som accepterar en hel sats?

        22 verb har det, fördelade på objekt, kommunikat och komplement.
        Vilken slot spelar ingen roll för ordföljden i något av de sju
        språken, så renderaren behöver inte veta — bara att den finns.
        """
        if verb not in self._bisatsverb:
            rad = self.conn.execute(
                """SELECT 1 FROM Mönster m
                   JOIN Koncept k ON k.id = m.koncept_id
                   JOIN MönsterKrav mk ON mk.mönster_id = m.id
                   WHERE k.nyckel = ? AND m.språk IS NULL
                     AND (mk.frastyp & ?) = ?""",
                (verb, BISATSFRAS, BISATSFRAS)).fetchone()
            self._bisatsverb[verb] = rad is not None
        return self._bisatsverb[verb]

    def duger(self, m: Mening) -> bool:
        return not self.validera(m)

    #: Valensens bitar (docs/BITMASK.md §8) → argumentplatserna ramen fyller.
    #: Intransitiv och reflexiv fyller inga — reflexivpronomenet sätter
    #: renderaren själv.
    RAMAR = {1: frozenset(), 2: frozenset({"objekt"}),
             4: frozenset({"objekt", "io"}), 8: frozenset(),
             16: frozenset({"predikativ"})}

    def valens(self, verb: str) -> int | None:
        if ("valens", verb) not in self._krav:
            rad = self.conn.execute(
                "SELECT valens FROM Koncept WHERE nyckel = ?", (verb,)).fetchone()
            self._krav[("valens", verb)] = rad["valens"] if rad else None
        return self._krav[("valens", verb)]

    def mönsterslottar(self, verb: str) -> frozenset:
        if ("slottar", verb) not in self._krav:
            self._krav[("slottar", verb)] = frozenset(r["slot"] for r in self.conn.execute(
                """SELECT mk.slot FROM Mönster m
                   JOIN Koncept k ON k.id = m.koncept_id
                   JOIN MönsterKrav mk ON mk.mönster_id = m.id
                   WHERE k.nyckel = ? AND m.språk IS NULL""", (verb,)))
        return self._krav[("slottar", verb)]

    def valensbrott(self, m: Mening) -> list[Brott]:
        """Fyller specen en av verbets ramar, varken mer eller mindre?

        `validera` prövar bara att de platser som är fyllda får fyllas med det
        de fylls med. Här prövas att platserna själva stämmer: «Blood is.»
        saknar kopulans predikativ, och «He will.» modalverbets komplement.

        Ramarna kommer ur valensens bitar, begränsade till de platser verbets
        mönster har. En komplementplats i mönstret är obligatorisk, och en
        argumentbisats fyller objektets plats. Används av den nya kärnan
        (KÄRNAN 6.1 punkt 6); `validera` är oförändrad för den gamla.
        """
        brott: list[Brott] = []
        valens = self.valens(m.verb)
        if valens is not None:
            slottar = self.mönsterslottar(m.verb)
            ramar = set()
            for bit, ram in self.RAMAR.items():
                if valens & bit:
                    ramar.add((ram & slottar) | ({"komplement"} & slottar))
            fyllda = {slot for slot in ("objekt", "io", "predikativ", "komplement")
                      if getattr(m, slot) is not None}
            if m.bisats is not None:
                fyllda.add("objekt")
            if frozenset(fyllda) not in ramar or (m.bisats is not None
                                                  and m.objekt is not None):
                brott.append(Brott("valens", m.verb, valens, None))
        for b in ([m.bisats] if m.bisats else []) + [
                a for a in m.adverbial if isinstance(a, Bisats)]:
            brott += self.valensbrott(b.sats)
        return brott
