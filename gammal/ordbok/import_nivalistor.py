#!/usr/bin/env python3
"""
Importerar nivålistor för sv/en/fr/es/it/ja/de till en gemensam lexemdatabas.

Output:
  - ordbok/lexem_niva.db
  - ordbok/lexem_niva.csv
  - ordbok/lexem_niva.jsonl
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import xlrd


BASE = Path(__file__).resolve().parent
NIVALISTOR = BASE / "nivålistor"
OUT_DB = BASE / "lexem_niva.db"
OUT_CSV = BASE / "lexem_niva.csv"
OUT_JSONL = BASE / "lexem_niva.jsonl"

CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
JP_ORDER = {"N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}
ALLOWED_CEFR_LEVELS = {"A1", "A2", "B1", "B2"}
ALLOWED_CEFR_LEVELS_FR_ES = {"A1", "A2", "B1"}


@dataclass(frozen=True)
class LexemRad:
    lemma: str
    språk: str
    ordklass: str
    nivå: str
    källa: str


def normalisera_lemma(lemma: str) -> str:
    lemma = (lemma or "").strip().replace("_", " ")
    lemma = re.sub(r"\s+", " ", lemma)
    return lemma


def normalisera_cefr(raw: str) -> Optional[str]:
    if not raw:
        return None
    m = re.search(r"(A1|A2|B1|B2|C1|C2)", str(raw).upper())
    return m.group(1) if m else None


def normalisera_jlpt(raw: str) -> Optional[str]:
    if not raw:
        return None
    m = re.search(r"(N[1-5])", str(raw).upper())
    if m:
        return m.group(1)
    m2 = re.search(r"JLPT[_\s]?([1-5])", str(raw).upper())
    if m2:
        return f"N{m2.group(1)}"
    return None


def map_pos_common(raw: str) -> str:
    t = (raw or "").strip().lower()
    if not t:
        return "Unknown"

    direct = {
        "noun": "Noun",
        "verb": "Verb",
        "adjective": "Adjective",
        "adverb": "Adverb",
        "pronoun": "Pronoun",
        "preposition": "Preposition",
        "conjunction": "Conjunction",
        "interjection": "Interjection",
        "determiner": "Determiner",
        "definite article": "Determiner",
        "indefinite article": "Determiner",
        "auxiliary verb": "Verb",
        "linking verb": "Verb",
        "modal verb": "Verb",
        "number": "Numeral",
        "ordinal number": "Numeral",
        "infinitive marker": "Particle",
        "exclamation": "Interjection",
        "prep": "Preposition",
        "conj": "Conjunction",
        "aux verb": "Verb",
        "det": "Determiner",
        "numeral": "Numeral",
        "n": "Noun",
        "v": "Verb",
        "adj": "Adjective",
        "adv": "Adverb",
        "np": "ProperNoun",
        "pron": "Pronoun",
        "num": "Numeral",
        "int": "Interjection",
        "abb": "Abbreviation",
        "for": "Unknown",
        "subj": "Conjunction",
        "particle": "Particle",
        "particip": "Adjective",
        "pt0": "Pronoun",
        "pt": "Pronoun",
        "p00": "Pronoun",
        "nm": "Verb",
    }
    if t in direct:
        return direct[t]

    # Svenska Kelly
    if t.startswith("noun"):
        return "Noun"
    if t in {"adjective", "adverb", "verb", "pronoun", "prep"}:
        return map_pos_common(t)

    # Franska FLELex
    fr = {
        "nom": "Noun",
        "ver": "Verb",
        "adj": "Adjective",
        "adv": "Adverb",
        "pro": "Pronoun",
        "prp": "Preposition",
        "prp:det": "Determiner",
        "det:art": "Determiner",
        "det:pos": "Determiner",
        "kon": "Conjunction",
        "int": "Interjection",
    }
    if t in fr:
        return fr[t]

    # Spanska ELELex: EAGLES-liknande taggar
    first = t.split()[0].split(",")[0].replace("?", "")
    if first.startswith("nc") or first == "ncp":
        return "Noun"
    if first.startswith("np"):
        return "ProperNoun"
    if first.startswith("v"):
        return "Verb"
    if first.startswith("aq") or first.startswith("ao") or first.startswith("ap"):
        return "Adjective"
    if first.startswith("rg") or first.startswith("rn"):
        return "Adverb"
    if first.startswith("pp") or first.startswith("pd") or first.startswith("pi") or first.startswith("pr"):
        return "Pronoun"
    if first.startswith("d"):
        return "Determiner"
    if first.startswith("sp") or first == "s":
        return "Preposition"
    if first.startswith("cc") or first.startswith("cs"):
        return "Conjunction"
    if first.startswith("i"):
        return "Interjection"
    if first.startswith("z"):
        return "Numeral"

    return "Unknown"


def infer_japanese_pos(expression: str, meaning: str) -> str:
    meaning = (meaning or "").strip().lower()
    expression = (expression or "").strip()
    if meaning.startswith("to "):
        return "Verb"
    if expression.endswith("する"):
        return "Verb"
    if expression.endswith("い") and not expression.startswith("～"):
        return "Adjective"
    return "Unknown"


def infer_spanish_level(row: dict[str, str]) -> Optional[str]:
    """
    Frekvensheuristik:
    - Beräkna viktad tyngdpunkt över nivåerna A1..C1 (från level_freq@*)
    - Jämför med toppnivå (max frekvens)
    - Om toppnivån dominerar tydligt (>=45% av total frekvens), välj toppen,
      annars välj närmaste nivå till tyngdpunkten.
    """
    nivåer = ["A1", "A2", "B1", "B2", "C1"]
    vikter = {n: i + 1 for i, n in enumerate(nivåer)}
    värden: dict[str, float] = {}
    for n in nivåer:
        raw = row.get(f"level_freq@{n.lower()}", "0")
        try:
            värden[n] = float(raw or 0)
        except ValueError:
            värden[n] = 0.0
    total = sum(värden.values())
    if total <= 0:
        return None

    topp = max(värden, key=värden.get)
    dominans = värden[topp] / total

    score = sum(vikter[n] * v for n, v in värden.items()) / total
    närmast = round(score)
    närmast = min(5, max(1, närmast))
    score_nivå = nivåer[närmast - 1]

    return topp if dominans >= 0.45 else score_nivå


def parse_english_oxford() -> Iterable[LexemRad]:
    p = NIVALISTOR / "oxford5000.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        iterator = data.values()
    else:
        iterator = data

    for item in iterator:
        # Oxford5000 ligger som [{"id": ..., "value": {...}}], Oxford3000 som dict values.
        payload = item.get("value", item) if isinstance(item, dict) else {}
        lemma = normalisera_lemma(payload.get("word", ""))
        nivå = normalisera_cefr(payload.get("level", payload.get("cefr", "")))
        ordklass = map_pos_common(payload.get("type", ""))
        if lemma and nivå in ALLOWED_CEFR_LEVELS:
            yield LexemRad(lemma, "en", ordklass, nivå, p.name)


def parse_french_flelex() -> Iterable[LexemRad]:
    p = NIVALISTOR / "FleLex_TT_Beacco.tsv"
    with p.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            lemma = normalisera_lemma(row.get("word", ""))
            nivå = normalisera_cefr(row.get("level", ""))
            ordklass = map_pos_common(row.get("tag", ""))
            if lemma and nivå in ALLOWED_CEFR_LEVELS_FR_ES:
                yield LexemRad(lemma, "fr", ordklass, nivå, p.name)


def parse_spanish_elelex() -> Iterable[LexemRad]:
    p = NIVALISTOR / "ELELex.tsv"
    with p.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            lemma = normalisera_lemma(row.get("word", ""))
            nivå = infer_spanish_level(row)
            ordklass = map_pos_common(row.get("tag", ""))
            if lemma and nivå in ALLOWED_CEFR_LEVELS_FR_ES:
                yield LexemRad(lemma, "es", ordklass, nivå, p.name)


def parse_italian_xls() -> Iterable[LexemRad]:
    p = NIVALISTOR / "it_m3.xls"
    wb = xlrd.open_workbook(str(p))
    sh = wb.sheet_by_index(0)
    idx = {str(sh.cell_value(0, c)).strip().lower(): c for c in range(sh.ncols)}
    c_lemma = idx.get("lemma")
    c_pos = idx.get("pos")
    c_level = idx.get("points")
    if c_lemma is None or c_pos is None or c_level is None:
        raise ValueError("it_m3.xls: saknar förväntade kolumner Lemma/Pos/Points")

    for r in range(1, sh.nrows):
        lemma_raw = str(sh.cell_value(r, c_lemma)).strip()
        pos_raw = str(sh.cell_value(r, c_pos)).strip()
        level_raw = str(sh.cell_value(r, c_level)).strip()
        nivå = normalisera_cefr(level_raw)
        ordklass = map_pos_common(pos_raw)
        if nivå not in ALLOWED_CEFR_LEVELS:
            continue
        for bit in lemma_raw.split(","):
            lemma = normalisera_lemma(bit)
            if lemma:
                yield LexemRad(lemma, "it", ordklass, nivå, p.name)


def parse_swedish_kelly() -> Iterable[LexemRad]:
    p = NIVALISTOR / "Swedish-Kelly_M3_CEFR.xls"
    wb = xlrd.open_workbook(str(p))
    sh = wb.sheet_by_name("Swedish_M3_CEFR")
    headers = [str(sh.cell_value(0, c)).strip().lower().replace("\n", " ") for c in range(sh.ncols)]

    def find_col(needle: str) -> int:
        for i, h in enumerate(headers):
            if needle in h:
                return i
        raise ValueError(f"Swedish-Kelly_M3_CEFR.xls: kunde inte hitta kolumn '{needle}'")

    c_level = find_col("cefr")
    c_word = find_col("swedish items")
    c_pos = find_col("word classes")

    for r in range(1, sh.nrows):
        lemma_raw = str(sh.cell_value(r, c_word)).strip()
        pos_raw = str(sh.cell_value(r, c_pos)).strip()
        level_raw = str(sh.cell_value(r, c_level)).strip()
        nivå = normalisera_cefr(level_raw)
        if nivå not in ALLOWED_CEFR_LEVELS:
            continue
        ordklass = map_pos_common(pos_raw)

        # Vissa rader har alternativ inom parentes.
        lemma_raw = re.sub(r"\(.*?\)", "", lemma_raw).strip()
        for bit in lemma_raw.split(","):
            lemma = normalisera_lemma(bit)
            if lemma:
                yield LexemRad(lemma, "sv", ordklass, nivå, p.name)


def parse_japanese_jlpt() -> Iterable[LexemRad]:
    for level_file in ["n5.csv", "n4.csv", "n3.csv", "n2.csv"]:
        p = NIVALISTOR / level_file
        nivå = normalisera_jlpt(level_file.upper())  # ger N5/N4/...
        with p.open(encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                lemma = normalisera_lemma(row.get("expression", ""))
                if not lemma or not nivå:
                    continue
                ordklass = infer_japanese_pos(row.get("expression", ""), row.get("meaning", ""))
                yield LexemRad(lemma, "ja", ordklass, nivå, p.name)


def parse_german_cefr_vocab() -> Iterable[LexemRad]:
    p = NIVALISTOR / "cefr_vocab.csv"
    with p.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            nivå = normalisera_cefr(row.get("level", ""))
            lemma = normalisera_lemma(row.get("lemma", "") or row.get("word", ""))
            if lemma and nivå in ALLOWED_CEFR_LEVELS:
                # Källan saknar robust POS, så vi bevarar Unknown här och infererar senare i länkningssteget.
                yield LexemRad(lemma, "de", "Unknown", nivå, p.name)


def deduplicera(rader: Iterable[LexemRad]) -> list[LexemRad]:
    """
    Dedupe på (språk, lemma, ordklass) och behåll lägsta nivå.
    CEFR och JLPT hålls isär via respektive ordningskartor.
    """
    best: dict[tuple[str, str, str], LexemRad] = {}
    for rad in rader:
        key = (rad.språk, rad.lemma, rad.ordklass)
        old = best.get(key)
        if old is None:
            best[key] = rad
            continue

        order = CEFR_ORDER if rad.nivå in CEFR_ORDER else JP_ORDER
        old_v = order.get(old.nivå, 999)
        new_v = order.get(rad.nivå, 999)
        if new_v < old_v:
            best[key] = rad
    return sorted(best.values(), key=lambda x: (x.språk, x.nivå, x.ordklass, x.lemma))


def skriv_db(rader: list[LexemRad]) -> None:
    if OUT_DB.exists():
        OUT_DB.unlink()
    db = sqlite3.connect(OUT_DB)
    db.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE lexem_niva (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            language TEXT NOT NULL,
            pos TEXT NOT NULL,
            level TEXT NOT NULL,
            source TEXT NOT NULL
        );
        CREATE INDEX idx_lexem_niva_lang ON lexem_niva(language);
        CREATE INDEX idx_lexem_niva_level ON lexem_niva(level);
        CREATE INDEX idx_lexem_niva_pos ON lexem_niva(pos);
        """
    )
    db.executemany(
        "INSERT INTO lexem_niva (lemma, language, pos, level, source) VALUES (?, ?, ?, ?, ?)",
        [(r.lemma, r.språk, r.ordklass, r.nivå, r.källa) for r in rader],
    )
    db.commit()
    db.close()


