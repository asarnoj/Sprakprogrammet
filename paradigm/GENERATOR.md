# Meningsgeneratorn och kortmodellen — beslut

*2026-08-13, utökad 2026-08-14. Framtagen i diskussion, med mätningar mot
databasen efter hand. Skriven innan något byggdes.*

---

## Premissen

Meningar **författas inte, de löses fram**. Systemet ser vilka kort som är
förfallna och konstruerar en mening som tränar dem, blandat med ord
användaren redan kan.

Det inverterar den vanliga ordningen och gör två saker bärande: de
semantiska restriktionerna (se `RESTRIKTIONER.md`) och en kortmodell som
tål att många kort prövas samtidigt.

**Meningen genereras på nytt varje gång.** Användaren ser aldrig samma
mening två gånger. Det utesluter meningen som korttyp och möjliggör exakt
styrning av svårighetsgraden.

---

## Korttyperna

Sju identifierades. Fyra används.

| # | Typ | Läge | Motivering |
|---|---|---|---|
| 1 | **Ordkort** | ✅ | Att ordet finns och betyder något |
| 2 | **Formkort** | ✅ | En specifik böjd form |
| 3 | **Böjningsval** | ✅ | Att en viss böjning *ska* användas |
| 4 | **Ordföljd** | ✅ | Ledens inbördes ordning |
| 5 | **Lexikal egenskap** | ✅ | Genus, hjälpverb, prenominal, böjningsklass |
| 6 | Konstruktion | ❌ | Löser upp sig i 3, 4 och 5 |
| 7 | Meningskort | ❌ | Utesluten av att meningar är färska varje gång |

Typ 5 var inte med i första genomgången och är viktig: att veta att *Buch*
är neutrum är varken ordet eller en form, men det syns när artikeln blir
fel. Det ligger redan i `Lexem.genus`, `Lexem.hjälpverb`, `Lexem.prenominal`.

**Böjningsklass tillkom 2026-08-14** och hör hemma här av samma skäl: att
franskans *finir* och *partir* böjs olika syns inte i något av orden själva.
Se nästa avsnitt för hur stor den posten är — den visade sig liten och
mätbar.

### Ord mot form

> **Formen är det som fysiskt läggs i meningen. Att testa formen testar
> ordet per definition.**

Följderna:

- **Fallerar ordkortet testades formen aldrig.** Den får inget betyg och
  behåller sitt passerade förfallodatum. Man kan inte böja ett ord man inte
  kan hämta fram, och utan den regeln skulle ett enda ordglapp fälla
  trettio formkort på en gång.
- **Ska ett ordkort repeteras väljer systemet den form som ger lagom
  svårighet.** Ordkortet behöver ingen egen presentation — det lånar en form.
- Ordkortet dominerar tidigt i ett ords liv, formkorten senare.
- Ett formkort som länge varit förfallet utan att kunna prövas är en signal
  att ordet hör tillbaka till introduktionen, inte till repetition.

### Ordföljdskort

**Ett kort per ordföljdsregel som renderaren faktiskt implementerar.**
Tyska får V2, satsklammer och dativ-före-ackusativ; svenska SVO och
adverbial-sist. Skälet är hållbarhet — kortlistan kan inte glida isär från
koden när reglerna *är* koden.

Franskans adjektivplacering är **inget** ordföljdskort. *Grand* står före,
*rouge* efter; det är `Lexem.prenominal`, alltså typ 5. Ingen regel att
lära sig, utan något man vet per ord.

---

## Hur fint ska ett formkort skäras?

*Avgjort 2026-08-14, efter fyra mätningar mot databasen.*

Frågan uppstod när tyskan visade sig ha **76 böjda former per adjektiv**.
Ska var och en vara ett eget kort? Spänningen är verklig och går åt båda
hållen: högsta möjliga upplösning på vad användaren kan, mot att utnyttja
att den som kan en regel får alla orden gratis.

```
              sv    en    de    fr    es    it    ja      former per ord
Substantiv     8     4     3     2     2     2     1
Verb          10     4    22    38    49    46    10
Adjektiv       8     2    76     4     4     4     5      ← ensam avvikare
```

