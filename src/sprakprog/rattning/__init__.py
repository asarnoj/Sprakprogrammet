"""Rättningen — steg 8 i kärnans byggordning (KÄRNAN 7.2 och 7.3).

Svaret jämförs med facit ord för ord, och varje kort får sitt betyg av de ord
det bestämde. Ett kort som bestämde ett ord som stämmer är rätt; stämmer något
av dess ord inte är det fel. Stavfel och accentfel räknas som fel: rättningen
gissar aldrig vad användaren menade (7.2).

Enheten är renderarens positioner (7.3). Spåret säger vilka utskrivna ord varje
kort bestämde, och luckorna säger var ett kort hade lagt till ett ord som inte
står i svaret. Diffen säger vilka positioner som stämmer.

Ett uppslag är inte alltid ett skrivet ord: "how many" och "inte längre" är
ett uppslag och två ord. `_spann` översätter mellan de två räkningarna.

VAD SOM INTE ÄR BYGGT ÄN. Version ett jämför med en variant: den mening som
ställdes. Flera godtagna varianter (6.5) och omrättningen (7.2) kommer med
entydighetsfiltret respektive gränssnittet. Sammansmälta ord — franskans «du»,
där två uppslag blir ETT skrivet ord — går åt andra hållet än `_spann` och
görs när ett språk som smälter samman ord kommer in.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from ..kortmodell import Formtabell, Kort, meningens_kort
from ..rendering.spår import Utskrift

#: Betygen som räknas fram ur diffen (7.2). `Hard` och `Easy` kommer bara från
#: användarens omrättning.
RÄTT, FEL = "good", "again"


class Rättningsfel(Exception):
    """Rättningen kan inte säga vilket kort som bär vilket ord.

    Kastas hellre än att betygsätta på en gissning: en falsk rad i loggen ger
    ett kort en repetition det inte förtjänat, och det som brast får ingen.
    """


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


#: Tecken som MENINGEN får av `spec.slutar` och av versaliseringen i
#: renderarens `rendera`, inte av något kort: punkt, frågetecken, utropstecken
#: och spanskans inledande ¿ och ¡.
SATSENS_FORM = ".!?¿¡…"


def _avskalad(ord_: list[str]) -> list[str]:
    """Orden utan det ingen bestämde: sluttecknet och den inledande versalen.

    Ett korts positioner är de utskrivna ord vars FORM kortet bestämde (6.2).
    Punkten i slutet bestämmer inget kort — den kommer ur `spec.slutar`, som
    läser meningens modus — och den inledande versalen kommer ur
    renderarens sista rad. Ändå satt de på samma tokens som orden, så ett
    svar utan punkt fällde varje kort som stod på sista ordet.

    Det hände direkt i den första riktiga körningen: «Time exists» i stället
    för «Time exists.» underkände fem kort, däribland ordet, ändelsen,
    kongruensen och ordföljden. Inget av dem hade gjort något.

    Skillnaden försvinner alltså ur ATTRIBUTIONEN. Den syns fortfarande för
    användaren, eftersom facit skrivs ut som det är.
    """
    if not ord_:
        return ord_
    ut = list(ord_)
    ut[-1] = ut[-1].rstrip(SATSENS_FORM)
    ut[0] = ut[0].lstrip(SATSENS_FORM)
    if ut[0][:1].isupper():
        ut[0] = ut[0][:1].lower() + ut[0][1:]
    return ut


def _spann(ut: Utskrift, facit: list[str]) -> list[range]:
    """Var varje uppslag står i den skrivna texten.

    Spåret räknar UPPSLAG och texten räknar SKRIVNA ORD, och det är inte
    samma sak. Ett uppslag är ett ord för spåret men kan vara flera på
    pappret: "how many", "inte längre", "den här". Läses spårets index som
    ett ordindex glider allt efter det första flerordiga uppslaget ett steg,
    och rättningen skyller på grannen i stället för på den skyldige.

    Felet var inte teoretiskt. Med facit "How many books does the girl
    read?" gav svaret "How many book does the girl read?" — fel numerus på
    substantivet — godkänt substantiv och underkänt do, kongruens och
    inversion, sex kort som inte hade gjort något. Och svaret "...the girl
    reads?" gick igenom helt, fast det var fel.

    Motsatsen — flera uppslag som smälter ihop till ETT skrivet ord, som
    franskans «du» — får samma svar när den dagen kommer: spannet är tomt
    eller delat i stället för ett ord långt (KÄRNAN 7.3).
    """
    spann: list[range] = []
    nästa = 0
    for o in ut.ord:
        antal = len(str(o).split())
        spann.append(range(nästa, nästa + antal))
        nästa += antal
    if nästa != len(facit):
        raise Rättningsfel(
            f"uppslagen är {nästa} skrivna ord men meningen har {len(facit)}: "
            f"{ut.text!r}. Rättningen kan inte säga vilket kort som bär vilket "
            f"ord, och vägrar hellre än gissar")
    return spann


def rätta(tabell: Formtabell, ut: Utskrift, svar: str) -> Rättning:
    """Betyget per kort, räknat ur diffen mellan facit och svaret."""
    facit = ut.text.split()
    spann = _spann(ut, facit)
    # Attributionen jämför utan satsens form; diffen som visas behåller den.
    lika, tillagda, _ = _jämför(_avskalad(facit), _avskalad(svar.split()))
    *_, diff = _jämför(facit, svar.split())
    betyg: dict[Kort, str] = {}
    for kort, platser in meningens_kort(tabell, ut):
        ord_ = {i for sort, j in platser if sort == "ord" for i in spann[j]}
        # Lucka `j` ligger före uppslag `j`, alltså vid spannets början, och
        # lucka `len(ord)` sist av allt.
        luckor = {spann[j].start if j < len(spann) else len(facit)
                  for sort, j in platser if sort == "lucka"}
        # En lucka är prövad bara när svaret varken lade till ett ord där eller
        # ändrade orden runt den: annars säger den ingenting om kortet.
        rätt = ord_ <= lika and all(
            i not in tillagda and (i == 0 or i - 1 in lika) and (i == len(facit) or i in lika)
            for i in luckor)
        # Ett kort kan stå på flera platser i samma mening; faller en faller kortet.
        if betyg.get(kort) != FEL:
            betyg[kort] = RÄTT if rätt else FEL
    return Rättning(len(lika) == len(facit) and not tillagda, betyg, tuple(diff))
