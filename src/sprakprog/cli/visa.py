"""ordbok visa <koncept> — drill-down för ett enskilt koncept.

Visar alla lemman per språk, och (när Fas B är klar) alla böjningar.
"""

from __future__ import annotations

import argparse
import sys

from ..db import STANDARD_DB, anslut


SPRÅKORDNING = ["sv", "en", "fr", "de", "es", "it", "ja"]


def kör(args: argparse.Namespace) -> int:
    if not STANDARD_DB.exists():
        print(
            f"FEL: {STANDARD_DB.name} finns inte. Kör 'ordbok import' först.",
            file=sys.stderr,
        )
        return 1

    conn = anslut()
    try:
        # ── Hämta koncept ─────────────────────────────────────────────
        koncept = conn.execute(
            "SELECT id, nyckel, ordklass, källa FROM Koncept WHERE nyckel = ?",
            (args.koncept,),
        ).fetchone()

        if koncept is None:
            # Fuzzy-förslag: koncept med liknande prefix
            prefix = args.koncept.split("_")[0] if "_" in args.koncept else args.koncept[:4]
            förslag = conn.execute(
                "SELECT nyckel FROM Koncept WHERE nyckel LIKE ? LIMIT 5",
                (f"{prefix}%",),
            ).fetchall()
            print(f"FEL: konceptet '{args.koncept}' finns inte.", file=sys.stderr)
            if förslag:
                print("Menade du kanske:", file=sys.stderr)
                for f in förslag:
                    print(f"  {f['nyckel']}", file=sys.stderr)
            return 1

        # ── Hämta lexem ────────────────────────────────────────────────
        lexem_rader = conn.execute(
            "SELECT språk, lemma FROM Lexem WHERE koncept_id = ? ORDER BY lemma",
            (koncept["id"],),
        ).fetchall()

        # Gruppera multi-lemma per språk
        lexem: dict[str, list[str]] = {s: [] for s in SPRÅKORDNING}
        for rad in lexem_rader:
            if rad["språk"] in lexem:
                lexem[rad["språk"]].append(rad["lemma"])

        # ── Hämta former (Fas B) ───────────────────────────────────────
        har_former = conn.execute(
            """SELECT COUNT(*) AS n FROM Former f
               JOIN Lexem l ON l.id = f.lexem_id
               WHERE l.koncept_id = ?""",
            (koncept["id"],),
        ).fetchone()["n"] > 0

    finally:
        conn.close()

    # ── Skriv ut ───────────────────────────────────────────────────────
    print(f"Koncept:  {koncept['nyckel']}")
    print(f"Ordklass: {koncept['ordklass']}")
    print(f"Källa:    {koncept['källa']}")
    print()

    print("Lemman:")
    for språk in SPRÅKORDNING:
        lemman = lexem[språk]
        if lemman:
            print(f"  {språk}  {' / '.join(lemman)}")
        else:
            print(f"  {språk}  —")

    print()
    if har_former:
        # Fas B: skriv ut böjningar
        print("Former: (visas i Fas B)")
    else:
        print("Former: (inga böjningar lagrade än)")

    return 0
