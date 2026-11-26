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

DELETE FROM Former WHERE id = 37415;
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (721, 'kunna', 1, NULL, NULL, NULL, NULL, NULL, NULL, 1);
INSERT INTO Former (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates) VALUES (721, 'kan', 2, NULL, NULL, NULL, NULL, NULL, NULL, 1);
