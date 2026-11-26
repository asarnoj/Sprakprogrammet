"""Prov för samplarens specar: en kandidat är HEL eller så finns den inte.

VARFÖR PROVET FINNS. `Samplare._välj` ger upp — den returnerar `None` när
begränsningen till kända ord tömt en slot, och det är riktigt (se dess egen
docstring: "GER UPP HELLRE ÄN FALLER TILLBAKA"). Men `None` är ett svar som
måste hanteras, och det gjorde tolv av fjorton anropsställen inte. De byggde
specen ändå, med ett hål i.

MÄTT 2026-08-26, före rättelsen, 3 000 kandidater per språk och nivå med
begränsat ordförråd:

    nivå  5   `Attribut(None)`              4–24 % av kandidaterna
    nivå  5   `Nominalfras(None)` i objekt  0–10 %
    nivå  8   naket `None` i `adverbial`   ~15 %
    nivå 15   `Prepositionsfras(None, …)`  ~20 %
    nivå 20   `self.o.verb[None]`           KeyError

DE TVÅ SORTERNAS SKADA ÄR OLIKA, och båda är dyra:

    tyst    `Attribut(None)` och `Nominalfras(None)` gav `RenderingsFel`,
            som `Generator._rendera` fångar och svarar `None` på. Kandidaten
            kastades alltså utan att något räknade det — 27 % av engelskans
            sökning på nivå 5 gick till spillo för en orsak ingen mätte.

    hård    ett naket `None` i `adverbial` träffar renderarens `else`-gren,
            som läser `.preposition`. Det ger `AttributeError`, och den
            ligger UTANFÖR de undantag `_rendera` fångar
            (`RenderingsFel, KeyError, ValueError`) — alltså en krasch rakt
            ut ur `föreslå`. Mätt föll 40 av 40 anrop för de, en och fr på
            nivå 21, och varje anrop till `ordbok öva` med den.

VARFÖR DET INTE SYNTES. Konstruktionerna låses upp med nivån: `attribut` vid
5, `adverbial` vid 8, `prepositionsfras` vid 15, `bisats` vid 20. Julius
kurser stod på nivå 1 och 4, alltså ETT steg under den första fällan. Felet
var därför osynligt i drift och hundraprocentigt i varje verktyg som öppnar
hela stegen — och det hade slagit till första dagen tyskan nådde nivå 5.

REGELN PROVET VAKTAR: en spec som lämnar samplaren är hel. Skillnaden mellan
en utsmyckning som hoppas över och en obligatorisk slot som kastar
kandidaten hör till `_välj`s docstring; här mäts bara resultatet, eftersom
det är resultatet renderaren möter.

ALDRIG MOT DEN RIKTIGA DATABASEN — kopia via SQLites backup, som de andra
proven. Provet LÄSER visserligen bara: det samplar kandidater och anropar
`föreslå`, aldrig `svara` eller `registrera`. Men regeln är inte "skriv inte"
utan "rör den inte", och det av ett skäl: vad ett prov råkar anropa ändras när
koden under det ändras, och då är skyddet borta just när det behövs. Julius
kan dessutom öva i en annan flik medan provet kör.

Kör:  python ordbok/verktyg/samplarprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut  # noqa: E402
from sprakprog.generator import Generator  # noqa: E402
from sprakprog.kort import anslut_kort  # noqa: E402

#: Nivåerna där de fyra hålen satt, plus toppen. Varje tal är en
#: konstruktion som låses upp och inte en jämn spridning: 5 attribut,
#: 8 adverbial, 15 prepositionsfras, 20 bisats, 21 allt.
NIVÅER = (5, 8, 15, 20, 21)

#: Så många kandidater per (språk, nivå). Andelen defekta låg på 4–24 %, så
#: några hundra räcker för att en regression ska synas med marginal.
KANDIDATER = 800


def _språk_med_kortlek(kort: sqlite3.Connection) -> list[str]:
    """Bara språk som har kort. Ett tomt bestånd bygger inga kandidater alls,
    och ett prov över noll kandidater är ett prov som inte kan falla."""
    return [r["språk"] for r in kort.execute(
        "SELECT språk, COUNT(*) AS n FROM Kort GROUP BY språk HAVING n > 50"
        " ORDER BY språk")]


def _hål(m) -> list[str]:
    """Vilka hål specen bär. Tom lista = hel spec."""
    fynd: list[str] = []
    if m.verb is None:
        fynd.append("verb=None")
    for nf, namn in ((m.subjekt, "subjekt"), (m.objekt, "objekt"), (m.io, "io")):
        if nf is None:
            continue
        if nf.koncept is None:
            fynd.append(f"{namn}.koncept=None")
        for a in nf.attribut:
            if a.koncept is None:
                fynd.append(f"{namn}.attribut=None")
        if getattr(nf, "ägare", None) is not None and nf.ägare.koncept is None:
            fynd.append(f"{namn}.ägare=None")
    for a in m.adverbial:
        if a is None:
            fynd.append("adverbial=None")
        elif not isinstance(a, str) and getattr(a, "preposition", "x") is None:
            fynd.append("prepositionsfras.preposition=None")
    if m.predikativ is not None and getattr(
            m.predikativ, "koncept", m.predikativ) is None:
        fynd.append("predikativ=None")
    if m.bisats is not None:
        # Bisatsen bär en HEL Mening, så hålen där är samma hål. Rekursionen
        # kostar ingenting (djupet är ett — en bisats tar ingen bisats) och
        # sparar en andra uppsättning kontroller som skulle kunna glida isär
        # från de här.
        if m.bisats.sats.verb is None:
            fynd.append("bisats.verb=None")
        else:
            fynd += [f"bisats.{h}" for h in _hål(m.bisats.sats)]
    return fynd


def prov_hela_specar(kort, språk_db) -> list[str]:
    """Ingen kandidat får lämna samplaren med ett hål i.

    BEGRÄNSNINGEN MÅSTE VARA PÅ, annars mäter provet ingenting: `_välj` kan
    bara ge `None` när `känt` är satt, och det är `Generator.föreslå` som
    sätter det. Utan `begränsa` väljs alltid ur hela ordförrådet och varje
    slot går att fylla.
    """
    fel = []
    for s in _språk_med_kortlek(kort):
        for nivå in NIVÅER:
            g = Generator(språk_db, kort, s, nivå=nivå, cefr="A1")
            g._läs_kort()
            g.samplare.begränsa(g._sedda_koncept())
            hål: dict[str, int] = {}
            for _ in range(KANDIDATER):
                try:
                    m = g.samplare.kandidat()
                except Exception as e:                       # noqa: BLE001
                    hål[f"KRASCH {type(e).__name__}"] = hål.get(
                        f"KRASCH {type(e).__name__}", 0) + 1
                    continue
                if m is None:
                    continue
                for h in _hål(m):
                    hål[h] = hål.get(h, 0) + 1
            if hål:
                fel.append(f"[{s} nivå {nivå}] {hål}")
    return fel


def prov_föreslå_kraschar_inte(kort, språk_db) -> list[str]:
    """`föreslå` får svara `None`, aldrig kasta.

    Det är den ENDA av de två kontrollerna som mäter det användaren faktiskt
    drabbades av. Specen kan ha ett hål utan att kandidaten råkar renderas;
    här går hela kedjan sampla → rendera → poängsätt, och ett undantag som
    tar sig ut ur den når webbtjänsten som ett femhundrasvar.
    """
    fel = []
    for s in _språk_med_kortlek(kort):
        for nivå in (8, 21):
            g = Generator(språk_db, kort, s, nivå=nivå, cefr="A1")
            for _ in range(10):
                try:
                    g.föreslå(kandidater=200)
                except Exception as e:                       # noqa: BLE001
                    fel.append(f"[{s} nivå {nivå}] {type(e).__name__}: {e}")
                    break
    return fel


PROV = [("varje spec är hel", prov_hela_specar),
        ("föreslå kastar aldrig", prov_föreslå_kraschar_inte)]


# ── falsifiering ────────────────────────────────────────────────────
#
# SABOTAGET ANGRIPER SPECEN, INTE `_välj`, och det är ett medvetet val värt
# att förklara — den uppenbara vägen prövades först och var STUM.
#
# Grindarna sitter numera i `kandidat` och `_nf`. Ett sabotage som bara gör
# `_välj` mer benägen att ge upp kan därför aldrig få den rättade koden att
# bygga ett hål: grinden hoppar över konstruktionen precis som den ska. Och
# gör man `_välj` snål på ALLT kastas varje kandidat redan på `verb is None`,
# så ingen spec byggs och provet blir grönt av fel skäl. Det var precis vad
# första försöket gjorde.
#
# Att i stället kopiera in den gamla `kandidat` vore hundratrettio rader som
# ruttnar isär från originalet. Kvar står det ärliga: injicera de FYRA
# historiska hålformerna i den färdiga specen och kräv att provet ser dem.
#
# Vad det då bevisar är avgränsat men är just det som kan rutta: att `_hål`
# och riggen faktiskt KAN falla. Ett prov vars kontroll tystnar när specen
# ändrar form är värre än inget, och det har hänt i det här projektet förut
# (`omkastningsprov`s första invariant var tom och kunde inte falla).

def _sabotage_hål_i_specen():
    """Före rättelsen: `Attribut(None)`, `None` i adverbial, prep utan ord."""
    from dataclasses import replace

    from sprakprog.generator.urval import Samplare
    from sprakprog.rendering import Attribut, Grad, Prepositionsfras
    orig = Samplare.kandidat

    def hålig(själv, *, kring=None):
        m = orig(själv, kring=kring)
        if m is None:
            return None
        # Var fjärde kandidat får ett hål, i tur och ordning över de fyra
        # formerna — så att ingen enskild kontroll kan bära hela provet.
        n = själv.rng.randrange(5)
        if n == 0 and m.subjekt is not None:
            return replace(m, subjekt=replace(
                m.subjekt, attribut=(Attribut(None, Grad.POSITIV),)))
        if n == 1:
            return replace(m, adverbial=m.adverbial + (None,))
        if n == 2 and m.subjekt is not None:
            return replace(m, adverbial=m.adverbial
                           + (Prepositionsfras(None, m.subjekt),))
        if n == 3 and m.objekt is not None:
            return replace(m, objekt=replace(m.objekt, koncept=None))
        return m

    Samplare.kandidat = hålig
    return lambda: setattr(Samplare, "kandidat", orig)


SABOTAGE = [(_sabotage_hål_i_specen, 0),
            (_sabotage_hål_i_specen, 1)]


def _kopia(mål: Path) -> sqlite3.Connection:
    """Inlärardatabasen, kopierad genom SQLites egen backup.

    `cp` duger inte: databasen körs i WAL-läge och en filkopia tappar precis
    det nyaste (I1). `backup` läser genom WAL.
    """
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(mål)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    return anslut_kort(mål)


def main() -> int:
    tmp = tempfile.TemporaryDirectory()
    kort = _kopia(Path(tmp.name) / "samplar.db")
    språk_db = anslut()
    språk_db.row_factory = sqlite3.Row
    fel = stumma = 0
    try:
        print(f"{len(PROV)} invarianter, {KANDIDATER} kandidater per "
              f"språk och nivå\n")
        for namn, f in PROV:
            brister = f(kort, språk_db)
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister[:6]:
                print(f"      {b}")

        print("\nfalsifiering — med hålet återinfört ska varje prov falla:")
        for sab, mål in SABOTAGE:
            ångra = sab()
            try:
                brister = PROV[mål][1](kort, språk_db)
            finally:
                ångra()
            if not brister:
                stumma += 1
            print(f"  {'✓ föll' if brister else '✗ STUMT'}  {PROV[mål][0]}")
    finally:
        # BÅDA anslutningarna stängs. `with sqlite3.connect(...)` avslutar en
        # TRANSAKTION och inte anslutningen — en läckt läsare mot kortfilen
        # fick varje senare `backup` att vänta ut den, och tog sviten från
        # 61 s till 2 830 s (G4).
        kort.close()
        språk_db.close()
        tmp.cleanup()
    print(f"\n{len(PROV)} invarianter, {fel} brott." if fel
          else f"\n{len(PROV)} invarianter, alla håller.")
    if stumma:
        print(f"{stumma} sabotage fällde inte sitt prov.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
