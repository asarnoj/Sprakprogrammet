# Överlämning — Språkprogrammet, 2026-08-14

Klistra in det här i en ny chatt.

---

## Vad projektet är

En språkinlärningsapp som bygger meningar på sju språk (sv, en, fr, de, es,
it, ja) ur en gemensam språkoberoende beskrivning. Meningen definieras en
gång och renderas till valfritt språk. Spårar vad inläraren kan ner till
enskild ordform, med FSRS-schemaläggning.

**Scope:** grammatik och böjning. INTE talspråk, idiomatik eller register.

Databasen har tre lager: `Koncept` (språkoberoende begrepp) → `Lexem` (ordet
på ett språk) → `Former` (alla böjda former). Plus `Mönster`/`MönsterKrav`
som styr vilka ord som får kombineras.

---

## Var vi står

**Datalagret, renderaren och restriktionerna är klara. Meningsformen är
utbyggd genom tjugoen nivåer — stegen är slut. Generatorn är inte byggd.**

```
Koncept        736        Mönster        271   (universella
Lexem        5 149        MönsterKrav    390    + språkspecifika)
Former      50 026        Attributkrav    73
```

Tre lager fungerar:

1. **Böjning och taggning.** Alla 1 043 fel granskningen hittade är
   åtgärdade; `ordbok tillämpa-granskning --torkörning` ger noll satser.
   Alla sju språk är granskade av en starkare modell.
2. **Renderaren.** Sju språk, en klass per språk, `RomanskRenderare` som
   gemensam bas för fr/es/it. `ordbok rendera --exempel --språk <xx>`.
3. **Semantiska restriktioner.** `Koncept.semantik` × `MönsterKrav.tagg`,
   matchat i disjunktiv normalform: bitar inom en rad är OCH, flera rader
   är ELLER. Validatorn arbetar på **specen**, inte på den renderade
   strängen — alltså en gång för alla sju språk. 68 % av slumpmässiga
   ord­kombinationer avvisas (28 % när mätningen började).

**Nästa steg är meningsgeneratorn** — se
[`paradigm/GENERATOR.md`](paradigm/GENERATOR.md). Den var blockerad av
uttrycksförmågan. Det är den inte längre; se nåbarhetsmätningen nedan.

---

## Vad som gjordes sist (2026-08-13 — 08-14)

Elva konstruktioner byggdes, en i taget, var och en i alla sju språk innan
nästa påbörjades. Ordningen togs inte på känsla utan **härleddes ur
`MönsterKrav.slot` × `MönsterKrav.frastyp`** — en kolumn som legat ifylld
sedan mönstertaggningen utan att någon läst den. Metoden flyttade
predikativ och modalverb från sist till först, och avslöjade att stegen har
fyra dimensioner och inte en. Se GENERATOR.md, avsnittet med samma namn.

| Nivå | Konstruktion | Fältet i `Mening` |
|---|---|---|
| 10 | genitiv | `Nominalfras.ägare` |
| 11 | predikativ | `predikativ` |
| 12 | negation | `negerad` |
| 13 | infinitivkomplement | `komplement` |
| 14 | perfekt | `Aspekt.PERFEKT` |
| 15 | prepositionsfras | `Prepositionsfras` i `adverbial` |
| 16 | ja/nej-fråga | `fråga` |
| 17 | passiv | `Diates`, båda svenska passiverna |
| 18 | komparation | `Grad`, `jämförelse` |
| 19 | imperativ | `Satsmodus` |
| 20 | bisatser | `Bisats`, och `Mening` i `Mening` |
| 21 | wh-frågor | `fråga_om`, `Nominalfras.frågedeterminant` |

Renderarna växte med det: `kein` i tyskan, do-support i engelskan,
klitikaordning och sandhi i de romanska, ukemi-passiv och より-jämförelse i
japanskan, Satzklammer och kasusrektion i tyskan.

**Varje utökning drog fram datahål som granskningen inte kunde se**, därför
att hålen inte är felaktiga former utan *saknade* eller *felavgränsade*:

- 47 tyska substantivformer hade artikeln inbakad (`Schwester` →
  `"der Schwester"`). Syntes som "in der der Schule". Granskningen missade
  dem för att de är rätt böjda, fel avgränsade.
- Engelskans `be` saknade am/are/were. "The girls be happy" gick att bygga
  långt innan passiven fanns.
- `verb_ha` es var `tener`; spanskan bildar perfekt med `haber`. Tillagt som
  ett andra lexem under samma koncept med `variant='hjälpverb'`.
- Pronomenen saknade `genus` i fem språk → "elle est heureux".
- Tyskan saknade predikativa adjektivformer (111) och predikativ
  komparativ/superlativ (218). Adjektivparadigmets 144 celler är alla
  attributiva.
- `komp_mer`/`komp_mest` fanns inte. `adv2_mest` en betyder "mestadels".

Det generella mönstret: **det som inte händer syns aldrig i en räknare.**
Sex tysta icke-matchande strängersättningar hittades bara genom att läsa
utdata ord för ord, och två egna bitmask-buggar (`& 65535` och `& 1048575`
som båda skar av semantikbitar) syntes bara som "en dyr sol" respektive
som att 29 av 77 ord fick sin klass.

---

## Nåbarhet: hur mycket av beståndet specen når

Nytt verktyg: [`ordbok/verktyg/nåbarhet.py`](ordbok/verktyg/nåbarhet.py).
Det instrumenterar `Uppslag.form`, sveper hela korsprodukten av det
`Mening` kan uttrycka, och räknar unionen av begärda celler mot lexikonet.

```
sv  4 728 / 4 988   95 %      de 19 242 / 23 494   82 %
en  2 034 / 2 293   89 %      it  7 877 / 10 246   77 %
ja  1 472 / 2 498   59 %      fr  6 650 /  9 070   73 %
                              es  7 114 / 10 608   67 %
```

Svenskan: 37 % → 45 % (genitiv) → 71 % → 80 % → **95 %**.
Japanskan: 31 % → 45 % (imperativ) → **59 %** (bisatser).

**Siffran mäter svepet lika mycket som specen — FYRA gånger har svepet varit
det som begränsade**, och varje gång såg det ut som en spec-brist:

```
subjektet var alltid tredje person      hela personböjningen såg onåbar ut
attributet satt bara i objektet         bara ackusativ mättes
bisatsens subjekt var 3sg               2 av 12 konjunktivceller mättes
ägaren var alltid bestämd singular      genitivböjningen såg onåbar ut
```

Den sista tog svenskan från 80 till **95 %** och engelskan från 79 till 89 %
utan att en rad renderarkod ändrades. Mönstret är alltid detsamma: en axel
som varieras i huvudsatsen men inte i den inbäddade frasen.

Den tredje låg i RENDERAREN och är den viktiga. Japanskan mätte 31 % tills
uppmaningen byggdes, och även då syntes bara 8 av 346 nya former — därför
att renderaren hämtade cellerna direkt ur `_celler` i stället för genom
`Uppslag.form`, som är den enda väg instrumenteringen ser. Samma genväg
fanns i engelskans presens och preteritum och i den syntetiska
komparationen i sv/en/fr/es/it. Alla är omlagda, vilket lyfte sv 71→75 %,
en 72→78 % och ja 31→45 % **utan att ändra en enda renderad mening**.

Det spelar roll bortom mätningen: generatorns attribution ska gå samma väg.
En form som hämtas förbi `form()` går inte att knyta till ett kort, och
felet hade annars upptäckts först när generatorn inte kunde svara på vilket
kort som fällde en mening. Lägg till dimensionen i svepet — och kontrollera
att renderaren går genom `form()` — innan du drar slutsatsen att specen
inte når en cell.

Vad som faktiskt är onått, efter de rättelserna:

| Språk | Block | Vad som krävs |
|---|---|---|
| fr/es/it | konditionalis (6 celler per verb) | villkorssatser |
| es | konjunktiv imperfekt i huvudsats | villkorssatser |
| ja | ku, kereba, pot, vol | adverbiell adjektivform, villkor, potentialis, volitiv |

**Tyskan gick 36 → 82 % på två utökningar**, båda om nominalfrasens inre:
attributiv komparation och artikellös fras. Se de två avsnitten nedan.

---

## Passivbuggen — lagad 2026-08-14

Nåbarhetssvepet hittade att passiv i futurum och perfekt renderades som
presens i fem språk, och att `PASSIV_HÄNDELSE` + `FRAMTID` kastade
`KeyError` i svenskan. Regressionssvepen såg det aldrig: de sveper inte
diates × tempus × aspekt.

**Orsaken var densamma i alla fem.** Passivgrenen låg först i `verbdelar`
och returnerade innan tempus- och aspektlogiken — den byggde hjälpverbet
med en egen liten tempusmappning som bara kände presens och preteritum.

**Rättelsen tar bort de mappningarna i stället för att fylla på dem.**
Passiven är hjälpverb + particip, och hjälpverbet är ett verb: det böjs som
alla andra. Grenen bygger nu om meningen med `replace(m, verb=<hjälpverbet>,
diates=AKTIV)` och skickar den genom den aktiva grenen. Varje framtida
tempusutökning når därmed passiven gratis, i stället för att behöva skrivas
in på två ställen.

