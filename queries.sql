PRAGMA foreign_keys=ON;

BEGIN;

/* ════════════════════════════════════════════════════════════
   KONCEPT  (språkoberoende, engelska namn)
════════════════════════════════════════════════════════════ */
INSERT INTO Koncept (id, namn, ordklass) VALUES
    (1,  'eat',       'Verb'),
    (2,  'ball',      'Substantiv'),
    (3,  'cute',      'Adjektiv'),
    (4,  'he',        'Pronomen'),
    (5,  'like',      'Verb'),
    (6,  'rain',      'Verb'),
    (7,  'red',       'Adjektiv'),
    (8,  'kind',      'Adjektiv'),
    (9,  'teacher',   'Substantiv'),
    (10, 'give',      'Verb'),
    (11, 'tired',     'Adjektiv'),
    (12, 'child',     'Substantiv'),
    (13, 'book',      'Substantiv'),
    (14, 'beautiful', 'Adjektiv'),
    (15, 'I',         'Pronomen'),
    (16, 'love',      'Verb'),
    (17, 'run',       'Verb'),
    (18, 'quickly',   'Adverb'),
    (19, 'believe',   'Verb'),
    (20, 'that',      'Subjunktion'),
    (21, 'in',        'Preposition'),
    (22, 'park',      'Substantiv'),
    (23, 'and',       'Konjunktion'),
    (24, 'but',       'Konjunktion'),
    (25, 'or',        'Konjunktion'),
    (26, 'often',     'Adverb'),
    (27, 'school',    'Substantiv'),
    (28, 'to',        'Preposition'),
--  Negationsadverb
    (36, 'never',        'Negationsadverb'),
    (37, 'no longer',    'Negationsadverb'),
--  Frågeord
    (29, 'who',       'Frågepronomen'),
    (30, 'what',      'Frågepronomen'),
    (31, 'where',     'Frågadverb'),
    (32, 'when',      'Frågadverb'),
    (33, 'how',       'Frågadverb'),
    (34, 'why',       'Frågadverb'),
    (35, 'which',     'Interrogativdeterminant');


/* ════════════════════════════════════════════════════════════
   LEXEM  (ett per språk per koncept)
   valens:       1=Intransitiv, 2=Transitiv, 4=Ditransitiv, 8=Reflexiv
   personlighet: 1=Personlig, 2=Opersonlig
   genus: sv: 1=Utrum 2=Neutrum | fr: 1=Maskulin 2=Feminin
   prenominal: 1=adjektiv FÖRE substantivet, 0=EFTER (NULL tolkas som 1)
════════════════════════════════════════════════════════════ */
INSERT INTO Lexem (id, koncept_id, språk, lemma, genus, valens, personlighet, gradbarhet, prenominal, person, numerus) VALUES
--                                                                    person  numerus
--  eat
    (1,  1,  'sv', 'äta',        NULL, 3, 1, NULL,      NULL, NULL, NULL),
    (2,  1,  'fr', 'manger',     NULL, 3, 1, NULL,      NULL, NULL, NULL),
