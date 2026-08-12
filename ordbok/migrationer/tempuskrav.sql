/* ── tempuskrav — vilka tempus ett adverb får stå i ──────────────────
   Bitarna är tempus-bitarna ur _legend.yaml: Pres=2, Pret=4, Fut=64.
   NULL = passar alla tempus.

   Matchningen är MEDLEMSKAP, inte OCH: meningens tidsreferens ska finnas
   bland de tillåtna. Det skiljer sig från semantik/tagg, där konceptet
   måste ha alla krävda bitar. Se setup.sql.

   Bara fyra av femton tidsadverb taggas, och det är avsiktligt. "Nu gick
   han", "då ska jag gå", "snart kom han" och "plötsligt förstår jag" är
   alla korrekt svenska — de flesta tidsadverb är genuint tempusflexibla.
   Att tagga dem hårdare skulle blockera riktiga meningar för att fånga
   inbillade fel. Det som taggas är de fall där fel tempus är ett
   kategorifel, inte bara ovanligt.

   KÖRS EFTER VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────── */

/* igår kan bara stå i förfluten tid — "igår ger jag" är inte svenska,
   och inte engelska, tyska eller franska heller. Konceptet är
   språkoberoende och kravet gäller alla sju. */
UPDATE Koncept SET tempuskrav = 4  WHERE nyckel = 'adv_igår';
UPDATE Koncept SET tempuskrav = 64 WHERE nyckel = 'adv_imorgon';

/* "fortfarande" och "redan" refererar bakåt eller till nuet, aldrig framåt:
   "jag ska fortfarande gå" betyder inte vad det ser ut att betyda. */
UPDATE Koncept SET tempuskrav = 6 WHERE nyckel IN ('adv_fortfarande', 'adv_redan');
