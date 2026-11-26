# Kärnan

Den fullständiga specifikationen av kärnan — korten, nivåerna, dagspasset,
meningsbygget och bedömningen — så som den ska byggas. Filen beskriver målet,
inte ändringar i den kod som finns.

> **Läge 2026-09-12.** Specen är avgjord utom en fråga (punkt 10), och den
> blockerar inget. Kortmodellen och aspektvalet avgjordes samma dag. Det som
> står först i tur är arbete, inte beslut: språkens böjningsregler (steg 0) och
> renderarnas redovisning (steg 1), som kan göras samtidigt.

Här står besluten och de skäl en byggare behöver för att inte ändra dem av
misstag. Resonemangen och mätningarna bakom dem finns i git-historiken
(`git log -- paradigm/KÄRNAN.md`). Idéer som prövats och fallit står i bilaga A.

## Innehåll

1. Uppdraget
2. Grundreglerna
3. Korten
4. Nivåerna
5. Dagspasset
6. Meningsbygget
7. Bedömningen
8. Koden
9. Byggordningen
10. Öppen fråga
11. Acceptans
12. Kända fel i data och kod

Bilaga A · Förkastat, och varför
Bilaga B · Varför varje tal ska vara mätt

---

## 1 · Uppdraget

Kärnan avgör vad användaren ska lära sig, i vilken ordning, i vilka meningar,
och vad ett svar säger om vad hen kan.

Den byggs **från grunden**. Renderarna, språkdatabasen och ordboksbygget står
kvar; resten av dagens kärna raderas (punkt 8). `PROBLEM.md` och `GENERATOR.md`
beskriver det gamla systemet.

### Vad som var fel

Franskans dag 2026-09-05: 19 meningar och 214 kortmöten — men **bara 13 % av
mötena gav en mätning**. Planen införde 7 nya kort; meningarna införde 25.

Två grundfel, och resten av specen är deras motsats:

- **Meningens kortmängd upptäcktes i stället för att väljas.** Systemet valde en
  mening för att täcka några kort och fick först efteråt veta vad den mer
  innehöll. Undanhållande, ett-betyg-per-dygn, medföljande kort och nödutgångar
  var alla skadebegränsning på det.
- **Böjningen och renderarens beslut grindades inte.** Alla böjningsceller
  öppnades på nivå 1, och franskans objektspronomen dök upp så fort en mening
  råkade innehålla ett.

---

## 2 · Grundreglerna

Sex regler. Allt annat i specen följer av dem eller av en mätning.

**R1 · Axiomet**

> En mening får bara innehålla kort som är införda. Inga kort införs under
> meningsfasen.

Nya kort införs i dagspassets introfas (5.1). Inget kort får komma in för att en
mening ska gå ihop — det var så planens 7 nya kort blev 25.

**R2 · Entydigheten**

> En uppgift är giltig endast om exakt en målmening är korrekt.

Har källmeningen två korrekta översättningar vet användaren inte vad som
efterfrågas, och rättningen mäter en gissning. Egenskapen är att relationen
källmening → målmening är en *funktion*; den är varken injektivitet eller
surjektivitet.

**R3 · Varje beslut renderaren fattar är en nivå och ett kort**

> Allt renderaren avgör är något användaren måste kunna. Därför måste varje
> beslut gå att grinda och att pröva.

Det kräver att renderaren **redovisar** sina beslut (8.3). Ett beslut som sker
tyst kan varken låsas eller rättas.

**R4 · Mätt skrivs, härlett räknas, inget gissas**

> Om meningen var rätt eller fel är mätt. Vilket kort som bär skulden är
> härlett. Loggen får bara innehålla det mätta och det entydigt härledda.

Sannolikheter får styra vad som prövas härnäst — aldrig vad som skrivs.

**R5 · Rättningen ska aldrig behöva gissa**

> Är ett svar tvetydigt eller ett fel omöjligt att knyta till ett kort, var
> uppgiften fel vald.

Varje sådant fall är en brist i generatorn, inte i rättaren. Vad rättaren gör när
det ändå händer står i 7.3.

**R6 · Inga valda tal**

> Varje tal i kärnan är härlett, mätt eller användarens val.

Retentionsmålet 0,9 är grunden; toleranser, fönster och trösklar härleds ur det.
Bilaga B visar varför regeln finns.

---

## 3 · Korten

### 3.1 Vad ett kort är

Ett kort är **ett läromoment: något användaren ska kunna producera, och som går
att klara eller missa oberoende av andra kort.** Två test:

- **Isoleringstestet** — går det att lära ut ensamt? Annars kan det inte planeras.
- **Produktionstestet** — övas kortet genom att användaren skriver en riktig
  form? Kortet bedöms på sin del av formen: ett ändelsekort på `-ais` i
  `parlais`, ett undantagskort på `aur-` i `aurai`. En klasskod som `K0` ingår
  aldrig i någon form och klarar därför inte testet.

Ett kort tillhör ingen nivå. En nivå *öppnar* kort; därefter är ett kort bara ett
kort.

### 3.2 Korttyperna

Typerna är inte valda. De är svaren på de frågor renderaren ställer när den
skriver ett ord, och den listan är sluten:

| Renderarens fråga | Kort | Nyckel | Familj |
|---|---|---|---|
| vilket ord betyder detta? | `ord` | lexemet | ord |
| vilken form — **läst** ur en tabell? | `oregelbunden` | lexemet (+ stamgrupp) | ord |
| vilken form — **byggd** ur ett mönster? | `ändelse` | ordklass, klass, sträng | mönster |
| vad kräver det styrande ordet? | `rektion` | ordet + slotten | ord |
| vilken egenskap hos ordet syns på ett **annat** ord? | `egenskap` | lexemet | ord |
| var står ordet, och övriga beslut? | `regel` | regeln | mönster |

**Två familjer.** Ordfamiljen växer med ordförrådet. Mönsterfamiljen växer inte
alls — det är det som gör något till ett mönster.

Kunskapen om former delas i mönster (`ändelse`, och `regel` för
ljudanpassningar) och undantag (`oregelbunden`). Var gränsen går avgörs av
förutsägbarhetsprincipen i 3.4.

