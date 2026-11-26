# Kärnan

Den fullständiga specifikationen av kärnan — korten, nivåerna, dagspasset,
meningsbygget och bedömningen — så som den ska byggas. Filen beskriver målet,
inte ändringar i den kod som finns.

> **Läge 2026-09-14.** Designen är avgjord utom frågorna i punkt 10. Steg 0, 1 och 1b är
> gjorda för det första språkparet, svenska och engelska (8.3, 6.7). Kvar i dem är
> granskningen av komparationen och de godtagbara utfallen. Kortmodellen (steg 3) ger
> korten, och sammansättningen (steg 2) bygger meningar av kartan. Nästa steg är
> nivåerna (steg 4), som läser kraven ur de minsta meningarna.

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

Sju regler. Allt annat i specen följer av dem eller av en mätning.

**R1 · Axiomet**

> En mening får bara innehålla kort som är införda eller har presenterats i dag.
> Inga kort presenteras under meningsfasen.

Nya kort presenteras i dagspassets introfas och blir införda när de gått rätt i en
mening (5.1). Inget kort får komma in för att en mening ska gå ihop — det var så
planens 7 nya kort blev 25.

**R2 · Entydigheten**

> En uppgift är giltig endast om varje målkort ingår i varje korrekt svar som
> går att bygga av de kort meningen får använda.

En mening har ofta flera korrekta översättningar: `leo` och `yo leo`, `igår läste
hon` och `hon läste igår`, `sade` och `sa`. Det är inget fel i sig. Felet uppstår
när användaren kan svara rätt utan att målet prövas — då mäter rättningen
ingenting. Tvetydighet i källmeningen är samma fall: «jag arbetade» har två
franska översättningar, och imperfektkortet finns bara i den ena.

Tillägget om kort meningen får använda behövs, annars skulle en variant som bygger på
något användaren aldrig lärt sig göra uppgiften ogiltig. Varianterna hittas i 6.5 och
bedöms i 7.3.

**Synonymer är ett undantag.** Skriver användaren ett annat lexem för samma koncept ber
systemet om ett annat ord i stället för att underkänna (7.4). Efter ledtråden innehåller
varje korrekt svar målet, så R2 gäller för uppgiften som den då ser ut. Grammatiska
varianter som `leo` och `yo leo` omfattas inte av undantaget.

**R3 · Varje beslut renderaren fattar är ett kort**

> Allt renderaren avgör är något användaren måste kunna. Därför måste varje
> beslut gå att grinda och att pröva: det blir ett kort, och kortet öppnas av en
> nivå (4.1).

Det kräver att renderaren **redovisar** sina beslut (8.3). Ett beslut som sker
tyst kan varken låsas eller rättas.

**R4 · Mätt skrivs, härlett räknas, inget gissas**

> Om meningen var rätt eller fel är mätt. Vilket kort som bär skulden är
> härlett. Loggen får bara innehålla det mätta och det entydigt härledda.

Sannolikheter får styra vad som prövas härnäst — aldrig vad som skrivs. Ett undantag
är medvetet: **minsta förklaring** (7.3) väljer ett fel framför två oberoende, och det
vilar på budgeten. Att två fel i samma mening är osannolika är precis vad τ anger (6.3).

**R5 · Rättningen ska aldrig behöva gissa**

> Är ett svar tvetydigt eller ett fel omöjligt att knyta till ett kort, var
> uppgiften fel vald.

Varje sådant fall är en brist i generatorn, inte i rättaren. Vad rättaren gör när
det ändå händer står i 7.3.

**R6 · Inga valda tal**

> Varje tal i kärnan är härlett, mätt eller användarens val.

Retentionsmålet 0,9 är grunden; toleranser, fönster och trösklar härleds ur det.
Bilaga B visar varför regeln finns.

**R7 · Bygget svarar på vad som går att lära, dagen på vad som bör läras nu**

> Allt som är likadant varje dag räknas fram när kartan och nivåerna byggs. Vid
> körtid ställs bara de frågor vars svar beror på ANVÄNDAREN: vad hen kan väl,
> och vad hen redan sett i dag.

Sökningen är uttömmande (6.7), och det gör frågorna osymmetriska. Ett **ja** är
billigt: sökningen slutar när den hittat en mening. Ett **nej** kräver att hela
rummet gås igenom, och rummet växer med antalet tillåtna kort. Mätt 2026-09-27,
samma fråga om `ord:räkn_1` tre gånger:

| tillåtet | nejet kostar |
|--|--|
| bara kortets krav | 6 s |
| de sjuttio införda korten | 82 s |
| samma, plus dagens sexton valda | 821 s |

En körtidsfråga som *kan* svara nej är därför inte en kostnad utan en risk, och
den växer med kursen. Regeln tar bort risken i stället för att begränsa den: en
fråga bygget redan besvarat kan inte svara nej vid körtid, för den ställs inte.

Regeln kommer ur fyra fel funna samma dygn, alla samma sak — en körtidsfråga vars
svar bygget kunde ha gett:

- grinden (4.4) släppte upp kort ur en kravtabell som var falsk, och passet
  betalade ett nej per kort och dag,
- paketet (3.10) byggde en giltig övning för att få fram en minsta mening, fast
  beviset redan fanns,
- ordvalet (5.6) väntade på ord i en ordklass dagens kort inte kan nå,
- kandidatinsamlingen (5.1) tar ett tak meningar per kort som inte alltid finns.

**Gränsen är skarp, och det är det som gör regeln användbar.** En mening byggd av
kortets krav, kortet självt och fria ord är giltig **varje dag från och med den
dag kortet låses upp**: grinden öppnar kortet först när kravet är infört (4.4),
och de införda korten blir aldrig färre (5.1). Sådana meningar kan alltså räknas
fram en gång per språkpar och gälla kursen ut. Vad som beror på dagen är bara två
filter, och båda är mängdtest: är alla meningens kort tillåtna i dag (R1), och
har meningen redan ställts i dag (6.1 punkt 8).

Kvar vid körtid hör det som mäter användaren — lånekortens vikt (5.4), som vilar
på retrievability, täckningen per kort (5.6) — och urvalet: vilken mening som bär
vilket kort. Det är räkning över en ändlig tabell, inte sökning.

Hur många meningar per kort som ska räknas fram är ett tal, och lyder därför
under R6: det mäts, det väljs inte.

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

**Upplåsning.** Ett `ord`-kort är upplåst från början. Övriga kort öppnas av en nivå:
mönsterkort och kort för slutna ordklasser av sin egen nivå (4.1), och ett ords övriga
kort av den nivå som gör dem synliga — regeln som väljer cellen för ett undantag, regeln
där egenskapen syns för en egenskap, regeln som fyller slotten för en rektion. Vilken
nivå som öppnade ett kort lagras, eftersom grinden behöver det (4.4). Därefter är ett
kort bara ett kort och schemaläggs som alla andra.

### 3.2 Korttyperna

Typerna är inte valda. De är svaren på de frågor renderaren ställer när den
skriver ett ord, och den listan är sluten:

| Renderarens fråga | Kort | Nyckel | Familj |
|---|---|---|---|
| vilket ord betyder detta? | `ord` | lexemet | ord |
| vilken form — **läst** ur en tabell? | `oregelbunden` | lexemet (+ stamgrupp) | ord |
| vilken form — **byggd** ur ett mönster? | `ändelse` | ordklass, klass, cell | mönster |
| vad kräver det styrande ordet? | `rektion` | ordet + slotten | ord |
| vilken egenskap hos ordet syns på ett **annat** ord? | `egenskap` | lexemet | ord |
| var står ordet, och övriga beslut? | `regel` | regeln | mönster |

**Två familjer.** Ordfamiljen växer med ordförrådet. Mönsterfamiljen växer inte
alls — det är det som gör något till ett mönster.

Kunskapen om former delas i mönster (`ändelse`, och `regel` för
ljudanpassningar) och undantag (`oregelbunden`). Var gränsen går avgörs av
förutsägbarhetsprincipen i 3.4.

### 3.3 `ord`

**Kortet klaras om användaren skriver en form reglerna kan bygga av rätt lexem.**
Läromomentet är att ordet hämtades ur minnet, och kortet är prerekvisit för alla
formkort:

    strängen är en form reglerna kan bygga av lexemet?
       nej -> ord föll; formkorten är OGRADERADE, de prövades aldrig
       ja  -> ord klarat; formkorten graderas mot cellen

En form reglerna kan bygga är varje form i databasen och varje form som går att få ur
lexemet med någon cell, någon klass och någon ändelse, med eller utan ljudregler (3.4).
Det måste vara så, eftersom felaktiga former är just det formkorten ska fånga: `köpade`
är köpa med ar-klassens ändelse, så ordet klarades och undantagskortet `köper` föll
(3.8). `hsu` går inte att bygga av `hus`, och där föll ordet. Är strängen ett annat
lexem för samma koncept gäller 7.4.

Presenteras som glosa: betydelse → form.

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

**«Den första formen» är den första i nivåordningen** (4.2): cellen vars regel öppnas
tidigast. Öppnas flera celler av samma nivå spelar valet ingen roll för vad som kan
prövas — kräver en form ett undantagskort som inte är infört, väljs de som ett paket
(3.10) — och cellerna tas då i kartans ordning (6.7). Steg 0 använder i dag en
provisorisk cellordning, som byts när nivåerna finns.

#### Enheten för ett undantag

**Kortet är den minsta bit som inte går att förutsäga:**

    avoir   aur-                      en bas som ger tolv celler    ett kort
    aller   vais · vas · va · vont    ingen gemensam bas            fyra kort

En bas som ger flera celler är ett kort; en form utan gemensam bas är ett eget
kort. Det motsvarar `stamgrupp ≥ 0` och `stamgrupp = −1` i `stammar.tsv`, men
följer nu av principen i stället för av stränganalysen.

**Reglerna ger en tabell från form till kort.** För varje lexem och cell räknas ut
vilka kort formen består av — ordet, ändelsen, ljudreglerna, undantaget — och vilken
del av formen varje kort står för. Ett undantagskorts del är det som skiljer formen
från vad standardklassen hade gett: `aur-` i `aurai`, `-te` i `köpte` (mot `köpade`).
Kontrollen i steg 0 namnger undantaget med den första form som visar det; tabellen,
som räknas fram i steg 3, avgör vilken del av varje form kortet står för.
`Uppslag.form` redovisar ur tabellen (8.3), och rättningen graderar varje kort på dess
del (3.1, 7.3).

**Tabellen räknas fram, den skrivs inte** (`kortmodell/`). Böjningsreglerna namnger
klassen för varje ändelse de använder, efter klassens synliga villkor (`er`,
`neutrum_vokal`). Vilka undantag och ljudregler en form beror på räknas ut som
positionerna i 6.2: kortet tas bort, formerna förutsägs igen, och de som ändras hör
till kortet. `köper` ingår därför i `köpte`, `köpt` och `köps`, och ljudregeln i `kände`
också i `känt`. En form kan alltså ha flera formkort. Väljer reglerna ändelse efter
stammens ljud utan en namngiven ljudregel — neutrum `-t` efter vokal, annars `-et` —
blir varianterna olika ändelsekort, vilket är det försiktiga valet. Svenskan får 77
ändelsekort och 10 ljudregler, engelskan 10 och 6.

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
pronomenet) och spanskans **ser eller estar** (syns på kopulan). Svenskan redovisar
reflexivt verb (8.3); i övriga språk läses båda förbi instrumenteringen
(`paradigm/TYSTA_BESLUT.md`, A8–A9).

**Genus får ett kort per substantiv, även där genuset syns på ordet** (`-tion`,
`-ung`, `-chen`). Förutsägbarhetsprincipen i 3.4 tillämpas inte här, och skälet är
införandet:

| | Utan mönsterkort | Löser FSRS det själv? |
|---|---|---|
| genus | ett kort per substantiv, som ändå införs med ordet när genuset syns i en upplåst regel | ja — kan användaren mönstret skjuts korten snabbt upp |
| former | ett kort per ord och cell, och alla måste införas (R1) | nej — en övning som måste göras försvinner inte för att den blir lätt |

FSRS rättar till det som *repeteras*, men inte det som måste *införas*. Att kunna
böja ett regelbundet verb man aldrig sett är vad det betyder att kunna böjningen;
att kunna genus för varje ord man lärt sig är allt som finns att kunna om genus.
Franskan har 162 genuskort.

### 3.6 `rektion` och `regel`

**`rektion`** är det ett ord *styr*: `helfen` tar dativ, `vouloir` tar infinitiv,
en viss konjunktion kräver konjunktiv. Nyckeln är det styrande ordet och slotten.

**`regel`** är ett beslut renderaren fattar — ordföljd (`v2`, `klitika_före`),
kongruens, elision. Varje `regel` öppnas av en nivå (4.1).

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
därför saknar `ord`-kort (`ne`, `est-ce que`, japanskans partiklar), och 24
läsningar av befintliga kort som går förbi instrumenteringen i sex språk
(`hjälpverb`, `prenominal`, konjunktivrektion). Svenskan har inga kvar (8.3).

### 3.9 Oböjliga ord

Ett ord som inte böjs har **en enda form som gäller i alla celler**, och bara ett
`ord`-kort. Det är inget specialfall: paradigmet har bara en cell.

Japanskans `no`-adjektiv (いっぱい) och verbfrasadjektiv (疲れた) saknar i dag
former helt — se punkt 12.

### 3.10 Prövbara kort

> **Ett kort är prövbart om det kan vara mål i minst en giltig mening (6.1). Bara
> prövbara kort får införas.**

Utan regeln kunde ett kort införas, bli förfallet och aldrig klaras. Eftersom passet
slutar först när högarna är tomma (5.3) skulle passet då aldrig ta slut. Det gamla
systemet hade just det felet: onåbara kort.

**Två sorters prövbar.** Frågan ställs mot två olika mängder kort:

| | Mot vilka kort | Används till |
|---|---|---|
| **prövbart i princip** | alla kort i de öppna nivåerna och hela ordförrådet | nivåerna (4.1) — samma för alla användare |
| **prövbart nu** | användarens införda kort, plus de kort som redan valts för dagen | införandet (5.6) — beror på användaren |

Ett kort kan sakna en sådan mening på fyra sätt, och de fångas på olika ställen:

| Fall | Exempel | Fångas av |
|---|---|---|
| ingen öppen nivå använder kortet | svenskans supinum före perfekt | nivådefinitionen (4.1): nivån som öppnar kortet gör det prövbart i princip |
| en korrekt variant saknar kortet (R2) | spanskans subjektsform `yo`, som alltid kan utelämnas | kontrollen före införandet |
| kortet kräver ett kort som inte är infört | imperfekt utan ett ord som «chaque jour» | kontrollen före införandet |
| ett nytt kort gör ett gammalt oprövbart | imperfekt införs, och passé composé kräver nu ett ord som «igår» | omkontrollen vid införandet |

**Kontrollen före införandet:** generatorn försöker bygga en giltig mening med kortet
som mål, av införda kort och dagens redan valda. Lyckas det sparas meningen som kortets
**bevis**. Går det inte väntar kortet.

**Kort som bara kan prövas tillsammans införs som ett paket.** Första dagen är inget
kort prövbart ensamt: ett verb kan inte vara mål utan ett subjekt, och ett pronomen inte
utan ett verb.

**Paketet är de oinförda korten i en minsta mening för kortet** (avgjort 2026-09-14). Det
räknas som kraven i 4.2, men över alla kort, ord inräknade, och med de införda korten
tillåtna: en mening med kortet hittas, och ett oinfört kort i taget förbjuds tills inget
går att ta bort. Grafen räcker inte till paketet, eftersom ord inte har kanter där — och
första dagen kräver pronomenet ett verb, som då aldrig kom med. Paketet väljs helt eller
inte alls. Kan kortet prövas med flera paket jämförs de med sin nya täckning per kort
(5.6). Ett kort som många andra kräver finns i många paket och vinner därför ofta, så
efterfrågan syns utan ett eget mått. Hur alternativen söks utan att hela kartan gås
igenom för varje kandidat avgörs i steg 6.

**Omkontrollen vid införandet:** varje infört korts bevis prövas mot entydighetsfiltret
(6.5) igen, nu med det nya kortet. Klarar beviset sig är kortet fortfarande prövbart.
Faller det söks ett nytt bevis, och hittas inget väntar det nya kortet. Någon
förteckning över vilka kort som konkurrerar behövs inte: filtret hittar det själv, och
det kostar en filtrering av en sparad mening per infört kort.

**Ett nytt kort får aldrig göra ett annat kort oprövbart för gott** (avgjort 2026-09-14).
Väntar ett kort för att ett infört kort står i vägen, och finns ingen mening som skiljer
dem, väntar det för alltid — och varje nivå som kräver det förblir stängd. Det är därför
ett fel i programmet och ingen väntan: provsviten (steg P3) kontrollerar att varje kort
som väntar på det sättet blir prövbart igen, och märkningen av källmeningen (6.5) tar
bort de flesta fallen.

Kontrollen kommer fram till rätt sak av sig själv. `yo` blir aldrig ett kort, och det
stämmer: den som aldrig skriver `yo` talar korrekt spanska. Pronomenet prövas genom
sina andra former (`mí`, `me`).

#### Invarianten är sträng

> **Varje kort i dagsplanen är prövbart.** Ett brott är ett fel i programmet, aldrig
> ett tillstånd att leva med.

