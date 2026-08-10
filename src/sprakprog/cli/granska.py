"""ordbok granska-former — låt en starkare modell läsa igenom Former.

Exempel:
  ordbok granska-former --språk de --ordklass Adjektiv --verbose
  ordbok granska-former --alla-språk --rapport ordbok/granskning.tsv --fortsätt
  ordbok granska-former --språk es --ordklass Verb --modell claude-sonnet-5

Granskningen ändrar aldrig databasen — den skriver en TSV med förslag.
Att tillämpa dem är ett separat beslut (KONVENTIONER.md §9).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..db import STANDARD_DB, anslut
from ..generering.granskning import (
    STANDARD_GRANSKNINGSMODELL, granska_former,
)
from ..modeller import ORDKLASSER, SPRÅK
from .generera import ALLA_ORDKLASSER_MED_MORFOLOGI

STANDARD_RAPPORT = "ordbok/granskning.tsv"


def lägg_till_argument(p: argparse.ArgumentParser) -> None:
    grupp = p.add_mutually_exclusive_group()
    grupp.add_argument("--språk", default="sv",
                       help="Språkkod: sv/en/fr/de/es/it/ja (default: sv)")
    grupp.add_argument("--alla-språk", action="store_true",
                       help="Granska alla 7 språk")
    p.add_argument("--ordklass", default=None,
                   help=f"Ordklass (default: alla med morfologi). "
                        f"Giltiga: {', '.join(ALLA_ORDKLASSER_MED_MORFOLOGI)}")
    p.add_argument("--lemma", default=None,
                   help="Kommaseparerad lista av lemman (default: alla i DB)")
    p.add_argument("--rapport", default=STANDARD_RAPPORT,
                   help=f"TSV-fil att skriva avvikelser till (default: {STANDARD_RAPPORT})")
    p.add_argument("--batch-storlek", type=int, default=None,
                   dest="batch_storlek",
                   help="Antal lexem per LLM-anrop. Default: räknas ut från "
                        "antalet celler i slot-filen, som vid generering.")
    p.add_argument("--modell", default=STANDARD_GRANSKNINGSMODELL,
                   help=f"Claude-modell (default: {STANDARD_GRANSKNINGSMODELL}). "
                        f"Poängen är en starkare modell än genereringens — "
                        f"claude-sonnet-5 är ett billigare alternativ.")
    p.add_argument("--fortsätt", action="store_true",
                   help="Hoppa över lexem som redan står i rapporten")
    p.add_argument("--verbose", action="store_true",
                   help="Skriv ut batch-progress")


def kör(args: argparse.Namespace) -> int:
    if not STANDARD_DB.exists():
        print(f"FEL: {STANDARD_DB.name} finns inte. Kör 'ordbok import' först.",
              file=sys.stderr)
        return 1

    if args.alla_språk:
        språk_lista = sorted(SPRÅK)
    else:
        if args.språk not in SPRÅK:
            print(f"FEL: okänt språk {args.språk!r}. "
                  f"Giltiga: {', '.join(sorted(SPRÅK))}", file=sys.stderr)
            return 1
        språk_lista = [args.språk]

    if args.ordklass and args.ordklass not in ORDKLASSER:
        print(f"FEL: okänd ordklass {args.ordklass!r}.", file=sys.stderr)
        return 1
    ordklasser = [args.ordklass] if args.ordklass else ALLA_ORDKLASSER_MED_MORFOLOGI

    lemman = [l.strip() for l in args.lemma.split(",") if l.strip()] if args.lemma else None

    rapport = Path(args.rapport)
    rapport.parent.mkdir(parents=True, exist_ok=True)
    if rapport.exists() and not args.fortsätt:
        print(f"FEL: {rapport} finns redan. Använd --fortsätt för att lägga till, "
              f"eller radera filen först.", file=sys.stderr)
        return 1

    conn = anslut()
    summa_fel = summa_osäkra = summa_lexem = summa_körfel = 0

    for språk in språk_lista:
        for ordklass in ordklasser:
            print(f"\n{'─' * 50}")
            print(f"Granskar: {språk} / {ordklass}   (modell: {args.modell})")

            stat = granska_former(
                språk=språk,
                ordklass=ordklass,
                conn=conn,
                rapport=rapport,
                lemman=lemman,
                batch_storlek=args.batch_storlek,
                modell=args.modell,
                fortsätt=args.fortsätt,
                verbose=args.verbose,
            )
            stat.skriv_ut()
            summa_fel += stat.avvikelser_fel
            summa_osäkra += stat.avvikelser_osäkra
            summa_lexem += stat.granskade_lexem
            summa_körfel += len(stat.fel)

    conn.close()

    print(f"\n{'═' * 50}")
    print(f"Granskade lexem : {summa_lexem}")
    print(f"Fel             : {summa_fel}")
    print(f"Osäkra          : {summa_osäkra}")
    if summa_lexem:
        print(f"Rapport         : {rapport}")
    if summa_körfel:
        print(f"\n{summa_körfel} körningsfel — se utskriften ovan.", file=sys.stderr)
        return 1
    return 0
