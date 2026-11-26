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

from .romansk import FEMININ, MASKULIN, Mening, Numerus, RomanskRenderare


class SpanskRenderare(RomanskRenderare):
    SPRÅK = "es"
    SUBJEKTSCELL = "sujeto"
    TONISK = "tonico"
    SAMMANSATT_DÅTID = False
    HJÄLPVERB_FAST = "ha"
    UTROPSTECKEN_FÖRE = "¡"
    PARTITIV_MED_PREPOSITION = False
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

    #: Vokalgrupper räknas för att hitta betoningen. Diftonger är EN grupp
    #: — "agua" är a-gua, två stavelser, inte tre.
    VOKALER = "aeiouáéíóúü"

    @classmethod
    def _betonat_a(cls, lemma: str) -> bool:
        """Börjar ordet på BETONAT a? Då tar det el, inte la.

        "el agua", "el águila" — feminina ord vars första stavelse bär
        betoningen byter artikel i singular, för att undvika att två
        a-ljud stöter ihop. Plural gör det inte: "las aguas".

        Betoningen går att räkna fram, för spanskan stavar den regelbundet:
        finns en skriven accent ligger betoningen där, annars på näst sista
        stavelsen om ordet slutar på vokal, n eller s, och sist annars. Ett
        tvåstavigt ord på vokal har alltså betoningen på första stavelsen.

        Att härleda i stället för att lista `agua` är poängen: regeln gäller
        också de ord som läggs till sedan.
        """
        ord = lemma.lower().removeprefix("h")
        if not ord.startswith(("a", "á")):
            return False
        if ord.startswith("á"):
            return True                 # skriven accent på första stavelsen
        if any(t in "áéíóú" for t in ord):
            return False                # accenten ligger någon annanstans
        grupper = 0
        i = 0
        while i < len(ord):
            if ord[i] in cls.VOKALER:
                grupper += 1
                while i < len(ord) and ord[i] in cls.VOKALER:
                    i += 1
            else:
                i += 1
        return grupper == 2 and ord[-1] in cls.VOKALER + "ns"

    def artikelcell(self, genus: int, numerus: Numerus, huvudord: str,
                    bestämd: bool) -> str:
        if (genus == FEMININ and numerus is Numerus.SG
                and self._betonat_a(huvudord)):
            # Formen är maskulin, ordet är det inte — adjektiv och
            # kongruens följer fortfarande femininum: "el agua fría".
            return "m_sg"
        return super().artikelcell(genus, numerus, huvudord, bestämd)

    def frågedeterminantcell(self, genus: int, numerus: Numerus) -> str:
        # qué böjs inte alls.
        return "inv"

    def frågecell(self, koncept: str, subjekt: bool) -> str:
        # Spanskan böjer quién i numerus, inte i kasus, och qué inte alls.
        return "quien_sg" if koncept.endswith("person") else "que"

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
