"""Spela en hel dag och visa ALLT som händer — för att kunna se, inte pröva.

VARFÖR DET HÄR VERKTYGET FINNS. Proven svarar ja eller nej. När något känns
fel utan att något prov faller behövs något annat: en körning man kan LÄSA.
Julius rapporterade "exakt samma buggar som innan" medan nio prov stod gröna,
och det gick inte att komma vidare på den informationen — varken han eller
jag kunde se vad passet faktiskt bestod av.

Verktyget spelar en dag genom `Övningstjänst`, alltså samma väg som
webbgränssnittet, och skriver ut tre saker som annars är osynliga:

    PASSETS INNEHÅLL   varje rad: roll, korttyp, koncept, facit
    VARJE STEG         vad skärmen skulle visa, före och efter
    SLUTSTÄLLNINGEN    vad som blev gjort, fällt och AVSKRIVET

Den sista kolumnen är den viktiga. Ett kort med status `onåbar` planerades in
i dagen och gick sedan inte att bygga en mening kring — och det talet, inte
antalet meningar, är måttet på om dagsplaneringen fungerar.

ALDRIG MOT DEN RIKTIGA DATABASEN. Verktyget övar och inför kort, så det
arbetar i en kopia. `--riktig` läser den riktiga databasen utan att röra den:
då visas bara dagens läge, ingen körning.

Kör:  python ordbok/verktyg/passkörning.py [kurs_id] [--nollställ] [--riktig]
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kort import pass_ as passlager            # noqa: E402
from sprakprog.kort.db import anslut_kort                # noqa: E402
from sprakprog.webb import Övningstjänst                 # noqa: E402

MAXVARV = 200


def _kopia(mål: Path) -> sqlite3.Connection:
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(mål)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    return anslut_kort(mål, delad_mellan_trådar=True)


def visa_passet(kort: sqlite3.Connection, kurs_id: int, rubrik: str) -> None:
    """Passets rader, som de står i databasen. Ingen tolkning."""
    rad = passlager.nuvarande(kort, kurs_id)
    if rad is None:
        print(f"\n{rubrik}: inget pass")
        return
    rader = kort.execute(
        """SELECT pk.roll, pk.status, k.typ, k.koncept, k.cell, k.facit
           FROM Passkort pk LEFT JOIN Kort k ON k.id = pk.kort_id
           WHERE pk.pass_id = ? ORDER BY pk.ordning, pk.id""",
        (rad["id"],)).fetchall()
    print(f"\n{rubrik}  (pass {rad['id']}, "
          f"{'avslutat' if rad['avslutad'] else 'pågår'}, {len(rader)} rader)")
    for r in rader:
        märke = {"väntar": " ", "rätt": "✓", "fel": "✗", "onåbar": "—"}[r["status"]]
        print(f"   {märke} {r['roll']:10s} {str(r['typ'] or 'BORTA'):9s} "
              f"{str(r['koncept'] or r['cell'] or ''):22s} {r['facit']!r}")


def _skärmen(tj, kurs_id: int) -> str:
    i = tj.hem(kurs_id)["idag"]
    return (f"att göra {i['att_göra']:3d} = {i['glosor']:2d} glosor "
            f"+ {i['förfallna']:2d} förf + {i['nya']:3d} nya + {i['igen']:2d} igen"
            + ("   KLAR" if i["klar"] else ""))


def spela(tj, kort: sqlite3.Connection, kurs_id: int) -> None:
    print(f"\n{'─' * 72}\nSPELAR DAGEN\n{'─' * 72}")
    print(f"  start   {_skärmen(tj, kurs_id)}")
    meningar = drillade = 0
    for varv in range(MAXVARV):
        h = tj.hem(kurs_id)["idag"]
        if h["klar"]:
            print(f"  klar efter {varv} steg")
            break
        if h["glosor"]:
            g = tj.glosor(kurs_id)
            ord_ = [o["koncept"] for o in g["ord"]]
            for o in g["ord"]:
                tj.glossvar(kurs_id, o["kort_id"], True)
            drillade += len(ord_)
            print(f"  drill   {len(ord_)} ord: {', '.join(ord_)}")
            print(f"          {_skärmen(tj, kurs_id)}")
            continue
        u = tj.uppgift(kurs_id)
        if u is None:
            print("  STOPP   generatorn gav None"); break
        if u.get("tomt"):
            print(f"  STOPP   inget mer går att bygga "
                  f"({u.get('oåtkomliga', 0)} kort avskrivna)")
            print(f"          {_skärmen(tj, kurs_id)}")
            break
        f = tj._öppna[u["id"]][1]
        rörda = [f"{k['typ']}:{k['koncept'] or k['cell']}" for k in f.kort]
        tj.svara(u["id"], f.text)
        tj.bokför(u["id"])
        meningar += 1
        print(f"  mening  {f.text!r}"
              + ("   [NÖDFALL: upprepning, inget alternativ]" if u.get("nödfall") else ""))
        print(f"          rör {len(rörda)} kort: {', '.join(rörda[:6])}"
              + (f" +{len(rörda)-6}" if len(rörda) > 6 else ""))
        print(f"          {_skärmen(tj, kurs_id)}")
    print(f"\n  {drillade} ord drillade, {meningar} meningar")


def _varför_onåbar(kort: sqlite3.Connection, kurs: sqlite3.Row,
                   rad: sqlite3.Row) -> str:
    """Varför gick just det här kortet inte att öva?

    "Onåbar" är ett utfall, inte en orsak, och orsakerna kräver olika svar.
    B8 räknar upp tre; mätningen på Julius franskkurs hittade en fjärde som
    dokumentet inte namnger, och som var den vanligaste:

        KLASSEN SAKNAR ORD   ett systemkort bär en ändelse för en
                             BÖJNINGSKLASS. Franskans `pres_1sg` finns två
                             gånger — `-e` för K0 och `-s` för K1 — och
                             K1-ändelsen går bara att möta genom ett
                             REGELBUNDET K1-verb. Julius hade `avoir`, som
                             är K1 men oregelbundet och hämtar sina former
                             ur egna formkort. Kortet var alltså inte
                             omöjligt utan OLÄRBART: det prövar något
                             ordförrådet inte innehåller.

        STRUKTURELLT ONÅBAR  inget i kedjan pekar på kortet alls (A3).

        NIVÅN SAKNAR         cellen kräver en konstruktion nivån inte öppnat.

        SÖKNINGEN MISSADE    kortet GÅR att nå, men ingen av kandidaterna
                             råkade göra det. Det enda av de fyra som är ett
                             sökproblem, och det enda fler försök hjälper.
    """
    if rad["typ"] == "ordföljd":
        return "ordföljdskort — kräver en konstruktion nivån kanske inte öppnat"
    if rad["typ"] == "system" and rad["klass"] and rad["cell"]:
        # REGELBUNDET I JUST DEN HÄR CELLEN, inte bara "har rätt klass".
        # `avoir` är K1 men hämtar `ai`, `as`, `avons` ur egna FORMKORT — det
        # kan alltså inte pröva K1:s ändelser, hur mycket K1 det än är.
        # Villkoret är därför: finns ett infört ord med stam i klassen som
        # INTE har ett formkort för cellen?
        n = kort.execute(
            """SELECT COUNT(*) AS n FROM Kort st
               WHERE st.språk = ? AND st.typ = 'stam' AND st.klass = ?
                 AND EXISTS (SELECT 1 FROM Kort o WHERE o.språk = st.språk
                             AND o.typ = 'ord' AND o.koncept = st.koncept
                             AND o.sedd IS NOT NULL)
                 AND NOT EXISTS (SELECT 1 FROM Kort f WHERE f.språk = st.språk
                                 AND f.typ = 'form' AND f.koncept = st.koncept
                                 AND f.cell = ?)""",
            (kurs["målspråk"], rad["klass"], rad["cell"])).fetchone()["n"]
        if not n:
            return (f"inget infört ord böjer REGELBUNDET i klass "
                    f"{rad['klass']} på {rad['cell']} — ändelsen går inte "
                    f"att möta")
        # DUBBELTÄCKNING. Cellen har ett kort per klass, och en mening rör
        # bara den klass dess verb tillhör. Går det andra klassens kort inte
        # att nå är det samma sak en nivå ner.
        syskon = kort.execute(
            """SELECT COUNT(*) AS n FROM Kort
               WHERE språk = ? AND typ = 'system' AND cell = ?
                 AND klass IS NOT ?""",
            (kurs["målspråk"], rad["cell"], rad["klass"])).fetchone()["n"]
        if syskon:
            return (f"cellen {rad['cell']} har ett kort per böjningsklass; "
                    f"dagens meningar rörde en annan klass än {rad['klass']}")
    return "sökningen hittade ingen mening som rör det"


def sammanfatta(kort: sqlite3.Connection, kurs_id: int) -> None:
    rad = passlager.nuvarande(kort, kurs_id)
    if rad is None:
        return
    per = {r["status"]: r["n"] for r in kort.execute(
        """SELECT status, COUNT(*) AS n FROM Passkort
           WHERE pass_id = ? GROUP BY status""", (rad["id"],))}
    totalt = sum(per.values())
    onåbara = per.get("onåbar", 0)
    print(f"\n{'─' * 72}\nSLUTSTÄLLNING\n{'─' * 72}")
    for status in ("rätt", "fel", "onåbar", "väntar"):
        if per.get(status):
            print(f"   {status:8s} {per[status]:3d}")
    if onåbara:
        kurs = kort.execute("SELECT * FROM Kurs WHERE id = ?",
                            (kurs_id,)).fetchone()
        print("\n   VARFÖR DE INTE GICK ATT ÖVA:")
        for r in kort.execute(
                """SELECT k.typ, k.cell, k.klass, k.koncept, k.facit
                   FROM Passkort pk JOIN Kort k ON k.id = pk.kort_id
                   WHERE pk.pass_id = ? AND pk.status = 'onåbar'
                   ORDER BY pk.ordning""", (rad["id"],)):
            namn = f"{r['typ']}:{r['koncept'] or r['cell']} {r['facit']!r}"
            print(f"     {namn:34s} {_varför_onåbar(kort, kurs, r)}")
    if totalt:
        print(f"\n   AVSKRIVNA SOM ONÅBARA: {onåbara} av {totalt} "
              f"({onåbara / totalt:.0%} av dagen)")
        if onåbara / totalt > 0.25:
            print("   → dagen planerades till stor del med kort som inte gick "
                  "att öva.\n     Det är inte generatorns fel utan urvalets: "
                  "korten valdes på rang,\n     inte på om ordförrådet räcker "
                  "till en mening som rör dem.")


def main() -> int:
    argv = [a for a in sys.argv[1:]]
    riktig = "--riktig" in argv
    nollställ = "--nollställ" in argv
    kurs_id = next((int(a) for a in argv if a.isdigit()), None)

    if riktig:
        kort = anslut_kort(ROT / "kort.db")
        for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
            if kurs_id and kurs["id"] != kurs_id:
                continue
            visa_passet(kort, kurs["id"],
                        f"KURS {kurs['id']} {kurs['källspråk']}→{kurs['målspråk']}")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        kort = _kopia(Path(tmp) / "k.db")
        språk = sqlite3.connect(ROT / "sprak.db", check_same_thread=False)
        språk.row_factory = sqlite3.Row
        tj = Övningstjänst(kort, språk)
        kurser = [r for r in kort.execute("SELECT * FROM Kurs ORDER BY id")
                  if not kurs_id or r["id"] == kurs_id]
        for kurs in kurser:
            print(f"\n{'═' * 72}\nKURS {kurs['id']}  "
                  f"{kurs['källspråk']}→{kurs['målspråk']}  nivå {kurs['nivå']}"
                  f"\n{'═' * 72}")
            if nollställ:
                tj.nollställ(kurs["id"], "RESET")
                print("  (nollställd)")
            tj.hem(kurs["id"])
            visa_passet(kort, kurs["id"], "PASSET VID START")
            spela(tj, kort, kurs["id"])
            visa_passet(kort, kurs["id"], "PASSET EFTERÅT")
            sammanfatta(kort, kurs["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
