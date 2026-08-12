/* ── variant — diskriminator när ett koncept har flera lemman per språk ──
   21 koncept har två lemman i samma språk. Utan en etikett går de inte att
   skilja åt, och renderaren kan bara gissa. Det tydligaste fallet är svenska
   possessiver: poss_3sg_fem har både "hennes" och "sin", och valet mellan
   dem är rent grammatiskt — "sin" när possessorn är samma som subjektet.

   Etiketterna är beskrivande, inte språkspecifika, så att renderaren kan
   fråga efter samma sak i flera språk (mask/fem gäller både es och fr).

     reflexiv / icke_reflexiv   sv sin vs hans/hennes/deras/dess
     mask / fem                 es nosotros/nosotras, ellos/ellas, fr ils/elles
     familjär / artig           es vosotros vs ustedes, ja 君 vs あなた
     neutral / mask_vardaglig   ja 私 vs 僕
     neutral / vardaglig        ja なぜ vs なんで
     medial / distal            ja その (nära lyssnaren) vs あの (fjärran båda)
     person / sak               ja みんな (om personer) vs すべて (om ting)
     allmän / medel             ja どう vs どうやって (på vilket sätt)
     analytisk / syntetisk      sv "den här" (två ord) vs "denna" (ett)
     sekventiell / retrospektiv de dann (och sedan) vs damals (på den tiden)
     upprepad / engångs_dåtid   de wenn (varje gång) vs als (den gången)
     permanent / tillfällig     es ser vs estar

   Nycklat på koncept + språk + lemma. KÖRS EFTER VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* ── svenska possessiver: reflexiv eller inte ─────────────────────── */
UPDATE Lexem SET variant = 'reflexiv' WHERE språk = 'sv' AND lemma = 'sin'
  AND koncept_id IN (SELECT id FROM Koncept WHERE nyckel IN
      ('poss_3sg_mask', 'poss_3sg_fem', 'poss_3sg_neutr', 'poss_3pl'));
UPDATE Lexem SET variant = 'icke_reflexiv' WHERE språk = 'sv'
  AND lemma IN ('hans', 'hennes', 'dess', 'deras')
  AND koncept_id IN (SELECT id FROM Koncept WHERE nyckel IN
      ('poss_3sg_mask', 'poss_3sg_fem', 'poss_3sg_neutr', 'poss_3pl'));

/* ── genus på pronomen ────────────────────────────────────────────── */
UPDATE Lexem SET variant = 'mask' WHERE språk = 'es' AND lemma = 'nosotros'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_1pl');
UPDATE Lexem SET variant = 'fem' WHERE språk = 'es' AND lemma = 'nosotras'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_1pl');
UPDATE Lexem SET variant = 'mask' WHERE språk = 'es' AND lemma = 'ellos'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3pl');
UPDATE Lexem SET variant = 'fem' WHERE språk = 'es' AND lemma = 'ellas'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3pl');
UPDATE Lexem SET variant = 'mask' WHERE språk = 'fr' AND lemma = 'ils'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3pl');
UPDATE Lexem SET variant = 'fem' WHERE språk = 'fr' AND lemma = 'elles'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_3pl');

/* ── tilltal: familjärt eller artigt ──────────────────────────────── */
UPDATE Lexem SET variant = 'familjär' WHERE språk = 'es' AND lemma = 'vosotros'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_2pl');
UPDATE Lexem SET variant = 'artig' WHERE språk = 'es' AND lemma = 'ustedes'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_2pl');
UPDATE Lexem SET variant = 'familjär' WHERE språk = 'es' AND lemma = 'vuestro'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'poss_2pl');
UPDATE Lexem SET variant = 'artig' WHERE språk = 'es' AND lemma = 'su'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'poss_2pl');
UPDATE Lexem SET variant = 'familjär' WHERE språk = 'ja' AND lemma = '君'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_2sg');
UPDATE Lexem SET variant = 'neutral' WHERE språk = 'ja' AND lemma = 'あなた'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_2sg');
UPDATE Lexem SET variant = 'familjär' WHERE språk = 'ja' AND lemma = '君の'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'poss_2sg');
UPDATE Lexem SET variant = 'neutral' WHERE språk = 'ja' AND lemma = 'あなたの'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'poss_2sg');

/* ── japanska förstapersonsord ────────────────────────────────────── */
UPDATE Lexem SET variant = 'neutral' WHERE språk = 'ja' AND lemma = '私'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_1sg');
UPDATE Lexem SET variant = 'mask_vardaglig' WHERE språk = 'ja' AND lemma = '僕'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pronomen_1sg');
UPDATE Lexem SET variant = 'neutral' WHERE språk = 'ja' AND lemma = '私の'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'poss_1sg');
UPDATE Lexem SET variant = 'mask_vardaglig' WHERE språk = 'ja' AND lemma = '僕の'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'poss_1sg');

/* ── japanska demonstrativer och frågeord ─────────────────────────── */
UPDATE Lexem SET variant = 'medial' WHERE språk = 'ja' AND lemma = 'その'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'demonstrativ_fjärran');
UPDATE Lexem SET variant = 'distal' WHERE språk = 'ja' AND lemma = 'あの'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'demonstrativ_fjärran');
UPDATE Lexem SET variant = 'neutral' WHERE språk = 'ja' AND lemma = 'なぜ'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'frågadverb_orsak');
UPDATE Lexem SET variant = 'vardaglig' WHERE språk = 'ja' AND lemma = 'なんで'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'frågadverb_orsak');
UPDATE Lexem SET variant = 'allmän' WHERE språk = 'ja' AND lemma = 'どう'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'frågadverb_sätt');
UPDATE Lexem SET variant = 'medel' WHERE språk = 'ja' AND lemma = 'どうやって'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'frågadverb_sätt');
UPDATE Lexem SET variant = 'person' WHERE språk = 'ja' AND lemma = 'みんな'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kvant_alla');
UPDATE Lexem SET variant = 'sak' WHERE språk = 'ja' AND lemma = 'すべて'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kvant_alla');

/* ── svensk demonstrativ: två ord eller ett ───────────────────────── */
UPDATE Lexem SET variant = 'analytisk' WHERE språk = 'sv' AND lemma = 'den här'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'demonstrativ_nara');
UPDATE Lexem SET variant = 'syntetisk' WHERE språk = 'sv' AND lemma = 'denna'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'demonstrativ_nara');

/* ── tyska: dann/damals och wenn/als ──────────────────────────────── */
UPDATE Lexem SET variant = 'sekventiell' WHERE språk = 'de' AND lemma = 'dann'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'adv_då');
UPDATE Lexem SET variant = 'retrospektiv' WHERE språk = 'de' AND lemma = 'damals'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'adv_då');
UPDATE Lexem SET variant = 'upprepad' WHERE språk = 'de' AND lemma = 'wenn'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'subj_när');
UPDATE Lexem SET variant = 'engångs_dåtid' WHERE språk = 'de' AND lemma = 'als'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'subj_när');

/* ── spanska ser/estar ────────────────────────────────────────────── */
UPDATE Lexem SET variant = 'permanent' WHERE språk = 'es' AND lemma = 'ser'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_vara');
UPDATE Lexem SET variant = 'tillfällig' WHERE språk = 'es' AND lemma = 'estar'
  AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_vara');
