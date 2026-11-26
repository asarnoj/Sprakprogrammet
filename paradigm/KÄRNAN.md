# Kärnan

Den fullständiga specifikationen av kärnan — korten, nivåerna, dagspasset,
meningsbygget och bedömningen — så som den ska byggas. Filen beskriver målet,
inte ändringar i den kod som finns.

> **Läge 2026-09-13.** Designen är avgjord utom frågorna i punkt 10, och ingen av
> dem blockerar bygget. Steg 0 är gjort för svenska och väntar på granskning
> (`ordbok/regelkontroll/sv.md`). Steg 1 är inventerat men inte byggt
> (`paradigm/TYSTA_BESLUT.md`). Nästa arbete är att bygga steg 1 och ta fram
> böjningsreglerna för övriga språk.

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
10. Öppna frågor
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

> En uppgift är giltig endast om varje målkort ingår i varje korrekt svar som
> går att bygga av användarens införda kort.

En mening har ofta flera korrekta översättningar: `leo` och `yo leo`, `igår läste
hon` och `hon läste igår`, `sade` och `sa`. Det är inget fel i sig. Felet uppstår
när användaren kan svara rätt utan att målet prövas — då mäter rättningen
ingenting. Tvetydighet i källmeningen är samma fall: «jag arbetade» har två
franska översättningar, och imperfektkortet finns bara i den ena.

Tillägget om införda kort behövs, annars skulle ett synonymt ord som användaren
aldrig lärt sig göra uppgiften ogiltig. Varianterna hittas i 6.5 och bedöms i 7.3.

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
    varje form som reglerna inte ger är
        ett undantagskort,
        en regel som saknas, eller
        ett fel i datan

Kontrollen sorterar själv ut datafel där formen bryter mot ett samband utan
undantag — en passiv som inte är aktiv form plus -s, en genitiv som inte är formen
plus -s. Resten granskar en människa, och bara listan över avvikelser. Det är en
kontroll av att reglerna stämmer, inte statistik.

**Kontrollen ensam räcker inte.** Formerna i databasen är genererade, och regler som
tas fram på samma sätt kan stämma med dem utan att någon av dem är rätt. Därför
finns tre lager till:

| Lager | Vad det fångar | Finns för |
|---|---|---|
| kaikki som oberoende facit | fel som reglerna och datan delar | de, es, fr, it, sv |
| AI-granskning av former och meningar | det kaikki saknar | alla språk |
| användarens flagga «facit är fel» (7.2) | det som slinker igenom | alla språk |

Svenskan är gjord: `python -m sprakprog.bojning.kontroll sv`. Slutna ordklasser —
pronomen, artiklar, possessiv, räkneord — ska också kontrolleras. Deras paradigm
har inga regler, så varje form är ett undantagskort.

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
homonymer åt och blir inget kort.

Två egenskaper saknas i tabellen men följer av samma kriterium, eftersom värdet hör
till ett ord och syns på ett annat: **reflexivt verb** (`skynda sig`, syns på
pronomenet) och spanskans **ser eller estar** (syns på kopulan). I dag läses båda
förbi instrumenteringen (`paradigm/TYSTA_BESLUT.md`, A8–A9).

**Genus får ett kort per substantiv, även där genuset syns på ordet** (`-tion`,
`-ung`, `-chen`). Förutsägbarhetsprincipen i 3.4 tillämpas inte här, och skälet är
införandet:

| | Utan mönsterkort | Löser FSRS det själv? |
|---|---|---|
| genus | ett kort per substantiv, som ändå införs med ordet | ja — kan användaren mönstret skjuts korten snabbt upp |
| former | ett kort per ord och cell, och alla måste införas (R1) | nej — en övning som måste göras försvinner inte för att den blir lätt |

FSRS rättar till det som *repeteras*, men inte det som måste *införas*. Att kunna
böja ett regelbundet verb man aldrig sett är vad det betyder att kunna böjningen;
att kunna genus för varje ord man lärt sig är allt som finns att kunna om genus.
Franskan har 162 genuskort.

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

