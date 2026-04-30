"""ordbok lägg-till — interaktivt lägga till ett nytt koncept.

Kontrollnivåer innan sparande:
  1. Exakt nyckel-match     → stopp, konceptet finns redan
  2. Lemma-match            → varning, trolig dubblett
  3. Prefix-match           → info, visar befintliga i samma kategori
"""

from __future__ import annotations

import sys

import argparse

from ..db import STANDARD_DB, anslut
from ..modeller import ORDKLASSER, SPRÅK

SPRÅKORDNING = ["sv", "en", "fr", "de", "es", "it", "ja"]


def fråga(ledtext: str, default: str = "") -> str:
    """Läser en rad från stdin med ledtext. Returnerar default om tomt."""
    try:
        svar = input(ledtext).strip()
        return svar if svar else default
    except (EOFError, KeyboardInterrupt):
        print("\nAvbruten.")
        sys.exit(0)


def välj_från_lista(ledtext: str, alternativ: list[str]) -> str:
    """Visar numrerade alternativ och returnerar valt värde."""
    for i, alt in enumerate(alternativ, 1):
        print(f"  {i}. {alt}")
    while True:
        svar = fråga(ledtext)
        if svar.isdigit() and 1 <= int(svar) <= len(alternativ):
            return alternativ[int(svar) - 1]
        # Direktinmatning om det matchar
        if svar in alternativ:
            return svar
        print(f"  Ange 1–{len(alternativ)} eller skriv värdet direkt.")


def kör(args: argparse.Namespace) -> int:
    if not STANDARD_DB.exists():
        print(
            f"FEL: {STANDARD_DB.name} finns inte. Kör 'ordbok import' först.",
            file=sys.stderr,
        )
        return 1

    conn = anslut()
    print("Lägg till nytt koncept (ctrl-c för att avbryta)\n")

    # ── 1. Koncept-nyckel ─────────────────────────────────────────────
    while True:
        nyckel = fråga("Koncept-nyckel: ")
        if not nyckel:
            print("  Nyckel kan inte vara tom.")
            continue

        befintlig = conn.execute(
            "SELECT id FROM Koncept WHERE nyckel = ?", (nyckel,)
        ).fetchone()
        if befintlig:
            print(f"  FEL: konceptet '{nyckel}' finns redan. Kör 'ordbok visa {nyckel}' för att se det.")
            conn.close()
            return 1
        break

    # ── 2. Ordklass ───────────────────────────────────────────────────
    print("\nOrdklass:")
    ordklass = välj_från_lista("Välj (nummer eller namn): ", sorted(ORDKLASSER))

    # ── 3. Prefix-check ───────────────────────────────────────────────
    if "_" in nyckel:
        prefix = nyckel.split("_")[0]
        liknande = conn.execute(
            "SELECT nyckel FROM Koncept WHERE nyckel LIKE ? ORDER BY nyckel LIMIT 8",
            (f"{prefix}_%",),
        ).fetchall()
        if liknande:
            print(f"\nBefintliga koncept med prefix '{prefix}_':")
            for r in liknande:
                print(f"  {r['nyckel']}")
            svar = fråga("\nFortsätt ändå? [j/n]: ").lower()
            if svar != "j":
                print("Avbruten.")
                conn.close()
                return 0

    # ── 4. Lemman per språk ───────────────────────────────────────────
    print("\nLemman (enter = hoppa över, ' / ' separerar flera lemman per språk):")
    # lemman: dict[språk → lista av lemman]
    lemman: dict[str, list[str]] = {}
    for språk in SPRÅKORDNING:
        råinput = fråga(f"  {språk}: ")
        if råinput:
            delar = [d.strip() for d in råinput.split("/") if d.strip()]
            if delar:
                lemman[språk] = delar

    if not lemman:
        print("  Minst ett lemma krävs.")
        conn.close()
        return 1

    # ── 5. Lemma-dubblettcheck ────────────────────────────────────────
    varningar: list[str] = []
    for språk, lemmalista in lemman.items():
        for lemma in lemmalista:
            träffar = conn.execute(
                """SELECT k.nyckel FROM Lexem l
                   JOIN Koncept k ON k.id = l.koncept_id
                   WHERE l.språk = ? AND l.lemma = ? AND k.ordklass = ?""",
                (språk, lemma, ordklass),
            ).fetchall()
            for t in träffar:
                varningar.append(
                    f"  '{lemma}' ({språk}) finns redan under '{t['nyckel']}'"
                )

    if varningar:
        print("\nVarning — liknande lemman finns redan:")
        for v in varningar:
            print(v)
        svar = fråga("\nFortsätt ändå? [j/n]: ").lower()
        if svar != "j":
            print("Avbruten.")
            conn.close()
            return 0

    # ── 6. Förhandsvisning ────────────────────────────────────────────
    lemma_preview = "  |  ".join(
        f"{s}: {' / '.join(lemman[s])}"
        for s in SPRÅKORDNING if s in lemman
    )
    print(f"\nFörhandsvisning:")
    print(f"  {nyckel}  [{ordklass}]  källa: manuell")
    print(f"  {lemma_preview}")
    svar = fråga("\nSpara? [j/n]: ").lower()
    if svar != "j":
        print("Avbruten.")
        conn.close()
        return 0

    # ── 7. Spara ──────────────────────────────────────────────────────
    antal_lexem = sum(len(v) for v in lemman.values())
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO Koncept (nyckel, ordklass, källa) VALUES (?, ?, 'manuell')",
                (nyckel, ordklass),
            )
            koncept_id = cur.lastrowid
            for språk, lemmalista in lemman.items():
                for lemma in lemmalista:
                    conn.execute(
                        "INSERT INTO Lexem (koncept_id, språk, lemma) VALUES (?, ?, ?)",
                        (koncept_id, språk, lemma),
                    )
    finally:
        conn.close()

    print(f"✓ '{nyckel}' sparat ({antal_lexem} lexem på {len(lemman)} språk).")
    return 0
