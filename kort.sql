/* ═══════════════════════════════════════════════════════════════════════════
   kort.sql — schemat för INLÄRARDATABASEN

   Egen fil, skild från sprak.db, och det är ett medvetet beslut
   (GENERATOR.md, "Var kortlagret bor"): `ordbok import --återinitiera`
   bygger om språkdatabasen från grunden, och repetitionshistoriken är det
   enda i systemet som inte går att återskapa. De två får aldrig dela fil.

   Följden åt andra hållet: ingenting här får peka på ett id i sprak.db.
   `Former.id` flyttar vid varje ombyggnad — det är redan skälet till att
   granskningsrattelser.sql ligger utanför migrationerna. Kopplingen går i
   stället genom NATURLIGA nycklar: konceptnyckel, språk, variant, cell.
   Alla fyra är strängar som överlever att raderna skrivs om.

   En ombyggd språkdatabas ska kunna mötas av en orörd inlärardatabas.
   ═══════════════════════════════════════════════════════════════════════════ */

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


/* ── Kort ────────────────────────────────────────────────────────────────────
   Ett kort är ett distinkt kunskapsmoment. Vilka de är avgörs av
   GENERATOR.md, "Hur fint ska ett formkort skäras?": en form får eget kort
   först när den inte går att härleda ur det användaren redan har kort för.

   typ         vad kortet är, GENERATOR.md korttyp 1–5
   ───────────────────────────────────────────────────────────────────────────
   ord         (1) att ordet finns och betyder något
   stam        (2) en av ordets stammar — groß / größer / größt
   form        (2) en form som INTE gick att härleda; rest ur stammar.tsv
   system      (3) en ändelse i en klass tabell — delas av alla ord i klassen
   rektion     (3) att ett styrande ord kräver en viss form: geben → dativ
   egenskap    (5) genus, hjälpverb, prenominal, böjningsklass
   ordföljd    (4) en ordföljdsregel renderaren implementerar

   `nyckel` är den naturliga nyckeln, hopfogad till en läsbar sträng, och
   den enda identitet ett kort har. Delarna ligger också som egna kolumner
   för att gå att fråga på; de är sparsamt ifyllda och kostar ingenting.

   `schemalagt` skiljer kort som DRIVER urvalet från kort som bara MÄTS.
   Ett kort som möts i nästan varje mening går inte att schemalägga och
   behöver inte det — spacing finns mot glömska, och något man möter arton
   gånger dagligen glöms inte. Se GENERATOR.md, "Schemalagda kort mot mätta".
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Kort (
    id         INTEGER PRIMARY KEY,
    nyckel     TEXT    NOT NULL UNIQUE,
    typ        TEXT    NOT NULL CHECK (typ IN (
                   'ord', 'stam', 'form', 'system', 'rektion',
                   'egenskap', 'ordföljd')),
    språk      TEXT    NOT NULL CHECK (språk IN ('sv','en','fr','de','es','it','ja')),

    /* naturlig nyckel — olika delar ifyllda per typ, aldrig id:n */
    koncept    TEXT,
    variant    TEXT,
    ordklass   TEXT,
    klass      TEXT,
    cell       TEXT,
    stamgrupp  INTEGER,
    egenskap   TEXT,

    /* vad kortet testar: ordformen, ändelsen, genusvärdet, regelns namn */
    facit      TEXT    NOT NULL,
    /* hur många celler stammen eller ändelsen täcker */
    räckvidd   INTEGER NOT NULL DEFAULT 1,

    /* I VILKEN ORDNING ORD SKA INFÖRAS. Lägre = tidigare.

       Utan den sorterades nya kort på `räckvidd` och sedan på id — men
       räckvidden är 1 för samtliga ordkort, så det som återstod var
       databasordningen, alltså i praktiken ordlistornas filordning. Följden
       var att en fransk nybörjare mötte `argent`, `s'asseoir` och `kosten`
       före `je` och `le`.

       Rangen väger tre saker som ALLA redan finns i språkdatabasen:

         källa        bas_kärna före grundord — de slutna ordklasserna är
                      kärnan, och den uppdelningen är redan gjord i
                      ordbok/nivålistor/
         nivå         A1 före A2 före B1
         centralitet  hur många meningar ordet gör möjliga, normaliserat
                      INOM ordklassen: 169 möjliga subjekt och 65 möjliga
                      verb är inte samma skala, och att jämföra dem rakt av
                      satte modalverben före pronomenen

       Se befolka._rang. Kort utan koncept — ordföljd, systemkort — får
       samma neutrala rang och ordnas som förut. */
    rang       INTEGER NOT NULL DEFAULT 0,

    /* uppmätt antal möten per genererad mening. NULL = inte mätt än.
       Räckvidden duger INTE som proxy: alla celler i en klass har samma
       räckvidd, men nom_sg möts i varannan mening och gen_pl nästan aldrig.
       Mätt på 2 000 tyska meningar var medianen 0,023 för systemkort och
       0,003 för stamkort — de allestädes närvarande är 13 av 58, inte alla. */
    exponering REAL,
    schemalagt INTEGER NOT NULL DEFAULT 1 CHECK (schemalagt IN (0, 1)),

    /* ── FSRS-tillstånd ──────────────────────────────────────────────────
       Speglar fsrs.Card exakt, så att en rad går att lyfta in i biblioteket
       och tillbaka utan översättningsförlust. `stabilitet` och `svårighet`
       är algoritmens två tillståndsvariabler; `förfaller` är det enda
       urvalet behöver läsa. Tiderna är ISO-8601 i UTC.

       `tillstånd` och `steg` hör till inlärningsstegen. Vi kör UTAN sådana
       (GENERATOR.md: "Inga relearning-steg behövs" — genereringen ersätter
       Ankis tiominutersmekanik), men kolumnerna finns ändå: biblioteket
       bär dem, och att tappa dem vid varje rundtur vore att tyst ändra
       kortets tillstånd. */
    tillstånd  INTEGER NOT NULL DEFAULT 1,
    steg       INTEGER,
    stabilitet REAL,
    svårighet  REAL,
    förfaller  TEXT,
    sedd       TEXT,
    antal      INTEGER NOT NULL DEFAULT 0,
    fall       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_kort_förfaller ON Kort(språk, schemalagt, förfaller);
