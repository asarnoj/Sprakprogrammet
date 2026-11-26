"""Läs rättningsspåren — vad användaren skrev, vad diffen såg, vad korten fick.

    python ordbok/verktyg/spår.py                 senaste meningarna
    python ordbok/verktyg/spår.py --språk fr      bara en kurs
    python ordbok/verktyg/spår.py --tysta         meningar som bedömde NOLL kort
    python ordbok/verktyg/spår.py --struktur      specarna grupperade, för granskning
    python ordbok/verktyg/spår.py --misstänkta    specar som ser semantiskt trasiga ut

TRE FRÅGOR VERKTYGET FINNS FÖR, och alla tre var obesvarbara innan `Spår`:

  1. "Jag gjorde massor av fel men `again` växte inte." — `--tysta` visar
     meningarna där ingen dom bokfördes, och `kortlägen` säger varför: kortet
     var undanhållet, skyddat, redan bedömt eller redan fällt idag.

  2. "Ibland krympte new/due." — samma sak sett från andra hållet: ett kort
     som bedömdes i mening 3 kan inte bedömas igen i mening 7 samma dygn, så
     senare meningar ser tomma ut fast de gjorde sitt jobb.

  3. "Ibland sätts det ihop väldigt konstiga meningar." — `--struktur` och
     `--misstänkta` läser `Mening.spec`, som ÄR den språkoberoende
     strukturen och alltid har lagrats. Det som saknades var att titta.

Verktyget SKRIVER INGENTING. Det läser en kopia av inlärardatabasen om
sökvägen pekar på den skarpa, så att en analys aldrig kan röra kursen.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kort.db import STANDARD_KORT_DB            # noqa: E402

#: Läget → hur det ska läsas. Ordningen är den i `registrera_mening`.
LÄGEN = {
    "bedömd":       "fick en dom",
    "undanhållen":  "diffen kunde inte knyta felet till kortet (D3)",
    "skyddad":      "ordkortet fallerade, formen prövades aldrig (E5)",
    "redan_bedömd": "redan bedömt rätt idag — en dom per kort och dygn (E2)",
    "redan_fälld":  "redan fällt idag — felet är sant men bokförs inte igen",
}


def _öppna(sökväg: Path) -> sqlite3.Connection:
    """Läs en KOPIA om det är den skarpa databasen. En analys får inte röra kursen."""
    if sökväg == STANDARD_KORT_DB:
        kopia = Path(tempfile.mkdtemp()) / "läskopia.db"
        shutil.copy(sökväg, kopia)
        sökväg = kopia
    conn = sqlite3.connect(f"file:{sökväg}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _spec_form(spec: dict) -> str:
    """Specens FORM — vilka slots som är fyllda, utan att bry sig om vilka ord.

    Det är den nivån konstiga meningar går att gruppera på: "verb + subjekt +
    objekt" säger ingenting, men samma form med samma verb om och om igen
    säger vad generatorn fastnat i.
    """
    delar = [k for k in ("subjekt", "objekt", "io", "predikativ", "komplement",
                         "bisats", "fråga_om") if spec.get(k)]
    if spec.get("adverbial"):
        delar.append(f"adverbial×{len(spec['adverbial'])}")
    for flagga in ("negerad", "fråga"):
        if spec.get(flagga):
            delar.append(flagga)
    for axel in ("tid", "aspekt", "modus", "diates"):
        v = spec.get(axel)
        if v and v not in ("nutid", "imperfektiv", "indikativ", "aktiv"):
            delar.append(f"{axel}={v}")
    return " + ".join(delar) or "bara verb"


def _misstänkt(spec: dict) -> str | None:
    """Ser specen semantiskt trasig ut? Returnerar skälet, annars None.

    REGLERNA ÄR AVSIKTLIGT FÅ OCH GROVA. Det här är inte en semantikmodell
    utan ett såll som lyfter fram kandidater för mänsklig granskning — och
    varje regel här är en restriktion som SAKNAS i `Attributkrav`/mönstren.
    Flyttar en regel dit ska den tas bort härifrån.
    """
    s, o, io = (spec.get(k) or {} for k in ("subjekt", "objekt", "io"))
    if s and o and s.get("koncept") == o.get("koncept"):
        # "Je m'ai" — jag har mig. Samma pronomen som subjekt och objekt är
        # koreferens, och den kräver ett reflexivt verb för att bli språk.
        return f"subjekt = objekt ({s['koncept']})"
    if s and io and s.get("koncept") == io.get("koncept"):
        return f"subjekt = indirekt objekt ({s['koncept']})"
    if o and io and o.get("koncept") == io.get("koncept"):
        return f"objekt = indirekt objekt ({o['koncept']})"
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", type=Path, default=STANDARD_KORT_DB)
    p.add_argument("--språk")
    p.add_argument("--antal", type=int, default=20)
    p.add_argument("--tysta", action="store_true",
                   help="bara meningar där inget kort fick en dom")
    p.add_argument("--struktur", action="store_true",
                   help="gruppera på specens form i stället för att lista")
    p.add_argument("--misstänkta", action="store_true",
                   help="bara specar som ser semantiskt trasiga ut")
    a = p.parse_args()

    conn = _öppna(a.db)
    if not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Spår'"
    ).fetchone():
        print("Databasen har ingen Spår-tabell än — anslut med programmet "
              "en gång så skapas den.", file=sys.stderr)
        return 1

    villkor = "WHERE m.språk = ?" if a.språk else ""
    argument = (a.språk,) if a.språk else ()
    rader = conn.execute(
        f"""SELECT m.id, m.tidpunkt, m.språk, m.text, m.spec, m.fel,
                   s.svar, s.anmärkningar, s.kortlägen
            FROM Mening m LEFT JOIN Spår s ON s.mening_id = m.id
            {villkor} ORDER BY m.id DESC""", argument).fetchall()

    if a.struktur or a.misstänkta:
        return _strukturvy(rader, a)
    return _spårvy(rader, a)


def _spårvy(rader, a) -> int:
    visade = 0
    for r in rader:
        lägen = json.loads(r["kortlägen"]) if r["kortlägen"] else []
        bedömda = [l for l in lägen if l["läge"] == "bedömd"]
        if a.tysta and bedömda:
            continue
        if visade >= a.antal:
            break
        visade += 1
        print(f"\n─── #{r['id']}  {r['tidpunkt'][:16].replace('T',' ')}  "
              f"{r['språk']} " + "─" * 30)
        print(f"  facit  {r['text']}")
        print(f"  svar   {r['svar'] if r['svar'] is not None else '(ej spårat)'}")
        for anm in json.loads(r["anmärkningar"] or "[]"):
            osäker = "  ~osäker" if anm.get("osäker") else ""
            print(f"    fel  skrev {anm['skrev']!r} väntat {anm['väntat']!r}"
                  f"  → {anm.get('slutsats') or anm.get('nyckel')}{osäker}")
        if not lägen:
            print("    (inget spår — meningen är äldre än Spår-tabellen)")
        for l in lägen:
            dom = {True: "rätt", False: "FEL", None: "—"}[l["rätt"]]
            print(f"    {l.get('typ','?'):<9} {str(l.get('facit'))[:18]:<18} "
                  f"{dom:<5} {l['läge']}")
        if lägen and not bedömda:
            print(f"    ⚠ INGEN dom bokfördes — {len(lägen)} kort, alla utanför "
                  f"bedömningen")
    if not visade:
        print("Inga meningar matchade.")
    else:
        print(f"\n{visade} meningar. Läget betyder:")
        for k, v in LÄGEN.items():
            print(f"  {k:<14} {v}")
    return 0


def _strukturvy(rader, a) -> int:
    """Specarna grupperade — för att se VAD generatorn bygger, inte hur det gick."""
    former: Counter = Counter()
    misstänkta: list[tuple] = []
    for r in rader:
        spec = json.loads(r["spec"])
        skäl = _misstänkt(spec)
        if skäl:
            misstänkta.append((r, skäl))
        if not a.misstänkta:
            former[(spec.get("verb"), _spec_form(spec))] += 1

    if a.misstänkta:
        for r, skäl in misstänkta[:a.antal]:
            print(f"  #{r['id']:<5} {r['språk']}  {r['text']:<34} ⚠ {skäl}")
        print(f"\n{len(misstänkta)} av {len(rader)} meningar ser semantiskt "
              f"trasiga ut.")
        print("Varje rad är en restriktion som saknas i mönstren — se C4/C8.")
        return 0

    print(f"{'antal':>6}  {'verb':<18} form")
    for (verb, form), n in former.most_common(a.antal):
        print(f"{n:>6}  {str(verb):<18} {form}")
    print(f"\n{len(former)} olika (verb, form)-kombinationer över "
          f"{sum(former.values())} meningar.")
    if misstänkta:
        print(f"⚠ {len(misstänkta)} av dem ser semantiskt trasiga ut — "
              f"kör med --misstänkta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
