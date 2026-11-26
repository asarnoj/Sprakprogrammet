"""Räkna ut kraven och nivåerna ur en sparad karta.

    python -m sprakprog.nivaer KARTA [KORT …]

Utan KORT räknas alla nivåkort i språket. Ett kort skrivs som i
`python -m sprakprog.sammansattning`: regel:val/tempusform/preteritum.
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path

from ..kortmodell import Kort
from ..rendering.karta import ladda
from ..sammansattning import Sammansättare
from . import Krav, Nivåkort, rita_nivåer

ROT = Path(__file__).resolve().parents[3]


def main() -> None:
    p = argparse.ArgumentParser(description="Räkna ut kraven och nivåerna.")
    p.add_argument("karta")
    p.add_argument("kort", nargs="*")
    a = p.parse_args()

    karta = ladda(a.karta)
    språk = karta["språk"]
    s = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta)
    nivå = Nivåkort(s.tabell)
    if a.kort:
        kort = []
        for text in a.kort:
            typ, _, nyckel = text.partition(":")
            kort.append(Kort(språk, typ, tuple(nyckel.split("/"))))
    else:
        kort = sorted(nivå.alla(karta), key=str)
    print(f"{språk}: {len(kort)} nivåkort", flush=True)

    krav = Krav(s, nivå)
    t = time.perf_counter()
    karta_ = rita_nivåer(krav, kort, rapport=lambda r: print(r, flush=True))
    print(f"\n{krav.frågor} frågor, {time.perf_counter() - t:.0f} s")

    print(f"\n{len(karta_.nivåer)} nivåer:")
    for i, nivån in enumerate(karta_.nivåer, 1):
        kraven = sorted({str(d) for k in nivån for d in karta_.krav[k] if d not in nivån})
        print(f"  {i:>3}. {', '.join(sorted(map(str, nivån)))}")
        if kraven:
            print(f"       kräver {', '.join(kraven)}")
    if karta_.oprövbara:
        print(f"\ninte prövbara ({len(karta_.oprövbara)}): "
              f"{', '.join(map(str, karta_.oprövbara))}")


if __name__ == "__main__":
    main()
