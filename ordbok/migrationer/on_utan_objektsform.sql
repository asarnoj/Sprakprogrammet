/* ── franskans `on` har ingen objektsform ────────────────────────────
   Strukturkontrollen fann att TVÅ OLIKA SPECAR renderade identiskt i
   Julius logg: `Tu nous as.` byggd med objektet `pronomen_1pl` och samma
   mening byggd med `pronomen_impersonal`. Uppslaget förklarar varför:

       on    sujet=on   cod=nous   coi=nous
       nous  sujet=nous cod=nous   coi=nous

   `on` är ett SUBJEKTSKLITIKON i franskan och har ingen objektsform. Det
   som står i cod/coi är `nous`, alltså ett ANNAT ord som används
   suppletivt — och att lägga in det som en form av `on` gör två skilda
   betydelser omöjliga att skilja åt.

   Följden var inte bara tvetydighet utan FEL BETYDELSE: uppgiften "man"
   fick facit `Tu nous as`, som betyder "du har oss".

   Andra språk rörs inte, och det är avsiktligt — deras opersonliga
   pronomen HAR egna objektsformer: svenskans `man` (kasus 7, nom+ack),
   spanskans `uno`, italienskans `lo`. Bara franskan lånar.

   Utan formen kastar `Uppslag.form` för cod/coi, generatorn kastar
   kandidaten, och specen byggs aldrig. Det är rätt väg: renderaren ska
   vägra det språket inte kan uttrycka. */

DELETE FROM Former
WHERE id IN (
    SELECT f.id FROM Former f
    JOIN Lexem l ON l.id = f.lexem_id
    JOIN Koncept k ON k.id = l.koncept_id
    WHERE k.nyckel = 'pronomen_impersonal' AND l.språk = 'fr'
      AND f.form = 'nous');
