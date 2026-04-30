"""
importera_bas.py
════════════════
Läser ordbok/nivålistor/bas_kärna.csv och lägger in Koncept + Lexem
direkt i ordbok/ord.db.

Körning:
    python3 ordbok/importera_bas.py

Scriptet är idempotent — säkert att köra flera gånger.
"""

import csv
import sqlite3
from pathlib import Path

# ── Sökvägar ──────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent
DB_PATH      = SCRIPT_DIR / "ord.db"
CSV_PATH     = SCRIPT_DIR / "nivålistor" / "bas_kärna.csv"


# ── Konceptnivå-metadata ──────────────────────────────────────────────────────
# Fält som inte finns i CSV:n utan hör till Koncept-tabellen.
# person      : grammatisk person (pronomen)
# valens      : bitmask (Valens-flaggor)   1=Intransitiv 2=Transitiv 4=Ditransitiv 8=Reflexiv 16=Kopula
# personlighet: bitmask                    1=Personlig   2=Opersonlig
# (numerus borttaget — finns ej i Koncept-tabellen i ord.db)

KONCEPT_META: dict[str, dict] = {
    # ── Personliga pronomen ────────────────────────────────────────────────
    "pronomen_1sg":          {"person": 1},
    "pronomen_2sg":          {"person": 2},
    "pronomen_2sg_formal":   {"person": 2},
    "pronomen_3sg_mask":     {"person": 3},
    "pronomen_3sg_fem":      {"person": 3},
    "pronomen_3sg_neutr":    {"person": 3},
    "pronomen_1pl":          {"person": 1},
    "pronomen_2pl":          {"person": 2},
    "pronomen_3pl":          {"person": 3},
    "pronomen_reflexiv":     {"person": 3},   # reflexivt — alltid 3:e person som form

    # ── Demonstrativa ──────────────────────────────────────────────────────
    # Inga extra fält; genus/numerus-böjning hanteras i Former

    # ── Kopulaverb ────────────────────────────────────────────────────────
    "verb_vara":   {"valens": 16, "personlighet": 1},   # KOPULA | PERSONLIG
    "verb_ha":     {"valens":  2, "personlighet": 1},   # TRANSITIV | PERSONLIG
    "verb_bli":    {"valens": 16, "personlighet": 1},   # KOPULA | PERSONLIG
    "verb_finnas": {"valens":  1, "personlighet": 2},   # INTRANSITIV | OPERSONLIG

    # ── Modala hjälpverb ──────────────────────────────────────────────────
    # Transitiv (valens=2): öppnar infinitivlucka / komplement
    "modal_kan":    {"valens": 2},
    "modal_ska":    {"valens": 2},
    "modal_måste":  {"valens": 2},
    "modal_bör":    {"valens": 2},
    "modal_vill":   {"valens": 2},
    "modal_får":    {"valens": 2},
    "modal_brukar": {"valens": 2},
    "modal_torde":  {"valens": 2},
}


# ── Hjälpfunktioner ───────────────────────────────────────────────────────────

def läs_csv(path: Path) -> list[dict]:
    """Läser CSV-filen och hoppar över kommentarrader (#) samt tomma rader."""
    rader = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(
            (rad for rad in f if not rad.lstrip().startswith("#") and rad.strip()),
            fieldnames=["koncept", "ordklass", "nivå", "språk", "lemma"],
        )
        for rad in reader:
            if rad["koncept"] == "koncept":   # hoppa över header-raden om den slunkit igenom
                continue
            rader.append(rad)
    return rader


def samla_koncept(rader: list[dict]) -> dict[str, dict]:
    """
    Returnerar ett dict keyed på konceptnamn.
    Värdet är: {"ordklass": str, "nivå": str}
    Nivå = lägsta nivå bland alla lexem (A1 < A2 < B1 < B2 < C1 < C2).
    """
    NIVÅ_ORDNING = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}

    koncept: dict[str, dict] = {}
    for rad in rader:
        namn = rad["koncept"].strip()
        if not namn:
            continue
        nivå = rad["nivå"].strip()
        if namn not in koncept:
            koncept[namn] = {"ordklass": rad["ordklass"].strip(), "nivå": nivå}
        else:
            # behåll lägsta nivå
            if NIVÅ_ORDNING.get(nivå, 99) < NIVÅ_ORDNING.get(koncept[namn]["nivå"], 99):
                koncept[namn]["nivå"] = nivå
    return koncept


# ── Importlogik ───────────────────────────────────────────────────────────────

def importera(db_path: Path, csv_path: Path) -> None:
    rader = läs_csv(csv_path)
    koncept_info = samla_koncept(rader)

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    cur = con.cursor()

    nya_koncept  = 0
    nya_lexem    = 0
    dubbla_koncept = 0
    dubbla_lexem   = 0

    # ── Steg 1: sätt in Koncept ───────────────────────────────────────────
    for namn, info in koncept_info.items():
        meta = KONCEPT_META.get(namn, {})

        # Kontrollera om konceptet redan finns
        cur.execute("SELECT id FROM Koncept WHERE namn = ?", (namn,))
        befintlig = cur.fetchone()

        if befintlig:
            dubbla_koncept += 1
            continue

        cur.execute(
            """
            INSERT INTO Koncept (namn, ordklass, valens, personlighet, person)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                namn,
                info["ordklass"],
                meta.get("valens"),
                meta.get("personlighet"),
                meta.get("person"),
            ),
        )
        nya_koncept += 1

    con.commit()

    # Bygg en cache: konceptnamn → id
    cur.execute("SELECT namn, id FROM Koncept")
    koncept_id_cache: dict[str, int] = dict(cur.fetchall())

    # ── Steg 2: sätt in Lexem ─────────────────────────────────────────────
    for rad in rader:
        namn  = rad["koncept"].strip()
        språk = rad["språk"].strip()
        lemma = rad["lemma"].strip()
        nivå  = rad["nivå"].strip()

        if not namn or not lemma:
            continue

        koncept_id = koncept_id_cache.get(namn)
        if koncept_id is None:
            print(f"  VARNING: koncept '{namn}' saknas i databasen — hoppar över lexem '{lemma}'")
            continue

        # Kontrollera om lexemet redan finns (koncept_id + språk + lemma = unik rad)
        cur.execute(
            "SELECT id FROM Lexem WHERE koncept_id = ? AND språk = ? AND lemma = ?",
            (koncept_id, språk, lemma),
        )
        if cur.fetchone():
            dubbla_lexem += 1
            continue

        cur.execute(
            "INSERT INTO Lexem (koncept_id, språk, lemma, nivå) VALUES (?, ?, ?, ?)",
            (koncept_id, språk, lemma, nivå),
        )
        nya_lexem += 1

    con.commit()
    con.close()

    # ── Rapport ───────────────────────────────────────────────────────────
    print(f"\n✅  Import klar")
    print(f"    Nya Koncept   : {nya_koncept:>6}  (redan i DB: {dubbla_koncept})")
    print(f"    Nya Lexem     : {nya_lexem:>6}  (redan i DB: {dubbla_lexem})")
    print(f"    Källa         : {csv_path}")
    print(f"    Databas       : {db_path}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Databasen hittades inte: {DB_PATH}")
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV-filen hittades inte: {CSV_PATH}")

    importera(DB_PATH, CSV_PATH)