### 3.3 `ord`

**Kortet klaras om användaren skriver någon form av rätt lexem.** Läromomentet är
att ordet hämtades ur minnet, och kortet är prerekvisit för alla formkort:

    strängen är en form av lexemet?
       nej -> ord föll; formkorten är OGRADERADE, de prövades aldrig
       ja  -> ord klarat; formkorten graderas mot cellen

Införs som glosa: betydelse → form.

### 3.4 Former: förutsägbarhetsprincipen

Hur ett ords former blir kort avgörs av en enda princip:

> **Ett ord får ett eget formkort precis där formen inte går att förutsäga ur det
> användaren redan kan: ordet självt, språkets regler och ordets andra kort.**

Ett ord utan formkort är regelbundet och kostar ingenting. Vad som räknas som en
regel följer av att ett mönster bara kan mätas genom att användaren skriver rätt
på ett ord hen inte har övat (6.4):

> **En regel är ett mönster som gäller för nya ord, och vars villkor syns i ordet
> eller i något användaren redan kan.**

Ett mönster som bara gäller en sluten grupp ord går aldrig att pröva på ett nytt
ord och kan därför inte mätas som mönster. Det räknas som kunskap om varje ord.
I oklara fall gäller det försiktiga valet, kort per ord: det kostar några kort
men påstår aldrig att användaren kan ett mönster hen inte kan.

#### Tre sorters formkunskap

| Kort | Vad det är | Exempel |
|---|---|---|
| `ändelse` | ändelsen för en cell i en klass | imparfait 1 sg för -er-verb: `-ais` |
| `regel` | en ljudanpassning som beror på stammens ljud, inte på klassen | tyskans `arbeit-e-st`, japanskans `飲ん-で` |
| `oregelbunden` | den minsta bit av ett ords form som inte går att förutsäga | `köper`, `gick`, `aur-`, `vais` |

**Ett ändelsekort gäller en cell, inte en sträng.** Presens `-e` och konjunktiv
`-e` är två kort: man kan kunna det ena utan det andra, och renderaren fattar
beslutet per cell (R3). Mängden är sluten och växer inte med ordförrådet. Dagens
`ordbok/ändelser.tsv` har 831 rader för sju språk, men tabellerna görs om i
steg 0.

**En ljudanpassning är ett eget kort bara när den beror på ljudet.** Beror den på
klassen hör den till klassens ändelser: svenskans `köpte` är er-klassens mönster,
ingen egen regel.

#### Klassen, och vilken som är standard

En klass som syns i ordet är ingen kunskap — franskans `-er` visar sin klass. En
klass som inte syns är det. `arbeta` och `köpa` slutar båda på `-a` men blir
`arbetar` och `köper`; `choisir` och `partir` slutar båda på `-ir` men blir
`choisissons` och `partons`.

Då gäller **den produktiva klassen som standard** — den klass nya ord får:
`googla → googlar → googlade`, och nya franska `-ir`-verb tar `-iss-`. Ett ord
som avviker får ett kort på den första form som visar avvikelsen, och resten
följer:

| Form | Går den att förutsäga? | Kort |
|---|---|---|
| `arbetar`, `arbetade` | ja — ar-verb är standard | inga |
| `köper` | nej — `köpa` ser ut som `arbeta` | ett |
| `köpte` | ja, när man vet att det heter `köper` | inget |
| `gick` | nej | ett |

Kunskapen *«köpa är ett er-verb»* behöver alltså ingen klasskod. Den visas med en
riktig form. Användaren får aldrig frågan vilken klass ett ord tillhör.

#### Enheten för ett undantag

**Kortet är den minsta bit som inte går att förutsäga:**

    avoir   aur-                      en bas som ger tolv celler    ett kort
    aller   vais · vas · va · vont    ingen gemensam bas            fyra kort

En bas som ger flera celler är ett kort; en form utan gemensam bas är ett eget
kort. Det motsvarar `stamgrupp ≥ 0` och `stamgrupp = −1` i `stammar.tsv`, men
följer nu av principen i stället för av stränganalysen.

#### Hur reglerna tas fram

Principen kräver att varje språks regler skrivs ner: klasserna med sina synliga
villkor, ändelserna per cell och ljudreglerna. De kontrolleras mekaniskt:

    generera alla former i databasen med reglerna
    varje form som reglerna inte ger är antingen
        ett undantagskort, eller
        en regel som saknas

Det är en kontroll av att reglerna stämmer, inte statistik, och en människa
granskar bara listan över avvikelser. Svenskan görs först, eftersom Julius kan
bedöma den; övriga språk tas fram ur standardgrammatiker och kontrolleras på
samma sätt.

**Basen härleds ur de renderade formerna, inte ur lemmasträngen.** Annars blir
lexem som böjs i två led fel (`sœur aînée` blev `sœurs aînée`), och flerordslexem
där det böjda ordet står först får inga kort alls (`être d'accord`).

### 3.5 `egenskap`

Kortet finns av ett enda skäl: **attributionen**. I `ett hus` och `en bil` syns
genuset inte på substantivet utan på artikeln och adjektivet. Skriver användaren
`en hus` är det genuskortet som föll — inte ordkortet, och inte artikelns form.

Gränsen finns redan i `sprak.db`. Det som ligger på **`Lexem`** (en rad per
språk) måste läras per språk och blir kort. Det som ligger på **`Koncept`** (en
rad för alla språk) följer av betydelsen och blir inget kort.

| Blir kort (`Lexem`) | Språk | Blir inte kort (`Koncept`) |
|---|---|---|
| `genus` | de, es, fr, it, sv | `valens` |
| `hjälpverb` | de, fr, it | `gradbarhet` |
| `prenominal` | es, fr, it | `räknebar` |
| `ja_adjektiv_typ` | ja | `semantik` |

`prenominal` varierar från ord till ord (16 av franskans 111 adjektiv står före
substantivet) och är därför en egenskap, inte en regel. `variant` skiljer
homonymer åt och blir inget kort. Franskan har 162 genuskort — ett per
substantiv.

### 3.6 `rektion` och `regel`

