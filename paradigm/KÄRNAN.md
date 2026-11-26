# Kärnan

*Specifikation, avgjord 2026-09-09 efter trettio frågor över fem omgångar
mellan Julius och Claude. Läsbar version med tabeller och mätningar finns som
artifact — sök upp den med `Artifact action:list`, titeln är «Inget utanför
dagens plan».*

**Det här dokumentet beskriver en kärna som byggs FRÅN GRUNDEN.** Det är ingen
ändringslista mot koden som finns. `PROBLEM.md` beskriver det gamla systemets
frågor och `GENERATOR.md` dess beslut; båda gäller kod som ska raderas.

---

## Varför

Franskans dag 2026-09-05: 19 meningar, 214 kortmöten, 11,3 kort per mening —
och **13 % av mötena producerade en mätning**. Planen införde 7 nya kort.
Meningarna införde 25.

Två fel, inte ett.

**Meningens kortmängd var upptäckt, inte vald.** Systemet valde en mening för
att täcka några målkort och fick sedan reda på vad den också innehöll.
Undanhållandet, ett-betyg-per-dygn, medföljande kort, återförsöken och
nödutgången är alla skadebegränsning på den upptäckten.

**Och böjningen grindades inte alls.** Alla 42 böjningsceller låstes upp på
nivå 1; de 22 nivåerna grindade bara konstruktioner. Samma sak gällde
renderarens beslut: franskans `klitika_före` fanns som kort men inte som nivå,
och dök upp när en mening råkade innehålla ett objektspronomen.

---

## 1 · Axiomet

> **En mening får bara innehålla kort som redan är införda, eller som står i
> dagens plan.** Inget kort får komma in för att en mening ska gå ihop.

Julius: *«Kort kan introduceras i meningar MEN då måste kortet tillhöra den
uttänkta gruppen kort som ska testas idag. Vi kan INTE slänga in nya kort bara
för att få ihop en mening.»*

Syskonregeln, ur fråga 30:

> **En uppgift är giltig endast om avbildningen från källspråket till
> målspråket är injektiv.** Är den inte det vet användaren inte vilket svar
> som efterfrågas, och rättningen mäter en gissning.

Följden för planen: den får inte innehålla kort som ingen mening kan nå.
Planen byggs mot byggbarheten. Eftersom byggbarheten inte kan sjunka under
dagen — inga kort försvinner — kan sökningen aldrig misslyckas, och därmed
behövs varken reservutgång, nödfallstier eller nödutgång.

---

## 2 · Kortet

Ett kort är **en sak användaren ska kunna producera**. Två test avgör:

- **Isoleringstestet** — går det att lära ut ensamt? Kan det inte det kan det
  heller inte planeras, och då bryter det mot axiomet.
- **Produktionstestet** — är facit en form en människa faktiskt skriver?

**Korttyperna, efter omgång 3.** Varje typ är ett läromoment som går att
klara eller missa oberoende av de andra — det är hela kriteriet.

| Typ | Läromomentet | Ersätter |
|---|---|---|
| `ord` | ordet finns och betyder detta | `ord` |
| `ändelse` | mönstret för den här cellen | `system`, utvidgad |
| `oregelbunden` | **just detta ord** bryter mönstret här | `stam` + `form` |
| `egenskap: genus` | substantivets genus | oförändrat |
| `egenskap: hjälpverb` | avoir eller être | oförändrat |
| `rektion` | vilket kasus verbet styr | oförändrat |
| `regel` | renderarens beslut — blir nivå **och** kort | `ordföljd`, utvidgad |

**Borta:** `stam` och `form` som egna typer, och `egenskap: böjningsklass`.

`stam` föll på produktionstestet — «vad är stammen för *arbeta*?» är ingen
fråga en människa besvarar — och på att den är **härledbar ur lemmat för 121 av
franskans 174 verb**. `form` och `stam` visade sig dessutom vara samma
läromoment: `aur-` och `vais` är båda «detta ord bryter mönstret här», och
skillnaden är bara om en regelbunden ändelse råkar fästa efteråt.

**Regelbundenhet spåras inte — bara undantagen.** Av franskans 1 946
(ord × tempus)-par följer 1 527 regeln «stryk `-er/-ir/-re/-oir`» och 419
bryter mot den. De 78 % som följer behöver inget kort; basen faller ur
ordkortet. Så lär sig också en människa: mönstret först, sedan undantagen.

### 541 kort som ingen kan möta

`böjningsklass` har facit `K0`, `K1` eller `K2` — en klasskod. Ingen människa
skriver «K0», så kortet faller på produktionstestet. Mätt: **210 i franskan,
191 i tyskan, 140 i engelskan, och ingen av de 541 har någonsin mötts eller
införts.**

De behövs inte heller. Kunskapen «det här verbet böjs så här» bärs redan av
**stammen**: `regarder` får imperfektstammen `regard-` och `finir` får
`finiss-`, medan ändelsen `-ais` är densamma. Klassen *är* stammen.

Franskans lek går från 810 till **600 kort**.

### Genus

Julius: *«För tyska och franska måste man lära sig genuset på varendaste
substantiv, vilket tar väldigt mycket tid. För varje substantiv man lär sig
ingår även genuset.»* — 162 kort av 600, alltså 27 %, och det är rätt
proportion.

*(Rättelse: utkast 2–4 skrev «427 genuskort, 53 %». 427 är alla
`egenskap`-kort tillsammans.)*

### Faktoriseringen

Stam plus ändelse ger 151 kort där en cell per lexem skulle ge 4 924. Modellen
är rätt; det var härledningen som brast för lexem som böjs i två leder —
`sœur aînée` blev `sœurs aînée`. **Stammen härleds ur de renderade formerna i
stället för ur lemmasträngen** — renderarna kan redan kongruens.

---

## 3 · Tre nivåstegar

> **Varje beslut renderaren fattar är något användaren måste förstå. Alltså är
> det en nivå.**

| Stege | Grindar | Idag | Franskan |
|---|---|---|---|
| Konstruktion | vad meningen får innehålla | 22 | 22 |
| Böjning | vilka celler som finns | 1 | 11 |
| Realisering | vilka beslut renderaren får ta | 0 | 25 |
| | | **22** | **58** |

En mening får bara använda det alla tre har låst upp.

### Realiseringsstegen per språk

