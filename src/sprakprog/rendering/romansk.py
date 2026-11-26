"""Gemensam bas för de romanska renderarna.

Franskan byggdes först och ensam. När spanskan och italienskan skulle till
visade det sig att de delar nästan allt: substantiv med sg/pl, adjektiv och
particip som kongruerar i genus och numerus, possessiv som följer det ägda,
fyra pronomenserier, och prepositionsrealiserat indirekt objekt.

Det som faktiskt skiljer ligger som klassattribut här nedanför. Tre saker
är värda att peka ut, för de är inte kosmetiska:

  SAMMANSATT_DÅTID   Franskan och italienskan bygger perfektiv dåtid av
                     hjälpverb plus particip (a donné, ha dato). Spanskan
                     använder ett syntetiskt pretteritum (dio). Samma
                     specifikation, två helt olika verbfraser.

  hjälpverb          fr avoir/être och it avere/essere väljs per verb ur
                     Lexem.hjälpverb. Spanskan har bara haber och läser
                     aldrig kolumnen.

  artikelcell        Italienskan har fonologiskt betingade allomorfer
                     (il/lo, i/gli) som ligger som egna celler i Former.
                     Franskan och spanskan har inga.

Sandhi — elision och sammandragning — ligger kvar i renderaren och inte i
Former, eftersom den beror på NÄSTA ord och därför inte kan lagras som en
cell. Italienskans lo/gli är motsatt fall: allomorfen bestäms av det
följande ordet men är lexikaliserad nog att vara en riktig form.
"""

from __future__ import annotations

import sqlite3

from .spec import (
    Aspekt, Bestämdhet, Diates, Mening, Nominalfras, Numerus, Referentgenus,
    RenderingsFel, Tidsreferens,
)
from .uppslag import Uppslag

MASKULIN, FEMININ = 1, 2

ENKELT_TEMPUS = {
    (Tidsreferens.NUTID, Aspekt.PERFEKTIV): "pres",
    (Tidsreferens.NUTID, Aspekt.IMPERFEKTIV): "pres",
    (Tidsreferens.FÖRFLUTEN, Aspekt.IMPERFEKTIV): "imperf",
    (Tidsreferens.FRAMTID, Aspekt.PERFEKTIV): "fut",
    (Tidsreferens.FRAMTID, Aspekt.IMPERFEKTIV): "fut",
}


def _kön(genus: int) -> str:
    return "msc" if genus == MASKULIN else "fem"


def _tal(numerus: Numerus) -> str:
    return "pl" if numerus is Numerus.PL else "sg"