Tre saker gör brott omöjliga, inte bara ovanliga:

1. **Beviset visar att en mening finns.** Det meningarna får använda ändras inte under
   meningsfasen, så beviset gäller hela dagen. Sökningen är exakt (6.7) och hittar därför
   en mening för varje kort som har ett bevis — beviset är kontrollen av det, ingen reserv.
2. **Kontrollen körs varje gång något kan ha ändrats.** Ett infört kort kan bli
   oprövbart på två sätt: ett nytt kort införs (omkontrollen ovan), eller koden eller
   datan ändras — en ny renderare, en rättad böjning. När en ny version tas i bruk
   kontrolleras alla införda kort innan passet startar.
3. **Provsviten simulerar kurser** (steg P3). Simulerade användare svarar slumpvis
   tills kursens alla nivåer är öppna, och invarianten kontrolleras varje dag. Det är
   där omöjligheten visas, innan något släpps.

Budgeten kan inte orsaka ett brott: när ingen mening ryms tas reservstegen i 6.3.

**Om den ändå bryts** — vid passets start, eller när sökningen under dagen inte hittar
någon giltig mening för ett kort som har ett bevis:

- **En felrapport skrivs:** kortet, de införda korten, varje byggförsök och varför det
  föll (ett saknat kort, ett byggvillkor, en variant som saknade kortet), och
  vad som ändrats sedan kortet senast var prövbart (vilket kort som infördes, vilken
  version).
- **Kortet sätts i karantän:** inget betyg, FSRS-tillståndet orört, inte klarat. Passet
  kan ta slut utan det.
- **Karantänen hävs bara när felet är rättat** och kortet klarar kontrollen igen. Då är
  kortet förfallet som vanligt.

Karantänen är felhantering, inte förlåtelse: inget räknas som klarat, och varje fall är
en rapport som ska leda till en rättelse.

#### När reglerna eller datan ändras

Reglerna och datan ändras medan kurser pågår, med flit: en granskningsfråga besvaras,
eller en användarflagga leder till en rättelse (3.4). Då kan kort försvinna — en form
visar sig gå att förutsäga — eller tillkomma. Kortets identitet är dess nyckel (3.2):

- **Ett kort som försvinner** behåller sin historik men används inte längre.
- **Ett kort som tillkommer** är inte infört. Kräver ett infört kort det nya, presenteras
  det nya i nästa introfas, före andra nya kort och oavsett tidsmodellen.
- **Resten fångar kontrollen vid ny version** (punkt 2 ovan), som räknar med dagens
  presenterade kort.

---

## 4 · Nivåerna

### 4.1 Vad en nivå är

> **En nivå är det minsta steg som gör minst ett nytt kort prövbart i princip (3.10).**

Nivåerna täcker varje kunskapsmoment som inte redan bärs av ett ord: varje grammatisk
regel renderaren förhåller sig till. Det gamla systemet tog många små regler för
givna, och då blir språket svårt att lära genom programmet. Därför finns **många
nivåer, en för varje litet steg.**

Definitionens två delar behövs båda:

- **«Minsta»** ger ett steg per regel och inga grupper som valts efter känsla (R6).
- **«Prövbart»** hindrar steget från att bli för litet. Svenskans supinum och perfekt
  kan bara prövas tillsammans och blir därför en nivå. Den grupperingen är tvingad av
  prövbarheten (3.10), inte vald.

**Nivåerna räknas fram ur grafen.** Nivåernas kort är de som inte växer med
ordförrådet: mönsterkorten och korten för slutna ordklasser — pronomen, artiklar,
possessiv, räkneord. Mellan dem går kraven i 4.2. Kort som kräver varandra, direkt eller
genom andra, kan bara prövas tillsammans. **En nivå är därför en grupp kort som kräver
varandra åt båda håll** — en stark komponent i grafen — och ett kort som inte ingår i
någon sådan grupp är en egen nivå. «Minsta steg» blir en algoritm och ingen bedömning.

Alla nivåer är av samma sort: de öppnar kort. En
**konstruktion** — objekt, negation, fråga — är varken nivå eller kort. Den hör till
meningens innehåll, som är detsamma i alla språk, och kan användas i en mening när de
regler och celler den behöver är upplåsta i språket. Samma konstruktion blir därför
tillgänglig vid olika tidpunkter i olika språk.

Hur många nivåer det blir avgörs av renderarna. Inventeringen i steg 1
(`paradigm/TYSTA_BESLUT.md`) räknade reglerna:

| | sv | en | de | fr | es | it | ja | summa |
|---|---|---|---|---|---|---|---|---|
| ordföljdsregler som redan redovisas | 4 | 3 | 6 | 3 | 4 | 3 | 4 | **27** |
| tysta beslut | 29 | 23 | 35 | 36 | 34 | 37 | 12 | **206** |

Till det kommer böjningens celler och de slutna ordklasserna. Det exakta antalet nivåer
blir känt i steg 4, och ofta öppnas flera på en gång. För användaren blir nivån främst
ett mått på framsteg;
takten sätts av hur många kort som införs (5.5). Hur många regler som blir kort beror
på frågorna i punkt 10 — till exempel om skiljetecken är kort.

### 4.2 Ordningen är en graf

Kraven **läses ur kartan** (6.7): ett korts krav är de kort som finns i dess minsta
meningar. Kartan går igenom varje del av renderaren uttömmande, så inget krav kan
missas. Att i stället rendera exempelmeningar vore sampling, och ett krav som inte
råkar dyka upp skulle missas.

    klitika_före   kräver  objektsform
    inversion_wh   kräver  whfråga
    satsklammer    kräver  hjälpverb
    pres_1pl       kräver  nous

Ett krav på en konstruktion (`whfråga`) betyder de kort konstruktionen kräver i språket.

**Kraven är de minsta kortmängderna** (avgjort 2026-09-14). För ett nivåkort räknas, i
varje giltig mening där kortet syns, mängden av meningens övriga nivåkort. Kortets krav är
de mängder som ingen annan av mängderna ryms i. De kortaste meningarna räcker inte: den
kortaste med objektsformen `mig` är «Se mig!», och då skulle objektsformen kräva
imperativ, fast «Barnen ser mig» prövar samma kort utan den.

- **Bara beslut som syns räknas** (6.2). «I walked» visar ingen kongruens, så preteritum
  kräver den inte.
- **Ordkort räknas inte**, eftersom ord är upplåsta från början (3.1). Nivåkorten är
  mönsterkorten och korten för slutna ordklasser (4.1).
- **Kraven räknas per språkpar**, med entydighetsfiltret och märkningen (6.5), och med
  bara nivåns egna kort och föregångarnas tillåtna. Om ett kort kan prövas beror på vad
  källspråket kan visa och på vilka varianter som finns, så nivåerna är desamma för alla
  användare av samma kurs men inte för alla kurser med samma målspråk.
- **Har kortet flera minsta mängder väljs en**, efter täckningen nedan. Tills
  frekvenserna finns (steg P2) söks bara en: den som krymps fram ur den första mening
  sammansättningen hittar. Alternativen och valet mellan dem kommer med frekvenserna.
  Att bevisa att inga fler minsta mängder finns kräver att nästan hela kartan gås igenom
  för varje kort, och det lönar sig först när valet kan göras efter täckning. Till dess
  kan ett krav bli ett sämre alternativ: objektsformen kan komma att kräva imperativ,
  eftersom «Se mig!» är den första meningen.

**Mängderna hittas med frågor som sammansättningen besvarar uttömmande:** finns en giltig
mening som prövar kortet, byggd av bara de här nivåkorten? Meningarna är oändligt många —
en bisats kan innehålla en bisats — men ingen del behöver upprepas mer än en gång längs en
gren, eftersom satsen i bisatsen i bisatsen kan kortas utan att något kort tillkommer. Då
är det ändligt många sammansättningar att gå igenom, och ett nej är ett bevis.

1. **En mening hittas**, och dess nivåkort är en första mängd.
2. **Mängden krymps**: ett kort i taget förbjuds, och går det fortfarande att bygga en
   mening tas den nya, mindre mängden. När inget kort går att ta bort är mängden minst.
3. **Nästa minsta mängd** (med frekvenserna, se ovan) måste sakna minst ett kort ur varje
   mängd som redan hittats, så frågorna upprepas med ett sådant kort förbjudet tills inga
   nya mängder finns.

**Version 1 av nivåerna hoppar över krympningen** (avgjort 2026-09-19). Steg 1 är en snabb
fråga: sökningen letar tills den hittar en mening och slutar där, ungefär en sekund per
kort. Steg 2 är den dyra: för varje kort i mängden ska ett nej bevisas, och ett nej kräver
att allt som går att bygga gås igenom. Mätt 2026-09-17, med förklaringarna: tolv timmar
gav 43 av engelskans 214 nivåkort och 5 av svenskans 323. Kravet är därför tills vidare
nivåkorten i den första mening sökningen hittar, utan krympning.

- **Invarianten håller.** Kortet går att pröva när kravet är infört, och meningen sparas
  som dess bevis (3.10).
- **Priset** är ordningen: kravet kan innehålla kort som inte behövdes, och kortet kommer
  då senare i kursen än nödvändigt.
- **Krympningen är en senare förbättring**, som körs per kurs när resten fungerar. Den
  ändrar bara ordningen, aldrig vad som går att pröva.

Vilka beslut som syns avgör spåret på den riktiga meningen (8.3), inte kartan. Kartan
kan inte avgöra det själv: om «Blood exists» hade kunnat vara en uppmaning beror på
subjektets ord, och ett beslut som syns i en del kan försvinna när en annan del vägrar.
Två ord med samma formkortsmönster, samma celler, samma sammanfallande former och samma
egenskaper ger samma kort i samma mening, så ett av dem prövas.

**Ett nej går fort med förklaringar** (avgjort 2026-09-14). Utan dem renderas varje
ordval i varje sammansättning, och de flesta faller av samma skäl: ett förbjudet val
syns, vilka ord som än står där. För engelskans «the» utan valet `bestämd_artikel` blev
det omkring 210 renderingar i var och en av 50 484 sammansättningar, timmar för en enda
fråga (mätt 2026-09-14). En mening som faller på ett förbjudet val lämnar därför ett
bevis. Beviset består av tre delar:
- den innersta del kring beslutet som lämnar tillbaka lika mycket när beslutet tvingas
  till ett annat utfall
- ett ord i delen som då ändras
- allt delen läste: svaren om orden på dess platser och värdena i specfälten.

Varje sammansättning med samma del hoppas över när varje ord som kan stå på delens
platser uppfyller beviset. Det gäller också i senare frågor där samma kort är förbjudet.
Beviset vilar på kartans egna förutsättningar (6.7): renderaren läser ord bara genom
uppslaget, och en del påverkar resten av meningen bara genom vad den lämnar tillbaka.
Därför är det exakt: det som hoppas över hade fallit. I kontrolläget hoppas inget över.
Allt som ett bevis täcker renderas då ändå, och sökningen stannar om en sådan mening går
att bygga (P3). Med förklaringarna tog engelskans första nivåkort 69 s.

**Krav med flera alternativ.** Många krav kan uppfyllas av flera kort. Franskans `je`
kräver ett verb i 1 sg, som kan ha vilken klass ändelse som helst, och varje sådan
ändelse kräver `je`. Blev kravet en kant till varje alternativ skulle alla kräva
varandra, och `je` och alla klassers ändelser bli en enda nivå. Därför:

- **Ett krav som ordförrådet kan uppfylla är alltid uppfyllt.** Subjektet kan vara vilket
  substantiv som helst, och ord är upplåsta från början (3.1). Det blir ingen kant.
- **Övriga krav med flera alternativ blir en kant till ett av dem**: det som ger mest
  täckning per kort (5.6), räknat med hela ordförrådet. Vid lika avgör kartans
  ordning. Tills frekvenserna finns (steg P2) är täckningen okänd, och då blir kanten den
  minsta mängd som krymps fram ur sammansättningens första mening.

**Krav som följer av entydigheten står också i grafen.** När två kort konkurrerar om
samma val, som imparfait och passé composé, kan vart och ett bara prövas i en mening med
ett ord som avgör valet (6.5). Aspektregeln kräver därför något ord med `aspektkrav`.
Annars vet införandet inte att ordet saknas, och kortet kan vänta hur länge som helst.

En nivå kräver en annan när dess kort kräver den andras. Mellan nivåerna är grafen
**acyklisk av konstruktion**, eftersom kort som kräver varandra redan hör till samma
nivå (4.1). Den ger en **partiell** ordning: flera nivåer kan vara möjliga samtidigt,
och alla vars grind är uppfylld öppnas (4.4).

**Den första nivån följer av definitionen.** Nästan varje regel kräver att en enkel
mening redan går att bygga, så den första nivån blir de kort en enkel mening kräver: ett
subjektspronomen, presens och grundordföljden. Verbet är ett ord och upplåst från början
(3.1). Nivåer som negation och fråga kräver den och öppnas efter.

### 4.3 Varje nivå öppnar minst ett kort

> **Invariant.** Varje nivå öppnar minst ett kort, och varje kort den öppnar är
> prövbart i princip när nivån och dess föregångare är öppna. Bryts det är nivålistan fel; det är
> inget tillstånd att hantera när programmet körs.

Att språk har objekt och frågor vet användaren redan. Det som ska läras är hur *just
det här* språket uttrycker dem, och det blir kort:

    för att «objekt» ska kunna användas …   och det som lärs är
      fr   klitika_före          regel      objektspronomen före verbet
           objektsformerna       celler
      de   dativ_före_ackusativ  regel      ordningen mellan två objekt
           akk · dat             celler

### 4.4 Grinden

> **En nivå kan öppnas när föregångarnas kort infördes en tidigare dag.**

Infört betyder att kortet har gått rätt i en mening (5.1); att klara introövningen
räcker inte. Föregångarnas kort är nivåkorten i 4.1 — de som inte växer med ordförrådet, oavsett
korttyp: regler, ändelser, `nous`. Ett enskilt ords kort räknas inte, annars skulle
grinden bli långsammare för varje nytt ord i ordförrådet.

- **Knappen öppnar alla nivåer vars grind är uppfylld.** Nivåer öppnas bara när passet
  startas: *starta* eller *starta med nya nivåer*. Planen räknas ut efter valet och
  ändras inte under passet.
- **Takten är användarens egen.** Grinden kräver att korten först har införts, och
  införandet styrs av tidsmodellen (5.5), som mäter hur fort användaren klarar sina
  kort. Den som kämpar låser upp långsammare, utan att något tal är valt.
- **Längs en kedja öppnas högst en nivå per dygn**, eftersom föregångarens kort måste
  ha införts en tidigare dag. Nivåer som inte beror på varandra behöver inte vänta på
  varandra.
- **Ingen grind för arbetsbördan.** Att öppna en nivå lägger inga kort i passet, bara
  kandidater. Arbete tillkommer först när kort införs, och det taket sätter
  tidsmodellen redan. En grind som prövade arbetsbördan vid upplåsningen skulle
  aldrig spärra.
- **Ingen grind för «materialet räcker».** Grinden kräver ett lyckat möte, och ett
  möte kräver en mening som gick att bygga. Att en nivå skulle sakna material kan
  bara hända om den öppnar noll kort — och det förbjuder invarianten.

#### Byggd 2026-09-27, och tre fel som kom ur samma sammanblandning

`nästa_nivå` prövade bara MÄNGDEN införda kort, aldrig vilken dag de infördes. Nivå 2
öppnade en minut efter att nivå 1:s kort införts, och en användare tog fyra nivåer på
fem minuter. Dagsvillkoret i den första raden ovan är alltså hela grinden: med det gäller
«högst en nivå per dygn längs en kedja» av sig själv, och en oberoende nivå får ändå
öppna samma dag — mätt: `regel:val/satsart/imperativ` öppnar bredvid nivå 1, vilket är
riktigt, eftersom den inte beror på den.

**Planen lades per `n`-tryck i stället för per dag**, så «dagens plan» var i själva verket
«den här nivåns plan». Raden ovan säger motsatsen: planen räknas ut efter valet och ändras
inte under passet. En plan per dygn.

**Och en arbetsbördegrind byggdes vid upplåsningen**, som det här stycket uttryckligen
förbjuder. Den prövade dessutom mot paketet — sju kort för nivå 1 — medan dagen lärde ut
tretton, och läste budgeten ur gårdagens rad så att den aldrig förbrukades. Taket hör
till införandet (5.5), inte till grinden.

**Det som mätningen sedan visade var det motsatta problemet.** Med dagsvillkoret och en
plan per dygn får dag 1 tretton kort, dag 2 tolv, och **dag 3 och framåt ett till tre** —
medan takten tillåter tjugosju. Kursens 951 kort skulle ta omkring 475 dagar i stället för
de 36 tidsmodellen räknar fram. Orsaken är version-1-noteringen i 5.6: kandidatmängden är
nästa nivå, och en nivå har median ett kort. 4.5 beskriver redan vad som ska gälla i
stället — «att låsa upp tio nivåer ger en kö av kort» — och kön var blockerad på
tidsmodellen, som nu finns.

### 4.5 Upplåsning är inte införande

| | Frågan | Rätt svar? | Kostar |
|---|---|---|---|
| **Upplåsning** | vad *går* att lära nu | ja — grammatiken avgör | ingenting |
| **Införande** | vad *borde* läras nu | nej — ett omdöme (5.6) | minuter per dag |

