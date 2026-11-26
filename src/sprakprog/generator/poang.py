"""Poängsättning av kandidatmeningar.

Sökningen tar den bästa av tusen kandidater, så allt som styr valet ligger
här. GENERATOR.md: "Arbetet ligger i poängfunktionen, inte i sökningen."

Sex termer, och de tre första kommer direkt ur besluten om svårighetsgrad:

  TÄCKNING       hur många köade kort meningen packar in. Ryggsäckens nytta.

  TOMGÅNG        en mening som täcker NOLL kort straffas hårt. Budgeten
                 finns för att forma HUR ett kort övas, inte för att avgöra
                 OM. Utan den här termen vann den kortaste möjliga meningen
                 varje gång: "Seht!" är två kort, träffar budgeten perfekt
                 och lär ut ingenting.

  BUDGET         avståndet från Σ(1−R) till målet, över de kort som FAKTISKT
                 HAR EN HISTORIK. Kvadratiskt, så att små avvikelser är
                 gratis och stora dyra.

                 Att osedda kort räknas för sig är ingen finess utan en
                 nödvändighet. R är odefinierat för ett kort som aldrig
                 prövats; att sätta det till noll och summera betyder att
                 varje osett kort räknas som ett säkert fel, och då blir
                 budgeten omöjlig att träffa vid kallstart. Sökningen
                 degenererade till kortast möjliga mening — "Malt Zimmer!"
                 — eftersom varje ytterligare ord kostade en hel felenhet.

                 Ett osett kort är inte ett förväntat fel utan material som
                 INTRODUCERAS. Det är samma skillnad som Anki gör mellan
                 nya kort och repetitioner, och den har sin egen kvot.

  NYA            hur många osedda kort meningen introducerar. Straffas mjukt
                 över NYKVOT — man lär sig inte fem nya ord i en mening.

  KONCENTRATION  svårigheten ska bäras av FÅ kort. Tio kort à R=0,90 och
                 ett à R=0,30 plus nio à R=0,98 ger nästan samma budget och
                 helt olika upplevelser — "en sak jag sträcker mig efter,
                 omgiven av fast mark" mot "allt vacklar lite".

  INTERFERENS    två kort ur SAMMA ändelsetabell i samma mening är inte
                 träning utan förvirring. De liknar varandra för mycket för
                 att gå att skilja åt, och det är precis det som får en att
                 fastna på liknande kort i evighet.

  UPPREPNING     ord som stod i förra meningen ger mindre. Färska meningar
                 är halva poängen med att generera.

  LÄNGD          mycket långa meningar straffas lätt. Inte för att de är
                 fel, utan för att felet blir svårare att lokalisera.

VIKTERNA ÄR EN FÖRSTA GISSNING. De går bara att hitta genom att köra
systemet och se vad som känns rätt, och de ligger därför samlade överst i
en enda tabell i stället för utspridda i koden.
"""

from __future__ import annotations

import collections
import math
import sqlite3
from dataclasses import dataclass

VIKT = {
    "täckning": 10.0,
    "tomgång": -40.0,
    "budget": -4.0,
    "nya": -3.0,
    "koncentration": 3.0,
    "interferens": -2.0,
    "upprepning": -1.5,
    "längd": -0.15,
}

#: Så många osedda kort får en mening introducera gratis. Över det straffas
#: varje ytterligare. Två är en gissning som ska mätas mot verklig
#: användning, som alla vikter här.
NYKVOT = 2

#: Under det här R räknas kortet som ett stretchkort — utfallet är genuint
#: osäkert. Över det är kortet stöd: det fyller meningen utan att pröva.
STRETCHGRÄNS = 0.85


@dataclass(frozen=True, slots=True)
class Poäng:
    total: float
    delar: dict[str, float]
    förväntat: float
    stretchkort: int
    täckta: int
    nya: int

    def __str__(self) -> str:
        d = "  ".join(f"{k}={v:+.1f}" for k, v in self.delar.items())
        return (f"{self.total:6.1f}  Σ(1−R)={self.förväntat:.2f} "
                f"stretch={self.stretchkort} nya={self.nya} "
                f"täckta={self.täckta}   {d}")


class Poängsättare:
    def __init__(self, kort_db: sqlite3.Connection, schemaläggare,
                 budget: float = 1.5) -> None:
        self.db = kort_db
        self.s = schemaläggare
        self.budget = budget
        self._förra: set[str] = set()

    def minns(self, koncept: set[str]) -> None:
        """Vad förra meningen innehöll — underlag för upprepningstermen."""
        self._förra = koncept

    def sätt(self, kort: list[sqlite3.Row], förfallna: set[int], nu=None) -> Poäng:
        if not kort:
            return Poäng(-math.inf, {}, 0.0, 0, 0, 0)
        sedda = [k for k in kort if k["sedd"] is not None]
        nya = len(kort) - len(sedda)
        r = [self.s.retention(k, nu) for k in sedda]
        förväntat = sum(1 - x for x in r)
        stretch = [k for k, x in zip(sedda, r) if x < STRETCHGRÄNS]
        täckta = sum(1 for k in kort if k["id"] in förfallna)

        delar = {}
        delar["täckning"] = VIKT["täckning"] * täckta
        delar["tomgång"] = VIKT["tomgång"] if täckta == 0 else 0.0

        # Kvadratiskt avstånd till budgeten — små avvikelser gratis.
        #
        # Termen VÄGS med hur stor del av meningen som har en historik.
        # Budgeten mäter förväntade fel bland det man lärt sig; består
        # meningen bara av nytt finns ingenting att mäta, och att kräva
        # Σ(1−R)=1,5 av den vore att kräva att användaren minns fel på
        # material hen aldrig sett. Utan viktningen straffades varje
        # kallstartsmening med hela budgetavståndet, oavsett vad den gjorde.
        andel = len(sedda) / len(kort)
        delar["budget"] = (VIKT["budget"] * andel
                           * (förväntat - self.budget) ** 2)
        delar["nya"] = VIKT["nya"] * max(0, nya - NYKVOT)

        # Koncentration: full poäng när ETT kort bär svårigheten, avtagande
        # ju fler som delar på den. Noll stretchkort ger noll — meningen
        # prövar ingenting.
        delar["koncentration"] = (
            VIKT["koncentration"] / len(stretch) if stretch else 0.0)

        # Interferens: par ur samma ändelsetabell, och bara bland de kort
        # som faktiskt prövas. Två säkra kort ur samma tabell stör inte.
        tabeller = collections.Counter(
            (k["ordklass"], k["klass"]) for k in stretch
            if k["typ"] in ("system", "stam") and k["klass"])
        delar["interferens"] = VIKT["interferens"] * sum(
            n - 1 for n in tabeller.values() if n > 1)

        delar["upprepning"] = VIKT["upprepning"] * len(
            {k["koncept"] for k in kort if k["koncept"]} & self._förra)
        delar["längd"] = VIKT["längd"] * len(kort)

        return Poäng(sum(delar.values()), delar, förväntat, len(stretch),
                     täckta, nya)
