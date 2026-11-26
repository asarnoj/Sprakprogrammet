/* ═══════════════════════════════════════════════════════════════════════════
   PASSKORT FÅR EN FEMTE ROLL: `övervakad`

   Ett kort med `schemalagt = 0` möts oftare än en gång om dagen, och FSRS
   kortaste meningsfulla intervall är ett dygn — spacing har alltså ingen spak
   att dra i (`exponeringsgräns`). Flaggan togs fram som en NEGATION och
   lämnade kortet utan mått: det betygsattes, men ingenting läste betygen, och
   ett övervakat kort som gick sönder kunde aldrig komma tillbaka i sikte.

   `Schemaläggare.i_larm` är avläsningen, och den behöver en väg in i passet.
   Rollen är egen och inte `förfallen`, därför att de två vilar på olika
   grunder: `förfallen` kommer ur en förfallodag, `övervakad` ur en rullande
   andel rätt. Att kalla dem samma sak hade dolt att kortet saknar det första.

   ROLLERNA SUMMERAR TILL `väntar`, och det är ett faktum gränssnittet ärver
   (`läget`s `delar`). En femte roll som inte står med i uppräkningen hade
   brutit summan tyst — exakt det fel som `nya − glosor` en gång var.
   ═══════════════════════════════════════════════════════════════════════════ */

CREATE TABLE IF NOT EXISTS Passkort_ny (
    id      INTEGER PRIMARY KEY,
    pass_id INTEGER NOT NULL REFERENCES Pass(id) ON DELETE CASCADE,
    /* NULL betyder att kortet är borta — se `passkort_bevara_bevis.sql`. */
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
