#!/usr/bin/env python3
"""
Steg 2: Bygg synonymlänkar mellan lexem över språk via ConceptNet.

Input:
  - ordbok/lexem_niva.db (från import_nivalistor.py)
  - ordbok/conceptnet-assertions-5.7.0.csv.gz

Output:
  - ordbok/lexem_synonymlankar.csv
  - ordbok/lexem_olosta.csv
  - ordbok/lexem_olosta.jsonl
"""

from __future__ import annotations

import csv
import gzip
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


BASE = Path(__file__).resolve().parent
LEXEM_DB = BASE / "lexem_niva.db"
CONCEPTNET = BASE / "conceptnet-assertions-5.7.0.csv.gz"
OUT_LINKS = BASE / "lexem_synonymlankar.csv"
OUT_UNRESOLVED_CSV = BASE / "lexem_olosta.csv"
OUT_UNRESOLVED_JSONL = BASE / "lexem_olosta.jsonl"
OUT_NO_MATCH = BASE / "lexem_ingen_match.csv"
OUT_NO_MATCH_BEGINNER = BASE / "lexem_ingen_match_nybörjare.csv"

LANGS = {"sv", "en", "fr", "es", "it", "ja", "de"}
BEGINNER_LEVELS = {"A1", "A2", "N5", "N4"}
LANGUAGE_PASS_ORDER = ["sv", "en", "fr", "es", "it", "de", "ja"]
CN_POS = {"n", "v", "a", "r"}
UNKNOWN_POS_LANGS = {"de", "ja"}
POS_TO_CN = {
    "Noun": "n",
    "ProperNoun": "n",
    "Numeral": "n",
    "Pronoun": "n",
    "Verb": "v",
    "Adjective": "a",
    "Adverb": "r",
    "Preposition": "r",
}
CN_TO_POS = {
    "n": "Noun",
    "v": "Verb",
    "a": "Adjective",
    "r": "Adverb",
}

