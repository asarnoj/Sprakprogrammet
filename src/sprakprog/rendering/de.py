"""Tysk renderare.

Andra språket, och det som tvingar fram arkitekturen. Svenskan kom undan
med rak SVO och inget kasus. Tyskan kräver fyra saker som svenskan inte gör:

  KASUS          Varje nominalfras måste veta sin kasus, och kasusen kommer
                 inte från frasen utan från verbet. Det är därför
                 ordbok/migrationer/rektion.sql finns.

  DEKLINATION    Adjektivets ändelse beror på vad som står FRAMFÖR det:
                 "der rote Wein" (svag), "ein roter Wein" (blandad),
                 "roter Wein" (stark). Samma adjektiv, samma kasus, tre
                 ändelser. Determineraren styr alltså adjektivet.

  V2             Det finita verbet står på plats två i huvudsats. Ett — och
                 exakt ett — led står före det.

  SATSKLAMMER    Infinita verbdelar hamnar sist: "wird ... geben". Det gör
                 att verbfrasen inte kan renderas som ett sammanhängande
                 block, vilket den kunde i svenskan.

Personkongruens är också nytt: svenska "gav" är samma form för alla
personer, tyska "gab/gabst/gabt" är det inte.
"""

from __future__ import annotations

import sqlite3

from .spec import (
    Bestämdhet, Mening, Nominalfras, Numerus, RenderingsFel, Tidsreferens,
)
from .uppslag import Uppslag

# _legend.yaml: kasus är IntFlag (Nom=1, Ack=2, Dat=4, Gen=8), genus är
# IntEnum där tyskan läser UtrMask=maskulinum, NeuFem=femininum, Alla=neutrum.
KASUSNAMN = {1: "nom", 2: "akk", 4: "dat", 8: "gen"}
GENUSNAMN = {1: "m", 2: "f", 3: "n"}

# Kasus per slot när verbet inte säger något annat. Ackusativ på objektet
# är det normala; undantagen (helfen, danken, folgen ...) ligger i
# MönsterKrav och skriver över det här.
STANDARDKASUS = {"subjekt": 1, "objekt": 2, "io": 4}

TEMPUSSTAM = {
    Tidsreferens.NUTID: "pres",
    Tidsreferens.FÖRFLUTEN: "pret",
}


def _substantivcell(kasus: int, numerus: Numerus) -> str:
    """Tyska substantiv skiljer fyra kasus i singular, två i plural.

    Pluralen har egen dativform (den Bruedern) men slår ihop nom/akk/gen —
    därför cellen nom_akk_gen_pl, en bitmaskkollaps enligt SCHEMA.md §5.
    """
    if numerus is Numerus.PL:
        return "dat_pl" if kasus == 4 else "nom_akk_gen_pl"
    return f"{KASUSNAMN[kasus]}_sg"


