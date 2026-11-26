"""Nät för sökningens soundhet — KÄRNAN 3.10 och 6.7.

> Sökningen är exakt (6.7) och hittar därför en mening för varje kort som har
> ett bevis — beviset är kontrollen av det, ingen reserv.

VARFÖR DET HÄR NÄTET FINNS. Sökningen svarade **nej när svaret var ja**, tyst,
och det syntes inte i något prov. `Sammansättare._minnesnyckel` memoiserade vad
en del gav under

    (nod, bindning, budget, måste, kedja)

`måste` är en bool — «måste den här delen innehålla målet» — och VILKET mål fanns
inte i nyckeln. En sökning efter `ord:pronomen_1sg` lagrade därför «ingenting
här» under en nyckel som en senare sökning efter `ord:frågepronomen_person`
återanvände. Mätt mitt i `dagsplan`, samma kort och samma predikat: **noll
träffar med varmt minne, tio med nollställt.**

Att det inte setts förr beror på skalan. Minnet töms när predikatet byts, och
passet skapar ett predikat per anrop, så med en nivås fem kort hann
kollisionerna sällan skada. Med tjugotvå kort ur tjugo nivåer växte minnet till
55 679 poster och sex kort tappade sina meningar — och då såg det ut som att
kandidatkön (4.5) inte fungerade, när det var sökningen som ljög.

INVARIANTEN ÄR ENKEL ATT SÄGA OCH SVÅR ATT SNUBBLA PÅ: sökningens svar får inte
bero på vad som söktes före. Ett minne som bryter det är inte en optimering utan
ett fel.

Kör:  python ordbok/verktyg/sökningsprov.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kortmodell import Kort                             # noqa: E402
from sprakprog.rendering.karta import ladda                       # noqa: E402
from sprakprog.sammansattning import Sammansättare                # noqa: E402

KARTA = ROT / "kartor" / "en.pkl"
NIVÅER = ROT / "kartor" / "nivaer_en.json"

#: Längsta mening, som i passet (6.3).
LÄNGSTA = 10

#: Hur många meningar som räknas per kort. Talet behöver inte vara stort: felet
#: visar sig som noll mot tio, inte som nio mot tio.
TAK = 6


def _nivå_ett() -> set[Kort]:
    """Nivå 1:s kort plus de ord en minsta mening för dem behöver.

    Provet behöver ett läge där flera mål söks under SAMMA predikat, och nivå 1
    plus dess ordförråd är det minsta sådana läget som finns.
    """
    d = json.loads(NIVÅER.read_text(encoding="utf-8"))

    def kort(rad) -> Kort:
        return Kort(rad[0], rad[1], tuple(rad[2]))

    nivå = {kort(k) for k in d["nivåer"][0]}
    ord_ = {Kort("en", "ord", (n, "")) for n in
            ("tid_tid", "väd_väder", "mat_vatten", "abs_kärlek",
             "pos_stå", "rör_falla", "gen_passa", "pos_sitta",
             "per_se", "kom_säga", "rör_komma", "kog_veta")}
    return nivå | ord_


#: Målen som söks, i ordning. De senare är de som drabbades: ett funktionsord
#: vars mening kräver en fråga eller en kvantifierad fras.
MÅLEN = [Kort("en", "ord", (n, "")) for n in
         ("pos_stå", "rör_falla", "pronomen_1sg", "frågepronomen_person",
          "kvant_ingen", "kvant_någon")]


def _räkna(s: Sammansättare, mål: Kort, tillåten) -> int:
    n = 0
    for _ in s.meningar(mål, tillåten, högst_ord=LÄNGSTA, per_mall=None,
                        grupperat=False):
        n += 1
        if n >= TAK:
            break
    return n


def svaret_beror_inte_på_ordningen() -> list[str]:
    """Samma fråga ska ge samma svar, varm eller kall.

    Varje mål söks två gånger: en gång i en FÄRSK sammansättare, och en gång
    efter att de tidigare målen sökts under samma predikat. Skiljer sig talen
    minns sökningen något som inte gäller.
    """
    karta = ladda(KARTA)
    tillåtna = _nivå_ett() | set(MÅLEN)

    def tillåten(k: Kort) -> bool:
        return k in tillåtna

    # Varm: ett predikat, målen i följd.
    varm = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta, "sv")
    varma = [_räkna(varm, mål, tillåten) for mål in MÅLEN]

    # Kall: en egen sammansättare per mål, alltså inget minne att ärva.
    kalla = []
    for mål in MÅLEN:
        ny = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta, "sv")
        kalla.append(_räkna(ny, mål, tillåten))

    brister = []
    for mål, v, k in zip(MÅLEN, varma, kalla):
        if v != k:
            brister.append(f"{mål}: {v} träffar varm, {k} kall — "
                           "minnet bär ett svar som inte gäller")
    return brister


def _nivå(i: int) -> set[Kort]:
    """Nivå `i`:s kort, ettindexerat som i kursen."""
    d = json.loads(NIVÅER.read_text(encoding="utf-8"))
    return {Kort(r[0], r[1], tuple(r[2])) for r in d["nivåer"][i - 1]}


def svaret_beror_inte_på_det_tillåtna_före() -> list[str]:
    """Samma fråga ska ge samma svar vare sig mängden växt under körningen.

    VARFÖR DEN HÄR KONTROLLEN FINNS. Minnet av vad delar gav kastades förut så
    snart predikatet byttes, och bars därför aldrig över ett dygnsbyte — hela
    dagsplanens 42,7 sekunder gick till att bygga upp det på nytt. Sedan
    2026-10-11 bär varje post i stället VAD DEN FRÅGADE OM och gäller så länge
    de korten svarar likadant. Dag två gick från 40,1 till 9,9 sekunder.

    Men beständigheten flyttar felrisken. En del som hämtar sitt svar ur minnet
    frågar inte predikatet, så dess kort hamnar inte i förälderns beroende —
    och föräldern lever då vidare när barnet blivit ogiltigt. Mätt utan den
    ärvningen: dag tre med buret minne tog 3,6 s mot en färsk motors 39,5 och
    gav ANDRA meningar.

    DÄRFÖR GÅR KONTROLLEN TRE MÄNGDER DJUPT. Dag ett och två stämde även med
    felet inne; det syntes först på den tredje. En kontroll på två mängder hade
    gått igenom och släppt ut ett tyst nej.
    """
    karta = ladda(KARTA)
    mängder = [_nivå_ett() | set(MÅLEN)]
    for i in (2, 3):
        mängder.append(mängder[-1] | _nivå(i))

    def svep(s, mängd: set) -> list[int]:
        # Nytt predikatobjekt varje gång, som i passet: `dagsplan`,
        # `_ordförråd` och `paket_för` bygger var sitt.
        def tillåten(k: Kort) -> bool:
            return k in mängd
        return [_räkna(s, mål, tillåten) for mål in MÅLEN]

    buren = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta, "sv")
    brister = []
    for n, mängd in enumerate(mängder, 1):
        varma = svep(buren, mängd)
        färsk = Sammansättare(sqlite3.connect(ROT / "sprak.db"), karta, "sv")
        kalla = svep(färsk, mängd)
        for mål, v, k in zip(MÅLEN, varma, kalla):
            if v != k:
                brister.append(
                    f"mängd {n} ({len(mängd)} kort), {mål}: {v} träffar med "
                    f"buret minne, {k} med färskt — minnet bär ett svar som "
                    "inte gäller sedan mängden växte")
    return brister


PROV = [("svaret beror inte på ordningen", svaret_beror_inte_på_ordningen),
        ("svaret beror inte på det tillåtna före",
         svaret_beror_inte_på_det_tillåtna_före)]


def _falsifiera() -> list[str]:
    """Det gamla läget ska fälla provet: nyckeln utan målet."""
    import sprakprog.sammansattning as S

    brister = []
    print("\nfalsifiering — varje gammalt läge ska fälla sitt prov:")

    gammal_nyckel = S.Sammansättare._minnesnyckel

    def utan_mål(self, nod, bindning, budget, tillåten, kedja, måste, nåbar=None):
        """Nyckeln som den var: `måste` men inte VILKET mål."""
        if nod not in self._delar_med_anrop:
            return None
        if (tillåten is not self._minne_för
                or len(self._bevismängd) != self._minne_bevis):
            self._minne_för, self._minne, self._sedda = tillåten, {}, set()
            self._minne_bevis = len(self._bevismängd)
        return (nod, tuple(bindning.items()), budget, måste, kedja)

    S.Sammansättare._minnesnyckel = utan_mål
    try:
        fel = svaret_beror_inte_på_ordningen()
    finally:
        S.Sammansättare._minnesnyckel = gammal_nyckel
    if fel:
        print(f"  ✓ föll  nyckeln utan målet  ({fel[0][:60]}…)")
    else:
        print("  ✗ STUMT  nyckeln utan målet")
        brister.append("provet vaktar inte minnesnyckeln")

    return brister


def main() -> int:
    brister: list[str] = []
    for namn, fn in PROV:
        fel = fn()
        print(f"  {'✓' if not fel else '✗'} {namn}")
        for b in fel:
            print(f"      {b}")
        brister += fel
    brister += _falsifiera()
    print(f"\n{len(PROV)} kontroller, "
          + (f"{len(brister)} brister." if brister else "alla håller."))
    return 1 if brister else 0


if __name__ == "__main__":
    raise SystemExit(main())
