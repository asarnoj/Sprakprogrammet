/* ── spår — hur rättningen kom fram till sin dom ─────────────────────
   Julius mätte symptomet: "jag gjorde jättemånga fel men ändå växte inte
   again, och ibland krympte new/due". Frågan gick inte att svara på ur
   `Mening` och `Repetition`, därför att de bara bevarar UTFALLET.

   Det som saknades är tre saker, och alla tre fanns i minnet en kort
   stund innan de kastades:

     svar          vad användaren faktiskt skrev. Lagrades ingenstans.
     anmärkningar  vad diffen SÅG — skrev/väntat/slutsats per fel, med
                   det kort felet lades på och om attributionen var osäker.
     kortlägen     varför varje kort fick eller INTE fick en dom.

   Den sista är den viktigaste och den som var omöjlig att härleda. Ett
   kort utan `Repetition`-rad kan ha hamnat där på fem olika sätt —
   undanhållet, skyddat, redan bedömt idag, redan fällt idag, eller aldrig
   prövat — och de har helt olika innebörd. Utan raden går det bara att
   gissa, vilket är precis vad som gjorde symptomet outrett.

   JSON OCH INTE KOLUMNER, med flit. Det här är DIAGNOSTIK: den läses av
   människor och verktyg som redan vet vad de letar efter, den ingår inte i
   någon modell, och inget beslut i programmet hänger på den. En relationell
   uppdelning hade kostat tre tabeller och gett noll frågor vi faktiskt
   ställer. Blir en fråga återkommande hör den hemma som en riktig kolumn.

   Spåret PÅVERKAR INGENTING. Det skrivs efter att domarna fallit och läses
   aldrig av schemaläggningen — annars vore det inte längre ett spår utan
   en del av modellen.
   ──────────────────────────────────────────────────────────────── */
CREATE TABLE IF NOT EXISTS Spår (
    id           INTEGER PRIMARY KEY,
    mening_id    INTEGER NOT NULL REFERENCES Mening(id) ON DELETE CASCADE,
    svar         TEXT,
    anmärkningar TEXT NOT NULL DEFAULT '[]',
    kortlägen    TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_spår_mening ON Spår(mening_id);
