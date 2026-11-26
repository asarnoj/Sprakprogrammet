# Kärnan

Den fullständiga specifikationen av kärnan — korten, nivåerna, dagspasset,
meningsbygget och bedömningen — så som den ska byggas. Filen beskriver målet,
inte ändringar i den kod som finns.

> **Läge 2026-09-12.** Specen är avgjord utom tre frågor, samlade i punkt 10.
> **En av dem blockerar bygget:** kortmodellen (10.1), som väntar på Julius
> regelbundenhetsregel för svenska verb.

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
- **Produktionstestet** — är facit något en människa faktiskt skriver?

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

*Om formkunskapen ska delas i `ändelse` och `oregelbunden`, och om det behövs en
tredje formkomponent, är öppen fråga 10.1. Resten av punkt 3 gäller oavsett
svaret.*

### 3.3 `ord`

**Kortet klaras om användaren skriver någon form av rätt lexem.** Läromomentet är
att ordet hämtades ur minnet, och kortet är prerekvisit för alla formkort:

    strängen är en form av lexemet?
       nej -> ord föll; formkorten är OGRADERADE, de prövades aldrig
       ja  -> ord klarat; formkorten graderas mot cellen

Införs som glosa: betydelse → form.

### 3.4 `ändelse` och `oregelbunden`

**Ett ändelsekort är en ändelsesträng för en (ordklass, böjningsklass)** — inget
ord ingår i nyckeln. Celler som delar sträng inom samma klass är samma kort,
eftersom de inte lär ut två saker:

    fr, -er-verb   -e     imp_2sg · pres_1sg · pres_3sg · subj_1sg · subj_3sg
                   -ais   imperf_1sg · imperf_2sg
                   ...    45 celler blir 33 kort

Mätt över `ordbok/ändelser.tsv`: 831 rader blir **394 ändelsekort för sju
språk**, varav 39 i tyskan. Talen gäller dagens tabeller, som är fel dragna
(10.1). Slutsatsen att mönsterfamiljen är liten håller; de exakta talen gör det
inte.

**Ett `oregelbunden`-kort betyder «just det här ordet bryter mönstret här».** Det
gäller både suppletiva former (`vais`) och avvikande baser (`aur-`). Enheten
följer `stamgrupp` i `stammar.tsv`:

| `stamgrupp` | Vad det är | Kort |
|---|---|---|
| ≥ 0 | en bas som delas av flera celler — `aur-` | ett per grupp |
| −1 | en form utan delad bas — `vais` | ett per form |

**Regelbundenhet spåras inte, bara undantagen.** Ett ord utan undantagskort är
regelbundet och kostar ingenting. Användaren lär sig mönstret och sedan
undantagen, precis som en människa gör.

**Böjningsklassen är inget kort.** Den går att läsa ur lemmat — i franskan
stämmer «-er → K0, annars K1» för 165 av 174 verb — och de nio avvikande bärs av
`oregelbunden`. Klassen avgör vilka kort som *finns*. Användaren får aldrig
frågan vilken klass ett ord tillhör.

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
| 4 | vilken cell — kongruens, bestämdhet | `regel`, när renderaren redovisat (8.3) |
| 5 | vilken sträng cellen har | se nedan |
| 6 | var ordet står | `regel` |

Givet rätt ord och rätt cell kan strängen bli fel på fem sätt:

| | Felet | Kort |
|---|---|---|
| a | kan inte mönstret | `ändelse` |
| b | kan mönstret, men ordet är ett undantag — `gådde` | `oregelbunden` |
| c | minns undantaget fel | `oregelbunden` |
| d | använde fel klass — `finit` i stället för `finis` | behövs inte — klassen läses ur lemmat (3.4) |
| e | missade en ljudanpassning — `arbeitst` | **saknas** — öppen fråga 10.1 |

**Modellen har två kända hål.** Det ena är (e). Det andra är valet av aspekt och
modus när ingenting i meningen styr det. Det är ingen formfråga utan en fråga om
vad meningen betyder (10.2).

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

Den fasta kostnaden per mening dominerar. **När påfyllningen ska sluta är öppen
fråga 10.3.**

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
  faller är ofta två läromoment i ett — ett `oregelbunden`-kort som gäller sex
  celler kan behöva bli sex kort.
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

    0   regelbundenhetsregel per språk       blockerar 3 — svenskan först (10.1)
    1   renderarna redovisar sina beslut     allt annat bygger på detta
    2   nivåstegarna och grafen              följer ur 1; kontrollera att grafen är acyklisk
    3   kortmodellen                         kräver 0
    3b  ändelsetabellerna görs om            kräver 0
    4   dagspasset och införandet            kräver 2 och 3
    5   meningsbygget                        kräver 4
    5b  neutraliseringstabellerna            kräver 1; en per språkpar
    6   rättningen                           kräver 1
    7   lektioner och frekvenslista          parallellt
    7b  provsviten                           parallellt — finns inte i dag

**Steg 1 är det billigaste sättet att upptäcka om modellen håller.** När
renderarna redovisar går det att mäta hur många regler en mening faktiskt
använder, och alltså om attributionen fungerar med 133 regelkort i stället för
dagens tre. Håller den inte syns det innan något har raderats.

**Rent arbete, utan kvarstående beslut:** renderarnas redovisade beslut, omkring
133 lektionstexter, den semantiska frekvenslistan (japanskan för hand), en
neutraliseringstabell per språkpar, och datafelen i punkt 12.

---

## 10 · Öppna frågor

### 10.1 Kortmodellen — blockerar bygget

**Frågan:** ska kunskapen om former delas upp i mönster och undantag, eller ska
varje kombination av lexem och cell vara ett eget kort?

