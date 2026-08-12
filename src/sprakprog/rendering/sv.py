"""Svensk renderare.

Första språket, av två skäl: Julius kan bedöma resultatet direkt, och det
är billigare att upptäcka en arkitekturmiss här än på sju språk samtidigt.

Svenskan har inget kasus att hantera och rak SVO-ordföljd i huvudsats, så
den här filen visar strukturen utan att drunkna i den. Tyskan kommer näst
och tvingar fram kasus och V2 medan arkitekturen fortfarande är billig att
ändra.

Det renderaren INTE gör: gissar. Varje fall som inte är implementerat
kastar RenderingsFel med vad som saknas. En tyst felaktig mening är värre
än ett stopp.
"""

from __future__ import annotations

import sqlite3

from .spec import (
    Bestämdhet, Mening, Nominalfras, Numerus, RenderingsFel, Tidsreferens,
)
from .uppslag import Uppslag

UTRUM, NEUTRUM = 1, 2

# Tidsreferens + aspekt → verbcell. Svenskan saknar morfologisk aspekt, så
# axeln ignoreras här — men den finns i specifikationen för fr/es/it, där
# "il donnait" och "il a donné" skiljs åt just på den.
TEMPUSCELL = {
    Tidsreferens.NUTID: "pres",
    Tidsreferens.FÖRFLUTEN: "pret",
}

SUBSTANTIVCELL = {
    (Bestämdhet.OBESTÄMD, Numerus.SG): "obest_sg_ack_dat_nom",
    (Bestämdhet.BESTÄMD, Numerus.SG): "best_sg_ack_dat_nom",
    (Bestämdhet.OBESTÄMD, Numerus.PL): "obest_pl_ack_dat_nom",
    (Bestämdhet.BESTÄMD, Numerus.PL): "best_pl_ack_dat_nom",
}


def _adjektivcell(bestämdhet: Bestämdhet, numerus: Numerus, genus: int,
                  efter_possessiv: bool = False) -> str:
    """Svensk adjektivkongruens.

    Cellnamnen använder m/f för utrum/neutrum enligt _legend.yaml, där
    UtrMask och NeuFem delas mellan svenska och de romanska språken.

    En possessiv tvingar fram den bestämda (svaga) formen oavsett frasens
    bestämdhet: "sin röda bok", aldrig "sin röd bok". Possessiven beter sig
    som en bestämd artikel för adjektivet, trots att substantivet samtidigt
    står i obestämd form. Svenskan drar alltså isär de två.
    """
    if efter_possessiv or bestämdhet is Bestämdhet.BESTÄMD:
        return "best_a_sg_pos" if numerus is Numerus.SG else "best_a_pl_pos"
    if numerus is Numerus.PL:
        return "obest_a_pl_pos"
    return "obest_m_sg_pos" if genus == UTRUM else "obest_f_sg_pos"


def _artikelcell(numerus: Numerus, genus: int) -> str:
    """Fristående bestämd artikel: den / det / de."""
    if numerus is Numerus.PL:
        return "pl"
    return "utr" if genus == UTRUM else "neu"


def _possessivcell(numerus: Numerus, genus: int) -> str:
    """Possessiven kongruerar med det ÄGDA, inte med ägaren.

    "sin bror" (utrum) mot "sitt hus" (neutrum) — ägaren är samma flicka i
    båda. Det var precis det PARAMETER_AUDIT §1b handlade om.
    """
    if numerus is Numerus.PL:
        return "a_pl"
    return "m_sg" if genus == UTRUM else "f_sg"


