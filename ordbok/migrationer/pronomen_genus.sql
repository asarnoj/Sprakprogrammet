/* ── pronomengenus ───────────────────────────────────────────────────
   Tredje personens pronomen bär genus, och det styr kongruens:
   "elle est heureuse", "det är glatt", "sie ist gegangen".

   Utan det defaultar renderaren till maskulinum och producerar
   "elle est heureux". Hittat när predikativet byggdes 2026-08-13.

   Första och andra person lämnas NULL med flit — "jag är glad" säger
   ingenting om talarens kön, och där det spelar roll uttrycks det med
   Referentgenus i meningsspecifikationen i stället.

   Genuskoderna är språkspecifika (BITMASK.md §5): sv 1=utrum 2=neutrum,
   de 1=mask 2=fem 3=neutr, fr/es/it 1=mask 2=fem.

   KÖRS EFTER VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* svenska: han och hon är utrum, det är neutrum */
UPDATE Lexem SET genus = 1 WHERE språk = 'sv' AND koncept_id IN
  (SELECT id FROM Koncept WHERE nyckel IN ('pronomen_3sg_mask', 'pronomen_3sg_fem'));
UPDATE Lexem SET genus = 2 WHERE språk = 'sv' AND koncept_id IN
  (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3sg_neutr');

/* tyska: er/sie/es */
UPDATE Lexem SET genus = 1 WHERE språk = 'de' AND koncept_id IN
  (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3sg_mask');
UPDATE Lexem SET genus = 2 WHERE språk = 'de' AND koncept_id IN
  (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3sg_fem');
UPDATE Lexem SET genus = 3 WHERE språk = 'de' AND koncept_id IN
  (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3sg_neutr');

/* romanska: il/elle, él/ella, lui/lei */
UPDATE Lexem SET genus = 1 WHERE språk IN ('fr', 'es', 'it') AND koncept_id IN
  (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3sg_mask');
UPDATE Lexem SET genus = 2 WHERE språk IN ('fr', 'es', 'it') AND koncept_id IN
  (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3sg_fem');

/* könsskilda pluralpronomen: ils/elles, ellos/ellas, nosotros/nosotras */
UPDATE Lexem SET genus = 1 WHERE variant = 'mask' AND språk IN ('fr', 'es');
UPDATE Lexem SET genus = 2 WHERE variant = 'fem'  AND språk IN ('fr', 'es');
