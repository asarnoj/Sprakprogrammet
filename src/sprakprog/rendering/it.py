"""Italiensk renderare.

Det italienska särdraget är artikelallomorferna. il/lo och i/gli väljs på
det FÖLJANDE ordets ljudform: lo studente, lo zio, lo psicologo, l'amico,
men il libro. Formerna ligger som egna celler i Former (m_sg_lo, m_pl_gli)
eftersom de är något en inlärare måste kunna — valet mellan dem görs här,
eftersom det beror på nästa ord och inte på artikeln.
"""

from __future__ import annotations

from .romansk import MASKULIN, Numerus, RenderingsFel, RomanskRenderare

# Ord som kräver lo/gli i stället för il/i.
LO_INLEDNING = ("z", "gn", "ps", "pn", "x", "y")


VOKALER = "aeiouàèéìòù"


def _kräver_lo(ord: str) -> bool:
    """Tar ordet lo/gli i stället för il/i?

    Vokalinledda ord räknas hit: "lo amico" elideras sedan till "l'amico",
    och pluralen är "gli amici". Det är samma allomorf som lo/gli, bara med
    elision ovanpå.
    """
    o = ord.lower()
    if o.startswith(LO_INLEDNING) or o[:1] in VOKALER:
        return True
    # s + konsonant ("studente", "sbaglio") — men inte s + vokal ("sole").
    return len(o) > 1 and o[0] == "s" and o[1] not in VOKALER


class ItalienskRenderare(RomanskRenderare):
    SPRÅK = "it"
    SUBJEKTSCELL = "soggetto"
    TONISK = "tonico"
    SAMMANSATT_DÅTID = True
    # Italienskan smälter ihop preposition och bestämd artikel obligatoriskt.
    # Sex prepositioner × sju artikelformer; de vanligaste tas här.
    SAMMANDRAG = {("a", "il"): "al", ("a", "lo"): "allo", ("a", "la"): "alla",
                  ("a", "i"): "ai", ("a", "gli"): "agli", ("a", "le"): "alle",
                  ("di", "il"): "del", ("di", "lo"): "dello", ("di", "la"): "della",
                  ("di", "i"): "dei", ("di", "gli"): "degli", ("di", "le"): "delle",
                  ("in", "il"): "nel", ("in", "lo"): "nello", ("in", "la"): "nella",
                  ("in", "i"): "nei", ("in", "gli"): "negli", ("in", "le"): "nelle",
                  ("da", "il"): "dal", ("da", "la"): "dalla",
                  ("su", "il"): "sul", ("su", "la"): "sulla",
                  ("con", "il"): "col"}

    def possessivcell(self, genus: int, numerus: Numerus) -> str:
        kön = "m" if genus == MASKULIN else "f"
        return f"{kön}_{'pl' if numerus is Numerus.PL else 'sg'}"

    def artikelcell(self, genus: int, numerus: Numerus, huvudord: str,
                    bestämd: bool) -> str:
        if genus != MASKULIN:
            return "f_pl" if numerus is Numerus.PL else "f_sg"
        if numerus is Numerus.PL:
            # Obestämd plural finns inte — den fångas som saknad cell.
            return "m_pl_gli" if _kräver_lo(huvudord) else "m_pl"
        return "m_sg_lo" if _kräver_lo(huvudord) else "m_sg"

    def ordna_klitika(self, cod, coi) -> list[str]:
        """Italienskan smälter ihop två klitika: gli + lo → glielo, mi + lo → me lo.

        De sammansmälta formerna finns inte i Former — de är egna ord, inte
        celler i något av de befintliga paradigmen. Ett enskilt klitikum går
        bra; två stoppar hellre än gissar.
        """
        if cod and coi:
            raise RenderingsFel(
                "it: två klitika smälter ihop (glielo, me lo) och de formerna "
                "finns inte i databasen — de är egna ord, inte celler")
        return [x[0] for x in (cod, coi) if x]

    def eliderar(self, första: str, andra: str) -> bool:
        """lo/la → l' framför vokal. il elideras aldrig."""
        return (första in ("lo", "la")
                and andra[:1].lower() in self.VOKAL)
