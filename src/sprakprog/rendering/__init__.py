"""Renderarlagret — meningsspecifikation → ordad mening per språk."""

from .spec import (
    Aspekt, Bestämdhet, Mening, Nominalfras, Numerus, Referentgenus,
    RenderingsFel, Tidsreferens,
)
from .de import TyskRenderare
from .fr import FranskRenderare
from .sv import SvenskRenderare
from .uppslag import Uppslag

__all__ = [
    "Aspekt", "Bestämdhet", "Mening", "Nominalfras", "Numerus",
    "Referentgenus",
    "FranskRenderare", "RenderingsFel", "SvenskRenderare",
    "Tidsreferens", "TyskRenderare",
    "Uppslag",
]
