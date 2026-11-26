# Kärnan

*Specifikation, avgjord 2026-09-09 efter trettio frågor över fem omgångar
mellan Julius och Claude. Omgång 7 (2026-09-12) byggde om meningsbygget,
budgeten och grindarna; se punkt 12. Läsbar version med tabeller och mätningar finns som
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

Syskonregeln, ur fråga 30 — *omformulerad i omgång 7*:

> **En uppgift är giltig endast om relationen källmening → målmening är
> ENTYDIG: exakt en målmening är korrekt.** Är den inte det vet användaren inte
> vilket svar som efterfrågas, och rättningen mäter en gissning.

*Utkast 1–27 skrev «injektiv». Det är fel egenskap: injektivitet betyder att
olika källmeningar ger olika målmeningar, vilket är harmlöst här. Surjektivitet
är inte heller det. Det som krävs är att avbildningen är en **funktion** —
enkelvärd. Julius: «det finns endast ett ord på svenskan men flera ord på tyskan
som knyter till samma koncept.» Två målmeningar, en källmening; relationen är
inte entydig.*

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
| `egenskap: prenominal` | står adjektivet före eller efter | oförändrat |
| `egenskap: ja_adjektiv_typ` | japanskans i-, na-, no- eller verbfrasadjektiv | oförändrat |
| `rektion` | vilket kasus verbet styr | oförändrat |
| `regel` | renderarens beslut — blir nivå **och** kort | `ordföljd`, utvidgad |

**Borta:** `stam` och `form` som egna typer, och `egenskap: böjningsklass`.

`stam` föll på produktionstestet — «vad är stammen för *arbeta*?» är ingen
fråga en människa besvarar — och på att den är härledbar ur lemmat för
**franskans 122 `-er`-verb av 174**, den enda klass vars stam är lemmat minus
infinitivändelsen. `form` och `stam` visade sig dessutom vara samma
läromoment: `aur-` och `vais` är båda «detta ord bryter mönstret här», och
skillnaden är bara om en regelbunden ändelse råkar fästa efteråt.

**Regelbundenhet spåras inte — bara undantagen.** Följer ordet mönstret
behövs inget kort; basen faller ur ordkortet. Så lär sig också en människa:
mönstret först, sedan undantagen.

Hur många undantag det blir är **inte mätt** — se punkt 11.1. Utkast 1–21 stod
«1 527 följer, 419 bryter»; det talet går inte att återskapa och är struket.

### 541 kort som ingen kan möta

`böjningsklass` har facit `K0`, `K1` eller `K2` — en klasskod. Ingen människa
skriver «K0», så kortet faller på produktionstestet. Mätt: **210 i franskan,
191 i tyskan, 140 i engelskan, och ingen av de 541 har någonsin mötts eller
införts.**

De behövs inte heller. Kunskapen «det här verbet böjs så här» bärs redan av
de två korttyper som finns kvar: `regarder` tar mönsterkortet för imperfekt och
behöver inget mer, medan `finir` har `finiss-` och får ett `oregelbunden`-kort
där. **Klassen är ändelsekortet plus undantagen** — den behöver ingen egen kod.

Franskan tappar därmed 210 kort. *(Den gamla modellens lek var 810 kort och
blir 600 — båda mätta i `kort.db`. Den nya modellens totalsumma är inte
bestämd, eftersom den hänger på punkt 11.1.)*

### Varför det blir just dessa typer, och inga andra

Typerna är inte valda — de faller ur **vad renderaren måste avgöra för att
skriva ett ord.** Den listan är sluten, och därmed är kortmängden komplett:

| Renderarens fråga | Kortet | Nyckeln |
|---|---|---|
| vilket ord betyder detta? | `ord` | ordet |
| vilken form ska ordet ha? — **läst** ur en tabell | `oregelbunden` | ordet |
| vilken form ska ordet ha? — **byggd** ur ett mönster | `ändelse` | mönstret |
| vad kräver det regerande ordet? | `rektion` | ordet |
| var i satsen står det? | `regel` | mönstret |
| vad är ordets egenskap, när den syns på ett **annat** ord? | `egenskap` | ordet |

**Medlemskapet i mönstret spåras inte — bara undantagen.** Användaren lär sig
inte «dessa 102 svenska verb är svaga». Hen lär sig regeln, och de 66 starka får
vart sitt kort. *Ett ord utan undantagskort är regelbundet, och det kostar
ingenting.* Frågan «är `springa` svagt?» lärs som `sprang` — det är samma
faktum, ett kort.

**Formfrågan har exakt två svar och inget tredje:** antingen läste renderaren
en sträng, eller byggde den en. Det är därför `oregelbunden` och `ändelse` är
två typer och inte en — och testet på att delningen är rätt är att de kan
**falla var för sig**:

    arbetde    ordet rätt, ändelsen fel    ->  ändelsekortet föll
    gådde      mönstret rätt, ordet inte   ->  det oregelbundna kortet föll

**Egenskapskortet finns av ett skäl och bara ett: attributionen.** `ett hus`
mot `en bil` — genuset syns varken i `hus` eller i `bil` utan i artikeln, och i
`ett stort hus` mot `en stor bil` också i adjektivet. Beslutet hör till
substantivet, följden syns på grannen. Skriver användaren `en hus` är det
genuskortet som föll, inte ordkortet och inte artikelns ändelse.

### Täckningsrevisionen

*Omgång 7. Julius kriterium: «vårt system ska täcka alla kunskapsmoment så att
det inte blir en situation där en mening blir fel men det inte finns någonting
att gå på varför.» Det kriteriet räcker för att härleda modellen — ingen
undersökning behövs, bara uppräkningen ovan tagen på allvar.*

**Steg 1 — vad måste vetas för att producera ett ord?** Listan är sluten, för
den är vad renderaren gör:

| # | Det som måste vetas | Kort |
|---|---|---|
| 1 | vilket ord som betyder detta | `ord` |
| 2 | ordets egenskap som syns på grannen | `egenskap` |
| 3 | vad det regerande ordet kräver | `rektion` |
| 4 | vilken **cell** ordet ska stå i — kongruens, bestämdhet | de tysta besluten → `regel` efter steg 1 i byggordningen |
| 5 | vilken **sträng** cellen har | se steg 2 |
| 6 | var i satsen ordet står | `regel` |

Fem av sex är täckta eller har en namngiven väg dit. Hela frågan ligger i rad 5.

**Steg 2 — vad kan gå fel i rad 5?** Givet rätt ord och rätt cell, uttömmande:

| | Felet | Specens modell | Ord+form |
|---|---|---|---|
| **a** | kan inte mönstret alls | `ändelse` | formkort |
| **b** | kan mönstret, ordet är undantag — `gådde` | `oregelbunden` | formkort |
| **c** | minns undantaget fel — `gigck` | `oregelbunden` | formkort |
| **d** | tillämpade **fel klass** — `finit` för `finis` | **inget** | formkort |
| **e** | missade en **ljudanpassning** — `arbeitst` | **inget** | formkort |

Där står båda modellernas problem, exakt:

> **Specens modell UNDER-täcker:** två av fem felsätt har inget kort, alltså kan
> en mening bli fel utan att något kort bär skulden — precis det Julius kriterium
> förbjuder.
>
> **Ord+form ÖVER-täcker:** alla fem blir samma kort. Täckningen är komplett men
> odifferentierad, och bryter mot det andra kravet — att kortet ska vara ett
> naturligt läromoment. (a) och (b) är bevisligen olika moment; det är
> distinktionstestet ovan, `arbetde` mot `gådde`.

**Steg 3 — (d) upplöser sig, mätt.** Är «vilken klass tillhör verbet» ett eget
läromoment? Bara om det inte går att läsa ur ordet. Franskan:

    lemma slutar på -er   ->  K0: 116   K1:  1
    lemma slutar på -ir   ->  K0:   2   K1: 24
    lemma slutar på -re   ->  K0:   2   K1: 25
    annat                 ->  K0:   2   K1:  2

Regeln «-er → K0, annars K1» träffar **165 av 174 = 95 %**. Klassen läses ur
stavningen, precis som en människa gör, och de nio resterande är undantag som
redan har en korttyp. **(d) behöver inget eget kort** — vilket självständigt
bekräftar att `böjningsklass` var rätt att stryka.

