/* ── restriktioner — tre nya semantikbitar ──────────────────────────
   Se paradigm/RESTRIKTIONER.md. Bitarna är POSITIVA påståenden om världen,
   inte förbud knutna till enskilda verb — därför räcker en matchningsregel
   (OCH) och därför återanvänds de mellan verb.

     131072  ÖVERLÅTBAR    kan byta ägare (ge, sälja, låna, köpa, erbjuda)
     262144  HANTERBAR     kan lyftas och bäras för hand
     524288  ÖPPNINGSBAR   har en öppning (öppna, stänga)

   ÖVERLÅTBAR och HANTERBAR taggas KLASSVIS — de befintliga semantikklasserna
   är sammanhängande nog. Två medvetna förluster:

     Kroppsdelar är inte HANTERBAR. "lyfta handen" går därmed inte att
     bygga, men "kasta en näsa" stoppas. Det var det viktigare av de två.

     Inredning är inte HANTERBAR. "lyfta lampan" faller bort tillsammans
     med "bära en vägg".

   ÖPPNINGSBAR följer INGEN befintlig klass — dörr och fönster är INREDNING,
   mun och öga är KROPPSDEL, affär är PLATS, bok är KOMMUNIKAT. Den taggas
   därför per ord, och det är den enda av de tre som gör det.

   KÖRS EFTER semantik_utökad.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */


/* ── substantiv, klassvis ─────────────────────────── */

UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 2;
UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 3;
UPDATE Koncept SET semantik = semantik | 131072 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 4;
UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 10;
UPDATE Koncept SET semantik = semantik | 131072 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 18;
UPDATE Koncept SET semantik = semantik | 131072 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 260;
UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 1026;
UPDATE Koncept SET semantik = semantik | 131072 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 1090;
UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 2050;
UPDATE Koncept SET semantik = semantik | 131072 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 2052;
UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 4098;
UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 4106;
UPDATE Koncept SET semantik = semantik | 393216 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 16386;
UPDATE Koncept SET semantik = semantik | 131072 WHERE ordklass = 'Substantiv' AND semantik & 65535 = 32770;

/* ── ÖPPNINGSBAR, per ord ─────────────────────────── */

UPDATE Koncept SET semantik = semantik | 524288 WHERE nyckel IN
  ('hem_dörr', 'hem_fönster', 'hem_kylskåp', 'hem_frys', 'hem_ugn', 'hem_byrå', 'skol_bok', 'skol_väska', 'plats_affär', 'plats_apotek', 'plats_bar', 'plats_bibliotek', 'plats_café', 'plats_restaurang', 'plats_kontor', 'krop_mun', 'krop_öga');

/* ── verben: byt ut den trubbiga KONKRET-biten ────── */

UPDATE MönsterKrav SET tagg = 131072 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('fys_ge', 'fys_ta', 'fys_köpa', 'fys_sälja', 'eko_v_låna', 'eko_v_äga', 'eko_v_tjäna', 'arb_betala', 'gen_dela', 'rör_byta', 'gen_erbjuda'));
UPDATE MönsterKrav SET tagg = 262144 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('fys_bära', 'fys_dra', 'fys_kasta', 'fys_lyfta', 'fys_lägga', 'fys_hålla', 'fys_trycka', 'fys_samla'));
UPDATE MönsterKrav SET tagg = 524288 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('fys_öppna', 'fys_stänga'));
UPDATE MönsterKrav SET tagg = 1088 WHERE slot = 'objekt'
  AND mönster_id IN (SELECT m.id FROM Mönster m JOIN Koncept k
    ON k.id = m.koncept_id WHERE m.språk IS NULL AND k.nyckel IN ('rör_köra'));
