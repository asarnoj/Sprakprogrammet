/* ── Tidsloggning: hur länge en uppgift tog ──────────────────────────
   Mot kort.db (inlärardatabasen), inte sprak.db.

   VAD DEN INTE ÄR. Svarstid är INTE en signal om minnet, och får aldrig bli
   det. FSRS egen optimerare läser `review_datetime` och `rating`, och skickar
   uttryckligen `review_duration=None` när parametrarna anpassas —
   förlustfunktionen jämför förutsagd retention mot faktiskt utfall, 0 eller 1.
   Anki gör likadant: `revlog.taken` sparas, syns i statistiken, och rör inte
   schemaläggningen. Se E3 i PROBLEM.md, där ett förslag att härleda Hard ur
   svarstid prövades och föll.

   VAD DEN ÄR. En KOSTNAD, och den har två användningar:

     `compute_optimal_retention` simulerar vilken `desired_retention` mellan
     0,70 och 0,95 som ger mest kunskap per minut. Den kräver `review_duration`
     på VARJE loggpost och minst 512 poster — och den funktionen är det enda
     sättet att välja retentionsmålet på mätning i stället för på känsla (C2).

     Omräkningen minuter → kort. B4 gjorde minuter per dag till användarens
     enda val, och utan sekunder per repetition finns ingen växelkurs mellan
     det talet och en kortlek. Där är tidsloggningen LASTBÄRANDE och inte en
     extramätning för framtiden.

   VAR DEN LAGRAS, OCH VARFÖR PÅ TVÅ STÄLLEN. Tiden lagras där den faktiskt
   MÄTTES, aldrig som ett härlett tal:

     Mening.millisekunder      en mening är ETT tidtaget moment, hur många
                               kort den än rör
     Repetition.millisekunder  bara för rader UTAN mening — glosläget, där
                               ett kort och ett svar är hela momentet

   Kostnaden per repetition är då en fråga och ingen kolumn: meningens tid
   delad på dess bedömda kort. Att dela på det sättet är legitimt just för att
   det är en kostnad — ANSTRÄNGNING går inte att fördela mellan korten i en
   mening, men SEKUNDER gör det.

   RÅTIDEN SPARAS OKAPAD. Anki kapar vid 60 sekunder för att en kafferast
   annars blir en timmes "kostnad". Det taket behövs, men det är ett
   ANALYSVAL och inte en mätning: kapas det vid skrivningen är den verkliga
   fördelningen borta för alltid, och gränsen går aldrig att mäta fram ur
   datan. Här sparas alltså allt, och kapningen görs när talet används.

   Kör:  sqlite3 kort.db < ordbok/migrationer/kort_tidsloggning.sql
   ─────────────────────────────────────────────────────────────────────── */

ALTER TABLE Mening     ADD COLUMN millisekunder INTEGER;
ALTER TABLE Repetition ADD COLUMN millisekunder INTEGER;
