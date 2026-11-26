"""Frekvens per koncept, mätt en gång och sparad (KÄRNAN 5.6, steg P2).

Införandeordningen ska följa hur ofta något används, och frekvensen hör till
KONCEPTET: `per_känna` och `per_lukta` är olika kort fast båda heter `sentir`.
`wordfreq` räknar däremot STRÄNGAR och vet ingenting om ordklass eller
betydelse — `zipf("får", "sv")` slår ihop fåret, «får» av «få» och modalverbet.
Uppdelningen är därför vår, och görs så här:

1. **Per språk delas lemmats frekvens mellan de koncept som bär det.** «that» är
   både demonstrativen och subjunktionen i engelskan, och då räknas ordet inte
   två gånger.
2. **Konceptets frekvens är MEDIANEN över de språk det finns i.** Ett ord som är
   tvetydigt i ett språk är sällan tvetydigt i de andra: «får» är uppblåst i
   svenskan, men `sheep`, `Schaf`, `mouton`, `oveja`, `pecora` och 羊 är det inte,
   och medianen rensar bort den uppblåsningen. Det är samma tanke som specen:
   konceptet är gemensamt för alla språk.
3. **Ett lemma med flera ord mäts på sitt ovanligaste ord**: «skynda sig» på
   «skynda», tyskans «nicht mögen» på «mögen». Det vanliga ordet i frasen är ett
   funktionsord som säger mer om språket än om konceptet.

Resultatet skrivs som en tabell. Programmet läser tabellen och aldrig
`wordfreq`, så biblioteket är ett verktyg och inget beroende i kärnan.

Kör:  python ordbok/verktyg/frekvensmätning.py [FIL]
"""

from __future__ import annotations

import csv
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

from wordfreq import available_languages, word_frequency

ROT = Path(__file__).resolve().parents[2]
FIL = ROT / "ordbok" / "nivålistor" / "frekvens.csv"


def _huvudord(lemma: str, språk: str) -> str:
    """Lemmats huvudord: frasens ovanligaste ord.

    «skynda sig» mäts på «skynda» och tyskans «nicht mögen» på «mögen». Det
    vanliga ordet i en fras är ett funktionsord som säger mer om språket än om
    konceptet, och det ovanliga är innehållsordet.
    """
    ord_ = lemma.split()
    return min(ord_, key=lambda o: word_frequency(o, språk)) if len(ord_) > 1 else lemma


def mät(conn: sqlite3.Connection) -> list[dict]:
    """Varje koncepts frekvens, som zipf: 6 är ett av tusen ord, 3 ett av en miljon."""
    conn.row_factory = sqlite3.Row
    rader = conn.execute(
        """SELECT k.nyckel, k.ordklass, k.nivå, l.språk, l.lemma FROM Koncept k
           JOIN Lexem l ON l.koncept_id = k.id ORDER BY k.nyckel, l.språk""").fetchall()
    # Japanskan kräver en egen tokeniserare (MeCab). Utan den mäts språket inte
    # alls, och medianen tas över de övriga.
    saknas: set[str] = set()
    språken = []
    for språk in sorted({r["språk"] for r in rader} & set(available_languages())):
        try:
            word_frequency("a", språk)
            språken.append(språk)
        except ImportError:
            saknas.add(språk)

    #: (språk, huvudord) → de koncept som bär ordet, för delningen
    bärare: dict[tuple, set] = defaultdict(set)
    for r in rader:
        if r["språk"] in språken:
            bärare[(r["språk"], _huvudord(r["lemma"], r["språk"]).lower())].add(r["nyckel"])

    per_koncept: dict[str, dict] = {}
    for r in rader:
        if r["språk"] not in språken:
            continue
        ord_ = _huvudord(r["lemma"], r["språk"])
        frekvens = word_frequency(ord_, r["språk"])
        delat = frekvens / len(bärare[(r["språk"], ord_.lower())])
        post = per_koncept.setdefault(r["nyckel"], {
            "koncept": r["nyckel"], "ordklass": r["ordklass"], "nivå": r["nivå"],
            "värden": {}})
        if delat > 0:
            post["värden"][r["språk"]] = delat

    ut = []
    for post in per_koncept.values():
        värden = post.pop("värden")
        post["språk"] = len(värden)
        post["zipf"] = round(math.log10(median(värden.values()) * 1e9), 2) if värden else 0.0
        ut.append(post)
    if saknas:
        print(f"utan tokeniserare, och därför omätta: {', '.join(sorted(saknas))}")
    return sorted(ut, key=lambda p: (-p["zipf"], p["koncept"]))


def main() -> None:
    fil = Path(sys.argv[1]) if len(sys.argv) > 1 else FIL
    rader = mät(sqlite3.connect(ROT / "sprak.db"))
    with fil.open("w", encoding="utf-8", newline="") as f:
        skrivare = csv.DictWriter(f, ["koncept", "ordklass", "nivå", "zipf", "språk"])
        skrivare.writeheader()
        skrivare.writerows(rader)
    utan = [p["koncept"] for p in rader if not p["zipf"]]
    print(f"{len(rader)} koncept mätta, {len(utan)} utan frekvens, sparat i {fil}")
    print("\nde tjugo vanligaste:")
    for p in rader[:20]:
        print(f"  {p['zipf']:>5}  {p['koncept']:<24} {p['ordklass']:<14} {p['nivå']}")
    if utan:
        print("\nutan frekvens:", ", ".join(utan[:10]))


if __name__ == "__main__":
    main()
