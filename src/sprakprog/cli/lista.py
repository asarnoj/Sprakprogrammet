"""ordbok lista — översikt av alla koncept i databasen.

Visar en rad per koncept med ordklass, lemma för valt språk, och källa.
Multi-lemma slås ihop med ' / '. Saknat lemma visas som '—'.

Filter:
  --språk    sv / en / fr / de / es / it / ja  (default: sv)
  --källa    bas_kärna / grundord / ...
  --ordklass Verb / Substantiv / ...
"""

from __future__ import annotations

import argparse
import sys

from ..db import STANDARD_DB, anslut
from ..modeller import ORDKLASSER, SPRÅK


def kör(args: argparse.Namespace) -> int:
    if not STANDARD_DB.exists():
        print(
            f"FEL: {STANDARD_DB.name} finns inte. Kör 'ordbok import' först.",
            file=sys.stderr,
        )
        return 1

    if args.språk not in SPRÅK:
        print(
            f"FEL: okänt språk {args.språk!r}. Giltiga: {', '.join(sorted(SPRÅK))}",
            file=sys.stderr,
        )
        return 1

    if args.ordklass and args.ordklass not in ORDKLASSER:
        print(
            f"FEL: okänd ordklass {args.ordklass!r}. "
            f"Giltiga: {', '.join(sorted(ORDKLASSER))}",
            file=sys.stderr,
        )
        return 1

    # ── Bygg query med valfria filter ────────────────────────────────────
    villkor: list[str] = []
    parametrar: list[object] = [args.språk]

    if args.källa:
        villkor.append("k.källa = ?")
        parametrar.append(args.källa)

    if args.ordklass:
        villkor.append("k.ordklass = ?")
        parametrar.append(args.ordklass)

    where_klausul = f"WHERE {' AND '.join(villkor)}" if villkor else ""

    sql = f"""
        SELECT
            k.nyckel       AS nyckel,
            k.ordklass     AS ordklass,
            k.källa        AS källa,
            GROUP_CONCAT(l.lemma, ' / ') AS lemman
        FROM Koncept k
        LEFT JOIN Lexem l
            ON l.koncept_id = k.id AND l.språk = ?
        {where_klausul}
        GROUP BY k.id
        ORDER BY k.nyckel
    """

    conn = anslut()
    try:
        rader = conn.execute(sql, parametrar).fetchall()
    finally:
        conn.close()

    if not rader:
        print("(inga koncept matchar filtren)")
        return 0

    # ── Beräkna kolumnbredder ───────────────────────────────────────────
    rubriker = ("KONCEPT", "ORDKLASS", "LEMMA", "KÄLLA")
    bredd_nyckel   = max(len(rubriker[0]), max(len(r["nyckel"])   for r in rader))
    bredd_ordklass = max(len(rubriker[1]), max(len(r["ordklass"]) for r in rader))
    bredd_lemma    = max(len(rubriker[2]), max(len(r["lemman"] or "—") for r in rader))
    bredd_källa    = max(len(rubriker[3]), max(len(r["källa"])   for r in rader))

    fmt = f"{{:<{bredd_nyckel}}}  {{:<{bredd_ordklass}}}  {{:<{bredd_lemma}}}  {{:<{bredd_källa}}}"
    total_bredd = bredd_nyckel + bredd_ordklass + bredd_lemma + bredd_källa + 6

    # ── Skriv ut ────────────────────────────────────────────────────────
    print(fmt.format(*rubriker))
    print("─" * total_bredd)
    for r in rader:
        print(fmt.format(
            r["nyckel"],
            r["ordklass"],
            r["lemman"] or "—",
            r["källa"],
        ))

    # Sammanfattning
    print()
    per_källa: dict[str, int] = {}
    for r in rader:
        per_källa[r["källa"]] = per_källa.get(r["källa"], 0) + 1
    delar = ", ".join(f"{antal} {källa}" for källa, antal in sorted(per_källa.items()))
    saknar_lemma = sum(1 for r in rader if r["lemman"] is None)
    saknad_text = f", {saknar_lemma} saknar {args.språk}-lemma" if saknar_lemma else ""
    print(f"{len(rader)} koncept ({delar}){saknad_text}")
    return 0
