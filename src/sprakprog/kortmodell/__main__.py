"""Räkna ut formtabellen för ett språk och visa korten.

    python -m sprakprog.kortmodell sv
"""

from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from pathlib import Path

from ..rendering.uppslag import Uppslag
from . import Formtabell

ROT = Path(__file__).resolve().parents[3]

EXEMPEL = {
    "sv": ("köpa", "gå", "känna", "skriva", "hus", "fågel", "flicka", "glad", "gammal", "jag"),
    "en": ("buy", "stop", "carry", "write", "be", "city", "child", "big", "happy", "I"),
}


def main() -> None:
    språk = sys.argv[1] if len(sys.argv) > 1 else "sv"
    conn = sqlite3.connect(ROT / "sprak.db")
    u = Uppslag(conn, språk)
    tabell = Formtabell(u)
    rader = conn.execute(
        """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id
           WHERE l.språk = ? ORDER BY k.ordklass, l.lemma""", (språk,)).fetchall()

    unika = set()
    former = 0
    formkort = Counter()
    for lexem in rader:
        for kort in tabell.former(lexem).values():
            former += 1
            unika.update(kort)
            formkort[len(kort) - 1] += 1

    print(f"{språk}: {len(rader)} lexem, {former} former, {len(unika)} olika kort\n")
    for familj in ("ord", "mönster"):
        typer = Counter(k.typ for k in unika if k.familj == familj)
        print(f"  {familj:8} {sum(typer.values()):>5}  {dict(typer)}")
    print(f"\n  formkort per form: {dict(sorted(formkort.items()))}")
    print(f"  datafel: {len(tabell.datafel)}   celler utan regel: {len(tabell.utan_regel)}")
    namn = {r["id"]: r["lemma"] for r in rader}
    for lexem_id, cell in sorted(tabell.utan_regel)[:15]:
        print(f"    utan regel: {namn[lexem_id]} {cell}")

    ändelser = sorted(k for k in unika if k.typ == "ändelse")
    print(f"\n  ändelsekort ({len(ändelser)}):")
    for k in ändelser:
        print(f"    {'/'.join(k.nyckel)}")
    ljud = sorted(k for k in unika if k.typ == "regel")
    print(f"\n  ljudregler ({len(ljud)}): {', '.join(k.nyckel[1] for k in ljud)}")

    print("\n  exempel:")
    for lemma in EXEMPEL.get(språk, ()):
        for lexem in (r for r in rader if r["lemma"] == lemma):
            print(f"    {lemma} ({lexem['ordklass']})")
            celler = u._celler(lexem)
            for cell, kort in tabell.former(lexem).items():
                print(f"      {cell:24} {celler[cell]:14} "
                      f"{' + '.join(str(k) for k in kort[1:]) or '—'}")


if __name__ == "__main__":
    main()
