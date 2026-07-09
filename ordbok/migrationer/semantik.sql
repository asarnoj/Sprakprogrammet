/* ── semantik — semantisk taggning av substantiv- och pronomenkoncept ───────
   Bitmask enligt BITMASK.md §11:
     1=ANIMAT 2=KONKRET 4=ABSTRAKT 8=ÄTBAR 16=PLATS 32=MÄNSKLIG
     64=RÖRELSE 128=RIKTNING 256=HÄNDELSE 512=TID 1024=INSTRUMENT
     2048=KOMMUNIKAT

   KÖRS EFTER VARJE `ordbok import`:
       sqlite3 sprak.db < ordbok/migrationer/semantik.sql

   Klassningsprinciper (första pass av Claude 2026-07-09, granskas av Julius):
   - Följer kombinationsexemplen i BITMASK.md §11 (hund=3, lärare=35,
     stad=50, bil=1090, dag=516, fråga=2052, krig≈HÄNDELSE).
   - INSTRUMENT sätts konservativt: tydliga verktyg (penna, dator, telefon)
     och transportmedel — inte vitvaror/lampor.
   - ÄTBAR sätts bara på mat/dryck — inte medicin (undviker "äter medicin"
     i meningsbyggaren).
   - Verb: semantik = NULL (kodas i valens + MönsterKrav), utom
     rörelseverben som får RÖRELSE-biten per §11.
   - Pronomen med tydlig mänsklig referens = 35; det/de/sig = NULL
     (kan referera till vad som helst — inget krav ska matcha på dem).
   ─────────────────────────────────────────────────────────────────────────── */

-- 2 = KONKRET (fysiska föremål, substanser, kroppsdelar, kläder, väder)
UPDATE Koncept SET semantik = 2 WHERE nyckel IN (
  'eko_pengar',
  'hem_bokhylla', 'hem_bord', 'hem_byrå', 'hem_dörr', 'hem_frys',
  'hem_fönster', 'hem_golv', 'hem_kylskåp', 'hem_lampa', 'hem_matta',
  'hem_stol', 'hem_säng', 'hem_tak', 'hem_trappa', 'hem_ugn', 'hem_vägg',
  'häls_medicin',
  'kläd_byxa', 'kläd_glasögon', 'kläd_halsduk', 'kläd_hatt', 'kläd_jacka',
  'kläd_jeans', 'kläd_kalsong', 'kläd_kjol', 'kläd_kläder', 'kläd_klänning',
  'kläd_mössa', 'kläd_skjorta', 'kläd_sko', 'kläd_solglasögon',
  'kläd_strumpa', 'kläd_trosor', 'kläd_tröja', 'kläd_tshirt',
  'kläd_underkläder', 'kläd_vantar',
  'krop_ansikte', 'krop_arm', 'krop_axel', 'krop_ben', 'krop_blod',
  'krop_bröst', 'krop_finger', 'krop_fot', 'krop_hals', 'krop_hand',
  'krop_hjärta', 'krop_huvud', 'krop_hår', 'krop_knä', 'krop_mage',
  'krop_mun', 'krop_näsa', 'krop_rygg', 'krop_tand', 'krop_tunga',
  'krop_öga', 'krop_öra',
  'nat_blomma', 'nat_eld', 'nat_gräs', 'nat_is', 'nat_jord', 'nat_luft',
  'nat_måne', 'nat_rök', 'nat_sand', 'nat_sten', 'nat_stjärna', 'nat_träd',
  'nat_växt',
  'skol_papper', 'skol_väska',
  'trans_biljett',
  'väd_dimma', 'väd_hagel', 'väd_moln', 'väd_regn', 'väd_snö', 'väd_sol',
  'väd_storm', 'väd_åska'
);

-- 3 = ANIMAT+KONKRET (djur)
UPDATE Koncept SET semantik = 3 WHERE nyckel IN (
  'djur_elefant', 'djur_fisk', 'djur_fågel', 'djur_får', 'djur_gris',
  'djur_hund', 'djur_häst', 'djur_katt', 'djur_ko', 'djur_lejon',
  'djur_mus', 'djur_orm'
);

-- 4 = ABSTRAKT
UPDATE Koncept SET semantik = 4 WHERE nyckel IN (
  'abs_anledning', 'abs_del', 'abs_exempel', 'abs_form', 'abs_historia',
  'abs_hälsa', 'abs_idé', 'abs_kultur', 'abs_kärlek', 'abs_liv',
  'abs_ljud', 'abs_makt', 'abs_miljö', 'abs_möjlighet', 'abs_problem',
  'abs_sanning', 'abs_situation', 'abs_smak', 'abs_sätt', 'abs_typ',
  'eko_pris',
  'häls_sjukdom', 'häls_skada', 'häls_smärta',
  'sam_fred',
  'skol_klass', 'skol_läxa',
  'väd_väder'
);

-- 10 = KONKRET+ÄTBAR (mat och dryck)
UPDATE Koncept SET semantik = 10 WHERE nyckel IN (
  'mat_bröd', 'mat_fisk', 'mat_frukt', 'mat_grönsak', 'mat_juice',
  'mat_kaffe', 'mat_kyckling', 'mat_kött', 'mat_mat', 'mat_mjölk',
  'mat_olja', 'mat_ost', 'mat_pasta', 'mat_potatis', 'mat_ris',
  'mat_salt', 'mat_smör', 'mat_socker', 'mat_soppa', 'mat_te',
  'mat_vatten', 'mat_vin', 'mat_ägg', 'mat_öl'
);