CREATE INDEX idx_kort_koncept   ON Kort(språk, koncept);
CREATE INDEX idx_kort_typ       ON Kort(språk, typ);


/* ── Cellkort ────────────────────────────────────────────────────────────────
   Från en ordform till de kort som prövas när den används.

   Det är den här tabellen renderarens beroendekarta landar i. `Uppslag.form`
   känner redan till (lexem, cell); den här översätter det till kort, och
   utan den går attributionen inte att göra — GENERATOR.md, "Renderaren
   lämnar en beroendekarta".

   En cell pekar normalt på TVÅ kort: ordets stam och klassens ändelse. Är
   formen en rest pekar den på ett enda formkort i stället. Ordkortet ligger
   inte här — det slås upp på konceptet direkt.

   Nycklarna är naturliga hela vägen, precis som i Kort.
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Cellkort (
    språk   TEXT    NOT NULL,
    koncept TEXT    NOT NULL,
    variant TEXT,
    cell    TEXT    NOT NULL,
    kort_id INTEGER NOT NULL REFERENCES Kort(id) ON DELETE CASCADE
);

CREATE INDEX idx_cellkort ON Cellkort(språk, koncept, variant, cell);
CREATE INDEX idx_cellkort_kort ON Cellkort(kort_id);


/* ── Mening ──────────────────────────────────────────────────────────────────
   Varje genererad mening, med den budget den byggdes mot och det utfall den
   gav. Meningen är INTE ett kort — den ses aldrig igen — men den är enheten
   svårighetsgraden mäts på, och utan den går inte frågan "vilken budget lär
   man sig mest av" att besvara.

   `spec` är meningsspecifikationen serialiserad, så att en mening går att
   återskapa exakt. `budget` är Σ(1−R) den siktade mot, `förväntat` samma
   summa för de kort den faktiskt fick.

   `förväntat` RÄKNAS BARA ÖVER SEDDA KORT, och `nya` står för sig. Det är
   inte en detalj utan förutsättningen för att loggen ska gå att analysera:
   `förväntat` är FSRS förutsägelse av antalet fel, och en förutsägelse om
   ett kort modellen aldrig sett finns inte. Räknas osedda kort med R = 0
   blir talet förväntade fel PLUS antalet nya ord — två storheter adderade,
   och skillnaden mot `fel` mäter då ingenting.

   Det är den skillnaden hela svårighetsfrågan hänger på: faktiska fel minus
   förväntade fel är det enda måttet som skiljer "meningen var för svår" från
   "korten i den var svaga", eftersom kortens svaghet är precis vad
   förutsägelsen redan räknar bort.
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Mening (
    id         INTEGER PRIMARY KEY,
    tidpunkt   TEXT    NOT NULL,
    språk      TEXT    NOT NULL,
    källspråk  TEXT,
    spec       TEXT    NOT NULL,
    text       TEXT    NOT NULL,
    budget     REAL,
    förväntat  REAL,
    sedda      INTEGER,
    nya        INTEGER,
    fel        INTEGER NOT NULL DEFAULT 0,

    /* Hur länge uppgiften tog, RÅTT och okapat. En mening är ett tidtaget
       moment hur många kort den än rör, så det är här tiden faktiskt mäts.

       Kostnaden per repetition är därmed en fråga och ingen kolumn: den här
       tiden delad på meningens bedömda kort. Att dela så är legitimt just för
       att det är en KOSTNAD — ansträngning går inte att fördela mellan kort,
       sekunder gör det.

       Svarstid är aldrig en signal om minnet. Se `Repetition.millisekunder`. */
    millisekunder INTEGER
);

