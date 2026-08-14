"""`ordbok kort` — bygg och inspektera inlärardatabasen."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..db import anslut
from ..kort import anslut_kort, befolka, sammanfattning, skapa_kortdatabas
from ..kort.befolka import mät_exponering, sätt_schemalagt
from ..kort.db import STANDARD_KORT_DB

SPRÅK = ("sv", "en", "de", "fr", "es", "it", "ja")


def kör(args: argparse.Namespace) -> int:
    mål = Path(args.db) if args.db else STANDARD_KORT_DB
    språk = set(args.språk) if args.språk else set(SPRÅK)

    if args.återinitiera:
        if mål.exists() and not args.ja:
            svar = input(f"{mål} finns. All repetitionshistorik raderas. "
                         f"Skriv 'radera' för att fortsätta: ")
            if svar.strip() != "radera":
                print("Avbrutet.")
                return 1
        kort_db = skapa_kortdatabas(mål)
        print(f"✓ tom inlärardatabas → {mål}")
    else:
        if not mål.exists():
            print(f"{mål} finns inte — kör med --återinitiera först.")
            return 1
        kort_db = anslut_kort(mål)

    with anslut() as språk_db:
        r = befolka(kort_db, språk_db, språk)
        print(f"✓ {r['nya']} nya kort, {r['totalt']} totalt, "
              f"{r['kopplingar']} cellkopplingar")
        if r["föräldralösa"]:
            print(f"  ⚠ {r['föräldralösa']} kort saknar täckning i språkdatabasen "
                  f"— behålls, historiken kastas inte")

        if args.mät:
            for s in sorted(språk):
                n = mät_exponering(kort_db, språk_db, s, args.meningar)
                print(f"  {s}: exponering mätt på {n} meningar")
            print(f"✓ {sätt_schemalagt(kort_db)} kort möts för ofta för att "
                  f"schemaläggas — de mäts i stället")

    print()
    print(f"{'':4}{'typ':12}{'antal':>7}{'schemalagda':>13}{'räckvidd':>10}")
    for rad in sammanfattning(kort_db):
        print(f"{rad['språk']:4}{rad['typ']:12}{rad['antal']:7}"
              f"{rad['schemalagda']:13}{rad['snitträckvidd']:10}")
    return 0


def lägg_till_parser(sub) -> None:
    p = sub.add_parser("kort", help="Bygg och inspektera inlärardatabasen")
    p.add_argument("--återinitiera", action="store_true",
                   help="skapa en TOM databas — raderar all repetitionshistorik")
    p.add_argument("--ja", action="store_true", help="hoppa över bekräftelsen")
    p.add_argument("--språk", nargs="+", choices=SPRÅK,
                   help="bara dessa språk (förval: alla sju)")
    p.add_argument("--mät", action="store_true",
                   help="mät exponering och sätt schemalagt/mätt")
    p.add_argument("--meningar", type=int, default=2000,
                   help="antal meningar per språk vid mätning")
    p.add_argument("--db", help="annan sökväg än kort.db")
    p.set_defaults(func=kör)
