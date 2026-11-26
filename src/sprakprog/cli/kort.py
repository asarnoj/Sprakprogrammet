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
        # VYN VISAR DET SOM GRINDAR, och ingenting annat. Fram till
        # 2026-08-26 visade den `rep/dag`, `meningar/dag` och "hela högen
        # ryms" — tal räknade med det gamla `per_kort`, som B2 mätte som fem
        # till trettio gånger för högt, och som efter F1 inte grindade
        # någonting. Webbvyn hade redan slutat skicka dem; den här vyn var
        # den sista läsaren och därmed det enda skälet att räkna dem alls.
        #
        # Kvar står de två tal som betyder något: går nivån att ÖVA, och hur
        # lång tid tar den i den takt du faktiskt håller.
        from ..kort import dagsplan, upplåsningsläge
        print("\nBeståndet — och vad nästa nivå skulle kosta (--kostnad NIVÅ)")
        print(f"   {'':4}{'kort':>7}{'osedda':>8}{'kort/mening':>13}")
        for s_ in sorted(språk):
            l = upplåsningsläge(kort_db, s_)
            if not l["totalt"]:
                continue
            # `kort/mening` är mätt ur historiken och saknas på en oövad
            # kurs. "—" och inte noll: noll vore ett påstående.
            k = f"{l['kort_per_mening']:.1f}" if l["kort_per_mening"] else "—"
            print(f"   {s_:4}{l['totalt']:7}{l['osedda']:8}{k:>13}")
        if args.kostnad:
            from ..kort.schemalaggning import kostnad
            with anslut() as språk_db:
                språk_db.row_factory = sqlite3.Row
                for s_ in sorted(språk):
                    k = kostnad(kort_db, språk_db, s_, args.kostnad, args.cefr)
                    if not k["före"]["totalt"]:
                        continue
                    rad = f"\n   {s_} → nivå {args.kostnad}: +{k['nya_kort']} kort"
                    if k["byggbarhet"] is None:
                        print(rad + " — byggbarheten går inte att mäta")
                        continue
                    # NIVÅNS STORLEK I DYGN, inte i kort. "Ryms N kort" har
                    # inget svar när villkoret sitter på en takt; "hur länge
                    # tar N kort" har det (F1).
                    p = dagsplan(kort_db, s_)
                    takt = p["inflödestak"]
                    tid = (f", {-(-k['nya_kort'] // takt)} dygn i din takt"
                           if takt else ", takten inte mätt än")
                    print(f"{rad}{tid}   byggbarhet {k['byggbarhet']:.3f}   "
                          + ("✓ går att öva" if k["redo"] else
                             "✗ för få kända ord — varje mening blir en "
                             "ordlektion"))
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
        # Befolkningen mäter exponeringen själv — beståndet ändrades, alltså
        # ändrades också hur ofta korten möts. `--meningar` finns kvar för att
        # kunna mäta noggrannare än förvalet.
        r = befolka(kort_db, språk_db, språk, nivå=args.nivå, cefr=args.cefr,
                    mät=not args.utan_mätning)
        print(f"✓ {r['nya']} nya kort, {r['totalt']} totalt, "
              f"{r['kopplingar']} cellkopplingar")
        if r["föräldralösa"]:
            print(f"  ⚠ {r['föräldralösa']} kort saknar täckning i språkdatabasen "
                  f"— behålls, historiken kastas inte")

        if args.meningar and not args.utan_mätning:
            for s in sorted(språk):
                n = mät_exponering(kort_db, språk_db, s, args.meningar)
                # Skriv flaggan för det språk som just mätts, inte för alla
                # — se `sätt_schemalagt`.
                sätt_schemalagt(kort_db, språk=s)
                print(f"  {s}: exponering ommätt på {n} meningar")
        if not args.utan_mätning:
            print(f"✓ {r['ej_schemalagda']} kort möts för ofta för att "
                  f"schemaläggas — de mäts i stället")
            if r["omätta"]:
                print(f"  {r['omätta']} kort har ingen mätning "
                      f"(andra språk) — de förblir schemalagda")

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
    p.add_argument("--utan-mätning", action="store_true", dest="utan_mätning",
                   help="hoppa över exponeringsmätningen (snabbare, men "
                        "allestädes närvarande kort hamnar i kön)")
    p.add_argument("--meningar", type=int,
                   help="mät om exponeringen på så här många meningar per "
                        "språk (förvalet räcker i normalfallet)")
    p.add_argument("--nivå", type=int,
                   help="skapa bara kort som går att möta på den här nivån "
                        "på komplexitetsstegen (utelämnad: alla)")
    p.add_argument("--cefr", default="C2",
                   choices=("A1", "A2", "B1", "B2", "C1", "C2"),
                   help="tak på ordförrådets CEFR-nivå")
    p.add_argument("--kö", choices=SPRÅK, help="visa dagens kö för ett språk")
    p.add_argument("--antal", type=int, default=20, help="kölängd")
    # `--meningar-per-dag` TOGS BORT 2026-08-26. Den matade bara den gamla
    # kapacitetsmatten i `upplåsningsläge`, som inte grindar något efter F1
    # och räknade fem till trettio gånger fel. Användarens ratt är minuter
    # och sätts på kursen (`ordbok kurs`, eller kursvyn).
    p.add_argument("--kostnad", type=int, metavar="NIVÅ",
                   help="vad en nivå skulle kosta, utan att låsa upp den")
    p.add_argument("--läge", action="store_true",
                   help="hur nära nästa nivå kursen står")
    p.add_argument("--db", help="annan sökväg än kort.db")
    p.set_defaults(func=kör)
