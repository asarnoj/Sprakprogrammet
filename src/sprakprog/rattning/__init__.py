"""Rättningen — steg 8 i kärnans byggordning (KÄRNAN 7.2 och 7.3).

Svaret jämförs med facit ord för ord, och varje kort får sitt betyg av de ord
det bestämde. Ett kort som bestämde ett ord som stämmer är rätt; stämmer något
av dess ord inte är det fel. Stavfel och accentfel räknas som fel: rättningen
gissar aldrig vad användaren menade (7.2).

Enheten är renderarens positioner (7.3). Spåret säger vilka utskrivna ord varje
kort bestämde, och luckorna säger var ett kort hade lagt till ett ord som inte
står i svaret. Diffen säger vilka positioner som stämmer.

VAD SOM INTE ÄR BYGGT ÄN. Version ett jämför med en variant: den mening som
ställdes. Flera godtagna varianter (6.5) och omrättningen (7.2) kommer med
entydighetsfiltret respektive gränssnittet. Sammansmälta ord — franskans «du» —
kräver att positionerna spåras genom sammansmältningen, och det görs när ett
språk som smälter samman ord kommer in.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from ..kortmodell import Formtabell, Kort, meningens_kort
from ..rendering.spår import Utskrift

#: Betygen som räknas fram ur diffen (7.2). `Hard` och `Easy` kommer bara från
#: användarens omrättning.
RÄTT, FEL = "good", "again"


@dataclass(frozen=True, slots=True)
class Rättning:
    """Vad diffen säger om svaret."""
    rätt: bool
    #: kort → again · good, räknat ur diffen
    betyg: dict[Kort, str]
    #: (facit, svar) per position: None när ordet saknas på sin sida
    diff: tuple[tuple[str | None, str | None], ...]

    @property
    def fel(self) -> list[Kort]:
        return sorted((k for k, b in self.betyg.items() if b == FEL), key=str)


def _jämför(facit: list[str], svar: list[str]) -> tuple[set[int], set[int], list]:
    """Vilka av facits ord som stämmer, var svaret lagt till ord, och diffen.

    De tillagda orden räknas per lucka: lucka `i` ligger före facits ord `i`,
    och lucka `len(facit)` sist, som i spåret.
    """
    lika: set[int] = set()
    tillagda: set[int] = set()
    diff: list[tuple[str | None, str | None]] = []
    for tagg, i1, i2, j1, j2 in difflib.SequenceMatcher(
            a=facit, b=svar, autojunk=False).get_opcodes():
        if tagg == "equal":
            lika.update(range(i1, i2))
            diff.extend((facit[i], svar[j]) for i, j in zip(range(i1, i2), range(j1, j2)))
        elif tagg == "insert":
            tillagda.add(i1)
            diff.extend((None, svar[j]) for j in range(j1, j2))
        elif tagg == "delete":
            diff.extend((facit[i], None) for i in range(i1, i2))
        else:
            # Ett utbytt stycke kan också ha fler ord i svaret än i facit, och de
            # orden är tillagda i styckets båda ändar.
            if j2 - j1 > i2 - i1:
                tillagda.update({i1, i2})
            diff.extend((facit[i] if i < i2 else None, svar[j] if j < j2 else None)
                        for i, j in zip(range(i1, max(i2, i1 + j2 - j1)),
                                        range(j1, max(j2, j1 + i2 - i1))))
    return lika, tillagda, diff


def rätta(tabell: Formtabell, ut: Utskrift, svar: str) -> Rättning:
    """Betyget per kort, räknat ur diffen mellan facit och svaret."""
    facit = ut.text.split()
    lika, tillagda, diff = _jämför(facit, svar.split())
    betyg: dict[Kort, str] = {}
    for kort, platser in meningens_kort(tabell, ut):
        ord_ = {i for sort, i in platser if sort == "ord"}
        luckor = {i for sort, i in platser if sort == "lucka"}
        # En lucka är prövad bara när svaret varken lade till ett ord där eller
        # ändrade orden runt den: annars säger den ingenting om kortet.
        rätt = ord_ <= lika and all(
            i not in tillagda and (i == 0 or i - 1 in lika) and (i == len(facit) or i in lika)
            for i in luckor)
        # Ett kort kan stå på flera platser i samma mening; faller en faller kortet.
        if betyg.get(kort) != FEL:
            betyg[kort] = RÄTT if rätt else FEL
    return Rättning(len(lika) == len(facit) and not tillagda, betyg, tuple(diff))
