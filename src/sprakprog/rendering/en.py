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

from .spec import (
    Aspekt, Bestämdhet, Mening, Nominalfras, Numerus, RenderingsFel, Tidsreferens,
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

    def _tredje_person_sg(self, nf: Nominalfras) -> bool:
        rad = self.conn.execute(
            "SELECT person, numerus FROM Koncept WHERE nyckel = ?",
            (nf.koncept,)).fetchone()
        person = rad["person"] if rad and rad["person"] else 3
        if nf.numerus is Numerus.PL or (rad and rad["numerus"] == 2):
            return False
        return person == 3

    def verbdelar(self, m: Mening) -> list[str]:
        if m.negerad:
            return self._negerat_verb(m)
        if m.aspekt is Aspekt.PERFEKT:
            # "has read" / "had read". Hjälpverbet kongruerar, participet
            # inte — och engelskan använder alltid have, aldrig be.
            hjälp = ("pret" if m.tid is Tidsreferens.FÖRFLUTEN
                     else "pres_3sg" if self._tredje_person_sg(m.subjekt)
                     else "inf_imp")
            return [self.u.form_för("verb_ha", hjälp),
                    self.u.form_för(m.verb, "sup")]
        if m.tid is Tidsreferens.FRAMTID:
            return [self.u.form_för("modal_ska", "pres_3sg"),
                    self.u.form_för(m.verb, "inf_imp")]
        if m.tid is Tidsreferens.FÖRFLUTEN:
            return [self.u.form_för(m.verb, "pret")]
        cell = "pres_3sg" if self._tredje_person_sg(m.subjekt) else "inf_imp"
        return [self.u.form_för(m.verb, cell)]

    def _negerat_verb(self, m: Mening) -> list[str]:
        """Engelsk negation kräver do-omskrivning — utom med be och modaler.

        "she does not read" men "she is not happy" och "she will not read".
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
                return self.u.form_för(koncept, "pret")
            return self.u.form_för(
                koncept, "pres_3sg" if self._tredje_person_sg(m.subjekt)
                else "inf_imp")

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
        if isinstance(m.predikativ, str):
            # Engelska predikativa adjektiv böjs inte: "she is happy".
            return [self.u.form_för(m.predikativ, "pos")]
        # Till skillnad från de andra sex KRÄVER engelskan artikel här:
        # "she is a doctor", aldrig "she is doctor".
        return self.nominalfras(m.predikativ)

    def rendera(self, m: Mening) -> str:
        ord = [*self.nominalfras(m.subjekt, "subjekt"), *self.verbdelar(m)]
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
            else:
                ord.append(self.u.form_för(adverbial.preposition, "inv"))
                ord += self.nominalfras(adverbial.komplement)
        mening = " ".join(self.sandhi(ord))
        return mening[0].upper() + mening[1:] + "."