**`rektion`** är det ett ord *styr*: `helfen` tar dativ, `vouloir` tar infinitiv,
en viss konjunktion kräver konjunktiv. Nyckeln är det styrande ordet och slotten.

**`regel`** är ett beslut renderaren fattar — ordföljd (`v2`, `klitika_före`),
kongruens, elision. Varje `regel` är också en nivå (4.1).

### 3.7 Facit

**Ett korts facit är det `Uppslag.form(lexem, cell)` returnerar.** För
`travailler` i `subj_3sg` är det `travaille`; `que` och pronomenet hör till
andra kort. För ett flerordslexem är facit hela frasen: `suis d'accord`,
`veut dire`.

En cell renderaren inte slog upp har inte prövats. Står verbet i infinitiv sker
ingen personkongruens, och personcellerna graderas inte.

### 3.8 Täckningen

Kravet: **en mening får inte kunna bli fel utan att något kort bär skulden.**
Vad måste användaren veta för att skriva ett ord?

| # | Det som måste vetas | Kort |
|---|---|---|
| 1 | vilket ord | `ord` |
| 2 | ordets egenskap som syns på grannen | `egenskap` |
| 3 | vad det styrande ordet kräver | `rektion` |
| 4 | vilken cell — kongruens, bestämdhet, tempus | `regel`, när renderaren redovisat (8.3) |
| 5 | vilken sträng cellen har | se nedan |
| 6 | var ordet står | `regel` |

Givet rätt ord och rätt cell kan strängen bli fel på fem sätt:

| | Felet | Kort |
|---|---|---|
| a | kan inte mönstret | `ändelse` |
| b | kan mönstret, men ordet är ett undantag — `gådde` | `oregelbunden` |
| c | minns undantaget fel | `oregelbunden` |
| d | använde standardklassen på ett ord som avviker — `köpade` | `oregelbunden` på formen som visar klassen (`köper`) |
| e | missade en ljudanpassning — `arbeitst` | `regel` (3.4) |

**Aspekt och modus.** Valet mellan till exempel imparfait och passé composé är
ingen formfråga utan en fråga om vad meningen betyder. Det blir ett `regel`-kort
där renderaren väljer tempus utifrån aspekten, och uppgiften görs entydig genom
att källmeningen visar valet (6.5). Samma sak gäller modus som inte styrs av ett
ord.

Därmed finns inga kända hål i täckningen, förutsatt att renderarna redovisar sina
beslut (steg 1).

### 3.9 Oböjliga ord

Ett ord som inte böjs har **en enda form som gäller i alla celler**, och bara ett
`ord`-kort. Det är inget specialfall: paradigmet har bara en cell.

Japanskans `no`-adjektiv (いっぱい) och verbfrasadjektiv (疲れた) saknar i dag
former helt — se punkt 12.

---

## 4 · Nivåerna

### 4.1 Tre stegar

En mening får bara använda det som alla tre stegarna har låst upp.

| Stege | Grindar | Exempel |
|---|---|---|
| **Konstruktion** | vad meningen får innehålla | objekt, negation, tempus, bisats, wh-fråga |
| **Böjning** | vilka celler som finns | `pres_1sg`, `imperf_3pl` |
| **Realisering** | vilka beslut renderaren får fatta | `v2`, `klitika_före`, elision |

Konstruktionerna är desamma i alla sju språk, eftersom de hör till konceptlagret.
Dagens kod har 20 (`urval.ANVÄNDER`), sammanflätade med böjningen till en stege
på 22 steg (24 i japanskan).

Realiseringsstegen per språk, uppskattad:

| | ordföljd | övriga beslut | totalt |
|---|---|---|---|
| sv | 4 | 11 | 15 |
| en | 3 | 9 | 12 |
| de | 7 | 10 | 17 |
| fr | 3 | 22 | 25 |
| es | 4 | 24 | 28 |
| it | 3 | 23 | 26 |
| ja | 4 | 6 | 10 |
| | **28** | **105** | **133** |

Ordföljdsreglerna redovisas redan; `befolka.ORDFÖLJD` har 27, varav sex i
tyskan. De 105 övriga besluten fattas tyst i dag och kan räknas exakt först när
renderarna redovisar dem (steg 1).

### 4.2 Ordningen är en graf

Beroendena läses ur renderaren, som vet vad den slår upp när den tillämpar en
regel:

    perfekt        kräver  particip
    klitika_före   kräver  objektsform
    inversion_wh   kräver  whfråga
    satsklammer    kräver  hjälpverb

Grafen ger en **partiell** ordning: flera nivåer kan vara möjliga samtidigt, och
användaren väljer bland dem. «Föregående nivå» betyder nivåns föregångare i
grafen. Grafen måste vara acyklisk, och det kontrolleras när den byggs.

Böjningen ordnar sig på samma sätt: `pres_1pl` har inget att kongruera med förrän
`nous` finns.

### 4.3 Varje nivå öppnar minst ett kort

> **Invariant.** Varje nivå öppnar minst ett kort — en regel, en cell eller ett
> ord. Bryts den är nivålistan fel; det är inget tillstånd att hantera när
> programmet körs.

En konstruktion är själv **inget kort**. Att språk har objekt och frågor vet
användaren redan. Det som ska läras är hur *just det här* språket uttrycker dem,
och det blir kort:

    konstruktionen «objekt» öppnar …     och det som lärs är
      fr   klitika_före          regel   objektspronomen före verbet
           objektsformerna       celler
      de   dativ_före_ackusativ  regel   ordningen mellan två objekt
           akk · dat             celler

### 4.4 Grinden

> **En nivå kan öppnas när föregångarnas kort har mötts och gått rätt minst en
> gång, och den prövningen inte skedde i dag.**

- **Högst en ny nivå per dygn.** Ett kort som införs i dag kan inte räknas som
  lärt förrän i morgon, eftersom FSRS kortaste meningsfulla intervall är ett
  dygn. Regeln behöver alltså inget valt tal.
- **Nivån byts bara när passet startas.** Två knappar: *starta* och *starta på
  nästa nivå*. Planen räknas ut efter valet och ändras inte under passet.
