"""Kaikki-mappning — översätter Wiktionary-data till slot-fil-celler.

Pipeline-modul för Fas B3. Läser kaikki-dumpar (lokalt cachade
Wiktionary-böjningstabeller från `gammal/datafiler/kaikki/`),
filtrerar och översätter taggar till våra bitmask-axlar, och
matchar mot slot-filerna i `paradigm/{språk}/`.

Endast svenska (sv) är implementerat just nu via `sv.py`. Övriga
språk får egna moduler i ett senare steg.

Public API:
    KaikkiAccess          — datalager
    mappa_lemma_sv        — huvudfunktion för svenska
    Mappningsrapport      — output-typ
"""

from __future__ import annotations

from .data_access import KaikkiAccess
from .sv import Mappningsrapport, mappa_lemma_sv

__all__ = ["KaikkiAccess", "Mappningsrapport", "mappa_lemma_sv"]