class RomanskRenderare:
    SPRÅK: str
    SUBJEKTSCELL: str
    TONISK: str
    SAMMANSATT_DÅTID: bool
    # Spanskan bildar ALLTID perfekt med haber. Franskan och italienskan
    # väljer per verb ur Lexem.hjälpverb, som därför bara är ifylld för dem.
    HJÄLPVERB_FAST: str | None = None
    VOKAL = set("aeiouyàâäéèêëîïôöûüùáíóúñòì")
    SAMMANDRAG: dict[tuple[str, str], str] = {}

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, self.SPRÅK)
        self.conn = conn

    # ── språkspecifika krokar ────────────────────────────────────────

    def possessivcell(self, genus: int, numerus: Numerus) -> str:
        raise NotImplementedError

    def artikelcell(self, genus: int, numerus: Numerus, huvudord: str,
                    bestämd: bool) -> str:
        """Cell i artikelparadigmet. `huvudord` behövs bara för italienskan."""
        if numerus is Numerus.PL:
            return "m_pl" if genus == MASKULIN else "f_pl"
        return "m_sg" if genus == MASKULIN else "f_sg"

    # ── rektion ──────────────────────────────────────────────────────

    def preposition_för(self, verb: str, slot: str) -> str | None:
        rad = self.conn.execute(
            """SELECT p.nyckel FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               JOIN Koncept p ON p.id = mk.preposition_koncept_id
               WHERE k.nyckel = ? AND m.språk = ? AND mk.slot = ?""",
            (verb, self.SPRÅK, slot),
        ).fetchone()
        return rad["nyckel"] if rad else None

    # ── nominalfras ──────────────────────────────────────────────────

    def nominalfras(self, nf: Nominalfras, roll: str = "objekt") -> list[str]:
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

        if huvud["ordklass"] == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"{self.SPRÅK}/{huvud['lemma']}: ett pronomen kan inte ta "
                    f"artikel, attribut eller possessiv")
            if roll == "subjekt":
                return [self.u.form(huvud, self.SUBJEKTSCELL)]
            if roll == "efter_preposition":
                return [self.u.form(huvud, self.TONISK)]
            raise RenderingsFel(
                f"{self.SPRÅK}/{huvud['lemma']}: objektspronomen är klitika och "
                f"står FÖRE verbet, inte där ett substantiv står. "
                f"Klitikaplacering är inte byggd — se RENDERARE_KRAV §3.9")

        genus = huvud["genus"]
        if genus is None:
            raise RenderingsFel(
                f"{self.SPRÅK}/{huvud['lemma']}: genus saknas — artikel, "
                f"adjektiv och possessiv kongruerar alla med det")

        huvudform = self.u.form(huvud, _tal(nf.numerus))
        före: list[str] = []
        if nf.possessiv is not None:
            före.append(self.u.form_för(
                nf.possessiv, self.possessivcell(genus, nf.numerus)))
        else:
            bestämd = nf.bestämdhet is Bestämdhet.BESTÄMD
            före.append(self.u.form_för(
                "artikel_bestamd" if bestämd else "artikel_obestamd",
                self.artikelcell(genus, nf.numerus, huvudform, bestämd)))

        # Adjektivets plats är lexikal, inte regelstyrd: de flesta romanska
        # adjektiv står efter substantivet, men en liten grupp står före.
        efter: list[str] = []
        for attribut in nf.attribut:
            adjektiv = self.u.lexem(attribut)
            form = self.u.form(
                adjektiv, f"pos_{_kön(genus)}_{_tal(nf.numerus)}")
            (före if adjektiv["prenominal"] else efter).append(form)

        # "le livre de la fille" — romanska språk uttrycker genitiv med
        # preposition, inte med kasus, och attributet står efter huvudordet.
        # Sammandragningen de+le→du och di+il→del sköts av sandhi().
        if nf.ägare is not None:
            efter.append(self.u.form_för("prep_av", "inv"))
            efter.extend(self.nominalfras(nf.ägare))

        return [*före, huvudform, *efter]

    # ── verb ─────────────────────────────────────────────────────────

    def _subjektsform(self, nf: Nominalfras) -> tuple[int, str, int]:
        rad = self.conn.execute(
            "SELECT person, numerus FROM Koncept WHERE nyckel = ?",
            (nf.koncept,)).fetchone()
        person = rad["person"] if rad and rad["person"] else 3
        numerus = "pl" if nf.numerus is Numerus.PL else "sg"
        if rad and rad["numerus"] == 2:
            numerus = "pl"
        if nf.referent is not None:
            genus = FEMININ if nf.referent is Referentgenus.FEMININ else MASKULIN
        else:
            genus = self.u.lexem(nf.koncept)["genus"] or MASKULIN
        return person, numerus, genus

    def verbdelar(self, m: Mening, föregående_objekt=None) -> list[str]:
        if m.diates is not Diates.AKTIV:
            # "le livre est lu", "el libro es leído" — vara plus particip
            # som kongruerar med subjektet, precis som être-participen i
            # sammansatt dåtid. Spanskan använder ser, inte estar.
            person, numerus, genus = self._subjektsform(m.subjekt)
            # Dåtida passiv skiljer sig: spanskan tar indefinido ("fue
            # leído"), franskan och italienskan imperfekt ("était lu", "era
            # letto") eftersom deras pret är passé simple respektive passato
            # remoto — litterära tempus som ingen inlärare behöver.
            #
            # KÄND GRÄNS: den sammansatta perfektiva passiven ("a été lu",
            # "è stato letto") är inte byggd. Den kräver tre verbdelar.
            if m.tid is not Tidsreferens.FÖRFLUTEN:
                stam = "pres"
            else:
                stam = "imperf" if self.SAMMANSATT_DÅTID else "pret"
            return [self.u.form_för("verb_vara", f"{stam}_{person}{numerus}",
                                    "permanent"),
                    self.u.form_för(m.verb, f"pp_{_kön(genus)}_{numerus}")]
        """`föregående_objekt` är (genus, numerus) för ett objektsklitikum.

        Med 'ha'-hjälpverbet kongruerar participet med det direkta objektet
        BARA när objektet står före verbet — vilket det gör just när det är
        ett klitikum: "la fille les lui a donnés". Står objektet efter sker
        ingen kongruens: "la fille a donné les livres".
        """
        person, numerus, subjektsgenus = self._subjektsform(m.subjekt)
        variant = self.kopulavariant(m)

        # Perfekt är alltid sammansatt. Perfektiv dåtid är det bara i
        # franskan och italienskan — spanskan har ett syntetiskt preteritum
        # där, vilket är hela skillnaden mellan "ha leído" och "leyó".
        sammansatt = m.aspekt is Aspekt.PERFEKT or (
            self.SAMMANSATT_DÅTID and m.tid is Tidsreferens.FÖRFLUTEN
            and m.aspekt is Aspekt.PERFEKTIV)
        if sammansatt:
            verb = self.u.lexem(m.verb)
            hjälp = self.HJÄLPVERB_FAST or verb["hjälpverb"]
            if hjälp == "båda":
                # 'båda' betyder att valet inte kan avgöras på lexemet utan
                # på användningen: transitivt tar avere ("ha corso i 100 m"),
                # intransitivt essere ("è corso via"). Meningen vet vilket,
                # eftersom den säger om det finns ett direkt objekt — och det
                # är precis därför kolumnen fick värdet 'båda' i stället för
                # att gissas när den fylldes.
                hjälp = "ha" if m.objekt is not None else "vara"
            if hjälp not in ("ha", "vara"):
                raise RenderingsFel(
                    f"{self.SPRÅK}/{verb['lemma']}: hjälpverb={hjälp!r} — "
                    f"sammansatt dåtid kan inte byggas utan att veta vilket")
            # Particip med 'vara' kongruerar med subjektet (elle est venue,
            # è andata); med 'ha' gör det inte det när objektet står efter.
            if hjälp == "vara":
                cell = f"pp_{_kön(subjektsgenus)}_{numerus}"
            elif föregående_objekt is not None:
                objgenus, objnumerus = föregående_objekt
                cell = f"pp_{_kön(objgenus)}_{_tal(objnumerus)}"
            else:
                cell = "pp_msc_sg"
            # Pluskvamperfekt: hjälpverbet i imperfekt. "elle avait lu".
            hjälpstam = ("imperf" if m.aspekt is Aspekt.PERFEKT
                         and m.tid is Tidsreferens.FÖRFLUTEN else "pres")
            return [self.u.form_för("verb_ha" if hjälp == "ha" else "verb_vara",
                                    f"{hjälpstam}_{person}{numerus}",
                                    "hjälpverb" if hjälp == "ha" else None),
                    self.u.form(verb, cell)]

        if m.tid is Tidsreferens.FÖRFLUTEN and m.aspekt is Aspekt.PERFEKTIV:
            stam = "pret"
        else:
            stam = ENKELT_TEMPUS.get((m.tid, m.aspekt))
        if stam is None:
            raise RenderingsFel(
                f"{self.SPRÅK}: {m.tid}/{m.aspekt} saknar mappning till cell")
        return [self.u.form_för(m.verb, f"{stam}_{person}{numerus}", variant)]

    # ── sandhi ───────────────────────────────────────────────────────

    def sandhi(self, ord: list[str]) -> list[str]:
        """Elision och sammandragning mellan intilliggande ord."""
        ut: list[str] = []
        for o in ord:
            if ut:
                ersättning = self.SAMMANDRAG.get((ut[-1], o))
                if ersättning is not None:
                    ut[-1] = ersättning
                    continue
                if self.eliderar(ut[-1], o):
                    # Sista vokalen faller: le → l', ne → n', que → qu'.
                    ut[-1] = ut[-1][:-1] + "'" + o
                    continue
            ut.append(o)
        return ut

    def eliderar(self, första: str, andra: str) -> bool:
        return False

    # ── klitika ──────────────────────────────────────────────────────

    DUBBLERAR = False

    def _pronomen(self, nf: Nominalfras | None):
        """Lexemet om frasen är ett rent pronomen, annars None."""
        if nf is None:
            return None
        lx = self.u.lexem(nf.koncept, nf.referent.value if nf.referent else None)
        return lx if lx["ordklass"] == "Pronomen" else None

    def _klitika(self, nf: Nominalfras | None, cell: str):
        """(form, person) för ett objektspronomen, annars None."""
        lx = self._pronomen(nf)
        if lx is None:
            return None
        rad = self.conn.execute(
            "SELECT person FROM Koncept WHERE nyckel = ?", (nf.koncept,)).fetchone()
        return self.u.form(lx, cell), (rad["person"] if rad else 3) or 3

    def _objektskongruens(self, nf: Nominalfras | None):
        """(genus, numerus) för ett objektsklitikum, för participkongruens."""
        if nf is None:
            return None
        rad = self.conn.execute(
            "SELECT numerus FROM Koncept WHERE nyckel = ?", (nf.koncept,)).fetchone()
        numerus = (Numerus.PL if (rad and rad["numerus"] == 2)
                   or nf.numerus is Numerus.PL else Numerus.SG)
        if nf.referent is not None:
            genus = FEMININ if nf.referent is Referentgenus.FEMININ else MASKULIN
        else:
            genus = self.u.lexem(nf.koncept)["genus"] or MASKULIN
        return genus, numerus

    # Franskans ne har ingen motsvarighet i es/it, som klarar sig med en
    # enda preverbal partikel.
    NEKANDE_FÖRLED: str | None = None
    # Franskan inleder ja/nej-frågor med est-ce que. Spanskan och
    # italienskan behåller ordföljden och markerar bara med skiljetecken.
    FRÅGEINLEDNING: str | None = None
    FRÅGETECKEN_FÖRE: str = ""

    def negation(self, m: Mening) -> tuple[list[str], list[str]]:
        """(före verbet, efter verbet). Romanska språk skiljer sig här.

        es och it sätter en partikel före verbet: "no lee", "non legge".
        Franskan klämmer in verbet mellan två: "ne lit pas". Förledet ne
        finns inte som lexem i databasen — det är en ren grammatisk klitika
        utan egen betydelse, hårdkodad här på samma sätt som japanskans
        partiklar. Efterledet pas ligger däremot i neg_inte.
        """
        if not m.negerad:
            return [], []
        if self.NEKANDE_FÖRLED is not None:
            return [self.NEKANDE_FÖRLED], [self.u.form_för("neg_inte", "inv")]
        return [self.u.form_för("neg_inte", "inv")], []

    def ordna_klitika(self, cod, coi) -> list[str]:
        """Inbördes ordning mellan klitika framför verbet.

        Franskans regel: första och andra person står först (me le donne),
        tredje person tvärtom (le lui donne). Det är inte godtyckligt utan
        två skilda serier som råkar dela plats.
        """
        if cod and coi:
            return ([coi[0], cod[0]] if coi[1] in (1, 2)
                    else [cod[0], coi[0]])
        return [x[0] for x in (cod, coi) if x]

    # ── sats ─────────────────────────────────────────────────────────

    def kopulavariant(self, m: Mening) -> str | None:
        """Vilken kopula språket ska använda. Bara spanskan har ett val."""
        return None

    def predikativ(self, m: Mening) -> list[str]:
        if isinstance(m.predikativ, str):
            # Romanska predikativ kongruerar med subjektet i genus och
            # numerus: "elle est heureuse", "ils sont heureux".
            _, numerus, genus = self._subjektsform(m.subjekt)
            tal = Numerus.PL if numerus == "pl" else Numerus.SG
            return [self.u.form_för(
                m.predikativ, f"pos_{_kön(genus)}_{_tal(tal)}")]
        # Yrkesbeteckningar står utan artikel: "elle est médecin".
        return [self.u.form(self.u.lexem(m.predikativ.koncept),
                            _tal(m.predikativ.numerus))]

    def rendera(self, m: Mening) -> str:
        ord: list[str] = []
        if m.fråga and self.FRÅGEINLEDNING:
            ord.append(self.FRÅGEINLEDNING)
        ord += self.nominalfras(m.subjekt, "subjekt")

        # Objektspronomen realiseras som klitika FÖRE verbet, inte på
        # substantivets plats. Det är därför nominalfras() vägrar rollen
        # "objekt" för pronomen — de ska aldrig hamna där.
        cod = self._klitika(m.objekt, "cod")
        coi = self._klitika(m.io, "coi")
        if coi is None and self.DUBBLERAR and m.io is not None:
            coi = self._dubblering(m.io)

        före, efter = self.negation(m)
        ord += före
        ord += self.ordna_klitika(cod, coi)
        verb = self.verbdelar(m, self._objektskongruens(m.objekt) if cod else None)
        # Negationens efterled hamnar efter det FINITA verbet, inte efter
        # participet: "elle n'a pas donné", aldrig "elle n'a donné pas".
        ord.append(verb[0])
        ord += efter
        ord += verb[1:]

        if m.komplement is not None:
            markör = self.u.infinitivmarkör(m.verb)
            if markör is not None:
                ord.append(self.u.form_för(markör, "inv"))
            ord.append(self.u.form_för(m.komplement, "inf"))
        if m.predikativ is not None:
            ord += self.predikativ(m)
        if m.objekt is not None and cod is None:
            ord += self.nominalfras(m.objekt, "objekt")
        if m.io is not None and self._pronomen(m.io) is None:
            prep = self.preposition_för(m.verb, "io")
            if prep is not None:
                ord.append(self.u.form_för(prep, "inv"))
                ord += self.nominalfras(m.io, "efter_preposition")
            else:
                ord += self.nominalfras(m.io, "objekt")
        for adverbial in m.adverbial:
            if isinstance(adverbial, str):
                ord.append(self.u.form_för(adverbial, "inv"))
            else:
                # Sammandragningen de+le→du sköts av sandhi, precis som
                # för genitivet — samma mekanism, annan preposition.
                ord.append(self.u.form_för(adverbial.preposition, "inv"))
                ord += self.nominalfras(adverbial.komplement)

        mening = " ".join(self.sandhi(ord))
        mening = mening[0].upper() + mening[1:]
        if m.fråga:
            return self.FRÅGETECKEN_FÖRE + mening + "?"
        return mening + "."
