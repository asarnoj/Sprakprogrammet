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
from ..kortmodell import Kort, meningens_kort
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


def _ställ(passet: Passet, uppgift, *, fas: str = "mening",
           paket: frozenset = frozenset()) -> bool:
    """Ställ meningen och rätta svaret.

    Ger True när allt gick rätt, False när något föll och None när användaren
    hoppade över. Utan det sista satt man fast: ett `n` för att gå vidare
    rättades som översättning, tre gånger i rad i den första körningen.

    I introfasen (`fas="intro"`) BOKFÖRS INGENTING (5.4). Övningen finns för
    att användaren inte ska möta ny kunskap oförberedd, inte för FSRS; kortet
    prövas på riktigt först i meningsfasen.
    """
    uppgift = passet.ställ(uppgift, fas)
    print(f"\n  {uppgift.källtext}")
    start = time.perf_counter()
    svar = _fråga("  > ")
    if svar == "q":
        raise SystemExit
    if svar == "s":
        print("  hoppade över.")
        return None
    rättning = passet.rätta(uppgift, svar, time.perf_counter() - start)
    intro = fas == "intro"
    if rättning.rätt:
        if intro:
            print("  rätt.")
            return True
        val = _fråga("  rätt.    [enter] vidare · h svårt · e lätt\n  ")
        höjt = {k: "hard" if val == "h" else "easy" for k in rättning.betyg} \
            if val in ("h", "e") else None
        passet.bokför(uppgift, rättning, höjt=höjt, paket=paket)
        return True
    print(f"  facit:   {uppgift.facit}")
    print(f"  fel i:   {', '.join(str(k) for k in rättning.fel) or '—'}")
    if intro:
        _fråga("  [enter] vidare\n  ")
        return False
    val = _fråga("  [enter] vidare · r jag hade rätt · f flagga facit\n  ")
    if val == "r":
        # Rätt svar som facit inte hade: korten godkänns och facit granskas.
        passet.bokför(uppgift, rättning, godkända=frozenset(rättning.betyg),
                      flagga=svar, paket=paket)
        print("  godkänt, och facit flaggat för granskning.")
        return True
    if val == "f":
        passet.bokför(uppgift, rättning, flagga=svar, paket=paket)
        print("  facit flaggat.")
    else:
        passet.bokför(uppgift, rättning, paket=paket)
    return False


def _glosor(passet: Passet, kö: list) -> bool:
    """Lär ut övningens okända innehållsord först (5.4).

    «Ordningen inom dagen följer kraven. Ett kort presenteras efter de kort
    det kräver, så att lånekorten redan är införda eller presenterade.»

    Utan det här prövade den första övningen tre okända saker och kallade en
    av dem mål: SVO lärdes ut med «Tid står.», där varken `tid` eller `står`
    hade visats. Dag ett ska i stället nå sin första mening när användaren kan
    ett pronomen och ett verb (5.4).

    Ger False när användaren avbröt.
    """
    if not kö:
        return True
    print(f"    orden först ({len(kö)} st):")
    envis = 0
    while kö:
        glosa = kö.pop(0)
        mening_id = passet.data.ny_mening(
            "glosa", str(glosa.kort), glosa.källtext, sorted(glosa.former))
        svar = _fråga(f"      {glosa.källtext}  →  ")
        if svar == "q":
            raise SystemExit
        if svar == "s":
            print("      hoppade över.")
            return False
        passet.data.svara(mening_id, svar, 0.0)
        if passet.rätta_glosa(glosa, svar):
            print("      rätt.")
            passet.data.presentera(glosa.kort)
            envis = 0
            continue
        print(f"      facit: {glosa.facit}")
        kö.append(glosa)                      # sist i kön (5.4)
        envis += 1
        if envis > len(kö):
            print("      orden sitter inte än — introfasen pausas.")
            return False
    passet.uppdatera()
    return True