**Steg 4 — tre läromoment återstår, och det är modellen:**

    mönstret       "vad är ändelsen för den här cellen?"      ändelse
    justeringen    "hur fäster den på just den här stammen?"  regel        <- saknas
    undantaget     "bryter det här ordet mönstret?"           oregelbunden

Tre kort, tre frågor, ingen överlappning, och tillsammans täcker de alla fem
felsätten. Det är den enda uppdelningen som uppfyller **båda** kraven samtidigt.

`ord` står kvar oförändrat som prerekvisit ovanför alla tre. Ord+form-modellen är
inte fel — den är den här modellen med rad 2 och 3 hopslagna med rad 1.
**Skillnaden mellan dem är en enda fråga: ska mönstret ha ett eget kort?** Där
ligger de 2,2–5,1× i kortantal och transferargumentet; se punkt 11.1.

**Vad revisionen hittade.** Kört över hela listan har modellen **exakt två hål**,
och båda är redan namngivna:

| Hål | Var | Fix |
|---|---|---|
| ljudanpassningen (e) | rad 5 | den morfofonologiska regeln blir ett `regel`-kort — punkt 11.1 |
| aspekt- och modusvalet | inte ens rad 4 — det är vad meningen BETYDER | punkt 11.2 |

Allt annat täcks, förutsatt att steg 1 i byggordningen görs.

---

### Två familjer, inte sex typer

Nyckelkolumnen ovan har bara två värden, och det är hela strukturen:

| | nyckel | växer med | exempel |
|---|---|---|---|
| **ordfamiljen** | ett ord | ordförrådet | `gå → gick` är ett faktum om ett ord |
| **mönsterfamiljen** | ett mönster | ingenting | `-rna` är bestämd plural: `bilarna` |

*(Utkast 24 skrev «`-de` är dåtid för svaga verb» som exempel. Det kortet finns
inte — svenskans `pret`-ändelse är **tom** i `ändelser.tsv`, och hela `-ade`
ligger i stammen. Se lucka 1; det är den felaktiga gränsen i sin renaste form.)*

    språk    ordfamiljen    mönsterfamiljen
    de             1 172                 42
    fr             1 281                 34
    ja               843                 24
    en               734                 19

**Mönsterfamiljen är liten och sluten.** Den växer inte när ordförrådet växer —
det är definitionen av ett mönster. Ordfamiljen växer linjärt, och det ska den.

**Vad ett ändelsekort ÄR, mätt i omgång 7.** Julius frågade: *«är det hela
böjningen för ett typ av verb, eller en hel serie för ett specifikt verb, eller
en specifik böjningsändelse för ett verb?»* Inget av dem. Nyckeln i `befolka`
har tomt `koncept`:

> **Ett ändelsekort är en ändelsesträng för en (ordklass, böjningsklass).**
> Inget ord, ingen hel tabell, ingen serie.

Franskans `-er`-verb, grupperade på strängen — 45 celler blir 33 kort:

    -e        5 celler   imp_2sg · pres_1sg · pres_3sg · subj_1sg · subj_3sg
    -ais      2 celler   imperf_1sg · imperf_2sg
    -ons      2 celler   imp_1pl · pres_1pl
    -erai     1 cell     fut_1sg
    ...

Att fem celler delar `-e` är ingen hopklumpning — det är att de fem inte lär ut
fem saker. Samma kriterium som `dimensioner.projicera` redan använder.

Hela mönsterfamiljen, alla ordklasser, alla sju språk:

    språk   rader i ändelser.tsv   distinkta strängar   krympning
    de              241                    39             6,2x
    es              191                   109             1,8x
    it              180                    97             1,9x
    fr              111                    75             1,5x
    sv               68                    39             1,7x
    en               20                    16             1,2x
    ja               20                    19             1,1x
                    831                   394

**394 kort för sju språk**, och tyskans hela böjningslära — den tyngsta av de
sju — är 39. Det är inte mönsterfamiljen som hotar renheten. Undantagsfamiljen
gör det, och dess storlek är fortfarande omätt: se punkt 11.1.

Därför behöver ingen fråga «vilken typ är det här kortet». Frågan är **«vad
slog renderaren upp — ett ord eller ett mönster?»**, och typen är svarets form.

### Vilka egenskaper som blir kort

`sprak.db` drar redan gränsen: **`Lexem` har en rad per språk, `Koncept` har en
rad för alla sju.** Det som måste läras per språk ligger därför på `Lexem`, och
det som följer av betydelsen ligger på `Koncept`.

| `Lexem` — blir kort | satt på | | `Koncept` — blir inte kort | |
|---|---|---|---|---|
| `genus` | de, es, fr, it, sv | | `valens` (transitivitet) | 174 koncept |
| `hjälpverb` | de, fr, it | | `gradbarhet` | 111 |
| `prenominal` | es, fr, it | | `räknebar` | 259 |
| `ja_adjektiv_typ` | ja | | `semantik` | 323 |

**Fördelningen bevisar gränsen.** `genus` är satt för de fem språk som har
genus och saknas i engelskan och japanskan. `hjälpverb` finns bara i de tre
språk där valet existerar. `prenominal` varierar **per ord inom språket** — 16
av franskans 111 adjektiv står före substantivet, 95 efter — men är konstant 1
i tyskan, engelskan, svenskan och japanskan, som alltid har adjektivet före.
Kriteriet begränsar sig alltså själv till rätt språk.

`variant` ligger på `Lexem` men blir inget kort: den skiljer homonymer åt, den
är inget användaren producerar.

*(`prenominal` är en lexikal egenskap och inte en `regel`, just därför att den
varierar per ord. Renderaren har regeln — «adjektivet står där lexemet säger» —
och ordet bär värdet.)*

### Genus

Julius: *«För tyska och franska måste man lära sig genuset på varendaste
substantiv, vilket tar väldigt mycket tid. För varje substantiv man lär sig
ingår även genuset.»* — 162 genuskort i franskan mot den gamla modellens
600, alltså 27 %, och det är rätt proportion. Genus rörs inte av omgång 3, så
talet står.

*(Rättelse: utkast 2–4 skrev «427 genuskort, 53 %». 427 är alla
`egenskap`-kort tillsammans.)*

### Faktoriseringen

Att faktorisera är rätt: ett kort per cell och lexem skulle ge 4 924 kort i
franskan, mönster plus undantag ger en bråkdel. Men det var **härledningen** som
brast för lexem som böjs i två leder — `sœur aînée` blev `sœurs aînée`.

Därför: **basen härleds ur de renderade formerna, inte ur lemmasträngen** —
renderarna kan redan kongruens. Det är samma beroende som byggordningen redan
vilar på, och skälet att punkt 11.1 inte kan avgöras före renderarna talat.

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
| | **28** | **105** | **133** |

De 28 ordföljdsreglerna redovisas redan. De 105 övriga sker tyst inuti
renderaren — se punkt 8.

*(Rättat i omgång 7. Utkast 1–27 skrev 22 och 111. Kolumnerna summerar till 28
och 105; 22 var konstruktionsnivåernas antal, återanvänt av misstag. Koden i
`befolka.ORDFÖLJD` har 27 — tyskan har sex regler, inte sju — så talet ska
kontrolleras mot renderarna när de redovisar.)*

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
| 1 | ~~**Materialet räcker.**~~ **Struken i omgång 7** — den var grind 2 för rotnivån, och roten är inte ett val. Ersatt av en bygginvariant, se nedan. |
| 2 | **Det föregående sitter.** Nivåns föregångare i grafen har mötts och gått rätt minst en gång, och inte i dag. |

> **INVARIANT (omgång 7).** Varje nivå öppnar minst ett kort — en regel, en
> cell eller ett ord. Bryts den är det en bugg i nivålistan, inte ett
> användartillstånd.

Grind 1 frågade om materialet räckte. Men för varje nivå med en föregångare
kräver grind 2 att föregångarens kort mötts och gått rätt, och ett möte kräver
en byggbar mening — alltså finns meningar. Det enda fall grind 1 fångade utöver
det är att nivån öppnar **noll kort**, och det är ett datahål, inte ett
tillstånd att hantera vid körning. Påståenden hör hemma i bygget.

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
mening — den får inte in i introfasen, och meningsfasen inför ingenting.