# ── Tvärspråkliga POS-overrides för Determiner-lexem ──────────────────────
# Olika språk klassificerar funktionsord på olika sätt:
#   - engelska/spanska: bred "Determiner"-klass (artiklar + possessiv + demonstrativ + kvantifikatorer)
#   - svenska/italienska: smal "Determiner" (nästan bara artiklar); resten är Pronoun/Adjective
#   - franska: mittemellan (artiklar + possessiv = Determiner; demonstrativ = Pronoun)
#
# Nyckel: (lemma_lowercase, språk, original_pos) → POS att använda vid länkning.
# Artiklar och "varje"-typer behålls som Determiner (implicit, utelämnas).
LINKING_POS_OVERRIDES: dict[tuple[str, str, str], str] = {
    # ═══ ENGELSKA ═══════════════════════════════════════════════════════════
    # Possessiv → Pronoun  (sv: min/hans/hennes… = Pronoun, it: mio/suo… = Pronoun)
    ("her", "en", "Determiner"): "Pronoun",
    ("his", "en", "Determiner"): "Pronoun",
    ("its", "en", "Determiner"): "Pronoun",
    ("my", "en", "Determiner"): "Pronoun",
    ("our", "en", "Determiner"): "Pronoun",
    ("their", "en", "Determiner"): "Pronoun",
    ("your", "en", "Determiner"): "Pronoun",
    ("whose", "en", "Determiner"): "Pronoun",
    # Demonstrativ → Pronoun  (sv: denna/vad/vilken = Pronoun, it: questo/quello = Pronoun)
    ("that", "en", "Determiner"): "Pronoun",
    ("this", "en", "Determiner"): "Pronoun",
    ("what", "en", "Determiner"): "Pronoun",
    ("whatever", "en", "Determiner"): "Pronoun",
    ("which", "en", "Determiner"): "Pronoun",
    ("such", "en", "Determiner"): "Pronoun",
    # Kvantifikatorer → Pronoun  (sv: alla/båda/ingen/någon/flera… = Pronoun)
    ("all", "en", "Determiner"): "Pronoun",
    ("another", "en", "Determiner"): "Pronoun",
    ("any", "en", "Determiner"): "Pronoun",
    ("both", "en", "Determiner"): "Pronoun",
    ("either", "en", "Determiner"): "Pronoun",
    ("many", "en", "Determiner"): "Pronoun",
    ("neither", "en", "Determiner"): "Pronoun",
    ("no", "en", "Determiner"): "Pronoun",
    ("several", "en", "Determiner"): "Pronoun",
    ("some", "en", "Determiner"): "Pronoun",
    # Kvantifikatorer → Adjective  (sv: få/halv/liten/sista… = Adjective, it: poco/doppio… = Adjective)
    ("double", "en", "Determiner"): "Adjective",
    ("few", "en", "Determiner"): "Adjective",
    ("half", "en", "Determiner"): "Adjective",
    ("last", "en", "Determiner"): "Adjective",
    ("least", "en", "Determiner"): "Adjective",
    ("less", "en", "Determiner"): "Adjective",
    ("little", "en", "Determiner"): "Adjective",
    ("more", "en", "Determiner"): "Adjective",
    ("most", "en", "Determiner"): "Adjective",
    ("much", "en", "Determiner"): "Adjective",
    # Grad/mängd → Adverb  (sv: nog/tillräckligt = Adverb)
    ("enough", "en", "Determiner"): "Adverb",
    ("lot", "en", "Determiner"): "Adverb",
    # Ordningstal → Numeral  (sv: första/andra = Numeral)
    ("first", "en", "Determiner"): "Numeral",
    ("one", "en", "Determiner"): "Numeral",
    ("second", "en", "Determiner"): "Numeral",
    # Mängdsubstantiv → Noun
    ("dozen", "en", "Determiner"): "Noun",
    # each, every → behålls som Determiner (sv: varje = Determiner)

    # ═══ SPANSKA ═════════════════════════════════════════════════════════════
    # Possessiv → Pronoun
    ("mi", "es", "Determiner"): "Pronoun",
    ("nuestro", "es", "Determiner"): "Pronoun",
    ("su", "es", "Determiner"): "Pronoun",
    ("tu", "es", "Determiner"): "Pronoun",
    ("vuestro", "es", "Determiner"): "Pronoun",
    # Demonstrativ → Pronoun
    ("aquél", "es", "Determiner"): "Pronoun",
    ("ese", "es", "Determiner"): "Pronoun",
    ("eso", "es", "Determiner"): "Pronoun",
    ("este", "es", "Determiner"): "Pronoun",
    ("esto", "es", "Determiner"): "Pronoun",
    ("ése", "es", "Determiner"): "Pronoun",
    ("éste", "es", "Determiner"): "Pronoun",
    # Interrogativ/indefinit → Pronoun
    ("algo", "es", "Determiner"): "Pronoun",
    ("alguien", "es", "Determiner"): "Pronoun",
    ("alguno", "es", "Determiner"): "Pronoun",
    ("algún", "es", "Determiner"): "Pronoun",
    ("cualquier", "es", "Determiner"): "Pronoun",
    ("cuánto", "es", "Determiner"): "Pronoun",
    ("nadie", "es", "Determiner"): "Pronoun",
    ("ninguno", "es", "Determiner"): "Pronoun",
    ("ningún", "es", "Determiner"): "Pronoun",
    ("qué", "es", "Determiner"): "Pronoun",
    ("todo", "es", "Determiner"): "Pronoun",
    # Kvantifikatorer → Adjective  (it: molto/poco/altro/tanto… = Adjective)
    ("bastante", "es", "Determiner"): "Adjective",
    ("demasiado", "es", "Determiner"): "Adjective",
    ("mucho", "es", "Determiner"): "Adjective",
    ("muchísimo", "es", "Determiner"): "Adjective",
    ("otro", "es", "Determiner"): "Adjective",
    ("poco", "es", "Determiner"): "Adjective",
    ("tanto", "es", "Determiner"): "Adjective",
    ("varios", "es", "Determiner"): "Adjective",
    # cada → behålls som Determiner (sv: varje = Determiner)
    # el, la, lo, los, un, una, uno, de, en → behålls som Determiner (artiklar)

    # ═══ FRANSKA ═════════════════════════════════════════════════════════════
    # Possessiv → Pronoun  (sv: min/vår/deras = Pronoun, it: mio/nostro = Pronoun)
    ("leur", "fr", "Determiner"): "Pronoun",
    ("mon", "fr", "Determiner"): "Pronoun",
    ("notre", "fr", "Determiner"): "Pronoun",
    ("son", "fr", "Determiner"): "Pronoun",
    ("ton", "fr", "Determiner"): "Pronoun",
    ("votre", "fr", "Determiner"): "Pronoun",
    # au, de, du, le, un → behålls som Determiner (artiklar)

    # ═══ SPANSKA — interrogativa/relativa ord ════════════════════════════════
    # Spanska klassificerar fråge-/relativadverb som Pronomen/Konjunktion/Preposition
    # medan sv/en/fr/it klassificerar dem som Adverb.
    ("adonde", "es", "Conjunction"): "Adverb",   # wohin/where to
    ("adonde", "es", "Pronoun"):     "Adverb",
    ("como",   "es", "Preposition"): "Adverb",   # hur/how
    ("cuando", "es", "Conjunction"): "Adverb",   # när/when
    ("cómo",   "es", "Pronoun"):     "Adverb",   # hur/how (betonad form)
    ("donde",  "es", "Pronoun"):     "Adverb",   # var/where
    ("dónde",  "es", "Pronoun"):     "Adverb",   # var/where (betonad form)
    # Relativpronomen/konjunktion → Pronoun  (en: that/which, sv: som/att)
    ("que",    "es", "Conjunction"): "Pronoun",
    ("que",    "fr", "Conjunction"): "Pronoun",

    # ═══ ITALIENSKA — förkortningar → Noun ═══════════════════════════════════
    # Italienska har POS=Abbreviation (unikt för it). Dessa internationella
    # förkortningar finns i andra språk som Noun.
    ("cd",    "it", "Abbreviation"): "Noun",
    ("cm",    "it", "Abbreviation"): "Noun",
    ("ecc.",  "it", "Abbreviation"): "Noun",
    ("es.",   "it", "Abbreviation"): "Noun",
    ("km",    "it", "Abbreviation"): "Noun",
    ("p.e.",  "it", "Abbreviation"): "Noun",
    ("pc",    "it", "Abbreviation"): "Noun",
    ("rai",   "it", "Abbreviation"): "Noun",
    ("tel.",  "it", "Abbreviation"): "Noun",
    ("tv",    "it", "Abbreviation"): "Noun",
}