def skriv_csv_jsonl(rader: list[LexemRad]) -> None:
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lemma", "language", "pos", "level", "source"])
        for r in rader:
            w.writerow([r.lemma, r.språk, r.ordklass, r.nivå, r.källa])

    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for r in rader:
            f.write(
                json.dumps(
                    {
                        "lemma": r.lemma,
                        "language": r.språk,
                        "pos": r.ordklass,
                        "level": r.nivå,
                        "source": r.källa,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def print_statistik(rader: list[LexemRad]) -> None:
    print("\nStatistik")
    print("=========")
    print("Totalt lexem:", len(rader))

    per_lang: dict[str, int] = {}
    unknown_pos: dict[str, int] = {}
    for r in rader:
        per_lang[r.språk] = per_lang.get(r.språk, 0) + 1
        if r.ordklass == "Unknown":
            unknown_pos[r.språk] = unknown_pos.get(r.språk, 0) + 1

    print("Per språk:")
    for lang in sorted(per_lang):
        print(f"  {lang}: {per_lang[lang]}")
    print("Unknown ordklass per språk:")
    for lang in sorted(per_lang):
        print(f"  {lang}: {unknown_pos.get(lang, 0)}")


def main() -> None:
    alla = []
    alla.extend(parse_swedish_kelly())
    alla.extend(parse_english_oxford())
    alla.extend(parse_french_flelex())
    alla.extend(parse_spanish_elelex())
    alla.extend(parse_italian_xls())
    alla.extend(parse_japanese_jlpt())
    alla.extend(parse_german_cefr_vocab())

    rader = deduplicera(alla)
    skriv_db(rader)
    skriv_csv_jsonl(rader)
    print_statistik(rader)
    print("\nKlart.")
    print("Skapade filer:")
    print(f"  - {OUT_DB}")
    print(f"  - {OUT_CSV}")
    print(f"  - {OUT_JSONL}")


if __name__ == "__main__":
    main()