**Två kända hål återstår**, båda inventerade i `paradigm/TYSTA_BESLUT.md` och båda
åtgärdas i steg 1: tio ord som renderaren skriver ut utan att de är lexem, och som
därför saknar `ord`-kort (`ne`, `est-ce que`, japanskans partiklar), och 26
läsningar av befintliga kort som går förbi instrumenteringen (`hjälpverb`,
`prenominal`, konjunktivrektion).

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

Realiseringsstegen per språk, inventerad i steg 1 (`paradigm/TYSTA_BESLUT.md`):

| | sv | en | de | fr | es | it | ja | summa |
|---|---|---|---|---|---|---|---|---|
| ordföljdsregler som redan redovisas | 4 | 3 | 6 | 3 | 4 | 3 | 4 | **27** |
| tysta beslut | 29 | 23 | 35 | 36 | 34 | 37 | 12 | **206** |

Specen uppskattade tidigare 105 tysta beslut. Hur många som blir regelkort beror på
frågorna i 10.2 — till exempel om skiljetecken är kort.

### 4.2 Ordningen är en graf

Beroendena **anges där beslutet fattas**, i redovisningsanropet (8.3). Provsviten
kontrollerar att renderaren aldrig slår upp något som regeln inte har angett. Att
i stället mäta beroendena genom att rendera exempelmeningar vore sampling, och ett
beroende som inte råkar dyka upp skulle missas.

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

> **En nivå kan öppnas när föregångarnas mönsterkort har införts, mötts och gått
> rätt minst en gång, och den prövningen inte skedde i dag.**

Mönsterkorten är de kort nivån själv öppnar — regler, ändelser, celler. Undantagskort
för enskilda ord räknas inte, annars skulle grinden bli långsammare för varje nytt
ord i ordförrådet.

- **Knappen öppnar alla nivåer vars grind är uppfylld.** Nivåer öppnas bara när passet
  startas: *starta* eller *starta med nya nivåer*. Planen räknas ut efter valet och
  ändras inte under passet.
- **Takten är användarens egen.** Grinden kräver att korten först har införts, och
  införandet styrs av tidsmodellen (5.5), som mäter hur fort användaren klarar sina
  kort. Den som kämpar låser upp långsammare, utan att något tal är valt.
- **Längs en kedja öppnas högst en nivå per dygn**, eftersom föregångarens kort måste
  ha klarats en tidigare dag. Nivåer som inte beror på varandra behöver inte vänta på
  varandra.
- **Ingen grind för arbetsbördan.** Att öppna en nivå lägger inga kort i passet, bara
  kandidater. Arbete tillkommer först när kort införs, och det taket sätter
  tidsmodellen redan. En grind som prövade arbetsbördan vid upplåsningen skulle
  aldrig spärra.
- **Ingen grind för «materialet räcker».** Grinden kräver ett lyckat möte, och ett
  möte kräver en mening som gick att bygga. Att en nivå skulle sakna material kan
  bara hända om den öppnar noll kort — och det förbjuder invarianten.

### 4.5 Upplåsning är inte införande

| | Frågan | Rätt svar? | Kostar |
|---|---|---|---|
| **Upplåsning** | vad *går* att lära nu | ja — grammatiken avgör | ingenting |
| **Införande** | vad *borde* läras nu | nej — ett omdöme (5.6) | minuter per dag |

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

**Att passet kan dra ut på tiden är ett medvetet val.** Det som räknas är arbete som
lyckas, inte nedlagd tid. Tidsratten styr hur mycket nytt som planeras (5.5), inte
när passet slutar, och ett kort som användaren inte klarar ligger kvar tills det
klaras.

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
| pronomen | hela paradigmet i följd, en övning per form — pronomen är ett system, inte sex fakta |
| `egenskap` | tvåval, t.ex. vilket genus ordet har |
| `rektion` | vilket kasus verbet styr |
| `regel` | lektion med regeln och två exempel |

Ett mönsterkort införs med ett ord användaren redan kan, så att bara mönstret är
nytt. Senare *prövas* det helst på ett nytt ord (6.4).

