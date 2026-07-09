"""ordbok generera — generera böjda former via Claude API.

Exempel:
  ordbok generera --språk sv --ordklass Verb --lemma tala,springa,vara
  ordbok generera --språk sv --ordklass Substantiv --batch-storlek 20
  ordbok generera --språk de --ordklass Adjektiv --torkörning --verbose
  ordbok generera --alla-språk --ordklass Verb
"""

from __future__ import annotations

import argparse
import sys

from ..db import STANDARD_DB, anslut
from ..modeller import ORDKLASSER, SPRÅK

from ..generering.pipeline import STANDARD_BATCH  # noqa: E402

STANDARD_MODELL = "claude-haiku-4-5"
ALLA_ORDKLASSER_MED_MORFOLOGI = [
    "Verb", "Substantiv", "Adjektiv", "Pronomen", "Frågepronomen",
]


def kör(args: argparse.Namespace) -> int:
    if not STANDARD_DB.exists():
        print(
            f"FEL: {STANDARD_DB.name} finns inte. Kör 'ordbok import' först.",
            file=sys.stderr,
        )
        return 1

    # Validera språk
    if args.alla_språk:
        språk_lista = sorted(SPRÅK)
    else:
        if args.språk not in SPRÅK:
            print(
                f"FEL: okänt språk {args.språk!r}. Giltiga: {', '.join(sorted(SPRÅK))}",
                file=sys.stderr,
            )
            return 1
        språk_lista = [args.språk]

    # Validera ordklass
    if args.ordklass and args.ordklass not in ORDKLASSER:
        print(
            f"FEL: okänd ordklass {args.ordklass!r}.",
            file=sys.stderr,
        )
        return 1
    ordklasser = [args.ordklass] if args.ordklass else ALLA_ORDKLASSER_MED_MORFOLOGI

    # Parsa lemman
    lemman: list[str] = []
    if args.lemma:
        lemman = [l.strip() for l in args.lemma.split(",") if l.strip()]

    conn = anslut()

    from ..generering.pipeline import generera_former

    batch_storlek = getattr(args, "batch_storlek", STANDARD_BATCH)
    modell = getattr(args, "modell", STANDARD_MODELL)
    torkörning = getattr(args, "torkörning", False)
    verbose = getattr(args, "verbose", False)
    fortsätt = getattr(args, "fortsätt", False)

    totalt_fel = 0

    for språk in språk_lista:
        for ordklass in ordklasser:
            print(f"\n{'─' * 50}")
            print(f"Genererar: {språk} / {ordklass}")
            if torkörning:
                print("  [TORKÖRNING — skriver inte till databasen]")

            stat = generera_former(
                lemman=lemman,
                språk=språk,
                ordklass=ordklass,
                conn=conn,
                batch_storlek=batch_storlek,
                modell=modell,
                torkörning=torkörning,
                verbose=verbose,
                fortsätt=fortsätt,
            )

            stat.skriv_ut()
            totalt_fel += len(stat.fel)

    conn.close()

    if totalt_fel:
        print(f"\n⚠ {totalt_fel} fel totalt. Se utskriften ovan.")
        return 1
    print("\n✓ Generering klar.")
    return 0


def lägg_till_argument(p: argparse.ArgumentParser) -> None:
    grupp = p.add_mutually_exclusive_group()
    grupp.add_argument("--språk", default="sv",
                       help="Språkkod: sv/en/fr/de/es/it/ja (default: sv)")
    grupp.add_argument("--alla-språk", action="store_true",
                       help="Kör alla 7 språk")
    p.add_argument("--ordklass", default=None,
                   help=f"Ordklass (default: alla med morfologi). "
                        f"Giltiga: {', '.join(ALLA_ORDKLASSER_MED_MORFOLOGI)}")
    p.add_argument("--lemma", default=None,
                   help="Kommaseparerad lista av lemman (default: alla i DB)")
    p.add_argument("--batch-storlek", type=int, default=STANDARD_BATCH,
                   dest="batch_storlek",
                   help=f"Antal lemman per LLM-anrop (default: {STANDARD_BATCH})")
    p.add_argument("--modell", default=STANDARD_MODELL,
                   help=f"Claude-modell (default: {STANDARD_MODELL})")
    p.add_argument("--torkörning", action="store_true",
                   help="Anropa LLM men skriv inte till databasen")
    p.add_argument("--fortsätt", action="store_true",
                   help="Hoppa över lexem som redan har Former-rader "
                        "(återuppta avbruten körning)")
    p.add_argument("--verbose", action="store_true",
                   help="Skriv ut batch-progress och råsvar vid fel")