| | ordföljd | övriga beslut | totalt |
|---|---|---|---|
| sv | 4 | 11 | 15 |
| en | 3 | 9 | 12 |
| de | 7 | 10 | 17 |
| fr | 3 | 22 | 25 |
| es | 4 | 24 | 28 |
| it | 3 | 23 | 26 |
| ja | 4 | 6 | 10 |
| | **22** | **111** | **133** |

De 22 ordföljdsreglerna redovisas redan. De 111 övriga sker tyst inuti
renderaren — se punkt 8.

### Ordningen är en graf, inte en lista

Beroendena är **mekaniska** och går att läsa ur renderaren: den vet vilka
celler och konstruktioner den slår upp när den tillämpar en regel.

    perfekt        kräver  particip
    klitika_före   kräver  objektsform
    inversion_wh   kräver  whfråga
    satsklammer    kräver  hjälpverb

Grafen ger en **partiell** ordning: flera nivåer är öppna samtidigt och
användaren väljer bland dem. «Den föregående nivån» betyder nivåns
föregångare i grafen, inte ett löpnummer.

Böjningsstegen ordnar sig på samma sätt: `pres_1pl` har ingenting att
kongruera med förrän `nous` finns, så pluralcellerna är otillgängliga utan att
någon gjort dem otillgängliga.

---

## 4 · Införandet

Julius: *«Man fyller endast i ett kort för varje introduktionsövning. Alltså
inte flera värden i en tabell på en gång utan en i taget.»*

    lära dig nu:  imperfekt, 1 sg

    regarder          sg              pl
    ─────────────────────────────────────────
    presens   1       regarde         regardons
              2       regardes        regardez
              3       regarde         regardent
    ─────────────────────────────────────────
    imperfekt 1       [            ]  ·
              2       ·               ·
    ─────────────────────────────────────────
    futurum                   (inte upplåst än)

    ifylld ruta = det du ska lära dig nu
    fast text  = det du redan kan
    ·          = upplåst men inte infört, går inte att fylla i

Cellen syns som fast text för **andra ord** först när den är klarad. Det gör
tabellen till en ärlig karta: den visar aldrig något du inte har visat.

| Vad som införs | Hur |
|---|---|
| `ord` | glosa: betydelse → form |
| böjningscell | en ruta i paradigmtabellen, en per övning |
| pronomen | hela paradigmet på en gång |
| `egenskap` | tvåval: vilket genus har ordet? |
| `rektion` | vilket kasus styr verbet? |
| realiseringssteg | lektion med regeln och två exempel |
| konstruktionssteg | lektion |

**Pronomenen är undantaget** — jag, du, han, hon, den, det införs tillsammans,
för de är ett system och inte sex fakta.

### Dag ett

Ordboken bär `numerus` på varje pronomen, och `numerus` är konstruktionsnivå
4. Nivå 1 ger därför, utan att någon väljer det: `pronomen_1sg`,
`pronomen_2sg`, `pronomen_3sg_mask`, `pronomen_3sg_fem`, `pronomen_3sg_neutr`,
`pronomen_impersonal` — jag, du, han, hon, den, det. Vi, ni och dem tillkommer
med `numerus`.

Dagen börjar med införanden och når sin första mening när ett pronomen och ett
verb sitter.

---

## 4b · Vad som öppnar en nivå

**Två grindar, och sedan bestämmer användaren.** Systemet säger när en nivå är
möjlig; användaren säger när den ska öppnas.

| | Villkor |
|---|---|
| 1 | **Materialet räcker.** Nivån går att öva. Kräver den en ny sorts kort läggs de i planen direkt. |
| 2 | **Det föregående sitter.** Nivåns föregångare i grafen har mötts och gått rätt minst en gång. |

Julius: *«Grind 3 motstrider FSRS. Det enda den borde styra är att man inte
kan börja nästa nivå förrän man har lyckats minst en gång med den
föregående.»*

**Belastningen flyttar dit den hör hemma.** Att låsa upp kostar ingenting; det
som kostar är korten nivån för in, och de köas under minuter per dag. Låser du
upp tio nivåer i rad får du en kö, inte tio nivåers arbete samma dag.

| Händelse | Kostar | Styrs av |
|---|---|---|
| låsa upp en nivå | ingenting | beroenden + ett lyckat möte |
| införa nivåns kort | en ström av repetitioner | minuter per dag |
| använda regeln i en mening | — | kortet måste vara infört |

En regel du låst upp men vars kort inte införts kan aldrig dyka upp i en
mening — axiomet kräver att kortet är infört.

### Upplåsning och införande är olika frågor

Julius: *«Upplåsning handlar om vad som går och inte går just nu. Införande
handlar om vad som borde läras in just nu. Detta har inga lika självklara
svar.»*

|  | Frågan | Har ett rätt svar? |
|---|---|---|
| Upplåsning | vad *går* att lära sig nu | ja — grammatiken avgör |
| Införande | vad *borde* läras nu | nej — ordningen är ett omdöme |

Lektionen är **införandet av regelkortet**, inte upplåsningen.

---

## 4c · Ordförrådets ordning

**Detta är den enda ordning som måste bestämmas utifrån.** Nivåerna ordnar sig
själva.

### Varför ingen intern signal duger

Två fanns, och båda mäter fel sak:

- **Centralitet** (dagens `rang`) mäter hur många meningar ett ord möjliggör.
  `exister` kan stå med vilket subjekt som helst och blir därför franskans
  *första verb*. Måttet belönar grammatisk räckvidd, inte användbarhet.
- **Exponering** mäter frekvens i våra genererade meningar, och generatorn
  väljer lexem ungefär jämnt. Mätt inom `grundord A1`: 215 ord, **50 av dem
  exakt noll**, median 0,008, max 0,066 — och toppen är `coûter`.

### Delningen finns redan

`Koncept.källa` skiljer precis där den ska:

| Källa | Koncept | Ordklasser | Ordning |
|---|---|---|---|
| `bas_kärna` | 170 | artikel, pronomen, preposition, konjunktion, räkneord, negation, frågeord + 11 hjälp- och modalverb | ingen — knyts till nivåer |
| `grundord` | 566 | substantiv 259 · verb 163 · adjektiv 111 · adverb 33 | frekvens, inom ordklass |

Julius: *«Om det bara handlar om de fyra ordklasserna funkar det nog med en
universell lista, eftersom dessa handlar om semantisk innebörd och inte om vad
grammatiken behöver.»*