```
              nutid          förfluten        framtid              perfekt
sv   passiv   läses          lästes           ska läsas            har lästs
sv   bli      blir läst      blev läst        ska bli läst         har blivit läst
en            is read        was read         will be read         has been read
de            wird gelesen   wurde gelesen    wird gelesen werden  ist gelesen worden
fr            est lu         était lu         sera lu              a été lu
es            es leído       era leído        será leído           ha sido leído
it            è letto        era letto        sarà letto           è stato letto
ja            読まれます      読まれました      読まれます            読まれました
```

Tre saker föll ut på köpet:

- **Den sammansatta perfektiva passiven** ("a été lu", "è stato letto",
  "ha sido leído") stod som känd gräns och krävde tre verbdelar. Den byggs
  nu av sig själv, och kongruensen blir rätt utan en rad kod om den: `stato`
  böjs i italienskan men `été` inte i franskan, därför att essere tar
  essere och être tar avoir — och hjälpverbsvalet stod redan i datan.
- **Engelskan tappade negationen i passiv** ("The book is read" med
  `negerad=True`) och byggde "does not read" i stället för "has not read".
  Do-omskrivningen finns bara därför att en enkel presens saknar hjälpverb
  att fästa negationen på; den ligger nu sist, dit bara de fallen når.
- **Spanskans sammansatta gren slog upp `verb_vara` utan variant**, vilket
  gav RenderingsFel på "ha sido" eftersom ser och estar är två lexem. Den
  enkla grenen skickade varianten, den sammansatta inte.

**Ett datahål:** tyskt perfekt passiv heter "ist gelesen **worden**", inte
"geworden". Den ge-lösa formen finns bara som passivhjälpverb och låg inte i
databasen. Den ligger nu som en egen cell `part2_passiv` (Sup + Passiv) i
`paradigm/de/verb.yaml`, tom för alla verb utom `werden` — samma lösning som
svenskans s-passivceller, och samma mönster som engelskans nio be-celler.

---

## Imperativen — nivå 19

**Subjektet står kvar och namnger den tilltalade.** Imperativen fick inget
eget fält för det: person och numerus kommer därifrån precis som i alla
andra satser, restriktionsvalidatorn kan pröva tilltalet mot verbets
subjektskrav utan att veta något om imperativ, och renderaren tiger om
subjektet i stället för att specen ska tappa det. `Mening.modus` är en
`Satsmodus`-enum och inte ett `imperativ: bool`, eftersom konjunktiv och
konditionalis ska in i samma axel när bisatserna finns.

Fyra tilltal räcker: 2sg, 2pl, artig, 1pl. Det största paradigmet (es) har
fem celler, och den femte — ustedes — är `artig` i plural, vilket numerus
redan säger.

```
        2sg                2pl                  artig                1pl
sv      Läs boken!         Läs boken!           Läs boken!           ✋
en      Read the book!     Read the book!       Read the book!       ✋
de      Lies das Buch!     Lest das Buch!       Lesen Sie das Buch!  Lesen wir das Buch!
fr      Lis le livre!      Lisez le livre!      Lisez le livre!      Lisons le livre!
es      ¡Lee el libro!     ¡Leed el libro!      ¡Lea el libro!       ¡Leamos el libro!
it      Leggi il libro!    Leggete il libro!    Legga il libro!      Leggiamo il libro!
ja      本を読んでください。 (samma för alla tre tilltal)              本を読みましょう。
```

Nekad imperativ är **inte** samma form som jakande i två språk:

| Språk | Jakande | Nekad | Varför |
|---|---|---|---|
| es | ¡Lee! | ¡No **leas**! | hela paradigmet byter till presens konjunktiv |
| it | Leggi! | Non **leggere**! | bara 2sg, och dit till infinitiv |
| övriga | — | oförändrad form | negationen läggs bara till |

Svenskan och engelskan saknar 1pl-imperativ: "låt oss läsa", "let's read"
är omskrivningar med ett verb databasen inte har. De vägrar med ett besked
om just det i stället för att rendera något annat. Japanskans nekade
förslag (`読むのはやめましょう`) vägras av samma skäl.

**Två beslut, båda i `ordbok/beslut.tsv`:**

*Tyskans imperativformer ska inte innehålla subjektspronomenet.* 17 av 167
verb hade `lesen Sie` / `Lesen wir!` i cellen, 105 slutade på utropstecken
och 56 var versalinledda — tre konventioner i samma cell, och noll sådana
fall i någon annan tysk cell eller något annat språk. 141 former städade.
Pronomenet är ett eget ord som renderaren placerar, av samma skäl som
artiklarna lades i `Former` i stället för att bakas in i substantiven.

*Japansk uppmaning renderas som てください, inte som paradigmets 命令形.*
読め finns i datan och är morfologiskt imperativen, men är en ren befallning
som knappt förekommer i tal. Renderaren har redan valt artig stil åt hela
japanskan; att blanda in 読め vore inte ett registerval utan en
inkonsekvens. Register ligger utanför projektets scope — men just därför
måste språket hålla EN stil, och valet var redan gjort.

**Datafixen avslöjade ett indikativfel.** För `finden` och `kriechen`
kollapsade den trasiga imperativraden över `pres_1pl`: "wir finden"
renderades som **"Wir Finden wir."** Felet låg alltså inte bara i
imperativen, och det hade stått där sedan formerna genererades.

**Utökningen var värd 3 744 former**, inte de 161 den svenska tabellen i
GENERATOR.md förutspådde:

```
es +1 388   it +674   de +668   fr +507   ja +346   sv +161   en ±0
```

Spanskan vinner mest därför att den nekade imperativen drar in halva
konjunktivparadigmet. Engelskan vinner noll: `inf_imp` ÄR imperativcellen,
och den var redan nådd som infinitiv.

### Två gränser, båda medvetna

**Jakande imperativ med klitika är inte byggd i fr/es/it.** "Donne-le-moi",
"¡dámelo!", "dammelo!" kräver enklis — klitikan fäster EFTER verbet, med
bindestreck och moi/toi i franskan, accentflytt i spanskan och
konsonantfördubbling i italienskan. Nekad imperativ är proklitisk som alla
andra satser ("no me lo des") och fungerar. Renderaren vägrar med ett
besked som säger just det. Eftersom spanskan dubblerar det indirekta
objektet med klitika träffar gränsen varje spansk imperativ med io.

**Tyska partikelverb står fel — och gjorde det redan.** "Rufen an Sie!"
i stället för "Rufen Sie an!". Partikeln ligger i själva formen (`ruft an`),
och indikativen har samma fel: "Das Mädchen ruft an den Bruder." Partikeln
hör hemma i satsklammern, sist i satsen, där infinita verbdelar redan
hamnar. 14 tyska verb berörs. Inte lagat — det är en egen konstruktion, inte
en del av imperativen.

---

## Bisatserna — nivå 20

Den första konstruktionen där **`Mening` innehåller en `Mening`**. Allt som
går att säga i en huvudsats går därmed att säga i en bisats — tempus,
negation, passiv, perfekt, komparation — utan att något behövde läggas till.

`Bisats(subjunktion, sats)` fyller två roller, och skillnaden ligger i
subjunktionen och inte i strukturen:

- **argument** — `Mening.bisats`. Satsen ÄR objektet: "hon vet att han kom".
  Bara de 22 verb vars `MönsterKrav.frastyp & 32` är satt tar en sådan.
  (`frastyp` är en bitmask, inte en sträng — Bisatsfras är bit 32.)
- **adverbial** — i `adverbial`-tupeln bredvid `Prepositionsfras`. Satsen är
  en omständighet: "hon läste när han kom". Vilket verb som helst tar den.

```
sv  Hon vet att han kom.            Hon läste boken när han kom.
en  She knows that he came.         She read the book when he came.
de  Sie weiß, dass er kam.          Sie las das Buch, als er kam.
fr  Elle sait qu'il est venu.       Elle a lu le livre quand il est venu.
es  Ella sabe que él vino.          Ella leyó el libro cuando él vino.
it  Lei sa che lui è venuto.        Lei ha letto il libro quando lui è venuto.
ja  彼女は彼が来たということを知ります。  彼女は彼が来たときに、本を読みました。
```

### Tre språk gör något annat än att lägga till en subjunktion

**Tyskan flyttar det finita verbet sist.** "dass er das Buch gelesen **hat**"
— satsklammern vänds ut och in: i huvudsats står det finita på plats två och
de infinita sist, i bisats står allihop sist med det finita allra sist.
Uppdelningen i finit och infinit fanns redan för satsklammerns skull, så
bisatsen kostade en rad. Perfekt passiv i bisats blir "dass das Buch gelesen
worden ist", med alla tre verbdelarna i rätt ordning.

**Svenskan flyttar satsadverbialet före verbet.** BIFF-regeln: "att han
**inte** kom" mot huvudsatsens "han kom **inte**".