76 är alltså inte typiskt. Det är det enda stället i hela databasen där ett
ord har fler än 49 former.

### Mätning 1: de 76 är inte 76 fakta

```
15 792 former (111 tyska adjektiv × ~76)
   333 fakta om ORDEN      111 adjektiv × 3 stammar (groß / größer / größt)
   144 fakta om SYSTEMET   ändelsetabellen, delad av alla adjektiv
   ───
   477 oberoende fakta, inte 15 792
```

**97,9 % av alla former är stam plus den ändelse cellen alltid har.**
Avvikelserna är inte utspridda: de är *orange*, *rosa* och *lila* — tre
oböjliga färgadjektiv som därför "avviker" i samtliga 111 böjda celler.

### Mätning 2: verben beter sig tvärtom

```
              former/ord   stammar (median)
de verb           22             5
sv verb           10             4
es verb           49             2
it verb           46             2
fr verb           38             1
```

Spanska verb har 49 former men två stammar; tyska har 22 men fem.
**Antalet former säger nästan ingenting om hur mycket som ska läras.**
Franskans 38 former är ett ord plus en tabell, tyskans 22 är fem separata
saker att veta.

Därför har frågan inget policysvar. Den har ett mätvärde per språk och
ordklass.

### Beslutet

> **En form får ett eget kort när den inte går att härleda ur det
> användaren redan har kort för.**

Ingen lista över undantag behövs — undantagen definierar sig själva genom
att misslyckas med härledningen, och testet är detsamma i alla sju språk.
*Orange* får kort för att den faller ur tabellen. *Gehen* får fem stamkort
för att den har fem stammar. *Hablar* får två.

Upplösningen försvinner inte, den **flyttar**. Systemfakta är kort de också
— det är typ 3 — så *dem größte* i stället för *dem größten* fäller
ändelsekortet, medan *dem großen* i stället för *dem größten* fäller
superlativstammen. Fortfarande två kort, men de rätta två.

```
        per cell   stam+system
de        23 494         1 929      12×
es        10 608         1 414       8×
fr         9 070         1 287       7×
sv         4 988         1 069       5×
en         2 293           934       2×
```

Faktorn följer hur mycket *system* språket har, vilket är precis det en
inlärare lär sig som en regel.

### Mätning 3: klasstillhörighet måste ibland läras

Invändningen som fyllde i hålet: om ett ord tillhör en böjningsklass är
DET en egenskap hos ordet, och den täcks varken av stammen eller av
tabellen. Mätt som "går ordets ändelsesignatur att gissa ur lemmats
stavning?":

```
                  klasser   går att gissa   måste läras per ord
de/Verb              150         17 %              145
it/Verb               69         44 %               97
fr/Verb               61         72 %               48
sv/Verb               87         73 %               47
de/Substantiv         81         83 %               45
ja/allt             1–23        100 %                0
```

**~500 ord över sju språk.** Två saker faller ut:

Där oregelbundenheten är hög **kollapsar klasskortet in i stamkortet**.
150 klasser på 174 tyska verb betyder att nästan varje starkt verb är sin
egen klass — att kunna `ging` *är* att kunna att *gehen* inte är svagt.

Det separata kortet behövs bara när klassen ändrar ÄNDELSER utan att ändra
stammen: fr *finir* mot *partir*. Där är det en lexikal egenskap av samma
sort som genus, alltså typ 5.

### Universaliteten, och varför den inte spårar ur

Stam-plus-ändelse är **ingen universell modell**. Den förutsätter
konkatenativ morfologi. Arabiskans rot och mönster (k-t-b → *kataba*,
*kitāb*, *maktūb*) har ingen stam att skala av; kinesiskan böjer inte alls.

Det som generaliserar är inte uppdelningen utan **kriteriet**, och det
faktum att härledbarheten *mäts* i stället för antas. Mätningen gav olika
svar per språk redan inom de sju: 97,9 % för tyska adjektiv, 13,7 % för
tyska verb med en stam, 100 % förutsägbarhet för japanska.

Två skydd, båda sådant projektet redan gör i övrigt:

- **Uppdelningen lagras som data, inte som kod.** Per språk och ordklass:
  vilka celler grupperar sig till vilken stam, vilka ändelser delas. Samma
  princip som `Mönster.språk` som skuggar det universella.