- **Ingen grind för «materialet räcker».** Grinden ovan kräver ett lyckat möte,
  och ett möte kräver en mening som gick att bygga. Att en nivå skulle sakna
  material kan bara hända om den öppnar noll kort — och det förbjuder
  invarianten.

### 4.5 Upplåsning är inte införande

| | Frågan | Rätt svar? | Kostar |
|---|---|---|---|
| **Upplåsning** | vad *går* att lära nu | ja — grammatiken avgör | ingenting |
| **Införande** | vad *borde* läras nu | nej — ett omdöme (5.5) | minuter per dag |

Att låsa upp tio nivåer ger en kö av kort, inte tio nivåers arbete samma dag. Ett
kort som är upplåst men inte infört kan aldrig stå i en mening (R1).

---

## 5 · Dagspasset

### 5.1 Två faser

| Fas | Vad som händer | Nya kort |
|---|---|---|
| **1 · Introfasen** | dagens nya kort införs, en övning i taget | alla dagens nya |
| **2 · Meningsfasen** | meningar översätts och rättas | **inga** |

Vilka nya kort dagen har är bestämt innan passet börjar. När meningsfasen startar
är alltså varje kort som används infört, precis som R1 kräver.

### 5.2 Planen är en fråga, inte en tabell

| | Vad det är | Innehåller |
|---|---|---|
| **Dagens mål** | det som måste klaras | förfallna kort (FSRS) + dagens nya |
| **Det tillåtna** | vad en mening får använda | alla införda kort |

Vilka kort som är förfallna kan när som helst räknas fram ur `Repetition`. **Det
enda som lagras är repetitionshistoriken och dagens tilldelning av nya kort.**

Ett infört kort som inte är förfallet får användas i meningar. Det bokförs som
alla andra, och går det fel hamnar det i dagens again-hög.

### 5.3 Dagen tar slut när högarna är tomma

Passet är klart när **new-, again- och due-högarna är tomma.** Varje fel ger mer
arbete. Att varje kort alltid går att nå garanteras av budgeten (6.3).

Det finns i dag ingen utväg för ett kort som användaren inte klarar under dagen
(se 7.7).

### 5.4 Introfasen: hur ett kort införs

**En ruta per övning.** Användaren fyller i en sak i taget, aldrig en hel tabell:

    lära dig nu:  imperfekt, 1 sg

    regarder          sg              pl
    presens   1       regarde         regardons
              2       regardes        regardez
              3       regarde         regardent
    imperfekt 1       [            ]  ·
              2       ·               ·
    futurum                   (inte upplåst än)

    [   ]  det du lär dig nu        text  det du redan kan
      ·    upplåst, inte infört

En cell visas som text för *andra* ord först när den är klarad; tabellen visar
aldrig något användaren inte själv har visat att hen kan. Om rutan i bakgrunden
bokför ett eller två kort märker användaren inte.

| Kort | Övning |
|---|---|
| `ord` | glosa: betydelse → form |
| böjningscell | en ruta i paradigmtabellen |
| pronomen | hela paradigmet på en gång — pronomen är ett system, inte sex fakta |
| `egenskap` | tvåval, t.ex. vilket genus ordet har |
| `rektion` | vilket kasus verbet styr |
| `regel` | lektion med regeln och två exempel |

Ett mönsterkort införs med ett ord användaren redan kan, så att bara mönstret är
nytt. Senare *prövas* det helst på ett nytt ord (6.4).

**Dag ett.** Nivå 1 ger singularpronomenen — jag, du, han, hon, den, det —
eftersom `numerus` är en senare konstruktion. Vi, ni och de kommer med den.
Passet når sin första mening när användaren kan ett pronomen och ett verb.

### 5.5 Vilka nya kort: införandeordningen

Tidsratten bestämmer **hur många** nya kort dagen får. Ordningen bestämmer
**vilka**, i två steg:

    1.  finns ouppfyllda mönsterkrav   -> inför kort som uppfyller dem
    2.  annars                         -> semantisk frekvens

**Steg 1 — det meningarna saknar.** Generatorn väljer först ett verb. Verbets
mönster säger vad varje slot kräver *innan* något ord är valt: «subjektet ska vara
mänskligt», «objektet ska vara ett räknebart föremål». Kan kravet inte uppfyllas
med införda ord loggas kravet. Kandidaterna är de oinförda lexem som uppfyller
det, och de hittas genom en sökning i ordboken. Generatorn behöver aldrig se
oinförda kort.

    krav som inte gick att uppfylla    kandidater
    subjekt: mänsklig                  oinförda koncept med semantik «mänsklig»
    verb med komplementslot            oinförda modalverb
    (exempel, inte en mätning)

Metoden rangordnar alla korttyper på samma skala, rättar sig själv när kravet
börjar gå att uppfylla, och kan aldrig föreslå ett kort som inte finns. Den kräver
att felet i `urval.py:219` är åtgärdat (punkt 12).

*Sekundärsignal:* effektivt antal olika ord som fyllt en slot, 1/Σp², mätt ur
loggen. Den visar att en slot håller på att bli trång innan kravet slutar gå att
uppfylla.

**Steg 2 — det som är värt att kunna.** Grammatiken bestämmer vad som går att
lära; betydelsen bestämmer vad som är värt att lära först.

| `Koncept.källa` | Innehåll | Ordning |
|---|---|---|
| `bas_kärna` (170) | artiklar, pronomen, prepositioner, konjunktioner, räkneord, negation, frågeord, hjälp- och modalverb | följer nivåerna |
| `grundord` (566) | substantiv, verb, adjektiv, adverb | frekvens inom ordklassen |

Frekvenslistan är gemensam för alla språk och rangordnar **koncept, inte lemman**.
Därför uppstår inga problem med ord som har flera betydelser: `per_känna` och
`per_lukta` får var sin plats, trots att båda heter `sentir` på franska. Version
ett har samma ordning för alla användare. Japanskan ska kontrolleras för hand
innan listan används.

### 5.6 Två rattar

> **Tidsratten bestämmer vad dagen innehåller. Svårighetsratten bestämmer hur
> tätt det packas.**

