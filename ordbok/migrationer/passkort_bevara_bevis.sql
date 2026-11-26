/* ═══════════════════════════════════════════════════════════════════════════
   PASSKORT.KORT_ID FÅR INTE KASKADRADERAS

   `ON DELETE CASCADE` kastade bevis. Nollställer man en kurs raderas alla
   dess kort, och kaskaden tog då med sig passets rader — kvar blev ett Pass
   utan innehåll. Noll rader betyder "inget väntar", alltså `klar`, och
   `starta` är idempotent: den hittade det tomma passet och byggde aldrig om.
   Resultatet var "Done for today" på en kurs man just nollställt.

   Värre: passet är knutet till KURSEN medan kortbeståndet är per MÅLSPRÅK.
   Två kurser mot franska delar kort, så en nollställning av den ena tömde
   den andras pass utan att någon rört den.

   PROJEKTETS EGEN REGEL SÄGER VAD SOM ÄR FEL: kasta aldrig bevis du HAR.
   Att raden pekar på ett kort som inte längre finns ÄR upplysningen — det är
   så man vet att passet byggdes ur ett bestånd som är borta. `SET NULL`
   bevarar den; `CASCADE` förstörde den.

   Med beviset kvar blir giltigheten HÄRLEDD i stället för ihågkommen: ett
   pass är giltigt så länge varje rad har ett kort. Det spelar då ingen roll
   VEM som raderade korten — webbgränssnittet, `ordbok kort`, en framtida
   väg som ingen tänkt på — eftersom regeln läser data och inte anrop.
   ═══════════════════════════════════════════════════════════════════════════ */

CREATE TABLE IF NOT EXISTS Passkort_ny (
    id      INTEGER PRIMARY KEY,
    pass_id INTEGER NOT NULL REFERENCES Pass(id) ON DELETE CASCADE,
    /* NULL betyder att kortet är borta — se ovan. Kolumnen är därför
       nullbar, och det är inte en uppmjukning utan hela poängen. */
    kort_id INTEGER REFERENCES Kort(id) ON DELETE SET NULL,
    roll    TEXT    NOT NULL
            CHECK (roll IN ('förfallen', 'ny', 'glosa', 'igen', 'övervakad')),
    ordning INTEGER NOT NULL,
    status  TEXT    NOT NULL DEFAULT 'väntar'
            CHECK (status IN ('väntar', 'rätt', 'fel', 'onåbar')),
    tidpunkt TEXT
);

INSERT INTO Passkort_ny (id, pass_id, kort_id, roll, ordning, status, tidpunkt)
SELECT id, pass_id, kort_id, roll, ordning, status, tidpunkt FROM Passkort;

DROP TABLE Passkort;
ALTER TABLE Passkort_ny RENAME TO Passkort;

CREATE INDEX IF NOT EXISTS idx_passkort_pass ON Passkort(pass_id, status);
