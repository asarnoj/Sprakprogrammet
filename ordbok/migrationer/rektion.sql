/* ── rektion — språkspecifik kasus- och prepositionsstyrning ─────────
   Andra passet som monstertaggning.sql pekar ut: de universella mönstren
   (språk = NULL) säger VILKA slots ett verb har, den här filen säger hur
   de realiseras i ett enskilt språk.

   Mekanism: Mönster.språk finns och är nullbar just för det här. Ett
   mönster med språk = 'de' skuggar det universella för tyska, och bär
   bara de krav som skiljer sig. Renderaren tar slotstrukturen ur det
   universella mönstret och rektionen ur det språkspecifika. Inget nytt
   i schemat — kolumnerna kasus och preposition_koncept_id fanns redan.

   Omfattningen är liten: bara fem koncept har io-slot (fys_ge,
   gen_erbjuda, kom_berätta, kom_fråga, kom_meddela), och tyskan har sex
   dativstyrande verb bland dem som har objekt-slot.

   Tyskan är inte enhetlig, vilket är hela poängen med kolumnen:
     geben, anbieten, erzählen  →  io i DATIV  ("ich gebe dir das Buch")
     fragen, benachrichtigen    →  io i ACKUSATIV ("ich frage dich etwas")
   Utan det här blir tyska meningar fel oavsett hur korrekt Former är.

   kasus-koder ur _legend.yaml: Nom=1, Ack=2, Dat=4, Gen=8.
   KÖRS EFTER monstertaggning.sql VID VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* ── tyska: ditransitiva mönster ──────────────────────────────────── */
INSERT INTO Mönster (koncept_id, språk)
SELECT id, 'de' FROM Koncept
WHERE nyckel IN ('fys_ge', 'gen_erbjuda', 'kom_berätta', 'kom_fråga', 'kom_meddela');

/* io i dativ: geben, anbieten, erzählen */
INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'io', 4 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de' AND k.nyckel IN ('fys_ge', 'gen_erbjuda', 'kom_berätta');

/* io i ackusativ: fragen tar dubbel ackusativ, benachrichtigen ackusativ */
INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'io', 2 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de' AND k.nyckel IN ('kom_fråga', 'kom_meddela');

/* direkt objekt i ackusativ i samtliga fem */
INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'objekt', 2 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de'
  AND k.nyckel IN ('fys_ge', 'gen_erbjuda', 'kom_berätta', 'kom_fråga', 'kom_meddela');

/* ── tyska: verb som styr dativ på sitt enda objekt ───────────────── */
INSERT INTO Mönster (koncept_id, språk)
SELECT id, 'de' FROM Koncept
WHERE nyckel IN ('arb_hjälpa', 'gen_lita', 'gen_passa', 'rör_följa',
                 'soc_förlåta', 'soc_tacka');

INSERT INTO MönsterKrav (mönster_id, slot, kasus)
SELECT m.id, 'objekt', 4 FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk = 'de' AND k.nyckel IN ('arb_hjälpa', 'gen_lita', 'gen_passa',
                                      'rör_följa', 'soc_förlåta', 'soc_tacka');
/* helfen, vertrauen, passen, folgen, vergeben, danken — alla med dativ.
   Jämför vermissen, mögen, erreichen, treffen som tar ackusativ och
   därför inte behöver någon rad alls: ackusativ är default. */

/* ── romanska: io realiseras med preposition ──────────────────────── */
INSERT INTO Mönster (koncept_id, språk)
SELECT k.id, s.språk FROM Koncept k
JOIN (SELECT 'fr' AS språk UNION SELECT 'es' UNION SELECT 'it') s
WHERE k.nyckel IN ('fys_ge', 'gen_erbjuda', 'kom_berätta', 'kom_fråga');

INSERT INTO MönsterKrav (mönster_id, slot, preposition_koncept_id)
SELECT m.id, 'io', (SELECT id FROM Koncept WHERE nyckel = 'prep_till')
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk IN ('fr', 'es', 'it')
  AND k.nyckel IN ('fys_ge', 'gen_erbjuda', 'kom_berätta', 'kom_fråga');
/* prep_till är fr à, es a, it a — donner à, dar a, dare a.
   kom_meddela är medvetet utelämnat: fr "informer quelqu'un" och it
   "informare qualcuno" tar direkt objekt, inte preposition. Verbspecifikt
   och inte samma mönster som de andra fyra. */
