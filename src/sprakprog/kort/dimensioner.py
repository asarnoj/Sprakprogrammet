"""Böjningsdimensioner som nivåer — en universell lista, projicerad per språk.

FRÅGAN SOM LÖSTES HÄR. Nivåstegen har 21 konstruktioner som styr vad en
MENING får innehålla, och de är samma för alla sju språken därför att de
sitter på konceptlagret. Böjningens egna axlar styrdes inte alls: franskans
sex personändelser skapades allihop på nivå 1.

Att göra varje böjningsdimension till en nivå gick inte rakt av — franskan har
60 sådana celler, tyskan 42 och svenskan NOLL, eftersom svenska verb inte
personböjs. En stege per språk hade brutit den delade axeln.

JULIUS LÖSNING (2026-08-27): *"Man hade kunnat ha en universell nivålista som
är detaljerad, och sen renderas nivålistan olika för de olika språken genom
att gå igenom och se att vissa rader faktiskt bidrar till något nytt i
språket."* Listan förblir universell; STEGEN blir en projektion av den. Samma
form som renderarna redan har — universell spec, språkspecifik realisering.

VAD "BIDRAR MED NÅGOT NYTT" BETYDER, och varför det inte är ett val:

    En cell lär ut något nytt om dess ÄNDELSE inte redan är känd från en
    tidigare cell i SAMMA böjningsklass.

Franskans K0 (-er-verben) har `pres_1sg = e` och `pres_3sg = e`. Har man lärt
sig den första finns ingenting kvar att lära i den andra — samma sträng, samma
tabell. K1 har `s` och `t` på samma två celler, och där är det två moment.

Kriteriet är alltså inte en tröskel någon satt, utan strängidentitet i data
som redan finns. Det är samma predikat som strukturkontrollen i
`meningsgranskning` använder för att hitta TAPPADE distinktioner — där är
"två specar renderar likadant" ett fel, här är det ett urvalskriterium.

PER KLASS OCH INTE PER SPRÅK. Synligheten sitter på ändelsetabellen, inte på
språket: `1sg` mot `3sg` är tomt i franskans K0 och meningsfullt i K1. Kort
av typen `system` hör redan till en klass och inte till ett ord, så
granulariteten finns i kortmodellen — ingen omskrivning behövs.

OREGELBUNDENHET RÖR INTE DET HÄR. Ett oregelbundet verb hör ändå till en
ändelsetabell; det som gör det oregelbundet ligger i STAMkorten bredvid
(`avoir` har stammarna `a` och `av`) och i sista hand i ett `form`-kort för
hela ordet. Därför räcker tre ändelseklasser för franskan.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ÄNDELSEFIL = Path(__file__).resolve().parents[3] / "ordbok" / "ändelser.tsv"

#: DEN UNIVERSELLA LISTAN HÄRLEDS, den författas inte.
#:
#: Första försöket var handskrivet — pres_1sg, pres_2sg, … — och det var en
#: fransk lista med universella anspråk. Mätt mot datan missade den 11 av
#: svenskans 12 celler (`pres`, `pret`, `sup`, `imp` och passiverna), 15 av
#: tyskans 31 (konjunktiverna och participen) och ALLA tio japanska (`masu`,
#: `te`, `ta`, `nai`, `pot`, `vol` …). Svenskan fick ett enda steg, och det
#: var listans fel och inte svenskans.
#:
#: Lärdomen är att cellnamnen inte är ett delat ordförråd. `pres` i svenskan
#: och `pres_1sg` i franskan är samma tempus i olika upplösning, och
#: japanskans `masu` är en artighetsform utan europeisk motsvarighet. En
#: författad lista blir därför alltid formad av det språk som skrev den.
#:
#: Unionen av alla språks celler ÄR den universella listan. Ordningen inom
#: den är (antal språk som har cellen, fallande; sedan namnet), alltså det
#: mest delade först — ett tal som räknas ur datan och inte väljs. Celler som
#: bara ett språk har hamnar sist och projiceras bara dit.
#:
#: DET ÅTERSTÅENDE ARBETET STÅR HÄR OCH INTE I EN KOMMENTAR NÅGON ANNANSTANS:
#: ordningen är delad men inte PEDAGOGISK. Att `pres_1sg` kommer före
#: `pret_1sg` följer av att fler språk har den, inte av att presens ska läras
#: först. En riktig ordning kräver att cellerna märks med sina axlar (tempus,
#: person, numerus, modus, diates) och sorteras på dem — och de axlarna finns
#: redan i `Former`, men inte i ändelsetabellen. Se F5b.


def universella_celler(ordklass: str = "Verb") -> tuple[str, ...]:
    """Unionen av alla språks celler, mest delade först."""
    tabeller = ändelsetabeller(ordklass)
    antal: dict[str, set[str]] = defaultdict(set)
    for (språk, _), tabell in tabeller.items():
        for cell in tabell:
            antal[cell].add(språk)
    return tuple(sorted(antal, key=lambda c: (-len(antal[c]), c)))


def ändelsetabeller(ordklass: str = "Verb") -> dict[tuple[str, str], dict[str, str]]:
    """(språk, klass) → {cell: ändelse}. Läst ur `ordbok/ändelser.tsv`."""
    ut: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    with ÄNDELSEFIL.open(encoding="utf-8") as f:
        for rad in csv.DictReader(f, delimiter="\t"):
            if rad["ordklass"] == ordklass:
                ut[(rad["språk"], rad["klass"])][rad["cell"]] = rad["ändelse"]
    return dict(ut)


def projicera(celler: tuple[str, ...] | None = None,
              ordklass: str = "Verb") -> dict[str, list[tuple[str, set[str]]]]:
    """språk → [(cell, klasser där cellen lär ut en NY ändelse)].

    Celler som ingen klass realiserar utelämnas helt — det är där stegen
    kortas av sig själv. En cell som bara några klasser realiserar står kvar
    med just de klasserna, och det är den partiella raden: nivån gäller de
    böjningstabeller där det finns något att lära.
    """
    celler = celler or universella_celler(ordklass)
    tabeller = ändelsetabeller(ordklass)
    per_språk: dict[str, list[tuple[str, set[str]]]] = {}
    for språk in sorted({s for s, _ in tabeller}):
        klasser = {k: t for (s, k), t in tabeller.items() if s == språk}
        # Vad varje klass redan lärt ut när vi vandrar nerför listan.
        kända: dict[str, set[str]] = {k: set() for k in klasser}
        steg: list[tuple[str, set[str]]] = []
        for cell in celler:
            nya = set()
            for klass, tabell in klasser.items():
                ändelse = tabell.get(cell)
                if ändelse is None or ändelse in kända[klass]:
                    continue
                kända[klass].add(ändelse)
                nya.add(klass)
            if nya:
                steg.append((cell, nya))
        per_språk[språk] = steg
    return per_språk
