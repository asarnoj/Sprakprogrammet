"""Taggning av Koncept och Mönster via LLM.

Två jobb som båda skriver SQL-migrationer i stället för att bara röra
databasen direkt. Skälet är projektets egen konvention: `ordbok import
--återinitiera` bygger om databasen från CSV och tappar all taggning, så
taggningen måste finnas som en fil att köra om (jfr semantik.sql,
valens.sql). Filerna är dessutom granskningsbara och diffbara i git.

`tagga-koncept`  — fyller luckorna på Koncept: gradbarhet (kan adjektivet
                   kompareras?), räknebar (tar substantivet obestämd
                   artikel?), valens för modalverben, semantik där den
                   saknas.

`tagga-monster`  — bygger Mönster + MönsterKrav för verben: vilka slots ett
                   verb kräver och vilken semantisk kategori som får fylla
                   dem. Det är det som hindrar "boken gav idén en röd bror".

Båda kör bara UNIVERSELLA mönster (Mönster.språk = NULL). Språkspecifik
kasusrektion och prepositionsrealisering (MönsterKrav.kasus,
preposition_koncept_id) är ett andra pass — kolumnerna finns, men att fylla
dem kräver per-språk-kunskap som hör till renderarfasen.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .pipeline import _anropa_llm

STANDARD_TAGGNINGSMODELL = "claude-opus-5"

SEMANTIK = {
    "ANIMAT": 1, "KONKRET": 2, "ABSTRAKT": 4, "ÄTBAR": 8, "PLATS": 16,
    "MÄNSKLIG": 32, "RÖRELSE": 64, "RIKTNING": 128, "HÄNDELSE": 256,
    "TID": 512, "INSTRUMENT": 1024, "KOMMUNIKAT": 2048,
    "DRICKBAR": 4096, "KROPPSDEL": 8192, "KLÄDESPLAGG": 16384,
    "INREDNING": 32768, "NATURFENOMEN": 65536,
}
FRASTYP = {
    "Nominalfras": 1, "Adjektivfras": 2, "Prepositionsfras": 4,
    "Adverbfras": 8, "Infinitivfras": 16, "Bisatsfras": 32,
}
VALENS = {"Intransitiv": 1, "Transitiv": 2, "Ditransitiv": 4,
          "Reflexiv": 8, "Kopula": 16}
SLOTS = ("subjekt", "objekt", "io", "predikativ",
         "komplement", "adverbial", "preposition", "kommunikat")

_SEMANTIK_LISTA = "\n".join(f"  {v:>4} {k}" for k, v in SEMANTIK.items())


@dataclass
class Taggningsstatistik:
    behandlade: int = 0
    satta_värden: int = 0
    fel: list[str] = field(default_factory=list)

    def skriv_ut(self) -> None:
        print(f"Koncept behandlade : {self.behandlade}")
        print(f"Värden satta       : {self.satta_värden}")
        if self.fel:
            print(f"Fel ({len(self.fel)}):")
            for f in self.fel[:10]:
                print(f"  {f}")
            if len(self.fel) > 10:
                print(f"  ... och {len(self.fel) - 10} till")


def _sql_sträng(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _batchar(rader: list, storlek: int):
    for i in range(math.ceil(len(rader) / storlek)):
        yield i + 1, math.ceil(len(rader) / storlek), rader[i * storlek:(i + 1) * storlek]


def _json_ur_svar(text: str) -> dict:
    start, slut = text.find("{"), text.rfind("}") + 1
    if start == -1 or slut == 0:
        raise ValueError("Inget JSON-block i svaret")
    return json.loads(text[start:slut])


# ── 1. Koncepttaggning ───────────────────────────────────────────────

def _bygg_konceptprompt(poster: list[sqlite3.Row]) -> str:
    rader = "\n".join(
        f"  {r['nyckel']}  [{r['ordklass']}]  sv={r['lemma']}"
        + (f"  en={r['en_lemma']}" if r["en_lemma"] else "")
        for r in poster
    )
    return f"""Du taggar koncept i en flerspråkig ordbok för ett språkinlärningsprogram.
