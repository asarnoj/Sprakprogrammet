"""ordbok import — läser CSV-filer och fyller sprak.db.

Designbeslut:
  1. Samma koncept i flera filer  → hårt fel
  2. källa härleds från filnamnet  → 'bas_kärna.csv' → 'bas_kärna'
  3. Befintlig databas              → vägra utan --återinitiera
  4. Ogiltiga rader                 → samla alla, avbryt utan att skriva
  5. Ordklass-konflikt per koncept  → hårt fel med radhänvisningar

Importen är transaktionell: antingen skrivs allt, eller inget.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from ..csv_läsare import CSVRad, läs_csv
from ..db import STANDARD_DB, skapa_tom_databas
from ..validering import validera_rad


def kör(args: argparse.Namespace) -> int:
    filer = [Path(f) for f in args.filer]

    # ── 1. Filer existerar ───────────────────────────────────────────────
    saknade = [f for f in filer if not f.is_file()]
    if saknade:
        for f in saknade:
            print(f"FEL: filen saknas: {f}", file=sys.stderr)
        return 1

    # ── 2. Databasen existerar inte (om inte --återinitiera) ─────────────
    if STANDARD_DB.exists() and not args.återinitiera:
        print(
            f"FEL: {STANDARD_DB.name} finns redan. "
            f"Använd --återinitiera för att radera och bygga om.",
            file=sys.stderr,
        )
        return 1

    # ── 3. Läs alla rader ─────────────────────────────────────────────────
    alla_rader: list[CSVRad] = []
    try:
        for fil in filer:
            alla_rader.extend(läs_csv(fil))
    except ValueError as e:
        print(f"FEL: {e}", file=sys.stderr)
        return 1

    # ── 4. Validera varje rad ────────────────────────────────────────────
    fel = [f for r in alla_rader if (f := validera_rad(r)) is not None]
    if fel:
        print(f"FEL: {len(fel)} ogiltig(a) rader, importen avbruten:", file=sys.stderr)
        for f in fel[:20]:
            print(f"  {f.rad.fil}:{f.rad.radnummer}  {f.meddelande}", file=sys.stderr)
        if len(fel) > 20:
            print(f"  ... och {len(fel) - 20} till", file=sys.stderr)
        return 1

    # ── 5. Konsistenskontroller per koncept ──────────────────────────────
    koncept_till_fil: dict[str, str] = {}
    koncept_till_ordklass: dict[str, str] = {}
    koncept_första_rad: dict[str, CSVRad] = {}
    lexem_per_koncept: dict[str, list[CSVRad]] = defaultdict(list)

    konflikter: list[str] = []

    for rad in alla_rader:
        nyckel = rad.koncept
        if nyckel in koncept_till_fil:
            första = koncept_första_rad[nyckel]
            if koncept_till_fil[nyckel] != rad.fil:
                konflikter.append(
                    f"koncept {nyckel!r} finns i flera filer: "
                    f"{första.fil}:{första.radnummer} och {rad.fil}:{rad.radnummer}"
                )
            if koncept_till_ordklass[nyckel] != rad.ordklass:
                konflikter.append(
                    f"koncept {nyckel!r} har motstridig ordklass: "
                    f"{första.fil}:{första.radnummer} '{koncept_till_ordklass[nyckel]}' "
                    f"vs {rad.fil}:{rad.radnummer} '{rad.ordklass}'"
                )
        else:
            koncept_till_fil[nyckel] = rad.fil
            koncept_till_ordklass[nyckel] = rad.ordklass
            koncept_första_rad[nyckel] = rad
        lexem_per_koncept[nyckel].append(rad)

    if konflikter:
        # Avduplicera (samma konflikt kan triggas flera gånger)
        unika = list(dict.fromkeys(konflikter))
        print(f"FEL: {len(unika)} konsistensproblem:", file=sys.stderr)
        for k in unika[:20]:
            print(f"  {k}", file=sys.stderr)
        if len(unika) > 20:
            print(f"  ... och {len(unika) - 20} till", file=sys.stderr)
        return 1

    # ── 6. Dubbletter inom samma koncept (samma språk + lemma) ──────────
    lexem_dubletter: list[str] = []
    for nyckel, rader in lexem_per_koncept.items():
        sett: dict[tuple[str, str], CSVRad] = {}
        for r in rader:
            par = (r.språk, r.lemma)
            if par in sett:
                första = sett[par]
                lexem_dubletter.append(
                    f"duplicerat lexem {nyckel!r} {r.språk}={r.lemma!r}: "
                    f"{första.fil}:{första.radnummer} och {r.fil}:{r.radnummer}"
                )
            else:
                sett[par] = r

    if lexem_dubletter:
        print(f"FEL: {len(lexem_dubletter)} duplicerade lexem-rader:", file=sys.stderr)
        for d in lexem_dubletter[:20]:
            print(f"  {d}", file=sys.stderr)
        return 1

    # ── 7. Skriv till databasen ──────────────────────────────────────────
    conn = skapa_tom_databas()
    try:
        with conn:
            koncept_id_map: dict[str, int] = {}
            for nyckel, ordklass in koncept_till_ordklass.items():
                källa = Path(koncept_till_fil[nyckel]).stem  # 'bas_kärna.csv' → 'bas_kärna'
                cur = conn.execute(
                    "INSERT INTO Koncept (nyckel, ordklass, källa) VALUES (?, ?, ?)",
                    (nyckel, ordklass, källa),
                )
                koncept_id_map[nyckel] = cur.lastrowid

            lexem_count = 0
            for nyckel, rader in lexem_per_koncept.items():
                koncept_id = koncept_id_map[nyckel]
                for r in rader:
                    conn.execute(
                        "INSERT INTO Lexem (koncept_id, språk, lemma) VALUES (?, ?, ?)",
                        (koncept_id, r.språk, r.lemma),
                    )
                    lexem_count += 1
    finally:
        conn.close()

    # ── 8. Sammanfattning ────────────────────────────────────────────────
    print(f"✓ Importerade {len(koncept_id_map)} koncept och {lexem_count} lexem")
    per_källa: dict[str, int] = defaultdict(int)
    for nyckel in koncept_till_fil:
        per_källa[Path(koncept_till_fil[nyckel]).stem] += 1
    for källa, antal in sorted(per_källa.items()):
        print(f"  {källa}: {antal} koncept")
    print(f"  → {STANDARD_DB.name}")
    return 0