@dataclass(frozen=True)
class Lexem:
    id: int
    lemma: str
    lemma_norm: str
    language: str
    pos: str
    level: str
    source: str
    pos_code: Optional[str]


def normalize_label(text: str) -> str:
    return (text or "").strip().replace("_", " ").lower()


def parse_concept_uri(uri: str) -> Optional[tuple[str, str, Optional[str]]]:
    """
    Returnerar (lang, lemma_norm, pos_code?) för URI som /c/en/run/v.
    """
    if not uri.startswith("/c/"):
        return None
    parts = uri.split("/")
    if len(parts) < 4:
        return None
    lang = parts[2]
    lemma = normalize_label(parts[3])
    pos = None
    for p in reversed(parts[4:]):
        if p in CN_POS:
            pos = p
            break
    return (lang, lemma, pos)


def classify_candidate(
    target_pos: Optional[str],
    target_evidence: set[str],
    source_evidence: set[str],
) -> str:
    """
    Regler (från test.py + användarkrav):
    - Om target-sidan har POS-evidens, använd den först.
    - Om bara source-sidan har POS-evidens, tillåt match (infererad POS).
    - Om ingen sida har POS-evidens -> unknown (olöst).
    """
    if target_pos is None:
        return "unsupported_source_pos"

    if target_evidence:
        has_match = target_pos in target_evidence
        has_contradiction = any(pos != target_pos for pos in target_evidence)
        scope = "target"
    elif source_evidence:
        has_match = target_pos in source_evidence
        has_contradiction = False if has_match else any(pos != target_pos for pos in source_evidence)
        scope = "source"
    else:
        has_match = False
        has_contradiction = False
        scope = "none"

    if has_match and not has_contradiction:
        return "validated"
    if has_match and has_contradiction and scope == "target":
        return "mixed_conflict"
    if has_contradiction:
        return "contradiction_only"
    return "unknown"