**En övning görs om tills svaret blir rätt.** Ett kort som misslyckas läggs sist i
introfasens kö. Det första svaret, som ges efter att kortet visats, är kortets
första FSRS-betyg; omtagen bokförs som vanliga möten (7.1).

**Dag ett.** Nivå 1 ger singularpronomenen — jag, du, han, hon, den, det —
eftersom `numerus` är en senare konstruktion. Vi, ni och de kommer med den.
Passet når sin första mening när användaren kan ett pronomen och ett verb.

### 5.5 Hur många nya kort

Beräkningen görs en gång, när passet startas och användaren har valt om nya nivåer
ska öppnas.

**Mätt ur loggen**
- tid per införandeövning, med omtag
- tid per förfallet kort som klaras, med de extra möten som fel kostar — talet visar
  också hur bra användaren är

**Härlett ur FSRS, med användarens egna parametrar**
- hur många repetitioner ett nytt kort ger upphov till, dag för dag framåt
- hur mycket arbete de redan införda korten ger, dag för dag framåt

> **Dagens antal nya kort är det största antal som gör att den förväntade
> arbetstiden ryms inom den inställda tiden varje dag framåt.**

Hur långt framåt behöver inte väljas: ett korts bidrag minskar när intervallen
växer, och beräkningen slutar när bidraget är mindre än ett enda kortmöte. Tar de
förfallna korten redan mer än den inställda tiden, till exempel efter några dagars
uppehåll, blir antalet noll.

Nivåns kort är inte tvingade att införas. De konkurrerar som alla andra kort, men
vinner nästan alltid, eftersom de är de mest efterfrågade (5.6).

### 5.6 Vilka nya kort: införandeordningen

    1.  efterfrågan   hur ofta ett meningsbygge stoppades av att kortet saknades
    2.  frekvens      skiljer kort med samma efterfrågan

**Steg 1 — efterfrågan, för alla korttyper.** Efterfrågan mäts i korten själva:

- **Saknas ett ord** som kan fylla en plats, är kandidaterna oinförda ord. Verbets
  mönster säger vad varje plats kräver *innan* något ord är valt — «subjektet ska vara
  mänskligt» — så generatorn behöver aldrig känna till oinförda ord i förväg.
- **Kräver en upplåst konstruktion en cell, regel eller egenskap** som inte är införd,
  är kandidaten just det kortet. Upplåsta kort vet generatorn om, eftersom nivågrafen
  säger att de är upplåsta.

Kandidaterna rangordnas efter **hur ofta generatorn stoppades för att just det kortet
saknades**, räknat i loggen från riktiga meningsbyggen. Ett allmänt kort — en regel,
en ändelse för en hel klass, ett hjälpverb — stoppar många byggen och kommer först;
ett enskilt ord stoppar få.

Därför behövs ingen särskild regel för när en nivås kort införs: de är de mest
efterfrågade i samma stund som nivån öppnas. Samma sak gäller slutna ordklasser:
hjälpverbet kommer när perfekt öppnas, eftersom perfektnivåns meningar inte går att
bygga utan det.

Metoden kräver att felet i `urval.py:219` är åtgärdat (punkt 12).

*Sekundärsignal:* effektivt antal olika ord som fyllt en plats, 1/Σp², mätt ur
loggen. Den visar att en plats håller på att bli trång innan kravet slutar gå att
uppfylla.

**Steg 2 — frekvensen skiljer lika.** Grammatiken bestämmer vad som går att lära;
betydelsen bestämmer vad som är värt att lära först.

| `Koncept.källa` | Innehåll | Ordning |
|---|---|---|
| `bas_kärna` (170) | artiklar, pronomen, prepositioner, konjunktioner, räkneord, negation, frågeord, hjälp- och modalverb | efterfrågan |
| `grundord` (566) | substantiv, verb, adjektiv, adverb | efterfrågan, sedan frekvens inom ordklassen |

Frekvenslistan är gemensam för alla språk och rangordnar **koncept, inte lemman**.
Därför uppstår inga problem med ord som har flera betydelser: `per_känna` och
`per_lukta` får var sin plats, trots att båda heter `sentir` på franska. Version ett
har samma ordning för alla användare.

