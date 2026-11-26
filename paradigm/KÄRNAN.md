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

| Typ | Franskan | Isolering | Produktion | Beslut |
|---|---|---|---|---|
| `ord` | 227 | ja | ja | oförändrat |
| `egenskap: genus` | 162 | ja | ja | står kvar |
| `egenskap: hjälpverb` | 55 | ja | ja | står kvar |
| `egenskap: böjningsklass` | 210 | ja | **nej** | **stryks** |
| `stam` | 105 | ja | nej | härledningen byts, modellen står |
| `form` | 30 | ja | ja | oförändrat |
| `system` | 16 | ja | ja | oförändrat |
| `ordföljd` | 3 | nej | — | blir nivå **och** kort |
| `rektion` | 2 | ja | ja | oförändrat |

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

**Läs det här avsnittet innan du fyller i något.** Punkterna är hittade genom
att systematiskt leta, och lämnade öppna med avsikt. Att fylla i dem utan att
väga alternativen vore att göra om det fel hela omskrivningen finns för att
rätta.

**Ordningen är byggordningen** — de översta blockerar närmast. Julius tar fyra
i taget uppifrån. Löser ett svar en punkt stryks den; lämnar svaret något
öppet blir resten en ny punkt sist i listan.

*Omgång 1 (punkt 1–4 i den gamla numreringen) är avklarad. Fyra punkter
kollapsade till en, och två nya föddes ur mätningarna. Besluten står i
avsnittet efter listan.*

---

### 1 · Hur många stammar får ett ord ha?

*Ersätter gamla punkt 1–4, som visade sig vara samma fråga.*

**Idag.** Ett ord har en stam. Mätt över franskans 174 verb, efter att
konjunktivens `que`-partikel räknats bort:

    61 %   stammen bär ordet (≥60 % av lemmat)
    21 %   stammen bär hälften
    18 %   stammen kollapsar     aller avoir être faire dire
                                 pouvoir vouloir boire lire mourir

Och de kollapsade är inte vilka verb som helst:

    de kollapsade    90 % på A1,  33 % i bas_kärna
    alla verb        36 % på A1,   6 % i bas_kärna

**Modellen fungerar för de verb man sällan använder och brister för dem man
använder mest.** Följden syns i täckningen: 33,3 former per verb i snitt men
19,9 celler i beroendekartan, och bara 44 av 174 verb helt täckta.

**Luckan.** Julius invände mot stammen som begrepp: *«ibland gäller inte
stammen för alla böjningar, och vårt system antyder att stammen ska vara just
en stam som alltid är en del av varje form»*. Han har rätt. Men han såg också
att alternativet — ett kort per form — tappar kunskapsmomentet att lära sig en
regel: *«nous, alltså -ons»*.

Franskans verb har i själva verket **flera stammar med regelbundna ändelser**:
`avoir` ger `av-ons`, `aur-ai`, `eu-s`, `ay-ez`. Det är samma struktur som
`stamgrupp` redan finns för. Tre modeller, mätta:

| Modell | Kort för franskans verb | Delade ändelser |
|---|---|---|
| en stam per ord | brister för 39 % | 210 |
| **en stam per tempusgrupp** | **1 714** | **189** |
| ingen stam, allt är former | 5 768 | — |
| hybrid: stam där den bär, form där den kollapsar | 2 595 | 210 |

**Alternativ.**

- **a) En stam per tempusgrupp.** Uniformt: regelbundna verb får en eller två
  stammar, oregelbundna får flera, suppletiva former (`vais`, `ont`, `est`)
  får formkort. 1 714 kort, 189 delade ändelser. Kunskapsmomentet blir
  «vilken stam gäller i den här tempusen» plus «vilken ändelse hör till den
  här personen» — båda naturliga.
- **b) Hybrid.** Stam plus ändelse för de 61 % där stammen bär, formkort för
  resten. 2 595 kort. Enklare regel, men två olika modeller i samma lek och en
  gräns någon måste dra vid de 21 %.