> **Grammatiken bestämmer vad som går att lära. Semantiken bestämmer vad som
> är värt att lära först.**

**En universell semantisk lista rankar koncept, inte lemman** — och modellen är
redan nycklad på koncept. Därmed försvinner polysemiproblemet: `per_känna` och
`per_lukta` får var sin rang, och att franskan stavar båda `sentir` spelar
ingen roll.

**Japanskan är undantaget.** Rangkorrelation mellan språk (Spearman) på
innehållsord: de–en, de–fr och en–fr ligger alla på **+1,00**; japanskan på
**+0,08 till +0,13**. Talet mäter dagens centralitet och inte semantisk
frekvens, så det bevisar inte tesen — men japanskan är det språk som ska
kontrolleras för hand innan listan används skarpt.

**Version ett har en ordning, densamma för alla.** Personalisering senare
byter ut listan, inte modellen.

---

## 5 · Meningsbygget

En mening är giltig endast om varje kort den kräver är infört eller står i
dagens plan, och varje regel den använder är upplåst i alla tre stegarna.

### Planen är dagens mål, inte meningens tillstånd

|  | Vad det är | Innehåller |
|---|---|---|
| **Dagens plan** | MÅLET — det som måste klaras | förfallna (FSRS) + dagens nya (tidsratten bestämmer antalet, ordningen vilka) |
| **Det tillåtna** | TILLSTÅNDET — vad en mening får röra | allt infört, plus planen |

Ett infört men inte förfallet kort ligger utanför målet men innanför
tillståndet. Det bokförs som allt annat, och går det fel hamnar det i
återförsökskön och måste klaras innan dagen är slut.

**Budgeten är det som gör att dagen tar slut.** Varje fel lägger till arbete,
men en mening får kosta högst Σ(1−R) ≤ budget i förväntade fel. Svårighetstaket
är termineringsgarantin.

### Tre lager

| Lager | Bestämmer | Styrs av |
|---|---|---|
| Regler | meningens FORM | vilka regelkort som är förfallna |
| Ord | meningens INNEHÅLL | vilka ordkort som är förfallna |
| Budget | hur svår den får bli | Σ(1−R) över allt meningen rör |

**Reglerna väljer formen, orden fyller den, budgeten sätter taket.** Ett
regelkort som inte är förfallet har R nära 1 och kostar nästan ingenting — det
får användas fritt när meningen behöver det. Ett förfallet drar meningen till
sig. Samma tal styr båda dragen, så de kan inte hamna i konflikt.

**Det som saknas är förmågan att bygga MOT en regel.** Generatorn bygger idag
en mening och får sedan veta vilka regler den råkade använda. Varje regel måste
bära sitt byggvillkor — «den här meningen måste ha ett objektspronomen» — och
villkoret finns redan som kunskap inne i renderaren.

### Längden

Julius: *«Det är värdefullt att träna på längre meningar.»* — och mätningen ger
honom rätt med en siffra. Tid per mening, ur loggen:

    kort i meningen   median sek   sek/kort
      1                 16,2         16,2
      2                 17,5          8,8
      4                 20,5          5,1
      8                 24,9          3,1

    korrelation meningslängd (tecken) ↔ tid   r = +0,47
    korrelation antal kort ↔ tid              r = +0,20

**Den fasta kostnaden dominerar.** Två kort i en mening tar 17,5 sekunder; två
enkortsmeningar tar 32. Arbetsbördan går alltså inte att dela på antalet kort.

Taket sitter därför inte på antalet kort utan på hur många som är nya eller
svaga: Σ(1−R) ≤ budget. Meningarna växer av sig själva när användaren blir
bättre.

### Två rattar

> **Tidsratten bestämmer vad dagen innehåller. Svårighetsratten bestämmer hur
> tätt det packas.**

Högre svårighet packar fler kort per mening, ger färre meningar, tar mindre
tid. Lägre svårighet ger fler och enklare meningar, tar mer tid. De förfallna
korten går inte att ändra på — FSRS bestämmer dem.

### Hur många regler en mening bär

Obegränsat per dagspass; flera i samma mening när budgeten tillåter. Budgeten
mäter dock **svårighet, inte möjlighet**: två regler kan kräva oförenliga
former, och då blir meningen inte svår utan obyggbar. Sökningen går vidare.

### Urvalet: hur meningen väljs

*Skrivet 2026-09-10, sedan Julius sagt att han inte har skillsetet att designa
algoritmen själv men vill vara med och bestämma aspekterna.*

**Läget vid varje steg:**

    F   förfallna kort som ännu inte klarats i dag
    N   nya kort dagen tillåter, ännu inte införda
    I   införda kort — det meningen FÅR röra
    B   budgeten, Σ(1−R) per mening

Ett steg: välj en målmängd ur `F ∪ N`, bygg en mening som täcker den inom `B`,
bedöm, lägg tillbaka det som föll i `F`.

#### Problemet är online, inte statiskt

Julius: *«ifall användaren svarar fel, förändrar det vad resten av meningarna
borde vara?»* — Ja. Ett fel lägger till arbete, så **universum växer medan man
löser problemet**. Det utesluter exakt optimering av hela dagen: första
felsvaret ogiltigförklarar planen. Kvar är att välja varje steg väl.

#### Girigt är säkert här, och det är axiomets förtjänst

Girig täckning har ett känt haveri: den kan lämna ett kort som ingen
kvarvarande mening når. **Under axiomet kan det inte hända** — planen byggs mot
byggbarheten, och byggbarheten kan inte sjunka under dagen eftersom inga kort
försvinner. Ett kort som gick att nå i morse går att nå i kväll.

Ingen framblick behövs alltså för korrekthetens skull. Girigt val av nästa
mening är **rätt**, inte bara billigt.

#### Budgeten fördelar risk, inte kort

    korttillstånd                R      kostnad 1−R    ryms i 1,5

    nytt kort, aldrig sett     0,00        1,00             2
    förfallet på sin dag       0,90        0,10            15
    lite försenat              0,80        0,20             8
    sitter, inte förfallet     0,99        0,01           150

**Budgeten binder på nya kort.** Ett nytt kort äter två tredjedelar av en
menings budget; resten räcker till fem förfallna. Den typiska meningen blir
**ett nytt kort och några förfallna** — härlett, inte valt. Det är svaret på
frågan «ett förfallet kort per mening eller flera»: flera, och budgeten säger
hur många.

