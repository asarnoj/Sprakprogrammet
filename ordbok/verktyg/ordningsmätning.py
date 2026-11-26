"""Vilken nivåordning lär ut mest språk snabbast? — KÄRNAN 5.6, steg 4.

VARFÖR DEN HÄR MÄTNINGEN FINNS. Nivåerna är grafens starka komponenter, och
deras ordning är en TOPOLOGISK sortering — men en sådan har enorm frihet.
132 av engelskans 164 nivåer har ett enda kort, och deras inbördes ordning är
obunden av kraven. Den ordning koden råkade ge var `sorted(noder, key=str)`,
alltså bokstavsordning efter svensk konceptnyckel: `a` före `d` före `f` före
`p`, och därför artikeln på nivå 3 och pronomenet `jag` på nivå 72.

Innan en ny ordning byggs in ska den mätas mot alternativen, på ett mått som
inte är ordningens eget. Måttet är KÄRNAN 5.6:s egen fråga:

> **Täckning** är hur stor del av språkets verkliga användning användaren kan
> producera.

Alltså: hur mycket av språket kan eleven säga efter tio nivåer, efter
tjugofem, efter femtio? Det är detsamma för alla fyra kandidaterna, och det
är det kursen finns till för.

ATT TÄCKNINGSORDNINGEN VINNER PÅ SITT EGET MÅTT är väntat och bevisar
ingenting i sig. Det mätningen visar är hur STOR skillnaden är, och om någon
av de billigare ordningarna räcker. Den visar också var de går fel, vilket är
det som gör resultatet läsbart i stället för bara högt.

Kör:  python ordbok/verktyg/ordningsmätning.py [SPRÅK]
"""

from __future__ import annotations

import csv
import json
import pickle
import sqlite3
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kortmodell import Formtabell, Kort                  # noqa: E402
from sprakprog.nivaer.tackning import (                            # noqa: E402
    Täckning, läs_användningar, väljare_ur_karta,
)
from sprakprog.rendering.karta import Väg                          # noqa: E402,F401
from sprakprog.rendering.uppslag import Uppslag                    # noqa: E402

MÄRKEN = ("ord:pronomen_1sg", "ord:artikel_bestamd",
          "regel:val/tempusform/preteritum", "ändelse:Substantiv/regelbunden/pl",
          "ord:interr_det_hur_mycket", "ord:frågadverb_orsak")


def _läs(språk: str):
    d = json.loads((ROT / "kartor" / f"nivaer_{språk}.json").read_text(encoding="utf-8"))

    def kort(rad) -> Kort:
        return Kort(rad[0], rad[1], tuple(rad[2]))

    nivåer = [frozenset(map(kort, n)) for n in d["nivåer"]]
    krav = {kort(k): frozenset(map(kort, m)) for k, m in d["krav"]}
    return nivåer, krav


def _frekvens() -> dict[str, float]:
    with (ROT / "ordbok" / "nivålistor" / "frekvens.csv").open(encoding="utf-8") as f:
        return {r["koncept"]: float(r["zipf"]) for r in csv.DictReader(f)}


def _låser_upp(nivåer, krav) -> dict[int, int]:
    """Hur många nivåer som (transitivt) väntar på varje nivå."""
    nivå_av = {x: i for i, n in enumerate(nivåer) for x in n}
    kant: dict[int, set] = {i: set() for i in range(len(nivåer))}
    for x, ks in krav.items():
        for k in ks:
            if k in nivå_av and x in nivå_av and nivå_av[k] != nivå_av[x]:
                kant[nivå_av[k]].add(nivå_av[x])
    ut = {}
    for i in range(len(nivåer)):
        nådda, kö = set(), [i]
        while kö:
            for j in kant[kö.pop()]:
                if j not in nådda:
                    nådda.add(j)
                    kö.append(j)
        ut[i] = len(nådda)
    return ut


def _grådig(nivåer, krav, nyckel) -> list[int]:
    """Topologisk ordning där `nyckel(i, öppnade)` får välja bland de möjliga."""
    öppnade: set = set()
    kvar = set(range(len(nivåer)))
    ordning: list[int] = []
    while kvar:
        möjliga = [i for i in kvar if all(
            k in öppnade for x in nivåer[i] for k in krav.get(x, ())
            if k not in nivåer[i])]
        if not möjliga:
            break
        b = max(möjliga, key=lambda i: (nyckel(i, öppnade), -i))
        ordning.append(b)
        öppnade |= nivåer[b]
        kvar.discard(b)
    return ordning


