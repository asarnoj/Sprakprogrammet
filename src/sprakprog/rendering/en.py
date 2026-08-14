"""Engelsk renderare.

Morfologiskt det tunnaste språket i uppsättningen: inget genus, ingen
kasus utom på pronomen, ingen adjektivkongruens. Det enda som kongruerar
är presens tredje person singular (gives).

Två saker är ändå värda att notera. Artikeln a/an väljs på nästa ords
ljudform, samma sorts sandhi som franskans elision — och lika omöjlig att
lagra som en cell. Och ordföljden är dativväxlad: "gave her brother a book"
sätter det indirekta objektet först, utan preposition, precis som svenskan.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from .spec import (
    Aspekt, Bestämdhet, Bisats, Diates, Grad, Mening, Nominalfras, Numerus, RenderingsFel,
    Satsmodus, Tidsreferens, slutar, tilltal,
)
from .uppslag import Uppslag

VOKAL = set("aeiou")


class EngelskRenderare:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, "en")
        self.conn = conn

    def nominalfras(self, nf: Nominalfras, roll: str = "objekt",
                    genitiv: bool = False) -> list[str]:
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

        if huvud["ordklass"] == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"en/{huvud['lemma']}: ett pronomen kan inte ta artikel, "
                    f"attribut eller possessiv")
            return [self.u.form(huvud, "nom" if roll == "subjekt" else "obl")]

        ord: list[str] = []
        if nf.ägare is not None:
            # "the girl's book" — ägaren står först och tar artikelplatsen.
            ord.extend(self.nominalfras(nf.ägare, genitiv=True))
        elif nf.possessiv is not None:
            ord.append(self.u.form_för(nf.possessiv, "obest"))
        elif nf.bestämdhet is Bestämdhet.BESTÄMD:
            ord.append(self.u.form_för("artikel_bestamd", "inv"))
        elif nf.numerus is Numerus.SG:
            ord.append(self.u.form_för("artikel_obestamd", "inv"))
        # Obestämd plural saknar artikel: "books".

        for attribut in nf.attribut:
            ord.append(self.u.form_för(attribut, "pos"))
        try:
            ord.append(self.u.form(huvud, ("pl_gen" if genitiv else "pl")
                                   if nf.numerus is Numerus.PL
                                   else ("sg_gen" if genitiv else "sg")))
        except RenderingsFel:
            # Plurale tantum: "stairs", "scissors". Tomma singularceller ÄR
            # markeringen — samma sak som sv pengar, de Jeans.
            if nf.numerus is Numerus.SG and not self.u._celler(huvud).get("sg"):
                raise RenderingsFel(
                    f"en/{huvud['lemma']}: saknar singular helt (plurale tantum) "
                    f"— meningen kan inte be om sg") from None
            raise
        return ord

    def _person_numerus(self, nf: Nominalfras) -> tuple[int, str]:
        rad = self.conn.execute(
            "SELECT person, numerus FROM Koncept WHERE nyckel = ?",
            (nf.koncept,)).fetchone()
        person = rad["person"] if rad and rad["person"] else 3
        numerus = ("pl" if nf.numerus is Numerus.PL
                   or (rad and rad["numerus"] == 2) else "sg")
        return person, numerus

    def presens(self, koncept: str, nf: Nominalfras) -> str:
        """Presens med personkongruens där verbet har den.

        Bara "be" böjs efter person i engelskan (am/is/are). Övriga verb har
        tomma personceller, och då faller uppslaget tillbaka på grundformen —
        vilket är rätt för dem: "the girls read".
        """
        person, numerus = self._person_numerus(nf)
        lexem = self.u.lexem(koncept)
        celler = self.u._celler(lexem)
        for cell in (f"pres_{person}{numerus}",
                     "pres_3sg" if (person, numerus) == (3, "sg") else None,
                     "inf_imp"):
            if cell and celler.get(cell):
                # Uppslaget görs om via form() i stället för att returnera
                # strängen direkt: allt som passerar DEN vägen går att spåra
                # till en cell, och generatorns attribution bygger på det.
                return self.u.form(lexem, cell)
        raise RenderingsFel(f"en/{lexem['lemma']}: ingen presensform")

    def preteritum(self, koncept: str, nf: Nominalfras) -> str:
        person, numerus = self._person_numerus(nf)
        lexem = self.u.lexem(koncept)
        celler = self.u._celler(lexem)
        for cell in (f"pret_{person}{numerus}", "pret"):
            if celler.get(cell):
                return self.u.form(lexem, cell)
        raise RenderingsFel(f"en/{lexem['lemma']}: ingen preteritumform")

    def _tredje_person_sg(self, nf: Nominalfras) -> bool:
        rad = self.conn.execute(
            "SELECT person, numerus FROM Koncept WHERE nyckel = ?",
            (nf.koncept,)).fetchone()
        person = rad["person"] if rad and rad["person"] else 3
        if nf.numerus is Numerus.PL or (rad and rad["numerus"] == 2):
            return False
        return person == 3

    def verbdelar(self, m: Mening) -> list[str]:
        if m.modus is Satsmodus.IMPERATIV:
            # "read!" — imperativen ÄR den nakna infinitiven, och delar cell
            # med den. Negationen tar do-omskrivning som vanligt, men utan
            # kongruens: "don't read!", aldrig "doesn't read!", eftersom
            # imperativen inte har någon person att kongruera med.
            tilltal(m, "en", ("2sg", "2pl", "artig"))
            bar = self.u.form_för(m.verb, "inf_imp")
            if m.negerad:
                return [self.u.form_för("fys_göra", "inf_imp"),
                        self.u.form_för("neg_inte", "inv"), bar]
            return [bar]
        if m.diates is not Diates.AKTIV:
            # "the book is read". Engelskan har bara en passiv, så båda
            # specvärdena ger samma konstruktion.
            #
            # BE bär hela apparaten — tempus, aspekt och negation: "will be
            # read", "has been read", "is not read". Kopulan går därför
            # genom den aktiva grenen i stället för att få egna fall här.
            # Passiven behöver aldrig do-omskrivning: hjälpverbet finns
            # alltid, så "not" har något att fästa vid.
            kopula = replace(m, verb="verb_vara", diates=Diates.AKTIV)
            return [*self.verbdelar(kopula), self.u.form_för(m.verb, "sup")]
        if m.negerad:
            return self._negerat_verb(m)
        if m.aspekt is Aspekt.PERFEKT:
            # "has read" / "had read". Hjälpverbet kongruerar, participet
            # inte — och engelskan använder alltid have, aldrig be.
            hjälp = (self.preteritum("verb_ha", m.subjekt)
                     if m.tid is Tidsreferens.FÖRFLUTEN
                     else self.presens("verb_ha", m.subjekt))
            return [hjälp, self.u.form_för(m.verb, "sup")]
        if m.tid is Tidsreferens.FRAMTID:
            return [self.u.form_för("modal_ska", "pres_3sg"),
                    self.u.form_för(m.verb, "inf_imp")]
        if m.tid is Tidsreferens.FÖRFLUTEN:
            return [self.preteritum(m.verb, m.subjekt)]
        return [self.presens(m.verb, m.subjekt)]

    def _negerat_verb(self, m: Mening) -> list[str]:
        """Engelsk negation fäster på hjälpverbet — do-omskrivning bara annars.

        "she will not read", "she has not read", "she is not happy" — men
        "she does not read", eftersom en enkel presens eller preteritum inte
        HAR något hjälpverb att fästa vid. Det är hela skälet till att
        do-omskrivningen finns, och därför står den sist: de fall som redan
        har ett hjälpverb ska aldrig nå den.

        Hjälpverbet do lånar sina former från fys_göra: auxiliärt och
        lexikalt do är samma ord, så formerna finns redan och behöver inte
        uppfinnas. Att de betyder olika saker spelar ingen roll här,
        eftersom bara formen används.
        """
        inte = self.u.form_för("neg_inte", "inv")

        if m.tid is Tidsreferens.FRAMTID:
            return [self.u.form_för("modal_ska", "pres_3sg"), inte,
                    self.u.form_för(m.verb, "inf_imp")]

        def böjt(koncept: str) -> str:
            if m.tid is Tidsreferens.FÖRFLUTEN:
                return self.preteritum(koncept, m.subjekt)
            return self.presens(koncept, m.subjekt)

        if m.aspekt is Aspekt.PERFEKT:
            # "she has not read" — have är hjälpverbet och bär negationen.
            return [böjt("verb_ha"), inte, self.u.form_för(m.verb, "sup")]
        if m.verb == "verb_vara":
            # Kopulan negeras direkt: "she is not happy", inte "does not be".
            return [böjt(m.verb), inte]
        return [böjt("fys_göra"), inte, self.u.form_för(m.verb, "inf_imp")]

    def sandhi(self, ord: list[str]) -> list[str]:
        """a → an framför vokalljud.

        Approximerat på stavning. Engelskan går på LJUD, inte bokstav — "an
        hour" men "a university" — och den skillnaden finns inte i databasen.
        Inget ord i det nuvarande ordförrådet faller på det.
        """
        return [("an" if o == "a" and i + 1 < len(ord)
                 and ord[i + 1][:1].lower() in VOKAL else o)
                for i, o in enumerate(ord)]

    def predikativ(self, m: Mening) -> list[str]:
        if isinstance(m.predikativ, str) and m.grad is not Grad.POSITIV:
            # "bigger" men "more interesting" — engelskan avgör per ord,
            # och datan vet: saknas cellen kompareras det analytiskt.
            cell = "komp" if m.grad is Grad.KOMPARATIV else "superl"
            adjektiv = self.u.lexem(m.predikativ)
            form = self.u._celler(adjektiv).get(cell)
            ut = ([self.u.form(adjektiv, cell)] if form else
                  [self.u.form_för("komp_mer" if m.grad is Grad.KOMPARATIV
                                   else "komp_mest", "pos"),
                   self.u.form_för(m.predikativ, "pos")])
            if m.jämförelse is not None:
                ut.append(self.u.form_för("komp_än", "inv"))
                ut += self.nominalfras(m.jämförelse)
            return ut
        if isinstance(m.predikativ, str):
            # Engelska predikativa adjektiv böjs inte: "she is happy".
            return [self.u.form_för(m.predikativ, "pos")]
        # Till skillnad från de andra sex KRÄVER engelskan artikel här:
        # "she is a doctor", aldrig "she is doctor".
        return self.nominalfras(m.predikativ)

    def satsled(self, m: Mening) -> list[str]:
        """Satsens ord. Engelsk bisats har SAMMA ordföljd som huvudsatsen.

        Det gör den till undantaget: svenskan flyttar satsadverbialet och
        tyskan verbet. Engelskan flyttar ingenting — bara subjunktionen
        läggs till. Bisatsen behöver därför ingen egen parameter här.
        """
        # Imperativen säger inte ut den tilltalade: "read the book!".
        subjekt = ([] if m.modus is Satsmodus.IMPERATIV
                   else self.nominalfras(m.subjekt, "subjekt"))
        verb = self.verbdelar(m)
        if m.fråga:
            # Engelskan kräver do-omskrivning i frågor precis som i
            # negationer, och av samma skäl: bara hjälpverb får inverteras.
            # "Does the girl read?" men "Is she happy?"
            if len(verb) == 1 and m.verb != "verb_vara":
                hjälp = self.u.form_för(
                    "fys_göra", "pret" if m.tid is Tidsreferens.FÖRFLUTEN
                    else "pres_3sg" if self._tredje_person_sg(m.subjekt)
                    else "inf_imp")
                verb = [hjälp, self.u.form_för(m.verb, "inf_imp")]
            ord = [verb[0], *subjekt, *verb[1:]]
        else:
            ord = [*subjekt, *verb]
        if m.komplement is not None:
            # Engelskan varierar inte bara MARKÖREN utan också FORMEN:
            # "try to read" men "stop reading". Vilket ett verb tar är
            # lexikalt precis som markören, men mekanismen i MönsterKrav
            # bär bara markören. Med nuvarande ordförråd är stop det enda
            # verb som kräver gerundium — kommer fler behöver formen bli
            # data, inte en rad kod.
            if m.verb == "asp_sluta":
                ord.append(self.u.form_för(m.komplement, "gerund"))
            else:
                markör = self.u.infinitivmarkör(m.verb)
                if markör is not None:
                    ord.append(self.u.form_för(markör, "inv"))
                ord.append(self.u.form_för(m.komplement, "inf_imp"))
        if m.predikativ is not None:
            ord += self.predikativ(m)
        for nf in (m.io, m.objekt):
            if nf is not None:
                ord += self.nominalfras(nf)
        for adverbial in m.adverbial:
            if isinstance(adverbial, str):
                ord.append(self.u.form_för(adverbial, "pos"))
            elif isinstance(adverbial, Bisats):
                ord += self.bisats(adverbial)
            else:
                ord.append(self.u.form_för(adverbial.preposition, "inv"))
                ord += self.nominalfras(adverbial.komplement)
        if m.bisats is not None:
            ord += self.bisats(m.bisats)
        return ord

    def bisats(self, b: Bisats) -> list[str]:
        return [self.u.form_för(b.subjunktion, "inv"), *self.satsled(b.sats)]

    def rendera(self, m: Mening) -> str:
        mening = " ".join(self.sandhi(self.satsled(m)))
        return mening[0].upper() + mening[1:] + slutar(m)
