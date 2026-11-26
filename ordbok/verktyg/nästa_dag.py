"""Flytta en kurs ett dygn framåt, för att kunna prova flera dagar i rad.

    python ordbok/verktyg/nästa_dag.py [--kurs FIL] [--dagar N]

Skälen och själva flytten står i `sprakprog.kurs.simulering`. Den här filen är
kommandoraden runt den, och finns för att flytten ska gå att göra utan att
starta ett pass. Dagspasset har samma val bakom `--simulera`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kurs.simulering import (  # noqa: E402
    OkändaStämplar, flytta_framåt)


def main() -> int:
    p = argparse.ArgumentParser(description="Flytta kursen ett dygn framåt.")
    p.add_argument("--kurs", default=str(ROT / "kurs.db"))
    p.add_argument("--dagar", type=int, default=1,
                   help="hur många dygn kursen ska flyttas framåt (1)")
    a = p.parse_args()
    if a.dagar < 1:
        p.error("--dagar måste vara minst 1")

    try:
        rader, kopia = flytta_framåt(a.kurs, a.dagar, rapport=print)
    except FileNotFoundError as fel:
        p.error(str(fel))
    except OkändaStämplar as fel:
        print(f"{a.kurs}: {fel}", file=sys.stderr)
        return 1

    print(f"\n{Path(a.kurs).name} flyttad {a.dagar} dygn framåt "
          f"({rader} tidsstämplar).")
    print(f"Kopia före flytten: {kopia.relative_to(ROT)}")
    print("Starta passet och tryck n — nya nivåer är öppna.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
