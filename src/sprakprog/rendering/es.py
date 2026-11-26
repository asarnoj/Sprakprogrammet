"""Spansk renderare.

Skiljer sig från franskan och italienskan på två punkter som båda syns i
exempelmeningen:

  Perfektiv dåtid är SYNTETISK. "dio", inte "ha dado". Spanskan har visserligen
  ett sammansatt perfekt med haber, men den perfektiva dåtiden är pretérito
  indefinido — ett eget tempus, inte en hjälpverbskonstruktion. Därför läser
  spanskan aldrig Lexem.hjälpverb.

  Klitikdubblering. "le dio un libro a su hermano" — dativklitikan `le` står
  kvar framför verbet ÄVEN när hela frasen skrivs ut. Det är obligatoriskt
  och unikt bland de tre romanska språken här (RENDERARE_KRAV §3.9).
"""

from __future__ import annotations

from .romansk import MASKULIN, Mening, Numerus, RomanskRenderare


class SpanskRenderare(RomanskRenderare):
    SPRÅK = "es"
    SUBJEKTSCELL = "sujeto"
    TONISK = "tonico"
    SAMMANSATT_DÅTID = False
    SAMMANDRAG = {("a", "el"): "al", ("de", "el"): "del"}

    def possessivcell(self, genus: int, numerus: Numerus) -> str:
        kön = "m" if genus == MASKULIN else "f"
        return f"obest_{kön}_{'pl' if numerus is Numerus.PL else 'sg'}"

    def klitika(self, m: Mening) -> list[str]:
        """Dativklitikan dubbleras när det finns ett indirekt objekt.

        Formen väljs på io:ets person och numerus, inte på subjektets.
        Tredje person ger le/les, som är det enda fallet som uppstår när
        io är en substantivfras.
        """
        if m.io is None:
            return []
        person, numerus, _ = self._subjektsform(m.io)
        koncept = "pronomen_3pl" if numerus == "pl" else "pronomen_3sg_mask"
        if person != 3:
            koncept = f"pronomen_{person}{numerus}"
        return [self.u.form_för(koncept, "coi", "mask" if person == 3 else None)]
