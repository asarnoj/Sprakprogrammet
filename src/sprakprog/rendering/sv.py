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

REDOVISNINGEN (KÄRNAN 8.3, steg 1). Varje beslut går genom `Uppslag`: valen
mellan utfall som `regel`, ordföljden som `ordning`, ordens egenskaper som
`egenskap` och verbets krav som `rektion`. Valen står uppräknade nedan med
sina utfall, och koden grenar på det utfall `regel` lämnar tillbaka — inte på
specen. Det är det som gör att ett beslut kan tvingas fram och dess positioner
räknas ut (`rendering/spår.py`).

Id:na i kommentarerna (G1, S1 …) är inventeringen i `paradigm/TYSTA_BESLUT.md`.
"""

from __future__ import annotations

import sqlite3

from .spec import (
    Aspekt, Attribut, Bestämdhet, Bisats, Diates, Grad, Mening, Nominalfras,
    NAKEN, Numerus, kontrollera_stöd, attribut_med_grad,
    Prepositionsfras,
    FRÅGESLOTTAR, RenderingsFel, Satsmodus, Tidsreferens, slutar,
)
from .uppslag import Ord, Uppslag, Val, frasdel

UTRUM, NEUTRUM = 1, 2

# ── besluten ─────────────────────────────────────────────────────────────

#: G1. jag/mig — pronomenets form efter roll.
PRONOMENFORM = Val("pronomenform", ("subjektsform", "objektsform"))

#: G2–G7, S1. Vad som står före huvudordet och vilken form huvudordet får:
#: "vilken bok", "flickans bok", "sin bok", "den röda boken", "vatten",
#: "en bok", "boken", "böcker".
BESTÄMNING = Val("bestämning", (
    "frågedeterminant", "genitiv", "possessiv", "demonstrativ",
    "dubbel_bestämdhet", "naken", "obestämd_artikel", "bestämd_suffix",
    "obestämd_plural"))

#: G8, G9, S2. Adjektivets form, attributivt och predikativt: "röda", "röda",
#: "röd", "rött".
ADJEKTIVFORM = Val("adjektivform", ("svag", "plural", "utrum", "neutrum"))

#: G12, S4. "den största boken" men "boken är störst".
SUPERLATIVFORM = Val("superlativform", ("bestämd", "obestämd"))

#: G10. "hon är läkare", inte "hon är en läkare".
PREDIKATIVT_SUBSTANTIV = Val("predikativt_substantiv",
                             ("utan_artikel", "med_artikel"))

#: G16, G17. "läser", "läste", "ska läsa", "har läst", "hade läst", "ska ha läst".
TEMPUSFORM = Val("tempusform", (
    "presens", "preteritum", "futurum", "perfekt", "pluskvamperfekt",
    "futurum_perfekt"))

#: G18. "boken lästes" eller "boken blev läst".
PASSIVFORM = Val("passivform", ("s_passiv", "bli_passiv"))

#: S5. Bli-passivens particip kongruerar: "blev läst", "blev målat", "blev lästa".
PARTICIPFORM = Val("participform", ("utrum", "neutrum", "plural"))

#: G21. "läs boken!" eller "du läser boken".
SATSART = Val("satsart", ("indikativ", "imperativ"))

#: G19, S6. Reflexivet kongruerar med subjektet, och artigt ni tar er.
REFLEXIVPRONOMEN = Val("reflexivpronomen", ("mig", "dig", "sig", "oss", "er"))

#: G20. vem eller vad.
FRÅGEPRONOMEN = Val("frågepronomen", ("person", "sak"))

# ── celler ───────────────────────────────────────────────────────────────

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

#: Bestämningens utfall → huvudordets bestämdhet. Efter en possessiv, en
#: genitiv eller en frågedeterminant står huvudordet obestämt: "sin bok",
#: "flickans bok", "vilken bok" — aldrig "sin boken".
HUVUDORDETS_BESTÄMDHET = {
    "frågedeterminant": Bestämdhet.OBESTÄMD, "genitiv": Bestämdhet.OBESTÄMD,
    "possessiv": Bestämdhet.OBESTÄMD, "dubbel_bestämdhet": Bestämdhet.BESTÄMD,
    # "den här boken": den analytiska demonstrativen tar suffixet med sig.
    "demonstrativ": Bestämdhet.BESTÄMD,
    "naken": Bestämdhet.OBESTÄMD, "obestämd_artikel": Bestämdhet.OBESTÄMD,
    "bestämd_suffix": Bestämdhet.BESTÄMD, "obestämd_plural": Bestämdhet.OBESTÄMD,
}

#: Bestämningar som ger adjektivet svag form: "den röda boken", "sin röda bok",
#: "flickans röda bok". En frågedeterminant gör det inte: "vilken röd bok".
SVAG_BESTÄMNING = frozenset({"genitiv", "possessiv", "dubbel_bestämdhet",
                             "bestämd_suffix", "demonstrativ"})

#: Reflexivpronomenets utfall → koncept. Bara tredje person har ett eget
#: reflexivt pronomen — "sig" — medan första och andra använder sitt vanliga
#: objektspronomen: mig, dig, oss, er.
REFLEXIVKONCEPT = {"mig": "pronomen_1sg", "dig": "pronomen_2sg",
                   "oss": "pronomen_1pl", "er": "pronomen_2pl",
                   "sig": "pronomen_reflexiv"}
REFLEXIV_EFTER_PERSON = {(1, "sg"): "mig", (2, "sg"): "dig",
                         (1, "pl"): "oss", (2, "pl"): "er"}


def _adjektivcell(utfall: str, numerus: Numerus) -> str:
    """Adjektivformens cell. Cellnamnen använder m/f för utrum/neutrum
    enligt _legend.yaml, där UtrMask och NeuFem delas med de romanska språken.
    """
    if utfall == "svag":
        return "best_a_sg_pos" if numerus is Numerus.SG else "best_a_pl_pos"
    return {"plural": "obest_a_pl_pos", "utrum": "obest_m_sg_pos",
            "neutrum": "obest_f_sg_pos"}[utfall]


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

    @frasdel
    def nominalfras(self, nf: Nominalfras, *, subjekt: bool = False,
                    genitiv: bool = False) -> list[Ord]:
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

        # Svenskan har kasus — men bara på pronomen. "jag" mot "mig" är den
        # enda morfologiska kasusdistinktionen språket har kvar, och därför
        # behöver renderaren veta om frasen är subjekt. Det syntes inte
        # förrän tyskan tvingade fram rollbegreppet.
        if self.u.ordklass(huvud) == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"sv/{self.u.lemma(huvud)}: ett pronomen kan inte ta "
                    f"artikel, attribut eller possessiv")
            if genitiv:
                # Specens ägare är ett substantiv; en pronominell ägare är en
                # possessiv. Förut blev det "mig bok".
                raise RenderingsFel(
                    f"sv/{self.u.lemma(huvud)}: en pronominell ägare uttrycks "
                    f"med possessiv ('min bok'), inte med genitiv")
            form = self.u.regel(PRONOMENFORM,
                                "subjektsform" if subjekt else "objektsform")
            return [self.u.form(huvud, "nom" if form == "subjektsform"
                                else "ack_dat")]

        self.u.kontrollera_naken(nf)
        kontrollera_stöd(nf, "sv", ("demonstrativ", "räkneord"))

        # Genus avgör artikel, possessiv och adjektiv bara i singular — "de
        # stora böckerna", "de stora husen". Egenskapen läses ändå alltid;
        # att den inte syns i plural räknar spåret ut (rendering/spår.py).
        genus = self.u.egenskap(huvud, "genus")
        if genus is None:
            raise RenderingsFel(
                f"sv/{self.u.lemma(huvud)}: genus saknas — artikel och "
                f"adjektivkongruens går inte att avgöra utan det")

        if nf.frågedeterminant is not None:
            naturlig = "frågedeterminant"
        elif nf.ägare is not None:
            naturlig = "genitiv"
        elif nf.possessiv is not None:
            naturlig = "possessiv"
        elif nf.demonstrativ is not None:
            naturlig = "demonstrativ"
        elif nf.bestämdhet is Bestämdhet.BESTÄMD and (nf.attribut
                                                      or nf.räkneord is not None):
            # Räkneordet utlöser den dubbla bestämdheten precis som ett
            # attribut gör: "de två böckerna", aldrig "två böckerna".
            naturlig = "dubbel_bestämdhet"
        elif nf.bestämdhet in NAKEN:
            naturlig = "naken"
        elif nf.bestämdhet is Bestämdhet.OBESTÄMD and nf.numerus is Numerus.SG:
            naturlig = "obestämd_artikel"
        elif nf.bestämdhet is Bestämdhet.BESTÄMD:
            naturlig = "bestämd_suffix"
        else:
            naturlig = "obestämd_plural"
        bestämning = self.u.regel(BESTÄMNING, naturlig)

        före: list[Ord] = []
        if bestämning == "frågedeterminant":
            # "vilken bok" — frågedeterminanten tar artikelns plats.
            if nf.frågedeterminant is None:
                raise RenderingsFel("sv: frasen har ingen frågedeterminant")
            före = [self.u.form_för(nf.frågedeterminant, _artikelcell(
                nf.numerus, genus).replace("utr", "utr_sg").replace("neu", "neu_sg"))]
        elif bestämning == "genitiv":
            # "flickans bok" — ägaren står i genitiv FÖRE huvudordet.
            if nf.ägare is None:
                raise RenderingsFel("sv: frasen har ingen genitivägare")
            with self.u.led("ägare"):
                före = self.nominalfras(nf.ägare, genitiv=True)
        elif bestämning == "possessiv":
            # Possessiven tar artikelns plats: "sin bror", aldrig "sin en bror".
            if nf.possessiv is None:
                raise RenderingsFel("sv: frasen har ingen possessiv")
            variant = "reflexiv" if nf.possessiv_koreferent else "icke_reflexiv"
            före = [self.u.form_för(
                nf.possessiv, _possessivcell(nf.numerus, genus), variant)]
        elif bestämning == "demonstrativ":
            # "den här boken" — demonstrativen kongruerar i genus och numerus
            # OCH tar suffixet med sig, precis som den dubbla bestämdheten.
            #
            # Varianten är den ANALYTISKA: svenskan har två konstruktioner
            # för samma koncept, "den här boken" och "denna bok", men bara
            # den analytiska finns för båda demonstrativerna — den fjärran
            # har inget "denne". Att den syntetiska också är riktig svenska
            # är en sak för entydighetsfiltret (KÄRNAN 6.5).
            if nf.demonstrativ is None:
                raise RenderingsFel("sv: frasen har ingen demonstrativ")
            före = [self.u.form_för(nf.demonstrativ, _artikelcell(
                nf.numerus, genus).replace("utr", "utr_sg").replace("neu", "neu_sg"),
                "analytisk")]
        elif bestämning == "dubbel_bestämdhet":
            # Svenskans dubbla bestämdhet: "den röda boken" kräver BÅDE den
            # fristående artikeln och suffixet på substantivet. Utan attribut
            # räcker suffixet ensamt ("boken").
            före = [self.u.form_för("artikel_bestamd",
                                    _artikelcell(nf.numerus, genus))]
        elif bestämning == "obestämd_artikel":
            före = [self.u.form_för("artikel_obestamd",
                                    "utr" if genus == UTRUM else "neu")]
        # naken ("vatten"), bestämd_suffix ("boken") och obestämd_plural
        # ("böcker") har inget ord före huvudordet.

        räkneord: list[Ord] = []
        if nf.räkneord is not None:
            # "de två böckerna": räkneordet står EFTER bestämningen och FÖRE
            # attributen.
            self.u.kontrollera_räkneord(nf)
            with self.u.led("räkneord"):
                räkneord = [self.u.form_för(nf.räkneord, "inv")]

        attribut: list[Ord] = []
        for i, a in enumerate(nf.attribut):
            with self.u.led(f"attribut{i}"):
                attribut.extend(self.attribut(a, bestämning, nf.numerus, genus))

        tabell = SUBSTANTIVCELL_GEN if genitiv else SUBSTANTIVCELL
        cell = tabell[(HUVUDORDETS_BESTÄMDHET[bestämning], nf.numerus)]
        try:
            huvudord = self.u.form(huvud, cell)
        except RenderingsFel:
            # Plurale tantum: "pengar" har ingen singular alls. Datan har
            # ingen flagga för det — tomma singularceller ÄR markeringen.
            if nf.numerus is Numerus.SG and not any(
                    self.u.har_form(huvud, c)
                    for (_, n), c in SUBSTANTIVCELL.items() if n is Numerus.SG):
                raise RenderingsFel(
                    f"sv/{self.u.lemma(huvud)}: saknar singular helt (plurale "
                    f"tantum) — meningen kan inte be om {nf.numerus.value}") from None
            raise
        efter = [*räkneord, *attribut, huvudord]
        self.u.ordning("bestämning_före_huvudord", före, efter)
        self.u.ordning("räkneord_före_attribut", räkneord, [*attribut, huvudord])
        self.u.ordning("attribut_före_huvudord", attribut, [huvudord])
        return [*före, *efter]

    # ── adjektiv ─────────────────────────────────────────────────────

    def _adjektiv(self, koncept: str, svag: bool, numerus: Numerus,
                  genus: int) -> Ord:
        """Adjektivet i positiv, i den form bestämningen och kongruensen ger.

        Predikativt tar adjektivet alltid obestämd form och kongruerar med
        subjektet: "hon är glad", "barnet är glatt", "de är glada".
        """
        if svag:
            naturlig = "svag"
        elif numerus is Numerus.PL:
            naturlig = "plural"
        else:
            naturlig = "utrum" if genus == UTRUM else "neutrum"
        form = self.u.regel(ADJEKTIVFORM, naturlig)
        return self.u.form_för(koncept, _adjektivcell(form, numerus))

    @frasdel
    def attribut(self, a: str | Attribut, bestämning: str, numerus: Numerus,
                 genus: int) -> list[Ord]:
        """Attributivt adjektiv i sin grad.

        Komparativen är OBÖJLIG i svenskan — "en större bok", "det större
        huset", "de större böckerna" är alla samma form. Superlativen böjs
        däremot, och attributivt tar den ALLTID den bestämda formen:
        "den största boken", aldrig "en störst bok".

        Kompareras ordet perifrastiskt är det MARKÖREN som bär graden medan
        adjektivet står i positiv: "den mest intressanta boken".
        """
        a = attribut_med_grad(a)
        svag = bestämning in SVAG_BESTÄMNING
        lexem_ = self.u.lexem(a.koncept)
        if self.u.ordklass(lexem_) == "Räkneord/ordningstal":
            # "den andra boken". Ordningstalet böjs som ett adjektiv men
            # kompareras inte — "mer andra" finns inte.
            if a.grad is not Grad.POSITIV:
                raise RenderingsFel(
                    f"sv/{self.u.lemma(lexem_)}: ett ordningstal kompareras inte")
            if numerus is Numerus.PL:
                return [self.u.form(lexem_, "a_pl")]
            return [self.u.form(lexem_, "best_a_sg" if svag else "obest_a_sg")]
        if a.grad is Grad.POSITIV:
            return [self._adjektiv(a.koncept, svag, numerus, genus)]

        if a.grad is Grad.SUPERLATIV and not svag:
            # "en störst bok" finns inte. Attributiv superlativ pekar ut ett
            # unikt exemplar och är därför alltid bestämd.
            raise RenderingsFel(
                f"sv/{a.koncept}: attributiv superlativ kräver bestämd fras "
                f"— 'den största boken', inte 'en störst bok'")
        lexem = self.u.lexem(a.koncept)
        if self.u.egenskap(lexem, "komparation") == "syntetisk":
            if a.grad is Grad.KOMPARATIV:
                return [self.u.form(lexem, "komp")]
            form = self.u.regel(SUPERLATIVFORM, "bestämd")
            return [self.u.form(lexem, "best_superl" if form == "bestämd"
                                else "obest_superl")]
        markör = self.u.form_för(
            "komp_mer" if a.grad is Grad.KOMPARATIV else "komp_mest", "pos")
        adjektiv = self._adjektiv(a.koncept, svag, numerus, genus)
        self.u.ordning("komparationsmarkör_före", [markör], [adjektiv])
        return [markör, adjektiv]

    # ── satsens delar ────────────────────────────────────────────────

    @frasdel
    def adverbial(self, a: str | Prepositionsfras | Bisats) -> list[Ord]:
        """Adverb, prepositionsfras eller bisats — samma slot, tre frastyper."""
        if isinstance(a, str):
            return [self.u.form_för(a, "pos")]
        if isinstance(a, Bisats):
            return self.bisats(a)
        preposition = self.u.form_för(a.preposition, "inv")
        with self.u.led("komplement"):
            komplement = self.nominalfras(a.komplement)
        self.u.ordning("preposition_före_komplement", [preposition], komplement)
        return [preposition, *komplement]

    @frasdel
    def komplement(self, m: Mening) -> list[Ord]:
        """Infinitivkomplement: "vill läsa", "börjar att läsa"."""
        markör = self.u.infinitivmarkör(m.verb)
        infinitiv = self.u.form_för(m.komplement, "inf")
        if markör is None:
            return [infinitiv]
        markörord = self.u.form_för(markör, "inv")
        self.u.ordning("infinitivmarkör_före", [markörord], [infinitiv])
        return [markörord, infinitiv]

    @frasdel
    def predikativ(self, m: Mening) -> list[Ord]:
        if isinstance(m.predikativ, str):
            if m.grad is not Grad.POSITIV:
                return self._komparation(m)
            genus = self.u.egenskap(self.u.lexem(m.subjekt.koncept), "genus") or UTRUM
            return [self._adjektiv(m.predikativ, False,
                                   self._subjektets_numerus(m.subjekt), genus)]
        # Predikativt substantiv står utan artikel: "hon är läkare".
        form = self.u.regel(PREDIKATIVT_SUBSTANTIV, "utan_artikel")
        lexem = self.u.lexem(m.predikativ.koncept)
        artikel: list[Ord] = []
        if form == "med_artikel":
            if m.predikativ.numerus is Numerus.PL:
                raise RenderingsFel("sv: obestämd artikel finns inte i plural")
            genus = self.u.egenskap(lexem, "genus")
            artikel = [self.u.form_för("artikel_obestamd",
                                       "utr" if genus == UTRUM else "neu")]
        substantiv = self.u.form(
            lexem, SUBSTANTIVCELL[(Bestämdhet.OBESTÄMD, m.predikativ.numerus)])
        self.u.ordning("bestämning_före_huvudord", artikel, [substantiv])
        return [*artikel, substantiv]

    def _komparation(self, m: Mening) -> list[Ord]:
        """Syntetisk komparation om formen finns, annars perifrastisk.

        "större" men "mer intressant" — svenskan avgör per ord, och datan
        vet vilket. Predikativ superlativ tar den OBESTÄMDA formen: "boken är
        störst", inte "största".
        """
        adjektiv = self.u.lexem(m.predikativ)
        if self.u.egenskap(adjektiv, "komparation") == "syntetisk":
            if m.grad is Grad.KOMPARATIV:
                ut = [self.u.form(adjektiv, "komp")]
            else:
                form = self.u.regel(SUPERLATIVFORM, "obestämd")
                ut = [self.u.form(adjektiv, "obest_superl" if form == "obestämd"
                                  else "best_superl")]
        else:
            markör = self.u.form_för(
                "komp_mer" if m.grad is Grad.KOMPARATIV else "komp_mest", "pos")
            genus = self.u.egenskap(self.u.lexem(m.subjekt.koncept), "genus") or UTRUM
            ord = self._adjektiv(m.predikativ, False,
                                 self._subjektets_numerus(m.subjekt), genus)
            self.u.ordning("komparationsmarkör_före", [markör], [ord])
            ut = [markör, ord]
        if m.jämförelse is not None:
            än = self.u.form_för("komp_än", "inv")
            with self.u.led("jämförelse"):
                jämfört = self.nominalfras(m.jämförelse)
            self.u.ordning("jämförelse_efter_adjektiv", ut, [än])
            self.u.ordning("än_före_jämförelseled", [än], jämfört)
            ut += [än, *jämfört]
        return ut

    @frasdel
    def verbfras(self, m: Mening, satsart: str, verb: str | None = None,
                 diates: Diates | None = None) -> list[Ord]:
        """Verbet, som ett eller flera ord.

        Svenskan har ingen syntetisk futurumform. "ska ge" byggs av
        modalverbet i presens plus huvudverbets infinitiv — samma sorts
        analytiska konstruktion som en/de använder, och skälet till att
        returtypen är en lista och inte en sträng.

        `verb` och `diates` skickas bara för bli-passivens hjälpverb: samma sats,
        ett annat verb, aktiv diates. Att skicka dem i stället för att kopiera
        specen gör att kartan ser exakt vad som ändrades (KÄRNAN 6.7).
        """
        verb = m.verb if verb is None else verb
        diates = m.diates if diates is None else diates
        lexem = self.u.lexem(verb)
        if satsart == "imperativ":
            # Svenskan har EN imperativform för alla tilltal: "läs!" säger
            # man till en som till många. Tilltalet läses ändå ut, för att
            # ett subjekt som inte är någon tilltalad ska stoppas här och
            # inte tyst rendera en uppmaning till tredje person.
            tal = self.u.tilltal(m.subjekt.koncept)
            if tal is None:
                raise RenderingsFel(
                    f"sv: imperativens subjekt måste vara den tilltalade, "
                    f"inte {m.subjekt.koncept!r}")
            if tal not in ("2sg", "2pl", "artig"):
                raise RenderingsFel(
                    f"sv: saknar imperativform för {tal} — svenskan uttrycker "
                    f"det med en omskrivning")
            return [self.u.form(lexem, "imp")]

        passiv = None
        if diates is not Diates.AKTIV:
            passiv = self.u.regel(PASSIVFORM, "bli_passiv"
                                  if diates is Diates.PASSIV_HÄNDELSE
                                  else "s_passiv")
        if passiv == "bli_passiv":
            # "boken blev läst" — bli plus perfektparticip, som kongruerar
            # med subjektet. Bli bär hela tempus- och aspektapparaten och
            # böjs som vilket verb som helst, så det går genom den aktiva
            # grenen i stället för att få egna tempusfall här.
            genus = self.u.egenskap(self.u.lexem(m.subjekt.koncept), "genus") or UTRUM
            if self._subjektets_numerus(m.subjekt) is Numerus.PL:
                naturlig = "plural"
            else:
                naturlig = "utrum" if genus == UTRUM else "neutrum"
            form = self.u.regel(PARTICIPFORM, naturlig)
            cell = {"plural": "perfpart_a", "utrum": "perfpart_obest_utr_sg",
                    "neutrum": "perfpart_obest_neu_sg"}[form]
            with self.u.led("hjälpverb"):
                hjälpverb = self.verbfras(m, satsart, verb="verb_bli",
                                         diates=Diates.AKTIV)
            particip = self.u.form(lexem, cell)
            self.u.ordning("hjälpverb_före_huvudverb", hjälpverb, [particip])
            return [*hjälpverb, particip]

        # S-passiven är svenskans omarkerade: läses, lästes, lästs. Den
        # ligger som egna celler i Former, inte som en konstruktion.
        suffix = "_passiv" if passiv == "s_passiv" or self._deponens(lexem) else ""
        if m.aspekt is Aspekt.PERFEKT:
            naturlig = {Tidsreferens.FÖRFLUTEN: "pluskvamperfekt",
                        Tidsreferens.FRAMTID: "futurum_perfekt"}.get(m.tid, "perfekt")
        elif m.tid is Tidsreferens.FRAMTID:
            naturlig = "futurum"
        elif m.tid is Tidsreferens.FÖRFLUTEN:
            naturlig = "preteritum"
        else:
            naturlig = "presens"
        tempus = self.u.regel(TEMPUSFORM, naturlig)
        if tempus in ("perfekt", "pluskvamperfekt"):
            # "har läst" / "hade läst" — hjälpverbet bär tempus, supinumet
            # är oföränderligt. Svenskan använder alltid ha, aldrig vara.
            hjälp = self.u.form_för(
                "verb_ha", "pret" if tempus == "pluskvamperfekt" else "pres")
            huvud = self.u.form(lexem, "sup" + suffix)
        elif tempus == "futurum_perfekt":
            # "ska ha läst" — förut blev det "har läst".
            ska = self.u.form_för("modal_ska", "pres")
            ha = self.u.form_för("verb_ha", "inf")
            huvud = self.u.form(lexem, "sup" + suffix)
            self.u.ordning("hjälpverb_före_huvudverb", [ska], [ha])
            self.u.ordning("hjälpverb_före_huvudverb", [ha], [huvud])
            return [ska, ha, huvud]
        elif tempus == "futurum":
            hjälp = self.u.form_för("modal_ska", "pres")
            huvud = self.u.form(lexem, "inf" + suffix)
        else:
            return [self.u.form(
                lexem, ("pres" if tempus == "presens" else "pret") + suffix)]
        self.u.ordning("hjälpverb_före_huvudverb", [hjälp], [huvud])
        return [hjälp, huvud]

    def _subjektets_numerus(self, nf: Nominalfras) -> Numerus:
        """Numeruset predikativet och bli-participet kongruerar med.

        Ett pronomen bär sitt numerus självt — "de är glada", "vi blev lurade" —
        oavsett vad frasen säger. Förut lästes frasens numerus, som för ett
        pronomen står kvar på singular, och facit blev "De är modig".
        """
        if (self.u.ordklass(self.u.lexem(nf.koncept)) == "Pronomen"
                and self.u.koncept(nf.koncept, "numerus") == 2):
            return Numerus.PL
        return nf.numerus

    def _deponens(self, lexem) -> bool:
        """Deponens: verb som bara finns i s-form (minnas, hoppas, trivas).

        De har ingen aktiv böjning alls — "minnas/minns/mindes" ligger under
        diates=Passiv i Former, och de aktiva cellerna är tomma. Att läsa av
        det ur datan är säkrare än en lista över deponensverb.
        """
        return (not self.u.har_form(lexem, "inf")
                and self.u.har_form(lexem, "inf_passiv"))

    @frasdel
    def reflexivpronomen(self, m: Mening) -> Ord | None:
        """Verbets reflexiva pronomen i subjektets person, annars None.

        Svenskans reflexiv kongruerar med subjektet: jag skyndar mig, vi
        skyndar oss, ni skyndar er. Att verbet är reflexivt är en egenskap hos
        verbet som syns på pronomenet (KÄRNAN 3.5).
        """
        if not self.u.egenskap(self.u.lexem(m.verb, None), "reflexiv"):
            return None
        nf = m.subjekt
        if self.u.tilltal(nf.koncept) == "artig":
            # Artigt `ni` är andra person SINGULAR i Koncept men tar
            # pluralens `er`. Utan undantaget blev det "ni skyndar dig".
            naturlig, koncept = "er", "pronomen_2sg_formal"
        else:
            person = self.u.koncept(nf.koncept, "person") or 3
            numerus = ("pl" if nf.numerus is Numerus.PL
                       or self.u.koncept(nf.koncept, "numerus") == 2 else "sg")
            naturlig = REFLEXIV_EFTER_PERSON.get((person, numerus), "sig")
            koncept = REFLEXIVKONCEPT[naturlig]
        utfall = self.u.regel(REFLEXIVPRONOMEN, naturlig)
        if utfall != naturlig:
            koncept = REFLEXIVKONCEPT[utfall]
        return self.u.form_för(koncept, "ack_dat")

    # ── satsen ───────────────────────────────────────────────────────

    @frasdel
    def satsled(self, m: Mening, bisats: bool = False) -> list[Ord]:
        """Satsens ord, utan skiljetecken och utan inledande subjunktion.

        `bisats` styr EN sak, och det är hela skillnaden mellan svensk huvud-
        och bisatsordföljd: satsadverbialet står FÖRE det finita verbet i
        bisats — "att han inte kom" mot "han kom inte". BIFF-regeln.
        """
        if m.fråga and m.fråga_om is not None:
            raise RenderingsFel("sv: en sats kan inte vara både ja/nej-fråga "
                                "och frågeordsfråga")
        if m.modus is Satsmodus.IMPERATIV and (m.fråga or m.fråga_om is not None):
            raise RenderingsFel("sv: en uppmaning kan inte samtidigt vara en fråga")
        satsart = self.u.regel(SATSART, "imperativ"
                               if m.modus is Satsmodus.IMPERATIV else "indikativ")
        with self.u.led("verb"):
            verb = self.verbfras(m, satsart)
        with self.u.led("reflexiv"):
            reflexiv = self.reflexivpronomen(m)

        # Wh-frågan ersätter det efterfrågade ledet med ett frågeord och
        # flyttar det först. Subjektsfrågan inverterar INTE: frågeordet står
        # redan på subjektets plats, så "vem läser boken?" har rak ordföljd
        # medan "vad läser hon?" har omvänd. Ett ersatt subjekt renderas inte
        # alls — en form som slås upp men aldrig skrivs ut räknas annars som
        # prövad.
        with self.u.led("frågeord"):
            frågeord = self.frågeord(m)
        if frågeord is not None and m.fråga_om == "subjekt":
            subjekt, frågeord = frågeord, None
        elif satsart == "imperativ":
            # Imperativen säger inte ut den tilltalade: "läs boken!".
            subjekt = []
        else:
            with self.u.led("subjekt"):
                subjekt = self.nominalfras(m.subjekt, subjekt=True)

        if bisats:
            # BIFF: negationen kilar in sig mellan subjektet och verbet.
            ord = [*subjekt]
            if m.negerad:
                negation = self.u.form_för("neg_inte", "inv")
                self.u.ordning("biff", [negation], [verb[0]])
                ord.append(negation)
            self.u.ordning("rak_ordföljd_i_bisats", subjekt, [verb[0]])
            ord.extend(verb)
            if frågeord is not None:
                # Frågeordet leder bisatsen: "hon vet vad blod kostar".
                self.u.ordning("frågeord_först", frågeord, ord[:1])
                ord[0:0] = frågeord
            if reflexiv is not None:
                self.u.ordning("objekt_efter_verb", verb, [reflexiv])
                ord.append(reflexiv)
        else:
            omvänd = m.fråga or frågeord is not None
            if omvänd:
                self.u.ordning("v2_fråga", [verb[0]], subjekt)
            else:
                self.u.ordning("svo", subjekt, [verb[0]])
            ord = [verb[0], *subjekt] if omvänd else [*subjekt, verb[0]]
            if frågeord is not None:
                self.u.ordning("frågeord_först", frågeord, ord[:1])
                ord[0:0] = frågeord
            # OBJEKTSSKIFTE. Ett pronominellt objekt flyttar vänster om
            # satsadverbialet BARA när huvudverbet självt har flyttat, alltså
            # i enkla tempus: "jag skyndar mig inte". Finns ett hjälpverb
            # står huvudverbet kvar och pronomenet stannar till höger om det:
            # "vi har inte oroat oss". Holmbergs generalisering.
            if reflexiv is not None and len(verb) == 1:
                ord.append(reflexiv)
            negation = None
            if m.negerad:
                # Satsadverbialet står efter det FINITA verbet: "ska inte ge",
                # inte "ska ge inte". Därför delas verbfrasen här.
                negation = self.u.form_för("neg_inte", "inv")
                ord.append(negation)
                self.u.ordning("negation_efter_finit", [verb[0]], [negation])
                self.u.ordning("negation_före_infinit", [negation], verb[1:])
            ord.extend(verb[1:])
            if reflexiv is not None:
                if len(verb) > 1:
                    ord.append(reflexiv)
                elif negation is not None:
                    self.u.ordning("objektsskifte", [reflexiv], [negation])
                self.u.ordning("objekt_efter_verb", verb, [reflexiv])

        objekt: dict[str, list[Ord]] = {}
        for slot, nf in (("io", m.io), ("objekt", m.objekt)):
            if nf is not None and slot != m.fråga_om:
                with self.u.led(slot):
                    objekt[slot] = self.nominalfras(nf)
                self.u.ordning("objekt_efter_verb", verb, objekt[slot])
                ord.extend(objekt[slot])
        if "io" in objekt and "objekt" in objekt:
            self.u.ordning("io_före_objekt", objekt["io"], objekt["objekt"])
        if m.komplement is not None:
            with self.u.led("komplement"):
                komplement = self.komplement(m)
            self.u.ordning("komplement_efter_verb", verb, komplement)
            ord.extend(komplement)
        if m.predikativ is not None:
            with self.u.led("predikativ"):
                predikativ = self.predikativ(m)
            self.u.ordning("predikativ_efter_verb", verb, predikativ)
            ord.extend(predikativ)
        if m.adverbial:
            adverbial: list[Ord] = []
            for i, a in enumerate(m.adverbial):
                with self.u.led(f"adverbial{i}"):
                    adverbial.extend(self.adverbial(a))
            self.u.ordning("adverbial_sist", ord[-1:], adverbial)
            ord.extend(adverbial)
        if m.bisats is not None:
            with self.u.led("bisats"):
                argumentbisats = self.bisats(m.bisats)
            self.u.ordning("objekt_efter_verb", verb, argumentbisats[:1])
            ord.extend(argumentbisats)
        return ord

    @frasdel
    def frågeord(self, m: Mening) -> list[Ord] | None:
        """Frågeordet i en wh-fråga, böjt efter sin roll. None = ingen sådan.

        Svenskan har kasus kvar bara i genitiv (vems), så subjekt och objekt
        får samma form — men rollen skickas ändå med, eftersom uppslaget är
        detsamma i alla sju och tyskan skiljer wer/wen/wem.
        """
        if m.fråga_om is None:
            return None
        if m.fråga_om not in FRÅGESLOTTAR:
            return [self.u.form_för(m.fråga_om, "inv")]
        efterfrågat = getattr(m, m.fråga_om)
        if efterfrågat is None:
            raise RenderingsFel(
                f"sv: fråga_om={m.fråga_om!r} men den slotten är tom — "
                f"frågan behöver ett svar att ställa sig om")
        if efterfrågat.frågedeterminant is not None:
            # "vilken bok läser hon?" — hela frasen flyttas, inte bara ett
            # pronomen. Huvudordet står kvar och sägs ut.
            return self.nominalfras(efterfrågat, subjekt=m.fråga_om == "subjekt")
        sort = self.u.regel(FRÅGEPRONOMEN, "person"
                            if self.u.mänsklig(efterfrågat.koncept) else "sak")
        return [self.u.form_för(
            "frågepronomen_person" if sort == "person" else "frågepronomen_sak",
            "nom" if m.fråga_om == "subjekt" else "ack_dat")]

    @frasdel
    def bisats(self, b: Bisats) -> list[Ord]:
        """Subjunktionen och satsen i bisatsordföljd.

        En frågeordsfråga leds av frågeordet självt och har ingen subjunktion
        (`spec.Bisats`): "hon vet varför blod finns".
        """
        if (b.subjunktion is None) != (b.sats.fråga_om is not None):
            raise RenderingsFel(
                "sv: en bisats leds av en subjunktion eller av ett frågeord, "
                f"aldrig av båda och aldrig av ingen (subjunktion={b.subjunktion!r}, "
                f"fråga_om={b.sats.fråga_om!r})")
        with self.u.led("sats"):
            sats = self.satsled(b.sats, bisats=True)
        if b.subjunktion is None:
            return sats
        subjunktion = self.u.form_för(b.subjunktion, "inv")
        self.u.ordning("subjunktion_först", [subjunktion], sats[:1])
        return [subjunktion, *sats]

    def rendera(self, m: Mening) -> str:
        """Svensk sats: subjekt, verb, indirekt objekt, objekt, adverbial."""
        self.osammansmält = self.satsled(m)
        mening = " ".join(self.osammansmält)
        return mening[0].upper() + mening[1:] + slutar(m)
