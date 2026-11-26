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
    "RENDERARE", "Uppslag", "Validator",
]

#: språk → renderarklass. Bor HÄR och inte i generatorn, därför att den som
#: behöver den inte alltid bygger meningar: rättningen frågar renderaren om
#: dess sandhi för att kunna spåra en sammansmält token tillbaka till sina
#: uppslag (`Rättare._sammansmälta`), och att importera den ur generatorn
#: hade varit en cirkel.
RENDERARE = {"sv": SvenskRenderare, "en": EngelskRenderare, "de": TyskRenderare,
             "fr": FranskRenderare, "es": SpanskRenderare,
             "it": ItalienskRenderare, "ja": JapanskRenderare}