- **Per-cell-modellen är GOLVET, inte alternativet.** Visar ett språks
  mätning låg härledbarhet överallt blir svaret automatiskt "varje form är
  sitt eget kort". Vi satsar inte på att stammar fungerar; vi mäter hur
  mycket de sparar och tar besparingen där den finns.

Det värsta som kan hända med ett framtida språk är att det inte får någon
rabatt — inte att kortmodellen blir konstig.

### Stamuppsättningen, härledd 2026-08-14

`ordbok/verktyg/stammar.py` räknar fram uppdelningen ur `Former` och skriver
`ordbok/stammar.tsv` (11 479 rader) och `ordbok/ändelser.tsv` (831).

```
                    former   klasser  ändelser  stammar  rester    kort
de/Adjektiv         16 121         1       147      275     476     898   18×
es/Verb              9 287         3       159      913     351   1 423    7×
it/Verb              8 996         3       156      840     520   1 516    6×
fr/Verb              7 815         2        90      519     528   1 137    7×
de/Verb              5 367         2        62      949     102   1 113    5×
ja/Verb              1 671         1        10      858     183   1 051    2×
de/Substantiv        1 500         2        12      651       1     664    2×
──────────────────────────────────────────────────────────────────────────
SUMMA               61 416                  831    9 013   2 466  12 310    5×
```

**61 416 former blir 12 310 kort.** Tyska adjektiv går från 16 121 till 898.

Ändelsen väljs som den längsta som en tröskelandel av orden delar, med ett
**tak på längden** — och taket är hela metoden. Utan det väljs `-sten` för
tyskans superlativ, ett suffix som mycket riktigt återkommer men som bakar
in gradmarkören och gör varje oregelbunden superlativ till en rest: `groß` →
`größte` slutar inte på `-sten`. Med taket blir ändelsen `-en`, stammen
`größt`, och alla fem superlativceller delar den.

Tröskel och tak söks per språk och ordklass genom att minimera kortantalet.
Vilket värde som är rätt beror på hur mycket språket delar och går inte att
veta i förväg — samma hållning som resten av projektet: mät, anta inte.

**Kvalitetsmåttet är var resterna hamnar.** Sprids de jämnt över lexikonet är
analysen fel; samlas de hos de ord som faktiskt är oregelbundna är den rätt.

```
de   33 av 560 ord ger rester      värst: rosa, lila, orange (oböjliga), groß
es   57 av 561                     värst: ser
fr   72 av 551                     värst: être och de vanligaste oregelbundna
```

Det är utfallet man vill se: metoden hittar oregelbundenhet, den skapar den
inte.

**Resultatet är en approximation, inte en morfologisk analys.** Sökningen
hittar inte alltid minimum — tyska adjektiv landar på 898 kort där 813
troligen går, därför att alla celler i en grad måste byta ändelselängd
samtidigt medan sökningen rör en åt gången. Det spelar ingen roll för
kortmodellen: skillnaden är tio procent i en ordklass, och kortidentiteten
bygger på konceptnyckel och stamgrupp, inte på att uppdelningen är optimal.

### Testet, i en mening

Gränsdragningen går att avgöra utan att räkna, med den här frågan:

> **Om inläraren lär sig det här — vad mer blir rätt på köpet?**
>
> Ingenting → ordkort.  Alla ord i klassen → systemkort.
> Alla ord med egenskapen → typ 5.

Fyra fall som visar den i arbete:

| Inläraren skriver | Facit | Vad som fallerar | Varför det är rätt |
|---|---|---|---|
| den **störst** boken | största | systemkort: attributiv superlativ tar bestämd form | samma fel kommer i *vackrast*, *intressantast* — ett missförstånd, inte hundra |
| dem **größte** Bruder | größten | systemkort: svag deklination m dat tar -en | hen KAN superlativen av *groß*; hen kan inte tabellen |
| yo **dormo** | duermo | stamkort: *dormir* har `duerm-` under betoning | ändelsen `-o` var rätt använd — regeln satt, ordet inte |
| **der** Mädchen | dem | typ 5: genus hos *Mädchen* | felet syns på artikeln, kortet hör till substantivet |