Att låsa upp tio nivåer ger en kö av kort, inte tio nivåers arbete samma dag. Ett
kort som är upplåst men varken infört eller presenterat i dag kan aldrig stå i en
mening (R1).

---

## 5 · Dagspasset

### 5.1 Två faser

| Fas | Vad som händer | Vilka kort |
|---|---|---|
| **1 · Introfasen** | dagens nya kort presenteras, en övning i taget | bara dagens nya |
| **2 · Meningsfasen** | meningar översätts och rättas | dagens nya och de förfallna; inga nya presenteras |

**Dagens kort** är de förfallna korten och dagens nya. Vilka nya kort dagen har är
bestämt innan passet börjar.

**Förfallna kort är aldrig med i introfasen.** Att öva ett förfallet kort precis före
meningen gör det lätt att klara något som egentligen var svårt, och då mäter meningen
fel sak. För ett nytt kort spelar det ingen roll: det är första gången, och introfasen
finns för att lära ut det.

**Presenterat och infört** är två steg:

| | Betyder | Följd |
|---|---|---|
| **presenterat** | har klarat introövningen i dag | får användas i dagens meningar |
| **infört** | har gått rätt i en mening | är inne i systemet och schemaläggs av FSRS |

Ett nytt korts första FSRS-betyg kommer från dess första mening. Blir kortet inte
infört under dagen — användaren avbryter, eller klarar det inte — börjar det om som nytt
och kan väljas igen nästa dag; mötena finns kvar i loggen. **Ett paket (3.10) blir
infört helt eller inte alls**, annars kunde ett verb vara infört utan det pronomen det
kräver.

**Ett dygn börjar klockan 04:00** i användarens lokala tid, som i Anki, så att den som
övar strax efter midnatt räknas till föregående dag. Tiden är en inställning (R6), och
04:00 är förvalet.

**Varje dag utgår från läget som det är.** Beräkningarna förutsätter att användaren gör
dagens arbete varje dag. Missas dagar växer arbetsbördan, och tidsmodellen svarar med
färre nya kort (5.5).

#### Dagsplanen: vilken mening som bär vilket kort (avgjort 2026-09-21)

Att bestämma dagens KORT räcker inte. Villkor 8 i 6.1 låter en källmening ställas en
gång per dag, så materialet FÖRBRUKAS medan dagen går: ett kort som var prövbart på
morgonen kan vara oåtkomligt på eftermiddagen. Passet lade därför upp varje övning för
sig och tog slut mitt i — fyra presenterade ord gick inte att pröva alls, och dagen
förklarades klar med fulla högar.

Planen läggs i stället före passet och är en TILLDELNING: en lektion och en egen
introövning per mönsterkort, och egna meningar reserverade åt huvuddelen. Tre saker
följer av att den ska hålla:

- **Ordförrådet är ett val, inte ett utfall.** Varje ord en mening använder och
  användaren inte kan är ett kort dagen måste betala för (5.4, 5.6). Utan ett val tog
  planen de meningar generatorn råkade räkna upp först, och de kommer substantiv för
  substantiv: femton meningar blev femton substantiv och ETT verb. Ett återkombinerande
  ordförråd ger lika många meningar för en bråkdel. Hur många ord per ordklass följer
  av vad planen ska räcka till: med c ordklasser i meningen och m ord i varje finns m^c
  källmeningar, och planen behöver 2P åt lektionerna och övningarna plus m åt
  huvuddelen, alltså det minsta m där **m^c − m ≥ 2P**. Orden nomineras ur vad som
  FAKTISKT går att bygga — nivå 1 har `bestämning/naken`, och då duger bara oräknebara
  substantiv — och väljs sedan på frekvens (5.6).
- **Flera kort får dela lektionsmening.** Villkor 8 gäller meningar som STÄLLS;
  lektionen visar. Samma mening gås igenom en gång per kort, med olika kort markerat
  varje gång, och det är dessutom den introduktion som bygger upp steg för steg. Egna
  lektionsmeningar kostade lika många källmeningar som övningarna och gjorde fyra av
  dagens tretton kort omöjliga att införa.
- **Huvuddelens täckning reserveras FÖRE övningarna.** Introfasen bokför ingenting
  (5.4), så ett kort blir infört först genom att gå rätt i en mening, och dagen tar
  slut när högarna är tomma (5.3). Täckningen är det hårda kravet och övningarna har
  många meningar att välja på; matchades övningarna först åt de upp just de meningar
  som bar ett ord ingen annan mening bar.

- **Materialet räknas per ÖVNINGSFORM, inte per kortfamilj** (avgjort 2026-09-26).
  Tabellen i 5.4 delar korten efter hur de övas: ett innehållsord får en glosa, som inte
  kräver någon mening, medan regler, ändelser, oregelbundna former OCH funktionsord får
  en mening och därför behöver eget material. Räkningen använde `familj != "ord"`, och ett
  funktionsord har familjen «ord»: nivån `ord:demonstrativ_fjärran` fick noll
  mönsterkort, taket en mening, och den enda meningen gick till lektionen. Kursen
  stannade där.
- **Ett infört ord är material bara om det går att använda på nivån.** Införda ord kostar
  ingenting och är dessutom bättre lånekort (5.4), men de får inte räknas utan att
  byggvillkoren tillfrågats: nivå 2 kräver artikel, alltså ett RÄKNEBART substantiv, och
  dag ett lär bara ut oräknebara eftersom nivå 1 kräver naken fras. Fyra substantiv fanns,
  talet stämde, och ändå fanns bara fem källmeningar i hela nivån.
- **Uppgiften märks med det kort den TILLDELATS.** Planen bygger uppgiften när
  källmeningen först dyker upp och märker den med det kort som råkade samla in den;
  matchningen ger den sedan till ett annat. Följer märkningen inte med läser bedömningen
  i 5.4 ett annat korts betyg, och kan godkänna en övning vars eget kort föll.
- **Tilldelningen sprids över orden.** En matchning får välja fritt bland lika goda
  meningar, och den fria tog den första varje gång: tre av fem introövningar hamnade på
  `passa`, som då hade EN mening kvar i huvuddelen medan `sitta` hade fyra. Föll `passa`
  fanns ingen mening att ta om det med. Hur många omtag en dag behöver går inte att veta
  i förväg — det beror på användaren — men ett ord vars meningar alla är förbrukade har
  garanterat noll, och spridningen är dagens enda reserv mot fel.

Ett kort planen inte kan ge en mening hamnar i karantän (3.10). **Dag ett ska karantänen
vara tom** — annars går kursen inte att börja. Att dagens meningar för ett INFÖRANDE tar
slut är däremot ingen karantän: villkor 8 gäller bara i dag, och kortet börjar om i
morgon.

**Meningsfasen väljer ur planen, inte ur generatorn.** Planen har redan räknat upp
dagens meningar, och att fråga generatorn om samma meningar kostade 18 s per val — efter
ETT felsvar faller flera kort på en gång och ska alla ha var sin ny mening, så passet
kröp i minuter mellan övningarna. Hela stegen i 6.3 tas därför inom planen först. Mätt
på nivå 1: **median 0,01 s per val** mot 10–20 s. Sökningen finns kvar som sista ord,
eftersom planen samlar in med ett tak och inte är garanterat uttömmande.

### 5.2 Planen är en fråga, inte en tabell

| | Vad det är | Innehåller |
|---|---|---|
| **Dagens mål** | det som måste klaras | förfallna kort (FSRS) + dagens nya |
| **Det tillåtna** | vad en mening får använda | införda kort + dagens presenterade |

Vilka kort som är förfallna kan när som helst räknas fram ur mötena. **Det som lagras
är det mätta och det valda:** möten med diffens och användarens betyg, flaggor, öppnade
nivåer och vilken nivå som öppnade varje kort, dagens tilldelning av nya kort, vilka som
presenterats och införts, sparat tempo (5.5), karantän och felrapporter, och
inställningar. Dessutom sparas bevisen (3.10), så att kontrollen inte behöver göras om.
Förfallodagar, R och fönster räknas fram.

Ett infört kort som inte är förfallet får användas i meningar. Det bokförs som
alla andra, och går det fel hamnar det i dagens again-hög.

### 5.3 Dagen tar slut när högarna är tomma

Passet är klart när **new-, again- och due-högarna är tomma.** Varje fel ger mer
arbete. Att varje kort i dagens mål går att nå garanteras av prövbarheten (3.10) och
reservstegen i budgeten (6.3). Bryts det ändå är det ett fel i programmet, och 3.10
säger vad som händer.

**Att passet kan dra ut på tiden är ett medvetet val.** Det som räknas är arbete som
lyckas, inte nedlagd tid. Tidsratten styr hur mycket nytt som planeras (5.5), inte
när passet slutar, och ett kort som användaren inte klarar ligger kvar tills det
klaras.

### 5.4 Introfasen: hur ett kort presenteras

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
aldrig något användaren inte själv har visat att hen kan.

**Övningen är alltid en riktig form**, eftersom kortet annars inte klarar
produktionstestet (3.1):

| Kort | Övning |
|---|---|
| `ord` | glosa: betydelse → form. Är källordet tvetydigt (`får`) visar uppgiften vilken betydelse som avses; annars bryter övningen mot R2 |
| funktionsord — artikel, hjälpverb, negation, subjunktion, infinitivmarkör | en mening med ordet som enda mål, som för en regel. En glosa vore sällan entydig: engelskans *a* är både `en` och `ett` (R2) |
| böjningscell | en ruta i paradigmtabellen |
| pronomen | en ruta i pronomentabellen, som en böjningscell. Formerna presenteras när de blir prövbara, ofta flera samma dag |
| `egenskap` | formen där egenskapen syns: `ett hus` |
| `rektion` | formen där kravet syns: `ich helfe dir` |
| `regel` | en lektion med ett exempel per utfall av regelns val, och sedan en mening med regeln som enda mål |

Lektionens exempel är inget valt antal. Omvänd ordföljd har två utfall — omvänd och
rak — och får två exempel; en regel med tre utfall får tre.

> **Introfasen bokför ingenting.** Den finns för att användaren inte ska möta ny kunskap
> oförberedd, inte för FSRS. Kortet prövas på riktigt först i meningsfasen, och blir
> infört där (5.1).

- **Lånekorten** — övningens övriga kort — **väljs utan gränsvärde.** Generatorn bygger
  övningen med det nya kortet som enda mål och väljer lånekort så att sannolikheten att
  alla blir rätt är så hög som möjligt. Ett mönsterkort presenteras alltså med ett ord
  användaren kan väl, så att bara mönstret är nytt. Senare *prövas* det helst på ett nytt
  ord (6.4).

  **«Kan väl» mäts i två steg, och ordningen mellan dem följer av `p`:s platshållare**
  (avgjort 2026-09-26). Måttet på vad användaren kan är FSRS:s retrievability — stability
  gånger tiden sedan senaste mötet, alltså «repeterat länge, ofta rätt, nyligen
  genomgått». Det behöver inte hittas på. Men ett kort som bara är PRESENTERAT i dag har
  inget FSRS-tillstånd, och `p` ger då retentionsmålet (5.1): samma tal som ett kort
  användaren drillat i en vecka, och ofta ett HÖGRE, eftersom det drillade kortets R har
  hunnit sjunka. Sorterat på `p` ensamt vinner därför orden som glosades för tre minuter
  sedan, och övningen prövar två nya saker i stället för en. Nyckeln är alltså

      (antalet OINFÖRDA lånekort, sedan risken ur `p`)

  Infört betyder att kortet gått rätt i en mening (5.1) — det är ett mått vi har, och det
  skiljer det prövade från det oprövade. **Dag ett är ingenting infört**, så båda talen är
  lika för varje mening, och då finns inget bättre än det som just gicks igenom.

  Satsen är ett MAXIMUM, inte ett golv. Finns inget infört ord som duger är ett nytt det
  bästa som finns, och nivå 2 är just så: den kräver ett räknebart substantiv, och nivå 1
  lär bara ut oräknebara eftersom den kräver naken fras. Mätt över åtta nivåer: 15 okända
  lånekort med regeln mot 18 utan, och hela skillnaden ligger på nivå 2 — 4 mot 7.
- **Regelns mening byggs som alla andra meningar** (6.4). Introfasen har ingen egen
  generator.

**En övning görs om tills det nya kortet blir rätt.** Ett kort som misslyckas läggs sist
i introfasens kö. Fel på lånekorten spelar ingen roll, utom när de döljer det nya kortet
(R5); då görs övningen om.

**Att döljas syns på att målet självt faller** (avgjort 2026-09-26). Rättningen knyter
varje avvikelse till de kort som bestämde ordet (7.3), så ett lånefel som rör målets
positioner fäller målet. Villkoret «målet gick rätt» är därför båda reglerna ovan på en
gång, och behöver inget eget mått. Bedömdes hela meningen föll en övning som gjort sitt:
«En stad faller.» besvarad «A city fall.» hade artikeln — övningens kort — helt rätt men
saknade verbets `-s`, och åtta kort föll ur dagen för ett fel på ett lånekort. Sist i en
TOM kö är dessutom samma fråga igen, direkt, med facit i minnet; finns inget annat kort
att lägga emellan pausas fasen i stället.

**Ordningen inom dagen följer kraven.** Ett kort presenteras efter de kort det kräver, så
att lånekorten redan är införda eller presenterade.

**Kravordningen räcker hela vägen, och friheten som blir över är verkligt fri**
(avgjort 2026-09-22). Regeln ovan är en PARTIELL ordning, och det som fyllde resten var
slump: introfasen frågade kort för kort «vilka av mina ord är inte utlärda än» och fick
3, 1, 1, 0, 0 plus en svans på 1. Orden kom i klumpar mellan strukturkorten, och några
lärdes ut sist av allt. Planen (5.1) visste hela tiden varenda ord dagen behövde — frågan
ställdes lokalt om något som var känt globalt, vilket är samma hål som gav materialbristen
och de långsamma valen.

Ställd om hela planen ger regeln en ordning av sig själv, i tre lager:

| Frihet | Vad som avgör den |
|---|---|
| innehållsord kontra mönsterkort | kraven. Innehållsordets övning är en GLOSA, och en glosa kräver ingen mening — kortet kräver alltså ingenting och går alltid först. Mönsterkortets övning är en mening, som kräver sina ord. Mätt på engelskan: av 119 ordkort som kräver en regel är 119 FUNKTIONSORD, som enligt tabellen ovan också övas med en mening, och noll innehållsord |
| mellan orden | den nya täckningen (5.6) — i version ett ordfrekvensen. Var bokstavsordning efter svensk konceptnyckel, samma slump som lade `he` på nivå 79 |
| mellan nivåns mönsterkort | ingenting, och det är riktigt: en nivå ÄR en starkt sammanhängande komponent (4.1), så korten kräver varandra ömsesidigt och ingen ordning kan respektera kraven. Nivå 1 har 20 krav mellan sina 5 kort. Därför paketet (3.10) |

**Dag ett.** Den första nivån är de kort en enkel mening kräver (4.2), och de väljs som
ett paket (3.10). Lånekorten är då de kort som presenterats tidigare samma dag. Passet
når sin första mening när användaren kan ett pronomen och ett verb.

### 5.5 Hur många nya kort

**Tiden styr bara hur många nya kort som väljs, aldrig hur långt passet blir** (5.3).
Passet är prestationsbaserat, och hur bra användaren är en viss dag går inte att veta i
förväg. Målet är en **jämn takt i det långa loppet**: ett enskilt pass får bli både
mycket kortare och mycket längre än den inställda tiden, för att takten ska hålla.

Beräkningen görs en gång, när passet startas och användaren har valt om nya nivåer
ska öppnas.

**Arbetet räknas i meningar, inte i kort.** Den fasta kostnaden per mening dominerar
(6.3), så tiden per kort beror på hur tätt meningarna packas.

**Mätt ur loggen**
- tid per introövning, med omtag
- tid per mening, som funktion av antalet mål och antalet övriga kort

**Formeln**

    T      den inställda tiden per dag
    E(t)   förväntad arbetstid dag t från de kort som redan är införda
    k(a)   förväntad arbetstid för ett nytt kort a dagar efter att det presenterats
    K(a)   k(0) + k(1) + … + k(a)

`k` räknas en gång ur FSRS-parametrarna och tidsmodellen, som ett väntevärde; hur — en genomräkning av FSRS-tillståndens sannolikheter dag för dag
— avgörs i steg 6. `E` räknas
på samma sätt ur de införda kortens tillstånd. Budgeten (6.3) och värdet (6.6) avgör hur
många meningar korten kräver. Införs n nya kort varje dag från och med i dag blir
arbetet dag t

    E(t) + n · K(t − i dag)

> **Dagens antal nya kort är det största jämna tempo som ryms varje dag till kursens
> slut:**

    n = minsta värdet av (T − E(t)) / K(t − i dag), över dagarna t fram till kursens slut

- **Ingen vald horisont.** Kursen slutar när alla kort är införda. När det sker beror på
  tempot, så räkningen görs om tills tempot och slutdagen stämmer överens; det tar några
  varv.
- **Inga ryck.** Formeln söker ett tempo som håller, inte ett antal som fyller de närmaste
  dagarna.
