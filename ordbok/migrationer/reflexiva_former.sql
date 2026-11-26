/* ── reflexiva_former — svenskan hade pronomenet inbakat i FORMEN ────
   `Former.form` stod som "skyndar sig", "oroade sig", "lärt sig". Det är
   rätt bara i tredje person: svenskans reflexiva pronomen kongruerar med
   subjektet — jag skyndar MIG, vi skyndar OSS, ni skyndar ER — så en
   inbakad `sig` gav facit "Vi skyndar sig".

   Samma sorts genväg som franskans 224 verbformer med subjektspronomenet
   inbakat (se kommentaren i rendering/fr.py): saknas mekanismen skriver
   någon in resultatet i datan, och felet blir osynligt.

   Pronomenet byggs numera av SvenskRenderare.reflexivpronomen, som läser
   reflexiviteten ur LEMMAT ("skynda sig") och böjer efter subjektet.
   Formerna ska därför stå nakna.

   34 rader, 6 koncept. Fem av dem i kog_lära var dessutom nonsens redan
   som de stod — "lärd sig", "lärdes sig", "lärts sig" är inte svenska.
   ──────────────────────────────────────────────────────────────── */
UPDATE Former
SET form = substr(form, 1, length(form) - 4)
WHERE form LIKE '% sig'
  AND lexem_id IN (SELECT id FROM Lexem WHERE språk = 'sv');
