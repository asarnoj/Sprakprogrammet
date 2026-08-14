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

    def eliderar(self, första: str, andra: str) -> bool:
        """le/la → l' framför vokal.

        h räknas som vokal: samtliga sex h-initiala substantiv i databasen
        (homme, heure, histoire, hôpital, huile, herbe) har h muet. Ett
        h aspiré-ord (héros) skulle kräva en flagga på Lexem, i stil med
        prenominal — skillnaden syns inte i stavningen.
        """
        if första == "que" or första.endswith(" que"):
            # que elideras framför vokal: "qu'il est venu", "parce qu'elle
            # lit", "est-ce qu'elle lit". Regeln gäller ORDET que, inte
            # ändelsen -que: "la bibliothèque a" elideras inte. Därför krävs
            # mellanslag före i de sammansatta subjunktionerna, som alla är
            # flerordiga (parce que, bien que, jusqu'à ce que).
            return andra[:1].lower() in self.VOKAL | {"h"}
        return (första in ELIDERAR
                and andra[:1].lower() in self.VOKAL | {"h"})
