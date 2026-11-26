"""Svep över FELTYPER: vad gör rättningen när man skriver fel på olika sätt?

VARFÖR DET HÄR VERKTYGET FINNS. Attributionen har lagats fem gånger, varje
gång utifrån ETT fall Julius råkade skriva. Det är en dålig metod: varje
lagning ser komplett ut tills nästa mening avslöjar nästa hål, och ingen vet
hur många hål som är kvar. Frågan "kommer det här någonsin bli bra?" går inte
att besvara med anekdoter — den behöver ett tal.

Svepet genererar meningar, förstör dem på ett KÄNT sätt, och kontrollerar tre
saker i fallande allvarlighetsgrad:

    FALSKT GODKÄNNANDE   ett kort som INTE visades fick Good. Det enda felet
                         som är värre än inget betyg: FSRS skjuter kortet
                         längre bort just när användaren visat motsatsen, och
                         raden ser exakt ut som en äkta. Allt annat går att
                         upptäcka; det här ljuger vidare i veckor.

    FEL SKULD            något föll, men inte det som brast. Kortet får en
                         repetition det inte förtjänade och det rätta förblir
                         svagt. Läker delvis av sig självt (D1, pinne 7).

    TYSTNAD              inget mättes. Slöseri, inte lögn — och enligt
                         modulens egen regel rätt svar när datan inte räcker.

MUTATIONERNA ÄR VALDA SÅ ATT DET RÄTTA SVARET ÄR KÄNT I FÖRVÄG. Byter man ut
ändelsen mot en annan cells ändelse VET vi att det är systemkortet som ska
falla. Det är skillnaden mot att läsa utdata och tycka att den ser rimlig ut.

Kör:  python ordbok/verktyg/felsvep.py [språk...] [--meningar N] [--visa]
"""

from __future__ import annotations

import random
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut                          # noqa: E402
from sprakprog.generator import Förslag, Generator       # noqa: E402
from sprakprog.generator.rattning import (               # noqa: E402
    ORDMELLANRUM, _normalisera,
)

#: Hur många meningar per språk. Varje mening muteras på varje tillämpligt
#: sätt, så antalet prövningar blir flera gånger detta.
MENINGAR = 40

#: Nivån svepet arbetar på. Högre ger fler konstruktioner — bisatser, frågor,
#: två objekt — och därmed fler sorters fel att göra.
NIVÅ = 6


def _bygg(kort, språk: str, antal: int) -> list:
    """Meningar med hela ordförrådet öppet, plus deras beroendekartor."""
    g = Generator(anslut(), kort, språk, källspråk="sv", nivå=NIVÅ,
                  cefr="A1", frö=17)
    g._läs_kort()
    ut = []
    for _ in range(antal * 60):
        if len(ut) >= antal:
            break
        m = g.samplare.kandidat()
        if m is None or g.validator.validera(m):
            continue
        r = g._rendera(m)
        if r is None or len(r[0].split()) < 3:
            continue
        ut.append((m, r))
    return g, ut


# ── mutationerna ────────────────────────────────────────────────────
#
# Var och en returnerar (svar, väntad_korttyp, brutet_uppslag) eller None när
# den inte går att göra på just den meningen. `brutet_uppslag` är den
# (koncept, variant, cell) vi avsiktligt förstörde — det är den som gör
# kontrollen exakt i stället för ungefärlig.

def _byt_ord(text: str, från: str, till: str) -> str | None:
    """Byt ut ett HELT ORD, inte en delsträng.

    `text.replace` bryr sig inte om ordgränser: att byta `der` mot `ein` i
    `Der Bruder benutzt…` gav `Der Bruein benutzt…`. Mutationen förstörde då
    ett ord i stället för att byta cell, och svepet rapporterade det som ett
    fel i RÄTTNINGEN — vilket det inte var. Ett svep som muterar slarvigt
    mäter sig självt.
    """
    ord_ = text.split()
    for i, o in enumerate(ord_):
        naket = o.strip(".?!,")
        if naket.lower() == från.lower():
            ord_[i] = o.replace(naket, till)
            return " ".join(ord_)
    return None


def _annan_cell(rt, text, uppslag, rng):
    """Byt en form mot en ANNAN CELL av samma ord: ren böjningsfel."""
    for koncept, variant, cell in rng.sample(uppslag, len(uppslag)):
        celler = rt._celler_för(koncept, variant)
        rätt = celler.get(cell)
        andra = [(c, f) for c, f in celler.items() if c != cell and f
                 and f != rätt and " " not in f]
        if not rätt or not andra or rätt not in text:
            continue
        skriven_cell, skriven_form = rng.choice(andra)
        ny = _byt_ord(text, rätt, skriven_form)
        if ny is None:
            continue
        return (ny, ("system", "stam", "form", "egenskap"),
                (koncept, variant, cell, skriven_cell))
    return None


