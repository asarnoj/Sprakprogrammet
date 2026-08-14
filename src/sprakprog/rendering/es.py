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
    HJÄLPVERB_FAST = "ha"
    UTROPSTECKEN_FÖRE = "¡"
    # Usted och ustedes tar tredje person: "¡lea!", "¡lean!" — artigheten
    # är grammatiskt en tredjepersonsform, precis som tyskans Sie.
    IMPERATIVCELL = {"2sg": "imp_2sg", "2pl": "imp_2pl",
                     "artig": "imp_3sg", "1pl": "imp_1pl"}
    # Spanskan har ingen nekad imperativ alls: "¡no leas!" är presens
    # konjunktiv, inte imperativens "lee". Hela paradigmet byter form, och
    # det är den enskilt största skillnaden mellan jakande och nekande
    # uppmaning i något av de sju språken.
    NEKAD_IMPERATIVCELL = {"2sg": "subj_2sg", "2pl": "subj_2pl",
                           "artig": "subj_3sg", "1pl": "subj_1pl"}
    FRÅGETECKEN_FÖRE = "¿"
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

    def kopulavariant(self, m: Mening) -> str | None:
        """Vilket av två spanska lexem huvudverbet ska bli.

        Två koncept har dubbla lemman i spanskan, av olika skäl.

        verb_ha: tener (äga) mot haber (hjälpverb). "Tengo un libro" men
        "he leído". Som huvudverb är det alltid tener — haber existerar
        bara som hjälpverb och kan inte stå ensamt.

        verb_vara: ser eller estar — spanskans mest kända distinktion.

        estar för tillfälliga tillstånd ("está contenta"), ser för
        inneboende egenskaper och yrken ("es médica"). Konceptnycklarnas
        adj_es_-grupp ÄR tillståndsadjektiven — glad, ledsen, arg, trött,
        sjuk — så valet går att läsa ur datan i stället för att listas.
        """
        if m.verb == "verb_ha":
            return "possessiv"
        if m.verb != "verb_vara":
            return None
        if isinstance(m.predikativ, str) and m.predikativ.startswith("adj_es_"):
            return "tillfällig"
        return "permanent"

    def ordna_klitika(self, cod, coi) -> list[str]:
        """Spanskan har indirekt före direkt, och le blir se framför lo/la.

        "se lo dio", aldrig "le lo dio" — en ren ljudregel som inte går att
        lagra som en form, eftersom den beror på vad som står EFTER.
        """
        if cod and coi:
            form = "se" if coi[0] in ("le", "les") else coi[0]
            return [form, cod[0]]
        return [x[0] for x in (cod, coi) if x]
