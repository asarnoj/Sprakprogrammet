/* ── valens — valensklassificering av samtliga verbkoncept ──────────────────
   Bitmask enligt BITMASK.md §8 / setup.sql:
     1=Intransitiv  2=Transitiv  4=Ditransitiv  8=Reflexiv  16=Kopula

   KÖRS EFTER VARJE `ordbok import`:
       sqlite3 sprak.db < ordbok/migrationer/valens.sql

   Klassningsprinciper (fastställda 2026-07-09, första pass av Claude,
   granskas av Julius):
   - En bit sätts när användningen är naturlig i enkla standardmeningar.
   - Objektlös användning av transitiva verb ger Intransitiv-biten endast
     när den är fullt idiomatisk ("jag äter", "hon läser") — inte för t.ex.
     "bygga", "ta".
   - Prepositionsobjekt räknas INTE som Transitiv ("lyssna på", "vänta på"
     → Intransitiv). Undantag: partikeln ingår i lemmat ("lita på",
     "hålla med" → Transitiv).
   - att-satser och infinitivkomplement räknas som Transitiv (objektsslotten
     fylls av en sats): "hoppas att…", "försöka att…".
   - Reflexiv-biten: lemman med "sig" (gifta sig, oroa sig) samt etablerade
     reflexiva bruk (bestämma sig, ändra sig, känna sig).
   - Modalverb (brukar, bör, får, kan, måste, ska, vill): valens = NULL —
     hjälpverb med VP-komplement; hanteras av mönstersystemet, inte valens.
   - Deponensverb klassas efter syntax, inte morfologi (finnas=1, minnas=3,
     andas=1, lyckas=1, hoppas=3).
   ─────────────────────────────────────────────────────────────────────────── */

-- 1: rent intransitiva
UPDATE Koncept SET valens = 1 WHERE nyckel IN (
  'arb_arbeta', 'arb_laga_mat', 'arb_leka', 'ext_dö', 'ext_hända',
  'ext_leva', 'gen_lyckas', 'gen_misslyckas', 'gen_växa', 'kog_drömma',
  'kom_prata', 'krop_v_andas', 'krop_v_hosta', 'krop_v_sova',
  'krop_v_vakna', 'krop_v_vila', 'käns_gråta', 'käns_njuta',
  'käns_skratta', 'per_lyssna', 'per_titta', 'pos_ligga', 'pos_sitta',
  'pos_stå', 'rör_falla', 'rör_flyga', 'rör_gå', 'rör_hoppa',
  'rör_klättra', 'rör_komma', 'rör_krypa', 'rör_resa', 'rör_simma',
  'rör_snubbla', 'rör_springa', 'rör_stanna', 'rör_åka', 'soc_dansa',
  'soc_le', 'soc_vänta', 'verb_finnas'
);

-- 2: rent transitiva
UPDATE Koncept SET valens = 2 WHERE nyckel IN (
  'arb_hjälpa', 'eko_v_kosta', 'eko_v_tjäna', 'eko_v_äga',
  'fys_använda', 'fys_blanda', 'fys_bryta', 'fys_bygga', 'fys_bära',
  'fys_dra', 'fys_fylla', 'fys_göra', 'fys_hitta', 'fys_hålla',
  'fys_lägga', 'fys_reparera', 'fys_röra', 'fys_samla', 'fys_skära',
  'fys_slå', 'fys_ta', 'fys_tvätta', 'gen_acceptera', 'gen_dela',
  'gen_döda', 'gen_förbättra', 'gen_förklara', 'gen_försöka',
  'gen_jämföra', 'gen_lita', 'gen_lösa', 'gen_mena', 'gen_rädda',
  'gen_sakna', 'gen_skapa', 'gen_skydda', 'gen_söka', 'gen_tycka',
  'gen_undvika', 'kog_märka', 'kog_välja', 'kom_beskriva',
  'kom_hålla_med', 'kom_säga', 'käns_gilla', 'käns_hata', 'käns_ogilla',
  'käns_älska', 'rör_byta', 'rör_följa', 'rör_lämna', 'rör_nå',
  'soc_besöka', 'soc_tacka', 'soc_träffa', 'verb_ha'
);

-- 3 = Intransitiv | Transitiv
UPDATE Koncept SET valens = 3 WHERE nyckel IN (
  'arb_spara', 'arb_studera', 'arb_städa', 'arb_öva', 'asp_börja',
  'asp_fortsätta', 'asp_sluta', 'fys_lyfta', 'fys_stänga', 'fys_trycka',
  'fys_öppna', 'gen_förlora', 'gen_måla', 'gen_passa', 'gen_räkna',
  'gen_spela', 'gen_vinna', 'kog_förstå', 'kog_glömma', 'kog_minnas',
  'kog_planera', 'kog_tro', 'kog_tänka', 'kog_undra', 'kog_veta',
  'kom_berätta', 'kom_diskutera', 'kom_läsa', 'kom_ringa', 'kom_sjunga',
  'kom_skriva', 'kom_svara', 'krop_v_dricka', 'krop_v_äta', 'käns_fira',
  'käns_hoppas', 'per_höra', 'per_se', 'rör_köra', 'rör_vända',
  'soc_hälsa'
);

-- 6 = Transitiv | Ditransitiv ("ge ngn ngt")
UPDATE Koncept SET valens = 6 WHERE nyckel IN (
  'eko_v_låna', 'fys_ge', 'fys_kasta', 'fys_köpa', 'fys_sälja',
  'fys_visa', 'gen_erbjuda', 'gen_önska', 'kom_meddela', 'soc_bjuda',
  'soc_förlåta', 'soc_lova'
);

-- 7 = Intransitiv | Transitiv | Ditransitiv
UPDATE Koncept SET valens = 7 WHERE nyckel IN (
  'arb_betala', 'kom_fråga'
);

-- 8: rent reflexiva (lemmat innehåller sig; ingen icke-reflexiv användning
--    i konceptets betydelse)
UPDATE Koncept SET valens = 8 WHERE nyckel IN (
  'kog_koncentrera', 'käns_oroa', 'rör_skynda', 'soc_gifta_sig'
);

-- 10 = Transitiv | Reflexiv (tar objekt och/eller används reflexivt)
UPDATE Koncept SET valens = 10 WHERE nyckel IN (
  'gen_förbereda', 'gen_ändra', 'kog_bestämma', 'kog_föreställa',
  'kog_lära', 'per_känna'
);

-- 16: kopulaverb (tar predikativ, inte objekt)
UPDATE Koncept SET valens = 16 WHERE nyckel IN (
  'ext_verka', 'verb_bli', 'verb_vara'
);

-- 17 = Intransitiv | Kopula ("det luktar" / "luktar gott")
UPDATE Koncept SET valens = 17 WHERE nyckel IN ('per_lukta');

-- 18 = Transitiv | Kopula ("smaka soppan" / "smakar gott")
UPDATE Koncept SET valens = 18 WHERE nyckel IN ('per_smaka');

-- Modalverb: valens förblir NULL (hjälpverb — VP-komplement, ej valens).

-- Kontroll: ska ge 0 rader (alla icke-modala verb ska vara taggade).
SELECT 'OTAGGAD: ' || nyckel
FROM Koncept
WHERE ordklass = 'Verb' AND valens IS NULL
  AND nyckel NOT IN ('modal_brukar', 'modal_bör', 'modal_får', 'modal_kan',
                     'modal_måste', 'modal_ska', 'modal_vill');
