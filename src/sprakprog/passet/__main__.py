"""Dagspasset i terminalen — version ett av gränssnittet (KÄRNAN 5.1, punkt 9).

    python -m sprakprog.passet --karta kartor/en.pkl --nivåer kartor/nivaer_en.json

Kursen är ett språkpar: källspråket är det du översätter från, målspråket det du
skriver. Kartan och nivåerna hör till målspråket.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from ..fsrslager import Lager
from ..kortmodell import Kort, meningens_kort
from ..kurs import Kursdata
from ..rattning import FEL
from ..rendering.karta import ladda
from .tid import Meningstid, Tidsmodell, arbetsprofil
from ..sammansattning import Sammansättare
from . import Passet

ROT = Path(__file__).resolve().parents[3]


def _nivåfil(fil: str) -> tuple[dict[Kort, frozenset], list[frozenset]]:
    """Kraven per kort och nivåerna i öppningsordning (4.2)."""
    data = json.loads(Path(fil).read_text(encoding="utf-8"))

    def kort(rad) -> Kort:
        return Kort(rad[0], rad[1], tuple(rad[2]))

    krav = {kort(k): frozenset(map(kort, m)) for k, m in data["krav"]}
    return krav, [frozenset(map(kort, n)) for n in data["nivåer"]]


#: Hur långt fram arbetsprofilen räknas. Ett kort kostar arbete i över ett år
#: (8,37 repetitioner), och profilen måste täcka den svansen för att 5.5:s
#: minimering ska hitta den verkliga toppen. Ett år plus lite marginal.
PROFILDAGAR = 400


def _kort_i_kursen(s: Sammansättare, nivåer: list[frozenset]) -> int:
    """Hur många kort kursen har i allt — horisonten i 5.5.

    «Kursen slutar när alla kort är införda.» Mängden är varje korts som
    formtabellen ger för språkets lexem, plus nivåernas regler och ändelser.
    """
    alla: set[Kort] = {k for n in nivåer for k in n}
    rader = s.u.conn.execute(
        """SELECT l.*, k.ordklass, k.roll, k.nyckel FROM Lexem l
           JOIN Koncept k ON k.id = l.koncept_id WHERE l.språk = ?""",
        (s.språk,)).fetchall()
    for rad in rader:
        try:
            for korten in s.tabell.former(rad).values():
                alla.update(korten)
        except Exception:                                          # noqa: BLE001
            continue
    return len(alla)


def _tidsmodell(data: Kursdata, retention: float, fil: str):
    """Tidsmodellen (5.5), eller None när något mått saknas.

    Tre mått krävs, och alla tre är mätta: meningens kostnad ur den gamla loggen
    (6.3), introövningens tid ur kursens egen logg, och hur tätt dagens meningar
    packas. Saknas något svarar modellen inte alls — «utan talet finns ingen väg
    från minuter till kort».
    """
    meningstid = Meningstid.ur_fil(fil)
    if meningstid is None:
        return None
    # Kursens egna mått när de finns, annars den gamla loggens (5.5).
    täthet = data.korttäthet() or meningstid.täthet
    introsekunder = data.introsekunder()
    if introsekunder is None:
        # Introövningen är en mening med ett enda mål, så dess kostnad är
        # linjens värde för ett kort. En övre gräns för en glosa, vilket är
        # riktningen 5.5 kräver: färre nya kort, aldrig fler.
        introsekunder = meningstid.fast + meningstid.per_kort
    profil, _ = arbetsprofil(retention, PROFILDAGAR)
    return Tidsmodell(profil, meningstid, täthet, introsekunder)


def _fråga(text: str) -> str:
    try:
        return input(text).strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def _ställ(passet: Passet, uppgift, *, fas: str = "mening",
           paket: frozenset = frozenset()) -> bool:
    """Ställ meningen och rätta svaret.

    Ger True när allt gick rätt, False när något föll och None när användaren
    hoppade över. Utan det sista satt man fast: ett `n` för att gå vidare
    rättades som översättning, tre gånger i rad i den första körningen.

    I introfasen (`fas="intro"`) BOKFÖRS INGENTING (5.4). Övningen finns för
    att användaren inte ska möta ny kunskap oförberedd, inte för FSRS; kortet
    prövas på riktigt först i meningsfasen.

    OCH DÄR BEDÖMS BARA DET NYA KORTET. «En övning görs om tills det NYA
    KORTET blir rätt … Fel på lånekorten spelar ingen roll, utom när de döljer
    det nya kortet (R5); då görs övningen om» (5.4). Att döljas syns på att
    målet självt faller: rättningen knyter avvikelsen till varje kort som
    bestämde ordet, så ett lånefel som rör målets positioner fäller målet.
    Villkoret «målet gick rätt» är alltså båda reglerna på en gång.

    Hela meningen bedömdes förut, och det fällde en övning som hade gjort sitt:
    «En stad faller.» besvarad «A city fall.» hade artikeln — övningens kort —
    helt rätt, men saknade verbets -s. Introfasen pausade, och åtta kort föll
    ur dagen för ett fel på ett lånekort.
    """
    uppgift = passet.ställ(uppgift, fas)
    print(f"\n  {uppgift.källtext}")
    start = time.perf_counter()
    svar = _fråga("  > ")
    if svar == "q":
        raise SystemExit
    if svar == "s":
        print("  hoppade över.")
        return None
    rättning = passet.rätta(uppgift, svar, time.perf_counter() - start)
    intro = fas == "intro"
    if intro:
        målen = {k for k in uppgift.mål if rättning.betyg.get(k) == FEL}
        if not målen:
            if rättning.rätt:
                print("  rätt.")
            else:
                # Lånekorten är inte övningens sak, men facit ska synas: annars
                # lär sig användaren en felstavning som «rätt».
                print(f"  rätt i {', '.join(str(k) for k in uppgift.mål)}.")
                print(f"  facit:   {uppgift.facit}")
                print(f"  ({', '.join(str(k) for k in rättning.fel)} föll, "
                      "men de prövas i meningsfasen)")
                _fråga("  [enter] vidare\n  ")
            return True
        print(f"  facit:   {uppgift.facit}")
        print(f"  fel i:   {', '.join(str(k) for k in rättning.fel) or '—'}")
        _fråga("  [enter] vidare\n  ")
        return False
    if rättning.rätt:
        val = _fråga("  rätt.    [enter] vidare · h svårt · e lätt\n  ")
        höjt = {k: "hard" if val == "h" else "easy" for k in rättning.betyg} \
            if val in ("h", "e") else None
        passet.bokför(uppgift, rättning, höjt=höjt, paket=paket)
        return True
    print(f"  facit:   {uppgift.facit}")
    print(f"  fel i:   {', '.join(str(k) for k in rättning.fel) or '—'}")
    val = _fråga("  [enter] vidare · r jag hade rätt · f flagga facit\n  ")
    if val == "r":
        # Rätt svar som facit inte hade: korten godkänns och facit granskas.
        passet.bokför(uppgift, rättning, godkända=frozenset(rättning.betyg),
                      flagga=svar, paket=paket)
        print("  godkänt, och facit flaggat för granskning.")
        return True
    if val == "f":
        passet.bokför(uppgift, rättning, flagga=svar, paket=paket)
        print("  facit flaggat.")
    else:
        passet.bokför(uppgift, rättning, paket=paket)
    return False


def _glosor(passet: Passet, kö: list) -> bool:
    """Lär ut övningens okända innehållsord först (5.4).

    «Ordningen inom dagen följer kraven. Ett kort presenteras efter de kort
    det kräver, så att lånekorten redan är införda eller presenterade.»

    Utan det här prövade den första övningen tre okända saker och kallade en
    av dem mål: SVO lärdes ut med «Tid står.», där varken `tid` eller `står`
    hade visats. Dag ett ska i stället nå sin första mening när användaren kan
    ett pronomen och ett verb (5.4).

    Ger False när användaren avbröt.
    """
    if not kö:
        return True
    # VISA FÖRST, FRÅGA SEDAN. En glosa på ett ord användaren aldrig sett är
    # inte en övning utan ett prov före undervisningen — och introfasen finns
    # för att ingen ska möta ny kunskap oförberedd (5.4). Alla ordparen visas
    # därför först, och frågas sedan i samma ordning: de som visades tidigast
    # hinner sjunka undan innan de efterfrågas.
    print(f"    orden först ({len(kö)} st):")
    for glosa in kö:
        print(f"      {glosa.källtext}  =  {glosa.facit}")
    _fråga("      [enter] när du sett dem\n      ")
    envis = 0
    while kö:
        glosa = kö.pop(0)
        mening_id = passet.data.ny_mening(
            "glosa", str(glosa.kort), glosa.källtext, sorted(glosa.former))
        # TIDEN TAS. Den var hårdkodad till noll, och då är glosfasens kostnad
        # osynlig för tidsmodellen — som enligt 5.5 ska mätas ur loggen: «tid
        # per introövning, med omtag». Sexton glosor låg i loggen med 0,0 s.
        start = time.perf_counter()
        svar = _fråga(f"      {glosa.källtext}  →  ")
        gick = time.perf_counter() - start
        if svar == "q":
            raise SystemExit
        if svar == "s":
            print("      hoppade över.")
            return False
        passet.data.svara(mening_id, svar, gick)
        if passet.rätta_glosa(glosa, svar):
            print("      rätt.")
            passet.data.presentera(glosa.kort)
            envis = 0
            continue
        # ETT RÄTT SVAR SOM FACIT INTE HADE. Glosans facit är ETT ord, och ett
        # ord har sällan en enda översättning: `passa` blev fällt för «fit»,
        # som är lika riktigt som «suit». Meningsfasen har haft `r` för det
        # här hela tiden; glosfasen hade det inte, fast dess facit är smalare.
        # Svaret flaggas för granskning av datan (3.4), precis som där.
        print(f"      facit: {glosa.facit}")
        val = _fråga("      [enter] vidare · r jag hade rätt\n      ")
        if val == "q":
            raise SystemExit
        if val == "r":
            passet.data.rapportera_fel(
                f"glosan «{glosa.källtext}» godtog inte «{svar}»", kort=glosa.kort,
                mening_id=mening_id)
            passet.data.presentera(glosa.kort)
            print("      godkänt, och facit flaggat för granskning.")
            envis = 0
            continue
        kö.append(glosa)                      # sist i kön (5.4)
        envis += 1
        if envis > len(kö):
            print("      orden sitter inte än — introfasen pausas.")
            return False
    passet.uppdatera()
    return True


def _lektion(passet: Passet, uppgift, kort, logga: bool = True) -> None:
    """Visa kortet i en färdig mening innan det prövas (5.4).

    Utan det här är introövningen ett prov före undervisningen: användaren
    möter regeln kall och kan omöjligt svara rätt. Exemplet visar meningen
    med facit, och vilka ord kortet självt bestämde — positionerna räknas
    fram, de skrivs inte för hand (6.2).

    Meningen loggas som en ställd lektion, så att samma källmening inte kommer
    igen som övning eller uppgift samma dag (6.1 punkt 8). Övningen blir
    därför en ANNAN mening med samma kort som mål.
    """
    if logga:
        uppgift = passet.ställ(uppgift, "lektion")
    orden = [str(o) for o in uppgift.ut.ord]
    platserna = [p for k, ps in meningens_kort(passet.s.tabell, uppgift.ut)
                 if k == kort for p in ps]
    egna = {i for sort, i in platserna if sort == "ord"}
    luckor = {i for sort, i in platserna if sort == "lucka"}
    # En lucka är platsen där ett ord HADE stått: den nakna frasens uteblivna
    # artikel syns bara så (6.2). Utan den vore lektionen tom för just de kort
    # vars hela innebörd är att ingenting skrivs.
    bitar = []
    for i, o in enumerate(orden):
        if i in luckor:
            bitar.append("_")
        bitar.append(f"[{o}]" if i in egna else o)
    if len(orden) in luckor:
        bitar.append("_")
    print(f"    exempel:  {uppgift.källtext}")
    print(f"              {uppgift.facit}")
    if egna or luckor:
        print(f"    kortet bestämmer:  {' '.join(bitar)}"
              + ("    (_ = ordet som INTE skrivs)" if luckor else ""))


def _introfas(passet: Passet, plan) -> None:
    """Gå igenom dagsplanens introövningar, ett kort i taget (5.1, 5.4).

    FASEN FÖLJER PLANEN och bygger ingenting själv. Planen lades innan passet
    började (5.1) och vet vilken mening som bär vilket kort; byggde fasen sin
    egen övning kunde den ta just den mening huvuddelen hade reserverat, och
    villkor 8 i 6.1 gör den då förbrukad.

    Ordningen följer kraven: övningens okända innehållsord lärs ut som glosor
    innan kortet som behöver dem. Ingenting bokförs — övningen finns för att
    användaren inte ska möta ny kunskap oförberedd, och kortet prövas på
    riktigt först i meningsfasen.

    Ett kort räknas som presenterat när det KLARAT övningen (5.1). Går den
    fel läggs kortet sist i kön och görs om senare, inte direkt: då har
    användaren facit i färskt minne.
    """
    for kort, orsak in plan.karantän:
        passet.data.sätt_i_karantän(kort, orsak)
        print(f"  ⚠ {kort} i karantän: {orsak}")
    kvar = [(k, u) for k, u in plan.introövningar
            if k not in passet.data.presenterade()]
    if not kvar:
        print("  allt i nästa nivå är redan presenterat i dag — korten prövas "
              "i meningar nu ([enter]).")
        return
    # Ett FUNKTIONSORD står i båda: det har en introövning som ett mönsterkort
    # och är ett ordkort. Räknades det två gånger stämde inte summan — «15 kort
    # — 4 mönsterkort och 12 ord».
    nya_ord = plan.orden - {k for k, _ in plan.introövningar}
    print(f"  introfasen: {len(plan.kort)} kort — {len(kvar)} med egen övning "
          f"och {len(nya_ord)} ord. Inget bokförs här.")

    # ORDEN FÖRST, ALLA PÅ EN GÅNG — och det är kravordningen i 5.4, inte ett
    # tycke. Ett innehållsords övning är en GLOSA, och en glosa kräver ingen
    # mening: kortet kräver alltså ingenting och kan alltid gå först. Ett
    # mönsterkorts övning är en mening, och den kräver sina ord. Mätt över
    # engelskans nivåer: av 119 ordkort som kräver en regel är 119 funktionsord
    # — som enligt 5.4 också övas med en mening — och noll innehållsord.
    #
    # Att fråga kort för kort «vilka av MINA ord är inte utlärda än» gav 3, 1,
    # 1, 0, 0 och en svans på 1: klumparna var den frågan ställd lokalt om
    # något planen redan visste globalt. Planen vet varje ord dagen behöver.
    allt = [u for _, u in plan.introövningar] + list(plan.lektioner.values()) \
        + list(plan.meningsfasen)
    if not _glosor(passet, passet.glosorna(*allt)):
        return

    lästa: set[str] = set()
    envis = 0
    while kvar:
        kort, övning = kvar.pop(0)
        lektion = plan.lektioner.get(kort)
        print(f"\n  lär dig nu:  {kort}")
        if lektion is not None:
            # Samma lektionsmening gås igenom en gång per kort, med olika kort
            # markerat — men den loggas som ställd EN gång (6.1 punkt 8).
            _lektion(passet, lektion, kort, logga=lektion.källtext not in lästa)
            lästa.add(lektion.källtext)
        utfall = _ställ(passet, övning, fas="intro")
        if utfall:
            passet.klarat_introövningen(kort)
            envis = 0
            continue
        if utfall is None:
            print("  introfasen avbruten.")
            return
        # «Ett kort som misslyckas läggs sist i introfasens kö» (5.4) — men
        # sist i en TOM kö är samma fråga igen, direkt, med facit i färskt
        # minne. Det är just det villkor 8 i 6.1 finns för att hindra, och en
        # körning ställde «Väder passar.» två gånger i rad. Finns inget annat
        # kort att skjuta in emellan pausas fasen i stället; kortet blir då
        # inte presenterat, och kan därför inte heller användas i dagens
        # meningar (5.1).
        if not kvar:
            print("  kortet sitter inte än, och det finns ingen annan övning "
                  "att lägga emellan — introfasen pausas.")
            return
        kvar.append((kort, övning))
        envis += 1
        if envis > len(kvar):
            print("  inget kort går rätt just nu — introfasen pausas.")
            return

    print("\n  nivån är presenterad. Korten prövas nu i meningar.")


def main() -> None:
    p = argparse.ArgumentParser(description="Ett dagspass i terminalen.")
    p.add_argument("--kurs", default=str(ROT / "kurs.db"))
    p.add_argument("--karta", default=str(ROT / "kartor" / "en.pkl"))
    p.add_argument("--nivåer", default=str(ROT / "kartor" / "nivaer_en.json"))
    p.add_argument("--källspråk", default="sv")
    p.add_argument("--minuter", type=float, default=20.0,
                   help="tiden per dag; tidsmodellen (5.5) gör den till ett "
                        "antal nya kort")
    p.add_argument("--meningstid",
                   default=str(ROT / "ordbok" / "nivålistor" / "meningstid.csv"),
                   help="meningens mätta kostnad (6.3); utan den finns ingen "
                        "gräns för hur mycket nytt en dag tar")
    a = p.parse_args()

    karta = ladda(a.karta)
    språk = karta["språk"]
    sprak = sqlite3.connect(ROT / "sprak.db")
    data = Kursdata(sqlite3.connect(a.kurs), a.källspråk, språk)
    krav, nivåer = _nivåfil(a.nivåer)
    lager = Lager(data)
    sam = Sammansättare(sprak, karta, par=a.källspråk)
    passet = Passet(data, sam,
                    lager, krav, nivåer,
                    tidsmodell=_tidsmodell(data, lager.retention, a.meningstid),
                    kort_i_kursen=_kort_i_kursen(sam, nivåer))

    print(f"{a.källspråk} → {språk}.  [enter] öva · n nästa nivå · q sluta")
    print("  när en mening ställs: skriv översättningen, "
          "s hoppar över, q slutar")
    # Dagens plan läggs en gång och gäller hela dagen (5.1). Den håller också
    # ihop faserna: introfasen tar sina övningar ur den, och meningsfasen sina
    # meningar, så att de två aldrig slåss om samma källmening (6.1 punkt 8).
    plan = None
    #: Dygnet planen lades. Nya nivåer öppnas bara vid passets start (4.4), så
    #: en plan per dygn — inte en per tangenttryckning.
    planens_dag = None
    #: Kort vars meningar tagit slut i dag (6.1 punkt 8). Dagsskopat, inte
    #: karantän: i morgon gäller villkoret inte och kortet tas om (5.1).
    utan_material: set = set()
    while True:
        läge = passet.läge()
        print(f"\n[{läge['dag']} {läge['tid']}]  införda {läge['införda']} · "
              f"presenterade {läge['presenterade']} · svaga {läge['svaga']} · "
              # `i_paketet` är PAKETETS kort (3.10) — de som en minsta mening
              # kräver. Dagsplanen är större, eftersom den också behöver ORD
              # att bygga olika meningar av (5.1): paketet sa 7 och dagen lärde
              # ut 13. Talet är ett golv tills planen finns, och sägs så.
              + (f"att lära in {len(plan.kort - passet.data.införda())}"
                 if plan is not None else
                 f"att lära in minst {läge['i_paketet']}"))
        val = _fråga("> ")
        if val == "q":
            return
        if val == "n":
            # EN PLAN PER DAG (4.4, 5.1). «Nivåer öppnas bara när passet startas:
            # starta eller starta med nya nivåer. Planen räknas ut efter valet
            # och ändras inte under passet.» Och 5.1: «vilka nya kort dagen har
            # är bestämt innan passet börjar».
            #
            # Förut lade varje `n`-tryck en NY plan, så «dagens plan» var i
            # själva verket «den här nivåns plan» — och fyra nivåer gick igenom
            # på fem minuter.
            if planens_dag == data.dag():
                print("  dagens plan är redan lagd, och den ändras inte under "
                      "passet (4.4). Öva det du har med [enter]; nya nivåer "
                      "öppnas i morgon.")
                continue
            svar = passet.tempo(a.minuter)
            if svar is not None:
                tempot, budget = svar
                print(f"  {a.minuter:.0f} min om dagen räcker till "
                      f"{tempot.nya} nya kort; med sparat {budget:.1f}. "
                      f"Kursen tar {tempot.slutdagen} dagar i det tempot.")
            print("  lägger dagens plan …")
            plan = passet.dagsplan(rapport=lambda r: print(r, flush=True))
            planens_dag = data.dag()
            nya = len(plan.kort - data.införda())
            if svar is not None:
                # Det som inte gick åt sparas till i morgon (5.5).
                data.spara_tempo(nya, max(0.0, budget - nya))
                if nya > budget:
                    print(f"  ⚠ planen har {nya} nya kort men budgeten var "
                          f"{budget:.1f} — paketet togs helt (3.10).")
            _introfas(passet, plan)
            # Faserna följer på varandra (5.1): efter introfasen prövas korten
            # i meningar. Att gå tillbaka till menyn här var det som lät
            # introfasen köras om i stället, och passet nådde aldrig fram.
            val = ""
        svaga = sorted(passet.svaga(), key=str)
        if not svaga:
            print("  inget svagt kort just nu — ta nästa nivå med n.")
            continue
        # Meningsfasen körs tills högarna är tomma (5.3), inte en mening per
        # tangenttryck: dagen är klar när det svaga är klarat.
        #
        # ETT KORT UTAN MENING ÄR INTE KLART. Förut ströks det bara ur den
        # lokala listan, och när listan tog slut sa passet «högarna är tomma —
        # dagens arbete är gjort». Det var falskt: `gen_passa` föll på «Tid
        # passar.», alla fyra meningar med ordet var förbrukade (villkor 8),
        # och kortet blev aldrig infört.
        #
        # Det är inget FEL och ingen karantän — 6.1 punkt 8 säger det rakt ut:
        # «En annan dag gäller inte villkoret … det är inget brott mot
        # invarianten i 3.10». Kortet börjar om som nytt i morgon (5.1). Men
        # dagen ska säga det.
        #
        # Mängden ligger UTANFÖR menyloopen. Låg den innanför prövades kortet
        # på nytt vid varje [enter], och att bevisa att ingen mening finns
        # kostar 18 s — passet blev obrukbart efter ett enda fel.
        while svaga:
            kortet = svaga[0]
            uppgift = passet.uppgift(kortet, plan)
            if uppgift is None:
                print(f"  {kortet}: dagens meningar för kortet är slut — "
                      "det börjar om i morgon (5.1).")
                utan_material.add(kortet)
                svaga = [k for k in svaga if k != kortet]
                continue
            if _ställ(passet, uppgift) is None:
                break
            svaga = [k for k in sorted(passet.svaga(), key=str)
                     if k not in utan_material]
        if svaga:
            continue
        kvar = sorted(passet.svaga() & utan_material, key=str)
        if kvar:
            print(f"\n  dagen är slut. {len(kvar)} kort kom inte in: "
                  + ", ".join(map(str, kvar)) + " — de tas om i morgon (5.1).")
        else:
            print("\n  högarna är tomma — dagens arbete är gjort (5.3).")


if __name__ == "__main__":
    main()
