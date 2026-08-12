"""Tillämpa granskningens förslag på Former — utan att fråga någon modell.

Granskningen har redan gjort det dyra arbetet: för varje fel står den rätta
formen i kolumnen `förslag`. Att skriva in dem är en databasuppdatering, inte
en ny generering. Noll LLM-anrop, några sekunder.

Rättelserna skrivs också som en SQL-migration, eftersom `ordbok import
--återinitiera` bygger om databasen och tappar allt som inte finns som fil.

Fyra operationer behövs, inte en:

  SKRIV OM   Cellen har en rad och ska ha en annan form. Det vanliga fallet.

  LÄGG TILL  Cellen är tom — det finns ingen rad att skriva om. Axlarna tas
             rakt av från slot-filens cell, som är den auktoritativa
             beskrivningen av vad cellen betyder.

  DELA       En rad täcker flera celler (SCHEMA.md §5) som visar sig behöva
             olika former. Kollapsen uppstod för att FELET gjorde formerna
             identiska: sv/chef hade `chefs` med kasus=15, alltså både
             nom/ack/dat och genitiv. Rätt former (chefer/chefers) skiljer
             sig åt, så raden måste bli två. Raden byggs om cell för cell.

  TA BORT    Tomt förslag: formen ska inte finnas. Täcker raden även andra
             celler byggs den om utan den här cellen, i stället för att
             raderas — it/chi har EN rad som täcker både cellen `chi` och
             cellen `cosa`, och en rå DELETE skulle ta bort lemmat helt.

Uppslaget är nycklat på KONCEPT, inte bara lemma. Ett lemma kan höra till
flera lexem inom samma språk — 177 fall, t.ex. de/finden som är både
fys_hitta och gen_tycka, it/giocare som är både arb_leka och gen_spela.

Den första versionen slog ihop dem (`WHERE l.lemma = ? AND l.språk = ?`) och
lät granskningens `koncept`-kolumn ligga oanvänd. Rättelsen hamnade då på det
lexem vars rad råkade komma först: `giocherebbero` skrevs till arb_leka medan
gen_spela, som granskningen faktiskt gällde, blev kvar med fel form. Felet
syntes inte i statistiken — den räknade en lyckad rättelse.

`ordbok/beslut.tsv` går före granskningen. Granskningen är en stark modells
förslag, inte facit; när den har fel skrivs det rätta svaret in där med
motivering, i stället för att granskningsrapporten ändras. Rapporten är vad
modellen sa, och ska förbli det.
"""

from __future__ import annotations

import csv
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..kaikki_mappning.paradigm import (
    ALLA_AXLAR, INTFLAG_AXLAR, Cell, Slot, ladda_legend, ladda_slot,
)
from .granskning import _former_per_cell, _matchar

BESLUTSFIL = Path("ordbok/beslut.tsv")

# (språk, ordklass, koncept, lemma) — den nyckel som pekar ut ett lexem entydigt.
type Lexemnyckel = tuple[str, str, str, str]


@dataclass
class Rättelsestatistik:
    tillämpade: int = 0
    tillagda: int = 0
    delade: int = 0
    borttagna: int = 0
    beslut: int = 0
    oförändrade: int = 0
    hoppade_okända: int = 0
    anmärkningar: list[str] = field(default_factory=list)

    def skriv_ut(self) -> None:
        print(f"Omskrivna former     : {self.tillämpade}")
        print(f"Tillagda former      : {self.tillagda}")
        print(f"Delade rader         : {self.delade}")
        print(f"Borttagna former     : {self.borttagna}")
        print(f"Redan rätt           : {self.oförändrade}")
        if self.beslut:
            print(f"Ur beslut.tsv        : {self.beslut}")
        if self.hoppade_okända:
            print(f"Kunde inte placeras  : {self.hoppade_okända}")
        if self.anmärkningar:
            print(f"Att titta på ({len(self.anmärkningar)}):")
            for a in self.anmärkningar:
                print(f"  {a}")