Svårighetsratten *är* τ i budgeten (6.3); förvalet τ = 0,10 är härlett, och ratten
flyttar det. Högre τ ger färre och tätare meningar och ett kortare pass, men
oftare fall där rättaren inte kan avgöra vilket kort som föll. De förfallna korten
bestäms av FSRS och påverkas av ingen av rattarna.

---

## 6 · Meningsbygget

### 6.1 En giltig mening

En mening får ställas endast om:

1. varje kort den kräver är **infört** (R1)
2. varje regel den använder är **upplåst** i alla tre stegarna
3. den är **entydig** — källmeningen har exakt en korrekt översättning (R2, 6.5)
4. **båda språken kan uttrycka den.** Motorn har inga fasta källspråk — alla språk
   är likvärdiga — men alla språk har inte alla celler. Svenskans `vantar` har
   ingen singular, och då ställs meningen inte. Det är rätt beteende, inget fel.
5. inga två **svaga** kort styr samma ställe i meningen (6.2)

Två regler kan kräva former som inte går ihop. Då är meningen inte svår utan
omöjlig att bygga, och sökningen fortsätter.

### 6.2 Urvalsregeln

> **De svaga korten sprids över oberoende positioner.**

I praktiken: **bygg meningen av de kort som har lägst R, så många som budgeten
tillåter, och se till att varje svagt kort är det enda svaga på sin plats.**

Två villkor, samma tal sett från två håll:

| Villkor | Skyddar |
|---|---|
| få svaga kort: P(≥2 fel) ≤ τ | att felet går att lokalisera |
| varje svagt kort ensamt på sin plats | att felet går att knyta till ett kort |

Exempel: när genuskortet för `hus` är målet duger `ett hus`, där genuset syns på
ett ställe. `ett stort hus` duger inte — där styr genuset både artikeln och
adjektivet, och ett fel går inte att knyta till ett enda kort.

**Det här är hela urvalet.** Följande beteenden följer av regeln och får inga
egna regler:

| Beteende | Därför att |
|---|---|
| dagens mål blir täckta | förfallna kort har lägst R |
| antalet mål per mening | budgeten avgör (6.3) |
| variation i ordval | ett kort som just använts har R ≈ 1 och väljs sist |
| variation i meningens form | formen bärs av regelkort, som också har R |
| inga upprepningar | att upprepa är alltid det dyraste valet |
| varierande längd | de förfallna korten tar slut under dagen, så passet börjar med korta, täta meningar och slutar med långa, lätta |

Mål och utfyllnad är alltså inte två mekanismer. Målen är helt enkelt de kort som
har lägst R.

### 6.3 Budgeten

Det som går sönder när en mening packas för hårt är **rättningen**: med ett fel
syns i diffen var det sitter, med två gör det inte. Därför:

    P(≥2 fel i meningen) ≤ τ        τ = 0,10

τ = 1 − retentionsmålet 0,9, samma tolerans som fönstret i 7.6. Det är
svårighetsrattens förval.

Med R = 0,90 för förfallna kort och R = 0,99 för övriga:

    förfallna   utfyllnad   P(0 fel)   P(1 fel)   P(≥2 fel)
        1           5         0,856      0,138      0,006
        3           5         0,693      0,266      0,041
        5           5         0,562      0,340      0,098   taket
        6           5         0,505      0,362      0,132   över

**Budgeten är en avvägning, inte ett fast tak.** Samma villkor tillåter en kort
och svår mening eller en lång och lätt:

    förfallna    max utfyllnad    total längd
        0             53              53
        1             43              44
        3             24              27
        5              5              10

**Varje kort går alltid att nå:** en mening med ett förfallet kort och tio
utfyllnadskort har P(≥2) = 0,013.

**Längden begränsas av annat än budgeten.** En mening med 53 kort är orimlig, men
det är byggbarheten och tiden som hindrar den, inte budgeten. Längre meningar är
billigare per kort (mätt ur loggen):

    kort i meningen   median sek   sek/kort
         1               16,2         16,2
         2               17,5          8,8
         4               20,5          5,1
         8               24,9          3,1

Den fasta kostnaden per mening dominerar. **När påfyllningen ska sluta är den
öppna frågan i punkt 10.**

### 6.4 Att bygga mot ett kort

Att ett kort är upplåst och förfallet gör inte att det dyker upp av sig självt.
Franskans `inversion_wh` förekommer bara i wh-frågor, så när kortet är förfallet
måste generatorn **välja** att bygga en wh-fråga. Varje regel ska därför ha ett
byggvillkor — «meningen måste innehålla ett objektspronomen» — och den kunskapen
finns redan i renderaren. Dagens generator kan sikta på ord men inte på regler.

**Ett mönsterkort prövas bäst på ett nytt ord.** Ett mönster möts alltid genom ett
ord. Skriver användaren `bilarna` rätt vet man inte om hen kan `-rna` eller bara
har sett `bilarna` femtio gånger. Mötet säger något om mönstret i den mån ordets
eget kort är svagare än mönsterkortet.

### 6.5 Entydighetsfiltret

Entydigheten kontrolleras när meningen byggs, i samma filter som låsta regler.
Den kan inte kontrolleras i förväg, eftersom den beror på vad användaren har låst
upp: «jag arbetade» har en fransk översättning innan `imperf` är upplåst, och två
efteråt.

Filtret bygger på en **neutraliseringstabell** per språkpar: de skillnader
målspråket gör men källspråket inte gör.

    för varje neutraliseringspunkt i meningen:
        har målspråket mer än ett UPPLÅST alternativ?
            ja -> källmeningen måste visa vilket, annars förkastas meningen

För svenska → franska innehåller tabellen ungefär: aspekt i dåtid, modus som inte
styrs av ett ord, `man` → `on`, och de 16 svenska lemman som har flera
betydelser (`fråga`, `får`, `hälsa` …). För de flesta av dem avgör meningen ändå,
eftersom betydelserna har olika ordklass. Två införda ord för samma koncept i
målspråket — tyskans `glauben` och `finden` — är samma sorts fall och hör till
samma tabell.

