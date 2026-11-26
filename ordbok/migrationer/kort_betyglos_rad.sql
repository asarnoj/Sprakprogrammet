/* ── Repetition: raden får finnas utan betyg ─────────────────────────
   Mot kort.db (inlärardatabasen), inte sprak.db.

   VARFÖR. Ett kort vars skuld inte gick att avgöra fick förut ingen rad
   alls. Regeln som skyddar mot dubbla bedömningar samma dygn — `_redan_idag`
   i schemalaggning.py — läser just `Repetition`-rader från dygnets början,
   och såg därför inte det undanhållna kortet över huvud taget. Kortet behöll
   dessutom sitt passerade förfallodatum, stod alltså kvar i kön, och plockades
   gärna till nästa mening. Under tiden hade användaren sett facit.

   Mätt vad det kostade: klarades kortet i nästa mening fick det ett fullt
   Good med hela den förflutna tiden inräknad, och stabiliteten hoppade
   10,96 → 46,28 i stället för till ~11.

   En rad UTAN betyg löser det utan att en enda rad i `_redan_idag` ändras:
   `graderade` fångar raden, så ett RÄTT senare samma dygn hoppas över, medan
   `fällda` filtrerar på betyg = FEL och därför släpper igenom ett FEL. Den
   asymmetrin är exakt E2:s och ska bevaras — att inte kunna något vars svar
   man nyss sett är information, tvärtemot.

   SQLite kan inte lätta på NOT NULL eller byta CHECK, så tabellen byggs om.
   Raderna kopieras oförändrade; `skäl` blir NULL för allt som redan finns,
   vilket är riktigt — de raderna ÄR bedömningar.

   Kör:  sqlite3 kort.db < ordbok/migrationer/kort_betyglos_rad.sql
   ─────────────────────────────────────────────────────────────────────── */

PRAGMA foreign_keys = OFF;

BEGIN;

CREATE TABLE Repetition_ny (
    id        INTEGER PRIMARY KEY,
    kort_id   INTEGER NOT NULL REFERENCES Kort(id) ON DELETE CASCADE,
    mening_id INTEGER          REFERENCES Mening(id) ON DELETE SET NULL,
    tidpunkt  TEXT    NOT NULL,
    betyg     INTEGER          CHECK (betyg IS NULL OR betyg IN (1, 2, 3, 4)),
    skäl      TEXT             CHECK (skäl IS NULL OR skäl IN
                                      ('undanhållen', 'skyddad', 'visad')),
    förfluten REAL,
    r_före    REAL,
    stabilitet REAL,
    svårighet  REAL,
    självrättad INTEGER NOT NULL DEFAULT 0 CHECK (självrättad IN (0, 1)),

    /* Exakt ett av dem, aldrig båda och aldrig ingetdera: raden är ANTINGEN
       en bedömning ELLER en anteckning om att ingen bedömning gjordes. */
    CHECK ((betyg IS NULL AND skäl IS NOT NULL)
        OR (betyg IS NOT NULL AND skäl IS NULL))
);

INSERT INTO Repetition_ny
    (id, kort_id, mening_id, tidpunkt, betyg, skäl,
     förfluten, r_före, stabilitet, svårighet, självrättad)
SELECT
     id, kort_id, mening_id, tidpunkt, betyg, NULL,
     förfluten, r_före, stabilitet, svårighet, självrättad
FROM Repetition;

DROP TABLE Repetition;
ALTER TABLE Repetition_ny RENAME TO Repetition;

CREATE INDEX idx_repetition_kort ON Repetition(kort_id, tidpunkt);

COMMIT;

PRAGMA foreign_keys = ON;
