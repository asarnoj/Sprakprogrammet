"""Räkna ut kraven och nivåerna ur en sparad karta.

    python -m sprakprog.nivaer KARTA [KORT …]

Utan KORT räknas alla nivåkort i språket. Ett kort skrivs som i
`python -m sprakprog.sammansattning`: regel:val/tempusform/preteritum.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from ..rendering.karta import ladda
from ..sammansattning import Sammansättare
from . import Krav, Nivåkort, rita_nivåer

ROT = Path(__file__).resolve().parents[3]


def main() -> None:
    p = argparse.ArgumentParser(description="Räkna ut kraven och nivåerna.")
    p.add_argument("karta")
    p.add_argument("kort", nargs="*")
    p.add_argument("--spara", metavar="FIL",
                   help="skriv kraven och nivåerna som JSON, för dagspasset")
    p.add_argument("--krymp", action="store_true",
                   help="krymp varje krav till en bevisat minsta mängd (dyrt, 4.2)")
    p.add_argument("--kontroll", action="store_true",
                   help="hoppa inte över något: pröva varje bevis mot renderingen")
    a = p.parse_args()

    karta = ladda(a.karta)
    språk = karta["språk"]
    s = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta)
    s.kontroll = a.kontroll
    nivå = Nivåkort(s.tabell)
    alla = sorted(nivå.alla(karta), key=str)
    if a.kort:
        # Namnet slås upp bland språkets nivåkort: texten utelämnar tomma
        # varianter och går inte att läsa tillbaka till en nyckel.
        namn = {str(k): k for k in alla}
        okända = [text for text in a.kort if text not in namn]
        if okända:
            p.error(f"inga sådana nivåkort i {språk}: {', '.join(okända)}")
        kort = [namn[text] for text in a.kort]
    else:
        kort = alla
    print(f"{språk}: {len(kort)} nivåkort", flush=True)

    krav = Krav(s, nivå)
    t = time.perf_counter()
    karta_ = rita_nivåer(krav, kort, rapport=lambda r: print(r, flush=True), krymp=a.krymp)
    print(f"\n{krav.frågor} frågor, {time.perf_counter() - t:.0f} s")
    print(f"förklaringar: {dict(sorted(s.statistik.items()))}")

    if a.spara:
        def rad(k) -> list:
            return [k.språk, k.typ, list(k.nyckel)]
        Path(a.spara).write_text(json.dumps({
            "språk": språk,
            "krav": [[rad(k), [rad(d) for d in sorted(m, key=str)]]
                     for k, m in sorted(karta_.krav.items(), key=lambda x: str(x[0]))],
            "nivåer": [[rad(k) for k in sorted(n, key=str)] for n in karta_.nivåer],
            "oprövbara": [rad(k) for k in karta_.oprövbara],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"sparat: {a.spara}")

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