**Nivån byts bara vid passets början.** Julius: *«när man startar passet så har
man två knappar, en för att starta passet på vanligt sätt och en för att starta
passet på nästa nivå.»* Nivåvalet sker alltså innan planen räknas ut, och
planen står stilla hela passet. Att tillgängliga nivåer skulle ändras mitt i
dagen kan inte inträffa.

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

> **Omgång 7 lade till ett lager ovanpå.** Frekvens inom ordklass ordnar
> ordförrådet, men ordnar ingenting mellan korttyper — och det hålet var öppet
> sedan omgång 6 strök efterfrågemätningen. Svaret är koncentrationen i loggen:
> är en plats trång går införandet dit, annars till frekvensen. Se omgång 7 i
> punkt 12.

---

## 5 · Meningsbygget

En mening är giltig endast om varje kort den kräver är **infört**, och varje
regel den använder är upplåst i alla tre stegarna.

### Dagspasset har två faser

*Avgjort i omgång 7. Utkast 1–27 lät axiomet säga «infört ELLER i dagens plan»,
och §4b säga «axiomet kräver att kortet är infört». De sa olika saker.*

Julius: *«ett dagspass består av två delar. Huvudsakligen meningsövningarna,
men innan det är det en introduktionsfas där användaren introduceras allting
nytt för dagen. Man måste först lära sig kunskapen innan man kan börja
repetera den.»*

| Fas | Vad som händer | Nya kort |
|---|---|---|
| **1 · introfasen** | dagens nya kort införs, ett per övning | alla dagens nya |
| **2 · meningsfasen** | meningarna ställs | **inga** |

> **Inget kort införs i meningsfasen.** Vilka nya kort dagen har är känt innan
> passet börjar.

Axiomets «eller står i dagens plan» är alltså inte en lucka utan en
tidsordning: när meningarna börjar HAR planen hunnit bli införd. Det gamla
problemet — att algoritmen ville slänga in ytterligare nya kort mitt i
meningsfasen för att få ihop en mening — upphör att vara en avvägning och blir
ett förbud.

**Och det avgör budgeten.** När meningsfasen börjar har varje kort i spel setts.
Ett kort som infördes för tio minuter sedan har R ≈ 0,99. **Det finns inget
kort med R = 0,00 i en mening**, och den budgettabell som byggde på det är
struken nedan.

### Planen är dagens mål, inte meningens tillstånd

|  | Vad det är | Innehåller |
|---|---|---|
| **Dagens plan** | MÅLET — det som måste klaras | förfallna (FSRS) + dagens nya (tidsratten bestämmer antalet, ordningen vilka) |
| **Det tillåtna** | TILLSTÅNDET — vad en mening får röra | allt infört, plus planen |

Ett infört men inte förfallet kort ligger utanför målet men innanför
tillståndet. Det bokförs som allt annat, och går det fel hamnar det i
återförsökskön och måste klaras innan dagen är slut.

**Dagen tar slut när högarna är tomma.** Julius: *«den är inte klar förrän alla
kort är inlärda — alltså att new-högen, again-högen och due-högen är tomma.»*
Varje fel lägger till arbete, och ett kort som inte tillhörde dagens pass men
som råkade prövas och falla växer högen.

*Utkast 1–27 skrev att svårighetstaket var termineringsgarantin. Det följer
inte: ett tak PER MENING säger ingenting om antalet meningar. Termineringen
vilar på FSRS relearning och på att varje kort går att nå — och det senare är
gratis under budgeten nedan, eftersom en mening med ett enda förfallet mål
alltid ryms.*

### Urvalsregeln

*Omgång 7 ersatte tre lager, en variationsregel och en utfyllnadsregel med
den här meningen.*

> ### De svaga korten sprids över oberoende positioner.

Två villkor, och de är samma tal — R — sett från två håll:

| | Villkoret | Vad det skyddar |
|---|---|---|
| **hur många** | P(≥2 fel i meningen) ≤ τ | att felet går att lokalisera |
| **var** | målkortet är det enda svaga kortet på sin position | att felet går att **attribuera** |

Och urvalet i en rad: **bygg meningen av de kort som har lägst R, så många som
budgeten tillåter.**

Vad som faller ur den utan att någon skriver en regel för det:

| Aspekt | Faller ur därför att… |
|---|---|
| minst ett mål ur dagsplanen | ett förfallet kort HAR per definition lägst R |
| hur många mål | budgeten svarar: fem |
| variation i ordval | ett kort du just använde har R ≈ 1,00 och väljs **sist**; ett du inte sett på tre veckor väljs först |
| variation i meningens form | formen bärs av regelkort, och regelkort har R som alla andra |
| ingen upprepning | behövs ingen spärr — upprepning är automatiskt det dyraste valet |
| längdvariation | mängden förfallna krymper under dagen, så passet börjar tätt och kort och slutar långt och lätt |

**Mål och utfyllnad är inte två mekanismer.** Målen är de kort som råkar ha
allra lägst R. Distinktionen försvinner, och med den försvinner de tre lagren.

**Det som saknas är fortfarande förmågan att bygga MOT en regel.** Generatorn
bygger idag en mening och får sedan veta vilka regler den råkade använda. Att
en regel är upplåst gör inte att den dyker upp: franskans `inversion_wh`
förekommer bara om meningen är en wh-fråga, så när det kortet är förfallet
måste generatorn VÄLJA att bygga en wh-fråga. Villkoret finns redan som
kunskap inne i renderaren.

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

Taket sitter därför inte på antalet kort utan på hur många som är **svaga**:
P(≥2 fel) ≤ τ. Meningarna växer av sig själva när användaren blir bättre, och
mätningen ovan säger varför det är rätt att låta dem göra det — en lång mening
är billigare per kort, och under attributionsbudgeten är den inte svårare.

### Två rattar

> **Tidsratten bestämmer vad dagen innehåller. Svårighetsratten bestämmer hur
> tätt det packas.**

Högre svårighet packar fler kort per mening, ger färre meningar, tar mindre
tid. Lägre svårighet ger fler och enklare meningar, tar mer tid. De förfallna
korten går inte att ändra på — FSRS bestämmer dem.

**Svårighetsratten ÄR τ** (omgång 7). Högre τ tillåter fler svaga kort per
mening; priset betalas i att rättaren oftare måste fråga vilket kort som föll.
Det är en avvägning användaren kan känna, till skillnad från en summa hen aldrig
ser.

### Hur många regler en mening bär

Obegränsat per dagspass; flera i samma mening när budgeten tillåter. Budgeten
mäter dock **attribuerbarhet, inte möjlighet**: två regler kan kräva oförenliga
former, och då blir meningen inte svår utan obyggbar. Sökningen går vidare.

Och positionsvillkoret gäller dem som allt annat: två svaga regler som styr
**samma** ställe i meningen får inte stå tillsammans, hur väl budgeten än räcker
— då går felet inte att attribuera.

### Urvalet: hur meningen väljs

*Skrivet 2026-09-10, sedan Julius sagt att han inte har skillsetet att designa
algoritmen själv men vill vara med och bestämma aspekterna.*

**Läget vid varje steg:**

    F   förfallna kort som ännu inte klarats i dag
    I   införda kort — det meningen FÅR röra (efter omgång 7: allt i spel,
        eftersom introfasen redan gått)
    B   budgeten, P(≥2 fel) ≤ τ

Ett steg: välj en målmängd ur `F`, bygg en mening som täcker den inom `B` och
med varje mål ensamt svagt på sin position, bedöm, lägg tillbaka det som föll
i `F`.

*Omgång 7 tog bort `N` ur läget. Nya kort införs i introfasen och är införda
när meningsfasen börjar — `N` och `I` är inte längre två mängder.*

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

#### Budgeten mäter attribution, inte svårighet

*Omgång 7. Den gamla budgeten var Σ(1−R) ≤ 1,5 och vilade på raden «nytt kort,
aldrig sett, R = 0,00» — ett tillstånd tvåfasstrukturen har byggt bort.*