#### Variation särskiljer, den styr inte

Bland meningar med samma täckning och godtagbar budget vinner den som **minst
liknar de senaste** — annan konstruktionstyp, annan längd. Variationen kostar
då aldrig täckning; den bryter bara likheter.

#### Utfyllnadsplatserna

En plats som inte bär ett mål fylls med ett kort som är infört, har högt `R`
— alltså nästan gratis i budgeten — och **setts minst nyligen**. Samma
kriterium som variationen, tillämpat på ord i stället för på form.

#### Komplexiteten ligger i dragningen

    2 000 samplingar → 1 692 kandidater → 727 distinkta kortmängder

Täckningsbeslutet över några hundra mängder är försumbart. **Kostnaden är att
dra mängderna** — sampla och rendera. Algoritmen är O(samplingar), och det som
går att optimera är hur få samplingar som räcker, inte hur täckningen räknas.

---

## 6 · Bedömningen

**Varje möte med ett schemalagt kort bokförs.**

Julius: *«Det går inte att förneka att korten testas. Frågan är ifall vi vill
bokföra det. Jag tycker det känns logiskt att bokföra.»*

Utkast 2 argumenterade emot med ett tal som mätte fel storhet. Mätt:

    50 massade rätt, ingen vila alls          S =  2,31
    2 rätt med vila emellan                   S = 10,96
    2 rätt med vila + 49 massade ovanpå       S = 11,29

    extra möten per tillfälle    stabilitet efter 120 dygn
      0                                 162,9
      1                                 163,2
      5                                 166,4
     11                                 168,6

Massning som **ersätter** vila skadar. Massning som **läggs till** vilan kostar
ingenting — elva extra per tillfälle ger 3 % *högre* stabilitet.

**Undanhållandet försvinner därmed helt**, och med det ett-betyg-per-dygn, de
olåsbara återförsöksraderna och hela kedjan av undantag som växte ur dem.

Kvar står en mindre kostnad: en logg full av möten vid R ≈ 1 bär lite
information. Svaret är att **filtrera vid optimeringen, inte att låta bli att
skriva** — man kastar aldrig bevis man har.

### När skulden inte går att avgöra

Julius: *«Programmet tvingar användaren specificera exakt vad som blev fel när
det finns flera möjliga svar. Det borde vara möjligt att bygga en rättare som
systematiskt hittar exakt alla tolkningar.»*

Rättningen ska inte **gissa** vilket kort som brast utan **räkna upp alla
tolkningar** som är förenliga med svaret. Är de exakt en bokförs den. Är de
flera frågar programmet.

**Två slags undanhållande måste hållas isär:**

- *«vi frågade efter något du inte fått lära dig»* — försvinner under axiomet.
- *«vi kan inte avgöra vilket kort som brast»* — en äkta gräns för vad en diff
  kan veta. Den finns kvar.

Mätt över hela loggen: 101 av 460 kortmöten undanhölls, men **42 av dem på
meningar som gick RÄTT** — där finns inget fel att fördela, alltså ingen
tvetydighet utan en brist i rättningen. Äkta tvetydighet finns bara bland de
34 på felaktiga meningar.

### Tvetydigheten begränsas av felets läge

En regel kan bara anklagas om den styr ett ställe där svaret avviker. Mätt:

    skilda ställen i meningen     meningar
      1                             36
      2                              8
      3 eller fler                   0

**82 % skiljer sig på exakt ett ställe.** En lång mening kan lyda tio regler,
men frågan blir «vilken av två», inte «vilken av 133».

**Omprov förkastas.** Julius fällde sin egen idé: *«då har användaren ogiltigt
hunnit träna precis innan på regeln som passades»*. Ett omprov mäter inte om du
kunde regeln utan om du kunde den efter att just ha sett svaret.

### När svaret är rätt men inte det som frågades

Systemet gör tre saker och inte fler: **godtar meningen, bokför inte
målkortet, säger inte vilket ord som var tänkt.** Kortet står kvar som
förfallet och kommer tillbaka en annan dag, omätt men oförstört.

Var injektiviteten brister är mätt: **16 svenska lemman** — `fråga`, `får`,
`hälsa`, `fisk`, `för`, `en`. För de flesta avgör meningen ändå, eftersom
läsningarna skiljer sig i ordklass. Facit godtar varje läsning som går att
rendera in i meningen och förkastar dem som inte gör det.

### Kort som möts oftare än en gång om dagen

För franskans `le` finns ingen förfallodag som betyder något: det står i fyra
meningar av fem och möts femton gånger om dagen vilket intervall FSRS än
sätter. Sådana kort får ett **fönster**: de tio senaste mötena och andelen rätt
i dem. Blir felen fler än slumpen bär blir kortet ett mål i dagens plan tills
fönstret är rent.

Fönstret är 1/(1−0,9) = tio möten; tröskeln är samma tolerans som
retentionsmålet. Båda härledda. **Byggt, mätt och prövat med tio invarianter —
bärs över.**

---

## 7 · Hur en nivå repeteras

**Varje nivå i böjnings- och realiseringsstegarna blir ett kort.**
Konstruktionsstegen blir det inte.

Julius: *«Konceptet av vad ett objekt är är redan helt självklart eftersom det
finns i det språk man kan. Hur man använder objektet och hur man placerar det
är det som användaren behöver lära sig.»*

Ett konstruktionssteg lär inte ut att objekt finns. Det som ska läras är
språkets **realisering** av objektet, och den har egna nivåer och egna kort:

    konstruktionen «objekt» öppnar…    och det som lärs är
      fr   klitika_före     regel      objektspronomen före verbet
           cod · coi        celler     objektsformerna
      de   dativ_före_ackusativ        ordningen mellan två objekt
           akk · dat        celler     kasusformerna

Modellen gör redan så: franskan har 22 konstruktionsnivåer och tre
ordföljdskort, alltså har **19 av dem inget kort**.

**Vilken sort ett regelkort blir faller ur exponeringen**, precis som för alla
andra kort:

| Regel | Möten/dag | Sort |
|---|---|---|
| `svo` | 20,0 | övervakad — fönster |
| `klitika_före` | låg | schemalagd — måste sökas upp |
| `inversion_wh` | låg | schemalagd — måste sökas upp |

