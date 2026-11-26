"""Prov för passets LIVSCYKEL: när är ett pass fortfarande giltigt?

VARFÖR DET HÄR PROVET FINNS. Passlagret löste att dagen räknades om vid varje
anrop och kunde krympa under användaren. Men ett faktum som bestäms en gång
får ett nytt problem i stället: det kan bli FÖRÅLDRAT. Och det blev det
omedelbart.

    nollställ en kurs   →  "Done for today" utan att man gjort något
    nollställ en ANNAN  →  samma sak i en kurs man inte rört
    kurs mot samma språk
    lås upp en nivå     →  149 nya kort, och dagen ändrades inte
    ändra minuterna     →  ratten fungerade men syntes aldrig

De två första var samma fel: `ON DELETE CASCADE` på `Passkort.kort_id`.
Raderas korten tog kaskaden passets rader med sig, och kvar blev ett Pass med
noll rader — vilket betyder "inget väntar", alltså klar. `starta` är
idempotent och hittade det tomma passet i stället för att bygga om.

PROJEKTETS EGEN REGEL SÄGER VAD SOM VAR FEL: kasta aldrig bevis du HAR. Att
raden pekar på ett kort som inte finns ÄR upplysningen. `SET NULL` bevarar
den, och först då går giltigheten att HÄRLEDA i stället för att komma ihåg —
vilket spelar roll, för beståndet ändras från fem ställen och två av dem är
kommandoradsverktyg som aldrig ser tjänsten.

TVÅ REGLER, OCH DE DRAR ÅT OLIKA HÅLL:

    ETT PASS ÄR GILTIGT så länge varje rad har ett kort. Saknas ett är passet
    en ruin och byggs om.

    ETT PASS ÄR APPEND-ONLY. Blir mer möjligt — en nivå öppnas, minuterna
    höjs — läggs det till. Blir mindre möjligt tas ingenting bort: det som
    planerats står kvar, och sänkningen syns i morgon.

ALDRIG MOT DEN RIKTIGA DATABASEN — kopia via SQLites backup.

Kör:  python ordbok/verktyg/passprov.py
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


def tjänst(kopia: Path):
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(kopia)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    kort = anslut_kort(kopia, delad_mellan_trådar=True)
    # RENT UTGÅNGSLÄGE. Passen är per dygn, så en kopia av den riktiga
    # databasen bär med sig dagens pass — och provet ska pröva hur ett pass
    # BLIR till, inte hur det ser ut efter Julius förmiddag.
    kort.execute("DELETE FROM Pass")
    kort.commit()
    språk = sqlite3.connect(ROT / "sprak.db", check_same_thread=False)
    språk.row_factory = sqlite3.Row
    return Övningstjänst(kort, språk), kort


def _fr_kurser(kort) -> list:
    """De två kurser som delar målspråk. Utan dem går delningen inte att pröva.

    KONFIGURATIONEN ÄR NUMERA FÖRBJUDEN och skapas därför med ren SQL, förbi
    `ny_kurs`. Det ser ut som fusk och är motsatsen: spärren hindrar NYA
    dubbletter, men databaser i drift har dem redan — Julius hade sv→fr och
    en→fr när spärren skrevs. Delningens beteende måste alltså fortsätta att
    hålla, och ett prov som inte längre kan bygga läget skulle tyst sluta
    vakta det. Att bygga fixturen förbi spärren är att pröva det som finns,
    inte att kringgå en regel.
    """
    delade = kort.execute(
        """SELECT * FROM Kurs WHERE målspråk IN
           (SELECT målspråk FROM Kurs GROUP BY målspråk HAVING COUNT(*) > 1)
           ORDER BY id""").fetchall()
    if delade:
        return delade
    förlaga = kort.execute(
        "SELECT * FROM Kurs WHERE källspråk <> 'en' ORDER BY id LIMIT 1").fetchone()
    if förlaga is None:
        return []
    from datetime import UTC, datetime
    nu = datetime.now(UTC).isoformat()
    kort.execute(
        """INSERT OR IGNORE INTO Kurs (källspråk, målspråk, nivå, cefr, budget,
                                       meningar_per_dag, startad, senast_öppnad)
           VALUES ('en', ?, ?, ?, ?, ?, ?, ?)""",
        (förlaga["målspråk"], förlaga["nivå"], förlaga["cefr"], förlaga["budget"],
         förlaga["meningar_per_dag"], nu, nu))
    kort.commit()
    return kort.execute(
        "SELECT * FROM Kurs WHERE målspråk = ? ORDER BY id",
        (förlaga["målspråk"],)).fetchall()


def prov_nollställning_bygger_om(tj, kort) -> list[str]:
    """En nollställd kurs ska ha en hel dag framför sig, inte noll."""
    fel = []
    for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
        tj.hem(kurs["id"])                     # bygger dagens pass
        tj.nollställ(kurs["id"], "RESET")
        h = tj.hem(kurs["id"])["idag"]
        if h["klar"] or not h["att_göra"]:
            fel.append(f"[{kurs['id']} {kurs['målspråk']}] efter nollställning: "
                       f"att_göra={h['att_göra']} klar={h['klar']}")
    return fel


def prov_grannkursen_överlever(tj, kort) -> list[str]:
    """Nollställs EN kurs får en annan mot samma målspråk inte tömmas.

    Passet hör till kursen, korten till språket. Två kurser mot franska delar
    bestånd, så en nollställning av den ena raderade den andras rader utan att
    någon rört den — och den kursen sa "Done for today" nästa gång den
    öppnades.
    """
    kurser = _fr_kurser(kort)
    if len(kurser) < 2:
        return ["ingen kurs delar målspråk — delningen går inte att pröva"]
    a, b = kurser[0], kurser[1]
    # GRANNEN MÅSTE HA NÅGOT ATT FÖRLORA, annars mäter provet ingenting.
    #
    # Uppsättningen läste tidigare grannens dag som den råkade se ut i den
    # kopierade databasen. Efter att Julius övat klart sin franska en
    # förmiddag stod den på `att_göra = 0, klar = True` REDAN före
    # nollställningen — och då är "blev den tömd?" en fråga utan innehåll.
    # Mätt 2026-08-26: kurs 5 gick 0 → 21, alltså växte av grannens
    # nollställning, och sabotaget kunde inte fällas.
    #
    # Det är samma brist som `prov_upplåsning_utökar` hade: ett prov vars
    # FÖRUTSÄTTNING beror på vilket tillstånd databasen råkar ha är grönt av
    # slump lika ofta som av riktighet. Att nollställa b först ger den en
    # hel dag att förlora.
    tj.nollställ(b["id"], "RESET")
    före = tj.hem(b["id"])["idag"]["att_göra"]
    if not före:
        return [f"kurs {b['id']} har inget att göra ens efter nollställning — "
                f"kontrollen mätte ingenting och kan därför inte falla"]
    tj.nollställ(a["id"], "RESET")
    efter = tj.hem(b["id"])["idag"]
    if efter["klar"] or not efter["att_göra"]:
        return [f"kurs {b['id']} hade {före} att göra, blev "
                f"att_göra={efter['att_göra']} klar={efter['klar']} när "
                f"kurs {a['id']} nollställdes"]
    return []


def prov_upplåsning_utökar(tj, kort) -> list[str]:
    """Låser man upp en nivå ska de nya korten kunna komma in IDAG.

    PROVET VAR STUMT, och det upptäcktes av falsifieringspasset: sabotaget
    som slår av `utöka` helt fällde inte den här kontrollen. Orsaken var
    uppsättningen, inte regeln.

    `nollställ` gav rent rum att utöka i — men den stänger samtidigt dörren
    provet ska gå igenom. `lås_upp` kräver `redo_för_nivå`, och den vilar på
    `byggbarhet`: andelen samplade meningar utan okända ord. En just
    nollställd kurs har noll sedda ord, alltså byggbarhet noll, alltså
    "inte redo" — vilket är RÄTT produktbeteende (F1). Varje kurs föll
    därför ut genom `continue`, ingen kontroll kördes, och provet
    rapporterade grönt utan att ha mätt något.

    Rättat med det en användare faktiskt gör mellan de två stegen: DRILLA
    FÖRST. Dagens glosor besvaras rätt, byggbarheten stiger, och först då
    prövas upplåsningen.

    OCH ETT PROV SOM INTE MÄTTE NÅGOT SÄGER DET. Kunde ingen enda kurs nå
    en upplåsning är kontrollen fortfarande stum, och då är svaret en
    brist och inte ett godkännande — annars är vi tillbaka i samma
    trosbekännelse. Det är projektets egen regel om falsifiering, tillämpad
    på provets uppsättning i stället för på dess påstående.
    """
    fel: list[str] = []
    ostängbara: list[str] = []
    mätta = 0
    for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
        # Ren utgångspunkt: en förbrukad tilldelning har inget rum att
        # utöka i, och då mäter provet ingenting.
        tj.nollställ(kurs["id"], "RESET")
        # DRILLA EN PORTION I TAGET OCH PRÖVA UPPLÅSNINGEN EFTER VAR OCH EN.
        # Att drilla färdigt först och låsa upp sedan mäter fel scenario:
        # japanskan delar ut femtio ord i en enda portion, dagen blir klar
        # på ett varv, och ett AVSLUTAT pass utökas inte (`utöka` returnerar
        # noll på `avslutad`). Regeln gäller en dag som PÅGÅR — "det som är
        # gjort ska stå kvar, det nya ska kunna komma in idag" — så
        # upplåsningen ska ske vid första tillfälle den är möjlig.
        # DAGEN MÅSTE HA RUM UNDER SITT TAK, annars mäter provet fel sak.
        # `utöka` lägger till upp till `tak_nya − väntande_nytt`, och den
        # drill som gör kursen redo att låsa upp fyller samtidigt dagen till
        # taket. Mätt: varje kurs nådde upplåsningen med rummet noll — tyskan
        # på tak 5 med 5 planerade — och 110 nya kort kunde då inte komma in.
        # Det är RÄTT beteende (taket är minutbudgeten, B4), men det gör
        # invarianten omätbar, och ett omätbart prov är inget prov.
        #
        # Minuterna höjs därför före upplåsningen, och `före` fångas EFTER
        # höjningen. Då ligger minuternas verkan redan i utgångsvärdet och
        # tillväxten kan bara komma från upplåsningen.
        tj.sätt_minuter(kurs["id"], 60)
        r = före = None
        for _ in range(8):
            # `före` fångas i SAMMA varv som upplåsningen prövas, annars
            # jämförs dagen mot ett läge en drillportion tillbaka och
            # tillväxten kan komma från drillen i stället för från
            # upplåsningen.
            före = tj.hem(kurs["id"])["idag"]["att_göra"]
            r = tj.lås_upp(kurs["id"])
            if r is not None and r.get("nya_kort"):
                break
            g = tj.glosor(kurs["id"])
            if not g or not g["ord"]:
                break
            for o in g["ord"]:
                tj.glossvar(kurs["id"], o["kort_id"], True)
        if r is None or not r.get("nya_kort"):
            continue                            # nivån gick inte att öppna
        # EN STÄNGD DAG ÄR ETT ANNAT FAKTUM ÄN EN DAG SOM INTE VÄXTE, och
        # provet får inte blanda ihop dem. `utöka` returnerar noll på ett
        # `avslutad` pass, alltså gör en upplåsning efter att dagen tagit
        # slut ingenting — med flit, enligt B5.
        #
        # Japanskan hamnar där varje gång och det är ingen slump: dagen är
        # femtio glosor i EN portion, och det är just den drillen som gör
        # kursen redo att låsa upp. Kursen kan alltså aldrig låsa upp
        # MITT i en dag. Det ger användaren "jag låste upp nivå 2 och
        # ingenting hände", vilket är precis den lögn `utöka` byggdes mot —
        # men att öppna en avslutad dag igen strider mot B5. Frågan är
        # öppen och står i PROBLEM.md; provet DÖLJER den inte men fäller
        # den inte heller som en bugg.
        if not före:
            ostängbara.append(f"{kurs['målspråk']}: dagen var redan klar när "
                              f"upplåsningen blev möjlig ({r['nya_kort']} kort "
                              f"väntar till imorgon)")
            continue
        # DAGEN KAN VARA FULL ÄVEN VID SEXTIO MINUTER. `utöka` har rummet
        # `tak_nya − väntande_nytt`, och står dagen vid sitt tak är rummet
        # noll — då läggs ingenting till, med flit (B4: taket är
        # minutbudgeten, och en upplåsning höjer inte hur lång tid man har).
        #
        # Det blev verklighet när `osedda` fick räkna dagens ord som kända:
        # japanskans dag växte till 179 poster och fyllde taket redan innan
        # upplåsningen. Att kräva tillväxt där vore att kräva att
        # upplåsningen bryter mot taket.
        plan = tj._dagsplan(kurs)
        aktuellt = passlager.nuvarande(kort, kurs["id"])
        väntande_nytt = 0 if aktuellt is None else kort.execute(
            """SELECT COUNT(*) AS n FROM Passkort
               WHERE pass_id = ? AND status = 'väntar'
                 AND roll IN ('ny', 'glosa')""",
            (aktuellt["id"],)).fetchone()["n"]
        if plan.get("tak_nya", plan["nya"]) - väntande_nytt <= 0:
            ostängbara.append(
                f"{kurs['målspråk']}: dagen stod vid sitt tak när upplåsningen "
                f"blev möjlig (tak {plan.get('tak_nya', plan['nya'])}, "
                f"{väntande_nytt} redan planerade)")
            continue
        mätta += 1
        efter = tj.hem(kurs["id"])["idag"]["att_göra"]
        if efter <= före:
            fel.append(f"[{kurs['id']} {kurs['målspråk']}] {r['nya_kort']} nya "
                       f"kort men dagen gick {före} → {efter}")
    if ostängbara:
        print("      (ej mätbara, se docstring: "
              + "; ".join(ostängbara) + ")")
    if not mätta:
        fel.append("ingen kurs nådde en upplåsning MITT i en dag — "
                   "kontrollen mätte ingenting och kan därför inte falla")
    return fel


def prov_minuterna_syns(tj, kort) -> list[str]:
    """Höjer man minuterna ska dagen växa. Sänker man dem ska den INTE krympa.

    Det första är ratten som Julius mätte som verkningslös — den fungerade,
    linjärt, men taket fryses per dygn och ett uttryckligt val räknades som
    en mätning som driver.

    Det andra är append-only-regeln. Att dra tillbaka planerat arbete mitt i
    en dag vore att låta dagen krympa under användaren, alltså precis det
    passlagret byggdes för att få bort.
    """
    fel, prövade, växte = [], 0, 0
    for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
        idag = tj.hem(kurs["id"])["idag"]
        # EN FÄRDIG DAG VÄXER INTE, och ska inte göra det. `tjänst` raderar
        # `Pass` men inte dagens ARBETE — `gjort` räknas ur repetitionerna —
        # så en kurs Julius redan övat på i morse står som klar med noll kvar
        # att göra. Ratten kan inte skapa arbete ur en tom kortlek, och att
        # kräva det gjorde nätet beroende av när på dagen det kördes: kurs 4
        # (fr) föll 2026-08-29 med `gjort 10, klar True, finns 0`.
        if idag["klar"] or idag["finns"] == 0:
            continue
        prövade += 1
        före = idag["att_göra"]
        tj.sätt_minuter(kurs["id"], 600)
        höjt = tj.hem(kurs["id"])["idag"]["att_göra"]
        # DAGEN VÄXER INTE ALLTID AV MER TID, och att kräva det var att mäta
        # fel storhet. `nya_idag` tar `min(i_längden, idag)`, och det är ofta
        # LÅNGTIDSVILLKORET som binder (B4: måltakt 96, tak idag 91, i
        # längden 11). Då är det riktigt att tio timmar inte ger mer arbete —
        # systemet kan inte tillverka repetitioner FSRS inte schemalagt.
        #
        # Provet faller därför tillbaka på det som MÅSTE gälla för varje
        # kurs — dagen får aldrig krympa — och kräver tillväxt bara att den
        # sker för NÅGON kurs. Är knappen frånkopplad växer ingen.
        växte += höjt > före
        tj.sätt_minuter(kurs["id"], 2)
        sänkt = tj.hem(kurs["id"])["idag"]["att_göra"]
        if sänkt < höjt:
            fel.append(f"[{kurs['id']} {kurs['målspråk']}] 60 → 2 min KRYMPTE "
                       f"dagen {höjt} → {sänkt}")
    # UNDANTAGET FÅR INTE ÄTA UPP PROVET. Är varje kurs klar mäter provet
    # ingenting, och skulle rapportera ✓ för att det inte tittat. Då är det
    # ett brott, inte ett godkännande.
    if not prövade:
        fel.append("ingen kurs hade arbete kvar — ratten prövades aldrig")
    elif not växte:
        fel.append(f"ingen av {prövade} kurser växte av 10 → 600 min — "
                   f"ratten är frånkopplad")
    return fel


def prov_passet_är_stabilt(tj, kort) -> list[str]:
    """Att LÄSA dagen får aldrig ändra den.

    `starta` anropas som en bieffekt av `_dagsplan`, alltså vid varje anrop
    som rör dagen. Skapar eller ändrar den passet mer än en gång är hela
    poängen borta — då räknas dagen om igen, bara långsammare.
    """
    fel = []
    for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
        avtryck = None
        for varv in range(6):
            tj.hem(kurs["id"])
            rad = passlager.nuvarande(kort, kurs["id"])
            if rad is None:
                fel.append(f"[{kurs['id']} {kurs['målspråk']}] varv {varv}: "
                           f"inget pass finns efter att dagen lästs")
                break
            nu = (rad["id"], kort.execute(
                "SELECT COUNT(*) AS n FROM Passkort WHERE pass_id = ?",
                (rad["id"],)).fetchone()["n"])
            if avtryck is None:
                avtryck = nu
            elif nu != avtryck:
                fel.append(f"[{kurs['id']} {kurs['målspråk']}] varv {varv}: "
                           f"passet gick från {avtryck} till {nu}")
                break
    return fel


def prov_tomt_pass_fylls(tj, kort) -> list[str]:
    """Ett pass utan rader ska fyllas om dagen har arbete.

    Noll rader är ett GILTIGT svar — inget förfallet, tilldelningen redan
    tagen — men det är också vad som blev kvar efter den gamla kaskaden, och
    de två går inte att skilja på i efterhand. Att fylla löser båda: är dagen
    verkligen tom lägger konstruktionen till noll rader.

    Fallet är inte påhittat. Efter schemarättelsen stod Julius två
    franskkurser på "Done for today" med noll rader i passet medan
    dagsplanen sa 17 nya kort — raderna var hårdraderade INNAN `SET NULL`
    fanns, så det fanns inget bevis kvar för `_ruin` att läsa.
    """
    fel = []
    for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
        # NOLLSTÄLL FÖRST. Kopian bär dagens riktiga läge, och en kurs vars
        # tilldelning redan är förbrukad har en ÄKTA tom dag — då säger
        # provet ingenting om påfyllningen. Uppsättningen hör till provet.
        tj.nollställ(kurs["id"], "RESET")
        tj.hem(kurs["id"])
        rad = passlager.nuvarande(kort, kurs["id"])
        # Töm passet på det sätt den gamla kaskaden gjorde: raderna BORTA,
        # inte satta till NULL. `_ruin` kan då inte se något.
        kort.execute("DELETE FROM Passkort WHERE pass_id = ?", (rad["id"],))
        kort.commit()
        h = tj.hem(kurs["id"])["idag"]
        if h["klar"] or not h["att_göra"]:
            fel.append(f"[{kurs['id']} {kurs['målspråk']}] tomt pass fylldes "
                       f"inte: att_göra={h['att_göra']} klar={h['klar']}")
    return fel


def prov_nollställning_rensar_taket(tj, kort) -> list[str]:
    """En nollställd kurs får inte ärva gårdagens frysta inflödestak.

    Taket fryses per dygn för att brådska inte ska belönas (`dagsplan`), men
    det är ett tal OM EN KORTLEK. Nollställningen raderar kortleken, och ett
    tak från före den beskriver då ingenting som finns kvar.

    JULIUS MÄTTE FÖLJDEN: hans nollställda franskkurs hade rummet 51 kort men
    läste det frysta 7, och genom `nya_ord = int(tak / kort_per_koncept)` blev
    hela första dagens lektion `int(7 / 4,01) = 1`. Ett enda ord, `nous`, och
    sedan var dagen slut.

    Invarianten är på TAKET och inte på antalet ord, därför att antalet beror
    på ordförråd och kort-per-koncept i varje språk. Det som ska gälla är att
    talet räknas om — vad det landar på är en annan fråga.
    """
    fel: list[str] = []
    for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
        # Frys ett tak genom att läsa dagen, och nollställ sedan.
        tj.hem(kurs["id"])
        före = kort.execute("SELECT tak_datum, tak_kort FROM Kurs WHERE id = ?",
                            (kurs["id"],)).fetchone()
        if före["tak_datum"] is None:
            continue                      # kursen har inget tak att ärva
        tj.nollställ(kurs["id"], "RESET")
        efter = kort.execute("SELECT tak_datum, tak_kort FROM Kurs WHERE id = ?",
                             (kurs["id"],)).fetchone()
        if efter["tak_datum"] is not None:
            fel.append(f"[{kurs['id']} {kurs['målspråk']}] taket {efter['tak_kort']} "
                       f"från {efter['tak_datum']} överlevde nollställningen")
    return fel


def prov_medföljande_kort(tj, kort) -> list[str]:
    """Ett kort utanför dagens plan är gratis när det går rätt och ditt när
    det går fel.

    En mening måste kunna byggas på nivån, och drar då in kort ingen
    planerat (E4). Julius 2026-08-29: *"De nyinförda korten som egentligen
    inte tillhör passet ska inte läggas till i due eller new. De är osynliga
    hittills. Ifall vi klarar de så förs den datan in… Ifall de failar så
    borde due date flyttas till idag."*

    Regeln är alltså ASYMMETRISK, och båda halvorna prövas här:

        rätt   ingen rad läggs till, inga tal rör sig
        fel    en `igen`-rad läggs till, `igen` växer med ett

    Att bara pröva den ena halvan vore stumt åt fel håll: ett bygge som
    aldrig köar något klarar rätt-fallet, och ett som köar allting klarar
    fel-fallet.
    """
    fel = []
    for kurs in kort.execute("SELECT * FROM Kurs ORDER BY id"):
        tj.hem(kurs["id"])
        rad = passlager.nuvarande(kort, kurs["id"])
        if rad is None:
            continue
        i_passet = {r["kort_id"] for r in kort.execute(
            "SELECT kort_id FROM Passkort WHERE pass_id = ?", (rad["id"],))}
        utanför = [r["id"] for r in kort.execute(
            "SELECT id FROM Kort WHERE språk = ? LIMIT 400", (kurs["målspråk"],))
            if r["id"] not in i_passet][:2]
        if len(utanför) < 2:
            continue

        före = passlager.läget(kort, rad["id"])
        passlager.registrera(kort, rad["id"], {utanför[0]: True})
        efter = passlager.läget(kort, rad["id"])
        for nyckel in ("nya", "förfallna", "igen", "att_göra"):
            if efter[nyckel] != före[nyckel]:
                fel.append(f"[{kurs['id']} {kurs['målspråk']}] ett RÄTT "
                           f"medföljande kort ändrade {nyckel}: "
                           f"{före[nyckel]} → {efter[nyckel]}")

        passlager.registrera(kort, rad["id"], {utanför[1]: False})
        sist = passlager.läget(kort, rad["id"])
        if sist["igen"] != efter["igen"] + 1:
            fel.append(f"[{kurs['id']} {kurs['målspråk']}] ett FELAKTIGT "
                       f"medföljande kort gav igen {efter['igen']} → "
                       f"{sist['igen']}, väntat {efter['igen'] + 1}")
    return fel


PROV = [("nollställning bygger om passet", prov_nollställning_bygger_om),
        ("nollställning rensar dagens tak", prov_nollställning_rensar_taket),
        ("ett tomt pass fylls", prov_tomt_pass_fylls),
        ("grannkursen överlever en nollställning", prov_grannkursen_överlever),
        ("upplåsning utökar dagen", prov_upplåsning_utökar),
        ("minuterna syns, men krymper inte dagen", prov_minuterna_syns),
        ("att läsa dagen ändrar den inte", prov_passet_är_stabilt),
        ("medföljande kort: gratis rätt, ditt vid fel",
         prov_medföljande_kort)]


# ── falsifiering ────────────────────────────────────────────────────

def _sabotage_köa_aldrig():
    """Före Julius beslut 2026-08-27: ett kort utanför planen köades aldrig,
    inte ens när det fallerade."""
    orig = passlager._ska_tas_igen
    passlager._ska_tas_igen = lambda rätt: False
    return lambda: setattr(passlager, "_ska_tas_igen", orig)


def _sabotage_köa_allt():
    """Motsatsen: köa varje medföljande kort, även de som gick rätt. Då blir
    dagen aldrig klar — varje mening drar in kort den inte valdes för."""
    orig = passlager._ska_tas_igen
    passlager._ska_tas_igen = lambda rätt: True
    return lambda: setattr(passlager, "_ska_tas_igen", orig)


def _sabotage_ovillkorlig_idempotens():
    """Före rättelsen: `starta` gav tillbaka passet utan att pröva det."""
    orig = passlager._ruin
    passlager._ruin = lambda kort_db, pass_id: False
    return lambda: setattr(passlager, "_ruin", orig)


def _sabotage_utan_påfyllning():
    """Före rättelsen: ett tomt pass lämnades tomt."""
    orig = passlager._antal_rader
    passlager._antal_rader = lambda kort_db, pass_id: 1
    return lambda: setattr(passlager, "_antal_rader", orig)


def _sabotage_utan_utökning():
    """Före rättelsen: passet var oföränderligt när det väl byggts."""
    orig = passlager.utöka
    passlager.utöka = lambda *a, **kw: 0
    return lambda: setattr(passlager, "utöka", orig)


def _sabotage_bygg_om_alltid():
    """Motsatsen: bygg om passet vid varje anrop, alltså det gamla lagret."""
    orig = passlager.nuvarande
    passlager.nuvarande = lambda *a, **kw: None
    return lambda: setattr(passlager, "nuvarande", orig)


def _sabotage_behåll_taket():
    """Före rättelsen: `nollställ` lämnade dagens frysta tak orört.

    Sabotaget återställer taket EFTER nollställningen i stället för att hindra
    raderingen — `sqlite3.Connection` går inte att patcha, och utfallet är
    detsamma: kursen står med ett tak som beskriver en kortlek som är borta.
    """
    orig = Övningstjänst.nollställ
    def behåll(self, kurs_id, bekräftelse):
        rad = self.kort_db.execute(
            "SELECT målspråk, tak_datum, tak_kort FROM Kurs WHERE id = ?",
            (kurs_id,)).fetchone()
        svar = orig(self, kurs_id, bekräftelse)
        if svar is not None and rad is not None:
            self.kort_db.execute(
                "UPDATE Kurs SET tak_datum = ?, tak_kort = ? WHERE målspråk = ?",
                (rad["tak_datum"], rad["tak_kort"], rad["målspråk"]))
            self.kort_db.commit()
        return svar
    Övningstjänst.nollställ = behåll
    return lambda: setattr(Övningstjänst, "nollställ", orig)


SABOTAGE = [(_sabotage_ovillkorlig_idempotens, 0),
            (_sabotage_behåll_taket, 1),
            (_sabotage_utan_påfyllning, 2),
            (_sabotage_ovillkorlig_idempotens, 3),
            (_sabotage_utan_utökning, 4),
            (_sabotage_utan_utökning, 5),
            (_sabotage_bygg_om_alltid, 6),
            # BÅDA HALVORNA AV DEN ASYMMETRISKA REGELN. Ett
            # sabotage som aldrig köar fälls av fel-fallet, ett
            # som alltid köar av rätt-fallet.
            (_sabotage_köa_aldrig, 7),
            (_sabotage_köa_allt, 7)]


def main() -> int:
    fel = stumma = 0
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        print(f"{len(PROV)} invarianter över passets livscykel\n")
        for nr, (namn, kör) in enumerate(PROV):
            tj, kort = tjänst(d / f"liv{nr}.db")
            brister = kör(tj, kort)
            kort.close()
            fel += len(brister)
            print(f"  {'✗' if brister else '✓'} {namn}")
            for b in brister[:4]:
                print(f"      {b}")

        print("\nfalsifiering — varje gammalt läge ska fälla sitt prov:")
        for nr, (sab, mål) in enumerate(SABOTAGE):
            ångra = sab()
            try:
                tj, kort = tjänst(d / f"sab{nr}.db")
                brister = PROV[mål][1](tj, kort)
                kort.close()
            finally:
                ångra()
            if not brister:
                stumma += 1
            print(f"  {'✓ föll' if brister else '✗ STUMT'}  "
                  f"{sab.__doc__.splitlines()[0][:56]}  → {PROV[mål][0]}")
    print(f"\n{len(PROV)} invarianter, {fel} brott." if fel
          else f"\n{len(PROV)} invarianter, alla håller.")
    if stumma:
        print(f"{stumma} sabotage fällde inte sitt prov.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