Fråga vad som faktiskt går sönder när en mening packas för hårt. Inte
termineringen — den sköts av att högarna töms. Inte tiden — mätningen visar att
längre meningar är EFFEKTIVARE, 3,1 sek/kort mot 16,2. Det som går sönder är
**rättningen**: med ett fel vet diffen var det sitter, med två vet den inte.

Alltså:

    P(≥2 fel i meningen)  ≤  τ

och τ väljs inte — det är samma tolerans som retentionsmålet, precis som
fönstret i punkt 6. FSRS siktar på 0,9, alltså **τ = 0,10**.

Mätt, med R = 0,90 för förfallna och 0,99 för infört-idag och utfyllnad:

    förfallna  utfyllnad   Σ(1−R)   P(0 fel)  P(1 fel)  P(≥2 fel)
        1          5        0,15      0,856     0,138     0,006
        3          5        0,35      0,693     0,266     0,041
        5          5        0,55      0,562     0,340     0,098   <- taket
        6          5        0,65      0,505     0,362     0,132   över

**Fem förfallna per mening, plus utfyllnad.** Det är nästan exakt vad utkast
1–27 gissade — «ett nytt kort och några förfallna» — men nu härlett ur rätt
storhet i stället för ur en rad som inte kan inträffa. Σ(1−R) på taket är
**0,55, inte 1,5**: den gamla budgeten var ungefär tre gånger för slapp, och
det är därför den kändes tandlös.

**Budgeten är en front, inte ett tak.** Samma villkor, två riktningar:

    förfallna (R=0,90)   max utfyllnad (R=0,99)   total längd
            0                     53                   53
            1                     43                   44
            3                     24                   27
            5                      5                   10
            6                      0                    6   över budget

En mening får vara **kort och svår** eller **lång och lätt**. Det ÄR
svårighetsratten, och nu är ratten ett tal: τ. Högre τ ger tätare meningar,
färre meningar, kortare pass — men oftare att rättaren måste fråga. Det är en
avvägning användaren kan ha åsikter om, till skillnad från en summa hen aldrig
ser.

**Termineringen blir gratis.** En mening med ETT förfallet mål plus tio
utfyllnadskort ger P(≥2) = 0,013, under varje rimligt τ. Alltså finns alltid en
mening som kan bära vilket enskilt kort som helst, och inget kort kan bli
oåtkomligt därför att det blivit för dyrt.

**Vad budgeten INTE gör.** Den tillåter 53 kort i en mening, vilket är
orimligt. Attributionen är inte det som stoppar det — byggbarheten och
tidsratten är. Alltså: **attributionsbudgeten binder svårigheten, tidsbudgeten
binder längden.** Var exakt påfyllningen ska stanna är den enda verkligt öppna
parametern i meningsbygget, och det är där smaken för varierande längd hör
hemma — utskriven som en smak, inte gömd i en härledning.

#### ~~Variation särskiljer~~ · ~~Utfyllnadsplatserna~~ — strukna

*Strukna i omgång 7. Båda var regler för beteenden som faller ur urvalsregeln.*

Variationsregeln sa att meningen som «minst liknar de senaste» vinner.
Utfyllnadsregeln sa att lediga platser tar kort som är införda, har högt R och
setts minst nyligen. Men «setts minst nyligen» och «lägst R» är samma sak — R
faller med tiden sedan senaste mötet. Alltså:

> Ett kort du just använde har R ≈ 1,00 och är därmed det **dyraste** valet per
> vunnen information. Variation är inte en regel ovanpå urvalet; det är vad
> girigt urval GÖR.

Samma sak för formen: eftersom varje renderarbeslut är ett kort med eget R
väljer samma regel meningens skepnad. Ingen anti-upprepningsspärr behövs, och
ingen av dem kan hamna i konflikt med täckningen.

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

**Uppräkningen har två steg och inget tredje.**

1. **Prerekvisitordningen** avgör vertikalt. Kan man inte ordet kan man inte
   heller en form av ordet, alltså är formkortet OGRADERAT när ordkortet föll —
   det prövades aldrig. Julius: *«ifall vi testar ordet och formens kort och
   misslyckas med ordet så skippar vi att gradera formkortet eftersom vi helt
   enkelt inte vet.»*
2. **Minsta förklaringen** avgör horisontellt, där prerekvisiten är tyst.
   `ett stort hus` → `en stor hus` avviker på två ställen, och genuskortet
   förklarar båda; artikelns och adjektivets formkort kräver två oberoende fel.
   **Ta den minsta mängd kort vars fall förklarar samtliga avvikelser.**

> ### Rättningen ska aldrig behöva gissa.
> Är svaret tvetydigt eller felet oattribuerbart, var **uppgiften** fel vald.

*Avgjort i omgång 7, sedan tre skilda problem visat sig ha samma svar.*

| Såg ut som | Var i själva verket |
|---|---|
| flera rätta svar → rättningen måste välja | entydighetsfilter vid genereringen |
| rätt ord men inte det som testades | samma filter |
| oattribuerbart fel → rättningen måste gissa | byggregeln om positioner, punkt 5 |

Det ger ett mätbart krav: andelen möten där rättaren måste fråga ska sjunka av
**generatorns** förtjänst, inte av rättarens skicklighet. Varje gång rättningen
blir komplicerad har generatorn en bugg.

**Ett förkastat alternativ, och varför.** Utkast 27 föreslog att en tvetydighet
skulle lösas genom att ställa en isolerande mening direkt efteråt. Julius fällde
det med sin egen princip ur omprovsavsnittet nedan: har facit visats har
användaren *«ogiltigt hunnit träna precis innan»*, och ett falskt godkänt skjuter
kortet längre fram än hen klarar. Alltså: förebygg tvetydigheten vid bygget,
och när den ändå uppstår — bokför ingenting, säg ingenting.

**Och gissa aldrig med ett vägt betyg.** Julius: *«jag är rädd att ifall vi
börjar dra slutsatser på detta vis så bryter vi mot en grundfilosofi med hela
projektet.»* Han har rätt, och mekaniskt går det inte heller: `fsrs` 6.3.2 tar
en diskret `Rating` — Again, Hard, Good, Easy — utan vikt och utan partiell
kredit. Skillnaden som gör hela frågan hanterbar:

> **Om meningen var rätt eller fel är MÄTT. Vilket kort som bär skulden är
> HÄRLETT.** Härled när härledningen är entydig; gissa aldrig. Sannolikheten
> får styra vad som mäts härnäst — aldrig vad som skrivs i loggen.

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

### När mönstret blivit automatiskt

Julius: *«vid något tillfälle under inlärningen så slutar hjärnan tänka på det
viset utan endast se ordet som ordet oberoende av kontext.»*

Det är sant, och det har tre följder. **Två har redan sina mekanismer:**

- **FSRS modellerar automatiseringen som stigande stabilitet.** Ett mönster som
  gått rätt tvåhundra gånger får mycket långa intervall och slutar frågas. Det
  behövs ingen ny mekanism — kortet blir billigt av sig själv.
- **Mönsterkorten möts konstant.** Tyskans 39 ändelsekort träffas av nästan
  varje mening, precis som franskans `le`. De är alltså samma fall som redan
  har sitt svar: **fönster i stället för förfallodag.**

**Den tredje är ny, och den rör attributionen.** Ett mönsterkort möts alltid
*genom ett ord*, så en framgång är sammanblandad: skrev användaren `bilarna`
därför att hen kan `-rna`, eller därför att hen sett `bilarna` femtio gånger?

När båda är automatiserade bär mötet **ingen information**, och ett misstag
blir dessutom felattribuerat — skulden läggs på en regel som är stenhård.

> **Regeln visas bara av transfer: att få den rätt på ett ord man inte nött
> in.** Ett möte är informativt i den mån ordets eget kort är svagare än
> mönsterkortet.

Det är mätbart ur kortens egna FSRS-tillstånd och ger en urvalsregel: **vill man
pröva ett mönster ska det paras med ett färskt ord.** Det är också en
attributionsregel — faller en mening där mönsterkortet har hög retrievability
och ordkortet låg, är ordet den sannolika skulden.

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

### En bugg som måste lagas oavsett vad som raderas

