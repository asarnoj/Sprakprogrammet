"""ordbok tagga-koncept / tagga-monster — LLM-taggning av Koncept och Mönster.

  ordbok tagga-koncept --verbose
  ordbok tagga-monster --verbose

Båda skriver en SQL-migration i ordbok/migrationer/ OCH kör den mot
databasen. Migrationen behövs eftersom `ordbok import --återinitiera`
bygger om från CSV och tappar all taggning.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..db import STANDARD_DB, anslut
from ..generering.taggning import (
    STANDARD_TAGGNINGSMODELL, tagga_koncept, tagga_lexem, tagga_monster,
)

MIGRATIONSKATALOG = Path("ordbok/migrationer")


def lägg_till_argument(p: argparse.ArgumentParser, standard_batch: int) -> None:
    p.add_argument("--migration", default=None,
                   help="SQL-fil att skriva (default: ordbok/migrationer/<jobb>.sql)")
    p.add_argument("--antal", type=int, default=None,
                   help="Tagga bara de N första koncepten — för att provköra "
                        "och granska utdata innan hela satsen körs.")
    p.add_argument("--koncept", default=None,
                   help="Kommaseparerade konceptnycklar — tagga bara dessa. "
                        "Endast tagga-monster.")
    p.add_argument("--batch-storlek", type=int, default=standard_batch,
                   dest="batch_storlek",
                   help=f"Antal koncept per LLM-anrop (default: {standard_batch})")
    p.add_argument("--modell", default=STANDARD_TAGGNINGSMODELL,
                   help=f"Claude-modell (default: {STANDARD_TAGGNINGSMODELL})")
    p.add_argument("--verbose", action="store_true", help="Skriv ut batch-progress")


def _kör(args: argparse.Namespace, jobb: str) -> int:
    if not STANDARD_DB.exists():
        print(f"FEL: {STANDARD_DB.name} finns inte. Kör 'ordbok import' först.",
              file=sys.stderr)
        return 1

    migration = Path(args.migration) if args.migration else MIGRATIONSKATALOG / f"{jobb}.sql"
    migration.parent.mkdir(parents=True, exist_ok=True)

    conn = anslut()
    print(f"\n{'─' * 50}")
    print(f"Taggar: {jobb}   (modell: {args.modell})")
    funktion = {"koncepttaggning": tagga_koncept,
                "lexemtaggning": tagga_lexem,
                "monstertaggning": tagga_monster}[jobb]
    extra = {}
    if jobb == "monstertaggning" and args.koncept:
        extra["koncept"] = [k.strip() for k in args.koncept.split(",") if k.strip()]
    stat = funktion(conn, migration, antal=args.antal,
                    batch_storlek=args.batch_storlek,
                    modell=args.modell, verbose=args.verbose, **extra)
    conn.close()

    stat.skriv_ut()
    return 1 if stat.fel else 0


def kör_koncept(args: argparse.Namespace) -> int:
    return _kör(args, "koncepttaggning")


def kör_lexem(args: argparse.Namespace) -> int:
    return _kör(args, "lexemtaggning")


def kör_monster(args: argparse.Namespace) -> int:
    return _kör(args, "monstertaggning")
