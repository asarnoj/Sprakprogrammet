# Meningsgeneratorn och kortmodellen — beslut

*2026-08-13. Framtagen i diskussion, med mätningar mot databasen efter hand.
Skriven innan något byggdes.*

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
| 5 | **Lexikal egenskap** | ✅ | Genus, hjälpverb, prenominal |
| 6 | Konstruktion | ❌ | Löser upp sig i 3, 4 och 5 |
| 7 | Meningskort | ❌ | Utesluten av att meningar är färska varje gång |

Typ 5 var inte med i första genomgången och är viktig: att veta att *Buch*
är neutrum är varken ordet eller en form, men det syns när artikeln blir
fel. Det ligger redan i `Lexem.genus`, `Lexem.hjälpverb`, `Lexem.prenominal`.

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

## FSRS och de oavsiktliga repetitionerna

En mening rör 7–10 kort men valdes för ett av dem. Vad händer med de andra?

**De räknas, och det ligger inuti algoritmen.** FSRS tar faktisk förfluten
tid och beräknar hur väl du minns just då. En repetition som sker för
tidigt ger en *mindre* stabilitetsökning än en i tid — spacing-effekten är
explicit modellerad. Anki-användare repeterar för tidigt hela tiden.

Vi tvingar alltså inte in FSRS i något den inte är byggd för. Den
nedvärderar redan gratisrepetitioner själv.

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
19  läs!                            + imperativ        ✗
20  hon vet att han kom             + bisatser         ✗
21  vem läser boken?                + wh-frågor        ✗
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
| Imperativ | 161 | satsmodus |
| ~~Oböjda ordklasser~~ | ~~105~~ | ✅ prepositionsfraser byggda |

**Negation och frågor låser upp noll former** — negationsadverben har redan
sin `inv`-form. Men de mångdubblar antalet *meningar* som går att bygga av
samma ord. "Antal former" kan alltså inte vara enda måttet på en utökning.

Ordningen som valdes väger formvinst mot hur tidigt en nybörjare möter
konstruktionen: genitiv, negation, perfekt, frågor, komparation, passiv,
imperativ, resten.

## Det som blockerar

Mätt om 2026-08-14 efter de åtta utökningarna, nu på alla sju språk och med
ett verktyg i stället för för hand: `ordbok/verktyg/nåbarhet.py`. Det
instrumenterar `Uppslag.form`, sveper hela korsprodukten av det `Mening`
kan uttrycka, och räknar unionen av begärda celler mot hela lexikonet.

```
sv  3 526 / 4 988   71 %      fr  5 088 /  9 070   56 %
en  1 645 / 2 293   72 %      it  5 097 / 10 246   50 %
                              es  4 637 / 10 596   44 %
ja    770 / 2 498   31 %      de  7 839 / 23 493   33 %
```

Svenskan gick 37 % → 45 % → **71 %**. Men de sju språken skiljer sig mer än
väntat, och skälet är att **de stora onådda blocken inte är samma block**:

| Språk | Största onådda block | Vad som krävs |
|---|---|---|
| de | 96 av 147 adjektivceller — attributiv komparation | `Nominalfras.attribut` bär ingen grad |
| fr/es/it | konjunktiv (6–12 celler) + konditionalis (6) | bisatser respektive villkorssatser |
| alla | imperativ | satsmodus |
| de | stark deklination m/n sg — "roter Wein" | `Bestämdhet` saknar artikellös fras |
| ja | jisho/ta/nai — de enkla formerna | register, utanför scope |

**Tyskans siffra är låg av en enda anledning.** 16 121 av 23 493 tyska
former är adjektivformer, och två tredjedelar av adjektivparadigmet är
komparativ och superlativ i attributiv ställning. `Grad` finns på `Mening`
och styr predikativet; attributet är fortfarande bara en konceptnyckel.
Att flytta graden in i `Nominalfras.attribut` är den enskilt största
utökningen som återstår — värd omkring 10 500 tyska former.

**Generatorn är inte längre blockerad av uttrycksförmågan.** Med 71 % på
svenska och 72 % på engelska avgörs det som övas nu av strategin, inte av
vad specen kan säga. Frågan om täckande mot opportunistisk urvalsstrategi
är därmed mogen att ta.