--  ball — sv: Utrum(1)  fr: Feminin(2)
    (3,  2,  'sv', 'boll',       1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (4,  2,  'fr', 'balle',      2,    NULL, NULL, NULL, NULL, NULL, NULL),
--  cute — prenominal i båda
    (5,  3,  'sv', 'gullig',     NULL, NULL, NULL, 'Gradbar', 1,    NULL, NULL),
    (6,  3,  'fr', 'mignon',     NULL, NULL, NULL, 'Gradbar', 1,    NULL, NULL),
--  he — 3:e person singular
    (7,  4,  'sv', 'han',        NULL, NULL, NULL, NULL, NULL, 3, 1),
    (8,  4,  'fr', 'il',         NULL, NULL, NULL, NULL, NULL, 3, 1),
--  like — transitiv
    (9,  5,  'sv', 'gilla',      NULL, 2, 1, NULL, NULL, NULL, NULL),
    (10, 5,  'fr', 'aimer',      NULL, 2, 1, NULL, NULL, NULL, NULL),
--  rain — intransitiv, opersonlig
    (11, 6,  'sv', 'regna',      NULL, 1, 2, NULL, NULL, NULL, NULL),
    (12, 6,  'fr', 'pleuvoir',   NULL, 1, 2, NULL, NULL, NULL, NULL),
--  red — sv: prenominal(1)  fr: postnominal(0) färger
    (13, 7,  'sv', 'röd',        NULL, NULL, NULL, 'Gradbar', 1,    NULL, NULL),
    (14, 7,  'fr', 'rouge',      NULL, NULL, NULL, 'Gradbar', 0,    NULL, NULL),
--  kind — sv: prenominal  fr: postnominal
    (15, 8,  'sv', 'snäll',      NULL, NULL, NULL, 'Gradbar', 1,    NULL, NULL),
    (16, 8,  'fr', 'gentil',     NULL, NULL, NULL, 'Gradbar', 0,    NULL, NULL),
--  teacher — sv: Utrum(1)  fr: Maskulin(1)
    (17, 9,  'sv', 'lärare',     1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (18, 9,  'fr', 'professeur', 1,    NULL, NULL, NULL, NULL, NULL, NULL),
--  give — ditransitiv
    (19, 10, 'sv', 'ge',         NULL, 4, 1, NULL, NULL, NULL, NULL),
    (20, 10, 'fr', 'donner',     NULL, 4, 1, NULL, NULL, NULL, NULL),
--  tired — sv: prenominal  fr: postnominal
    (21, 11, 'sv', 'trött',      NULL, NULL, NULL, 'Gradbar', 1,    NULL, NULL),
    (22, 11, 'fr', 'fatigué',    NULL, NULL, NULL, 'Gradbar', 0,    NULL, NULL),
--  child — sv: Neutrum(2)  fr: Maskulin(1)
    (23, 12, 'sv', 'barn',       2,    NULL, NULL, NULL, NULL, NULL, NULL),
    (24, 12, 'fr', 'enfant',     1,    NULL, NULL, NULL, NULL, NULL, NULL),
--  book — sv: Utrum(1)  fr: Maskulin(1)
    (25, 13, 'sv', 'bok',        1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (26, 13, 'fr', 'livre',      1,    NULL, NULL, NULL, NULL, NULL, NULL),
--  beautiful — sv: prenominal  fr: prenominal (beau = BANGS-adjektiv)
    (27, 14, 'sv', 'vacker',     NULL, NULL, NULL, 'Gradbar', 1,    NULL, NULL),
    (28, 14, 'fr', 'beau',       NULL, NULL, NULL, 'Gradbar', 1,    NULL, NULL),
--  I — 1:a person singular
    (29, 15, 'sv', 'jag',        NULL, NULL, NULL, NULL, NULL, 1, 1),
    (30, 15, 'fr', 'je',         NULL, NULL, NULL, NULL, NULL, 1, 1),
--  love — transitiv (tar infinitivfras som objekt)
    (31, 16, 'sv', 'älska',      NULL, 2, 1, NULL, NULL, NULL, NULL),
    (32, 16, 'fr', 'adorer',     NULL, 2, 1, NULL, NULL, NULL, NULL),
--  run — intransitiv
    (33, 17, 'sv', 'springa',    NULL, 1, 1, NULL, NULL, NULL, NULL),
    (34, 17, 'fr', 'courir',     NULL, 1, 1, NULL, NULL, NULL, NULL),
--  quickly — adverb
    (35, 18, 'sv', 'snabbt',     NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (36, 18, 'fr', 'vite',       NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  believe — transitiv
    (37, 19, 'sv', 'tro',        NULL, 2, 1, NULL, NULL, NULL, NULL),
    (38, 19, 'fr', 'croire',     NULL, 2, 1, NULL, NULL, NULL, NULL),
--  that (subjunktion) — oböjt
    (39, 20, 'sv', 'att',        NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (40, 20, 'fr', 'que',        NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  in (preposition)
    (41, 21, 'sv', 'i',          NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (42, 21, 'fr', 'dans',       NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  park (utrum sv, maskulin fr)
    (43, 22, 'sv', 'park',       1,    2, 1, NULL, NULL, NULL, NULL),
    (44, 22, 'fr', 'parc',       1,    2, 1, NULL, NULL, NULL, NULL),
--  and / but / or — konjunktioner, oböjda
    (45, 23, 'sv', 'och',        NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (46, 23, 'fr', 'et',         NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (47, 24, 'sv', 'men',        NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (48, 24, 'fr', 'mais',       NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (49, 25, 'sv', 'eller',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (50, 25, 'fr', 'ou',         NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  often — adverb
    (51, 26, 'sv', 'ofta',       NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (52, 26, 'fr', 'souvent',    NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  school — utrum sv (genus=1), féminin fr (genus=2)
    (53, 27, 'sv', 'skola',      1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (54, 27, 'fr', 'école',      2,    NULL, NULL, NULL, NULL, NULL, NULL);


/* ════════════════════════════════════════════════════════════
   FORMER – SVENSKA
   tempus (bitmask): 1=Infinitiv 2=Presens 4=Preteritum 8=Supinum 16=Imperativ
                     32=Preteritum perfekt 64=Futurum
   Svenska preteritum (4) och preteritum perfekt (32) är SEPARATA former:
     tempus=4  → enkelt preteritum (åt, gav …)
     tempus=32 → sammansatt perfekt (har ätit, har gett …)
   grad: 1=Positiv 2=Komparativ 3=Superlativ
════════════════════════════════════════════════════════════ */

-- äta (lexem_id=1)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (1, 'äta',      1),
    (1, 'äter',     2),
    (1, 'åt',       4),
    (1, 'har ätit', 32),
    (1, 'ätit',     8),
    (1, 'ät',       16);

-- boll (lexem_id=3)
INSERT INTO Former (lexem_id, form, numerus, species, kasus) VALUES
    (3, 'boll',      1, 1, 7),
    (3, 'bollen',    1, 2, 7),
    (3, 'bollar',    2, 1, 7),
    (3, 'bollarna',  2, 2, 7),
    (3, 'bolls',     1, 1, 8),
    (3, 'bollens',   1, 2, 8),
    (3, 'bollars',   2, 1, 8),
    (3, 'bollarnas', 2, 2, 8);

-- gullig (lexem_id=5)
INSERT INTO Former (lexem_id, form, numerus, species, genus, grad) VALUES
    (5, 'gullig',     1, 1, 1,    1),
    (5, 'gulligt',    1, 1, 2,    1),
    (5, 'gulliga',    2, 1, NULL, 1),
    (5, 'gulliga',    1, 2, NULL, 1),
    (5, 'gulligare',  NULL, NULL, NULL, 2),
    (5, 'gulligast',  NULL, 1,    NULL, 3),
    (5, 'gulligaste', NULL, 2,    NULL, 3);

-- han (lexem_id=7)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (7, 'han',   1),
    (7, 'honom', 6),
    (7, 'hans',  8);

-- gilla (lexem_id=9)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (9, 'gilla',      1),
    (9, 'gillar',     2),
    (9, 'gillade',    4),
    (9, 'har gillat', 32),
    (9, 'gillat',     8),
    (9, 'gilla',      16);

-- regna (lexem_id=11)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (11, 'regna',      1),
    (11, 'regnar',     2),
    (11, 'regnade',    4),
    (11, 'har regnat', 32),
    (11, 'regnat',     8),
    (11, 'regna',      16);

-- röd (lexem_id=13)
INSERT INTO Former (lexem_id, form, numerus, species, genus, grad) VALUES
    (13, 'röd',      1, 1, 1,    1),
    (13, 'rött',     1, 1, 2,    1),
    (13, 'röda',     1, 2, NULL, 1),
    (13, 'röda',     2, 1, NULL, 1),
    (13, 'röda',     2, 2, NULL, 1),
    (13, 'rödare',   NULL, NULL, NULL, 2),
    (13, 'rödast',   NULL, 1,    NULL, 3),
    (13, 'rödaste',  NULL, 2,    NULL, 3);

-- snäll (lexem_id=15)
INSERT INTO Former (lexem_id, form, numerus, species, genus, grad) VALUES
    (15, 'snäll',     1, 1, 1,    1),
    (15, 'snällt',    1, 1, 2,    1),
    (15, 'snälla',    1, 2, NULL, 1),
    (15, 'snälla',    2, 1, NULL, 1),
    (15, 'snälla',    2, 2, NULL, 1),
    (15, 'snällare',  NULL, NULL, NULL, 2),
    (15, 'snällast',  NULL, 1,    NULL, 3),
    (15, 'snällaste', NULL, 2,    NULL, 3);

-- lärare (lexem_id=17)
INSERT INTO Former (lexem_id, form, numerus, species, kasus) VALUES
    (17, 'lärare',  1, 1, 7),
    (17, 'läraren', 1, 2, 7),
    (17, 'lärare',  2, 1, 7),
    (17, 'lärarna', 2, 2, 7);

-- ge (lexem_id=19)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (19, 'ge',       1),
    (19, 'ger',      2),
    (19, 'gav',      4),
    (19, 'har gett', 32),
    (19, 'gett',     8),
    (19, 'ge',       16);

-- trött (lexem_id=21)
-- samma form för utrum och neutrum i obestämd sg → genus=NULL
INSERT INTO Former (lexem_id, form, numerus, species, genus, grad) VALUES
    (21, 'trött',     1, 1, NULL, 1),
    (21, 'trötta',    1, 2, NULL, 1),
    (21, 'trötta',    2, 1, NULL, 1),
    (21, 'trötta',    2, 2, NULL, 1),
    (21, 'tröttare',  NULL, NULL, NULL, 2),
    (21, 'tröttast',  NULL, 1,    NULL, 3),
    (21, 'tröttaste', NULL, 2,    NULL, 3);

-- barn (lexem_id=23)
INSERT INTO Former (lexem_id, form, numerus, species, kasus) VALUES
    (23, 'barn',    1, 1, 7),
    (23, 'barnet',  1, 2, 7),
    (23, 'barn',    2, 1, 7),
    (23, 'barnen',  2, 2, 7);

-- bok (lexem_id=25)
INSERT INTO Former (lexem_id, form, numerus, species, kasus) VALUES
    (25, 'bok',      1, 1, 7),
    (25, 'boken',    1, 2, 7),
    (25, 'böcker',   2, 1, 7),
    (25, 'böckerna', 2, 2, 7);

-- vacker (lexem_id=27)
INSERT INTO Former (lexem_id, form, numerus, species, genus, grad) VALUES
    (27, 'vacker',    1, 1, 1,    1),
    (27, 'vackert',   1, 1, 2,    1),
    (27, 'vackra',    1, 2, NULL, 1),
    (27, 'vackra',    2, 1, NULL, 1),
    (27, 'vackra',    2, 2, NULL, 1),
    (27, 'vackrare',  NULL, NULL, NULL, 2),
    (27, 'vackrast',  NULL, 1,    NULL, 3),
    (27, 'vackraste', NULL, 2,    NULL, 3);


-- jag (lexem_id=29)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (29, 'jag',  1),
    (29, 'mig',  6),
    (29, 'min',  8);

-- älska (lexem_id=31)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (31, 'älska',      1),
    (31, 'älskar',     2),
    (31, 'älskade',    4),
    (31, 'har älskat', 32),
    (31, 'älskat',     8),
    (31, 'älska',      16);

-- springa (lexem_id=33)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (33, 'springa',      1),
    (33, 'springer',     2),
    (33, 'sprang',       4),
    (33, 'har sprungit', 32),
    (33, 'sprungit',     8),
    (33, 'spring',       16);

-- snabbt (lexem_id=35) — oböjt adverb
INSERT INTO Former (lexem_id, form) VALUES
    (35, 'snabbt');

-- tro (lexem_id=37)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (37, 'tro',       1),
    (37, 'tror',      2),
    (37, 'trodde',    4),
    (37, 'har trott', 32),
    (37, 'trott',     8),
    (37, 'tro',       16);

-- att (lexem_id=39) — subjunktion, oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (39, 'att');


/* ════════════════════════════════════════════════════════════
   FORMER – FRANSKA
   • species används inte (bestämdhet = separat artikel)
   • Adjektiv böjs i genus och numerus, inte species
   • Preteritum (4)         = imparfait
   • Preteritum perfekt (32) = passé composé
   • Supinum (8)            = participe passé
   • Franska superlativ: artikel från NP + "plus" + adjektivform (positiv/komparativ)
     → lagras UTAN inbäddad artikel, t.ex. "plus beau" inte "le plus beau"
   grad: 1=Positiv 2=Komparativ 3=Superlativ
════════════════════════════════════════════════════════════ */

-- manger (lexem_id=2)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (2, 'manger', 1),
    (2, 'mangé',  8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (2, 'mange',    2, 1, 1),
    (2, 'manges',   2, 2, 1),
    (2, 'mange',    2, 3, 1),
    (2, 'mangeons', 2, 1, 2),
    (2, 'mangez',   2, 2, 2),
    (2, 'mangent',  2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (2, 'mangeais',   4, 1, 1),
    (2, 'mangeais',   4, 2, 1),
    (2, 'mangeait',   4, 3, 1),
    (2, 'mangions',   4, 1, 2),
    (2, 'mangiez',    4, 2, 2),
    (2, 'mangeaient', 4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (2, 'ai mangé',    32, 1, 1),
    (2, 'as mangé',    32, 2, 1),
    (2, 'a mangé',     32, 3, 1),
    (2, 'avons mangé', 32, 1, 2),
    (2, 'avez mangé',  32, 2, 2),
    (2, 'ont mangé',   32, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (2, 'mange',    16, 2, 1),
    (2, 'mangeons', 16, 1, 2),
    (2, 'mangez',   16, 2, 2);

-- balle (lexem_id=4)
INSERT INTO Former (lexem_id, form, numerus, kasus) VALUES
    (4, 'balle',  1, 7),
    (4, 'balles', 2, 7);

-- mignon (lexem_id=6)
-- Superlativ utan inbäddad artikel: "plus mignon" (NP-artikeln läggs till av renderaren)
INSERT INTO Former (lexem_id, form, numerus, genus, grad) VALUES
    (6, 'mignon',         1, 1, 1),
    (6, 'mignonne',       1, 2, 1),
    (6, 'mignons',        2, 1, 1),
    (6, 'mignonnes',      2, 2, 1),
    (6, 'plus mignon',    1, 1, 2),
    (6, 'plus mignonne',  1, 2, 2),
    (6, 'plus mignons',   2, 1, 2),
    (6, 'plus mignonnes', 2, 2, 2),
    (6, 'plus mignon',    1, 1, 3),
    (6, 'plus mignonne',  1, 2, 3),
    (6, 'plus mignons',   2, 1, 3),
    (6, 'plus mignonnes', 2, 2, 3);

-- il (lexem_id=8)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (8, 'il',  1),
    (8, 'le',  2),
    (8, 'lui', 4),
    (8, 'son', 8);

-- aimer (lexem_id=10)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (10, 'aimer', 1),
    (10, 'aimé',  8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (10, 'aime',   2, 1, 1),
    (10, 'aimes',  2, 2, 1),
    (10, 'aime',   2, 3, 1),
    (10, 'aimons', 2, 1, 2),
    (10, 'aimez',  2, 2, 2),
    (10, 'aiment', 2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (10, 'aimais',   4, 1, 1),
    (10, 'aimais',   4, 2, 1),
    (10, 'aimait',   4, 3, 1),
    (10, 'aimions',  4, 1, 2),
    (10, 'aimiez',   4, 2, 2),
    (10, 'aimaient', 4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (10, 'ai aimé',    32, 1, 1),
    (10, 'as aimé',    32, 2, 1),
    (10, 'a aimé',     32, 3, 1),
    (10, 'avons aimé', 32, 1, 2),
    (10, 'avez aimé',  32, 2, 2),
    (10, 'ont aimé',   32, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (10, 'aime',   16, 2, 1),
    (10, 'aimons', 16, 1, 2),
    (10, 'aimez',  16, 2, 2);

-- pleuvoir (lexem_id=12)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (12, 'pleuvoir', 1),
    (12, 'plu',      8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (12, 'pleut',    2,  3, 1),
    (12, 'pleuvait', 4,  3, 1),
    (12, 'a plu',    32, 3, 1);

-- rouge (lexem_id=14)
-- Invariant: samma form för maskulin/feminin → genus=NULL
-- Superlativ utan inbäddad artikel
INSERT INTO Former (lexem_id, form, numerus, genus, grad) VALUES
    (14, 'rouge',       1, NULL, 1),
    (14, 'rouges',      2, NULL, 1),
    (14, 'plus rouge',  1, NULL, 2),
    (14, 'plus rouges', 2, NULL, 2),
    (14, 'plus rouge',  1, NULL, 3),
    (14, 'plus rouges', 2, NULL, 3);

-- gentil (lexem_id=16)
INSERT INTO Former (lexem_id, form, numerus, genus, grad) VALUES
    (16, 'gentil',          1, 1, 1),
    (16, 'gentille',        1, 2, 1),
    (16, 'gentils',         2, 1, 1),
    (16, 'gentilles',       2, 2, 1),
    (16, 'plus gentil',     1, 1, 2),
    (16, 'plus gentille',   1, 2, 2),
    (16, 'plus gentils',    2, 1, 2),
    (16, 'plus gentilles',  2, 2, 2),
    (16, 'plus gentil',     1, 1, 3),
    (16, 'plus gentille',   1, 2, 3),
    (16, 'plus gentils',    2, 1, 3),
    (16, 'plus gentilles',  2, 2, 3);

-- professeur (lexem_id=18)
INSERT INTO Former (lexem_id, form, numerus, kasus) VALUES
    (18, 'professeur',  1, 7),
    (18, 'professeurs', 2, 7);

-- donner (lexem_id=20)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (20, 'donner', 1),
    (20, 'donné',  8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (20, 'donne',    2, 1, 1),
    (20, 'donnes',   2, 2, 1),
    (20, 'donne',    2, 3, 1),
    (20, 'donnons',  2, 1, 2),
    (20, 'donnez',   2, 2, 2),
    (20, 'donnent',  2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (20, 'donnais',   4, 1, 1),
    (20, 'donnais',   4, 2, 1),
    (20, 'donnait',   4, 3, 1),
    (20, 'donnions',  4, 1, 2),
    (20, 'donniez',   4, 2, 2),
    (20, 'donnaient', 4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (20, 'ai donné',    32, 1, 1),
    (20, 'as donné',    32, 2, 1),
    (20, 'a donné',     32, 3, 1),
    (20, 'avons donné', 32, 1, 2),
    (20, 'avez donné',  32, 2, 2),
    (20, 'ont donné',   32, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (20, 'donne',   16, 2, 1),
    (20, 'donnons', 16, 1, 2),
    (20, 'donnez',  16, 2, 2);

-- fatigué (lexem_id=22)
INSERT INTO Former (lexem_id, form, numerus, genus, grad) VALUES
    (22, 'fatigué',          1, 1, 1),
    (22, 'fatiguée',         1, 2, 1),
    (22, 'fatigués',         2, 1, 1),
    (22, 'fatiguées',        2, 2, 1),
    (22, 'plus fatigué',     1, 1, 2),
    (22, 'plus fatiguée',    1, 2, 2),
    (22, 'plus fatigués',    2, 1, 2),
    (22, 'plus fatiguées',   2, 2, 2),
    (22, 'plus fatigué',     1, 1, 3),
    (22, 'plus fatiguée',    1, 2, 3),
    (22, 'plus fatigués',    2, 1, 3),
    (22, 'plus fatiguées',   2, 2, 3);

-- enfant (lexem_id=24)
INSERT INTO Former (lexem_id, form, numerus, kasus) VALUES
    (24, 'enfant',  1, 7),
    (24, 'enfants', 2, 7);

-- livre (lexem_id=26)
INSERT INTO Former (lexem_id, form, numerus, kasus) VALUES
    (26, 'livre',  1, 7),
    (26, 'livres', 2, 7);

-- beau (lexem_id=28)
-- Oregelbunden: beau/belle/beaux/belles
-- Superlativ utan inbäddad artikel: "plus beau" (NP-artikeln gör det till superlativ)
INSERT INTO Former (lexem_id, form, numerus, genus, grad) VALUES
    (28, 'beau',        1, 1, 1),
    (28, 'belle',       1, 2, 1),
    (28, 'beaux',       2, 1, 1),
    (28, 'belles',      2, 2, 1),
    (28, 'plus beau',   1, 1, 2),
    (28, 'plus belle',  1, 2, 2),
    (28, 'plus beaux',  2, 1, 2),
    (28, 'plus belles', 2, 2, 2),
    (28, 'plus beau',   1, 1, 3),
    (28, 'plus belle',  1, 2, 3),
    (28, 'plus beaux',  2, 1, 3),
    (28, 'plus belles', 2, 2, 3);

-- je (lexem_id=30)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (30, 'je',  1),
    (30, 'me',  6),
    (30, 'mon', 8);

-- adorer (lexem_id=32)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (32, 'adorer', 1),
    (32, 'adoré',  8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (32, 'adore',    2, 1, 1),
    (32, 'adores',   2, 2, 1),
    (32, 'adore',    2, 3, 1),
    (32, 'adorons',  2, 1, 2),
    (32, 'adorez',   2, 2, 2),
    (32, 'adorent',  2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (32, 'adorais',   4, 1, 1),
    (32, 'adorais',   4, 2, 1),
    (32, 'adorait',   4, 3, 1),
    (32, 'adorions',  4, 1, 2),
    (32, 'adoriez',   4, 2, 2),
    (32, 'adoraient', 4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (32, 'ai adoré',    32, 1, 1),
    (32, 'as adoré',    32, 2, 1),
    (32, 'a adoré',     32, 3, 1),
    (32, 'avons adoré', 32, 1, 2),
    (32, 'avez adoré',  32, 2, 2),
    (32, 'ont adoré',   32, 3, 2);

-- courir (lexem_id=34)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (34, 'courir', 1),
    (34, 'couru',  8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (34, 'cours',   2, 1, 1),
    (34, 'cours',   2, 2, 1),
    (34, 'court',   2, 3, 1),
    (34, 'courons', 2, 1, 2),
    (34, 'courez',  2, 2, 2),
    (34, 'courent', 2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (34, 'courais',   4, 1, 1),
    (34, 'courais',   4, 2, 1),
    (34, 'courait',   4, 3, 1),
    (34, 'courions',  4, 1, 2),
    (34, 'couriez',   4, 2, 2),
    (34, 'couraient', 4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (34, 'ai couru',    32, 1, 1),
    (34, 'as couru',    32, 2, 1),
    (34, 'a couru',     32, 3, 1),
    (34, 'avons couru', 32, 1, 2),
    (34, 'avez couru',  32, 2, 2),
    (34, 'ont couru',   32, 3, 2);

-- vite (lexem_id=36) — invariant adverb
INSERT INTO Former (lexem_id, form) VALUES
    (36, 'vite');

-- croire (lexem_id=38) — oregelbundet verb
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (38, 'croire', 1),
    (38, 'cru',    8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (38, 'crois',    2, 1, 1),
    (38, 'crois',    2, 2, 1),
    (38, 'croit',    2, 3, 1),
    (38, 'croyons',  2, 1, 2),
    (38, 'croyez',   2, 2, 2),
    (38, 'croient',  2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (38, 'croyais',   4, 1, 1),
    (38, 'croyais',   4, 2, 1),
    (38, 'croyait',   4, 3, 1),
    (38, 'croyions',  4, 1, 2),
    (38, 'croyiez',   4, 2, 2),
    (38, 'croyaient', 4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (38, 'ai cru',    32, 1, 1),
    (38, 'as cru',    32, 2, 1),
    (38, 'a cru',     32, 3, 1),
    (38, 'avons cru', 32, 1, 2),
    (38, 'avez cru',  32, 2, 2),
    (38, 'ont cru',   32, 3, 2);

-- que (lexem_id=40) — subjunktion, oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (40, 'que');

-- i (lexem_id=41) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (41, 'i');

-- dans (lexem_id=42) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (42, 'dans');

-- park (lexem_id=43) — utrum
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (43, 'park',    1, 1),
    (43, 'parken',  1, 2),
    (43, 'parker',  2, 1),
    (43, 'parkerna',2, 2);

-- parc (lexem_id=44) — maskulin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (44, 'parc',  1),
    (44, 'parcs', 2);

-- konjunktioner (lexem_id 45-50) — oböjda
INSERT INTO Former (lexem_id, form) VALUES
    (45, 'och'),
    (46, 'et'),
    (47, 'men'),
    (48, 'mais'),
    (49, 'eller'),
    (50, 'ou'),
    (51, 'ofta'),
    (52, 'souvent');

-- skola (lexem_id=53) — utrum
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (53, 'skola',    1, 1),
    (53, 'skolan',   1, 2),
    (53, 'skolor',   2, 1),
    (53, 'skolorna', 2, 2);

-- école (lexem_id=54) — féminin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (54, 'école',   1),
    (54, 'écoles',  2);


/* ════════════════════════════════════════════════════════════
   LEXEM – FRÅGEORD
════════════════════════════════════════════════════════════ */
INSERT INTO Lexem (id, koncept_id, språk, lemma, genus, valens, personlighet, gradbarhet, prenominal, person, numerus) VALUES
--  to (preposition)
    (55, 28, 'sv', 'till',     NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (56, 28, 'fr', 'à',        NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  who — frågepronomen (animat)
    (57, 29, 'sv', 'vem',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (58, 29, 'fr', 'qui',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  what — frågepronomen (inanimat)
    (59, 30, 'sv', 'vad',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (60, 30, 'fr', 'que',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  where — frågadverb (plats)
    (61, 31, 'sv', 'var',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (62, 31, 'fr', 'où',       NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  when — frågadverb (tid)
    (63, 32, 'sv', 'när',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (64, 32, 'fr', 'quand',    NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  how — frågadverb (sätt)
    (65, 33, 'sv', 'hur',      NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (66, 33, 'fr', 'comment',  NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  why — frågadverb (orsak)
    (67, 34, 'sv', 'varför',   NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (68, 34, 'fr', 'pourquoi', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  which — interrogativ determinant (böjs i genus+numerus)
    (69, 35, 'sv', 'vilken',   NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (70, 35, 'fr', 'quel',     NULL, NULL, NULL, NULL, NULL, NULL, NULL);


/* ════════════════════════════════════════════════════════════
   FORMER – FRÅGEORD – SVENSKA
════════════════════════════════════════════════════════════ */

-- till (lexem_id=55) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (55, 'till');

-- vem (lexem_id=57) — kasus: nom+ack+dat=7, genitiv=8
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (57, 'vem',  7),
    (57, 'vems', 8);

-- vad (lexem_id=59) — oböjt i kasus
INSERT INTO Former (lexem_id, form) VALUES
    (59, 'vad');

-- var (lexem_id=61) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (61, 'var');

-- när (lexem_id=63) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (63, 'när');

-- hur (lexem_id=65) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (65, 'hur');

-- varför (lexem_id=67) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (67, 'varför');

-- vilken (lexem_id=69) — böjs i genus+numerus
INSERT INTO Former (lexem_id, form, numerus, genus) VALUES
    (69, 'vilken',  1, 1),
    (69, 'vilket',  1, 2),
    (69, 'vilka',   2, NULL);


/* ════════════════════════════════════════════════════════════
   FORMER – FRÅGEORD – FRANSKA
════════════════════════════════════════════════════════════ */

-- à (lexem_id=56) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (56, 'à');

-- qui (lexem_id=58) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (58, 'qui');

-- que (lexem_id=60) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (60, 'que');

-- où (lexem_id=62) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (62, 'où');

-- quand (lexem_id=64) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (64, 'quand');

-- comment (lexem_id=66) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (66, 'comment');

-- pourquoi (lexem_id=68) — oböjt
INSERT INTO Former (lexem_id, form) VALUES
    (68, 'pourquoi');

-- quel (lexem_id=70) — böjs i genus+numerus
INSERT INTO Former (lexem_id, form, numerus, genus) VALUES
    (70, 'quel',    1, 1),
    (70, 'quelle',  1, 2),
    (70, 'quels',   2, 1),
    (70, 'quelles', 2, 2);


/* ════════════════════════════════════════════════════════════
   NEGATIONSADVERB
   Oböjda. Svenska: standalone negation.
   Franska: ersätter "pas" i ne...X-konstruktionen.
════════════════════════════════════════════════════════════ */
INSERT INTO Lexem (id, koncept_id, språk, lemma, genus, valens, personlighet, gradbarhet, prenominal, person, numerus) VALUES
--  never (aldrig / jamais)
    (71, 36, 'sv', 'aldrig',       NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (72, 36, 'fr', 'jamais',       NULL, NULL, NULL, NULL, NULL, NULL, NULL),
--  no longer (inte längre / ne plus)
    (73, 37, 'sv', 'inte längre',  NULL, NULL, NULL, NULL, NULL, NULL, NULL),
    (74, 37, 'fr', 'plus',         NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO Former (lexem_id, form) VALUES
    (71, 'aldrig'),
    (72, 'jamais'),
    (73, 'inte längre'),
    (74, 'plus');


/* ════════════════════════════════════════════════════════════
   NYA ORD — KONCEPT
════════════════════════════════════════════════════════════ */
INSERT INTO Koncept (id, namn, ordklass) VALUES
    (38, 'come',    'Verb'),
    (39, 'become',  'Verb'),
    (40, 'get',     'Verb'),
    (41, 'we',      'Pronomen'),
    (42, 'they',    'Pronomen'),
    (43, 'dog',     'Substantiv'),
    (44, 'food',    'Substantiv'),
    (45, 'house',   'Substantiv'),
    (46, 'car',     'Substantiv'),
    (47, 'water',   'Substantiv'),
    (48, 'city',    'Substantiv');


/* ════════════════════════════════════════════════════════════
   NYA ORD — LEXEM
════════════════════════════════════════════════════════════ */
INSERT INTO Lexem (id, koncept_id, språk, lemma, genus, valens, personlighet, gradbarhet, prenominal, person, numerus) VALUES
--  come — intransitiv, rörelseverb
    (75, 38, 'sv', 'komma',       NULL, 1, 1, NULL, NULL, NULL, NULL),
    (76, 38, 'fr', 'venir',       NULL, 1, 1, NULL, NULL, NULL, NULL),
--  become — intransitiv
    (77, 39, 'sv', 'bli',         NULL, 1, 1, NULL, NULL, NULL, NULL),
    (78, 39, 'fr', 'devenir',     NULL, 1, 1, NULL, NULL, NULL, NULL),
--  get — transitiv
    (79, 40, 'sv', 'få',          NULL, 2, 1, NULL, NULL, NULL, NULL),
    (80, 40, 'fr', 'recevoir',    NULL, 2, 1, NULL, NULL, NULL, NULL),
--  we — 1:a person plural
    (81, 41, 'sv', 'vi',          NULL, NULL, NULL, NULL, NULL, 1, 2),
    (82, 41, 'fr', 'nous',        NULL, NULL, NULL, NULL, NULL, 1, 2),
--  they — 3:e person plural
    (83, 42, 'sv', 'de',          NULL, NULL, NULL, NULL, NULL, 3, 2),
    (84, 42, 'fr', 'ils',         NULL, NULL, NULL, NULL, NULL, 3, 2),
--  dog — sv: utrum(1)  fr: maskulin(1)
    (85, 43, 'sv', 'hund',        1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (86, 43, 'fr', 'chien',       1,    NULL, NULL, NULL, NULL, NULL, NULL),
--  food — sv: utrum(1)  fr: feminin(2)
    (87, 44, 'sv', 'mat',         1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (88, 44, 'fr', 'nourriture',  2,    NULL, NULL, NULL, NULL, NULL, NULL),
--  house — sv: neutrum(2)  fr: feminin(2)
    (89, 45, 'sv', 'hus',         2,    NULL, NULL, NULL, NULL, NULL, NULL),
    (90, 45, 'fr', 'maison',      2,    NULL, NULL, NULL, NULL, NULL, NULL),
--  car — sv: utrum(1)  fr: feminin(2)
    (91, 46, 'sv', 'bil',         1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (92, 46, 'fr', 'voiture',     2,    NULL, NULL, NULL, NULL, NULL, NULL),
--  water — sv: neutrum(2)  fr: feminin(2)
    (93, 47, 'sv', 'vatten',      2,    NULL, NULL, NULL, NULL, NULL, NULL),
    (94, 47, 'fr', 'eau',         2,    NULL, NULL, NULL, NULL, NULL, NULL),
--  city — sv: utrum(1)  fr: feminin(2)
    (95, 48, 'sv', 'stad',        1,    NULL, NULL, NULL, NULL, NULL, NULL),
    (96, 48, 'fr', 'ville',       2,    NULL, NULL, NULL, NULL, NULL, NULL);


/* ════════════════════════════════════════════════════════════
   NYA ORD — FORMER — SVENSKA
════════════════════════════════════════════════════════════ */

-- komma (lexem_id=75)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (75, 'komma',        1),
    (75, 'kommer',       2),
    (75, 'kom',          4),
    (75, 'har kommit',   32),
    (75, 'kommit',       8),
    (75, 'kom',          16);

-- bli (lexem_id=77)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (77, 'bli',          1),
    (77, 'blir',         2),
    (77, 'blev',         4),
    (77, 'har blivit',   32),
    (77, 'blivit',       8),
    (77, 'bli',          16);

-- få (lexem_id=79)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (79, 'få',           1),
    (79, 'får',          2),
    (79, 'fick',         4),
    (79, 'har fått',     32),
    (79, 'fått',         8);

-- vi (lexem_id=81)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (81, 'vi',    1),
    (81, 'oss',   6),
    (81, 'vår',   8);

-- de (lexem_id=83)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (83, 'de',     1),
    (83, 'dem',    6),
    (83, 'deras',  8);

-- hund (lexem_id=85)
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (85, 'hund',      1, 1),
    (85, 'hunden',    1, 2),
    (85, 'hundar',    2, 1),
    (85, 'hundarna',  2, 2);

-- mat (lexem_id=87)
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (87, 'mat',       1, 1),
    (87, 'maten',     1, 2),
    (87, 'maträtter', 2, 1),
    (87, 'maträtterna', 2, 2);

-- hus (lexem_id=89)
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (89, 'hus',    1, 1),
    (89, 'huset',  1, 2),
    (89, 'hus',    2, 1),
    (89, 'husen',  2, 2);

-- bil (lexem_id=91)
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (91, 'bil',      1, 1),
    (91, 'bilen',    1, 2),
    (91, 'bilar',    2, 1),
    (91, 'bilarna',  2, 2);

-- vatten (lexem_id=93)
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (93, 'vatten',    1, 1),
    (93, 'vattnet',   1, 2),
    (93, 'vatten',    2, 1),
    (93, 'vattnen',   2, 2);

-- stad (lexem_id=95)
INSERT INTO Former (lexem_id, form, numerus, species) VALUES
    (95, 'stad',      1, 1),
    (95, 'staden',    1, 2),
    (95, 'städer',    2, 1),
    (95, 'städerna',  2, 2);


/* ════════════════════════════════════════════════════════════
   NYA ORD — FORMER — FRANSKA
════════════════════════════════════════════════════════════ */

-- venir (lexem_id=76) — être-verb, maskulina former
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (76, 'venir', 1),
    (76, 'venu',  8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (76, 'viens',    2, 1, 1),
    (76, 'viens',    2, 2, 1),
    (76, 'vient',    2, 3, 1),
    (76, 'venons',   2, 1, 2),
    (76, 'venez',    2, 2, 2),
    (76, 'viennent', 2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (76, 'venais',    4, 1, 1),
    (76, 'venais',    4, 2, 1),
    (76, 'venait',    4, 3, 1),
    (76, 'venions',   4, 1, 2),
    (76, 'veniez',    4, 2, 2),
    (76, 'venaient',  4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (76, 'suis venu',    32, 1, 1),
    (76, 'es venu',      32, 2, 1),
    (76, 'est venu',     32, 3, 1),
    (76, 'sommes venus', 32, 1, 2),
    (76, 'êtes venus',   32, 2, 2),
    (76, 'sont venus',   32, 3, 2);

-- devenir (lexem_id=78) — être-verb
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (78, 'devenir', 1),
    (78, 'devenu',  8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (78, 'deviens',    2, 1, 1),
    (78, 'deviens',    2, 2, 1),
    (78, 'devient',    2, 3, 1),
    (78, 'devenons',   2, 1, 2),
    (78, 'devenez',    2, 2, 2),
    (78, 'deviennent', 2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (78, 'devenais',    4, 1, 1),
    (78, 'devenais',    4, 2, 1),
    (78, 'devenait',    4, 3, 1),
    (78, 'devenions',   4, 1, 2),
    (78, 'deveniez',    4, 2, 2),
    (78, 'devenaient',  4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (78, 'suis devenu',    32, 1, 1),
    (78, 'es devenu',      32, 2, 1),
    (78, 'est devenu',     32, 3, 1),
    (78, 'sommes devenus', 32, 1, 2),
    (78, 'êtes devenus',   32, 2, 2),
    (78, 'sont devenus',   32, 3, 2);

-- recevoir (lexem_id=80)
INSERT INTO Former (lexem_id, form, tempus) VALUES
    (80, 'recevoir', 1),
    (80, 'reçu',     8);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (80, 'reçois',    2, 1, 1),
    (80, 'reçois',    2, 2, 1),
    (80, 'reçoit',    2, 3, 1),
    (80, 'recevons',  2, 1, 2),
    (80, 'recevez',   2, 2, 2),
    (80, 'reçoivent', 2, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (80, 'recevais',    4, 1, 1),
    (80, 'recevais',    4, 2, 1),
    (80, 'recevait',    4, 3, 1),
    (80, 'recevions',   4, 1, 2),
    (80, 'receviez',    4, 2, 2),
    (80, 'recevaient',  4, 3, 2);

INSERT INTO Former (lexem_id, form, tempus, person, numerus) VALUES
    (80, 'ai reçu',    32, 1, 1),
    (80, 'as reçu',    32, 2, 1),
    (80, 'a reçu',     32, 3, 1),
    (80, 'avons reçu', 32, 1, 2),
    (80, 'avez reçu',  32, 2, 2),
    (80, 'ont reçu',   32, 3, 2);

-- nous (lexem_id=82)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (82, 'nous',   1),
    (82, 'nous',   6),
    (82, 'notre',  8);

-- ils (lexem_id=84)
INSERT INTO Former (lexem_id, form, kasus) VALUES
    (84, 'ils',   1),
    (84, 'les',   2),
    (84, 'leur',  4),
    (84, 'leur',  8);

-- chien (lexem_id=86) — maskulin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (86, 'chien',   1),
    (86, 'chiens',  2);

-- nourriture (lexem_id=88) — feminin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (88, 'nourriture',   1),
    (88, 'nourritures',  2);

-- maison (lexem_id=90) — feminin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (90, 'maison',   1),
    (90, 'maisons',  2);

-- voiture (lexem_id=92) — feminin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (92, 'voiture',   1),
    (92, 'voitures',  2);

-- eau (lexem_id=94) — feminin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (94, 'eau',   1),
    (94, 'eaux',  2);

-- ville (lexem_id=96) — feminin
INSERT INTO Former (lexem_id, form, numerus) VALUES
    (96, 'ville',   1),
    (96, 'villes',  2);


/* ════════════════════════════════════════════════════════════
   SEMANTIK  (bitmask på Koncept)
   1=Animat 2=Konkret 4=Abstrakt 8=Ätbar 16=Plats 32=Mänsklig
════════════════════════════════════════════════════════════ */

-- Substantiv
UPDATE Koncept SET semantik = 2          WHERE id = 2;   -- ball:    konkret
UPDATE Koncept SET semantik = 2 | 32 | 1 WHERE id = 9;   -- teacher: konkret + mänsklig + animat
UPDATE Koncept SET semantik = 2 | 32 | 1 WHERE id = 12;  -- child:   konkret + mänsklig + animat
UPDATE Koncept SET semantik = 2          WHERE id = 13;  -- book:    konkret
UPDATE Koncept SET semantik = 2 | 16     WHERE id = 22;  -- park:    konkret + plats
UPDATE Koncept SET semantik = 2 | 16     WHERE id = 27;  -- school:  konkret + plats

-- Pronomen (han, jag = animat + mänsklig)
UPDATE Koncept SET semantik = 1 | 32     WHERE id = 4;   -- he
UPDATE Koncept SET semantik = 1 | 32     WHERE id = 15;  -- I

-- Verb (rörelse)
UPDATE Koncept SET semantik = 64         WHERE id = 17;  -- run: rörelse
UPDATE Koncept SET semantik = 64         WHERE id = 38;  -- come: rörelse

-- Prepositioner (riktning)
UPDATE Koncept SET semantik = 128        WHERE id = 28;  -- to: riktning

-- Nya pronomen
UPDATE Koncept SET semantik = 1 | 32     WHERE id = 41;  -- we: animat + mänsklig
UPDATE Koncept SET semantik = 1 | 32     WHERE id = 42;  -- they: animat + mänsklig

-- Oräkneliga substantiv
UPDATE Lexem SET räknebar = 0 WHERE koncept_id = 44;  -- food: mat/nourriture
UPDATE Lexem SET räknebar = 0 WHERE koncept_id = 47;  -- water: vatten/eau

-- Nya substantiv
UPDATE Koncept SET semantik = 1 | 2      WHERE id = 43;  -- dog: animat + konkret
UPDATE Koncept SET semantik = 2 | 8      WHERE id = 44;  -- food: konkret + ätbar
UPDATE Koncept SET semantik = 2 | 16     WHERE id = 45;  -- house: konkret + plats
UPDATE Koncept SET semantik = 2          WHERE id = 46;  -- car: konkret
UPDATE Koncept SET semantik = 2          WHERE id = 47;  -- water: konkret
UPDATE Koncept SET semantik = 2 | 16     WHERE id = 48;  -- city: konkret + plats


/* ════════════════════════════════════════════════════════════
   MÖNSTER + MÖNSTERKRAV
   Semantiska användningsmönster per styrande ord.
════════════════════════════════════════════════════════════ */

-- eat (id=1): animat äter ätbart (eller konkret som fallback)
INSERT INTO Mönster (id, koncept_id, språk) VALUES (1, 1, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (1, 'subjekt', 1, NULL),   -- animat
    (1, 'objekt',  8, NULL);   -- ätbar

-- like (id=5): animat gillar vad som helst
INSERT INTO Mönster (id, koncept_id, språk) VALUES (2, 5, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (2, 'subjekt', 1, NULL);   -- animat

-- rain (id=6): inga krav (opersonligt, hanteras redan via personlighet)

-- give (id=10), mönster 1: animat ger konkret till animat
INSERT INTO Mönster (id, koncept_id, språk) VALUES (3, 10, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (3, 'subjekt', 1, NULL),   -- animat
    (3, 'objekt',  2, NULL),   -- konkret
    (3, 'io',      1, NULL);   -- animat

-- give (id=10), mönster 2: konkret ger abstrakt till animat
INSERT INTO Mönster (id, koncept_id, språk) VALUES (4, 10, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (4, 'subjekt', 2, NULL),   -- konkret
    (4, 'objekt',  4, NULL),   -- abstrakt
    (4, 'io',      1, NULL);   -- animat

-- love (id=16): animat älskar vad som helst
INSERT INTO Mönster (id, koncept_id, språk) VALUES (5, 16, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (5, 'subjekt', 1, NULL);   -- animat

-- run (id=17): animat springer
INSERT INTO Mönster (id, koncept_id, språk) VALUES (6, 17, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (6, 'subjekt', 1, NULL);   -- animat

-- believe (id=19): animat tror
INSERT INTO Mönster (id, koncept_id, språk) VALUES (7, 19, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (7, 'subjekt', 1, NULL);   -- animat

-- in (id=21): komplement = plats
INSERT INTO Mönster (id, koncept_id, språk) VALUES (8, 21, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (8, 'komplement', 16, NULL);   -- plats

-- to (id=28): komplement = plats
INSERT INTO Mönster (id, koncept_id, språk) VALUES (9, 28, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (9, 'komplement', 16, NULL);   -- plats

-- come (id=38): animat kommer
INSERT INTO Mönster (id, koncept_id, språk) VALUES (10, 38, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (10, 'subjekt', 1, NULL);   -- animat

-- become (id=39): animat blir
INSERT INTO Mönster (id, koncept_id, språk) VALUES (11, 39, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (11, 'subjekt', 1, NULL);   -- animat

-- get (id=40): animat får konkret
INSERT INTO Mönster (id, koncept_id, språk) VALUES (12, 40, NULL);
INSERT INTO MönsterKrav (mönster_id, slot, tagg, koncept_id) VALUES
    (12, 'subjekt', 1, NULL),   -- animat
    (12, 'objekt',  2, NULL);   -- konkret

COMMIT;