**Frekvenslistan finns inte ännu.** `ordbok/nivålistor/grundord.csv` har en CEFR-nivå
per koncept (A1, A2, B1), men den är en bedömning och inte en mätning, och den ordnar
inte orden inom nivån. Den får användas tills en mätt frekvens finns, och är då ett
tillfälligt val. Japanskan ska kontrolleras för hand.

### 5.7 Två rattar

> **Tidsratten bestämmer vad dagen innehåller. Svårighetsratten bestämmer hur
> tätt det packas.**

Svårighetsratten flyttar budgeten i 6.3: tätare meningar ger färre meningar och ett
kortare pass. **Den får aldrig göra meningarna tätare än rättningen klarar.** Gränsen är
hur många samtidiga fel jämförelsen kan reda ut utan tvetydighet, och den mäts när
rättningen finns. Tills dess gäller förvalet τ = 0,10, och ratten kan bara göra
meningarna lättare. Så bryts R5 aldrig av ett val användaren gör.

De förfallna korten bestäms av FSRS och påverkas av ingen av rattarna.

---

## 6 · Meningsbygget

### 6.1 En giltig mening

En mening får ställas endast om:

1. varje kort den kräver är **infört** (R1)
2. varje regel den använder är **upplåst** i alla tre stegarna
3. varje målkort ingår i **varje korrekt svar** som går att bygga av användarens införda kort (R2, 6.5)
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

**Ett korts positioner är de utskrivna ord vars form kortet bestämde.** Renderaren
spårar det för varje ord (8.3), även när ord smälter ihop (`au` = `à` + `le`) och när
språket skrivs utan mellanslag. Två kort är oberoende när deras positioner inte
överlappar. Samma spår är rättningens underlag (7.3).

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
har lägst R. För övervakade kort är R andelen rätt i fönstret (7.6), så ett kort som
ses ofta men ofta blir fel blir också mål.

### 6.3 Budgeten

Det som går sönder när en mening packas för hårt är **rättningen**: med ett fel
syns i diffen var det sitter, med två gör det inte. Därför:

    P(≥2 fel i meningen) ≤ τ        τ = 0,10

τ = 1 − retentionsmålet 0,9, samma tolerans som fönstret i 7.6. Det är
svårighetsrattens förval, och ratten får flytta det upp till den gräns som mäts när
rättningen finns (5.7).

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

Den fasta kostnaden per mening dominerar. **När påfyllningen ska sluta är öppen
fråga 10.1.**

### 6.4 Att bygga mot ett kort

Att ett kort är upplåst och förfallet gör inte att det dyker upp av sig självt.
Franskans `inversion_wh` förekommer bara i wh-frågor, så när kortet är förfallet
måste generatorn **välja** att bygga en wh-fråga. Varje regel ska därför ha ett
byggvillkor — «meningen måste innehålla ett objektspronomen» — och den kunskapen
finns redan i renderaren. Villkoret anges i redovisningsanropet, bredvid regelns
beroenden (4.2, 8.3). Dagens generator kan sikta på ord men inte på regler.

**Ett mönsterkort prövas bäst på ett nytt ord.** Ett mönster möts alltid genom ett
ord. Skriver användaren `bilarna` rätt vet man inte om hen kan `-rna` eller bara
har sett `bilarna` femtio gånger. Mötet säger något om mönstret i den mån ordets
eget kort är svagare än mönsterkortet.

### 6.5 Entydighetsfiltret

R2 kontrolleras när meningen byggs, i samma filter som låsta regler. Det går inte att
kontrollera i förväg, eftersom resultatet beror på vad användaren har infört: «jag
arbetade» har en fransk översättning innan `imperf` är infört, och två efteråt.

**Filtret söker automatiskt, för vilket språkpar som helst.** Motorn behandlar alla
språk lika, så inga tabeller behöver skrivas för hand. Två sorters varianter söks:

