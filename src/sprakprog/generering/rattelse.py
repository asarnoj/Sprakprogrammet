"""Tillämpa granskningens förslag på Former — utan att fråga någon modell.

Granskningen har redan gjort det dyra arbetet: för varje fel står den rätta
formen i kolumnen `förslag`. Att skriva in dem är en databasuppdatering, inte
en ny generering. Noll LLM-anrop, några sekunder.

Rättelserna skrivs också som en SQL-migration, eftersom `ordbok import
--återinitiera` bygger om databasen och tappar allt som inte finns som fil.

Två fall hanteras inte automatiskt och rapporteras i stället:

  Kollaps med motstridiga förslag — en Former-rad kan täcka flera celler
  (SCHEMA.md §5). Får två av dem olika förslag går det inte att skriva båda
  till samma rad; formen behöver troligen delas i två rader först.

  Tomt förslag — granskningen menar att formen inte borde finnas. Att radera
  raden skulle ta bort den för alla celler den täcker, vilket sällan är vad
  som avses. Kräver ett mänskligt beslut.
"""

from __future__ import annotations

import csv
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..kaikki_mappning.paradigm import ALLA_AXLAR, ladda_legend, ladda_slot
from .granskning import _former_per_cell, _matchar


@dataclass
class Rättelsestatistik:
    tillämpade: int = 0
    hoppade_tomma: int = 0
    hoppade_konflikt: int = 0
    hoppade_okända: int = 0
    anmärkningar: list[str] = field(default_factory=list)

    def skriv_ut(self) -> None:
        print(f"Rättelser tillämpade : {self.tillämpade}")
        print(f"Hoppade (tomt förslag): {self.hoppade_tomma}")
        print(f"Hoppade (kollaps)     : {self.hoppade_konflikt}")
        print(f"Hoppade (hittades ej) : {self.hoppade_okända}")
        if self.anmärkningar:
            print(f"Att titta på ({len(self.anmärkningar)}):")
            for a in self.anmärkningar[:15]:
                print(f"  {a}")
            if len(self.anmärkningar) > 15:
                print(f"  ... och {len(self.anmärkningar) - 15} till")


def _rad_för_cell(rader: list[sqlite3.Row], slot, cell_id: str) -> sqlite3.Row | None:
    """Vilken Former-rad läste granskningen ur för den här cellen?

    Använder samma matchning som granskningen, så att rättelsen träffar
    exakt den rad som rapporterades.
    """
    cell = next((c for c in slot.celler if c.id == cell_id), None)
    if cell is None:
        return None
    former = _former_per_cell(rader, slot)
    väntad = former.get(cell_id)
    if not väntad:
        return None
    return next(
        (r for r in rader
         if r["form"] == väntad
         and all(_matchar(r[a], cell.axlar.get(a), a) for a in ALLA_AXLAR)),
        None,
    )


def tillämpa_granskning(
    conn: sqlite3.Connection,
    rapport: Path,
    migration: Path,
    *,
    torkörning: bool = False,
) -> Rättelsestatistik:
    stat = Rättelsestatistik()
    legend = ladda_legend()

    rader = [
        r for r in csv.DictReader(rapport.open(encoding="utf-8"), delimiter="\t")
        if r["allvar"] == "fel" and r["nuvarande"] != r["förslag"]
    ]

    # Gruppera per lexem så att slot-fil och Former-rader läses en gång.
    per_lexem: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in rader:
        per_lexem[(r["språk"], r["ordklass"], r["lemma"])].append(r)

    satser: list[str] = []
    for (språk, ordklass, lemma), poster in sorted(per_lexem.items()):
        slot = ladda_slot(språk, ordklass, legend=legend)
        db_rader = conn.execute(
            """SELECT f.* FROM Former f JOIN Lexem l ON l.id = f.lexem_id
               WHERE l.lemma = ? AND l.språk = ?""", (lemma, språk),
        ).fetchall()

        # Samla förslag per Former-rad, så att kollapskonflikter syns.
        per_rad: dict[int, list[dict]] = defaultdict(list)
        for p in poster:
            if not p["förslag"].strip():
                stat.hoppade_tomma += 1
                stat.anmärkningar.append(
                    f"tomt förslag: {språk}/{lemma} {p['cell']} = {p['nuvarande']!r}")
                continue
            rad = _rad_för_cell(db_rader, slot, p["cell"])
            if rad is None:
                stat.hoppade_okända += 1
                stat.anmärkningar.append(
                    f"hittade ingen rad: {språk}/{lemma} {p['cell']}")
                continue
            per_rad[rad["id"]].append(p)

        for rad_id, p_lista in per_rad.items():
            förslag = {p["förslag"] for p in p_lista}
            if len(förslag) > 1:
                stat.hoppade_konflikt += len(p_lista)
                celler = ", ".join(p["cell"] for p in p_lista)
                stat.anmärkningar.append(
                    f"kollaps med olika förslag: {språk}/{lemma} [{celler}] "
                    f"→ {sorted(förslag)}")
                continue
            ny = förslag.pop()
            satser.append(
                f"UPDATE Former SET form = '{ny.replace(chr(39), chr(39) * 2)}' "
                f"WHERE id = {rad_id};")
            stat.tillämpade += 1

    if torkörning:
        print(f"  [torrkörning] {len(satser)} UPDATE-satser skulle köras")
        for s in satser[:10]:
            print(f"    {s}")
        return stat

    if satser:
        migration.write_text(
            "/* ── granskningsrattelser — förslag ur ordbok/granskning.tsv ────────\n"
            "   Genererad av `ordbok tillämpa-granskning`. Ett UPDATE per rättad\n"
            "   form. Granskningen tog fram förslagen; det här skriver bara in\n"
            "   dem, utan att fråga någon modell.\n"
            "\n"
            "   OBS: raderna är knutna till Former.id, som ändras vid\n"
            "   ombyggnad. Kör därför den här migrationen SIST och bara mot en\n"
            "   databas byggd ur samma former.tsv. Exportera om former.tsv\n"
            "   efteråt, så blir rättelserna en del av datan i stället.\n"
            "   ──────────────────────────────────────────────────────────────── */\n\n"
            + "\n".join(satser) + "\n",
            encoding="utf-8",
        )
        with conn:
            conn.executescript("\n".join(satser))
        print(f"  → {migration} ({len(satser)} rättelser, körda mot databasen)")

    return stat
