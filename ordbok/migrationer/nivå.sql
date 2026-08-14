/* ── nivå ─────────────────────────────────────────────────────────────
   CEFR-nivån per koncept, ur ordbok/nivålistor/*.csv.

   Kolumnen fanns i CSV-filerna från början men lästes aldrig in — läsaren
   kastade den med kommentaren att den "inte längre är del av schemat". Det
   beslutet fattades innan generatorn fanns, och generatorn behöver veta
   vilka ord en nybörjare ska möta.

   Nivån är en egenskap hos KONCEPTET och inte hos lexemet: noll av 736
   koncept har olika nivå i olika språk, kontrollerat vid införandet och
   kontrollerat av importen vid varje körning sedan dess.

   Skild från komplexitetsstegens nivå, som styr KONSTRUKTIONER. De två är
   ortogonala: en nybörjare möter A1-ord i enkla satser, och båda taken
   flyttas oberoende av varandra.

   Filen genereras ur nivålistorna och behövs bara för en databas som redan
   importerats — `ordbok import` sätter kolumnen själv.
   KÖRS EFTER koncepttaggning.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */


/* A1: 393 koncept */
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('abs_kärlek', 'abs_liv', 'abs_värld', 'adj_es_arg', 'adj_es_frisk', 'adj_es_glad', 'adj_es_hungrig', 'adj_es_ledsen');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('adj_es_rädd', 'adj_es_sjuk', 'adj_es_trött', 'adj_es_törstig', 'adj_ev_rolig', 'adj_ev_snäll', 'adj_ev_tråkig', 'adj_ev_vacker');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('adj_ev_viktig', 'adj_k_bra', 'adj_k_dålig', 'adj_k_gammal', 'adj_k_ny', 'adj_k_ren', 'adj_k_smutsig', 'adj_k_ung');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('adj_s_hög', 'adj_s_kort', 'adj_s_liten', 'adj_s_lång', 'adj_s_stor', 'adj_t_het', 'adj_t_kall', 'adj_t_lätt');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('adj_t_tung', 'adj_t_varm', 'adv2_för', 'adv2_ganska', 'adv2_kanske', 'adv2_lite', 'adv2_okej', 'adv_alltid');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('adv_bara', 'adv_där', 'adv_då', 'adv_här', 'adv_ibland', 'adv_idag', 'adv_igen', 'adv_igår');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('adv_imorgon', 'adv_mycket', 'adv_nu', 'adv_också', 'adv_ofta', 'adv_redan', 'adv_snart', 'arb_arbeta');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('arb_hjälpa', 'arb_leka', 'artikel_bestamd', 'artikel_obestamd', 'asp_börja', 'asp_sluta', 'demonstrativ_fjärran', 'demonstrativ_nara');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('djur_fisk', 'djur_fågel', 'djur_får', 'djur_gris', 'djur_hund', 'djur_häst', 'djur_katt', 'djur_ko');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('djur_mus', 'eko_pengar', 'eko_v_kosta', 'ext_leva', 'fam_barn', 'fam_bror', 'fam_familj', 'fam_lillasyster');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('fam_lillebror', 'fam_mamma', 'fam_pappa', 'fam_storasyster', 'fam_storebror', 'fam_syster', 'fam_vän', 'frågadverb_orsak');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('frågadverb_plats', 'frågadverb_riktning', 'frågadverb_sätt', 'frågadverb_tid', 'frågadverb_ursprung', 'frågepronomen_person', 'frågepronomen_sak', 'fys_använda');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('fys_ge', 'fys_göra', 'fys_hitta', 'fys_hålla', 'fys_köpa', 'fys_stänga', 'fys_ta', 'fys_visa');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('fys_öppna', 'färg_blå', 'färg_brun', 'färg_grå', 'färg_grön', 'färg_gul', 'färg_röd', 'färg_svart');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('färg_vit', 'gen_försöka', 'gen_spela', 'gen_tycka', 'hem_badrum', 'hem_bord', 'hem_dörr', 'hem_fönster');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('hem_golv', 'hem_hus', 'hem_kylskåp', 'hem_kök', 'hem_lampa', 'hem_lägenhet', 'hem_rum', 'hem_stol');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('hem_säng', 'hem_tak', 'hem_toalett', 'hem_ugn', 'hem_vägg', 'interj_goodbye', 'interj_hello', 'interj_no');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('interj_oh', 'interj_please', 'interj_sorry', 'interj_thanks', 'interj_yes', 'interr_det_vilken', 'kläd_byxa', 'kläd_halsduk');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('kläd_jacka', 'kläd_jeans', 'kläd_kjol', 'kläd_kläder', 'kläd_klänning', 'kläd_mössa', 'kläd_skjorta', 'kläd_sko');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('kläd_strumpa', 'kläd_tröja', 'kläd_tshirt', 'kläd_vantar', 'kog_förstå', 'kog_lära', 'kog_tänka', 'kog_veta');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('kom_fråga', 'kom_läsa', 'kom_prata', 'kom_skriva', 'kom_svara', 'kom_säga', 'komp_mer', 'komp_mest');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('komp_som', 'komp_än', 'konj_eller', 'konj_men', 'konj_och', 'konj_så', 'krop_ansikte', 'krop_arm');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('krop_ben', 'krop_finger', 'krop_fot', 'krop_hand', 'krop_hjärta', 'krop_huvud', 'krop_hår', 'krop_mage');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('krop_mun', 'krop_näsa', 'krop_tand', 'krop_v_dricka', 'krop_v_sova', 'krop_v_vakna', 'krop_v_äta', 'krop_öga');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('krop_öra', 'kvant_alla', 'kvant_ingen', 'kvant_ingen_det', 'kvant_inget', 'kvant_någon', 'kvant_något', 'käns_gilla');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('käns_gråta', 'käns_skratta', 'käns_älska', 'mat_bröd', 'mat_fisk', 'mat_frukt', 'mat_grönsak', 'mat_kaffe');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('mat_kött', 'mat_mat', 'mat_mjölk', 'mat_pasta', 'mat_potatis', 'mat_ris', 'mat_salt', 'mat_socker');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('mat_te', 'mat_vatten', 'mat_ägg', 'modal_får', 'modal_kan', 'modal_måste', 'modal_ska', 'modal_vill');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('nat_berg', 'nat_blomma', 'nat_eld', 'nat_flod', 'nat_hav', 'nat_himmel', 'nat_jord', 'nat_luft');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('nat_sjö', 'nat_skog', 'nat_sten', 'nat_strand', 'nat_träd', 'neg_aldrig', 'neg_inte', 'per_höra');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('per_lyssna', 'per_se', 'per_titta', 'pers_flicka', 'pers_kvinna', 'pers_man', 'pers_person', 'pers_pojke');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('plats_affär', 'plats_apotek', 'plats_bar', 'plats_by', 'plats_café', 'plats_hem', 'plats_land', 'plats_park');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('plats_restaurang', 'plats_sjukhus', 'plats_skola', 'plats_stad', 'plats_väg', 'pos_ligga', 'pos_sitta', 'pos_stå');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('poss_1pl', 'poss_1sg', 'poss_2pl', 'poss_2sg', 'poss_3pl', 'poss_3sg_fem', 'poss_3sg_mask', 'prep_av');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('prep_bakom', 'prep_bredvid', 'prep_efter', 'prep_framför', 'prep_från', 'prep_för', 'prep_före', 'prep_i');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('prep_med', 'prep_mellan', 'prep_mot', 'prep_om', 'prep_på', 'prep_till', 'prep_under', 'prep_utan');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('prep_vid', 'prep_över', 'pronomen_1pl', 'pronomen_1sg', 'pronomen_2pl', 'pronomen_2sg', 'pronomen_3pl', 'pronomen_3sg_fem');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('pronomen_3sg_mask', 'pronomen_3sg_neutr', 'pronomen_impersonal', 'pronomen_reflexiv', 'räkn_0', 'räkn_1', 'räkn_10', 'räkn_100');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('räkn_1000', 'räkn_11', 'räkn_12', 'räkn_13', 'räkn_14', 'räkn_15', 'räkn_16', 'räkn_17');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('räkn_18', 'räkn_19', 'räkn_2', 'räkn_20', 'räkn_3', 'räkn_30', 'räkn_4', 'räkn_40');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('räkn_5', 'räkn_50', 'räkn_6', 'räkn_7', 'räkn_8', 'räkn_9', 'räkn_ord_1', 'räkn_ord_2');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('räkn_ord_3', 'rör_gå', 'rör_komma', 'rör_köra', 'rör_springa', 'rör_åka', 'skol_bok', 'skol_dator');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('skol_elev', 'skol_fråga', 'skol_klass', 'skol_lärare', 'skol_papper', 'skol_penna', 'skol_student', 'skol_svar');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('skol_telefon', 'skol_väska', 'soc_dansa', 'soc_hälsa', 'soc_le', 'soc_tacka', 'soc_träffa', 'soc_vänta');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('subj_att', 'subj_eftersom', 'subj_när', 'subj_om_konditional', 'tid_dag', 'tid_eftermiddag', 'tid_kväll', 'tid_middag');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('tid_minut', 'tid_morgon', 'tid_månad', 'tid_natt', 'tid_tid', 'tid_timme', 'tid_vecka', 'tid_år');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('trans_bil', 'trans_biljett', 'trans_buss', 'trans_busshållplats', 'trans_båt', 'trans_cykel', 'trans_flygplan', 'trans_flygplats');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('trans_taxi', 'trans_tåg', 'trans_tågstation', 'verb_bli', 'verb_finnas', 'verb_ha', 'verb_vara', 'väd_moln');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('väd_regn', 'väd_snö', 'väd_sol', 'väd_vind', 'väd_väder', 'yrke_brandman', 'yrke_läkare', 'yrke_polis');
UPDATE Koncept SET nivå = 'A1' WHERE nyckel IN ('yrke_sjuksköterska');

