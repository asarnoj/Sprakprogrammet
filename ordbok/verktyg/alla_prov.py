"""Kör hela skyddsnätet i en körning, och säg vad som föll.

VARFÖR DEN HÄR FILEN FINNS. Näten var elva separata skript utan gemensam
ingång. Ett skyddsnät som kräver att man minns elva filnamn körs inte, och
ett nät som inte körs är inget nät — det är projektets egen formulering om
`tjänsteprov`s körtid, tillämpad på uppställningen i stället för på
prestandan.

Två fel satt tysta i näten när den här filen skrevs, båda funna genom att
för första gången köra allt i följd:

    passprov      "upplåsning utökar dagen" var TOM. Uppsättningen
                  nollställde kursen, vilket stänger den dörr provet ska gå
                  igenom (`lås_upp` kräver byggbarhet, en nollställd kurs
                  har noll). Varje kurs föll ut genom `continue`, ingen
                  kontroll kördes, och provet rapporterade grönt.

    indikatorprov "kostnad per läge finns när takten finns" var FÖR STARK.
                  Den krävde ett tal för både mening och glosa så snart den
                  poolade takten fanns — men en kurs vars hela tidtagna
                  historik är drill har inget meningstal att ha.

ORDNINGEN ÄR SNABBAST FÖRST. De rena funktionsproven tar sekunder och
fäller de flesta regressioner; tjänste- och passproven bygger databaskopior
och tar minuter. Faller något tidigt slipper man vänta ut resten.

VAD SOM INTE ÄR MED. `nåbarhet`, `stammar`, `synk`, `rendera_prov`,
`ögonblicksbild`, `passkörning`, `ordvalsmätning` och
`meningstidsmätning` är MÄTVERKTYG, inte nät:
de svarar med tal eller listor och har ingen invariant som kan falla. `felsvep` ger också
ett tal, men det ingår ändå — dess "falska betyg" ska vara noll, och det är
ett påstående som går att bryta.

NÄTEN ÄR DELADE EFTER VILKEN KÄRNA DE PRÖVAR (2026-11-11). Fjorton av de
tjugoen näten importerar `sprakprog.kort`, `.generator` eller `.webb` — den
gamla kärnan, som §8.1 raderar i steg 9b. De mäter alltså kod som ska bort, och
de bar största delen av körtiden. De står kvar i `GAMLA_NÄT` och körs med
`--gammalt`, så länge den gamla kärnan är det enda sättet att köra programmet.
`NÄT` prövar den nya kärnan och det som står kvar (`rendering/`), och ett rött
nät där säger något om framtiden. Det är `G7` tillämpad på uppställningen: ett
nät som mäter raderad kod slutar mäta utan att bli rött.

FILERNA LIGGER KVAR I SAMMA KATALOG, inte i en undermapp. Varje prov hittar
projektroten med `Path(__file__).resolve().parents[2]`, och flera lägger till
den i `sys.path`; en nivå ner hade pekat på `ordbok/` i stället för på repot.
Delningen är därför två listor, inte en flytt.

Kör:  python ordbok/verktyg/alla_prov.py
      python ordbok/verktyg/alla_prov.py --snabb     (hoppa över de tunga)
      python ordbok/verktyg/alla_prov.py --gammalt   (även den gamla kärnans nät)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HÄR = Path(__file__).resolve().parent

#: (fil, tung). `tung` = bygger databaskopior och tar minuter.
#: Näten som prövar den NYA kärnan, och de som prövar det som står kvar.
NÄT = [
    ("rättningsprov.py",     False),
    ("konstruktionsprov.py", False),
    # Rent räknearbete: ingen databas, bara arbetsprofilen och tidsmodellen.
    ("tidsmodellprov.py",    False),
    # Sökningens soundhet: samma fråga, samma svar, varm eller kall. SIST bland
    # de snabba, för den är inte snabb längre: kontrollen «svaret beror inte på
    # det tillåtna före» söker sex mål i tre mängder med två motorer var, och
    # nätet gick från 180 till 313 sekunder (mätt 2026-10-28). Den bygger inga
    # databaskopior och hör därför inte till de tunga, men den ska inte stå
    # före de nät som faller på en tiondel av en sekund.
    ("sökningsprov.py",      False),
    ("renderarbild.py",      True),
    # Kravens löfte: grinden får inte släppa upp ett kort passet inte kan
    # införa. Tung, för ett nej kostar en uttömmande genomgång — men det var
    # elva sådana nej som gjorde dag fyras plan omöjlig. Sedan 2026-11-03
    # ställer den grindens två frågor var för sig: nivåns och kravets.
    ("kravprov.py",          True),
    # ~2 min: bygger en färsk kurs per invariant och kör introfasen i var
    # och en. Reglerna i passet, till skillnad från `passprov` som prövar
    # tjänsterna runt det.
    ("passprovet.py",        True),
]

#: Näten som bara prövar den GAMLA kärnan (`kort`, `generator`, `webb`). De
#: raderas med den i steg 9b; till dess körs de med `--gammalt`.
GAMLA_NÄT = [
    ("omkastningsprov.py",   False),
    ("attributionsprov.py",  False),
    ("arbetsbördeprov.py",   False),
    ("samplarprov.py",       False),
    ("strukturprov.py",      False),
    ("dimensionsprov.py",    False),
    ("lektionsprov.py",      False),
    # Bygger databaskopior men är ändå SNABB — 2 s, inte minuter — därför att
    # varje invariant skriver sin egen lilla logg i stället för att sampla
    # meningar. Kolumnen säger körtid och inte metod.
    ("övervakningsprov.py",  False),
    ("ordföljdsprov.py",     True),
    ("introduktionsprov.py", True),
    ("indikatorprov.py",     True),
    ("passprov.py",          True),
    ("tjänsteprov.py",       True),
    ("felsvep.py",           True),
]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Kör hela skyddsnätet.")
    p.add_argument("--snabb", action="store_true",
                   help="bara de nät som tar sekunder")
    p.add_argument("--fortsätt", action="store_true",
                   help="kör vidare även när ett nät fallit")
    p.add_argument("--gammalt", action="store_true",
                   help="kör även näten som bara prövar den gamla kärnan")
    args = p.parse_args(argv)

    alla = NÄT + (GAMLA_NÄT if args.gammalt else [])
    nät = [(f, t) for f, t in alla if not (args.snabb and t)]
    utfall: list[tuple[str, int, float]] = []
    for fil, _ in nät:
        print(f"\n{'═' * 72}\n  {fil}\n{'═' * 72}", flush=True)
        start = time.monotonic()
        r = subprocess.run([sys.executable, str(HÄR / fil)])
        sekunder = time.monotonic() - start
        utfall.append((fil, r.returncode, sekunder))
        if r.returncode and not args.fortsätt:
            print(f"\n{fil} föll — avbryter. Kör med --fortsätt för att "
                  f"se resten.")
            break

    print(f"\n{'═' * 72}\n  SAMMANFATTNING\n{'═' * 72}")
    for fil, kod, sekunder in utfall:
        print(f"  {'✓' if kod == 0 else '✗ FÖLL'}  {fil:24}{sekunder:7.1f} s")
    fallna = [f for f, k, _ in utfall if k]
    körda = len(utfall)
    if len(utfall) < len(nät):
        print(f"  … {len(nät) - körda} nät kördes aldrig")
    print(f"\n{körda} nät körda, {len(fallna)} föll."
          if fallna else f"\n{körda} nät körda, alla håller.")
    return 1 if fallna else 0


if __name__ == "__main__":
    raise SystemExit(main())