**Priset**, sagt rakt ut: det delade kortet kan inte peka ut vilket ord som
drog med sig felet. Sätter du fel ändelse på ett adjektiv men rätt på tjugo
andra ser kortet 21 repetitioner med ett fel och förblir starkt. Alternativet
påstår i gengäld att du kan `-en` efter `dem` för *Bruder* men inte för
*Vater* — att det vore två separata kunskaper. Det är det inte, och sitter
felet ändå i ett visst ord fälls ordets eget stamkort bredvid.

---

## FSRS och de oavsiktliga repetitionerna

En mening rör 7–10 kort men valdes för ett av dem. Vad händer med de andra?

**De räknas, och det ligger inuti algoritmen.** FSRS tar faktisk förfluten
tid och beräknar hur väl du minns just då. En repetition som sker för
tidigt ger en *mindre* stabilitetsökning än en i tid — spacing-effekten är
explicit modellerad. Anki-användare repeterar för tidigt hela tiden.

Vi tvingar alltså inte in FSRS i något den inte är byggd för. Den
nedvärderar redan gratisrepetitioner själv.

**Kostnaden, sagt rakt ut:** repeterar man systematiskt i förväg slutar
intervallen växa, och arbetsbördan ligger kvar. Modellen tar ingen skada,
men effektiviteten sjunker. Följden för sessionen är daglig kvot först och
frivillig fortsättning sedan — först blir det bara förtidsrepetition, men
efterhand skjuts korten fram och det uppstår rum för nytt.

### Schemalagda kort mot mätta kort

*Avgjort 2026-08-14.* Systemkorten är delade och möts därför mycket oftare
än ord. Mätt över 321 renderade tyska meningar:

```
Substantiv  nom_akk_gen_pl    0,91 ggr/mening      ← det mest frekventa
Substantiv  nom_sg            0,52
Verb        pres_3sg          0,46
median över alla 58            0,07 ggr/mening
ett vanligt ORD                0,012 ggr/mening
```

Vid 20 meningar om dagen möts det vanligaste systemkortet arton gånger,
medianen 1,4 gånger, ett vanligt ord var fjärde dag.

**Ett kort som möts i nästan varje mening går inte att schemalägga — och
behöver inte det.** Spacing finns för att motverka glömska, och något man
möter arton gånger dagligen glöms inte. Fallerar användaren det gör
prioritering ingenting, eftersom kortet skulle ha dykt upp ändå.

Schemaläggaren har alltså ingen spak för dem. Det är inte ett fel i FSRS —
kön är fel verktyg för något allestädes närvarande. Därav uppdelningen:

> **Schemalagda kort** avgör vilken mening som byggs.
> **Mätta kort** följs upp — rätt/fel registreras, resultatet syns för
> användaren och styr upplåsning — men de står aldrig i kön.

Gränsen sätts på uppmätt exponeringsfrekvens, inte på en tumregel.

### Misslyckade kort

**Inga relearning-steg behövs.** Ett kort som fallerat får hög prioritet i
nästa generering och dyker upp igen inom några meningar — i en *annan*
mening, vilket är bättre än att se samma kort igen.

Generering ersätter Ankis tiominutersmekanik. Det är ett av få ställen där
den här modellen är enklare än Anki.

### Kontexteffekten

Minns du *gaben* delvis för att *wir* stod bredvid var det ingen fristående
framplockning, och kortet skjuts längre fram än isolerad testning motiverat.

**Det är rätt ändå.** Du behöver aldrig kunna *gaben* isolerat — du behöver
producera den när du bygger en mening. Kontexten är inte brus i mätningen,
den är en del av det som mäts. Isolerad framplockning vore att mäta något
användaren inte behöver.

Risken ligger åt andra hållet: dyker en form bara upp i samma sammanhang
lär man sig frasen, inte formen. Det löser färska meningar redan.

---

## Svårighetsgrad

FSRS ger R, sannolikheten att kortet minns just nu. Då är

```
förväntat antal fel i meningen  =  Σ (1 − R)  över meningens kort
```

