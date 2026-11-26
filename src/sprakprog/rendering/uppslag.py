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
from .spec import RenderingsFel


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
