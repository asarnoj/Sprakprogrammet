"""Prov för B2 och F1 — arbetsbördans och upplåsningens aritmetik.

VARFÖR DET HÄR PROVET FINNS. `renderarbild.py` täcker renderarna,
`omkastningsprov.py` rättningen och `tjänsteprov.py` tjänstens invarianter.
Kostnadskurvan, tidsspärren, långsiktsvillkoret och byggbarhetströskeln har
inget nät alls — trots att de avgör hur mycket användaren lär sig per dag.

En tyst regression där syns inte. Talen ser rimliga ut oavsett vad de är, och
den enda som märker att inflödet halverats är någon som räknar efter för hand
om ett halvår. Det är exakt den feltypen som kostat mest i det här projektet:
`Cellkort` var tom i en månad, exponeringen omätt för tyskan i två.

VAD PROVET PRÖVAR. Aritmetiken, inte omdömet. Att horisonten ska vara ett år
är ett beslut som står i PROBLEM.md; att en styrning som dividerar med
kum(365) faktiskt håller målet vid dag 365 är en räkning, och den kan gå
sönder utan att någon märker det.

VARJE KONTROLL HAR ETT SABOTAGE. Ett prov som inte kan falla bevisar
ingenting — se `omkastningsprov.py`, där den första invarianten var tom, och
`tjänsteprov.py`, där ett sabotage tystnade när koden omkring ändrades.

Kör:  python ordbok/verktyg/arbetsbördeprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kort import arbetsborda as A  # noqa: E402
from sprakprog.kort import schemalaggning as S  # noqa: E402


def kopia(mål: Path) -> sqlite3.Connection:
    with sqlite3.connect(ROT / "kort.db") as käll:
        käll.backup(sqlite3.connect(mål))
    k = sqlite3.connect(mål)
    k.row_factory = sqlite3.Row
    return k


# ── kostnadskurvan ───────────────────────────────────────────────────

def prov_kurvans_form(k) -> list[str]:
    """Kurvan ska börja på exakt 1 och vara deterministisk.

    `kurva[0] == 1` är inte en avrundning utan en definition: varje infört
    kort kostar precis en repetition den dag det införs, nämligen
    introduktionen. Går den siffran sönder är hela kostnadsmodellen fel i
    första ledet, och tidsspärrens självstabilitet (`kurva[2] ≈ 1`) med den.

    Determinismen är lika viktig: fröet är fast, så samma dag måste ge samma
    svar. En kurva som vandrar mellan anrop gör inflödet slumpmässigt.
    """
    fel = []
    A._kurvor.clear()
    ett = A.nykortskurva(0.90)
    A._kurvor.clear()
    två = A.nykortskurva(0.90)
    if ett != två:
        fel.append("kurvan är inte deterministisk mellan anrop")
    if abs(ett[0] - 1.0) > 1e-9:
        fel.append(f"kurva[0] är {ett[0]:.4f}, ska vara exakt 1")
    if not 0.9 <= ett[2] <= 1.05:
        fel.append(f"kurva[2] är {ett[2]:.3f} — tidsspärrens självstabilitet "
                   f"vilar på att den ligger nära 1")
    if not 6.5 <= sum(ett) <= 10.0:
        fel.append(f"kum(365) är {sum(ett):.2f}, väntat 7–9")
    return fel


def prov_horisonten_håller_målet(k) -> list[str]:
    """En styrning som dividerar med kum(H) ska hålla målet vid dag H.

    DET ÄR HELA HÄRLEDNINGEN bakom `KOSTNADSHORISONT_DYGN = 365`: för man in
    k kort per dygn i evighet blir dygnets arbete `k × kum(D)` vid dag D, så
    valet av H bestämmer vid vilken dag målet håller. Provet gör räkningen
    baklänges — sätter k som styrningen skulle, och kontrollerar att
    belastningen vid horisonten landar på målet.
    """
    kurva = A.nykortskurva(0.90, A.KOSTNADSHORISONT_DYGN)
    kostnad = sum(kurva)
    mål, medel = 60.0, 5.0
    k_ = (mål - medel) / kostnad
    landar = medel + k_ * kostnad
    if abs(landar - mål) > 1e-6:
        return [f"styrningen landar på {landar:.3f} rep/dygn, målet var {mål}"]
    # Och att en KORTARE horisont överskjuter, vilket är skälet till valet.
    kort = sum(A.nykortskurva(0.90, 14))
    if not kostnad / kort > 2.0:
        return [f"en 14-dygnshorisont överskjuter bara {kostnad/kort:.1f}x — "
                f"härledningen bakom 365 bygger på att den överskjuter ~2,6x"]
    return []


# ── beslutet ─────────────────────────────────────────────────────────

def prov_beslutet_är_monotont(k) -> list[str]:
    """Mer tid ska aldrig ge FÄRRE nya kort.

    Monotonin är den svagaste egenskap ett sådant här beslut kan ha och ändå
    vara meningsfullt. Bryts den betyder det att någon term har fel tecken,
    och det syns inte på ett enskilt tal.
    """
    fel, förra = [], -1
    for mål in (10, 20, 40, 80, 160):
        r = A.nya_idag(k, "de", mål_rep_per_dag=mål)
        if r["nya"] is None:
            continue
        if r["nya"] < förra:
            fel.append(f"mål {mål} gav {r['nya']} nya, lägre mål gav {förra}")
        förra = r["nya"]
    return fel


def prov_villkoren_binder(k) -> list[str]:
    """Båda villkoren ska kunna binda, och det lägsta ska gälla.

    Ett villkor som ALDRIG binder är dött och kan tas bort; ett som alltid
    binder gör det andra dött. Provet visar att båda kan avgöra utfallet.
    """
    fel = []
    r = A.nya_idag(k, "de", mål_rep_per_dag=1000)
    if r["nya"] is None:
        return ["gick inte att räkna"]
    i_längden = (r["mål"] - r["medel"]) / r["kostnad_per_kort"]
    idag = (r["mål"] - r["idag_belastning"]) / r["kostnad_idag"]
    if r["nya"] != max(0, int(min(i_längden, idag))):
        fel.append(f"beslutet {r['nya']} är inte min({i_längden:.1f}, "
                   f"{idag:.1f}) — det lägsta villkoret gäller inte")
    # Vid ett mål under dagens belastning får ingenting släppas in.
    lågt = A.nya_idag(k, "de", mål_rep_per_dag=0.0)
    if lågt["nya"]:
        fel.append(f"mål 0 rep/dygn släppte ändå in {lågt['nya']} kort")
    return fel


def prov_prognosens_dag_noll(k) -> list[str]:
    """Prognosens dag 0 ska vara exakt de kort som är förfallna nu.

    Steg 1 i B2 är det enda som MÅSTE vara exakt — det är en fråga till
    databasen, ingen modell. Avviker den har simuleringen börjat gissa om
    nuet.
    """
    p = A.prognos(k, "de")
    förfallna = k.execute(
        """SELECT COUNT(*) FROM Kort WHERE språk = 'de' AND schemalagt = 1
           AND förfaller IS NOT NULL AND förfaller <= datetime('now')"""
    ).fetchone()[0]
    return ([] if abs(p[0] - förfallna) < 1e-9 else
            [f"prognos[0] = {p[0]:.0f}, faktiskt förfallna {förfallna}"])


# ── tidsspärren ──────────────────────────────────────────────────────

def prov_tidsspärren_är_binär(k) -> list[str]:
    """Spärren får ALDRIG räkna om tid till kort.

    Frestelsen är `tid_kvar / sekunder_per_repetition`, och den prövades och
    förkastades: en absurt liten uppmätt takt tar bort spärren helt — mätt gav
    ett prov som svarade på 20 ms per glosa taket 28 000 kort. Den robusta
    formen frågar bara om det finns tid kvar.

    Provet kontrollerar att `tidstak` bara antar sina två lagliga värden:
    noll, eller hela lagret.
    """
    fel = []
    for språk in ("de", "en", "fr"):
        p = S.dagsplan(k, språk)
        if p["tidstak"] not in (0, p["osedda"]):
            fel.append(f"{språk}: tidstak {p['tidstak']} är varken 0 eller "
                       f"osedda ({p['osedda']}) — spärren räknar om tid")
        if p["tid_kvar"] <= 0 and p["tidstak"] != 0:
            fel.append(f"{språk}: tiden är slut men tidstak är {p['tidstak']}")
    return fel


def prov_nya_är_ett_saldo(k) -> list[str]:
    """Att införa N kort ska minska dagens `nya` med N.

    `nya` var förut ett TAK och inte ett saldo, och glosläget kunde därför
    delas ut om och om igen. Mätt vid upptäckten: 44 införda kort mot ett tak
    på 34.
    """
    p = S.dagsplan(k, "de")
    if not p["nya"]:
        return []
    n = min(3, p["nya"])
    idn = [r["id"] for r in k.execute(
        """SELECT id FROM Kort WHERE språk = 'de' AND schemalagt = 1
           AND sedd IS NULL LIMIT ?""", (n,))]
    s = S.Schemaläggare(k)
    for kid in idn:
        s.repetera(kid, True)
    k.commit()
    efter = S.dagsplan(k, "de")
    if efter["nya"] != max(0, p["nya"] - n):
        return [f"införde {n} kort men `nya` gick {p['nya']} → {efter['nya']}, "
                f"väntat {max(0, p['nya'] - n)}"]
    return []


# ── upplåsningen ─────────────────────────────────────────────────────

def prov_upplåsningströskeln(k) -> list[str]:
    """`byggbarhet × kandidater ≥ 1`, exakt vid gränsen.

    Tröskeln är härledd ur sökningen själv: generatorn prövar `kandidater`
    kandidater, så andelen dugliga måste räcka till minst en väntad träff.
    Provet sätter den på gränsen från båda hållen.
    """
    fall = [(1 / 800, 800, True), (0.99 / 800, 800, False),
            (1.01 / 800, 800, True), (0.0, 800, False),
            (1.0, 800, True), (None, 800, None), (0.5, 0, None)]
    fel = []
    for b, kand, väntat in fall:
        fick = S.redo_för_nivå(b, kand)
        if fick != väntat:
            fel.append(f"redo_för_nivå({b}, {kand}) gav {fick}, väntat {väntat}")
    return fel


def prov_saldot_ser_de_oschemalagda(k) -> list[str]:
    """Ett kort som INTE är schemalagt förbrukar ändå av dagen när det införs.

    `INFÖRBAR = (schemalagt = 1 OR typ = 'ord')` satt på båda frågorna, och de
    är olika. Vad som får PLANERAS ska filtreras — ett allestädes närvarande
    ändelsekort hör inte i kön. Vad som FÖRBRUKATS ska inte: kortet blev
    bedömt så snart en mening råkade innehålla det, och den repetitionen
    kommer tillbaka som arbete oavsett hur den kom in.

    Mätt på franskans dag 2026-08-29: 34 kort infördes, filtret räknade 29.
    De fem osynliga var `system` 2, `form` 1, `ordföljd` 1, `stam` 1. Taket
    var 25, så filtret dolde en femtedel av överskridandet.
    """
    p = S.dagsplan(k, "de")
    if not p["nya"]:
        return ["kursen har inga nya kort kvar — provet kan inte mäta"]
    idn = [r["id"] for r in k.execute(
        """SELECT id FROM Kort WHERE språk = 'de' AND schemalagt = 0
           AND typ != 'ord' AND sedd IS NULL LIMIT 3""")]
    if not idn:
        return ["ingen oschemalagd kandidat — provet kan inte mäta"]
    s = S.Schemaläggare(k)
    for kid in idn:
        s.repetera(kid, True)
    k.commit()
    efter = S.dagsplan(k, "de")
    if efter["infört_idag"] != p["infört_idag"] + len(idn):
        return [f"införde {len(idn)} oschemalagda kort men `infört_idag` gick "
                f"{p['infört_idag']} → {efter['infört_idag']}"]
    return []


PROV = [
    ("kostnadskurvans form", prov_kurvans_form),
    ("horisonten håller målet", prov_horisonten_håller_målet),
    ("prognosens dag noll är exakt", prov_prognosens_dag_noll),
    ("beslutet är monotont", prov_beslutet_är_monotont),
    ("båda villkoren binder", prov_villkoren_binder),
    ("tidsspärren är binär", prov_tidsspärren_är_binär),
    ("nya är ett saldo", prov_nya_är_ett_saldo),
    ("saldot ser de oschemalagda", prov_saldot_ser_de_oschemalagda),
    ("upplåsningströskeln", prov_upplåsningströskeln),
]


def _sabotera(namn: str):
    """Återinför felet kontrollen finns för. Returnerar en ångra-funktion."""
    if namn == "saldot ser de oschemalagda":
        # Före rättelsen: `INFÖRBAR` satt på båda frågorna, så ett kort som
        # inte var schemalagt förbrukade ingenting av dagen.
        äkta = S._infört_idag
        def filtrerat(kort_db, språk, nu):
            return kort_db.execute(
                f"""SELECT COUNT(*) FROM Kort
                    WHERE språk = ? AND {S.INFÖRBAR} AND sedd >= ?""",
                (språk, S.dygnets_början(nu))).fetchone()[0]
        S._infört_idag = filtrerat
        return lambda: setattr(S, "_infört_idag", äkta)

    if namn == "kostnadskurvans form":
        äkta = A.nykortskurva
        A.nykortskurva = lambda dr, dygn=A.KOSTNADSHORISONT_DYGN: (
            [0.5] + list(äkta(dr, dygn))[1:])          # introduktionen halverad
        return lambda: setattr(A, "nykortskurva", äkta)

    if namn == "horisonten håller målet":
        äkta = A.KOSTNADSHORISONT_DYGN
        A.KOSTNADSHORISONT_DYGN = 14                   # den förkastade horisonten
        return lambda: setattr(A, "KOSTNADSHORISONT_DYGN", äkta)

    if namn == "prognosens dag noll är exakt":
        äkta = A.prognos
        A.prognos = lambda *a, **kw: [x * 2 for x in äkta(*a, **kw)]
        return lambda: setattr(A, "prognos", äkta)

    if namn in ("beslutet är monotont", "båda villkoren binder"):
        # Före härledningen delades det med kostnaden över PROGNOSFÖNSTRET,
        # alltså fel storhet — och för monotonin: ett tecken åt fel håll.
        äkta = A.nya_idag
        def bakvänt(kort_db, språk, *, mål_rep_per_dag, **kw):
            r = äkta(kort_db, språk, mål_rep_per_dag=mål_rep_per_dag, **kw)
            if r["nya"] is not None:
                r["nya"] = max(0, 200 - r["nya"])      # monotonin vänd
            return r
        A.nya_idag = bakvänt
        return lambda: setattr(A, "nya_idag", äkta)

    if namn == "tidsspärren är binär":
        # DEN FÖRKASTADE FORMEN, återinförd: räkna om tid till kort. Den ser
        # oskyldig ut och är det inte — en absurt liten uppmätt takt tar bort
        # spärren helt.
        äkta = S.tidsspärr
        S.tidsspärr = lambda tid_kvar, osedda: (
            0 if tid_kvar <= 0 else min(osedda, int(tid_kvar / 3.85)))
        return lambda: setattr(S, "tidsspärr", äkta)

    if namn == "nya är ett saldo":
        äkta = S.dygnets_början
        S.dygnets_början = lambda nu=None: "2099-01-01T00:00:00+00:00"
        return lambda: setattr(S, "dygnets_början", äkta)

    if namn == "upplåsningströskeln":
        äkta = S.redo_för_nivå
        S.redo_för_nivå = lambda b, kand: b is not None and b > 0
        return lambda: setattr(S, "redo_för_nivå", äkta)

    raise KeyError(namn)


def main() -> int:
    fel = 0
    with tempfile.TemporaryDirectory() as d:
        for nr, (namn, kör) in enumerate(PROV):
            k = kopia(Path(d) / f"p{nr}.db")
            brister = kör(k)
            k.close()
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister:
                print(f"      {b}")

        print("\nfalsifiering — med felet återinfört ska varje kontroll falla:")
        stumma = 0
        for nr, (namn, kör) in enumerate(PROV):
            ångra = _sabotera(namn)
            try:
                A._kurvor.clear()
                k = kopia(Path(d) / f"s{nr}.db")
                brister = kör(k)
                k.close()
            finally:
                ångra()
                A._kurvor.clear()
            if not brister:
                stumma += 1
            print(f"  {'✓ föll' if brister else '✗ STUMT PROV'}  {namn}")

    print(f"\n{len(PROV)} kontroller, {fel} brott, {stumma} stumma prov."
          if (fel or stumma) else
          f"\n{len(PROV)} kontroller, alla håller och alla kan falla.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
