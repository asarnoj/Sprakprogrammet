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
    Bisats, Diates, Mening, Nominalfras, Tidsreferens, attribut_med_grad,
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
        if self.slot == "bisats":
            return (f"verb={self.koncept}: tar ingen bisats — inget av "
                    f"verbets mönsterkrav har frastyp Bisatsfras")
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
