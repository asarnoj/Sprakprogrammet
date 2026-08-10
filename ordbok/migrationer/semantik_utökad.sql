/* ── semantik_utökad — fem nya semantikbitar ────────────────────────────────
   Bakgrund (2026-08-10): mätning visade att 259 substantiv föll på bara 15
   distinkta semantikvärden. Största facket var 84 ord med semantik=2 (enbart
   KONKRET), där näsa, byxa, bord, sten och regn behandlades som utbytbara.
   Konsekvens: "flickan gav sin bror en näsa" passerade varje semantiskt krav.

   Kategorierna fanns redan — i konceptnycklarnas prefix, inte i bitmasken.
   Den här migrationen lyfter in dem. Prefixhärledd och därför exakt; inget
   LLM-pass behövs.

   Nya bitar (BITMASK.md §11):
     4096  DRICKBAR      dricks snarare än äts
     8192  KROPPSDEL     kroppsdel — kan inte ges bort, köpas eller ätas
    16384  KLÄDESPLAGG   bärs på kroppen
    32768  INREDNING     möbel, husgeråd eller byggnadsdel
    65536  NATURFENOMEN  väder och naturkraft — inte ett gripbart föremål

   KÖRS EFTER VARJE `ordbok import`:
       sqlite3 sprak.db < ordbok/migrationer/semantik_utökad.sql

   Måste köras EFTER semantik.sql — den här filen OR:ar in bitar i värden
   som semantik.sql sätter. Filnamnet sorterar efter, vilket RUNBOOK-loopen
   (`for m in ordbok/migrationer/*.sql`) förlitar sig på.
   ─────────────────────────────────────────────────────────────────────── */

/* ── DRICKBAR ───────────────────────────────────────────────────────────
   Rena drycker tappar ÄTBAR, så att "äta vatten" faller. Soppa behåller
   båda — den både äts och dricks. Salt, socker, smör och olja är
   ingredienser och förblir ÄTBAR. */
UPDATE Koncept SET semantik = (semantik & ~8) | 4096
 WHERE nyckel IN ('mat_vatten', 'mat_mjölk', 'mat_kaffe', 'mat_te',
                  'mat_juice', 'mat_öl', 'mat_vin');

UPDATE Koncept SET semantik = semantik | 4096
 WHERE nyckel = 'mat_soppa';

/* ── KROPPSDEL (22) ─────────────────────────────────────────────────── */
UPDATE Koncept SET semantik = semantik | 8192
 WHERE ordklass = 'Substantiv' AND nyckel LIKE 'krop\_%' ESCAPE '\';

/* ── KLÄDESPLAGG (20) ───────────────────────────────────────────────────
   Inkluderar glasögon och solglasögon — bärs på kroppen. */
UPDATE Koncept SET semantik = semantik | 16384
 WHERE ordklass = 'Substantiv' AND nyckel LIKE 'kläd\_%' ESCAPE '\';

/* ── INREDNING (16) ─────────────────────────────────────────────────────
   Bara hem_-orden som är föremål. hem_hus, hem_kök, hem_rum, hem_badrum,
   hem_toalett, hem_lägenhet och hem_skafferi är PLATS (semantik=18) och
   rörs inte. */
UPDATE Koncept SET semantik = semantik | 32768
 WHERE ordklass = 'Substantiv'
   AND nyckel LIKE 'hem\_%' ESCAPE '\'
   AND (semantik & 16) = 0;

/* ── NATURFENOMEN (9) ───────────────────────────────────────────────────
   Väder och naturkrafter. Himlakroppar (sol räknas hit som väderfenomen,
   men måne och stjärna är föremål och lämnas som KONKRET) samt naturens
   material (sten, jord, sand, gräs) rörs inte. */
UPDATE Koncept SET semantik = semantik | 65536
 WHERE nyckel IN ('väd_dimma', 'väd_hagel', 'väd_moln', 'väd_regn',
                  'väd_snö', 'väd_sol', 'väd_storm', 'väd_åska',
                  'väd_vind', 'nat_eld', 'nat_rök');
