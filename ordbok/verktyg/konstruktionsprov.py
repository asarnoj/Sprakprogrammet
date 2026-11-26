"""Prov för de konstruktioner specen fick när de 69 hålen lagades.

VARFÖR DET HÄR PROVET FINNS. `renderarfacit` är nätet under renderarna, men
det prövar bara specar som den GAMLA samplaren bygger, och den känner inte
till demonstrativ, räkneord, kvantifikator, negationens art eller den
självständiga possessiven. De nya fälten har alltså noll täckning där: facit
säger "0 skillnader" oavsett vad de gör.

Det som byggdes verifierades för hand, en gång, i ett engångsskript. Det är
inte ett nät — det är ett minne. Ändrar någon prioritetskedjan i `nominalfras`
i morgon säger ingenting ifrån.

VAD PROVET PRÖVAR, och varför just det:

  TEXTEN ORD FÖR ORD för varje ny konstruktion, i båda språken. Det är hela
  poängen med fälten, och det enda som går att kontrollera utifrån.

  ATT DE VÄGRAR där de ska. "varje böcker" och "två bok" får inte gå att
  bygga, och att de inte gör det beror på data — `numeruskrav` respektive
  kravet på plural — som är lätt att råka tömma.

  ATT DE FEM OBYGGDA SPRÅKEN SÄGER IFRÅN. Ett fält en renderare inte känner
  till syns inte som ett fel, det försvinner: specen "de här två böckerna"
  blir "böckerna", tyst och trovärdigt. `kontrollera_stöd` finns för det, och
  vakten är värdelös om den tystnar.

VILAR INTE PÅ INLÄRARHISTORIKEN. Allt här är spec in, text ut. Provet åldras
inte med Julius övande.

Kör:  python ordbok/verktyg/konstruktionsprov.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.rendering import RENDERARE                          # noqa: E402
from sprakprog.rendering import spec as S                          # noqa: E402

NF, B, N, A, T = (S.Nominalfras, S.Bestämdhet, S.Numerus, S.Aspekt,
                  S.Tidsreferens)

#: Väntat utfall för ett språk som ska vägra frasen i stället för att bygga
#: den. Skilt från en väntad text, och skilt från ett fel i provet.
VÄGRAR = object()

#: Konceptnycklarna provet bygger av. Slås upp på lemmat i stället för att
#: skrivas som nycklar, så att provet inte tyst byter ord om nycklarna döps om.
LEMMAN = {"bok": ("sv", "bok"), "hus": ("sv", "hus"), "flicka": ("sv", "flicka"),
          "läsa": ("sv", "läsa"), "stor": ("sv", "stor"), "vara": ("sv", "vara")}


def _koncept(conn) -> dict[str, str]:
    ut = {}
    for namn, (språk, lemma) in LEMMAN.items():
        rad = conn.execute(
            """SELECT k.nyckel FROM Koncept k JOIN Lexem l ON l.koncept_id = k.id
               WHERE l.språk = ? AND l.lemma = ?""", (språk, lemma)).fetchone()
        if rad is None:
            raise SystemExit(f"provet hittar inget {språk}-lexem med lemmat {lemma!r}")
        ut[namn] = rad[0]
    return ut


def _mening(k, objekt=None, **fält):
    return S.Mening(verb=k["läsa"], subjekt=NF(k["flicka"], B.BESTÄMD),
                    objekt=objekt, **fält)


def fallen(k) -> list[tuple[str, S.Mening, str]]:
    """(namn, mening, väntad text per språk som {språk: text})."""
    bok, hus, stor = k["bok"], k["hus"], k["stor"]
    return [
        ("demonstrativ sg", _mening(k, NF(bok, demonstrativ="demonstrativ_nara")),
         {"sv": "Flickan läser den här boken.", "en": "The girl reads this book."}),
        ("demonstrativ neutrum", _mening(k, NF(hus, demonstrativ="demonstrativ_nara")),
         {"sv": "Flickan läser det här huset.", "en": "The girl reads this house."}),
        ("demonstrativ pl",
         _mening(k, NF(bok, numerus=N.PL, demonstrativ="demonstrativ_nara")),
         {"sv": "Flickan läser de här böckerna.", "en": "The girl reads these books."}),
        ("demonstrativ fjärran",
         _mening(k, NF(bok, demonstrativ="demonstrativ_fjärran")),
         {"sv": "Flickan läser den där boken.", "en": "The girl reads that book."}),
        ("räkneord", _mening(k, NF(bok, numerus=N.PL, räkneord="räkn_2")),
         {"sv": "Flickan läser två böcker.", "en": "The girl reads two books."}),
        ("räkneord i bestämd fras",
         _mening(k, NF(bok, B.BESTÄMD, numerus=N.PL, räkneord="räkn_2")),
         {"sv": "Flickan läser de två böckerna.",
          "en": "The girl reads the two books."}),
        ("hela bestämningen",
         _mening(k, NF(bok, numerus=N.PL, demonstrativ="demonstrativ_nara",
                       räkneord="räkn_2", attribut=(stor,))),
         {"sv": "Flickan läser de här två stora böckerna.",
          "en": "The girl reads these two big books."}),
        ("ordningstal bestämd",
         _mening(k, NF(bok, B.BESTÄMD, attribut=("räkn_ord_2",))),
         {"sv": "Flickan läser den andra boken.",
          "en": "The girl reads the second book."}),
        ("kvantifikator sg", _mening(k, NF(bok, kvantifikator="kvant_varje")),
         {"sv": "Flickan läser varje bok.", "en": "The girl reads each book."}),
        ("kvantifikator pl",
         _mening(k, NF(bok, numerus=N.PL, kvantifikator="kvant_alla")),
         {"sv": "Flickan läser alla böcker.", "en": "The girl reads all books."}),
        # Svenskan bär bestämdheten som suffix och klarar frasen; engelskan
        # kräver ett förbestämningsled som inte är byggt och ska VÄGRA
        # hellre än att tappa bestämdheten ur meningen.
        ("kvantifikator bestämd",
         _mening(k, NF(bok, B.BESTÄMD, numerus=N.PL, kvantifikator="kvant_alla")),
         {"sv": "Flickan läser alla böckerna.", "en": VÄGRAR}),
        ("kvantifikator böjd",
         _mening(k, NF(hus, kvantifikator="kvant_ingen_det")),
         {"sv": "Flickan läser inget hus.", "en": "The girl reads no house."}),
        ("kvantifikator som objekt", _mening(k, NF("kvant_inget")),
         {"sv": "Flickan läser inget.", "en": "The girl reads nothing."}),
        ("kvantifikator som subjekt",
         S.Mening(verb=k["läsa"], subjekt=NF("kvant_ingen"),
                  objekt=NF(bok, B.BESTÄMD)),
         {"sv": "Ingen läser boken.", "en": "Nobody reads the book."}),
        ("negation: aldrig",
         _mening(k, NF(bok, B.BESTÄMD), negerad=True, negation="neg_aldrig"),
         {"sv": "Flickan läser aldrig boken.",
          "en": "The girl never reads the book."}),
        ("negation: aldrig i perfekt",
         _mening(k, NF(bok, B.BESTÄMD), negerad=True, negation="neg_aldrig",
                 aspekt=A.PERFEKT),
         {"sv": "Flickan har aldrig läst boken.",
          "en": "The girl has never read the book."}),
        ("negation: inte kvar i sin form",
         _mening(k, NF(bok, B.BESTÄMD), negerad=True),
         {"sv": "Flickan läser inte boken.",
          "en": "The girl does not read the book."}),
        ("självständig possessiv",
         S.Mening(verb=k["vara"], subjekt=NF(bok, B.BESTÄMD),
                  predikativ=NF(bok, possessiv="poss_1sg", självständig=True)),
         {"sv": "Boken är min.", "en": "The book is mine."}),
        ("självständig possessiv, neutrum",
         S.Mening(verb=k["vara"], subjekt=NF(hus, B.BESTÄMD),
                  predikativ=NF(hus, possessiv="poss_1sg", självständig=True)),
         {"sv": "Huset är mitt.", "en": "The house is mine."}),
        ("självständig possessiv, plural",
         S.Mening(verb=k["vara"], subjekt=NF(bok, B.BESTÄMD, numerus=N.PL),
                  predikativ=NF(bok, numerus=N.PL, possessiv="poss_1sg",
                                självständig=True)),
         {"sv": "Böckerna är mina.", "en": "The books are mine."}),
    ]


def vägrandena(k) -> list[tuple[str, S.Mening, str]]:
    """(namn, mening, ord som måste stå i felmeddelandet). Gäller båda språken."""
    bok = k["bok"]
    return [
        ("varje i plural",
         _mening(k, NF(bok, numerus=N.PL, kvantifikator="kvant_varje")), "tillåter"),
        ("alla i singular",
         _mening(k, NF(bok, kvantifikator="kvant_alla")), "tillåter"),
        ("räkneord i singular",
         _mening(k, NF(bok, räkneord="räkn_2")), "plural"),
        ("självständig utan possessiv",
         S.Mening(verb=k["vara"], subjekt=NF(bok, B.BESTÄMD),
                  predikativ=NF(bok, självständig=True)), "possessiv"),
    ]


def _text(språk: str, m: S.Mening) -> str:
    return RENDERARE[språk](sqlite3.connect(ROT / "sprak.db")).rendera(m)


def main() -> int:
    conn = sqlite3.connect(ROT / "sprak.db")
    k = _koncept(conn)
    brister: list[str] = []

    print("── texten, ord för ord ──")
    for namn, m, väntat in fallen(k):
        rader = []
        for språk, vill in väntat.items():
            try:
                fick = _text(språk, m)
                if vill is VÄGRAR:
                    brister.append(f"{namn} ({språk}): byggde {fick!r} i stället "
                                   f"för att vägra")
                    rader.append(f"      {språk} byggde  {fick}")
                    continue
            except S.RenderingsFel as e:
                if vill is VÄGRAR:
                    continue
                fick = f"RenderingsFel: {e}"
            except Exception as e:                                  # noqa: BLE001
                fick = f"{type(e).__name__}: {e}"
            if vill is not VÄGRAR and fick != vill:
                brister.append(f"{namn} ({språk}): {fick!r}, väntade {vill!r}")
                rader.append(f"      {språk} fick   {fick}")
                rader.append(f"      {språk} väntade {vill}")
        print(f"  {'✓' if not rader else '✗'} {namn}")
        for r in rader:
            print(r)

    print("\n── det som måste vägras ──")
    for namn, m, ordet in vägrandena(k):
        rader = []
        for språk in ("sv", "en"):
            try:
                fick = _text(språk, m)
                rader.append(f"      {språk} byggde {fick!r} i stället för att vägra")
            except S.RenderingsFel as e:
                if ordet not in str(e):
                    rader.append(f"      {språk} vägrade, men utan att nämna "
                                 f"{ordet!r}: {e}")
            except Exception as e:                                  # noqa: BLE001
                rader.append(f"      {språk} gav {type(e).__name__} i stället "
                             f"för RenderingsFel: {e}")
        brister += rader
        print(f"  {'✓' if not rader else '✗'} {namn}")
        for r in rader:
            print(r)

    print("\n── vakten i de fem språk som inte byggt leden ──")
    led = {"demonstrativ": "demonstrativ_nara", "kvantifikator": "kvant_varje",
           "räkneord": "räkn_2", "självständig": True}
    for språk in ("de", "fr", "es", "it", "ja"):
        tysta = []
        for namn, värde in led.items():
            extra = {namn: värde}
            if namn == "räkneord":
                extra["numerus"] = N.PL
            if namn == "självständig":
                extra["possessiv"] = "poss_1sg"
            m = _mening(k, NF(k["bok"], **extra))
            try:
                _text(språk, m)
                tysta.append(namn)
            except S.RenderingsFel:
                pass
            except Exception:                                       # noqa: BLE001
                pass          # något annat vägrade först — leden syns ändå inte
        if tysta:
            brister.append(f"{språk} renderade {', '.join(tysta)} utan att bygga dem")
        print(f"  {'✓' if not tysta else '✗'} {språk}"
              + (f"   tyst om: {', '.join(tysta)}" if tysta else ""))

    antal = len(fallen(k)) * 2 + len(vägrandena(k)) * 2 + 5
    print(f"\n{antal} kontroller, {len(brister)} brister." if brister
          else f"\n{antal} kontroller, allt håller.")
    for b in brister[:15]:
        print(f"  {b}")
    return 1 if brister else 0


if __name__ == "__main__":
    raise SystemExit(main())
