"""Renderarlagret — meningsspecifikation → ordad mening per språk."""

from .de import TyskRenderare
from .es import SpanskRenderare
from .fr import FranskRenderare
from .it import ItalienskRenderare
from .spec import (
    Aspekt, Bestämdhet, Mening, Nominalfras, Numerus, Referentgenus,
    RenderingsFel, Tidsreferens,
)
from .sv import SvenskRenderare
from .uppslag import Uppslag

__all__ = [
    "Aspekt", "Bestämdhet", "FranskRenderare", "ItalienskRenderare", "Mening",
    "Nominalfras", "Numerus", "Referentgenus", "RenderingsFel",
    "SpanskRenderare", "SvenskRenderare", "Tidsreferens", "TyskRenderare",
    "Uppslag",
]