`urval.py:219` avslutar `uppfyller` med `self._cache[nyckel] = träffar or
kandidater`. Klarar inget infört koncept slottens semantiska krav **släpps kravet
tyst** och vilket ord som helst ur ordklassen används.

Två följder: meningar byggs som bryter mot verbets selektionsrestriktioner, och
den signal efterfrågemätningen vilar på kastas bort i samma rad. Raden ska logga
att kravet inte gick att fylla. Se omgång 7.

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
| sannolikhet för flera fel i en mening, P(≥2) | ej styrt | ≤ τ = 0,10 |
| kortmöten där målkortet inte är ensamt svagt på sin position | ej mätt | 0 |
| nya kort som införs i meningsfasen | ej mätt | 0 |
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

    0  regelbundenhetsregeln per språk    blockerar 3; svenskan först
    1  renderarna redovisar besluten      allt annat kräver detta
    2  nivåstegarna och grafen            faller ut ur 1; kontrollera acyklicitet
    3  kortmodellen                       541 klasskort stryks
    3b ändelsetabellerna dras om          gränsen stam/ändelse är fel i 6 av 7
    4  planen och införandet              kräver 2 och 3
    5  meningsbygget under axiomet        kräver 4
    5b neutraliseringstabellen             entydigheten; 5–10 rader per språkpar
    6  rättningen                         kräver 1 för regelattribution
    7  lektioner och frekvenslista        parallellt hela vägen
    7b provsviten                         finns inte; noll test_*.py i repot

**Tre poster tillkom i omgång 7.** Steg 0 och 3b därför att gränsen mellan stam
och ändelse visade sig vara fel dragen i sex av sju språk — se punkt 11.1. Steg
5b därför att entydigheten är ett acceptanskrav utan mekanism. Och 7b därför
att ett system vars värde är att mäta exakt vad användaren kan inte bör byggas
om utan något som kan säga att attributionen fortfarande fungerar.

**Steg 1 är också billigaste sättet att fälla modellen.** När renderarna
redovisar går det att mäta hur många regler en mening faktiskt använder, och
därmed om attributionen fungerar med 133 kort i stället för 3. Faller det där,
faller det innan något raderats.

---

## 11 · Kvarstående luckor

*Omgång 1–7 avklarade. **Två luckor kvar, och punkt 1 blockerar allt annat.** Punkt 1 föddes när Julius upptäckte
att korttabellen aldrig uppdaterats efter omgång 3, punkt 2 när hans krav «täcka
ALLA inlärningsmoment» prövades mot renderarna, och punkt 3 ströks när han
frågade varför olika antal kort per språk ens vore ett problem.*

---

### 1 · Vad är enheten för ett `oregelbunden`-kort?

*Ny 2026-09-10. Upptäckt när talen skulle räknas om för alla språk.*

Omgång 3 avgjorde att `stam` och `form` slås ihop till `oregelbunden` —
«just detta ord bryter mönstret här». **Men «här» är inte definierat**, och
skillnaden är ett verkligt läromoment:

- `avoir` har futurumbasen `aur-`, och den bär sex celler. Är det **ett**
  läromoment eller **sex**?
- `aller` har `vais`, `vas`, `va`, `vont` men `all-` i imperfekt. De fyra är
  suppletiva var för sig och delar ingen bas.

Den första talar för gruppnivå, den andra för formnivå. **Båda finns i samma
språk**, vilket är skälet att frågan inte har ett självklart svar.

**Varför mina två mätförsök gav artefakter — och vad det egentligen betyder.**
Två försök att definiera «regelbunden» föll:

1. *Stam = lemmat minus infinitivändelsen.* Faller på franskans futurum, där
   ändelsetabellen redan bär `-erai` och basen alltså är `parl`.
2. *Stam = lemmat minus klassens vanligaste avkortning.* Faller på tyskan:
   `arbeiten` → `gearbeitet` är ingen avkortning, så **alla 174 tyska verb**
   blev oregelbundna i particip. Japanskan likaså, 0 av 169.

**Felet var inte skriptet — det var att regelbundenheten inte finns i datan.**
Svenskan visar det renast, och utan franska:

    arbeta   ->  arbetade     svagt, varje svensk härleder det
    gå       ->  gick         starkt, måste memoreras

`stammar.tsv` lagrar **båda** som en stam med cellen `pret`. Strukturellt är
de identiska. Och klassen skiljer dem inte: svenskans 174 verb fördelar sig på
K0 och K1, men `arbeta` och `gå` ligger i **samma klass**.

**Orsaken är att gränsen mellan stam och ändelse är dragen fel för svenskans
verb**, och det syns direkt i ändelsetabellen:

    sv  Verb  K0  pret         ändelse = ''
    sv  Verb  K1  pret         ändelse = ''

Dåtidsändelsen är **tom**. Hela `-ade`, `-de`, `-te` ligger i stammen. Så
`arbetade` blir ett `oregelbunden`-kort — det mest regelbundna som finns i
svenskan bokförs som ett undantag.

Substantiven och adjektiven är dragna rätt: `bil → bilar → bilen → bilarna` ger
`-r`, `-en`, `-rna` som riktiga ändelsekort. Det är bara verbens tempusmarkör
som hamnat på fel sida, troligen för att `åka → åkte` tappar en vokal och
tabellen valde att lägga hela härledningen i stammen i stället för att låta
ändelsetabellen bära två varianter.

**Lucka 1 är alltså inte bara «hur stor är gruppen» utan «ligger gränsen rätt».**
Och den frågan går att bedöma på svenska, vilket den franska inte gjorde.

**Alltså hjälper inte renderarnas redovisning** — utkast 22 hade fel där.
Renderaren *läste* både `arbetade` och `gick` ur samma tabell, så dess
redovisning säger «uppslagen» om båda. Frågan den kan besvara är en annan än
den här.

**Vad som faktiskt behövs: en regelbundenhetsregel per språk, skriven för
hand.** Prövat på svenskan — «lemmat plus `de`, `te` eller `dde`, med tappat
slutvokal tillåtet» — och det fungerar:

    102 svaga, härledbara:   ha/hade · brukar/brukade · åka/åkte · köra/körde
     66 starka, memoreras:   vara/var · bli/blev · kan/kunde · ska/skulle

Regeln är en rad per språk, alltså **sju beslut**, och svenskan och engelskan
kan Julius skriva själv. Det är samma manuella väg han föreslog i omgång 2:
*«En lösning är att göra alla osäkerheter manuellt.»*

**Alternativ för enheten, när regelbundenheten går att avgöra.**

- **a) Per form.** Varje oregelbunden form är sitt eget kort. Renast mot
  produktionstestet — facit är alltid något man skriver — men flest kort, och
  varje cell måste införas.
- **b) Per grupp, där en gemensam bas finns.** `aur-` blir ett kort som bär sex
  celler; `vais` blir ett eget eftersom ingen bas delas. Följer språket, men
  gruppgränsen måste definieras.
- **c) Gruppen är den renderaren själv slår upp som en enhet.** Kräver inget
  eget gränsdragande — men förutsätter redovisningen och binder korten till
  renderarens interna struktur.

#### Omgång 7: (a) och (b) är inte alternativ, och luckan är större än så

**Först: enhetsfrågan har redan svarat sig själv.** Datan skiljer de två fallen
sedan länge, och kommentaren står i koden:

    befolka.py:161   "stamgrupp >= 0 är en stam; -1 är en rest, alltså en form
                      som inte gick att härleda och därför får ett eget formkort"

- `stamgrupp ≥ 0` — delad bas över flera celler → **alternativ (b)**, ett kort
  per grupp. Det är `aur-`.
- `stamgrupp = −1` — helform, ingen delad bas → **alternativ (a)**, ett kort per
  form. Det är `vais`.

`avoir` mot `aller`, som avsnittet ovan anför som skälet att frågan saknar
självklart svar, hamnar alltså i var sin kolumn automatiskt. De är inte
alternativ utan de två fall datan redan skiljer.

**Men luckan är inte svenskans — den är sex språks.** Mätt över `stammar.tsv`,
antal stamgrupper per verb:

    språk    1    2    3    4    5    6    7    8    9   median
    de       0    0   11   52   62   19   13    2    0     5
    ja       0    2    0    3   72   89    3    0    0     6
    sv       1    7   65   18   13   36   21   12    1     4
    it       0   55   34   14   42    6    9    4    3     3
    es       0   71   41   14   19   11    7    3    1     3
    fr       0   93   21   22    9   18    7    4    0     2
    en      57   80   30    2    0    0    0    0    0     2

