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

from .spec import (
    FRÅGESLOTTAR, Aspekt, Bisats, Diates, Grad, Mening, Nominalfras,
    RenderingsFel, Satsmodus,
    Tidsreferens, tilltal,
)
from .uppslag import Uppslag

# は markerar TEMA, が markerar subjekt. Skillnaden är
# informationsstruktur i huvudsats — men i bisats är den
# obligatorisk: en bisats har inget eget tema.
TOPIK, OBJEKT, DATIV, SUBJEKT = "は", "を", "に", "が"

# Frågadverb som kräver en partikel efter sig. どこ betyder "vilken
# plats" och är ett substantiv; どこで är "på vilken plats".
FRÅGEADVERBPARTIKEL = {"frågadverb_plats": "で"}


class JapanskRenderare:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, "ja")

    def nominalfras(self, nf: Nominalfras) -> str:
        huvud = self.u.lexem(nf.koncept)
        ord = ""

        if nf.frågedeterminant is not None:
            ord += self.u.form_för(nf.frågedeterminant, "inv")
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

    def verbform(self, m: Mening, enkel: bool = False) -> str:
        """Artig form. Register är renderarens val, inte en Former-axel.

        `enkel` ger den enkla formen i stället, och det är INTE ett
        registerval: en japansk bisats står alltid i enkel form, hur artig
        huvudsatsen än är. 彼が来たと言いました — 来た, aldrig 来ました.
        Artigheten sitter på satsen som helhet och realiseras en enda gång,
        på huvudverbet, sist.

        Det är därför de enkla formerna — jisho, ta, nai — var onåbara ända
        tills bisatsen byggdes, och det var fel att kalla dem register.
        """
        lexem = self.u.lexem(m.verb)
        celler = self.u._celler(lexem)
        if m.modus is Satsmodus.IMPERATIV:
            return self._uppmaning(m, lexem)
        if enkel:
            return self._enkel_form(m, lexem, celler)
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

    def _enkel_form(self, m: Mening, lexem, celler: dict[str, str]) -> str:
        """Enkel form: 読む / 読んだ / 読まない / 読まなかった.

        Tre av fyra ligger som egna celler. Den fjärde — enkelt förflutet
        NEKANDE — komponeras ur ない genom att byta ut ändelsen mot なかった,
        på samma sätt som ません komponeras ur ます-stammen. ない böjs som ett
        i-adjektiv, vilket är precis varför bytet är regelbundet.
        """
        förfluten = (m.tid is Tidsreferens.FÖRFLUTEN
                     or m.aspekt is Aspekt.PERFEKT)
        if m.diates is not Diates.AKTIV:
            # 読まれる är redan enkel form — det är den ARTIGA som måste
            # komponeras. Här räcker cellen, plus た-böjning för dåtid.
            ukemi = self.u.form(lexem, "ukemi")
            if not ukemi.endswith("る"):
                raise RenderingsFel(
                    f"ja: ukemi-formen {ukemi!r} slutar inte på る")
            if m.negerad:
                grund = ukemi[:-1] + "ない"
                return self._nekat_förflutet(grund) if förfluten else grund
            return ukemi[:-1] + "た" if förfluten else ukemi
        if m.negerad:
            nai = self.u.form(lexem, "nai")
            return self._nekat_förflutet(nai) if förfluten else nai
        if förfluten:
            return self.u.form(lexem, "ta")
        # i-adjektiv under ett verbkoncept (恋しい) har jisho men ingen masu;
        # jisho är rätt form för dem också, och utan です i bisats.
        return self.u.form(lexem, "jisho")

    @staticmethod
    def _nekat_förflutet(nai: str) -> str:
        """読まない → 読まなかった. ない böjs som i-adjektiv: い → かった."""
        if not nai.endswith("ない"):
            raise RenderingsFel(
                f"ja: ない-formen {nai!r} slutar inte på ない — enkelt nekat "
                f"förflutet kan inte komponeras")
        return nai[:-1] + "かった"

    def _uppmaning(self, m: Mening, lexem) -> str:
        """Uppmaning som て-form plus ください: 読んでください.

        Paradigmets 命令形 (読め) är den morfologiska imperativen, och den
        ligger i datan — men den är en ren befallning som knappt förekommer
        i tal, och renderaren har redan valt artig stil åt hela japanskan.
        Att blanda in 読め bland 読みます och 美しいです vore inte ett
        register­val utan en inkonsekvens. てください är den form en inlärare
        faktiskt möter som uppmaning, och ください finns redan i databasen
        som interj_please.

        Nekad uppmaning byggs ur ない-formen på samma sätt: 読まないでくださ
        い. Det är て-formen av negationen, komponerad ur cellen precis som
        ません komponeras ur ます-stammen.

        Förstapersonsplural är ingen uppmaning till någon annan utan ett
        förslag, och japanskan uttrycker det med ましょう ur samma ます-stam:
        読みましょう.
        """
        tal = tilltal(m, "ja", ("2sg", "2pl", "artig", "1pl"))
        if tal == "1pl":
            if m.negerad:
                # ましょう har ingen nekad motsvarighet. "Låt oss inte läsa"
                # blir en omskrivning (読むのはやめましょう) och byggs inte —
                # hellre det än att tappa negationen tyst.
                raise RenderingsFel(
                    "ja: nekat förslag (ましょう) finns inte som form — "
                    "japanskan skriver om det")
            masu = self.u.form(lexem, "masu")
            if not masu.endswith("ます"):
                raise RenderingsFel(
                    f"ja: masu-formen {masu!r} slutar inte på ます — "
                    f"ましょう kan inte komponeras")
            return masu[:-2] + "ましょう"
        snälla = self.u.form_för("interj_please", "inv")
        if m.negerad:
            return self.u.form(lexem, "nai") + "で" + snälla
        return self.u.form(lexem, "te") + snälla

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

    def satsled(self, m: Mening, bisats: bool = False) -> list[str]:
        """SOV: ämne, adverbial, indirekt objekt, objekt, verb.

        `bisats` ändrar två saker, och båda är grammatik och inte stil:
        verbet står i ENKEL form, och subjektet tar が i stället för は.
        は markerar satsens tema, och en bisats har inget eget tema — den
        ligger inuti huvudsatsens.
        """
        if m.komplement is not None:
            raise RenderingsFel(
                "ja: infinitivkomplement finns inte i japanskan. Modalitet "
                "uttrycks med suffix och konstruktioner på HUVUDVERBET — "
                "読みたい (vill), 読める (kan), 読まなければならない (måste) — "
                "inte med ett styrande verb plus infinitiv. Kräver en egen "
                "modell och är inte byggt")
        # Uppmaningen säger inte ut den tilltalade — 本を読んでください,
        # inte あなたは本を読んでください. Att sätta ut あなた är
        # dessutom påfallande i japanskan, inte bara överflödigt.
        # Wh-frågan flyttar INGENTING i japanskan: frågeordet står kvar där
        # ledet stod, med sin partikel kvar. Det är den enskilt största
        # syntaktiska skillnaden mot de sex andra språken, som alla flyttar
        # frågeordet först. Ett efterfrågat subjekt tar dessutom alltid が —
        # 誰は finns inte, eftersom det okända inte kan vara tema.
        if m.fråga_om == "subjekt":
            huvud = (self.nominalfras(m.subjekt)
                     if m.subjekt.frågedeterminant is not None
                     else self.u.form_för(
                         self.u.frågepronomen(m.subjekt.koncept), "jisho"))
            delar = [huvud + SUBJEKT]
        elif m.modus is Satsmodus.IMPERATIV:
            delar = []
        else:
            delar = [self.nominalfras(m.subjekt) + (SUBJEKT if bisats else TOPIK)]
        if m.fråga_om is not None and m.fråga_om not in FRÅGESLOTTAR:
            # どこ är ett substantiviskt frågeord och behöver platspartikeln
            # で precis som 学校で — den ligger redan i databasen som prep_i.
            # いつ och なぜ är adverb och står nakna. Skillnaden är lexikal,
            # inte syntaktisk, och därför en tabell och inte en regel.
            delar.append(self.u.form_för(m.fråga_om, "inv")
                         + FRÅGEADVERBPARTIKEL.get(m.fråga_om, ""))
        for adverbial in m.adverbial:
            if isinstance(adverbial, str):
                delar.append(self.u.form_för(adverbial, "inv") + "、")
            elif isinstance(adverbial, Bisats):
                delar.append(self.bisats(adverbial) + "、")
            else:
                # Japanskan har POSTpositioner: 学校で, inte で学校.
                # Ordningen är alltså omvänd mot alla sex andra språken.
                delar.append(self.nominalfras(adverbial.komplement)
                             + self.u.form_för(adverbial.preposition, "inv"))
        if m.bisats is not None:
            # ということ nominaliserar satsen. Resultatet ÄR en nominalfras
            # och tar objektspartikeln を som vilket objekt som helst —
            # ingen egen mekanism behövs, vilket är hela poängen med att
            # subjunktionen ligger i databasen som ett vanligt lemma.
            delar.append(self.bisats(m.bisats) + OBJEKT)
        if m.io is not None:
            delar.append(self._led(m, "io", m.io) + DATIV)
        if m.objekt is not None:
            delar.append(self._led(m, "objekt", m.objekt) + OBJEKT)
        if m.predikativ is not None:
            delar.append("".join(self.predikativ(m)))
            # I-adjektivet bär tempus i KOPULASATSER (嬉しかったです), men
            # inte med なる — där är det verbet som böjs (嬉しくなりました).
            if (m.verb == "verb_vara" and isinstance(m.predikativ, str)
                    and self.u.lexem(m.predikativ)["ja_adjektiv_typ"] == "i"):
                # です faller bort i bisats: 嬉しいとき, inte 嬉しいですとき.
                if not bisats:
                    delar.append(self.u.form_för(m.verb, "masu"))
                return delar
        delar.append(self.verbform(m, enkel=bisats))
        return delar

    def _led(self, m: Mening, slot: str, nf: Nominalfras) -> str:
        """Ledet självt, eller frågeordet om det är just det som efterfrågas."""
        if m.fråga_om == slot and nf.frågedeterminant is None:
            return self.u.form_för(self.u.frågepronomen(nf.koncept), "jisho")
        return self.nominalfras(nf)

    def bisats(self, b: Bisats) -> str:
        """Satsen först, subjunktionen sist — japanskan har POSTpositioner.

        Omvänt mot alla sex andra språken, precis som med prepositionerna.
        """
        return ("".join(self.satsled(b.sats, bisats=True))
                + self.u.form_för(b.subjunktion, "inv"))

    def rendera(self, m: Mening) -> str:
        frågande = m.fråga or m.fråga_om is not None
        return "".join(self.satsled(m)) + ("か。" if frågande else "。")