def _täckningsvärde(täck: Täckning, nivåer, nivåkort):
    def värde(i, öppnade):
        nivå = nivåer[i]
        tillgängligt = öppnade | nivå
        v = 0.0
        for k, andel in täck.vikt.items():
            if k <= öppnade or not (k & nivå):
                continue
            if any(x in nivåkort for x in k - tillgängligt):
                continue
            v += andel / len(k - öppnade)
        return v
    return värde


def _nådd(täck: Täckning, nivåer, ordning, nivåkort) -> list[float]:
    """Hur stor del av språket som är sägbart efter varje nivå.

    Ett ord räknas som tillgängligt: orden är upplåsta från början (3.1) och
    följer med sina paket. Det som mäts är alltså vad GRAMMATIKEN öppnar.
    """
    öppnade: set = set()
    ut = []
    for i in ordning:
        öppnade |= nivåer[i]
        ut.append(sum(v for k, v in täck.vikt.items()
                      if not any(x in nivåkort and x not in öppnade for x in k)))
    return ut


def main() -> int:
    språk = sys.argv[1] if len(sys.argv) > 1 else "en"
    nivåer, krav = _läs(språk)
    nivåkort = {x for n in nivåer for x in n}
    u = Uppslag(sqlite3.connect(ROT / "sprak.db"), språk)
    karta = pickle.load((ROT / "kartor" / f"{språk}.pkl").open("rb"))
    täck = Täckning(
        Formtabell(u),
        läs_användningar(ROT / "ordbok" / "nivålistor" / "användningar.csv", språk),
        väljare_ur_karta(karta))

    frek = _frekvens()
    vikt_ord = {i: max((frek.get(x.nyckel[0], 0.0) for x in n), default=0.0)
                for i, n in enumerate(nivåer)}
    låser = _låser_upp(nivåer, krav)
    värde = _täckningsvärde(täck, nivåer, nivåkort)

    kandidater = {
        "alfabetisk (dagens)": list(range(len(nivåer))),
        "låser upp flest": _grådig(nivåer, krav, lambda i, ö: låser[i]),
        "ordfrekvens": _grådig(nivåer, krav, lambda i, ö: vikt_ord[i]),
        "täckning": _grådig(nivåer, krav, värde),
    }
    # Prövat och förkastat: att bryta lika med upplåsningen. Täckningsvärden
    # är flyttal och krockar nästan aldrig, så ordningen blev densamma på
    # varje mätpunkt. Ett alternativ som inte mäter annorlunda får inte ligga
    # kvar och se ut som ett val.

    print(f"{språk}: {len(nivåer)} nivåer\n")
    print("  hur stor del av språket är sägbart efter N nivåer?\n")
    punkter = [5, 10, 25, 50, 100]
    print("    " + "ordning".ljust(22) + "".join(f"{n:>9}" for n in punkter))
    for namn, ordning in kandidater.items():
        nådd = _nådd(täck, nivåer, ordning, nivåkort)
        rad = "".join(f"{100*nådd[min(n, len(nådd)) - 1]:8.1f} %" for n in punkter)
        print(f"    {namn:<22}{rad}")

    print("\n  var hamnar några nyckelkort?\n")
    print("    " + "kort".ljust(36)
          + "".join(f"{n.split()[0][:12]:>14}" for n in kandidater))
    for märke in MÄRKEN:
        rad = ""
        for ordning in kandidater.values():
            plats = next((p for p, i in enumerate(ordning, 1)
                          if any(str(x) == märke for x in nivåer[i])), None)
            rad += f"{plats if plats else '—':>14}"
        print(f"    {märke:<36}{rad}")

    bäst = "täckning"
    print(f"\n  {bäst}, första tolv nivåerna:\n")
    öppnade: set = set()
    for p, i in enumerate(kandidater[bäst][:12], 1):
        v = värde(i, öppnade)
        öppnade |= nivåer[i]
        print(f"    {p:>3}  {100*v:5.2f} %  "
              + " · ".join(sorted(map(str, nivåer[i])))[:62])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