| Sort | Hur den hittas | Exempel |
|---|---|---|
| samma källmening, olika innehåll | variera meningens innehåll längs de axlar där språk skiljer sig — tid och aspekt, singular eller plural för «du», referentens genus, lexemvarianter — och se vilka varianter som ger samma källmening | «jag arbetade» → imparfait eller passé composé |
| samma innehåll, olika korrekta målmeningar | renderaren räknar upp de former språket tillåter: utelämnbart subjekt, godtagna ordföljder, stavningsvarianter, sammandragningar | `leo` / `yo leo` |

Bara varianter som går att bygga av användarens införda kort räknas. Därefter:

    ingår varje målkort i varje korrekt målmening?   nej -> förkasta

Sökningen körs per kandidatmening och kostar några renderingar. Varianterna den
hittar är också de svar rättningen godtar (7.3).

**Aspekt och modus löses genom att källmeningen visar valet.** Är både imparfait och
passé composé införda får en dåtidsmening bara ha imperfektkortet som mål om den
innehåller ett ord som avgör valet: «jag arbetade **varje dag**», «jag arbetade
**igår**». Generatorn lägger till ett sådant ord när meningen annars vore tvetydig, och
användaren tränar då just det som är svårt — att läsa valet ur sammanhanget.

Vilka ord som avgör valet kan sökningen inte hitta, eftersom det hör till betydelsen
och inte till ett visst språk. Det märks därför en gång på konceptet och gäller för
alla sju språk: adverben har redan `tempuskrav`, och behöver ett **`aspektkrav`**
bredvid. Det finns inte ännu (steg 5b).

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

### 7.2 Betyg och omrättning

`Again` och `Good` räknas fram ur diffen. **Stavfel och accentfel räknas som fel** —
rättningen gissar inte vad användaren menade.

Efter meningen visas rättningen, och användaren kan **markera om**:

- ett underkänt kort som godkänt — ett stavfel, eller en korrekt variant som
  renderaren missade
- ett godkänt kort som `Hard` eller `Easy`
- facit som fel — en flagga som går till granskningen av datan (3.4)

Loggen sparar både diffens betyg och användarens. Diffens betyg är mätt och
användarens är användarens eget; båda är tillåtna enligt R4, och FSRS får
användarens. `Hard` och `Easy` räknas aldrig fram, inte heller ur svarstiden.

`fsrs` tar bara hela betyg. Något «0,7 av ett Good» finns inte och ska inte
efterliknas (R4).

### 7.3 Vilket kort föll

**Först väljs varianten.** Svaret jämförs med varje godtagen variant (6.5), och den som
har minst avvikelser är den användaren skrev. Korten i den varianten graderas; ett
kort som bara finns i en annan variant är ograderat, eftersom det inte prövades.

**Sedan knyts avvikelserna till kort.** Varje avvikande ord har de kort som bestämde
dess form, enligt renderarens spår (6.2). Rättaren går igenom de tolkningar som
stämmer med svaret, i två steg:

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

### 7.4 Korrekta svar som inte fanns bland varianterna

Två fall återstår när användaren skriver något korrekt som sökningen i 6.5 inte
räknade upp:

- **Ett korrekt ord som inte är infört.** Renderaren känner igen det som en form av ett
  annat lexem för samma koncept. Systemet godtar meningen, bokför inte målkortet och
  säger inte vilket ord som var tänkt — att säga det vore att avslöja svaret. Kortet
  står kvar som förfallet.
- **En korrekt variant som renderaren missade.** Diffen underkänner den, och användaren
  markerar om (7.2). Omrättningen loggas, så att varianten kan läggas till.

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

**För ett övervakat kort är R andelen rätt i fönstret.** FSRS bedömer ett kort som setts
femton gånger samma dag som mycket starkt, även när användaren gör fel, och
urvalsregeln (6.2) skulle då aldrig välja det som mål. Sju rätt av tio ger R = 0,7, och
kortet blir mål som alla andra svaga kort. För de här korten är det också en bättre
skattning än FSRS, eftersom förfallodagen inte betyder något för dem.

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
- **Inom en dag behövs ingen utväg.** Passet slutar först när again-högen är tom, och
  det är ett medvetet val (5.3).

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

Renderaren hämtar allt via `Uppslag`, och i dag är fyra anrop instrumenterade:

