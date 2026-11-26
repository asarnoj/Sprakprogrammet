/* ── prenominal_fasta — adjektivposition i språk där den är invariant ───────
   Tyska, engelska och japanska har attributivt adjektiv ALLTID före
   substantivet. Det finns inget att bedöma per ord, så det sätts
   deterministiskt i stället för via LLM.

   Bakgrund: lexemtaggningens prompt gav bara positionsregler för de
   romanska språken och svenska, så 30 tyska adjektiv blev otaggade och
   engelska och japanska kördes aldrig alls (tagga-lexem loopar bara över
   genusspråken).

   KÖRS EFTER VARJE `ordbok import`, efter lexemtaggning.sql.
   ─────────────────────────────────────────────────────────────────────── */

UPDATE Lexem SET prenominal = 1
 WHERE språk IN ('de', 'en', 'ja')
   AND koncept_id IN (SELECT id FROM Koncept WHERE ordklass = 'Adjektiv');
