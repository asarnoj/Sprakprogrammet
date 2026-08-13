/* ── prepositionsrektion ─────────────────────────────────────────────
   Tyska prepositioner styr kasus på sitt komplement, och det måste läras
   per preposition: "mit dem Buch" men "für das Buch".

   Samma mekanism som verbens rektion — ett Mönster med språk satt, på
   PREPOSITIONENS koncept. Överlämningen noterade att schemat tillåter
   prepositioner som styrande ord men att ingen taggat dem; det här är den
   taggningen.

   Fyra grupper. De tre första är fasta. Den fjärde — Wechselpräpositionen —
   styr dativ vid befintlighet och ackusativ vid rörelse: "im Haus" (var)
   mot "ins Haus" (vart). Skillnaden är semantisk och ligger i verbet, inte
   i prepositionen. Här taggas de som DATIV, vilket är rätt för adverbial
   som anger plats — det vanliga fallet. Rörelseriktning kräver att
   Mening kan uttrycka mål, vilket den inte kan.

   kasus-koder: Nom=1, Ack=2, Dat=4, Gen=8.
   KÖRS EFTER rektion.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

INSERT INTO Mönster (koncept_id, språk)
SELECT id, 'de' FROM Koncept WHERE ordklass = 'Preposition';

/* dativ: von, nach, mit, zu, bei */
INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'komplement', 4 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de' AND k.nyckel IN
  ('prep_av', 'prep_efter', 'prep_från', 'prep_med', 'prep_till', 'prep_vid');

/* ackusativ: gegen, für, durch, ohne, entlang */
INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'komplement', 2 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de' AND k.nyckel IN
  ('prep_emot', 'prep_för', 'prep_genom', 'prep_utan', 'prep_längs');

/* genitiv: trotz, innerhalb, außerhalb, in Richtung */
INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'komplement', 8 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de' AND k.nyckel IN
  ('prep_trots', 'prep_innanför', 'prep_utanför', 'prep_mot');

/* Wechselpräpositionen — dativ som förval, se filhuvudet */
INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'komplement', 4 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de' AND k.nyckel IN
  ('prep_bakom', 'prep_bland', 'prep_bredvid', 'prep_framför', 'prep_före',
   'prep_i', 'prep_mellan', 'prep_om', 'prep_på', 'prep_under', 'prep_över');
