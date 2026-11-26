"""Dagspasset i terminalen — version ett av gränssnittet (KÄRNAN 5.1, punkt 9).

    python -m sprakprog.passet --karta kartor/en.pkl --nivåer kartor/nivaer_en.json

Kursen är ett språkpar: källspråket är det du översätter från, målspråket det du
skriver. Kartan och nivåerna hör till målspråket.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from ..fsrslager import Lager
from ..kortmodell import Kort
from ..kurs import Kursdata
from ..rendering.karta import ladda
from ..sammansattning import Sammansättare
from . import Passet

ROT = Path(__file__).resolve().parents[3]


def _nivåfil(fil: str) -> tuple[dict[Kort, frozenset], list[frozenset]]:
    """Kraven per kort och nivåerna i öppningsordning (4.2)."""
    data = json.loads(Path(fil).read_text(encoding="utf-8"))

    def kort(rad) -> Kort:
        return Kort(rad[0], rad[1], tuple(rad[2]))

    krav = {kort(k): frozenset(map(kort, m)) for k, m in data["krav"]}
    return krav, [frozenset(map(kort, n)) for n in data["nivåer"]]


def _fråga(text: str) -> str:
    try:
        return input(text).strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def _ställ(passet: Passet, uppgift) -> None:
    uppgift = passet.ställ(uppgift)
    print(f"\n  {uppgift.källtext}")
    start = time.perf_counter()
    svar = _fråga("  > ")
    if svar == "q":
        raise SystemExit
    rättning = passet.rätta(uppgift, svar, time.perf_counter() - start)
    if rättning.rätt:
        print("  rätt.")
    else:
        print(f"  facit: {uppgift.facit}")
        print("  fel i:", ", ".join(str(k) for k in rättning.fel) or "—")


def main() -> None:
    p = argparse.ArgumentParser(description="Ett dagspass i terminalen.")
    p.add_argument("--kurs", default=str(ROT / "kurs.db"))
    p.add_argument("--karta", default=str(ROT / "kartor" / "en.pkl"))
    p.add_argument("--nivåer", default=str(ROT / "kartor" / "nivaer_en.json"))
    p.add_argument("--källspråk", default="sv")
    a = p.parse_args()

    karta = ladda(a.karta)
    språk = karta["språk"]
    sprak = sqlite3.connect(ROT / "sprak.db")
    data = Kursdata(sqlite3.connect(a.kurs), a.källspråk, språk)
    krav, nivåer = _nivåfil(a.nivåer)
    passet = Passet(data, Sammansättare(sprak, karta, par=a.källspråk),
                    Lager(data), krav, nivåer)

    print(f"{a.källspråk} → {språk}.  [enter] nästa mening · n nytt kort · q sluta")
    while True:
        läge = passet.läge()
        print(f"\n[{läge['dag']} {läge['tid']}]  införda {läge['införda']} · "
              f"svaga {läge['svaga']} · att införa {läge['kandidater']}")
        val = _fråga("> ")
        if val == "q":
            return
        if val == "n":
            kandidater = passet.kandidater()
            if not kandidater:
                print("  inget kort går att införa nu.")
                continue
            paket = passet.paket(kandidater[0])
            if paket is None:
                print(f"  {kandidater[0]}: ingen mening inom budgeten ännu.")
                continue
            uppgift, nya = paket
            print("  nya kort:", ", ".join(sorted(map(str, nya))))
            for kort in nya:
                data.presentera(kort)
            passet.uppdatera()
            _ställ(passet, uppgift)
            continue
        svaga = sorted(passet.svaga(), key=str)
        if not svaga:
            print("  inget förfallet just nu — ta ett nytt kort med n.")
            continue
        uppgift = passet.uppgift(svaga[0])
        if uppgift is None:
            print(f"  {svaga[0]}: ingen mening inom budgeten ännu.")
            continue
        _ställ(passet, uppgift)


if __name__ == "__main__":
    main()
