"""`ordbok kort` — bygg och inspektera inlärardatabasen."""

from __future__ import annotations

import argparse
import sqlite3
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

    # Läsvyerna befolkar INTE. Att göra det skulle rasera nivåspärren:
    # utan --nivå skapar befolka() hela beståndet, och `--läge` är en fråga
    # och inte en ändring.
    if args.läge:
        from ..kort import upplåsningsläge
        print("\nUpplåsning — ryms nästa nivå i dagen?")
        print(f"   {'':4}{'kort':>7}{'rep/dag':>10}{'kort/mening':>13}"
              f"{'meningar/dag':>14}{'du valt':>9}")
        for s_ in sorted(språk):
            l = upplåsningsläge(kort_db, s_, args.meningar_per_dag)
            if not l["totalt"]:
                continue
            k = f"{l['kort_per_mening']:.1f}" if l["kort_per_mening"] else "—"
            krävs = f"{l['krävs']:.1f}" if l["krävs"] is not None else "oövad"
            rep = f"{l['rep_per_dag']:.1f}" if l["rep_per_dag"] is not None else "—"
            märke = "  ✓ plats finns" if l["klar"] else ""
            print(f"   {s_:4}{l['totalt']:7}{rep:>10}{k:>13}"
                  f"{krävs:>14}{l['kapacitet']:9}{märke}")
        if args.kostnad:
            from ..kort.schemalaggning import kostnad
            with anslut() as språk_db:
                språk_db.row_factory = sqlite3.Row
                for s_ in sorted(språk):
                    k = kostnad(kort_db, språk_db, s_, args.kostnad, args.cefr,
                                args.meningar_per_dag)
                    if not k["före"]["totalt"]:
                        continue
                    e = k["efter"]
                    rad = f"\n   {s_} → nivå {args.kostnad}: +{k['nya_kort']} kort"
                    if e["krävs"] is None:
                        print(rad + " — kursen oövad, kostnaden går inte att mäta")
                        continue
                    print(f"{rad}, {e['rep_per_dag']:.0f} rep/dag "
                          f"= {e['krävs']:.1f} meningar/dag   "
                          + ("✓ ryms" if k["ryms"] else
                             f"✗ över de {e['kapacitet']} du valt"))
        return 0

    if args.kö:
        from ..kort import Schemaläggare, kö
        s = Schemaläggare(kort_db)
        rader = kö(kort_db, args.kö, args.antal)
        print(f"\nKö för {args.kö}: {len(rader)} kort")
        print(f"{'typ':10}{'facit':16}{'R':>6}{'förfaller':>22}{'antal':>7}")
        for r in rader:
            print(f"{r['typ']:10}{(r['facit'] or '')[:15]:16}"
                  f"{s.retention(r):6.2f}{(r['förfaller'] or '—')[:19]:>22}{r['antal']:7}")
        return 0


    with anslut() as språk_db:
        r = befolka(kort_db, språk_db, språk, nivå=args.nivå, cefr=args.cefr)
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
    p.add_argument("--nivå", type=int,
                   help="skapa bara kort som går att möta på den här nivån "
                        "på komplexitetsstegen (utelämnad: alla)")
    p.add_argument("--cefr", default="C2",
                   choices=("A1", "A2", "B1", "B2", "C1", "C2"),
                   help="tak på ordförrådets CEFR-nivå")
    p.add_argument("--kö", choices=SPRÅK, help="visa dagens kö för ett språk")
    p.add_argument("--antal", type=int, default=20, help="kölängd")
    p.add_argument("--meningar-per-dag", type=int, dest="meningar_per_dag",
                   help="hur mycket du vill öva — annars kursens inställning")
    p.add_argument("--kostnad", type=int, metavar="NIVÅ",
                   help="vad en nivå skulle kosta, utan att låsa upp den")
    p.add_argument("--läge", action="store_true",
                   help="hur nära nästa nivå kursen står")
    p.add_argument("--db", help="annan sökväg än kort.db")
    p.set_defaults(func=kör)
