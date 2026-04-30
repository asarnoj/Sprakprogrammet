#!/usr/bin/env python3
"""
Generera LLM-översättningar för icke-noun-lexem som saknar match i ConceptNet.

Input:  ordbok/lexem_ingen_match_nybörjare.csv
Output: ordbok/llm_oversattningar.jsonl

Kör i batchar om 100 ord. Återupptagbar: ord som redan finns i output-filen hoppas över.

Använder Claude CLI (`claude -p`) – kräver att du är inloggad med Claude Pro.
Kör UTANFÖR Claude Code (öppna ett vanligt terminal-fönster).
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
INPUT = BASE / "lexem_ingen_match_nybörjare.csv"
OUTPUT = BASE / "llm_oversattningar.jsonl"

BATCH_SIZE = 100
MODEL = "claude-haiku-4-5-20251001"
SKIP_POS = {"Noun", "ProperNoun"}

PROMPT_TEMPLATE = """\
Du är en professionell lingvist som hjälper till att bygga ett flerspråkigt lexikon.
Ditt svar ska ALLTID vara ett giltigt JSON-array – inget annat, inga förklaringar.

Nedan finns {n} ord på ett källspråk. Översätt varje ord till de 6 andra språken:
sv=svenska, en=engelska, de=tyska, fr=franska, es=spanska, it=italienska, ja=japanska.

Regler (VIKTIGT):
1. Ange BARA översättning om du är helt säker på att den är korrekt och naturlig.
2. Använd kanonisk lexemform: infinitiv för verb (sv: "springa", ja: 走る), singular/maskulinum för adjektiv.
3. Om det inte finns ett tydligt enskilt ord som motsvarighet, sätt null för det språket.
4. För källspråkets eget språk: sätt alltid null.
5. För ord med pos="Unknown": bestäm den faktiska ordklassen och ange den som "pos" i svaret.
   Tillåtna ordklasser: Verb/Adjective/Adverb/Noun/Pronoun/Preposition/Conjunction/Interjection/Particle/Numeral/Determiner
6. Hellre null än fel – felen skapar kaos i systemet.

Indata (JSON):
{input_json}

Svara med ett JSON-array där varje element har exakt detta format:
{{
  "lemma": "<källlemma>",
  "language": "<källspråk>",
  "pos": "<ordklass>",
  "translations": {{
    "sv": "<översättning eller null>",
    "en": "<översättning eller null>",
    "de": "<översättning eller null>",
    "fr": "<översättning eller null>",
    "es": "<översättning eller null>",
    "it": "<översättning eller null>",
    "ja": "<översättning eller null>"
  }}
}}
"""


def load_already_processed() -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    if not OUTPUT.exists():
        return done
    with OUTPUT.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                done.add((obj["lemma"], obj["language"]))
            except (json.JSONDecodeError, KeyError):
                pass
    return done


def load_words() -> list[dict]:
    with INPUT.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["pos"] not in SKIP_POS]


def build_prompt(batch: list[dict]) -> str:
    input_items = [
        {"lemma": r["lemma"], "language": r["language"], "pos": r["pos"]}
        for r in batch
    ]
    return PROMPT_TEMPLATE.format(
        n=len(batch),
        input_json=json.dumps(input_items, ensure_ascii=False, indent=2),
    )


def call_claude_cli(prompt: str) -> list[dict]:
    result = subprocess.run(
        ["claude", "--model", MODEL, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI fel: {result.stderr.strip()}")

    text = result.stdout.strip()

    # Rensa bort eventuella markdown-kodblock
    if text.startswith("```"):
        lines = text.splitlines()
        end = -1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])

    return json.loads(text)


def validate_result(results: list[dict], batch: list[dict]) -> list[dict]:
    batch_keys = {(r["lemma"], r["language"]) for r in batch}
    valid = []
    for item in results:
        if not isinstance(item, dict):
            continue
        if "lemma" not in item or "language" not in item:
            continue
        if (item["lemma"], item["language"]) not in batch_keys:
            print(f"  VARNING: okänt lemma i svar: {item['lemma']}/{item['language']}")
            continue
        if "translations" not in item or not isinstance(item["translations"], dict):
            continue
        valid.append(item)
    return valid


def process_batch(batch: list[dict], out_file, batch_num: int, total_batches: int) -> int:
    print(f"Batch {batch_num}/{total_batches} ({len(batch)} ord)...", end=" ", flush=True)
    prompt = build_prompt(batch)

    for attempt in range(3):
        try:
            results = call_claude_cli(prompt)
            break
        except (json.JSONDecodeError, RuntimeError, subprocess.TimeoutExpired) as e:
            print(f"\n  Fel (försök {attempt+1}): {e}")
            if attempt == 2:
                print("  Hoppar över denna batch.")
                return 0
            time.sleep(3 * (attempt + 1))

    results = validate_result(results, batch)

    written = 0
    for item in results:
        out_file.write(json.dumps(item, ensure_ascii=False) + "\n")
        written += 1

    out_file.flush()
    print(f"OK ({written} poster skrivna)")
    return written


def main() -> None:
    # Kontrollera att claude CLI finns
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Fel: 'claude' CLI hittades inte. Installera Claude Code och logga in.")
        sys.exit(1)

    words = load_words()
    print(f"Totalt icke-noun-lexem: {len(words)}")

    done = load_already_processed()
    remaining = [w for w in words if (w["lemma"], w["language"]) not in done]
    print(f"Redan klara: {len(done)}, kvar: {len(remaining)}")

    if not remaining:
        print("Allt klart!")
        return

    batches = [remaining[i:i + BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]
    print(f"Antal batchar: {len(batches)} (à {BATCH_SIZE} ord)")
    print(f"Modell: {MODEL}\n")

    total_written = 0

    with OUTPUT.open("a", encoding="utf-8") as out_file:
        for i, batch in enumerate(batches, 1):
            written = process_batch(batch, out_file, i, len(batches))
            total_written += written

    print(f"\nKlart! Totalt {total_written} poster skrivna till {OUTPUT}")


if __name__ == "__main__":
    main()
