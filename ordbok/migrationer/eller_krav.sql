/* ── ELLER-krav — disjunktiv normalform ──────────────────────────────
   Flera rader för samma slot betyder ELLER. Tre krav visade sig omöjliga
   att uttrycka med enbart OCH, och alla tre hade kringgåtts med en bredare
   bit eller en accepterad förlust:

     bryta   KONSTRUERAD eller KROPPSDEL   "bryta armen" gick inte att bygga
     blanda  ÄTBAR eller DRICKBAR          löstes med HANTERBAR, för brett
     snabb   RÖRELSE eller ANIMAT          en snabb bil, en snabb pojke

   Ingen av dem har en gemensam bit, och ingen bredare bit fångar bara dem.

   KÖRS EFTER langsvans.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* ── bryta: tillverkat föremål ELLER kroppsdel ────────────────────── */
INSERT INTO MönsterKrav (mönster_id, slot, tagg)
SELECT m.id, 'objekt', 8192 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk IS NULL AND k.nyckel = 'fys_bryta';

/* ── blanda: ätbart ELLER drickbart, i stället för det bredare HANTERBAR */
UPDATE MönsterKrav SET tagg = 8 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel = 'fys_blanda');
INSERT INTO MönsterKrav (mönster_id, slot, tagg)
SELECT m.id, 'objekt', 4096 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk IS NULL AND k.nyckel = 'fys_blanda';

/* ── snabb och långsam: något som rör sig ELLER någon som lever ───── */
INSERT INTO Attributkrav (koncept_id, tagg)
SELECT id, 64 FROM Koncept WHERE nyckel IN ('adj_s_snabb', 'adj_s_långsam');
INSERT INTO Attributkrav (koncept_id, tagg)
SELECT id, 1 FROM Koncept WHERE nyckel IN ('adj_s_snabb', 'adj_s_långsam');

/* ── möjlig, omöjlig, nödvändig: bara abstrakta ting ──────────────── */
INSERT INTO Attributkrav (koncept_id, tagg)
SELECT id, 4 FROM Koncept
WHERE nyckel IN ('adj_m_möjlig', 'adj_m_omöjlig', 'adj_m_nödvändig');
