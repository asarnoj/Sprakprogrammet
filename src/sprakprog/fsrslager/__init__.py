"""FSRS-lagret — steg 3c i kärnans byggordning (KÄRNAN 5.2, 7.1, 7.6).

Algoritmen kommer ur paketet `fsrs` och skrivs inte om (8.2). Det som är vårt är
hur den används, och tre beslut syns i koden:

INGA INLÄRNINGSSTEG. `Scheduler` lägger normalt ett fallerat kort i en loop om
tio minuter. Vi kör med tomma steglistor: samma kort om och om igen är just det
som gör att man fastnar, och dagens again-hög ger i stället kortet i en ny mening
med andra ord runt sig (5.3).

TILLSTÅNDET LAGRAS INTE. Det räknas fram ur mötena varje gång (5.2). Mötena är
det enda som mätts, och ett lagrat tillstånd kan glida isär från dem.

ÖVERVAKADE KORT (7.6). För ett kort som möts flera gånger om dagen säger
förfallodagen ingenting. Det är övervakat när dess tio senaste möten skett på
färre än tio dagar, och då är R andelen rätt i fönstret. Kortet är förfallet när
R är under retentionsmålet. Fönstrets längd följer av målet: 1/(1 − 0,9) = tio
möten vid förvalet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction

from fsrs import Card, Rating, Scheduler

from ..kortmodell import Kort
from ..kurs import Kursdata, Möte

#: Användarens betyg (7.2) → FSRS. `Hard` och `Easy` kommer bara från
#: omrättningen, aldrig ur svarstiden.
BETYG = {"again": Rating.Again, "hard": Rating.Hard, "good": Rating.Good,
         "easy": Rating.Easy}


@dataclass(frozen=True, slots=True)
class Tillstånd:
    """Ett korts läge, framräknat ur dess möten."""
    kort: Kort
    card: Card                  # FSRS eget tillstånd
    möten: int
    övervakat: bool             # möts oftare än en gång om dagen (7.6)
    fönster: tuple[bool, ...]   # de tio senaste mötenas utfall, äldst först

    @property
    def förfaller(self) -> datetime:
        return self.card.due


def schemaläggare(retention: float) -> Scheduler:
    """FSRS med projektets val: inga inlärningssteg, ingen fuzz i tiden.

    Fuzz sprider förfallodagarna för att undvika toppar. Här väljs dagens kort
    av urvalsregeln (6.2) och inte av förfallodagen ensam, så slumpen skulle
    bara göra det svårare att räkna ut vad som händer.
    """
    return Scheduler(desired_retention=retention, learning_steps=(),
                     relearning_steps=(), enable_fuzzing=False)


def _fönstret(möten: list[Möte], längd: int) -> tuple[tuple[bool, ...], bool]:
    """De `längd` senaste mötenas utfall, och om kortet är övervakat (7.6)."""
    senaste = möten[-längd:]
    utfall = tuple(m.betyg != "again" for m in senaste)
    dagar = {m.tid[:10] for m in senaste}
    return utfall, len(senaste) == längd and len(dagar) < längd


def fönsterlängd(retention: str) -> int:
    """Fönstret är retentionsmålets tolerans: 1/(1 − mål) möten (7.6).

    Räknas exakt ur talet användaren valt. I flyttal blir 1/(1 − 0,9) lite mer
    än tio, och fönstret ett möte för långt.
    """
    return math.ceil(1 / (1 - Fraction(retention)))


class Lager:
    """Kortens FSRS-tillstånd och förfallodagar för en kurs."""

    def __init__(self, data: Kursdata) -> None:
        self.data = data
        mål = data.inställning("retention")
        self.retention = float(mål)
        self.schemaläggare = schemaläggare(self.retention)
        self.fönster = fönsterlängd(mål)

    def tillstånd(self, kort: Kort | None = None) -> dict[Kort, Tillstånd]:
        """Varje korts tillstånd, framräknat ur mötena i tidsordning (5.2)."""
        per_kort: dict[Kort, list[Möte]] = {}
        for möte in self.data.möten(kort):
            per_kort.setdefault(möte.kort, []).append(möte)
        ut: dict[Kort, Tillstånd] = {}
        for k, möten in per_kort.items():
            card = Card()
            for möte in möten:
                card, _ = self.schemaläggare.review_card(
                    card, BETYG[möte.betyg], datetime.fromisoformat(möte.tid))
            utfall, övervakat = _fönstret(möten, self.fönster)
            ut[k] = Tillstånd(k, card, len(möten), övervakat, utfall)
        return ut

    def r(self, t: Tillstånd, tid: datetime | None = None) -> float:
        """Sannolikheten att kortet går rätt nu.

        För ett övervakat kort är den andelen rätt i fönstret, som är en bättre
        skattning än FSRS när kortet möts flera gånger om dagen (7.6).
        """
        if t.övervakat:
            return sum(t.fönster) / len(t.fönster)
        return self.schemaläggare.get_card_retrievability(
            t.card, tid or datetime.now(timezone.utc))

    def förfallet(self, t: Tillstånd, tid: datetime | None = None) -> bool:
        """Hör kortet till dagens mål (5.2)?

        Ett schemalagt kort förfaller på sin dag; ett övervakat när andelen rätt
        i fönstret är under retentionsmålet (7.6).
        """
        if t.övervakat:
            return self.r(t) < self.retention
        return t.förfaller <= (tid or datetime.now(timezone.utc))

    def förfallna(self, tid: datetime | None = None) -> set[Kort]:
        """Dagens förfallna kort, bland dem som är införda (5.1)."""
        införda = self.data.införda()
        return {k for k, t in self.tillstånd().items()
                if k in införda and self.förfallet(t, tid)}