Ett kort du minns med 95 % bidrar med 0,05, ett med 30 % bidrar med 0,70.
Att lägga till fem lätta ord flyttar summan knappt — ett svårt ord blir
inte lättare av sällskap, vilket var kravet.

**Rikta mot 1–2 förväntade fel per mening.**

Meningen behöver aldrig ett samlat betyg. **Betyget sätts per kort**,
eftersom diffen lokaliserar felen.

---

## Attribution: vems fel var det?

### Renderaren lämnar en beroendekarta

Flera kort hör till ett ord medan felet syns på ett **annat** ord:

```
das Buch      genusfelet syns på "das", kortet hör till "Buch"
ist gegangen  hjälpverbsfelet syns på "ist", kortet hör till "gehen"
```

Renderaren vet det här — den slog upp egenskaperna medan den byggde. Så
den ska lämna ifrån sig mer än en sträng: **en karta från varje token till
de kort den beror på.**

```
das  →  formkort(der, n_nom)  +  genuskort(Buch)
Buch →  ordkort(Buch)  +  formkort(Buch, nom_sg)
```

Kartan kan aldrig hamna ur synk, eftersom den är renderaren som talar.
`Uppslag.form` känner redan till `(lexem, cell)`.

### Vad datan redan avgör

Databasen innehåller varje form med axelkoordinater, så attribution är
uppslag och inte gissning:

```
skrev "gab", förväntat "gaben"    → RÄTT ord, fel cell. Skiljer på: numerus
skrev "ger", förväntat "gav"      → RÄTT ord, fel cell. Skiljer på: tempus
skrev "bok", förväntat "boken"    → RÄTT ord, fel cell. Skiljer på: species
skrev "der", förväntat "dem"      → RÄTT ord, fel cell. Skiljer på: kasus
skrev "nahm", förväntat "gaben"   → ingen form av geben — fel ord
```

### När datan inte räcker

`die Buch` kan vara fel artikelform eller fel genus. Tre mekanismer, i tur
och ordning:

1. **Meningen vittnar.** Skriver användaren `die rote Buch` är
   adjektivändelsen konsekvent med femininum — hen kan artikelparadigmet
   och tror att *Buch* är feminint. Genuskortet fällde. Är hen inkonsekvent
   är det artikelformen. Ju fler kongruerande ord, desto säkrare.
2. **Historiken.** Vittnar meningen inte: skyll på det kort som har lägst R.
   Har användaren producerat `das` korrekt fem gånger nyligen är
   artikelformen stark, och det är *Buchs* genus som brister.
3. **Självrättning som möjlighet, inte fråga.** Visa vad systemet antog —
   *"jag trodde du missade att Buch är neutrum"* — med möjlighet att rätta.
   Ingen dialogruta efter varje fel.

**Felattribution självläker.** Skyller systemet fel får det kortet en
repetition det inte behövde och klarar den; det rätta kortet förblir svagt
och blir skyldig nästa gång. Beslutet måste inte vara rätt varje gång, bara
inte systematiskt fel.

Att skylla på **båda** korten valdes bort: det straffar garanterat ett kort
användaren kan, varje gång. Mekanism 1 och 2 har fel ibland; att alltid
skylla på båda har fel halva tiden per definition.

---

## Var kortlagret bor

*Avgjort 2026-08-14, innan något byggdes.*

**Repetitionshistoriken ligger i en EGEN databasfil, inte i `sprak.db`.**
`ordbok import --återinitiera` bygger om språkdatabasen från grunden, och
en användares historik är det enda i systemet som inte går att återskapa.

**Ett kort får aldrig peka på `Former.id`.** Överlämningen slår fast att
DELETE/INSERT flyttar id:n — det är redan skälet till att
`granskningsrattelser.sql` ligger utanför migrationerna. Den stabila
nyckeln är den naturliga:

```
formkort    (konceptnyckel, språk, variant, cell)
stamkort    (konceptnyckel, språk, variant, stamgrupp)
systemkort  (språk, ordklass, klass, cell)
typ 5       (konceptnyckel, språk, egenskap)
```

Fyra strängar i varje fall, alla oberoende av radordning. En ombyggd
språkdatabas ska kunna mötas av en orörd inlärardatabas.

---

## Övriga beslut

