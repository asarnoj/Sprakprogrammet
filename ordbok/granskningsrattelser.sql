/* ── granskningsrattelser — LOGG, INTE EN MIGRATION ─────────────────
   Genererad av `ordbok tillämpa-granskning`. Granskningen tog fram
   förslagen; det här skriver bara in dem, utan att fråga någon
   modell. ordbok/beslut.tsv går före när granskningen har fel.

   SPELA INTE UPP DEN HÄR FILEN IGEN. Satserna är knutna till
   Former.id, och DELETE/INSERT flyttar id:n — mot en ombyggd
   databas träffar de fel rader. Därför ligger filen medvetet
   UTANFÖR ordbok/migrationer/, som körs i en loop vid varje
   ombyggnad.

   Rättelserna bevaras i stället genom `ordbok exportera-former
   ordbok/former.tsv` direkt efter körningen. Då är de en del av
   datan. Filen finns kvar bara för att gå att läsa i efterhand.
   ──────────────────────────────────────────────────────────────── */

UPDATE Former SET form = 'blauesten' WHERE id = 19737;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3846, 'Leben', NULL, 11, 2, NULL, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3846, 'Leben', NULL, 4, 2, NULL, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 26940;
DELETE FROM Former WHERE id = 44284;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3713, 'Professor', NULL, 6, 1, NULL, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3713, 'Professors', NULL, 8, 1, NULL, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 47753;
DELETE FROM Former WHERE id = 24928;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (1837, 'finden', 1026, NULL, 2, NULL, NULL, NULL, 1, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (1837, 'Finden wir', 16, NULL, 2, NULL, NULL, NULL, 1, 1);
UPDATE Former SET form = 'fandest' WHERE id = 24921;
UPDATE Former SET form = 'Finden Sie' WHERE id = 24926;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (53, 'ustedes', NULL, 8, NULL, NULL, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 5367;
DELETE FROM Former WHERE id = 5366;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (161, 'qu''est-ce qui', NULL, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3215, 'neiges', NULL, NULL, 2, NULL, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (751, 'veuille', 16, NULL, 1, NULL, NULL, NULL, 2, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (751, 'veuillons', 16, NULL, 2, NULL, NULL, NULL, 1, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (751, 'veuillez', 16, NULL, 2, NULL, NULL, NULL, 2, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4135, 'minore', NULL, NULL, 1, NULL, NULL, 2, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4135, 'minori', NULL, NULL, 2, NULL, NULL, 2, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4135, 'minore', NULL, NULL, 1, NULL, NULL, 3, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4135, 'minori', NULL, NULL, 2, NULL, NULL, 3, NULL, NULL);
DELETE FROM Former WHERE id = 14776;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (157, 'chi', NULL, 7, NULL, NULL, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 14785;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (164, 'cosa', NULL, 7, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (69, 'sé', NULL, 8, NULL, NULL, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 35567;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3400, 'caffè', NULL, NULL, 2, NULL, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 21691;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2098, 'migliorate', 2, NULL, 2, NULL, NULL, NULL, 2, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2098, 'miglioriate', 1040, NULL, 2, NULL, NULL, NULL, 2, 1);
UPDATE Former SET form = 'giocherebbero' WHERE id = 24701;
DELETE FROM Former WHERE id = 45265;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2224, 'sposate', 18, NULL, 2, NULL, NULL, NULL, 2, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2224, 'sposiate', 1024, NULL, 2, NULL, NULL, NULL, 2, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4515, 'intressantare', NULL, NULL, NULL, NULL, NULL, 2, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4515, 'intressantast', NULL, NULL, NULL, NULL, NULL, 3, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4515, 'intressantaste', NULL, NULL, NULL, 2, NULL, 3, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4522, 'populärare', NULL, NULL, NULL, NULL, NULL, 2, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4522, 'populärast', NULL, NULL, NULL, NULL, NULL, 3, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (4522, 'populäraste', NULL, NULL, NULL, 2, NULL, 3, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2982, 'frysar', NULL, 7, 2, 1, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2982, 'frysars', NULL, 8, 2, 1, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2982, 'frysarna', NULL, 7, 2, 2, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2982, 'frysarnas', NULL, 8, 2, 2, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 26487;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2954, 'väggarna', NULL, 7, 2, 2, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2954, 'väggarnas', NULL, 8, 2, 2, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 32267;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2422, 'huvuden', NULL, 7, 2, 1, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2422, 'huvudens', NULL, 8, 2, 1, NULL, NULL, NULL, NULL);
DELETE FROM Former WHERE id = 35788;
DELETE FROM Former WHERE id = 35790;
DELETE FROM Former WHERE id = 35792;
DELETE FROM Former WHERE id = 47987;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3766, 'chefer', NULL, 7, 2, 1, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (3766, 'chefers', NULL, 8, 2, 1, NULL, NULL, NULL, NULL);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2114, 'förberedd', 8, NULL, 1, 1, 1, NULL, NULL, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2114, 'förberett', 8, NULL, 1, 1, 2, NULL, NULL, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (2114, 'förberedda', 8, NULL, NULL, NULL, 3, NULL, NULL, 1);
