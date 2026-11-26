"""Semantisk validering av en meningsspecifikation.

Renderaren kontrollerar ingenting — den bygger den mening den får. Det är
rätt arbetsdelning: renderaren svarar för att formen blir korrekt, den här
modulen för att innehållet är välformat.

Validering sker på SPECEN, inte på den renderade strängen, och därför en
enda gång för alla sju språk. `MönsterKrav` hänger på det universella
mönstret (`Mönster.språk IS NULL`), som är språkoberoende per definition.

Matchningsregeln är OCH: konceptet måste ha ALLA bitar kravet anger.

    Koncept.semantik & MönsterKrav.tagg == MönsterKrav.tagg

Regeln var odefinierad fram till 2026-08-12 — BITMASK.md §11 sade att
masken används för att matcha, men aldrig hur. Se paradigm/RESTRIKTIONER.md.

Vad den här modulen INTE gör: bedömer rimlighet. `Flickan köpte en dörr`
passerar, och ska göra det enligt scope-beslutet. Kategorifel stoppas,
osannolikhet inte.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .spec import Mening, Nominalfras

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


def _etiketter(mask: int | None) -> str:
    if not mask:
        return "—"
    return "+".join(namn for bit, namn in BITNAMN.items() if mask & bit)


@dataclass(frozen=True, slots=True)
class Brott:
    """Ett krav som specen inte uppfyller."""
    slot: str
    koncept: str
    krav: int
    faktisk: int | None

    def __str__(self) -> str:
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
        self._attributkrav: dict[str, int | None] = {}

    def krav_för(self, verb: str) -> dict[str, int]:
        """Slot → krävd bitmask, ur det universella mönstret."""
        if verb not in self._krav:
            rader = self.conn.execute(
                """SELECT mk.slot, mk.tagg FROM Mönster m
                   JOIN Koncept k ON k.id = m.koncept_id
                   JOIN MönsterKrav mk ON mk.mönster_id = m.id
                   WHERE k.nyckel = ? AND m.språk IS NULL
                     AND mk.tagg IS NOT NULL""", (verb,)).fetchall()
            self._krav[verb] = {r["slot"]: r["tagg"] for r in rader}
        return self._krav[verb]

    def semantik(self, koncept: str) -> int | None:
        if koncept not in self._semantik:
            rad = self.conn.execute(
                "SELECT semantik FROM Koncept WHERE nyckel = ?", (koncept,)).fetchone()
            self._semantik[koncept] = rad["semantik"] if rad else None
        return self._semantik[koncept]

    def attributkrav(self, koncept: str) -> int | None:
        """Vad ett adjektiv kräver av huvudordet. NULL = inget krav."""
        if koncept not in self._attributkrav:
            rad = self.conn.execute(
                "SELECT attributkrav FROM Koncept WHERE nyckel = ?",
                (koncept,)).fetchone()
            self._attributkrav[koncept] = rad["attributkrav"] if rad else None
        return self._attributkrav[koncept]

    def _attributbrott(self, slot: str, nf: Nominalfras) -> list[Brott]:
        """Får adjektiven beskriva huvudordet?

        Kravet går åt motsatt håll mot verbets: adjektivet begränsar vad det
        får fästa på, i stället för att öppna en plats.
        """
        huvud = self.semantik(nf.koncept)
        ut = []
        for attribut in nf.attribut:
            krävd = self.attributkrav(attribut)
            if krävd is None:
                continue
            if huvud is None or huvud & krävd != krävd:
                ut.append(Brott(f"{slot}.attribut={attribut}", nf.koncept,
                                krävd, huvud))
        return ut

    def validera(self, m: Mening) -> list[Brott]:
        """Alla krav specen bryter mot. Tom lista = välformad."""
        krav = self.krav_för(m.verb)
        brott: list[Brott] = []

        for slot, nf in (("subjekt", m.subjekt), ("objekt", m.objekt),
                         ("io", m.io)):
            if nf is None or slot not in krav:
                continue
            krävd = krav[slot]
            faktisk = self.semantik(nf.koncept)
            if faktisk is None or faktisk & krävd != krävd:
                brott.append(Brott(slot, nf.koncept, krävd, faktisk))

        for slot, nf in (("subjekt", m.subjekt), ("objekt", m.objekt),
                         ("io", m.io)):
            if nf is not None:
                brott += self._attributbrott(slot, nf)

        return brott

    def duger(self, m: Mening) -> bool:
        return not self.validera(m)