**Inmatning: fritext.** Mekanisk rättning först — databasen har alla former
med koordinater, så uppslag ersätter gissning. LLM först om det mekaniska
tar slut, inte i stället för att försöka. Andra övningsformer (flerval,
bild, tal) byggs ovanpå samma teknik senare.

**Riktning: båda.** Källspråk → målspråk och tvärtom, från början, så att
både läs- och skrivförmåga tränas.

**Kursmodell.** Man väljer källspråk och målspråk; kombinationen är låst per
kurs. Alla kombinationer av de sju är tillåtna. Flera kurser parallellt går
bra.

**Strategi: täckande med reservutgång.** Bygg meningen om det går, skjut upp
kortet om det inte går. Förvräng aldrig en mening för att klämma in ett kort.

**Upplåsning: automatisk tröskel, användaren får skjuta upp.** Nivån öppnas
när tillräckligt är kunnat, men man tvingas inte börja.

**Undervisning vid upplåsning**, med möjlighet att gå tillbaka till
lektionen. Att undervisa en regel och att schemalägga den är olika saker.

---

## Mätningar som beslutet vilar på

**Inget ord är strandat.** Varje substantiv passar som objekt till minst 39
av 93 verb (median 53); varje adjektiv beskriver minst 17 av 259 substantiv.
Generatorn hittar alltid någon mening och kan vara kräsen om annat.

**Kortmängden är inget hinder.**

```
             ord/mening    former totalt    meningar för att röra varje form
svenska         7,3            4 742                 647
tyska           9,7           13 271               1 364
franska         9,1            7 899                 871
```

13 000 tyska kort låter oöverstigligt, men en mening rör tio åt gången. Vid
20 meningar om dagen är hela beståndet genomgånget på drygt två månader.

---

## Komplexitetsstegen

Nivåerna är **finare än specutökningarna**, och tio av dem fungerar redan.
Att begränsa generatorn till en nivå är generatorns sak, inte specens —
utökningarna flyttar bara taket.

```
 1  flickan sover                   subjekt + verb
 2  flickan läser en bok            + objekt
 3  boken                           + bestämdhet
 4  böcker                          + numerus
 5  en röd bok                      + adjektiv
 6  sin bok                         + possessiv
 7  ger sin bror en bok             + indirekt objekt
 8  ... igår                        + adverbial
 9  gav / ska ge                    + tempus
10  flickans bok                    + genitiv          ✅ 2026-08-13
11  hon är glad / hon är läkare     + predikativ       ✅ 2026-08-13
12  flickan läser inte              + negation         ✅ 2026-08-13
13  hon vill läsa / börjar att läsa + infinitivkompl.   ✅ 2026-08-13
14  har läst / hade läst            + perfekt          ✅ 2026-08-13
15  hon läser i skolan              + prepositionsfras ✅ 2026-08-13
16  läser flickan boken?            + ja/nej-fråga     ✅ 2026-08-13
17  boken lästes / blev läst        + passiv           ✅ 2026-08-13
18  boken är större än huset        + komparation      ✅ 2026-08-13
──────────────────────────────────  allt ovan fungerar
    japanskan saknar både infinitivkomplement och perfektform
19  läs boken!                      + imperativ        ✅ 2026-08-14
20  hon vet att han kom             + bisatser         ✅ 2026-08-14
21  vem läser boken?                + wh-frågor        ✅ 2026-08-14
──────────────────────────────────  stegen är slut
```

## Nivåerna härleds ur slot × frastyp

Den ursprungliga ordningen var min rangordning på känsla. En bättre metod:
läs `MönsterKrav.slot` och `MönsterKrav.frastyp` — kolumnen som legat
ifylld sedan mönstertaggningen utan att någon läst den — och låt datan
säga vad som är möjligt.

```
slot         frastyp             antal   läge
subjekt      Nominalfras          174    ✅
objekt       Nominalfras           93    ✅
io           Nominalfras            5    ✅
predikativ   Adjektivfras           4    ✅ 2026-08-13
predikativ   Nominalfras            3    ✅ 2026-08-13
──────────────────────────────────────────────
komplement   Infinitivfras         12    ✅ 2026-08-13
objekt       Bisatsfras            11    ✗   hon vet att han kom
kommunikat   Bisatsfras            10    ✗   hon säger att han kom
kommunikat   Nominalfras            6    ✗
objekt       Infinitivfras          6    ✗   hon vill springa
adverbial    Prepositionsfras       3    ✗   hon är i skolan
io           Prepositionsfras       1    ✗
komplement   Bisatsfras             1    ✗
adverbial    Adverbfras             1    ✗
kommunikat   Infinitivfras          1    ✗
```