Julius: *«De första nivåerna upprepas naturligt i typ alla meningar MEN de
senare mer komplexa förekommer inte lika naturligt.»* — och uppdelningen
behöver därför inte göras för hand.

---

## 8 · Repot och koden

**Repot behålls.** Risken är att renderaren fattar beslut som kortmodellen inte
grindar — ett gränssnittsproblem, inte gammal restkod. Renderarna följer med
oförändrade till ett nytt repo, så samma hål skulle finnas där.

**Villkoret: den nya kärnan får inte importera något ur den gamla.** De gamla
filerna raderas, de anpassas inte. Det är den enda mekanism som säkert hindrar
restkod, och den är starkare än ett nytt repo där frestelsen att kopiera in
«det som fungerade» finns kvar.

| Del | Rader | Beslut |
|---|---|---|
| renderarna, sju språk | 4 400 | står kvar — utökas med 111 redovisade beslut |
| språkdatabasen och paradigmen | — | står kvar |
| ordboksbygget | 2 200 | står kvar |
| FSRS-integrationen | — | skrivs om, tunn |
| övervakade kort | — | bärs över som modell |
| näten och mätkorpusen | — | acceptanskrav på det nya |
| befolkning · schemaläggning · pass | 3 800 | **raderas** |
| generator · urval · poäng | 1 800 | **raderas** |
| rättningen | 1 200 | **raderas** |

Följande skrivs inte om, för de finns bara för att hantera följderna av att
meningen upptäcks: undanhållandet, ett-betyg-per-dygn, medföljande kort,
reservutgången, nödfallstiern, tomgångsspärren, nödutgången.

### Vad «redovisa» betyder

Maskineriet finns. `Uppslag.ordföljd(regel)` är den fjärde instrumenteringen
och dess egen docstring säger: *«här ÄR anropet hela informationen»*.

```python
self.u.ordföljd("inversion_wh")     # redovisas — observerbar
...
def eliderar(self, första, andra):  # redovisas inte — sker tyst
```

Den enda raden gör tre jobb: gör regeln till en **nivå**, till ett **kort**,
och ger **beroendegrafen sin kant**.

---

## 9 · Acceptans

| Mått | Idag | Krav |
|---|---|---|
| kort i en mening som varken är införda eller planerade | 4 | 0 |
| nya kort som införs utanför planen | 25 av 32 | 0 |
| andel kortmöten som bokförs | 13 % | 100 % |
| regler renderaren använder utan att vara upplåsta | ej mätt | 0 |
| förväntat antal fel per mening, Σ(1−R) | ej styrt | ≤ budget |
| kortmöten där rättaren måste fråga | ≤ 31 % av fel | mäts, ska sjunka |
| uppgifter med mer än ett rätt svar | ej mätt | 0 |

### Vilka ställen som är lösa

Julius förlitar sig på resonemang och FSRS vetenskapliga grund, och accepterar
prov på *«de aspekter som är lite mer lösa»*. Det är rätt skiljelinje. Dessa
fyra är lösa; allt annat är härlett ur axiomet eller ur en mätning.

| Löst ställe | Varför | Vad ett prov mäter |
|---|---|---|
| ordförrådets ordning | kommer utifrån, japanskan avviker | att de första hundra orden går att bygga meningar av |
| svårighetsrattens verkan | modell av beteende, inte härledning | att högre svårighet ger färre och kortare pass |
| hur ofta rättaren frågar | mätt på 44 meningar med 3 regler | samma tal när regelkorten är 133 |
| lektionernas granularitet | en funktion är kanske inte ett steg | — syns bara på användaren |

### Sex ställen där resonemang gav fel svar

Under specarbetet, som skäl att behålla måtten:

| Resonemanget sa | Mätningen sa |
|---|---|
| massade repetitioner skadar | de kostar 0 ovanpå ett vilat schema |
| schemalagda kort möts högst en gång per dygn | 13 % möts oftare, ett så mycket som tolv |
| 427 av leken är genuskort | 162 — resten var annat |
| arbetsbördan delas på antalet kort | fast kostnad dominerar |
| exponeringen kan ordna ordförrådet | platt fördelning, 50 nollor, `coûter` först |
| böjningsklasskorten bär kunskap | 541 kort, aldrig mötta, aldrig införda |

---

## 10 · Byggordningen

Tre saker kan inte härledas och är arbete snarare än beslut: **renderarnas 111
redovisade beslut**, **133 lektionstexter**, och **den semantiska
frekvenslistan** (japanskan kontrolleras för hand).

    1  renderarna redovisar besluten      allt annat kräver detta
    2  nivåstegarna och grafen            faller ut ur 1
    3  kortmodellen                       541 klasskort stryks
    4  planen och införandet              kräver 2 och 3
    5  meningsbygget under axiomet        kräver 4
    6  rättningen som räknar upp          kräver 1 för regelattribution
    7  lektioner och frekvenslista        parallellt hela vägen

**Steg 1 är också billigaste sättet att fälla modellen.** När renderarna
redovisar går det att mäta hur många regler en mening faktiskt använder, och
därmed om attributionen fungerar med 133 kort i stället för 3. Faller det där,
faller det innan något raderats.

---

## 11 · Kvarstående luckor

*Omgång 1–6 avklarade. En ny punkt föddes när Julius upptäckte att punkt 2
aldrig uppdaterats efter omgång 3.*

---

### 1 · Vad är enheten för ett `oregelbunden`-kort?

*Ny 2026-09-10. Upptäckt när talen skulle räknas om för alla språk.*

Omgång 3 avgjorde att `stam` och `form` slås ihop till `oregelbunden` —
«just detta ord bryter mönstret här». **Men «här» är inte definierat**, och
talet svänger med hur gränsen dras. Mätt på franskan, samma data, tre
tolkningar:

    per FORM              4 460 kort   varje oregelbunden form för sig
    per (ord × grupp)     1 037 kort   grupp = tempus och species
    per (ord × tempus)      419 kort   grupp = bara tempus

**En faktor tio mellan ytterligheterna.** Och skillnaden är ett verkligt
läromoment, inte en teknikalitet:

- `avoir` har futurumbasen `aur-`, och den bär sex celler. Är det **ett**
  läromoment eller **sex**?
- `aller` har `vais`, `vas`, `va`, `vont` men `all-` i imperfekt. De fyra är
  suppletiva var för sig och delar ingen bas.

