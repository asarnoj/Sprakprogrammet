"""ordbok exportera-former / importera-former — Former-tabellen som TSV.

Bakgrund: böjningskörningen görs på en annan maskin (RUNBOOK §6) och
resultatet ska tillbaka. Att skicka `sprak.db` som binär fil fungerar men
är osynligt — den går inte att granska, inte att diffa i git, och den kan
vara byggd på ett äldre schema än mottagarens.

TSV:n nycklas därför på **(koncept, språk, lemma)** och inte på lexem_id.
Radnummer i Lexem-tabellen ändras varje gång databasen byggs om från CSV;
den naturliga nyckeln gör det inte. Importen slår upp lexem_id lokalt.

Formatet är avsiktligt tråkigt: tabbseparerat, en rad per Former-rad, tom
sträng för NULL, deterministiskt sorterat så att två körningar ger
identiska filer och git-diffen visar exakt vad som ändrats.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from ..db import STANDARD_DB, anslut

# Nyckelkolumner först, sedan formen, sedan axlarna i Former-ordning.
NYCKEL_KOLUMNER = ("koncept", "språk", "lemma")
AXEL_KOLUMNER = (
    "numerus", "species", "kasus", "genus", "tempus", "grad", "person", "diates",
)
KOLUMNER = (*NYCKEL_KOLUMNER, "form", *AXEL_KOLUMNER)


def kör_export(args: argparse.Namespace) -> int:
    if not STANDARD_DB.exists():
        print(f"FEL: {STANDARD_DB.name} finns inte.", file=sys.stderr)
        return 1

    mål = Path(args.fil)
    conn = anslut()
    try:
        rader = conn.execute(
            f"""SELECT k.nyckel AS koncept, l.språk, l.lemma, f.form,
                       {', '.join('f.' + a for a in AXEL_KOLUMNER)}
                FROM Former f
                JOIN Lexem l   ON l.id = f.lexem_id
                JOIN Koncept k ON k.id = l.koncept_id
                ORDER BY k.nyckel, l.språk, l.lemma, f.form,
                         {', '.join('f.' + a for a in AXEL_KOLUMNER)}"""
        ).fetchall()
    finally:
        conn.close()

    if not rader:
        print("VARNING: Former är tom — filen blir bara en rubrikrad.", file=sys.stderr)

    with mål.open("w", encoding="utf-8", newline="") as fh:
        skrivare = csv.writer(fh, delimiter="\t", lineterminator="\n")
        skrivare.writerow(KOLUMNER)
        for r in rader:
            skrivare.writerow(
                ["" if r[kol] is None else r[kol] for kol in KOLUMNER]
            )

    print(f"✓ Exporterade {len(rader)} Former-rader → {mål}")
    return 0


def kör_import(args: argparse.Namespace) -> int:
    källa = Path(args.fil)
    if not källa.is_file():
        print(f"FEL: filen saknas: {källa}", file=sys.stderr)
        return 1
    if not STANDARD_DB.exists():
        print(f"FEL: {STANDARD_DB.name} finns inte. Kör 'ordbok import' först.",
              file=sys.stderr)
        return 1

    conn = anslut()
    try:
        befintliga = conn.execute("SELECT COUNT(*) FROM Former").fetchone()[0]
        if befintliga and not args.ersätt:
            print(
                f"FEL: Former innehåller redan {befintliga} rader. "
                f"Använd --ersätt för att radera dem och importera på nytt.",
                file=sys.stderr,
            )
            return 1

        # Slå upp lexem_id på den naturliga nyckeln.
        lexem_id: dict[tuple[str, str, str], int] = {
            (r["nyckel"], r["språk"], r["lemma"]): r["id"]
            for r in conn.execute(
                """SELECT l.id, k.nyckel, l.språk, l.lemma
                   FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id"""
            )
        }

        rader: list[tuple] = []
        okända: list[str] = []
        with källa.open(encoding="utf-8", newline="") as fh:
            läsare = csv.DictReader(fh, delimiter="\t")
            if list(läsare.fieldnames or []) != list(KOLUMNER):
                print(
                    f"FEL: oväntade kolumner i {källa.name}.\n"
                    f"  förväntat: {'  '.join(KOLUMNER)}\n"
                    f"  hittade:   {'  '.join(läsare.fieldnames or [])}",
                    file=sys.stderr,
                )
                return 1
            for radnr, rad in enumerate(läsare, start=2):
                nyckel = (rad["koncept"], rad["språk"], rad["lemma"])
                if nyckel not in lexem_id:
                    okända.append(
                        f"{källa.name}:{radnr}  okänt lexem: "
                        f"{rad['koncept']}/{rad['språk']}/{rad['lemma']!r}"
                    )
                    continue
                rader.append((
                    lexem_id[nyckel],
                    rad["form"],
                    *(int(rad[a]) if rad[a] else None for a in AXEL_KOLUMNER),
                ))

        # Ett okänt lexem betyder att TSV:n och CSV-ordboken är osynkade —
        # importera inget alls hellre än en halv tabell.
        if okända:
            print(f"FEL: {len(okända)} rader matchar inget lexem i databasen. "
                  f"Är ordboken byggd från samma CSV-filer?", file=sys.stderr)
            for o in okända[:20]:
                print(f"  {o}", file=sys.stderr)
            if len(okända) > 20:
                print(f"  ... och {len(okända) - 20} till", file=sys.stderr)
            return 1

        with conn:
            conn.execute("DELETE FROM Former")
            conn.executemany(
                f"""INSERT INTO Former (lexem_id, form, {', '.join(AXEL_KOLUMNER)})
                    VALUES (?, ?, {', '.join('?' * len(AXEL_KOLUMNER))})""",
                rader,
            )
    finally:
        conn.close()

    print(f"✓ Importerade {len(rader)} Former-rader från {källa}")
    if befintliga:
        print(f"  (ersatte {befintliga} befintliga rader)")
    return 0
