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

    DUBBLERAR = True

    def _dubblering(self, io: Nominalfras):
        """Dativklitikan som dubblerar en utskriven io-fras.

        Formen väljs på io:ets person och numerus, inte på subjektets.
        En substantivfras är alltid tredje person, alltså le eller les.
        """
        _, numerus, _ = self._subjektsform(io)
        koncept = "pronomen_3pl" if numerus == "pl" else "pronomen_3sg_mask"
        return self.u.form_för(koncept, "coi", "mask"), 3

    def ordna_klitika(self, cod, coi) -> list[str]:
        """Spanskan har indirekt före direkt, och le blir se framför lo/la.

        "se lo dio", aldrig "le lo dio" — en ren ljudregel som inte går att
        lagra som en form, eftersom den beror på vad som står EFTER.
        """
        if cod and coi:
            form = "se" if coi[0] in ("le", "les") else coi[0]
            return [form, cod[0]]
        return [x[0] for x in (cod, coi) if x]
