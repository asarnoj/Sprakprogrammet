"""CSV-läsare för bas_kärna.csv och grundord.csv.

CSV-formatet är: koncept,ordklass,nivå,språk,lemma

Notera: nivå-kolumnen läses men ignoreras — den finns kvar i
filerna men är inte längre del av schemat. Den kommer att tas
bort ur CSV:erna i ett senare städsteg.

Rader som börjar med '#' eller är tomma hoppas över.
Header-raden ('koncept,ordklass,...') hoppas också över.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True, slots=True)
class CSVRad:
    """En enskild datarad från CSV-fil."""
    koncept: str
    ordklass: str
    språk: str
    lemma: str
    radnummer: int  # 1-indexerat, för felmeddelanden
    fil: str


def läs_csv(sökväg: Path) -> Iterator[CSVRad]:
    """Yield:ar CSVRad för varje datarad i filen.

    Hoppar över kommentarer, tomma rader och header.
    Lemma kan innehålla kommatecken om det är citerat — men våra
    filer använder inte citering, så vi splittrar på max 4 kommatecken
    och låter resten gå till lemma.
    """
    filnamn = sökväg.name
    with sökväg.open(encoding="utf-8") as f:
        for radnummer, rå_rad in enumerate(f, start=1):
            rad = rå_rad.strip()
            if not rad or rad.startswith("#"):
                continue
            if rad.startswith("koncept,"):  # header
                continue

            delar = rad.split(",", 4)
            if len(delar) != 5:
                raise ValueError(
                    f"{filnamn}:{radnummer}: förväntade 5 fält, fick {len(delar)}: {rad!r}"
                )
            koncept, ordklass, _nivå, språk, lemma = delar
            yield CSVRad(
                koncept=koncept.strip(),
                ordklass=ordklass.strip(),
                språk=språk.strip(),
                lemma=lemma.strip(),
                radnummer=radnummer,
                fil=filnamn,
            )
