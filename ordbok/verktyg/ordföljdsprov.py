"""Prov för A7 punkt 2: går ordföljdsreglerna att MÖTA och att SKYLLA PÅ?

VARFÖR DET HÄR PROVET FINNS. Ordföljd är den enda kunskapen i systemet som
inte står någonstans i data. Formen står i `Former`, genuset på lexemet,
rektionen i `MönsterKrav` — men att tyskans finita verb står på plats två är
INGET annat än renderarens egen struktur. Det enda som går att observera
utifrån är att regeln tillämpades, och det kräver att renderaren säger det.

Sexton ordföljdskort över fyra språk stod därför `schemalagt = 1` utan att
någon mening kunde röra dem (A3). De låg i kön som mål som aldrig kunde nås,
åt av dagens tilldelning, och avslutade dagen i förtid när det nåbara var
gjort.

TRE INVARIANTER, EN PER LED I KEDJAN:

  1. NÅBARHET   varje ordföljdskort ska gå att möta. Mäts genom att sampla
                meningar och samla vilka kort de rör — samma metod som A3:s
                omätning använder.

  2. UPPDELNINGEN FALLER UT AV E6, den skrivs inte. En regel som gäller i
                varje mening får exponering nära 1 och lyfts ur schemat; en
                som kräver en konstruktion får en som går att schemalägga.
                Provet kräver att BÅDA lägena förekommer — annars mäter
                loggen något annat än regeln.

  3. SKULDEN    ett ordföljdsfel ska fälla ordföljdskortet när exakt EN
                schemalagd regel är i spel, och ingenting när flera är det.

ALDRIG MOT DEN RIKTIGA DATABASEN — kopia via SQLites backup.

Kör:  python ordbok/verktyg/ordföljdsprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut                          # noqa: E402
from sprakprog.generator import Förslag, Generator       # noqa: E402
from sprakprog.generator.rattning import ORDMELLANRUM    # noqa: E402
from sprakprog.kort.befolka import (                     # noqa: E402
    ORDFÖLJD, mät_exponering, sätt_schemalagt,
)
from sprakprog.rendering import Uppslag                  # noqa: E402

#: Hur många kandidater nåbarheten samplas med. Reglerna som kräver en
#: konstruktion — bisats, fråga, två objekt — är sällsynta i en fri sampling,
#: så det behövs fler än man tror. Mätt: vid 400 saknades fortfarande två.
KANDIDATER = 1500

#: Takten gränsen räknas med. En KULISS OCH INTE EN MÄTNING: påståendena här
#: gäller EXPONERINGEN — att mätningen skiljer grundordföljden från
#: konstruktionsreglerna — inte hur mycket någon råkar öva.
#:
#: Sedan 2026-09-04 kommer takten annars ur `Mening` (`meningstakt`), och
#: japanskan har aldrig övats: den hade då fått takten None, alltså INGA kort
#: ur schemat, och provet hade fallit på en egenskap hos loggen i stället för
#: hos renderaren. Att talet står här och inte i koden är hela skillnaden — i
#: koden var samma tal en tyst inställning som ingen satt.
TAKT = 20.0

#: Svepets storlek när exponeringen mäts. Bara grundordföljden behöver
#: mätas här, och den träffar varje mening.
SVEP = 300


def _kopia(mål: Path) -> sqlite3.Connection:
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(mål)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    kort = sqlite3.connect(mål)
    kort.row_factory = sqlite3.Row
    return kort


def _generator(kort, kurs, språk_db, frö=11):
    # STEGENS TOPP, inte talet 21. Nivån indexerar den flätade stegen, som är
    # olika lång i olika språk — se `dimensioner.toppnivå`.
    from sprakprog.kort.dimensioner import toppnivå
    g = Generator(språk_db, kort, kurs["målspråk"], källspråk=kurs["källspråk"],
                  nivå=toppnivå(kurs["målspråk"]), cefr="C2",
                  budget=kurs["budget"], frö=frö)
    g._läs_kort()
    return g


def prov_nåbarhet(kort, kurs, språk_db) -> list[str]:
    """Varje ordföljdskort ska gå att möta av någon mening."""
    s = kurs["målspråk"]
    kort.execute("UPDATE Kort SET sedd = '2026-01-01T00:00:00+00:00' "
                 "WHERE språk = ?", (s,))
    kort.commit()
    g = _generator(kort, kurs, språk_db)
    rörda: set[int] = set()
    for _ in range(KANDIDATER):
        m = g.samplare.kandidat()
        if m is None or g.validator.validera(m):
            continue
        r = g._rendera(m)
        if r is not None:
            rörda |= {k["id"] for k in r[1]}
    saknas = [r["egenskap"] for r in kort.execute(
        "SELECT id, egenskap FROM Kort WHERE språk = ? AND typ = 'ordföljd'",
        (s,)) if r["id"] not in rörda]
    return ([] if not saknas else
            [f"{len(saknas)} ordföljdskort går inte att möta: {saknas}"])


def prov_e6_delar_upp(kort, kurs, språk_db) -> list[str]:
    """Exponeringen ska skilja grundordföljden från konstruktionsreglerna.

    Provet skriver INGEN lista över vilka regler som är högfrekventa — hela
    poängen med A7 punkt 2 är att den listan inte behöver finnas. Det kräver
    bara att mätningen faktiskt separerar: minst en regel ur schemat och
    minst en kvar i det. Loggar renderaren ingenting alls hamnar allt i den
    ena högen, och då faller provet.
    """
    s = kurs["målspråk"]
    if len(ORDFÖLJD.get(s, [])) < 2:
        return []
    mät_exponering(kort, språk_db, s, meningar=SVEP)
    sätt_schemalagt(kort, TAKT, språk=s)
    rader = kort.execute(
        "SELECT egenskap, exponering, schemalagt FROM Kort "
        "WHERE språk = ? AND typ = 'ordföljd'", (s,)).fetchall()
    ur = [r["egenskap"] for r in rader if not r["schemalagt"]]
    kvar = [r["egenskap"] for r in rader if r["schemalagt"]]
    fel = []
    if not ur:
        fel.append("ingen regel lyftes ur schemat — grundordföljden möts i "
                   "varje mening och kan inte spacas (E6)")
    if not kvar:
        fel.append("ingen regel blev kvar i schemat — då finns inget "
                   "ordföljdskort kvar att öva")
    return fel


def prov_skulden(kort, kurs, språk_db) -> list[str]:
    """En omkastning ska fälla ordföljdskortet — men bara när regeln är EN.

    Provet kastar om de två första orden, vilket är en ren omkastning: varje
    ord är rätt hämtat och rätt böjt, så inget ORDKORT får fällas. Skulden
    hör till ordföljden.

    TVÅ LÄGEN, OCH DET ANDRA ÄR DET SOM GÖR PROVET SKARPT:

      ENTYDIGT   fler regler tillämpade än schemalagda, och exakt en av dem
                 schemalagd. Då ska just den fällas. Att kräva att FLER
                 tillämpats är inte pedanteri — det är det enda läget där
                 schemafiltret gör någon skillnad, och utan det kunde ett
                 prov utan filter se identiskt ut.

      FLERTYDIGT två eller fler SCHEMALAGDA regler i samma mening. Då vet vi
                 inte vilken som brast, och svaret ska vara tystnad — samma
                 regel som pinne 7 i D1 finns till för att undvika.

    JAPANSKAN UNDANTAS, och det är ingen lucka i provet utan D7. Japanskan
    skrivs utan mellanslag, så det finns ingen ordvis diff att göra — och
    utan diff finns ingen omkastning att upptäcka. Ordföljdskorten går att
    MÖTA på japanska (invariant 1 gäller där), men inte att skylla på.
    """
    s = kurs["målspråk"]
    if s not in ORDMELLANRUM:
        return []
    # ATTRIBUTIONEN FÖRUTSÄTTER ATT E6 HAR DELAT UPP. Utan mätningen är varje
    # regel schemalagd, och då finns inget läge där schemafiltret gör
    # skillnad — provet skulle mäta något annat än det påstår. Uppsättningen
    # hör alltså till provet och inte till en tidigare invariant.
    mät_exponering(kort, språk_db, s, meningar=SVEP)
    sätt_schemalagt(kort, TAKT, språk=s)
    g = _generator(kort, kurs, språk_db)
    fel: list[str] = []
    entydiga = flertydiga = 0
    for _ in range(KANDIDATER * 3):
        if entydiga >= 3 and flertydiga >= 1:
            break
        m = g.samplare.kandidat()
        if m is None or g.validator.validera(m):
            continue
        r = g._rendera(m)
        if r is None:
            continue
        text, kortlista, uppslag, egenskaper, rektioner, ordföljder, osm = r
        tillämpade = set(ordföljder)
        schemalagda = [k["egenskap"] for k in kortlista
                       if k["typ"] == "ordföljd" and k["schemalagt"]
                       and k["egenskap"] in tillämpade]
        entydigt = len(schemalagda) == 1 and len(tillämpade) > 1
        flertydigt = len(schemalagda) > 1
        if not (entydigt or flertydigt):
            continue
        if entydigt and entydiga >= 3:
            continue
        if flertydigt and flertydiga >= 1:
            continue
        ord_ = text.replace("?", "").replace(".", "").replace("!", "").split()
        if len(ord_) < 4 or ord_[0].lower() == ord_[1].lower():
            continue
        # DE TVÅ FÖRSTA ORDEN MÅSTE VARA VANLIGA ORD. Franskans frågeinledning
        # `Qu'est-ce que` är ett FAST UTTRYCK över flera tokens — att kasta om
        # dess två första delar är inte en omkastning av satsled utan att
        # trasa sönder en idiomatisk enhet, och då finns ingen ordföljdsregel
        # att skylla på. Provet skulle mäta något annat än det påstår.
        if any("'" in o for o in ord_[:2]):
            continue
        f = Förslag(m, text, None, kortlista, None, uppslag, egenskaper,
                    rektioner, ordföljder, False, osm)
        rätt = g.rätta(f, " ".join([ord_[1], ord_[0], *ord_[2:]]))
        fällda = [kort.execute("SELECT typ, egenskap FROM Kort WHERE id = ?",
                               (kid,)).fetchone()
                  for kid, ok in rätt.utfall.items() if not ok]
        typer = {k["typ"] for k in fällda}
        if entydigt:
            entydiga += 1
            if typer != {"ordföljd"}:
                fel.append(f"{text!r} ({sorted(tillämpade)}, schemalagd: "
                           f"{schemalagda}): fällde {sorted(typer) or 'inget'}, "
                           f"väntat bara ordföljd")
            elif fällda[0]["egenskap"] != schemalagda[0]:
                fel.append(f"{text!r}: fällde {fällda[0]['egenskap']!r}, "
                           f"väntat {schemalagda[0]!r}")
        else:
            flertydiga += 1
            if "ordföljd" in typer:
                fel.append(f"{text!r} har {len(schemalagda)} schemalagda regler "
                           f"({schemalagda}) men fällde ändå ett ordföljdskort")
    if not entydiga:
        fel.append("hittade ingen mening där schemafiltret gör skillnad — "
                   "provet mätte inte det det påstår")
    return fel


PROV = [("nåbarhet — varje regel går att möta", prov_nåbarhet),
        ("E6 delar upp reglerna själv", prov_e6_delar_upp),
        ("skulden landar på ordföljdskortet", prov_skulden)]


# ── falsifiering ────────────────────────────────────────────────────

def _sabotage_utan_logg():
    """Före A7 punkt 2: renderarna sa ingenting om vilken regel de tillämpade."""
    orig = Uppslag.ordföljd
    Uppslag.ordföljd = lambda själv, regel: None
    # Generatorns instrumentering ersätter metoden, så den måste tystas där
    # den LÄSES: `_rendera` sparar undan originalet och kallar det. Att
    # tomma ut den här räcker alltså inte — men listan byggs av anropet, så
    # vi tystar i stället källan: renderarna slutar anropa.
    from sprakprog.rendering import de as de_mod
    äkta = de_mod.TyskRenderare.satsled

    def tyst(själv, m, bisats=False):
        u = själv.u
        orig_metod = type(u).ordföljd
        type(u).ordföljd = lambda s_, regel: None
        try:
            return äkta(själv, m, bisats)
        finally:
            type(u).ordföljd = orig_metod

    de_mod.TyskRenderare.satsled = tyst

    def ångra():
        Uppslag.ordföljd = orig
        de_mod.TyskRenderare.satsled = äkta
    return ångra


def _sabotage_utan_entydighet():
    """Ta första schemalagda regeln i stället för att kräva exakt en."""
    from sprakprog.generator.rattning import Rättare
    orig = Rättare._ordföljdskortet

    def första(själv, kort, ordföljder):
        tillämpade = set(ordföljder)
        for k in kort:
            if (k["typ"] == "ordföljd" and k["schemalagt"]
                    and k["egenskap"] in tillämpade):
                return k
        return None

    Rättare._ordföljdskortet = första
    return lambda: setattr(Rättare, "_ordföljdskortet", orig)


def _sabotage_utan_schemafilter():
    """Räkna ALLA tillämpade regler, också de E6 lyft ur schemat.

    Då är svaret nästan alltid "flera regler, alltså tystnad", eftersom varje
    mening tillämpar sin grundordföljd — och den lågfrekventa regel som
    faktiskt brast kan aldrig fällas.
    """
    from sprakprog.generator.rattning import Rättare
    orig = Rättare._ordföljdskortet

    def utan_filter(själv, kort, ordföljder):
        tillämpade = set(ordföljder)
        k = [x for x in kort
             if x["typ"] == "ordföljd" and x["egenskap"] in tillämpade]
        return k[0] if len(k) == 1 else None

    Rättare._ordföljdskortet = utan_filter
    return lambda: setattr(Rättare, "_ordföljdskortet", orig)


SABOTAGE = [(_sabotage_utan_logg, 0),
            (_sabotage_utan_schemafilter, 2),
            (_sabotage_utan_entydighet, 2)]

NAMN = {0: "renderaren loggar ingen regel",
        2: "utan schemafiltret — grundordföljden dränker svaret",
        3: "utan entydighetskrav — gissar bland flera"}


def _kör(d: Path, märke: str, prov_f, språk_db) -> list[str]:
    brister = []
    kort = _kopia(d / f"{märke}.db")
    for kurs in kort.execute(
            "SELECT * FROM Kurs GROUP BY målspråk ORDER BY målspråk").fetchall():
        for b in prov_f(kort, kurs, språk_db):
            brister.append(f"[{kurs['målspråk']}] {b}")
    kort.close()
    return brister


def main() -> int:
    språk_db = anslut()
    fel = stumma = 0
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        print(f"{len(PROV)} invarianter, {KANDIDATER} kandidater per språk\n")
        for i, (namn, prov_f) in enumerate(PROV):
            brister = _kör(d, f"ren{i}", prov_f, språk_db)
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister[:5]:
                print(f"      {b}")

        print("\nfalsifiering — varje gammalt läge ska fälla sitt prov:")
        for i, (sab, mål) in enumerate(SABOTAGE):
            ångra = sab()
            try:
                brister = _kör(d, f"sab{i}", PROV[mål][1], språk_db)
            finally:
                ångra()
            if not brister:
                stumma += 1
            namn = sab.__doc__.splitlines()[0] if sab.__doc__ else str(i)
            print(f"  {'✓ föll' if brister else '✗ STUMT'}  {namn}"
                  + (f"  ({len(brister)} fynd)" if brister else ""))

    print(f"\n{len(PROV)} invarianter, {fel} brott." if fel
          else f"\n{len(PROV)} invarianter, alla håller.")
    if stumma:
        print(f"{stumma} sabotage fällde inte sitt prov.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