class TyskRenderare:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, "de")
        self.conn = conn

    # ── rektion ──────────────────────────────────────────────────────

    def kasus_för(self, verb: str, slot: str) -> int:
        """Vilken kasus styr det här verbet på den här slotten?

        Läser det språkspecifika mönstret (Mönster.språk = 'de') som skuggar
        det universella. Finns ingen rad gäller standardkasus — ackusativ på
        objekt, dativ på indirekt objekt.
        """
        rad = self.conn.execute(
            """SELECT mk.kasus FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               WHERE k.nyckel = ? AND m.språk = 'de' AND mk.slot = ?
                 AND mk.kasus IS NOT NULL""",
            (verb, slot),
        ).fetchone()
        return rad["kasus"] if rad else STANDARDKASUS[slot]

    # ── nominalfras ──────────────────────────────────────────────────

    def nominalfras(self, nf: Nominalfras, kasus: int) -> list[str]:
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

        # Ett pronomen ÄR hela frasen. Det bär sin kasus i själva formen
        # (ich/mich/mir) och tar varken artikel eller attribut.
        if huvud["ordklass"] == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"de/{huvud['lemma']}: ett pronomen kan inte ta artikel, "
                    f"attribut eller possessiv")
            return [self.u.form(huvud, KASUSNAMN[kasus])]

        genus = huvud["genus"]
        if genus is None:
            raise RenderingsFel(
                f"de/{huvud['lemma']}: genus saknas — artikel, adjektivändelse "
                f"och possessiv går alla att avgöra först med det")
        g = GENUSNAMN[genus]
        k = KASUSNAMN[kasus]
        ord: list[str] = []

        # Determineraren avgör adjektivets deklination. Det är den enskilt
        # mest tyska regeln i filen: samma adjektiv får tre olika ändelser
        # beroende på vad som råkar stå framför det.
        if nf.possessiv is not None:
            cell = f"{g}_{k}" if nf.numerus is Numerus.SG else f"pl_{k}"
            ord.append(self.u.form_för(nf.possessiv, cell, "reflexiv"
                                       if nf.possessiv_koreferent else None))
            deklination = "bland"
        elif nf.bestämdhet is Bestämdhet.BESTÄMD:
            cell = f"{g}_{k}" if nf.numerus is Numerus.SG else f"pl_{k}"
            ord.append(self.u.form_för("artikel_bestamd", cell))
            deklination = "svag"
        elif nf.numerus is Numerus.SG:
            ord.append(self.u.form_för("artikel_obestamd", f"{g}_{k}"))
            deklination = "bland"
        else:
            # Obestämd plural saknar artikel i tyskan ("rote Buecher"), och
            # utan determinerare tar adjektivet stark ändelse.
            deklination = "stark"

        formgenus = g if nf.numerus is Numerus.SG else "pl"
        for attribut in nf.attribut:
            ord.append(self.u.form_för(
                attribut, f"pos_{deklination}_{formgenus}_{k}"))

        try:
            ord.append(self.u.form(huvud, _substantivcell(kasus, nf.numerus)))
        except RenderingsFel:
            # Plurale tantum: "Jeans" har ingen singular. Datan har ingen
            # flagga för det — tomma singularceller ÄR markeringen.
            celler = self.u._celler(huvud)
            if nf.numerus is Numerus.SG and not any(
                    celler.get(f"{k}_sg") for k in KASUSNAMN.values()):
                raise RenderingsFel(
                    f"de/{huvud['lemma']}: saknar singular helt (plurale tantum) "
                    f"— meningen kan inte be om sg") from None
            raise
        return ord

    # ── verb ─────────────────────────────────────────────────────────

    def _subjektsform(self, nf: Nominalfras) -> tuple[int, str]:
        """Person och numerus för kongruensen.

        Pronomenkoncept bär person och numerus på Koncept-nivå; vanliga
        substantiv är alltid tredje person.
        """
        rad = self.conn.execute(
            "SELECT person, numerus FROM Koncept WHERE nyckel = ?",
            (nf.koncept,)).fetchone()
        person = rad["person"] if rad and rad["person"] else 3
        numerus = "pl" if nf.numerus is Numerus.PL else "sg"
        if rad and rad["numerus"] == 2:
            numerus = "pl"
        return person, numerus

    def verbdelar(self, m: Mening) -> tuple[str, list[str]]:
        """Returnerar (finit verb, infinita delar sist i satsen).

        Uppdelningen ÄR satsklammern. Svenskan kunde returnera en lista som
        hölls ihop; tyskan måste skilja på det som står på plats två och det
        som hamnar i slutet.
        """
        person, numerus = self._subjektsform(m.subjekt)
        if m.tid is Tidsreferens.FRAMTID:
            # Futurum: werden böjt + huvudverbets infinitiv sist.
            return (self.u.form_för("modal_ska", f"pres_{person}{numerus}"),
                    [self.u.form_för(m.verb, "inf")])
        if m.tid not in TEMPUSSTAM:
            raise RenderingsFel(f"de: {m.tid} saknar mappning till verbcell")
        return self.u.form_för(m.verb, f"{TEMPUSSTAM[m.tid]}_{person}{numerus}"), []

    # ── sats ─────────────────────────────────────────────────────────

    def rendera(self, m: Mening) -> str:
        """Tysk huvudsats med V2 och satsklammer.

        Vorfeld | finit verb | Mittelfeld | infinita verbdelar

        I Mittelfeld står dativobjektet före ackusativobjektet när båda är
        substantiv, och tidsadverbialet mellan dem. Ordningen är hårdkodad
        precis som svenskans — men uppdelningen i fält är det inte, och det
        är den som en riktig ordföljdsmodell kommer att behöva.
        """
        finit, infinit = self.verbdelar(m)

        vorfeld = self.nominalfras(m.subjekt, self.kasus_för(m.verb, "subjekt"))
        mittelfeld: list[str] = []
        if m.io is not None:
            mittelfeld += self.nominalfras(m.io, self.kasus_för(m.verb, "io"))
        for adverbial in m.adverbial:
            mittelfeld.append(self.u.form_för(adverbial, "inv"))
        if m.objekt is not None:
            mittelfeld += self.nominalfras(m.objekt, self.kasus_för(m.verb, "objekt"))

        ord = [*vorfeld, finit, *mittelfeld, *infinit]
        mening = " ".join(ord)
        return mening[0].upper() + mening[1:] + "."
