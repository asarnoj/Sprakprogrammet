"""Vilken ordning ska DAGENS ORD väljas i? — KÄRNAN 5.6.

VARFÖR DEN HÄR MÄTNINGEN FINNS. 5.6 säger «inför först det som ger mest ny
täckning per kort», och noteringen om version ett lovar att täckningen «ersätter
både urvalet och ordningen» när den finns. Den finns nu — `nivaer/tackning.py` —
och för NIVÅORDNINGEN vann den stort: `ordningsmätning.py` visade att
täckningsordningen slår både bokstavsordning och ordfrekvens, och att det var
den som flyttade `jag` från nivå 72.

Frågan här är en annan: när dagens nivå är bestämd, och planen ska välja vilka
ORD dagen lär ut, hjälper täckningen då? Tre kandidater:

    närsynt täckning   `Täckning.per_kort` för ordets egna kort, räknat mot de
                       införda korten plus dagens nivå. Det är 5.6:s formulering
                       ordagrant: «de användningar där just det kortet är det
                       sista som saknas», delat med vad valet kostar
    total användning   ordets sammanlagda andel över ALLA sina celler, också de
                       som inte är upplåsta än
    ordfrekvens        `frekvens.csv`, alltså konceptets lemma — det koden gör

Måttet är detsamma som i `ordningsmätning.py`: hur stor del av språkets uppmätta
användning eleven kan producera. Samma antal kort i alla tre fallen, så talen är
jämförbara rakt av.

RESULTATET, mätt på engelskan över sex nivåer (34 kort):

    ordfrekvens          17,19 %
    total användning     17,07 %
    närsynt täckning     16,97 %

Alltså: **för ordvalet ger täckningen ingenting**, och den närsynta varianten är
till och med något sämre. Skälet står i 5.6 själv: «ett kort som kräver något som
inte är infört ger ingenting ensamt». Ett ords värde ligger i alla dess former,
och de flesta cellerna är inte upplåsta än — så «ny täckning nu» mäter fel
horisont. Frekvensen fångar hela horisonten på en gång.

Slutsatsen är inte att 5.6 har fel, utan att kriteriet hör till de kort som
GRINDAR: en regel låser upp olika mycket, och där avgör täckningen. Inom en nivå
konkurrerar orden om samma meningsformer, och då är det bara hur ofta språket
använder dem som skiljer dem — vilket är frekvensen.

Kör:  python ordbok/verktyg/ordvalsmätning.py [SPRÅK] [NIVÅER]
"""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.fsrslager import Lager                             # noqa: E402
from sprakprog.kortmodell import Kort                             # noqa: E402
from sprakprog.kurs import Kursdata                               # noqa: E402
from sprakprog.nivaer.tackning import (                           # noqa: E402
    Täckning, läs_användningar, väljare_ur_karta,
)
from sprakprog.passet import Passet                               # noqa: E402
from sprakprog.rendering.karta import ladda                       # noqa: E402
from sprakprog.sammansattning import Sammansättare                # noqa: E402


def _nivåfil(språk: str) -> tuple[dict, list]:
    d = json.loads((ROT / "kartor" / f"nivaer_{språk}.json").read_text(encoding="utf-8"))

    def kort(rad) -> Kort:
        return Kort(rad[0], rad[1], tuple(rad[2]))

    return ({kort(k): frozenset(map(kort, m)) for k, m in d["krav"]},
            [frozenset(map(kort, n)) for n in d["nivåer"]])


def _kör(språk: str, läge: str, antal: int, täck: Täckning, total: dict,
         karta: dict, krav: dict, nivåer: list) -> tuple[int, float]:
    """Ta N nivåer med perfekta svar och mät hur mycket som blivit sägbart.

    Ordvalet byts ut genom `Sammansättare._ordvikt`, som är den enda ingång
    `_ordförråd`, `glosorna` och `kandidater` delar — så en annan ordning går
    att pröva utan att röra koden.
    """
    s = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta, "sv")
    frekvens = s._ordvikt                                         # noqa: SLF001

    with tempfile.TemporaryDirectory() as mapp:
        data = Kursdata(sqlite3.connect(Path(mapp) / "k.db"), "sv", språk)
        p = Passet(data, s, Lager(data), krav, nivåer)

        def nyckel(koncept: str) -> tuple:
            """Minst först, med frekvensen som tiebreak (5.6 vill samma ordning
            varje gång när två kandidater ger lika mycket)."""
            bas = frekvens(koncept)
            if läge == "ordfrekvens":
                return bas
            if läge == "total användning":
                return (-total.get(koncept, 0.0), *bas)
            # Närsynt täckning: ordets EGNA kort — «ett ords egna kort är en
            # kostnad, inte en vinst» (5.6) — räknade mot dagens läge, eftersom
            # «ett kort som kräver något som inte är infört ger ingenting
            # ensamt».
            kort = Kort(språk, "ord", (koncept, ""))
            try:
                lexem = s.u.lexem(koncept)
                egna = frozenset(k for ks in s.tabell.former(lexem).values() for k in ks)
            except Exception:                                      # noqa: BLE001
                egna = frozenset({kort})
            grund = data.införda() | p.nästa_nivå()
            return (-täck.per_kort(egna, grund), *bas)

        s._ordvikt = nyckel                                       # noqa: SLF001
        try:
            for _ in range(antal):
                plan = p.dagsplan()
                if not plan.introövningar:
                    break
                for k in plan.kort:
                    data.presentera(k)
                p.uppdatera()
                for u in plan.meningsfasen:
                    u2 = p.ställ(u)
                    p.bokför(u2, p.rätta(u2, u2.facit, 1.0), paket=p.paket())
                p.uppdatera()
        finally:
            s._ordvikt = frekvens                                 # noqa: SLF001
        införda = data.införda()
        return len(införda), sum(v for kr, v in täck.vikt.items() if kr <= införda)


def main() -> int:
    språk = sys.argv[1] if len(sys.argv) > 1 else "en"
    antal = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    karta = ladda(ROT / "kartor" / f"{språk}.pkl")
    krav, nivåer = _nivåfil(språk)
    anv = läs_användningar(ROT / "ordbok" / "nivålistor" / "användningar.csv", språk)
    s = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta, "sv")
    täck = Täckning(s.tabell, anv, väljare_ur_karta(karta))

    total: dict[str, float] = defaultdict(float)
    for (koncept, _cell), andel in anv.items():
        total[koncept] += andel

    print(f"{språk}: {antal} nivåer med perfekta svar\n")
    print("  hur stor del av språket kan eleven producera?\n")
    rader = []
    for läge in ("ordfrekvens", "total användning", "närsynt täckning"):
        kort, del_ = _kör(språk, läge, antal, täck, total, karta, krav, nivåer)
        rader.append((läge, kort, del_))
        print(f"    {läge:<20} {kort:>3} kort → {100 * del_:6.2f} %", flush=True)

    bäst = max(rader, key=lambda r: r[2])
    print(f"\n  bäst: {bäst[0]}")
    if bäst[0] == "ordfrekvens":
        print("  Täckningen ger alltså ingenting för ORDVALET. Den hör till de "
              "kort\n  som grindar (nivåordningen), inte till orden inom en nivå.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