def _cite(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


def _tilldelning(
    rader: list[sqlite3.Row], slot: Slot,
) -> dict[str, sqlite3.Row | None]:
    """Vilken Former-rad läser granskningen ur för varje cell?

    Samma matchning som granskningen använder, så att rättelsen träffar
    exakt den rad som rapporterades. Beräknas en gång per lexem.
    """
    former = _former_per_cell(rader, slot)
    ut: dict[str, sqlite3.Row | None] = {}
    for cell in slot.celler:
        väntad = former.get(cell.id)
        if not väntad:
            ut[cell.id] = None
            continue
        ut[cell.id] = next(
            (r for r in rader
             if r["form"] == väntad
             and all(_matchar(r[a], cell.axlar.get(a), a) for a in ALLA_AXLAR)),
            None,
        )
    return ut


def _slå_ihop_axlar(celler: list[Cell]) -> dict[str, int | None]:
    """Axlarna för en rad som ska täcka precis de här cellerna.

    Bitmask-axlar (tempus, kasus) OR:as ihop — det är just den kollapsen
    SCHEMA.md §5 beskriver. Övriga axlar måste redan vara lika; grupperingen
    i `_bygg_om` ser till det.
    """
    axlar: dict[str, int | None] = {}
    for axel in ALLA_AXLAR:
        if axel in INTFLAG_AXLAR:
            bitar = 0
            for c in celler:
                bitar |= c.axlar.get(axel) or 0
            axlar[axel] = bitar or None
        else:
            axlar[axel] = celler[0].axlar.get(axel)
    return axlar


def _bygg_om(celler_med_form: list[tuple[Cell, str]]) -> list[tuple[str, dict]]:
    """Gruppera (cell, form) till så få rader som möjligt.

    Två celler kan dela rad bara om de vill ha samma form OCH är lika på
    alla icke-bitmask-axlar. Celler utan form (tomt = ska inte finnas)
    faller bort.
    """
    grupper: dict[tuple, list[Cell]] = defaultdict(list)
    for cell, form in celler_med_form:
        if not form:
            continue
        fast = tuple(cell.axlar.get(a) for a in ALLA_AXLAR if a not in INTFLAG_AXLAR)
        grupper[(form, fast)].append(cell)
    return [(form, _slå_ihop_axlar(celler)) for (form, _), celler in grupper.items()]


def _infoga(lexem_id: int, form: str, axlar: dict[str, int | None]) -> str:
    kolumner = ["lexem_id", "form", *ALLA_AXLAR]
    värden = [str(lexem_id), _cite(form)]
    värden += ["NULL" if axlar.get(a) is None else str(axlar[a]) for a in ALLA_AXLAR]
    return f"INSERT INTO Former ({', '.join(kolumner)}) VALUES ({', '.join(värden)});"


def _läs_beslut(fil: Path) -> dict[tuple[Lexemnyckel, str], dict]:
    if not fil.is_file():
        return {}
    ut = {}
    for r in csv.DictReader(fil.open(encoding="utf-8"), delimiter="\t"):
        if not r.get("cell") or r["cell"].startswith("#"):
            continue
        nyckel = (r["språk"], r["ordklass"], r["koncept"], r["lemma"])
        ut[(nyckel, r["cell"])] = r
    return ut


def tillämpa_granskning(
    conn: sqlite3.Connection,
    rapport: Path,
    migration: Path,
    *,
    torkörning: bool = False,
    beslutsfil: Path = BESLUTSFIL,
) -> Rättelsestatistik:
    stat = Rättelsestatistik()
    legend = ladda_legend()
    beslut = _läs_beslut(beslutsfil)

    rader = [
        r for r in csv.DictReader(rapport.open(encoding="utf-8"), delimiter="\t")
        if r["allvar"] == "fel"
    ]

    # Nyckla på koncept, inte lemma: samma lemma kan vara flera lexem.
    per_lexem: dict[Lexemnyckel, dict[str, dict]] = defaultdict(dict)
    for r in rader:
        nyckel = (r["språk"], r["ordklass"], r["koncept"], r["lemma"])
        per_lexem[nyckel][r["cell"]] = r
    # Beslut kan gälla celler granskningen inte nämnde.
    for (nyckel, cell), r in beslut.items():
        per_lexem[nyckel].setdefault(cell, r)

    satser: list[str] = []
    for nyckel, poster in sorted(per_lexem.items()):
        språk, ordklass, koncept, lemma = nyckel
        slot = ladda_slot(språk, ordklass, legend=legend)

        lexem = conn.execute(
            """SELECT l.id FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id
               WHERE l.språk = ? AND l.lemma = ? AND k.nyckel = ?""",
            (språk, lemma, koncept),
        ).fetchall()
        if len(lexem) != 1:
            stat.hoppade_okända += len(poster)
            stat.anmärkningar.append(
                f"{len(lexem)} lexem för {språk}/{lemma} ({koncept}) — hoppar över")
            continue
        lexem_id = lexem[0]["id"]

        db_rader = conn.execute(
            "SELECT * FROM Former WHERE lexem_id = ?", (lexem_id,)).fetchall()
        tilldelat = _tilldelning(db_rader, slot)
        celler = {c.id: c for c in slot.celler}

        # Målform per cell: beslut går före granskning.
        mål: dict[str, str] = {}
        for cell_id, r in poster.items():
            if cell_id not in celler:
                stat.hoppade_okända += 1
                stat.anmärkningar.append(
                    f"okänd cell {språk}/{lemma} {cell_id} — finns inte i slot-filen")
                continue
            if (nyckel, cell_id) in beslut:
                mål[cell_id] = beslut[(nyckel, cell_id)]["form"]
                stat.beslut += 1
            else:
                mål[cell_id] = r["förslag"]

        # ── LÄGG TILL: celler utan rad ────────────────────────────────
        for cell_id, ny in mål.items():
            if tilldelat.get(cell_id) is not None:
                continue
            if not ny:
                stat.oförändrade += 1   # ska vara tom, är redan tom
                continue
            satser.append(_infoga(lexem_id, ny, celler[cell_id].axlar))
            stat.tillagda += 1

        # ── SKRIV OM / DELA / TA BORT: rader som berörs ───────────────
        celler_per_rad: dict[int, list[str]] = defaultdict(list)
        for cell_id, rad in tilldelat.items():
            if rad is not None:
                celler_per_rad[rad["id"]].append(cell_id)

        rad_per_id = {r["id"]: r for r in db_rader}
        for rad_id, cell_ids in celler_per_rad.items():
            berörda = [c for c in cell_ids if c in mål]
            if not berörda:
                continue
            rad = rad_per_id[rad_id]
            nya = {c: mål.get(c, rad["form"]) for c in cell_ids}

            if len(set(nya.values())) == 1:
                ny = next(iter(nya.values()))
                if ny == rad["form"]:
                    stat.oförändrade += len(berörda)
                elif ny:
                    satser.append(
                        f"UPDATE Former SET form = {_cite(ny)} WHERE id = {rad_id};")
                    stat.tillämpade += 1
                else:
                    satser.append(f"DELETE FROM Former WHERE id = {rad_id};")
                    stat.borttagna += 1
                continue

            # Formerna skiljer sig åt — raden måste byggas om.
            satser.append(f"DELETE FROM Former WHERE id = {rad_id};")
            grupper = _bygg_om([(celler[c], nya[c]) for c in cell_ids])
            for form, axlar in grupper:
                satser.append(_infoga(lexem_id, form, axlar))
            stat.delade += 1
            stat.borttagna += sum(1 for c in cell_ids if not nya[c])
            stat.anmärkningar.append(
                f"delade {språk}/{lemma} ({koncept}): 1 rad → {len(grupper)} "
                f"({', '.join(sorted({f for f, _ in grupper}))})")

    if torkörning:
        print(f"  [torrkörning] {len(satser)} satser skulle köras")
        for s in satser[:20]:
            print(f"    {s}")
        if len(satser) > 20:
            print(f"    ... och {len(satser) - 20} till")
        return stat

    if satser:
        migration.write_text(
            "/* ── granskningsrattelser — LOGG, INTE EN MIGRATION ─────────────────\n"
            "   Genererad av `ordbok tillämpa-granskning`. Granskningen tog fram\n"
            "   förslagen; det här skriver bara in dem, utan att fråga någon\n"
            "   modell. ordbok/beslut.tsv går före när granskningen har fel.\n"
            "\n"
            "   SPELA INTE UPP DEN HÄR FILEN IGEN. Satserna är knutna till\n"
            "   Former.id, och DELETE/INSERT flyttar id:n — mot en ombyggd\n"
            "   databas träffar de fel rader. Därför ligger filen medvetet\n"
            "   UTANFÖR ordbok/migrationer/, som körs i en loop vid varje\n"
            "   ombyggnad.\n"
            "\n"
            "   Rättelserna bevaras i stället genom `ordbok exportera-former\n"
            "   ordbok/former.tsv` direkt efter körningen. Då är de en del av\n"
            "   datan. Filen finns kvar bara för att gå att läsa i efterhand.\n"
            "   ──────────────────────────────────────────────────────────────── */\n\n"
            + "\n".join(satser) + "\n",
            encoding="utf-8",
        )
        with conn:
            conn.executescript("\n".join(satser))
        print(f"  → {migration} ({len(satser)} satser, körda mot databasen)")

    return stat