- **Den följer läget.** Formeln räknas om varje dag. Har arbetsbördan vuxit, till exempel
  efter några missade dagar, blir n noll.
- **Den är billig:** en summa per dag framåt, ingen simulering. Arbetsbördan är summan av
  varje korts arbetsprofil, förskjuten till den dag kortet presenterades.
- **Tempot är ett genomsnitt.** Ett paket (3.10) tas med helt, så en dag kan ge färre kort
  än n. Det som inte används sparas till nästa dag.

**Prognosen räknar för högt, och det rättas med en mätning.** FSRS räknar med att varje
förfallet kort kräver en egen repetition. Så blir det inte: kort som behövs i andra
meningar möts och bokförs innan de förfaller (7.1). Hur stor del av prognosen som
faller bort mäts ur historiken. Tills mätningen finns räknas ingen del bort — det ger
färre nya kort, aldrig fler.

Nivåns kort är inte tvingade att införas. De konkurrerar som alla andra kort, men
vinner ofta, eftersom de ger mycket täckning (5.6).

**Innan användarens egen historik finns** används FSRS standardparametrar och tiderna
ur den gamla loggen (6.3), tills historiken räcker för att ersätta dem.

#### Byggd 2026-09-27 — `passet/tid.py`

**`k(a)` är ett väntevärde, räknat med HOPSLAGNA tillstånd.** Varje repetition grenar
sig — rätt med sannolikhet R, fel med 1 − R — så en exakt uppräkning växer som 2^n. Att
i stället gallra de minsta grenarna är fel åt farligt håll: de grenar som faller ofta är
just de som ger många repetitioner, så gallringen underskattar arbetet och släpper in
FLER nya kort. Mätt: gallring vid 1e-6 gav 7,88 repetitioner på ett år mot den gamla
modulens uppmätta 8,4, och att skärpa gränsen slutade konvergera innan den blev rätt.
Lösningen är att tillstånd i samma ruta räknas som ett; då är antalet levande tillstånd
bundet av rutnätet. Upplösningen är mätt fram — en dubblering flyttar årssumman under en
promille — och profilen möter den gamla Monte Carlo-mätningen: **3,685 repetitioner
första månaden mot 3,7, och 8,37 första året mot 8,4.**

**Växelkursen är mätt, och 6.3:s påstående höll.** `ordbok/verktyg/meningstidsmätning.py`
räknar fram meningens kostnad ur den gamla loggen: **sekunder = 13,4 + 2,8 × kort**. Den
fasta kostnaden är alltså fem gånger kortets, vilket är oberoende bekräftelse på varför
arbetet räknas i meningar. Mätpunkterna är inte monotona vid den urvalsstorleken, så
formen tas ur 6.3:s eget påstående — «den fasta kostnaden per mening dominerar» — och
anpassningen mäter dess två tal.

**Horisonten måste gå förbi slutdagen**, vilket är en rättelse av formeln ovan: ett kort
kostar arbete i över ett år, så arbetsbördan fortsätter efter sista införandet. Men den
bär inte talet, och det ska stå rätt: den korta horisonten ger 30 kort vid tjugo minuter
mot 27 med den hela, eftersom dagarna efter slutdagen aldrig binder. **Det som tämjer
tempot är introduktionskostnaden** — utan den gav en timme om dagen 265 nya kort och en
kurs på sex dagar.

**Glosfasens tid var hårdkodad till noll** fram till i dag, så 5.5:s «tid per introövning,
med omtag» gick inte att mäta för ord. Tills de mätta raderna finns används
introövningens kostnad för båda: en övning är en hel mening och en glosa ett ord, så det
är en övre gräns — riktningen 5.5 kräver.

**Grinden.** Budgeten är n plus det sparade, och ett paket tas helt eller inte alls
(3.10), så ett paket som inte ryms väntar tills det gör det. Mätt på engelskans 951
kort: fem minuter om dagen ger fyra nya kort och nivå 1:s paket på sju ryms inte — det
sparas. Tio minuter ger tio kort och 96 dagar, tjugo ger 27 och 36 dagar.

Tempot växer FASTARE än tiden, och det är riktigt: den bindande dagen är sista
införandedagen, och en kortare kurs hinner bara samla en del av kortets livstidskostnad
innan dess — 56 % vid tjugo minuter, 41 % vid sextio. Resten sprids över året efteråt och
ryms. Ett prov som krävde linjäritet fällde därför en korrekt modell och fick skrivas om
till det som verkligen är påståendet: **ingen dag spränger budgeten.**

### 5.6 Vilka nya kort: införandeordningen

> **Inför först det som ger mest ny täckning per kort.**

**Täckning** är hur stor del av språkets verkliga användning användaren kan producera.
Varje gång språket använder ett ord i en viss form, eller tillämpar en regel, är en
användning. Den är täckt när alla kort den kräver är införda. Ett korts **nya täckning**
är de användningar där just det kortet är det sista som saknas.

Kandidaterna är de kort som är upplåsta, inte införda och prövbara nu (3.10), ensamma
eller i ett paket. Ett paket jämförs med sin nya täckning delad med sitt antal kort.
Korten väljs ett i taget, och varje val ändrar vad nästa kort ger. Ger två kandidater
lika mycket avgör kartans ordning (6.7), så att ordningen blir densamma varje gång.

| Kort | Vad det ger |
|---|---|
| ett vanligt regelbundet verb | alla verbets användningar, för ett kort |
| ett sällsynt oregelbundet verb | färre användningar, för ordet och dess undantagskort. Det kommer därför senare — `vara` är ändå så vanligt att det kommer tidigt |
| regeln «artikeln följer genus» | varje infört substantiv med artikel, på en gång |
| `inversion_wh` | alla wh-frågor som går att bygga med de ord som redan är införda |
| ett kort som kräver något som inte är infört | ingenting ensamt, och väljs därför i ett paket |

**Ett ords egna kort är en kostnad, inte en vinst.** Ett ord som kräver många kort ger
inte fler användningar än ett regelbundet ord som är lika vanligt, men kostar fler kort.

**Ordningen balanserar sig själv.** Tidigt ger grundreglerna och de vanligaste orden
mest, eftersom nästan inga användningar är täckta utan dem. Hjälpverbet kommer när
perfekt blir möjligt, eftersom inga perfektformer är täckta utan det. När grunderna
sitter ger ett nytt ord bara sina egna användningar, och då avgör hur vanligt det är.

**Räkningen görs utan att bygga meningar.** Den nya täckningen läses ur tabellen från
form till kort (3.4) och kartan (6.7), så räkningen är snabb även med tusentals kort.
Bara de kort som faktiskt väljs för dagen provbyggs, en mening var (3.10).

**Frekvenserna.** Grammatiken bestämmer vad som går att lära; hur språket används
bestämmer vad som är värt att lära först. Två sorters frekvens behövs:

| Frekvens | Räknas per | Därför |
|---|---|---|
| hur ofta ett ord används | koncept, gemensamt för alla språk, och delat på lexem i varje språk | `per_känna` och `per_lukta` får var sin plats trots att båda heter `sentir`, och två synonymer får var sin andel (7.4) |
| hur ofta innehållets drag används | drag: dåtid, första person plural, fråga, negation … | en egenskap hos betydelsen, liksom konceptens frekvens; mäts en gång i en korpus, till exempel trädbankerna i Universal Dependencies |

Version ett har samma ordning för alla användare.

**Båda frekvenserna är nu mätta** (2026-09-21), och ingen korpus behövdes.

| Frekvens | Mätt som | Fil |
|---|---|---|
| hur ofta ett ord används | konceptets lemma, delat mellan de koncept som bär det, median över språken | `ordbok/nivålistor/frekvens.csv` |
| hur ofta innehållets drag används | **varje FORM är en sträng, och `wordfreq` mäter strängar** — «book» 66 % mot «books» 34 %, «is» 45 % mot «was» 25 %. Summerad per cell ger det dragets andel av språket | `ordbok/nivålistor/användningar.csv` |

Den andra raden var tänkt att kräva en korpus — trädbankerna i Universal
Dependencies — men en form ÄR en sträng, så samma verktyg räcker. Det sparar också
den handgjorda mappningen mellan korpusens etiketter och våra kort, och ger samma
mätning för alla språk på en gång. Engelskan, de tyngsta dragen:

    18,0 %  Preposition/inv     4,8 %  Verb/pres_3sg
    12,7 %  Artikel/inv         3,4 %  Verb/pret
     7,6 %  Verb/inf_imp        1,9 %  Verb/sup

Strängen mäts en gång och delas mellan dem som bär den, i två led: mellan cellerna i
samma lexem (engelskans `read` är infinitiv, presens och preteritum) och mellan lexem
(`stand` är både substantiv och verb). Annars överstiger summan språket självt.

**Varför det behövdes.** Utan dragets frekvens sjunker varje rent grammatiskt moment
till kursens slut, eftersom ett regelkort inte har någon ordfrekvens. Mätt på
nivåordningen, omordnad efter enbart konceptfrekvens: preteritum hamnade på nivå 127
av 164, frågeinversionen på 135 och substantivets plural på 163. Hundratjugo gloser
före dåtid.

`grundord.csv` har en CEFR-nivå per koncept (A1, A2, B1), men den är en bedömning och
inte en mätning, och den ordnar inte orden inom nivån. Den behövs inte längre för
ordningen. Japanskan saknar tokeniserare (MeCab) och är omätt i båda tabellerna; den
ska kontrolleras för hand.

**Tio nivåer av 164 består bara av ordföljdsregler** — `objekt_efter_verb`,
`frågeord_först`, `inversion_i_fråga` och sju till. De hänger inte på någon form och
får ingen vikt ur användningarna. I version 1 tas de i beroendeordning; att låta dem
ärva vikt från de former de gör sägbara är en senare förbättring.

**Version 1 väljer bara ur nästa nivå, och mönsterkorten först** (avgjort 2026-09-20).
Kandidatmängden ovan — upplåsta, oinförda, prövbara — innehåller varje ordkort från dag
ett, eftersom orden är upplåsta (3.1). Men ordningen som ska sålla dem är TÄCKNINGEN, och
den är inte räknad. Öppnas mängden innan dess väljer kursen på frekvens ensamt och kan
lära ut femtio substantiv innan den rör grammatiken. Version 1 tar därför kandidaterna ur
nästa nivå, med mönsterkorten före orden.

- **Det är ett närmevärde för täckningen, inte en egen regel.** Ett mönsterkort behövs av
  varje mening och har därför hög ny täckning; tabellen ovan säger samma sak om «artikeln
  följer genus». Orden kommer ändå med, som lånekort till mönstren, och lärs ut som
  glosor innan kortet som kräver dem (5.4).
- **Priset** är att ett mycket vanligt ord kan komma senare än ett sällsynt mönster.
- **Täckningen är eget arbete.** När den finns ersätter den både urvalet och ordningen,
  och den här noteringen faller bort. Ingen annan del behöver ändras: kandidatmängden är
  det enda som är avsmalnat.

**Täckningen ordnar NIVÅERNA, inte orden inom en nivå** (avgjort 2026-09-26). Löftet
ovan — att täckningen ersätter både urvalet och ordningen — visade sig gälla halvt.
För nivåordningen vann den stort (`ordningsmätning.py`). För ORDVALET inom en bestämd
nivå ger den ingenting, och det är mätt: `ordbok/verktyg/ordvalsmätning.py` jämför tre
ordningar på samma mått, engelskan över sex nivåer och 34 kort.

    ordfrekvens          17,19 %
    total användning     17,07 %
    närsynt täckning     16,97 %

Skälet står i 5.6 själv: «ett kort som kräver något som inte är infört ger ingenting
ensamt». Ett ords värde ligger i alla dess former, och de flesta cellerna är inte
upplåsta än — så «ny täckning nu» mäter fel horisont, medan frekvensen fångar hela.
Kriteriet hör alltså till de kort som GRINDAR: en regel låser upp olika mycket, och där
avgör täckningen. Inom en nivå konkurrerar orden om samma meningsformer, och då skiljer
bara hur ofta språket använder dem.

**Kvar av noteringen är därför bara KANDIDATMÄNGDEN**, inte ordningen: att låta dagen
välja bland varje upplåst kort i stället för bara nästa nivås. Det kräver att dagen har
en budget att fördela, alltså tidsmodellen (5.5).

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

1. varje kort den kräver är **tillåtet**: infört eller presenterat i dag (R1, 5.2)
2. varje regel den använder är **upplåst**
3. varje målkort ingår i **varje korrekt svar** som går att bygga av det tillåtna (R2, 6.5)
4. **båda språken kan uttrycka den.** Motorn har inga fasta källspråk — alla språk
   är likvärdiga — men alla språk har inte alla celler. Svenskans `vantar` har
   ingen singular, och då ställs meningen inte. Det är rätt beteende, inget fel.
5. inga två **svaga** kort styr samma ställe i meningen (6.2)
6. **innehållet uppfyller konceptens krav**, `valens` och `semantik` (3.5). Ett krav som
   inte går att uppfylla gör meningen omöjlig och släpps aldrig tyst (punkt 12,
   `urval.py:219`)
7. **ett fel på ett mål går att knyta till just det kortet**: inget annat enskilt kort
   förklarar samma avvikelser, efter prerekvisiten (7.3). Det kontrolleras med samma rendering som rättningen
   använder, och gör R5 till ett villkor när meningen byggs i stället för en förhoppning
8. **källmeningen har inte ställts i dag.** Efter ett fel har användaren sett facit, och
   samma fråga igen mäter minnet av facit i stället för kortet — samma skäl som omprovet
   i bilaga A föll på. Värdet (6.6) ser det inte, eftersom p efter ett fel mäts över
   olika meningar. En annan dag gäller inte villkoret. Finns ingen annan mening för
   kortet tas ensamövningen (6.3), och det är inget brott mot invarianten i 3.10

Två regler kan kräva former som inte går ihop. Då är meningen inte svår utan
omöjlig att bygga, och sökningen fortsätter.

**Villkor 8 gallrar på KÄLLTEXT, och sökningen får inte gallra på kort** (avgjort
2026-09-21). Generatorn har två sparsamheter som båda antar att en mening per
korttäckning räcker: `per_mall` tar en mening per mall, och `grupperat` prövar ett ord
per kortsignatur — `stå`, `sitta`, `passa` och `falla` är alla regelbundna verb och
blev ETT ord. Båda är rätt tills just den meningen är förbrukad, och då blir sökningen
blind: var «Kärlek står.» ställd fanns ingen mening alls för `kärlek`, fast fyra stod
oställda i dagens plan. Passet svarade att materialet var slut med fulla högar.

Därför: taket per mall är antalet ställda meningar plus en — fler kan inte vara
uteslutna — och grupperingen körs först för farten, men ett ogrupperat svep följer när
det grupperade uteslöt något på källtexten. Samma signatur ger samma kort och därmed
samma risk och samma åtskillnad, så det ogrupperade svepet kan bara hitta en annan
KÄLLTEXT; uteslöts ingenting behöver det inte köras.

**Reservsteg 1 lär inte ut.** Ensamövningen (6.3) byggs bara av kort användaren redan
mött. Fick den fylla ut med nya ord dök outlärda ord upp mitt i meningsfasen —
«Kärlek ligger.», med `ligga` aldrig visat — och det blev ett kort dagen aldrig
planerade för. Att lära ut ord är introfasens sak, med glosan först (5.4).

### 6.2 Urvalsregeln

> **De svaga korten sprids över oberoende positioner.**

I praktiken: **bygg meningen av så många svaga kort som budgeten tillåter, se till att
varje svagt kort är det enda svaga på sin plats, och ta inte med fler kort än meningen
behöver.** Vilken av de möjliga meningarna som väljs avgörs av värdet i 6.6.

**Ett kort är svagt när det hör till dagens mål och inte har klarats i dag** — mängden
`F` i 6.6: förfallna kort, dagens nya och kort som fallit i dag. Ett övervakat kort är
förfallet när andelen rätt i fönstret är under 0,9 (7.6). En menings svaga kort är dess
**mål**; de **övriga** korten är de som meningen behöver för att vara en mening.

**Varje kort har en sannolikhet p att bli rätt**, som budgeten (6.3) och värdet (6.6)
räknar med:

| Kort | p |
|---|---|
| inte mött i dag | FSRS:s R; för ett övervakat kort andelen rätt i fönstret |
| senast rätt i dag | FSRS:s R |
| presenterat i dag men inte mött i en mening, eller senast fel i dag | mäts ur loggen: andelen rätt i nästa mening efter en presentation, respektive efter ett fel samma dag |

Direkt efter ett möte ger FSRS R ≈ 1 oavsett om svaret var rätt, och ett nytt kort har
inget FSRS-tillstånd alls. Därför mäts de två sista fallen. Tills mätningarna finns är
p = 0,9, retentionsmålet, som ett tillfälligt värde.

Två villkor, samma tal sett från två håll:

| Villkor | Skyddar |
|---|---|
| få svaga kort: P(≥2 fel) ≤ τ | att felet går att lokalisera |
| varje svagt kort ensamt på sin plats | att felet går att knyta till ett kort |

Exempel: när genuskortet för `hus` är målet duger `ett hus`, där genuset syns på
ett ställe. `ett stort hus` duger inte — där styr genuset både artikeln och
adjektivet, och ett fel går inte att knyta till ett enda kort.

