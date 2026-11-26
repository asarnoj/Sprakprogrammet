"""FSRS-schemaläggning ovanpå kortlagret.

Algoritmen kommer från paketet `fsrs` (6.3.2) och skrivs inte om här. Skälet
är projektets eget: en tyst felaktig implementation av en minnesmodell märks
inte på månader, och det är precis den sortens fel som har kostat mest i det
här projektet. Ett testat bibliotek är billigare än en egen härledning.

Vad som DÄREMOT är vårt är hur systemet används, och där finns tre beslut
ur GENERATOR.md som alla syns i koden nedan.

INGA INLÄRNINGSSTEG. `Scheduler` startar normalt varje kort i en kedja om
en och tio minuter, och lägger tillbaka fallerade kort i en tiominutersloop.
Vi kör med tomma steglistor: att se SAMMA kort om och om igen är precis det
som gör att man fastnar, och genereringen kan i stället ge kortet i en ny
mening med andra ord runt sig.

Men den ersättningen sker INTE här, och det påstod den här texten tidigare
att den gjorde. FSRS minsta intervall är ett dygn, så ett fallerat kort
schemaläggs i morgon och kan inte komma tillbaka i dagens kö hur kön än
sorteras. Återförsöket ligger i generatorns PASSKÖ (`generator/__init__.py`),
som är per pass och lever i minnet. Schemaläggningen här rörs inte av den —
återförsöket blir en tidig repetition, med den mindre stabilitetsökning
FSRS ger sådana.

OAVSIKTLIGA REPETITIONER RÄKNAS. En mening rör sju till tio kort men valdes
för ett av dem. Alla får betyg. FSRS räknar på faktisk förfluten tid och ger
en repetition före förfallodatum en MINDRE stabilitetsökning — spacing-
effekten är modellerad, inte kringgången.

ETT FALLERAT ORDKORT SKYDDAR SINA FORMER. Kan man inte hämta fram ordet alls
testades formen aldrig, och den ska inte straffas för det. Utan den regeln
skulle ett enda ordglapp fälla trettio formkort på en gång.
"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import UTC, datetime, timedelta

from fsrs import Card, Rating, Scheduler, State


def _kategori(rad: sqlite3.Row) -> str:
    """Konceptets semantiska kategori — nyckelns prefix, `krop_öga` → `krop`.

    Finns redan i datan och behöver varken importeras eller gissas. Kort utan
    koncept grupperas på sin typ i stället.
    """
    koncept = rad["koncept"]
    return koncept.split("_", 1)[0] if koncept and "_" in koncept else rad["typ"]


def _fläta(rader: list[sqlite3.Row], gräns: int) -> list[sqlite3.Row]:
    """Behåll rangordningen, men undvik två ur samma kategori i rad.

    Girigt: ta alltid det högst rankade kort vars kategori skiljer sig från
    det förra. Finns inget sådant tas det högst rankade ändå — ordningen får
    aldrig offras för växlingen, bara justeras av den.
    """
    kvar = list(rader)
    ut: list[sqlite3.Row] = []
    förra: str | None = None
    while kvar and len(ut) < gräns:
        vald = next((r for r in kvar if _kategori(r) != förra), kvar[0])
        kvar.remove(vald)
        ut.append(vald)
        förra = _kategori(vald)
    return ut


def dygnets_början(nu: datetime | None = None) -> str:
    """När det nuvarande dygnet började, som UTC-tidsstämpel.

    LOKAL midnatt, inte UTC. UTC-midnatt är 02:00 i Sverige, så ett pass
    klockan 00:30 skulle räknas till gårdagen — vilket är fel för den som
    övar. Gränsen härleds ur systemets tidszon och innehåller därför inget
    valt tal.

    (Anki lägger gränsen några timmar efter midnatt, för att ett sent pass
    ska höra till kvällen man började. Det är en inställning och inte en
    härledning, och den läggs till om användningen visar att den behövs.)
    """
    lokal = (nu or datetime.now(UTC)).astimezone()
    midnatt = lokal.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnatt.astimezone(UTC).isoformat()

#: VILLKORET FÖR ATT FÅ INFÖRAS, som SQL. `schemalagt` styr REPETITIONEN —
#: ett ord som möts i varannan mening behöver ingen spacing (kort.sql) — men
#: det säger ingenting om huruvida användaren har mött ordet. Att låta flaggan
#: grinda introduktionen gjorde vanliga ord till ord som aldrig lärdes ut, och
#: lät meningarna presentera dem ändå: `un`, `avoir` och `coûter` var exakt de
#: tre franska ordkort som hade `schemalagt = 0`.
#:
#: Frågor om `sedd` — vad som är infört, vad som återstår, vad dagen har kostat
#: — använder därför den här, medan frågor om `förfaller` behåller
#: `schemalagt = 1`. Se `Schemaläggare.osedda` och `introduktionsprov.py`.
INFÖRBAR = "(schemalagt = 1 OR typ = 'ord')"

#: Betyg. FSRS har fyra steg, men en diff mot facit ger bara två signaler:
#: formen stod där eller inte. HARD och EASY lämnas oanvända hellre än att
#: härledas ur något som inte mäter dem — svarstid är en kandidat senare.
FEL, RÄTT = Rating.Again, Rating.Good


def _skapa_schemaläggare(retentionsmål: float | None = None, *,
                         fuzza: bool = True) -> Scheduler:
    """Schemaläggaren. `retentionsmål` bara för simuleringar av ANDRA mål —
    kursens eget värde är bibliotekets förval tills E7 mätt fram ett bättre.

    `fuzza=False` FÖR SIMULERINGAR. FSRS sprider förfallodagar med en liten
    slump, vilket är rätt i drift — annars klumpar en hel dags införda kort
    ihop sig för alltid. Men fuzzningen drar ur `random`-MODULEN, inte ur ett
    frö man kan skicka in, så en simulering med fast frö blir ändå inte
    deterministisk. Mätt: kostnadskurvans kum(365) vandrade mellan 8,231 och
    8,267 beroende på globalt slumptillstånd.

    Det är litet i tal och stort i art: kurvan styr hur många nya kort som
    införs per dag, och ett tal som ändrar sig mellan anrop går inte att
    resonera om. Provet `arbetsbördeprov.py` hittade det.
    """
    return Scheduler(learning_steps=(), relearning_steps=(),
                     enable_fuzzing=fuzza,
                     **({} if retentionsmål is None
                        else {"desired_retention": retentionsmål}))


def _till_card(rad: sqlite3.Row) -> Card:
    """Databasrad → fsrs.Card, utan översättningsförlust."""
    return Card(
        card_id=rad["id"],
        state=State(rad["tillstånd"]),
        step=rad["steg"],
        stability=rad["stabilitet"],
        difficulty=rad["svårighet"],
        due=datetime.fromisoformat(rad["förfaller"]) if rad["förfaller"]
        else datetime.now(UTC),
        last_review=datetime.fromisoformat(rad["sedd"]) if rad["sedd"] else None,
    )


class Schemaläggare:
    """Läser och skriver FSRS-tillstånd för kort i inlärardatabasen."""

    def __init__(self, kort_db: sqlite3.Connection) -> None:
        self.db = kort_db
        self.fsrs = _skapa_schemaläggare()

    # ── läsa ─────────────────────────────────────────────────────────

    def retention(self, rad: sqlite3.Row, nu: datetime | None = None) -> float:
        """R — sannolikheten att kortet minns just nu.

        Det är den här siffran svårighetsbudgeten summerar: förväntat antal
        fel i en mening är Σ(1−R) över dess kort. Ett osett kort har inget
        minne att mäta och räknas som 0.
        """
        if rad["sedd"] is None:
            return 0.0
        return self.fsrs.get_card_retrievability(_till_card(rad), nu or datetime.now(UTC))

    def förfallna(self, språk: str, gräns: int = 100,
                  nu: datetime | None = None) -> list[sqlite3.Row]:
        """Schemalagda kort som är förfallna, svagast först.

        Bara `schemalagt = 1`. Ett kort som möts i nästan varje mening går
        inte att schemalägga och står inte i kön — se kort.sql.
        """
        tid = (nu or datetime.now(UTC)).isoformat()
        # SVAGAST FÖRST BETYDER LÄGST R, INTE ÄLDST FÖRFALLODATUM. R beror på
        # FÖRHÅLLANDET mellan förfluten tid och stabilitet, inte på antalet
        # dagar: ett kort med S = 2 som är ETT dygn försenat ligger på R =
        # 0,870, medan ett med S = 100 som är TRETTIO dygn försenat ligger på
        # 0,881. Sortering på datum gynnar alltså systematiskt kort med långa
        # intervall — och docstringen har hela tiden påstått motsatsen.
        #
        # R är monotont avtagande i (förfluten / stabilitet), så den kvoten
        # ger samma ordning utan att FSRS-formeln behöver in i SQL.
        #
        # Uppskjutningen (`skjut_upp`) gör detta nödvändigt och inte bara
        # riktigare: den flyttar `förfaller` till imorgon, så ett kort som
        # varit försenat i tre veckor skulle annars tappa hela sin plats i
        # kön. Med kvoten behåller det den, eftersom `sedd` inte rörs.
        return self.db.execute(
            """SELECT * FROM Kort
               WHERE språk = ? AND schemalagt = 1
                 AND förfaller IS NOT NULL AND förfaller <= ?
               ORDER BY (julianday(?) - julianday(sedd))
                        / MAX(COALESCE(stabilitet, 0.001), 0.001) DESC
               LIMIT ?""", (språk, tid, tid, gräns)).fetchall()

    #: Ordningen nya kort introduceras i. Ordet först, alltid: man kan inte
    #: lära sig att svag maskulin dativ tar -en innan man har ett ord att
    #: sätta ändelsen på. Inom en typ går det mest räckviddiga först — den
    #: stam som täcker fyrtionio celler är mer värd än den som täcker en.
    #:
    #: Det här är schemaläggarens FÖRVAL. Vilket kort en viss mening ska
    #: byggas kring är generatorns beslut, och den kan välja annorlunda.
    INTRODUKTIONSORDNING = ("ord", "egenskap", "stam", "form", "system",
                            "rektion", "ordföljd")

    def kommande(self, språk: str, gräns: int = 100,
                 nu: datetime | None = None) -> list[sqlite3.Row]:
        """Kort som ÄNNU INTE förfallit, det som förfaller först först.

        Det här är extraövningens kö. Att göra en repetition i förväg är
        tillåtet i FSRS och inte ett kringgående av den: algoritmen räknar på
        faktiskt förfluten tid och ger en tidig repetition en MINDRE
        stabilitetsökning. Men den ger en ökning, och det är det som gör
        extraövningen till något annat än tomgång — kortets nästa förfallodag
        flyttas framåt, dess 1/intervall sjunker, och belastningen med den.

        Det är precis den vägen ny plats uppstår utan att någonting väntar:
        `dagsplan` läser om belastningen efter varje mening.
        """
        tid = (nu or datetime.now(UTC)).isoformat()
        # KORT SOM INFÖRTS IDAG HÖR INTE HIT. De kan inte betygsättas igen
        # samma dygn (E2), så en extraövning byggd på dem bokför ingenting
        # alls — passet skulle se ut att göra något och göra noll.
        #
        # Mätt efter en nollställning: alla 14 kort i "early available" var
        # införda samma dag. Hela högen var alltså tom på verkan.
        return self.db.execute(
            """SELECT * FROM Kort
               WHERE språk = ? AND schemalagt = 1 AND sedd IS NOT NULL
                 AND sedd < ?
                 AND förfaller IS NOT NULL AND förfaller > ?
               ORDER BY förfaller LIMIT ?""",
            (språk, dygnets_början(nu), tid, gräns)).fetchall()

    def oglosade(self, språk: str, gräns: int = 10) -> list[sqlite3.Row]:
        """Ordkort som aldrig prövats — de som ska LÄRAS IN som glosor först.

        ETT ORDKORT ÄR EN GLOSA, INTE EN BÖJNINGSFRÅGA. Det frågar om ordet
        finns och vad det betyder, och det går inte att svara på ur en
        meningskontext man inte kan läsa. Mätt på en ny fransk kurs var den
        allra första meningen `Hon tittar.` → `Elle regarde.` med BÅDA orden
        osedda: uppgiften gick inte att lösa, bara att gissa.

        Övriga korttyper — stam, ändelse, genus — handlar om BÖJNING, och den
        lär man sig i en mening. De introduceras därför som förut. Skillnaden
        följer alltså kortmodellens egen uppdelning och är ingen ny kategori.

        Ordningen är `osedda`s: kategorierna varvade, mest räckviddigt först.
        """
        return [r for r in self.osedda(språk, gräns * 20) if r["typ"] == "ord"][:gräns]

    def osedda(self, språk: str, gräns: int = 100,
               uteslut: tuple[str, ...] = ()) -> list[sqlite3.Row]:
        """Kort som aldrig prövats. Det är här nya ord kommer in.

        RANGEN STYR, KATEGORIN BRYTER UPP KÖER. Två krav som drar åt olika
        håll, och ordningen mellan dem visade sig avgörande.

        Rangen (`Kort.rang`, se befolka._rang) säger vad som är viktigast:
        kärnordförrådet före det öppna, A1 före A2, och inom ordklassen det
        ord som gör flest meningar möjliga. Utan den föll ordningen tillbaka
        på databasordningen — en fransk nybörjare mötte `argent` och
        `s'asseoir` före `je`.

        Kategorin — konceptnyckelns prefix (`krop_`, `djur_`) — finns för att
        ordlistorna är skrivna kategori för kategori. Rakt av gav det femton
        kroppsdelar i rad, alltså precis den semantiska interferens
        poängsättaren straffar inom en mening.

        Att låta kategorin rotera FÖRST dränkte rangen: varje varv tog ett ord
        ur var och en av ett trettiotal kategorier, och eftersom de flesta är
        substantivkategorier hamnade `väder`, `flicka` och `brandman` före
        `jag`. Därför sorteras det på rang, och kategorin används bara till att
        skjuta upp ett ord som skulle följa direkt på ett ur samma kategori.

        ORDET FÖRST, SEDAN DESS BÖJNING. Ett `stam`- eller `egenskap`-kort för
        ett ord användaren aldrig mött är inte en böjningsfråga utan en
        glosfråga i förklädnad: den går inte att svara på, och att ställa den
        INFÖR ordet — meningen renderas, ordkortet rörs, betygsätts och
        schemaläggs, helt utanför glosläget och dagsplanens tak.

        Det var vägen in för `coûter`. Mätt i bruk: sex ord introducerade i
        drillen klockan 14:19, och passet gav sedan tio meningar i rad som
        vart och ett införde ett ord som inte var något av de sex — `homme`,
        `fille`, `famille`, `frère cadet`. `uteslut=("ord",)` höll ordKORTET
        borta men inte ordet: egenskapskortet för samma koncept kom in i kön,
        blev MÅLORD, och samplaren byggde meningen kring det. Målordet går
        förbi `Samplare.begränsa`, som bara styr fyllnaden.

        Villkoret nedan är därför inte ett filter utan en ORDNINGSREGEL: ett
        kort får introduceras först när ordet det hör till är introducerat.
        Ordkortet självt går fri (`o.id <> Kort.id`), och ett koncept helt
        utan ordkort — systemkorten, som inte hör till något ord — likaså.

        ATT INTRODUCERA ÄR INTE ATT SCHEMALÄGGA. `schemalagt = 0` betyder att
        ordet möts så ofta att spacing är meningslöst (kort.sql) — inte att
        användaren redan kan det. Att låta det filtret gälla INTRODUKTIONEN
        gjorde ett ord som möts ofta till ett ord som aldrig lärs ut, och
        sedan lät meningarna presentera det ändå.

        De tre franska ordkort som var `schemalagt = 0` — `un` (exponering
        0,846), `avoir` (0,354) och `coûter` (0,066) — är exakt de tre ord som
        dök upp oannonserade i passet. Det var inte ett sammanträffande utan
        samma rad kod sedd från andra hållet.

        Därför gäller `schemalagt` fortsatt för REPETITIONEN (`förfallna`
        filtrerar på den), men inte här: ett ordkort får introduceras oavsett
        exponering. En gång, i glosläget, och sedan aldrig mer i kön.
        """
        ordning = " ".join(
            f"WHEN '{t}' THEN {i}" for i, t in enumerate(self.INTRODUKTIONSORDNING))
        # Filtret måste ligga i FRÅGAN och inte efteråt: ordkorten sorteras
        # först av INTRODUKTIONSORDNING, så en efterfiltrering på ett fönster
        # om hundra rader gav noll kvar och kön blev tom.
        filter = ("AND typ NOT IN (" + ",".join("?" * len(uteslut)) + ")"
                  if uteslut else "")
        # Ett bredare fönster än `gräns`, så att omflätningen har något att
        # välja mellan. Fyra gånger räcker för att bryta varje kö som
        # ordlistorna innehåller.
        rader = self.db.execute(
            f"""SELECT * FROM Kort
                WHERE språk = ? AND sedd IS NULL {filter}
                  AND {INFÖRBAR}
                  AND NOT EXISTS (SELECT 1 FROM Kort o
                                  WHERE o.språk = Kort.språk
                                    AND o.koncept = Kort.koncept
                                    AND o.typ = 'ord' AND o.sedd IS NULL
                                    AND o.id <> Kort.id)
                ORDER BY CASE typ {ordning} ELSE 99 END,
                         rang, räckvidd DESC, id LIMIT ?""",
            (språk, *uteslut, gräns * 4)).fetchall()
        return _fläta(rader, gräns)

    # ── skriva ───────────────────────────────────────────────────────

    def repetera(self, kort_id: int, rätt: bool, *, mening_id: int | None = None,
                 nu: datetime | None = None,
                 självrättad: bool = False,
                 millisekunder: int | None = None) -> sqlite3.Row:
        """Registrera EN prövning och skriv tillbaka det nya tillståndet."""
        nu = nu or datetime.now(UTC)
        rad = self.db.execute("SELECT * FROM Kort WHERE id = ?", (kort_id,)).fetchone()
        if rad is None:
            raise KeyError(f"kort {kort_id} finns inte")
        före = _till_card(rad)
        förfluten = ((nu - före.last_review).total_seconds() / 86400
                     if före.last_review else None)
        # Nollmodellen, sparad före prövningen. Se kort.sql, Repetition.
        r_före = self.retention(rad, nu) if rad["sedd"] else None
        efter, _ = self.fsrs.review_card(före, RÄTT if rätt else FEL, nu)

        self.db.execute(
            """UPDATE Kort SET tillstånd = ?, steg = ?, stabilitet = ?,
                   svårighet = ?, förfaller = ?, sedd = ?,
                   antal = antal + 1, fall = fall + ?
               WHERE id = ?""",
            (int(efter.state), efter.step, efter.stability, efter.difficulty,
             efter.due.isoformat(), nu.isoformat(), 0 if rätt else 1, kort_id))
        self.db.execute(
            """INSERT INTO Repetition
               (kort_id, mening_id, tidpunkt, betyg, förfluten, r_före,
                stabilitet, svårighet, självrättad, millisekunder)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (kort_id, mening_id, nu.isoformat(), int(RÄTT if rätt else FEL),
             förfluten, r_före, efter.stability, efter.difficulty,
             int(självrättad),
             # BARA för rader utan mening. Har raden en mening ligger tiden
             # på DEN, eftersom det är meningen som är det tidtagna momentet.
             millisekunder if mening_id is None else None))
        return self.db.execute("SELECT * FROM Kort WHERE id = ?", (kort_id,)).fetchone()

    def skjut_upp(self, kort_id: int, skäl: str, *,
                  mening_id: int | None = None,
                  nu: datetime | None = None) -> None:
        """Ingen mätning ägde rum. Bokför DET, och lägg undan kortet till imorgon.

        Ankis `bury` gör samma sak och av samma skäl: ett syskonkort läggs
        undan till nästa dag eftersom att repetera det strax efter avslöjar
        svaret. Vårt fall är detsamma ett steg kortare — kortets EGET facit
        stod nyss på skärmen.

        MINNESMODELLEN RÖRS INTE. Bara `förfaller` flyttas; `sedd`,
        stabilitet och svårighet står kvar. FSRS räknar R ur `sedd` och inte
        ur `förfaller`, så kortets retention är oförändrad — det kommer
        tillbaka imorgon med sin sanna svaghet. Uppskjutningen är alltså inte
        en repetition utan betyg, den är ingen repetition alls.

        RADEN BEHÖVS ÄNDÅ, eftersom kortet kan hamna i en mening OAVSIKTLIGT:
        en mening vald för ett annat kort kan råka innehålla det, och då
        skulle det betygsättas trots uppskjutningen. `_redan_idag` läser
        dagens rader, så en betyglös rad skyddar kortet resten av dygnet utan
        att en enda regel behöver ändras — och asymmetrin faller ut rätt:
        `graderade` fångar raden så ett RÄTT hoppas över, medan `fällda`
        filtrerar på betyg = FEL och därför släpper igenom ett FEL.

        NYA KORT SKA ALDRIG SKJUTAS UPP. Deras första möte ÄR introduktionen.
        Anropar man ändå gör metoden ingenting, hellre än att skjuta undan
        något som aldrig införts.
        """
        nu = nu or datetime.now(UTC)
        rad = self.db.execute("SELECT sedd FROM Kort WHERE id = ?",
                              (kort_id,)).fetchone()
        if rad is None or rad["sedd"] is None:
            return
        i_morgon = datetime.fromisoformat(dygnets_början(nu)) + timedelta(days=1)
        self.db.execute("UPDATE Kort SET förfaller = ? WHERE id = ?",
                        (i_morgon.isoformat(), kort_id))
        self.db.execute(
            """INSERT INTO Repetition (kort_id, mening_id, tidpunkt, skäl)
               VALUES (?,?,?,?)""",
            (kort_id, mening_id, nu.isoformat(), skäl))

    def registrera_mening(self, språk: str, spec: str, text: str,
                          utfall: dict[int, bool], *, källspråk: str | None = None,
                          budget: float | None = None,
                          nu: datetime | None = None,
                          självrättade: set[int] | None = None,
                          rörda: set[int] | None = None,
                          millisekunder: int | None = None,
                          svar: str | None = None,
                          anmärkningar: list | None = None) -> int:
        """Logga en hel mening och betygsätt varje kort den rörde.

        `utfall` är kort_id → klarade det. Ett fallerat ORDKORT skyddar sina
        egna form- och stamkort: de tas ur betygsättningen helt och behåller
        sitt passerade förfallodatum, eftersom de aldrig prövades.
        """
        nu = nu or datetime.now(UTC)
        # NOLLMODELLEN RÄKNAS BARA ÖVER SEDDA KORT. Ett osett kort har R = 0,
        # och att summera det in i `förväntat` vore att påstå att FSRS
        # förutsäger ett säkert fel — men modellen förutsäger ingenting alls
        # om ett kort den aldrig sett. Talet blev då två storheter adderade,
        # förväntade fel plus antalet nya ord, och därmed oanvändbart som
        # nollmodell. Poängsättaren gjorde redan den här uppdelningen; loggen
        # gjorde det inte, så samma namn betydde olika saker på två ställen.
        # `rörda` är alla kort meningen innehöll, `utfall` bara de som fick
        # en dom. Skillnaden är de UNDANHÅLLNA — utan den kan de inte skjutas
        # upp, och då står de kvar som förfallna resten av dagen.
        rörda_idn = rörda if rörda is not None else set(utfall)
        rader = self._rader(utfall)
        sedda = [r for r in rader if r["sedd"] is not None]
        förväntat = sum(1 - self.retention(r, nu) for r in sedda)
        markör = self.db.execute(
            """INSERT INTO Mening (tidpunkt, språk, källspråk, spec, text,
                                   budget, förväntat, sedda, nya, fel,
                                   millisekunder)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (nu.isoformat(), språk, källspråk, spec, text, budget, förväntat,
             len(sedda), len(rader) - len(sedda),
             sum(1 for v in utfall.values() if not v), millisekunder))
        mening_id = markör.lastrowid

        skyddade = self._skyddade(utfall)
        graderade, fällda = self._redan_idag(utfall, nu)

        # VARJE KORTS LÄGE SKRIVS NER, inte bara de som får en dom. Ett kort
        # utan `Repetition`-rad kan ha hamnat där på fem sätt med helt olika
        # innebörd, och skillnaden var omöjlig att härleda i efterhand. Se
        # migrationen `spar.sql`.
        lägen: list[dict] = []

        # UNDANHÅLLNA KORT. Rättningen tog dem ur `utfall` därför att felet
        # inte gick att knyta till ett kort. De stod tidigare kvar som
        # förfallna och plockades gärna till nästa mening — efter att facit
        # visats. Nu skjuts de upp i stället.
        for kort_id in set(rörda_idn) - set(utfall):
            self.skjut_upp(kort_id, "undanhållen", mening_id=mening_id, nu=nu)
            lägen.append({"kort": kort_id, "läge": "undanhållen", "rätt": None})

        for kort_id, rätt in utfall.items():
            if kort_id in skyddade:
                # Ordkortet fallerade, så formen prövades aldrig. Samma sak:
                # ingen mätning, alltså ingen bedömning — och kortet får inte
                # prövas igen idag, eftersom ordet just visades.
                self.skjut_upp(kort_id, "skyddad", mening_id=mening_id, nu=nu)
                lägen.append({"kort": kort_id, "läge": "skyddad", "rätt": rätt})
                continue
            # EN BEDÖMNING PER KORT OCH DYGN. Se `_redan_idag`.
            if rätt and kort_id in graderade:
                lägen.append({"kort": kort_id, "läge": "redan_bedömd",
                              "rätt": True})
                continue
            if not rätt and kort_id in fällda:
                # DEN HÄR GRENEN ÄR SVÅRAST ATT SE UTIFRÅN, och den är skälet
                # till att `again` kan stå stilla medan användaren gör fel:
                # kortet ligger redan i Again sedan tidigare idag, så felet är
                # sant och bokföringen ändå tom.
                lägen.append({"kort": kort_id, "läge": "redan_fälld",
                              "rätt": False})
                continue
            self.repetera(kort_id, rätt, mening_id=mening_id, nu=nu,
                          självrättad=kort_id in (självrättade or ()))
            lägen.append({"kort": kort_id, "läge": "bedömd", "rätt": rätt})
        self._logga_spår(mening_id, svar, anmärkningar, lägen)
        self.db.commit()
        return mening_id

    def _logga_spår(self, mening_id: int, svar: str | None,
                    anmärkningar: list | None, lägen: list[dict]) -> None:
        """Bevara HUR domen kom till, vid sidan av vad den blev.

        Spåret läses aldrig av schemaläggningen. Skulle det göra det vore det
        inte längre ett spår utan en del av modellen, och då måste det
        provas som en. Se `spar.sql`.

        Korten berikas med typ och facit här och inte vid läsningen, därför
        att ett kort kan hinna raderas — en nollställning river hela
        kortleken — och ett spår som pekar på ett kort som inte finns kan
        inte längre läsas. Spåret ska överleva det det beskriver.
        """
        if lägen:
            rader = {r["id"]: r for r in self.db.execute(
                "SELECT id, typ, koncept, facit FROM Kort WHERE id IN "
                f"({','.join('?' * len(lägen))})",
                [l["kort"] for l in lägen])}
            for l in lägen:
                k = rader.get(l["kort"])
                if k is not None:
                    l["typ"], l["koncept"] = k["typ"], k["koncept"]
                    l["facit"] = k["facit"]
        self.db.execute(
            """INSERT INTO Spår (mening_id, svar, anmärkningar, kortlägen)
               VALUES (?,?,?,?)""",
            (mening_id, svar,
             json.dumps([a for a in (anmärkningar or [])], ensure_ascii=False),
             json.dumps(lägen, ensure_ascii=False)))

    def _redan_idag(self, utfall: dict[int, bool],
                    nu: datetime | None = None) -> tuple[set[int], set[int]]:
        """(kort som redan bedömts idag, kort som redan fällts idag).

        EN BEDÖMNING PER KORT OCH DYGN, och ett fel väger alltid tyngre än ett
        rätt. FSRS minsta intervall är ett dygn och modellen är byggd för den
        takten; allt tätare ligger utanför vad den beskriver.

        Mätt före regeln, på 705 riktiga repetitioner:

            48,7 %  skedde inom EN MINUT från förra mötet av samma kort
            62,1 %  skedde vid R ≥ 0,99 — kortet var så gott som säkert
             0,4 %  skedde vid R < 0,90, alltså som ett genuint minnesprov

        Av 447 prövningar av redan sedda kort var 438 tagna vid R ≈ 1. Det är
        inte att FSRS räknar fel — det räknar rätt, och rätt svar på "kan du
        det här tio sekunder efter att du skrev det?" bär ingen information.
        Femtio massade rätt lämnade stabiliteten på 2,31 (intervall 2 dygn);
        ETT rätt, vila till förfallodagen, och ett rätt till gav 10,96
        (intervall 11 dygn). Samma två svar, fem gånger så lång verkan.

        Ett FEL får däremot alltid registreras, även om kortet redan bedömts
        idag: att inte kunna något man nyss skrev rätt är information, och
        motsatt ordning — rätt efter fel samma dag — är det inte. Just den
        rundan är dessutom mätt som nästan verkningslös i FSRS (S 0,61 → 0,66,
        D 7,39 → 7,38), så passkön förlorar ingenting på att inte bokföras.
        """
        if not utfall:
            return set(), set()
        platser = ",".join("?" * len(utfall))
        rader = self.db.execute(
            f"""SELECT kort_id, betyg FROM Repetition
                WHERE kort_id IN ({platser}) AND tidpunkt >= ?""",
            (*utfall, dygnets_början(nu))).fetchall()
        graderade = {r["kort_id"] for r in rader}
        fällda = {r["kort_id"] for r in rader if r["betyg"] == int(FEL)}
        return graderade, fällda

    # ── hjälp ────────────────────────────────────────────────────────

    def _rader(self, utfall: dict[int, bool]) -> list[sqlite3.Row]:
        if not utfall:
            return []
        platser = ",".join("?" * len(utfall))
        return self.db.execute(
            f"SELECT * FROM Kort WHERE id IN ({platser})", tuple(utfall)).fetchall()

    def _skyddade(self, utfall: dict[int, bool]) -> set[int]:
        """Form- och stamkort vars ordkort fallerade i samma mening."""
        fallna_ord = {r["koncept"] for r in self._rader(utfall)
                      if r["typ"] == "ord" and not utfall[r["id"]]}
        if not fallna_ord:
            return set()
        return {r["id"] for r in self._rader(utfall)
                if r["typ"] in ("form", "stam") and r["koncept"] in fallna_ord}


#: Förval för hur mycket användaren vill öva, när kursen inte säger något.
#: DET ENDA VALDA TALET I UPPLÅSNINGEN — och det är användarens val och inte
#: vårt: en uppgift om hens dygn, som ingen mätning kan ersätta. Allt annat
#: räknas fram (se `upplåsningsläge`).
STANDARD_MENINGAR_PER_DAG = 20

#: Så många osedda kort får en mening introducera gratis; över det straffar
#: poängsättaren varje ytterligare. Talet bor här och inte i `poang.py`
#: därför att det styr TAKTEN nytt material kommer in i, vilket är en
#: schemaläggningsfråga — poängsättaren är bara stället där regeln verkställs
#: per mening. `dagsplan` använder samma tal för att veta vad ett HELT pass
#: kan bära, så att de två inte kan säga olika saker.
#:
#: Två är fortfarande en gissning som ska mätas mot verklig användning.
NYKVOT = 2


def belastning(kort_db: sqlite3.Connection, språk: str) -> tuple[float, float | None]:
    """(repetitioner per dag för det lärda, per osett kort) — i jämvikt.

    Ett kort med stabilitet S ska enligt FSRS ses var I(S):e dag, alltså
    1/I(S) gånger per dag. Summan över de SEDDA korten är kursens dagliga
    arbetsmängd i jämvikt. Intervallet är schemaläggarens eget.

    ETT OSETT KORT KAN INTE RÄKNAS SÅ. Frestelsen är att sätta in stabiliteten
    efter första rätta svaret, men det ger kortets kostnad DEN DAG det lärs in,
    och beskriver därmed en topp som aldrig inträffar: generatorn introducerar
    nya kort i den takt användaren övar, inte alla på en gång, och intervallen
    växer med varje repetition. Måttet skulle säga att 262 nya kort kostar
    22 meningar om dagen för alltid, när sanningen är att de kostar det en dag
    var och sedan allt mindre.

    Vad ett osett kort kostar när det väl SITTER går däremot att mäta, och
    inte på användare i allmänhet utan på just den här: medelbelastningen över
    hens egna sedda kort i samma kurs. Det är en mätning av hens minne, inte
    ett antagande om det. None när kursen är oövad och mätningen saknas.

    Bara SCHEMALAGDA kort räknas. De mätta står aldrig i kön och belastar inte.
    """
    f = _skapa_schemaläggare()
    takter = [1 / f._next_interval(stability=r["stabilitet"])
              for r in kort_db.execute(
                  """SELECT stabilitet FROM Kort
                     WHERE språk = ? AND schemalagt = 1 AND sedd IS NOT NULL
                       AND stabilitet IS NOT NULL""", (språk,))]
    return sum(takter), (sum(takter) / len(takter) if takter else None)


#: Över så här länge räknas en uppgift som avbruten och inte som arbete.
#: ANALYSVAL, inte mätning — därför står det HÄR och inte i skrivningen, och
#: därför sparas råtiden okapad. Anki använder samma tak för samma sak.
#: Talet ska ersättas av en gräns mätt ur den egna fördelningen så snart den
#: finns; tills dess är det Ankis, och det står som ovägt.
AVBROTTSGRÄNS_MS = 60_000

#: Så många tidtagna meningar krävs innan växelkursen används alls.
#:
#: DET HÄR ÄR ETT VAL, och skälet är mätt: med sex tidtagna meningar gav
#: mätningen 0,16 sekunder per repetition, vilket översatte tjugo minuter till
#: 7 300 repetitioner om dagen och släppte in 813 nya kort. Ett tal som styr
#: inflödet får inte vila på tre punkter.
#:
#: Tio är valt för att medelvärdet då inte kan definieras av ett par mätningar,
#: och för att avbrottsgränsen ovan begränsar vad en enskild avvikare kan
#: flytta det. PROVET som avgör om det räcker: hur mycket rör sig skattningen
#: mellan tio och femtio mätningar? Rör den sig mycket är tröskeln för låg.
#: Det går att mäta så snart loggen växt, och tills dess står talet som OMÄTT.
MINSTA_TIDTAGNA = 10


def övade_idag(kort_db: sqlite3.Connection, språk: str,
               nu: datetime | None = None) -> set[str]:
    """Koncept som funnits i en mening som ställts idag.

    SIGNALEN TAS UR SPECEN, inte ur betygen, och det är nödvändigt. En mening
    lämnar inte alltid ett `Repetition`-spår per koncept: dygnsregeln hoppar
    över kort som redan bedömts (E2), skyddade och undanhållna kort får rader
    utan betyg, och ett kort kan sakna rad helt. Mätt fall: meningen
    `You play.` lämnade NOLL koncept med rad.

    Specen är däremot exakt — den ÄR vad meningen byggdes av, oberoende av
    vad rättningen sedan gjorde. `Mening.spec` finns redan och lagras för
    varje ställd mening.
    """
    def plocka(nod, ut: set[str]) -> None:
        if isinstance(nod, dict):
            for nyckel, värde in nod.items():
                if nyckel in ("koncept", "verb") and isinstance(värde, str):
                    ut.add(värde)
                else:
                    plocka(värde, ut)
        elif isinstance(nod, list):
            for x in nod:
                plocka(x, ut)

    ut: set[str] = set()
    for rad in kort_db.execute(
            """SELECT spec FROM Mening WHERE språk = ? AND tidpunkt >= ?""",
            (språk, dygnets_början(nu))):
        try:
            plocka(json.loads(rad["spec"]), ut)
        except (ValueError, TypeError):
            continue
    return ut


def _kort_per_koncept(kort_db: sqlite3.Connection, språk: str) -> float:
    """Hur många kort ett koncept drar med sig. MÄTT ur beståndet.

    Mätt 2026-08-24: fr 4,01 · de 4,79 · en 2,72 · ja 2,00. Skillnaden är
    verklig — japanskan har inga genuskort och få stammar — och det är just
    därför talet inte får vara en konstant: "tio nya kort" betyder två ord på
    tyska och fem på japanska.
    """
    rad = kort_db.execute(
        """SELECT COUNT(DISTINCT koncept) AS k, COUNT(*) AS n FROM Kort
           WHERE språk = ? AND schemalagt = 1 AND koncept IS NOT NULL""",
        (språk,)).fetchone()
    return (rad["n"] / rad["k"]) if rad and rad["k"] else 1.0


def oövade_koncept(kort_db: sqlite3.Connection, språk: str,
                   nu: datetime | None = None) -> list[str]:
    """Ord som INFÖRTS idag men ännu inte mötts i en mening.

    Listan, inte bara antalet: generatorn behöver den som MÅLORD. Ett
    nyinfört ord är inte förfallet — det ligger två dygn bort — och står
    därför inte i kön. Utan den här listan hade det aldrig blivit målet för
    en mening, och ordningsregeln hade bara stängt drillen utan att ge något
    i stället. Mätt före rättelsen: fjorton meningar i rad om osedda
    substantiv medan de tio drillade orden låg orörda.
    """
    övade = övade_idag(kort_db, språk, nu)
    return [r["koncept"] for r in kort_db.execute(
        """SELECT DISTINCT koncept FROM Kort
           WHERE språk = ? AND typ = 'ord'
             AND koncept IS NOT NULL AND sedd >= ?""",
        (språk, dygnets_början(nu))) if r["koncept"] not in övade]


def oövade_idag(kort_db: sqlite3.Connection, språk: str,
                nu: datetime | None = None) -> int:
    """Ord som INFÖRTS idag men ännu inte mötts i en mening.

    Det här talet är F4:s ordningsregel: introduktion och övning är två olika
    saker, och det andra ska följa på det första innan mer förs in. Utan
    regeln fyller drillen hela dagen — mätt på en kallstart delades portion
    efter portion ut tills tiden var slut, noll meningar.

    Regeln kräver inget nytt tal. Portionsstorleken finns redan, och
    villkoret är helt enkelt att förra portionen ska vara övad.
    """
    return len(oövade_koncept(kort_db, språk, nu))


def tidsspärr(tid_kvar: float, osedda: int) -> int:
    """Dagens tak på nytt material: allt eller inget, aldrig ett omräknat tal.

    Egen funktion för att regeln ska gå att BRYTA i `arbetsbördeprov.py`. En
    invariant som inte går att falsifiera bevisar ingenting — samma lärdom som
    `_igen_efter` och `_extraläge` i webblagret.

    Två lagliga värden och inga andra. Se `dagsplan` för varför omräkningen
    `tid_kvar / sekunder_per_repetition` förkastades.
    """
    return 0 if tid_kvar <= 0 else osedda


def tid_idag(kort_db: sqlite3.Connection, språk: str,
             nu: datetime | None = None) -> float:
    """Sekunder som faktiskt lagts på kursen idag, MÄTT.

    Det här talet gör kallstartskonstanten överflödig. Att räkna om minuter
    till kort kräver en växelkurs som inte finns dag ett — men att mäta hur
    lång tid dagen HITTILLS tagit kräver ingen växelkurs alls. Det är samma
    rörelse som B5 gjorde för meningar: sluta räkna enheter, mät arbetet.

    Avbrottsgränsen gäller per moment, inte per dag: en kafferast mitt i en
    mening ska inte räknas som arbete, men fem verkliga minuter ska.
    """
    gräns = dygnets_början(nu)
    m = kort_db.execute(
        """SELECT COALESCE(SUM(MIN(millisekunder, ?)), 0) AS ms FROM Mening
           WHERE språk = ? AND millisekunder IS NOT NULL AND tidpunkt >= ?""",
        (AVBROTTSGRÄNS_MS, språk, gräns)).fetchone()["ms"]
    g = kort_db.execute(
        """SELECT COALESCE(SUM(MIN(r.millisekunder, ?)), 0) AS ms
           FROM Repetition r JOIN Kort k ON k.id = r.kort_id
           WHERE k.språk = ? AND r.mening_id IS NULL
             AND r.millisekunder IS NOT NULL AND r.tidpunkt >= ?""",
        (AVBROTTSGRÄNS_MS, språk, gräns)).fetchone()["ms"]
    return (m + g) / 1000


def kostnad_per_läge(kort_db: sqlite3.Connection, språk: str) -> dict:
    """Sekunder per repetition, UPPDELAT på mening och glosa.

    Frågan "går en mening snabbare per kort än en glosa?" har ett svar så
    snart båda är tidtagna, och svaret är intressant — men det används INTE
    av styrningen. Där är det poolade medelvärdet rätt statistik: användarens
    minuter köper repetitioner i den blandning som faktiskt uppstår, och att
    väga med en framtida blandning vi inte känner vore att gissa.

    Talet finns alltså som UPPLYSNING, inte som ratt.

    ÄRVER MELLAN SPRÅK PÅ SAMMA VILLKOR SOM `sekunder_per_repetition`, och
    det var en riktig inkonsekvens att den inte gjorde det. Takten sa
    "3,67 s/rep" för tyskan — ärvt från franskan, som dokumenterat — medan
    uppdelningen sa None, eftersom den krävde tyska rader. Två tal ur samma
    logg, det ena "mätt" och det andra "omätt", bredvid varandra på samma
    skärm. Minst ett av dem var då fel, och det gick inte att se vilket.
    """
    ut = {}
    # Samma tröskel och samma reservväg som `sekunder_per_repetition`: räcker
    # inte språkets egna mätningar används alla, för takten är en egenskap
    # hos människan och inte hos språket.
    # TIDTAGNA rader, inte alla. Tröskeln måste räkna samma sak som talet
    # bygger på — annars kan ett språk ha hundra betyg utan en enda klocka
    # och ändå se mätt ut. Det var precis tyskans läge: 33 repetitioner, noll
    # med `millisekunder`.
    egna = kort_db.execute(
        """SELECT COUNT(*) AS n FROM Repetition r JOIN Kort k ON k.id = r.kort_id
           LEFT JOIN Mening m ON m.id = r.mening_id
           WHERE k.språk = ? AND r.betyg IS NOT NULL
             AND (r.millisekunder IS NOT NULL
                  OR m.millisekunder IS NOT NULL)""", (språk,)).fetchone()["n"]
    if egna < MINSTA_TIDTAGNA:
        språk = None
    villkor = "k.språk = ?" if språk else "1 = 1"
    p = (AVBROTTSGRÄNS_MS, språk) if språk else (AVBROTTSGRÄNS_MS,)
    m = kort_db.execute(
        f"""SELECT SUM(ms) AS ms, SUM(n) AS n FROM (
               SELECT MIN(m.millisekunder, ?) AS ms, COUNT(*) AS n
               FROM Repetition r JOIN Mening m ON m.id = r.mening_id
               JOIN Kort k ON k.id = r.kort_id
               WHERE {villkor} AND r.betyg IS NOT NULL
                 AND m.millisekunder IS NOT NULL GROUP BY m.id)""",
        p).fetchone()
    g = kort_db.execute(
        f"""SELECT SUM(MIN(millisekunder, ?)) AS ms, COUNT(*) AS n
           FROM Repetition r JOIN Kort k ON k.id = r.kort_id
           WHERE {villkor} AND r.betyg IS NOT NULL AND r.mening_id IS NULL
             AND r.millisekunder IS NOT NULL""",
        p).fetchone()
    for namn, rad in (("mening", m), ("glosa", g)):
        ut[namn] = (rad["ms"] / rad["n"] / 1000
                    if rad and rad["n"] and rad["ms"] else None)
    return ut


def sekunder_per_repetition(kort_db: sqlite3.Connection, språk: str,
                            *, före: str | None = None) -> float | None:
    """Vad EN repetition kostar i tid. Växelkursen mellan minuter och kort.

    B4 gjorde minuter per dag till användarens enda val. Utan det här talet
    finns ingen väg från det talet till "hur många nya kort tål dygnet", och
    hela arbetsbörderegleringen (B2) står stilla.

    MEDELVÄRDE OCH INTE MEDIAN. Frestelsen är medianen, som är robust mot
    avbrott — men användarens tjugo minuter köper repetitioner i GENOMSNITTLIG
    takt, inte i typisk. Fördelningen är högersvansad, så medianen skulle
    systematiskt underskatta tiden och därmed släppa in för mycket nytt.
    Avvikarna hanteras i stället av `AVBROTTSGRÄNS_MS`, och bruset av
    `MINSTA_TIDTAGNA`.

    MENINGENS TID DELAS PÅ DESS BEDÖMDA KORT. Ansträngning går inte att
    fördela mellan korten i en mening — det var slutsatsen som fällde
    svarstid som minnessignal (E3) — men SEKUNDER gör det. En mening som gav
    två bedömningar på tjugo sekunder kostade tio sekunder per repetition,
    oavsett vilket av korten som var svårt.

    Divisorn är BEDÖMDA kort, inte rörda: uppskjutna kort (D3, E5) förbrukade
    tid utan att ge en repetition, och då ÄR kostnaden per repetition högre.
    Det är precis vad kostnadsmodellen ska veta.

    TVÅ KORNIGHETER, och de får inte blandas. Tiden hör till MENINGEN,
    bedömningarna till KORTEN. En rak join ger en rad per bedömning där varje
    rad bär meningens hela tid, och summan räknar då samma tid en gång per
    kort — mätt gav det 26,6 sekunder per repetition där det rätta var 5,2.
    Meningarna summeras därför för sig, med `GROUP BY m.id`.

    Glosläget räknas med men på egen hand: där finns ingen mening, och ett
    kort och ett svar ÄR hela momentet, så tiden står på raden själv.

    None när ingen tid ännu loggats — talet gissas inte fram.
    """
    # DAGENS BESLUT FÅR INTE PÅVERKAS AV DAGENS EGNA FÖLJDER. Utan `före`
    # sjönk skattningen medan användaren drillade snabbt, vilket HÖJDE dagens
    # mål och släppte in fler kort — mätt växte inflödestaket från 50 till 57
    # mitt under en lektion. Brådska belönades med mer arbete, och dagens tal
    # rörde sig medan man tittade på dem.
    tak = f"AND m.tidpunkt < '{före}'" if före else ""
    tak_r = f"AND r.tidpunkt < '{före}'" if före else ""

    def antal(villkor: str, *p) -> int:
        return kort_db.execute(
            f"""SELECT COUNT(DISTINCT m.id) AS n FROM Mening m
                JOIN Repetition r ON r.mening_id = m.id
                JOIN Kort k ON k.id = r.kort_id
                WHERE m.millisekunder IS NOT NULL {tak} AND {villkor}""",
            p).fetchone()["n"]

    # EN NY KURS ÄRVER ANVÄNDARENS TAKT. Sekunder per repetition är en
    # egenskap hos MÄNNISKAN — hur fort hen läser och skriver — och inte hos
    # språket. Att låta en nystartad kurs vara måttlös när samma användare
    # har hundra tidtagna pass i ett annat språk vore att kasta en mätning
    # som redan finns.
    #
    # Språkets egen siffra går före när den finns; den fångar att japanska tar
    # längre tid att skriva än franska.
    if antal("k.språk = ?", språk) < MINSTA_TIDTAGNA:
        if antal("1 = 1") < MINSTA_TIDTAGNA:
            # Ingen mätning någonstans. Att svara None är inte en brist utan
            # hela poängen: anroparen faller tillbaka i stället för att styra
            # inflödet efter brus.
            return None
        språk = None
    filter_ = "k.språk = ?" if språk else "1 = 1"
    p = (AVBROTTSGRÄNS_MS, språk) if språk else (AVBROTTSGRÄNS_MS,)
    m = kort_db.execute(
        f"""SELECT SUM(ms) AS ms, SUM(n) AS n FROM (
               SELECT MIN(m.millisekunder, ?) AS ms, COUNT(*) AS n
               FROM Repetition r
               JOIN Mening m ON m.id = r.mening_id
               JOIN Kort k   ON k.id = r.kort_id
               WHERE {filter_} AND r.betyg IS NOT NULL
                 AND m.millisekunder IS NOT NULL {tak}
               GROUP BY m.id)""", p).fetchone()
    g = kort_db.execute(
        f"""SELECT SUM(MIN(r.millisekunder, ?)) AS ms, COUNT(*) AS n
           FROM Repetition r JOIN Kort k ON k.id = r.kort_id
           WHERE {filter_} AND r.betyg IS NOT NULL
             AND r.mening_id IS NULL AND r.millisekunder IS NOT NULL {tak_r}""",
        p).fetchone()
    ms = (m["ms"] or 0) + (g["ms"] or 0)
    n = (m["n"] or 0) + (g["n"] or 0)
    return ms / n / 1000 if n and ms else None


def extranytta(kort_db: sqlite3.Connection, språk: str,
               nu: datetime | None = None) -> float | None:
    """Hur mycket en extraövning är värd JUST NU, som andel av full nytta.

    B6 slog fast att extraövning fungerar men avtagande: en repetition före
    förfallodagen ger en mindre stabilitetsökning, eftersom tillväxttermen
    `(e^(w10·(1−R)) − 1)` går mot noll när R går mot ett (B1). Vad som saknats
    är att SÄGA det. Knappen har hela tiden lovat "träna extra" utan att
    skilja en dag då det ger nästan allt från en då det ger noll.

    MÅTTET ÄR EN KVOT OCH INGET VALT TAL: för varje kort i extraövningens kö
    körs FSRS två gånger — en gång nu, en gång på kortets förfallodag — och
    kvoten mellan stabilitetsökningarna är hur stor del av nyttan man får ut
    av att göra det i förtid. Mätt på ett moget kort (S = 10,96, D = 2,11,
    förfaller om elva dygn):

        repeteras   11 d före    8 d      5 d      3 d      1 d    i tid
        andel av
        full nytta        0 %   35 %     63 %     79 %     93 %    100 %

    Och samma dygn som kortet infördes är svaret exakt noll: FSRS
    korttidsformel klämmer ökningen till 1,0× när mindre än ett dygn gått
    (E2), så en extraövning på dag ett bokför ingenting alls.

    None när kön är tom — det finns då ingen nytta att uttala sig om.
    """
    nu = nu or datetime.now(UTC)
    rader = Schemaläggare(kort_db).kommande(språk, 100, nu)
    if not rader:
        return None
    s = _skapa_schemaläggare(fuzza=False)
    andelar = []
    for rad in rader:
        if rad["stabilitet"] is None or rad["förfaller"] is None:
            continue
        kort = _till_card(rad)
        före = kort.stability
        nu_kort, _ = s.review_card(kort, RÄTT, review_datetime=nu)
        # SAMMA KORT, PRÖVAT PÅ SIN FÖRFALLODAG. Det är nämnaren: den fulla
        # nyttan man avstår från genom att göra det i förtid.
        i_tid, _ = s.review_card(
            _till_card(rad), RÄTT,
            review_datetime=datetime.fromisoformat(rad["förfaller"]))
        full = i_tid.stability - före
        andelar.append(max(0.0, (nu_kort.stability - före) / full)
                       if full > 0 else 0.0)
    return sum(andelar) / len(andelar) if andelar else None


def sekunder_per_rad(kort_db: sqlite3.Connection, språk: str) -> float | None:
    """Vad EN PASSRAD kostar i tid. Växelkursen mellan `att_göra` och minuter.

    VARFÖR DEN INTE ÄR `sekunder_per_repetition`. Det talet har BEDÖMDA KORT
    i nämnaren: en menings sekunder delas på de kort den betygsatte. Det är
    rätt bokföring för vad en repetition kostar (E7), och det är den kursen
    inflödesstyrningen ska använda.

    Men `att_göra` räknar något annat: PASSRADER. Och en mening stänger
    färre rader än den betygsätter kort — den betygsätter allt den rör, men
    stänger bara de rader som stod i dagens plan. Mätt på verkliga pass:

        glosor    1,00 rader per svar   (per definition — en glosa, ett svar)
        meningar  1,33–1,80 rader per svar

    `minuter_kvar = att_göra × sekunder_per_repetition` multiplicerade alltså
    två tal med olika nämnare. Mätt över en simulerad vecka med användarens
    egna svarstider underskattade det genomgående med omkring hälften:

        dag 1   lovade 1 min   verkligt 1,5
        dag 3   lovade 2 min   verkligt 3,4
        dag 5   lovade 3 min   verkligt 4,4
        dag 7   lovade 4 min   verkligt 5,7

    DEN HÄR NÄMNAREN GÅR ATT MÄTA och behöver inte modelleras.
    `Passkort.tidpunkt` sätts en gång per `registrera`-anrop, alltså en gång
    per svar, så antalet STÄNGDA RADER är en rak räkning. Täljaren är samma
    tid som `sekunder_per_repetition` summerar. Kvoten är därför sekunder per
    rad, vilket är precis vad `att_göra` ska multipliceras med.

    ÄRVER MELLAN SPRÅK på samma villkor som takten: hur fort någon läser och
    skriver är en egenskap hos människan. None när ingenting är mätt — ett
    tomt fält är ärligare än en gissad tid.
    """
    # KAPAS, INTE UTESLUTS. En uppgift som stått öppen i en timme är en
    # kafferast och inte en mätning, men att kasta raden vore att kasta det
    # arbete som faktiskt gjordes. `AVBROTTSGRÄNS_MS` är Ankis tal och står
    # som ovägt tills en egen gräns går att mäta fram (E7).
    def stängda(målspråk: str | None) -> int:
        villkor = "ku.målspråk = ?" if målspråk else "1 = 1"
        return kort_db.execute(
            f"""SELECT COUNT(*) AS n FROM Passkort pk
                JOIN Pass s  ON s.id  = pk.pass_id
                JOIN Kurs ku ON ku.id = s.kurs_id
                WHERE pk.tidpunkt IS NOT NULL AND {villkor}""",
            (målspråk,) if målspråk else ()).fetchone()["n"]

    if stängda(språk) < MINSTA_TIDTAGNA:
        if stängda(None) < MINSTA_TIDTAGNA:
            return None
        språk = None
    rader = stängda(språk)
    ms = kort_db.execute(
        f"""SELECT COALESCE(SUM(MIN(millisekunder, ?)), 0) AS ms FROM Mening
            WHERE millisekunder IS NOT NULL
              AND {'språk = ?' if språk else '1 = 1'}""",
        (AVBROTTSGRÄNS_MS, språk) if språk else (AVBROTTSGRÄNS_MS,)
    ).fetchone()["ms"]
    ms += kort_db.execute(
        f"""SELECT COALESCE(SUM(MIN(r.millisekunder, ?)), 0) AS ms
            FROM Repetition r JOIN Kort k ON k.id = r.kort_id
            WHERE r.mening_id IS NULL AND r.millisekunder IS NOT NULL
              AND {'k.språk = ?' if språk else '1 = 1'}""",
        (AVBROTTSGRÄNS_MS, språk) if språk else (AVBROTTSGRÄNS_MS,)
    ).fetchone()["ms"]
    return ms / rader / 1000 if rader and ms else None


def kort_per_mening(kort_db: sqlite3.Connection, språk: str) -> float | None:
    """Hur många kort en mening rör. MÄTT ur användarens egen historik.

    Bron mellan det användaren väljer (meningar per dag) och det systemet
    räknar i (repetitioner per dag). Storheten är stram — 5,3 till 6,7 över
    språk och nivåer, med sd omkring 1 — så medelvärdet konvergerar på tio
    meningar. Därför ingen spärr för minsta historik.

    None när kursen är oövad. Då finns heller ingen upplåsningsfråga: man kan
    inte lämna en nivå man inte börjat på, och att öva den skapar mätningen.
    """
    rad = kort_db.execute(
        """SELECT COUNT(*) AS rep, COUNT(DISTINCT r.mening_id) AS meningar
           FROM Repetition r
           JOIN Kort k ON k.id = r.kort_id
           WHERE k.språk = ? AND r.mening_id IS NOT NULL""", (språk,)).fetchone()
    return rad["rep"] / rad["meningar"] if rad["meningar"] else None


def redo_för_nivå(byggbarhet: float | None, kandidater: int) -> bool | None:
    """Går nästa nivå att ÖVA, eller blir varje mening en ordlektion?

    EFTER B2 ÄR KAPACITETEN INTE LÄNGRE EN GRIND. Inflödestakten räknas om
    varje dygn och tittar aldrig på nivå: `nya = min(osedda, inflödestak,
    dagstak)`. Fler osedda kort kan alltså BEVISLIGEN inte öka arbetsbördan,
    och att låsa en nivå för kapacitetens skull skyddar därför ingenting.

    Kvar står en helt annan fråga, och den är verklig: kan generatorn bygga
    meningar på den nya nivån med högst ett okänt ord? Franskans allra första
    mening blev `Elle regarde.` där båda orden var osedda.

    TRÖSKELN ÄR HÄRLEDD UR SÖKNINGEN SJÄLV. Generatorn prövar `kandidater`
    kandidater per mening, så andelen dugliga måste vara stor nog att minst
    en väntas i varje sökning:

        byggbarhet × kandidater ≥ 1

    Samma form som E6:s exponeringströskel, och av samma skäl: gränsen
    kommer ur systemets egen takt i stället för ur ett valt tal.

    None när byggbarheten inte gick att mäta — då finns inget svar att ge.
    """
    if byggbarhet is None or not kandidater:
        return None
    return byggbarhet * kandidater >= 1


def upplåsningsläge(kort_db: sqlite3.Connection, språk: str,
                    nästa_nivå_kort: int | None = None,
                    *, byggbarhet: float | None = None,
                    kandidater: int = 800,
                    inflödestak: int | None = None) -> dict:
    """Går nästa nivå att öva, och hur lång tid skulle den ta?

    KAPACITETSVILLKORET ÄR BORTA, och det var inte en försvagning utan en
    rättelse. Nivån öppnades förut när "belastningen den skulle ge ryms i
    det användaren valt att öva" — tre tal, varav ett var
    `meningar_per_dag × kort_per_mening` och ett var `per_kort`, kortets
    nuvarande repetitionstakt behandlad som evig.

    Två saker fällde det. B2 mätte att `per_kort` överskattar ett korts
    kostnad med en faktor 5 på en månad och 28 på ett år — ett kort kostar
    3,7 repetitioner den första månaden, inte 19. Och B2 gjorde samtidigt
    villkoret överflödigt: inflödet räknas om varje dygn som
    `nya = min(osedda, inflödestak, dagstak)` och tittar aldrig på nivå, så
    fler OSEDDA kort kan bevisligen inte öka arbetsbördan. Att låsa en nivå
    för kapacitetens skull skyddade därför ingenting.

    `rum`, `saknas`, `krävs`, `kapacitet`, `plats` och `hela_högen_ryms`
    räknades här ända till 2026-08-26, med den gamla matten. De grindade
    ingenting, gränssnittet slutade skicka dem, och kvar stod bara
    `ordbok kort --läge` som läsare. Ett tal som är både fel och oanvänt är
    en inbjudan att använda det igen, så de är borta i stället för
    kommenterade.

    KVAR STÅR TVÅ FRÅGOR, och båda är mätta:

        redo    går nivån att ÖVA? `redo_för_nivå`, alltså byggbarheten mot
                sökningens egen kandidatmängd. Franskans allra första mening
                blev `Elle regarde.` där båda orden var osedda — det är den
                gränsen som är verklig.

        dygn    hur lång tid nästa nivås kort tar i den takt användaren
                faktiskt håller. "Ryms N kort" har inget svar när villkoret
                sitter på en takt; "hur länge tar N kort" har det.

    Att skilja dem åt är hela poängen: `redo` låser en dörr, `dygn` är
    upplysning. Ett tal som bara upplyser behöver inte vara stabilt på samma
    sätt som ett som låser, och det var instabiliteten — kravet svängde med
    en faktor tio när kortleken mognade — som gjorde det gamla måttet
    omöjligt att planera efter.
    """
    rad = kort_db.execute(
        """SELECT COUNT(*) AS totalt,
                  SUM(CASE WHEN sedd IS NULL THEN 1 ELSE 0 END) AS osedda
           FROM Kort WHERE språk = ? AND schemalagt = 1""", (språk,)).fetchone()
    return {"redo": redo_för_nivå(byggbarhet, kandidater),
            "byggbarhet": byggbarhet,
            "dygn_till_klart": (math.ceil(nästa_nivå_kort / inflödestak)
                                if nästa_nivå_kort and inflödestak else None),
            "totalt": rad["totalt"], "osedda": rad["osedda"] or 0,
            "kort_per_mening": kort_per_mening(kort_db, språk),
            "nästa_nivå_kort": nästa_nivå_kort}


def _kapacitetsval(kort_db: sqlite3.Connection, språk: str,
                   meningar_per_dag: int | None) -> int:
    """Kursens `meningar_per_dag`, eller förvalet.

    KVARLEVA MED EN ENDA KVARVARANDE UPPGIFT. B4 gjorde minuter till
    användarens ratt, och kolumnen ersattes — men växelkursen mellan minuter
    och kort kräver en mätning som inte finns dag ett. Tills dess är
    `meningar_per_dag × kort_per_mening` reservmålet i `dagsplan` (B4:
    "reservvägen byter enhet på MÅLET, inte på räkningen").

    Den bodde tidigare också i `upplåsningsläge`, där den var indata till en
    kapacitetsgrind som B2 gjorde överflödig och `per_kort` gjorde fel med en
    faktor 5–28. Den vägen är borta; det här är det sista stället talet styr
    något.
    """
    if meningar_per_dag is not None:
        return meningar_per_dag
    rad = kort_db.execute(
        "SELECT meningar_per_dag FROM Kurs WHERE målspråk = ?", (språk,)).fetchone()
    return rad["meningar_per_dag"] if rad else STANDARD_MENINGAR_PER_DAG


def dagsplan(kort_db: sqlite3.Connection, språk: str,
             meningar_per_dag: int | None = None, *, passkö: int = 0,
             minuter_per_dag: float | None = None,
             nu: datetime | None = None) -> dict:
    """Dagens arbete, och hur mycket nytt som får komma in i det.

    HUR MYCKET SOM SKA GÖRAS är tre högar med olika ursprung:

        förfallna   FSRS säger att de ska prövas idag
        igen        kort som gick fel i det pågående passet (generatorns kö)
        nya         det här beslutet

    NYA KORT ÄR EN KAPACITETSFRÅGA, precis som upplåsningen. Ett nytt kort
    kostar inte en repetition utan en STRÖM av dem, avtagande med tiden, och
    summan av de strömmarna är den dagliga arbetsbördan. Att införa nytt
    tills högen känns lagom stor idag är att bygga en skuld som förfaller om
    tre veckor. Därför räknas taket ur inlärningskurvan i stället:
    `_rum` säger hur många kort till som ryms i det användaren valt att öva.

    TVÅ TAK, OCH DET LÄGSTA GÄLLER:

        rum              vad framtiden bär       (belastningen i jämvikt)
        kvar × NYKVOT    vad idag kan bära       (samma tak per mening som
                                                  poängsättaren tillämpar)

    Det andra behövs därför att `rum` är ett LAGER och inte en takt. Ryms
    fyrahundra kort betyder det inte att fyrahundra ska in idag; det betyder
    att strömmen har plats. Passets längd är takten.

    Talet är LEVANDE och behöver ingen dagbokföring: ett kort som just
    introducerats är sett, ligger i belastningen med sitt korta intervall, och
    har därmed redan ätit sin plats. `rum` sjunker alltså av sig självt när
    nytt förs in och stiger igen när korten mognar — eller när extraövningen
    flyttar fram förfallodagar. Det är samma mekanism i båda fallen.
    """
    meningar_per_dag = _kapacitetsval(kort_db, språk, meningar_per_dag)
    if minuter_per_dag is None:
        rad = kort_db.execute(
            "SELECT minuter_per_dag FROM Kurs WHERE målspråk = ?",
            (språk,)).fetchone()
        minuter_per_dag = rad["minuter_per_dag"] if rad else 20
    tid = (nu or datetime.now(UTC)).isoformat()
    gjort = kort_db.execute(
        "SELECT COUNT(*) FROM Mening WHERE språk = ? AND tidpunkt >= ?",
        (språk, dygnets_början())).fetchone()[0]
    förfallna = kort_db.execute(
        """SELECT COUNT(*) FROM Kort
           WHERE språk = ? AND schemalagt = 1
             AND förfaller IS NOT NULL AND förfaller <= ?""",
        (språk, tid)).fetchone()[0]
    # Kort som ännu inte förfallit — det extraövningen har att ta av.
    tidiga = kort_db.execute(
        """SELECT COUNT(*) FROM Kort
           WHERE språk = ? AND schemalagt = 1 AND sedd IS NOT NULL
             AND sedd < ? AND förfaller IS NOT NULL AND förfaller > ?""",
        (språk, dygnets_början(nu), tid)).fetchone()[0]

    k = kort_per_mening(kort_db, språk)
    osedda = kort_db.execute(
        f"""SELECT COUNT(*) FROM Kort
           WHERE språk = ? AND {INFÖRBAR} AND sedd IS NULL""",
        (språk,)).fetchone()[0]
    # REDAN INFÖRDA IDAG. Utan det här talet är `nya` ett TAK och inte ett
    # SALDO: glosläget kunde delas ut om och om igen, tio ord i taget, och
    # ingenting räknade. Hela styrningen i B2 gick att gå förbi genom att
    # lämna vyn och komma tillbaka.
    #
    # Måttet behöver ingen egen bokföring — ett infört kort ÄR sett, och
    # `sedd` bär tidpunkten.
    infört_idag = kort_db.execute(
        f"""SELECT COUNT(*) FROM Kort
           WHERE språk = ? AND {INFÖRBAR} AND sedd >= ?""",
        (språk, dygnets_början(nu))).fetchone()[0]
    ord_infört_idag = kort_db.execute(
        """SELECT COUNT(*) FROM Kort
           WHERE språk = ? AND typ = 'ord' AND sedd >= ?""",
        (språk, dygnets_början(nu))).fetchone()[0]

    # INFLÖDET STYRS AV TID, INTE AV MENINGAR (B4). Måltakten är användarens
    # minuter omräknade till repetitioner via sekunder per repetition, mätt
    # ur den egna loggen.
    #
    # SAKNAS DEN MÄTNINGEN faller vi tillbaka på det gamla måttet för
    # MÅLET — meningar × kort per mening — men aldrig på det gamla måttet för
    # KOSTNADEN. `per_kort` behandlade kortets nuvarande takt som evig och var
    # därför fel med en faktor fem till trettio; kostnadskurvan kommer numera
    # ur en FSRS-simulering. Reservvägen byter alltså bara enhet på målet, inte
    # på räkningen.
    from .arbetsborda import måltakt, nya_idag
    # DAGENS TAK SÄTTS EN GÅNG, ur läget vid dygnets början. Saldot rör sig
    # (via `infört_idag`), men taket gör det inte — annars är "dagens
    # tilldelning" inte ett tal utan en följd av hur fort man råkat svara.
    dygnsstart = dygnets_början(nu)
    mål_rep = måltakt(kort_db, språk, minuter_per_dag)
    if mål_rep is None and k:
        mål_rep = meningar_per_dag * k
    beslut = nya_idag(kort_db, språk, mål_rep_per_dag=mål_rep, nu=nu)
    # HÅLLBAR INFÖRSELTAKT, kort per dygn. Det är en TAKT och inte ett lager,
    # till skillnad från `upplåsningsläge["rum"]` som fortfarande räknar
    # "hur många kort till får plats". De två går inte att jämföra, och
    # namnet får därför inte vara detsamma. Se F1 i PROBLEM.md: efter B2 är
    # upplåsningens fråga malformulerad — "ryms N kort" har inget svar när
    # villkoret sitter på takten, medan "hur lång tid tar N kort i den här
    # takten" har det.
    # DAGENS TILLDELNING BESLUTAS EN GÅNG OCH SPARAS.
    #
    # Att bara räkna om den varje anrop gav en återkoppling där brådska
    # belönades: snabba svar sänkte sekunder-per-repetition, vilket höjde
    # målet, vilket släppte in fler kort. Mätt växte taket från 50 till 57
    # mitt under en genomgång, och "dagens tilldelning" var inte ett tal utan
    # en följd av hur fort man råkat svara.
    #
    # Ett första försök löste det genom att räkna takten på data FÖRE dygnets
    # början. Det var värre: en användare vars hela historik är från idag fick
    # ingen takt alls, och då blev taket hela den osedda högen — 836 kort på
    # en ny kurs. Måttet ska använda all historik; det är BESLUTET som ska
    # ligga stilla, inte underlaget.
    inflödestak = beslut["rum"]
    if inflödestak is not None:
        rad = kort_db.execute(
            "SELECT tak_datum, tak_kort FROM Kurs WHERE målspråk = ?",
            (språk,)).fetchone()
        idag = dygnsstart[:10]
        if rad and rad["tak_datum"] == idag and rad["tak_kort"] is not None:
            inflödestak = rad["tak_kort"]
        elif rad:
            kort_db.execute(
                "UPDATE Kurs SET tak_datum = ?, tak_kort = ? WHERE målspråk = ?",
                (idag, inflödestak, språk))
            kort_db.commit()
    takt = beslut["idag_tak"]

    # DE TVÅ TAKEN GÄLLER OLIKA PASS, och det är hela skillnaden mellan
    # dagens övning och extraövningen. Passlängden är ett tak på hur mycket
    # nytt som får plats IDAG; `rum` är ett tak på vad framtiden bär. Den som
    # klickar "träna extra" har uttryckligen valt bort det första — men aldrig
    # det andra, för det är inte en fråga om dagens ork utan om nästa månads.
    #
    # Oövad kurs: ingen mätning, alltså inget tak ur den. Passets egen längd
    # är då det enda som begränsar, och det är rätt — man kan inte räkna ut
    # någons inlärningskurva innan hen börjat.
    # Oövad kurs: ingen mätning, alltså inget tak ur den. Då finns ingenting
    # att räkna på och passets egen längd är det enda som begränsar — man kan
    # inte räkna ut någons inlärningskurva innan hen börjat.
    # DAGENS TAK ÄR TID, INTE ETT ANTAL. Att räkna om minuter till kort
    # kräver en växelkurs som inte finns dag ett — men att mäta hur lång tid
    # dagen HITTILLS tagit kräver ingen. Samma rörelse som B5 gjorde för
    # meningar: sluta räkna enheter, mät arbetet.
    #
    # Ett fast kallstartstal fanns här innan (först 40 kort, sedan 10) och
    # båda var samma sorts fel: en konstant som stod in för en mätning. Tio
    # ord tog några enstaka minuter av en tiominuterssättning — talet kunde
    # inte veta något om användaren.
    #
    # SJÄLVSTABILT PÅ KORT SIKT, vilket är skälet att det får styra: ett
    # nyinfört kort har `kurva[2] ≈ 1,0`, alltså kommer varje infört kort
    # tillbaka en gång två dygn senare. Fylls dagen till målet blir dag två
    # exakt målet. Räknat: 60 kort à 10 s = 10 min idag, 60 förfallna = 10 min
    # om två dygn.
    # SPÄRREN RÄKNAR INTE OM TID TILL KORT. Frestelsen är
    # `tid_kvar / sekunder_per_repetition`, och den är inte robust: en absurt
    # liten uppmätt takt tar bort spärren helt. Mätt i ett prov som svarade på
    # 20 ms per glosa blev taket 28 000 kort.
    #
    # Den robusta formen är INKREMENTELL. Frågan är inte "hur många ryms" utan
    # "finns det tid kvar" — ja eller nej. Inflödet sker i portioner, tiden
    # mäts efter varje, och felet kan aldrig bli större än en portion. Ingen
    # växelkurs behövs, och därmed kan ingen skakig växelkurs förstöra något.
    tid_kvar = minuter_per_dag * 60 - tid_idag(kort_db, språk, nu)
    tidstak = tidsspärr(tid_kvar, osedda)
    if inflödestak is None:
        inflödestak, takt = None, tidstak
    # TRE TAK, DET LÄGSTA GÄLLER: dagens tid, den hållbara takten, och lagret.
    tak = min(tidstak, takt if inflödestak is None else min(inflödestak, takt))
    # SALDO, INTE TAK: dagens kvot minus det som redan förts in idag.
    nya = max(0, min(osedda, tak - infört_idag))
    nya_extra = (osedda if inflödestak is None
                 else max(0, min(inflödestak - infört_idag, osedda)))
    # `oövade` RÄKNAS INTE SOM EGET ARBETE, och det var ett fel att göra det.
    # Skälet var riktigt — dagen tog slut direkt efter genomgången — men
    # orsaken låg någon annanstans: drillen åt hela tilldelningen, så inga
    # böjningskort blev kvar att införa i meningar. Med `nya_ord` löst är
    # `nya` positivt efter genomgången, och dagen fortsätter av sig själv.
    #
    # Att räkna dem här gjorde dessutom skada: kan ingen mening byggas kring
    # ett infört ord (B8) lovade hemskärmen arbete som generatorn inte kunde
    # leverera, och knappen sa "börja" på en dag som var slut.
    #
    # De gör fortfarande sitt arbete som MÅLORD — se `oövade_koncept`.
    oövade = oövade_idag(kort_db, språk, nu)
    finns_idag = förfallna + passkö + nya

    # `kvar_meningar` LÅG HÄR OCH ÄR BORTA (2026-08-26). Den räknade
    # `meningar_per_dag − gjort`, alltså hur många meningar som återstod av
    # ett tak B5 tog bort: dagen tar slut när KORTEN är gjorda, aldrig efter
    # N meningar. Ingen läste den. Samma sak med `belastning`, `per_kort`
    # och `kapacitet_kort` längre ner — noll läsare utanför den här filen.
    return {"språk": språk,
            "mål": meningar_per_dag, "gjort": gjort,
            "förfallna": förfallna, "igen": passkö, "nya": nya,
            "nya_extra": nya_extra, "tidiga": tidiga,
            "att_göra": finns_idag,
            # Vad de två knapparna har att ta av. Räknas här och inte i
            # generatorn, så att hemskärmens siffror och passets innehåll är
            # samma tal — en knapp som säger "0" och ett pass som ändå startar
            # är två åsikter om samma sak.
            "finns_idag": finns_idag,
            "finns_extra": förfallna + passkö + nya_extra + tidiga,
            "inflödestak": inflödestak, "osedda": osedda,
            "infört_idag": infört_idag,
            "tid_idag": round(minuter_per_dag * 60 - tid_kvar, 1),
            "tid_kvar": round(max(0, tid_kvar), 1),
            "tidstak": tidstak,
            # ANTALET ÄR OBESTÄMT när bara tidsspärren binder: inflödet sker
            # i portioner tills tiden är slut, och hur många det blir beror på
            # hur fort användaren arbetar. Att visa ett tal då vore att hitta
            # på ett. Gränssnittet ska visa TIDEN i stället.
            "nya_obestämt": inflödestak is None and tidstak > 0,
            # F4: ord som införts idag men ännu inte mötts i en mening.
            # Så länge de finns tas inget nytt in — se `Övningstjänst.glosor`.
            "oövade": oövade,
            # ORDENS ANDEL AV DAGENS TILLDELNING. Drillen inför ORDKORT,
            # meningarna inför böjningskorten — och de drar ur samma pott.
            # Tog drillen hela potten fanns inget kvar att införa i meningar,
            # och dagen tog slut direkt efter genomgången.
            #
            # Andelen är MÄTT och inte vald: ett koncept drar med sig 2,0
            # (ja) till 4,8 (de) kort, varav ett är ordkortet. Delas
            # tilldelningen med det talet blir resten kvar åt böjningen.
            # Räknas ur dagens HELA tilldelning minus de ord som redan
            # införts idag — inte ur det som återstår. Ur resten sjönk andelen
            # för varje ord man tog, så ett återbesök i lektionen gav alltid
            # "ett ord till", i all oändlighet. Det är samma fel som gjorde
            # `nya` till ett tak i stället för ett saldo.
            "nya_ord": max(0, min(
                nya,
                int(tak / max(1.0, _kort_per_koncept(kort_db, språk)))
                - ord_infört_idag)),
            "kostnad_per_läge": kostnad_per_läge(kort_db, språk),
            "kort_per_mening": k,
            "minuter_per_dag": minuter_per_dag,
            "sekunder_per_repetition": sekunder_per_repetition(kort_db, språk),
            # TVÅ VÄXELKURSER, MED OLIKA NÄMNARE OCH OLIKA UPPGIFTER.
            # `sekunder_per_repetition` (per bedömt kort) styr INFLÖDET — den
            # svarar på vad en repetition kostar, vilket är vad B2 räknar med.
            # `sekunder_per_rad` (per passrad) översätter `att_göra` till
            # MINUTER, eftersom `att_göra` räknar rader. Att använda den ena
            # där den andra hör hemma var felet bakom "about 1 min left" på
            # en dag som tog en och en halv.
            "sekunder_per_rad": sekunder_per_rad(kort_db, språk),
            "prognos": beslut["prognos"],
            "kostnad_per_kort": beslut["kostnad_per_kort"],
            # `klar` FINNS INTE HÄR LÄNGRE, och det är hela poängen med
            # passlagret hållet ut i praktiken.
            #
            # `dagsplan` räknade fram `förfallna == 0 and nya == 0 and
            # passkö == 0` — en HÄRLEDNING ur databasens nuläge. `Pass`
            # svarar på samma fråga med en RÄKNING: `klar` är att ingen rad
            # står som `väntar` (`pass_.läget`). Passlagrets egen text säger
            # att "det finns inget andra ställe som kan komma fram till något
            # annat", och så länge den här raden stod kvar var det inte sant.
            #
            # Att den var oskadlig i praktiken — `Övningstjänst._dagsplan`
            # slår ihop dem med passets tal SIST, så passet vann — gjorde
            # den inte ofarlig. Den var ett andra svar som väntade på en
            # anropare, och varje bugg passlagret byggdes mot var två svar
            # som inte var överens.
            #
            # DAGEN ÄR KLAR NÄR KORTEN ÄR GJORDA — inte efter N meningar.
            # FSRS bygger på att rätt kort repeteras i tid, så ett pass som
            # tar slut efter tjugo meningar med förfallna kort kvar bryter
            # mot precis det. Regeln står kvar; det är bara det andra stället
            # som räknade den som är borta.
            }


def kostnad(kort_db: sqlite3.Connection, språk_db: sqlite3.Connection, språk: str,
            nivå: int, cefr: str) -> dict:
    """Vad nivån `nivå` skulle kosta, utan att låsa upp den.

    Befolkningen är additiv och idempotent men skriver, så frågan ställs i en
    kopia av inlärardatabasen. Att fråga vad något kostar får inte vara att
    köpa det.

    `ryms` FANNS HÄR OCH ÄR BORTA. Det jämförde nivåns tillskott mot
    `upplåsningsläge["rum"]`, alltså mot den gamla `per_kort`-matten som B2
    mätte som 5–28× för hög. Frågan "ryms N kort" har dessutom inget svar
    när villkoret sitter på en takt (F1). Det som återstår är `nya_kort` —
    hur många kort nivån lägger till — och `byggbarhet`, som är den grind
    som faktiskt gäller.
    """
    import tempfile
    from pathlib import Path

    from .befolka import befolka
    from .db import anslut_kort

    läge = upplåsningsläge(kort_db, språk)
    with tempfile.TemporaryDirectory() as d:
        kopia = Path(d) / "prov.db"
        kort_db.commit()
        with sqlite3.connect(kopia) as mål:
            kort_db.backup(mål)
        prov = anslut_kort(kopia)
        # Ingen exponeringsmätning: frågan är hur många kort nivån
        # LÄGGER TILL, inte hur ofta de skulle mötas. Att mäta här vore
        # att betala 2 sekunder för ett svar som kastas.
        befolka(prov, språk_db, {språk}, nivå=nivå, cefr=cefr, mät=False)
        efter = upplåsningsläge(prov, språk)
        # BYGGBARHETEN MÄTS I KOPIAN, mot användarens FAKTISKA sedda kort.
        # Det är hela poängen: frågan är inte om nivån går att bygga i
        # allmänhet utan om den går att bygga för DEN HÄR användaren, nu.
        from ..generator import Generator
        g = Generator(språk_db, prov, språk, nivå=nivå, cefr=cefr, frö=0)
        # OCH DEN MÄTS PÅ NIVÅNS EGEN KONSTRUKTION. Utan `nivå=` räknas varje
        # byggbar mening, också de som inte innehåller det nivån handlar om —
        # och eftersom varje ny konstruktion är VALFRI bestod urvalet nästan
        # helt av meningar från nivån under. Grinden mätte alltså den nivå
        # användaren redan hade. Mätt: tjugo nivåer i följd efter en dag.
        byggbar = g.byggbarhet(nivå=nivå)
        prov.close()
    return {"nivå": nivå, "före": läge, "efter": efter,
            "nya_kort": efter["totalt"] - läge["totalt"],
            "byggbarhet": byggbar,
            # GRINDEN, och den enda. Samma villkor som knappen visas på och
            # som `lås_upp` prövar — ett tal, ett ställe.
            "redo": redo_för_nivå(byggbar, 800)}


def kö(kort_db: sqlite3.Connection, språk: str, antal: int = 20) -> list[sqlite3.Row]:
    """Dagens kort: förfallna först, sedan osedda om det finns plats."""
    s = Schemaläggare(kort_db)
    förfallna = s.förfallna(språk, antal)
    if len(förfallna) >= antal:
        return förfallna
    return förfallna + s.osedda(språk, antal - len(förfallna))


def spec_json(spec) -> str:
    """Meningsspecifikationen som text, för att kunna återskapa meningen."""
    from dataclasses import asdict, is_dataclass

    def rensa(v):
        if is_dataclass(v):
            return {k: rensa(x) for k, x in asdict(v).items() if x not in (None, (), False)}
        if isinstance(v, (list, tuple)):
            return [rensa(x) for x in v]
        return str(v) if hasattr(v, "value") else v

    return json.dumps(rensa(spec), ensure_ascii=False, sort_keys=True)