- **c) Allt är formkort.** 5 768 kort, inga stammar, inga ändelser. Renast och
  följer Julius egen observation att en regelbunden form lärs snabbt och
  därför kostar lite i FSRS. Men införandet kostar: varje cell av varje ord
  måste mötas en gång.

---

### 2 · Exponeringen ger alla pronomen 0,0

**Idag.** `mät_exponering` bygger 2 000 slumpmeningar och räknar vilka kort de
rör. Men samplaren bygger alltid samma sats: transitivt verb, substantiv som
subjekt, substantiv med adjektiv som objekt. **Pronomen används aldrig som
subjekt.** Mätt i franskan: samtliga pronomen har exponering 0,000 utom `se`
som råkar komma in reflexivt på 0,025.

**Luckan.** Exponeringen avgör om ett kort schemaläggs eller övervakas.
Pronomenen klassas alltså på en mätning som aldrig gjorts — och de är bland de
mest frekventa korten i vilket språk som helst. **Det här är den enda punkten
i listan som är en känd defekt i befintlig kod och inte en obesvarad fråga.**

**Alternativ.** Ingen om *att* den ska lagas. Frågan är hur brett: bara
pronomen som subjekt, eller ska samplaren byggas om för att täcka alla
meningsformer? Samma snedvridning drabbar allt som kräver en konstruktion
samplaren inte bygger — frågor, bisatser, negation.

---

### 3 · Är `que` en del av konjunktivformen?

**Idag.** Konjunktivformerna lagras med partikeln: `que je travaille`,
`que nous travaillions`. Det syns i paradigmtabellen på grammatiksajterna
under «Vol». Det fick min första stammätning att kollapsa för varje
regelbundet verb — prefixet mellan `travaille` och `que je travaille` är tomt.

**Luckan.** Om formen är `que je travaille` är kortets facit det, alltså
inklusive både partikeln och pronomenet. Då är det ingen böjningscell utan en
fras. Och en mening som använder konjunktiv renderar bara verbet — `que`
kommer från konstruktionen, inte från böjningen.

**Alternativ.**

- **a)** `que` och pronomenet skalas av i datan; cellen är `travaille` och
  partikeln hör till konstruktionen som kräver konjunktiv.
- **b)** Formen står som den är, och konjunktivcellerna är fraser snarare än
  böjningar — en egen sorts kort.
- **c)** Formen står som den är i ordboken men skalas vid kortbygget:
  visningen behåller `que`, kortet bär `travaille`.

---

### 4 · Flerordiga lexem har noll kort

**Idag.** `être d'accord` (hålla med) har 35 former och **noll kort**.
`vouloir dire` (mena) har 34 former och noll kort. Orsaken: kortbyggaren
härleder stammen som längsta gemensamma prefix, och när det böjda ledet står
först — `suis d'accord`, `es d'accord`, `sommes d'accord` — blir prefixet
tomt och byggaren ger upp. Tyst.

**Luckan.** Modellen antar att det varierande ligger som ett **suffix**. För
flerordiga lexem stämmer det inte, och de får då inga kort alls. Det gäller
inte bara franskan: varje språk har fraser som böjs i mitten.

**Alternativ.**

- **a)** Flerordiga lexem får formkort per cell — hela frasen är facit.
- **b)** Det böjda ledet identifieras och får egna kort; det fasta ledet
  (`d'accord`) hör till ordkortet.
- **c)** Flerordiga lexem behandlas som ett eget ord med egen böjning, alltså
  som om `être d'accord` vore ett verb i sig.

---

### 5 · Skrivs dagens plan ner eller räknas den om?

**Idag.** Det gamla passlagret skrev ner den, av ett skäl som visade sig hårt:
en plan som räknas om vid varje anrop **kan krympa under användaren mitt i ett
pass**. Innan uppdelningen fanns tre lager lappar ovanpå det — ett minne av
onåbarhet, en sil på oövade ord och en omräkning av taket — och alla tre kunde
tas bort när passet fick vara tillstånd.

**Luckan.** Specen beskriver planen som ett mål men säger inte var det bor.
Och det gamla passlagret raderas.

