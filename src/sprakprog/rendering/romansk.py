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
    Aspekt, Bestämdhet, Mening, Nominalfras, Numerus, Referentgenus,
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

    def verbdelar(self, m: Mening) -> list[str]:
        person, numerus, subjektsgenus = self._subjektsform(m.subjekt)

        sammansatt = (self.SAMMANSATT_DÅTID
                      and m.tid is Tidsreferens.FÖRFLUTEN
                      and m.aspekt is Aspekt.PERFEKTIV)
        if sammansatt:
            verb = self.u.lexem(m.verb)
            hjälp = verb["hjälpverb"]
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
            cell = ("pp_msc_sg" if hjälp == "ha" else
                    f"pp_{_kön(subjektsgenus)}_{numerus}")
            return [self.u.form_för("verb_ha" if hjälp == "ha" else "verb_vara",
                                    f"pres_{person}{numerus}"),
                    self.u.form(verb, cell)]

        if m.tid is Tidsreferens.FÖRFLUTEN and m.aspekt is Aspekt.PERFEKTIV:
            stam = "pret"
        else:
            stam = ENKELT_TEMPUS.get((m.tid, m.aspekt))
        if stam is None:
            raise RenderingsFel(
                f"{self.SPRÅK}: {m.tid}/{m.aspekt} saknar mappning till cell")
        return [self.u.form_för(m.verb, f"{stam}_{person}{numerus}")]

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
                    ut[-1] = ut[-1][:-1] + "'" + o
                    continue
            ut.append(o)
        return ut

    def eliderar(self, första: str, andra: str) -> bool:
        return False

    # ── sats ─────────────────────────────────────────────────────────

    def klitika(self, m: Mening) -> list[str]:
        """Obligatoriska klitika före verbet. Bara spanskan har några."""
        return []

    def rendera(self, m: Mening) -> str:
        ord = [*self.nominalfras(m.subjekt, "subjekt"), *self.klitika(m),
               *self.verbdelar(m)]

        if m.objekt is not None:
            ord += self.nominalfras(m.objekt, "objekt")
        if m.io is not None:
            prep = self.preposition_för(m.verb, "io")
            if prep is not None:
                ord.append(self.u.form_för(prep, "inv"))
                ord += self.nominalfras(m.io, "efter_preposition")
            else:
                ord += self.nominalfras(m.io, "objekt")
        for adverbial in m.adverbial:
            ord.append(self.u.form_för(adverbial, "inv"))

        mening = " ".join(self.sandhi(ord))
        return mening[0].upper() + mening[1:] + "."
