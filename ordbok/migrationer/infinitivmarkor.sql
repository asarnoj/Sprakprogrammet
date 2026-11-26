/* ── infinitivmarkör — att, to, zu, à, di ────────────────────────────
   Vilken markör ett verb kräver framför sitt infinitivkomplement är
   LEXIKALT och skiljer sig mellan språken: "hon vill läsa" men "hon
   börjar att läsa", "she wants TO read" men "she can read", "sie will
   lesen" men "sie versucht ZU lesen".

   Ingen rad = ren infinitiv utan markör. Det är därför modalverben mest
   lyser med sin frånvaro här.

   Mekanismen är den från rektion.sql: ett Mönster med språk satt skuggar
   det universella och bär bara det som skiljer. Samma kolumn
   (preposition_koncept_id) som det romanska indirekta objektet använder.

   KÖRS EFTER rektion.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* Idempotent: rensa tidigare komplementkrav och deras mönster först. */
DELETE FROM MönsterKrav WHERE slot = 'komplement'
  AND mönster_id IN (SELECT id FROM Mönster WHERE språk IS NOT NULL);
DELETE FROM Mönster WHERE språk IS NOT NULL AND id NOT IN
  (SELECT mönster_id FROM MönsterKrav);

INSERT INTO Mönster (koncept_id, språk)
SELECT k.id, s.språk FROM Koncept k
JOIN (SELECT 'sv' AS språk UNION SELECT 'en' UNION SELECT 'de'
      UNION SELECT 'fr' UNION SELECT 'es' UNION SELECT 'it') s
WHERE k.nyckel IN ('asp_börja','asp_sluta','asp_fortsätta','gen_försöka',
                   'käns_hoppas','modal_brukar','modal_vill','modal_ska');

/* svenska: att på allt utom modalverben */
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='subj_att')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id WHERE m.språk='sv'
  AND k.nyckel IN ('asp_börja','asp_sluta','asp_fortsätta','gen_försöka','käns_hoppas');

/* engelska: to — även på want och tend, som inte är riktiga modalverb */
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_till')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id WHERE m.språk='en'
  AND k.nyckel IN ('asp_börja','asp_sluta','asp_fortsätta','gen_försöka',
                   'käns_hoppas','modal_brukar','modal_vill');

/* tyska: zu på allt utom de sex äkta modalverben */
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_till')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id WHERE m.språk='de'
  AND k.nyckel IN ('asp_börja','asp_sluta','asp_fortsätta','gen_försöka',
                   'käns_hoppas','modal_brukar');

/* romanska: à/a på inkoativa och durativa, de/di på avslutande och
   försökande. Uppdelningen är godtycklig ur inlärarens synvinkel och
   måste helt enkelt läras per verb — vilket är precis varför den ligger
   i datan och inte i en regel. */
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_till')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk IN ('fr','es','it') AND k.nyckel IN ('asp_börja','asp_fortsätta');
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_av')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk IN ('fr','es','it') AND k.nyckel = 'asp_sluta';
/* försöka: fr essayer DE, it provare A, es intentar utan markör alls.
   Tre språk, tre svar på samma verb — och ingen av dem går att härleda. */
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_av')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'fr' AND k.nyckel = 'gen_försöka';
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_till')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'it' AND k.nyckel IN ('gen_försöka', 'asp_börja');
/* it sperare di, es esperar utan markör */
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_av')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'it' AND k.nyckel = 'käns_hoppas';
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_av')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'fr' AND k.nyckel = 'modal_brukar';
INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'komplement', (SELECT id FROM Koncept WHERE nyckel='prep_till')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'es' AND k.nyckel = 'modal_ska';
