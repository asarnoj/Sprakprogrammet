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

from .spec import Aspekt, Diates, Grad, Mening, Nominalfras, RenderingsFel, Tidsreferens
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
        if m.diates is not Diates.AKTIV:
            # Japanskan har en egen passivform i paradigmet — 受身 — precis
            # som svenskans s-passiv. Ingen konstruktion behövs, men den
            # artiga formen måste komponeras: 読まれる → 読まれます.
            ukemi = self.u.form_för(m.verb, "ukemi")
            if not ukemi.endswith("る"):
                raise RenderingsFel(
                    f"ja: ukemi-formen {ukemi!r} slutar inte på る")
            stam = ukemi[:-1]
            if m.negerad:
                grund = stam + "ません"
                return grund + "でした" if m.tid is Tidsreferens.FÖRFLUTEN else grund
            grund = stam + "ます"
            return (stam + "ました"
                    if m.tid is Tidsreferens.FÖRFLUTEN
                    or m.aspekt is Aspekt.PERFEKT else grund)

        masu = self.u.form_för(m.verb, "masu")
        if m.negerad:
            # Japanskan har inget nekande ord i satsen — verbet böjs.
            # あげます → あげません → あげませんでした. Samma komposition ur
            # ます-stammen som det artiga förflutna, ett steg längre.
            if not masu.endswith("ます"):
                raise RenderingsFel(
                    f"ja: masu-formen {masu!r} slutar inte på ます")
            stam = masu[:-2] + "ません"
            return stam + "でした" if m.tid is Tidsreferens.FÖRFLUTEN else stam
        # Japanskan har ingen egen perfektform — た-formen täcker både
        # avslutad dåtid och nuvarande relevans. Perfekt renderas därför
        # som förfluten, vilket är korrekt men gör att distinktionen inte
        # går att öva på japanska.
        förfluten = (m.tid is Tidsreferens.FÖRFLUTEN
                     or m.aspekt is Aspekt.PERFEKT)
        if förfluten:
            if not masu.endswith("ます"):
                raise RenderingsFel(
                    f"ja: masu-formen {masu!r} slutar inte på ます — artigt "
                    f"förflutet kan inte komponeras")
            return masu[:-2] + "ました"
        # Japanskan har inget futurum: icke-förfluten form täcker nutid och
        # framtid, och tidsadverbialet gör skillnaden.
        return masu

    def predikativ(self, m: Mening) -> list[str]:
        """Predikativ i japanskan — och tempus hamnar på ADJEKTIVET.

        彼女は嬉しいです / 彼女は嬉しかったです. Kopulan です böjs inte i
        adjektivsatser; det är adjektivet som bär tempus. Att skriva
        嬉しいでした är fel. Med substantiv är det tvärtom: 医者です blir
        医者でした, och där bär kopulan tempus.

        na-adjektiv tar INTE な här. な är attributivt (簡単な本) medan
        predikativet är bart (簡単です).
        """
        if not isinstance(m.predikativ, str):
            return [self.u.form(self.u.lexem(m.predikativ.koncept), "jisho")]
        if m.grad is not Grad.POSITIV:
            # Japanskan böjer inte adjektiv i grad. Komparativ markeras med
            # もっと eller inte alls, och jämförelseledet med より FÖRE det
            # jämförda — omvänt mot alla sex andra språken.
            adjektiv = self.u.lexem(m.predikativ)
            ut = ""
            if m.jämförelse is not None:
                ut += self.nominalfras(m.jämförelse) + self.u.form_för(
                    "komp_än", "inv")
            elif m.grad is Grad.KOMPARATIV:
                ut += self.u.form_för("komp_mer", "inv")
            return [ut + self.u.form(adjektiv, "jisho")]
        adjektiv = self.u.lexem(m.predikativ)
        typ = adjektiv["ja_adjektiv_typ"]

        # "bli glad" är inte kopula utan なる, och adjektivet står i ku-form:
        # 嬉しくなりました. En helt annan konstruktion än 嬉しいです.
        if m.verb == "verb_bli":
            if typ != "i":
                raise RenderingsFel(
                    f"ja/{adjektiv['lemma']}: なる med {typ}-adjektiv kräver "
                    f"に i stället för く — inte byggt")
            return [self.u.form(adjektiv, "ku")]
        if typ == "i":
            cell = "ta" if m.tid is Tidsreferens.FÖRFLUTEN else "jisho"
            return [self.u.form(adjektiv, cell)]
        if typ in ("na", "no", "verbfras"):
            return [self.u.form(adjektiv, "jisho") if typ == "na"
                    else adjektiv["lemma"]]
        raise RenderingsFel(
            f"ja/{adjektiv['lemma']}: ja_adjektiv_typ saknas")

    def rendera(self, m: Mening) -> str:
        """SOV: ämne, adverbial, indirekt objekt, objekt, verb."""
        if m.komplement is not None:
            raise RenderingsFel(
                "ja: infinitivkomplement finns inte i japanskan. Modalitet "
                "uttrycks med suffix och konstruktioner på HUVUDVERBET — "
                "読みたい (vill), 読める (kan), 読まなければならない (måste) — "
                "inte med ett styrande verb plus infinitiv. Kräver en egen "
                "modell och är inte byggt")
        delar = [self.nominalfras(m.subjekt) + TOPIK]
        for adverbial in m.adverbial:
            if isinstance(adverbial, str):
                delar.append(self.u.form_för(adverbial, "inv") + "、")
            else:
                # Japanskan har POSTpositioner: 学校で, inte で学校.
                # Ordningen är alltså omvänd mot alla sex andra språken.
                delar.append(self.nominalfras(adverbial.komplement)
                             + self.u.form_för(adverbial.preposition, "inv"))
        if m.io is not None:
            delar.append(self.nominalfras(m.io) + DATIV)
        if m.objekt is not None:
            delar.append(self.nominalfras(m.objekt) + OBJEKT)
        if m.predikativ is not None:
            delar.append("".join(self.predikativ(m)))
            # I-adjektivet bär tempus i KOPULASATSER (嬉しかったです), men
            # inte med なる — där är det verbet som böjs (嬉しくなりました).
            if (m.verb == "verb_vara" and isinstance(m.predikativ, str)
                    and self.u.lexem(m.predikativ)["ja_adjektiv_typ"] == "i"):
                delar.append(self.u.form_för(m.verb, "masu"))
                return "".join(delar) + ("か。" if m.fråga else "。")
        delar.append(self.verbform(m))
        return "".join(delar) + ("か。" if m.fråga else "。")
