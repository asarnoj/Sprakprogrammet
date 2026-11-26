"""Hur mycket nytt material dygnet tål — en STYRNING, inte en prognos.

Efter B4 och B5 i PROBLEM.md är det här den enda ratten för arbetsbörda som
finns kvar. Dagens arbete är de kort som förfallit, hela mängden, utan tak —
ett tak motsäger FSRS, som bygger på att rätt kort repeteras i tid. Blir
dygnet för tungt är svaret att föra in färre nya kort, aldrig att lämna
förfallna kort ogjorda.

VARFÖR STYRNING OCH INTE PROGNOS. En prognos över ett år ärver alla fel den
gör. En styrning som räknas om varje dag korrigerar dem. Därför fyra steg,
och bara det första behöver vara exakt:

    1.  I MORGON ÄR EXAKT KÄNT. Varje sett kort har ett `förfaller`-datum.
        Att räkna hur många som faller på varje kommande dag är en fråga,
        ingen modell.
    2.  SVANSEN SIMULERAS. Kort som prövas i morgon schemaläggs om, och vart
        de hamnar beror på betyget. Sannolikheten för fel är 1−R, som FSRS
        redan ger.
    3.  KOSTNADEN MÄTS I TID. Sekunder per repetition ur användarens egen
        logg — växelkursen mellan minuter och kort.
    4.  BESLUTET FATTAS OM VARJE DAG. Fel i steg 2 rättas i morgon i stället
        för att ackumuleras.

DET GAMLA MÅTTET VAR FEL MED EN FAKTOR FEM TILL TRETTIO. `per_kort` =
belastning / antal sedda behandlade kortets NUVARANDE takt som om den vore
evig — alltså påståendet "varje kort ses var 1,5:e dygn för alltid", när hela
poängen med FSRS är att intervallet växer. Simulerat med modellens egna
formler kostar ett kort 3,7 repetitioner den första månaden och 8,4 det
första året; det gamla måttet påstod 19 och 236.

ATT SLARVA FALLER UT AV SIG SJÄLVT. Uteblir ett pass ligger korten kvar OCH
blir mer försenade, så både antalet och svårigheten stiger. Steg 1 ser det
direkt, och steg 4 skär ned inflödet samma dag. Ingen särskild regel behövs.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import UTC, datetime, timedelta

from fsrs import Card, Rating

from .schemalaggning import (
    _skapa_schemaläggare, _till_card, sekunder_per_repetition,
)

#: TVÅ HORISONTER, OCH DE ÄR INTE SAMMA SAK. Att slå ihop dem var det första
#: felet i den här modulen, och det gav svar som var fel med en faktor fem.

#: Hur långt fram den BEFINTLIGA kortleken simuleras. En ren
#: tillförlitlighetsgräns: bortom ett par veckor beror varje kort på utfall
#: som ännu inte skett, och simuleringen säger då mer om slumptalen än om
#: användaren. Fjorton dygn är två veckor av användarens liv.
PROGNOSFÖNSTER_DYGN = 14

#: Hur länge ETT nytt korts kostnad räknas. Det här är HÄRLETT och inte valt.
#:
#: För man in k kort per dygn i evighet blir dygnets arbete `k × kum(D)` vid
#: dag D, där `kum` är kortets kumulativa repetitioner. En styrning som
#: dividerar med `kum(H)` sätter alltså k så att målet håller vid dag H — och
#: överskjuter med `kum(D)/kum(H)` längre fram. Räknat på kurvan:
#:
#:     H =   7 d   kum 2,21   överskjuter 3,8x vid ett år
#:     H =  14 d   kum 3,24   överskjuter 2,6x
#:     H =  30 d   kum 3,68   överskjuter 2,3x
#:     H =  90 d   kum 5,41   överskjuter 1,6x
#:     H = 365 d   kum 8,40   överskjuter 1,0x
#:
#: Frågan "hur lång ska horisonten vara" har alltså ett exakt svar så snart
#: man sagt över vilken tidsrymd användarens mål ska HÅLLA. Ska tjugo minuter
#: om dagen betyda tjugo minuter om ett år, är horisonten ett år.
#:
#: Kontroll åt andra hållet: 20 repetitioner/dygn är 7 300 om året, och ett
#: kort kostar 8,40 — alltså 869 kort om året, 2,4 om dagen. Det är den
#: ärliga takten, och den är långsammare än den känns.
#:
#: KVAR STÅR EN ÖVERSKJUTNING PÅ 1,3x VID TVÅ ÅR. Den försvinner inte med
#: någon horisont, eftersom kurvan växer logaritmiskt utan gräns — det är
#: samma sak som B2 fann: ett stadigt inflöde stannar aldrig.
KOSTNADSHORISONT_DYGN = 365

#: Hur många kort som simuleras när kostnadskurvan tas fram.
#:
#: MÄTT samplingsfel i kum(365), som spann över fem olika frön:
#:
#:      200 kort   0,33 s   9,7 %
#:      500 kort   0,89 s   8,7 %
#:    1 000 kort   1,80 s   4,0 %
#:    3 000 kort   5,34 s   3,0 %
#:
#: Konvergensen är långsam därför att felen är sällsynta och dyra — variansen
#: sitter i dem. Tusen är vald för att fyra procent på en divisor som ändå
#: trunkeras till heltal inte syns i svaret, medan fem sekunder i ett
#: webbanrop gör det. Värdet är dessutom DETERMINISTISKT: fröet är fast, så
#: samma dag ger samma svar.
SIMULERADE_KORT = 1000

_kurvor: dict[tuple[float, int], list[float]] = {}


def nykortskurva(retentionsmål: float,
                 dygn: int = KOSTNADSHORISONT_DYGN) -> list[float]:
    """Förväntade repetitioner dag 0..dygn från ETT kort som införs idag.

    Räknas fram genom att köra FSRS, inte genom en formel: korten införs,
    repeteras på förfallodagen, och fel dras med sannolikhet 1−R — alltså
    modellens egen förutsägelse. Inga antaganden utifrån.

    Talen är cachade per (retentionsmål, dygn). Kurvan beror bara på
    parametrarna och inte på användarens kortlek.
    """
    nyckel = (retentionsmål, dygn)
    if nyckel in _kurvor:
        return _kurvor[nyckel]
    s = _skapa_schemaläggare(retentionsmål, fuzza=False)
    rng = random.Random(0)                    # samma dag → samma svar
    per_dag = [0.0] * (dygn + 1)
    start = datetime(2000, 1, 1, tzinfo=UTC)
    for _ in range(SIMULERADE_KORT):
        c, _log = s.review_card(Card(), Rating.Good, start)
        per_dag[0] += 1                       # introduktionen kostar också
        while True:
            d = (c.due - start).days
            if d > dygn:
                break
            t = start + timedelta(days=d)
            R = s.get_card_retrievability(c, current_datetime=t)
            c, _log = s.review_card(
                c, Rating.Good if rng.random() < R else Rating.Again, t)
            per_dag[d] += 1
    _kurvor[nyckel] = [x / SIMULERADE_KORT for x in per_dag]
    return _kurvor[nyckel]


def prognos(kort_db: sqlite3.Connection, språk: str, *,
            dygn: int = PROGNOSFÖNSTER_DYGN,
            nu: datetime | None = None) -> list[float]:
    """Repetitioner per dygn de närmaste `dygn` dagarna, från KORTLEKEN som den är.

    Dag 0 är exakt: de kort som redan förfallit plus de som förfaller idag.
    Därefter rullas varje kort framåt med FSRS — vid varje förfallodag prövas
    det, faller med sannolikhet 1−R, och schemaläggs om. Det är svansen i
    steg 2, och den är näst intill hela skillnaden mot att bara räkna
    `förfaller`-datum: ett kort som prövas idag med intervall två dygn är
    tillbaka inom fönstret, ett med intervall fyrtio är det inte.

    Osedda kort räknas INTE med. De kostar ingenting förrän de införs, och
    införseltakten är just det den här modulen ska bestämma.
    """
    nu = nu or datetime.now(UTC)
    s = _skapa_schemaläggare(fuzza=False)
    rng = random.Random(1)
    per_dag = [0.0] * (dygn + 1)
    rader = kort_db.execute(
        """SELECT * FROM Kort
           WHERE språk = ? AND schemalagt = 1 AND sedd IS NOT NULL
             AND förfaller IS NOT NULL""", (språk,)).fetchall()
    slut = nu + timedelta(days=dygn)
    for rad in rader:
        c = _till_card(rad)
        while c.due <= slut:
            # Ett kort som redan är försenat prövas IDAG, inte på sitt gamla
            # datum — annars skulle förseningen räknas som arbete i det
            # förflutna i stället för som arbete som väntar.
            t = max(c.due, nu)
            d = (t - nu).days
            if d > dygn:
                break
            per_dag[d] += 1
            R = s.get_card_retrievability(c, current_datetime=t)
            c, _log = s.review_card(
                c, Rating.Good if rng.random() < R else Rating.Again, t)
    return per_dag


def måltakt(kort_db: sqlite3.Connection, språk: str,
            minuter_per_dag: float, *, före: str | None = None) -> float | None:
    """Hur många repetitioner per dygn användarens minuter räcker till.

    Växelkursen är `sekunder_per_repetition`, mätt ur den egna loggen. Utan
    den finns ingen väg från minuter till kort, och då svarar funktionen None
    i stället för att gissa — samma regel som resten av systemet.
    """
    sek = sekunder_per_repetition(kort_db, språk, före=före)
    if not sek:
        return None
    return minuter_per_dag * 60 / sek


def nya_idag(kort_db: sqlite3.Connection, språk: str, *,
             mål_rep_per_dag: float | None,
             fönster: int = PROGNOSFÖNSTER_DYGN,
             kostnadshorisont: int = KOSTNADSHORISONT_DYGN,
             nu: datetime | None = None) -> dict:
    """Hur många nya kort som får införas idag. Steg 4.

    TVÅ VILLKOR, OCH DET LÄGSTA GÄLLER. Ett enda räcker inte, och båda felen
    syns i siffrorna.

        I LÄNGDEN   medel(prognos) + k × kostnad_per_kort ≤ mål

            `kostnad_per_kort` är repetitionerna ett kort drar över
            KOSTNADSHORISONTEN, alltså 8,40 på ett år. Läsningen är
            "om jag för in k kort om dagen i evighet, vad blir dygnets arbete
            när kortleken mognat" — och det är den läsningen som gäller,
            eftersom beslutet fattas varje dag och inflödet därför ÄR
            stadigt.

            Att i stället dela med kostnaden över prognosfönstret var det
            första felet här: det svarade på "vad kostar EN dags införsel de
            närmaste två veckorna", vilket är en annan och mycket mindre
            fråga. Skillnaden var en faktor fem.

        IDAG        prognos[0] + k × kurva[0] ≤ mål

            Kurvans första dygn är en ETTA — introduktionen kostar en
            repetition på en gång. Utan det här villkoret hade en tunn dag
            släppt in en klump: mätt på tyskans läge gav långtidsvillkoret
            ensamt 73 nya kort samma dag, ovanpå 34 förfallna.

    SENARE DYGN FÅR VARA TUNGA UTAN ATT BLOCKERA. Att kräva att varje dygn i
    fönstret ryms vore för hårt — en enda tung dag om två veckor skulle strypa
    inflödet idag. Blir den dagen verkligen tung syns det i den dagens egen
    beräkning. Det är skillnaden mellan en styrning och en prognos.

    `mål_rep_per_dag = None` betyder att växelkursen minuter → kort ännu inte
    är mätt. Anroparen får då välja ett annat mått — se `dagsplan`.
    """
    p = prognos(kort_db, språk, dygn=fönster, nu=nu)
    kurva = nykortskurva(_skapa_schemaläggare().desired_retention,
                         kostnadshorisont)
    medel = sum(p) / len(p)
    kostnad_per_kort = sum(kurva)
    if mål_rep_per_dag is None or kostnad_per_kort <= 0 or kurva[0] <= 0:
        i_längden = idag = nya = None
    else:
        i_längden = (mål_rep_per_dag - medel) / kostnad_per_kort
        idag = (mål_rep_per_dag - p[0]) / kurva[0]
        nya = max(0, int(min(i_längden, idag)))
    return {"mål": mål_rep_per_dag, "medel": medel, "idag_belastning": p[0],
            "kostnad_per_kort": kostnad_per_kort, "kostnad_idag": kurva[0],
            # `i_längden` ÄR det gamla `rum`, fast räknat rätt: hur många kort
            # till som ryms när kortleken mognat. Taket för idag är en annan
            # fråga — takt, inte lager — och de skiljs därför åt här i stället
            # för att blandas ihop av anroparen.
            "rum": None if i_längden is None else max(0, int(i_längden)),
            "idag_tak": None if idag is None else max(0, int(idag)),
            "nya": nya, "prognos": p}