| Anrop | Ger kort av typen |
|---|---|
| `form(lexem, cell)` | `ändelse` / `oregelbunden` |
| `egenskap(lexem, namn)` | `egenskap` |
| `rektion(koncept, slot, namn, värde)` | `rektion` |
| `ordföljd(regel)` | `regel` |

Allt som går förbi dem är osynligt. Den som läser `lexem["genus"]` direkt gör
genuskortet omöjligt att pröva. **Inventeringen i steg 1 visar att de fyra anropen inte
räcker** (`paradigm/TYSTA_BESLUT.md`): 206 beslut fattas tyst, 26 läsningar av
befintliga kort går förbi anropen, och tio ord skrivs ut utan att vara lexem.

Steg 1 gör därför fem saker:

1. **`ordföljd` byter namn till `regel`.** Anropet har redan rätt form, men de flesta
   tysta besluten gäller kongruens, konstruktion och ljud, inte ordföljd.
2. **Förbigångarna lagas först**, eftersom de gör befintliga korttyper omätbara.
3. **De hårdkodade orden blir lexem**, så att de får `ord`-kort.
4. **Varje anrop anger regelns beroenden och byggvillkor.** Det ger nivågrafen dess
   kanter (4.2) och generatorn förmågan att bygga mot regeln (6.4).
5. **Renderaren spårar vilka kort som bestämde varje utskrivet ord.** Det är
   positionerna i 6.2 och rättningens underlag i 7.3.

Att redovisa ett beslut betyder att göra det till ett sådant anrop:

```python
self.u.regel("klitika_före", kräver=["objektsform"])   # redovisat — syns
def eliderar(self, första, andra):                      # inte redovisat — sker tyst
```

Anropet gör tre saker: regeln blir en nivå, ett kort och en kant i beroendegrafen.

---

## 9 · Byggordningen

    0   böjningsreglerna per språk         svenskan gjord, väntar på granskning; slutna ordklasser och sex språk kvar
    1   renderarna redovisar sina beslut   inventerat, inte byggt (8.3); allt annat bygger på detta
    2   nivåstegarna och grafen            följer ur 1; kontrollera att grafen är acyklisk
    3   kortmodellen                       kräver 0; ändelser, ljudregler och undantag genereras ur reglerna
    3b  datamodellen                       kort, möten, nivåer, dagens tilldelning, inställningar, kursens språkpar
    4   dagspasset och införandet          kräver 2 och 3; tidsmodellen (5.5) och efterfrågan (5.6)
    5   meningsbygget                      kräver 4
    5b  entydighetsfiltret                 kräver 1; variantsökningen och aspektkrav på koncept (6.5)
    6   rättningen                         kräver 1; spåret från ord till kort, och omrättningen (7.2)
    7   lektioner och frekvenslista        parallellt
    7b  provsviten                         parallellt — finns inte i dag
    7c  valideringen                       parallellt — kaikki, AI-granskning, användarflaggor (3.4)

**Steg 1 är det billigaste sättet att upptäcka om modellen håller.** När renderarna
redovisar går det att mäta hur många regler en mening faktiskt använder, och alltså
om attributionen fungerar med ett par hundra regelkort i stället för dagens tre.
Håller den inte syns det innan något har raderats.

**Rent arbete, utan kvarstående beslut:** böjningsreglerna för övriga sex språk,
renderarnas redovisning, en lektionstext per regelkort, den semantiska
frekvenslistan (japanskan för hand), aspektkraven på adverbialkoncepten, och
datafelen i punkt 12.

---

## 10 · Öppna frågor

Ingen av frågorna blockerar bygget.

### 10.1 När påfyllningen ska sluta

Budgeten tillåter långa meningar, och långa meningar är billiga per kort, men något
måste avgöra när en mening är lång nog. Det är den enda öppna parametern i
meningsbygget, och det enda stället där en smaksak — «ibland långa, ibland korta
meningar» — kan få avgöra. Blir det ett val ska det stå som ett val.

Frågan besvaras bäst när meningsbygget finns och kan mätas.

### 10.2 Frågor som väntar på Julius

