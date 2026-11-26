/* ═══════════════════════════════════════════════════════════════════════════
   PASSET FÅR EN IDENTITET

   Före den här tabellen fanns inget objekt som var "dagens pass". Det fanns
   en databas som frågades om och om igen, plus åtta lexikon i minnet på
   Övningstjänst som råkade hänga ihop. Ingenting tvingade dem att vara
   överens, och varje bugg i passet under vecka 34 var två av dem som inte
   var det:

       passet avslutades oväntat      innehållet räknades om vid varje anrop
                                      och kunde krympa under användaren
       siffrorna följde inte passet   de beskrev databasen, inte passet
       "7 new" / "1 new" på en klar   talen hämtades ett anrop före
       dag                            meddelandet bredvid dem
       samma mening om och om igen    meningsminnet levde bara i minnet

   DAGSPLANEN ÄR POLITIK, PASSET ÄR TILLSTÅND. Skillnaden är hela poängen.
   `dagsplan` räknar ut hur mycket som FÅR göras — takten, taket, tiden — och
   det ska räknas om, för det är en styrning (B2). Men VAD dagen innehåller
   är ett faktum som ska bestämmas EN gång och sedan stå kvar. Det är den här
   tabellen.

   Efter det är varje tal på skärmen en RÄKNING och inte en härledning:

       att göra   rader med status 'väntar'
       klar       inga rader med status 'väntar'
       igen       rader med roll 'igen' som väntar

   `klar` blir därmed ett faktum i stället för en slutsats, och det finns
   inget andra ställe som kan komma fram till något annat.
   ═══════════════════════════════════════════════════════════════════════════ */

CREATE TABLE IF NOT EXISTS Pass (
    id       INTEGER PRIMARY KEY,
    kurs_id  INTEGER NOT NULL REFERENCES Kurs(id) ON DELETE CASCADE,

    /* LOKALT dygn, inte UTC. Samma gräns som `dygnets_början` använder — ett
       pass klockan 00:30 hör till natten man började, inte till gårdagen. */
    datum    TEXT    NOT NULL,

    /* 'dagens' eller 'extra'. Extraövningen har en egen kö (kort som ännu
       inte förfallit) och därför ett eget pass: att blanda dem vore att låta
       tidiga repetitioner räknas som dagens arbete, vilket B6 uttryckligen
       säger att de inte är. */
    läge     TEXT    NOT NULL DEFAULT 'dagens'
             CHECK (läge IN ('dagens', 'extra')),

    startad  TEXT    NOT NULL,
    /* Sätts när sista raden lämnat 'väntar'. Ett avslutat pass går inte att
       återuppta — dagen är gjord. */
    avslutad TEXT,

    UNIQUE (kurs_id, datum, läge)
);

CREATE TABLE IF NOT EXISTS Passkort (
    id      INTEGER PRIMARY KEY,
    pass_id INTEGER NOT NULL REFERENCES Pass(id) ON DELETE CASCADE,

    /* SET NULL OCH INTE CASCADE, och kolumnen är därför NULLBAR. Det är
       inte en uppmjukning utan hela poängen — se
       `passkort_bevara_bevis.sql` för varför.

       Raderas kortet tog CASCADE med sig passets rad, och kvar blev ett
       Pass utan innehåll. Noll rader betyder "inget väntar", alltså klar,
       och `starta` är idempotent: den hittade det tomma passet och byggde
       aldrig om. Resultatet var "Done for today" på en kurs man just
       nollställt — och på en GRANNKURS mot samma målspråk, som ingen rört,
       eftersom passet hör till kursen medan kortbeståndet är per språk.

       Att raden pekar på ett kort som inte finns ÄR upplysningen. Med
       beviset kvar går passets giltighet att HÄRLEDA (`_ruin`) i stället
       för att kommas ihåg av varje väg som råkar röra beståndet.

       Den här filen deklarerade CASCADE ända tills 2026-08-26, alltså
       skapade den en NY databas med precis det fel ombyggnaden finns för
       att laga. Källan och rättelsen sa olika saker, och källan vann på
       varje ny installation. */
    kort_id INTEGER REFERENCES Kort(id) ON DELETE SET NULL,

    /* VARFÖR kortet är med. Rollen är inte en etikett utan det som avgör hur
       kortet ska mötas: en glosa läses i drillen, ett förfallet kort och ett
       nytt böjningskort möts i en mening, ett `igen` är ett återförsök inom
       samma pass (B7).

       ETT KORT KAN HA FLERA RADER. En rad är ett planerat MÖTE, inte ett
       kort — faller ett kort läggs en ny rad med roll 'igen' till, och den
       gamla står kvar med sitt utfall. Det är därför det inte finns någon
       unik nyckel på (pass_id, kort_id): historiken i passet är en följd av
       rader och inte ett tillstånd per kort. */
    roll    TEXT    NOT NULL
            CHECK (roll IN ('förfallen', 'ny', 'glosa', 'igen')),

    /* Ordningen bestämd vid konstruktionen. Drillen först, sedan meningarna
       — F4:s ordningsregel, skriven en gång i stället för härledd på nytt
       vid varje anrop. */
    ordning INTEGER NOT NULL,

    /* TILLSTÅNDSMASKINEN, och den är hela skälet att tabellen finns.

           väntar   ogjort
           rätt     mötte kortet och klarade det
           fel      mötte kortet och missade det (en 'igen'-rad läggs till)
           onåbar   generatorn kunde inte bygga en mening som rör kortet
                    (B8). Räknas som gjort för dagen men ger INGET betyg —
                    ett kort utan mätning är ärligt, ett med påhittad
                    mätning är värre än tomt.

       Att den är en TEXT och inte ett heltal är avsiktligt: `utfall = NULL`
       betydde tre olika saker på tre ställen i den gamla koden. */
    status  TEXT    NOT NULL DEFAULT 'väntar'
            CHECK (status IN ('väntar', 'rätt', 'fel', 'onåbar')),

    tidpunkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_passkort_pass ON Passkort(pass_id, status);
CREATE INDEX IF NOT EXISTS idx_pass_kurs ON Pass(kurs_id, datum, läge);
