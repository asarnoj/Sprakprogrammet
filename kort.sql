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
    fel        INTEGER NOT NULL DEFAULT 0
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
    betyg     INTEGER NOT NULL CHECK (betyg IN (1, 2, 3, 4)),
    förfluten REAL,
    r_före    REAL,
    stabilitet REAL,
    svårighet  REAL
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
    meningar_per_dag INTEGER NOT NULL DEFAULT 20,
    startad   TEXT    NOT NULL,
    /* När kursen senast öppnades. Programmet startar i den som användes
       sist — en kurs man höll på med igår är den man vill fortsätta med. */
    senast_öppnad TEXT,
    UNIQUE (källspråk, målspråk),
    CHECK (källspråk <> målspråk)
);
