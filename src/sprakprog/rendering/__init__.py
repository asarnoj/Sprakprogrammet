"""Renderarlagret — meningsspecifikation → ordad mening per språk."""

from .de import TyskRenderare
from .en import EngelskRenderare
from .es import SpanskRenderare
from .fr import FranskRenderare
from .it import ItalienskRenderare
from .ja import JapanskRenderare
from .restriktioner import Brott, Validator
from .spec import (
    Aspekt, Attribut, Bestämdhet, Bisats, Diates, Grad, Mening, Nominalfras,
    Numerus,
    Prepositionsfras,
    Referentgenus,
    RenderingsFel, Satsmodus, Tidsreferens,
)
from .sv import SvenskRenderare
from .uppslag import Uppslag

__all__ = [
    "Aspekt", "Attribut", "Bestämdhet", "Bisats", "Brott", "Diates", "Grad", "EngelskRenderare", "FranskRenderare",
    "ItalienskRenderare", "JapanskRenderare", "Mening",
    "Nominalfras", "Numerus", "Prepositionsfras", "Referentgenus",
    "RenderingsFel", "Satsmodus",
    "SpanskRenderare", "SvenskRenderare", "Tidsreferens", "TyskRenderare",
    "Uppslag", "Validator",
]