- **Svenska böjningsregler** — fem frågor i `ordbok/regelkontroll/sv.md`. Den första,
  om utrala substantiv på konsonant har en standardklass, kan principen själv besvara:
  är både `-ar` och `-er` produktiva, blir pluralen ett kort per ord.
- **Renderarnas beslut** — tre frågor i `paradigm/TYSTA_BESLUT.md` punkt 6: om
  skiljetecken är kort, om ett språks fasta val (passé composé) är ett kort eller en
  del av lektionen, och om `vem`/`vad` är ett läromoment för en svensk.
- **Komparationens typ.** Om ett adjektiv kompareras syntetiskt (`större`) eller med
  `mer` syns inte i ordet och är kunskap per ord. Är det en `egenskap` — det syns på
  `mer`, alltså på ett annat ord — eller ett undantagskort?

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
| målkort som inte ingår i varje korrekt svar | ej mätt | 0 |
| former i databasen som varken reglerna ger eller ett undantagskort täcker | ej mätt | 0 |
| kortmöten där rättaren inte kan avgöra vilket kort som föll | ≤ 31 % av felen | mäts, ska minska |
| korrekta svar som underkänns och markeras om | ej mätt | mäts, ska minska |
| samtidiga fel som jämförelsen reder ut utan tvetydighet | ej mätt | mäts — sätter svårighetsrattens gräns (5.7) |

**Det som bara kan prövas med användare.** Allt ovan följer av grundreglerna
eller av mätningar, utom:

| | Varför | Vad ett prov visar |
|---|---|---|
| ordförrådets ordning | bestäms utifrån; japanskan avviker | att de första hundra orden räcker till meningar |
| svårighetsrattens effekt | en modell av beteende | att högre τ ger färre och kortare pass |
| hur ofta rättaren inte kan avgöra | mätt med 3 regelkort | samma tal med alla regelkort |
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
| 52 misstänkta datafel i svenska former — passiv utan -s, genitiv, genus | fel facit | `ordbok/regelkontroll/sv.md` |
| 26 läsningar av befintliga kort går förbi instrumenteringen (`hjälpverb`, `prenominal`, `ja_adjektiv_typ`, konjunktivrektion, infinitivmarkör …) | korten kan inte prövas | steg 1; `TYSTA_BESLUT.md` punkt 1 |
| tio ord skrivs ut utan att vara lexem (`ne`, `est-ce que`, japanskans partiklar) | inget kort bär skulden om de blir fel | steg 1; `TYSTA_BESLUT.md` punkt 2 |
| de romanska renderarna skriver alltid ut subjektspronomenet (`yo leo`) | varianten `leo` finns inte | variantsökningen (6.5) |
| `urval.py:219`: `träffar or kandidater` | ett semantiskt krav som inte går att uppfylla släpps tyst; meningar bryter mot verbets krav, och signalen i 5.6 går förlorad | logga i stället för att släppa kravet |
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
| exakt en korrekt målmening (tidigare R2) | för sträng: `leo` och `yo leo`, `sade` och `sa` är båda rätt; det som krävs är att målet prövas i varje korrekt svar |
| högst en ny nivå per dygn | följer redan av grinden längs en kedja; nivåer som inte beror på varandra har ingen anledning att vänta |
| grind för arbetsbördan när en nivå öppnas | spärrar aldrig: upplåsning lägger inga kort i passet, och införandet begränsas redan av tidsmodellen |
| att gruppera nivåer | en vald storlek utan grund (R6) |
| regelkort för genus | genus införs ändå med ordet, och FSRS skjuter snabbt upp det användaren redan kan |
| förlåtande rättning av stavfel och accenter | rättningen skulle gissa vad användaren menade; användaren markerar om i stället |
| beroendegrafen mätt genom att rendera exempelmeningar | sampling — ett beroende som inte råkar dyka upp missas |
| neutraliseringstabeller skrivna för hand per språkpar | 42 par, de flesta omöjliga att granska; sökningen hittar tvetydigheten automatiskt |
| FSRS:s R för övervakade kort | ligger nära 1 även när användaren gör fel, så kortet väljs aldrig som mål |

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
