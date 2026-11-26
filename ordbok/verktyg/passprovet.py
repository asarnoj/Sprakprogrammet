"""Nät för dagspassets invarianter — KÄRNAN 5.1, 5.4 och 6.1.

VARFÖR DET HÄR NÄTET FINNS. Tre fel i passet hittades samma dag, och alla tre
hade samma form: koden räknade upp något för hand och KÄRNAN sa något annat.

    villkor 8 i 6.1   källmeningen fick ställas om samma dag. Fyra av fjorton
                      meningar i den första riktiga körningen var upprepningar,
                      och andra gången mätte de minnet av facit i stället för
                      kortet.

    villkor 5 och 7   ingenting kontrollerade att två svaga kort inte styr
                      samma ställe. Budgeten gjorde felen FÅ, aldrig
                      ÅTSKILJBARA — KÄRNAN 6.2 kallar dem samma tal sett från
                      två håll, och bara det ena hölls.

    5.4               introfasen bokförde. `Passet.presentera` gjorde rätt sak
                      och anropades aldrig; gränssnittet ställde i stället en
                      mening med hela paketet som mål och skrev betygen till
                      FSRS.

Inget prov hade fångat något av dem. `passprov` prövar tjänsterna runt passet,
inte reglerna i det.

VAD PROVET GÖR. Bygger en färsk kurs, kör introfasen och några meningar, och
prövar invarianterna på det som faktiskt ställs. Sedan FALSIFIERAS varje
invariant: det gamla beteendet återinförs, och en invariant som inte faller då
är ingen invariant utan en förhoppning. Det är samma uppställning som
`övervakningsprov`.

VILAR INTE PÅ INLÄRARHISTORIKEN. Kursen byggs från noll i en temporärfil.

Kör:  python ordbok/verktyg/passprovet.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.fsrslager import Lager                             # noqa: E402
from sprakprog.kortmodell import Kort, meningens_kort             # noqa: E402
from sprakprog.kurs import Kursdata                               # noqa: E402
from sprakprog.passet import Passet                               # noqa: E402
from sprakprog.rendering.karta import ladda                       # noqa: E402
from sprakprog.sammansattning import Sammansättare                # noqa: E402

KARTA = ROT / "kartor" / "en.pkl"
NIVÅER = ROT / "kartor" / "nivaer_en.json"

#: Taket för hur länge det får ta att VÄLJA en uppgift. Mätt i KÄRNAN 6.3:
#: att svara på den kortaste meningen tar 16,2 s i median, och att välja den
#: får inte kosta mer än att besvara den. Frysningen som gav upphov till det
#: här provet höll sig långt över taket — kortet gav aldrig någon mening alls.
TAK_SEKUNDER = 16.2


def _nivåfil() -> tuple[dict, list]:
    data = json.loads(NIVÅER.read_text(encoding="utf-8"))

    def kort(rad) -> Kort:
        return Kort(rad[0], rad[1], tuple(rad[2]))

    return ({kort(k): frozenset(map(kort, m)) for k, m in data["krav"]},
            [frozenset(map(kort, n)) for n in data["nivåer"]])


def _passet(fil: Path) -> tuple[Passet, Kursdata]:
    s = Sammansättare(sqlite3.connect(ROT / "sprak.db"), ladda(KARTA), "sv")
    data = Kursdata(sqlite3.connect(fil), "sv", "en")
    krav, nivåer = _nivåfil()
    return Passet(data, s, Lager(data), krav, nivåer), data


@contextmanager
def _utan(objekt, namn: str, ersättning):
    """Återinför ett gammalt beteende, för falsifieringen."""
    gammalt = getattr(type(objekt), namn)
    setattr(type(objekt), namn, ersättning)
    try:
        yield
    finally:
        setattr(type(objekt), namn, gammalt)


# ── invarianterna ────────────────────────────────────────────────────


def introfasen_bokför_ingenting(p: Passet, data: Kursdata) -> list[str]:
    """5.4. Övningen finns för att användaren inte ska möta ny kunskap
    oförberedd, inte för FSRS."""
    före = len(data.möten())
    kort = p.kandidater()[0]
    uppgift = p.presentera(kort, paket=p.nästa_nivå())
    if uppgift is None:
        return ["ingen introövning gick att bygga för det första kortet"]
    uppgift = p.ställ(uppgift, "intro")
    p.rätta(uppgift, "struntprat", 1.0)
    efter = len(data.möten())
    return ([f"introfasen bokförde {efter - före} möten"] if efter != före else [])


def introövningen_har_ett_mål(p: Passet) -> list[str]:
    """5.4. Bara det nya kortet är mål; resten är lånekort."""
    brister = []
    for kort in p.kandidater()[:3]:
        uppgift = p.presentera(kort, paket=p.nästa_nivå())
        if uppgift is None:
            continue
        if uppgift.mål != frozenset({kort}):
            brister.append(f"{kort}: introövningen hade målen "
                           f"{sorted(map(str, uppgift.mål))}")
    return brister


def källmeningen_ställs_en_gång(p: Passet, data: Kursdata) -> list[str]:
    """6.1 punkt 8. Efter ett fel har användaren sett facit."""
    ställda: list[str] = []
    for kort in p.kandidater():
        uppgift = p.presentera(kort, paket=p.nästa_nivå())
        if uppgift is None:
            continue
        p.ställ(uppgift, "intro")
        ställda.append(uppgift.källtext)
    dubbletter = {t for t in ställda if ställda.count(t) > 1}
    return ([f"samma källmening ställdes flera gånger: {sorted(dubbletter)}"]
            if dubbletter else [])


def målen_är_åtskilda(p: Passet) -> list[str]:
    """6.1 punkt 5 och 7. Två mål får inte styra samma ställe."""
    brister = []
    for kort in p.kandidater()[:3]:
        uppgift = p.presentera(kort, paket=p.nästa_nivå())
        if uppgift is None:
            continue
        if not p._åtskilda(uppgift.ut, set(uppgift.mål)):
            brister.append(f"{kort}: målen delar ställe i «{uppgift.facit}»")
    return brister


def uppgiften_väljs_i_tid(p: Passet) -> list[str]:
    """Frysningen. Att välja en uppgift får inte kosta mer än att besvara den."""
    brister = []
    for kort in p.kandidater()[:3]:
        t = time.perf_counter()
        p.presentera(kort, paket=p.nästa_nivå())
        gick = time.perf_counter() - t
        if gick > TAK_SEKUNDER:
            brister.append(f"{kort}: att välja uppgiften tog {gick:.0f} s "
                           f"(taket är {TAK_SEKUNDER} s)")
    return brister


def paketet_införs_helt(p: Passet, data: Kursdata) -> list[str]:
    """5.1. Annars kunde ett verb vara infört utan det pronomen det kräver."""
    nivån = p.nästa_nivå()
    kort = p.kandidater()[0]
    uppgift = p.presentera(kort, paket=nivån)
    if uppgift is None:
        return ["ingen övning gick att bygga"]
    uppgift = p.ställ(uppgift)
    # Ett svar där ETT ord är fel. Då klarar sig de flesta korten och ett
    # faller — och först då skiljer sig «helt eller inte alls» från det gamla
    # «kort för kort». Ett svar som gör allt fel gör lägena omöjliga att
    # skilja åt, eftersom inget kort införs i någotdera.
    orden = uppgift.facit.split()
    svar = " ".join(orden[:-1] + ["xyzzy"])
    rättning = p.rätta(uppgift, svar, 1.0)
    if all(b == "again" for b in rättning.betyg.values()):
        return ["provet kunde inte få något kort att klara sig — fallet "
                "skiljer inte lägena åt"]
    p.bokför(uppgift, rättning, paket=nivån)
    infört = data.införda() & nivån
    return ([f"{len(infört)} av {len(nivån)} kort i paketet infördes trots att "
             f"paketet föll: {sorted(map(str, infört))}"] if infört else [])


def dag_ett_går_att_komma_igenom(p: Passet, data: Kursdata) -> list[str]:
    """6.3: budgeten kan aldrig göra ett kort onåbart.

    Dag ett är alla kort svaga och står på samma få ord, så villkor 5 gör
    varje mening med flera mål ogiltig. Utan ensamövningen (reservsteg 1)
    fanns då ingen uppgift alls, och passet gick inte att komma igenom.
    """
    nivån = p.nästa_nivå()
    for kort in p.kandidater():
        uppgift = p.presentera(kort, paket=nivån)
        if uppgift is not None:
            p.ställ(uppgift, "intro")
    p.uppdatera()
    utan = [k for k in sorted(p.svaga(), key=str) if p.uppgift(k) is None]
    return ([f"{len(utan)} svaga kort utan uppgift efter introfasen: "
             f"{sorted(map(str, utan))}"] if utan else [])


def meningen_använder_bara_tillåtet(p: Passet) -> list[str]:
    """6.1 punkt 1. Ett kort som inte är infört eller presenterat får inte stå
    i en mening — utom målet självt och orden, som är upplåsta (3.1)."""
    brister = []
    tillåtna = p.tillåtna()
    for kort in p.kandidater()[:3]:
        uppgift = p.presentera(kort, paket=p.nästa_nivå())
        if uppgift is None:
            continue
        otillåtna = {k for k in uppgift.träff.kort
                     if k != kort and k not in tillåtna and k.familj != "ord"
                     and k not in p.nästa_nivå()}
        if otillåtna:
            brister.append(f"{kort}: «{uppgift.facit}» använder otillåtna kort "
                           f"{sorted(map(str, otillåtna))}")
    return brister


def korten_införs_när_de_går_rätt(p: Passet, data: Kursdata) -> list[str]:
    """5.1. Ett nytt kort blir infört när det går rätt i en mening.

    I den första riktiga körningen infördes noll kort på 32 ställda meningar.
    Passet kom aldrig ur introfasen — som inför ingenting — eftersom
    gränssnittet lät den köras om, och räknaren stod stilla eftersom den
    räknade oinförda kort. Provet går hela vägen: presentera, svara RÄTT,
    och kräv att korten är inne.
    """
    nivån = p.nästa_nivå()
    for kort in p.att_presentera():
        uppgift = p.presentera(kort, paket=nivån)
        if uppgift is not None:
            p.ställ(uppgift, "intro")
    p.uppdatera()
    if p.att_presentera():
        return [f"{len(p.att_presentera())} kort kvar att presentera efter "
                f"introfasen — den tar aldrig slut"]
    for _ in range(12):
        svaga = sorted(p.svaga(), key=str)
        if not svaga:
            break
        uppgift = p.uppgift(svaga[0])
        if uppgift is None:
            break
        uppgift = p.ställ(uppgift)
        rättning = p.rätta(uppgift, uppgift.facit, 1.0)   # svarar rätt
        if not rättning.rätt:
            return [f"ett svar lika med facit underkändes: «{uppgift.facit}» "
                    f"fällde {sorted(map(str, rättning.fel))}"]
        p.bokför(uppgift, rättning)
    return ([] if data.införda() else
            ["inget kort infördes trots att varje svar var lika med facit"])


INVARIANTER = [
    ("introfasen bokför ingenting", introfasen_bokför_ingenting, True),
    ("introövningen har ett enda mål", introövningen_har_ett_mål, False),
    ("källmeningen ställs en gång per dag", källmeningen_ställs_en_gång, True),
    ("målen är åtskilda", målen_är_åtskilda, False),
    ("uppgiften väljs i tid", uppgiften_väljs_i_tid, False),
    ("paketet införs helt eller inte alls", paketet_införs_helt, True),
    ("dag ett går att komma igenom", dag_ett_går_att_komma_igenom, True),
    ("meningen använder bara tillåtet", meningen_använder_bara_tillåtet, False),
    ("korten införs när de går rätt", korten_införs_när_de_går_rätt, True),
]


def _kör(namn, fn, med_data, mapp: Path, n: int) -> list[str]:
    p, data = _passet(mapp / f"kurs{n}.db")
    return fn(p, data) if med_data else fn(p)


# ── falsifieringen ───────────────────────────────────────────────────


def _falsifiera(mapp: Path) -> list[str]:
    """Varje gammalt beteende ska fälla sin invariant."""
    brister = []
    fall = [
        ("källmeningen fick ställas om samma dag",
         "källmeningen ställs en gång per dag", källmeningen_ställs_en_gång, True,
         (Kursdata, "dagens_källtexter", lambda self: set())),
        ("paketet infördes kort för kort",
         "paketet införs helt eller inte alls", paketet_införs_helt, True,
         (Passet, "bokför", None)),
        ("ensamövningen fanns inte",
         "dag ett går att komma igenom", dag_ett_går_att_komma_igenom, True,
         (Passet, "ensamövning", lambda self, kort: None)),
    ]
    for i, (gammalt, invariant, fn, med_data, (klass, namn, ers)) in enumerate(fall):
        p, data = _passet(mapp / f"fals{i}.db")
        objekt = data if klass is Kursdata else p
        if ers is None:
            # Det gamla `bokför`: inför varje kort som inte föll, oavsett paket.
            def ers(self, uppgift, rättning, godkända=frozenset(), höjt=None,
                    flagga=None, paket=frozenset()):
                from sprakprog.rattning import FEL, RÄTT
                for kort, mätt in rättning.betyg.items():
                    betyg = RÄTT if kort in godkända else mätt
                    self.data.bokför(kort, mål=kort in uppgift.mål, betyg_diff=mätt,
                                     betyg=betyg, mening_id=uppgift.mening_id)
                    if betyg != FEL:
                        self.data.inför(kort, uppgift.mening_id)
                self.uppdatera()
        with _utan(objekt, namn, ers):
            fel = fn(p, data) if med_data else fn(p)
        status = "✓ föll" if fel else "✗ HÖLL ÄNDÅ"
        print(f"  {status}  {gammalt}")
        if not fel:
            brister.append(f"invarianten «{invariant}» fångar inte «{gammalt}»")
    return brister


def main() -> int:
    if not KARTA.exists() or not NIVÅER.exists():
        print(f"saknar {KARTA.name} eller {NIVÅER.name} — bygg dem först")
        return 0
    brister: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        mapp = Path(t)
        print("── invarianterna ──")
        for n, (namn, fn, med_data) in enumerate(INVARIANTER):
            start = time.perf_counter()
            fel = _kör(namn, fn, med_data, mapp, n)
            print(f"  {'✓' if not fel else '✗'} {namn}"
                  f"   ({time.perf_counter() - start:.1f} s)")
            for b in fel:
                print(f"      {b}")
            brister += fel

        print("\n── falsifiering: varje gammalt läge ska fälla sitt prov ──")
        brister += _falsifiera(mapp)

    antal = len(INVARIANTER) + 2
    print(f"\n{antal} kontroller, {len(brister)} brister." if brister
          else f"\n{antal} kontroller, alla håller.")
    return 1 if brister else 0


if __name__ == "__main__":
    raise SystemExit(main())