**Aspekt och modus löses genom att källmeningen visar valet.** Är både
imparfait och passé composé upplåsta får en dåtidsmening bara ställas om den
innehåller ett ord som avgör valet: «jag arbetade **varje dag**», «jag arbetade
**igår**». Generatorn lägger till ett sådant ord när meningen annars vore
tvetydig. Användaren tränar då just det som är svårt — att läsa valet ur
sammanhanget. Tabellen behöver därför för varje sådan punkt en lista över vilka
ord i källspråket som pekar mot vilket alternativ.

Tabellen finns inte ännu (steg 5b).

### 6.6 Algoritmen

    F   förfallna kort som inte klarats i dag
    I   införda kort — det meningen får använda
    τ   budgeten

Ett steg: välj mål ur `F`, bygg en giltig mening (6.1) enligt urvalsregeln (6.2),
rätta svaret, och lägg tillbaka de kort som föll i `F`.

- **Problemet löses steg för steg.** Varje fel ger mer arbete, så dagen kan inte
  planeras i förväg. Varje mening väljs för sig.
- **Att välja girigt är korrekt, inte bara billigt.** Girigt urval kan i allmänhet
  lämna kort som ingen mening når. Här kan det inte hända: inga kort försvinner
  under dagen, och budgeten rymmer alltid en mening med ett enda mål.
- **Kostnaden ligger i att ta fram kandidater**, inte i att välja bland dem. Mätt:
  2 000 försök gav 1 692 kandidatmeningar med 727 olika kortmängder. Det som ska
  optimeras är hur få försök som räcker.

---

## 7 · Bedömningen

### 7.1 Varje möte bokförs

Varje gång ett kort prövas i en mening bokförs det — även om kortet inte var
förfallet och även om det redan mötts samma dag. Mätt i FSRS:

    50 rätt i följd, ingen vila                S =  2,31
    2 rätt med vila emellan                    S = 10,96
    2 rätt med vila, plus 49 extra ovanpå      S = 11,29

Extra repetitioner som **ersätter** vila skadar. Extra repetitioner som **läggs
till** kostar ingenting.

Möten där R ≈ 1 säger lite. De filtreras bort **när FSRS-parametrarna
optimeras**, inte när loggen skrivs — data kastas aldrig.

### 7.2 Betyg

`Again` och `Good` räknas fram ur diffen, och det räcker för FSRS. `Hard` och
`Easy` räknas aldrig fram, inte heller ur svarstiden. Längre fram får användaren
sätta dem själv.

`fsrs` tar bara hela betyg. Något «0,7 av ett Good» finns inte och ska inte
efterliknas (R4).

### 7.3 Vilket kort föll

Rättaren går igenom de tolkningar som stämmer med svaret, i två steg:

1. **Prerekvisit.** Kan man inte ordet kan man inte heller dess form. Föll `ord`
   är formkorten ograderade.
2. **Minsta förklaring.** Kan ett kort förklara alla avvikelser väljs det framför
   flera kort som felat oberoende av varandra. `ett stort hus` → `en stor hus`
   avviker på två ställen, och genuskortet förklarar båda.

**Finns bara en tolkning bokförs den. Annars bokförs ingenting och användaren får
inget besked om vilket kort det gällde** — kortet står kvar som förfallet. Det är
en verklig gräns för vad en diff kan avslöja, och varje sådant fall är en brist i
generatorn (R5).

Gränsen nås sällan. I den gamla loggen, mätt med tre regelkort, skilde sig 36 av
44 felaktiga meningar (82 %) från facit på exakt ett ställe, och ingen på tre
eller fler. En regel kan bara få skulden om den styr ett ställe där svaret
avviker. Talet ska mätas om med alla regelkort (punkt 11).

Ställ **inte** en isolerande fråga direkt efter ett tvetydigt fel. Användaren har
då just sett facit, och ett rätt svar skulle skjuta upp kortet längre än hen
klarar.

### 7.4 Rätt svar, men inte det som efterfrågades

Skriver användaren en korrekt översättning med ett annat ord än målkortet gör
systemet tre saker och inget mer: **godtar meningen, bokför inte målkortet, och
säger inte vilket ord som var tänkt.** Att säga det vore att avslöja svaret och
förstöra nästa mätning. Kortet står kvar som förfallet.

Är det andra ordet infört var uppgiften inte entydig, och filtret i 6.5 borde ha
stoppat den. Är det inte infört går det inte att förutse.

### 7.5 Mönster som blivit automatiska

- FSRS behandlar automatisering som hög stabilitet. Ett mönster som länge gått
  rätt får långa intervall och blir billigt av sig självt.
- När både mönstret och ordet sitter säger mötet ingenting nytt. Därför prövas
  mönster helst på nya ord (6.4).
- Faller en mening där mönsterkortet har högt R och ordkortet lågt, är ordet den
  troliga orsaken. Det får påverka nästa urval, men inte vad som bokförs (R4).

### 7.6 Kort som möts flera gånger om dagen

Franskans `le` finns i fyra meningar av fem, och för sådana kort säger
förfallodagen ingenting. De får i stället ett **fönster**: de tio senaste mötena.
Blir felen fler än toleransen blir kortet ett mål i dagens plan tills fönstret är
felfritt.

Fönstret är 1/(1 − 0,9) = tio möten, och tröskeln är retentionsmålets tolerans.
Mekanismen finns byggd och testad i dag och tas över som modell.

Om ett kort är **schemalagt** eller **övervakat** avgörs av hur ofta det faktiskt
mötts per dygn enligt loggen, inte av en simulering. Ett nytt kort är schemalagt
tills det visat sig mötas oftare än en gång om dagen. På så sätt sorterar
reglerna sig själva: `svo` möts ungefär tjugo gånger om dagen och övervakas,
`inversion_wh` möts sällan och schemaläggs.

### 7.7 Leech — uppskjutet

Byggs inte i version ett. När det byggs:

- **Gränsen kommer från FSRS:** `MAX_DIFFICULTY = 10.0`. När svårigheten nått taket
  och kortet ändå faller kan schemaläggaren inte justera mer.
