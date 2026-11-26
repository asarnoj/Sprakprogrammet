"""Renderarlagret — meningsspecifikation → ordad mening per språk."""

from .spec import (
    Aspekt, Bestämdhet, Mening, Nominalfras, Numerus, RenderingsFel,
    Tidsreferens,
)
from .de import TyskRenderare
from .sv import SvenskRenderare
from .uppslag import Uppslag

__all__ = [
    "Aspekt", "Bestämdhet", "Mening", "Nominalfras", "Numerus",
    "RenderingsFel", "Tidsreferens", "SvenskRenderare", "TyskRenderare",
    "Uppslag",
]
