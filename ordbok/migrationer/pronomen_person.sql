/* ── pronomen_person — person och numerus på pronomen och possessiver ──────
   Fälten är dokumenterade i setup.sql men har aldrig fyllts. Renderaren
   behöver dem för verbkongruens: "jag springer" mot "de springer" kan inte
   avgöras utan att veta att pronomen_1sg är första person singular.

   Härleds exakt ur konceptnyckeln — inget LLM-pass behövs.

   numerus lämnas NULL där konceptet täcker båda talen (sig, som är samma
   form för han/hon/de).

   KÖRS EFTER VARJE `ordbok import`.
   ─────────────────────────────────────────────────────────────────────── */

/* ── Person ──────────────────────────────────────────────────────────── */
UPDATE Koncept SET person = 1 WHERE nyckel IN
  ('pronomen_1sg', 'pronomen_1pl', 'poss_1sg', 'poss_1pl');

UPDATE Koncept SET person = 2 WHERE nyckel IN
  ('pronomen_2sg', 'pronomen_2sg_formal', 'pronomen_2pl',
   'poss_2sg', 'poss_2sg_formal', 'poss_2pl');

UPDATE Koncept SET person = 3 WHERE nyckel IN
  ('pronomen_3sg_mask', 'pronomen_3sg_fem', 'pronomen_3sg_neutr',
   'pronomen_3pl', 'pronomen_reflexiv', 'pronomen_impersonal',
   'poss_3sg_mask', 'poss_3sg_fem', 'poss_3sg_neutr', 'poss_3pl');

/* ── Numerus ─────────────────────────────────────────────────────────── */
UPDATE Koncept SET numerus = 1 WHERE nyckel IN
  ('pronomen_1sg', 'pronomen_2sg', 'pronomen_2sg_formal',
   'pronomen_3sg_mask', 'pronomen_3sg_fem', 'pronomen_3sg_neutr',
   'pronomen_impersonal',
   'poss_1sg', 'poss_2sg', 'poss_2sg_formal',
   'poss_3sg_mask', 'poss_3sg_fem', 'poss_3sg_neutr');

UPDATE Koncept SET numerus = 2 WHERE nyckel IN
  ('pronomen_1pl', 'pronomen_2pl', 'pronomen_3pl',
   'poss_1pl', 'poss_2pl', 'poss_3pl');

/* pronomen_reflexiv (sig) täcker både singular och plural — numerus NULL. */