-- 18 = KONKRET+PLATS
UPDATE Koncept SET semantik = 18 WHERE nyckel IN (
  'abs_värld',
  'hem_badrum', 'hem_hus', 'hem_kök', 'hem_lägenhet', 'hem_rum',
  'hem_skafferi', 'hem_toalett',
  'nat_berg', 'nat_hav', 'nat_himmel', 'nat_sjö', 'nat_skog', 'nat_strand',
  'plats_affär', 'plats_apotek', 'plats_bar', 'plats_bibliotek',
  'plats_café', 'plats_hem', 'plats_kontor', 'plats_kyrka',
  'plats_marknad', 'plats_park', 'plats_restaurang', 'plats_sjukhus',
  'plats_skola', 'plats_universitet', 'plats_väg',
  'trans_busshållplats', 'trans_flygplats', 'trans_tågstation'
);

-- 35 = ANIMAT+KONKRET+MÄNSKLIG (människor och roller)
UPDATE Koncept SET semantik = 35 WHERE nyckel IN (
  'fam_barn', 'fam_bekant', 'fam_bror', 'fam_dotter', 'fam_familj',
  'fam_lillasyster', 'fam_lillebror', 'fam_maka', 'fam_make', 'fam_mamma',
  'fam_pappa', 'fam_son', 'fam_storasyster', 'fam_storebror', 'fam_syster',
  'fam_vän',
  'pers_flicka', 'pers_granne', 'pers_gäst', 'pers_kvinna', 'pers_man',
  'pers_person', 'pers_pojke', 'pers_vuxen',
  'skol_elev', 'skol_lärare', 'skol_professor', 'skol_student',
  'yrke_advokat', 'yrke_artist', 'yrke_bonde', 'yrke_brandman',
  'yrke_chef', 'yrke_författare', 'yrke_ingenjör', 'yrke_kock',
  'yrke_kollega', 'yrke_konstnär', 'yrke_läkare', 'yrke_polis',
  'yrke_sjuksköterska', 'yrke_säljare'
);

-- 50 = KONKRET+PLATS+MÄNSKLIG (platser med mänsklig kontext, per §11-exempel)
UPDATE Koncept SET semantik = 50 WHERE nyckel IN (
  'plats_by', 'plats_land', 'plats_stad'
);

-- 66 = KONKRET+RÖRELSE (naturligt rörliga fenomen)
UPDATE Koncept SET semantik = 66 WHERE nyckel IN ('väd_vind');

-- 82 = KONKRET+PLATS+RÖRELSE (flod: geografisk och strömmande)
UPDATE Koncept SET semantik = 82 WHERE nyckel IN ('nat_flod');

-- 260 = ABSTRAKT+HÄNDELSE
UPDATE Koncept SET semantik = 260 WHERE nyckel IN (
  'abs_upplevelse', 'sam_krig'
);

-- 516 = ABSTRAKT+TID
UPDATE Koncept SET semantik = 516 WHERE nyckel IN (
  'abs_framtid',
  'tid_dag', 'tid_eftermiddag', 'tid_kväll', 'tid_middag', 'tid_minut',
  'tid_morgon', 'tid_månad', 'tid_natt', 'tid_sekund', 'tid_tid',
  'tid_timme', 'tid_vecka', 'tid_år'
);

-- 1026 = KONKRET+INSTRUMENT (verktyg)
UPDATE Koncept SET semantik = 1026 WHERE nyckel IN (
  'skol_dator', 'skol_penna', 'skol_telefon'
);

-- 1090 = KONKRET+RÖRELSE+INSTRUMENT (transportmedel, per §11-exempel)
UPDATE Koncept SET semantik = 1090 WHERE nyckel IN (
  'trans_bil', 'trans_buss', 'trans_båt', 'trans_cykel', 'trans_flygplan',
  'trans_taxi', 'trans_tunnelbana', 'trans_tåg'
);

-- 2050 = KONKRET+KOMMUNIKAT (fysiska bärare av kommunikat)
UPDATE Koncept SET semantik = 2050 WHERE nyckel IN ('skol_bok');

-- 2052 = ABSTRAKT+KOMMUNIKAT
UPDATE Koncept SET semantik = 2052 WHERE nyckel IN (
  'abs_nyhet', 'abs_ord', 'skol_fråga', 'skol_svar'
);

-- Rörelseverb: RÖRELSE-biten per §11 (styr meningsbyggarens adverbial)
UPDATE Koncept SET semantik = 64 WHERE nyckel IN (
  'rör_falla', 'rör_flyga', 'rör_gå', 'rör_hoppa', 'rör_klättra',
  'rör_komma', 'rör_krypa', 'rör_köra', 'rör_resa', 'rör_simma',
  'rör_springa', 'rör_åka'
);

-- Pronomen med tydlig mänsklig referens
UPDATE Koncept SET semantik = 35 WHERE nyckel IN (
  'pronomen_1sg', 'pronomen_1pl', 'pronomen_2sg', 'pronomen_2pl',
  'pronomen_2sg_formal', 'pronomen_3sg_mask', 'pronomen_3sg_fem',
  'pronomen_impersonal'
);
-- pronomen_3sg_neutr, pronomen_3pl, pronomen_reflexiv: NULL — kan referera
-- till vad som helst; inga semantiska krav ska matcha på dem.

-- Kontroll: ska ge 0 rader (alla substantiv ska vara taggade).
SELECT 'OTAGGAD: ' || nyckel
FROM Koncept
WHERE ordklass = 'Substantiv' AND semantik IS NULL;
