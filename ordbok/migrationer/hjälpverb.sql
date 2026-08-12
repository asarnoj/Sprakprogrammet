/* ── hjälpverb — vilket hjälpverb som bildar sammansatt dåtid ────────
   fr être/avoir, de sein/haben, it essere/avere. Lagras abstrakt som
   'ha' / 'vara' / 'båda'; se setup.sql för kodningen.

   Grundregeln är 'ha' — den sätts först för samtliga fr/de/it-verb, och
   undantagen skrivs över efteråt. Undantagen är av fyra slag:

     Rörelse och tillståndsförändring: de gehen/kommen/fallen/wachsen,
     fr venir/tomber/mourir, it andare/venire/cadere/crescere.

     Reflexiver i fr och it tar ALLTID être/essere: se marier, sposarsi,
     s'arrêter, fermarsi. Tyska reflexiver tar haben — sich beeilen är
     'ha', inte 'vara'. Det är den vanligaste fällan.

     Italienska modalverb ärver hjälpverbet från verbet de styr:
     "ho dovuto lavorare" men "sono dovuto andare". Därför 'båda' —
     valet kan inte avgöras på lexemet, bara i renderaren.

     Verb som tar båda med olika betydelse: de "ist gefahren" (åkte)
     vs "hat gefahren" (körde), it "è corso" vs "ha corso",
     de "ist zerbrochen" vs "hat zerbrochen".

   Nycklat på koncept, inte lemma: de/finden är två lexem (fys_hitta och
   gen_tycka) och it/giocare likaså. Se rattelse.py om varför det spelar roll.

   KÖRS EFTER VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

UPDATE Lexem SET hjälpverb = 'ha'
WHERE språk IN ('fr', 'de', 'it')
  AND koncept_id IN (SELECT id FROM Koncept WHERE ordklass = 'Verb');


/* ── 'vara' — être / sein / essere ─────────────────────── */

UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'arb_öva');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'eko_v_kosta');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'ext_dö');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'ext_dö');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'ext_dö');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'ext_hända');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'ext_hända');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'ext_hända');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'ext_verka');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_lita');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_lyckas');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_misslyckas');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_passa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_sakna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_växa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_växa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kog_koncentrera');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kog_koncentrera');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kog_minnas');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kog_undra');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kog_undra');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kom_hålla_med');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'kom_hålla_med');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'krop_v_vakna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'krop_v_vakna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'krop_v_vakna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'krop_v_vila');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'krop_v_vila');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'käns_gilla');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'käns_ogilla');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'käns_oroa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'käns_oroa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_ska');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_ska');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_ska');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pos_ligga');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pos_ligga');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pos_sitta');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pos_sitta');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pos_stå');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'pos_stå');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_falla');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_falla');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_falla');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_följa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_gå');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_hoppa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_klättra');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_klättra');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_komma');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_komma');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_komma');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_krypa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_lämna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_lämna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_resa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_skynda');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_skynda');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_snubbla');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_snubbla');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_springa');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_stanna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_stanna');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_åka');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_åka');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'soc_gifta_sig');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'soc_gifta_sig');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'fr' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_bli');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_bli');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_bli');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_finnas');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_vara');
UPDATE Lexem SET hjälpverb = 'vara' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'verb_vara');

/* ── 'båda' — hjälpverbet avgörs i renderaren, inte här ─── */

UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'asp_börja');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'asp_fortsätta');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'fys_bryta');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_förbättra');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_misslyckas');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'gen_ändra');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_bör');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_får');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_kan');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_måste');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'modal_vill');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_flyga');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_flyga');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_hoppa');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_köra');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_simma');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'it' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_springa');
UPDATE Lexem SET hjälpverb = 'båda' WHERE språk = 'de' AND koncept_id = (SELECT id FROM Koncept WHERE nyckel = 'rör_åka');