**Inget verb i tyskan, spanskan, franskan, italienskan eller japanskan har en
enda stam.** Ett enda svenskt verb har det. «Antal stammar» kan alltså inte
skilja regelbundet från oregelbundet i sex av sju språk.

    de arb_arbeta  arbeit · arbeite · arbeitet · arbeitete · gearbeitet   5 grupper
    de fys_hitta   find · finde · fand · fande · fänd · gefunden          6 grupper

Skillnaden mellan tyskans mest regelbundna svaga verb och ett starkt verb är
**en grupp**.

#### Hypotesen: det saknas en tredje komponent, och den är redan en korttyp

Modellen är `form = stam[grupp] + ändelse[klass, cell]` — två komponenter. Stammarna
hittas med stränganalys, så **allt ändelsetabellen inte kan uttrycka sugs upp i
stammen.** Vad en människa lär sig om `arbeiten` är tre saker:

    1  svagt mönster        -e/-st/-t/-en · -te- · ge-...-t     ändelse        finns
    2  e-inskott efter t/d  arbeit + st -> arbeitest            ???            finns inte
    3  ingenting mer                                            oregelbunden   0 kort

Rad 2 är en **morfofonologisk regel** — och i punkt 2:s egen taxonomi finns den
redan som korttyp: `regel` är «renderarens beslut». Det som saknas är att
renderaren aldrig fattar beslut UNDER ordnivån; de togs vid databygget och göts
in i stammarna.

    sv   åka -> åkte            ändelse -te  + regel: tappad slutvokal
    de   arbeiten -> arbeitete  ändelse -te  + regel: e-inskott efter t/d
    ja   飲む -> 飲んで           ändelse -て  + regel: godan む -> んで
    fr   finir -> finissons     ändelse -ons + regel: -iss- i andra konjugationen

Fyra «undantag» som inte är undantag blir en regel var, och de fyra reglerna är
vad en lärobok lär ut på sidan ett.

**Hypotesen är oprövad.** Den är visad på fyra exempel, inte på datan, och det
är den enskilt största osäkerheten i modellen. Provet som avgör den är billigt
och Julius kan bedöma det själv:

    1  Julius skriver regelbundenhetsregeln för svenska verb för hand
    2  stamanalysen körs om med regeln på
    3  medianen stamgrupper per svenskt verb mäts

       idag       4
       1-2        faktoriseringen är räddad — behåll ändelsekortet
       kvar på 4  faktoriseringen bär inte — ord+form-modellen vinner, mätt

#### Den konkurrerande modellen, och vad den kostar

Julius i omgång 7: *«det känns mycket mer logiskt att ha ordkort och formkort
eftersom de direkt representerar kunskapen som ska läras in… ifall man lyckas
skriva överhuvudtaget en form som tillhör ordet så får man rätt ord.»*

Den definitionen av `ord`-kortet **bärs över oavsett hur resten landar** — den
är bättre än lemmat som facit, och den ger en rättningsregel utan felmodell:

    strängen är någon form av lexemet?
       nej  -> ordkortet föll, formkortet OGRADERAT — det prövades aldrig
       ja   -> ordkortet klart; är det rätt cell klarade också formkortet

Men att slopa `ändelse` kostar, mätt i `Former` mot `stammar.tsv` + `ändelser.tsv`:

    språk   ord+form (lexem×cell)   faktoriserat   kvot
    de             13 617              2 733       5,0x
    es              9 936              1 953       5,1x
    it              9 204              2 223       4,1x
    fr              7 900              1 702       4,6x
    sv              4 757              1 745       2,7x
    ja              2 495              1 137       2,2x
    en              2 138                817       2,6x

Och kortantalet är inte det tyngsta argumentet. Det här är: användaren kan
`parler` i elva celler och möter sedan `regarder`. Faktoriserat är det **en**
introduktionsövning — ordet; cellerna är härledbara. Under ord+form är det
**elva**, för ett helt regelbundet verb hen redan kan böja.

Och: utan ett ändelsekort kan systemet aldrig veta om användaren har
generaliserat. Det ser `parlais`, `regardais`, `travaillais` rätt och vet
fortfarande inte om hen kan imparfait eller bara kan tre ord. Det är det enda
stället i modellen där mätbarhet skulle bytas mot enkelhet — och Julius egen
formulering talar emot det: *«en av de bästa sakerna med hela projektet är att
vi kan med exakt precision förstå exakt vad användaren kan och inte kan.»*

**Beslutet väntar på svenskprovet. Ingenting nedströms kan avgöras före det.**

---

### 2 · Aspektvalet är ett läromoment utanför systemet

*Ny 2026-09-11. Hittad när Julius krav 2 — «kortsystemet ska täcka ALLA möjliga
inlärningsmoment för meningen» — prövades mot renderarna.*

**Idag.** Renderaren tar aspekten som **indata**, den härleder den inte:

    ENKELT_TEMPUS = {
        (NUTID,     PERFEKTIV):   "pres",
        (NUTID,     IMPERFEKTIV): "pres",
        (FÖRFLUTEN, IMPERFEKTIV): "imperf",     <- imparfait
        (FRAMTID,   PERFEKTIV):   "fut",
        ...
    }

`(FÖRFLUTEN, PERFEKTIV)` saknas i tabellen och faller därför till den
sammansatta dåtiden — passé composé. Aspekten är alltså ett **val generatorn
gör och talar om**, inte något användaren avgör.

**Luckan.** Systemet lär ut *«producera imperfekt när imperfekt efterfrågas»*.
Det lär aldrig ut *«den här situationen kräver imperfekt»* — och för franskan,
italienskan och spanskan är det ett av de svåraste momenten som finns.

**Och det är inget förbiseende — det följer ur injektiviteten.** Skulle samma
svenska mening kunna bli både imparfait och passé composé hade uppgiften inte
haft exakt ett rätt svar, vilket axiomets syskonregel förbjuder. Så länge
uppgiften är «översätt den här svenska meningen» **måste** aspekten ges bort.

**Alternativ.**

- **a) Lämna det utanför.** Scopet är grammatisk produktion, inte aspektval.
  Då ska specen säga det rakt ut i stället för att kravet tros vara uppfyllt.
- **b) En egen uppgiftstyp.** Aspektvalet prövas i en uppgift som inte är en
  översättning — ett tvåval på svensk kontext, likt genuskortets införande.
  Då blir det ett kort, men det bryter formen «en mening, ett facit».
- **c) Källspråket bär aspekten synligt.** «jag arbetade varje dag» mot «jag
  arbetade igår» — svenskan har adverbialen som avgör. Då blir aspektvalet
  lärbart *inom* översättningen, men bara när generatorn kan garantera att
  adverbialet finns, och det är en ny grind.

#### Omgång 7: (c) följer av entydighetsregeln, men priset måste godkännas

Termen i punkt 1 var fel. **Injektiv** betyder att olika källmeningar ger olika
målmeningar, och det spelar ingen roll här; **surjektiv** är inte heller det.
Egenskapen som krävs är att avbildningen är en **funktion**:

> **En uppgift är giltig endast om relationen källmening → målmening är
> ENTYDIG: exakt en målmening är korrekt.**

Och entydigheten är **inget eget steg**. Den blir en rad i samma filter som de
låsta reglerna, vid genereringen — vilket den måste vara, eftersom meningarna
genereras i stunden och en neutraliseringspunkt bara spelar roll när fler än
ett av dess målvärden är UPPLÅSTA. Före `imperf` har «jag arbetade» en fransk
rendering; efteråt två.

    för varje neutraliseringspunkt (axel där källspråket gör färre skillnader):
        har målspråket mer än ett UPPLÅST värde på axeln?
            ja -> källmeningen måste markera axeln, annars förkasta specen

Alternativ **(c)** följer därmed: källspråket bär aspekten. Priset är att den
svenska prompten blir mer markerad än naturlig svenska, ju fler nivåer som
öppnas — «jag arbetade **varje dag**» i stället för «jag arbetade». Det är ett
val Julius bör godkänna medvetet, inte upptäcka i drift.