CREATE INDEX idx_mening_tid ON Mening(tidpunkt);


/* ── Repetition ──────────────────────────────────────────────────────────────
   Varje prövning av varje kort, för alltid. Två skäl, båda i GENERATOR.md:

   FSRS-parametrarna optimeras mot den egna historiken — utan logg går det
   inte, och den kan inte rekonstrueras i efterhand.

   Och: "vilken svårighetsgrad man lär sig mest av går inte att slå upp,
   eftersom ingen byggt det här systemet, men den går att MÄTA i efterhand."
   Därför loggas budget och utfall per mening, inte bara betyget per kort.

   `betyg` följer FSRS fyra steg. `förfluten` är faktisk tid sedan förra
   prövningen i dagar — det är den algoritmen räknar på, och den sparas
   explicit så att loggen går att läsa utan att räkna om den.

   `r_före` är FSRS förutsägelse av att kortet skulle klaras, FÖRE prövningen.
   Den är nollmodellen: skillnaden mellan faktiska och förutsagda fel är det
   enda sättet att pröva om meningens sammansättning gör något utöver vad
   korten var för sig gör. Utan den frågan går det inte att skilja "svåra
   meningar orsakar fel" från "svaga kort är svaga".

   Den går att räkna fram ur föregående rads `stabilitet` och den här radens
   `förfluten`, men sparas ändå: kedjan bryts om FSRS-parametrarna någon gång
   optimeras om, och en logg som måste tolkas i ljuset av vilka parametrar som
   gällde när den skrevs är inte en logg. `stabilitet` och `svårighet` är
   värdena EFTER prövningen; `r_före` är det enda som beskriver läget före.
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Repetition (
    id        INTEGER PRIMARY KEY,
    kort_id   INTEGER NOT NULL REFERENCES Kort(id) ON DELETE CASCADE,
    mening_id INTEGER          REFERENCES Mening(id) ON DELETE SET NULL,
    tidpunkt  TEXT    NOT NULL,

    /* BETYG SAKNAS NÄR INGEN MÄTNING ÄGDE RUM. Raden finns ändå, och den har
       ett jobb: `_redan_idag` läser dagens rader för att veta vad som redan
       bedömts, och en betyglös rad skyddar därför kortet resten av dygnet
       utan att en enda regel behöver ändras.

       Utan raden var kortet oskyddat på det farligaste sättet som finns. Ett
       undanhållet kort behöll sitt passerade förfallodatum, stod alltså kvar
       i kön, och plockades gärna till NÄSTA mening — efter att facit visats.
       Klarade användaren det då fick kortet ett fullt Good med hela den
       förflutna tiden inräknad. Mätt: stabiliteten hoppade 10,96 → 46,28 i
       stället för till ~11.

       `skäl` säger vilken sorts icke-mätning det var, och gör dem räknebara:

         undanhållen  diffen kunde inte knyta felet till ett kort (D3)
         skyddad      ordkortet fallerade, så formen prövades aldrig (E5)
         visad        lektionen eller glosläget visade kortets facit (F4)

       NYA kort får aldrig en sådan rad. Deras första möte ÄR introduktionen,
       och FSRS begynnelsestabilitet är byggd för precis det. */
    betyg     INTEGER          CHECK (betyg IS NULL OR betyg IN (1, 2, 3, 4)),
    skäl      TEXT             CHECK (skäl IS NULL OR skäl IN
                                      ('undanhållen', 'skyddad', 'visad')),

    förfluten REAL,
    r_före    REAL,
    stabilitet REAL,
    svårighet  REAL,

    /* Betyget kom från ANVÄNDAREN och inte från diffen mot facit.

       Självrättningen finns för de fall bara människan kan avgöra: hen skrev
       en annan giltig mening, eller en variant systemet inte känner. Utan
       den vore de felen inte bara omätta utan felmätta — ett rätt svar som
       registreras som fel sänker stabiliteten på kort som mår bra, vilket är
       den enda feltypen som fördärvar data i stället för att bara sakna den.

       Kolumnen gör den till ett INSTRUMENT och inte bara en eftergift: blir
       en viss sorts anmärkning överprövad om och om igen är det rättningen
       som har fel, och användningen säger det utan att någon behöver gissa.
       Jämför andelen självrättade betyg per konstruktion — stiger den är det
       generatorn eller renderaren som ska ses över, inte användaren. */
    /* Bara för rader UTAN mening — glosläget, där ett kort och ett svar är
       hela momentet. Har raden en mening ligger tiden på den, och delas.

       ANVÄNDS ALDRIG SOM MINNESSIGNAL. FSRS optimerare läser tidpunkt och
       betyg, och skickar uttryckligen `review_duration=None` när parametrarna
       anpassas. Talet finns för `compute_optimal_retention`, som väljer
       retentionsmålet på mest kunskap per minut, och för omräkningen mellan
       användarens minuter per dag och en kortlek. */
    millisekunder INTEGER,

    självrättad INTEGER NOT NULL DEFAULT 0 CHECK (självrättad IN (0, 1)),

    /* Exakt ett av dem, aldrig båda och aldrig ingetdera: raden är ANTINGEN
       en bedömning ELLER en anteckning om att ingen bedömning gjordes. */
    CHECK ((betyg IS NULL AND skäl IS NOT NULL)
        OR (betyg IS NOT NULL AND skäl IS NULL))
);

