#!/usr/bin/env python3
"""
Importera LLM-genererade översättningar till lexem_synonymlankar.csv.

Input:  ordbok/llm_oversattningar.jsonl
        ordbok/lexem_niva.db
Output: Nya rader läggs till ordbok/lexem_synonymlankar.csv (deduplicerat)

Samma POS-matchningslogik som bygg_synonymlankar.py:
  - Verb ↔ Verb
  - Adjective ↔ Adjective
  - Adverb/Preposition ↔ Adverb/Preposition (POS-kod "r")
  - Noun/ProperNoun/Numeral/Pronoun ↔ (POS-kod "n")
  - Conjunction, Interjection, Particle, Determiner → exakt POS-match
"""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
INPUT = BASE / "llm_oversattningar.jsonl"
LEXEM_DB = BASE / "lexem_niva.db"
OUT_LINKS = BASE / "lexem_synonymlankar.csv"

METHOD = "llm_translation"

# Språk där lexem_niva har POS="Unknown" för (nästan) alla poster
UNKNOWN_POS_LANGS = {"de", "ja"}

# POS som grupperas med ConceptNet-koden "n" (substantiv-liknande)
N_POS = {"Noun", "ProperNoun", "Numeral", "Pronoun"}
# POS som grupperas med "r" (adverb-liknande)
R_POS = {"Adverb", "Preposition"}
# POS som kräver exakt match
EXACT_POS = {"Conjunction", "Interjection", "Particle", "Determiner", "Abbreviation"}
V_POS = {"Verb"}
A_POS = {"Adjective"}


def normalize(text: str) -> str:
    return (text or "").strip().replace("_", " ").lower()


def pos_group(pos: str) -> str:
    """Returnera POS-grupp för matchning."""
    if pos in V_POS:
        return "v"
    if pos in A_POS:
        return "a"
    if pos in R_POS:
        return "r"
    if pos in N_POS:
        return "n"
    return pos  # exakt för Conjunction, Interjection, etc.


def load_lexemes(db_path: Path) -> dict:
    """
    Returnera uppslagsdikt:
      (language, lemma_norm, pos_group) -> [lexem_id, ...]
    """
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT id, lemma, language, pos FROM lexem_niva"
    ).fetchall()
    con.close()

    index: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row_id, lemma, lang, pos in rows:
        norm = normalize(lemma)
        grp = pos_group(pos)
        index[(lang, norm, grp)].append(row_id)
    return index


def load_existing_links() -> set[tuple[int, int]]:
    """Läs befintliga länkpar för deduplicering."""
    existing: set[tuple[int, int]] = set()
    if not OUT_LINKS.exists():
        return existing
    with OUT_LINKS.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                existing.add((int(row["source_lexem_id"]), int(row["target_lexem_id"])))
            except (KeyError, ValueError):
                pass
    return existing


def find_lexem_ids(
    index: dict,
    lang: str,
    lemma: str,
    pos: str,
) -> list[int]:
    """Hitta lexem-IDs för (lang, lemma, pos) med POS-gruppslogik.

    För språk där lexem_niva lagrar alla POS som "Unknown" (de, ja)
    faller vi tillbaka på Unknown-matchning.
    """
    norm = normalize(lemma)
    grp = pos_group(pos)
    ids = index.get((lang, norm, grp), [])

    # Fallback: Unknown-POS-poster för de och ja
    if not ids and lang in UNKNOWN_POS_LANGS:
        ids = index.get((lang, norm, "Unknown"), [])

    return ids


def main() -> None:
    if not INPUT.exists():
        print(f"Fel: {INPUT} saknas. Kör generera_llm_oversattningar.py först.")
        return

    print("Laddar lexem...")
    index = load_lexemes(LEXEM_DB)
    print(f"  {len(index)} unika (språk, lemma, pos-grupp)-kombinationer")

    print("Laddar befintliga länkar...")
    existing_links = load_existing_links()
    print(f"  {len(existing_links)} befintliga länkpar")

    # Bygg snabb omvänd uppslag: source_lexem_id per (language, lemma_norm, pos_group)
    # (redan i index)

    print("Behandlar LLM-översättningar...")
    new_links: list[dict] = []
    stats = defaultdict(int)

    with INPUT.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            src_lemma = item.get("lemma", "")
            src_lang = item.get("language", "")
            src_pos = item.get("pos", "Unknown")
            translations = item.get("translations", {})

            if not src_lemma or not src_lang:
                continue

            # Hitta källexem-IDs
            src_ids = find_lexem_ids(index, src_lang, src_lemma, src_pos)
            if not src_ids:
                stats["source_not_found"] += 1
                continue

            for tgt_lang, tgt_lemma in translations.items():
                if tgt_lemma is None or tgt_lang == src_lang:
                    continue
                tgt_lemma = str(tgt_lemma).strip()
                if not tgt_lemma:
                    continue

                # Hitta målexem-IDs med samma POS-grupp
                tgt_ids = find_lexem_ids(index, tgt_lang, tgt_lemma, src_pos)
                if not tgt_ids:
                    stats["target_not_found"] += 1
                    continue

                for src_id in src_ids:
                    for tgt_id in tgt_ids:
                        pair = (src_id, tgt_id)
                        if pair in existing_links:
                            stats["duplicate"] += 1
                            continue
                        existing_links.add(pair)
                        new_links.append({
                            "source_lexem_id": src_id,
                            "source_lemma": src_lemma,
                            "source_language": src_lang,
                            "source_pos": src_pos,
                            "target_lexem_id": tgt_id,
                            "target_language": tgt_lang,
                            "target_lemma": tgt_lemma,
                            "relation": "translation",
                            "method": METHOD,
                        })
                        stats["added"] += 1

    print(f"\nNya länkar att skriva: {stats['added']}")
    print(f"Dubbletter (redan finns): {stats['duplicate']}")
    print(f"Källexem ej hittat: {stats['source_not_found']}")
    print(f"Målexem ej hittat: {stats['target_not_found']}")

    if not new_links:
        print("Inga nya länkar att lägga till.")
        return

    # Skriv till CSV
    fields = [
        "source_lexem_id", "source_lemma", "source_language", "source_pos",
        "target_lexem_id", "target_language", "target_lemma", "relation", "method",
    ]

    file_exists = OUT_LINKS.exists()
    with OUT_LINKS.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        for row in new_links:
            writer.writerow(row)

    print(f"\nKlart! {len(new_links)} nya rader tillagda i {OUT_LINKS}")

    # Statistik per målspråk
    per_lang: dict[str, int] = defaultdict(int)
    for lnk in new_links:
        per_lang[lnk["target_language"]] += 1
    print("\nNya länkar per målspråk:")
    for lang in sorted(per_lang):
        print(f"  {lang}: {per_lang[lang]}")


if __name__ == "__main__":
    main()
