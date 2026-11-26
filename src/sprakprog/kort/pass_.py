"""Passet som ett objekt — vad dagen INNEHÅLLER, bestämt en gång.

DAGSPLANEN ÄR POLITIK, PASSET ÄR TILLSTÅND, och att blanda ihop dem var
grundfelet. `dagsplan` räknar ut hur mycket som FÅR göras — takten, taket,
tiden — och den ska räknas om vid varje anrop, för den är en styrning (B2)
som korrigerar sig själv varje dygn. Men VAD dagen innehåller är ett faktum,
och ett faktum ska bestämmas en gång och sedan stå kvar.

Före den här modulen fanns inget objekt som var "dagens pass". Det fanns en
databas som frågades om och om igen, plus åtta lexikon i minnet på
Övningstjänst som råkade hänga ihop. Ingenting tvingade dem att vara överens,
och varenda bugg i passet under vecka 34 var två av dem som inte var det:

    passet avslutades oväntat      innehållet räknades om vid varje anrop och
                                   kunde krympa under användaren
    siffrorna följde inte passet   de beskrev databasen, inte passet
    "7 new" på en klar dag         talen hämtades ett anrop före meddelandet
    onåbara kort malde i evighet   ingen kunde skriva ner att de var onåbara

Efter den här modulen är varje tal på skärmen en RÄKNING i `Passkort` och
inte en härledning: `att_göra` är rader som väntar, `klar` är att inga gör
det. `klar` blir ett faktum i stället för en slutsats, och det finns inget
andra ställe som kan komma fram till något annat.

VAD MODULEN INTE GÖR. Den bestämmer inte hur mycket som ska in — det gör
`dagsplan`, och passet tar emot dess svar som ett tal. Den betygsätter inte —
det gör `Schemaläggare.registrera_mening`. Den bygger inga meningar. Den vet
bara vilka kort dagen består av och hur långt man kommit.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from .schemalaggning import (
    Schemaläggare, _kort_per_koncept, dygnets_början,
)

#: Hur många gånger urvalet får växla mellan ord och böjning. Varje varv
#: förbrukar av samma tak, så loopen tar slut av sig själv — talet är en
#: SPÄRR mot att en bugg ska snurra, inte en inställning.
VÄXELVARV = 6

#: Rollerna, i den ordning de ska mötas. Drillen först — ett ordkort är en
#: glosa och går inte att svara på ur en mening man inte kan läsa (C2/D3) —
#: och sedan allt som hör hemma i en mening. Ordningen skrivs EN gång här i
#: stället för att härledas på nytt vid varje anrop.
ROLLORDNING = ("glosa", "igen", "förfallen", "ny")


def _lokalt_datum(nu: datetime | None = None) -> str:
    """Dygnet som `dygnets_början` räknar med, som YYYY-MM-DD.

    LOKAL midnatt och inte UTC, av samma skäl som `dygnets_början`: UTC-
    midnatt är 02:00 i Sverige, så ett pass klockan 00:30 skulle höra till
    gårdagen. Gränsen måste vara densamma i båda, annars kan ett pass finnas
    för ett dygn dagsplanen räknar som ett annat.
    """
    return (nu or datetime.now(UTC)).astimezone().date().isoformat()


def nuvarande(kort_db: sqlite3.Connection, kurs_id: int, *,
              läge: str = "dagens", nu: datetime | None = None):
    """Dagens pass för kursen, eller None om inget startats."""
    return kort_db.execute(
        "SELECT * FROM Pass WHERE kurs_id = ? AND datum = ? AND läge = ?",
        (kurs_id, _lokalt_datum(nu), läge)).fetchone()


def starta(kort_db: sqlite3.Connection, kurs: sqlite3.Row, plan: dict, *,
           läge: str = "dagens", nu: datetime | None = None,
           nåbara=None) -> sqlite3.Row:
    """Bestäm dagens innehåll EN gång och skriv ner det.

    `plan` är `dagsplan`s svar: därifrån kommer bara TALEN — hur många nya
    kort och hur många av dem som ska vara ord. Vilka kort det blir avgörs
    här, ur samma köer som förut.

    IDEMPOTENT MEN INTE OVILLKORLIG. Finns passet redan returneras det —
    två flikar, en omladdning eller ett dubbelklick ska inte kunna ge
    användaren två olika dagar. Men ett pass som byggdes ur ett kortbestånd
    som inte längre finns är inte samma dag, det är en ruin, och att lämna
    tillbaka den var precis det fel idempotensen skulle skydda mot.

    Mätt: en nollställd kurs sa "Done for today" utan att användaren gjort
    något. Korten raderades, passets rader förlorade sina kort, noll rader
    kvar betyder "inget väntar" — och `starta` hittade det tomma passet och
    byggde aldrig om. Samma sak drabbade en ANNAN kurs mot samma målspråk,
    som ingen rört: passet hör till kursen, korten till språket.

    GILTIGHETEN ÄR HÄRLEDD OCH INTE IHÅGKOMMEN, och det är skälet att den
    håller. Regeln läser data — har någon rad förlorat sitt kort? — i stället
    för att förlita sig på att varje väg som rör beståndet minns att anropa
    något. Och vägarna är fler än man tror: webbgränssnittets nollställning,
    `ordbok kurs`, `ordbok kort`, upplåsningen av en nivå.
    """
    finns = nuvarande(kort_db, kurs["id"], läge=läge, nu=nu)
    if finns is not None and not _ruin(kort_db, finns["id"]):
        # ETT TOMT PASS FYLLS, det byggs inte om. Noll rader är ett giltigt
        # svar — inget förfallet, tilldelningen redan tagen — men det är
        # ocksåvad som blir kvar efter en gammal kaskadradering, och de två
        # går inte att skilja på i efterhand. Att FYLLA löser båda: är dagen
        # verkligen tom lägger konstruktionen till noll rader och passet står
        # oförändrat, id och allt.
        #
        # Att i stället kasta och bygga om vore att byta identitet på passet
        # vid varje läsning av en tom dag, alltså återinföra precis den
        # instabilitet lagret finns för att ta bort.
        if not _antal_rader(kort_db, finns["id"]):
            _lägg_in(kort_db, finns["id"],
                     _rader(kort_db, kurs, plan, läge, nu, nåbara))
        # STÄDNINGEN KÖRS VID VARJE LÄSNING och inte bara när passet byggs:
        # rader blir bedömda under dagens gång, av glosläget och av andra
        # meningar, och passet ska följa med. Den är billig och idempotent.
        _stäng_redan_bedömda(kort_db, finns["id"], nu)
        _kanske_avsluta(kort_db, finns["id"], nu or datetime.now(UTC))
        kort_db.commit()
        return kort_db.execute(
            "SELECT * FROM Pass WHERE id = ?", (finns["id"],)).fetchone()
    if finns is not None:
        # RUINEN KASTAS, inte lappas. Ett halvt pass ur ett halvt bestånd är
        # inte en dag någon kan lita på, och kortet som saknas kan ha varit
        # det enda som återstod.
        kort_db.execute("DELETE FROM Pass WHERE id = ?", (finns["id"],))
        kort_db.commit()

    nu = nu or datetime.now(UTC)
    kort_db.execute(
        "INSERT INTO Pass (kurs_id, datum, läge, startad) VALUES (?, ?, ?, ?)",
        (kurs["id"], _lokalt_datum(nu), läge, nu.isoformat()))
    pass_id = kort_db.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    _lägg_in(kort_db, pass_id, _rader(kort_db, kurs, plan, läge, nu, nåbara))
    _stäng_redan_bedömda(kort_db, pass_id, nu)
    _kanske_avsluta(kort_db, pass_id, nu)
    kort_db.commit()
    return kort_db.execute("SELECT * FROM Pass WHERE id = ?", (pass_id,)).fetchone()


def _stäng_redan_bedömda(kort_db: sqlite3.Connection, pass_id: int,
                         nu: datetime | None = None) -> int:
    """Rader vars kort redan bedömts idag är GJORDA, inte väntande.

    JULIUS MÄTTE FÖLJDEN: *"en övning som jag gjorde helt korrekt flyttade
    inga kort. Det var exakt lika många i due, again och new."* Meningen
    `Il existe.` rörde sju kort och alla sju var redan bedömda tidigare samma
    dag, så bedömningen blev en nolloperation. Spåret visade det direkt.

    Orsaken låg inte i rättningen utan HÄR: fyra av passets tio väntande
    rader var kort som redan hade en dom idag. Passet räknade dem som arbete,
    `att_göra` visade dem, och generatorn byggde meningar för att täcka dem —
    men E2 hoppar över dem vid bokföringen, med rätta. Två delar av systemet
    hade olika åsikt om vad som återstod.

    *"Övningar ska endast ta fram ett kort som behöver tränas. Annars är
    övningen meningslös."*

    REGELN ÄR EXAKT E2:S, inte en egen. Ett kort med en dom idag är klart för
    dagen — en upprepad rätt ger FSRS-faktor 1,0 och gör bokstavligen
    ingenting. Ett kort som FÄLLTS idag står kvar: det ska tas igen, och det
    är hela poängen med `igen`-rollen (B7). Skulle de två reglerna gå isär är
    det den här funktionen som är fel, inte E2.
    """
    rader = kort_db.execute(
        """SELECT DISTINCT pk.id, pk.kort_id FROM Passkort pk
           WHERE pk.pass_id = ? AND pk.status = 'väntar'
             AND pk.kort_id IS NOT NULL""", (pass_id,)).fetchall()
    if not rader:
        return 0
    ider = [r["kort_id"] for r in rader]
    platser = ",".join("?" * len(ider))
    domar = kort_db.execute(
        f"""SELECT kort_id, betyg FROM Repetition
            WHERE kort_id IN ({platser}) AND tidpunkt >= ?""",
        (*ider, dygnets_början(nu))).fetchall()
    graderade = {d["kort_id"] for d in domar}
    fällda = {d["kort_id"] for d in domar if d["betyg"] == 1}
    klara = [r["id"] for r in rader
             if r["kort_id"] in graderade and r["kort_id"] not in fällda]
    if not klara:
        return 0
    tid = (nu or datetime.now(UTC)).isoformat()
    kort_db.execute(
        f"""UPDATE Passkort SET status = 'rätt', tidpunkt = ?
            WHERE id IN ({",".join("?" * len(klara))})""", (tid, *klara))
    return len(klara)


def behöver_fyllas(kort_db: sqlite3.Connection, pass_id: int) -> bool:
    """Ska passet byggas eller fyllas? Anroparen behöver veta INNAN.

    Nåbarhetsmätningen kostar några hundra renderingar, så den ska bara göras
    när den behövs. Frågan är alltså inte "är passet giltigt" utan "kommer
    `starta` att skriva några rader" — och det är sant i två fall: passet är
    en ruin, eller det är tomt.
    """
    return _ruin(kort_db, pass_id) or not _antal_rader(kort_db, pass_id)


def _antal_rader(kort_db: sqlite3.Connection, pass_id: int) -> int:
    return kort_db.execute(
        "SELECT COUNT(*) AS n FROM Passkort WHERE pass_id = ?",
        (pass_id,)).fetchone()["n"]


def _lägg_in(kort_db: sqlite3.Connection, pass_id: int,
             rader: list[tuple[int, str]]) -> None:
    kort_db.executemany(
        "INSERT INTO Passkort (pass_id, kort_id, roll, ordning) VALUES (?,?,?,?)",
        [(pass_id, kid, roll, n) for n, (kid, roll) in enumerate(rader)])


def _rader(kort_db: sqlite3.Connection, kurs: sqlite3.Row, plan: dict,
           läge: str, nu: datetime,
           nåbara=None) -> list[tuple[int, str]]:
    """Vilka kort dagen består av. Konstruktionen, skild från skrivningen.

    `nåbara` är en FUNKTION och inte en mängd, och det är inte en detalj.
    Den tar de koncept som tillkommer genom dagens drill och svarar med de
    kort en mening då kan röra (`Generator.nåbara_kort`). Ordningen måste
    vara den: orden väljs FÖRST, och nåbarheten mäts med dem inräknade.

    Mäter man före drillen är svaret vid kallstart noll — inget ord är sett,
    ingen mening går att bygga, hela tilldelningen går till ord och dagen
    blir sju glosor och NOLL meningar. Mätt precis så.

    NYA böjningskort silas genom svaret. Ett kort som ingen byggbar mening
    rör hör inte hemma i dagen, hur högt rankat det än är.

    GLOSOR SILAS INTE. De möts i drillen och inte i en mening, så nåbarheten
    säger ingenting om dem. FÖRFALLNA silas inte heller: de SKA göras, hur
    svåra de än är att nå (B5), och når man dem inte finns nödutgången (B8).
    """
    språk = kurs["målspråk"]
    s = Schemaläggare(kort_db)
    rader: list[tuple[int, str]] = []

    if läge == "dagens":
        # GLOSORNA FÖRST. `nya_ord` är ordens andel av dagens tilldelning —
        # drillen och meningarna drar ur samma pott (se `dagsplan`).
        # ORD OCH BÖJNING VÄXELVIS, tills taket är fyllt eller inget mer
        # går att nå. Ett enda varv räcker inte, och de två sätten att göra
        # fel är varandras motsatser:
        #
        #   mät nåbarheten FÖRE drillen  →  vid kallstart är svaret noll,
        #                                   allt går till ord, dagen får
        #                                   sju glosor och NOLL meningar
        #   ge resten till ord rakt av   →  ett ord drar med sig 4,01 kort,
        #                                   och en dag med tak 17 införde 56
        #
        # Varvet gör i stället det enda som stämmer: välj de ord dagen ska
        # ge, mät vad de gör nåbart, ta de böjningskorten, och är taket inte
        # fyllt — köp fler ord för det som är kvar, till MÄTT växelkurs, och
        # mät om. Loopen kan inte skena: varje varv förbrukar av samma tak.
        per_koncept = max(1.0, _kort_per_koncept(kort_db, språk))
        tak = max(0, plan["nya"])
        valda_ord: list = []
        valda_kort: list = []
        önskat_ord = max(0, plan["nya_ord"])
        for _ in range(VÄXELVARV):
            glosor = [r for r in s.oglosade(språk, önskat_ord)
                      if r["id"] not in {x["id"] for x in valda_ord}]
            valda_ord += glosor
            kvar = tak - len(valda_ord) - len(valda_kort)
            if kvar <= 0:
                break
            möjliga_kort = (nåbara({r["koncept"] for r in valda_ord
                                    if r["koncept"]})
                            if nåbara is not None else None)
            i_dagen = {x["id"] for x in valda_ord} | {x["id"] for x in valda_kort}
            # DAGENS ORD RÄKNAS SOM KÄNDA, precis som i `nåbara`. Utan det
            # sa loopens två halvor emot varandra: nåbarheten räknade dagens
            # ord som kända och svarade femton, medan `osedda` krävde att de
            # redan var sedda och lämnade tre. Passet planerade tre kort och
            # meningarna införde sju.
            dagens = {r["koncept"] for r in valda_ord if r["koncept"]}
            nya_kort = [r for r in s.osedda(språk, kvar * 6, uteslut=("ord",),
                                            plus=dagens)
                        if r["id"] not in i_dagen
                        and (möjliga_kort is None or r["id"] in möjliga_kort)]
            valda_kort += nya_kort[:kvar]
            rest = tak - len(valda_ord) - len(valda_kort)
            # ETT VARV SOM INTE LÅSER UPP NÅGOT KÖPER INGENTING, och då ska
            # loopen sluta köpa ord.
            #
            # Villkoret var `not glosor and not nya_kort`, alltså "bryt bara
            # om BÅDA är tomma". Men det finns nästan alltid ett ord till att
            # ta, så `glosor` är sällan tom — och loopen fortsatte köpa ord
            # långt efter att de slutat låsa upp böjningskort. Mätt på en
            # färsk franskkurs med taket 25:
            #
            #     varv 0   6 ord  →  7 böjningskort
            #     varv 1   8 ord  →  2
            #     varv 2   9 ord  →  0      ← härifrån är varje varv rent
            #     varv 3  10 ord  →  0        slöseri: ett ord till, noll kort
            #     varv 4  11 ord  →  0
            #     varv 5  12 ord  →  0
            #
            # Dagen fick 12 ord där modellen räknat fram 6. De sex extra
            # låste inte upp något; de fanns bara för att fylla ett tak.
            #
            # OCH DET ÄR PRECIS VAD B8 MÄTTE OCH FÖRKASTADE: "Taket är ett
            # tak, inte en kvot. Frestelsen var att lägga den outnyttjade
            # delen på fler ORD, så att minuterna fylls. Det mättes och
            # förkastades." Passlagret byggdes efteråt och återinförde
            # beteendet på ett annat ställe — samma fel, ny plats.
            #
            # Vid kallstart är ordförrådet för tunt för att bära sin egen
            # tilldelning, och det botas av att morgondagen kommer.
            if rest <= 0 or not nya_kort:
                break
            # Resten av taket köper ord, till mätt växelkurs.
            önskat_ord = len(valda_ord) + max(1, int(rest / per_koncept))
        for r in valda_ord:
            rader.append((r["id"], "glosa"))
        for r in valda_kort:
            rader.append((r["id"], "ny"))
        # FÖRFALLNA UTAN TAK. B5: ett tak på arbetsmängden motsäger FSRS,
        # som bygger på att rätt kort repeteras i tid.
        for r in s.förfallna(språk, 10_000, nu):
            rader.append((r["id"], "förfallen"))
    else:
        # EXTRAPASSET har en egen kö: kort som ännu inte förfallit, det som
        # förfaller först först (B6). Inget nytt material — extraövning ska
        # inte kunna öka morgondagens arbete.
        for r in s.kommande(språk, max(0, plan["tidiga"]), nu):
            rader.append((r["id"], "förfallen"))

    rader.sort(key=lambda x: ROLLORDNING.index(x[1]))
    return rader


def _ruin(kort_db: sqlite3.Connection, pass_id: int) -> bool:
    """Har passet förlorat kort? Då byggdes det ur ett bestånd som är borta.

    `Passkort.kort_id` blir NULL när kortet raderas (`ON DELETE SET NULL`) i
    stället för att raden försvinner. Det är därför frågan går att ställa
    över huvud taget — med `CASCADE` fanns inget spår kvar att läsa.
    """
    return bool(kort_db.execute(
        "SELECT 1 FROM Passkort WHERE pass_id = ? AND kort_id IS NULL LIMIT 1",
        (pass_id,)).fetchone())


def utöka(kort_db: sqlite3.Connection, kurs: sqlite3.Row, plan: dict, *,
          nu: datetime | None = None) -> int:
    """Lägg till kort som blivit MÖJLIGA sedan passet byggdes.

    Ett pass är inte oföränderligt — det är APPEND-ONLY. Skillnaden är
    avgörande. Att låsa dagen helt gav två fel som Julius mätte i bruk:
    låser man upp en nivå händer ingenting förrän imorgon, och ändrar man
    minuterna gör det inte heller det. Båda är uttryckliga val, och ett val
    som inte syns är samma sorts lögn som ett tal som inte stämmer.

    Att i stället bygga OM passet vore fel åt andra hållet: det som redan är
    gjort ska stå kvar, och det som redan är avskrivet som onåbart ska inte
    prövas igen samma dag. Därför läggs bara till.

    UTRYMMET ÄR VAD SOM ÅTERSTÅR AV DAGENS TAK, och taket heter `tak_nya`
    och inte `nya`. Skillnaden är hela poängen med uppdelningen: `nya` är vad
    PASSET har kvar, `tak_nya` är vad PLANEN tillåter. Läser man fel av dem
    blir rummet alltid noll — passets kvarvarande minus passets kvarvarande —
    och utökningen gör tyst ingenting. Det var precis vad som hände första
    gången den kopplades in.

    Passets väntande nya rader ligger inne i takets tal, eftersom de ännu
    inte är införda, och dras därför av. Utan avdraget skulle varje anrop
    lägga till en omgång till.

    KRYMPER TAKET TAS INGENTING BORT. Sänker användaren minuterna är rummet
    negativt och utökningen gör ingenting — passet är append-only, och det
    som redan planerats står kvar. Sänkningen syns i morgon. Att dra tillbaka
    arbete mitt i en dag vore att låta dagen krympa under användaren, alltså
    exakt det beteende hela passlagret byggdes för att få bort.
    """
    rad = nuvarande(kort_db, kurs["id"], nu=nu)
    if rad is None or rad["avslutad"]:
        return 0
    väntande_nytt = kort_db.execute(
        """SELECT COUNT(*) AS n FROM Passkort
           WHERE pass_id = ? AND status = 'väntar' AND roll IN ('ny', 'glosa')""",
        (rad["id"],)).fetchone()["n"]
    rum = max(0, plan.get("tak_nya", plan["nya"]) - väntande_nytt)
    if not rum:
        return 0
    i_passet = {r["kort_id"] for r in kort_db.execute(
        "SELECT kort_id FROM Passkort WHERE pass_id = ?", (rad["id"],))}
    s = Schemaläggare(kort_db)
    nästa = kort_db.execute(
        "SELECT COALESCE(MAX(ordning), 0) + 1 AS n FROM Passkort WHERE pass_id = ?",
        (rad["id"],)).fetchone()["n"]
    nya: list[tuple] = []
    for r in s.oglosade(kurs["målspråk"], max(0, plan["nya_ord"])):
        if r["id"] not in i_passet and len(nya) < rum:
            nya.append((rad["id"], r["id"], "glosa", nästa + len(nya)))
    for r in s.osedda(kurs["målspråk"], rum, uteslut=("ord",)):
        if r["id"] not in i_passet and len(nya) < rum:
            nya.append((rad["id"], r["id"], "ny", nästa + len(nya)))
    if not nya:
        return 0
    kort_db.executemany(
        "INSERT INTO Passkort (pass_id, kort_id, roll, ordning) VALUES (?,?,?,?)",
        nya)
    _kanske_avsluta(kort_db, rad["id"], nu)
    kort_db.commit()
    return len(nya)


def läget(kort_db: sqlite3.Connection, pass_id: int) -> dict:
    """Passets tal — RÄKNADE, inte härledda.

    Det här är den enda platsen som svarar på "hur långt har vi kommit", och
    det är hela vinsten med tabellen. Förut fanns svaret på tre ställen —
    `dagsplan`, generatorns passkö och sidans egna räknare — och de kunde
    säga olika saker utan att något larmade.
    """
    # `kort_id IS NOT NULL`: en rad vars kort är borta är inte arbete. Den
    # står kvar som BEVIS för att passet byggdes ur ett bestånd som inte
    # finns (se `_ruin`), men den kan inte göras och ska inte räknas. Utan
    # villkoret hade ett förlorat pass sett fullt av arbete ut ända tills
    # någon försökte hämta en uppgift ur det.
    per: dict[str, int] = {}
    for r in kort_db.execute(
            """SELECT roll, status, COUNT(*) AS n FROM Passkort
               WHERE pass_id = ? AND kort_id IS NOT NULL
               GROUP BY roll, status""", (pass_id,)):
        per[f"{r['roll']}:{r['status']}"] = r["n"]

    def antal(roll: str | None = None, status: str | None = None) -> int:
        return sum(n for k, n in per.items()
                   if (roll is None or k.split(":")[0] == roll)
                   and (status is None or k.split(":")[1] == status))

    väntar = antal(status="väntar")
    return {
        "pass_id": pass_id,
        "att_göra": väntar,
        "glosor": antal("glosa", "väntar"),
        "förfallna": antal("förfallen", "väntar"),
        "nya": antal("ny", "väntar"),
        "igen": antal("igen", "väntar"),
        "gjorda": antal(status="rätt") + antal(status="fel"),
        "onåbara": antal(status="onåbar"),
        "klar": väntar == 0,
        # UPPDELNINGEN SOM EN LISTA, i den ordning korten möts.
        #
        # DEN FINNS FÖR ATT GRÄNSSNITTET INTE SKA RÄKNA. Sidan härledde
        # tidigare sin egen uppdelning i JS — `former = max(0, nya − glosor)`
        # — och det var fel: `nya` och `glosor` är OLIKA roller i `Passkort`
        # och överlappar aldrig, så subtraktionen drog bort ett tal som inte
        # ingick. Mätt 2026-08-26 på fem kurser:
        #
        #     kurs 1  rubriken 57 kort, raden summerade till 52
        #     kurs 2  rubriken 48, raden 45, knappen under den 5
        #     kurs 3  rubriken 50, knappen "0 due · 0 new"
        #
        # Subtraktionen var en kvarleva från när `nya` innehöll ordkorten.
        # Inget prov fångade den, och det är hela poängen: näten prövar
        # API:t, och ingenting prövade vad SIDAN räknade fram ur det.
        #
        # Rollerna är disjunkta och summerar per konstruktion till `väntar`,
        # eftersom `antal(status="väntar")` går över exakt de fyra. Att lämna
        # ut listan i stället för fyra lösa tal gör summan till ett faktum
        # gränssnittet ärver i stället för ett det räknar om.
        #
        # NYCKELN OCH INTE TEXTEN. All gränssnittstext bor i `T` i sida.html,
        # så att ett andra programspråk är en kolumn där och ingenting här.
        "delar": [{"nyckel": nyckel, "antal": antal(roll, "väntar")}
                  for roll, nyckel in (("glosa", "glosor"),
                                       ("igen", "igen"),
                                       ("förfallen", "förfallna"),
                                       ("ny", "nya"))
                  if antal(roll, "väntar")],
    }


def väntande(kort_db: sqlite3.Connection, pass_id: int,
             roll: str | None = None) -> list[sqlite3.Row]:
    """Kort som ännu inte mötts, i passets egen ordning."""
    villkor = " AND p.roll = ?" if roll else ""
    p = (pass_id, roll) if roll else (pass_id,)
    return kort_db.execute(
        f"""SELECT k.*, p.id AS passkort_id, p.roll FROM Passkort p
            JOIN Kort k ON k.id = p.kort_id
            WHERE p.pass_id = ? AND p.status = 'väntar'{villkor}
            ORDER BY p.ordning, p.id""", p).fetchall()


def väntande_ider(kort_db: sqlite3.Connection, pass_id: int,
                  roll: str | None = None) -> set[int]:
    """Kort-id:n som väntar. Generatorn behöver mängden, inte raderna."""
    return {r["id"] for r in väntande(kort_db, pass_id, roll)}


def _syskonpass(kort_db: sqlite3.Connection, pass_id: int) -> list[int]:
    """Dagens öppna pass för SAMMA MÅLSPRÅK, inklusive det egna.

    KORTEN ÄR PER SPRÅK, PASSEN PER KURS. Två kurser mot franska delar
    kortbestånd: introduceras `tu` i den ena är det infört också för den
    andra, och FSRS vägrar dessutom ett andra betyg samma dygn (E2). En rad
    som väntar på ett kort som redan mötts kan därför aldrig bli gjord, och
    dagen tog aldrig slut — mätt: kurs 5 stod på `att_göra = 17` genom
    hundra varv medan bara 13 kort fanns kvar att göra.

    Att låta händelsen "kortet mötte användaren" verka i alla dagens pass för
    språket är inte en genväg utan den sanna beskrivningen: mötet skedde, och
    vilken kurs som råkade vara öppen är en egenskap hos gränssnittet.
    """
    return [r["id"] for r in kort_db.execute(
        """SELECT p2.id FROM Pass p
           JOIN Kurs k  ON k.id  = p.kurs_id
           JOIN Kurs k2 ON k2.målspråk = k.målspråk
           JOIN Pass p2 ON p2.kurs_id = k2.id AND p2.datum = p.datum
                       AND p2.läge = p.läge
           WHERE p.id = ?""", (pass_id,))]


def _hör_till_passet(kort_db: sqlite3.Connection, pass_id: int,
                     kort_id: int) -> bool:
    """Står kortet i dagens plan över huvud taget — i vilken status som helst?

    Skiljer TVÅ fall som båda saknar en väntande rad, och som ska behandlas
    olika när kortet fallerar:

        avklarat idag    raden finns med status `rätt`. Felet är då en verklig
                         försämring av något dagen redan bokfört, och ska
                         tillbaka som `igen`.

        aldrig planerat  kortet stod inte i dagen. Det råkade vara med i en
                         mening som valdes för något annat (E4). Mötet
                         betygsätts, men dagen ska inte växa av det — annars
                         kan ett pass aldrig ta slut, eftersom varje mening
                         drar in kort som inte var planerade.
    """
    return bool(kort_db.execute(
        "SELECT 1 FROM Passkort WHERE pass_id = ? AND kort_id = ? LIMIT 1",
        (pass_id, kort_id)).fetchone())


def registrera(kort_db: sqlite3.Connection, pass_id: int,
               utfall: dict[int, bool], nu: datetime | None = None) -> int:
    """Skriv in vad som hände med de kort meningen rörde.

    ETT FALLERAT KORT FÅR EN NY RAD med roll `igen` (B7): felet ska tas igen
    i en ANNAN mening inom samma pass, och FSRS kan inte ge det — utan
    inlärningssteg är minsta intervall ett dygn. Den gamla raden står kvar
    med sitt `fel`, så passets historik är en följd av möten och inte ett
    tillstånd per kort.

    Ett kort kan förekomma i en mening utan att stå i passet — seedda kort
    som råkade vara med. De har ingen rad och får ingen.
    """
    nu = (nu or datetime.now(UTC)).isoformat()
    rörda = 0
    for pid in _syskonpass(kort_db, pass_id):
        for kort_id, rätt in utfall.items():
            rad = kort_db.execute(
                """SELECT id FROM Passkort WHERE pass_id = ? AND kort_id = ?
                   AND status = 'väntar' ORDER BY ordning, id LIMIT 1""",
                (pid, kort_id)).fetchone()
            if rad is not None:
                if pid == pass_id:
                    rörda += 1
                kort_db.execute(
                    "UPDATE Passkort SET status = ?, tidpunkt = ? WHERE id = ?",
                    ("rätt" if rätt else "fel", nu, rad["id"]))
            elif rätt:
                # Kortet hade ingen väntande rad och klarades — inget att
                # göra. ETT FEL KÖAS DÄREMOT ALLTID, även på ett kort som
                # inte stod i dagens plan.
                #
                # Det var inte så förut, och skälet var att en dag annars
                # aldrig kan ta slut: varje mening drar in kort den inte
                # valdes för (E4). BESLUTAT AV JULIUS 2026-08-27 att det är
                # rätt pris: *"Hela grejen med FSRS är att det inte finns x
                # antal övningar utan att alla korten ska passeras. Användaren
                # måste KLARA övningarna för att bli klar med dagen. Det
                # kräver framgång, inte bara effort."*
                #
                # Tillväxten är dessutom bunden av FEL och inte av antalet
                # meningar: en mening som går rätt lägger till noll, hur många
                # oplanerade kort den än rörde. Dagen växer bara när något
                # faktiskt inte satt.
                continue
            # ÅTERFÖRSÖKET LÄGGS BARA I DET EGNA PASSET. Att ta igen ett fel
            # är en handling i det pass man sitter i; grannkursen ska veta
            # att kortet mötts, inte ärva ett återförsök man aldrig får.
            #
            # OCH DET GÄLLER ÄVEN ETT KORT SOM REDAN ÄR AVKLARAT IDAG. Raden
            # ovan letade efter status `väntar` och hoppade över allt annat,
            # så ett kort som drillats rätt på morgonen och sedan fallerade i
            # en mening fick INGEN `igen`-rad. Följderna var tre, och alla
            # tre är sådant passlagret finns för att omöjliggöra:
            #
            #   · `att_göra` rörde sig inte, så dagen kunde säga "klart" med
            #     ett kort som just rasat
            #   · huvudradens `igen` (generatorns minnesinterna passkö) och
            #     `dagsläge`s `igen` (den här tabellen) gled isär och
            #     återförenades aldrig — mätt 5 mot 3 efter fem meningar
            #   · återförsöket levde bara i minnet och dog vid omstart
            #
            # Mätt på `ord:avoir`, drillat rätt och sedan fällt samma dag:
            # S 2,307 → 0,775, D 2,12 → 7,39, förfaller flyttad ETT DYGN
            # BAKÅT — medan passraden stod kvar som `glosa: rätt`.
            #
            # Att felet bokförs är riktigt (E2: "ett FEL får alltid
            # registreras"). Det som saknades var att dagen fick veta om det.
            # B7 säger att ett fel inte får lämnas ofixat, och den regeln
            # skiljer inte på om kortet råkade vara avklarat.
            if not rätt and pid == pass_id:
                kort_db.execute(
                    """INSERT INTO Passkort (pass_id, kort_id, roll, ordning)
                       VALUES (?, ?, 'igen',
                               (SELECT COALESCE(MAX(ordning), 0) + 1
                                FROM Passkort WHERE pass_id = ?))""",
                    (pid, kort_id, pid))
        _kanske_avsluta(kort_db, pid, nu)
    kort_db.commit()
    return rörda


def avskriv(kort_db: sqlite3.Connection, pass_id: int,
            nu: datetime | None = None) -> int:
    """Allt som väntar är ONÅBART. Passets nödutgång (B8).

    Anropas när generatorn sökt igenom flera hundra kandidater och inte
    hittat en enda mening som rör något av det som väntar. Då går det inte
    att komma längre idag, och det ska stå skrivet — inte upptäckas om igen
    vid nästa anrop.

    Korten får INGET betyg. Ett kort utan mätning är ärligt osäkert; ett med
    påhittad mätning är värre än tomt (D3).

    GLOSOR SKRIVS ALDRIG AV. En glosa möts i drillen och inte i en mening, så
    att generatorn inte når den säger ingenting om huruvida den går att göra.
    """
    nu = (nu or datetime.now(UTC)).isoformat()
    n = kort_db.execute(
        """UPDATE Passkort SET status = 'onåbar', tidpunkt = ?
           WHERE pass_id = ? AND status = 'väntar' AND roll <> 'glosa'""",
        (nu, pass_id)).rowcount
    _kanske_avsluta(kort_db, pass_id, nu)
    kort_db.commit()
    return n


def _kanske_avsluta(kort_db: sqlite3.Connection, pass_id: int, nu) -> None:
    kvar = kort_db.execute(
        """SELECT COUNT(*) AS n FROM Passkort WHERE pass_id = ?
           AND status = 'väntar' AND kort_id IS NOT NULL""",
        (pass_id,)).fetchone()["n"]
    tid = nu if isinstance(nu, str) else (nu or datetime.now(UTC)).isoformat()
    kort_db.execute(
        "UPDATE Pass SET avslutad = ? WHERE id = ?",
        (None if kvar else tid, pass_id))
