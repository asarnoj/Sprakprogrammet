"""`ordbok öva` — en övningsrunda i terminalen.

Hela slingan i ett kommando: generera, visa, läs svar, rätta, registrera.
Tunt med flit — det är gränssnittet mot det som redan finns, inte ny logik.
"""

from __future__ import annotations

import argparse
import sqlite3

from ..db import anslut
from ..generator import Generator
from ..kort import anslut_kort
from ..kort.db import STANDARD_KORT_DB

SPRÅK = ("sv", "en", "de", "fr", "es", "it", "ja")


def kör(args: argparse.Namespace) -> int:
    if not STANDARD_KORT_DB.exists():
        print("kort.db finns inte — kör `ordbok kort --återinitiera` först.")
        return 1
    kort_db = anslut_kort()
    with anslut() as språk_db:
        språk_db.row_factory = sqlite3.Row
        g = Generator(språk_db, kort_db, args.språk, nivå=args.nivå,
                      cefr=args.cefr, budget=args.budget)
        rätt = fel = 0
        for i in range(args.antal):
            f = g.föreslå(kandidater=args.kandidater)
            if f is None:
                print("Ingen mening gick att bygga.")
                return 1
            print(f"\n{i + 1}/{args.antal}  ({f.poäng.täckta} köade kort, "
                  f"Σ(1−R)={f.poäng.förväntat:.2f})")
            if args.facit:
                print(f"   {f.text}")
            svar = input("   > ")
            r = g.svara(f, svar)
            if r.korrekt:
                rätt += 1
                print("   ✓")
            else:
                fel += 1
                print(f"   ✗ {f.text}")
                for a in r.anmärkningar:
                    print(f"     {a}")
        print(f"\n{rätt} rätt, {fel} fel av {args.antal}")
    return 0


def lägg_till_parser(sub) -> None:
    p = sub.add_parser("öva", help="En övningsrunda: generera, svara, rätta")
    p.add_argument("språk", choices=SPRÅK)
    p.add_argument("--antal", type=int, default=10, help="antal meningar")
    p.add_argument("--nivå", type=int, default=21, help="tak på komplexitetsstegen")
    p.add_argument("--cefr", default="C2", choices=("A1", "A2", "B1", "B2", "C1", "C2"),
                   help="tak på ordförrådets CEFR-nivå")
    p.add_argument("--budget", type=float, default=1.5,
                   help="Σ(1−R) att sikta på per mening")
    p.add_argument("--kandidater", type=int, default=800)
    p.add_argument("--facit", action="store_true",
                   help="visa meningen innan svaret — för att prova systemet")
    p.set_defaults(func=kör)
