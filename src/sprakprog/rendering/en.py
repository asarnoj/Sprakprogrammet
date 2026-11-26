"""Engelsk renderare.

Morfologiskt det tunnaste språket i uppsättningen: inget genus, ingen kasus
utom på pronomen, ingen adjektivkongruens. Verbet kongruerar i presens tredje
person singular (gives), och be dessutom i fler personer (am, are, were).

Tre saker är ändå engelska. Artikeln a/an väljs på nästa ords första ljud.
Negation och fråga kräver ett hjälpverb att fästa vid, och finns inget tas do.
Och dativväxlingen sätter det indirekta objektet först: "gave her brother a
book".

REDOVISNINGEN (KÄRNAN 8.3, steg 1). Samma uppbyggnad som `sv.py`: valen mellan
utfall går genom `regel`, ordföljden genom `ordning`, ordens egenskaper genom
`egenskap` och verbets krav genom `rektion`. Koden grenar på det utfall `regel`
lämnar tillbaka och inte på specen, så att varje beslut kan tvingas fram.

Passiven är inget val: engelskan har bara en, be plus particip, och den syns i
be:s tempus och kongruens och i participets form.

Id:na i kommentarerna (G1, E1 …) är inventeringen i `paradigm/TYSTA_BESLUT.md`.
"""

from __future__ import annotations

import sqlite3

from .spec import (
    Aspekt, Attribut, Bestämdhet, Bisats, Diates, Grad, Mening, Nominalfras,
    NAKEN, Numerus, Prepositionsfras, FRÅGESLOTTAR, RenderingsFel, Satsmodus,
    Tidsreferens, attribut_med_grad, slutar,
)
from .uppslag import Ord, Uppslag, Val, frasdel

# ── besluten ─────────────────────────────────────────────────────────────

#: G1. I/me.
PRONOMENFORM = Val("pronomenform", ("subjektsform", "objektsform"))

#: G2–G7. Vad som står före huvudordet: "which book", "the girl's book",
#: "her book", "the book", "water", "a book", "books".
BESTÄMNING = Val("bestämning", (
    "frågedeterminant", "genitiv", "possessiv", "bestämd_artikel", "naken",
    "obestämd_artikel", "obestämd_plural"))

#: E1. "a book", "an apple".
ARTIKELFORM = Val("artikelform", ("a", "an"))

#: G10. "she is a doctor" — engelskan tar artikel där de andra sex inte gör det.
PREDIKATIVT_SUBSTANTIV = Val("predikativt_substantiv",
                             ("med_artikel", "utan_artikel"))

#: G16, G17. "reads", "read", "will read", "has read", "had read", "will have read".
TEMPUSFORM = Val("tempusform", (
    "presens", "preteritum", "futurum", "perfekt", "pluskvamperfekt",
    "futurum_perfekt"))

