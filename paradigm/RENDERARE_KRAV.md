# Vad renderaren behöver — vertikal skiva genom en mening

*2026-08-01. Metod: ta EN mening, specificera den för hand som det universella
objekt systemet är tänkt att bygga på, rendera den för hand till alla sju
språk, och notera vad varje steg behövde och varifrån.*

*Motivering: possessivhålet (PARAMETER_AUDIT §1b) hittades genom att fråga
"var tar den här formen vägen?". Samma fråga ställd om en hel mening hittar
resten. Övningen är billig nu och dyr när `Former` är fylld.*

---

## 1. Meningen

```
mönster:    fys_ge                      (Verb, valens=6 → Transitiv|Ditransitiv)
  subjekt:  pers_flicka                 bestämd, sg
  io:       fam_bror                    possessiv: poss_3sg_fem, koreferent med subjektet
  objekt:   skol_bok                    obestämd, sg, attribut: färg_röd
  adverbial: adv_igår
tempus:     förfluten tid, perfektiv aspekt
```

Samtliga sex koncept finns i databasen med lemman på alla sju språk.

| | |
|---|---|
| **sv** | Flickan gav sin bror en röd bok igår. |
| **en** | The girl gave her brother a red book yesterday. |
| **de** | Das Mädchen gab ihrem Bruder gestern ein rotes Buch. |
| **fr** | La fille a donné un livre rouge à son frère hier. |
| **es** | La chica le dio un libro rojo a su hermano ayer. |
| **it** | La ragazza ha dato un libro rosso a suo fratello ieri. |
| **ja** | 女の子は昨日、兄弟に赤い本をあげました。 |

Alla sju går att härleda ur specifikationen för hand. **Modellen bär** — det
som saknas är lagrade fakta och renderarkod, inte en riktig konstruktion.

---

## 2. Vad varje element krävde

| Element | Behövde | Källa |
|---|---|---|
| `flickan` / `la fille` | Former: species=Best, sg | ✅ Former |
| `das` / `la` / `il` | Artikelparadigm + huvudordets genus | ❌ §3.3 ❌ §3.1 |
| `gav` / `gab` / `dio` | Former: tempus=Pret (+person/numerus) | ✅ Former |
| `a donné` / `ha dato` | hjälpverb avoir/avere + particip | ❌ §3.4 |
| universell dåtid → cell | mappning per språk | ❌ §3.6 |
| `sin` (inte `hennes`) | diskriminator mellan multi-lemman | ❌ §3.7 |
| `sin` böjd efter *bror* | brors genus | ❌ §3.1 |
| `ihrem` | dativ (geben styr dativ) + Bruders genus | ❌ §3.5 ❌ §3.1 |
| `en` / `un` / `ein` | obestämd artikel + boks genus | ❌ §3.3 ❌ §3.1 |
| `röd` / `rotes` / `rouge` | boks genus, kasus, species=Bland (de) | ❌ §3.1 |
| `rouge` **efter** substantivet | `Lexem.prenominal` | ❌ §3.2 |
| `à son frère` / `a su hermano` | slot → preposition | ❌ §3.8 |
| `le dio` | spansk klitikdubblering | ❌ §3.9 |
| ordföljd (alla sju) | V2, TeKaMoLo, SOV, klitikaordning | ❌ §3.10 |
| `あげました` | ます-stam + た, komponerad | ❌ §3.11 |
| `igår` / `hier` / `昨日` | lemmat | ✅ Lexem |

---

## 3. Bristerna

### Grupp A — tomma kolumner som redan finns i schemat

#### 3.1 `Lexem.genus` är NULL för samtliga 3 669 lexem

Kolumnen finns och är dokumenterad i `setup.sql`, men ingen migration fyller
den och CSV-formatet (`koncept,ordklass,nivå,språk,lemma`) har ingen kolumn
för den.

Detta stoppar **varje nominalfras** i sv, de, fr, es och it: artikelval,
adjektivkongruens och possessivkongruens hämtar alla huvudordets genus.

Meningen innehåller fällan: tyska **`Mädchen` är neutrum**, inte femininum.
Det går inte att härleda ur betydelsen — det är precis vad kolumnen är till för.