**Ett korts positioner är de utskrivna ord vars form kortet bestämde.** De räknas ut
och märks inte för hand (8.3): beslutet tvingas till vart och ett av sina andra utfall,
meningen renderas om, och de ord som ändras är positionerna. Ett beslut kan också synas
som en **lucka** — platsen där ett ord hade stått. Syns beslutet inte alls, som genuset
i svensk plural, prövades det inte. Det gäller även när ord smälter ihop (`au` = `à` +
`le`) och när språket skrivs utan mellanslag. Två kort är oberoende när deras
positioner och luckor inte överlappar. Samma omrenderingar är rättningens alternativ
(7.3).

Undantaget är ett ord och dess formkort, och ett beslut som väljer cell och den cellens
formkort. De delar alltid position, men prerekvisiten i 7.3 håller isär dem — föll ordet
är formen ograderad, och är svaret en annan av beslutets former har beslutet fallit — och
därför får ett mönster prövas på ett nytt ord (6.4).

**Det här är hela urvalet.** Följande beteenden följer av regeln och får inga
egna regler:

| Beteende | Därför att |
|---|---|
| dagens mål blir täckta | de svaga korten är målen, och bara mål ger värde (6.6) |
| antalet mål per mening | budgeten avgör (6.3) |
| variation i ordval | vid lika värde väljs övriga kort med lägst p, och ett kort som just klarats har p nära 1 |
| variation i meningens form | formen bärs av regelkort, som också har p |
| inga upprepningar samma dag | en källmening ställs inte två gånger samma dag (6.1 punkt 8) |
| varierande längd | många förfallna kort ger täta meningar; mot dagens slut återstår få, och meningarna blir korta |

Det finns alltså ingen utfyllnad. Ett kort som inte är mål står i meningen bara för att
meningen behöver det. För övervakade kort är R andelen rätt i fönstret (7.6), så ett
kort som ses ofta men ofta blir fel blir också mål.

### 6.3 Budgeten

Det som går sönder när en mening packas för hårt är **rättningen**: med ett fel
syns i diffen var det sitter, med två gör det inte. Därför:

    P(≥2 fel i meningen) ≤ τ        τ = 0,10

τ = 1 − retentionsmålet 0,9, samma tolerans som fönstret i 7.6. Det är
svårighetsrattens förval, och ratten får flytta det upp till den gräns som mäts när
rättningen finns (5.7).

Med p = 0,90 för mål och p = 0,99 för övriga kort:

    mål   övriga   P(0 fel)   P(1 fel)   P(≥2 fel)
     1       5       0,856      0,138      0,006
     3       5       0,693      0,266      0,041
     5       5       0,562      0,340      0,098   taket
     6       5       0,505      0,362      0,132   över

**När ingen mening ryms.** Budgeten förutsätter att meningens övriga kort är starka. Tre
gånger är de inte det: tidigt i kursen, när de få korten presenterades samma dag och
förfaller samma dag; efter ett uppehåll, när nästan allt är svagt; och för regelkort som
varje mening behöver. Då tas två reservsteg, i ordning:

1. **Ensamövning.** Ett kort som ingen mening inom budgeten når prövas ensamt, i samma
   form som introövningen (5.4) men utan att kortet visas först. Svaret bokförs som en
   vanlig repetition. Övningen är provet, ingen förberedelse, och krockar därför inte med
   att förfallna kort aldrig övas i introfasen (5.1). Ett klarat kort kan sedan stå i
   andra meningar. Korten tas ett i taget, först det som gör flest blockerade mål
   byggbara. Ensamövningen hör till meningsfasen.
2. **Den minst riskabla meningen.** En regel syns bara i en mening och kan inte prövas
   ensam. Ryms ett regelkort ändå inte när alla kort som kan övas ensamma är klarade,
   väljs den giltiga mening som har lägst P(≥2 fel). Budgeten släpps bara här, och bara
   för att det annars inte blir någon övning alls.

Budgeten kan därför aldrig göra ett kort onåbart.

**Längden begränsas av tiden, inte av budgeten.** Längre meningar är billigare per kort
(mätt ur loggen):

    kort i meningen   median sek   sek/kort
         1               16,2         16,2
         2               17,5          8,8
         4               20,5          5,1
         8               24,9          3,1

Den fasta kostnaden per mening dominerar. Därför lönar sig ett extra mål — det sparar
en hel mening senare — medan ett kort som inte är mål bara kostar tid. Det avgör när
meningen är lång nog (6.6).

### 6.4 Att bygga mot ett kort

Att ett kort är upplåst och förfallet gör inte att det dyker upp av sig självt.
Franskans `inversion_wh` förekommer bara i wh-frågor, så när kortet är förfallet
måste generatorn **välja** att bygga en wh-fråga. Varje regel ska därför ha ett
byggvillkor — «meningen måste innehålla ett objektspronomen» — och den kunskapen
finns redan i renderaren. Byggvillkoret läses ur kartan (6.7): det är villkoren på de
vägar där kortet finns.

**Samma bygge används tre gånger:** i kontrollen före införandet (3.10), i
introövningen för en regel (5.4) och i meningsfasen.

**Ett mönsterkort prövas bäst på ett nytt ord.** Ett mönster möts alltid genom ett
ord. Skriver användaren `bilarna` rätt vet man inte om hen kan `-rna` eller bara
har sett `bilarna` femtio gånger. Mötet säger något om mönstret i den mån ordets
eget kort är svagare än mönsterkortet.

### 6.5 Entydighetsfiltret

R2 kontrolleras när meningen byggs, i samma filter som låsta regler. Resultatet beror
på vad användaren har infört: «jag arbetade» har en fransk översättning innan `imperf`
är infört, och två efteråt. Därför prövas bevisen om när ett kort införs (3.10).

Filtret ska hitta **alla svar som är rätt**, av två skäl: rättningen ska godta dem, och
målkortet måste finnas i vart och ett (R2). Det bygger på en princip:

> **Två innehåll som ger samma källmening är samma fråga.**

Två sorters varianter söks, för vilket språkpar som helst:

| Sort | Hur den hittas | Exempel |
|---|---|---|
| samma källmening, olika innehåll | varje fält i meningsspecen är en axel: fältets andra värden renderas på källspråket, och de som ger samma källmening är samma fråga. För ordens koncept görs det med ett uppslag — de koncept vars ord på källspråket är detsamma | «jag arbetade» → *I worked* eller *I was working*; «you are tired» → *du är trött* eller *ni är trötta* |
| samma innehåll, olika korrekta målmeningar | de utfall renderaren redovisar som godtagbara (8.3): utelämnbart subjekt, godtagna ordföljder, sammandragningar | `leo` / `yo leo`; «hon läste igår» / «igår läste hon» |

**Ingen lista över axlar skrivs för hand.** Kommer ett fält till i specen blir det en
axel. En handskriven lista kunde glömma en axel, och då skulle korrekta svar underkännas
utan att något märker det.

Bara varianter som går att bygga av det tillåtna (5.2) räknas. Därefter:

    ingår varje målkort i varje korrekt målmening?   nej -> förkasta

Varianterna filtret hittar är också de svar rättningen godtar (7.3).

**Kostnaden hålls nere på två sätt.** Källspråkets karta (6.7) visar vilka fält
meningen läste. Ett fält som inte lästes syns inte i källmeningen och varieras; ett fält
som lästes varieras bara där två värden ger samma form (tyskans `sie` är både «hon» och
«de»). Och filtret körs på kandidaterna i värdeordning (6.6), tills en klarar sig.

**Det filtret inte räknar upp:**
- **Stavning.** Stavningsvarianter är inga renderarbeslut. En alternativ stavning godtas
  bara om den står på lexemet; saknas den fångas den av omrättningen (7.2) och läggs
  till.
- **Helt andra konstruktioner** för samma sak, som passiv i stället för aktiv. De är
  andra innehåll och fångas också av omrättningen (7.4).
- **Synonymer** — ett annat lexem för samma koncept. De löses med ett nytt försök (7.4),
  och R2 har ett undantag för dem.

**Aspekt och modus löses genom att källmeningen visar valet.** Är både imparfait och
passé composé införda får en dåtidsmening bara ha imperfektkortet som mål om den
innehåller ett ord som avgör valet: «jag arbetade **varje dag**», «jag arbetade
**igår**». Generatorn lägger till ett sådant ord när meningen annars vore tvetydig, och
användaren tränar då just det som är svårt — att läsa valet ur sammanhanget.

Vilka ord som avgör valet kan sökningen inte hitta, eftersom det hör till betydelsen
och inte till ett visst språk. Det märks därför en gång på konceptet och gäller för
alla sju språk: adverben har redan `tempuskrav`, och behöver ett **`aspektkrav`**
bredvid. Det finns inte ännu (steg 5b).

**Det källspråket inte skiljer visas med en märkning** (avgjort 2026-09-14). «You are
tired» är både «du är trött» och «ni är trötta», och från svenska är «de läser» både
*ils* och *elles*. Utan hjälp ingår *ni* och *elles* aldrig i varje korrekt svar (R2), så
de korten går aldrig att öva i den kursen, och varje nivå som kräver dem förblir stängd.
Därför märks källmeningen när två innehåll ger samma källmening men olika svar:
«you (flera) are tired», «de (kvinnorna) läser».

- **Märkningen kommer ur filtret.** Den visar det fält och det värde som skiljer
  innehållen åt, och inget annat. Den visas bara när två innehåll annars skulle vara
  samma fråga.
- **Den skrivs en gång per fältvärde och källspråk** — «flera», «kvinnorna», «artigt» —
  och är ingen kunskap om målspråket.
- **Ett märkt innehåll är en egen fråga.** Efter märkningen ingår målkortet i varje
  korrekt svar, och R2 prövas som vanligt.

### 6.6 Algoritmen

    F   dagens mål som inte klarats i dag: förfallna, dagens nya och kort som fallit i dag
    I   det tillåtna: införda och dagens presenterade kort (5.2)
    τ   budgeten

Ett steg: sök den giltiga mening av `I` med mål ur `F` som har högst värde (6.1, 6.2,
6.7), rätta svaret, och lägg tillbaka de kort som föll i `F`. Ryms inget mål i någon
mening tas reservstegen i 6.3.

**Kandidaterna jämförs med hur många mål som klaras per sekund:**

    värde = summan av p över meningens mål / förväntad tid för meningen

- **Dagens arbete är redan bestämt.** Varje förfallet kort ska klaras (5.3), och nästan
  all uppskjutning som dagen ger kommer från dem: extra möten med ett starkt kort flyttar
  knappt stabiliteten (7.1). Det enda meningsvalet påverkar är hur lång tid dagen tar.
- **p och inte antal**, eftersom ett mål som faller hamnar i `F` igen.
- **Tiden** kommer ur tidsmodellen (5.5). **Svårigheten** behöver inget eget mått: den
  är budgeten.
- **Vid lika värde** väljs de övriga korten med lägst p (6.2).

Två följder:

- **Påfyllningen slutar av sig själv.** Ett kort som inte är mål kostar tid men klarar
  inget, så inga kort tas med utöver dem meningen behöver. Ett extra mål kostar lika
  lite men sparar en hel mening senare, så mål läggs till tills budgeten sätter stopp.
- **Meningarna blir korta mot dagens slut**, när få förfallna kort återstår.

Vill man ha längre meningar av något skäl som inte gäller korten, till exempel läsvana,
är det ett eget mål och ska stå som ett val. Korten motiverar det inte.

Om algoritmen i övrigt:

- **Problemet löses steg för steg.** Varje fel ger mer arbete, så dagen kan inte
  planeras i förväg. Varje mening väljs för sig.
- **Att välja girigt är korrekt, inte bara billigt.** Girigt urval kan i allmänhet
  lämna kort som ingen mening når. Här kan det inte hända: bara prövbara kort är
  införda, varje kort har ett bevis (3.10), inga kort tillkommer under meningsfasen,
  och budgeten kan inte göra ett kort onåbart (6.3).
- **Sökningen är exakt** (6.7). Den hittar den bästa meningen, inte en bra mening bland
  slumpade kandidater.

### 6.7 Kartan och sökningen

**Generatorns uppgift.** In: det tillåtna, dagens mål och deras p. Ut: den giltiga
mening (6.1) som har högst värde (6.6), bevisat bäst — eller beskedet att inget mål
ryms, och då tas reservstegen (6.3). Giltigheten och värdet ligger utanför sökningen.
Sökningen kan därför bytas mot en bättre utan att något annat ändras, och provsviten
kan jämföra två sökningar på samma mått.

#### Kartan

En renderare ställer frågor medan den skriver: är satsen nekad, är subjektet i plural,
är ordet neutrum? Varje svar leder till nya frågor tills meningen är skriven. Frågorna
och svaren bildar ett träd, och **kartan** är det trädet, avläst i förväg.

Kartan tas fram genom att köra renderaren med ett orakel som svarar på varje läsning,
och gå igenom alla svar. Varje väg ger:

- **villkoret** — vilka fält i specen och vilka ordegenskaper som lästes, med vilka värden
- **utfallet** — vilka kort, former och regler vägen gav och var i meningen, eller att
  renderaren vägrade

Kartan skrivs inte, den läses av. Den kan därför inte glida isär från renderaren, och
inga krav eller byggvillkor skrivs för hand. Det är inte sampling: varje del gås igenom
i sin helhet.

#### Delarna

**Hela satsen går inte att gå igenom, men dess delar gör det.** Mätt 2026-09-14 med
`rendering/karta.py` på den svenska och den engelska renderaren:

                               svenska              engelska
    del                        vägar     utfall     vägar     utfall
    hela satsen, odelad        ≈ 70 000 000 (skattat, svenska)
    satsled                    87 570    8 052      34 569    3 444
    nominalfras                 5 532       98       5 124      128
    verbfras                      258       38       5 688      124
    attribut                      164       14           —        —
    predikativ                    107       36          12       10
    reflexivpronomen               52        7           —        —
    frågeord                       19        8          19        8
    rendera, komplement,          ≤ 8      ≤ 3         ≤ 8      ≤ 3
    adverbial, bisats

Satsens oberoende val — negation, tempus, fråga, adverbial — multipliceras med
varandra, men varje frasfunktion läser bara en liten del av specen. Svenskan tar 569
sekunder och engelskan 374, mest för att satsen gås igenom igen när delarna under den
ändras. Ingen väg går förbi gränssnittet, kraschar eller blir stående och vänta.
Engelskans verbfras är större än svenskans, eftersom do-omskrivningen, kongruensen och
passivens be ligger i den. Antalet olika utfall är det sökningen kombinerar. Svenskans
8 052 satsutfall är sju gånger fler än en tidig prototyps, och sökningens svarstid mäts
därför i steg 2.

**En dels listor sammanfattas bara så noga som anroparna läser dem.** Satsen läser
bara bisatsens första ord, så det räcker att veta att bisatsen inte är tom. Annars får
en del som innehåller sig själv — satsen i bisatsen — allt längre listor för varje varv,
och genomgången tar aldrig slut. Läser en anropare hela längden av en sådan lista
stoppar kartan med ett fel.

Kartan är en övermängd. Ordens egenskaper tas per ordklass ur databasen utan samband
mellan dem, och sökningen binder sedan orden till verkliga lexem. Svenskan och engelskan
är mätta; de andra språken mäts i steg 1b.

**En del** är en frasfunktion med uttryckliga indata: de fält den läser och det
sammanhang den får som argument (kasus, roll, bisats). Läser två delar samma fält i
specen — predikativet läser subjektets numerus — binds de samman av sökningen.

#### Sammansättningen

Byggd för svenska och engelska (`sammansattning/`, steg 2). Kartan sparar varje väg med
sina villkor — vad orakelt svarade på varje läsning — sina händelser och sina anrop, med
vilket specobjekt eller koncept varje argument var. En mening byggs i tre steg:

1. **Vägarna fogas ihop uppifrån.** En väg genom `rendera`, och för varje anrop en väg
   genom den anropade delen med samma argument. Delens namn döps om till meningens
   (`nf.bestämdhet` blir `m.subjekt.bestämdhet`). Vägarna passar ihop bara om samma
   läsning fick samma svar, och om anroparen fick den utdata delen gav.
2. **Orden binds** till lexem med de egenskaper vägarna läste. Konceptens krav prövas så
   fort orden på båda sidor är bundna: verbets valens, subjektets och objektets
   semantik, adjektivets krav på huvudordet och adverbets tempuskrav.
3. **Meningen renderas på riktigt** på båda språken i paret, och korten räknas ur spåret
   med kortmodellen. Kartan är en övermängd, så det är renderingen som avgör.

**Valensen prövas som ramar.** `Koncept.valens` har en bit per ram (docs/BITMASK.md §8):
utan objekt, med objekt, med objekt och indirekt objekt, reflexiv, med predikativ. En
mening fyller exakt en av verbets ramar, begränsad till platserna i verbets mönster, och
en komplementplats i mönstret är obligatorisk. Förut prövades bara att fyllda platser
fick fyllas, och «Blood is.» släpptes igenom. Bitarna är alternativ: `köpa` har valens 6
och tar både «köpa en bok» och «köpa henne en bok».

Meningarna kommer i ordning efter antal ord. Ett mål som hör till ett ord — ett formkort,
en egenskap — binds direkt till ord som bär det. Mätt 2026-09-14 med paret svenska och
engelska: «Mammor simmade.» för `Verb/ar/pret` på 0,2 s, «Is blood big?» för
`inversion_i_fråga` på 4,9 s, «Den stora mamman finns.» för `dubbel_bestämdhet` på 12 s.