- **Åtgärden är att granska kortet, inte att stänga av det.** Ett kort som ständigt
  faller är ofta fel avgränsat, och det tyder på att en regel i 3.4 saknas eller
  är fel för just det ordet.
- **Inom en dag finns i dag ingen utväg.** Dagen tar slut först när again-högen är
  tom, även om användaren inte klarar ett visst kort.

Inget går förlorat på att vänta, eftersom svårigheten redan lagras för varje kort.

---

## 8 · Koden

### 8.1 Vad som står kvar och vad som raderas

Repot behålls. **Den nya kärnan får inte importera något ur den gamla.** De gamla
filerna raderas i stället för att anpassas, eftersom det är det enda som säkert
hindrar att gammal kod lever kvar.

| Del | Rader | Beslut |
|---|---|---|
| renderarna, sju språk (`rendering/`) | 4 400 | står kvar — utökas med redovisade beslut |
| språkdatabasen och paradigmen | — | står kvar |
| ordboksbygget | 2 200 | står kvar |
| FSRS-integrationen | — | skrivs om, tunn |
| fönstret för övervakade kort | — | tas över som modell |
| näten och mätkorpusen | — | blir acceptanskrav för det nya |
| befolkning · schemaläggning · pass (`kort/`) | 3 800 | raderas |
| generator · urval · poäng (`generator/`) | 1 800 | raderas |
| rättningen | 1 200 | raderas |

Utanför sig själv importerar `rendering/` bara `generering.granskning` och
`kaikki_mappning.paradigm`. Ingen av dem raderas.

### 8.2 Vad som inte skrivs om

Undanhållandet, ett-betyg-per-dygn, medföljande kort, reservutgången,
nödfallstiern, tomgångsspärren och nödutgången fanns bara för att meningarnas
innehåll upptäcktes i efterhand. R1 tar bort orsaken, och därmed behovet.

### 8.3 Redovisning

Renderaren hämtar allt via `Uppslag`, och fyra anrop är instrumenterade:

| Anrop | Ger kort av typen |
|---|---|
| `form(lexem, cell)` | `ändelse` / `oregelbunden` |
| `egenskap(lexem, namn)` | `egenskap` |
| `rektion(koncept, slot, namn, värde)` | `rektion` |
| `ordföljd(regel)` | `regel` |

Allt som går förbi dem är osynligt. Den som läser `lexem["genus"]` direkt gör
genuskortet omöjligt att pröva.

**Att redovisa ett beslut** betyder att göra det till ett sådant anrop:

```python
self.u.ordföljd("inversion_wh")     # redovisat — syns
def eliderar(self, första, andra):  # inte redovisat — sker tyst
```

Anropet gör tre saker: regeln blir en nivå, ett kort och en kant i
beroendegrafen. Steg 1 i byggordningen är att göra så med varje beslut som i dag
fattas tyst.

---

## 9 · Byggordningen

    0   böjningsreglerna per språk         skrivs och kontrolleras mot alla former (3.4); svenskan först
    1   renderarna redovisar sina beslut   allt annat bygger på detta
    2   nivåstegarna och grafen            följer ur 1; kontrollera att grafen är acyklisk
    3   kortmodellen                       kräver 0; ändelser, ljudregler och undantag genereras ur reglerna
    4   dagspasset och införandet          kräver 2 och 3
    5   meningsbygget                      kräver 4
    5b  neutraliseringstabellerna          kräver 1; en per språkpar, med ord som avgör aspekt
    6   rättningen                         kräver 1
    7   lektioner och frekvenslista        parallellt
    7b  provsviten                         parallellt — finns inte i dag

**Steg 0 och 1 är oberoende och kan göras samtidigt.** Steg 0 kräver
språkkunskap, steg 1 kodarbete i renderarna.

**Steg 1 är det billigaste sättet att upptäcka om modellen håller.** När
renderarna redovisar går det att mäta hur många regler en mening faktiskt
använder, och alltså om attributionen fungerar med 133 regelkort i stället för
dagens tre. Håller den inte syns det innan något har raderats.

**Rent arbete, utan kvarstående beslut:** böjningsreglerna för sju språk,
renderarnas redovisade beslut, omkring 133 lektionstexter, den semantiska
frekvenslistan (japanskan för hand), en neutraliseringstabell per språkpar, och
datafelen i punkt 12.

---

## 10 · Öppen fråga

### När påfyllningen ska sluta

Budgeten tillåter långa meningar, och långa meningar är billiga per kort, men
något måste avgöra när en mening är lång nog. Det är den enda öppna parametern i
meningsbygget, och det enda stället där en smaksak — «ibland långa, ibland korta
meningar» — kan få avgöra. Blir det ett val ska det stå som ett val.

Frågan blockerar inget och besvaras bäst när meningsbygget finns och kan mätas.

---

## 11 · Acceptans

| Mått | I dag | Krav |
|---|---|---|
| kort i en mening som inte är införda | 4 | 0 |
| nya kort som införs utanför introfasen | 25 av 32 | 0 |
| andel kortmöten som bokförs | 13 % | 100 % |
| regler som renderaren använder utan att de är upplåsta | ej mätt | 0 |
| meningar med P(≥2 fel) > τ | ej styrt | 0 |
| mål som inte är ensamt svaga på sin plats | ej mätt | 0 |
| uppgifter med mer än ett rätt svar | ej mätt | 0 |
| former i databasen som varken reglerna ger eller ett undantagskort täcker | ej mätt | 0 |
| kortmöten där rättaren inte kan avgöra vilket kort som föll | ≤ 31 % av felen | mäts, ska minska |

**Det som bara kan prövas med användare.** Allt ovan följer av grundreglerna
eller av mätningar, utom:

| | Varför | Vad ett prov visar |
|---|---|---|
| ordförrådets ordning | bestäms utifrån; japanskan avviker | att de första hundra orden räcker till meningar |
| svårighetsrattens effekt | en modell av beteende | att högre τ ger färre och kortare pass |
| hur ofta rättaren inte kan avgöra | mätt med 3 regelkort | samma tal med 133 |
| lektionernas storlek | en funktion är kanske inte ett steg | syns bara hos användaren |

