"""Valideringsfunktioner för CSV-rader.

Returnerar listor av varningar/fel som anropare kan presentera.
Validering kraschar inte importen — det är importerar.py som
beslutar hur fel hanteras.
"""

from __future__ import annotations

from dataclasses import dataclass

from .csv_läsare import CSVRad
from .modeller import ORDKLASSER, SPRÅK


@dataclass(frozen=True, slots=True)
class Varning:
    """En icke-fatal observation om en CSV-rad."""
    rad: CSVRad
    meddelande: str


@dataclass(frozen=True, slots=True)
class Fel:
    """Ett fatalt problem som hindrar import av en rad."""
    rad: CSVRad
    meddelande: str


def validera_rad(rad: CSVRad) -> Fel | None:
    """Per-rad-validering. Returnerar Fel om raden inte ska importeras."""
    if rad.ordklass not in ORDKLASSER:
        return Fel(rad, f"okänd ordklass: {rad.ordklass!r}")
    if rad.språk not in SPRÅK:
        return Fel(rad, f"okänt språk: {rad.språk!r}")
    if not rad.koncept:
        return Fel(rad, "tom koncept-nyckel")
    if not rad.lemma:
        return Fel(rad, "tomt lemma")
    return None
