"""Nät för kravens löfte — KÄRNAN 4.2 och 4.4.

> **Invarianten håller.** Kortet går att pröva när kravet är infört, och
> meningen sparas som dess bevis (3.10).

VARFÖR DET HÄR NÄTET FINNS. Kraven i `kartor/nivaer_en.json` var **falska**, och
ingenting sa det. Grinden (4.4) släpper upp en nivå när föregångarnas kort är
införda, alltså på kravens ord — och för elva av dag fyras trettiotvå köade kort
fanns ingen mening att bygga. Passet svarade då nej, uttömmande, varje dag:

    ord:räkn_1, bara kravet tillåtet ................  6 s
    ord:räkn_1, 70 införda tillåtna .................  82 s
    ord:räkn_1, 70 införda + 16 dagens valda ........  821 s

Nejets pris växer med den tillåtna mängden, så kön blev dyrare för varje kort
den fick. Dag fyras plan tog över nittiofyra minuter utan att bli klar.

TVÅ ORSAKER, mätta 2026-09-27:

1. **Nivåbygget körde utan språkpar.** Kraven var lästa ur meningar som
   «How much dog sees.» och «One mice see.». 4.2 kräver motsatsen: «Kraven
   räknas per språkpar … nivåerna är desamma för alla användare av samma kurs
   men inte för alla kurser med samma målspråk.» Verktyget tar nu
   `--källspråk`, filen bär paret, och passet vägrar en fil byggd för ett annat.
2. **Kartan var äldre än grammatiken** — `en.pkl` byggd 09-20 00:16, `sprak.db`
   ändrad 09-20 23:29, renderaren 09-20 och 09-21. Kraven beskrev meningar
   grammatiken inte längre byggde.

FRÅGAN NÄTET STÄLLER ÄR PASSETS EGEN, inte kravets. Nivå i prövas med alla kort
ur nivå 1…i tillåtna — grindens läge när nivån öppnas — plus nivåns egna som
lånekort, eftersom nivåns kort kräver varandra (4.1). Det är mer tillåtet än
kravet ensamt, alltså precis den fråga passet ställer, och ett ja kommer
billigt. Bara de äkta nejen är dyra, och dem vill vi hitta.

Kör:  python ordbok/verktyg/kravprov.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.avtryck import avtryck, skiljer                    # noqa: E402
from sprakprog.kortmodell import Kort                             # noqa: E402
from sprakprog.passet import SLUTNA_ORDKLASSER                    # noqa: E402
from sprakprog.rendering.karta import ladda                       # noqa: E402
from sprakprog.sammansattning import Sammansättare                # noqa: E402

KARTA = ROT / "kartor" / "en.pkl"
NIVÅER = ROT / "kartor" / "nivaer_en.json"


def _kort(rad) -> Kort:
    return Kort(rad[0], rad[1], tuple(rad[2]))


def _nivåfilen() -> dict:
    return json.loads(NIVÅER.read_text(encoding="utf-8"))


def _fritt(s: Sammansättare, minne: dict):
    """Passets egen regel (`Passet._fritt_ord`): ord ur en ÖPPEN ordklass.

    Familjen «ord» rymmer också `oregelbunden`, så «stood» är fritt fast det är
    ett eget kort. Skrevs villkoret som `typ == "ord"` föll
    `regel:val/tempusform/preteritum` som oprövbart, fast passet bygger
    «Tid stod.» utan vidare — provet mätte då sin egen stränghet.
    """
    def fritt(k: Kort) -> bool:
        if k.familj != "ord":
            return False
        if k.nyckel[0] not in minne:
            rad = s.u.conn.execute(
                "SELECT ordklass FROM Koncept WHERE nyckel = ?",
                (k.nyckel[0],)).fetchone()
            minne[k.nyckel[0]] = bool(
                rad and rad["ordklass"] not in SLUTNA_ORDKLASSER)
        return minne[k.nyckel[0]]
    return fritt


def _gå_igenom(nivåer: list[frozenset], par: str,
               rapport=None) -> list[str]:
    """Varje nivås kort, prövat med nivå 1…i tillåtna."""
    s = Sammansättare(sqlite3.connect(ROT / "sprak.db"), ladda(KARTA), par)
    fritt = _fritt(s, {})
    tillåtna: set[Kort] = set()
    brister: list[str] = []
    for i, nivån in enumerate(nivåer, 1):
        här = tillåtna | nivån
        for k in sorted(nivån, key=str):
            t0 = time.perf_counter()
            träff = s.finns(k, lambda x: x in här or fritt(x))
            if träff is None:
                brister.append(
                    f"nivå {i}: {k} går inte att införa när nivån öppnas — "
                    "grinden lovar mer än sökningen kan ge")
            if rapport:
                rapport(i, k, träff is not None, time.perf_counter() - t0)
        tillåtna = här
    return brister


def varje_kort_går_att_införa() -> list[str]:
    """Grinden (4.4) får inte släppa upp ett kort passet inte kan införa."""
    d = _nivåfilen()
    if not d.get("källspråk"):
        return [f"{NIVÅER.name} bär inget källspråk — kraven gäller per "
                "språkpar (4.2), och utan paret är de räknade för ingen kurs"]

    # ARTEFAKTERNA MÅSTE VARA BYGGDA UR NUVARANDE GRAMMATIK, annars prövar det
    # här nätet en annan version än den som körs. Det var precis så de falska
    # kraven kunde leva: kartan var byggd tjugotre timmar före `sprak.db`.
    nu = avtryck()
    brister = [f"{NIVÅER.name}: {rad}" for rad in skiljer(d.get("avtryck"), nu)]
    brister += [f"{KARTA.name}: {rad}"
                for rad in skiljer(ladda(KARTA).get("avtryck"), nu)]
    if brister:
        return brister

    def rapport(i, k, ja, dt):
        if not ja or dt > 20:
            print(f"      nivå {i:>3}  {dt:>7.1f} s  "
                  f"{'ja' if ja else 'GÅR INTE'}  {k}", flush=True)

    return _gå_igenom([frozenset(map(_kort, n)) for n in d["nivåer"]],
                      d["källspråk"], rapport)


PROV = [("varje kort går att införa när dess nivå öppnas",
         varje_kort_går_att_införa)]


def _falsifiera() -> list[str]:
    """En nivåordning som lovar för mycket ska fälla provet.

    Den sista nivån läggs först. Då står dess kort utan sina föregångare, och
    om provet inte märker det mäter det ingenting: det var precis så de falska
    kraven kunde leva — nivåerna öppnades i en ordning ingenting prövade.
    """
    d = _nivåfilen()
    nivåer = [frozenset(map(_kort, n)) for n in d["nivåer"]]
    kastad = [nivåer[-1]] + nivåer[:-1]
    print("\nfalsifiering — en ordning som lovar för mycket ska fällas:")
    fel = _gå_igenom(kastad, d.get("källspråk") or "sv")
    if fel:
        print(f"  ✓ föll  sista nivån först  ({fel[0][:70]}…)")
        return []
    print("  ✗ STUMT  sista nivån först")
    return ["provet vaktar inte ordningen — sista nivån först går igenom"]


def main() -> int:
    brister: list[str] = []
    for namn, fn in PROV:
        t0 = time.perf_counter()
        fel = fn()
        print(f"  {'✓' if not fel else '✗'} {namn}   "
              f"({time.perf_counter() - t0:.1f} s)")
        for b in fel:
            print(f"      {b}")
        brister += fel
    # FALSIFIERINGEN BARA NÄR KONTROLLEN HÖLL. Den kostar en egen genomgång av
    # alla nivåer, och mot en fallen kontroll säger den ingenting: är
    # artefakterna byggda ur en annan grammatik prövar båda svaren fel version.
    if not brister:
        brister += _falsifiera()
    print(f"\n{len(PROV)} kontroller, "
          + (f"{len(brister)} brister." if brister else "alla håller."))
    return 1 if brister else 0


if __name__ == "__main__":
    raise SystemExit(main())