**Alternativ.**

- **a)** Planen skrivs ner en gång per dygn, som passet gjorde. Stabilt, men
  en tabell till att hålla i synk med kortleken.
- **b)** Planen räknas om men ur ett fruset läge vid dygnets början.
- **c)** Planen räknas om fritt. Enklast, och felet som fällde det förra
  försöket kommer tillbaka.

---

### 6 · Ordningen mellan kort från flera upplåsta nivåer

**Idag.** Att låsa upp kostar ingenting; korten köas och införs under minuter
per dag. Låser användaren upp tio nivåer ligger deras kort i kön tillsammans.

**Luckan.** Ordförrådets ordning är avgjord — frekvens inom ordklass — men den
säger inget om hur ett ordkort från nivå 3 rangordnas mot ett ändelsekort från
nivå 7.

**Alternativ.**

- **a)** Nivåordning går före: allt från den tidigast upplåsta nivån först.
- **b)** Korttyp går före: ord före böjning före regler, oavsett nivå.
- **c)** Frekvens går före, rakt över alla nivåer.

---

### 7 · Betygsskalan är inte omtagen

**Idag.** `FEL, RÄTT = Rating.Again, Rating.Good` — två av FSRS fyra betyg.
Skälet står i koden: *«en diff mot facit ger bara två signaler: formen stod
där eller inte. HARD och EASY lämnas oanvända hellre än att härledas ur något
som inte mäter dem.»*

**Luckan.** Under «bokför allt» gäller resonemanget fortfarande, men det står
ingenstans i specen. En läsare ser fyra betyg i FSRS, ser att svarstid finns i
loggen, och drar slutsatsen att `Hard` borde härledas ur att det tog lång tid.
E3 avvisade just det: svarstid mäter inte minnet.

**Alternativ.**

- **a)** Två betyg, och skälet skrivs in i specen så att det inte behöver
  återupptäckas.
- **b)** Fyra betyg där `Hard`/`Easy` härleds ur något nytt — men då måste det
  som härleder dem först mätas.

---

### 8 · Källspråkets rendering silar tyst

**Idag.** Uppgiften renderas av källspråkets renderare. Misslyckas den
returnerar `_rendera_källa` `None` och kandidaten hoppas över. Mätt på 505
renderade franska kandidater: **2 gick inte att rendera på svenska, 0,4 %.**

**Luckan.** Mekanismen finns men står inte i specen. Andelen är liten; det som
gör den värd att nämna är att den är en **tyst sil**, och under axiomet ska
planen vara byggbar per konstruktion.

**Alternativ.**

- **a)** Skriv in den i specen och mät den som ett acceptansmått.
- **b)** Låt byggbarheten räkna källspråket också.

---

### 9 · Extraövning saknas helt

**Idag.** Det gamla systemet hade «keep practising»: när dagen var klar kunde
användaren fortsätta med kort som ännu inte förfallit, det som förfaller först
först.

**Luckan.** Modellen nämner det inte. Notera att svaret kan ha blivit enklare:
punkt 6 visar att massning ovanpå ett vilat schema kostar noll — 2 rätt med
vila plus 49 massade gav `S = 11,29` mot 10,96 utan.

**Alternativ.**

- **a)** Extraövning finns inte. Dagen är slut när den är slut.
- **b)** Samma kö som förut, nu utan invändningen.
- **c)** Extraövningen bygger meningar av allt infört utan att sikta på något.

---

### 10 · Korttabellen är franskspecifik

**Idag.** Punkt 2:s tabell visar franskan. `egenskap`-kort finns bara i tre
språk: tyskan (genus 136, hjälpverb 55), engelskan (inga efter att
klasskorten stryks), franskan (162 · 55). Japanskan har inga alls.

**Luckan.** Specen säger aldrig vilka korttyper som finns per språk.

**Alternativ.**

- **a)** Tabellen får en kolumn per språk.
- **b)** Specen säger att korttyperna är en möjlig mängd som varje språk
  fyller efter behov.

---

## 12 · Beslut ur omgång 1

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