**Japanskan byter form, inte bara ordning.** En bisats står alltid i ENKEL
form, hur artig huvudsatsen än är: 彼が来た**と**言いました, aldrig 来ました.
Subjektet tar dessutom が i stället för は — は markerar satsens tema, och en
bisats har inget eget tema. Och subjunktionen står SIST, som postpositionerna.

### Det som var fel i förra överlämningen

De japanska enkla formerna (jisho, ta, nai) stod bokförda som **"register,
utanför scope"**. Det var fel. Plain mot polite är register i huvudsats men
**grammatik i bisats** — en bisats KAN inte stå i artig form. De cellerna
var alltså inte utanför scope utan bara onåbara, och bisatsen låste upp
343 av dem: japanskan gick 45 % → **58 %**.

Det är också det enda språk som vinner något. De sex andra vinner **noll
former** — en bisats använder samma celler som en huvudsats, bara i annan
ordning. En mätning som räknar former hade aldrig visat skillnaden mellan
"tyskan kastade om orden" och "japanskan bytte paradigm".

### Två fel som bisatsen drog fram

**Validatorn kraschade på varje prepositionsfras-adverbial**, och hade gjort
det sedan nivå 15. `tempuskrav()` slog upp adverbialet i databasen utan att
kontrollera att det var en sträng, så en `Prepositionsfras` gav
`ProgrammingError: type 'Prepositionsfras' is not supported`. Ingen hade
validerat en mening som hade en. Bara adverb har tempuskrav; fraser och
bisatser hoppas nu över, och bisatsen valideras rekursivt som den mening
den är.

**Franskans que elideras inte automatiskt.** "parce que il vient" i stället
för "parce qu'il vient". Regeln gäller ORDET que, inte ändelsen -que — "la
bibliothèque a" ska inte elideras — så villkoret är `que` eller `... que`
med mellanslag. Alla franska sammansatta subjunktioner är flerordiga, vilket
gör den avgränsningen exakt.

Konjunktivstyrande subjunktioner vägrades först, och byggdes sedan — se
nästa avsnitt.

---

## Artikellös nominalfras — och tyskan i mål

`Bestämdhet` hade OBESTÄMD och BESTÄMD. Det räckte i tjugoen nivåer, men
bara därför att meningarna alltid handlade om räknebara exemplar. Två värden
till, och de skiljer sig åt på ett sätt fyra av sju språk inte visar men tre
gör:

- **GENERISK** — frasen namnger en SORT: "böcker är dyra", "vin är gott".
- **PARTITIV** — frasen namnger en obestämd MÄNGD: "jag dricker vatten".

```
              GENERISK                   PARTITIV
sv/en/de/ja   naken fras                 naken fras
fr            les livres sont chers      elle boit de l'eau
es            los libros son caros       ella bebe agua
it            i libri sono cari          lei beve dell'acqua
```

**Partitiven kostade ingen ny data.** Den är prepositionen de/di plus den
bestämda artikeln, och sammandragningen du/della sköts av sandhi — exakt
samma mekanism som genitivet redan använder. Spanskan står naken i
mängdbetydelse och behöver inte ens det.

**Tyskan gick 61 → 82 %.** Den starka deklinationen bor precis här: utan
determinerare måste adjektivet självt bära kasus, genus och numerus —
*roter Wein*, *kaltes Wasser* — och det är därför den starka böjningen ser
ut som den bestämda artikeln. Tillsammans med attributiv komparation tog de
två utökningarna tyskan från 36 till 82 %, båda om nominalfrasens inre.

### Naken singular kräver ett oräknebart ord

"Hon läser bok" finns inte. Plural är fri — "böcker är dyra" är den
generiska frasen för räknebara ord — men singular kräver att huvudordet
namnger ett ämne. `Koncept.räknebar` fylldes vid koncepttaggningen och hade
aldrig lästs av någon konstruktion; kontrollen ligger i `Uppslag` så att
alla sju delar den.

**Och taggningen visade sig inkonsekvent.** te, vin och öl stod som
räknebara medan juice, kaffe och mjölk stod som oräknebara — samma sorts
dryck, två olika svar. Kriteriet som gäller för de senare är att ordet
namnger ett ämne som mäts i mängd, och det gäller alla sex. De tre är
rättade, med motivering i `koncepttaggning.sql`. Kvar som inkonsekvens: ost,
soppa och bröd, som har en levande räkneläsning ("ett bröd") och därför
lämnas — men gränsen är inte skarp.

### Två elisioner till

**Italienskans sammandragna prepositionsartiklar elideras**: *dell'acqua*,
inte *della acqua*. Bristen fanns sedan genitivet byggdes men syntes aldrig,
eftersom ingen ägare i svepen började på vokal. Listan räknas upp i stället
för att härledas ur ändelsen -la, annars skulle "la scuola è aperta" bli
"la scuol'è".

**Spanskans *el agua* är INTE byggd.** Feminina ord som börjar på betonat
/a/ tar `el` i singular — *el agua*, *el águila* — trots att de är
feminina. Renderaren ger *la agua*. Felet är pre-existerande (det syns med
BESTÄMD också) och kräver en flagga på lexemet, i stil med `prenominal`,
eftersom betoningen inte syns i stavningen.

---

## Attributiv komparation — den största enskilda utökningen

`Nominalfras.attribut` tog bara konceptnycklar. Graden fanns på `Mening` och
styrde PREDIKATIVET ("boken är störst"), men attributet sitter inuti en
nominalfras och kan ha en annan grad än predikativet i samma mening. Nu:

```python
attribut: tuple[str | Attribut, ...]     # Attribut(koncept, grad)
```

Naken sträng betyder positiv grad — samma billiga normalfall som `adverbial`
har med sina strängar. **Tyskan gick 36 → 61 %**, 5 886 former, mer än någon
annan utökning i projektet gett något språk.

Skälet att den var så stor: tyskans adjektivparadigm har 49 celler per grad
med IDENTISK struktur, så `pos_stark_m_nom` blir `komp_stark_m_nom` blir
`superl_stark_m_nom`. Två tredjedelar av 147 celler låg onådda bakom ett
saknat fält, och det räckte med att byta prefix för att nå dem.

```
sv  den största boken        de  das größte Buch     dem größten Bruder
en  the biggest book         fr  le livre le plus intéressant
es  el libro más interesante it  il libro più interessante
ja  一番面白い本
```

### Tre saker som inte är samma i de sju

**Perifrastisk reserv.** sv/en/es/it har suppletiva former för ett fåtal ord
och bygger resten med mer/more/más/più — datan avgör, precis som för
predikativet. Franskan är nästan alltid perifrastisk (12 av 444 celler
fyllda), tyskan aldrig (5 341 av 5 439).

**Komparationen kan FLYTTA adjektivet.** es/it ställer det komparerade efter
huvudordet oavsett var positiven står: *un libro mayor*, aldrig *un mayor
libro*. Franskan behåller placeringen — *le plus grand livre* — och markerar
i stället superlativen med **dubblerad artikel** när adjektivet står efter:
*le livre le plus intéressant*. Utan den vore komparativ och superlativ
omöjliga att skilja åt, eftersom *plus* är samma ord i båda.

**Attributiv superlativ kräver en bestämd fras** i sex av sju språk. "En
störst bok", "a biggest book", "un libro más interesante" som superlativ —
ingen av dem finns. Superlativen pekar ut ett unikt exemplar. Possessiv och
genitivägare räknas som bestämda: *mitt största problem*, *mein größtes
Problem*. Renderarna vägrar den obestämda i sv/en/de/fr/es/it; japanskan
släpper igenom den, eftersom 一番 markerar graden utan att bry sig om
bestämdhet — som japanskan inte har.

### En pre-existerande brist som syntes på vägen

**Italienska possessiver saknar sin artikel.** *"suo libro"* ska vara *"il
suo libro"* — italienskan sätter bestämd artikel före possessiven, utom vid
oböjda släktskapsord i singular (*mia madre*). Felet finns i positiv grad
också och är alltså inte nytt, men det syns tydligare nu när frasen blir
längre.

---

## Modusrektionen — schemaändringen

**`MönsterKrav.tempus`** bär det modus en bisats måste stå i. 1024 (Vol i
`_legend.yaml`) betyder konjunktiv; NULL betyder indikativ. Kolumnen är ny i
`setup.sql`, och `ordbok/migrationer/modusrektion.sql` fyller den.

Mekanismen är **exakt kasusrektionens**: ett `Mönster` med `språk` satt, på
det STYRANDE ordets koncept. fr *avant que* styr konjunktiv medan *après
que* inte gör det, precis som de *mit* styr dativ medan *für* styr
ackusativ. Det är en lexikal egenskap hos varje enskilt ord, per språk — och
därför data, inte en lista i renderaren.

Rektionen sitter på **två ordklasser**:

- **subjunktioner** — slotten heter `komplement`, satsen de tar. 11 rader.
- **verb** — slotten är den verbet redan har sin Bisatsfras på (objekt,
  kommunikat eller komplement), så migrationen slår upp den ur det
  universella mönstret. 7 rader.

