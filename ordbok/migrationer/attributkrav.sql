/* ── attributkrav — vad ett adjektiv får beskriva ────────────────────
   Bitmask som HUVUDORDET måste uppfylla. NULL = adjektivet passar allt.
   Se paradigm/RESTRIKTIONER.md och setup.sql om varför det är en kolumn
   och inte en MönsterKrav-rad.

   Taggat PER ORD, inte per grupp. Konceptnycklarnas andra led (adj_ev_,
   adj_es_, färg_) bar substantivens kategorier bra nog att lyftas rakt in
   i bitmasken, men adjektivens gör det inte: adj_ev_ innehåller både
   "snäll" (kräver levande) och "viktig" (kräver ingenting alls). Samma
   lärdom som ÖPPNINGSBAR gav — se RESTRIKTIONER.md.

   Fyra krav används, alla återanvända bitar:

     ANIMAT (1)        känslor och personlighet — en glad bok finns inte
     KONKRET (2)       färg, temperatur, textur — en röd idé finns inte
     ÖVERLÅTBAR (131072)  pris — bara det som kan byta ägare har ett
     ÖPPNINGSBAR (524288) öppen/stängd — bara det med öppning

   KÖRS EFTER restriktioner.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* ── kräver ANIMAT: känslotillstånd ───────────────────────────────── */
UPDATE Koncept SET attributkrav = 1 WHERE ordklass = 'Adjektiv' AND nyckel IN (
  'adj_es_arg', 'adj_es_ensam', 'adj_es_frisk', 'adj_es_förvånad',
  'adj_es_glad', 'adj_es_hungrig', 'adj_es_kär', 'adj_es_ledsen',
  'adj_es_nervös', 'adj_es_nöjd', 'adj_es_rädd', 'adj_es_sjuk',
  'adj_es_skamsen', 'adj_es_stressad', 'adj_es_trött', 'adj_es_törstig');

/* ── kräver ANIMAT: personlighet och beteende ─────────────────────── */
UPDATE Koncept SET attributkrav = 1 WHERE ordklass = 'Adjektiv' AND nyckel IN (
  'adj_ev_besviken', 'adj_ev_dum', 'adj_ev_elak', 'adj_ev_flitig',
  'adj_ev_intresserad', 'adj_ev_lat', 'adj_ev_modig', 'adj_ev_nyfiken',
  'adj_ev_snäll', 'adj_ev_stolt', 'adj_ev_ärlig', 'adj_ev_lugn');

/* ── kräver ANIMAT: liv och ålder ─────────────────────────────────── */
UPDATE Koncept SET attributkrav = 1 WHERE ordklass = 'Adjektiv' AND nyckel IN (
  'adj_k_död', 'adj_k_levande', 'adj_k_ung');

/* ── kräver KONKRET: färg ─────────────────────────────────────────── */
UPDATE Koncept SET attributkrav = 2 WHERE ordklass = 'Adjektiv'
  AND nyckel LIKE 'färg\_%' ESCAPE '\';

/* ── kräver KONKRET: temperatur, textur, vikt ─────────────────────── */
UPDATE Koncept SET attributkrav = 2 WHERE ordklass = 'Adjektiv' AND nyckel IN (
  'adj_t_het', 'adj_t_hård', 'adj_t_kall', 'adj_t_mjuk', 'adj_t_skarp',
  'adj_t_sval', 'adj_t_torr', 'adj_t_tung', 'adj_t_varm', 'adj_t_våt');
/* adj_t_lätt utelämnat: "ett lätt problem" är standardsvenska. */

/* ── kräver KONKRET: fysiskt tillstånd ────────────────────────────── */
UPDATE Koncept SET attributkrav = 2 WHERE ordklass = 'Adjektiv' AND nyckel IN (
  'adj_k_smutsig', 'adj_k_ren', 'adj_k_trasig', 'adj_k_tom', 'adj_k_full');

/* ── kräver KONKRET: form ─────────────────────────────────────────── */
UPDATE Koncept SET attributkrav = 2 WHERE ordklass = 'Adjektiv' AND nyckel IN (
  'adj_s_rund', 'adj_s_bred', 'adj_s_smal', 'adj_s_tjock', 'adj_s_tunn');
/* stor, liten, lång, kort, hög, djup utelämnade: "en stor idé", "en lång
   dag", "kort tid" är alla standardsvenska. Storlek är metaforiskt
   produktiv på ett sätt som form inte är. */

/* ── kräver ÖVERLÅTBAR: pris ──────────────────────────────────────── */
UPDATE Koncept SET attributkrav = 131072 WHERE ordklass = 'Adjektiv'
  AND nyckel IN ('adj_eko_billig', 'adj_eko_dyr', 'adj_eko_gratis');

/* ── kräver ÖPPNINGSBAR ───────────────────────────────────────────── */
UPDATE Koncept SET attributkrav = 524288 WHERE ordklass = 'Adjektiv'
  AND nyckel IN ('adj_k_öppen', 'adj_k_stängd');