**Tabellen finns inte.** Lucka 2 är dess första rad. För sv→fr rör det sig om
5–10 rader: aspekten, modus där det inte styrs, `man` → `on`, de 16 uppmätta
homonymerna. Det är en dags arbete per språkpar, och byggordningens steg 5b.

*Samma fråga finns för de sammansatta tiderna och för modus där modusvalet inte
styrs av ett regerande ord. `rektion` täcker det som **styrs** — `vouloir` +
infinitiv, konjunktionen som kräver konjunktiv. Det som styrs av betydelsen
täcks inte.*

---

### 3 · ~~Korttypernas mix skiljer sig mellan språken~~ — struken

*Struken 2026-09-11. Julius: «Jag förstår inte riktigt vad problemet är. Varför
skulle det vara problematiskt att de har olika många kort?»*

Han har rätt. Att tyskan har 241 ändelserader och engelskan 20 är inget
designfel — **det är språken som skiljer sig, och modellen som speglar dem
korrekt.** Engelskans hela böjningslära ryms i tjugo rader därför att engelskan
har tjugo ändelser:

    Substantiv   -s · -'s · -s'        Verb   -s · -ed · -ing
    Adjektiv     -er · -est            Possessiv  -r · -rs

Att ändelserna är **färre än orden** är inte heller misstänkt — det är hela
poängen med att faktorisera. Tjugo rader betjänar engelskans 734 ord.

Kvar av punkten står bara alternativ (b), och det är ingen lucka utan en
formulering: *korttyperna är en möjlig mängd som varje språk fyller efter
behov, och mixen är en mätning, inte en norm.* Det är infört i punkt 2.

---

## 12 · Beslut ur omgångarna

### Omgång 7 (2026-09-12)

*Sju invändningar från Julius, varav fyra fällde något jag skrivit. Fyra
räknefel och två inbördes motsägelser rättade i brödtexten.*

#### Dagspasset har två faser, och det avgör budgeten

Se punkt 5. Kort: introfasen inför dagens nya kort, meningsfasen inför inga.
Axiomets «eller står i dagens plan» är en tidsordning, inte en lucka. Följden
är att inget kort med R = 0,00 kan stå i en mening, och den gamla budgetens
ankarrad beskrev ett tillstånd som inte inträffar.

#### Urvalet är en regel, och de andra faller ur den

> **De svaga korten sprids över oberoende positioner.**

Tre lager, en variationsregel och en utfyllnadsregel ersattes av den. Nyckeln
är att «setts minst nyligen» och «lägst R» är **samma tal** — R faller med tiden
sedan senaste mötet. Alltså är variation inte en regel ovanpå urvalet utan vad
girigt urval gör: ett kort du just använde har R ≈ 1,00 och är det dyraste valet
per vunnen information.

Julius krav var att beteendena inte skulle tvingas fram: *«det är väldigt
viktigt att vi inte tvingar fram beteenden utan att de kommer naturligt genom
vår optimala algoritm.»* Täckning, variation i ord, variation i form,
repetitionsskydd och längdvariation faller alla ur den enda regeln. Det enda som
INTE gör det är avsiktlig längdvariation för nöjes skull, och den står nu
utskriven som en smak i stället för dold i en härledning.

#### Budgeten mäter attribution, inte svårighet

Se punkt 5. `P(≥2 fel) ≤ τ`, τ = 0,10 ur retentionsmålet. Ger fem förfallna per
mening. Σ(1−R) på taket är 0,55 — den gamla budgeten på 1,5 var tre gånger för
slapp, vilket är varför den kändes tandlös. Budgeten är en front: kort och svår,
eller lång och lätt.

Och påståendet att svårighetstaket var termineringsgarantin är struket. Julius:
*«dagen tar slut när alla kort är repeterade… den är inte klar förrän new-högen,
again-högen och due-högen är tomma.»* Det är termineringsvillkoret; budgeten
säkrar bara att varje enskilt kort alltid går att nå.

#### Rättningen ska aldrig behöva gissa

Se punkt 6. Tre problem som såg ut som rättningsproblem visade sig alla vara
generatorvillkor. Och ett förslag föll: att lösa en tvetydighet med en
isolerande mening direkt efteråt är ett omprov i förklädnad, fällt av Julius
egen princip — har facit visats mäter nästa fråga de senaste fem sekunderna.

Julius fråga om vägda betyg besvaras på två plan. Mekaniskt: `fsrs` 6.3.2 tar en
diskret `Rating` utan vikt. Principiellt: *«jag är rädd att vi bryter mot en
grundfilosofi med hela projektet»* — och det stämmer, men bara innanför loggen.
Sannolikheten får styra vad som mäts härnäst, aldrig vad som skrivs.

#### Grindarna kollapsar till en invariant plus en grind

Julius: *«kanske man ska ha en sådan grind men att den aldrig kommer att behövas,
och ifall vi kan bevisa det genom logik så kan vi skippa den grinden.»*

Beviset: för varje nivå med en föregångare kräver grind 2 ett lyckat möte, ett
möte kräver en byggbar mening, alltså finns meningar. Det enda grind 1 fångade
därutöver är att en nivå öppnar noll kort — ett datahål, inte ett
användartillstånd. Grind 1 blir en **bygginvariant**.

Och konstruktionsstegen. Julius först: *«det känns som att alla nivåer borde vara
kort.»* Sedan, efter att ha sett vad stegarna innehåller, hans egen rättelse:

> *«Konceptet av att ha ett objekt eller konceptet av att språket har en fråga är
> något vi inte tränar. Men bakom varje ny konstruktion finns kunskap som
> användaren måste lära sig, och det är just det som borde vara kort.»*

Rätt, och det räddar både produktionstestet och grind 2: konstruktionen är inte
kortet, men **varje nivå öppnar minst ett kort** — en regel, en cell eller ett
ord. Att veta att språk har frågor är inget kort; att franskan inverterar är ett
`regel`-kort i realiseringsstegen.

#### Efterfrågan mäts som ouppfyllda mönsterkrav

Två förslag föll innan det här, och båda på Julius invändningar.

**Det första:** mät vilket saknat kort som blockerade en kandidat. Julius:
*«varför skulle generatorn från första början ha tillgång till en grupp kort som
ännu inte är introducerade? Jag trodde att den endast kunde se ord som vi redan
hade.»* Rätt — en generator som inte ser oinförda kort kan inte förkasta på
grund av dem.

**Det andra:** mät koncentrationen bland dem som faktiskt fyllde varje plats.
Julius: *«det som brister är att vi inte kan veta vad vi inte har.»* Också rätt.
Koncentration svarar på «hur trångt var det bland dem vi hade», inte på «vad
ville algoritmen ha».

**Det tredje håller, och koden räknar redan ut det.** Generatorn bygger spec
först och fyller sedan — verbets mönster säger vad varje slot KRÄVER innan något
lexem valts:

    urval.py:459   val = self.o.uppfyller(slotkrav[slot])   # vilka klarar kravet
    urval.py:460   if not val: return None                  # ingen gjorde det

Kravet — «subjektet måste vara mänskligt», «objektet måste vara ett räknebart
föremål» — är formulerat oberoende av vad som är infört. Alltså **går frågan
«vad ville den ha» att ställa utan att generatorn någonsin ser ett oinfört
kort.**

    krav som inte gick att fylla          gånger   kandidatkorten är…
    subjekt: mänsklig                       143    de oinförda mänskliga koncepten
    objekt: föremål, räknebart               88    ...
    verb med komplementslot (modalverb)      31    ...

**Generatorn beskriver hålet; införandet fyller det.** Den behöver aldrig se
kandidaterna — kravet räcker, eftersom de oinförda lexem som uppfyller kravet är
en sökning i ordboken.

> **BUGG SOM MÅSTE LAGAS OAVSETT.** `urval.py:219` avslutar `uppfyller` med
> `self._cache[nyckel] = träffar or kandidater`. Finns inget koncept som klarar
> det semantiska kravet **släpps kravet tyst** och vilket ord som helst ur
> ordklassen tas. Det gör två saker: bygger meningar som bryter mot verbets
> selektionsrestriktioner, och kastar bort exakt den signal som beskrivs här.
> Raden ska logga, inte tiga.