Till sökningen (steg 5) återstår värdet, budgeten, entydighetsfiltret och en ordning
efter kort i stället för efter ord. Fält som målspråkets renderare inte läser får sitt
förvalda värde, så andra språket i paret prövas bara med dem.

#### Sökningen

Sökningen väljer en väg i varje del så att delarna passar ihop, och ord ur det tillåtna
så att vägarnas villkor, konceptens krav (6.1 punkt 6) och målen uppfylls.

- **Delarna kombineras nerifrån och upp**, eftersom meningen är ett träd av delar:
  satsen innehåller nominalfraser, som kan innehålla ägare.
- **Varje delresultat sammanfattas med fyra tal:** summan av p för målen, antalet kort,
  P(0 fel) och P(1 fel). De räcker för att räkna värdet och budgeten för hela meningen.
  För två delar A och B är P(0) = P₀(A)·P₀(B) och P(1) = P₁(A)·P₀(B) + P₀(A)·P₁(B).
- **Ett delresultat som är sämre än ett annat på alla fyra kastas.** Det kan aldrig
  ingå i den bästa meningen.
- **Att varje svagt kort är ensamt på sin plats** (6.2) prövas inom delen, eftersom
  positionerna finns i utfallet.
- **Det som gäller hela meningen prövas sist, i värdeordning:** entydighetsfiltret (6.5)
  och villkor 7–8 i 6.1. Den första kandidat som klarar dem är bevisat bäst.

Sökningens svarstid mäts i provsviten. Blir den för lång tas exaktheten upp som ett eget
beslut; sökningen lämnar aldrig tyst en mening som inte är bevisat bäst.

#### Vad kartan också ger

| Specen behöver | Kartan ger |
|---|---|
| kraven och nivåerna (4.1, 4.2) | varje korts minsta meningar |
| prövbarhet och bevis (3.10) | en sökning med kortet som enda mål |
| byggvillkoren (6.4) | villkoren på de vägar där kortet finns |
| entydighetsfiltrets axlar (6.5) | källspråkets karta: vilka fält källmeningen läste |
| «förklara» i rättningen (7.3) | ett besluts andra utfall är grenen bredvid |
| båda språken kan uttrycka meningen (6.1) | vägarna där renderaren vägrar |

#### Vad renderarna måste uppfylla

1. **Allt läses genom vägar kartan ser** — specens fält, ordens egenskaper och ljud
   (italienskans `lo`/`il` beror på nästa ords första ljud). Läser en del något förbi,
   stoppar genomgången med ett fel, och förbigångarna i steg 1 hittas av sig själva.
2. **Renderaren är delad i frasfunktioner med uttryckliga indata.**
3. **Ingen del är för stor att gå igenom.** Blir en del det, delas den. Storleken mäts
   per språk.
4. **Renderaren får aldrig titta på en konceptnyckel.** `karta.Symbol` kastar
   Förbigång både vid jämförelse och vid uppslagning, så den kan omöjligt skilja
   `räkn_2` från `räkn_ord_2`. Konsekvensen är att varje skillnad renderaren behöver
   göra mellan två ord i samma ordklass **måste stå i datan**. Två kolumner finns för
   det, och båda tillkom när ett hål skulle lagas:

   * `Koncept.roll` delar en ordklass som bär två syntaktiska roller —
     `Räkneord/grundtal` mot `Räkneord/ordningstal`, `Kvantifikator/bestämning` mot
     `Kvantifikator/huvudord`, `Negationsadverb/satsnegation` mot
     `.../satsadverbial`. Rollen lämnas ut som en del av klassnamnet genom
     `Uppslag.ordklass`, alltså samma väg som ordklassen alltid gått.
   * `Koncept.numeruskrav` säger vilka numeri en bestämning tillåter hos huvudordet,
     som en bitmask — samma mekanism som `Adverb.tempuskrav`. Utan den bygger kartan
     lika gärna "varje böcker".

   Saknas den skillnaden i datan finns bara två hederliga utvägar: fyll datan, eller
   håll ordet utanför kartan. Att låta renderaren gissa är ingen.

---

## 7 · Bedömningen

### 7.1 Varje möte bokförs

Varje gång ett kort prövas i en mening eller en ensamövning (6.3) bokförs det — även om
kortet inte var förfallet och även om det redan mötts samma dag. Introfasen bokför
ingenting (5.4). I meningsfasen bokförs inte kort vars betyg beror på en tolkning
rättaren inte kan välja (7.3).

Mätt i FSRS:

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
användarens.

**Renderaren behöver inte fånga varje nyans** (avgjort 2026-09-19). Ingen
renderare täcker allt ett språk kan uttrycka, och en jakt på varje nyans är ett
arbete utan slut. Omrättningen är utvägen: användaren markerar sitt svar som
rätt, FSRS får det betyget, och flaggan gör fallet till en rad i granskningen av
datan (3.4) i stället för ett stopp. Det som däremot förblir strängt är att
rättningen aldrig gissar vad användaren menade — den räknar fram sitt betyg ur
diffen, och användaren är den som får ändra det. `Hard` och `Easy` räknas aldrig fram, inte heller ur svarstiden.

**Betygen går till FSRS när användaren går vidare** till nästa mening, inte när diffen
räknats fram. Omrättningen kan ändra vilka kort som graderas: markeras ett underkänt
ordkort som godkänt blir dess formkort graderade, och attributionen i 7.3 görs om med
markeringen.

`fsrs` tar bara hela betyg. Något «0,7 av ett Good» finns inte och ska inte
efterliknas (R4).

### 7.3 Vilket kort föll

**Först paras svaret ihop med varianterna.** Enheten är renderarens positioner: de
utskrivna orden med sitt spår (6.2). Svaret delas i ord och paras med varje godtagen
variants positioner (6.5), så att flest ord stämmer exakt. Ett ord som delats i satsen
(`ruft … an`) är två positioner med samma kort. Japanskan har inga mellanslag; där paras
svaret tecken för tecken och förs sedan över till positionerna genom spåret.

**Sedan väljs varianten.** Den variant som har minst avvikande positioner är den
användaren skrev. Korten i den varianten graderas; ett kort som bara finns i en annan
variant är ograderat, eftersom det inte prövades.

**Sedan knyts avvikelserna till kort.** En avvikande position har de kort som bestämde
den, enligt spåret: formens kort, och för ett ord på fel plats den regel som placerade
det. Rättaren går igenom de tolkningar som stämmer med svaret, i två steg:

1. **Prerekvisit.** Kan man inte ordet kan man inte heller dess form, och väljer man fel
   form kan man inte heller den formens ändelse (avgjort 2026-09-14):
   - Föll `ord` är formkorten ograderade.
   - Förklarar ett beslut som väljer cell avvikelsen — svaret är den form ett annat utfall
     hade gett, «she read» för «reads» — har beslutet fallit, och den valda cellens
     formkort är ograderade.
   - Är svaret en form som inte finns — «she readed» — har formkortet fallit och beslutet
     klarats.

   Ett formkort gäller strängen i en klass, som svenskans er-verb `-te` mot ar-verbens
   `-ade`, och de felen blir former som inte finns (`köpade`). Att utelämna engelskans
   `-s` är att inte markera tredje person, alltså kongruensen. Har användaren i själva
   verket valt rätt men glömt ändelsen får valet skulden: det kommer tillbaka snart och
   klaras, och formkortet mäts en annan gång.
2. **Minsta förklaring.** Kan ett kort förklara alla avvikelser väljs det framför
   flera kort som felat oberoende av varandra. `ett stort hus` → `en stor hus`
   avviker på två ställen, och genuskortet förklarar båda.

**Tre saker som steg 1 vilar på, och som stod underförstådda** (avgjort 2026-09-26).
Utan dem var rättningen rent positionell — varje kort som bestämde ett avvikande ord föll
— och «Time suits.» besvarad «Time fits.» fällde FEM kort, varav fyra hade gjort allt
rätt: ordföljden, kongruensen, tempus och ändelsen. Ett ordslarv skrev alltså falska
FSRS-betyg på grammatiken.

- **Ordkortet gäller LEXEMET, inte den ställda formen.** Ett svar är klarat om det är en
  form reglerna kan bygga av rätt lexem (3.3), som glosan. Krävdes exakt formen föll ordet
  för en glömd ändelse — och då ograderade stegen ändelsekortet, så ingen bar felet.
- **«Fel plats» betyder att ordet flyttat, inte att det är felstavat.** Regeln som
  placerade ett ord får skulden bara för ett ord på fel plats, och ett ord har flyttat när
  dess sträng finns i svaret men inte där den skulle, eller inte finns alls. «Time fits»
  rör inte ordföljden; «stands Time» gör det.
- **Ett formkort ograderas bara när något ANNAT kort bär felet.** Stegen förutsätter att
  det finns ett beslut att lägga skulden på, och ibland finns det inte: engelskans «how
  many books» blir plural av frågedeterminantens krav, inte av något `val`-kort.
  Ograderades pluraländelsen ändå föll ingenting, och «how many book …» blev ett perfekt
  svar. Då är formkortet det enda kort som kan bära felet. **Rättningen får aldrig tiga.**

Punkt 3 i stegen — att skilja «en form som inte finns» från «den form ett annat utfall
hade gett» — kräver att meningen renderas om, alltså entydighetsfiltret (6.5). Tills det
finns graderas cellbesluten positionellt, och 7.3 säger själv vad det kostar: «har
användaren i själva verket valt rätt men glömt ändelsen får valet skulden».

**Vad «förklara» betyder beror på korttypen:**

| Kort | Förklarar avvikelserna när |
|---|---|
| `ändelse`, `oregelbunden`, ljudregel | avvikelsen ligger i kortets del av formen (3.4) |
| `egenskap`, `rektion`, övriga `regel` | meningen renderad med ett annat utfall av beslutet stämmer med svaret på alla ställen beslutet styr |

`ett stort hus` renderat med utrum blir `en stor hus`, som stämmer med svaret på båda
ställena genuset styr. Mot svaret `ett stor hus` stämmer det inte — `ett` skulle bli
fel — och där är det adjektivets ändelse som föll.

**Ett kort vars betyg är detsamma i alla tolkningar bokförs.** Ett kort vars betyg
skiljer sig mellan tolkningarna bokförs inte, och användaren får inget besked om det.
Samma sak gäller när två varianter har lika få avvikelser och ger kortet olika betyg.

**Ett kort som inte graderades på en felaktig plats bokförs inte mer samma dag**
(avgjort 2026-09-14) — varken som mål eller som övrigt kort, och vare sig det var
tvetydigt eller ograderat genom prerekvisiten. Är det förfallet flyttas det till nästa
dag med FSRS-tillståndet orört. Användaren har sett facit just där, och ett rätt svar
samma dag mäter minnet av facit och inte kortet — samma skäl som villkor 8 i 6.1. Annars
skulle FSRS få ett rätt svar och skjuta upp kortet längre än användaren klarar. Kortet
som föll övas igen samma dag som vanligt: felet är bokfört, så ett rätt svar efteråt är
återinlärning. Det är en verklig gräns för vad en diff kan
avslöja, och varje sådant fall är en brist i generatorn (R5). Villkor 7 i 6.1 gör att det
bara kan ske vid två samtidiga fel, genom ett fel i programmet, eller när budgeten har
släppts (6.3).

Gränsen nås sällan. I den gamla loggen, mätt med tre regelkort, skilde sig 36 av
44 felaktiga meningar (82 %) från facit på exakt ett ställe, och ingen på tre
eller fler. En regel kan bara få skulden om den styr ett ställe där svaret
avviker. Talet ska mätas om med alla regelkort (punkt 11).

Ställ **inte** en isolerande fråga direkt efter ett tvetydigt fel. Användaren har
då just sett facit, och ett rätt svar skulle skjuta upp kortet längre än hen
klarar.

### 7.4 Korrekta svar som inte fanns bland varianterna

**En synonym.** Skriver användaren ett annat lexem för samma koncept än målet — `också`
där målet är `även` — underkänns svaret inte. Systemet svarar: rätt, men byt ut *också*
mot ett annat ord.

- **Det nya försöket är ett riktigt prov.** Användaren har inte sett facit, bara fått veta
  att ett annat ord söks. Efter ledtråden innehåller varje korrekt svar målet (R2).
- **Målkortet graderas på det nya försöket**, alla andra kort på det första svaret.
- **Synonymens eget ordkort bokförs som rätt** om det är infört, eftersom användaren
  faktiskt hämtade det ordet ur minnet (7.1).
- Det gäller oavsett om synonymen är införd eller inte.

En kommentar i uppgiften i förväg vore sämre: den visar ett ord på målspråket varje gång
ordet är mål, även när användaren aldrig hade tänkt på synonymen.

**En korrekt variant som renderaren missade.** Diffen underkänner den, och användaren
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
Kortet är förfallet, och hör alltså till dagens mål, när andelen rätt i fönstret är
under 0,9 (6.2).

Fönstret är 1/(1 − 0,9) = tio möten, och tröskeln är retentionsmålets tolerans.
Mekanismen finns byggd och testad i dag och tas över som modell.

**För ett övervakat kort är R andelen rätt i fönstret.** FSRS bedömer ett kort som setts
femton gånger samma dag som mycket starkt, även när användaren gör fel, och
urvalsregeln (6.2) skulle då aldrig välja det som mål. Sju rätt av tio ger R = 0,7, och
kortet blir mål som alla andra svaga kort. För de här korten är det också en bättre
skattning än FSRS, eftersom förfallodagen inte betyder något för dem.

Om ett kort är **schemalagt** eller **övervakat** avgörs av hur ofta det faktiskt
mötts enligt loggen, inte av en simulering: kortet är övervakat när fönstrets tio
möten har skett på färre än tio dagar, alltså oftare än en gång om dagen. Ett nytt
kort är schemalagt tills det har visat sig. På så sätt sorterar
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

Radtalen är mätta 2026-11-11; de som stod här förut var från 2026-09-14 och
underskattade det som raderas med nästan hälften.

| Del | Rader | Beslut |
|---|---|---|
| renderarna, sju språk (`rendering/`) | 6 936 | står kvar — utökas med redovisade beslut och delas i delar för kartan (6.7) |
| språkdatabasen och paradigmen | — | står kvar |
| ordboksbygget | 2 200 | står kvar |
| FSRS-integrationen (`fsrslager/`) | 131 | skriven, tunn (steg 3c) |
| fönstret för övervakade kort | — | tas över som modell |
| näten och mätkorpusen | — | blir acceptanskrav för det nya; de fjorton nät som bara prövar den gamla kärnan ligger i `GAMLA_NÄT` (`alla_prov.py`) och raderas med den |
| befolkning · schemaläggning · pass (`kort/`) | 4 875 | raderas |
| generator · urval · poäng (`generator/` utom `rattning.py`) | 1 833 | raderas |
| rättningen (`generator/rattning.py`) | 1 179 | raderas |
| gränssnittet — webben (`webb/` 2 361) och kommandoraden (`cli/` 1 930) | 4 291 | raderas med den gamla kärnan; ett nytt byggs i steg 9 |
| **summa som raderas i steg 9b** | **12 178** | |

**SKARVEN ÄR MÄTT, och den är två rader** (2026-11-11). Utanför sig själv
importerar `rendering/` bara `generering.granskning` och
`kaikki_mappning.paradigm`. Ingen av dem raderas. Och i andra riktningen går
det bara en tråd:

| Från | Till |
|---|---|
| `rendering/uppslag.py:38` | `generering.granskning._former_per_cell` — den enda symbol den nya kärnan hämtar ur `generering/` |
| `generering/meningsgranskning.py:48` | `generator.rattning.ORDMELLANRUM` |
| `generering/meningsgranskning.py:137` | `kort.schemalaggning.spec_json` |

Ingen annan import går mellan kärnorna. Steg 9b är därför en radering plus två
inlinade symboler i `meningsgranskning.py`, inte ett ingrepp med okänd
omfattning. Det som håller kvar den gamla kärnan är inte beroenden utan att
webben och kommandoraden är det enda sättet att köra programmet.

### 8.2 Vad som inte skrivs om

Undanhållandet, ett-betyg-per-dygn, medföljande kort, reservutgången,
nödfallstiern, tomgångsspärren och nödutgången fanns bara för att meningarnas
innehåll upptäcktes i efterhand. R1 tar bort orsaken, och därmed behovet.

### 8.3 Redovisning

Renderaren hämtar allt via `Uppslag`. Före steg 1 var fyra anrop instrumenterade:

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

Steg 1 gör fem saker per språk:

1. **Varje beslut blir ett anrop** (se nedan).
2. **Förbigångarna lagas**, eftersom de gör befintliga korttyper omätbara.
3. **De hårdkodade orden blir lexem**, så att de får `ord`-kort.
4. **Renderaren delas i led med uttryckliga indata**, så att kartan kan gå igenom varje
   del uttömmande (6.7). Kraven och byggvillkoren läses sedan ur kartan i stället för att
   skrivas för hand. Ett anrop under renderingen hade kommit för sent, men kartan finns
   innan något byggs. Den ger nivågrafen dess kanter (4.2), generatorn förmågan att
   bygga mot en regel (6.4), och underlaget för prövbarheten (3.10) och
   införandeordningen (5.6).