Svara ENBART med giltig JSON.

Koncept att tagga:
{rader}

Sätt bara de fält som gäller ordklassen:

ADJEKTIV → "gradbar": true/false
  true om adjektivet kan kompareras med grad (stor–större–störst,
  intressant–mer intressant). false för absoluta adjektiv som inte tål
  gradering: död, gravid, gift, fyrkantig, daglig, huvudsaklig.
  Färger räknas som gradbara (rödare, mest röd).

SUBSTANTIV → "räknebar": true/false
  true om ordet kan stå i plural och ta obestämd artikel (en bok, tre böcker).
  false för massubstantiv och abstrakta oräknebara: mjölk, ris, snö, luft,
  vatten, salt, socker, smör, kött, blod, musik, tid, hälsa, makt.
  Ord som finns i båda betydelserna räknas som räknebara.

VERB → "valens": lista av "Intransitiv", "Transitiv", "Ditransitiv",
  "Reflexiv", "Kopula". Flera tillåtna. Modalverb (kan, ska, måste, bör,
  vill, får, brukar) tar infinitivkomplement → ["Transitiv"].

PRONOMEN → "semantik": lista av etiketter nedan.

Semantikbitar:
{_SEMANTIK_LISTA}

Returnera:
{{"koncept": {{"nyckel1": {{"gradbar": true}}, "nyckel2": {{"räknebar": false}}}}}}"""


def tagga_koncept(
    conn: sqlite3.Connection,
    migration: Path,
    *,
    antal: int | None = None,
    batch_storlek: int = 25,
    modell: str = STANDARD_TAGGNINGSMODELL,
    verbose: bool = False,
) -> Taggningsstatistik:
    """Fyll gradbarhet, räknebar, valens och semantik där de saknas."""
    stat = Taggningsstatistik()

    poster = conn.execute("""
        SELECT k.id, k.nyckel, k.ordklass,
               (SELECT lemma FROM Lexem WHERE koncept_id=k.id AND språk='sv' LIMIT 1) AS lemma,
               (SELECT lemma FROM Lexem WHERE koncept_id=k.id AND språk='en' LIMIT 1) AS en_lemma
        FROM Koncept k
        WHERE (k.ordklass = 'Adjektiv'    AND k.gradbarhet IS NULL)
           OR (k.ordklass = 'Substantiv'  AND k.räknebar   IS NULL)
           OR (k.ordklass = 'Verb'        AND k.valens     IS NULL)
           OR (k.ordklass = 'Pronomen'    AND k.semantik   IS NULL)
        ORDER BY k.ordklass, k.nyckel""").fetchall()

    if antal:
        poster = poster[:antal]

    if not poster:
        print("  Inget kvar att tagga på Koncept.")
        return stat

    satser: list[str] = []
    for nr, av, batch in _batchar(poster, batch_storlek):
        if verbose:
            print(f"  Batch {nr}/{av}: {len(batch)} koncept")
        try:
            svar = _json_ur_svar(_anropa_llm(_bygg_konceptprompt(batch), modell))
        except Exception as e:
            stat.fel.append(f"Batch {nr}: {e}")
            continue

        per_nyckel = svar.get("koncept", {})
        for r in batch:
            data = per_nyckel.get(r["nyckel"])
            if not isinstance(data, dict):
                stat.fel.append(f"Inget svar för {r['nyckel']}")
                continue
            stat.behandlade += 1

            if r["ordklass"] == "Adjektiv" and "gradbar" in data:
                v = "Gradbar" if data["gradbar"] else "Icke gradbar"
                satser.append(f"UPDATE Koncept SET gradbarhet = {_sql_sträng(v)} "
                              f"WHERE nyckel = {_sql_sträng(r['nyckel'])};")
                stat.satta_värden += 1
            elif r["ordklass"] == "Substantiv" and "räknebar" in data:
                satser.append(f"UPDATE Koncept SET räknebar = {1 if data['räknebar'] else 0} "
                              f"WHERE nyckel = {_sql_sträng(r['nyckel'])};")
                stat.satta_värden += 1
            elif r["ordklass"] == "Verb" and data.get("valens"):
                bits = sum(VALENS.get(x, 0) for x in data["valens"])
                if bits:
                    satser.append(f"UPDATE Koncept SET valens = {bits} "
                                  f"WHERE nyckel = {_sql_sträng(r['nyckel'])};")
                    stat.satta_värden += 1
            elif r["ordklass"] == "Pronomen" and data.get("semantik"):
                bits = sum(SEMANTIK.get(x, 0) for x in data["semantik"])
                if bits:
                    satser.append(f"UPDATE Koncept SET semantik = {bits} "
                                  f"WHERE nyckel = {_sql_sträng(r['nyckel'])};")
                    stat.satta_värden += 1

    if satser:
        migration.write_text(
            "/* ── koncepttaggning — gradbarhet, räknebar, valens, semantik ───────\n"
            "   Genererad av `ordbok tagga-koncept`. Granskas av Julius.\n"
            "   KÖRS EFTER VARJE `ordbok import`.\n"
            "   ──────────────────────────────────────────────────────────────── */\n\n"
            + "\n".join(satser) + "\n",
            encoding="utf-8",
        )
        with conn:
            conn.executescript("\n".join(satser))
        print(f"  → {migration} ({len(satser)} UPDATE-satser, körda mot databasen)")

    return stat


# ── 2. Mönstertaggning ───────────────────────────────────────────────

def _bygg_monsterprompt(poster: list[sqlite3.Row]) -> str:
    rader = "\n".join(
        f"  {r['nyckel']}  sv={r['lemma']}  en={r['en_lemma'] or '?'}"
        f"  valens={r['valens'] or '?'}"
        for r in poster
    )
    return f"""Du bygger valensmönster för verb i ett språkinlärningsprogram.