Den första talar för gruppnivå, den andra för formnivå. **Båda finns i samma
språk**, vilket är skälet att frågan inte har ett självklart svar.

**Alternativ.**

- **a) Per form.** Varje oregelbunden form är sitt eget kort. Renast mot
  produktionstestet — facit är alltid något man skriver — men 4 460 kort i
  franskan och varje cell måste införas.
- **b) Per grupp, där en gemensam bas finns.** `aur-` blir ett kort som bär sex
  celler; `vais` blir ett eget eftersom ingen bas delas. Följer språket, men
  gruppgränsen måste definieras per dimension och det är där de tre talen ovan
  kommer ifrån.
- **c) Per grupp, med gruppen given av paradigmets egen struktur** — alltså
  det renderaren slår upp som en enhet. Skjuter frågan till renderaren, som
  redan vet, men kräver att den redovisar det (samma arbete som de 111
  besluten).

---

### 2 · Korttypernas mix skiljer sig mellan språken

**Idag.** Räknat i den nya modellen, per (lexem × tempusgrupp):

    språk    ord    ändelse    oregelbunden
    en       734         63             144
    de       734        577             956
    fr       732        298           1 037
    ja       724         23           1 554

**Luckan.** Specen visar franskan och säger aldrig att japanskan har **23
ändelser mot franskans 298** och nästan allt i `oregelbunden` — vilket är rätt
för ett agglutinerande språk, men överraskande för en läsare. Svenskan har
inga kort alls, eftersom ingen kurs har svenska som målspråk.

*Talen ovan hänger på punkt 1 och ändras när den avgörs.*

**Alternativ.**

- **a)** Tabellen får en kolumn per språk.
- **b)** Korttyperna är en möjlig mängd som varje språk fyller efter behov, och
  mixen visas som en mätning i stället för som en norm.

---

## 12 · Beslut ur omgångarna

### Omgång 6 (2026-09-10)

#### Efterfrågemätningen stryks — den går inte att mäta rent

Julius: *«jag vill endast ha detta ifall vi verkligen kan mäta det bra. Hur ska
man avgöra något sådant när meningar i teorin kan bli oändligt stora och helt
olika?»*

Två versioner prövades och båda föll.

**Den samplade** — räkna hur ofta varje ordklass efterfrågas i genererade
kandidater — har **exakt samma fel som exponeringsmätningen som ströks i
omgång 2**: den mäter samplarens fördelning, inte språkets. Att jag byggde om
det felet en omgång senare är värt att skriva ner.

**Den strukturella** — räkna hur många införda kort som kan fylla varje roll —
ger ingen diskriminering. Mätt: varje franskt verb kan stå med **alla 736
koncept**. Selektionsrestriktionerna är inte finkorniga nog för att någon roll
ska kunna vara «tom».

Julius villkor var att måttet skulle gå att mäta bra. Det gör det inte, och
idén läggs ner. **Införandeordningen förblir frekvens inom ordklass.**

#### Japanskan är inte svårare, den är annorlunda formad

Julius: *«har inte alla språk samma kortmetodik? Kanske japanskan är lite
svårare?»*

Metodiken är densamma; mixen är helt annan.

    typ         fr    ja
    egenskap   427     0     inget genus, inga böjningsklasser
    form        30   145     femton gånger fler helformer
    stam       105    55
    system      16     4

    böjningsdimensioner i bruk
    fr   diates, genus, grad, numerus, person, tempus      6
    ja   diates, grad, tempus                              3
    de   + kasus, species                                  8

    distinkta former:  de 13 617 · fr 7 900 · ja 2 495

**Japanskan har färre dimensioner och färre former än både franskan och
tyskan** — den är enklare mätt så. Det den har mycket av är helformer, därför
att verbformerna är agglutinerande och lärs som helheter: 食べる, 食べます,
食べた.

Och det **stämmer med kortmodellen från omgång 3**: `ord` + `ändelse` +
`oregelbunden`. Japanskan hamnar nästan helt i `oregelbunden`, vilket är rätt —
dess former lärs som helheter. Modellen behöver inte anpassas per språk; den
fördelar sig själv.

---


### Omgång 5 (2026-09-10)

#### Grind 1 binder vid två ord och aldrig mer

Julius: *«jag är skeptisk till att det finns situationer där vi har fysiskt för
få kort för att kunna aktivera en nivå. Det finns en risk att vi bygger detta
och ser att denna grind aldrig sätter stopp för något.»*

**Mätt, och han har rätt.** Byggbarheten på franskans TOPPNIVÅ, med växande
ordförråd:

    ordförråd    byggbarhet nivå 22    × 1000     grind 1
        2              0,000               0      STÄNGD
        4              0,985             985      ÖPPEN
        8              0,998             998      ÖPPEN
       32              0,968             968      ÖPPEN

Grinden kräver `byggbarhet × kandidater ≥ 1`, alltså 0,001. Den ligger på
0,97 — **tusen gånger från att binda**. Den stoppar det degenererade fallet på
dag ett och aldrig något annat.

Den får stå kvar därför att den är gratis och korrekt, men **den är inte
takten**. Takten är regeln om en nivå per dygn och införselhastigheten.

#### Efterfrågan per ordklass är en verklig signal

Julius föreslog att mäta *«vilka typer av ord det är hög eller låg efterfrågan
på, så att vi håller värdena balanserade»*. Mätt på franskan, 1 500
kandidater mot de 85 införda korten:

    ordklass       i leken   andel   efterfrågan   andel   kvot
    Substantiv        17      53 %       1 694      36 %   0,67
    Artikel            2       6 %       1 430      30 %   4,84
    Verb               5      16 %       1 280      27 %   1,73
    Pronomen           8      25 %         321       7 %   0,27

Kvot över 1 betyder att klassen efterfrågas oftare än den finns. **Införandet
lägger alltså in för många substantiv och pronomen och för få verb** i
förhållande till vad meningar faktiskt behöver.

**En nyans som måste med:** artiklarnas 4,84 går inte att åtgärda — franskan
har två obestämda artiklar och fler finns inte. Signalen får bara styra de
**öppna** ordklasserna, där det finns fler kort att införa.

#### Det finns inga källspråk i motorn

Julius: *«resonemanget att just källspråket är trasigt låter konstigt eftersom
det inte finns några källspråk. Kurserna kanske har det, men motorn ser alla
språk som symmetriska och likvärdiga i alla riktningar.»*