5. **Positionerna räknas ut ur renderingen** (`rendering/spår.py`) i stället för att
   märkas för hand.
6. **Godtagbara utfall redovisas** (se nedan), så att entydighetsfiltret och rättningen
   känner varianterna.
7. **Sammansmälta ord redovisas** (se nedan), så att positionerna följer med genom dem.

#### Anropen

Allt renderaren vet om språket hämtas genom `Uppslag`. Fem anrop bär kunskap som kan bli
kort:

| Anrop | Vad det redovisar | Alternativ |
|---|---|---|
| `form(lexem, cell)` | ordformen | — formkortets del av formen (3.4) |
| `egenskap(lexem, namn)` | en egenskap hos ordet: genus, reflexivt verb, komparation | egenskapens värden i språket |
| `rektion(koncept, slot, namn, värde)` | vad ett styrande ord kräver: infinitivmarkör, kasus | kravets värden i språket |
| `regel(val, utfall)` | ett val mellan namngivna utfall: bestämning, tempusform | valets övriga utfall |
| `ordning(namn, före, efter)` | att ett led står före ett annat: svo, adverbial_sist | de två leden omkastade |

Övriga läsningar — ordklass, lemma, om en cell finns, konceptets person — bär ingen
kunskap men går ändå genom `Uppslag`, så att kartan ser dem. En egenskap utan värde i
datan redovisas inte: har "du" inget genus finns inget att kunna. Renderaren grenar på
det utfall `regel` lämnar tillbaka och inte på specen, och markerar med `led` vilket led
i specen den renderar:

```python
BESTÄMNING = Val("bestämning", ("possessiv", "obestämd_artikel", "bestämd_suffix", …))

bestämning = self.u.regel(BESTÄMNING, naturlig)      # redovisat — kan tvingas fram
if bestämning == "possessiv": …
self.u.ordning("attribut_före_huvudord", attribut, [huvudord])
def eliderar(self, första, andra):                   # inte redovisat — sker tyst
```

Anropet gör beslutet till ett kort. Var i kartan anropet finns ger kortets krav och
byggvillkor.

**Positionerna räknas ut.** Spåret tvingar varje beslut till vart och ett av dess andra
utfall och renderar om. Ord som ändras är positioner, och ett ord som bara finns i den
tvingade meningen ger en lucka. Omrenderingarna är samtidigt de alternativ rättningen
jämför med (7.3). Spåret kontrollerar också renderaren: en ordningsregel som inte
stämmer med meningen, eller en form som slås upp men inte syns, är ett fel.

Det gör tre handskrivna saker onödiga: att logga genus bara i singular, att logga en
ordföljdsregel bara där den syns, och att märka vilka ord ett beslut rör.

**Godtagbara utfall.** Ett beslut kan ha flera utfall som är rätt i sammanhanget: «hon
läste igår» och «igår läste hon», spanskans `leo` och `yo leo`. Renderaren redovisar dem
med beslutet — `regel(val, utfall, godtagbara)` — och spåret skiljer då två sorters
alternativ:

| Alternativ | Används till |
|---|---|
| godtagbart | en variant: rättningen godtar den (7.3), och målkortet måste finnas i den (R2, 6.5) |
| övrigt | ett fel: positionerna och förklaringen räknas mot det (6.2, 7.3) |

Vilka utfall som är godtagbara är språkkunskap och skrivs per beslut. En ordningsregels
omkastning är alltid ett fel. En godtagbar annan ordföljd — adverbialet först, med omvänd
ordföljd — är ett eget val med två godtagbara utfall.

**Sammansmälta ord.** När två uppslag skrivs som ett ord — franskans `à` + `le` → `au` —
står båda kvar i spåret, och positionen är det sammansmälta ordet. Sammansmältningen är
själv ett beslut (TYSTA_BESLUT R13–R14) och redovisas som ett val, så att spåret vet vilka
uppslag som blev ett ord. Svenskan har inga sammansmältningar; det byggs i steg 1 för
franska, spanska och italienska.

#### Svenskan, 2026-09-13

Byggd och mätt. Inventeringens 29 tysta beslut, de fyra ordföljdsreglerna och
förbigångarna A6 och A8 redovisas som 11 val med 35 utfall, 22 ordningsregler, tre
egenskaper och infinitivmarkörens rektion (`rendering/sv.py`).

- **Texten är oförändrad** för 99 818 av 100 000 specar
  (`ordbok/verktyg/renderarfacit.py`). De 182 skillnaderna är rättelser:
  - ett pluralpronomen kongruerar i plural: «De är modiga», inte «De är modig» (103)
  - ett subjekt som ersätts av vem eller vad renderas inte längre, och kan därför inte
    få frågan att vägras (38)
  - «vilken nyfiken rygg» i stället för «vilken nyfikna rygg» (30)
  - vilken med superlativ vägras (11)

  En pronominell genitivägare («mig bok») vägras också; samplaren bygger inga sådana.
  De övriga sex språken har noll skillnader.
- **Spåret håller** för alla 88 297 renderbara meningar: ingen ordningsregel motsäger
  meningen, och ingen form slås upp utan att synas.
- **Den gamla kärnans nät håller** (`alla_prov.py --snabb`, 8 av 8). `ordning` anropar
  även den gamla `ordföljd`-loggen, som tas bort med den gamla kärnan (8.1).
- **Godtagbara utfall är inte redovisade.** Varje svenskt beslut har i dag ett enda
  godtaget utfall, och renderaren kan till exempel inte skriva adverbialet först. Det görs
  innan svenskan används som målspråk.

**Steg 1:s prov** (`ordbok/verktyg/redovisningsmätning.py`, 5 000 meningar):

    ord per mening                             4,9
    kort per mening, ord och former inräknade  18,5
    högst samtidigt svaga kort (6.2)           10,8
    förväxlingsbara beslut (villkor 7)         0,6 %

**Attributionen håller.** En mening rymmer i snitt elva kort som kan vara svaga samtidigt
utan att dela plats, medan budgeten (6.3) bara släpper in ett fåtal mål. Det som
begränsar är alltså budgeten och inte positionerna. De förväxlingsbara besluten är nästan
alla kongruens där genuset bara syns på det kongruerande ordet: «ölet … blivit litat»
kan vara substantivets genus eller participformen. Där hindrar villkor 7 att båda är
svaga samtidigt.

#### Engelskan, 2026-09-14

Byggd och mätt (`rendering/en.py`). Besluten redovisas som 10 val med 33 utfall, 19
ordningsregler, en egenskap (komparationen) och två rektioner: infinitivmarkören och
komplementets form (`stop reading`, TYSTA_BESLUT A10).

Tre saker är gjorda annorlunda än i svenskan:

- **Ordets första ljud och om ett verb tar do är vanliga läsningar** (`Uppslag.förljud`,
  `Uppslag.operator`), inte egenskaper. Båda syns i ordet självt. Lästa som egenskaper
  gick de inte att skilja från artikelvalet och do-valet, eftersom båda ger samma
  felaktiga mening.
- **Passiven är inget val.** Engelskan har bara en, och den syns i be:s tempus och
  kongruens och i participet.
- **Attributet är ingen egen del för kartan**, eftersom artikeln framför det väljs på dess
  första ljud.

Resultat:

- **Texten skiljer sig för 8 934 av 100 000 specar, och alla skillnader är rättelser:**
  - futurum perfekt: «will have read», förut «has read» och nekat «will not read» (5 546)
  - motsägelsefulla specar vägras: både ja/nej-fråga och frågeordsfråga, eller uppmaning
    och fråga (1 590)
  - ett frågeord som subjekt tappade tempus: «who will discuss», förut «who discusses» (936)
  - modalverben renderas i alla personer och nekade: «we may solve», förut vägrat (610)
  - ett frågeord som subjekt kongruerar i tredje person singular och renderar inte svaret:
    «what was learned», förut «what were learned» (210)
  - «how much» och «which» med superlativ vägras (42)

  Svenskan har samma två första rättelser: «ska ha läst», förut «har läst» (5 549), och
  motsägelsefulla specar vägras (1 617). Spåret håller där för alla 86 718 renderbara
  meningar.
- **Spåret håller** för alla 87 084 renderbara meningar.
- **Kartan** går igenom på 374 sekunder, utan förbigångar, krascher eller väntande
  vägar (6.7).

**Steg 1:s prov** (5 000 meningar):

    ord per mening                             5,8
    kort per mening, ord och former inräknade  20,2
    högst samtidigt svaga kort (6.2)           11,7
    förväxlingsbara beslut (villkor 7)         0,5 %

De förväxlingsbara besluten är nästan alla predikativets artikel mot frasens bestämning:
«she is doctor» kan vara båda.

---

## 9 · Byggordningen

    0   böjningsreglerna per språk         svenskan och engelskan gjorda, granskning av komparationen kvar; slutna ordklasser och fem språk kvar
    1   renderarna redovisar sina beslut   svenskan och engelskan byggda och mätta (8.3), utom godtagbara utfall; fem språk kvar, inventerade i TYSTA_BESLUT.md
    1b  kartan                             kräver 1; rendering/karta.py; svenskan och engelskan klara (6.7)
    2   sammansättningen                   kräver 1b och 3; delarna kombineras till meningar med ord ur det tillåtna (6.7) — sökningens kärna, utan värde och budget; sammansattning/: byggd för svenska och engelska, efter antal ord
    3   kortmodellen                       kräver 0; kortmodell/: korten för svenskan och engelskan gjorda, och besluten kopplade till kort; delen av formen per kort kvar (3.4)
    3b  datamodellen                       möten, betyg och omrättningar, nivåer, dagens tilldelning, presenterade och införda kort, sparat tempo, bevis, karantän, felrapporter, inställningar, kursens språkpar; kurs/: byggd, en fil per maskin, tillståndet räknas fram ur mötena
    3c  FSRS-lagret                        kräver 3b; tillstånd och betyg, optimeringen av parametrarna (7.1), mätningen av p (6.2); fsrslager/: byggt utom optimeringen av parametrarna och mätningen av p
    4   nivåerna och grafen                kräver 2 och 5a; kraven är kortens minsta mängder per språkpar (4.2), nivåerna grafens starka komponenter (4.1); kontrollerar invarianten i 4.3; nivaer/: version 1 tar den första meningens kortmängd utan krympning (4.2), än så länge utan språkpar och filter; krympningen är en senare förbättring, och dess nej-frågor går fort med förklaringar (sammansattning/forklaring.py)
    5a  entydighetsfiltret och märkningen  kräver 2; varianterna och källmeningens märkning (6.5); behövs av 4 och 5
    5   sökningen                          kräver 5a och 3c; värdet, budgeten, villkoren 6–8 i 6.1; svarstiden mäts med en tidig prototyp innan steg 6–9 byggs
    5b  aspektkrav på koncept              parallellt (6.5)
    6   dagspasset och införandet          kräver 4 och 5; presenterat och infört (5.1), prövbarheten med bevis och karantän (3.10), introövningarna (5.4), tidsmodellen (5.5), täckningen (5.6); passet/: två faser, glosan för innehållsord och meningen för funktionsord (5.4), ensamövningen som reservsteg 1 (6.3), villkor 1, 4, 5, 6 och 8 i 6.1; tidsmodellen byggd (`passet/tid.py`), täckningen ordnar nivåerna men inte orden inom en nivå (5.6); villkor 3 och 7 kräver 5a
    7   urvalet                            kräver 6; p och värdet per mening (6.2, 6.6), reservstegen (6.3)
    8   rättningen                         kräver 5; parningen, förklaringen per korttyp, synonymer och omrättningen (7.2–7.4); rattning/: diffen per kort, omrättningen och prerekvisitstegen byggda; parningen mot flera varianter kvar, liksom stegens tredje punkt och minsta förklaring, som båda kräver 5a
    9   gränssnittet                       kräver 6–8; introövningarna (5.4), meningen och rättningen med omrättning och flaggor (7.2), knappen för nya nivåer (4.4), inställningarna för tid, dygnsgräns och svårighet (5.1, 5.7)
    9b  den gamla kärnan raderas           kräver 9; när det nya passet går att använda från början till slut (8.1); skarven i Uppslag.ordning tas bort
    P1  lektionerna                        parallellt — punkt 10
    P2  frekvenserna                       parallellt — punkt 10
    P3  provsviten                         parallellt — simulerade kurser (3.10)
    P4  valideringen                       parallellt — kaikki, AI-granskning, användarflaggor (3.4)
    P5  täckningen                         parallellt — den nya täckningen per kort, läst ur formtabellen (3.4) och kartan (6.7) utan att bygga meningar (5.6); ersätter både kandidatmängden och ordningen i 5.6, som tills dess är nästa nivå med mönsterkorten först
    P6  semantiken                         parallellt — meningarna är grammatiska men befängda («Weather stands.», «See under lives!»); mekanismen finns (bitmasken i `docs/BITMASK.md` §11), tabellen är halvfylld och kravet släpps tyst; planen nedan

**Kärnan byggs först för ett språkpar: svenska och engelska.** En kurs har två språk.
Entydighetsfiltret behöver källspråkets karta (6.5), och målspråket behöver allt:
böjningsregler, redovisning och karta. Därför görs steg 0, 1 och 1b för engelskan före
steg 2, och resten av kärnan byggs och prövas på paret. Engelskan har näst minst att
redovisa (23 tysta beslut), och Julius kan bedöma båda språken. De övriga fem språken tar
samma steg när paret fungerar från början till slut, med samma verktyg: facit
(`renderarfacit.py`), spåret, mätningen (`redovisningsmätning.py`) och kartan.

**Sammansättningen kommer före nivåerna.** Ett korts krav är de kort som finns i dess
minsta meningar (4.2), och att hitta de minsta meningarna är att sätta samman delarna ur
kartan.

**Steg 1 är det billigaste sättet att upptäcka om modellen håller.** När renderarna
redovisar går det att mäta hur många regler en mening faktiskt använder, och alltså
om attributionen fungerar med ett par hundra regelkort i stället för dagens tre.
Håller den inte syns det innan något har raderats. För svenskan höll den (8.3).

**Rent arbete, utan kvarstående beslut:** böjningsreglerna och redovisningen för övriga
språk, aspektkraven på adverbialkoncepten, och datafelen i punkt 12. Lektionerna och
frekvenserna väntar på beslut (punkt 10).

### Semantiken (P6) i fem steg

Meningarna är grammatiska men befängda: «Weather stands.», «Love suits.», «See under
lives!», «Who says?» utan objekt. Mätt 2026-10-06 på trettio meningspar spridda över
kursens 171 nivåer — ingen av dem är grammatiskt fel av det här skälet, men många är
semantiskt tomma, och dag ett visar tre av dem.

**Mekanismen finns redan och behöver inte uppfinnas.** Tjugo semantikbitar på
`Koncept.semantik` matchas mot `MönsterKrav.tagg` med OCH (`docs/BITMASK.md` §11).
Bitarna sitter på KONCEPTET, inte på lexemet, så varje ifylld rad gäller alla sju
språken. Arbetet är att fylla tabellen och att låta kravet bita.

1. **Kravet får inte släppas tyst.** `generator/urval.py:219` gör
   `träffar or kandidater`: uppfyller inget koncept kravet används alla kandidater.
   Därför biter semantiken inte alls i dag — `fys_ha` har ett objektskrav, och
   «Have worlds!» byggs ändå. Bygget ska stanna i stället. Det här steget är
   **först** därför att det gör de andra mätbara: innan kravet biter går det inte
   att se effekten av en ifylld bit.

2. **Koncepten får sina bitar.** 409 av 736 koncept har `semantik = 0`, och
   eftersom matchningen är OCH kan ett sådant koncept inte fylla NÅGON taggad
   plats. Det är en rad per koncept. Förslagen kan komma ur en språkmodell, som
   för böjningen; kontrollen är ett nät.

3. **De nio verben får sitt subjektskrav.** Tjugo verb saknar taggat
   subjektskrav och elva ska sakna det: modalerna, kopulorna, `asp_börja` och
   `ext_verka` tar med rätta vilket subjekt som helst. Kvar är `pos_stå`,
   `pos_sitta`, `pos_ligga`, `gen_passa`, `gen_skydda`, `gen_växa`, `per_lukta`,
   `per_smaka`, `eko_v_kosta`.

4. **Komplementen får krav.** Nittiosju komplementkrav, noll med tagg. Därav
   «See under lives!» och «Se mot världar!».

5. **Obligatoriska argument.** «Vem säger?» byggs därför att objektsplatsen får
   stå tom: ett krav säger i dag vad objektet måste VARA, aldrig att det måste
   FINNAS. Det är ett fält till på `MönsterKrav`.

**Varje steg kräver ett ombygge** av kartan och nivåerna, eftersom färre lagliga
kombinationer kan göra kort oprövbara — och stämpeln (R7) vägrar annars att
starta passet. Räkna en timme obevakad maskintid per steg och språkpar.

**Ett semantiskt krav är inget kort.** Renderaren VÄLJER inte semantik; den
hindras från olagliga kombinationer, precis som `restriktioner.py` hindrar
oräknebara substantiv i plural. Alltså inga nya nivåkort, och R3 gäller
oförändrat.

