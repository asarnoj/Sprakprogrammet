"""Japansk renderare.

Det språk som bryter flest antaganden i de andra sex:

  SOV           Verbet står sist, inte på plats två eller efter subjektet.

  PARTIKLAR     Rollen märks ut på frasen med は/を/に i stället för med
                kasusböjning eller ordföljd. BITMASK.md slår fast att
                kasus alltid är NULL för japanska av just det skälet.

  INGA MELLANSLAG  Orden fogas ihop utan separator.

  INGEN BESTÄMDHET  は/が-distinktionen är informationsstruktur, inte
                bestämdhet. Nominalfrasens bestämdhet ignoreras därför helt.

Artigt förflutet komponeras morfologiskt: ます-formen med ます utbytt mot
ました. Det är RENDERARE_KRAV §3.11, och skälet till att det inte är en
egen cell är PARAMETER_AUDIT §2 — register är inte en Former-axel.

Känd gräns: partiklarna är hårdkodade här. Enligt samma argument som lade
determinerarna i Former borde de vara spårbara lexem — de är det mest
övade i japansk grammatik — men det kräver nya Koncept-rader för
grammatiska morfem, vilket är ett större beslut än den här filen.
"""

from __future__ import annotations

import sqlite3

from .spec import Mening, Nominalfras, RenderingsFel, Tidsreferens
from .uppslag import Uppslag

TOPIK, OBJEKT, DATIV = "は", "を", "に"


class JapanskRenderare:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, "ja")

    def nominalfras(self, nf: Nominalfras) -> str:
        huvud = self.u.lexem(nf.koncept)
        ord = ""

        if nf.ägare is not None:
            # 女の子の本 — ägaren följd av partikeln の, före huvudordet.
            # Samma partikel som possessivlemmana redan bär (彼女の).
            ord += self.nominalfras(nf.ägare) + "の"

        if nf.possessiv is not None and not nf.possessiv_koreferent:
            # Japanska possessiver är redan の-fraser i lemmat (彼女の).
            #
            # Är possessorn samma som subjektet utelämnas den helt:
            # 女の子は兄弟に本をあげました, inte 女の子は彼女の兄弟に…
            # Ägandet är återvinningsbart ur sammanhanget, och att skriva ut
            # det låter främmande. Det är samma observation som
            # RENDERARE_KRAV §6 gör — japanskan ignorerar reflexivfrågan utan
            # att något går sönder — men den måste realiseras som ett aktivt
            # utelämnande, inte som att inget händer.
            ord += self.u.form_för(nf.possessiv, "jisho")

        for attribut in nf.attribut:
            adjektiv = self.u.lexem(attribut)
            typ = adjektiv["ja_adjektiv_typ"]
            if typ == "i":
                ord += self.u.form(adjektiv, "jisho")
            elif typ == "na":
                ord += self.u.form(adjektiv, "jisho") + "な"
            elif typ == "no":
                ord += adjektiv["lemma"] + "の"
            elif typ == "verbfras":
                ord += adjektiv["lemma"]
            else:
                raise RenderingsFel(
                    f"ja/{adjektiv['lemma']}: ja_adjektiv_typ saknas — "
                    f"attribueringen (い / な / の) går inte att avgöra")

        return ord + self.u.form(huvud, "jisho")

    def verbform(self, m: Mening) -> str:
        """Artig form. Register är renderarens val, inte en Former-axel."""
        lexem = self.u.lexem(m.verb)
        celler = self.u._celler(lexem)
        # Läses genom VERB-paradigmet, så adjektivets ku-cell syns inte här.
        # Kännetecknet är i stället att ます saknas medan grundformen slutar
        # på い — det är ett i-adjektiv som råkat hamna under ett verbkoncept.
        if not celler.get("masu") and celler.get("jisho", "").endswith("い"):
            # ku-formen finns bara i adjektivparadigmet. Konceptet är ett
            # Verb, men japanskan uttrycker det adjektiviskt: gen_sakna är
            # 恋しい, "X が恋しい". Predikatet blir då adjektivform + です,
            # inte en ます-form — 恋しいです / 恋しかったです.
            grund = celler.get("ta" if m.tid is Tidsreferens.FÖRFLUTEN else "jisho")
            if not grund:
                raise RenderingsFel(
                    f"ja/{lexem['lemma']}: varken ます- eller adjektivform finns")
            return grund + "です"
        masu = self.u.form_för(m.verb, "masu")
        if m.tid is Tidsreferens.FÖRFLUTEN:
            if not masu.endswith("ます"):
                raise RenderingsFel(
                    f"ja: masu-formen {masu!r} slutar inte på ます — artigt "
                    f"förflutet kan inte komponeras")
            return masu[:-2] + "ました"
        # Japanskan har inget futurum: icke-förfluten form täcker nutid och
        # framtid, och tidsadverbialet gör skillnaden.
        return masu

    def rendera(self, m: Mening) -> str:
        """SOV: ämne, adverbial, indirekt objekt, objekt, verb."""
        delar = [self.nominalfras(m.subjekt) + TOPIK]
        for adverbial in m.adverbial:
            delar.append(self.u.form_för(adverbial, "inv") + "、")
        if m.io is not None:
            delar.append(self.nominalfras(m.io) + DATIV)
        if m.objekt is not None:
            delar.append(self.nominalfras(m.objekt) + OBJEKT)
        delar.append(self.verbform(m))
        return "".join(delar) + "。"
