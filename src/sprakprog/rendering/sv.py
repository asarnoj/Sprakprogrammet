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
from dataclasses import replace

from .spec import (
    Aspekt, Bestämdhet, Diates, Grad, Mening, Nominalfras, Numerus, Prepositionsfras,
    RenderingsFel, Satsmodus, Tidsreferens, slutar, tilltal,
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

# Genitiv är svenskans enda kvarvarande kasus på substantiv.
SUBSTANTIVCELL_GEN = {
    (Bestämdhet.OBESTÄMD, Numerus.SG): "obest_sg_gen",
    (Bestämdhet.BESTÄMD, Numerus.SG): "best_sg_gen",
    (Bestämdhet.OBESTÄMD, Numerus.PL): "obest_pl_gen",
    (Bestämdhet.BESTÄMD, Numerus.PL): "best_pl_gen",
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


def _predikativcell(numerus: Numerus, genus: int) -> str:
    """Predikativt adjektiv tar OBESTÄMD form och kongruerar med subjektet.

    "hon är glad", "barnet är glatt", "de är glada". Aldrig den bestämda
    formen — "hon är glada" finns inte. Det skiljer predikativet från
    attributet, som styrs av frasens bestämdhet.
    """
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

    def nominalfras(self, nf: Nominalfras, *, subjekt: bool = False,
                    genitiv: bool = False) -> list[str]:
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

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
        if nf.ägare is not None:
            # "flickans bok" — ägaren står i genitiv FÖRE huvudordet, och
            # huvudordet blir obestämt precis som efter en possessiv.
            # Svenskan säger aldrig "flickans boken".
            ord.extend(self.nominalfras(nf.ägare, genitiv=True))
            substantivform = Bestämdhet.OBESTÄMD
        elif nf.possessiv is not None:
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
            # Genitivattribut styr adjektivet likadant som en possessiv:
            # "flickans röda bok", aldrig "flickans röd bok".
            ord.append(self.u.form_för(attribut, _adjektivcell(
                nf.bestämdhet, nf.numerus, genus,
                efter_possessiv=nf.possessiv is not None or nf.ägare is not None)))

        tabell = SUBSTANTIVCELL_GEN if genitiv else SUBSTANTIVCELL
        cell = tabell[(substantivform, nf.numerus)]
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

    def adverbial(self, a: str | Prepositionsfras) -> list[str]:
        """Adverb eller prepositionsfras — samma slot, två frastyper."""
        if isinstance(a, str):
            return [self.u.form_för(a, "pos")]
        return [self.u.form_för(a.preposition, "inv"),
                *self.nominalfras(a.komplement)]

    def komplement(self, m: Mening) -> list[str]:
        """Infinitivkomplement: "vill läsa", "börjar att läsa"."""
        markör = self.u.infinitivmarkör(m.verb)
        infinitiv = self.u.form_för(m.komplement, "inf")
        if markör is None:
            return [infinitiv]
        return [self.u.form_för(markör, "inv"), infinitiv]

    def predikativ(self, m: Mening) -> list[str]:
        if isinstance(m.predikativ, str):
            if m.grad is not Grad.POSITIV:
                return self._komparation(m)
            huvud = self.u.lexem(m.subjekt.koncept)
            genus = huvud["genus"] or UTRUM
            return [self.u.form_för(
                m.predikativ, _predikativcell(m.subjekt.numerus, genus))]
        # Predikativt substantiv står utan artikel: "hon är läkare".
        return [self.u.form(
            self.u.lexem(m.predikativ.koncept),
            SUBSTANTIVCELL[(Bestämdhet.OBESTÄMD, m.predikativ.numerus)])]

    def _komparation(self, m: Mening) -> list[str]:
        """Syntetisk komparation om formen finns, annars perifrastisk.

        "större" men "mer intressant" — svenskan avgör per ord, och datan
        vet vilket: adjektiv som saknar komp-cell kompareras analytiskt.
        Predikativ superlativ tar den OBESTÄMDA formen: "boken är störst",
        inte "störste".
        """
        cell = "komp" if m.grad is Grad.KOMPARATIV else "obest_superl"
        adjektiv = self.u.lexem(m.predikativ)
        form = self.u._celler(adjektiv).get(cell)
        if form:
            ut = [self.u.form(adjektiv, cell)]
        else:
            markör = "komp_mer" if m.grad is Grad.KOMPARATIV else "komp_mest"
            huvud = self.u.lexem(m.subjekt.koncept)
            ut = [self.u.form_för(markör, "pos"),
                  self.u.form_för(m.predikativ, _predikativcell(
                      m.subjekt.numerus, huvud["genus"] or UTRUM))]
        if m.jämförelse is not None:
            ut.append(self.u.form_för("komp_än", "inv"))
            ut += self.nominalfras(m.jämförelse)
        return ut

    def verbfras(self, m: Mening) -> list[str]:
        """Verbet, som ett eller flera ord.

        Svenskan har ingen syntetisk futurumform. "ska ge" byggs av
        modalverbet i presens plus huvudverbets infinitiv — samma sorts
        analytiska konstruktion som en/de använder, och skälet till att
        returtypen är en lista och inte en sträng.
        """
        lexem = self.u.lexem(m.verb)
        if m.modus is Satsmodus.IMPERATIV:
            # Svenskan har EN imperativform för alla tilltal: "läs!" säger
            # man till en som till många. Tilltalet läses ändå ut, för att
            # ett subjekt som inte är någon tilltalad ska stoppas här och
            # inte tyst rendera en uppmaning till tredje person.
            tilltal(m, "sv", ("2sg", "2pl", "artig"))
            return [self.u.form(lexem, "imp")]
        if m.diates is Diates.PASSIV_HÄNDELSE:
            # "boken blev läst" — bli plus perfektparticip, som kongruerar
            # med subjektet. Den betonar händelsen; s-passiven är omarkerad.
            huvud = self.u.lexem(m.subjekt.koncept)
            genus = huvud["genus"] or UTRUM
            cell = ("perfpart_a" if m.subjekt.numerus is Numerus.PL
                    else "perfpart_obest_utr_sg" if genus == UTRUM
                    else "perfpart_obest_neu_sg")
            # Bli bär hela tempus- och aspektapparaten och böjs som vilket
            # verb som helst: "ska bli läst", "har blivit läst". Den går
            # därför genom den aktiva grenen i stället för att få egna
            # tempusfall här — annars måste varje ny tempusform skrivas in
            # på två ställen, och passiven blir efter.
            hjälp = replace(m, verb="verb_bli", diates=Diates.AKTIV)
            return [*self.verbfras(hjälp), self.u.form(lexem, cell)]
        # S-passiven är svenskans omarkerade: läses, lästes, lästs. Den
        # ligger som egna celler i Former, inte som en konstruktion.
        suffix = ("_passiv" if m.diates is Diates.PASSIV
                  or self._deponens(lexem) else "")
        if m.aspekt is Aspekt.PERFEKT:
            # "har läst" / "hade läst" — hjälpverbet bär tempus, supinumet
            # är oföränderligt. Svenskan använder alltid ha, aldrig vara.
            hjälpcell = "pret" if m.tid is Tidsreferens.FÖRFLUTEN else "pres"
            return [self.u.form_för("verb_ha", hjälpcell),
                    self.u.form(lexem, "sup" + suffix)]
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
        verb = self.verbfras(m)
        # Imperativen säger inte ut den tilltalade: "läs boken!". Subjektet
        # finns kvar i specen och har redan prövats mot verbets krav — det
        # är bara ordet som uteblir.
        if m.modus is Satsmodus.IMPERATIV:
            subjekt: list[str] = []
        else:
            subjekt = self.nominalfras(m.subjekt, subjekt=True)
        # Ja/nej-fråga är ren omkastning: det finita verbet först, subjektet
        # sedan. Samma sats, annan ordning — inget ord läggs till.
        ord = [verb[0], *subjekt] if m.fråga else [*subjekt, verb[0]]
        if m.negerad:
            # Satsadverbialet står efter det FINITA verbet: "ska inte ge",
            # inte "ska ge inte". Därför delas verbfrasen här.
            ord.append(self.u.form_för("neg_inte", "inv"))
        ord.extend(verb[1:])
        for nf in (m.io, m.objekt):
            if nf is not None:
                ord.extend(self.nominalfras(nf))
        if m.komplement is not None:
            ord.extend(self.komplement(m))
        if m.predikativ is not None:
            ord.extend(self.predikativ(m))
        for adverbial in m.adverbial:
            ord.extend(self.adverbial(adverbial))

        mening = " ".join(ord)
        return mening[0].upper() + mening[1:] + slutar(m)
