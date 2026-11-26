"""ordbok tillämpa-granskning — skriv in granskningens förslag i Former.

  ordbok tillämpa-granskning --torkörning
  ordbok tillämpa-granskning

Noll LLM-anrop. Granskningen har redan tagit fram rätt form för varje fel;
det här skriver bara in dem.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..db import STANDARD_DB, anslut
from ..generering.rattelse import tillämpa_granskning


def lägg_till_argument(p: argparse.ArgumentParser) -> None:
    p.add_argument("--rapport", default="ordbok/granskning.tsv",
                   help="Granskningsrapport att läsa förslagen ur")
    p.add_argument("--migration", default="ordbok/granskningsrattelser.sql",
                   help="SQL-fil att logga rättelserna till (INTE en migration — "
                        "se filhuvudet; sanningen är ordbok/former.tsv)")
    p.add_argument("--torkörning", action="store_true",
                   help="Visa vad som skulle ändras, skriv ingenting")


def kör(args: argparse.Namespace) -> int:
    rapport = Path(args.rapport)
    if not rapport.is_file():
        print(f"FEL: {rapport} finns inte.", file=sys.stderr)
        return 1
    if not STANDARD_DB.exists():
        print(f"FEL: {STANDARD_DB.name} finns inte.", file=sys.stderr)
        return 1

    conn = anslut()
    print(f"\n{'─' * 50}")
    print(f"Tillämpar granskningsförslag ur {rapport}")
    stat = tillämpa_granskning(conn, rapport, Path(args.migration),
                               torkörning=args.torkörning)
    conn.close()
    stat.skriv_ut()
    return 0
