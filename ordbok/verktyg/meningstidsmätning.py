"""Vad en mening KOSTAR i tid, som funktion av hur många kort den bär — KÄRNAN 6.3.

VARFÖR DEN HÄR MÄTNINGEN FINNS. Tidsmodellen (5.5) ska översätta användarens
minuter per dag till ett antal nya kort, och den översättningen går genom
meningen: «Arbetet räknas i MENINGAR, inte i kort. Den fasta kostnaden per
mening dominerar (6.3), så tiden per kort beror på hur tätt meningarna packas.»

Utan talet finns ingen väg från minuter till kort, och då ska modellen svara
«vet inte» i stället för att gissa — samma regel som `sekunder_per_repetition` i
det gamla systemet följer.

TALEN STÅR I 6.3 SOM PROSA, och det räcker inte: en tabell som bara finns i en
text kan inte räknas om när loggen växer, och den går inte att pröva. Det här
verktyget räknar fram den ur loggen i stället, och skriver den som en fil som
tidsmodellen läser — precis som `frekvens.csv` och `användningar.csv`.

KÄLLAN ÄR DEN GAMLA LOGGEN, och 5.5 tillåter det uttryckligen: «Innan
användarens egen historik finns används FSRS standardparametrar och tiderna ur
den gamla loggen (6.3).» Den nya kursen nollställs vid varje prov, så någon egen
historik finns inte än. När den finns mäts samma sak ur `kurs.db`:s `mening`.

GRUPPERAT PÅ BEDÖMDA KORT, inte på sedda. En mening kan visa kort som inte
graderas — uppskjutna kort förbrukade tid utan att ge en repetition — och det är
graderingarna som är arbetet. Grupperat på `Mening.sedda` blir kurvan
meningslös: den går 13,5 → 11,1 → 12,2 → 17,4 utan riktning, eftersom `sedda`
räknar något annat än vad meningen prövade.

EN RÄT LINJE, INTE PUNKTERNA. Mätpunkterna är inte monotona — tre kort ger 24,7 s
och fyra 21,9, med tjugotvå respektive tjugoen meningar bakom sig — och en
kostnadsfunktion som sjunker när meningen växer ger orimliga svar. Formen står i
6.3 själv: «den fasta kostnaden per mening dominerar», alltså

    sekunder = fast + per_kort × kort

Linjen anpassas med minsta kvadrat, VIKTAD med antalet meningar i varje grupp, så
att en grupp med tjugonio meningar väger tyngre än en med tretton. Det är ingen
utjämning som hittats på: tvåparameterformen är 6.3:s påstående, och anpassningen
mäter dess två tal.

MEDIAN OCH INTE MEDELVÄRDE, till skillnad från `sekunder_per_repetition`. Det
talet är en växelkurs — användarens tjugo minuter köper repetitioner i
GENOMSNITTLIG takt — medan det här är en kostnadskurva vars form ska läsas.
Fördelningen är högersvansad av avbrott, och ett enda avbrott på nio minuter
skulle annars dominera en grupp med tre meningar i.

Kör:  python ordbok/verktyg/meningstidsmätning.py [FIL]
"""

from __future__ import annotations

import csv
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]

FIL = ROT / "ordbok" / "nivålistor" / "meningstid.csv"

#: Ett svar som tog längre än så är ett AVBROTT och inte en mening: användaren
#: gick ifrån. Samma gräns som `kort.schemalaggning.AVBROTTSGRÄNS_MS`, av samma
#: skäl — tiden kapas i stället för att raden kastas, så meningen räknas men
#: dess frånvaro inte.
AVBROTT_MS = 60_000

#: Så många tidtagna meningar krävs i en grupp innan dess median används. Med
#: färre säger medianen mer om vilka tre meningar som råkade mätas än om
#: kostnaden. Samma skäl som `MINSTA_TIDTAGNA` i det gamla systemet, där sex
#: meningar gav en växelkurs som släppte in 813 nya kort.
MINSTA_I_GRUPP = 10


