"""Meningsgeneratorn — löser fram en mening ur repetitionskön.

Premissen ur GENERATOR.md: meningar författas inte, de löses fram. Systemet
ser vilka kort som är förfallna och konstruerar en mening som tränar dem,
blandat med ord användaren redan kan.

Sökningen är sampla-och-poängsätt. Att välja verb, mönster, fyllnad och alla
grammatiska parametrar så att budgeten träffas, förfallna kort täcks och
restriktionerna hålls är i allmänhet NP-svårt — men genomströmningen gör det
ointressant: 41 000 kandidater i sekunden mätt, så tusen kandidater kostar
tre hundradelar och den bästa av dem är gott nog. Skillnaden mellan bästa och
näst bästa mening är omätbar för användaren.

Kedjan per mening:

    kön          förfallna kort, svagast först
    samplaren    kandidater byggda RUNT målorden, giltiga från början
    renderaren   texten, och beroendekartan som säger vilka kort den rörde
    poängen      sex termer, budget och koncentration bland dem
    valet        bästa kandidaten, eller den minst dåliga

Sista ledet är viktigt: sökningen misslyckas aldrig. Finns ingen bra mening
tas den minst dåliga, och det förfallna kort som inte gick att bygga kring
skjuts upp till nästa gång — GENERATOR.md, "täckande med reservutgång".
"""

from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass, replace

from ..kort import Schemaläggare, spec_json
from ..rendering import RENDERARE, Mening, RenderingsFel, Uppslag, Validator
from .poang import Poäng, Poängsättare
from .rattning import Anmärkning, Rättare, Rättning
from .urval import Ordförråd, Samplare, använder_nivån


@dataclass(frozen=True, slots=True)
class Förslag:
    mening: Mening
    #: Meningen på MÅLSPRÅKET — facit.
    text: str
    #: Samma mening på KÄLLSPRÅKET — uppgiften användaren ser. None när
    #: kursen saknar källspråk, alltså när systemet provas utan uppgift.
    uppgift: str | None = None
    kort: list = None
    poäng: Poäng = None
    #: (koncept, variant, cell) i den ordning formerna slogs upp. Rättningen
    #: behöver den för att veta vilket ord i facit som kom varifrån.
    uppslag: list = None
    #: (koncept, egenskapsnamn) — de lexikala egenskaper som VALDE cellerna.
    #: Rättningen behöver dem för att kunna skylla ett artikelfel på
    #: substantivets genus i stället för på artikelformen.
    egenskaper: list = None
    #: (verbkoncept, slot, egenskapsnamn) — vad VERBET krävde av sina slots.
    #: Genus hör till substantivet, rektionen till verbet, och rättningen
    #: behöver båda för att kunna skilja "fel artikelform" från "rätt form,
    #: fel kasus".
    rektioner: list = None
    #: Vilka ORDFÖLJDSREGLER renderaren tillämpade. Regeln är kod och inte
    #: data, så det enda som går att observera är att den tillämpades.
    ordföljder: list = None
    #: Meningen är en ORDAGRANN UPPREPNING som togs för att sökningen inte
    #: hade något annat. Flaggan finns för att skillnaden ska gå att SE:
    #: en upprepning som var enda utvägen är något helt annat än en som
    #: slapp igenom, och utan flaggan går de inte att skilja på i efterhand.
    nödfall: bool = False
    #: Sökningen fick SLÄPPA begränsningen till kända ord för att hitta något
    #: alls (C5:s reservutgång). Ett ord meningen inför kommer då därifrån och
    #: inte ur en läcka — och utan flaggan går de två inte att skilja åt.
    reserv_släppt: bool = False
    #: Renderarens ord FÖRE sandhi. Rättningen diffar mot dem, så att en
    #: sammansmältning inte döljer en tokengräns — `je` + `existe` blir
    #: `j'existe`, och utan listan gick böjningsfelet i `exister` inte att se.
    osammansmält: list = None


