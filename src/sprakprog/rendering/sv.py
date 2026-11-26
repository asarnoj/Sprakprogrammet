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


def _adjektivcell(bestämdhet: Bestämdhet, numerus: Numerus, genus: int) -> str:
    """Svensk adjektivkongruens.

    Cellnamnen använder m/f för utrum/neutrum enligt _legend.yaml, där
    UtrMask och NeuFem delas mellan svenska och de romanska språken.
    """
    if bestämdhet is Bestämdhet.BESTÄMD:
        return "best_a_sg_pos" if numerus is Numerus.SG else "best_a_pl_pos"
    if numerus is Numerus.PL:
        return "obest_a_pl_pos"
    return "obest_m_sg_pos" if genus == UTRUM else "obest_f_sg_pos"


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

    def nominalfras(self, nf: Nominalfras) -> list[str]:
        huvud = self.u.lexem(nf.koncept)
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
            variant = "reflexiv" if nf.possessiv_koreferent else "icke_reflexiv"
            ord.append(self.u.form_för(
                nf.possessiv, _possessivcell(nf.numerus, genus), variant))
            substantivform = Bestämdhet.OBESTÄMD
        elif nf.bestämdhet is Bestämdhet.OBESTÄMD and nf.numerus is Numerus.SG:
            ord.append(self.u.form_för(
                "artikel_obestamd", "utr" if genus == UTRUM else "neu"))
            substantivform = Bestämdhet.OBESTÄMD
        else:
            # Obestämd plural har ingen artikel i svenskan ("böcker"), och
            # bestämdhet uttrycks med suffix på substantivet.
            substantivform = nf.bestämdhet

        if nf.attribut and nf.bestämdhet is Bestämdhet.BESTÄMD and nf.possessiv is None:
            # "den röda boken" kräver den fristående bestämda artikeln, som
            # inte finns som lexem — artikel_bestamd har inget sv-lemma
            # eftersom svenskans bestämda artikel normalt är ett suffix.
            # Dubbel bestämdhet är alltså ett äkta datahål, inte en glömska.
            raise RenderingsFel(
                "sv: bestämd nominalfras med attribut ('den röda boken') kräver "
                "den fristående artikeln 'den/det/de', som saknas i databasen — "
                "artikel_bestamd har inget svenskt lemma")

        for attribut in nf.attribut:
            ord.append(self.u.form_för(
                attribut, _adjektivcell(nf.bestämdhet, nf.numerus, genus)))

        ord.append(self.u.form(huvud, SUBSTANTIVCELL[(substantivform, nf.numerus)]))
        return ord

    # ── sats ─────────────────────────────────────────────────────────

    def verbform(self, m: Mening) -> str:
        if m.tid not in TEMPUSCELL:
            raise RenderingsFel(
                f"sv: {m.tid} är analytisk i svenskan ('ska ge') och kräver "
                f"hjälpverbskonstruktion, som inte är byggd än")
        return self.u.form_för(m.verb, TEMPUSCELL[m.tid])

    def rendera(self, m: Mening) -> str:
        """Svensk huvudsats: subjekt, verb, indirekt objekt, objekt, adverbial.

        Ordföljden är hårdkodad här och inte datadriven. Det är medvetet så
        länge bara svenskan finns — tyskans V2 och japanskans SOV kommer att
        kräva en riktig ordföljdsmodell, och den byggs när det andra språket
        visar vilken form den behöver ha, inte innan.
        """
        ord = list(self.nominalfras(m.subjekt))
        ord.append(self.verbform(m))
        for nf in (m.io, m.objekt):
            if nf is not None:
                ord.extend(self.nominalfras(nf))
        for adverbial in m.adverbial:
            ord.append(self.u.form_för(adverbial, "pos"))

        mening = " ".join(ord)
        return mening[0].upper() + mening[1:] + "."