Rätt, och min framing dolde det verkliga felet. Prövat symmetriskt — 1 010
meningsspecar mot alla sju renderare:

    språk som klarar specen     antal specar
       7                             612
       6                             322
       5                              69
       4                               5
       3                               2

    misslyckanden per språk
       it  292  (28,9 %)      en   14  (1,4 %)
       de   79  ( 7,8 %)      sv   10  (1,0 %)
       es   62  ( 6,1 %)      fr    2  (0,2 %)
       ja   24  ( 2,4 %)

**Italienskan faller på 29 % av alla specar — 145 gånger oftare än
franskan.** Och 291 av de 292 fallen kommer från ETT lexem:

    es   un, unos, una, unas     4 former
    fr   un, une, des            3
    it   un, uno, una            3   ← alla singular

**Italienskan saknar obestämd plural helt.** Systemet visste redan — koden bär
noten *«Italian is missing indefinite plurals — about a third of sentences
cannot be built yet»* — och mätningen bekräftar «about a third» exakt.

Tyskans 79 är något annat: fraslexem med framförställt adjektiv,
`älterer Bruder`, alltså samma tvåledsböjning som `sœur aînée`.

Julius gissning att alla renderingsfel är buggar stämmer nästan. Undantaget är
svenskans plurale tantum — `vantar` har ingen singular, och då **ska** meningen
inte ställas. Det är inte en bugg utan en språkskillnad, och den syns bara som
ett fel därför att den räknas tillsammans med dem.

---


### Omgång 4 (2026-09-10)

#### Grind 1 är redan en fysisk begränsning

Julius: *«det tar emot att sätta begränsningar i stället för att utnyttja
fysiska begränsningar. Så fort jag sätter manuella begränsningar förstör jag
renheten.»* — och invändningen bygger på ett missförstånd som är mitt fel att
inte ha rett ut.

Grind 1 är **inte** ett valt tal som «du behöver tjugo substantiv». Den frågar
om generatorn faktiskt kan bygga meningar på nivån, och tröskeln är härledd ur
sökningens egen takt:

    byggbarhet × kandidater ≥ 1

Alltså: andelen dugliga kandidater måste vara stor nog att minst en väntas per
sökning. Samma form som exponeringströskeln och av samma skäl. Det **är** den
fysiska begränsningen — nivån öppnas när språket och ordförrådet räcker, inte
när någon tycker det.

Julius fråga *«borde det finnas krav på ett visst antal ord per nivå?»* har
därmed svaret nej, och det är redan så: kravet är byggbarhet, inte antal.

#### En nivåuppgradering per dygn, härledd ur FSRS

Julius ville ha regeln men uttryckt snyggt: *«i stället för att gå efter att
kortet ska bli klart borde regeln vara att man endast kan höja nivån en gång
per dag.»*

Den behöver inget eget tak. Nivåns kort är ett kort som alla andra, och FSRS
kortaste meningsfulla intervall är **ett dygn** — ett kort som införs i dag kan
inte prövas igen förrän i morgon. Regeln blir därför:

> **Nästa nivå öppnas när föregående nivås kort har prövats en gång, och den
> prövningen inte skedde i dag.**

Det ger exakt en nivåuppgradering per dygn, utan ett valt tal, och det stänger
kryphålet Julius pekade på — att gå ut ur passet, höja nivån och gå in igen.
Formuleringen är hans egen: kortet räknas som lärt först nästa dag.

#### Två betyg nu, manuellt Hard/Easy senare

Julius: *«vi kommer inte kunna mäta hard eller easy på något hållbart sätt. Det
är användarens egna upplevelse. Däremot är jag inte emot att användaren själv
kan skriva in det.»*

Avgjort. `Again` och `Good` härleds ur diffen och räcker för FSRS. `Hard` och
`Easy` **härleds aldrig** — särskilt inte ur svarstid, som E3 avvisade. Men
användaren får senare markera dem för hand, med en genväg på kortet. Det är
inom FSRS logik: betyget är då en uppgift från användaren och inte en gissning
från systemet.

#### Källspråket silar inte modellen, det silar datan

Julius: *«detta är oroväckande eftersom vårt universella språksystem bygger på
att man bygger upp universella meningar med pythonobjekt som sedan kan renderas
till vilket språk som helst.»*

Mätt, och arkitekturen står. Av 2 557 franska kandidater föll 24 på svenskan:

    17   svenskan har ingen sådan form   «vantar» är plurale tantum
     7   formen saknas i ordboken        sv/bröd, best_pl_ack_dat_nom tom

De 17 är **rätt beteende**. Meningsobjektet är universellt, men ett enskilt
språk realiserar inte varje cell — och då ska meningen inte ställas, för den
går inte att översätta. De 7 är en datalucka, inte ett arkitekturfel.

---


### Omgång 3 (2026-09-10)

#### Kortmodellen: tre läromoment, inte fem

Julius ställde den avgörande frågan: *«fyller bas och stam något intuitivt
naturligt läromoment? Är inte det typ samma sak som korttypen ord? Samma
problem har jag gällande ändelse och form — besvarar de inte ungefär samma
läromoment?»*

Med hans egen princip — **ett kort ska representera ett naturligt läromoment,
annars är datan meningslös och man kan inte veta när man lyckas** — prövas
varje par genom att fråga: kan man klara det ena och misslyckas med det andra?

    ord   mot bas     kan avoir, vet inte att futurum är aur-     DISTINKT
    ord   mot ändelse kan travailler, vet inte att imperfekt är -ais  DISTINKT
    ändelse mot bas   kan -ai, vet inte aur-; kan aur-, vet inte -ai  DISTINKT
    bas   mot form    aur- och vais är BÅDA «detta ord bryter
                      mönstret här»                              SAMMA

**Julius hade rätt: `bas` och `form` är samma läromoment.** Skillnaden är bara
om en regelbunden ändelse råkar fästa efteråt, vilket är en egenskap hos
språket och inte hos inlärarens uppgift. De slås ihop till `oregelbunden`.

| Kort | Läromomentet | Franskan |
|---|---|---|
| `ord` | ordet finns och betyder detta | 227 |
| `ändelse` | mönstret för den här cellen | ~189 |
| `oregelbunden` | **just detta ord** bryter mönstret här | 419 |