Införanderegeln blir en regel för alla korttyper:

    1.  ouppfyllda krav finns  -> inför kort som uppfyller dem   grammatiken först
    2.  inga krav faller       -> semantisk frekvens             ordförrådet sedan

Den självkorrigerar, den rangordnar tvärs korttyper, och omgång 5:s
artikelproblem försvinner av sig självt: en artikel som inte finns kan inte stå
som kandidat, hur ofta kravet än faller.

**Koncentrationen bärs över som sekundärsignal** — effektivt antal fyllare,
1/Σp², per plats. Den säger när en plats är på väg att bli trång innan den
faller helt, och den är mätt ur loggen över verkliga meningar precis som omgång
2 kräver. Men den är komplementet, inte måttet.

#### Mönsterfamiljen är mätt: 394 kort för sju språk

Se punkt 2. Ett ändelsekort är en ändelsesträng för en (ordklass, böjningsklass),
utan koncept i nyckeln. 831 rader i `ändelser.tsv` blir 394 distinkta läromoment;
tyskans hela böjningslära är 39 kort.

Julius krav var *«inte mängder av olika undantag, och inga kort som inte konkret
kan representera ett läromoment»*. Mönsterfamiljen klarar båda. Det är
undantagsfamiljen som är omätt, och den mäts av svenskprovet i punkt 11.1.

#### Leech skjuts upp, och ingenting förloras på det

Julius: *«det är inte otroligt viktigt att fixa direkt eftersom det inte är något
fundamentalt utan en add-on.»* Godtaget. Två anteckningar för den dag det byggs:

- **Tröskeln behöver inget valt tal.** `fsrs/scheduler.py:107` sätter
  `MAX_DIFFICULTY = 10.0`. När D nått taket och kortet fortfarande faller har
  FSRS ingen justering kvar — kortet är olärbart i sin nuvarande formulering
  enligt modellens egna termer.
- **Åtgärden är SuperMemos, inte Ankis.** Anki suspenderar efter åtta lapses (ett
  valt tal). SuperMemo behandlar ett leech som bevis för att posten är dåligt
  formulerad. Det andra passar den här modellen, för ett `oregelbunden`-kort som
  bär sex celler och ständigt faller ÄR evidens för att det är sex kort. Leech
  blir ett diagnosverktyg för kortmodellen, inte en nödutgång.

Ingenting går förlorat på att vänta: `svårighet` lagras redan per kort.

#### Oböjliga ordklasser har inget sätt att lagras

*Hittad när «36 japanska adjektiv saknar former» skulle förklaras. Det var inte
en datalucka.*

    typ = i          54/54  har former      böjs:  高い -> 高かった
    typ = na         21/21  har former      böjs via kopulan
    typ = no          0/14  har former      いっぱい · 空っぽ · 病気
    typ = verbfras    0/22  har former      乾いた · 疲れた · お腹が空いた

Hålet är inte slumpmässigt — det är **exakt de två typer som inte böjs.**
`no`-adjektiven är substantiv som tar の; `verbfras` är verbformer använda
attributivt. `paradigm/ja/adjektiv.yaml` beskriver い- och な-adjektiv men nämner
inte de två andra, så pipelinen genererade ingenting för dem.

Julius: *«borde det inte vara ett lemma och en form, alltså att det inte är
böjningsbart? Genom flaggor kan vi visa att denna form ska användas för alla
situationer.»* Precis så. **36 rader att skriva, inte 36 ord att slå upp.**

Och kortmodellen är redan rätt för dem: ett oböjligt ord har ett `ord`-kort och
inga form-, ändelse- eller undantagskort. Det är inget specialfall — det är vad
«mönstret gäller inte här» betyder när paradigmet har en enda cell.

*(Två falsklarm ströks samtidigt. «Japanskan saknar två slot-filer» var ingen
lucka: de saknade är `artikel.yaml` och `relativpronomen.yaml`, och japanskan har
varken artiklar eller relativpronomen. Att jämföra ANTAL filer mellan språk mäter
ingenting; innehållet måste jämföras, inte antalet.)*

#### Räknefel och motsägelser som rättats

| Ställe | Stod | Är |
|---|---|---|
| punkt 3, realiseringstabellen | 22 ordföljd, 111 övriga | **28 och 105** — kolumnerna summerade aldrig; 22 var konstruktionernas antal |
| punkt 3, mot koden | — | `befolka.ORDFÖLJD` har **27**; tyskan har sex regler, inte sju |
| omgång 6 om japanskan | helformerna är «rätt» | **artefakt** — en enda verbklass i tabellen, godan-verben faller ur |
| omgång 5 om efterfrågan | «en verklig signal» | **upphävd** av omgång 6, som inte markerade det |
| punkt 1 och 4b | «infört eller i planen» mot «kräver infört» | **tvåfasstrukturen** — de sa olika saker |
| punkt 11.1, termen | injektiv | **entydig** — varken injektiv eller surjektiv |
| efterfrågan, omgång 7 utkast 1 | koncentration i loggen | **ouppfyllda mönsterkrav** — koncentration ser bara det vi har |
| «36 japanska adjektiv saknas» | datalucka | **modellucka** — oböjliga typer har ingen cell |
| «japanskan saknar slot-filer» | lucka | **ingen lucka** — artikel och relativpronomen finns inte i japanskan |

#### Vad omgång 7 INTE avgjorde

- **Kortmodellen.** Ord+form mot faktoriserat. Blockerad på en rad från Julius:
  regelbundenhetsregeln för svenska verb. Allt nedströms hänger på den.
- **Den morfofonologiska hypotesen.** Visad på fyra exempel, inte på datan.
- **Aspektvalets pris.** Alternativ (c) följer av entydighetsregeln, men att den
  svenska prompten blir mer markerad än naturlig svenska är ett val som ska
  godkännas, inte upptäckas.

---


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
`oregelbunden`. Japanskan hamnar nästan helt i `oregelbunden`, och modellen
behöver inte anpassas per språk; den fördelar sig själv.

> **RÄTTAD I OMGÅNG 7.** Utkast 1–27 skrev här att japanskans helformer är
> *«rätt — dess former lärs som helheter»*. Det är fel, och det motsäger punkt
> 11.1 i samma dokument. `ändelser.tsv` har **en enda japansk verbklass**, K0,
> med `ta = た` och `te = て` — ichidan-mönstret. Godan-verben passar inte i
> det, så deras former lagras hela:
>
>     食べる   食べ · 食べよ · 食べら · 食べられ · 食べろ          ichidan, passar K0
>     飲む     飲ま · 飲み · 飲め · 飲も
>              + 飲む · 飲めば · 飲んだ · 飲んで   <- helformer, stamgrupp −1
>
> `飲んだ` och `飲んで` är det mest regelbundna som finns i japansk morfologi —
> む → んだ/んで gäller varje godan-verb på む/ぶ/ぬ. **43 % av de japanska
> verben har minst en sådan rad.** De «145 helformerna» är alltså exakt den
> artefakt punkt 11.1 beskriver för svenskan, inte ett språkfaktum.

---


### Omgång 5 (2026-09-10)

#### ~~Grind 1 binder vid två ord och aldrig mer~~ — grinden struken i omgång 7

> Mätningen står; slutsatsen drogs vidare. Att grinden ligger tusen gånger från
> att binda var förstadiet till beviset att den kan tas bort helt. Se omgång 7.

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

#### ~~Efterfrågan per ordklass är en verklig signal~~ — upphävd

> **Läsanvisning (omgång 7).** Omgång 6 strök den här mätningen och omgång 7
> ersatte den med koncentration mätt ur loggen. Avsnittet står kvar som
> historik. Slutsatsen om artiklarnas 4,84 bärs över; resten gör det inte.

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

#### ~~Grind 1 är redan en fysisk begränsning~~ — grinden struken i omgång 7

> Resonemanget höll — grinden var fysisk och inte ett valt tal. Omgång 7 visade
> att den dessutom är överflödig: grind 2 medför den för varje nivå som har en
> föregångare, och resten är en bygginvariant.

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
