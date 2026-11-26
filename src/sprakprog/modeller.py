"""Dataklasser för Koncept, Lexem och Form.

Dessa speglar tabellerna i setup.sql men är språkkods-agnostiska
i den meningen att de inte vet hur de hamnar i databasen — det är
db.py:s ansvar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ── Typalias ────────────────────────────────────────────────────────────────
Språk = Literal["sv", "en", "fr", "de", "es", "it", "ja"]

# Måste hållas i synk med CHECK-listan för Koncept.ordklass i setup.sql.
ORDKLASSER: frozenset[str] = frozenset({
    "Substantiv", "Verb", "Adjektiv", "Adverb",
    "Pronomen", "Possessiv", "Preposition", "Konjunktion", "Subjunktion",
    "Interjektion", "Räkneord", "Frågepronomen", "Frågadverb",
    "Interrogativdeterminant", "Negationsadverb",
    "Demonstrativ", "Relativpronomen", "Artikel", "Kvantifikator",
})

SPRÅK: frozenset[str] = frozenset({"sv", "en", "fr", "de", "es", "it", "ja"})


@dataclass(frozen=True, slots=True)
class Koncept:
    """Språkoberoende begrepp. Identifieras av nyckel."""
    nyckel: str
    ordklass: str
    källa: str


@dataclass(frozen=True, slots=True)
class Lexem:
    """Ett lexem per språk per koncept."""
    koncept_nyckel: str
    språk: str
    lemma: str


@dataclass(slots=True)
class Form:
    """En böjd form av ett lexem. Reserveras för Fas B."""
    lexem_id: int
    form: str
    numerus: int | None = None
    species: int | None = None
    kasus: int | None = None
    genus: int | None = None
    tempus: int | None = None
    grad: int | None = None
    person: int | None = None
