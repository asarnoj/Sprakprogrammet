"""Böjningsregler — steg 0 i kärnans byggordning (KÄRNAN.md punkt 9).

Förutsägbarhetsprincipen, KÄRNAN 3.4: ett ord får ett eget formkort precis där
formen inte går att förutsäga ur det användaren redan kan — ordet självt,
språkets regler och ordets andra kort.

Paketet har två delar. Reglerna per språk (`sv.py`) förutsäger ett ords former
ur grundformen och de former som redan är kort. Kontrollen (`kontroll.py`) kör
reglerna mot varje form i databasen och tar fram korten.

Paketet hör till den nya kärnan och får inte importera något ur den gamla
(`kort`, `generator`). Formerna läses genom `rendering.Uppslag`, eftersom ett
korts facit är det `Uppslag.form` returnerar (KÄRNAN 3.7).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable


class Spår:
    """Vilka ljudregler och ändelser som användes, per cell.

    En ljudanpassning som beror på ljudet och inte på klassen är ett eget
    regelkort (KÄRNAN 3.4). Förutsägelsen sätter `cell` innan den räknar ut en
    cell, och anropar spåret med regelns namn när en ljudregel ska tillämpas.
    Svaret säger om den får det: en avstängd regel tillämpas inte, och så räknar
    kortmodellen ut vilka former regeln bestämmer.

    `ändelse(klass)` säger att cellen byggdes med klassens ändelse. Klassen
    namnges efter sitt synliga villkor, och ändelsekortet är (ordklass, klass,
    cell).
    """

    def __init__(self, avstängda: frozenset = frozenset()) -> None:
        self.cell: str | None = None
        self.per_cell: dict[str | None, set[str]] = defaultdict(set)
        self.klasser: dict[str, str] = {}
        self.avstängda = avstängda

    def __call__(self, regel: str) -> bool:
        if regel in self.avstängda:
            return False
        self.per_cell[self.cell].add(regel)
        return True

    def ändelse(self, klass: str, *celler: str) -> None:
        for cell in celler or (self.cell,):
            self.klasser[cell] = klass


@dataclass(frozen=True)
class Ordklass:
    """Reglerna för en ordklass i ett språk.

    ordning    cellerna i införandeordning, utan grundformen. Ordningen avgör
               vilken avvikande form som blir kort först.
    bas        (facit, lexem) -> (info, facit): grundformen och formerna,
               normaliserade så att de går att jämföra med förutsägelsen
    förutsäg   (info, kända kort, spår) -> cell -> form, eller None
    datafel    (facit, info) -> cell -> skäl, för former som bryter mot en
               regel utan undantag
    saknad     celler där en form som saknas betyder något: ordet uttrycks
               med ett annat ord (`mer`, `more`) eller böjs inte så. Där
               reglerna ger en form som datan saknar visar kontrollen det.
    """
    ordning: tuple[str, ...]
    bas: Callable
    förutsäg: Callable
    datafel: Callable
    saknad: tuple[str, ...] = ()
