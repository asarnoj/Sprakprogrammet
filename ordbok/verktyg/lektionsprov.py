"""Lektionerna — finns en för varje steg, och beskriver den rätt sak?

HÅLET SOM GJORDE PROVET NÖDVÄNDIGT. Inget nät rörde lektionskoden när
böjningsdimensionerna flätades in i nivåstegen (F5b). Följden mättes efteråt:
franskans steg 21 visade rubriken "Wh-questions" men var i verkligheten
`inf`-böjningen, och steg 22 fanns inte i tabellen alls — ett klick dit hade
kastat `KeyError`. Tretton nät var gröna hela tiden.

Felet var inte svårt att se; det var osett. En hel vy utan en enda invariant
är en vy som bara användaren provkör.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut                                  # noqa: E402
from sprakprog.generator.urval import NIVÅ                       # noqa: E402
from sprakprog.kort.db import STANDARD_KORT_DB                   # noqa: E402
from sprakprog.kort.dimensioner import (                         # noqa: E402
    nivåns_krav, stege, toppnivå,
)
from sprakprog.webb.lektion import LEKTIONER, Lektioner          # noqa: E402

SPRÅK = ("sv", "en", "de", "fr", "es", "it", "ja")


def _lektioner():
    kort = sqlite3.connect(f"file:{STANDARD_KORT_DB}?mode=ro", uri=True)
    kort.row_factory = sqlite3.Row
    return Lektioner(anslut(), kort)


def prov_varje_steg_har_en_lektion() -> list[str]:
    """Varje nivå i varje språks stege ska ha en text — ingen `KeyError`.

    Det var precis det som brast: `LEKTIONER` var nycklad på nivåTALET, så
    tabellen slutade vid 21 medan franskans stege är 22 steg och japanskans
    24. Provet går igenom hela stegen i alla sju språken.
    """
    fel = []
    for språk in SPRÅK:
        for nivå in range(1, toppnivå(språk) + 1):
            nyckel = Lektioner._nyckel_för(språk, nivå)
            if nyckel not in LEKTIONER:
                fel.append(f"{språk} nivå {nivå}: ingen lektion för {nyckel!r}")
    return fel


def prov_texten_beskriver_steget() -> list[str]:
    """Lektionens nyckel ska vara det steget FAKTISKT är.

    DEN TYSTA HALVAN AV FELET. Att en text finns säger inget om att det är
    RÄTT text: franskans steg 21 hade en — "Wh-questions" — och den beskrev
    ett steg som lär ut infinitiv. En felparad lektion är värre än en som
    saknas, eftersom den inte klagar.
    """
    fel = []
    for språk in SPRÅK:
        for nivå in range(1, toppnivå(språk) + 1):
            nyckel = Lektioner._nyckel_för(språk, nivå)
            konstruktion, celler = nivåns_krav(språk, nivå)
            if nivå == 1:
                väntat = "grund"
            elif konstruktion is not None:
                väntat = konstruktion
            else:
                väntat = "böjning"
            if nyckel != väntat:
                fel.append(f"{språk} nivå {nivå}: visar {nyckel!r} men steget "
                           f"är {väntat!r}")
            # Och konstruktionsnamnet måste finnas i NIVÅ — annars är det en
            # nyckel någon hittat på.
            if (konstruktion is not None
                    and konstruktion not in NIVÅ.values()):
                fel.append(f"{språk} nivå {nivå}: {konstruktion!r} är ingen "
                           f"konstruktion i NIVÅ")
    return fel


def prov_listan_följer_stegen() -> list[str]:
    """`lista()` ska ge exakt stegens längd, i stegens ordning.

    Den itererade `LEKTIONER` och gav därför alltid 21 rader oavsett språk —
    fel antal i alla sju, och fel ordning så snart ett böjningssteg låg
    mellan två konstruktioner.
    """
    L = _lektioner()
    fel = []
    for språk in SPRÅK:
        rader = L.lista(språk, 1, "A1")
        väntat = toppnivå(språk)
        if len(rader) != väntat:
            fel.append(f"{språk}: lista() gav {len(rader)} rader, stegen har "
                       f"{väntat}")
            continue
        if [r["nivå"] for r in rader] != list(range(1, väntat + 1)):
            fel.append(f"{språk}: nivåerna är inte 1…{väntat} i ordning")
        for r in rader:
            if r["nyckel"] != Lektioner._nyckel_för(språk, r["nivå"]):
                fel.append(f"{språk} nivå {r['nivå']}: listans nyckel "
                           f"{r['nyckel']!r} matchar inte steget")
    return fel


def prov_upplåst_stämmer() -> list[str]:
    """Ett steg är upplåst när dess nivå är ≤ kursens, inget annat."""
    L = _lektioner()
    fel = []
    for språk in SPRÅK:
        for kursnivå in (1, 5, toppnivå(språk)):
            for r in L.lista(språk, kursnivå, "A1"):
                if r["upplåst"] != (r["nivå"] <= kursnivå):
                    fel.append(f"{språk} kurs på {kursnivå}: nivå {r['nivå']} "
                               f"upplåst={r['upplåst']}")
    return fel


PROV = [("varje steg har en lektion", prov_varje_steg_har_en_lektion),
        ("texten beskriver steget", prov_texten_beskriver_steget),
        ("listan följer stegen", prov_listan_följer_stegen),
        ("upplåst stämmer med kursnivån", prov_upplåst_stämmer)]


# ── falsifiering ────────────────────────────────────────────────────

def _sabotage_nyckel_på_nivåtal():
    """Före rättelsen: lektionen slogs upp på nivåTALET, inte på steget.

    TROGET MOT FELET, och det krävde ett andra försök. Första sabotaget
    hade `gamla.get(nivå, "grund")` — en fallback som aldrig missar, så
    "varje steg har en lektion" höll och såg stum ut. Den gamla koden var
    `LEKTIONER[nivå]` med en heltalsnycklad tabell som slutade vid 21: över
    det kastade den. Sabotaget måste alltså sakna nyckel, inte falla tillbaka.
    """
    import sprakprog.webb.lektion as m
    gamla = dict(NIVÅ)
    gamla[1] = "grund"
    äkta = m.Lektioner._nyckel_för
    m.Lektioner._nyckel_för = staticmethod(
        lambda språk, nivå: gamla.get(nivå, f"#saknas:{nivå}"))
    # `staticmethod` VID ÅTERSTÄLLNINGEN. `äkta` är den nakna funktionen —
    # deskriptorn har redan löst upp sig — så att sätta tillbaka den rakt av
    # gör den till en instansmetod, och nästa anrop får `self` som första
    # argument. Det syntes som `takes 2 positional arguments but 3 were
    # given` i NÄSTA prov, inte i det här.
    return lambda: setattr(m.Lektioner, "_nyckel_för", staticmethod(äkta))


def _sabotage_upplåst_på_tabellen():
    """Före rättelsen: upplåstheten räknades mot LEKTIONER-tabellens index."""
    import sprakprog.webb.lektion as m
    äkta = m.Lektioner.lista
    def gammal(själv, språk, nivå, cefr):
        rader = äkta(själv, språk, nivå, cefr)
        # Index i tabellen i stället för stegets nivå — samma sorts
        # förväxling som gjorde listan 21 rader lång.
        for i, r in enumerate(rader, 1):
            r["upplåst"] = i <= nivå + 1
        return rader
    m.Lektioner.lista = gammal
    return lambda: setattr(m.Lektioner, "lista", äkta)


def _sabotage_lista_över_tabellen():
    """Före rättelsen: `lista()` itererade LEKTIONER, alltid 21 rader."""
    import sprakprog.webb.lektion as m
    äkta = m.Lektioner.lista
    def gammal(själv, språk, nivå, cefr):
        return [{"nivå": i, "titel": LEKTIONER[n]["titel"], "nyckel": n,
                 "upplåst": i <= nivå}
                for i, n in enumerate(sorted(LEKTIONER), 1)]
    m.Lektioner.lista = gammal
    return lambda: setattr(m.Lektioner, "lista", äkta)


SABOTAGE = [(_sabotage_nyckel_på_nivåtal, 0),
            (_sabotage_nyckel_på_nivåtal, 1),
            (_sabotage_lista_över_tabellen, 2),
            (_sabotage_upplåst_på_tabellen, 3)]


def main() -> int:
    print("lektionerna — en per steg, och rätt en\n")
    print(f"  stegens längd: "
          + ", ".join(f"{s}:{toppnivå(s)}" for s in SPRÅK) + "\n")
    fel = 0
    for namn, prov in PROV:
        rader = prov()
        fel += bool(rader)
        print(f"  {'✓' if not rader else '✗'} {namn}")
        for r in rader[:4]:
            print(f"      {r}")
        if len(rader) > 4:
            print(f"      … och {len(rader) - 4} till")

    print("\nfalsifiering — varje invariant mot sitt eget sabotage:")
    stumma = []
    for sabotera, i in SABOTAGE:
        namn, prov = PROV[i]
        ångra = sabotera()
        try:
            höll = not prov()
        finally:
            ångra()
        if höll:
            stumma.append(namn)
        print(f"  {'✗ STUM' if höll else '✓ föll'}  {namn}"
              f"  ← {sabotera.__doc__.splitlines()[0]}")

    print(f"\n{len(PROV)} invarianter, {fel} brott, {len(stumma)} stumma.")
    return 1 if fel or stumma else 0


if __name__ == "__main__":
    raise SystemExit(main())