def _lektion(passet: Passet, uppgift, kort) -> None:
    """Visa kortet i en färdig mening innan det prövas (5.4).

    Utan det här är introövningen ett prov före undervisningen: användaren
    möter regeln kall och kan omöjligt svara rätt. Exemplet visar meningen
    med facit, och vilka ord kortet självt bestämde — positionerna räknas
    fram, de skrivs inte för hand (6.2).

    Meningen loggas som en ställd lektion, så att samma källmening inte kommer
    igen som övning eller uppgift samma dag (6.1 punkt 8). Övningen blir
    därför en ANNAN mening med samma kort som mål.
    """
    uppgift = passet.ställ(uppgift, "lektion")
    orden = [str(o) for o in uppgift.ut.ord]
    platserna = [p for k, ps in meningens_kort(passet.s.tabell, uppgift.ut)
                 if k == kort for p in ps]
    egna = {i for sort, i in platserna if sort == "ord"}
    luckor = {i for sort, i in platserna if sort == "lucka"}
    # En lucka är platsen där ett ord HADE stått: den nakna frasens uteblivna
    # artikel syns bara så (6.2). Utan den vore lektionen tom för just de kort
    # vars hela innebörd är att ingenting skrivs.
    bitar = []
    for i, o in enumerate(orden):
        if i in luckor:
            bitar.append("_")
        bitar.append(f"[{o}]" if i in egna else o)
    if len(orden) in luckor:
        bitar.append("_")
    print(f"    exempel:  {uppgift.källtext}")
    print(f"              {uppgift.facit}")
    if egna or luckor:
        print(f"    kortet bestämmer:  {' '.join(bitar)}"
              + ("    (_ = ordet som INTE skrivs)" if luckor else ""))


def _introfas(passet: Passet) -> None:
    """Presentera nästa nivås kort, ett i taget (5.1, 5.4).

    Ordningen följer kraven: övningens okända innehållsord lärs ut som glosor
    innan kortet som behöver dem. Ingenting bokförs — övningen finns för att
    användaren inte ska möta ny kunskap oförberedd, och kortet prövas på
    riktigt först i meningsfasen.

    Ett kort räknas som presenterat när det KLARAT övningen (5.1). Går den
    fel läggs kortet sist i kön och görs om senare, inte direkt: då har
    användaren facit i färskt minne.
    """
    kö = passet.att_presentera()
    if not kö:
        print("  allt i nästa nivå är redan presenterat i dag — korten prövas "
              "i meningar nu ([enter]).")
        return
    nivån = frozenset(kö)
    print(f"  introfasen: {len(kö)} kort i nästa nivå. Inget bokförs här.")
    kvar = list(kö)
    envis = 0
    while kvar:
        kort = kvar.pop(0)
        steg = passet.introsteg(kort, paket=nivån)
        if steg is None:
            print(f"  {kort}: ingen övning går att bygga ännu — hoppas över.")
            continue
        glosor, uppgift = steg
        print(f"\n  lär dig nu:  {kort}")
        if not _glosor(passet, glosor):
            return
        _lektion(passet, uppgift, kort)
        övning = passet.presentera(kort, paket=nivån, markera=False)
        if övning is None:
            print("  ingen andra mening att öva på — kortet prövas i "
                  "meningsfasen.")
            passet.klarat_introövningen(kort)
            continue
        utfall = _ställ(passet, övning, fas="intro")
        if utfall:
            passet.klarat_introövningen(kort)
            envis = 0
            continue
        if utfall is None:
            print("  introfasen avbruten.")
            return
        kvar.append(kort)          # sist i kön (5.4)
        envis += 1
        if envis > len(kvar):
            print("  inget kort går rätt just nu — introfasen pausas.")
            return
    print("\n  nivån är presenterad. Korten prövas nu i meningar.")


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

    print(f"{a.källspråk} → {språk}.  [enter] öva · n nästa nivå · q sluta")
    print("  när en mening ställs: skriv översättningen, "
          "s hoppar över, q slutar")
    while True:
        läge = passet.läge()
        print(f"\n[{läge['dag']} {läge['tid']}]  införda {läge['införda']} · "
              f"presenterade {läge['presenterade']} · svaga {läge['svaga']} · "
              f"att presentera {läge['att_presentera']}")
        val = _fråga("> ")
        if val == "q":
            return
        if val == "n":
            _introfas(passet)
            # Faserna följer på varandra (5.1): efter introfasen prövas korten
            # i meningar. Att gå tillbaka till menyn här var det som lät
            # introfasen köras om i stället, och passet nådde aldrig fram.
            val = ""
        svaga = sorted(passet.svaga(), key=str)
        if not svaga:
            print("  inget svagt kort just nu — ta nästa nivå med n.")
            continue
        # Meningsfasen körs tills högarna är tomma (5.3), inte en mening per
        # tangenttryck: dagen är klar när det svaga är klarat.
        while svaga:
            kortet = svaga[0]
            uppgift = passet.uppgift(kortet)
            if uppgift is None:
                print(f"  {kortet}: ingen mening att pröva det med i dag.")
                svaga = [k for k in svaga if k != kortet]
                continue
            if _ställ(passet, uppgift) is None:
                break
            svaga = sorted(passet.svaga(), key=str)
        if not svaga:
            print("\n  högarna är tomma — dagens arbete är gjort (5.3).")


if __name__ == "__main__":
    main()
