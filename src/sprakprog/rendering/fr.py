"""Fransk renderare — konfiguration ovanpå den romanska basen.

Franskan byggdes först och ensam; det mesta i den här filen har flyttat till
romansk.py när spanskan och italienskan visade hur mycket som var gemensamt.
Kvar står det som faktiskt är franskt.
"""

from __future__ import annotations

from .romansk import MASKULIN, Numerus, RomanskRenderare


class FranskRenderare(RomanskRenderare):
    SPRÅK = "fr"
    SUBJEKTSCELL = "sujet"
    TONISK = "tonique"
    # a donné, inte "donna" — passé simple är litterärt och passé composé
    # är den levande perfektiva dåtiden.
    SAMMANSATT_DÅTID = True
    NEKANDE_FÖRLED = "ne"
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
        if första == "ne":
            return andra[:1].lower() in self.VOKAL | {"h"}
        return (första in ("le", "la")
                and andra[:1].lower() in self.VOKAL | {"h"})
