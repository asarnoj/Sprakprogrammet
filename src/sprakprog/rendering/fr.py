"""Fransk renderare.

Tredje språket, och det som sätter tre kolumner på prov som varken svenskan
eller tyskan rör:

  hjälpverb              "a donné" mot "est venue". Valet är lexikalt per
                         verb och ligger på Lexem.

  prenominal             "un livre rouge" — adjektivet står EFTER
                         substantivet. Både sv och de har det före, så
                         ordningen inuti nominalfrasen har aldrig prövats.

  preposition_koncept_id "à son frère". Det indirekta objektet realiseras
                         med preposition i stället för kasus, vilket är
                         andra halvan av det rektion.sql beskriver.

Och det är här `Aspekt` börjar göra nytta. Svenskan och tyskan ignorerar
axeln; franskan kan inte det. "a donné" (passé composé) och "donnait"
(imparfait) är samma tidsreferens och skiljs BARA på aspekt.

Satsklammern från tyskan återanvänds men placeras annorlunda: franskans
particip står direkt efter hjälpverbet, tyskans infinita delar sist. Att
uppdelningen håller men placeringen skiljer sig är precis vad en riktig
ordföljdsmodell behöver kunna uttrycka.
"""

from __future__ import annotations

import sqlite3

from .spec import (
    Aspekt, Bestämdhet, Mening, Nominalfras, Numerus, Referentgenus,
    RenderingsFel, Tidsreferens,
)
from .uppslag import Uppslag

MASKULIN, FEMININ = 1, 2

# h räknas med: alla sex h-initiala substantiv i databasen (homme,
# heure, histoire, hôpital, huile, herbe) har h muet och ska elideras.
VOKAL = set("aeiouyàâäéèêëîïôöûüùh")

# Sammandragningar som franskan gör obligatoriskt mellan två ord.
# à + le → au, de + les → des. Ordnas som (första, andra) → ersättning.
SAMMANDRAG = {
    ("à", "le"): "au", ("à", "les"): "aux",
    ("de", "le"): "du", ("de", "les"): "des",
}


def _sammandrag(ord: list[str]) -> list[str]:
    """Elision och sammandragning — franskans obligatoriska sandhi.

    Elisionen (le/la → l' framför vokal) lades medvetet här och inte i
    Former: den beror på NÄSTA ord, inte på artikeln, och kan därför inte
    lagras som en cell. it lo/gli är motsatt fall — där är allomorfen
    lexikaliserad nog att höra hemma i datan.

    Känd gräns: h aspiré. Franskan skiljer på "l'homme" (h muet) och
    "le héros" (h aspiré), och skillnaden syns inte i stavningen — den är
    lexikal och databasen har ingen markering för den. Samtliga sex
    h-initiala substantiv som finns är h muet, så elision är rätt för hela
    det nuvarande ordförrådet. Läggs ett h aspiré-ord till behövs en flagga
    på Lexem, i stil med prenominal.
    """
    ut: list[str] = []
    for o in ord:
        if ut:
            ersättning = SAMMANDRAG.get((ut[-1], o))
            if ersättning is not None:
                ut[-1] = ersättning
                continue
            if ut[-1] in ("le", "la") and o[:1].lower() in VOKAL:
                ut[-1] = "l'" + o
                continue
        ut.append(o)
    return ut

# Franskan saknar kasus. Tidsreferens + aspekt räcker för att peka ut cellen,
# utom i passé composé som byggs av två ord.
ENKELT_TEMPUS = {
    (Tidsreferens.NUTID, Aspekt.PERFEKTIV): "pres",
    (Tidsreferens.NUTID, Aspekt.IMPERFEKTIV): "pres",
    (Tidsreferens.FÖRFLUTEN, Aspekt.IMPERFEKTIV): "imperf",
    (Tidsreferens.FRAMTID, Aspekt.PERFEKTIV): "fut",
    (Tidsreferens.FRAMTID, Aspekt.IMPERFEKTIV): "fut",
}


def _participcell(genus: int, numerus: Numerus) -> str:
    kön = "msc" if genus == MASKULIN else "fem"
    tal = "pl" if numerus is Numerus.PL else "sg"
    return f"pp_{kön}_{tal}"


def _adjektivcell(genus: int, numerus: Numerus) -> str:
    kön = "msc" if genus == MASKULIN else "fem"
    tal = "pl" if numerus is Numerus.PL else "sg"
    return f"pos_{kön}_{tal}"