Det avslöjade att nivåerna har **fyra dimensioner**, inte en:

| Dimension | Vad det är | Exempel |
|---|---|---|
| A | slot × frastyp | objekt kan vara bisats |
| B | vad som fyller frasen | bestämdhet, numerus, attribut, ägare |
| C | verbparametrar | tempus, aspekt, modus, diates |
| D | satstyp | nekande, frågande |

Den första listan — negation, perfekt, frågor, komparation, passiv,
imperativ — var nästan bara C och D. **Hela dimension A saknades.**

Och den innehöll de två viktigaste posterna: `predikativ` har bara fyra
verbmönster men två av dem är `vara` och `bli`, och `komplement`
+ Infinitivfras rymmer alla sju modalverb. Metoden flyttade dem från sist
till först.

## Utökningarnas avkastning

Mätt på svenska: vilka celler är onådda, och vad låser upp dem?

| Utökning | Former | Vad `Mening` behöver |
|---|---|---|
| ~~Genitiv~~ | ~~992~~ | ✅ `Nominalfras.ägare` |
| ~~Passiv~~ | ~~601~~ | ✅ `Diates` |
| ~~Perfektparticip~~ | ~~454~~ | ✅ används av bli-passiven |
| ~~Komparation~~ | ~~294~~ | ✅ `Grad` |
| ~~Perfekt~~ | ~~165~~ | ✅ `Aspekt.PERFEKT` |
| ~~Imperativ~~ | ~~161~~ | ✅ `Satsmodus` |
| ~~Oböjda ordklasser~~ | ~~105~~ | ✅ prepositionsfraser byggda |

Tabellen mäter bara svenskan, och det visade sig underskatta imperativen
grovt. Svenskan har EN imperativform; de andra sex har tre till fem, och
spanskans nekade imperativ drar dessutom in halva konjunktivparadigmet.
Mätt på alla sju blev utökningen värd **3 744 former**, inte 161:

```
es +1 388   (860 imperativ + konjunktiven som den nekade formen kräver)
it   +674     de +668     fr +507     ja +346     sv +161     en ±0
```

Engelskan vinner noll: `inf_imp` ÄR imperativcellen, och den var redan nådd
som infinitiv. Att en utökning ger noll former i ett språk och 1 388 i ett
annat är regel, inte undantag — vilket är skälet att mäta per språk.

**Wh-frågorna är det motsatta fallet.** De låser upp 8–23 former per språk
— frågeorden själva, inget mer — men de är den utökning en nybörjare möter
tidigast av alla. "Antal former" är ett dåligt mått också åt det hållet.

**Bisatserna är det tydligaste fallet.** Sex av sju språk vinner NOLL
former: en bisats använder samma celler som en huvudsats, bara i annan
ordning. Japanskan vinner 343 (45 → 58 %), därför att den byter FORM och
inte bara ordföljd — bisatsen står alltid i enkel form. De cellerna stod
tidigare bokförda som "register, utanför scope". Det var fel: plain/polite
är register i huvudsats men grammatik i bisats, och en mätning som bara
räknar former hade aldrig avslöjat skillnaden.

**Negation och frågor låser upp noll former** — negationsadverben har redan
sin `inv`-form. Men de mångdubblar antalet *meningar* som går att bygga av
samma ord. "Antal former" kan alltså inte vara enda måttet på en utökning.

Ordningen som valdes väger formvinst mot hur tidigt en nybörjare möter
konstruktionen: genitiv, negation, perfekt, frågor, komparation, passiv,
imperativ, resten.

## Det som blockerar

Mätt om 2026-08-14 efter de elva utökningarna, nu på alla sju språk och med
ett verktyg i stället för för hand: `ordbok/verktyg/nåbarhet.py`. Det
instrumenterar `Uppslag.form`, sveper hela korsprodukten av det `Mening`
kan uttrycka, och räknar unionen av begärda celler mot hela lexikonet.