**Regelbundenhet spåras inte — bara undantagen.** Mätt: av franskans 1 946
(ord × tempus)-par följer **1 527 regeln** «stryk `-er/-ir/-re/-oir`» och 419
bryter mot den. De 78 % som följer behöver inget kort alls; basen faller ur
ordkortet. Det är också så en människa lär sig: mönstret först, sedan vilka ord
som bryter det.

`stam` och `form` försvinner som korttyper. Täckningen går samtidigt från 60 %
av paradigmet till 100 %, eftersom undantagskortet inte kräver att det
varierande ligger som ett suffix — vilket var buggen som gav `être d'accord`
noll kort.

#### Dagens plan är en fråga, inte en tabell

Julius: *«dagens pass är inget komplicerat. Det är ju bara en lista på
förfallna kort. Vi har ju all info från användarhistorik vad som har bedömts
när. Att skriva ner det en gång per dygn känns meningslöst.»*

Rätt. `Repetition` bär kort, tidpunkt och betyg, så **vilka kort som är
förfallna är härledbart när som helst**. Ingen plantabell behövs.

Det gamla passlagret skrevs ner av ett skäl som inte längre finns. Det som
kunde krympa under användaren var tre saker — onåbara kort, silen på oövade
ord, omräkningen av taket — och alla tre är borta: axiomet gör att byggbarheten
inte kan sjunka under dagen, «oövade» finns inte som begrepp, och dagens tak
fryses redan en gång per dygn av belastningsmodellen.

**Kvar att lagra är bara det som redan lagras:** repetitionshistoriken, och
dagens tilldelning av nya kort.

#### Ett kort tillhör ingen nivå

Julius: *«vad menas med ordkort från nivå 3? Kortet kanske låses upp vid nivå 3
men efter det har det ingen anknytning till nivåer. Under själva lektionerna är
ju kort alltid bara kort.»*

Han har rätt, och frågan var min egen förvirring. En nivå **öppnar** ett kort;
därefter är kortet ett kort. Införandeordningen är redan avgjord — frekvens
inom ordklass — och den behöver ingen nivåkomponent.

Det som var verkligt i frågan blev punkt 2 i listan: vad som krävs för nästa
nivå, och om det syns.

---


### Omgång 2 (2026-09-09)

#### Exponeringsmätningen stryks — den mäter fel sak

Julius: *«Detta exponeringsexperiment verkar trasigt och konstigt. Såklart ska
pronomen dyka upp i meningar, och det som ska trigga ifall ett pronomen ska
repeteras är ifall kortet behöver repeteras.»*

Han har rätt, och invändningen går djupare än buggen. `mät_exponering`
**simulerar** hur ofta ett kort möts genom att sampla 2 000 meningar. Men
sedan omgång 1 bokförs varje möte, alltså **finns siffran i loggen**. Ett
simulerat tal där ett mätt finns är precis den sortens antagande projektets
egen regel förbjuder.

Uppdelningen schemalagt mot övervakat drivs därför av **observerade möten per
dygn**, inte av en samplare. Följderna:

- Samplarens snedvridning försvinner — det finns ingen samplare.
- Ett nytt kort har ingen historik och är därför **schemalagt** tills det visat
  sig mötas oftare än en gång om dagen. Rätt förval: det ofarliga hållet.
- Gamla punkt 2 i lucklistan är struken. Buggen behöver inte lagas, koden
  behöver inte skrivas.

#### Kortets facit är det renderaren slår upp

Gamla punkt 3 och 4 — `que` i konjunktiven och de flerordiga lexemen — har
samma svar, och det står redan i koden:

    arb_arbeta    subj_3sg   → 'travaille'        que och pronomenet avskalade
    arb_arbeta    pres_1sg   → 'travaille'
    kom_hålla_med pres_1sg   → "suis d'accord"    hela frasen
    gen_mena      pres_3sg   → 'veut dire'

`Uppslag.form(lexem, cell)` returnerar redan det som ska produceras. `que je`
i ordboken är visningsmaterial som renderaren inte använder; för ett flerordigt
lexem är hela frasen det som produceras.

> **Kortets facit är det `Uppslag.form` returnerar.** Vad renderaren lägger
> runt omkring hör till andra kort eller till konstruktionen.

Att `être d'accord` i dag har noll kort är därmed inget modellproblem utan en
bugg i kortbyggaren: den härleder en stam som längsta gemensamma prefix och
ger upp när det böjda ledet står först. Renderaren har aldrig haft det
problemet.

---

### Omgång 1 (2026-09-09)


*Julius svarade på gamla punkt 1–4 den 2026-09-09. Fyra punkter kollapsade
till en; det som blev kvar står som punkt 1, 3 och 4 ovan.*

### Cellen är gränssnittet, korten är modellen

Julius: *«Här kan vi se tydligt att det alltid finns endast ett ord per
cell.»* Han har rätt, och missförståndet var mitt. En ruta i paradigmtabellen
har alltid ett ord. Att systemet bakom rutan bokför ett eller två kort är
intern bokföring om vad som ska prövas och vad som ska få skulden — användaren
ser det aldrig.

**«Ett kort per övning» läses «en ruta per övning».** Det kan modellen alltid
uppfylla, oavsett hur punkt 1 avgörs.

### Regelbundenhet är inte ett kort

Julius: *«ifall man hade kort för att fånga just regelbundenheten hade det
behövts ett kort som trackar att användaren vet att just detta ord tillhör
denna regelbundenhet»*. Precis — och det kortet fanns: `böjningsklass`, 541
stycken, aldrig mötta.

**Vilken klass ett ord tillhör är inte ett kort utan en egenskap som avgör
vilka kort som finns.** Användaren får aldrig frågan «vilken klass tillhör
det här»; de får former, och vilka former de får skiljer sig åt beroende på
klassen.

### En böjning som inte påverkar meningen prövas inte

Julius: *«i vissa former såsom infinitiv spelar inte pronomenets böjning roll…
vi måste ha ett robust system för att veta när en böjning faktiskt har en
påverkan»*.

Systemet finns redan. Renderaren **slår upp** de celler den behöver, och
`Uppslag.form(lexem, cell)` är instrumenterad. Slog den aldrig upp en
personböjd cell skedde ingen kongruens, och då finns ingenting att pröva. Det
är samma instrumentering som gör renderarens beslut till nivåer.
