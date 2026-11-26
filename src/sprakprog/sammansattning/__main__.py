"""Bygg meningar ur en sparad karta.

    python -m sprakprog.sammansattning KARTA [--mål TYP:NYCKEL] [--ord N] [--antal K]

KARTA är en fil från `python -m sprakprog.rendering.karta SPRÅK FIL`. Målet
skrivs som kortets typ och nyckel, med / mellan delarna:

    regel:val/tempusform/preteritum    regel:ordning/v2_fråga
    ändelse:Verb/ar/pret               ord:fys_köpa
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path

from ..kortmodell import Kort
from ..rendering.karta import ladda
from . import Sammansättare

ROT = Path(__file__).resolve().parents[3]


def _kort(språk: str, text: str) -> Kort:
    typ, _, nyckel = text.partition(":")
    delar = tuple(nyckel.split("/"))
    if typ == "ord" and len(delar) == 1:
        delar = (delar[0], "")
    if typ == "oregelbunden" and len(delar) == 2:
        delar = (delar[0], "", delar[1])
    return Kort(språk, typ, delar)


def main() -> None:
    p = argparse.ArgumentParser(description="Bygg meningar ur en sparad karta.")
    p.add_argument("karta")
    p.add_argument("--mål")
    p.add_argument("--par", help="kursens andra språk; meningen måste gå att uttrycka där")
    p.add_argument("--ord", type=int, required=True, help="högsta antal ord")
    p.add_argument("--antal", type=int, required=True, help="antal meningar att visa")
    p.add_argument("--per-mall", type=int, default=1)
    p.add_argument("--kort", action="store_true", help="visa korten")
    a = p.parse_args()

    karta = ladda(a.karta)
    conn = sqlite3.connect(ROT / "sprak.db")
    t = time.perf_counter()
    s = Sammansättare(conn, karta, par=a.par)
    print(f"{karta['språk']}: kartan laddad på {time.perf_counter() - t:.1f} s")
    mål = _kort(karta["språk"], a.mål) if a.mål else None
    t = time.perf_counter()
    for i, träff in enumerate(s.meningar(mål, högst_ord=a.ord, per_mall=a.per_mall)):
        print(f"  {träff.ord} ord  {träff.text:40}  {len(träff.kort)} kort  "
              f"({time.perf_counter() - t:.1f} s)")
        if a.kort:
            print("      " + ", ".join(sorted(str(k) for k in träff.kort)))
        if i + 1 >= a.antal:
            break


if __name__ == "__main__":
    main()