**Falsifieringen är två listor, inte en.** Den ena är meningar vi dömt befängda
och som inte längre får gå att bygga. Den andra är meningar vi dömt riktiga och
som fortfarande måste gå. Utan den andra mäter arbetet bara hur mycket det
förbjuder, och ett krav som förbjuder allt ser ut som en framgång.

---

## 10 · Öppna frågor

Frågorna väntar på Julius. Lektionerna och frekvenserna behövs först i steg 6 och 9; de
övriga blockerar inte bygget.

- **Lektionstexterna** (5.4, steg P1). Varje regelkort ska ha en lektion på varje
  källspråk, alltså flera tusen texter. Förslag: **exemplen renderas** — en mening per
  utfall, ur regelns egna alternativ (spåret, 8.3) — så att de är korrekta av
  konstruktion. Bara den förklarande texten skrivs av en språkmodell, per regel och
  källspråk. Den granskas av AI mot exemplen och fångas av användarflaggan «lektionen är
  fel». Julius granskar svenska och engelska.
- **Frekvensdatan** (5.6, steg P2). Förslag: **ordens frekvens** ur `wordfreq`, som har
  mätta frekvenser för alla sju språken ur flera korpusar, summerad över ett lexems
  former. Ett ord med flera betydelser går inte att dela upp ur en ordlista, så
  betydelserna får lika stora andelar tills en betydelsemärkt korpus finns — ett
  tillfälligt val. **Dragens frekvens** — dåtid, första person plural, fråga, negation —
  räknas ur trädbankerna i Universal Dependencies, som märker de flesta av dragen.
  Eftersom dragen hör till betydelsen räcker det att mäta dem där de är märkta.
  Mappningen från trädbankens drag till specens fält skrivs en gång per fält.

- **Svensk komparation** — vilka adjektiv som ska kompareras med `mer` i stället för
  med en syntetisk komparativ (`intressantare`), och vilka former som är fel i datan
  (`ordbok/regelkontroll/sv.md`). De fyra andra frågorna om böjningsreglerna avgjordes
  2026-09-13: former som inte syns i stavningen, eller som gäller en sluten grupp, blir
  kort per ord (3.4).
- **Renderarnas beslut** — tre frågor i `paradigm/TYSTA_BESLUT.md` punkt 6: om
  skiljetecken är kort, om ett språks fasta val (passé composé) är ett kort eller en
  del av lektionen, och om `vem`/`vad` är ett läromoment för en svensk.
- **Komparationens typ.** Om ett adjektiv kompareras syntetiskt (`större`) eller med
  `mer` syns inte i ordet och är kunskap per ord. Är det en `egenskap` — det syns på
  `mer`, alltså på ett annat ord — eller ett undantagskort? Den svenska renderaren
  redovisar den i dag som egenskap (8.3); blir svaret undantagskort ändras bara
  kortmodellen.
- **Översättning åt båda hållen** (Julius 2026-09-14, tas upp efter kärnan). Att
  översätta från målspråket till sitt eget språk prövar förståelse, en annan förmåga än
  den kärnan i dag prövar, som är att producera målspråket. Svaret skrivs dessutom på
  användarens eget språk, så de kort som graderas i dag säger inget om målspråket. Det
  behöver alltså egna kort eller en egen bokföring. Det löser inte behovet av märkning
  (6.5), eftersom produktionen av *elles* fortfarande måste gå att öva.
- **Japansk skrift.** Stavfel räknas som fel (7.2), men att skriva ett ord med kana när
  facit har kanji är ett val av skrift, inte ett stavfel. Ska båda godtas?
---

## 11 · Acceptans

| Mått | I dag | Krav |
|---|---|---|
| kort i en mening som varken är införda eller presenterade i dag | 4 | 0 |
| paket som blivit delvis införda | ej mätt | 0 |
| läsningar i renderarna som går förbi kartan | 22 kända i fem språk; svenskans och engelskans kartor hittar 0 | 0 — genomgången stoppar på dem (6.7) |
| meningar som inte är bevisat bäst | ej styrt | 0 |
| källmeningar som ställs två gånger samma dag | ej styrt | 0 |
| införda kort som inte är prövbara | ej mätt | 0 |
| kort i dagsplanen utan bevis vid passets start | ej mätt | 0 |
| kort i karantän | ej mätt | 0 — varje fall är en felrapport |
| möten i introfasen som bokförs | ej mätt | 0 |
| nya kort som presenteras utanför introfasen | 25 av 32 | 0 |
| andel kortmöten som bokförs | 13 % | 100 % |
| regler som renderaren använder utan att de är upplåsta | ej mätt | 0 |
| meningar med P(≥2 fel) > τ | ej styrt | 0, utom reservsteg 2 i 6.3 |
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
| 24 läsningar av befintliga kort går förbi instrumenteringen i sex språk (`hjälpverb`, `prenominal`, `ja_adjektiv_typ`, konjunktivrektion, infinitivmarkör …); svenskans två är lagade | korten kan inte prövas | steg 1; `TYSTA_BESLUT.md` punkt 1 |
| tio ord skrivs ut utan att vara lexem (`ne`, `est-ce que`, japanskans partiklar) | inget kort bär skulden om de blir fel | steg 1; `TYSTA_BESLUT.md` punkt 2 |
| de romanska renderarna skriver alltid ut subjektspronomenet (`yo leo`) | varianten `leo` finns inte | variantsökningen (6.5) |
| `urval.py:219`: `träffar or kandidater` | ett semantiskt krav som inte går att uppfylla släpps tyst, och meningar bryter mot verbets krav | stoppa bygget i stället för att släppa kravet |
| kandidatmängden är nästa nivå, inte «upplåsta, oinförda, prövbara» (5.6) | ett vanligt ord kan komma senare än ett sällsynt mönster | täckningen (5.6), som eget arbete; se noteringen där |
| ingen provsvit i pytest-mening (inga `test_*.py`) | näten ligger som fristående skript i `ordbok/verktyg/` och körs genom `alla_prov.py`; de täcker attribution, rättningens positioner, de nya konstruktionerna, ordföljd, passet och tjänsterna, men ingenting kör dem automatiskt | steg P3, om en riktig svit behövs — ingången finns |
| `neg_heller` har det engelska lemmat `not either` | ordet är diskontinuerligt — "she does not read it **either**" — och går inte att slå upp som ett; konceptet hålls utanför kartan och kan inte läras ut | lemmat ska vara `either`, och negationen bäras av `neg_inte` |
| `kvant_båda` kräver bestämd form i svenskan — "båda **böckerna**" | ingen kolumn bär den egenskapen, så konceptet hålls utanför kartan | en kolumn som säger att bestämningen tvingar fram bestämd form, eller samma sak som ett `numeruskrav` för species |
| `alla` och `några` tar singular framför ett ORÄKNEBART huvudord — "all mat", "some water" | `numeruskrav` är en flat bitmask och kan inte säga "plural om räknebar"; fraserna går inte att bygga | villkora kravet på `räknebar`, eller lämna det — mängden sägs med en naken fras |
| engelskan kan inte bygga "all the books" | en bestämd kvantifierad fras kräver ett förbestämningsled som inte finns i specen; renderaren vägrar hellre än tappar bestämdheten | ett förbestämningsled i `Nominalfras`, om något kort behöver det |
| substantivets NUMERUS ägs av inget kort: det kommer ur meningens innehåll, inte ur ett `val`-beslut | ett numerusfel går inte att attribuera. «Time suits.» besvarad «times suits.» fäller `regel:val/bestämning/naken` — den nakna frasens regel, som satt i luckan före ordet — eftersom «times» är en FORM av `tid` och ordkortet därför klarar sig (7.3). Skulden landar, men på fel kort | antingen ett kort för numerusvalet, eller att attributionen får säga «ingen bär detta» i stället för att ta närmaste granne |
| nio verb ställer inget semantiskt krav på sitt subjekt: `pos_stå`, `pos_sitta`, `pos_ligga`, `gen_passa`, `gen_skydda`, `gen_växa`, `per_lukta`, `per_smaka`, `eko_v_kosta` (de elva övriga utan krav — modalverben, kopulorna, `börja` — tar med rätta vilket subjekt som helst) | meningarna är grammatiska men befängda: «Water sits.», «Love suits.» Dag ett använder tre av dem, så det är det första en användare ser | en `tagg` på subjektsplatsen i deras mönster (§11 i `docs/BITMASK.md`). Koncepten delas av alla sju språken, så ändringen gäller alla |
| **dagsplanen räknar om samma grammatikfakta varje dag.** Hela dag ett:s 42,7 s ligger i meningssökningen — insamlingen 28,0, `_ordförråd` 8,7, `dagens_kort` 6,0 — och lektionsvalet, huvuddelens reservering och matchningen kostar noll. Av de 42,7 bär `_minne`, minnet av vad grammatikens delar gav, ensamt 27: samma svep tre gånger med samma predikat tog 29,6 → 6,9 → 1,1 s, och ett NYTT men likvärdigt predikat kostade 30,5 s, alltså full pris. Minnet nycklas på predikatOBJEKTETS identitet (`tillåten is not self._minne_för`), och passet bygger ett predikat per anrop — `dagens_kort` ett, `_ordförråd` ett, insamlingen ett — så allt kastas tre gånger per dagsplan och alltid mellan dygnen. Antalet poster säger ingenting om kostnaden: `_vägar_tillåtna` har 55 415 poster och är värd noll, `_minne` har 868 och är värd 27 sekunder, eftersom varje post står för ett helt uppräknat delträd. Av posterna är 615 tomma och 253 fyllda, och båda halvorna behövs — var och en för sig tar bort tre fjärdedelar av tiden, tillsammans nästan allt (mätt 2026-10-11) | en dag kostar 43 sekunder i stället för de 1,1 ett varmt minne visar. Det gör steg P3 ogörligt — de simulerade kurserna, där omöjligheten ska visas innan något släpps (3.10), är 40–80 dagar styck | **härled** per grammatikposition, ur grammatiken och vid bygget, vilka kort som kan påverka den, och låt posten gälla så länge de korten svarar likadant. Då är beroendet sunt genom konstruktion. Att i stället **spela in** vid körtid vad varje post frågade om räcker inte, och det är prövat: ett dussin andra cacher — `_vägar_tillåtna`, `_filtrerat`, `_klass_möjlig`, `_bärarcache`, `_gallringar` … — frågar predikatet en gång och svarar sedan ur minnet, så den första delen som rör en sådan cache får frågorna i sitt beroende och varje senare del får svaret utan beroendet. Mätt 2026-10-11: dag två gav identiskt utfall och 40,1 → 9,9 s, men dag tre tappade nio meningar — de bestämda formerna, «Tiden står.» — när den bestämda artikeln låstes upp. `sökningsprov.py` «svaret beror inte på det tillåtna före» vaktar det, och den måste gå minst **tre** mängder djupt: felet syntes inte på två |
| **ett krav kan vara uppfyllt och kortet ändå obyggbart.** Kravet räknas ur vad bevismeningen PRÖVAR (4.2, 6.2), men för att bygga meningen måste också kort som den inte prövar vara tillåtna. Mätt 2026-10-27: `regel:val/satsart/imperativ` har **tomt** krav, eftersom dess bevis är «Se!» → «See!» vars prövade kort bara är `ord:per_se` och kortet självt. Men «See!» går inte att bygga utan `ord:pronomen_impersonal` — imperativens outtalade subjekt, «man»/«one» — vars beslut inte SYNS i meningen och därför inte blir ett prövat kort. `finns()` svarar NEJ med bevisets två kort tillåtna och JA när allt är tillåtet, och minimeringen ger exakt det ena kortet som tillägg | tomt krav betyder upplåst dag ett (4.5), så kön erbjuder kortet från första dagen medan dess subjekt ligger på nivå 26 och kortet självt på nivå 82. Varje dagsplan väljer det, ingen mening går att bygga, och det hamnar i karantän — vilket 5.1 förbjuder på dag ett («annars går kursen inte att börja») och §11 kräver noll av. Dag ett har alltså ett kort i karantän i dag | kravet måste räknas ur vad meningen BEHÖVER, inte bara ur vad den prövar: ett kort som måste vara tillåtet för att meningen ska gå att bygga hör till kravet även när dess beslut är osynligt. Tills dess kan kön inte lita på ett tomt krav. Två närliggande luckor hör till samma rättelse: listan `oprövbara` (13 kort) skrivs av nivåbygget men **läses aldrig** av passet — bara av en utskrift — och `kravprov.py` prövar att ett kort går att införa när DESS NIVÅ öppnas, medan kön låser upp på kravet, alltså vid en annan tidpunkt för just de kort där krav och ordning säger olika saker |

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
| tre nivåstegar: konstruktion, böjning, realisering | gav tre beskrivningar av nivåer som motsade varandra; en sorts nivå, definierad av prövbarheten, räcker |
| konstruktioner som egna nivåer | en konstruktion är meningens innehåll och har inget eget att lära; det som lärs är reglerna som uttrycker den |
| prövbarhet säkrad av nivåerna ensamma | nivåerna ser vad som är upplåst, men inte vad som är infört eller vilka varianter som finns (`yo`, aspekten) |
| efterfrågan räknad ur loggen över meningsbyggen | har inga data första dagen eller när en nivå just öppnats, och generatorn kan inte efterfråga det den inte får använda |
| efterfrågan beräknad genom att prova bygga meningar vid passtart | tungt, och i ett stort utrymme sampling |
| utfyllnad för att göra meningar längre | ett kort som inte är mål kostar tid men klarar inget; extra möten flyttar knappt stabiliteten (7.1) |
| en handskriven lista över axlar i entydighetsfiltret | en glömd axel underkänner korrekta svar utan att något märker det; axlarna är specens fält (6.5) |
| regelkort som tränas direkt i meningsfasen, utan introövning | bryter mot R1, och kortet saknar FSRS-tillstånd, så R och budgeten är odefinierade |
| lånekort som graderas i introövningen | urvalsregeln har inte valt dem, och övningen prövar dem inte (5.4) |
| tvåval och kasusfrågor som introövningar | svaret är en etikett och ingen form; klarar inte produktionstestet (3.1) |
| ett oprövbart kort i dagsplanen som tyst hoppas över eller räknas som klarat | döljer ett fel i programmet; karantän med felrapport i stället (3.10) |
| en förteckning över vilka kort som konkurrerar | filtret hittar det själv när bevisen prövas om (3.10) |
| nivålistan som en bedömning av «minsta steg» | nivåerna är grafens starka komponenter (4.1) |
| «tills fönstret är felfritt» för övervakade kort | en andra definition av förfallet; ett övervakat kort är förfallet när andelen rätt är under 0,9 |
| beroenden angivna i anropet under renderingen | kommer för sent: generatorn och grafen behöver dem innan meningen byggs (8.3) |
| «flest andra kort prövbara» som införandeordning | räknade ett ords egna kort som vinst: sällsynta oregelbundna ord gick före vanliga regelbundna, och regler som inget kräver kom aldrig; ersatt av täckning per kort (5.6) |
| svagt definierat som R < 0,9 | FSRS ger R ≈ 1 direkt efter varje möte, så dagens nya kort blev aldrig mål och ett kort som just fallit räknades som säkert (6.2) |
| introövningens svar som första FSRS-betyg | svaret ges direkt efter att kortet visats; introfasen är till för att lära ut, inte för att mäta (5.4) |
| förfallna kort i introfasen | att öva kortet precis före meningen gör det lätt att klara något som var svårt (5.1) |
| ett kort räknat som infört när introövningen är klarad | ett avbrutet pass lämnade kort, och halva paket, i systemet utan att de prövats (5.1) |
| största antal nya kort som ryms varje dag framåt | fyller de närmaste dagarna och ger ett ryckigt införande; ersatt av jämnt tempo (5.5) |
| «budgeten rymmer alltid en mening med ett mål» | falskt när meningens övriga kort är svaga, tidigt i kursen och efter uppehåll; ersatt av reservstegen (6.3) |
| krav med flera alternativ som kanter till varje alternativ | alla alternativ kräver varandra, och nivåerna smälter ihop (4.2) |
| ordkortet fallet när svaret inte är en form av lexemet | felaktiga former som `köpade` skulle belasta ordet i stället för undantaget (3.3) |
| en kommentar i uppgiften om vilken synonym som inte söks | visar ett ord på målspråket varje gång, även när användaren aldrig hade tänkt på synonymen (7.4) |
| sampla kandidater och poängsätt dem (det gamla systemets generator) | upptäcker meningens innehåll i efterhand, hittar inte den bästa, och poängens vikter är valda (6.7) |
| krav och byggvillkor skrivna för hand i ett register | kan glida isär från renderaren; kartan läser av dem (6.7) |
| en karta över hela satsen i ett stycke | ≈ 70 miljoner vägar i svenskan; delarna har högst 87 570 (6.7) |
| samma mening igen samma dag, när den är den bästa | användaren har just sett facit; svaret mäter minnet av facit och inte kortet (6.1 punkt 8) |
| kärnan byggd på ett enda språk först | en kurs har två språk; entydighetsfiltret behöver källspråkets karta (9) |
| nivåerna före sammansättningen | kraven är kortens minsta meningar, och de hittas genom att sätta samman delarna (9) |
| ett besluts alla andra utfall som fel | blandar ihop varianter och fel: «igår läste hon» är rätt (8.3) |
| glosa för funktionsord | sällan entydig: *a* är både `en` och `ett` (5.4) |

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
