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

BESLUTEN SOM VÄLJER CELLEN väger också. Att säga något i preteritum kräver
både preteritumformen och beslutet att använda den, men formtabellen känner
bara formens egna kort — så utan det här vägde preteritumBESLUTET noll och
hamnade på nivå 145, fast preteritumFORMEN är 3,4 % av engelskan.

Vilket beslut som väljer vilken cell läses ur kartan (`väljare_ur_karta`),
och det krävde två försök. Att räkna hur ofta ett beslut och en cell syns på
samma VÄG mäter kombinatorisk samförekomst, inte urval: adjektivets `pos`
följde med varje bestämningsval på nitton procent var, bara för att de är
oberoende. Matchas de i stället på LED — ett beslut om verbet och en form av
verbet hör till samma led — försvinner bruset helt, och `pos` får noll
beslut.

Kvar står då att skilja det val som VÄLJER cellen från det som bara råkar
finnas. Diskriminatorn är enkel: ett val väljer cellen om bara en DELMÄNGD av
dess utfall förekommer med den. Cellen `pret` ses med två av sex
tempusutfall — preteritum och pluskvamperfekt — men med alla sex
kongruensutfall, och alltså väljer tempus cellen medan kongruens inte gör
det.

    pret      <- tempusform in {preteritum, pluskvamperfekt}
    sup       <- tempusform in {perfekt, pluskvamperfekt, futurum_perfekt}
    pres_3pl  <- kongruens in {3pl}, tempusform in {presens}, do_omskrivning in {utan_do}

Kan flera utfall välja samma cell delas vikten mellan dem, som strängen
delas mellan cellerna och lemmat mellan koncepten.

VAD SOM ÄNDÅ INTE VÄGS är ordföljdsreglerna, som inte hänger på någon form
alls. Tio nivåer av 164 består bara av sådana, och de tas i
beroendeordning (5.6).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from itertools import product

from ..kortmodell import Formtabell, Kort


def väljare_ur_karta(karta: dict) -> dict[str, dict[str, frozenset]]:
    """cell → {valets namn: de utfall som väljer cellen}.

    Beslut och former matchas på LED, så att ett beslut om verbet bara
    kopplas till verbets form. Ett val räknas som väljare bara när en
    delmängd av dess utfall förekommer med cellen; ses alla utfall bestämmer
    valet ingenting om cellen.
    """
    alla_utfall: dict[str, set] = {}
    sedda: dict[str, dict[str, set]] = {}
    for vägar in karta["vägar"].values():
        for väg in vägar:
            per_led: dict = {}
            for h in väg.händelser:
                if h[0] == "regel":
                    per_led.setdefault(h[1], set()).add((h[2], h[3]))
                    alla_utfall.setdefault(h[2], set()).add(h[3])
            for h in väg.händelser:
                if h[0] != "form":
                    continue
                for namn, utfall in per_led.get(h[1], ()):
                    sedda.setdefault(h[3], {}).setdefault(namn, set()).add(utfall)
    return {cell: {namn: frozenset(u) for namn, u in valen.items()
                   if len(u) < len(alla_utfall[namn])}
            for cell, valen in sedda.items()}


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
                 användningar: dict[tuple[str, str], float],
                 väljare: dict[str, dict[str, frozenset]] | None = None) -> None:
        self.tabell = tabell
        self.väljare = väljare or {}
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
            # Formen kräver också besluten som väljer dess cell. Väljer flera
            # utfall samma cell delas vikten mellan kombinationerna.
            valen = [sorted(u) for u in self.väljare.get(cell, {}).values()]
            if not valen:
                self.vikt[krav] += andel
                continue
            kombinationer = list(product(*valen))
            for kombination in kombinationer:
                beslut = {Kort(tabell.språk, "regel", ("val", namn, utfall))
                          for namn, utfall in zip(
                              self.väljare[cell], kombination)}
                self.vikt[krav | frozenset(beslut)] += andel / len(kombinationer)

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