def mät(logg: sqlite3.Connection) -> list[dict]:
    """(bedömda kort, antal meningar, mediansekunder) ur loggen."""
    logg.row_factory = sqlite3.Row
    tid = {r["id"]: min(r["millisekunder"], AVBROTT_MS)
           for r in logg.execute("""SELECT id, millisekunder FROM Mening
                                    WHERE millisekunder IS NOT NULL""")}
    bedömda: dict[int, int] = defaultdict(int)
    for r in logg.execute("""SELECT mening_id FROM Repetition
                             WHERE mening_id IS NOT NULL"""):
        bedömda[r["mening_id"]] += 1

    per_antal: dict[int, list[float]] = defaultdict(list)
    for mening_id, ms in tid.items():
        n = bedömda.get(mening_id, 0)
        if n:
            per_antal[n].append(ms / 1000)
    return [{"kort": n, "meningar": len(v),
             "sekunder": round(statistics.median(v), 2)}
            for n, v in sorted(per_antal.items())]


def anpassa(rader: list[dict]) -> tuple[float, float] | None:
    """(fast kostnad, kostnad per kort) ur grupperna som är stora nog.

    Viktad minsta kvadrat: vikten är antalet meningar, så en grupp med
    tjugonio meningar väger tyngre än en med tretton.
    """
    säkra = [r for r in rader if r["meningar"] >= MINSTA_I_GRUPP]
    if len(säkra) < 2:
        return None
    v = [float(r["meningar"]) for r in säkra]
    x = [float(r["kort"]) for r in säkra]
    y = [float(r["sekunder"]) for r in säkra]
    sv = sum(v)
    mx = sum(a * b for a, b in zip(v, x)) / sv
    my = sum(a * b for a, b in zip(v, y)) / sv
    täljare = sum(a * (b - mx) * (c - my) for a, b, c in zip(v, x, y))
    nämnare = sum(a * (b - mx) ** 2 for a, b in zip(v, x))
    if not nämnare:
        return None
    per_kort = täljare / nämnare
    return my - per_kort * mx, per_kort


def main() -> int:
    fil = Path(sys.argv[1]) if len(sys.argv) > 1 else FIL
    logg = ROT / "kort.db"
    if not logg.exists():
        print(f"ingen logg i {logg} — ingenting att mäta")
        return 1
    rader = mät(sqlite3.connect(logg))
    if not rader:
        print("loggen har inga tidtagna meningar med bedömda kort")
        return 1

    print("  kostnaden per mening, ur den gamla loggen:\n")
    print("    kort   meningar   median sek   sek/kort")
    for r in rader:
        märke = "" if r["meningar"] >= MINSTA_I_GRUPP else "   (för få)"
        print(f"    {r['kort']:>4} {r['meningar']:>10} {r['sekunder']:>12.1f}"
              f" {r['sekunder'] / r['kort']:>10.1f}{märke}")

    säkra = [r for r in rader if r["meningar"] >= MINSTA_I_GRUPP]
    print(f"\n  {len(säkra)} av {len(rader)} grupper har minst "
          f"{MINSTA_I_GRUPP} meningar och används.")
    linje = anpassa(rader)
    if linje is None:
        print("  För få grupper för en linje — tidsmodellen får svara «vet inte».")
    else:
        fast, per_kort = linje
        print(f"\n  anpassad linje:  sekunder = {fast:.1f} + {per_kort:.1f} × kort")
        print(f"    Den FASTA kostnaden är {fast:.1f} s och kortet {per_kort:.1f} s, "
              f"alltså {fast / per_kort:.0f} gånger\n    mer. Det är därför ett extra "
              "MÅL lönar sig — det sparar en hel mening\n    senare — medan ett kort "
              "som inte är mål bara kostar tid (6.3).")
        print("\n    kort   mätt    linjen")
        for r in säkra:
            print(f"    {r['kort']:>4} {r['sekunder']:>6.1f} {fast + per_kort * r['kort']:>9.1f}")

    # Bara mätpunkterna sparas. Linjen räknas om ur dem av den som läser
    # (`anpassa`), så att det finns ETT ställe där de två talen bestäms — och
    # en `#`-rad är ingen kommentar för `csv.DictReader`, den blir rubrik.
    with fil.open("w", encoding="utf-8", newline="") as f:
        skrivare = csv.DictWriter(f, ["kort", "meningar", "sekunder"])
        skrivare.writeheader()
        skrivare.writerows(rader)
    print(f"\n  sparat: {fil}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
