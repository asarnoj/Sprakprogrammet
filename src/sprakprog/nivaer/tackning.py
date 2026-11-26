"""Ny täckning per kort — KÄRNAN 5.6.

> **Täckning** är hur stor del av språkets verkliga användning användaren kan
> producera. Varje gång språket använder ett ord i en viss form, eller
> tillämpar en regel, är en användning. Den är täckt när alla kort den kräver
> är införda. Ett korts **nya täckning** är de användningar där just det
> kortet är det sista som saknas.

Två tabeller möts här och behöver inga meningar byggas:

    ordbok/nivålistor/användningar.csv   hur tung varje (koncept, cell) är,
                                         mätt med `användningsmätning.py`
    Formtabell.kort(lexem, cell)         vilka kort formen består av (3.4)

En användnings krav är alltså formens kort: ordkortet, ändelsen eller
undantaget, och ljudregeln när en sådan gäller.

VAD SOM INTE VÄGS. Ett `val`-beslut väljer vilken cell som slås upp — att
säga något i preteritum kräver både preteritumformen och beslutet att
använda den — men formtabellen känner bara formens egna kort. Detsamma
gäller ordföljdsreglerna, som inte hänger på någon form alls.

Det spelar mindre roll än det låter, eftersom täckningen används för att
ordna NIVÅER: en nivå med `val/bestämning/bestämd_artikel` innehåller också
`ord:artikel_bestamd`, och väger genom det. Mätt på engelskan får 154 av 164
nivåer vikt den här vägen. De tio som inte får det består bara av
ordföljdsregler och tas i beroendeordning (5.6).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from ..kortmodell import Formtabell, Kort


def läs_användningar(fil: str | Path, språk: str) -> dict[tuple[str, str], float]:
    """(koncept, cell) → andel av språkets uppmätta användning."""
    ut: dict[tuple[str, str], float] = {}
    with Path(fil).open(encoding="utf-8") as f:
        for rad in csv.DictReader(f):
            if rad["språk"] == språk:
                ut[(rad["koncept"], rad["cell"])] = float(rad["andel"])
    return ut


class Täckning:
    """Vad varje kort låser upp, räknat ur användningarna och formtabellen."""

    def __init__(self, tabell: Formtabell,
                 användningar: dict[tuple[str, str], float]) -> None:
        self.tabell = tabell
        #: krav → den sammanlagda vikten av de användningar som har just de kraven.
        #: Flera användningar med samma kortmängd slås ihop, vilket gör
        #: räkningen billig: en användning per (koncept, cell) blir några
        #: tusen poster, och uppslagningen nedan går över dem en gång.
        self.vikt: dict[frozenset, float] = defaultdict(float)
        self.utan_krav: list[tuple[str, str]] = []
        for (koncept, cell), andel in användningar.items():
            krav = self._krav(koncept, cell)
            if krav is None:
                self.utan_krav.append((koncept, cell))
                continue
            self.vikt[krav] += andel

    def _krav(self, koncept: str, cell: str) -> frozenset | None:
        try:
            lexem = self.tabell.u.lexem(koncept)
            return frozenset(self.tabell.kort(lexem, cell))
        except Exception:                                          # noqa: BLE001
            # Ett koncept med flera lexem i samma språk, eller en cell som
            # formtabellen inte känner. Användningen vägs inte, och det syns
            # i `utan_krav` i stället för att tyst försvinna.
            return None

    def ny_täckning(self, mängd: frozenset[Kort] | set[Kort],
                    införda: frozenset[Kort] | set[Kort]) -> float:
        """Vikten av de användningar som blir täckta när `mängd` införs.

        «De användningar där just det kortet är det sista som saknas» (5.6),
        generaliserat till en mängd: de användningar vars krav ryms i
        `införda | mängd` men inte i `införda` ensamt. För ett ensamt kort är
        det definitionen ordagrant.
        """
        efter = set(införda) | set(mängd)
        return sum(v for krav, v in self.vikt.items()
                   if krav <= efter and not krav <= införda)

    def per_kort(self, mängd: frozenset[Kort] | set[Kort],
                 införda: frozenset[Kort] | set[Kort]) -> float:
        """Nivåns eller paketets täckning delad med dess antal kort (5.6).

        Ett paket som låser upp mycket med få kort går före ett som behöver
        många kort för samma sak.
        """
        nya = {k for k in mängd if k not in införda}
        return self.ny_täckning(mängd, införda) / len(nya) if nya else 0.0
