#!/usr/bin/env python3
"""
Granska lemman i bas_kärna.csv för en given ordklass med hjälp av Claude.

Bygger en markdown-tabell för ordklassen, kombinerar med KONVENTIONER.md,
och anropar claude -p för lingvistisk granskning.

Användning:
    python3 ordbok/granska_ordklass.py --lista
    python3 ordbok/granska_ordklass.py --ordklass Preposition
    python3 ordbok/granska_ordklass.py --ordklass Preposition --modell claude-opus-4-5
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
CSV_FIL = BASE / "nivålistor" / "bas_kärna.csv"
KONVENTIONER = BASE / "nivålistor" / "KONVENTIONER.md"
MODEL = "claude-sonnet-4-5"

GRANSKNING_INSTRUKTION = """\
Du är lingvistisk granskare av en flerspråkig ordbok för ett datoriserat språkinlärningssystem.

Läs KONVENTIONER.md noggrant — det beskriver exakt hur lemman används i systemet och vilka
förenklingar som är medvetna designbeslut (flagga INTE dessa).

Granska tabellen nedan med tre perspektiv:
1. MENINGSBYGGNAD: Kan lemmat användas för att generera korrekta meningar i alla vanliga kontexter?
2. HÅLLBAR FÖRENKLING: Om lemmat är en förenkling, är den konsistent och icke-vilseledande?
3. BÖJNING: Skapar lemmaformen problem vid morfologisk böjning (fel kasus, fel grundform, tvetydig paradigm)?

Flagga INTE saker som hanteras av renderaren (se avsnitt 4 i KONVENTIONER.md).
Flagga INTE de kända undantagen (se avsnitt 8 i KONVENTIONER.md).

För varje problem du hittar, skriv exakt detta format:
---
[KONCEPT] [SPRÅK]: TYP (FEL / VARNING / NOTERING)
Observation: [vad du ser i tabellen]
Problem: [varför det är ett problem i systemets kontext]
Alternativ: [ett eller flera förslag på lemman, med motivering]
---

Hoppa över rader utan problem — lista bara problem.
Avsluta med en sammanfattningsrad: "Granskade X concepts, flaggade Y."
"""


def läs_csv() -> list[dict]:
    rader = []
    with CSV_FIL.open(encoding="utf-8") as f:
        for rad in f:
            rad = rad.strip()
            if not rad or rad.startswith("#"):
                continue
            delar = rad.split(",", 4)
            if len(delar) < 5 or delar[0] == "koncept":
                continue
            koncept, ordklass, nivå, språk, lemma = delar
            rader.append({
                "koncept": koncept.strip(),
                "ordklass": ordklass.strip(),
                "nivå": nivå.strip(),
                "språk": språk.strip(),
                "lemma": lemma.strip(),
            })
    return rader


def hämta_ordklasser(rader: list[dict]) -> list[str]:
    ordklasser = sorted(set(r["ordklass"] for r in rader))
    return ordklasser


def bygg_tabell(rader: list[dict], ordklass: str) -> str:
    """Pivoterar data till en markdown-tabell med språk som kolumner."""
    filtrerade = [r for r in rader if r["ordklass"] == ordklass]
    if not filtrerade:
        return ""

    # Samla alla språk och lemman per concept+språk
    concepts_data: dict[str, dict] = defaultdict(lambda: defaultdict(list))
    nivå_per_concept: dict[str, str] = {}

    for r in filtrerade:
        concepts_data[r["koncept"]][r["språk"]].append(r["lemma"])
        nivå_per_concept[r["koncept"]] = r["nivå"]

    # Fasta kolumnordning
    SPRÅKORDNING = ["sv", "en", "fr", "de", "es", "it", "ja"]
    concepts = list(concepts_data.keys())

    # Beräkna kolumnbredder
    headers = ["koncept (nivå)"] + SPRÅKORDNING
    rows = []
    for koncept in concepts:
        nivå = nivå_per_concept[koncept]
        rad = [f"{koncept} ({nivå})"]
        for språk in SPRÅKORDNING:
            lemman = concepts_data[koncept].get(språk, [])
            if lemman:
                rad.append(" / ".join(lemman))
            else:
                rad.append("—")
        rows.append(rad)

    # Bygg markdown-tabell
    col_widths = [max(len(headers[i]), max(len(row[i]) for row in rows)) for i in range(len(headers))]

    def fmt_row(cells):
        return "| " + " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cells)) + " |"

    separator = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"

    lines = [
        f"## {ordklass} ({len(concepts)} concepts)\n",
        fmt_row(headers),
        separator,
    ]
    for row in rows:
        lines.append(fmt_row(row))

    return "\n".join(lines)


def läs_konventioner() -> str:
    if not KONVENTIONER.exists():
        return "(KONVENTIONER.md saknas)"
    return KONVENTIONER.read_text(encoding="utf-8")


def bygg_prompt(tabell: str, ordklass: str) -> str:
    konventioner = läs_konventioner()
    return f"""{GRANSKNING_INSTRUKTION}

---

# KONVENTIONER.md

{konventioner}

---

# Data att granska: {ordklass}

{tabell}
"""


def kör_claude(prompt: str, modell: str) -> str:
    print(f"Anropar claude ({modell})...", flush=True)
    result = subprocess.run(
        ["claude", "--model", modell, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI fel: {result.stderr.strip()}")
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Granska lemman i bas_kärna.csv per ordklass med hjälp av Claude."
    )
    parser.add_argument("--ordklass", help="Ordklass att granska (t.ex. Preposition)")
    parser.add_argument("--lista", action="store_true", help="Lista alla tillgängliga ordklasser")
    parser.add_argument("--modell", default=MODEL, help=f"Claude-modell (standard: {MODEL})")
    parser.add_argument("--visa-tabell", action="store_true", help="Skriv ut tabellen utan att anropa Claude")
    args = parser.parse_args()

    rader = läs_csv()

    if args.lista:
        ordklasser = hämta_ordklasser(rader)
        print(f"\nTillgängliga ordklasser i {CSV_FIL.name}:\n")
        for ok in ordklasser:
            antal = len(set(r["koncept"] for r in rader if r["ordklass"] == ok))
            print(f"  {ok:<30} ({antal} concepts)")
        print()
        return

    if not args.ordklass:
        parser.print_help()
        sys.exit(1)

    # Validera ordklass
    tillgängliga = hämta_ordklasser(rader)
    if args.ordklass not in tillgängliga:
        print(f"Fel: '{args.ordklass}' finns inte i CSV:en.")
        print(f"Tillgängliga: {', '.join(tillgängliga)}")
        sys.exit(1)

    tabell = bygg_tabell(rader, args.ordklass)

    if args.visa_tabell:
        print(tabell)
        return

    # Kontrollera att claude CLI finns (bara när vi faktiskt ska anropa det)
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True, timeout=10)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print("Fel: 'claude' CLI hittades inte. Installera Claude Code och logga in.")
        sys.exit(1)

    prompt = bygg_prompt(tabell, args.ordklass)
    print(f"\nGranskar ordklass: {args.ordklass}")
    print(f"Prompt-storlek: {len(prompt)} tecken (~{len(prompt)//4} tokens)\n")
    print("─" * 60)

    try:
        svar = kör_claude(prompt, args.modell)
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"Fel: {e}")
        sys.exit(1)

    print(svar)
    print("\n" + "─" * 60)
    print(f"Klar! Granska förslagen ovan och besluta rad för rad.")


if __name__ == "__main__":
    main()