```
sv  4 728 / 4 988   95 %      de 19 242 / 23 494   82 %
en  2 034 / 2 293   89 %      it  7 877 / 10 246   77 %
ja  1 472 / 2 498   59 %      fr  6 650 /  9 070   73 %
                              es  7 114 / 10 608   67 %
```

Svenskan gick 37 % → 45 % → 71 % → **78 %**. Men de sju språken skiljer sig
mer än väntat, och skälet är att **de stora onådda blocken inte är samma
block**:

| Språk | Största onådda block | Vad som krävs |
|---|---|---|
| fr/es/it | konditionalis (6 celler) | villkorssatser |
| ja | ku, kereba, pot, vol | adverbiell adjektivform, villkor, potentialis, volitiv |
| ja | ku, kereba, pot, vol | adverbiell adjektivform, villkor, potentialis, volitiv |

**Tyskan var låg av en enda anledning, och den är åtgärdad.** 16 121 av
23 494 tyska former är adjektivformer, och två tredjedelar av paradigmet är
komparativ och superlativ i attributiv ställning. `Grad` fanns på `Mening`
och styrde predikativet; attributet var bara en konceptnyckel. Med
`Attribut(koncept, grad)` gick tyskan **36 → 61 %**, en vinst på 5 886
former — den största enskilda utökningen i projektet.

Kvar i tyskan är den STARKA deklinationen: 39 celler som kräver en fras helt
utan determinerare ("roter Wein", "kaltes Wasser"). `Bestämdhet` har bara
OBESTÄMD och BESTÄMD, och den obestämda ger "ein roter Wein".

**Fyra gånger har SVEPET varit det som begränsade mätningen**, och varje
gång såg det ut som en spec-brist:

```
subjektet var alltid tredje person      hela personböjningen såg onåbar ut
attributet satt bara i objektet         bara ackusativ mättes
bisatsens subjekt var 3sg               2 av 12 konjunktivceller mättes
ägaren var alltid bestämd singular      genitivböjningen såg onåbar ut
```

Den sista tog svenskan från 80 till **95 %** och engelskan från 79 till 89 %
utan att en rad renderarkod ändrades. Mönstret är alltid detsamma: en axel
som varieras i huvudsatsen men inte i den inbäddade frasen.

**Modusrektionen flyttade de tre romanska språken mest av allt.** it 57 →
77 %, fr 62 → 73 %, es 57 → 67 % — konjunktivparadigmet är 6–12 celler per
verb och var helt onått innan bisatserna kunde styras i modus. Italienskan
gick från näst sämst till näst bäst av de sju.

Men **halva den vinsten låg i svepet igen**: med bisatsens subjekt låst till
tredje person singular mättes bara 2 av 12 konjunktivceller, och siffrorna
stannade på 64/59/60 %. Samma artefakt som huvudsatsens subjekt hade, en
nivå ner. Tredje gången personvariation visade sig vara det som begränsade
mätningen.

**Mätningen mäter också sig själv.** Japanskan låg på 31 % tills
uppmaningen byggdes — men bara 8 av de 346 formerna syntes först, eftersom
renderaren hämtade て- och ない-cellerna direkt ur `_celler` i stället för
genom `Uppslag.form`, som är den enda väg instrumenteringen ser. Samma
genväg fanns i engelskans presens och preteritum och i den syntetiska
komparationen. Alla är omlagda nu, vilket lyfte sv 71→75 %, en 72→78 % och
ja 31→45 % utan att ändra en enda renderad mening.

Det spelar roll bortom mätningen: **generatorns attribution bygger på exakt
samma väg.** En form som hämtas förbi `form()` går inte att knyta till ett
kort, och felet hade upptäckts först när generatorn inte kunde svara på
vilket kort som fällde en mening.

**Generatorn är inte längre blockerad av uttrycksförmågan.** Med 78 % på
svenska och engelska avgörs det som övas nu av strategin, inte av vad
specen kan säga. Frågan om täckande mot opportunistisk urvalsstrategi är
därmed mogen att ta.