def load_lexemes(path: Path) -> list[Lexem]:
    con = sqlite3.connect(path)
    rows = con.execute(
        "SELECT id, lemma, language, pos, level, source FROM lexem_niva ORDER BY id"
    ).fetchall()
    con.close()
    lexemes = []
    for row in rows:
        original_pos = row[3]
        lemma_norm = normalize_label(row[1])
        linking_pos = LINKING_POS_OVERRIDES.get(
            (lemma_norm, row[2], original_pos), original_pos
        )
        pos_code = POS_TO_CN.get(linking_pos)
        lexemes.append(
            Lexem(
                id=row[0],
                lemma=row[1],
                lemma_norm=lemma_norm,
                language=row[2],
                pos=linking_pos,
                level=row[4],
                source=row[5],
                pos_code=pos_code,
            )
        )
    return lexemes


def collect_conceptnet_data(
    conceptnet_path: Path,
    lexicon_words: dict[str, set[str]],
) -> tuple[dict[str, dict[str, set[str]]], dict[tuple[str, str], list[dict]]]:
    pos_map: dict[str, dict[str, set[str]]] = {lang: defaultdict(set) for lang in LANGS}
    candidates: dict[tuple[str, str], list[dict]] = defaultdict(list)

    with gzip.open(conceptnet_path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i and i % 2_000_000 == 0:
                print(f"ConceptNet-rad {i}...")

            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue

            rel = parts[1]
            p2 = parts[2]
            p3 = parts[3]

            if rel == "/r/PartOfSpeech":
                node = parse_concept_uri(p2)
                if node is None:
                    continue
                lang, lemma, _ = node
                pos = p3.split("/")[-1]
                if lang in LANGS and lemma in lexicon_words.get(lang, set()) and pos in CN_POS:
                    pos_map[lang][lemma].add(pos)
                continue

            if rel != "/r/Synonym":
                continue

            for source_node, other_node in ((p2, p3), (p3, p2)):
                src = parse_concept_uri(source_node)
                other = parse_concept_uri(other_node)
                if src is None or other is None:
                    continue

                src_lang, src_lemma, src_pos = src
                tgt_lang, tgt_lemma, tgt_uri_pos = other

                if src_lang not in LANGS or tgt_lang not in LANGS:
                    continue
                if src_lemma not in lexicon_words.get(src_lang, set()):
                    continue

                candidates[(src_lang, src_lemma)].append(
                    {
                        "target_lang": tgt_lang,
                        "target_lemma": tgt_lemma,
                        "source_pos": src_pos,
                        "target_uri_pos": tgt_uri_pos,
                        "target_exists": tgt_lemma in lexicon_words.get(tgt_lang, set()),
                    }
                )

    return pos_map, candidates


def build_links_and_unresolved(
    lexemes: list[Lexem],
    pos_map: dict[str, dict[str, set[str]]],
    candidates: dict[tuple[str, str], list[dict]],
) -> tuple[list[dict], list[dict]]:
    lexeme_ids_by_lang_lemma_pos: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    lexeme_ids_by_lang_lemma_pos_label: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    lexeme_ids_by_lang_lemma_unknown: dict[tuple[str, str], list[int]] = defaultdict(list)
    known_pos_by_lang_lemma: dict[tuple[str, str], set[str]] = defaultdict(set)

    for lx in lexemes:
        if lx.pos_code:
            lexeme_ids_by_lang_lemma_pos[(lx.language, lx.lemma_norm, lx.pos_code)].append(lx.id)
            known_pos_by_lang_lemma[(lx.language, lx.lemma_norm)].add(lx.pos_code)
        if lx.pos and lx.pos != "Unknown":
            lexeme_ids_by_lang_lemma_pos_label[(lx.language, lx.lemma_norm, lx.pos)].append(lx.id)
        elif lx.pos == "Unknown":
            lexeme_ids_by_lang_lemma_unknown[(lx.language, lx.lemma_norm)].append(lx.id)

    inferred_unknown_pos: dict[tuple[str, str], set[str]] = defaultdict(set)

    def source_pos_set_for_key(lang: str, lemma: str) -> set[str]:
        key = (lang, lemma)
        out = set(known_pos_by_lang_lemma.get(key, set()))
        if lang in UNKNOWN_POS_LANGS:
            out.update(inferred_unknown_pos.get(key, set()))
        return out

    def propagate_from_sources(
        source_langs: set[str],
        target_langs: set[str],
    ) -> int:
        added = 0
        for (src_lang, src_lemma), cand_rows in candidates.items():
            if src_lang not in source_langs:
                continue
            source_pos_set = source_pos_set_for_key(src_lang, src_lemma)
            if not source_pos_set:
                continue
            for c in cand_rows:
                if not c["target_exists"]:
                    continue
                target_lang = c["target_lang"]
                target_lemma = c["target_lemma"]
                if target_lang not in target_langs:
                    continue
                if (target_lang, target_lemma) not in lexeme_ids_by_lang_lemma_unknown:
                    continue
                edge_source_pos = c["source_pos"] if c["source_pos"] in CN_POS else None
                for pos_code in source_pos_set:
                    if edge_source_pos and edge_source_pos != pos_code:
                        continue
                    if pos_code not in inferred_unknown_pos[(target_lang, target_lemma)]:
                        inferred_unknown_pos[(target_lang, target_lemma)].add(pos_code)
                        added += 1
        return added

    # Språkpass i explicit ordning: sv/en/fr/es/it/de/ja.
    # Vid varje pass försöker källspråket översätta till alla andra språk.
    for source_lang in LANGUAGE_PASS_ORDER:
        propagate_from_sources({source_lang}, LANGS - {source_lang})

    # Sista extra varv: de -> ja igen, för att fånga ny ja-POS som uppstår
    # efter ja->de-pass.
    propagate_from_sources({"de"}, {"ja"})

    effective_pos_by_lexeme_id: dict[int, set[str]] = {}
    for lx in lexemes:
        if lx.pos_code:
            effective_pos_by_lexeme_id[lx.id] = {lx.pos_code}
        elif lx.language in UNKNOWN_POS_LANGS and lx.pos == "Unknown":
            effective_pos_by_lexeme_id[lx.id] = set(
                inferred_unknown_pos.get((lx.language, lx.lemma_norm), set())
            )
        else:
            effective_pos_by_lexeme_id[lx.id] = set()

    links: list[dict] = []
    link_keys: set[tuple[int, int]] = set()
    unresolved: list[dict] = []

    for lx in lexemes:
        failed_langs: list[str] = []
        failed_reasons: dict[str, str] = {}
        matched_langs = 0

        key = (lx.language, lx.lemma_norm)
        all_candidates = candidates.get(key, [])
        source_pos_codes = effective_pos_by_lexeme_id.get(lx.id, set())

        for target_lang in sorted(LANGS - {lx.language}):
            if not source_pos_codes and lx.pos == "Unknown":
                failed_langs.append(target_lang)
                failed_reasons[target_lang] = "unsupported_source_pos"
                continue

            scoped = [
                c
                for c in all_candidates
                if c["target_lang"] == target_lang and c["target_exists"]
            ]
            if not scoped:
                failed_langs.append(target_lang)
                failed_reasons[target_lang] = "no_candidate_in_lexicon"
                continue

            aggregated: dict[str, dict[str, set[str]]] = {}
            for c in scoped:
                w = c["target_lemma"]
                if w not in aggregated:
                    aggregated[w] = {
                        "source_pos_set": set(),
                        "target_uri_pos_set": set(),
                        "lexicon_pos_set": set(),
                    }
                if c["source_pos"] in CN_POS:
                    aggregated[w]["source_pos_set"].add(c["source_pos"])
                if c["target_uri_pos"] in CN_POS:
                    aggregated[w]["target_uri_pos_set"].add(c["target_uri_pos"])
                aggregated[w]["lexicon_pos_set"].update(
                    known_pos_by_lang_lemma.get((target_lang, w), set())
                )
                aggregated[w]["lexicon_pos_set"].update(pos_map[target_lang].get(w, set()))

            accepted_words: list[tuple[str, Optional[str]]] = []
            seen_statuses: set[str] = set()
            for word, data in aggregated.items():
                if target_lang not in UNKNOWN_POS_LANGS and lx.pos != "Unknown":
                    # För språk där båda sidor har explicit ordklass räcker exakt POS-match
                    # i lexem_niva även om ConceptNet saknar POS-tag för relationen.
                    target_ids_same_pos = lexeme_ids_by_lang_lemma_pos_label.get(
                        (target_lang, word, lx.pos), []
                    )
                    if target_ids_same_pos:
                        accepted_words.append((word, None))
                        continue

                target_evidence = set(data["target_uri_pos_set"]) | set(data["lexicon_pos_set"])
                source_evidence = set(data["source_pos_set"])
                for pos_code in source_pos_codes:
                    # Om ConceptNet explicit taggar källsidan (t.ex. /c/de/abfahren/v),
                    # får vi endast länka för just den POS-koden.
                    if source_evidence and pos_code not in source_evidence:
                        continue
                    # Källlexemets (möjligen infererade) POS används som extra evidens
                    # för att kunna länka även när ConceptNet saknar explicit POS-tag.
                    status = classify_candidate(pos_code, target_evidence, source_evidence | {pos_code})
                    seen_statuses.add(status)
                    # mixed_conflict betyder att målordet har blandad POS-evidens,
                    # men inkluderar även önskad POS. Vi länkar ändå.
                    if status in {"validated", "mixed_conflict"}:
                        accepted_words.append((word, pos_code))

            added_links = 0
            for word, pos_code in accepted_words:
                if pos_code is None:
                    ids = set(lexeme_ids_by_lang_lemma_pos_label.get((target_lang, word, lx.pos), []))
                else:
                    ids = set(lexeme_ids_by_lang_lemma_pos.get((target_lang, word, pos_code), []))
                    # Unknown-poster används bara för språk där POS saknas i importen.
                    if target_lang in UNKNOWN_POS_LANGS:
                        ids.update(lexeme_ids_by_lang_lemma_unknown.get((target_lang, word), []))
                for target_id in ids:
                    lk = (lx.id, target_id)
                    if lk in link_keys:
                        continue
                    link_keys.add(lk)
                    added_links += 1
                    links.append(
                        {
                            "source_lexem_id": lx.id,
                            "source_lemma": lx.lemma,
                            "source_language": lx.language,
                            "source_pos": lx.pos if lx.pos_code else CN_TO_POS.get(pos_code, lx.pos),
                            "target_lexem_id": target_id,
                            "target_language": target_lang,
                            "target_lemma": word,
                            "relation": "synonym",
                            "method": "conceptnet_pos_filtered",
                        }
                    )

            if added_links == 0:
                failed_langs.append(target_lang)
                if "unknown" in seen_statuses:
                    failed_reasons[target_lang] = "unknown_pos_evidence"
                elif "mixed_conflict" in seen_statuses:
                    failed_reasons[target_lang] = "mixed_pos_evidence"
                elif "contradiction_only" in seen_statuses:
                    failed_reasons[target_lang] = "pos_contradiction"
                elif "unsupported_source_pos" in seen_statuses:
                    failed_reasons[target_lang] = "unsupported_source_pos"
                else:
                    failed_reasons[target_lang] = "no_validated_candidate"
            else:
                matched_langs += 1

        # Olöst = minst ett målspråk saknar länk (även om andra språk lyckades).
        if failed_langs:
            unresolved.append(
                {
                    "lemma": lx.lemma,
                    "language": lx.language,
                    "pos": lx.pos,
                    "level": lx.level,
                    "source": lx.source,
                    "failed_languages": ",".join(sorted(failed_langs)),
                    "failure_reasons": json.dumps(
                        {k: failed_reasons[k] for k in sorted(failed_reasons)},
                        ensure_ascii=False,
                    ),
                }
            )

    return links, unresolved


def write_outputs(links: list[dict], unresolved: list[dict]) -> None:
    with OUT_LINKS.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "source_lexem_id",
            "source_lemma",
            "source_language",
            "source_pos",
            "target_lexem_id",
            "target_language",
            "target_lemma",
            "relation",
            "method",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in links:
            w.writerow(row)

    with OUT_UNRESOLVED_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "lemma",
            "language",
            "pos",
            "level",
            "source",
            "failed_languages",
            "failure_reasons",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in unresolved:
            w.writerow(row)

    with OUT_UNRESOLVED_JSONL.open("w", encoding="utf-8") as f:
        for row in unresolved:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    unresolved_fields = [
        "lemma", "language", "pos", "level", "source",
        "failed_languages", "failure_reasons",
    ]

    # Lexem som saknar match i samtliga målspråk
    no_match = [
        row for row in unresolved
        if len(row["failed_languages"].split(",")) == len(LANGS) - 1
    ]
    with OUT_NO_MATCH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=unresolved_fields)
        w.writeheader()
        for row in no_match:
            w.writerow(row)

    # Nybörjarvariant: A1/A2 (japanska: N5/N4), ingen match i något målspråk
    no_match_beginner = [
        row for row in no_match
        if row["level"] in BEGINNER_LEVELS
    ]
    with OUT_NO_MATCH_BEGINNER.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=unresolved_fields)
        w.writeheader()
        for row in no_match_beginner:
            w.writerow(row)


