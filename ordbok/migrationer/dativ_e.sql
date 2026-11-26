/* ── dativ-e — tyskans ålderdomliga dativ singular ──────────────────
   Modellgranskningen 2026-08-29 flaggade `dem Hunde` i fyra av svepets
   meningar: `Sie hilft dem Hunde nicht`, `hinter dem Hunde`, `vor dem
   Hunde`, `Helft dem Hunde!`.

   DATIV-E:ET ÄR INTE FEL, DET ÄR FÖRÅLDRAT. Enstaviga maskulina och neutra
   substantiv tog historiskt -e i dativ singular; i modern standardtyska är
   formen borta ur bruket och Duden märker den "veraltet oder gehoben". Kvar
   lever den bara i lexikaliserade uttryck — `zu Hause`, `im Grunde` — och
   de byggs inte ur dativcellen utan är egna fraser.

   Fem substantiv i hela lexikonet har den: Hals, Haus, Hemd, Hund, Hut.
   Alla fem hör till just den klassen, vilket är ett gott tecken på att
   formerna kommer ur en historisk källa och inte ur ett slumpfel.

   Bara SINGULAR rörs. Dativ plural behåller sitt -n (`den Hunden`), som är
   fullt levande och obligatoriskt.

   kasus 4 = dativ; numerus 1 = singular. Se _legend.yaml. */

UPDATE Former
SET form = (SELECT l.lemma FROM Lexem l WHERE l.id = Former.lexem_id)
WHERE numerus = 1
  AND kasus = 4
  AND lexem_id IN (
      SELECT l.id FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id
      WHERE l.språk = 'de' AND k.ordklass = 'Substantiv')
  AND form <> (SELECT l.lemma FROM Lexem l WHERE l.id = Former.lexem_id);
