"""Hur ofta varje FORM används — KÄRNAN 5.6:s andra frekvens.

> Varje gång språket använder **ett ord i en viss form**, eller tillämpar en
> regel, är en användning. Den är täckt när alla kort den kräver är införda.

Två sorters frekvens behövs för införandeordningen, och bara den ena fanns.
`frekvensmätning.py` mäter KONCEPT — hur ofta ordet `bok` används, oavsett
form. Den här mäter ANVÄNDNINGAR: hur ofta `bok` används i just plural.

VARFÖR DET BEHÖVS. Utan den sjunker varje rent grammatiskt moment till
kursens slut, eftersom ett regelkort inte har någon ordfrekvens. Mätt på den
alfabetiska nivåordningen, omordnad efter enbart konceptfrekvens: preteritum
hamnade på nivå 127 av 164, frågeinversionen på 135 och substantivets plural
på 163. Man skulle lära sig hundratjugo gloser före dåtid.

Med formernas frekvenser summerade per cell blir bilden en annan, och den
stämmer med vad engelskan faktiskt är:

    15,2 %  Preposition/inv        3,8 %  Verb/pres_3sg
    10,0 %  Artikel/inv            3,7 %  Verb/pret
     8,7 %  Pronomen/nom           1,6 %  Substantiv/pl

KÄRNAN föreslår en korpus för det här — «trädbankerna i Universal
Dependencies». Det behövs inte: `wordfreq` mäter enskilda strängar, och en
form ÄR en sträng. «book» 66 % mot «books» 34 %, «is» 45 % mot «was» 25 %.
Mätningen blir dessutom densamma för alla sju språken utan handgjord
mappning mellan korpusens etiketter och våra kort.

TVÅ SORTERS DELNING, båda av samma skäl som i `frekvensmätning.py`: strängen
mäts en gång, och de som bär den delar på den.

1. **Samma sträng i flera celler av samma lexem.** Engelskans `read` är
   infinitiv, presens och preteritum. Räknades den en gång per cell skulle
   summan överstiga språket självt.
2. **Samma sträng i flera lexem.** `stand` är både substantiv och verb.

Resultatet skrivs som en tabell över ANVÄNDNINGAR — koncept, cell, andel —
och programmet läser tabellen, aldrig `wordfreq`. Biblioteket är ett verktyg
och inget beroende i kärnan.

Kör:  python ordbok/verktyg/användningsmätning.py [FIL]
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from wordfreq import available_languages, word_frequency

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.rendering.uppslag import Uppslag                   # noqa: E402

FIL = ROT / "ordbok" / "nivålistor" / "användningar.csv"


def _mätbar(språk: str) -> bool:
    """Japanskan kräver en egen tokeniserare (MeCab) och mäts utan den inte alls."""
    if språk not in available_languages():
        return False
    try:
        word_frequency("a", språk)
        return True
    except ImportError:
        return False


def _vikt(form: str, språk: str) -> float:
    """Formens frekvens. En fras mäts på sitt ovanligaste ord.

    Samma regel som `frekvensmätning._huvudord`: det vanliga ordet i en fras
    är ett funktionsord som säger mer om språket än om formen.
    """
    delar = form.split()
    if len(delar) > 1:
        return min(word_frequency(d, språk) for d in delar)
    return word_frequency(form, språk)


def mät(conn: sqlite3.Connection, språk: str) -> list[dict]:
    """Varje (koncept, cell) med sin andel av språkets uppmätta användning."""
    u = Uppslag(conn, språk)
    rader = conn.execute(
        """SELECT l.*, k.ordklass, k.roll, k.nyckel FROM Lexem l
           JOIN Koncept k ON k.id = l.koncept_id
           WHERE l.språk = ? ORDER BY l.id""", (språk,)).fetchall()

    #: sträng → de (koncept, ordklass, cell) som skriver den likadant
    bärare: dict[str, list[tuple]] = defaultdict(list)
    for rad in rader:
        for cell, form in u._celler(rad).items():
            if form:
                bärare[form.lower()].append((rad["nyckel"], rad["ordklass"], cell))

    rå: dict[tuple, float] = defaultdict(float)
    for form, platser in bärare.items():
        # Strängen mäts EN gång och delas mellan dem som bär den — annars
        # räknas `read` tre gånger och summan överstiger språket självt.
        delad = _vikt(form, språk) / len(platser)
        for plats in platser:
            rå[plats] += delad

    total = sum(rå.values())
    if not total:
        return []
    return sorted(
        ({"språk": språk, "koncept": k, "ordklass": ok, "cell": c,
          "andel": round(v / total, 8)} for (k, ok, c), v in rå.items()),
        key=lambda r: (-r["andel"], r["koncept"], r["cell"]))


def main() -> None:
    fil = Path(sys.argv[1]) if len(sys.argv) > 1 else FIL
    conn = sqlite3.connect(ROT / "sprak.db")
    conn.row_factory = sqlite3.Row
    språken = sorted({r[0] for r in conn.execute("SELECT DISTINCT språk FROM Lexem")})
    ut: list[dict] = []
    hoppade: list[str] = []
    for språk in språken:
        if not _mätbar(språk):
            hoppade.append(språk)
            continue
        rader = mät(conn, språk)
        ut += rader
        celler: dict[tuple, float] = defaultdict(float)
        for r in rader:
            celler[(r["ordklass"], r["cell"])] += r["andel"]
        tyngst = sorted(celler.items(), key=lambda x: -x[1])[:3]
        print(f"  {språk}: {len(rader)} användningar, {len(celler)} celler — "
              + ", ".join(f"{ok}/{c} {100*v:.1f} %" for (ok, c), v in tyngst))

    with fil.open("w", encoding="utf-8", newline="") as f:
        skrivare = csv.DictWriter(f, ["språk", "koncept", "ordklass", "cell", "andel"])
        skrivare.writeheader()
        skrivare.writerows(ut)
    print(f"\n{len(ut)} användningar sparade i {fil}")
    if hoppade:
        print(f"utan tokeniserare, och därför omätta: {', '.join(hoppade)}")


if __name__ == "__main__":
    main()
