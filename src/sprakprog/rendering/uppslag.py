"""Uppslagslagret — koncept + cell → ordform.

Renderaren ska aldrig känna till Former-tabellens axelkodning. Den frågar
efter "bok, bestämd singular" via cell-ID och får tillbaka en sträng.

Cellmatchningen återanvänder `_former_per_cell` från granskningen i stället
för att skriva en ny. Den logiken har rättats två gånger (SCHEMA.md §5 om
bitmask-kollaps, och kandidaten som tillhör en mer specifik cell) och en
andra implementation skulle med säkerhet återinföra samma buggar.
"""

from __future__ import annotations

import sqlite3
from ..generering.granskning import _former_per_cell
from ..kaikki_mappning.paradigm import ladda_legend, ladda_slot
from .spec import NAKEN, Numerus, RenderingsFel

# docs/BITMASK.md §11. Enda biten uppslaget behöver känna till, och bara
# för att välja mellan vem och vad.
MÄNSKLIG = 32


class Uppslag:
    """Slår upp lexem och former för ETT språk."""

    def __init__(self, conn: sqlite3.Connection, språk: str) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.språk = språk
        self._legend = ladda_legend()
        self._slot: dict[str, object] = {}
        # Cellmatchningen är dyr och svaret beror bara på lexemet. Utan
        # cache körs den om för varje enskild ordform: ett brett svep över
        # databasen gick från minuter till sekunder med den här raden.
        self._cellcache: dict[int, dict[str, str]] = {}

    # ── lexem ────────────────────────────────────────────────────────

    def lexem(self, koncept: str, variant: str | None = None) -> sqlite3.Row:
        """Hitta lexemet för ett koncept i det här språket.

        `variant` behövs när ett koncept har flera lemman i samma språk —
        sv hans/sin, es ser/estar. Utan den är uppslaget tvetydigt och vi
        vägrar hellre än gissar.
        """
        rader = self.conn.execute(
            """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id
               WHERE k.nyckel = ? AND l.språk = ?""",
            (koncept, self.språk),
        ).fetchall()
        if not rader:
            raise RenderingsFel(f"{self.språk}: inget lexem för konceptet {koncept!r}")
        if len(rader) == 1:
            return rader[0]

        träffar = [r for r in rader if r["variant"] == variant]
        if len(träffar) == 1:
            return träffar[0]

        # Etiketten 'neutral' betyder omarkerad form: ja 私 mot 僕, あなた mot
        # 君. Skillnaden är register, som ligger utanför projektets scope
        # (se ÖVERLÄMNING.md), så den omarkerade formen är rätt default när
        # meningen inte säger något annat.
        if variant is None:
            neutrala = [r for r in rader if r["variant"] == "neutral"]
            if len(neutrala) == 1:
                return neutrala[0]
        varianter = sorted(str(r["variant"]) for r in rader)
        raise RenderingsFel(
            f"{self.språk}: {koncept!r} har {len(rader)} lemman "
            f"(varianter: {', '.join(varianter)}) och variant={variant!r} "
            f"pekar inte ut ett enda")

    # ── former ───────────────────────────────────────────────────────

    def _celler(self, lexem: sqlite3.Row) -> dict[str, str]:
        if lexem["id"] not in self._cellcache:
            rader = self.conn.execute(
                "SELECT * FROM Former WHERE lexem_id = ?", (lexem["id"],)).fetchall()
            self._cellcache[lexem["id"]] = _former_per_cell(
                rader, self._slot_för(lexem["ordklass"]))
        return self._cellcache[lexem["id"]]

    def infinitivmarkör(self, verb: str) -> str | None:
        """Konceptnyckeln för markören framför ett infinitivkomplement.

        None = ren infinitiv. Läses ur det språkspecifika mönstret, samma
        väg som kasusrektionen och den romanska io-prepositionen.
        """
        rad = self.conn.execute(
            """SELECT p.nyckel FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               JOIN Koncept p ON p.id = mk.preposition_koncept_id
               WHERE k.nyckel = ? AND m.språk = ? AND mk.slot = 'komplement'""",
            (verb, self.språk)).fetchone()
        return rad["nyckel"] if rad else None

    def kontrollera_naken(self, nf) -> None:
        """En naken SINGULAR kräver ett oräknebart huvudord.

        "vatten", "vin", "kaffe" går bra; "bok" gör det inte — "hon läser
        bok" finns inte i något av de sju språken. Plural är fri: "böcker är
        dyra" är den generiska frasen för räknebara ord, och oräknebara har
        ingen plural att be om.

        `Koncept.räknebar` fylldes långt innan någon konstruktion behövde
        den. Det här är den första som gör det — samma sak som hände med
        MönsterKrav.frastyp och hjälpverbskolumnen.
        """
        if nf.bestämdhet not in NAKEN or nf.numerus is not Numerus.SG:
            return
        rad = self.conn.execute(
            "SELECT räknebar FROM Koncept WHERE nyckel = ?", (nf.koncept,)).fetchone()
        if rad is not None and rad["räknebar"]:
            raise RenderingsFel(
                f"{self.språk}/{nf.koncept}: naken singular kräver ett "
                f"oräknebart ord — 'vatten' går, 'bok' gör det inte. "
                f"Räknebara ord tar artikel i singular eller står i plural")

    def frågepronomen(self, koncept: str) -> str:
        """vem eller vad — avgörs på det EFTERFRÅGADE, inte på slotten.

        "Vem läser boken?" men "Vad läser flickan?": samma slot, olika ord,
        och skillnaden ligger i om svaret är mänskligt. Semantikbiten som
        restriktionerna redan använder räcker för att avgöra det, så
        frågeordet behöver ingen egen taggning.
        """
        rad = self.conn.execute(
            "SELECT semantik FROM Koncept WHERE nyckel = ?", (koncept,)).fetchone()
        mänsklig = bool(rad and (rad["semantik"] or 0) & MÄNSKLIG)
        return "frågepronomen_person" if mänsklig else "frågepronomen_sak"

    def _slot_för(self, ordklass: str):
        if ordklass not in self._slot:
            self._slot[ordklass] = ladda_slot(
                self.språk, ordklass, legend=self._legend)
        return self._slot[ordklass]

    def form(self, lexem: sqlite3.Row, cell: str) -> str:
        """Ordformen i en given cell. Kastar hellre än returnerar tomt."""
        celler = self._celler(lexem)
        if cell not in celler:
            känd = ", ".join(sorted(celler))
            raise RenderingsFel(
                f"{self.språk}/{lexem['lemma']}: cellen {cell!r} finns inte i "
                f"{lexem['ordklass']}-paradigmet (har: {känd})")
        form = celler[cell]
        if not form:
            raise RenderingsFel(
                f"{self.språk}/{lexem['lemma']}: cellen {cell!r} är tom — "
                f"formen saknas i databasen")
        return form

    def form_för(self, koncept: str, cell: str, variant: str | None = None) -> str:
        return self.form(self.lexem(koncept, variant), cell)
