"""Nivåerna — steg 4 i kärnans byggordning (KÄRNAN 4 och punkt 9).

En nivå är det minsta steg som gör minst ett nytt kort prövbart i princip (4.1).
Nivåkorten är de som inte växer med ordförrådet: mönsterkorten (ändelser och
regler) och korten för slutna ordklasser. Ett korts krav är de andra nivåkorten
i en mening som prövar kortet, och nivåerna är grafens starka komponenter.

Kravet är version 1 (4.2): nivåkorten i den FÖRSTA mening sammansättningen
hittar. Den frågan går fort, eftersom sökningen slutar vid första meningen.
Med `krymp` förbjuds sedan ett kort i taget, och mängden blir bevisat minst —
men varje nej kräver att allt som går att bygga gås igenom, och det tar dygn för
ett språk. Krympningen ändrar bara ordningen mellan korten, aldrig vad som går
att pröva. Kortets andra minsta mängder, och valet mellan dem efter täckning,
kommer med frekvenserna (steg P2).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable

from ..kortmodell import Formtabell, Kort
from ..sammansattning import Sammansättare, Träff

#: Ordklasser som inte växer med ordförrådet (KÄRNAN 4.1): pronomen, artiklar,
#: possessiv, räkneord och de andra funktionsordens klasser. Ett ord i en öppen
#: klass — substantiv, verb, adjektiv, adverb, interjektion — är upplåst från
#: början (3.1), också när renderaren använder det som hjälpverb.
SLUTNA_ORDKLASSER = frozenset({
    "Pronomen", "Possessiv", "Demonstrativ", "Frågepronomen", "Relativpronomen",
    "Frågadverb", "Interrogativdeterminant", "Artikel", "Konjunktion",
    "Subjunktion", "Preposition", "Negationsadverb", "Räkneord", "Kvantifikator",
})


class Nivåkort:
    """Avgör vilka kort som är nivåkort, och räknar upp dem."""

    def __init__(self, tabell: Formtabell) -> None:
        self.tabell = tabell
        self.u = tabell.u
        self._ordklass: dict[str, str] = {}

    def ordklass(self, koncept: str) -> str:
        if koncept not in self._ordklass:
            rad = self.u.conn.execute(
                "SELECT ordklass FROM Koncept WHERE nyckel = ?", (koncept,)).fetchone()
            self._ordklass[koncept] = rad[0] if rad else ""
        return self._ordklass[koncept]

    def __call__(self, kort: Kort) -> bool:
        if kort.typ in ("ändelse", "regel"):
            return True
        if kort.typ in ("ord", "oregelbunden"):
            return self.ordklass(kort.nyckel[0]) in SLUTNA_ORDKLASSER
        return False

    def alla(self, karta: dict) -> set[Kort]:
        """Varje nivåkort i språket: regler ur kartans vägar, formkort ur tabellen."""
        språk = self.tabell.språk
        ut: set[Kort] = set()
        for vägar in karta["vägar"].values():
            for väg in vägar:
                for h in väg.händelser:
                    if h[0] == "regel":
                        ut.add(Kort(språk, "regel", ("val", h[2], h[3])))
                    elif h[0] == "ordning":
                        ut.add(Kort(språk, "regel", ("ordning", h[2])))
        rader = self.u.conn.execute(
            """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id WHERE l.språk = ?""",
            (språk,)).fetchall()
        for lexem in rader:
            for kort in self.tabell.former(lexem).values():
                ut.update(k for k in kort if self(k))
        return ut


class Krav:
    """Ett nivåkorts minsta kortmängd (KÄRNAN 4.2)."""

    def __init__(self, sammansättare: Sammansättare, nivå: Nivåkort) -> None:
        self.s, self.nivå = sammansättare, nivå
        self.frågor = 0

    def _finns(self, mål: Kort, tillåtna: frozenset | None) -> Träff | None:
        """En mening som prövar målet av ordkort och nivåkort ur `tillåtna`
        (None = alla)."""
        nivå = self.nivå

        def tillåten(k: Kort) -> bool:
            return k == mål or not nivå(k) or tillåtna is None or k in tillåtna

        self.frågor += 1
        return self.s.finns(mål, tillåten)

    def _nivåkorten(self, träff: Träff, mål: Kort) -> frozenset:
        return frozenset(k for k in träff.kort if self.nivå(k)) - {mål}

    def mängd(self, mål: Kort, krymp: bool = False) -> frozenset | None:
        """Kortets krav, eller None om ingen giltig mening prövar kortet.

        Den första mening sammansättningen hittar ger mängden (version 1, 4.2).
        Med `krymp` förbjuds ett kort i taget, och går det fortfarande att bygga
        en mening tas den mindre mängden. När inget kort går att ta bort är
        mängden bevisat minst, men varje nej kostar en uttömmande genomgång.
        """
        träff = self._finns(mål, None)
        if träff is None:
            return None
        mängd = self._nivåkorten(träff, mål)
        krympte = krymp
        while krympte:
            krympte = False
            for kort in sorted(mängd, key=str):
                träff = self._finns(mål, mängd - {kort})
                if träff is not None:
                    mängd = self._nivåkorten(träff, mål)
                    krympte = True
                    break
        return mängd


def starka_komponenter(noder: Iterable, kanter: dict) -> list[frozenset]:
    """Grafens starka komponenter, var och en efter de komponenter den kräver.

    Tarjans algoritm ger en komponent först när allt den når är klart, och en
    kant går från ett kort till det kort det kräver — så komponenterna kommer i
    den ordning nivåerna kan öppnas.
    """
    index: dict = {}
    lägst: dict = {}
    stack: list = []
    på_stack: set = set()
    ut: list[frozenset] = []

    def besök(nod) -> None:
        index[nod] = lägst[nod] = len(index)
        stack.append(nod)
        på_stack.add(nod)
        for granne in sorted(kanter.get(nod, ()), key=str):
            if granne not in index:
                besök(granne)
                lägst[nod] = min(lägst[nod], lägst[granne])
            elif granne in på_stack:
                lägst[nod] = min(lägst[nod], index[granne])
        if lägst[nod] == index[nod]:
            komponent = set()
            while True:
                x = stack.pop()
                på_stack.discard(x)
                komponent.add(x)
                if x == nod:
                    break
            ut.append(frozenset(komponent))

    for nod in sorted(noder, key=str):
        if nod not in index:
            besök(nod)
    return ut


@dataclass
class Nivåkarta:
    """Kraven och nivåerna för ett språk."""
    krav: dict          # kort → dess minsta mängd
    nivåer: list        # starka komponenter, i den ordning de kan öppnas
    oprövbara: list     # kort utan någon giltig mening


def rita_nivåer(krav: Krav, kort: Iterable[Kort],
                rapport: Callable[[str], None] | None = print,
                krymp: bool = False, täckning=None) -> Nivåkarta:
    """Varje korts krav, grafen och nivåerna (4.1, 4.2).

    Med `täckning` ordnas nivåerna efter ny täckning per kort (5.6) i stället
    för i den godtyckliga ordning den topologiska sorteringen råkar ge. Utan
    den behålls komponentordningen, så att nivåerna går att räkna fram även
    innan användningarna är mätta.
    """
    mängder: dict = {}
    for k in sorted(kort, key=str):
        t, frågor = time.perf_counter(), krav.frågor
        mängder[k] = krav.mängd(k, krymp)
        if rapport:
            text = ("inte prövbart" if mängder[k] is None
                    else "{" + ", ".join(sorted(map(str, mängder[k]))) + "}")
            rapport(f"  {k}: {text}  ({krav.frågor - frågor} frågor, "
                    f"{time.perf_counter() - t:.1f} s)")
    valda = {k: m for k, m in mängder.items() if m is not None}
    kanter = {k: {d for d in m if d in valda} for k, m in valda.items()}
    nivåer = starka_komponenter(valda, kanter)
    if täckning is not None:
        from .tackning import ordna_nivåer
        nivåer = ordna_nivåer(nivåer, valda, täckning)
    return Nivåkarta(valda, nivåer,
                     sorted((k for k, m in mängder.items() if m is None), key=str))
