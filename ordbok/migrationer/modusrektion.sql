/* ── modusrektion ─────────────────────────────────────────────────────
   Vilket MODUS en bisats måste stå i, styrt av det ord som inleder eller
   styr den. Samma mekanism som kasusrektionen: ett Mönster med språk satt,
   på det STYRANDE ordets koncept, och kravet på den slot satsen fyller.

   fr "avant que" styr konjunktiv medan "après que" inte gör det, precis som
   de "mit" styr dativ medan "für" styr ackusativ. Det är en lexikal
   egenskap hos varje enskilt ord, per språk, och därför data — inte en
   lista i renderaren. Listan låg i renderaren fram till 2026-08-14 och
   användes då bara för att VÄGRA bygga meningen.

   MönsterKrav.tempus = 1024 (Vol i _legend.yaml) betyder konjunktiv.
   NULL betyder indikativ, vilket är normalfallet och därför otaggat.

   Ligger på två ordklasser:

     SUBJUNKTIONER  inleder satsen och styr den: bien que, para que,
                    benché. Slotten heter 'komplement' — det är satsen
                    subjunktionen tar, samma slotnamn som prepositionernas
                    komplement.

     VERB           styr satsen som argument: vouloir que, esperar que,
                    pensare che. Slotten är den verbet redan har sin
                    Bisatsfras på (objekt, kommunikat eller komplement),
                    så den måste slås upp ur det universella mönstret.

   VAD SOM MEDVETET INTE TAGGATS

   Fem subjunktioner styr konjunktiv BARA under villkor som specen inte
   uttrycker, och de lämnas i indikativ hellre än att gissa:

     es aunque      tar båda, och valet ändrar betydelsen: "aunque llueve"
                    (fastän det regnar, faktum) mot "aunque llueva" (även
                    om det skulle regna, medgivande). Konceptet heter
                    subj_trots_att och namnger den FAKTISKA läsningen, som
                    tar indikativ.
     es hasta que   konjunktiv när satsen syftar framåt, indikativ om ett
                    inträffat faktum: "hasta que venga" mot "hasta que vino".
     es cuando      samma villkor: "cuando venga" men "cuando vino".
     it finché      indikativ i normalt bruk; konjunktiven är litterär.
     fr au cas où   styr KONDITIONALIS, inte konjunktiv — ett tredje modus
                    som varken specen eller den här kolumnen uttrycker än.

   Villkoren i es hasta que/cuando går att härleda ur bisatsens tempus, som
   specen faktiskt bär. Det kräver en andra kolumn eller en regel, och är
   inte byggt.

   KÖRS EFTER monstertaggning.sql VID VARJE `ordbok import`.
   Idempotent: tar bort sina egna rader först.
   ──────────────────────────────────────────────────────────────── */

/* Rensa tidigare körning: mönstren den här filen äger är de språkspecifika
   på subjunktioner, plus tempus-kolumnen på verbens befintliga rader. */
DELETE FROM Mönster WHERE språk IS NOT NULL AND koncept_id IN
  (SELECT id FROM Koncept WHERE ordklass = 'Subjunktion');
UPDATE MönsterKrav SET tempus = NULL WHERE tempus IS NOT NULL;

/* ── subjunktioner ──────────────────────────────────────────────── */

INSERT INTO Mönster (koncept_id, språk)
SELECT id, 'fr' FROM Koncept WHERE ordklass = 'Subjunktion'
  AND nyckel IN ('subj_trots_att', 'subj_innan', 'subj_för_att', 'subj_tills');
INSERT INTO Mönster (koncept_id, språk)
SELECT id, 'es' FROM Koncept WHERE ordklass = 'Subjunktion'
  AND nyckel IN ('subj_innan', 'subj_för_att', 'subj_ifall');
INSERT INTO Mönster (koncept_id, språk)
SELECT id, 'it' FROM Koncept WHERE ordklass = 'Subjunktion'
  AND nyckel IN ('subj_trots_att', 'subj_innan', 'subj_för_att', 'subj_ifall');

/* bien que, avant que, pour que, jusqu'à ce que — alla obligatoriska
   antes de que, para que, en caso de que
   benché, prima che, affinché, nel caso che */
INSERT INTO MönsterKrav (mönster_id, slot, tempus)
SELECT m.id, 'komplement', 1024 FROM Mönster m
JOIN Koncept k ON k.id = m.koncept_id
WHERE m.språk IS NOT NULL AND k.ordklass = 'Subjunktion';

/* ── verb ───────────────────────────────────────────────────────── */

/* Verben har redan ett språkspecifikt mönster i flera fall (hjälpverb,
   infinitivmarkör), så här skapas ett bara när det saknas. Slotten hämtas
   ur det UNIVERSELLA mönstret, där Bisatsfras-biten sitter. */
INSERT INTO Mönster (koncept_id, språk)
SELECT k.id, s.språk FROM Koncept k
JOIN (SELECT 'fr' AS språk UNION SELECT 'es' UNION SELECT 'it') s
WHERE k.nyckel IN ('gen_önska', 'käns_hoppas', 'kog_tro', 'kog_tänka')
  AND NOT EXISTS (SELECT 1 FROM Mönster m
                  WHERE m.koncept_id = k.id AND m.språk = s.språk);

/* souhaiter/desear/desiderare que + konjunktiv — viljeverb i alla tre. */
INSERT INTO MönsterKrav (mönster_id, slot, tempus)
SELECT m.id, u.slot, 1024
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
JOIN Mönster um ON um.koncept_id = k.id AND um.språk IS NULL
JOIN MönsterKrav u ON u.mönster_id = um.id AND (u.frastyp & 32) = 32
WHERE m.språk IN ('fr', 'es', 'it') AND k.nyckel = 'gen_önska';

/* esperar/sperare que + konjunktiv, men franskans espérer tar INDIKATIV.
   Ett av de tydligaste fallen på att modusrektion är per språk och inte
   per betydelse: samma koncept, samma sats, olika modus i två av tre. */
INSERT INTO MönsterKrav (mönster_id, slot, tempus)
SELECT m.id, u.slot, 1024
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
JOIN Mönster um ON um.koncept_id = k.id AND um.språk IS NULL
JOIN MönsterKrav u ON u.mönster_id = um.id AND (u.frastyp & 32) = 32
WHERE m.språk IN ('es', 'it') AND k.nyckel = 'käns_hoppas';

/* credere/pensare che + konjunktiv — BARA italienskan. Franskan och
   spanskan tar indikativ efter jakande trosverb (je crois qu'il vient,
   creo que viene). */
INSERT INTO MönsterKrav (mönster_id, slot, tempus)
SELECT m.id, u.slot, 1024
FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
JOIN Mönster um ON um.koncept_id = k.id AND um.språk IS NULL
JOIN MönsterKrav u ON u.mönster_id = um.id AND (u.frastyp & 32) = 32
WHERE m.språk = 'it' AND k.nyckel IN ('kog_tro', 'kog_tänka');