class Generator:
    def __init__(self, språk_db: sqlite3.Connection, kort_db: sqlite3.Connection,
                 språk: str, *, källspråk: str | None = None,
                 nivå: int = 21, cefr: str = "C2",
                 budget: float = 1.5, frö: int | None = None) -> None:
        self.språk = språk
        self.källspråk = källspråk
        self.språk_db = språk_db
        self.kort_db = kort_db
        self.rng = random.Random(frö)
        self.renderare = RENDERARE[språk](språk_db)
        # UPPGIFTEN ÄR SAMMA SPEC PÅ ETT ANNAT SPRÅK. Det är hela skälet till
        # att `Mening` är språkoberoende: frågan och svaret är inte två texter
        # som råkar höra ihop utan en enda specifikation, renderad två gånger.
        # Utan den här renderaren finns ingen uppgift att ställa, bara ett
        # facit att visa.
        self.källrenderare = RENDERARE[källspråk](språk_db) if källspråk else None
        self.validator = Validator(språk_db)
        self.schemaläggare = Schemaläggare(kort_db)
        self.poängsättare = Poängsättare(kort_db, self.schemaläggare, budget)
        self.samplare = Samplare(
            Ordförråd(språk_db, språk, cefr), nivå, self.rng)
        # PASSKÖN — kort som fallerat under det HÄR passet och ännu inte
        # tagits igen. Den finns för att FSRS inte kan ge återförsök samma
        # dag: minsta intervall är ett dygn, och utan relearning-steg
        # schemaläggs ett fallerat kort i morgon. Att gå ifrån ett fel utan
        # att någon gång ha fått rätt är dålig pedagogik, och det var aldrig
        # meningen — designen säger att kortet ska komma tillbaka "i en
        # ANNAN mening", vilket är precis vad den här kön åstadkommer.
        #
        # Den rör INTE schemaläggningen. FSRS behåller sin bedömning; kortet
        # är förfallet i morgon oavsett. Återförsöket blir en tidig
        # repetition, vilket FSRS hanterar med en mindre stabilitetsökning —
        # samma spacing-regel som gäller alla oavsiktliga repetitioner.
        #
        # Den är per PASS och inte per dag, och lever därför i minnet. Ett
        # avbrutet pass ska inte lämna en skuld i databasen.
        self._passkö: set[int] = set()
        #: De senast STÄLLDA meningarnas text. Passkön ger målordet, och med
        #: ett litet ordförråd finns ofta bara en mening som innehåller det —
        #: mätt gav ett återförsök `Vi åker.` åtta gånger i rad. B7 säger att
        #: kortet ska tillbaka i en ANNAN mening, just för att se samma sak om
        #: och om igen är det som gör att man fastnar.
        self._förra_texter: list[str] = []
        self._karta = self._läs_karta()
        self._kort: dict[int, sqlite3.Row] = {}
        self._läs_kort()
        # Ordkortet hänger på KONCEPTET och inte på cellen, så det ligger
        # inte i Cellkort. Att glömma det gjorde att varje mening
        # attribuerade noll ordkort — det mest grundläggande av alla.
        self.rättare = Rättare(språk_db, kort_db, språk)
        self._ordkort: dict[tuple, int] = {
            (r["koncept"], r["variant"]): r["id"]
            for r in self._kort.values() if r["typ"] == "ord"}
        # (koncept, egenskap) → kort. Genus och böjningsklass hänger på
        # konceptet precis som ordkortet, inte på en cell, och ligger därför
        # inte heller i Cellkort.
        self._egenskapskort: dict[tuple, int] = {
            (r["koncept"], r["egenskap"]): r["id"]
            for r in self._kort.values() if r["typ"] == "egenskap"}
        # (verbkoncept, slot, egenskap) → kort. Rektionen hänger på VERBET
        # och den slot det styr, inte på det uppslagna ordet.
        self._rektionskort: dict[tuple, int] = {
            (r["koncept"], r["cell"], r["egenskap"]): r["id"]
            for r in self._kort.values() if r["typ"] == "rektion"}
        # regelnamn → kort. Ordföljden hör varken till ett ord eller en cell,
        # bara till språket, så nyckeln är regeln själv.
        self._ordföljdskort: dict[str, int] = {
            r["egenskap"]: r["id"]
            for r in self._kort.values() if r["typ"] == "ordföljd"}

    def _läs_kort(self) -> None:
        """Läs om kortbeståndet. EN GÅNG PER MENING, inte per kandidat.

        Raderna bär FSRS-tillståndet, och poängsättaren läser `sedd` och
        `stabilitet` ur dem för varje kandidat den väger. Lästes de bara vid
        konstruktionen — vilket de gjorde — såg poängsättaren hela passet
        igenom det läge som rådde när passet BÖRJADE: ett kort som
        introducerats för tre meningar sedan räknades fortfarande som osett,
        och dess R som noll.

        Felet växer med passets längd och syns inte i något felmeddelande.
        Det slår mot både budgeten (Σ(1−R) över fel kort) och nykvoten (som
        ska hindra att samma nya kort trycks in om och om igen), och därmed
        mot precis det dagsplanen finns till för att hålla jämnt.

        Omläsningen kostar 3 ms mot meningens 200. Att i stället uppdatera de
        rörda raderna vore snabbare och en kopia av databasen — det finns
        redan ett ställe som vet vad ett kort är värt, och det är kortraden.
        """
        self._kort = {r["id"]: r for r in self.kort_db.execute(
            "SELECT * FROM Kort WHERE språk = ?", (self.språk,))}

    def _sedda_koncept(self) -> set[str]:
        """Koncepten användaren redan mött, ur det nyss omlästa beståndet."""
        return {r["koncept"] for r in self._kort.values()
                if r["sedd"] is not None and r["koncept"]}

    def _läs_karta(self) -> dict:
        karta: dict = {}
        for r in self.kort_db.execute(
                """SELECT språk, koncept, variant, cell, kort_id
                   FROM Cellkort WHERE språk = ?""", (self.språk,)):
            karta.setdefault(
                (r["koncept"], r["variant"], r["cell"]), []).append(r["kort_id"])
        return karta

    # ── rendering med beroendekarta ──────────────────────────────────

    def _rendera(self, m: Mening) -> tuple[str, list, list, list] | None:
        """Texten och de kort meningen rörde, eller None om den inte går.

        Instrumenteringen är samma väg som nåbarhetsmätningen använder, och
        det är hela skälet att renderarna måste hämta former genom
        `Uppslag.form` — en form som hämtas förbi den går inte att knyta
        till ett kort.
        """
        rörda: list = []
        egenskaper: list = []
        rektioner: list = []
        ordföljder: list = []
        original = Uppslag.form
        original_egenskap = Uppslag.egenskap
        original_rektion = Uppslag.rektion
        original_ordföljd = Uppslag.ordföljd

        def logga(själv, lexem, cell):
            rörda.append((lexem["nyckel"], lexem["variant"], cell))
            return original(själv, lexem, cell)

        # Samma instrumentering, men för det som VÄLJER cellen i stället för
        # det som står i den. Genus är inget cellvärde — `das` slogs upp i
        # `n_nom` därför att Kind är neutrum — och utan den här loggen var
        # genuskorten oåtkomliga: 428 av tyskans 1 112, den största
        # korttypen, med noll kopplingar och noll prövningar.
        def logga_egenskap(själv, lexem, namn):
            egenskaper.append((lexem["nyckel"], namn))
            return original_egenskap(själv, lexem, namn)

        # TREDJE LOGGEN, för det VERBET kräver av sin slot. Genus hör till
        # substantivet och fångas ovan; rektionen hör till verbet — `helfen`
        # tar dativ — och var därmed osynlig för båda de andra. Sex tyska och
        # två franska rektionskort stod schemalagda utan någon väg (A3).
        def logga_rektion(själv, koncept, slot, namn, värde):
            rektioner.append((koncept, slot, namn))
            return original_rektion(själv, koncept, slot, namn, värde)

        # FJÄRDE LOGGEN, för renderarens egen STRUKTUR. Ordföljden står inte
        # i något lexem och i ingen cell — den är kod — så varken formloggen
        # eller de två andra kunde se den. Sexton ordföljdskort över fyra
        # språk stod schemalagda utan väg (A3).
        def logga_ordföljd(själv, regel):
            ordföljder.append(regel)
            return original_ordföljd(själv, regel)

        Uppslag.form = logga
        Uppslag.egenskap = logga_egenskap
        Uppslag.rektion = logga_rektion
        Uppslag.ordföljd = logga_ordföljd
        try:
            text = self.renderare.rendera(m)
        except (RenderingsFel, KeyError, ValueError):
            return None
        finally:
            Uppslag.form = original
            Uppslag.egenskap = original_egenskap
            Uppslag.rektion = original_rektion
            Uppslag.ordföljd = original_ordföljd

        idn: set[int] = set()
        for nyckel in rörda:
            idn.update(self._karta.get(nyckel, ()))
        for koncept, variant, _ in rörda:
            kid = self._ordkort.get((koncept, variant))
            if kid is not None:
                idn.add(kid)
        for koncept, namn in egenskaper:
            kid = self._egenskapskort.get((koncept, namn))
            if kid is not None:
                idn.add(kid)
        for koncept, slot, namn in rektioner:
            kid = self._rektionskort.get((koncept, slot, namn))
            if kid is not None:
                idn.add(kid)
        for regel in ordföljder:
            kid = self._ordföljdskort.get(regel)
            if kid is not None:
                idn.add(kid)
        kort = [self._kort[i] for i in idn if i in self._kort]
        # ORDEN FÖRE SANDHI, hämtade direkt efter renderingen. Rättningen
        # diffar mot dem i stället för mot den färdiga texten — se
        # `Rättare._ordvis`. `getattr` för att en renderare utan sandhi inte
        # behöver bry sig.
        return (text, kort, rörda, egenskaper, rektioner, ordföljder,
                list(getattr(self.renderare, "osammansmält", []) or []))

    # ── generering ───────────────────────────────────────────────────

    def föreslå(self, *, kandidater: int = 1000, kölängd: int = 30,
                nya_tillåtna: int | None = None, extra: bool = False,
                oövade: list | None = None,
                passkö: set[int] | None = None,
                nya: set[int] | None = None,
                nu=None) -> Förslag | None:
        """Bästa meningen av `kandidater` försök.

        `nya_tillåtna` är dagsplanens tak på hur många OSEDDA kort som får
        stå i kön. Det är taket för dagen och inte för meningen — det senare
        är poängsättarens NYKVOT — och det räknas om inför varje mening,
        eftersom ett kort som just introducerats redan har ätit sin plats i
        belastningen. None betyder inget tak, vilket gäller den oövade kursen:
        utan mätning finns ingen kapacitetsmodell att begränsa med.

        `extra` är övningen utöver dagens. Där fylls kön på med kort som ännu
        INTE förfallit, det som förfaller först först, så att passet blir
        tidiga repetitioner i stället för tomgång.
        """
        self._läs_kort()
        # SILAS HÄR, EN GÅNG, så att kön och målorden inte kan säga olika.
        # Ett oövat ord som inte går att bygga en mening kring lades ändå i
        # kön, och räknades då som TÄCKT av varje mening — vilket höll
        # `täckta` över noll för alltid och stängde av passets nödutgång.
        # Mätt på engelskan: `a` låg kvar som oövat, varje mening "täckte"
        # det, och dagen tog aldrig slut trots att de fyra kvarvarande korten
        # var onåbara.
        oövade = self.övningsbara(list(oövade or [])) or None
        kö = self.schemaläggare.förfallna(self.språk, kölängd, nu)
        if extra and len(kö) < kölängd:
            kö += self.schemaläggare.kommande(self.språk, kölängd - len(kö), nu)
        # Nya kort fyller på det som är kvar av kölängden, upp till dagens tak.
        # Tidigare kom de in bara när det förfallna var HELT slut, vilket gav
        # dem två lägen och inget mellan: allt eller ingenting. Nu blandas de
        # in medan det förfallna finns kvar, vilket är vad ett pass av jämn
        # längd kräver — och taket är det som hindrar att de tar över.
        plats = kölängd - len(kö)
        if nya_tillåtna is not None:
            plats = min(plats, nya_tillåtna)
        if plats > 0:
            # OSEDDA ORDKORT HÖR INTE HIT. Ett ordkort frågar om ordet finns
            # och vad det betyder — en glosa — och den frågan går inte att
            # besvara ur en mening man inte kan läsa. De introduceras i
            # glosläget (`Övningstjänst.glosor`) och kommer hit först när de
            # är sedda. Böjningskorten — stam, ändelse, genus — hör däremot
            # hemma i en mening och introduceras som förut.
            #
            # PASSETS EGNA NYA KORT GÅR FÖRE, när anroparen har ett pass.
            #
            # DE TVÅ KÖERNA VAR HELT DISJUNKTA, och det var det allvarligaste
            # felet i den här kedjan. Passet väljer dagens nya kort och silar
            # dem genom `nåbara_kort` — bara kort någon byggbar mening kan
            # röra kommer med (`pass_._rader`). Generatorn frågade i stället
            # `osedda` på nytt, som svarar med de HÖGST RANKADE osedda korten
            # oavsett nåbarhet. Mätt på en färsk franskkurs, varv för varv:
            #
            #     passet väntar på 9 nya kort, generatorn köar 9
            #     gemensamma 0 · bara i passet 9 · bara i generatorn 9
            #
            # Noll överlapp, varje varv. Generatorn byggde alltså meningar
            # mot kort som per konstruktion INTE gick att nå, medan de kort
            # dagen faktiskt planerat aldrig blev målord. När de oövade orden
            # tagit slut föll `täckta` till noll, nödutgången löste ut, och
            # passets kort skrevs av som "onåbara" — trots att meningarna som
            # når dem aldrig hade ställts:
            #
            #     K0 pres_1pl  `Nous existons.`   (visad var `Nous avons.`)
            #     K1 pres_2sg  `Tu as.`           (visad var `Tu existes.`)
            #
            # Det är G6:s felklass: `dagsplan`/`Pass` är auktoriteten på vad
            # dagen innehåller, och en ändpunkt räknade fram sitt eget svar.
            # Passets rader går före; `osedda` fyller bara på om det behövs,
            # och det behövs bara för anropare UTAN pass — proven och
            # mätverktygen.
            if nya is not None:
                planerade = [self._kort[i] for i in nya if i in self._kort]
                kö += planerade[:plats]
                plats -= len(planerade[:plats])
            if plats > 0:
                kö += [k for k in self.schemaläggare.osedda(
                           self.språk, plats, uteslut=("ord",))
                       if k["id"] not in {x["id"] for x in kö}]
        # Passkön läggs FÖRST och räknas som täckt, så att poängfunktionen
        # aktivt bygger meningen runt det som nyss gick fel.
        # PASSKÖN KOMMER UTIFRÅN när anroparen har ett PASS. Kön är ett
        # faktum om dagen — vilka kort som fallerat och ännu inte tagits igen
        # — och ett faktum hör hemma i `Passkort`, inte i ett lexikon som dör
        # med processen. `self._passkö` står kvar för anropare utan pass
        # (proven, mätverktygen), och de två kan inte gå isär eftersom bara
        # en av dem används i taget.
        kö_ider = self._passkö if passkö is None else passkö
        igen = [self._kort[i] for i in kö_ider if i in self._kort]
        kö = igen + [k for k in kö if k["id"] not in kö_ider]
        # OCH DE OÖVADE ORDEN LÄGGS I KÖN, av samma skäl. Att bara ge dem som
        # MÅLORD räckte inte: målordet styr vad samplaren bygger kring, men
        # poängen avgör vilken kandidat som vinner — och ett ord som inte står
        # i kön bidrar noll till täckningen. Mätt gav det fjorton meningar i
        # rad om osedda substantiv, som täckte mer, medan de drillade orden
        # låg orörda.
        #
        # De är varken förfallna eller osedda: ett ord som infördes i
        # glosläget är SETT och ligger två dygn bort. Kön är alltså inte bara
        # FSRS kö längre, utan dagens arbete — och det är den ärligare
        # definitionen, eftersom B5 säger att dagen är slut när arbetet är
        # gjort.
        if oövade:
            i_kö = {k["id"] for k in kö}
            kö = [k for k in self._kort.values()
                  if k["typ"] == "ord" and k["koncept"] in set(oövade)
                  and k["id"] not in i_kö] + kö
        if not kö and not oövade:
            return None
        förfallna = {k["id"] for k in kö}
        # PASSKÖN FÅR MÅLORDET SÅ LÄNGE DEN HAR NÅGOT. Att bara lägga den
        # först i kön räckte inte: `kring` lottas per kandidat ur HELA kön, så
        # tre återförsök bland trettio köade kort blev målord i en tiondel av
        # fallen. Mätt i extraläget — där kön fylls på med kommande kort —
        # rördes de i 1 mening av 30 och kön tömdes aldrig.
        #
        # Prioriteringen är inte en avvägning utan en följd av vad kön ÄR: ett
        # fallerat kort är det enda i passet med en deadline idag. Allt annat
        # är redan schemalagt av FSRS och kommer tillbaka i morgon av sig
        # självt; det som gick fel nyss gör det inte, för utan inlärningssteg
        # är minsta intervall ett dygn. Därför går målordet dit först.
        igen_mål = [k["koncept"] for k in igen if k["koncept"]]
        # NYINFÖRDA ORD SOM ÄNNU INTE ÖVATS är också målord, och de kommer
        # inte ur kön: ett ord som infördes i glosläget är SETT och ligger två
        # dygn bort, alltså varken förfallet eller osett. Utan det här ledet
        # stängde ordningsregeln (F4) drillen utan att ge något i stället —
        # mätt gav generatorn fjorton meningar i rad om osedda substantiv
        # medan de tio drillade orden låg orörda.
        #
        # Ordningen är passkön först (deadline idag), sedan de oövade (dagens
        # andra halva), sedan kön.
        #
        # VARJE NIVÅ SILAS GENOM `duger_som_mål`. Ett koncept samplaren inte
        # kan bygga KRING ignoreras tyst av `kandidat` — den tar ett slumpvis
        # verb i stället — och eftersom nivåerna ERSÄTTER varandra räckte ett
        # enda sådant koncept för att slå ut hela målstyrningen. `un` gjorde
        # precis det: drillat som ord, därmed "infört men inte övat", först i
        # listan, och omöjligt att bygga en mening kring. Resultatet var fyra
        # meningar i rundgång med täckning noll, 330 gånger.
        #
        # Silen gör inte att ordet aldrig övas — `un` kommer med i varje
        # nominalfras som tar obestämd artikel. Den säger bara att det inte
        # går att STYRA mot, och därför inte får hålla styrningen gisslan.
        # ETT ÄNDELSEKORT KAN INTE BLI MÅLORD, och det är en känd gräns och
        # inte en glömska. `koncept` är NULL på `system`- och `ordföljd`-kort
        # — ändelsen delas av en hel böjningsklass — så det finns inget ord
        # att bygga KRING. De hittas i stället av poängfunktionen, som räknar
        # dem som täckta när en mening råkar röra dem.
        #
        # En omväg via `Cellkort` (som vet vilka ord som rör en viss ändelse)
        # byggdes och MÄTTES 2026-08-26: noll skillnad i avskrivna kort och
        # noll skillnad i antal meningar per dag, på franska nivå 1, tyska
        # nivå 4 och engelska nivå 1. Den togs bort igen — en mekanism som
        # inte går att visa någon verkan av är en skuld och inte en tillgång.
        # Se A7 i PROBLEM.md.
        sedda = self._sedda_koncept()
        nivåer = [igen_mål, list(oövade or []),
                  [k["koncept"] for k in kö if k["koncept"]]]
        mål = next((d for d in ([k for k in n if self.samplare.duger_som_mål(k)]
                                for n in nivåer) if d), [None])
        # FYLLNADEN HÅLLS TILL DET ANVÄNDAREN MÖTT. Ett kort som inte
        # står i "nytt idag" får inte dyka upp i en mening — då är dagsplanen
        # inte ett tak utan en beskrivning av något annat.
        #
        # Spärren fanns men SLÄPPTES ovillkorligt här (`begränsa(None)`), och
        # då är den verkningslös: målordet väljs ur kön, men resten av
        # meningens ord väljs fritt, och varje osett ord som råkar hamna i en
        # mening blir sett, betygsatt och infört. Mätt när spärren infördes:
        # sextio meningar med taket satt till NOLL nya kort införde ändå 35.
        #
        # Den släpptes en gång av ett riktigt skäl: med tio inlärda ord fanns
        # inget att variera med och samma mening kom fyra gånger i rad. Det
        # skälet är borta — `_förra_texter` avvisar numera ordagranna
        # upprepningar, och glosläget ser till att ordförrådet växer innan
        # meningarna behöver det.
        #
        # RESERVEN ÄR KVAR. Går ingen mening att bygga ur det kända vinner
        # reservkandidaten ändå, för sökningen får aldrig misslyckas. Men det
        # är då ett UNDANTAG som syns, inte den vanliga vägen.
        #
        # (`sedda` räknades fram redan ovan, för målstyrningen.)
        self.samplare.begränsa(sedda)

        # TVÅ BÄSTA: den som klarar okändgränsen, och den bästa oavsett.
        # Sökningen får aldrig misslyckas (GENERATOR.md, "täckande med
        # reservutgång"), och gränsen på okända ord är en PREFERENS med
        # reserv — inte ett villkor som kan tömma sökningen. Som hårt filter
        # gav den `None` med jämna mellanrum: engelskan tog slut efter en
        # mening när ingen av 200 kandidater råkade hålla sig under gränsen.
        bäst, reserv, nödfall = self._sök(kandidater, mål, förfallna, sedda, nu)

        # RESERVUTGÅNGEN, på hela sökningens nivå. Gick ingen mening att bygga
        # ur det användaren mött släpps begränsningen och sökningen görs om.
        # Vid kallstart är nästan allt osett, och då MÅSTE passet fungera —
        # men undantaget är då ett beslut om hela meningen, inte ett ord som
        # smugit in i en slot.
        #
        # NÖDFALLET RÄKNAS SOM EN TRÄFF HÄR, och det var felet när tiern
        # infördes. Villkoret prövade bara `bäst` och `reserv`, så när ALLA
        # rena kandidater råkade vara upprepningar — vilket de blir så snart
        # ordförrådet är mindre än minnet är djupt — såg sökningen tom ut och
        # begränsningen släpptes. Mätt i drift: fyra ord drillade, och
        # `Tu existes.` införde `tu` som ingen introducerat.
        #
        # En ordagrann upprepning är sämre pedagogik men ÄRLIG. Att i stället
        # ta in ett oanmält ord bryter mot både C5 och dagsplanens tak, och
        # ger dessutom en uppgift som inte går att lösa. Upprepningen vinner
        # alltså över undantaget, och undantaget är kvar för det läge det
        # byggdes för: när ingenting alls gick att bygga.
        släppt = False
        if bäst is None and reserv is None and nödfall is None:
            self.samplare.begränsa(None)
            bäst, reserv, nödfall = self._sök(
                kandidater, mål, förfallna, sedda, nu)
            # OCH DET SYNS ATT DEN TOGS. C5 kallar reserven "ett UNDANTAG som
            # syns, inte den vanliga vägen" — men den syntes ingenstans, och
            # då går den inte att skilja från en läcka.
            #
            # Skillnaden är inte akademisk. Ett ord som kommer in via reserven
            # gör det för att INGEN mening kunde byggas ur det användaren
            # mött; ett ord som kommer in på något annat sätt är en bugg av
            # det slag C5 stängde tre gånger. `introduktionsprov` mätte de två
            # som samma sak och rapporterade fel: när kortbeståndet råkade ge
            # drillen tre modalverb — oanvändbara innan nivå 13 låser upp
            # komplement — kunde ingen mening byggas, reserven löste ut, och
            # provet kallade det en läcka.
            släppt = True

        # FANNS INGEN ANNAN MENING MED MÅLORDET skjuts återförsöket upp i
        # stället för att upprepas. Kortet står kvar i passkön och kommer när
        # ordförrådet räcker till en annan mening; att servera samma mening
        # igen vore att låtsas att en repetition skedde. Mätt före den här
        # regeln: `Vi åker.` åtta gånger i rad, med samma två kort fällda
        # varje gång.
        if bäst is None and igen_mål:
            övriga = [k["koncept"] for k in kö if k["koncept"]
                      and k["koncept"] not in igen_mål]
            if övriga:
                bäst, reserv2, nöd2 = self._sök(kandidater, övriga, förfallna,
                                                sedda, nu)
                reserv = reserv or reserv2
                nödfall = nödfall or nöd2

        # NÖDFALLET ÄR ORDAGRANN UPPREPNING, och det serveras bara när
        # ingenting annat finns. B7 säger att ett fallerat kort ska tillbaka
        # i en ANNAN mening; kan ingen annan byggas är svaret enligt D3 att
        # SKJUTA UPP, inte att servera samma igen. Mätt före uppdelningen:
        # japanskan gav samma mening nio gånger i rad.
        #
        # `None` här betyder alltså inte "sökningen misslyckades" utan
        # "ingenting NYTT går att bygga", och `Övningstjänst.uppgift` svarar
        # på det med samma nödutgång som B8 använder.
        var_nödfall = bäst is None and reserv is None and nödfall is not None
        bäst = bäst or reserv or nödfall
        if bäst is not None:
            bäst = replace(bäst, nödfall=var_nödfall, reserv_släppt=släppt)
            self.poängsättare.minns(
                {k["koncept"] for k in bäst.kort if k["koncept"]})
            # Bara de tre senaste: längre minne skulle strypa en liten
            # kortlek helt, kortare fångar inte en tvåtakt (A, B, A, B).
            self._förra_texter = ([bäst.text] + self._förra_texter)[:3]
        return bäst

    def _duglig(self, okända: int, text: str) -> bool:
        """Får kandidaten vinna, eller hör den hemma i reservtiern?

        Två villkor, båda beskrivna i `_sök` och `föreslå`: noll okända ord
        (C5) och ingen ordagrann upprepning av de tre senaste.

        DE TVÅ VILLKOREN HÖR TILL OLIKA TIERS, och att konjungera dem här
        räcker inte. Villkoren handlar om skilda saker: det ena om vad
        användaren kan läsa, det andra om att inte servera samma mening
        igen. Vid kallstart är det FÖRSTA alltid falskt — inget ord är sett —
        och då blev upprepningsspärren död: varje kandidat föll till
        reservtiern, som inte hade någon. Mätt i japanskan: samma mening nio
        gånger i rad, med minnet fyllt av tre kopior av den.

        Därför prövas upprepningen också på reserven, i `_sök`.

        Regeln bor i en egen metod därför att den ska gå att SABOTERA i ett
        prov utan att skriva i källfilen. Den vägen prövades och är en fälla:
        `.pyc`-cachen jämför källans mtime i HELA SEKUNDER, så två skrivningar
        inom samma sekund gav gammal bytekod tillbaka — sabotaget tog inte,
        provet rapporterade grönt, och felet var återinfört utan att någon
        märkte det. Ett prov som ljuger åt det hållet är värre än inget.
        """
        return okända == 0 and text not in self._förra_texter

    def _sök(self, kandidater: int, mål: list, förfallna: set,
             sedda: set, nu) -> tuple["Förslag | None", "Förslag | None"]:
        """Bästa kandidaten kring `mål`, och bästa oavsett. Se `föreslå`.

        Två tiers, och skälet till att sökningen aldrig får misslyckas står i
        GENERATOR.md: som HÅRT filter gav okändgränsen `None` med jämna
        mellanrum — engelskan tog slut efter en mening när ingen av 200
        kandidater råkade hålla sig under den.
        """
        bäst: Förslag | None = None
        reserv: Förslag | None = None
        nödfall: Förslag | None = None
        # MÅLORDEN VARVAS, DE LOTTAS INTE. `rng.choice` gav varje mål samma
        # FÖRVÄNTADE antal försök, vilket är något annat än samma antal: med
        # trettio mål och tusen kandidater är spridningen stor nog att ett mål
        # kan få hälften så många chanser som ett annat, och vilket kort som
        # övas härnäst blev därmed ett lotteri i stället för ett beslut.
        #
        # Varvningen kostar ingenting och tar bort variansen helt: mål i
        # prioritetsordning, kandidat i tur och ordning, sedan poängen som
        # avgör. Slumpen är kvar där den hör hemma — i HUR meningen byggs,
        # alltså vilka fyllnadsord och vilken konstruktion — men inte längre i
        # VAD den handlar om.
        for i in range(kandidater):
            m = self.samplare.kandidat(kring=mål[i % len(mål)])
            if m is None or self.validator.validera(m):
                continue
            resultat = self._rendera(m)
            if resultat is None:
                continue
            (text, kort, uppslag, egenskaper, rektioner, ordföljder,
             osammansmält) = resultat
            okända = sum(1 for k in kort
                         if k["typ"] == "ord" and k["sedd"] is None
                         and k["koncept"] not in sedda)
            p = self.poängsättare.sätt(kort, förfallna, nu)
            # EN ORDAGRANT UPPREPAD MENING FÅR INTE VINNA. Den flyttas till
            # reservtiern, alltså tas den bara om ingenting annat finns.
            # `upprepning`-vikten räcker inte: den straffar återanvända
            # KONCEPT, men när det bara finns en möjlig mening förlorar
            # straffet mot täckningen varje gång.
            #
            # NOLL OKÄNDA, INTE ETT. Gränsen `<= 1` var en NYKVOT från tiden
            # då meningen fick införa ord — den regeln är borta (C2/D3: ord
            # införs i glosläget), och kvoten blev då den sista vägen in.
            #
            # Den vägen är inte fyllnaden, som `Samplare.begränsa` styr, utan
            # de STRUKTURORD renderaren skjuter in på egen hand: artikeln i
            # `Un frère existe.` väljs aldrig av `_välj` utan följer av
            # `Bestämdhet.OBESTÄMD`. Mätt vid kallstart med sex drillade ord:
            # tre meningar av tolv införde `un`, som ingen hade sett.
            #
            # Med noll faller en sådan mening till reservtiern och tas bara
            # när ingen ren mening finns — vilket är samma reservutgång som
            # alltid, och alltså synlig i stället för tyst.
            # TRE TIERS, INTE TVÅ. `bäst` är den som klarar allt; `reserv`
            # den som har okända ord men INTE är en upprepning; `nödfall`
            # den som är en upprepning. Den sista finns bara för att
            # sökningen aldrig får misslyckas — men den som tar emot den ska
            # kunna se att det var enda utvägen, och därför är den skild.
            upprepning = text in self._förra_texter
            duglig = self._duglig(okända, text)
            jämför = bäst if duglig else (nödfall if upprepning else reserv)
            if jämför is not None and p.total <= jämför.poäng.total:
                continue
            # Källspråket renderas FÖRST NU och inte för varje kandidat.
            # Samma beslut som allt annat i sökningen: gör det dyra bara för
            # den kandidat som faktiskt kan vinna.
            uppgift = None
            if self.källrenderare is not None:
                uppgift = self._rendera_källa(m)
                if uppgift is None:
                    continue
            förslag = Förslag(m, text, uppgift, kort, p, uppslag, egenskaper,
                              rektioner, ordföljder, False, osammansmält)
            if duglig:
                bäst = förslag
            elif upprepning:
                nödfall = förslag
            else:
                reserv = förslag
        return bäst, reserv, nödfall

    def _rendera_källa(self, m: Mening) -> str | None:
        """Meningen på källspråket, eller None om det språket inte når den.

        Ingen instrumentering: uppgiftens ord är inte användarens kort. Det
        är målspråket som övas, källspråket bara ställer frågan.
        """
        try:
            return self.källrenderare.rendera(m)
        except (RenderingsFel, KeyError, ValueError):
            return None

    def passkö_ider(self) -> set[int]:
        """Kön som mängd. `passkö()` ger antalet; den här ger vilka."""
        return set(self._passkö)

    def passkö(self) -> int:
        """Hur många kort som väntar på att tas igen i det här passet."""
        return len(self._passkö)

    def nytt_pass(self) -> None:
        """Töm passkön. Ett avbrutet pass ska inte följa med till nästa."""
        self._passkö.clear()

    def rätta(self, förslag: Förslag, svar: str) -> Rättning:
        """Användarens text → ett betyg per kort."""
        return self.rättare.rätta(svar, förslag.text, förslag.uppslag or [],
                                  förslag.kort, förslag.egenskaper or [],
                                  förslag.rektioner or [],
                                  förslag.ordföljder or [],
                                  förslag.osammansmält or [])

    def svara(self, förslag: Förslag, svar: str, *, källspråk: str | None = None,
              nu=None) -> Rättning:
        """Rätta OCH registrera — hela slingan i ett anrop."""
        rättning = self.rätta(förslag, svar)
        # Fallerade kort in i passkön, klarade ut ur den. Ett kort som gick
        # fel och sedan rätt i samma pass är avklarat: poängen med kön är
        # att inte lämna passet på ett fel, inte att kräva flera rätta svar.
        for kid, klarade in rättning.utfall.items():
            (self._passkö.discard if klarade else self._passkö.add)(kid)
        self.registrera(förslag, rättning.utfall,
                        källspråk=källspråk or self.källspråk, nu=nu)
        return rättning

    def nåbara_kort(self, *, kandidater: int = 400,
                    plus: set[str] | None = None) -> set[int]:
        """Vilka kort en mening FAKTISKT kan röra med dagens ordförråd.

        DAGENS URVAL VALDE PÅ RANG OCH INTE PÅ NÅBARHET, och det är felet
        bakom nästan varje symptom Julius rapporterat. Mätt på en franskkurs
        med fyra drillade ord: dagen planerade 17 kort, kunde leverera 9, och
        skrev av 8 som onåbara — 47 %. `pres_2sg` kräver `tu`, `pres_2pl`
        kräver `vous`, `sg` kräver ett substantiv, och två ordföljdskort
        kräver konstruktioner nivån inte öppnat. Inget av dem gick att göra;
        alla planerades in.

        Från användarens sida såg det ut som att passet slutade oväntat efter
        fyra meningar. Det gjorde det inte — det gjorde precis vad det skulle,
        med en dag som var omöjlig från början.

        SAMMA BEGRÄNSNING SOM GENERERINGEN. Samplingen körs med fyllnaden
        låst till det användaren mött (`begränsa(sedda)`), alltså exakt de
        meningar passet skulle kunna bygga. Att sampla fritt vore att mäta
        något annat än frågan.

        `plus` ÄR DAGENS EGNA ORD, och utan dem blir svaret fel åt andra
        hållet. Drillen ligger i SAMMA dag som meningarna: mäter man
        nåbarheten före den är ordförrådet det gårdagens, och vid kallstart
        är svaret noll — mätt gav det en dag med sju ord och NOLL meningar.
        Orden som ska delas ut idag räknas därför som kända här, för det är
        de när meningarna kommer.

        Kostar några hundra renderingar och görs EN gång per dag och kurs —
        inte per anrop. Det är skillnaden mot en prognos: det här är en
        mätning av vad som går just nu.
        """
        self._läs_kort()
        sedda = self._sedda_koncept() | (plus or set())
        self.samplare.begränsa(sedda)
        try:
            # SLUTAR NÄR DEN SLUTAR HITTA NYTT. Mängden nåbara kort mättas
            # fort — med ett litet ordförråd är den full efter några tiotal
            # meningar — och att köra vidare kostar bara tid. Mätt: 400
            # kandidater gav 4,6 sekunder på första sidladdningen, vilket
            # ser ut som att programmet hängt sig.
            #
            # Spärren är inte en tröskel för vad som räknas som nåbart utan
            # en gräns för hur länge vi letar efter mer. Att den är
            # proportionell mot `kandidater` gör att en anropare som vill
            # leta noggrannare får göra det.
            nåbara: set[int] = set()
            utan_nytt = 0
            tålamod = max(20, kandidater // 8)
            for _ in range(kandidater):
                if utan_nytt >= tålamod:
                    break
                m = self.samplare.kandidat()
                if m is None or self.validator.validera(m):
                    continue
                r = self._rendera(m)
                if r is None:
                    continue
                före = len(nåbara)
                nåbara |= {k["id"] for k in r[1]}
                utan_nytt = 0 if len(nåbara) > före else utan_nytt + 1
            return nåbara
        finally:
            self.samplare.begränsa(None)

    def övningsbara(self, koncept: list[str]) -> list[str]:
        """De av `koncept` som går att bygga en mening KRING.

        Tjänsten behöver den för att veta vad som är arbete: ett ord som
        införts men inte övats är arbete kvar för dagen — men bara om det går
        att öva. `un` går inte att styra mot (se `Samplare.duger_som_mål`),
        och att räkna det som arbete höll dagen öppen i evighet.
        """
        return [k for k in koncept if self.samplare.duger_som_mål(k)]

    #: URVALET MÅSTE KUNNA UPPLÖSA TRÖSKELN. `redo_för_nivå` frågar om
    #: `byggbarhet × kandidater ≥ 1`, alltså om andelen är minst 1/800 — men
    #: måttet samplade 200 kandidater, och ett urval på 200 kan inte skilja
    #: 1/800 från noll. Grinden prövade en gräns dess eget underlag inte nådde
    #: ner till.
    #:
    #: Mätt 2026-08-26: nivå 6 (possessiv) hade den sanna andelen 2/800, alltså
    #: över tröskeln — men med 200 kandidater blev skattningen noll gång på
    #: gång, och kursen stod låst på nivå 5 i evighet. Talet är därför
    #: detsamma som sökningens: samma tal som tröskeln härleds ur.
    STANDARDKANDIDATER = 800

    def byggbarhet(self, *, kandidater: int = STANDARDKANDIDATER,
                   nivå: int | None = None) -> float | None:
        """Andel samplade meningar med HÖGST ETT okänt ord.

        Måttet finns för upplåsningen (F1). Efter B2 är kapaciteten inte
        längre en grind — inflödestakten styrs per dygn oavsett vilka nivåer
        som är öppna, så en öppnad nivå kan bevisligen inte öka arbetsbördan.
        Kvar står en annan fråga: går nivån att ÖVA, eller blir varje mening
        en ordlektion?

        Mätt fall: franskans första mening blev `Elle regarde.` där båda orden
        var osedda — en uppgift som bara gick att gissa. Det är den
        situationen måttet upptäcker i förväg.

        Samma okändgräns som genereringen redan använder (C5), och samma skäl:
        ett okänt ord i en mening man annars förstår går att sluta sig till,
        två går inte.

        `nivå` KRÄVER ATT MENINGEN ANVÄNDER NIVÅNS KONSTRUKTION, och utan det
        mätte grinden fel sak. `upplåst(nivå)` säger vad som är TILLÅTET, så
        på nivå 2 är en vanlig subjekt-verb-mening fortfarande giltig — och
        eftersom objekt är valfritt bestod nästan hela urvalet av
        nivå-1-meningar. Måttet svarade alltså "nivå 2 går att öva" genom att
        visa att nivå 1 går att öva.

        Mätt 2026-08-26: efter EN dags franska gick tjugo nivåer att låsa upp
        i följd — 632 kort, utan att öva emellan — med byggbarhet 0,006–0,067
        mot tröskeln 0,00125. Med kravet inkopplat mäts i stället hur många av
        meningarna som faktiskt bär det nivån handlar om.

        NÄMNAREN ÄR ALLA BYGGDA MENINGAR, inte bara de som använder
        konstruktionen. Det är avsiktligt: frågan är hur ofta sökningen kan
        producera en ÖVBAR mening på den nya nivån, och en nivå vars
        konstruktion nästan aldrig går att bygga är inte redo — oavsett hur
        bra de meningar som lyckas råkar vara.
        """
        sedda = self._sedda_koncept()
        träffar = byggda = 0
        for _ in range(kandidater):
            m = self.samplare.kandidat()
            if m is None or self.validator.validera(m):
                continue
            resultat = self._rendera(m)
            if resultat is None:
                continue
            _text, kort, _uppslag, _egenskaper, _rekt, _ordf, _osm = resultat
            byggda += 1
            okända = sum(1 for k in kort
                         if k["typ"] == "ord" and k["sedd"] is None
                         and k["koncept"] not in sedda)
            träffar += okända <= 1 and (nivå is None or använder_nivån(m, nivå))
        return träffar / byggda if byggda else None

    def registrera(self, förslag: Förslag, utfall: dict[int, bool],
                   *, källspråk: str | None = None, nu=None,
                   självrättade: set[int] | None = None,
                   millisekunder: int | None = None) -> int:
        return self.schemaläggare.registrera_mening(
            self.språk, spec_json(förslag.mening), förslag.text, utfall,
            källspråk=källspråk or self.källspråk,
            budget=self.poängsättare.budget, nu=nu,
            självrättade=självrättade,
            # ALLA kort meningen innehöll, inte bara de som fick en dom.
            # Skillnaden är de undanhållna, och utan den kan schemaläggaren
            # inte skjuta upp dem.
            rörda={k["id"] for k in förslag.kort},
            millisekunder=millisekunder)

    def uppdatera_passkö(self, utfall: dict[int, bool]) -> None:
        """Fallerade kort in i passkön, klarade ut ur den.

        Skild från `svara` sedan betygsättningen sköts upp: kön ska följa det
        SLUTLIGA utfallet, alltså efter en eventuell självrättning, inte det
        maskinen gissade först.
        """
        for kid, klarade in utfall.items():
            (self._passkö.discard if klarade else self._passkö.add)(kid)


__all__ = ["Anmärkning", "Förslag", "Generator", "Ordförråd", "Poäng",
           "Poängsättare", "Rättare", "Rättning", "Samplare"]
