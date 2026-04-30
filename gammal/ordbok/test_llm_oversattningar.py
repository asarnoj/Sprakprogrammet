#!/usr/bin/env python3
"""
Testa LLM-översättningsgenereringen med bara första batch (100 ord).

Använder claude -p CLI. Sparar resultat till llm_oversattningar_test.jsonl.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
INPUT = BASE / "lexem_ingen_match_nybörjare.csv"
OUTPUT_TEST = BASE / "llm_oversattningar_test.jsonl"
MODEL = "claude-haiku-4-5-20251001"

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


def load_words() -> list[dict]:
    with INPUT.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    non_nouns = [r for r in rows if r["pos"] not in {"Noun", "ProperNoun"}]
    return non_nouns[:50]  # 50 ord för test


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
    print("Kallar claude -p...")
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
    errors = []

    for i, item in enumerate(results):
        if not isinstance(item, dict):
            errors.append(f"  Item {i}: inte ett dict")
            continue
        if "lemma" not in item or "language" not in item:
            errors.append(f"  Item {i}: saknar lemma/language")
            continue
        if (item["lemma"], item["language"]) not in batch_keys:
            errors.append(f"  Item {i}: okänt lemma {item['lemma']}/{item['language']}")
            continue
        if "translations" not in item or not isinstance(item["translations"], dict):
            errors.append(f"  Item {i}: saknar translations dict")
            continue
        valid.append(item)

    if errors:
        print("\nValiderings-varningar:")
        for err in errors:
            print(err)

    return valid


def main() -> None:
    # Kontrollera claude CLI
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Fel: 'claude' CLI hittades inte.")
        sys.exit(1)

    print("Läser första 100 icke-noun-ord...")
    batch = load_words()
    print(f"Batch storlek: {len(batch)} ord")
    print(f"Språk: {sorted(set(r['language'] for r in batch))}")
    print(f"POS-typer: {sorted(set(r['pos'] for r in batch))}")

    prompt = build_prompt(batch)
    print(f"\nPrompt-storlek: {len(prompt)} tecken, ~{len(prompt)//4} tokens ungefär")

    try:
        results = call_claude_cli(prompt)
    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"Fel vid API-anrop: {e}")
        sys.exit(1)

    print(f"Svar innehöll {len(results)} poster")

    valid = validate_result(results, batch)
    print(f"Giltiga poster: {len(valid)}/{len(results)}")

    # Räkna översättningar
    trans_count = 0
    trans_by_lang = {}
    for item in valid:
        for lang, trans in item["translations"].items():
            if trans is not None:
                trans_count += 1
                trans_by_lang[lang] = trans_by_lang.get(lang, 0) + 1

    print(f"\nÖversättningar per språk:")
    for lang in sorted(trans_by_lang):
        print(f"  {lang}: {trans_by_lang[lang]}")
    print(f"  Totalt: {trans_count}/{len(valid)*6}")

    # Spara till test-fil
    with OUTPUT_TEST.open("w", encoding="utf-8") as f:
        for item in valid:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n✓ Sparade {len(valid)} poster till {OUTPUT_TEST.name}")
    print("\nNästa steg:")
    print(f"  1. Inspektera {OUTPUT_TEST.name} för att verifiera resultat")
    print(f"  2. Om det ser bra ut, kör: python3 ordbok/generera_llm_oversattningar.py")
    print(f"  3. Sedan: python3 ordbok/importera_llm_oversattningar.py")


if __name__ == "__main__":
    main()
