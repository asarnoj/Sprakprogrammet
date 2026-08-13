/* ── artikelläckage — 47 tyska substantivformer ──────────────────────
   Genereringen skrev in den bestämda artikeln i själva substantivformen:
   Schwester fick formen "der Schwester" i stället för "Schwester".

   Upptäckt 2026-08-13 när prepositionsfraser byggdes, genom att renderaren
   producerade "in der der Schule" — artikeln kom både från renderaren och
   ur formen. Det syntes aldrig tidigare, eftersom renderaren fram till dess
   satte artikeln och formen intill varandra utan att någon läste resultatet
   ord för ord.

   Granskningen missade dem: de är rätt BÖJDA, bara fel avgränsade. Alla 47
   är enordslemman vars form börjar med der/die/das/dem/den/des. Äkta
   flerordslemman som "älterer Bruder" rörs inte.
   ──────────────────────────────────────────────────────────────── */

UPDATE Former SET form = 'Schwester' WHERE id = 15231;
UPDATE Former SET form = 'Schwester' WHERE id = 15232;
UPDATE Former SET form = 'Schwestern' WHERE id = 15230;
UPDATE Former SET form = 'Schwestern' WHERE id = 15233;
UPDATE Former SET form = 'Schulter' WHERE id = 32772;
UPDATE Former SET form = 'Schulter' WHERE id = 32773;
UPDATE Former SET form = 'Schultern' WHERE id = 32771;
UPDATE Former SET form = 'Schultern' WHERE id = 32774;
UPDATE Former SET form = 'Schuh' WHERE id = 27484;
UPDATE Former SET form = 'Schuh' WHERE id = 27485;
UPDATE Former SET form = 'Schuh' WHERE id = 27487;
UPDATE Former SET form = 'Schuhes' WHERE id = 27488;
UPDATE Former SET form = 'Schuhen' WHERE id = 27486;
UPDATE Former SET form = 'Schuhe' WHERE id = 27489;
UPDATE Former SET form = 'Socke' WHERE id = 27525;
UPDATE Former SET form = 'Socke' WHERE id = 27526;
UPDATE Former SET form = 'Socken' WHERE id = 27524;
UPDATE Former SET form = 'Socken' WHERE id = 27527;
UPDATE Former SET form = 'See' WHERE id = 38186;
UPDATE Former SET form = 'See' WHERE id = 38187;
UPDATE Former SET form = 'See' WHERE id = 38189;
UPDATE Former SET form = 'Sees' WHERE id = 38190;
UPDATE Former SET form = 'Seen' WHERE id = 38188;
UPDATE Former SET form = 'Seen' WHERE id = 38191;
UPDATE Former SET form = 'Sekunde' WHERE id = 47966;
UPDATE Former SET form = 'Sekunde' WHERE id = 47967;
UPDATE Former SET form = 'Sekunden' WHERE id = 47965;
UPDATE Former SET form = 'Sekunden' WHERE id = 47968;
UPDATE Former SET form = 'Schule' WHERE id = 40128;
UPDATE Former SET form = 'Schule' WHERE id = 40129;
UPDATE Former SET form = 'Schulen' WHERE id = 40127;
UPDATE Former SET form = 'Schulen' WHERE id = 40130;
UPDATE Former SET form = 'Schwein' WHERE id = 13278;
UPDATE Former SET form = 'Schwein' WHERE id = 13279;
UPDATE Former SET form = 'Schweins' WHERE id = 13281;
UPDATE Former SET form = 'Schweinen' WHERE id = 13280;
UPDATE Former SET form = 'Schweine' WHERE id = 13282;
UPDATE Former SET form = 'Schüler' WHERE id = 45470;
UPDATE Former SET form = 'Schüler' WHERE id = 45471;
UPDATE Former SET form = 'Schüler' WHERE id = 45473;
UPDATE Former SET form = 'Schülers' WHERE id = 45474;
UPDATE Former SET form = 'Schülern' WHERE id = 45472;
UPDATE Former SET form = 'Schüler' WHERE id = 45475;
UPDATE Former SET form = 'Situation' WHERE id = 409;
UPDATE Former SET form = 'Situation' WHERE id = 410;
UPDATE Former SET form = 'Situationen' WHERE id = 408;
UPDATE Former SET form = 'Situationen' WHERE id = 411;