---

## 12 · Kända fel i data och kod

| Fel | Följd | Åtgärd |
|---|---|---|
| gränsen mellan stam och ändelse är dragen med stränganalys — tyskans helt regelbundna `arbeiten` har fem stamgrupper, svenskans dåtidsändelse är tom | regelbundna ord blir undantag | genereras om ur böjningsreglerna (3.4, steg 0) |
| japanskan har bara en verbklass (ichidan) | godan-verbens former lagras som hela former | steg 0 |
| italienskan saknar obestämd artikel i plural (`un · uno · una`) | 29 % av alla meningsspecar faller på italienskan | lägg till formerna |
| tyska fraslexem med adjektiv först (`älterer Bruder`) | 79 specar faller | böj båda leden, som `sœur aînée` |
| japanskans `no`- och verbfrasadjektiv (36 st) saknar former | orden kan inte renderas | en form per ord, giltig i alla celler (3.9) |
| enstaka tomma celler, t.ex. `sv/bröd best_pl` | enstaka specar faller | fyll i |
| `urval.py:219`: `träffar or kandidater` | ett semantiskt krav som inte går att uppfylla släpps tyst; meningar bryter mot verbets krav, och signalen i 5.5 går förlorad | logga i stället för att släppa kravet |
| `befolka.ORDFÖLJD` har 27 regler, tabellen i 4.1 räknar 28 | antalet i tyskan är osäkert | räknas om i steg 1 |
| ingen provsvit (inga `test_*.py`) | inget visar att attributionen fortfarande fungerar | steg 7b |

---

## Bilaga A · Förkastat, och varför

Idéer som har prövats och fallit. De står här så att de inte byggs igen.

| Idé | Varför den föll |
|---|---|
| `böjningsklass` som kort | facit är en klasskod som ingen skriver; 541 kort som aldrig mötts eller införts |
| `stam` och `form` som egna korttyper | en regelbunden stam går att förutsäga och är ingen kunskap; en oregelbunden är ett undantagskort, och stam och form är samma läromoment |
| nya kort under meningsfasen | bryter mot R1; det var så planens 7 nya kort blev 25 |
| budgeten Σ(1−R) ≤ 1,5 | mäter förväntat antal fel, inte om felet går att knyta till ett kort; tillåter meningar som blir fel 79 % av gångerna |
| egna regler för variation och utfyllnad | «senast sedd för längst sedan» och «lägst R» är samma sak; båda följer av urvalsregeln |
| en grind för att «materialet räcker» | följer redan av grinden i 4.4; ett datafel, inte ett tillstånd |
| alla nivåer, även konstruktioner, som kort | en konstruktion har inget facit |
| en plantabell per dag | förfallna kort kan räknas fram ur historiken |
| centralitet (`rang`) som ordning för ordförrådet | gynnar ord som passar i många meningar: `exister` blev franskans första verb |
| exponering simulerad med en samplare | talet finns i loggen, och det som kan mätas ska inte simuleras |
| efterfrågan räknad bland införda kort (per ordklass eller som koncentration) | ser bara det som redan finns, aldrig det som saknas |
| efterfrågan som antal kort som kan fylla en roll | skiljer inte ut något — varje franskt verb kan kombineras med alla 736 koncept |
| efterfrågan ur kandidater som förkastats | generatorn ser inte oinförda kort och kan inte förkasta på grund av dem |
| omprov, eller en isolerande fråga direkt efter ett tvetydigt fel | användaren har just sett facit; ger falska godkännanden |
| viktade betyg när attributionen är osäker | FSRS tar bara hela betyg; bryter mot R4 |
| `Hard` och `Easy` räknade fram ur svarstiden | avvisat (E3); betyget ska vara användarens eget, inte en gissning |
| undanhållande, ett-betyg-per-dygn, medföljande kort, nödutgångar | skadebegränsning för meningar vars innehåll upptäcktes i efterhand; R1 tar bort orsaken |
| ord + form: ett kort per lexem och cell | under R1 måste varje form införas innan den används, så en regelbunden form kostar en övning; enda utvägen är att räkna mönstret som kunskap, och då är det den uppdelade modellen. Bokför dessutom symptom i stället för orsaker |
| gränsen mellan stam och ändelse dragen med stränganalys | gjorde `arbetade` till ett undantag; gränsen följer av förutsägbarhetsprincipen (3.4) |
| en regelbundenhetsregel per språk, på en rad | för lite — det som behövs är språkets produktiva böjningsregler, kontrollerade mot alla former |
| böjningsklassen läses alltid ur lemmat | syns inte på svenska (`arbeta`/`köpa`) eller för franska `-ir`-verb (`choisir`/`partir`); att regeln träffade 165 av 174 franska verb dolde det |
| ändelsekort per sträng, där celler med samma ändelse slås ihop | klarar inte isoleringstestet: presens `-e` och konjunktiv `-e` är olika kunskap |
| aspektvalet utanför projektet, båda svaren godtas | användaren lär sig böja imparfait men aldrig när formen ska användas |
| en egen övningstyp för aspektvalet | bryter formen «en mening, ett facit»; källmeningen kan visa valet i stället |

---

## Bilaga B · Varför varje tal ska vara mätt

Under arbetet med specen gav resonemang fel svar sex gånger:

| Resonemanget sa | Mätningen visade |
|---|---|
| extra repetitioner i följd skadar | de kostar ingenting när vilan finns kvar |
| schemalagda kort möts högst en gång per dygn | 13 % möts oftare, ett av dem tolv gånger |
| 427 av franskans kort är genuskort | 162 |
| arbetsbördan beror på antalet kort | den fasta kostnaden per mening dominerar |
| exponeringen kan avgöra ordningen för ordförrådet | jämn fördelning, 50 nollor, `coûter` först |
| böjningsklasskorten bär kunskap | 541 kort, aldrig mötta |

Därför finns R6, och därför är varje tal i den här filen härlett, mätt eller
tydligt markerat som ett val.

---

*Historik: `git log -- paradigm/KÄRNAN.md`. Artifacten «Inget utanför dagens plan»
bygger på en äldre version och är inte aktuell.*