#### 3.2 `Lexem.prenominal` är NULL för samtliga

Kolumnen finns för exakt det här: `un livre **rouge**`, `un libro **rojo**`,
`un libro **rosso**` står efter substantivet, medan germanska språk har
adjektivet före. Utan den hamnar adjektivet på fel sida i tre av sju språk.

Berör bara adjektivlexem (~780 rader).

### Grupp B — saknade paradigm

#### 3.3 Determinerarna har inga slot-filer

117 lexem i Artikel, Demonstrativ, Kvantifikator, Interrogativdeterminant och
Relativpronomen ligger i databasen som Koncept + Lexem men kan aldrig få
Former-rader. Sex av sju meningar ovan börjar med ett sådant ord.

PARAMETER_AUDIT §3 rekommenderade att hårdkoda dem i renderaren. Beslutet är
fortfarande öppet, men det måste tas — de kan inte bara lämnas.

#### 3.11 Japanskt artigt förflutet finns inte som cell

`ja/verb.yaml` har `masu` (artig presens) och `ta` (vanligt förflutet), men
inte kombinationen. `あげました` måste komponeras morfologiskt av renderaren
ur ます-stammen. Det är i linje med PARAMETER_AUDIT §2 ("register är INTE en
Former-axel"), men innebär att renderaren behöver böjningslogik för japanska
och inte bara uppslagning.

### Grupp C — saknade fält för renderarlagret

#### 3.4 Hjälpverbsvalet finns ingenstans

`a donné` kräver *avoir*, men `elle est allée` kräver *être*. Valet är en
lexikal egenskap per verb: fr être/avoir, de sein/haben, it essere/avere.
`Lexem` har ingen kolumn. Samma sak med participkongruens (`elle est allée`,
`les livres que j'ai lus`).

#### 3.5 Kasusrektion saknar plats i schemat

`MönsterKrav` har `slot, tagg, frastyp` men ingen kasuskolumn. Tyska `geben`
styr dativ på indirekt objekt; `in` styr ackusativ vid rörelse och dativ vid
befintlighet. Utan detta blir tyska meningar grammatiskt fel oavsett hur
korrekt `Former` är.

**Det här är det enda av bristerna som är ett verkligt hål i schemat** —
resten är ofylld data eller obyggd kod.

#### 3.6 Ingen mappning från universell tempus till cell

Specifikationen säger "förfluten tid, perfektiv". fr måste välja mellan
passé composé (`a donné`), passé simple (`donna`) och imparfait (`donnait`);
sv/en/de har inga celler alls för perfekt och futurum eftersom de är
analytiska. Mappningstabellen universell TAM → cell per språk finns inte.

#### 3.7 Multi-lemma saknar diskriminator

`poss_3sg_fem` har två svenska lemman, `hans` och `sin`, och ingenting säger
vilket som är den reflexiva varianten. Gäller redan ja 私/僕 och es ser/estar.
Enklaste fixen är en `variant`-kolumn på `Lexem`.

#### 3.8 Slot → preposition

Franskt och spanskt indirekt objekt realiseras med `à`/`a`. `MönsterKrav` har
en `preposition`-slot men inget sätt att säga "io-slotten realiseras med à i
franska".

#### 3.9 Språkspecifika syntaxregler

Spanskan kräver klitikdubblering: `le dio un libro a su hermano` — dativ­klitikan
`le` står kvar även när hela frasen finns utskriven.

#### 3.10 Ordföljd är inte representerad alls

Tysk V2 med verbfinal bisats, TeKaMoLo-ordning för adverbial, japansk SOV,
franska klitiska pronomen i fast inbördes ordning. Renderarkod snarare än
data, men den enskilt största posten som återstår.

---

## 4. Vad som INTE är blockerat

**Böjningskörningen.** `generera_former` hämtar bara `l.id, l.lemma` — den
läser aldrig `Lexem.genus` eller `prenominal`. Adjektivets egna former
(röd/rött/röda) beror inte på något substantivs genus, så genereringen ger
samma resultat oavsett om kolumnerna är fyllda.

Ingen av bristerna ovan tvingar fram en omkörning av `Former`. De kan alla
åtgärdas efteråt, till samma kostnad.

---

## 5. Skiss: de två taggningsmigrationerna

Skrivs som `ordbok/migrationer/genus.sql` och `prenominal.sql`, i samma stil
som `semantik.sql` — grupperade UPDATE-satser, körs om efter varje import.

> **Lägg inte halvfärdiga filer i `ordbok/migrationer/`.** RUNBOOK §3 kör
> `for m in ordbok/migrationer/*.sql`, så en stub skulle köras skarpt och
> lämna resten NULL utan att någon märker det. Skisserna står därför här.

### genus.sql

~3 669 värden över fem språk, alltså ~700 koncept × 5. Kodning enligt
BITMASK.md §5: sv 1=utrum 2=neutrum; fr/es/it 1=maskulin 2=feminin;
de 1=maskulin 2=feminin 3=neutrum. en/ja lämnas NULL.

```sql
/* ── genus — lexikalt genus per (lexem, språk) ──────────────────────────
   sv: 1=Utrum 2=Neutrum   fr/es/it: 1=Mask 2=Fem   de: 1=Mask 2=Fem 3=Neutr
   en/ja: NULL (genus saknas)
   KÖRS EFTER VARJE `ordbok import`.
   ──────────────────────────────────────────────────────────────────── */

UPDATE Lexem SET genus = 3 WHERE språk = 'de' AND lemma IN
  ('Mädchen', 'Buch', 'Kind', ...);          -- neutrum
UPDATE Lexem SET genus = 1 WHERE språk = 'de' AND lemma IN
  ('Bruder', 'Mann', 'Abend', ...);          -- maskulinum
UPDATE Lexem SET genus = 2 WHERE språk = 'de' AND lemma IN
  ('Frau', 'Antwort', 'Apotheke', ...);      -- femininum

UPDATE Lexem SET genus = 1 WHERE språk = 'sv' AND lemma IN
  ('flicka', 'bok', 'bror', ...);            -- utrum
UPDATE Lexem SET genus = 2 WHERE språk = 'sv' AND lemma IN
  ('hus', 'barn', ...);                      -- neutrum

UPDATE Lexem SET genus = 2 WHERE språk = 'fr' AND lemma IN
  ('fille', 'maison', ...);                  -- femininum
```

Framställning: en LLM-pass över (språk, lemma) i batchar om 20 → ~175 anrop.
Genus för A1–B1-ordförråd är något modellen kan nära nog perfekt, och
kaikki-dumparna finns för alla fem språken som facit vid stickprov.

### prenominal.sql

Bara adjektivlexem, ~780 rader. Default är prenominalt (NULL = 1), så filen
behöver bara lista undantagen.

```sql
/* ── prenominal — 0 = adjektivet står EFTER substantivet ────────────────
   NULL/1 = före (default). Romanska språk har efterställning som norm för
   de flesta beskrivande adjektiv; färg, form och nationalitet alltid efter.
   Undantag som står FÖRE i fr: grand, petit, bon, mauvais, jeune, vieux,
   beau, joli, nouveau, gros, long (BAGS-gruppen).
   ──────────────────────────────────────────────────────────────────── */

UPDATE Lexem SET prenominal = 0
  WHERE språk IN ('fr', 'es', 'it')
    AND koncept_id IN (SELECT id FROM Koncept WHERE ordklass = 'Adjektiv');

UPDATE Lexem SET prenominal = 1 WHERE språk = 'fr' AND lemma IN
  ('grand', 'petit', 'bon', 'mauvais', 'jeune', 'vieux', 'beau', 'joli',
   'nouveau', 'gros', 'long');
```

Franskans BAGS-undantag är den enda delen som kräver eftertanke; es/it är
nästan undantagslöst efterställda för beskrivande adjektiv.

---

## 6. Vad övningen validerade

Possessivomläggningen (PARAMETER_AUDIT §1b) bär i skarpt läge:

- fr `son frère` kongruerar med *frère*, inte med flickan — precis det som den
  gamla `kasus=Gen`-konventionen fick fel.
- en `her` hämtar ägarens genus från konceptet.
- ja ignorerar hela reflexivfrågan utan att något går sönder.

Och `Former` levererade varje form den ombads leverera. Ingen brist i den här
listan ligger i böjningslagret.
