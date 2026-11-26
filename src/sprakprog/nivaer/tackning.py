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


def väljare_ur_karta(karta: dict) -> dict[tuple[str, str], dict[str, frozenset]]:
    """(ordklass, cell) → {valets namn: de utfall som väljer cellen}.

    ORDKLASSEN MÅSTE VARA MED. Cellen `inv` är en jättehink: prepositioner,
    konjunktioner, artiklar och adverb använder alla den, och tillsammans är
    de nära halva engelskan. Nycklades tabellen på cellnamnet ensamt ärvde
    `Interrogativdeterminant/inv` vikt från varenda preposition, och «hur
    mycket» blev kursens fjärde nivå.

    Beslut och former matchas på LED, så att ett beslut om verbet bara
    kopplas till verbets form. Ett val räknas som väljare bara när en
    delmängd av dess utfall förekommer med cellen; ses alla utfall bestämmer
    valet ingenting om cellen.
    """
    alla_utfall: dict[str, set] = {}
    sedda: dict[tuple, dict[str, set]] = {}
    for vägar in karta["vägar"].values():
        for väg in vägar:
            # Ordklassen för ett symboliskt koncept står bland vägens villkor.
            klass = {k[1]: v for k, v in väg.villkor
                     if isinstance(k, tuple) and k[0] == "ordklass"}
            per_led: dict = {}
            for h in väg.händelser:
                if h[0] == "regel":
                    per_led.setdefault(h[1], set()).add((h[2], h[3]))
                    alla_utfall.setdefault(h[2], set()).add(h[3])
            for h in väg.händelser:
                if h[0] != "form":
                    continue
                koncept = h[2]
                ok = (klass.get(koncept[1]) if isinstance(koncept, tuple)
                      else None)
                if ok is None:
                    continue
                nyckel = (ok.split("/")[0], h[3])
                for namn, utfall in per_led.get(h[1], ()):
                    sedda.setdefault(nyckel, {}).setdefault(namn, set()).add(utfall)
    # Ett val VÄLJER cellen bara om någon systercell får en DISJUNKT
    # utfallsmängd. Att utfallen bara delvis förekommer med cellen räcker
    # inte: `bestämning` ses med nästan vartenda utfall för både `sg` och
    # `pl`, och skiljer dem alltså inte åt — men testet släppte igenom det,
    # och då ärvde varje determinerare en andel av allt substantivbruk.
    # Pronomenet «jag» sjönk från plats 4 till 60 av just det skälet.
    #
    # Tempus klarar testet med 39 disjunkta cellpar, kongruens med 32,
    # pronomenform med ett — och `bestämning` med ett enda, mellan
    # determinerarens EGNA former (`inv` mot `obest`), vilket är riktigt.
    per_val: dict[str, dict[str, frozenset]] = {}
    for cell, valen in sedda.items():
        for namn, utfall in valen.items():
            per_val.setdefault(namn, {})[cell] = frozenset(utfall)
    ut: dict[tuple, dict[str, frozenset]] = {}
    for namn, celler in per_val.items():
        for nyckel, utfall in celler.items():
            # Bara systerceller i SAMMA ordklass jämförs.
            syskon = [a for (ok, c), a in celler.items()
                      if ok == nyckel[0] and c != nyckel[1]]
            if any(not (utfall & a) for a in syskon):
                ut.setdefault(nyckel, {})[namn] = utfall
    return ut


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
                 väljare: dict[tuple[str, str], dict[str, frozenset]] | None = None
                 ) -> None:
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
            ok = self.tabell.u.lexem(koncept)["ordklass"]
            väljarna = self.väljare.get((ok, cell), {})
            valen = [sorted(u) for u in väljarna.values()]
            if not valen:
                self.vikt[krav] += andel
                continue
            kombinationer = list(product(*valen))
            for kombination in kombinationer:
                beslut = {Kort(tabell.språk, "regel", ("val", namn, utfall))
                          for namn, utfall in zip(väljarna, kombination)}
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


def ordna_nivåer(nivåer: list[frozenset], krav: dict,
                 täckning: "Täckning") -> list[frozenset]:
    """Nivåerna i den ordning som ger mest ny täckning per kort (5.6).

    Nivåerna är grafens starka komponenter, och deras ordning är en TOPOLOGISK
    sortering — men en sådan har enorm frihet. 132 av engelskans 164 nivåer
    har ett enda kort, och deras inbördes ordning är obunden av kraven.
    Ordningen var därför `sorted(noder, key=str)`, alltså bokstavsordning
    efter svensk konceptnyckel: artikeln på nivå 3 och pronomenet `jag` på 72.

    Här väljs i stället vid varje steg den öppna nivå som låser upp mest, och
    måttet är KÄRNAN 5.6:s eget: de användningar som blir sägbara, delade med
    hur många kort det kostar. Mätt med `ordningsmätning.py`, andel av
    engelskan som är sägbar efter N nivåer:

        ordning              5      10      25      50     100
        alfabetisk        43,7    44,3    48,6    60,1    82,3
        täckning          48,2    53,7    58,7    69,9    83,4

    GIRIGHETEN ÄR NÄRSYNT, och det syns i svansen: en ordning som i stället
    tar den nivå flest andra väntar på når 92,1 % efter hundra nivåer mot
    täckningens 83,4. Den betalar för det tidigt — 29,4 % efter fem nivåer mot
    48,2 — och det är tidigt en kurs avgörs. Att se längre fram än ett steg är
    en möjlig förbättring; att byta bort början för svansen är det inte.

    Bara ord får fylla ut det som saknas. Ett mönsterkort ur en annan nivå
    räknas inte som tillgängligt, eftersom nivåerna är grindar (4.5).
    """
    nivåkort = {x for n in nivåer for x in n}

    def värde(nivå: frozenset, öppnade: set) -> float:
        tillgängligt = öppnade | nivå
        v = 0.0
        for k, andel in täckning.vikt.items():
            if k <= öppnade or not (k & nivå):
                continue
            if any(x in nivåkort for x in k - tillgängligt):
                continue
            v += andel / len(k - öppnade)
        return v

    öppnade: set = set()
    kvar = list(range(len(nivåer)))
    ut: list[frozenset] = []
    while kvar:
        möjliga = [i for i in kvar if all(
            k in öppnade for x in nivåer[i] for k in krav.get(x, ())
            if k not in nivåer[i])]
        if not möjliga:
            # Kraven går inte ihop — lämna resten i den ordning de kom, så att
            # ingenting tappas bort tyst.
            ut += [nivåer[i] for i in kvar]
            break
        # `-i` håller ordningen densamma varje gång när värdena är lika (5.6).
        bäst = max(möjliga, key=lambda i: (värde(nivåer[i], öppnade), -i))
        ut.append(nivåer[bäst])
        öppnade |= nivåer[bäst]
        kvar.remove(bäst)
    return ut