| Modell | Kort | Styrka | Svaghet |
|---|---|---|---|
| **Uppdelad** | `ord` + `ändelse` + `oregelbunden` (+ ev. ljudregler) | mönstret mäts och överförs till nya ord; få kort | kräver att gränsen mellan stam och ändelse är rätt dragen |
| **Ord + form** | `ord` + ett formkort per lexem och cell | enkel; kräver ingen gräns | mäter aldrig om användaren har generaliserat |

**Kostnaden för ord + form**, mätt i `Former` jämfört med `stammar.tsv` och
`ändelser.tsv`:

    språk   ord+form   uppdelad   kvot
    de       13 617      2 733    5,0x
    es        9 936      1 953    5,1x
    it        9 204      2 223    4,1x
    fr        7 900      1 702    4,6x
    sv        4 757      1 745    2,7x
    ja        2 495      1 137    2,2x
    en        2 138        817    2,6x

Viktigare än antalet: kan användaren redan `parler` i elva celler blir
`regarder` en enda introduktionsövning i den uppdelade modellen, men elva i ord +
form. Och i ord + form går det aldrig att se om rätt `parlais`, `regardais` och
`travaillais` betyder att hen kan imparfait, eller bara kan tre ord.

**Varför frågan inte kan avgöras i dag: gränsen är fel dragen.** Datan har två
delar, `stam` och `ändelse`. Allt som ändelsetabellen inte kan uttrycka hamnar i
stammen, och då ser regelbundna verb oregelbundna ut. Antal stamgrupper per verb:

    språk    1    2    3    4    5    6    7    8    9   median
    de       0    0   11   52   62   19   13    2    0     5
    ja       0    2    0    3   72   89    3    0    0     6
    sv       1    7   65   18   13   36   21   12    1     4
    it       0   55   34   14   42    6    9    4    3     3
    es       0   71   41   14   19   11    7    3    1     3
    fr       0   93   21   22    9   18    7    4    0     2
    en      57   80   30    2    0    0    0    0    0     2

Tyskans helt regelbundna `arbeiten` har fem stamgrupper
(`arbeit · arbeite · arbeitet · arbeitete · gearbeitet`); starka `finden` har sex.
Svenskans dåtidsändelse är tom i `ändelser.tsv`, så `arbetade` lagras som ett
undantag. Japanskan har bara en verbklass, så godan-verbens `飲んだ` och `飲んで`
lagras som hela former (43 % av verben har sådana rader).

**Hypotesen:** det saknas en tredje del — **ljudanpassningen**, en regel för hur
ändelsen fogas till stammen:

    sv   åka -> åkte            -te   + slutvokalen faller bort
    de   arbeiten -> arbeitete  -te   + e skjuts in efter t/d
    ja   飲む -> 飲んで           -て   + godan-växlingen む -> んで
    fr   finir -> finissons     -ons  + -iss- i andra konjugationen

En sådan regel finns redan som korttyp: `regel`. Om hypotesen håller krymper
`oregelbunden` kraftigt, och den uppdelade modellen fungerar. Hypotesen är visad
på fyra exempel, inte prövad på datan.

**Provet som avgör:**

    1  Julius skriver regelbundenhetsregeln för svenska verb
       (förslag: «lemmat + de/te/dde, slutvokalen får falla bort» — gav 102 svaga, 66 starka)
    2  stamanalysen körs om med regeln
    3  medianen stamgrupper per svenskt verb mäts

       i dag      4
       1–2        uppdelad modell, ljudanpassningar som regelkort
       fortf. 4   ord + form

Oavsett utfall gäller definitionen av `ord`-kortet (3.3), prerekvisitregeln (7.3)
och hur `oregelbunden`-kort avgränsas (3.4).

### 10.2 Aspekt och modus — priset måste godkännas

Renderaren får aspekten som indata: generatorn bestämmer om det blir imparfait
eller passé composé. Systemet lär alltså ut «skriv imperfekt när imperfekt
efterfrågas», men aldrig «den här situationen kräver imperfekt» — ett av de
svåraste momenten i franska, spanska och italienska. Samma sak gäller modus när
inget ord i meningen styr det.

Svenskan gör inte den skillnaden, så med «jag arbetade» kan valet inte prövas
utan att bryta mot R2. Tre vägar:

| | Väg | Pris |
|---|---|---|
| **a** | aspektvalet ligger utanför projektet | ett verkligt läromoment tränas inte; det ska då stå uttryckligen |
| **b** | en egen uppgiftstyp, t.ex. ett tvåval utifrån svensk kontext | bryter formen «en mening, ett facit» |
| **c** | källmeningen visar valet: «jag arbetade **varje dag**» | svenskan blir mer markerad än naturlig svenska, och mer ju fler nivåer som låses upp |

(c) följer direkt av entydighetsfiltret (6.5) och kräver ingen ny mekanism.
**Det som återstår att besluta är om priset för (c) är acceptabelt.**

### 10.3 När påfyllningen ska sluta

Budgeten tillåter långa meningar, och långa meningar är billiga per kort, men
något måste avgöra när en mening är lång nog. Det är den enda öppna parametern i
meningsbygget, och det enda stället där en smaksak — «ibland långa, ibland korta
meningar» — kan få avgöra. Blir det ett val ska det stå som ett val.

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
| gränsen mellan stam och ändelse är fel dragen i sex av sju språk | regelbundna ord blir undantag | 10.1, steg 0 och 3b |
| japanskan har bara en verbklass (ichidan) | godan-verbens former lagras som hela former | steg 3b |
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
| `stam` och `form` som egna korttyper | en stam är inget man producerar, och stam och form är samma läromoment |
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