#: G13, G14. Det finita verbets person och numerus: "I am", "she reads", "they
#: were". Ett frågeord som subjekt kongruerar som tredje person singular.
KONGRUENS = Val("kongruens", ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl"))

#: E2, E4. "she does not read", "does she read?", "do not read!" — men "she is
#: not happy" och "can she read?".
DO_OMSKRIVNING = Val("do_omskrivning", ("med_do", "utan_do"))

#: G21. "read the book!" eller "you read the book".
SATSART = Val("satsart", ("indikativ", "imperativ"))

#: G20. who eller what.
FRÅGEPRONOMEN = Val("frågepronomen", ("person", "sak"))

#: E5. who eller whom.
FRÅGEPRONOMENFORM = Val("frågepronomenform", ("subjektsform", "objektsform"))

#: Bestämningar som pekar ut ett bestämt exemplar och därför bär en attributiv
#: superlativ: "the biggest book", "her biggest book", "the girl's biggest book".
BESTÄMD_BESTÄMNING = frozenset({"bestämd_artikel", "possessiv", "genitiv"})


def _ljudform(ord: Ord, text: str) -> Ord:
    """Samma uppslag med en annan ljudform: a → an. Id:t följer med, så att
    spåret ser det som samma ord."""
    ny = type(ord)(text)
    ny.__dict__.update(ord.__dict__)
    return ny


class EngelskRenderare:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, "en")

    # ── nominalfras ──────────────────────────────────────────────────

    @frasdel
    def nominalfras(self, nf: Nominalfras, *, subjekt: bool = False,
                    genitiv: bool = False, artikel: bool = True) -> list[Ord]:
        """`artikel` är False bara när predikativets artikel tvingats bort."""
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

        if self.u.ordklass(huvud) == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"en/{self.u.lemma(huvud)}: ett pronomen kan inte ta artikel, "
                    f"attribut eller possessiv")
            if genitiv:
                raise RenderingsFel(
                    f"en/{self.u.lemma(huvud)}: en pronominell ägare uttrycks "
                    f"med possessiv ('my book'), inte med genitiv")
            form = self.u.regel(PRONOMENFORM,
                                "subjektsform" if subjekt else "objektsform")
            return [self.u.form(huvud, "nom" if form == "subjektsform" else "obl")]

        self.u.kontrollera_naken(nf)

        if nf.frågedeterminant is not None:
            naturlig = "frågedeterminant"
        elif nf.ägare is not None:
            naturlig = "genitiv"
        elif nf.possessiv is not None:
            naturlig = "possessiv"
        elif nf.bestämdhet is Bestämdhet.BESTÄMD:
            naturlig = "bestämd_artikel"
        elif nf.bestämdhet in NAKEN:
            naturlig = "naken"
        elif nf.numerus is Numerus.SG:
            naturlig = "obestämd_artikel"
        else:
            naturlig = "obestämd_plural"
        bestämning = self.u.regel(BESTÄMNING, naturlig)

        attribut: list[Ord] = []
        for i, a in enumerate(nf.attribut):
            with self.u.led(f"attribut{i}"):
                attribut.extend(self._attribut(a, bestämning))

        cell = ("pl" if nf.numerus is Numerus.PL else "sg") + ("_gen" if genitiv else "")
        try:
            huvudord = self.u.form(huvud, cell)
        except RenderingsFel:
            # Plurale tantum: "stairs", "jeans". Tomma singularceller ÄR
            # markeringen — samma sak som sv pengar.
            if nf.numerus is Numerus.SG and not self.u.har_form(huvud, "sg"):
                raise RenderingsFel(
                    f"en/{self.u.lemma(huvud)}: saknar singular helt (plurale "
                    f"tantum) — meningen kan inte be om sg") from None
            raise

        före: list[Ord] = []
        if bestämning == "frågedeterminant":
            if nf.frågedeterminant is None:
                raise RenderingsFel("en: frasen har ingen frågedeterminant")
            före = [self.u.form_för(nf.frågedeterminant, "inv")]
        elif bestämning == "genitiv":
            # "the girl's book" — ägaren står först och tar artikelns plats.
            if nf.ägare is None:
                raise RenderingsFel("en: frasen har ingen genitivägare")
            with self.u.led("ägare"):
                före = self.nominalfras(nf.ägare, genitiv=True)
        elif bestämning == "possessiv":
            if nf.possessiv is None:
                raise RenderingsFel("en: frasen har ingen possessiv")
            före = [self.u.form_för(nf.possessiv, "obest")]
        elif bestämning == "bestämd_artikel" and artikel:
            före = [self.u.form_för("artikel_bestamd", "inv")]
        elif bestämning == "obestämd_artikel" and artikel:
            före = [self._obestämd_artikel([*attribut, huvudord][0])]
        # naken ("water") och obestämd_plural ("books") har inget ord före.

        self.u.ordning("bestämning_före_huvudord", före, [*attribut, huvudord])
        self.u.ordning("attribut_före_huvudord", attribut, [huvudord])
        return [*före, *attribut, huvudord]

    def _obestämd_artikel(self, nästa: Ord) -> Ord:
        """a eller an efter nästa ords första ljud (E1).

        Ljudet hör till nästa ord självt och är ingen egen kunskap. Det läses
        ur stavningen, så "an hour" och "a university" går inte att få fram
        (TYSTA_BESLUT punkt 7).
        """
        ljud = self.u.förljud(self.u.lexem(nästa.koncept, nästa.variant))
        form = self.u.regel(ARTIKELFORM, "an" if ljud == "vokal" else "a")
        artikel = self.u.form_för("artikel_obestamd", "inv")
        return _ljudform(artikel, "an") if form == "an" else artikel

    def _attribut(self, a: str | Attribut, bestämning: str) -> list[Ord]:
        """Attributivt adjektiv i sin grad: "a bigger book", "a more interesting book".

        Engelskan böjer inte attributet efter huvudordet, så graden är hela
        variationen. Attributet är ingen egen del för kartan, eftersom artikeln
        framför det väljs på dess första ljud.
        """
        a = attribut_med_grad(a)
        if a.grad is Grad.POSITIV:
            return [self.u.form_för(a.koncept, "pos")]
        if a.grad is Grad.SUPERLATIV and bestämning not in BESTÄMD_BESTÄMNING:
            # "a biggest book" finns inte — superlativen pekar ut ett unikt
            # exemplar och kräver the. Samma sak som i svenskan.
            raise RenderingsFel(
                f"en/{a.koncept}: attributiv superlativ kräver bestämd fras "
                f"— 'the biggest book', inte 'a biggest book'")
        lexem = self.u.lexem(a.koncept)
        if self.u.egenskap(lexem, "komparation") == "syntetisk":
            return [self.u.form(lexem, "komp" if a.grad is Grad.KOMPARATIV
                                else "superl")]
        markör = self.u.form_för(
            "komp_mer" if a.grad is Grad.KOMPARATIV else "komp_mest", "pos")
        adjektiv = self.u.form(lexem, "pos")
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
        """Infinitivkomplement: "wants to read", "can read" — eller gerundium:
        "stops reading". Både markören och formen är kunskap om det styrande
        verbet (TYSTA_BESLUT A6, A10)."""
        if self.u.komplementform(m.verb) == "gerundium":
            return [self.u.form_för(m.komplement, "gerund")]
        markör = self.u.infinitivmarkör(m.verb)
        infinitiv = self.u.form_för(m.komplement, "inf_imp")
        if markör is None:
            return [infinitiv]
        markörord = self.u.form_för(markör, "inv")
        self.u.ordning("infinitivmarkör_före", [markörord], [infinitiv])
        return [markörord, infinitiv]

    @frasdel
    def predikativ(self, m: Mening) -> list[Ord]:
        if isinstance(m.predikativ, str):
            if m.grad is Grad.POSITIV:
                # Engelska predikativa adjektiv böjs inte: "she is happy".
                return [self.u.form_för(m.predikativ, "pos")]
            return self._komparation(m)
        # Till skillnad från de andra sex KRÄVER engelskan artikel här: "she is
        # a doctor", aldrig "she is doctor".
        form = self.u.regel(PREDIKATIVT_SUBSTANTIV, "med_artikel")
        return self.nominalfras(m.predikativ, artikel=form == "med_artikel")

    def _komparation(self, m: Mening) -> list[Ord]:
        """"bigger" men "more interesting" — engelskan avgör per ord."""
        adjektiv = self.u.lexem(m.predikativ)
        if self.u.egenskap(adjektiv, "komparation") == "syntetisk":
            ut = [self.u.form(adjektiv, "komp" if m.grad is Grad.KOMPARATIV
                              else "superl")]
        else:
            markör = self.u.form_för(
                "komp_mer" if m.grad is Grad.KOMPARATIV else "komp_mest", "pos")
            ord = self.u.form(adjektiv, "pos")
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
    def verbfras(self, m: Mening, satsart: str, stöd: bool,
                 verb: str | None = None, diates: Diates | None = None) -> list[Ord]:
        """Verbet, som ett eller flera ord. Negationen läggs in av satsen.

        `stöd` säger att satsen behöver ett hjälpverb att fästa negation eller
        inversion vid. Har verbfrasen inget — enkel presens eller preteritum av
        ett verb som inte är operator — tas do: "she does not read", "does she
        read?". `verb` och `diates` skickas bara för passivens be (KÄRNAN 6.7).
        """
        verb = m.verb if verb is None else verb
        diates = m.diates if diates is None else diates
        lexem = self.u.lexem(verb)
        if satsart == "imperativ":
            # "read!" — imperativen ÄR den nakna infinitiven. Nekad tar den
            # alltid do, också för be ("do not be late!"), och utan kongruens,
            # eftersom imperativen inte har någon person.
            tal = self.u.tilltal(m.subjekt.koncept)
            if tal is None:
                raise RenderingsFel(
                    f"en: imperativens subjekt måste vara den tilltalade, "
                    f"inte {m.subjekt.koncept!r}")
            if tal not in ("2sg", "2pl", "artig"):
                raise RenderingsFel(
                    f"en: saknar imperativform för {tal} — engelskan uttrycker "
                    f"det med en omskrivning")
            bar = self.u.form(lexem, "inf_imp")
            if not stöd or self.u.regel(DO_OMSKRIVNING, "med_do") == "utan_do":
                return [bar]
            hjälp = self.u.form_för("fys_göra", "inf_imp")
            self.u.ordning("hjälpverb_före_huvudverb", [hjälp], [bar])
            return [hjälp, bar]

        if diates is not Diates.AKTIV:
            # "the book is read". Be bär tempus, kongruens och negation — "will
            # be read", "has been read", "is not read" — och går därför genom
            # den aktiva grenen. Be är operator och tar aldrig do.
            with self.u.led("hjälpverb"):
                hjälpverb = self.verbfras(m, satsart, stöd, verb="verb_vara",
                                          diates=Diates.AKTIV)
            particip = self.u.form(lexem, "sup")
            self.u.ordning("hjälpverb_före_huvudverb", hjälpverb, [particip])
            return [*hjälpverb, particip]

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
            # "has read" / "had read" — engelskan använder alltid have.
            hjälp = self._finit(self.u.lexem("verb_ha"), m,
                                "preteritum" if tempus == "pluskvamperfekt" else "presens")
            huvud = self.u.form(lexem, "sup")
        elif tempus == "futurum_perfekt":
            # "will have read" — förut blev det "has read", och nekat "will
            # not read".
            will = self.u.form_för("modal_ska", "pres_3sg")
            have = self.u.form_för("verb_ha", "inf_imp")
            huvud = self.u.form(lexem, "sup")
            self.u.ordning("hjälpverb_före_huvudverb", [will], [have])
            self.u.ordning("hjälpverb_före_huvudverb", [have], [huvud])
            return [will, have, huvud]
        elif tempus == "futurum":
            hjälp = self.u.form_för("modal_ska", "pres_3sg")
            huvud = self.u.form(lexem, "inf_imp")
        else:
            if stöd:
                operator = self.u.operator(lexem)
                do = self.u.regel(DO_OMSKRIVNING, "utan_do" if operator else "med_do")
            else:
                do = "utan_do"
            if do == "utan_do":
                return [self._finit(lexem, m, tempus)]
            hjälp = self._finit(self.u.lexem("fys_göra"), m, tempus)
            huvud = self.u.form(lexem, "inf_imp")
        self.u.ordning("hjälpverb_före_huvudverb", [hjälp], [huvud])
        return [hjälp, huvud]

    def _finit(self, lexem, m: Mening, tempus: str) -> Ord:
        """Det finita verbet i presens eller preteritum, kongruent med subjektet.

        Be har egna personformer (am, are, were). Övriga verb skiljer bara
        tredje person singular i presens, och modalverben har en enda form,
        can, i alla personer.
        """
        kongruens = self.u.regel(KONGRUENS, self._kongruens(m))
        if tempus == "presens":
            if self.u.har_form(lexem, f"pres_{kongruens}"):
                cell = f"pres_{kongruens}"
            elif kongruens == "3sg" or not self.u.har_form(lexem, "inf_imp"):
                cell = "pres_3sg"
            else:
                cell = "inf_imp"
        else:
            cell = (f"pret_{kongruens}" if self.u.har_form(lexem, f"pret_{kongruens}")
                    else "pret")
        return self.u.form(lexem, cell)

    def _kongruens(self, m: Mening) -> str:
        """Subjektets person och numerus. Ett frågeord som subjekt är tredje
        person singular: "who reads", också när svaret är flera (G14)."""
        nf = m.subjekt
        if m.fråga_om == "subjekt" and nf.frågedeterminant is None:
            return "3sg"
        person = self.u.koncept(nf.koncept, "person") or 3
        numerus = ("pl" if nf.numerus is Numerus.PL
                   or self.u.koncept(nf.koncept, "numerus") == 2 else "sg")
        return f"{person}{numerus}"

    # ── satsen ───────────────────────────────────────────────────────

    @frasdel
    def satsled(self, m: Mening, bisats: bool = False) -> list[Ord]:
        """Satsens ord. Engelsk bisats har samma ordföljd som huvudsatsen — utom
        att en FRÅGA inte inverterar i bisats.

        "Does blood exist?" men "she knows if blood exists", "whom does blood
        cost?" men "she knows whom blood costs". Inversionen och do-omskrivningen
        hör till den fristående frågan.
        """
        if m.fråga and m.fråga_om is not None:
            raise RenderingsFel("en: en sats kan inte vara både ja/nej-fråga "
                                "och frågeordsfråga")
        if m.modus is Satsmodus.IMPERATIV and (m.fråga or m.fråga_om is not None):
            raise RenderingsFel("en: en uppmaning kan inte samtidigt vara en fråga")
        satsart = self.u.regel(SATSART, "imperativ"
                               if m.modus is Satsmodus.IMPERATIV else "indikativ")
        with self.u.led("frågeord"):
            frågeord = self.frågeord(m)
        subjektsfråga = frågeord is not None and m.fråga_om == "subjekt"
        # Frågan inverterar hjälpverbet och subjektet: "does the girl read?".
        # Subjektsfrågan gör det inte — frågeordet står redan på subjektets
        # plats: "who reads the book?".
        inversion = not bisats and (m.fråga or (frågeord is not None and not subjektsfråga))
        with self.u.led("verb"):
            verb = self.verbfras(m, satsart, m.negerad or inversion)

        if subjektsfråga:
            subjekt, frågeord = frågeord, None
        elif satsart == "imperativ":
            # Imperativen säger inte ut den tilltalade: "read the book!".
            subjekt = []
        else:
            with self.u.led("subjekt"):
                subjekt = self.nominalfras(m.subjekt, subjekt=True)

        if inversion:
            self.u.ordning("inversion_i_fråga", [verb[0]], subjekt)
            ord = [verb[0], *subjekt]
        else:
            self.u.ordning("svo", subjekt, [verb[0]])
            ord = [*subjekt, verb[0]]
        if frågeord is not None:
            self.u.ordning("frågeord_först", frågeord, ord[:1])
            ord[0:0] = frågeord
        if m.negerad:
            # Not står efter det finita hjälpverbet: "has not read", "does not
            # read", "is not happy".
            negation = self.u.form_för("neg_inte", "inv")
            ord.append(negation)
            self.u.ordning("negation_efter_finit", [verb[0]], [negation])
            self.u.ordning("negation_före_infinit", [negation], verb[1:])
        ord.extend(verb[1:])

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
        # Dativväxlingen: "gave her brother a book".
        objekt: dict[str, list[Ord]] = {}
        for slot, nf in (("io", m.io), ("objekt", m.objekt)):
            if nf is not None and slot != m.fråga_om:
                with self.u.led(slot):
                    objekt[slot] = self.nominalfras(nf)
                self.u.ordning("objekt_efter_verb", verb, objekt[slot])
                ord.extend(objekt[slot])
        if "io" in objekt and "objekt" in objekt:
            self.u.ordning("io_före_objekt", objekt["io"], objekt["objekt"])
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
        """who/whom/what, eller en hel fras med frågedeterminant. None = ingen fråga."""
        if m.fråga_om is None:
            return None
        if m.fråga_om not in FRÅGESLOTTAR:
            return [self.u.form_för(m.fråga_om, "inv")]
        efterfrågat = getattr(m, m.fråga_om)
        if efterfrågat is None:
            raise RenderingsFel(
                f"en: fråga_om={m.fråga_om!r} men den slotten är tom")
        if efterfrågat.frågedeterminant is not None:
            # "which book does she read?" — hela frasen flyttas.
            return self.nominalfras(efterfrågat, subjekt=m.fråga_om == "subjekt")
        sort = self.u.regel(FRÅGEPRONOMEN, "person"
                            if self.u.mänsklig(efterfrågat.koncept) else "sak")
        # Engelskan har kasus kvar på who: "whom did you see?".
        form = self.u.regel(FRÅGEPRONOMENFORM, "subjektsform"
                            if m.fråga_om == "subjekt" else "objektsform")
        return [self.u.form_för(
            "frågepronomen_person" if sort == "person" else "frågepronomen_sak",
            "nom" if form == "subjektsform" else "obl")]

    @frasdel
    def bisats(self, b: Bisats) -> list[Ord]:
        """Subjunktionen och satsen, i rak ordföljd.

        En frågeordsfråga leds av frågeordet självt och har ingen subjunktion
        (`spec.Bisats`): "she knows why blood exists".
        """
        if (b.subjunktion is None) != (b.sats.fråga_om is not None):
            raise RenderingsFel(
                "en: en bisats leds av en subjunktion eller av ett frågeord, "
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
        self.osammansmält = self.satsled(m)
        mening = " ".join(self.osammansmält)
        return mening[0].upper() + mening[1:] + slutar(m)