class FranskRenderare:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, "fr")
        self.conn = conn

    # ── nominalfras ──────────────────────────────────────────────────

    def preposition_för(self, verb: str, slot: str) -> str | None:
        """Realiseras slotten med preposition i franskan?

        Läser MönsterKrav via det språkspecifika mönstret, samma väg som
        tyskan hämtar sin kasus. Samma kolumnpar, två olika strategier.
        """
        rad = self.conn.execute(
            """SELECT p.nyckel FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               JOIN Koncept p ON p.id = mk.preposition_koncept_id
               WHERE k.nyckel = ? AND m.språk = 'fr' AND mk.slot = ?""",
            (verb, slot),
        ).fetchone()
        return rad["nyckel"] if rad else None

    def nominalfras(self, nf: Nominalfras, roll: str = "objekt") -> list[str]:
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

        if huvud["ordklass"] == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"fr/{huvud['lemma']}: ett pronomen kan inte ta artikel, "
                    f"attribut eller possessiv")
            # Franskan har fyra pronomenserier, en per syntaktisk roll:
            # sujet (je), cod (me), coi (me), tonique (moi). Tyskan klarade
            # sig med kasus på EN serie; franskan gör inte det.
            if roll == "subjekt":
                return [self.u.form(huvud, "sujet")]
            if roll == "efter_preposition":
                return [self.u.form(huvud, "tonique")]
            raise RenderingsFel(
                f"fr/{huvud['lemma']}: objektspronomen är klitika och står FÖRE "
                f"verbet ('elle le lui a donné'), inte där ett substantiv står. "
                f"Klitikaplacering är inte byggd — se RENDERARE_KRAV §3.9")

        genus = huvud["genus"]
        if genus is None:
            raise RenderingsFel(
                f"fr/{huvud['lemma']}: genus saknas — artikel, adjektiv och "
                f"possessiv kongruerar alla med det")

        före: list[str] = []
        if nf.possessiv is not None:
            # Possessiven kongruerar med det ÄGDA: "son frère" om brodern är
            # maskulin, oavsett om ägaren är hon eller han. Franskan saknar
            # helt svenskans sin/hans-distinktion, så koreferensen syns inte.
            cell = ("obest_a_pl" if nf.numerus is Numerus.PL
                    else "obest_m_sg" if genus == MASKULIN else "obest_f_sg")
            före.append(self.u.form_för(nf.possessiv, cell))
        else:
            artikel = ("artikel_bestamd" if nf.bestämdhet is Bestämdhet.BESTÄMD
                       else "artikel_obestamd")
            cell = ("pl" if nf.numerus is Numerus.PL
                    else "m_sg" if genus == MASKULIN else "f_sg")
            före.append(self.u.form_för(artikel, cell))

        # Adjektivets plats är en LEXIKAL egenskap, inte en regel: de flesta
        # franska adjektiv står efter substantivet, men BAGS-gruppen (grand,
        # petit, bon ...) står före. Därför Lexem.prenominal.
        efter: list[str] = []
        for attribut in nf.attribut:
            adjektiv = self.u.lexem(attribut)
            form = self.u.form(adjektiv, _adjektivcell(genus, nf.numerus))
            (före if adjektiv["prenominal"] else efter).append(form)

        return [*före, self.u.form(huvud, "pl" if nf.numerus is Numerus.PL else "sg"),
                *efter]

    # ── verb ─────────────────────────────────────────────────────────

    def _subjektsform(self, nf: Nominalfras) -> tuple[int, str, int]:
        rad = self.conn.execute(
            "SELECT person, numerus FROM Koncept WHERE nyckel = ?",
            (nf.koncept,)).fetchone()
        person = rad["person"] if rad and rad["person"] else 3
        numerus = "pl" if nf.numerus is Numerus.PL else "sg"
        if rad and rad["numerus"] == 2:
            numerus = "pl"
        # Participet kongruerar med subjektets genus. För pronomen finns
        # inget grammatiskt genus på lexemet — där är det referentens kön
        # som avgör, och det står i specifikationen.
        if nf.referent is not None:
            genus = FEMININ if nf.referent is Referentgenus.FEMININ else MASKULIN
        else:
            genus = self.u.lexem(nf.koncept)["genus"] or MASKULIN
        return person, numerus, genus

    def verbdelar(self, m: Mening) -> list[str]:
        """Verbet som ett eller två ord — hjälpverbet först, participet direkt efter."""
        person, numerus, subjektsgenus = self._subjektsform(m.subjekt)

        if m.tid is Tidsreferens.FÖRFLUTEN and m.aspekt is Aspekt.PERFEKTIV:
            verb = self.u.lexem(m.verb)
            hjälp = verb["hjälpverb"]
            if hjälp not in ("ha", "vara"):
                raise RenderingsFel(
                    f"fr/{verb['lemma']}: hjälpverb={hjälp!r} — passé composé "
                    f"kan inte byggas utan att veta om det är avoir eller être")
            hjälpkoncept = "verb_ha" if hjälp == "ha" else "verb_vara"

            # Particip med être kongruerar med subjektet ("elle est venue");
            # med avoir gör det inte det så länge objektet står efter verbet.
            if hjälp == "vara":
                cell = _participcell(
                    subjektsgenus,
                    Numerus.PL if numerus == "pl" else Numerus.SG)
            else:
                cell = "pp_msc_sg"
            return [self.u.form_för(hjälpkoncept, f"pres_{person}{numerus}"),
                    self.u.form(verb, cell)]

        stam = ENKELT_TEMPUS.get((m.tid, m.aspekt))
        if stam is None:
            raise RenderingsFel(f"fr: {m.tid}/{m.aspekt} saknar mappning till cell")
        return [self.u.form_för(m.verb, f"{stam}_{person}{numerus}")]

    # ── sats ─────────────────────────────────────────────────────────

    def rendera(self, m: Mening) -> str:
        """Fransk huvudsats: subjekt, verb, objekt, prepositionsobjekt, adverbial.

        Det direkta objektet står före det indirekta när det senare är en
        prepositionsfras — "donné un livre rouge à son frère", inte tvärtom.
        Det är motsatt tyskan, där dativobjektet kommer först.
        """
        ord = [*self.nominalfras(m.subjekt, "subjekt"), *self.verbdelar(m)]

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

        mening = " ".join(_sammandrag(ord))
        return mening[0].upper() + mening[1:] + "."