def _annat_ord(rt, text, uppslag, rng, alla_former):
    """Byt ut en form mot ett HELT ANNAT ords form: rent lexikalt fel."""
    for koncept, variant, cell in rng.sample(uppslag, len(uppslag)):
        rätt = rt._celler_för(koncept, variant).get(cell)
        if not rätt or rätt not in text:
            continue
        främmande = [f for f in alla_former if f and f != rätt
                     and not f.startswith(rätt[:2]) and " " not in f]
        if not främmande:
            continue
        ny = _byt_ord(text, rätt, rng.choice(främmande))
        if ny is None:
            continue
        return (ny, ("ord",), (koncept, variant, cell))
    return None


def _utelämnat(rt, text, uppslag, rng):
    """Stryk ett ord helt."""
    ord_ = text.rstrip(".?!").split()
    if len(ord_) < 3:
        return None
    i = rng.randrange(len(ord_))
    return (" ".join(ord_[:i] + ord_[i + 1:]), None, None)


def _extra_ord(rt, text, uppslag, rng, alla_former):
    """Lägg till ett ord som inte hör dit."""
    if not alla_former:
        return None
    ord_ = text.rstrip(".?!").split()
    i = rng.randrange(len(ord_) + 1)
    extra = rng.choice([f for f in alla_former if f and " " not in f])
    return (" ".join(ord_[:i] + [extra] + ord_[i:]), None, None)


def _omkastning(rt, text, uppslag, rng):
    """Kasta om två grannord — rätt ord, fel plats."""
    ord_ = text.rstrip(".?!").split()
    if len(ord_) < 3 or any("'" in o for o in ord_):
        return None
    i = rng.randrange(len(ord_) - 1)
    if ord_[i].lower() == ord_[i + 1].lower():
        return None
    ord_[i], ord_[i + 1] = ord_[i + 1], ord_[i]
    return (" ".join(ord_), None, None)


def _stavfel(rt, text, uppslag, rng):
    """Byt en bokstav inne i ett ord."""
    ord_ = text.rstrip(".?!").split()
    långa = [i for i, o in enumerate(ord_) if len(o) > 3]
    if not långa:
        return None
    i = rng.choice(långa)
    j = rng.randrange(1, len(ord_[i]))
    o = ord_[i]
    ord_[i] = o[:j] + ("x" if o[j] != "x" else "q") + o[j + 1:]
    return (" ".join(ord_), None, None)


def _missad_sandhi(rt, text, uppslag, rng, osammansmält):
    """Skriv isär det som ska smälta samman — bara där sandhi faktiskt slår ihop."""
    if not osammansmält or not rt._smälter_ihop(osammansmält):
        return None
    return (" ".join(osammansmält), None, None)


def _rätt_svar(rt, text, uppslag, rng):
    """Kontrollen mot falska LARM: ett rätt svar får inte fälla något."""
    return (text, None, None)


# ── körningen ───────────────────────────────────────────────────────

def svep(kort, språk: str, antal: int, visa: bool) -> Counter:
    rng = random.Random(11)
    g, meningar = _bygg(kort, språk, antal)
    rt = g.rättare
    alla_former = [r["facit"] for r in kort.execute(
        """SELECT facit FROM Kort WHERE språk = ? AND typ IN ('ord','form')
           AND facit IS NOT NULL AND facit <> ''""", (språk,))]
    räknare: Counter = Counter()

    for m, (text, kl, upp, eg, rk, of, osm) in meningar:
        f = Förslag(m, text, None, kl, None, upp, eg, rk, of, False, osm)
        muterade = [
            ("rätt svar", _rätt_svar(rt, text, upp, rng)),
            ("annan cell (böjningsfel)", _annan_cell(rt, text, upp, rng)),
            ("annat ord (lexikalt)", _annat_ord(rt, text, upp, rng, alla_former)),
            ("utelämnat ord", _utelämnat(rt, text, upp, rng)),
            ("extra ord", _extra_ord(rt, text, upp, rng, alla_former)),
            ("omkastning", _omkastning(rt, text, upp, rng)),
            ("stavfel", _stavfel(rt, text, upp, rng)),
            ("missad sandhi", _missad_sandhi(rt, text, upp, rng, osm)),
        ]
        for namn, mut in muterade:
            if mut is None:
                continue
            svar, väntad, brutet = mut
            if _normalisera(svar) == _normalisera(text) and namn != "rätt svar":
                continue
            r = g.rätta(f, svar)
            räknare[f"{namn}|n"] += 1

            if namn == "rätt svar":
                if not r.korrekt or any(not v for v in r.utfall.values()):
                    räknare[f"{namn}|FALSKT LARM"] += 1
                    if visa:
                        print(f"    FALSKT LARM {text!r}")
                continue

            # FALSKT GODKÄNNANDE: korten bakom den form vi avsiktligt bröt
            # får inte ha fått Good. Frågan går via uppslaget och inte via
            # strängjämförelse — samma väg som `_kan_ha_burit`.
            if brutet is not None:
                koncept, variant, cell = brutet[:3]
                bakom = {k["id"] for k in rt._kort_för(koncept, variant, cell)}
                if len(brutet) > 3:
                    # BARA DET SOM SKILJER CELLERNA ÅT. En STAM spänner över
                    # celler per definition — skriver man `Lehrers` för
                    # `Lehrer` har man visat stammen — och ordkortet likaså.
                    # Avdraget nedan räcker inte ensamt: har den skrivna
                    # cellen inga kort alls blir mängden tom och stammen
                    # räknas som falskt godkänd. Därför filtreras det som
                    # KAN skilja: ändelsen, eller hela formen när ordet är
                    # oregelbundet.
                    bakom = {k["id"] for k in rt._kort_för(koncept, variant, cell)
                             if k["typ"] in ("system", "form", "egenskap")}
                    # SKREV ANVÄNDAREN EN ANNAN CELL AV SAMMA ORD har hon
                    # ändå visat det de två cellerna DELAR — stammen, och
                    # ordet självt. `pompiers` för `pompier` är fel numerus
                    # och rätt stam, och att kräva att stamkortet faller vore
                    # att kräva ett falskt betyg åt andra hållet.
                    #
                    # Kontrollen gäller därför bara det som skiljer cellerna
                    # åt: ändelsen. Första versionen av svepet saknade
                    # avdraget och rapporterade 16 falska godkännanden som
                    # alla var korrekta bedömningar.
                    bakom -= {k["id"] for k in
                              rt._kort_för(koncept, variant, brutet[3])}
                else:
                    ordkort = rt._ordkort(koncept, variant)
                    if ordkort:
                        bakom.add(ordkort["id"])
                if any(r.utfall.get(k) for k in bakom):
                    räknare[f"{namn}|FALSKT GODKÄNNANDE"] += 1
                    if visa:
                        print(f"    FALSKT GODK  {text!r} → {svar!r}")
            if not r.utfall or all(v for v in r.utfall.values()):
                räknare[f"{namn}|tyst"] += 1
                continue
            fällda = {kort.execute("SELECT typ FROM Kort WHERE id = ?",
                                   (k,)).fetchone()["typ"]
                      for k, v in r.utfall.items() if not v}
            if väntad:
                if fällda & set(väntad):
                    räknare[f"{namn}|rätt typ"] += 1
                else:
                    räknare[f"{namn}|fel typ"] += 1
                    if visa:
                        print(f"    FEL TYP      {text!r} → {svar!r}  "
                              f"fällde {sorted(fällda)}, väntat {väntad}")
            else:
                räknare[f"{namn}|fällde något"] += 1
    return räknare