Svara ENBART med giltig JSON.

För varje verb: vilka satsdelar KRÄVER det, och vilken semantisk kategori
måste fylla dem? Syftet är att generatorn aldrig ska kunna bygga meningar
som "boken gav idén en röd bror".

Verb att beskriva:
{rader}

Slots: subjekt, objekt, io (indirekt objekt), predikativ, komplement,
adverbial, kommunikat.

Semantikbitar (välj de som KRÄVS — flera tillåtna, tolkas som "måste ha
alla dessa"):
{_SEMANTIK_LISTA}

Frastyper: Nominalfras, Adjektivfras, Prepositionsfras, Adverbfras,
Infinitivfras, Bisatsfras.

Regler:
- Ta bara med slots som verbet KRÄVER, inte valfria tillägg. "springa" har
  bara subjekt; "på gatan" är ett fritt adverbial och ska inte med.
- Håll semantikkraven MINIMALA. Ett för snävt krav gör att inga meningar
  kan byggas. "äta" kräver ÄTBAR på objektet — men "ge" kräver bara att
  objektet är KONKRET, inte att det är ett INSTRUMENT.
- ÄTBAR och DRICKBAR är skilda: "äta" kräver ÄTBAR, "dricka" kräver
  DRICKBAR. Vatten och öl har bara DRICKBAR, bröd bara ÄTBAR, soppa båda.
- Subjekt för handlingsverb är oftast ANIMAT. För verb som beskriver
  händelser eller tillstånd (regna, finnas, kosta) kan subjektet vara
  vad som helst — utelämna då semantikkravet med "tagg": [].
- io (indirekt objekt) är nästan alltid ANIMAT.
- Modalverb och hjälpverb (kan, ska, måste, bör, vill, får, brukar) tar ett
  komplement med frastyp Infinitivfras.
- Kopulaverb (vara, bli, verka) tar predikativ med Adjektivfras+Nominalfras.

Returnera:
{{"verb": {{
  "fys_ge": [
    {{"slot": "subjekt", "tagg": ["ANIMAT"], "frastyp": ["Nominalfras"]}},
    {{"slot": "io", "tagg": ["ANIMAT"], "frastyp": ["Nominalfras"]}},
    {{"slot": "objekt", "tagg": ["KONKRET"], "frastyp": ["Nominalfras"]}}
  ]
}}}}"""


def tagga_monster(
    conn: sqlite3.Connection,
    migration: Path,
    *,
    antal: int | None = None,
    koncept: list[str] | None = None,
    batch_storlek: int = 10,
    modell: str = STANDARD_TAGGNINGSMODELL,
    verbose: bool = False,
) -> Taggningsstatistik:
    """Bygg universella Mönster + MönsterKrav för alla verbkoncept."""
    stat = Taggningsstatistik()

    poster = conn.execute("""
        SELECT k.id, k.nyckel, k.valens,
               (SELECT lemma FROM Lexem WHERE koncept_id=k.id AND språk='sv' LIMIT 1) AS lemma,
               (SELECT lemma FROM Lexem WHERE koncept_id=k.id AND språk='en' LIMIT 1) AS en_lemma
        FROM Koncept k
        WHERE k.ordklass = 'Verb'
          AND NOT EXISTS (SELECT 1 FROM Mönster m WHERE m.koncept_id = k.id)
        ORDER BY k.nyckel""").fetchall()

    if koncept:
        valda = set(koncept)
        poster = [r for r in poster if r["nyckel"] in valda]
    if antal:
        poster = poster[:antal]

    if not poster:
        print("  Alla verb har redan mönster.")
        return stat

    satser: list[str] = []
    for nr, av, batch in _batchar(poster, batch_storlek):
        if verbose:
            print(f"  Batch {nr}/{av}: {', '.join(r['nyckel'] for r in batch)}")
        try:
            svar = _json_ur_svar(_anropa_llm(_bygg_monsterprompt(batch), modell))
        except Exception as e:
            stat.fel.append(f"Batch {nr}: {e}")
            continue

        per_verb = svar.get("verb", {})
        for r in batch:
            krav = per_verb.get(r["nyckel"])
            if not isinstance(krav, list) or not krav:
                stat.fel.append(f"Inget mönster för {r['nyckel']}")
                continue
            stat.behandlade += 1

            nyckel = _sql_sträng(r["nyckel"])
            satser.append(
                f"INSERT INTO Mönster (koncept_id, språk) "
                f"SELECT id, NULL FROM Koncept WHERE nyckel = {nyckel};"
            )
            for k in krav:
                slot = k.get("slot")
                if slot not in SLOTS:
                    continue
                tagg = sum(SEMANTIK.get(x, 0) for x in k.get("tagg") or [])
                frastyp = sum(FRASTYP.get(x, 0) for x in k.get("frastyp") or [])
                # tagg=NULL betyder "slotten krävs, utan innehållsbegränsning".
                # Nödvändigt för verb vars subjekt kan vara vad som helst
                # (regna, kosta, finnas) — slotten får INTE hoppas över, då
                # skulle mönstret sluta kräva ett subjekt.
                satser.append(
                    f"INSERT INTO MönsterKrav (mönster_id, slot, tagg, frastyp) "
                    f"SELECT m.id, {_sql_sträng(slot)}, {tagg or 'NULL'}, "
                    f"{frastyp or 'NULL'} FROM Mönster m "
                    f"JOIN Koncept k ON k.id = m.koncept_id "
                    f"WHERE k.nyckel = {nyckel} AND m.språk IS NULL;"
                )
                stat.satta_värden += 1

    if satser:
        migration.write_text(
            "/* ── mönstertaggning — valensmönster för verb ───────────────────────\n"
            "   Genererad av `ordbok tagga-monster`. Granskas av Julius.\n"
            "   Endast universella mönster (språk = NULL). Språkspecifik\n"
            "   kasusrektion och prepositionsrealisering är ett andra pass —\n"
            "   kolumnerna finns i MönsterKrav men fylls inte här.\n"
            "   KÖRS EFTER VARJE `ordbok import`.\n"
            "   ──────────────────────────────────────────────────────────────── */\n\n"
            + "\n".join(satser) + "\n",
            encoding="utf-8",
        )
        with conn:
            conn.executescript("\n".join(satser))
        print(f"  → {migration} ({len(satser)} satser, körda mot databasen)")

    return stat