/* A2: 328 koncept */
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('abs_anledning', 'abs_del', 'abs_exempel', 'abs_form', 'abs_framtid', 'abs_historia', 'abs_hälsa', 'abs_idé');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('abs_ljud', 'abs_makt', 'abs_miljö', 'abs_nyhet', 'abs_ord', 'abs_problem', 'abs_sanning', 'abs_situation');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('abs_smak', 'abs_sätt', 'abs_typ', 'abs_upplevelse', 'adj_eko_billig', 'adj_eko_dyr', 'adj_eko_fri', 'adj_es_ensam');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_es_förvånad', 'adj_es_kär', 'adj_es_nervös', 'adj_es_nöjd', 'adj_es_skamsen', 'adj_es_stressad', 'adj_ev_besviken', 'adj_ev_dum');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_ev_elak', 'adj_ev_flitig', 'adj_ev_ful', 'adj_ev_intressant', 'adj_ev_intresserad', 'adj_ev_lat', 'adj_ev_lugn', 'adj_ev_modig');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_ev_nyfiken', 'adj_ev_oväntad', 'adj_ev_populär', 'adj_ev_smart', 'adj_ev_stolt', 'adj_ev_ärlig', 'adj_k_död', 'adj_k_enkel');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_k_fel', 'adj_k_full', 'adj_k_halv', 'adj_k_hel', 'adj_k_levande', 'adj_k_normal', 'adj_k_rätt', 'adj_k_stark');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_k_stängd', 'adj_k_svag', 'adj_k_svår', 'adj_k_tom', 'adj_k_trasig', 'adj_k_öppen', 'adj_m_farlig', 'adj_m_klar');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_m_lik', 'adj_m_möjlig', 'adj_m_nödvändig', 'adj_m_olik', 'adj_m_omöjlig', 'adj_m_speciell', 'adj_m_säker', 'adj_m_vanlig');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_s_bred', 'adj_s_djup', 'adj_s_långsam', 'adj_s_rund', 'adj_s_smal', 'adj_s_snabb', 'adj_s_tjock', 'adj_s_tunn');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adj_t_hård', 'adj_t_mjuk', 'adj_t_skarp', 'adj_t_sval', 'adj_t_torr', 'adj_t_våt', 'adv2_alltså', 'adv2_annars');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adv2_bort', 'adv2_dessutom', 'adv2_direkt', 'adv2_faktiskt', 'adv2_fram', 'adv2_gärna', 'adv2_inne', 'adv2_istället');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adv2_länge', 'adv2_mest', 'adv2_naturligtvis', 'adv2_ner', 'adv2_nästan', 'adv2_plötsligt', 'adv2_precis', 'adv2_säkert');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adv2_tillbaka', 'adv2_tillsammans', 'adv2_troligen', 'adv2_tyvärr', 'adv2_ungefär', 'adv2_upp', 'adv2_ute', 'adv2_verkligen');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('adv2_ändå', 'adv_fortfarande', 'adv_sällan', 'arb_betala', 'arb_laga_mat', 'arb_spara', 'arb_studera', 'arb_städa');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('arb_öva', 'asp_fortsätta', 'djur_elefant', 'djur_lejon', 'djur_orm', 'eko_pris', 'eko_v_låna', 'eko_v_tjäna');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('eko_v_äga', 'ext_dö', 'ext_hända', 'fam_bekant', 'fam_dotter', 'fam_maka', 'fam_make', 'fam_son');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('fys_blanda', 'fys_bryta', 'fys_bygga', 'fys_bära', 'fys_dra', 'fys_fylla', 'fys_kasta', 'fys_lyfta');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('fys_lägga', 'fys_reparera', 'fys_röra', 'fys_samla', 'fys_skära', 'fys_slå', 'fys_sälja', 'fys_trycka');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('fys_tvätta', 'färg_lila', 'färg_orange', 'färg_rosa', 'gen_acceptera', 'gen_dela', 'gen_döda', 'gen_erbjuda');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('gen_förbereda', 'gen_förbättra', 'gen_förklara', 'gen_förlora', 'gen_lyckas', 'gen_lösa', 'gen_mena', 'gen_misslyckas');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('gen_måla', 'gen_passa', 'gen_rädda', 'gen_räkna', 'gen_sakna', 'gen_skapa', 'gen_skydda', 'gen_söka');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('gen_undvika', 'gen_vinna', 'gen_växa', 'gen_ändra', 'gen_önska', 'hem_bokhylla', 'hem_byrå', 'hem_frys');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('hem_matta', 'hem_skafferi', 'hem_trappa', 'häls_medicin', 'häls_sjukdom', 'häls_skada', 'häls_smärta', 'interr_det_hur_mycket');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('interr_det_hur_många', 'kläd_glasögon', 'kläd_hatt', 'kläd_kalsong', 'kläd_solglasögon', 'kläd_trosor', 'kläd_underkläder', 'kog_bestämma');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('kog_drömma', 'kog_glömma', 'kog_minnas', 'kog_märka', 'kog_planera', 'kog_tro', 'kog_undra', 'kog_välja');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('kom_berätta', 'kom_hålla_med', 'kom_meddela', 'kom_ringa', 'kom_sjunga', 'konj_för', 'konj_utan', 'krop_axel');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('krop_blod', 'krop_bröst', 'krop_hals', 'krop_knä', 'krop_rygg', 'krop_tunga', 'krop_v_andas', 'krop_v_hosta');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('krop_v_vila', 'kvant_båda', 'kvant_några', 'kvant_varje', 'käns_fira', 'käns_hata', 'käns_hoppas', 'käns_njuta');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('käns_ogilla', 'käns_oroa', 'mat_juice', 'mat_kyckling', 'mat_olja', 'mat_ost', 'mat_smör', 'mat_soppa');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('mat_vin', 'mat_öl', 'modal_brukar', 'modal_bör', 'nat_gräs', 'nat_is', 'nat_måne', 'nat_rök');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('nat_sand', 'nat_stjärna', 'nat_växt', 'neg_heller', 'neg_inte_längre', 'per_känna', 'per_lukta', 'per_smaka');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('pers_granne', 'pers_gäst', 'pers_vuxen', 'plats_bibliotek', 'plats_kontor', 'plats_kyrka', 'plats_marknad', 'plats_universitet');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('poss_2sg_formal', 'poss_3sg_neutr', 'prep_bland', 'prep_emot', 'prep_genom', 'prep_innanför', 'prep_längs', 'prep_trots');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('prep_utanför', 'pronomen_2sg_formal', 'rel_person', 'rel_sak', 'räkn_60', 'räkn_70', 'räkn_80', 'räkn_90');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('räkn_ord_4', 'räkn_ord_5', 'rör_byta', 'rör_falla', 'rör_flyga', 'rör_följa', 'rör_hoppa', 'rör_klättra');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('rör_lämna', 'rör_nå', 'rör_resa', 'rör_simma', 'rör_skynda', 'rör_snubbla', 'rör_stanna', 'sam_fred');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('sam_krig', 'skol_läxa', 'skol_professor', 'soc_besöka', 'soc_bjuda', 'soc_förlåta', 'soc_gifta_sig', 'soc_lova');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('subj_efter_att', 'subj_för_att', 'subj_ifall', 'subj_innan', 'subj_medan', 'subj_om_huruvida', 'subj_tills', 'subj_trots_att');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('tid_sekund', 'trans_tunnelbana', 'väd_dimma', 'väd_hagel', 'väd_storm', 'väd_åska', 'yrke_advokat', 'yrke_artist');
UPDATE Koncept SET nivå = 'A2' WHERE nyckel IN ('yrke_bonde', 'yrke_chef', 'yrke_författare', 'yrke_ingenjör', 'yrke_kock', 'yrke_kollega', 'yrke_konstnär', 'yrke_säljare');

/* B1: 15 koncept */
UPDATE Koncept SET nivå = 'B1' WHERE nyckel IN ('abs_kultur', 'abs_möjlighet', 'adj_m_offentlig', 'adj_m_officiell', 'adj_m_privat', 'adv2_åtminstone', 'ext_verka', 'gen_jämföra');
UPDATE Koncept SET nivå = 'B1' WHERE nyckel IN ('gen_lita', 'kog_föreställa', 'kog_koncentrera', 'kom_beskriva', 'kom_diskutera', 'rör_krypa', 'rör_vända');
