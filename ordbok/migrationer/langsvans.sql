/* ── långsvansen — de åtta bearbetningsverben ────────────────────────
   reparera, tvätta, måla, skära, bryta, blanda, fylla, bygga. De stod kvar
   med KONKRET efter restriktioner.sql, och det var de som producerade
   "Pappan bryter en full mamma" i mätningen av hela kedjan.

   Tre nya bitar, två återanvända:

     1048576  KONSTRUERAD   tillverkat föremål — reparera, bryta, bygga
     2097152  BEHÅLLARE     kan fyllas — fylla
     4194304  YTA           har en yta att måla eller tvätta

     HANTERBAR (262144)     skära och blanda — det man kan hantera

   Platser taggas ORD FÖR ORD: hus, kontor och kök är byggda, men berg, hav,
   himmel, sjö, skog, strand och värld är det inte. Klassen KONKRET+PLATS
   duger alltså inte som helhet, vilket är tredje gången en bit inte följer
   de befintliga klasserna (jfr ÖPPNINGSBAR och adjektivens attributkrav).

   En medveten förlust: "bryta armen" går inte att bygga, eftersom armen
   inte är ett tillverkat föremål. Alternativet hade varit att ge kroppsdelar
   KONSTRUERAD, vilket också hade tillåtit "reparera en arm" och "bygga ett
   ben". Med OCH-matchning går "KONSTRUERAD eller KROPPSDEL" inte att
   uttrycka; se RESTRIKTIONER.md.

   Klassjämförelsen maskar med 131071 — de SEXTON ursprungliga bitarna plus
   NATURFENOMEN. Att maska bredare tar med ÖVERLÅTBAR och HANTERBAR som
   restriktioner.sql redan satt, och då matchar ingen klass längre. Samma
   fälla som 65535/65536-buggen, en nivå upp.

   KÖRS EFTER restriktioner.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* Nollställ de tre nya bitarna så att filen är idempotent. */
UPDATE Koncept SET semantik = semantik & 1048575 WHERE ordklass = 'Substantiv';


/* ── KONSTRUERAD ─────────────────────────────────────── */

UPDATE Koncept SET semantik = semantik | 1048576 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 16386;
UPDATE Koncept SET semantik = semantik | 1048576 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 32770;
UPDATE Koncept SET semantik = semantik | 1048576 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 1090;
UPDATE Koncept SET semantik = semantik | 1048576 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 1026;
UPDATE Koncept SET semantik = semantik | 1048576 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 2050;
UPDATE Koncept SET semantik = semantik | 1048576 WHERE nyckel IN
  ('plats_affär', 'plats_apotek', 'hem_badrum', 'plats_bar', 'plats_bibliotek', 'trans_busshållplats', 'plats_café', 'trans_flygplats', 'plats_hem', 'hem_hus', 'plats_kontor', 'plats_kyrka', 'hem_kök', 'hem_lägenhet', 'plats_marknad', 'plats_park', 'plats_restaurang', 'hem_rum', 'plats_sjukhus', 'hem_skafferi', 'plats_skola', 'hem_toalett', 'trans_tågstation', 'plats_universitet', 'plats_väg', 'trans_biljett', 'häls_medicin', 'skol_papper', 'skol_väska');

/* ── BEHÅLLARE ─────────────────────────────────────── */

UPDATE Koncept SET semantik = semantik | 2097152 WHERE nyckel IN
  ('skol_väska', 'hem_rum', 'hem_hus', 'hem_lägenhet', 'hem_kylskåp', 'hem_frys', 'hem_ugn', 'hem_bokhylla', 'hem_byrå', 'hem_skafferi', 'hem_kök', 'hem_badrum', 'hem_toalett', 'trans_bil', 'trans_buss', 'trans_båt', 'trans_flygplan', 'trans_tåg', 'plats_affär', 'plats_restaurang', 'plats_café');

/* ── YTA ─────────────────────────────────────── */

UPDATE Koncept SET semantik = semantik | 4194304 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 16386;
UPDATE Koncept SET semantik = semantik | 4194304 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 32770;
UPDATE Koncept SET semantik = semantik | 4194304 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 1090;
UPDATE Koncept SET semantik = semantik | 4194304 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 1026;
UPDATE Koncept SET semantik = semantik | 4194304 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 2050;
UPDATE Koncept SET semantik = semantik | 4194304 WHERE ordklass = 'Substantiv' AND semantik & 131071 = 8194;
UPDATE Koncept SET semantik = semantik | 4194304 WHERE nyckel IN
  ('plats_affär', 'plats_apotek', 'hem_badrum', 'plats_bar', 'plats_bibliotek', 'trans_busshållplats', 'plats_café', 'trans_flygplats', 'plats_hem', 'hem_hus', 'plats_kontor', 'plats_kyrka', 'hem_kök', 'hem_lägenhet', 'plats_marknad', 'plats_park', 'plats_restaurang', 'hem_rum', 'plats_sjukhus', 'hem_skafferi', 'plats_skola', 'hem_toalett', 'trans_tågstation', 'plats_universitet', 'plats_väg', 'trans_biljett', 'häls_medicin', 'skol_papper', 'skol_väska');

/* ── verben ───────────────────────────────────────── */

UPDATE MönsterKrav SET tagg = 1048576 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('fys_reparera', 'fys_bryta', 'fys_bygga'));
UPDATE MönsterKrav SET tagg = 2097152 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('fys_fylla'));
UPDATE MönsterKrav SET tagg = 4194304 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('gen_måla', 'fys_tvätta'));
UPDATE MönsterKrav SET tagg = 262144 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('fys_skära', 'fys_blanda'));
