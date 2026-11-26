"""`ordbok kurs` — skapa och ställa in en kurs, och `ordbok webb` — kör den.

En kurs är ett par av käll- och målspråk med sina två nivåtak och sina två
inställningar. Den är också det enda stället användarens egna VAL bor:
`budget` och `meningar_per_dag`. Allt annat i systemet är härlett eller mätt.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from ..db import anslut
from ..kort import anslut_kort, befolka
from ..kort.db import STANDARD_KORT_DB

SPRÅK = ("sv", "en", "de", "fr", "es", "it", "ja")
CEFR = ("A1", "A2", "B1", "B2", "C1", "C2")


def kör(args: argparse.Namespace) -> int:
    if not STANDARD_KORT_DB.exists():
        print("kort.db finns inte — kör `ordbok kort --återinitiera` först.")
        return 1
    kort_db = anslut_kort()

    if args.ny:
        källa, mål = args.ny
        if källa == mål:
            print("Käll- och målspråk måste skilja sig.")
            return 1
        kort_db.execute(
            """INSERT INTO Kurs (källspråk, målspråk, nivå, cefr, budget,
                                 meningar_per_dag, startad)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT (källspråk, målspråk) DO UPDATE SET
                   nivå = excluded.nivå, cefr = excluded.cefr""",
            (källa, mål, args.nivå, args.cefr, args.budget,
             args.meningar_per_dag, datetime.now(UTC).isoformat()))
        kort_db.commit()
        # Att skapa kursen ÄR att befolka den. Nivån avgör vilka kort som
        # finns (se schemalaggning.upplåsningsläge), så en kurs utan
        # befolkning är en kurs utan material.
        with anslut() as språk_db:
            r = befolka(kort_db, språk_db, {mål}, nivå=args.nivå, cefr=args.cefr)
        print(f"✓ kurs {källa} → {mål}, nivå {args.nivå}, {args.cefr}")
        print(f"  {r['totalt']} kort ({r['nya']} nya)")

    rader = kort_db.execute("SELECT * FROM Kurs ORDER BY målspråk").fetchall()
    if not rader:
        print("Ingen kurs finns. Skapa en med `ordbok kurs --ny sv de`.")
        return 0
    print(f"\n{'kurs':>10}{'nivå':>6}{'cefr':>6}{'budget':>8}{'meningar/dag':>14}")
    for k in rader:
        print(f"{k['källspråk'] + ' → ' + k['målspråk']:>10}{k['nivå']:6}"
              f"{k['cefr']:>6}{k['budget']:8.1f}{k['meningar_per_dag']:14}")
    return 0


def kör_webb(args: argparse.Namespace) -> int:
    from ..webb import starta
    if not args.db and not STANDARD_KORT_DB.exists():
        print("kort.db finns inte — kör `ordbok kort --återinitiera` först.")
        return 1
    from pathlib import Path
    starta(args.port, kandidater=args.kandidater,
           kort_sökväg=Path(args.db) if args.db else None)
    return 0


def lägg_till_parser(sub) -> None:
    p = sub.add_parser("kurs", help="Skapa och visa kurser")
    p.add_argument("--ny", nargs=2, metavar=("KÄLLSPRÅK", "MÅLSPRÅK"),
                   choices=SPRÅK, help="skapa eller uppdatera en kurs")
    p.add_argument("--nivå", type=int, default=4,
                   help="tak på komplexitetsstegen (1–21)")
    p.add_argument("--cefr", default="A1", choices=CEFR,
                   help="tak på ordförrådets CEFR-nivå")
    p.add_argument("--budget", type=float, default=1.5,
                   help="Σ(1−R) att sikta på per mening")
    p.add_argument("--meningar-per-dag", type=int, dest="meningar_per_dag",
                   default=20, help="hur mycket du vill öva — styr upplåsningen")
    p.set_defaults(func=kör)

    w = sub.add_parser("webb", help="Kör övningsgränssnittet lokalt")
    w.add_argument("--port", type=int, default=8765)
    w.add_argument("--kandidater", type=int, default=800,
                   help="antal kandidatmeningar per uppgift")
    w.add_argument("--db", help="annan inlärardatabas än kort.db — för att "
                                "prova utan att röra den riktiga")
    w.set_defaults(func=kör_webb)