CREATE INDEX idx_repetition_kort ON Repetition(kort_id, tidpunkt);


/* ── Kurs ────────────────────────────────────────────────────────────────────
   Käll- och målspråk är låsta per kurs (GENERATOR.md, "Kursmodell"). Flera
   kurser parallellt går bra, och alla kombinationer av de sju är tillåtna.
   `nivå` och `cefr` är kursens två oberoende tak: komplexitetsstegen styr
   vilka KONSTRUKTIONER som finns, CEFR vilka ORD. Båda behövs — en kurs som
   bara känner sin stegnivå vet halva sin nivå.

   `meningar_per_dag` är hur mycket användaren vill öva. Det är ett VAL och
   ingen härledning — en uppgift om användarens liv, som systemet omöjligt kan
   räkna ut. Det står här bredvid `budget` därför att de är samma sorts tal:
   de två inställningar hela kursen styrs av. Upplåsningen räknas fram ur det
   här talet, FSRS egna intervall, och en mätning (schemalaggning.py).
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Kurs (
    id        INTEGER PRIMARY KEY,
    källspråk TEXT    NOT NULL,
    målspråk  TEXT    NOT NULL,
    nivå      INTEGER NOT NULL DEFAULT 1,
    cefr      TEXT    NOT NULL DEFAULT 'C2',
    budget    REAL    NOT NULL DEFAULT 1.5,

    /* HUR MYCKET ANVÄNDAREN VILL ÖVA, i minuter. Det enda valda talet i hela
       arbetsbörderäkningen — ett faktum om användarens dygn, inte om språket,
       och därför omöjligt att räkna fram.

       Det ersätter `meningar_per_dag`, som var fel storhet av två skäl. Ingen
       människas begränsning är "tjugo meningar"; begränsningen är tid. Och
       ett tak på antalet ÖVNINGAR konkurrerade med kravet att alla förfallna
       kort ska göras — två regler som kan säga olika saker om när dagen är
       slut är en regel för mycket.

       Antalet meningar är numera en KONSEKVENS: dagen innehåller de kort som
       förfallit, och hur många meningar det blir följer av hur många kort en
       mening rymmer. Arbetsbördan regleras i stället genom hur mycket nytt
       som förs in — se kort/arbetsborda.py. */
    minuter_per_dag INTEGER NOT NULL DEFAULT 20,
    meningar_per_dag INTEGER NOT NULL DEFAULT 20,
    startad   TEXT    NOT NULL,
    /* När kursen senast öppnades. Programmet startar i den som användes
       sist — en kurs man höll på med igår är den man vill fortsätta med. */
    senast_öppnad TEXT,
    UNIQUE (källspråk, målspråk),
    CHECK (källspråk <> målspråk)
);