```
                       fr              es              it
subj_innan             venga  ✓        venga  ✓        venga  ✓
subj_för_att           vienne ✓        venga  ✓        venga  ✓
subj_trots_att         vienne ✓        viene  —        venga  ✓
subj_ifall             —               venga  ✓        venga  ✓
subj_tills             vienne ✓        —               —
gen_önska    (vilja)   vienne ✓        venga  ✓        venga  ✓
käns_hoppas  (hoppas)  vient  —        venga  ✓        venga  ✓
kog_tro      (tro)     vient  —        viene  —        venga  ✓
```

**Att `käns_hoppas` skiljer sig i två av tre språk är hela argumentet för
att det ligger i datan.** Samma koncept, samma sats, olika modus: franskans
*espérer que* tar indikativ, spanskans *esperar que* och italienskans
*sperare che* konjunktiv. Ingen regel härleder det — bara ordet vet.

Tidsföljden avgörs av **bisatsens eget tempus**: presens konjunktiv för
icke-förfluten sats, imperfekt för förfluten. Franskan har ingen levande
imperfektkonjunktiv (*qu'il vînt* är litterärt som passé simple) och tar
alltid presens — och det avgörs av att paradigmet SAKNAR cellerna, inte av
en regel. Perfekt fungerar av sig självt: hjälpverbet byter modus och
participet står kvar. *"qu'il ait lu"*, *"que haya leído"*, *"che abbia
letto"*.

### Fem subjunktioner är medvetet otaggade

De styr konjunktiv bara under villkor specen inte uttrycker, och lämnas i
indikativ hellre än att gissa. Motiveringarna står i migrationens filhuvud:

| | varför inte |
|---|---|
| es *aunque* | tar båda, och valet ÄNDRAR betydelsen: *aunque llueve* (fastän det regnar, faktum) mot *aunque llueva* (även om det skulle regna). Konceptet heter `subj_trots_att` och namnger den faktiska läsningen. |
| es *hasta que* | konjunktiv om satsen syftar framåt, indikativ om ett inträffat faktum |
| es *cuando* | samma villkor: *cuando venga* men *cuando vino* |
| it *finché* | indikativ i normalt bruk; konjunktiven är litterär |
| fr *au cas où* | styr KONDITIONALIS — ett tredje modus som varken specen eller kolumnen uttrycker än |

De två spanska villkoren går att härleda ur bisatsens tempus, som specen
faktiskt bär. Det kräver en andra kolumn eller en regel och är inte byggt.

### Ett datahål och en mätartefakt

**Spanskans `haber` saknade hela konjunktiven.** Lexemet genererades som ett
rent hjälpverb med 27 av 53 celler, och perfekt konjunktiv gick därför inte
att bygga. 12 former tillagda (haya…hayan, hubiera…hubieran).

**Och mätningen låg för lågt av samma skäl som två gånger förut.** Med
bisatsens subjekt låst till tredje person singular nåddes bara 2 av 12
konjunktivceller, och siffrorna stannade på fr 64 %, es 59 %, it 60 %. Med
personvariation i bisatsen: **fr 73 %, es 67 %, it 77 %**. Italienskan gick
från näst sämst till näst bäst av de sju språken.

Tredje gången personvariation visar sig vara det som begränsar mätningen —
först huvudsatsens subjekt, sedan attributets slot, nu bisatsens subjekt.
Modulhuvudet i `nåbarhet.py` varnar för det, men varningen räcker uppenbart
inte: **lägg till dimensionen och mät om, varje gång en siffra ser låg ut.**

---

## Wh-frågorna — nivå 21, och stegen är slut

`Mening.fråga_om` säger vad frågan gäller. Två sorters värden, och
skillnaden är grammatisk:

- **`"subjekt"` / `"objekt"` / `"io"`** — ett argument efterfrågas. Slotten
  står kvar i specen **med svaret i sig**: "vem läser boken?" byggs ur
  "flickan läser boken", och renderaren byter ut ordet mot vem eller vad.
  Vilketdera avgörs på MÄNSKLIG-biten hos det efterfrågade — samma
  semantikbit restriktionerna redan använder, så frågeordet behövde ingen
  egen taggning.
- **`"frågadverb_tid"` m.fl.** — en omständighet efterfrågas. Inget
  argument tas bort; adverbet läggs till.

Att svaret ligger kvar i specen är inte en tillfällighet: en fråga och dess
svar är samma mening, och en inlärningsapp behöver båda. Restriktionerna
prövar därför frågan mot svaret utan att veta att det är en fråga.

```
             subjekt              objekt                     io
sv   Vem gav brodern boken?   Vad gav flickan brodern?   Vem gav flickan boken?
en   Who gave the brother…?   What did the girl give…?   Whom did the girl give…?
de   Wer gab dem Bruder…?     Was gab das Mädchen…?      Wem gab das Mädchen…?
fr   Qui a donné le livre…?   Qu'est-ce que la fille…?   À qui est-ce que…?
es   ¿Quién le dio el libro…? ¿Qué le dio la chica…?     ¿A quién le dio…?
it   Chi ha dato il libro…?   Cosa ha dato la ragazza…?  A chi ha dato…?
ja   誰が兄弟に本をあげましたか。 女の子は兄弟に何をあげましたか。 女の子は誰に本を…
```

### Två regler räckte till sex språk

**Subjektsfrågan inverterar inte.** Frågeordet står redan på subjektets
plats, så "vem läser boken?" har rak ordföljd medan "vad läser hon?" har
omvänd. Det gäller alla sex, och det är skälet till att engelskan säger
"Who reads the book?" och inte "Who does read the book?" — do-omskrivningen
finns bara för att något ska kunna flytta förbi subjektet, och här flyttar
ingenting.

**Tyskan behövde ingen regel alls.** Frågeordet tar Vorfeld och V2 gör
resten: subjektsfrågan blir rak ordföljd och objektsfrågan omvänd, av sig
självt. Kasus på frågeordet — wer/wen/wem — läses ur verbets rektion, samma
väg som för nominalfraser: "wem gibt sie das Buch" har dativ därför att
geben styr dativ på io.

**Japanskan flyttar ingenting.** 何 står kvar där objektet stod, med sin
partikel kvar. Det är den enskilt största syntaktiska skillnaden mot de sex
andra. Ett efterfrågat subjekt tar dessutom alltid が — 誰は finns inte,
eftersom det okända inte kan vara tema.

### Frågedeterminanterna

`Nominalfras.frågedeterminant` för "vilken bok": här står huvudordet kvar
och det är valet mellan exemplar som efterfrågas. Determinanten tar
artikelns plats precis som en possessiv, och styr adjektivet likadant —
tyskans `welcher` böjs som den bestämda artikeln och ger svag deklination.

```
sv  Vilken bok läste flickan?      de  Welchem Bruder gab das Mädchen das Buch?
en  Which book did the girl read?  fr  Quelle fille lit le livre?
```

### Det datan bar på

Jakten på snedstreck i formerna — `que/quoi` i franskans frågepronomen —
drog fram att **224 franska verbformer har subjektspronomenet inbakat**:
"je travaille", "j'écoute", "il/elle travailla". Sju lexem, sex av dem
vokalinledda.

Skälet visade sig vara **renderaren**: franskans elision fanns bara för
le/la/ne/que. "J'écoute" gick inte att bygga, så någon skrev in pronomenet
i formen. Med `je` och de andra klitika i elisionslistan bygger renderaren
det själv, och formerna kunde städas.

Det är tredje gången samma mönster dyker upp — tyska substantiv med artikeln
inbakad, tyska imperativer med pronomenet inbakat, franska verb med
pronomenet inbakat. Alla tre är *rätt böjda, fel avgränsade*, och alla tre
är osynliga för en granskning som frågar "är formen korrekt?".

Två småfel till: `fr/que` obl-cell hade "que/quoi" (två former i en cell,
nu "que" — quoi är den toniska varianten), och `es/vosotros` hade
"vosotros/vosotras". Femininum kräver ett eget lexem som `nosotras` har;
det saknas fortfarande och 2pl femininum vägrar därför i spanskan, precis
som förut.

### Vad wh-frågorna INTE låste upp

8–23 former per språk — frågeorden själva, inget mer. Det är den minsta
formvinsten av alla elva utökningar, och samtidigt den konstruktion en
nybörjare möter tidigast. "Antal former" duger inte som mått åt något håll.

---

## Kurserna och upplåsningen i gränssnittet

*Byggt 2026-08-15.* Programmet startar i den kurs som användes sist
(`Kurs.senast_öppnad`), och kursnamnet i huvudet är knappen som byter.

**Att skapa en kurs** är att välja käll- och målspråk. Alla 42 par erbjuds,
men italienskan bär en mätt varning: den misslyckas på 32 % av alla meningar,
nästan alla på obestämd artikel i plural som språket inte har. Varningen
försvinner när partitiven är löst.

**Upplåsningen är två klick, inte ett.** Systemet säger bara att det FINNS
plats (kapacitetsmodellen); användaren klickar "See the next step", läser
lektionen, och klickar sedan "Add this step to my course". Lektionen kommer
alltså FÖRE korten, vilket var Julius val, och nivån ändras när han aktiverar
den — inte när han läser om den.

**Nollställning är den enda oåterkalleliga knappen** och kräver ordet RESET
skrivet, inte ett klick. Allt annat går att bygga om ur `former.tsv`;
repetitionshistoriken gör det inte. Korten TAS BORT och byggs om i stället för
att bara nollställas — en kurs som stod på nivå 21 har kort som inte går att
möta på nivå 1, och att lämna dem vore att återskapa de spökkort nivåspärren
finns för. Det är tryggt just här: all historik är redan raderad.

Två fel som föll ut vid provningen: `hämta` kastade på statuskoden och svalde
därmed serverns eget felmeddelande, så en felstavad bekräftelse gav ingen
återkoppling alls; och nollställningen lämnade 1 112 kort kvar på nivå 1 där
864 hör hemma.

`ordbok webb --db X` kör mot en annan inlärardatabas. Det finns för att kunna
prova kursskapande och nollställning utan att röra den riktiga — och en kopia
måste tas med SQLites backup-API, inte med `cp`: en WAL-databas är inte en
enda fil, och en `cp` mitt i gav "database disk image is malformed".

---

## Lektionsvyn — och fem döda steg den avslöjade

*Byggt 2026-08-15.* Tre delar med helt olika kostnad, vilket är hela skälet
till formen: **prosan** skrivs (21 texter, inte 21 × 7 — konstruktionen är
språkoberoende och bara realiseringen skiljer), **exemplen** genereras av
generatorn på rätt nivå med användarens egna ord, och vad steget låser upp
**mäts** genom att befolka på N och N−1 och ta skillnaden.

Exemplen prövas mot ett villkor per konstruktion. Utan det visar lektionen om
passiv en mening i aktiv form, eftersom samplaren bara bygger konstruktionen
ibland.

**Fem steg införde noll nya kort**, och mätningen av vad samplaren faktiskt
bygger sa varför: possessiv, adverbial, genitiv, prepositionsfras och bisats
byggdes ALDRIG. Konstruktionerna finns i alla sju renderarna, är validerade,
står i stegen och renderas rätt i regressionsnätet — `_nf()` satte bara
bestämdhet, numerus, attribut och komparation, och `kandidat()` satte elva
konstruktioner men aldrig adverbial eller bisats.

Nåbarhetsmätningen kunde inte se det: den mäter vad samplaren NÅR, inte vad
specen KAN UTTRYCKA. Efter rättelsen tillkom 774 kort som aldrig gick att nå.

Två fel som föll ut under bygget och rättades: argumentbisatser tog vilken
subjunktion som helst ("hat gemeint, ALS ihre Maus öffnete"), och satsen stod
BREDVID objektet i stället för att vara det ("wissen einen Typ, dass …").
Satsen ÄR objektet — utom för verb med egen kommunikatslot, där båda är rätt.

---

## Ordboksvyn: paradigmet med kunskapen i sig

*Byggt 2026-08-15.* Svarar mot det Julius sa om kortövning: "när det är flera
liknande kort fastnar jag på de i evigheter … sedan tar jag en stund att kolla
på de utanför och faktiskt lära mig och få en överblick."

**LAYOUTEN HÄRLEDS UR AXLARNA, INTE UR ORDKLASSEN.** Varje cell i slot-filen
bär sina koordinater. Kongruensaxlarna — kasus, person, numerus, genus — blir
tabellens rader och kolumner; de kategoriala — grad, species, tempus, diates —
delar upp i flera tabeller. Skillnaden är grammatisk: kongruens är vad ordet
rättar sig EFTER något annat, det kategoriala är en egenskap hos formen själv.
Varje grammatikbok gör samma uppdelning.

Två axlar slås ihop när den enas DEFINIERADHET är en funktion av den andras
värde. Tyskans genus är satt i singular och osatt i plural, alltså m/f/n/pl som
fyra kolumner — inte 3 × 2. Utan hopslagningen blev tyska adjektiv 39 tabeller;
med den blir de tolv, vilket är hur boken skriver dem.

Ingen rad kod känner till vilket språk den ritar. Verifierat på de/sv/fr/es/ja.

```
[Pos · Strong]      Sg Masc.   Sg Fem.   Sg Neut.        Pl
        Nom           netter     nette      nettes     nette
        Ack           netten     nette      nettes     nette
        Dat           nettem    netter      nettem    netten
        Gen           netten    netter      netten    netter
```

**STYRKAN PER CELL ÄR DET SVAGASTE KORTET, OCH ETT OMÖTT KORT ÄR SVAGAST.**
Första versionen tog minimum över de MÖTTA korten, vilket lät en cell se stark
ut fastän en av dess delar aldrig prövats. Rättat, och då blir vyn sann:

```
spricht    stam sprich ✓  +  ändelse t  ✓     stark
sprichst   stam sprich ✓  +  ändelse st ✗     delvis
sprecht    stam sprech ✗  +  ändelse t  ✓     delvis
spreche    stam sprech ✗  +  ändelse e  ✗     omött
```

DELVIS är ett eget läge och inte en nyans: "du kan stammen men inte ändelsen"
är något annat att göra än "du kan ingenting här". Det är precis den skillnaden
kortmodellen finns för att kunna se, och ordboken är där den blir synlig.

**Genusetiketterna är språkberoende.** Legendens namn är språkoberoende bitar
med språkberoende betydelse — genus=3 heter "Alla" och är tyskans NEUTRUM. Att
visa dem råa vore vilseledande, så namnen är avlästa ur datan per språk
(de 1/2/3 = netter/nette/nettes, sv = snäll/snällt/snälla, fr = gentil/gentille).

---

## Hemvyn, passet och passkön

*Byggt 2026-08-15.*

**Passet slutar när det förfallna och passkön är tomma.** Nya kort hindrar
inte slutet — de möts INUTI meningar, inte som en egen kö, och det är den
viktigaste skillnaden mot Anki i gränssnittet.

**Passkön löser ett fel designen inte visste om.** `schemalaggning.py` påstod
att ett fallerat kort "dyker upp igen inom några meningar". Det gjorde det
inte: FSRS minsta intervall är ett dygn, så kortet schemaläggs i morgon och
kan inte komma tillbaka i dagens kö hur den än sorteras. Kön ligger nu i
generatorn, är per pass, lever i minnet och rör inte schemaläggningen —
återförsöket blir en tidig repetition med den mindre stabilitetsökning FSRS
ger sådana. Ett kort som gått fel och sedan rätt i samma pass är avklarat.

**Längden behöver inte tvingas fram.** Mätt, tyska:

```
nivå 4, ny         median 2 ord    spann 2–3
nivå 4, 120 dagar  median 4        spann 3–6
nivå 9, 120 dagar  median 8        spann 6–10
nivå 21, 120 dagar median 7        spann 5–11
```

Två oberoende effekter, båda följder och inte parametrar. Budgeten kopplar
längd till KUNSKAP: ett svagt kort (R=0,5) fyller Σ(1−R)=1,5 på tre kort,
starka kort (R=0,95) behöver trettio. Stegen kopplar längd till NIVÅ, men
bara upp till en punkt — efter nivå 9 planar medianen ut och det är spannet
som vidgas. Högre nivåer ger alltså variation i KONSTRUKTION, inte i längd.

Det enda som rör längden direkt är vikten `längd = -0,15`, som trycker
kortare för att felet ska gå att lokalisera. Ogissad i övrigt, och mätbar.

**Passets längd i jämvikt**, tyska, allt inlärt och moget i ett halvår:

```
nivå 4, A1    1112 kort     7 rep/dag     4 meningar
nivå 21, B2   3057 kort    18 rep/dag    11 meningar
```

Det finns inget enda jämviktstal: samma kurs gav 80 rep/dag efter 40 dagar och
7 efter 180. Belastningen faller medan man håller på, och passet krymper av
sig självt.

**En mening retirerar 1,7 förfallna kort.** Sökningen TÄCKER 3 och planar ut
där även vid 6 400 kandidater, men en ren slumpsvep hittade en mening med 5 —
packningen begränsas av poängfunktionen och inte av språket. Täckning per
mening ÄR passets längd, så det är den vikt som betyder mest för upplevelsen.

---

## Tre parallella rättelser, landade 2026-08-15

Tre sessioner arbetade samtidigt i egna worktrees. Ingen av dem committade;
allt låg ocommitterat och main var orörd. Regressionsnätet granskade var och en
med `--src` innan de landades.

**Tyskans verbalkomplex.** Ren infinitiv bildar ett koherent komplex med det
styrande verbet, och där står den styrande formen SIST — omvänt mot satsen i
övrigt. Därav Ersatzinfinitiv (`hat arbeiten können`, aldrig `hat gekonnt`) och
Oberfeld (`dass wir haben arbeiten können` — det enda stället i tyskan där
bisatsens finita verb inte står sist).

**Zu-frasen i bisats.** En zu-infinitiv är ingen del av verbalkomplexet utan en
egen fras: sist i huvudsats, före verbkedjan i bisats. Den gamla ordningen
delade klustret mitt itu.

De två gick INTE att kombinera mekaniskt — båda redigerade samma if/else i
`satsled()`. De var däremot komplementära, den ena i grenen `markör is None`
och den andra i `markör is not None`. Sammansatta för hand, verifierade mot
nätet: exakt 5 + 1 = 6 rader, ingenting annat i något av de sju språken.

**Inf-cellen.** Nio svenska verb hade sin IMPERATIV i inf-cellen, och futurum
renderas därifrån: "han ska försök att erbjuda". Felet var osynligt i raden —
inf och imp hade kollapsat till en rad med tempus=17, vilket är RÄTT för alla
-ar-verb. Först jämförelsen mot LEMMAT skiljer den riktiga kollapsen från den
felaktiga, och det är den kontrollen `--endast-struktur` nu gör utan modell.

### Kort.db städad, inte ombyggd

262 kort fanns kvar från en befolkning gjord före nivåspärren. Ombyggnad var
planen tills kontrollen före raderingen visade **10 repetitioner och 2 meningar
från verklig användning**. Spökkorten togs bort ett för ett i stället, efter en
spärr som vägrar om något av dem har historik (noll hade det). 1 374 → 1 112,
historiken orörd.

Regeln som gällde: titta på målet innan du raderar. Den var värd något här.

### Iakttagelse från första körningen

"Han springer" kom tre gånger på fem meningar. Upprepningstermen straffar bara
det som stod i FÖREGÅENDE mening, och vid kallstart med kort kö vinner samma
mål om och om igen. Det är en viktfråga och den ska mätas, inte gissas — men
den är noterad.

---

## Två skyddsnät, och varför de behövdes

*Byggt 2026-08-15, när flera renderarändringar pågick samtidigt.*

**`renderarbild.py` — 57 konstruktioner × 7 språk, fryst i en fil.** Det fanns
`ögonblicksbild.py` för datalagret och `rendera_prov.py` som skriver ut
meningar för en människa att läsa ("inte något som kan verifieras
automatiskt", dess egna ord). Mellan dem fanns ett hål precis där renderarna
bor.

Filen säger vad systemet GÖR, inte vad som är rätt. Kända fel står i den —
en rättelse SKA ge en diff, och diffen ska läsas: den visar vad som ändrades
UTÖVER det man tänkte ändra. `--src X` jämför ett annat träds renderare mot
bilden, vilket är hur en gren granskas utan att checkas ut.

Nätet provades genom att ändra ett tecken i franskans negation; det fångade
alla fyra elisionsställen. Men den första korpusen missade helt de
konstruktioner tre pågående rättelser gällde — **ett regressionsnät är bara
så bra som sin korpus**, och den ska växa när man upptäcker var den är tunn.

**`synk.py` — säger `sprak.db` och `former.tsv` samma sak?** Filen är
sanningen och databasen ska kunna byggas om ur den. Men rättelser landar i
DATABASEN, och exporten tillbaka är ett eget steg som går att glömma. Glöms
den lever rättelsen bara i en fil git inte ser.

Det HADE hänt: nio svenska verb hade fått imperativen åtskild från infinitiven
i databasen (`äg` tempus=16, `äga` tempus=1) medan filen hade en enda rad som
påstod sig vara båda (`äg` tempus=17). Arton rader bara i databasen, nio bara
i filen, i veckor, utan att något sa ifrån.

---

## Appen: uppgiften, servern och sidan

*Byggt 2026-08-15.*

**Uppgiften saknades helt.** `Kurs.källspråk` loggades men renderades aldrig —
generatorn hade en enda renderare, så `ordbok öva` utan `--facit` visade
ingenting alls. Det var inte en lucka i gränssnittet utan i modellen: uppgiften
ÄR samma spec renderad till källspråket, vilket är hela skälet att `Mening` är
språkoberoende. Frågan och svaret är inte två texter som råkar höra ihop.

```
sv  Ni har gått.          sv  En flygplats ska böra höra.
de  Ihr seid gegangen.    de  Ein Flughafen wird sollen hören.   ← fel ordföljd
```

Källspråket renderas först för den kandidat som vinner, inte för alla tusen.
En mening som inte går att STÄLLA förkastas, men det händer sällan nog att en
förhandskontroll inte lönar sig. Kostnad: 202 ms per mening.

**Servern** (`sprakprog/webb/`) är standardbiblioteket, utan beroenden. En
användare på localhost och fyra rutter — och slutmålet är en Tauri-app där
Python följer med som sidecar, där varje paket som ska buntas är arbete.
Anslutningarna delas mellan trådar och serialiseras av ett lås.

**Sidan är webb hela vägen.** Tauri är ett skal av Rust runt systemets webbvy,
så innehållet ÄR en webbfrontend: att bygga sidan nu är att bygga Tauri-appens
frontend, inte en prototyp som ska kastas. Det som tillkommer vid inramningen
är paketeringen av Python-körtiden, och den rör ingenting i sidan.

```bash
ordbok kurs --ny sv de --nivå 4 --cefr A1
ordbok webb          # http://127.0.0.1:8765
```

Rättningen visar vad kortmodellen är till för:

```
Han frågar.  →  skrev "Er fragen."
✗ Fel        Er fragt.
   fragen → fragt   rätt stam 'frag', fel ändelse — pres_1pl i stället för pres_3sg
```

**Känt: `kort.db` har 262 kort för många.** De kommer från en befolkning före
nivåspärren — adjektivens egenskapskort bland annat, och nivå 4 har inga
attributiva adjektiv. De ligger i kön som mål ingen mening kan nå. Ingen
historik finns, så ombyggnad kostar ingenting:
`ordbok kort --återinitiera --språk de` följt av `ordbok kurs --ny sv de`.

---

## Vad som faktiskt går att mäta ur användningen

*Skrivet 2026-08-15, efter en fråga om vilka tal som egentligen är mätbara.*

Nollmodellen är `Mening.förväntat` — FSRS egen förutsägelse av hur många ord
som blir fel, summerad över meningens SEDDA kort. Skillnaden mot utfallet är
det enda måttet som skiljer **"meningen var för svår"** från **"korten i den
var svaga"**, eftersom kortens svaghet är precis vad förutsägelsen räknar bort.

```
överskott = faktiska fel − förväntade fel
```

**Instrumentet är provat på en känd signal.** Med en inbyggd störeffekt över
Σ=1,5 hittar det tröskeln; utan effekt ligger det platt på noll och falsklarmar
i 2 % av körningarna. Styrkan:

| effekt | upptäcks efter |
|---|---|
| 0,24 extra fel/mening | ~200 meningar (tio dagar) |
| 0,12 | ~1 000 meningar (två månader) |
| 0,06 | mer än 2 000 |

**Fyra av åtta vikter har ett falsifierbart prov** — budget, interferens,
koncentration och nykvot förutsäger alla överskottsfel. De övriga fyra har det
inte: täckning och tomgång är effektivitetsmål, upprepning och längd är
variation och felsökbarhet. De ska inte låtsas vara mätningar.

Retentionsmålet 0,90 är **lånat** från FSRS, inte valt av oss. Ett försök att
härleda det ur kapacitetsmodellen gav optimum vid 0,70, monotont fallande —
inte en upptäckt utan ett tecken på att objektivet "kort × retention" är fel:
det straffar inte att ett glömt kort blir ett fel mitt i en mening.

---

## Upplåsningen: nivån avgör vilka kort som FINNS

*Byggt 2026-08-14.* Mätningen som avgjorde formen: en tysk nybörjare har
2 119 kort på A1, men på nivå 4 går bara **643 av dem att möta**. De övriga
1 476 skulle ligga i kön, väljas som mål, och aldrig kunna nås.

```
nivå 4    643 av 2119    30 %
nivå 9    813            38 %
nivå 14   938            44 %
nivå 21   984            46 %
```

Därav principen: **ett kort ska inte finnas förrän det går att möta.** Det
är samma regel som redan gällde för former specen inte når, med en gräns som
flyttar sig. Nivån är alltså inte ett lager ovanpå kortlagret utan det som
avgör vilka kort som existerar.

`befolka(..., nivå=N, cefr=X)` skapar bara nåbara kort, och nåbarheten MÄTS
— samplaren bygger meningar på nivån och instrumenteringen säger vilka
former som slogs upp. Bakvägen från cell till specparametrar finns inte och
behövs inte.

```
nivå  4 A1   1 112 kort        nivå 21 A1   1 601
nivå  9 A1   1 360             nivå 21 A2   2 987
nivå 14 A1   1 517             allt         4 821
```

Att öppna en nivå ÄR att köra befolkningen igen. Den är additiv och
idempotent, så historiken överlever — och det är precis vad som ska hända:
gamla ord får nya former att lära sig.

**Tröskeln** är en KAPACITETSFRÅGA och inte en behärskningsfråga. Att mäta om
användaren "kan" nivån vore att implementera om FSRS garanti: håller man
repetitionerna minns man per konstruktion 90 % av sina kort, hela tiden. Det
som däremot är en verklig gräns är arbetsmängden.

| storhet | varifrån |
|---|---|
| belastning, Σ 1/intervall | FSRS egna intervall |
| kort per mening | mätt ur användarens egen logg |
| meningar per dag | **användarens val**, i `Kurs` bredvid `budget` |

Ett enda valt tal, och det är en uppgift om användarens dygn. Hela cykeln,
körd på tysk A1 med kapaciteten satt till 20 meningar om dagen:

```
sedda kort   rep/dag   meningar/dag           nivå 9 (+262 kort)
       100     556,0           91,6              113,2  ✗ för dyrt
       400     178,7           29,5               36,4  ✗
       700     112,3           18,5  ✓ plats      22,9  ✗
     1 000      85,7           14,1  ✓ plats      17,5  ✓ RYMS
     1 112      80,8           13,3  ✓ plats      16,5  ✓
```

`ordbok kort --läge [--kostnad NIVÅ]` visar det, och kostnadsfrågan ställs i
en kopia — att fråga vad något kostar får inte vara att köpa det.

**Två mått förkastades, båda mätta först.** "Generatorn kan inte längre bygga
en tillräckligt svår mening" gav 1,18 halvlärt mot 1,02 helt lärt — ingen
spännvidd, och principiellt fel eftersom R faller med tiden sedan
repetitionen: måttet säger "slut" på kvällen och "inte slut" efter en veckas
uppehåll. Och att räkna osedda kort med stabiliteten efter första rätta
svaret beskrev en topp som aldrig inträffar. Vad ett kort kostar när det
sitter mäts i stället på just den användaren, ur hens egna sedda kort.

Kursen svarar hellre **"oövad"** än gissar. Utan historik finns ingen mätning,
och utan mätning inget svar — men heller ingen förlust, för man kan inte lämna
en nivå man inte börjat på.

---

## Nivåerna: två oberoende tak

*Infört 2026-08-14.* `Koncept.nivå` bär CEFR-nivån — 393 A1, 328 A2, 15 B1.
Kolumnen fanns i `ordbok/nivålistor/*.csv` från början men lästes aldrig in;
läsaren kastade den med kommentaren att den "inte längre är del av schemat".
Det beslutet fattades innan generatorn fanns.

**Nivån är en egenskap hos KONCEPTET, inte hos lexemet** — noll av 736
koncept har olika nivå i olika språk, vilket är väntat: nivån säger hur
grundläggande begreppet är, inte hur svårt ordet är. Importen kontrollerar
det påståendet vid varje körning i stället för att anta det.

Och de två taken är **ortogonala**:

```
ordbok öva sv --cefr A1 --nivå 4     Han spelar dig.  Ni arbetar.
ordbok öva de --cefr A1 --nivå 11    Er fragt euch.   Du danktest ihr.
ordbok öva de --cefr C2 --nivå 21    Wer vergab einem Mann?
```

Att blanda ihop dem vore att påstå att den som lärt sig bisatser också kan
alla ord.

---

## Tre språkfel, lagade 2026-08-14

Alla tre satt i kod som varit "klar" i flera pass, och alla tre hittades av
att systemet kördes på riktigt.

**Tyska partikelverb särar partikeln i finita former** och skriver ihop den i
infinitiv och particip. Datan lagrar formen som den ser ut — "ruft an" — men
partikeln hör hemma i satsklammern:

```
Das Mädchen ruft den Bruder an.          huvudsats: partikeln sist
Das Mädchen ruft den Bruder nicht an.    efter satsadverbialet
Das Mädchen hat den Bruder angerufen.    particip: ihopskriven, orörd
Wen ruft das Mädchen an?                 wh-fråga
dass das Mädchen den Bruder anruft       BISATS: partikeln återförenas
```

Regeln är att ett mellanslag i en finit form betyder partikel. Fjorton verb.
Att den återförenas i bisats följer av att verbet står sist där — ingenting
skiljer dem längre åt.

**Italienska possessiver tar bestämd artikel**: "il suo libro". Undantaget är
omodifierade släktskapsord i singular — "sua madre" — men inte familjen som
helhet ("la sua famiglia"), inte de sammansatta ("il suo fratello maggiore"),
inte plural ("le sue sorelle") och inte `loro` ("la loro madre").

En detalj som är lätt att missa: artikelns allomorf väljs på NÄSTA ord, och
det är possessiven som följer artikeln — "il suo amico", inte "lo suo amico".
Det är *suo* som avgör, inte *amico*.

**Spanskans `el agua`.** Feminina ord vars första stavelse bär betoningen
byter artikel i singular. Betoningen HÄRLEDS ur stavningen i stället för att
listas, för spanskan stavar den regelbundet: skriven accent går först,
annars näst sista stavelsen om ordet slutar på vokal/n/s, sist annars.

```
agua        a-gua, två stavelser på vokal  → el agua
águila      skriven accent på första       → el águila
arena       a-re-na, tre stavelser         → la arena
habitación  accenten ligger sist           → la habitación
```

Bara ett ord i dagens ordförråd berörs. Att ändå härleda är poängen: regeln
gäller också de ord som läggs till sedan.

---

## Kända täckningsgränser

(Inga fel, men bra att veta.)

- Mönster finns bara på verb. Schemat tillåter adjektiv och prepositioner
  som styrande ord (`rädd för`, `intresserad av`) — inte taggat.
- Ett mönster per verb. `äta` har ett transitivt mönster, men "hon äter"
  utan objekt är också korrekt. Additivt att lägga till.
- Japanskan saknar infinitivkomplement (modaliteten är suffixal) och skiljer
  inte perfekt från preteritum (た täcker båda).
- Tyska Wechselpräpositionen defaultar till dativ. Riktning kräver en
  målroll som specen inte har.
- `mappa-kaikki` (validering mot Wiktionary-dumpar) är bara implementerad
  för svenska.
- **Granskningens kvittofil skiljer inte på homonymer — men luckan är
  liten.** `granskning.tsv.klara` har en rad per `(språk, lemma)`. Av 177
  homonymgrupper har 126 identiska paradigm (de/finden = hitta/tycka), så en
  granskning av det ena täcker det andra morfologiskt. Kvar: 51 grupper där
  formerna skiljer sig, de flesta korsordklassiga med bara en form på ena
  sidan (en `back`, en `open`). Verkligt behov i en handfull: de/sein,
  de/sicher, es/poder, de/ihr. Fixen är densamma som `tillämpa-granskning`
  fick: nyckla kvittot på koncept i stället för lemma. **Kräver
  `granska-former`, som inte får köras från Claude Code.**
- **`paradigm/it/frågepronomen.yaml` har två celler med identiska
  koordinater.** `chi` och `cosa` är båda `kasus: [Nom, Ack, Dat]` och inget
  annat. Former lagrar axlar, inte cell-id, så en rad som täcker den ena
  täcker med nödvändighet den andra. Ofarligt för renderaren. Går inte att
  åtgärda i datan, bara i slot-filen. Beslutet att låta det vara står i
  `beslut.tsv`. Det enda sådana fallet i alla slot-filer (kontrollerat).

---

## Vad som återstår

**Slingan går runt.** `ordbok öva <språk>` genererar, tar emot ett svar,
rättar och registrerar. Rättningen ligger i
`src/sprakprog/generator/rattning.py`, och attributionen vilar på samma
stamuppdelning som definierar korten: skiljer sig bara ÄNDELSEN fälls
systemkortet, skiljer sig STAMMEN fälls ordets eget. Verifierat i sv och de
mot fyra felsorter — fel stam, fel ändelse, fel ord, fel tempus — och alla
fyra landar på rätt kort.

Kvar av de tre mekanismerna i GENERATOR.md: "meningen vittnar" (kongruens
över flera ord) och "självrättning som möjlighet" kräver mer kontext
respektive ett gränssnitt. Historikmekanismen finns.

1. **Lektionssidorna.** Upplåsningen fungerar (se avsnittet nedan), men
   ingenting VISAR paradigmtabellen och exempelmeningarna när en nivå
   öppnas. Tabellen går att generera ur systemkorten och exemplen ur
   generatorn — det som återstår att skriva är prosan, och den hör till
   komplexitetsstegens 21 konstruktioner och inte till 21 × 7, eftersom
   konstruktionen är språkoberoende och tabellen visar realiseringen.

2. **Vikterna i `poang.py`.** En första gissning, och det står i
   modulhuvudet. De går bara att hitta genom att köra systemet — men allt
   loggas redan, budget och utfall per mening, så frågan är besvarbar när
   det finns användning att mäta mot.

3. **Appen.** Desktop först, mobil senare. Terminalslingan (`ordbok öva`)
   finns och kan användas för att trimma vikterna innan gränssnittet byggs.

**Komplexitetsstegen är slut** — de 21 nivåerna är byggda i alla sju språk.
Det som återstår är inte fler satstyper utan djup i dem som finns, och
gränssnittet.

---

## Saker en ny session måste veta

**Kör aldrig LLM-kommandon inifrån Claude Code.** `generera`,
`granska-former`, `tagga-*` anropar `claude -p` som subprocess och hänger.
Alla fyra vägrar med ett tydligt besked.

**Migrationer är inte valfria.** `ordbok import --återinitiera` bygger om
databasen från CSV och tappar all taggning. Kör alltid
`for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m"; done`
efteråt, sedan `ordbok importera-former ordbok/former.tsv --ersätt`.

**Schemat ägs av `setup.sql`, migrationerna av datan.** Ingen migration gör
DDL. `MönsterKrav.tempus` tillkom 2026-08-14 och står därför i `setup.sql`;
`modusrektion.sql` fyller bara kolumnen. En databas byggd före den dagen
behöver `ALTER TABLE MönsterKrav ADD COLUMN tempus INTEGER;` en gång.
Migrationerna ska vara idempotenta. `semantik_utökad.sql` var det inte:
den satte bitar som dess egen villkorsjämförelse sedan läste, så andra
körningen gav ett annat resultat än första.

**`ordbok/granskningsrattelser.sql` och `ordbok/artikellackage.sql` är
LOGGAR, inga migrationer.** De ligger utanför `migrationer/` just för att
loopen ovan skulle ha spelat upp dem. Satserna är knutna till `Former.id`,
och DELETE/INSERT flyttar id:n — mot en ombyggd databas träffar de fel
rader. Rättelserna bevaras i stället i `former.tsv`, som exporteras om
direkt efter körningen.

**`sprak.db` ligger i `.gitignore`.** Sanningen är `ordbok/former.tsv` plus
migrationerna. Skicka aldrig databasfilen.

**`kort.db` ligger också i `.gitignore`, men av MOTSATT skäl.** sprak.db går
att bygga om ur repot; inlärardatabasen går inte det. Den innehåller
repetitionshistoriken, det enda i systemet som inte kan återskapas. Radera
den aldrig, och kör `ordbok kort --återinitiera` bara mot en ny användare.

**Lita inte på statistikrader.** Sex buggar hittills har rapporterat
"0 saknade, 0 tomma" och sett ut som lyckade körningar: duplicerade cell-ID:n
som tyst tappade hela svenska s-passiven, lemma-nycklat uppslag som gav 96
homonymer noll former, en cellmatchning som läste fel form och gav 588 falska
fel, ett lemma-nycklat uppslag i `tillämpa-granskning` som skrev rättelser
till fel homonym och räknade dem som lyckade, och två bitmaskjämförelser som
skar av semantikbitar. Jämför alltid antal producerade rader mot antal
celler — och för rättelser: ta en cell-för-cell-bild före och efter:

```bash
python ordbok/verktyg/ögonblicksbild.py före.json   # kör rättelsen   # sedan:
python ordbok/verktyg/ögonblicksbild.py efter.json && diff före.json efter.json
```

**Läs den renderade meningen ord för ord.** Sex strängersättningar i
renderarna matchade inte och gjorde alltså ingenting, utan att något
felmeddelande uppstod. De hittades bara genom genomläsning. Ett svep som
räknar krascher hittar dem aldrig.

**En gren som returnerar tidigt ser aldrig logiken under sig.** Det var
hela passivbuggen — och samma sak gjorde att engelsk negation aldrig nådde
perfektgrenen. Bygger du en konstruktion som lägger sig först i en
verbfunktion: fråga vad den skär bort, och delegera hellre till den
befintliga grenen än att bygga en egen liten kopia av tempuslogiken. Den
lilla kopian blir efter vid nästa utökning, och ingen räknare visar det.

**`bash -n` räcker inte** för att validera ett skript. `FÖRSÖK="${FÖRSÖK:-4}"`
passerade syntaxkontrollen men kraschar — bash tillåter inte å/ä/ö i
variabelnamn. Kör skriptet med stubbade LLM-anrop i stället.

**Julius kan svensk och engelsk grammatik, inte de övriga fem.**
Språkfrågor avgörs av assistenten, som redovisar grunden. Granskningar och
förslag är förslag; Julius beslutar. Fattade beslut skrivs in i
`ordbok/beslut.tsv` med motivering — `beslut.tsv` går före `granskning.tsv`,
och granskningsrapporten ändras aldrig i efterhand. Den ska förbli vad
modellen faktiskt sa.

**Inga quick fixes.** Är det ett verkligt problem som systemet inte kan
hantera, gås det igenom metodiskt — det lappas inte.

---

## Var det står dokumenterat

| Fil | Innehåll |
|---|---|
| `paradigm/SCHEMA.md` | slot-filernas format; §4 om unika cell-ID, §5 om bitmask-kollaps |
| `paradigm/PARAMETER_AUDIT.md` | revision av inflektionsrummen; §1b possessivhålet |
| `paradigm/RENDERARE_KRAV.md` | vad renderaren behöver — den vertikala skivan; statusrad per avsnitt |
| `paradigm/_legend.yaml` | axelkodningen, auktoritativ |
| `docs/BITMASK.md` | alla numeriska koder; §11 semantikbitarna |
| `ordbok/nivålistor/KONVENTIONER.md` | lemmaformat, förenklingsfilosofi §5, beslutsprocess §9 |
| `RUNBOOK.md` | operativ referens för genereringskörningen |
| `START_HÄR.md` | kort körinstruktion för den som genererar |
| `paradigm/RESTRIKTIONER.md` | semantiska restriktioner; scope-beslutet står där |
| `paradigm/GENERATOR.md` | kortmodellen, komplexitetsstegen, nåbarheten — alla beslut med motiveringar |
| `ordbok/beslut.tsv` | fattade beslut som går före granskningen, med motivering |
| `src/sprakprog/rendering/spec.py` | meningsspecifikationen — enda källan till vad som går att uttrycka |
| `ordbok/verktyg/nåbarhet.py` | mäter hur mycket av formbeståndet specen når; modulhuvudet varnar för mätartefakterna |
| `ordbok/verktyg/stammar.py` | härleder stamuppsättning och ändelsetabeller ur Former → `stammar.tsv`, `ändelser.tsv` |
| `kort.sql` | inlärardatabasens schema; huvudet förklarar varför den är en egen fil |
| `src/sprakprog/kort/befolka.py` | härleder kortbeståndet; ORDFÖLJD-listan är korttyp 4 |
| `src/sprakprog/kort/schemalaggning.py` | FSRS-omslaget; modulhuvudet förklarar de tre besluten som är våra |
| `src/sprakprog/generator/poang.py` | poängfunktionens sju termer, med vikterna samlade överst |
| `src/sprakprog/generator/urval.py` | samplaren och nivåstegen |
| `src/sprakprog/generator/rattning.py` | diff → betyg per kort; stamuppdelningen lokaliserar felet |
| `ordbok/migrationer/modusrektion.sql` | vilka ord som styr konjunktiv, och filhuvudet om de fem som medvetet inte taggats |
| `src/sprakprog/generering/rattelse.py` | modulhuvudet förklarar de fyra operationerna och koncept-nyckeln |

**Scope-beslutet, ordagrant:** *"Flickan köpte en dörr."* är helt okej trots
att det är osannolikt. Osannolikt men välformat är godkänt. Konsekvensen är
att klassbaserade restriktioner räcker — ingen LLM-validering av rimlighet
behövs, och inga klasser behöver bli finare än vad som krävs för att stoppa
*kategorifel*.

---

## Kommandon

```bash
ordbok import <csv...> --återinitiera     # bygg om från CSV
ordbok exportera-former <fil.tsv>         # Former → TSV (delningsformat)
ordbok importera-former <fil.tsv> --ersätt
ordbok generera --alla-språk --fortsätt   # böj alla ord (LLM)
ordbok granska-former --alla-språk --fortsätt --rapport <fil.tsv>
ordbok tillämpa-granskning                # skriv in granskningens förslag
ordbok tagga-koncept | tagga-lexem | tagga-monster
ordbok visa <koncept>                     # drill-down
ordbok rendera --exempel --språk <xx>     # rendera exempelmeningen
```

Mätverktygen körs med venvens python:

```bash
.venv/bin/python ordbok/verktyg/nåbarhet.py          # alla sju språk
.venv/bin/python ordbok/verktyg/nåbarhet.py de -v    # per ordklass
.venv/bin/python ordbok/verktyg/rendera_prov.py --språk sv
```

Efter `tillämpa-granskning`: kör alltid `ordbok exportera-former
ordbok/former.tsv`. Annars ligger rättelserna bara i `sprak.db`, som inte
versionshanteras.

Nattkörningarna gjordes med `kör_natt.sh` och `kör_natt2.sh` på en väns
maskin och konto. Båda är idempotenta, väntar ut kvoten själva och kan
avbrytas med Ctrl-C. De behövs inte längre — inget som återstår kräver
LLM-anrop.
