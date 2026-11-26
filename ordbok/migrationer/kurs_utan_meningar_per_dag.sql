/* ═══════════════════════════════════════════════════════════════════════════
   KURS.MENINGAR_PER_DAG TAS BORT

   Kolumnen var användarens ratt före B4: "så här många meningar vill jag göra
   per dag". Julius avskaffade den ratten själv, med skälet att den motsäger
   FSRS — man styr inte NÄR aktiva kort ska repeteras, bara hur mycket NYTT
   som förs in — och bytte till `minuter_per_dag`. Sedan dess har kolumnen
   stått kvar på 20 i varje kurs, satt av ingen.

   TRE LÄSARE FANNS, OCH BARA EN LEVDE:

     `exponeringsgräns`   avgjorde vilka kort som schemaläggs. LEVDE, och
                          talet 20 var fel: Julius franska dagar var 5, 10,
                          11, 13, 18, 21 meningar. Gränsen kommer nu ur
                          `meningstakt`, mätt ur `Mening`.
     `dagsplan` reservmål meningar × kort_per_mening när takten saknas. Dött —
                          alla kurser har en mätt sekunder-per-repetition — och
                          dessutom precis den sorts konstant som står in för en
                          mätning, vilket funktionen själv dömer ut.
     `dagsplan["mål"]`    skickades till gränssnittet. Ingen läsare i sida.html.

   ATT LÄMNA KVAR EN KOLUMN INGEN LÄSER ÄR EN INBJUDAN ATT LÄSA DEN IGEN. Det
   hände redan en gång: B4 ersatte talet, kommentaren i `db.py` sa "en kolumn
   som ingen längre läser skadar ingen" — och `exponeringsgräns` läste den
   ändå, i en månad, och styrde vilka kort som fick spacing.

   TILLÄGGET I `db.py` MÅSTE BORT SAMTIDIGT. `_migrera` kör ombyggnaderna FÖRE
   tilläggen, så en kvarlämnad rad i `TILLÄGG` hade lagt tillbaka kolumnen i
   samma anrop som den här filen tog bort den.
   ═══════════════════════════════════════════════════════════════════════════ */

ALTER TABLE Kurs DROP COLUMN meningar_per_dag;
