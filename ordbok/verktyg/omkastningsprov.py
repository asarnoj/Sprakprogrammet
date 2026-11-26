"""Prov för omkastningsdetektionen i rättningen.

VARFÖR ETT EGET PROV. `renderarbild.py` fryser vad renderarna producerar och
`ögonblicksbild.py` skyddar datalagret. Rättningen ligger mellan dem och hade
inget nät alls — trots att den är den logiktätaste delen av systemet och den
enda som kan skriva FALSKA rader i inlärarloggen.

VARFÖR JUST DEN HÄR BITEN. `Rättare._flyttade` är ren: in går två ordlistor
och difflibs opkoder, ut går de ord som flyttats. Ingen databas, inget
FSRS-tillstånd, inga id:n som ändras när Julius övar. Ett prov på den delen
åldras alltså inte, till skillnad från ett som fryser hela rättningar.

VAD DEN SKYDDAR MOT. Före omkastningsdetektionen bokförde systemet
"äter jag maten" som att användaren inte kunde ordet `äta` — ordkortet fick
Again och dess stam- och formkort undanhölls. Ordet var rätt skrivet och stod
bara på fel plats. Det är precis den sortens tysta felmätning som kostat mest
i det här projektet, och den ska inte kunna smyga tillbaka.

Kör:  python ordbok/verktyg/omkastningsprov.py
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sprakprog.generator.rattning import Rättare  # noqa: E402

#: (facit, svar, förväntade flyttade ord). Varje rad är en NAMNGIVEN
#: situation, inte ett slumpat par — en diff ska gå att läsa som "det här
#: fallet slutade fungera".
FALL: list[tuple[str, str, str, set[str]]] = [
    ("rak omkastning",
     "jag äter maten", "äter jag maten", {"äter"}),
    # HELVÄNDNING. Semantiskt bytte `jag` och `maten` plats medan `äter`
    # stod still — men difflib förankrar på det FÖRSTA lika långa blocket i
    # facit, alltså `jag`, och då blir `äter`/`maten` paret som ser flyttat
    # ut. Namnen i anmärkningen blir därmed inte de man själv skulle valt.
    #
    # Det är kosmetiskt och aldrig en felmätning: varje ord är antingen
    # matchat eller flaggat som flyttat, så inget ordkort fälls. En riktig
    # minsta-antal-flyttar-analys vore en permutationsdistans, och den
    # byggs om anmärkningstexten visar sig förvirra i praktiken.
    ("helvändning — difflibs förankring, inte minsta antal flyttar",
     "jag äter maten", "maten äter jag", {"äter", "maten"}),
    ("particip flyttat till slutet",
     "ich habe das buch gelesen", "ich habe gelesen das buch", {"gelesen"}),
    ("ren formfel — INGEN omkastning",
     "jag äter maten", "jag äter mat", set()),
    ("flyttat OCH felböjt — bara flytten känns igen",
     "jag äter maten", "äter jag mat", {"äter"}),
    ("extra ord — inte en omkastning",
     "jag äter maten", "jag äter maten idag", set()),
    ("ord saknas — inte en omkastning",
     "jag äter maten", "jag maten", set()),
    ("helt rätt",
     "jag äter maten", "jag äter maten", set()),
    ("felstavning liknar inte en flytt",
     "der hund läuft", "der hnud läuft", set()),
    ("samma ord två gånger — mängd, inte multimängd",
     "hunden ser hunden", "hunden ser katten", set()),
]


def flyttade(facit: str, svar: str) -> set[str]:
    f, s = facit.split(), svar.split()
    opkoder = difflib.SequenceMatcher(None, f, s, autojunk=False).get_opcodes()
    return Rättare._flyttade(f, s, opkoder)


def anklagade(facit: str, svar: str) -> set[str]:
    """Facitord som når skuldstegen, alltså kan få ett kort fällt.

    Andra passets diff efter att de flyttade orden tagits ut: allt som ligger
    i en opkod som INTE är `equal` går vidare till `_skyll`.
    """
    kvar_f, kvar_s = uppriktning(facit, svar)
    sm = difflib.SequenceMatcher(None, kvar_f, kvar_s, autojunk=False)
    return {o for tagg, i1, i2, _, _ in sm.get_opcodes() if tagg != "equal"
            for o in kvar_f[i1:i2]}


def uppriktning(facit: str, svar: str) -> tuple[list[str], list[str]]:
    """Vad som återstår att diffa när de flyttade orden plockats bort.

    Det andra passet är hela poängen med att ta ut dem: ett flyttat ord
    rubbar uppriktningen för sina grannar, så att ett felböjt ord bredvid
    hamnar i en `delete` utan motpart och skylls på ORDET i stället för på
    ändelsen.
    """
    rörda = flyttade(facit, svar)
    return ([o for o in facit.split() if o not in rörda],
            [o for o in svar.split() if o not in rörda])


def main() -> int:
    fel = 0
    for namn, facit, svar, väntat in FALL:
        fick = flyttade(facit, svar)
        if fick == väntat:
            print(f"  ✓ {namn}")
        else:
            fel += 1
            print(f"  ✗ {namn}\n      facit {facit!r}  svar {svar!r}"
                  f"\n      väntade {väntat or '{}'}, fick {fick or '{}'}")

    # Uppriktningen efter andra passet: det felböjda ordet ska stå kvar mot
    # sin rätta motpart, inte mot ingenting.
    f2, s2 = uppriktning("jag äter maten", "äter jag mat")
    if (f2, s2) == (["jag", "maten"], ["jag", "mat"]):
        print("  ✓ andra passet riktar upp resten")
    else:
        fel += 1
        print(f"  ✗ andra passet riktar upp resten: fick {f2} mot {s2}")

    # DEN EGENSKAP SOM FAKTISKT BETYDER NÅGOT, och hela skälet till att koden
    # finns: är svaret en REN OMKASTNING — samma ord, annan ordning — får
    # inget kort fällas alls. Användaren hämtade fram varje ord och böjde
    # varje ord rätt; det enda som brast var ordföljden, och den har inget
    # nåbart kort (A3).
    #
    # Villkoret är avsiktligt formulerat på hela meningen och inte per ord.
    # "ett rätt skrivet ord får aldrig skyllas" vore FÖR starkt: i
    # "hunden ser hunden" mot "hunden ser katten" är den andra `hunden` ett
    # äkta ordfel, och att ordet råkar stå rätt tidigare i meningen ändrar
    # inte det.
    #
    # Utan omkastningsdetektionen faller kontrollen på varje permutationsfall.
    brott = 0
    for namn, facit, svar, _ in FALL:
        if sorted(facit.split()) != sorted(svar.split()):
            continue                       # inte en ren omkastning
        skyllda = anklagade(facit, svar)
        if skyllda:
            brott += 1
            print(f"  ✗ {namn}: ren omkastning, men {skyllda} når skuldstegen")
    fel += brott
    if not brott:
        print("  ✓ ren omkastning fäller inget kort i något fall")

    antal = len(FALL) + 2
    print(f"\n{antal} kontroller, {fel} fel." if fel
          else f"\n{antal} kontroller, alla rätt.")
    return 1 if fel else 0


if __name__ == "__main__":
    raise SystemExit(main())