def main() -> int:
    argv = sys.argv[1:]
    visa = "--visa" in argv
    antal = MENINGAR
    if "--meningar" in argv:
        antal = int(argv[argv.index("--meningar") + 1])
    språken = [a for a in argv if a in ORDMELLANRUM] or ["fr", "de", "en", "sv"]

    with tempfile.TemporaryDirectory() as tmp:
        kopia = Path(tmp) / "k.db"
        käll = sqlite3.connect(ROT / "kort.db")
        dst = sqlite3.connect(kopia)
        try:
            käll.backup(dst)
        finally:
            dst.close()
            käll.close()
        kort = sqlite3.connect(kopia)
        kort.row_factory = sqlite3.Row
        for s in språken:
            kort.execute(
                "UPDATE Kort SET sedd = '2026-01-01T00:00:00+00:00' WHERE språk = ?",
                (s,))
        kort.commit()

        allt: dict[str, Counter] = {}
        for s in språken:
            # SPRÅK UTAN KORT HOPPAS ÖVER. Svenskan är källspråk och har
            # ingen kortlek — där finns ingen rättning att pröva.
            if not kort.execute(
                    "SELECT 1 FROM Kort WHERE språk = ? LIMIT 1", (s,)).fetchone():
                print(f"\n{s.upper()}: ingen kortlek — hoppas över")
                continue
            print(f"\n{'═' * 72}\n{s.upper()}  ({antal} meningar, nivå {NIVÅ})\n{'═' * 72}")
            r = svep(kort, s, antal, visa)
            allt[s] = r
            namn = sorted({k.split("|")[0] for k in r})
            print(f"  {'feltyp':26s} {'n':>4} {'rätt typ':>9} {'fel typ':>8} "
                  f"{'tyst':>6} {'FALSKT':>7}")
            for n in namn:
                falskt = (r[f"{n}|FALSKT GODKÄNNANDE"]
                          + r[f"{n}|FALSKT LARM"])
                print(f"  {n:26s} {r[f'{n}|n']:>4} {r[f'{n}|rätt typ']:>9} "
                      f"{r[f'{n}|fel typ']:>8} {r[f'{n}|tyst']:>6} "
                      f"{falskt:>7}")

        print(f"\n{'═' * 72}\nSAMMANLAGT — det enda talet som får vara noll\n{'═' * 72}")
        for s, r in allt.items():
            n = sum(v for k, v in r.items() if k.endswith("|n"))
            falskt = sum(v for k, v in r.items()
                         if "FALSKT" in k)
            tyst = sum(v for k, v in r.items() if k.endswith("|tyst"))
            felt = sum(v for k, v in r.items() if k.endswith("|fel typ"))
            print(f"  {s}: {n:4d} prövningar   falska betyg {falskt:3d}   "
                  f"fel skuld {felt:3d}   tysta {tyst:3d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
