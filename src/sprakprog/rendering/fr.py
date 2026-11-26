"""Fransk renderare — konfiguration ovanpå den romanska basen.

Franskan byggdes först och ensam; det mesta i den här filen har flyttat till
romansk.py när spanskan och italienskan visade hur mycket som var gemensamt.
Kvar står det som faktiskt är franskt.
"""

from __future__ import annotations

from .romansk import MASKULIN, Numerus, RomanskRenderare


# Ord som tappar sin slutvokal framför vokalljud. Listan är sluten och
# lexikal — det är enstaka småord, inte en fonologisk regel som gäller alla
# ord på -e. je/me/te/se är subjekts- och objektsklitika, le/la artiklar och
# objektsklitika, de/ne prepositioner och negationsförled.
#
# Att den saknade var skälet till att 224 franska verbformer hade pronomenet
# inbakat i datan: "j'écoute" gick inte att bygga, så någon skrev in det.
ELIDERAR = frozenset({"je", "me", "te", "se", "le", "la", "de", "ne", "ce"})


class FranskRenderare(RomanskRenderare):
    SPRÅK = "fr"
    SUBJEKTSCELL = "sujet"
    TONISK = "tonique"
    # a donné, inte "donna" — passé simple är litterärt och passé composé
    # är den levande perfektiva dåtiden.
    SAMMANSATT_DÅTID = True
    # Franskan saknar egen artighetsform i imperativ: vouvoiement ÄR
    # andra person plural. "Lisez!" säger man till både en främling och
    # till flera. Negationen ändrar ingen form — bara ne ... pas runt om.
    IMPERATIVCELL = {"2sg": "imp_2sg", "2pl": "imp_2pl",
                     "artig": "imp_2pl", "1pl": "imp_1pl"}
    # Franskans imperfektkonjunktiv ("qu'il vînt") är litterär på samma
    # sätt som passé simple, och paradigmet saknar cellerna helt.
    HAR_IMPERFEKTKONJUNKTIV = False
    # Franskans vouvoiement ÄR andra person plural.
    ARTIG_KONGRUENS = (2, "pl")
    KOMPARERAD_EFTERSTÄLLD = False
    DUBBEL_SUPERLATIVARTIKEL = True
    NEKANDE_FÖRLED = "ne"
    FRÅGEINLEDNING = "est-ce que"
    SAMMANDRAG = {("à", "le"): "au", ("à", "les"): "aux",
                  ("de", "le"): "du", ("de", "les"): "des"}

    def possessivcell(self, genus: int, numerus: Numerus) -> str:
        # Franskan slår ihop genus i plural: ses livres, ses filles.
        if numerus is Numerus.PL:
            return "obest_a_pl"
        return "obest_m_sg" if genus == MASKULIN else "obest_f_sg"

    def artikelcell(self, genus: int, numerus: Numerus, huvudord: str,
                    bestämd: bool) -> str:
        # les och des är genusneutrala — en enda pluralcell.
        if numerus is Numerus.PL:
            return "pl"
        return "m_sg" if genus == MASKULIN else "f_sg"

    def reflexivt(self, lemma: str) -> bool:
        # Franskan ställer pronomenet FÖRE infinitiven och skriver ut det
        # som eget ord: se réveiller, s'asseoir. Elisionen framför vokal
        # sköts av ELIDERAR ovan, som redan har med se/me/te.
        return lemma.startswith(("se ", "s'"))

    def eliderar(self, första: str, andra: str) -> bool:
        """le/la → l' framför vokal.

        h räknas som vokal: samtliga sex h-initiala substantiv i databasen
        (homme, heure, histoire, hôpital, huile, herbe) har h muet. Ett
        h aspiré-ord (héros) skulle kräva en flagga på Lexem, i stil med
        prenominal — skillnaden syns inte i stavningen.
        """
        # SISTA ORDET AVGÖR, inte hela strängen. Regeln gäller ORDET — "la
        # bibliothèque a" elideras inte, för sista ordet är `bibliothèque`
        # och inte `que`.
        #
        # DET GÄLLER FLERORDIGA LEXEM OCKSÅ, och det var felet. `que` hade
        # ett eget undantag (`parce que`, `bien que`), men prepositionerna
        # inte: `à côté de`, `au-dessus de`, `en dehors de`, `le long de` och
        # `à l'intérieur de` är ETT lexem var, och medlemskapstestet mot
        # ELIDERAR läste hela strängen. Modellgranskningen 2026-08-29:
        # `Elle joue devant le chien à côté de un chat` — `de un` i stället
        # för `d'un`, obligatorisk elision.
        return (första.rsplit(" ", 1)[-1] in ELIDERAR | {"que"}
                and andra[:1].lower() in self.VOKAL | {"h"})

    def obestämd_under_negation(self, roll: str, negerad: bool) -> str | None:
        """`un/une/des` → `de` på det direkta objektet efter negation.

        `Elle ne trouve pas de chat`, inte `pas un chat`. Regeln är
        obligatorisk i franskan och gäller det DIREKTA OBJEKTET till det
        negerade verbet — därav `roll`-villkoret. Ett prepositionsobjekt
        behåller sin artikel: `elle ne joue pas avec un chat`.

        KOPULAN ÄR UNDANTAGEN, och det behöver ingen kod: `ce n'est pas un
        chat` behåller artikeln, och i specen är det ledet ett PREDIKATIV och
        inte ett objekt, så det går aldrig genom den här vägen.

        Elisionen sköts av `eliderar`, som redan har `de`: framför vokal blir
        det `d'`.

        Funnet av modellgranskningen 2026-08-29:
        `Est-ce qu'elle ne trouve pas un chat?`
        """
        if negerad and roll == "objekt":
            return self.u.form_för("prep_av", "inv")
        return None

    def sammandrar(self, första: str, andra: str, nästa: str) -> bool:
        """ELISIONEN GÅR FÖRE SAMMANDRAGNINGEN i franskan.

        `au` och `du` finns bara när artikeln STÅR KVAR som `le`. Framför
        vokal blir artikeln `l'`, och då finns ingenting att dra ihop med:
        det heter `à l'enfant` och `de l'homme`, aldrig `au enfant`.

        Italienskan gör tvärtom och eliderar det sammandragna (`dell'acqua`),
        vilket är därför regeln sitter här och inte i `romansk.sandhi`.

        Funnet 2026-08-29 när korpusens `bitransitiv` bytte indirekt objekt
        till `fam_barn`: renderingen gav `Elle donne le chien au enfant`.
        Felet fanns hela tiden — ingen korpusmening hade råkat ställa `à` +
        `le` framför en vokal.
        """
        return not self.eliderar(andra, nästa)

    # Franskan ställer pronomenet före infinitiven, som eget ord.
    REFLEXIV_INFINITIV_ENKLITISK = False
