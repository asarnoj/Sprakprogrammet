"""Prov för H3: representerar varje tal på skärmen det man tror?

VARFÖR DET HÄR PROVET FINNS. Ett tal som är fel larmar inte. Det ser ut som
alla andra tal, det uppdateras som alla andra, och det enda som avslöjar det
är att man gör vad det säger och får något annat. Fem sådana fel hittades för
hand på ett testpass, och sedan tre till: "7 new" på en dag där glosläget hade
noll att dela ut, "1 new" kvar på en klar dag, en uppdelning som räknade ur
fel tak.

G6 prövar att alla VÄGAR IN lyder samma regel. Det här provet prövar det
omvända: att alla TAL UT beskriver samma verklighet. `tjänsteprov` frågar
"gör ändpunkterna samma sak?"; det här frågar "stämmer det som står?".

INVARIANTERNA ÄR FORMULERADE SOM HANDLINGAR, inte som formler. Att jämföra
`att_göra` med `förfallna + igen + nya` vore att skriva om samma uttryck en
gång till — provet skulle bara säga att koden är sig lik. I stället GÖRS
dagen: drillen körs så många gånger som `glosor` säger, passet så länge det
ger uppgifter, och sedan frågas skärmen igen.

ALDRIG MOT DEN RIKTIGA DATABASEN — kopia via SQLites backup.

Kör:  python ordbok/verktyg/indikatorprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kort.db import anslut_kort           # noqa: E402
from sprakprog.webb import Övningstjänst                 # noqa: E402

#: Så många varv dagen får ta innan provet ger upp. En dag som inte tar slut
#: på hundra varv tar inte slut.
VARV = 100


def tjänst(kopia: Path):
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(kopia)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    kort = anslut_kort(kopia, delad_mellan_trådar=True)
    språk = sqlite3.connect(ROT / "sprak.db", check_same_thread=False)
    språk.row_factory = sqlite3.Row
    tj = Övningstjänst(kort, språk)
    äkta = tj._generator

    def frödd(kurs):
        g = äkta(kurs)
        g.rng.seed(0)
        return g

    tj._generator = frödd
    return tj, kort


def _gör_dagen(tj, kurs_id, *, rätt=True, spår=None):
    """Gör exakt vad skärmen säger, och notera vad varje steg gav."""
    for _ in range(VARV):
        h = tj.hem(kurs_id)
        i = h["idag"]
        if spår is not None:
            spår.append(dict(i))
        if i["klar"]:
            return "klar"
        if i["glosor"]:
            g = tj.glosor(kurs_id)
            if not g["ord"]:
                return "glosor lovade men gav inga"
            for o in g["ord"]:
                tj.glossvar(kurs_id, o["kort_id"], True)
            continue
        u = tj.uppgift(kurs_id)
        if u is None:
            return "uppgift gav None"
        if u.get("tomt"):
            return "tomt"
        f = tj._öppna[u["id"]][1]
        tj.svara(u["id"], f.text if rätt else "")
        tj.bokför(u["id"])
    return "tog aldrig slut"


# ── invarianterna ────────────────────────────────────────────────────

def prov_dagen_tar_slut(tj, kort, kurs) -> list[str]:
    """Följer man skärmen ska `klar` bli sant och `att_göra` noll.

    DET ÄR DEN GRUNDLÄGGANDE UTFÄSTELSEN. Allt annat på hemskärmen är en
    uppdelning av den. Håller den inte spelar det ingen roll att delarna
    summerar rätt.
    """
    utfall = _gör_dagen(tj, kurs["id"])
    i = tj.hem(kurs["id"])["idag"]
    if utfall == "tog aldrig slut":
        return [f"dagen tog inte slut på {VARV} varv (att_göra={i['att_göra']})"]
    if not i["klar"]:
        return [f"passet svarade {utfall!r} men skärmen säger inte klar "
                f"(att_göra={i['att_göra']}, nya={i['nya']}, "
                f"förfallna={i['förfallna']}, igen={i['igen']})"]
    if i["att_göra"]:
        return [f"klar men att_göra={i['att_göra']}"]
    return []


def prov_inget_tal_lovar_för_mycket(tj, kort, kurs) -> list[str]:
    """Varje tal ska motsvaras av lika mycket faktiskt arbete.

    Talen kontrolleras EN I TAGET mot den ändpunkt som ska leverera dem.
    `glosor` mot glosvyn, `igen` mot passkön, `förfallna` mot kön.
    """
    fel = []
    h = tj.hem(kurs["id"])
    i = h["idag"]
    if i["glosor"]:
        fick = len(tj.glosor(kurs["id"])["ord"])
        if fick != i["glosor"]:
            fel.append(f"glosor sa {i['glosor']}, vyn gav {fick}")
    ordrad = next((r["nya"] for r in h["typer"] if r["typ"] == "ord"), 0)
    if ordrad != i["glosor"]:
        fel.append(f"uppdelningen sa {ordrad} nya ordkort, glosraden {i['glosor']}")
    g = tj._generatorer.get(
        (kurs["källspråk"], kurs["målspråk"], kurs["nivå"], kurs["budget"]))
    if g is not None and g.passkö() != i["igen"]:
        fel.append(f"igen sa {i['igen']}, passkön har {g.passkö()}")
    return fel


def prov_summan_stämmer(tj, kort, kurs) -> list[str]:
    """`att_göra` ska vara summan av sina delar, hela dagen igenom.

    Prövas på varje MELLANLÄGE och inte bara i början: felet som gav "1 new"
    kvar på en klar dag var just att en del uppdaterades utan att summan
    följde med.
    """
    spår: list[dict] = []
    _gör_dagen(tj, kurs["id"], spår=spår)
    fel = []
    for n, i in enumerate(spår):
        # GLOSORNA ÄR EN EGEN DEL sedan passlagret. Förut låg de inbakade i
        # `nya`, vilket dolde att drillen och meningarna drar ur olika delar
        # av dagen — och gjorde det omöjligt att se när den ena tog slut.
        summa = (i["förfallna"] + i["igen"] + i["nya"] + i["glosor"])
        if i["att_göra"] != summa:
            fel.append(f"varv {n}: att_göra={i['att_göra']} men delarna ger "
                       f"{summa} (förf {i['förfallna']} + igen {i['igen']} + "
                       f"nya {i['nya']} + glosor {i['glosor']})")
        if i["klar"] and i["att_göra"]:
            fel.append(f"varv {n}: klar men att_göra={i['att_göra']}")
        # OCH DEN UPPDELNING SKÄRMEN FAKTISKT RITAR ska summera till samma
        # tal. Raden ovan prövar de fyra LÖSA talen; `delar` är den lista
        # gränssnittet renderar, och det var där felet satt.
        #
        # Sidan räknade tidigare fram sin egen uppdelning i JS —
        # `former = max(0, nya − glosor)` — och drog därmed bort ett tal som
        # inte ingick, eftersom `nya` och `glosor` är olika roller i
        # `Passkort` och aldrig överlappar. Mätt 2026-08-26: rubriken sa 57
        # kort medan raden under summerade till 52, och japanskans rubrik sa
        # 50 med knapptexten "0 due · 0 new" bredvid sig.
        #
        # Inget prov fångade det, och det är hela lärdomen: näten prövade
        # API:t, och ingenting prövade vad SIDAN räknade fram ur det. Svaret
        # blev att flytta räkningen till servern, där den går att pröva —
        # inte att skriva ett prov som kör JavaScript.
        delar = i.get("delar")
        if delar is None:
            fel.append(f"varv {n}: `delar` saknas — gränssnittet får då "
                       f"räkna själv, vilket är felet regeln finns mot")
        else:
            d = sum(x["antal"] for x in delar)
            if d != i["att_göra"]:
                fel.append(f"varv {n}: att_göra={i['att_göra']} men `delar` "
                           f"ger {d} ({delar})")
            if any(x["antal"] <= 0 for x in delar):
                fel.append(f"varv {n}: `delar` bär en nolla — en del utan "
                           f"arbete ska inte ritas alls: {delar}")
    return fel[:4]


def prov_inget_tal_för_låst_läge(tj, kort, kurs) -> list[str]:
    """Ett låst läge ska inte visa hur mycket det skulle ha haft.

    Extraövningen är låst tills dagen är gjord (B6). Att den ändå rapporterar
    `nya` är att visa ett tal som ingen knapp kan lösa in — och det var så
    "7 new" kunde stå kvar bredvid en låst knapp.
    """
    e = tj.hem(kurs["id"])["extra"]
    if e["låst"] and (e["nya"] or e["tidiga"]):
        return [f"extraläget är låst men visar nya={e['nya']} "
                f"tidiga={e['tidiga']}"]
    return []


def prov_tiden_följer_arbetet(tj, kort, kurs) -> list[str]:
    """`minuter_kvar` ska vara `att_göra` omräknat med RÄTT växelkurs.

    Talet är användarens enhet (B4). Är det räknat ur något annat än det
    arbete skärmen samtidigt visar är det två åsikter om samma dag.

    OCH NÄMNAREN MÅSTE VARA DENSAMMA SOM TÄLJAREN RÄKNAR. Provet krävde
    tidigare `att_göra × sekunder_per_repetition`, och det var självt felet:
    `att_göra` räknar PASSRADER medan `sekunder_per_repetition` har BEDÖMDA
    KORT i nämnaren. En mening betygsätter fler kort än den stänger rader
    (mätt: 1,33–1,80 rader per svar mot 2,4 bedömda kort), så produkten
    underskattade dagen med omkring hälften — och provet höll med, eftersom
    det prövade samma felaktiga formel.

    Ett prov som skriver om koden en gång till bevisar bara att koden är sig
    lik. Det här jämför mot `sekunder_per_rad`, som mäter tid per rad direkt
    ur `Passkort.tidpunkt` — en räkning och inte en modell.
    """
    i = tj.hem(kurs["id"])["idag"]
    spr = i.get("sek_per_rad")
    if i["minuter_kvar"] is None:
        return ([] if not spr else
                [f"minuter_kvar är None fast raderna är mätta ({spr:.2f} s/rad)"])
    if not spr:
        return ["minuter_kvar visas utan att sekunder_per_rad är mätt"]
    väntat = round(i["att_göra"] * spr / 60)
    if i["minuter_kvar"] != väntat:
        return [f"minuter_kvar={i['minuter_kvar']} men {i['att_göra']} rader "
                f"× {spr:.2f} s ger {väntat}"]
    return []


def prov_kostnad_per_läge(tj, kort, kurs) -> list[str]:
    """Takten och uppdelningen ska vara ense om VAD som är mätt.

    De kommer ur samma logg, så de får aldrig vara oense om huruvida en
    mätning finns. Det var felet H3 fann: takten sa "3,67 s/rep" för tyskan
    — ärvt från franskan, som `sekunder_per_repetition` uttryckligen ska
    göra — medan uppdelningen sa None på BÅDA lägena, eftersom den krävde
    tyska rader. Två tal bredvid varandra på samma skärm, det ena mätt och
    det andra omätt, och ingen väg att se vilket som ljög.

    KRAVET ÄR "MINST ETT LÄGE", INTE "BÅDA", och det är en rättelse av
    provet och inte en uppmjukning. Formuleringen var `alla lägen har ett
    tal`, och den är inte härledd: takten är POOLAD över mening och glosa,
    medan uppdelningen skiljer dem åt. En kurs vars hela tidtagna historik
    är drill har därför ett giltigt poolat tal och inget meningstal — det
    finns ingenting att räkna det på.

    Mätt 2026-08-26, och det är precis franskans läge:

        de   50 bedömningar via mening,  0 tidtagna,  0 glosor
        en   39 via mening, 39 tidtagna, 11 glosor, 9 tidtagna
        fr    0 via mening,              11 glosor, 10 tidtagna

    Franskans 2,90 s/rep är alltså mätt, ur tio drillade ord, och att kräva
    ett meningstal där vore att kräva att systemet hittar på ett. Det gamla
    provet fällde koden för att den vägrade göra just det.

    Kvar står den kontroll som faktiskt fångar oenigheten, åt båda hållen.
    """
    i = tj.hem(kurs["id"])["idag"]
    lägen = i["per_läge"] or {}
    mätta = [k for k, v in lägen.items() if v is not None]
    if i["sek_per_rep"] and not mätta:
        return [f"takten är mätt ({i['sek_per_rep']:.2f} s/rep) men "
                f"inget läge har ett tal: {lägen}"]
    if not i["sek_per_rep"] and mätta:
        return [f"takten är omätt men per_läge har tal för {mätta}"]
    return []


PROV = [("dagen tar slut om man följer skärmen", prov_dagen_tar_slut),
        ("inget tal lovar mer än ändpunkten ger", prov_inget_tal_lovar_för_mycket),
        ("att_göra är summan av sina delar", prov_summan_stämmer),
        ("inget tal för ett låst läge", prov_inget_tal_för_låst_läge),
        ("minuter_kvar följer arbetet", prov_tiden_följer_arbetet),
        ("takten och uppdelningen är ense om vad som är mätt",
         prov_kostnad_per_läge)]


def main() -> int:
    fel = 0
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        print(f"{len(PROV)} invarianter över hemskärmens tal\n")
        for nr, (namn, kör) in enumerate(PROV):
            # Egen kopia per prov: de gör dagen och ändrar tillståndet.
            tj, kort = tjänst(d / f"ind{nr}.db")
            brister = []
            for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
                for b in kör(tj, kort, kurs):
                    brister.append(f"[{kurs['id']} {kurs['målspråk']}] {b}")
            kort.close()
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister[:6]:
                print(f"      {b}")
    print(f"\n{len(PROV)} invarianter, {fel} brott." if fel
          else f"\n{len(PROV)} invarianter, alla håller.")
    return 1 if fel else 0


if __name__ == "__main__":
    raise SystemExit(main())