def main() -> None:
    print("Laddar lexem...")
    lexemes = load_lexemes(LEXEM_DB)
    lexicon_words: dict[str, set[str]] = {lang: set() for lang in LANGS}
    for lx in lexemes:
        lexicon_words[lx.language].add(lx.lemma_norm)

    print("Skannar ConceptNet...")
    pos_map, candidates = collect_conceptnet_data(CONCEPTNET, lexicon_words)

    print("Bygger länkar + olösta...")
    links, unresolved = build_links_and_unresolved(lexemes, pos_map, candidates)

    write_outputs(links, unresolved)

    print("\nKlart.")
    print(f"Länkar: {len(links)} -> {OUT_LINKS}")
    print(f"Olösta lexem: {len(unresolved)} -> {OUT_UNRESOLVED_CSV}")

    # Kort språkstatistik för olösta
    per_lang = defaultdict(int)
    for row in unresolved:
        per_lang[row["language"]] += 1
    print("Olösta per språk:")
    for lang in sorted(LANGS):
        print(f"  {lang}: {per_lang.get(lang, 0)}")

    # Statistik för ingen-match-filer
    no_match = [
        row for row in unresolved
        if len(row["failed_languages"].split(",")) == len(LANGS) - 1
    ]
    no_match_beginner = [row for row in no_match if row["level"] in BEGINNER_LEVELS]

    print(f"\nIngen match alls: {len(no_match)} -> {OUT_NO_MATCH}")
    per_lang_nm = defaultdict(int)
    for row in no_match:
        per_lang_nm[row["language"]] += 1
    for lang in sorted(LANGS):
        print(f"  {lang}: {per_lang_nm.get(lang, 0)}")

    print(f"\nIngen match (nybörjare A1/A2/N5/N4): {len(no_match_beginner)} -> {OUT_NO_MATCH_BEGINNER}")
    per_lang_nb = defaultdict(int)
    for row in no_match_beginner:
        per_lang_nb[row["language"]] += 1
    for lang in sorted(LANGS):
        print(f"  {lang}: {per_lang_nb.get(lang, 0)}")


if __name__ == "__main__":
    main()