/* ── spår — hur rättningen kom fram till sin dom ─────────────────────
   Julius mätte symptomet: "jag gjorde jättemånga fel men ändå växte inte
   again, och ibland krympte new/due". Frågan gick inte att svara på ur
   `Mening` och `Repetition`, därför att de bara bevarar UTFALLET.

   Det som saknades är tre saker, och alla tre fanns i minnet en kort
   stund innan de kastades:

     svar          vad användaren faktiskt skrev. Lagrades ingenstans.
     anmärkningar  vad diffen SÅG — skrev/väntat/slutsats per fel, med
                   det kort felet lades på och om attributionen var osäker.
     kortlägen     varför varje kort fick eller INTE fick en dom.

   Den sista är den viktigaste och den som var omöjlig att härleda. Ett
   kort utan `Repetition`-rad kan ha hamnat där på fem olika sätt —
   undanhållet, skyddat, redan bedömt idag, redan fällt idag, eller aldrig
   prövat — och de har helt olika innebörd. Utan raden går det bara att
   gissa, vilket är precis vad som gjorde symptomet outrett.

   JSON OCH INTE KOLUMNER, med flit. Det här är DIAGNOSTIK: den läses av
   människor och verktyg som redan vet vad de letar efter, den ingår inte i
   någon modell, och inget beslut i programmet hänger på den. En relationell
   uppdelning hade kostat tre tabeller och gett noll frågor vi faktiskt
   ställer. Blir en fråga återkommande hör den hemma som en riktig kolumn.

   Spåret PÅVERKAR INGENTING. Det skrivs efter att domarna fallit och läses
   aldrig av schemaläggningen — annars vore det inte längre ett spår utan
   en del av modellen.
   ──────────────────────────────────────────────────────────────── */
/* IF NOT EXISTS, därför att migrationen `spar.sql` kör vid varje anslutning
   och `skapa_kortdatabas` ansluter FÖRE den kör grundschemat. Utan det kunde
   ingen ny kortdatabas skapas: tabellen fanns redan när schemat nådde hit.
   Det bröt `ordbok kort --återinitiera`. */
CREATE TABLE IF NOT EXISTS Spår (
    id           INTEGER PRIMARY KEY,
    mening_id    INTEGER NOT NULL REFERENCES Mening(id) ON DELETE CASCADE,
    svar         TEXT,
    anmärkningar TEXT NOT NULL DEFAULT '[]',
    kortlägen    TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_spår_mening ON Spår(mening_id);