class SvenskRenderare:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, "sv")

    # ── nominalfras ──────────────────────────────────────────────────

    def nominalfras(self, nf: Nominalfras, *, subjekt: bool = False) -> list[str]:
        huvud = self.u.lexem(nf.koncept)

        # Svenskan har kasus — men bara på pronomen. "jag" mot "mig" är den
        # enda morfologiska kasusdistinktionen språket har kvar, och därför
        # behöver renderaren veta om frasen är subjekt. Det syntes inte
        # förrän tyskan tvingade fram rollbegreppet.
        if huvud["ordklass"] == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"sv/{huvud['lemma']}: ett pronomen kan inte ta artikel, "
                    f"attribut eller possessiv")
            return [self.u.form(huvud, "nom" if subjekt else "ack_dat")]

        genus = huvud["genus"]
        if genus is None:
            raise RenderingsFel(
                f"sv/{huvud['lemma']}: genus saknas — artikel och "
                f"adjektivkongruens går inte att avgöra utan det")

        ord: list[str] = []

        # Bestämdhet realiseras olika beroende på vad som står framför
        # huvudordet: suffix i "flickan", fristående artikel i "en bok",
        # och ingen artikel alls när en possessiv tar platsen ("sin bror").
        if nf.possessiv is not None:
            # Possessiven tar artikelns plats: "sin bror", aldrig "sin en bror".
            # Substantivet står i obestämd form trots att frasen är bestämd.
            variant = "reflexiv" if nf.possessiv_koreferent else "icke_reflexiv"
            ord.append(self.u.form_för(
                nf.possessiv, _possessivcell(nf.numerus, genus), variant))
            substantivform = Bestämdhet.OBESTÄMD
        elif nf.bestämdhet is Bestämdhet.BESTÄMD and nf.attribut:
            # Svenskans dubbla bestämdhet: "den röda boken" kräver BÅDE den
            # fristående artikeln och suffixet på substantivet. Utan attribut
            # räcker suffixet ensamt ("boken"), och "den boken" skulle bli
            # demonstrativt i stället för bestämt.
            ord.append(self.u.form_för("artikel_bestamd", _artikelcell(nf.numerus, genus)))
            substantivform = Bestämdhet.BESTÄMD
        elif nf.bestämdhet is Bestämdhet.OBESTÄMD and nf.numerus is Numerus.SG:
            ord.append(self.u.form_för(
                "artikel_obestamd", "utr" if genus == UTRUM else "neu"))
            substantivform = Bestämdhet.OBESTÄMD
        else:
            # Obestämd plural har ingen artikel i svenskan ("böcker"), och
            # bestämdhet uttrycks med suffix på substantivet.
            substantivform = nf.bestämdhet

        for attribut in nf.attribut:
            ord.append(self.u.form_för(attribut, _adjektivcell(
                nf.bestämdhet, nf.numerus, genus,
                efter_possessiv=nf.possessiv is not None)))

        cell = SUBSTANTIVCELL[(substantivform, nf.numerus)]
        try:
            ord.append(self.u.form(huvud, cell))
        except RenderingsFel:
            # Plurale tantum: "pengar" har ingen singular alls. Datan har
            # ingen flagga för det — tomma singularceller ÄR markeringen.
            # Säg det rakt ut i stället för att låta felet se ut som ett hål.
            celler = self.u._celler(huvud)
            if nf.numerus is Numerus.SG and not any(
                    celler.get(c) for (_, n), c in SUBSTANTIVCELL.items()
                    if n is Numerus.SG):
                raise RenderingsFel(
                    f"sv/{huvud['lemma']}: saknar singular helt (plurale tantum) "
                    f"— meningen kan inte be om {nf.numerus.value}") from None
            raise
        return ord

    # ── sats ─────────────────────────────────────────────────────────

    def verbfras(self, m: Mening) -> list[str]:
        """Verbet, som ett eller flera ord.

        Svenskan har ingen syntetisk futurumform. "ska ge" byggs av
        modalverbet i presens plus huvudverbets infinitiv — samma sorts
        analytiska konstruktion som en/de använder, och skälet till att
        returtypen är en lista och inte en sträng.
        """
        lexem = self.u.lexem(m.verb)
        suffix = "_passiv" if self._deponens(lexem) else ""
        if m.tid is Tidsreferens.FRAMTID:
            return [self.u.form_för("modal_ska", "pres"),
                    self.u.form(lexem, "inf" + suffix)]
        return [self.u.form(lexem, TEMPUSCELL[m.tid] + suffix)]

    def _deponens(self, lexem) -> bool:
        """Deponens: verb som bara finns i s-form (minnas, hoppas, trivas).

        De har ingen aktiv böjning alls — "minnas/minns/mindes" ligger under
        diates=Passiv i Former, och de aktiva cellerna är tomma. Att läsa av
        det ur datan är säkrare än en lista över deponensverb: tom aktiv
        infinitiv plus fylld passiv är precis vad deponens betyder här.
        """
        celler = self.u._celler(lexem)
        return not celler.get("inf") and bool(celler.get("inf_passiv"))

    def rendera(self, m: Mening) -> str:
        """Svensk huvudsats: subjekt, verb, indirekt objekt, objekt, adverbial.

        Ordföljden är hårdkodad här och inte datadriven. Det är medvetet så
        länge bara svenskan finns — tyskans V2 och japanskans SOV kommer att
        kräva en riktig ordföljdsmodell, och den byggs när det andra språket
        visar vilken form den behöver ha, inte innan.
        """
        ord = list(self.nominalfras(m.subjekt, subjekt=True))
        ord.extend(self.verbfras(m))
        for nf in (m.io, m.objekt):
            if nf is not None:
                ord.extend(self.nominalfras(nf))
        for adverbial in m.adverbial:
            ord.append(self.u.form_för(adverbial, "pos"))

        mening = " ".join(ord)
        return mening[0].upper() + mening[1:] + "."
