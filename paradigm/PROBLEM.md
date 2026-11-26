# Problemen systemet ska lösa

*Påbörjad 2026-08-19. Utökad 2026-08-23 efter genomgång med kommentarer på
varje post. Det här dokumentet listar PROBLEMEN, inte lösningarna.*

`GENERATOR.md` är organiserad efter **beslut** — den säger vad vi valde och
varför, i den ordning valen fattades. Det gör den svår att använda som karta:
man ser svaren men inte frågorna, och därmed inte heller vilka frågor som
fortfarande är obesvarade.

Det här dokumentet vänder på det. Varje post är en **fråga systemet måste
kunna svara på**. Under frågan står tre saker, och bara de som finns:

- **vad frågan egentligen är**, och varför den är svårare än den låter
- **var vi står** — vad systemet gör idag, med mätningen som stöder det
- **vad som är obesvarat** — de frågor vi vet att vi inte har svarat på

När ett problem fått sitt svar skrivs det in som ett eget avsnitt,
`#### LÖSNING`, under problemtexten. Statusmarkören beskriver fortfarande
SYSTEMET och inte dokumentet: en beslutad lösning som ännu inte är byggd
lämnar statusen orörd, och avsnittets rubrik säger då uttryckligen att den
inte är byggd. Problemtexten skrivs aldrig om när lösningen kommer — den är
skälet till att lösningen ser ut som den gör.

## Status

    ✓   löst, och lösningen är mätt eller härledd
    ~   löst i praktiken, men vilar på ett antagande som inte prövats
    ?   öppen — vi vet att problemet finns men inte vad svaret är
    !   känd defekt: systemet gör något vi vet är fel

## Det övergripande målet

> Veta exakt vad varje enskild användare kan och inte kan, ner till minsta
> detalj, och använda den kunskapen till att bygga nästa övning.

Varje problem nedan är en delfråga i det. Måttstocken på en lösning är inte
"fungerar det" utan "**är det sant**" — ett system som påstår sig veta något
det inte vet är sämre än ett som säger att det inte vet.

## Avgränsningen (grundidé, fastslagen 2026-08-23)

Språkinlärning har två delar:

**KUNSKAPEN** — teorin, ordförrådet, allt tekniskt som krävs för att
överhuvudtaget kunna förmedla något på språket.

**ERFARENHETEN** — att förstå naturligt tal, uppfatta nyanser, sätta teorin
i bruk.

> **Programmet gör bara den första delen, och gör den så effektivt som det
> går. Erfarenheten släpps helt.**

Det är ett beslut och inte en brist, och det vilar på två skäl:

1. Erfarenhet går inte att bygga hemifrån framför en skärm — eller åtminstone
   inte effektivt. Den delen sker på språkcaféet, i samtalet, i landet.
2. Nyanser går inte att fånga i det här systemets form. Systemet bygger på
   ett UNIVERSELLT konceptlager delat av sju språk, och nyanser har ingen
   regelbundenhet — mycket ofta finns det inte ens en översättning.

**Avgränsningen är inte kosmetisk. Den gör tre saker:**

- Den ger projektet en **målfunktion**: maximera antalet kunskapsmoment som
  hålls över retentionsmålet, per minut användaren lägger. Utan den är
  "optimalt" ett ord utan innebörd, och systemet går bara att trimma på
  känsla. Med den går det att mäta.
- Den **rättfärdiggör konceptmodellen.** Ett universellt konceptlager över
  sju språk är hållbart precis så länge nyanser är utanför — det är på
  nyanserna en delad ordbok skulle brista. D5:s variantproblem är den
  synliga kanten av det, och det är litet just för att omfånget är litet.
- Den säger vad systemet INTE ska bedömas på. Volym av begriplig input,
  hörförståelse och automatisering ligger utanför, och att optimera systemet
  som om det vore hela metoden vore att optimera fel sak.

Programmet är alltså **precisionslagret bredvid världen**, inte i stället för
den.

## I korthet — vad genomgången kom fram till

*Det här avsnittet är hela dokumentet på en sida, med så få facktermer som
går. Resten är detaljerna.*

**Vad systemet gör.** Det bryter ner ett språk i minsta möjliga
kunskapsbitar — ordet, stammen, ändelsen, genuset — och bygger meningar som
prövar precis de bitar du är på väg att glömma. När du svarar jämförs ditt
svar med facit ord för ord, och systemet försöker avgöra vilken enskild bit
som brast. Det är det som skiljer det från vanliga glosor: Anki vet att du
missade kortet, vi försöker veta VARFÖR.

**Den viktigaste upptäckten.** På flera ställen berättade systemet saker för
minnesmodellen som inte var sanna. Det är värre än att inte mäta alls, för en
falsk mätning ser precis ut som en äkta. Tre exempel:

- Ett kort som du klarade tjugo sekunder efter att svaret stått på skärmen
  bokfördes som om du mindes det efter tre veckor. Stabiliteten hoppade från
  11 till 46 dagar.
- Skrev du rätt ord i fel ordning fick du veta att du inte kunde ordet.
- Nästan hela loggen bestod av frågor som ställdes när svaret redan var
  självklart — 438 av 447 prövningar. Den mätte ingenting. Orsaken var
  MASSAD repetition inom samma dygn, och den är åtgärdad: ett betyg per kort
  och dag. (Ett förslag att dessutom sluta bokföra kort man råkar möta
  prövades och föll — se E6. Att kasta bevis gör inte loggen renare, det gör
  modellen fel.)

Alla tre är nu diagnostiserade, och två har en färdig lösning i dokumentet.

**Arbetsbördan var räknad på ett sätt som var grovt fel.** Systemet antog att
ett kort kostar lika mycket arbete för alltid. Men hela poängen med
spaced repetition är att intervallen växer. Simulerat med modellens egna
formler kostar ett kort **3,7 repetitioner den första månaden och 8,4 det
första året** — den gamla räkningen påstod 19 och 236. Fem till tjugoåtta
gånger för mycket. Det är därför kraven för att låsa upp nästa nivå kändes
orimliga.

**Dagens arbete ska inte ha ett tak.** Det är alla kort som förfallit, precis
som i Anki. Att också kräva ett visst antal övningar var ett krav för mycket
— två regler som kan säga olika saker om när dagen är slut. Arbetsbördan
styrs i stället genom hur mycket nytt som förs in, och det räknas om varje
dag mot hur många minuter du sagt att du vill lägga.

**"Hur svår ska en mening vara" visade sig vara fel fråga.** Svårigheten är
vad kön levererar; man väljer den inte. Det som återstår är två andra saker:
vad sökningen ska maximera, och vad den inte får överskrida. Svaret på det
första kom ur din egen avgränsning — **återkallelser per sekund**. Svaret på
det andra är ett tak på hur mycket som får vackla samtidigt, eftersom fel i
samma mening ofta har samma orsak och då inte är två bevis utan ett.

**Att sätta ett mål gjorde tal mätbara som förut var tyckande.** Så länge
målet var "lära sig språket" fanns ingen nämnare, och då kunde effektivitet
inte vara annat än en åsikt. Med "teorin, per minut" blev fyra av åtta vikter
i poängfunktionen överflödiga och en femte mätbar.

**Vad som är kvar.** Nästan allt som fortfarande är öppet slutar i ett TAL som
bara mätning kan ge — hur mycket som får vackla samtidigt, hur många sekunder
ett ord kostar, vilka vikter som är rätt. Det är inget som mer tänkande kan
lösa. De faller ut ur ett par veckors verklig användning, och fram till dess
står de i dokumentet som **omätta** i stället för förklädda till härledningar.

Det är hela måttstocken: inte "fungerar det" utan "är det sant".

## Två principer som ser ut som motsatser

**1. Kasta aldrig bevis du HAR.**

En lyckad återhämtning är ett bevis oavsett om vi valde att bokföra den. Att
sluta logga kort man råkar möta gör inte loggen renare — det gör modellen
fel. Mätt: ett kort som möts var tredje dag och bokförs varje gång når
stabilitet 1 825 efter två år; samma kort, samma användare, samma faktiska
svar, men bokfört bara när det var förfallet, når 11,7. Se E6.

**2. Hitta aldrig på bevis du INTE har.**

Kan användaren inte hämta fram ordet alls prövades böjningen aldrig — det
finns ingenting att bokföra, och att skicka Good eller Again till formkortet
vore att uppfinna ett utfall. Samma sak när diffen inte kan avgöra vilket
kort som fällde meningen. Se A4, E5, D3.

**Skillnaden är inte om vi VILL mäta utan om en mätning ägde rum.** Det första
felet kastar en verklig observation, det andra hittar på en. Båda gör modellen
fel, åt var sitt håll, och båda ser ut som försiktighet.

## En princip som återkommer

Tre problem i olika delar av dokumentet visade sig vara samma problem:

> **Ett kort som redan har en historik får inte betygsättas i samma pass som
> facit visades för användaren.**

Det gäller D3 (kortet vars skuld inte gick att avgöra kommer tillbaka direkt
efteråt), E5 (formen vars ordkort just fallerade står kvar som förfallen
idag) och F4 (lektionen visar orden strax innan de prövas). Nya kort är
undantagna — deras första möte ÄR introduktionen, och FSRS begynnelse-
stabilitet är byggd för just det. Men ett kort med historik som klaras 30
sekunder efter att svaret stod på skärmen ger FSRS en falsk mätning, och den
är dyr: mätt hoppar stabiliteten 10,96 → 46,28 i stället för till ~11.

---

## A. Vad är kunskap? — kortmodellen

### A1 ✓ — Hur fint ska ett kunskapsmoment skäras?

Ja, ner till atomär nivå: varje mening bryts ner i de minsta enheter som kan
vara fel var för sig. Men "minst" behöver en regel, annars blir det antingen
ett kort per ordform (tyskans 23 494 celler) eller ett kort per ord (och då
går det inte att säga vad som brast).

Regeln är **härledbarhet**: en form får ett eget kort först när den inte går
att räkna ut ur det användaren redan har. Tyskans `sprecht` behöver inget
eget kort — har man stammen `sprech-` och systemkortet "2 pl tar `-t`" följer
formen. `spricht` behöver det, eftersom vokalskiftet inte finns någon
annanstans.

Det ger tre lager på samma ord:

    stam      det som står kvar genom hela paradigmet
    system    ändelsen, delad av alla ord i samma klass
    form      hela cellen som ett kort, när ingen stam går att bryta ut

**Taket på hur fint det går att skära sätts av rättningen.** Ett kort som är
finare än vad diffen kan se går aldrig att skylla rätt — det är den gränsen,
inte pedagogiken, som avgör var uppdelningen slutar.

**Mätt:** en mening ger idag 2,2 (fr) till 5,0 (de) betygsatta kort. Se B2 —
det talet har fallit sedan avdragsreglerna infördes och är inte stabilt.

### A2 ✓ — Vilka sorters kunskap finns?

Sju typer. Tyskan som exempel, med antal kort:

| Typ | Vad kortet frågar | Hänger på | de |
|---|---|---|---|
| `ord` | vad betyder ordet / hur säger man det — en glosa | konceptet | 223 |
| `stam` | vilken oföränderlig del ändelserna sitter på | konceptet | 383 |
| `form` | hela formen, när ingen stam går att bryta ut (`ging`) | en cell | 29 |
| `system` | ändelsen som en hel klass delar ("svag mask. dativ tar `-en`") | en cell, delad av många ord | 37 |
| `rektion` | att ett styrande ord kräver en viss form (`warten auf` + ack.) | det styrande ordet | 6 |
| `egenskap` | en egenskap som inte syns i ordet men styr andra ord — genus | konceptet | 428 |
| `ordföljd` | var ett led ska stå (V2, verbet sist i bisats) | en regel | 6 |

Summa 1 112 kort för tyskan. Genus är 38 % av dem, vilket är rimligt: tyskan
har 159 substantiv och genus är ett fristående faktum per substantiv.

Skillnaden mellan `form` och `system` är den enda som är lätt att blanda
ihop. Ett `system`-kort delas av alla ord i klassen — kan man det för ett
ord kan man det för alla. Ett `form`-kort gäller ett enda ord.

### A3 ! — Ett kort får inte finnas innan det går att möta

Det finns TVÅ sorters onåbarhet, och de har olika svar. Den här posten
blandade ihop dem.

**Nivåspärren.** Ett kort vars konstruktion nivån inte har låst upp ännu.
Bisatsordföljd finns inte i kortleken på nivå 1. Det är löst: `befolka`
körs per kurs och per nivå, och nivån bestämmer vilka kort som skapas.

**Strukturell onåbarhet.** Ett kort som INGEN mening kan innehålla, på någon
nivå, eftersom ingenting i kedjan pekar på det. Ett sådant kort står i kön
som ett mål som aldrig kan nås.

**Mätt 2026-08-23, och det här är defekten:** en menings kort samlas ur tre
källor — `Cellkort` (form/stam/system), ordkorten, och egenskapskorten via
`Uppslag.egenskap`. `ordföljd` och `rektion` har ingen av vägarna. De är
`schemalagt = 1`, de räknas in i `osedda` när upplåsningen beräknas, och de
kan aldrig mötas:

    de   6 ordföljd + 6 rektion  = 12 kort
    fr   3 ordföljd + 2 rektion  =  5 kort
    en   3 ordföljd              =  3 kort
    ja   4 ordföljd              =  4 kort

Nåbarheten MÄTS för de tre kända vägarna (`mät_exponering`), men mätningen
frågar aldrig om ett kort saknar väg helt. Det är samma sak som G5 saknar,
och samma sak som gjorde `Cellkort`-tömningen osynlig i en månad (I3).

**Svaret står under A7**, och det är BÅDA delarna, olika för olika kort:

    rektionskorten          görs nåbara — samma koordinatdiff som genus
                            redan använder, med kasus i stället för genus
    lågfrekvent ordföljd    görs nåbar — regelloggen plus omkastnings-
                            detektionen
    högfrekvent ordföljd    tas ur schemat (`schemalagt = 0`), eftersom E6
                            redan säger att det som möts i varje mening inte
                            går att schemalägga

Efter det finns inget schemalagt kort kvar utan väg, och G5:s invariant —
"varje schemalagt kort ska vara nåbart via minst en väg" — kan skrivas som
ett villkor som faktiskt håller i stället för ett som skulle falla direkt.

#### MÄTT OM 2026-08-24 — ingenting har ändrats, men konsekvensen har

Metoden är rakare än exponeringsmätningen: sampla några hundra meningar med
HELA ordförrådet öppet på nivå 21, samla unionen av kort de rör, och jämför
mot de schemalagda. Det som aldrig rörs saknar väg.

    de   327 meningar, 514 kort rörda   6 ordföljd + 6 rektion aldrig rörda
    fr   353 meningar, 503 kort rörda   3 ordföljd + 2 rektion
    en   331 meningar, 325 kort rörda   3 ordföljd
    ja   320 meningar, 318 kort rörda   4 ordföljd

Exakt de tal som stod här 2026-08-23.

**REKTIONEN ÄR LÖST 2026-08-25** — A7 punkt 3 byggd, `Uppslag.rektion` gör
korten nåbara. Kvar av rektionen är ett enda tyskt kort, och det är en rad i
språkdatabasen och inte ett kodfel (se A7). Ordföljden står orörd:
omkastningsdetektionen finns, men den kopplar inte ett fel till ett
ORDFÖLJDSKORT, så de korten är lika onåbara som förut.

    de   6 ordföljd + 1 rektion
    fr   3 ordföljd
    en   3 ordföljd
    ja   4 ordföljd

**Konsekvensen är däremot ny, och den är värre.** Korten ligger i kön som
osedda och äter av dagens tilldelning:

    ja   4 av dagens 25 nya kort kan aldrig besvaras
    fr   3 av 25   (var 5 innan rektionen kopplades in)
    en   3 av 25

Och sedan nödutgången rättades (B8) avslutar de dagen i förtid i stället för
att mala: när det nåbara är gjort täcker ingen mening dem, `täckta == 0`
faller ut, och passet säger "klart för idag" med kort kvar i tilldelningen.
Före rättelsen syntes de som rundgång; nu syns de som en kortare dag. Ingen
av visningarna är fel, men båda döljer att korten inte borde ha stått i kön.

**Det finns ett halvsteg som inte kräver A7:** `schemalagt = 0` på dem tills
vägen finns. Det är precis vad E6 föreskriver för det som inte går att pröva
i tid, och A3 föreslår det redan för högfrekvent ordföljd — skillnaden är att
det då skulle gälla ALL ordföljd och rektion, alltså också de lågfrekventa som
A7 var tänkt att göra nåbara. Det är ett beslut om vad kortleken PÅSTÅR sig
lära ut, inte en bugg att rätta, och står därför här och inte i koden.

### A4 ✓ — Ord och böjning är olika sorters kunskap, och de är ordnade

Två påståenden, och det andra är det viktiga.

**De är olika frågor.** Ett `ord`-kort frågar vad ordet betyder — en glosa.
Ett `stam`/`form`/`system`-kort frågar hur det böjs. Att kunna det ena säger
ingenting om det andra.

**Böjning förutsätter ordet.** Kan man inte hämta fram ordet alls prövades
böjningen aldrig, och den ska inte straffas för det. Ett enda ordglapp skulle
annars fälla trettio formkort på en gång. Det är därför `_skyddade` tar bort
form- och stamkorten ur betygsättningen när deras ordkort fallerar.

**"ALLS" ÄR ORDET SOM BÄR REGELN, och koden prövade något annat.** `_skyll`
frågade om det skrivna var exakt en känd cellform — och en felböjning är per
definition ingen känd cellform. `existerer` för `existez` blev därför "ingen
form av exister, alltså fel ord": ordkortet fick Again, och skyddet tog bort
stam- och systemkorten. Användaren hade skrivit stammen och missat ändelsen,
alltså visat ordkunskapen och brustit i böjningen, och fick motsatt besked.
Skyddet gällde precis de fall det inte var till för.

**Rättat: stammen i försöket räknas som bevis att ordet hämtades fram.** Bär
försöket konceptets stam faller skulden på systemkortet — ändelsen — och
böjningsfelet blir bedömt. Bär det inte stammen står den gamla slutsatsen kvar.

Prövningen är inte en naken prefixregel utan en BÄSTA FÖRKLARING: den längsta
matchande stammen avgör vilket ord försöket är. Skälet är mätt — stammarna är
korta, och `a` (avoir) är prefix till halva franskan. Var femte fransk form
(21 %) prefixas av någon främmande stam; låter man den längsta förklara faller
det till 3 % (fr), 6 % (de) och 0 % (en). `apprend` mot väntat `as` blir därmed
`apprendre` och inte `avoir` felböjt.

Provet är `ordbok/verktyg/attributionsprov.py`: sju fall med känd skada, och
två sabotage — det gamla villkoret och den nakna prefixregeln — som båda
fäller det.

Ordningsrelationen går bara åt ett håll: man kan kunna ordet utan att kunna
böjningen, men inte tvärtom. Se E5 för vad som händer med det skyddade
kortet efteråt — där finns det som inte är löst.

### A5 ✓ — Egenskaper som syns på ANDRA ord

Genus står inte i substantivet. `Mädchen` avslöjar ingenting; det är `das`
framför som bär informationen. Kunskapen "Mädchen är neutrum" är alltså ett
faktum om substantivet som bara går att pröva genom en annan ordform.

**Så här avgörs det automatiskt.** Cellnamnen är koordinater: `n_nom` är
neutrum + nominativ, `f_nom` är femininum + nominativ. När användaren skriver
en form som är fel för cellen frågar `_genusgivaren` vilka celler formen
HADE varit rätt för, och jämför koordinaterna. Skiljer de sig i exakt en
koordinat, och är den koordinaten genus, är felet genuskunskapen och inte
artikelparadigmet. Sedan letas vilket ord i meningen som lämnade det genuset
— det står i `egenskaper`, renderarens egen logg över vilka lexikala
egenskaper som valde cellerna — och det ordets `egenskap`-kort fälls.

Utan det steget skylldes `die Kind` alltid på artikelns formkort, alltså på
det kort som möts i nästan varje mening och därför nästan säkert sitter,
medan genuset för just `Kind` gick fritt. Fel kort i praktiskt taget varje
verkligt fall.

**Gränsen:** steget kräver att exakt EN cell matchar (`len(träffande) == 1`).
Skrev användaren en form som passar både ett annat genus och ett annat kasus
faller den igenom till paradigmkortet. Det är ärligt — men det betyder att
genusattributionen är bäst i språk med tydliga genusformer och sämst där
formerna sammanfaller.

**Mätt:** 0 av 428 tyska genuskort är sedda. Det är inte en defekt utan brist
på data: tyskan har bara tio meningar bakom sig och inget substantiv har
ännu dykt upp.

### A6 ? — Vad är ett kort som spänner över flera ord?

Partikelverb (`hört zu`, `lies down`) och fraslexem (`älterer Bruder`) är ett
kunskapsmoment men flera ord, ibland inte ens intill varandra.

**Rättningen är löst** (se D4): en känd flerordig form limmas ihop till EN
token före diffen, även när partikeln lossnat och står i andra änden.

**Modellen är inte löst.** Är `zuhören` ett kunskapsmoment eller tre — verbet,
partikeln, och regeln att partikeln lossnar i huvudsats? Förslaget att ha
BÅDE ett kort för helheten och kort för de enskilda orden är rimligt och har
en kostnad som måste räknas: attributionen blir svårare (vilket av de tre
brast?) och kortleken växer för just de ord som möts oftast.

Fraslexem är ett annat fall igen: `älterer Bruder` är ett koncept i ordboken
men två ord som var för sig böjs, och adjektivet böjs efter en deklination
som beror på artikeln framför. Renderaren vägrar idag den kombinationen
(se C7).

**Öppet:** ett kort eller flera; hur skulden delas när frasen blir fel; och
om separationsregeln är ett `ordföljd`-kort — vilket idag betyder att den
inte kan mötas alls (A3).

### A7 ? — Hur representeras kunskap som inte är lexikal?

Ordföljd, rektion och satsstruktur är regler, inte ord. De har kort. Frågan
är om de går att pröva och att skylla på.

**Mätt 2026-08-23, och svaret är att systemet gör fel.** Ta facit
`jag äter maten` och svaret `äter jag maten`. Den ordvisa diffen ger:

    insert   facit=[]        svar=['äter']
    delete   facit=['äter']  svar=[]

`insert` ger ingen anmärkning alls — loopen går över facits positioner och
det intervallet är tomt. `delete` ger en anmärkning med `väntat="äter"` och
`skrev=""`. `_skyll` frågar då vilken cell som renderar till tomma strängen,
hittar ingen, och tar grenen **"ingen form av konceptet, alltså fel ord"** —
alltså verbets `ord`-kort får Again. Och eftersom ett fallerat ordkort
skyddar sina former (A4) tas verbets stam- och formkort ur betygsättningen.

Användaren kunde ordet, skrev det korrekt, och får veta att hen inte kan
det. Ordföljdskortet, som är det enda som faktiskt brast, rörs inte — det
kan inte röras, eftersom det inte är nåbart (A3).

**Det här går att lösa automatiskt.** En omkastning är synlig i diffen: samma
token finns på båda sidor men på olika positioner. Det svåra fallet är när
ett ord både flyttats OCH böjts fel — då är det inte längre samma token, och
då krävs antingen självrättning eller ett svagare mått.

#### LÖSNING — del 1 BYGGD 2026-08-23, del 2 och 3 inte

Tre delar. Den första stoppade lögnen i loggen och **är byggd**; de två andra
avgör hur kunskapen ska representeras och löser samtidigt halva A3.

Statusen gick därmed från `!` till `?`: systemet påstår inte längre något
osant, men frågan i rubriken — hur icke-lexikal kunskap ska REPRESENTERAS —
är fortfarande obesvarad.

---

**1. OMKASTNINGAR SKA KÄNNAS IGEN — och det går**

Ett flyttat ord är synligt i diffen: **samma token finns på båda sidor, men
i olika opkoder.** Regeln är att samla alla tokens som tas bort ur facit
(`delete` och `replace`) och alla som lagts till i svaret (`insert` och
`replace`), och skära mängderna. Det som finns i båda är FLYTTAT, inte fel.

Prövat på sju fall:

    facit "jag äter maten"                bort          till          flyttade
    ─────────────────────────────────────────────────────────────────────────
    "äter jag maten"                      äter          äter          äter
    "maten äter jag"                      äter,maten    maten,äter    båda
    "jag äter mat"       (ren formfel)    maten         mat           —
    "äter jag mat"       (flyttat OCH     äter,maten    äter,mat      äter
                          fel form)
    "jag maten"          (ord saknas)     äter          —             —
    "jag äter maten idag" (extra ord)     —             idag          —

Det svåraste fallet faller ut rätt av sig självt: är ordet både flyttat och
felböjt känns flytten igen medan formfelet fortfarande attribueras som
vanligt. Regeln kräver inga trösklar och inga vikter.

**Vad som händer med ett flyttat ord:** ordkortet går fri. Det är hela
poängen — användaren kunde ordet och skrev det korrekt. Skulden går i stället
till ordföljden, enligt punkt 2.

**BYGGT.** `Rättare._flyttade` plus ett andra diffpass i `_ordvis`, en
`ordföljd`-flagga på `Anmärkning`, och ett undantag i `rätta` som låter
sådana anmärkningar passera utan att fälla något kort. Verifierat på en
riktig fransk mening (`Une nourriture coûte.`):

    svar                        före                     efter
    ─────────────────────────────────────────────────────────────────────
    nourriture Une coûte.       ord:mat_mat FÄLLD        inget kort fällt
    Une nourriture coûtent.     system:pres_3sg          oförändrat
    nourriture Une coûtent.     ord:eko_v_kosta FÄLLD    system:pres_3sg

Den sista raden är andra passets förtjänst: ett flyttat ord rubbar diffens
uppriktning för sina grannar, så det felböjda verbet hamnade i en `delete`
utan motpart och skylldes på ORDET i stället för på ändelsen. Plockas de
flyttade orden bort från båda sidor blir resten en ren diff igen.

**Provet:** `ordbok/verktyg/omkastningsprov.py`, tolv kontroller. Den
viktigaste är formulerad på hela meningen och inte per ord — *är svaret en
ren omkastning får inget kort fällas alls* — eftersom "ett rätt skrivet ord
får aldrig skyllas" vore för starkt: i `hunden ser hunden` mot
`hunden ser katten` är den andra `hunden` ett äkta ordfel. Utan
detektionen faller provet med åtta fel.

**Känd begränsning:** vid en helvändning förankrar difflib på det första lika
långa blocket, så de ord som NAMNGES som flyttade behöver inte vara de man
själv skulle valt. Det är kosmetiskt och aldrig en felmätning — varje ord är
antingen matchat eller flaggat som flyttat, så inget kort fälls.

**En andra lucka i samma kodväg, som hittades på vägen.** `_ordvis` loopar
över FACITS positioner: `for n, pos in enumerate(range(i1, i2))`. För en
`insert` är `i1 == i2`, alltså är intervallet tomt och **ingen anmärkning
skapas alls.** Ett ord användaren lagt till som inte ska finnas där är
osynligt för rättningen. Det är inte lika farligt som att skylla fel — under
D3:s princip är tystnad försvarbart — men extra ord är ofta just
strukturfel (en preposition för mycket, en dubblerad artikel), så det hör
hemma här.

---

**2. ORDFÖLJDEN — BYGGD 2026-08-25**

Ordföljd ÄR teori och ligger därmed innanför avgränsningen. Men alla
ordföljdsregler är inte lika, och systemets egen regel skiljer dem åt.

E6 säger att ett kort som möts oftare än tröskeln inte går att schemalägga —
det finns ingen tidpunkt då det INTE prövas. Tyskans V2 finns i praktiskt
taget varje huvudsats. Alltså:

    HÖGFREKVENTA regler    V2, rak SVO. Oschemalägbara per E6. De ska MÄTAS
                           som felfrekvens och styra genereringen — bygg fler
                           meningar med den konstruktion användaren missar —
                           inte ligga som FSRS-kort.

    LÅGFREKVENTA regler    bisatsordföljd, inversion i frågor. De dyker upp
                           först när nivån låser upp dem och har därför en
                           exponering som går att schemalägga. De KAN vara
                           kort, nu när punkt 1 gör dem attribuerbara.

Uppdelningen är inget påhitt — den följer ur en regel vi redan har, och
mätningen är den `mät_exponering` redan gör. Vad som saknas är att
renderarna LOGGAR vilken regel de tillämpade, på samma sätt som de redan
loggar uppslagna former (`Uppslag.form`) och lexikala egenskaper
(`Uppslag.egenskap`). Det är samma instrumenteringsmönster för tredje gången.

**Skulden när flera regler är i spel.** Är bara en ordföljdsregel schemalagd
i meningen är svaret entydigt. Är flera det vet vi inte vilken som brast —
och då säger vi ingenting, precis som D1 gör, och kortet skjuts upp enligt
D3. Att gissa vore samma fel som pinne 7.

**BYGGT, i tre led.**

*Loggen.* `Uppslag.ordföljd(regel)` — fjärde instrumenteringen, och den
enda utan värde att lämna tillbaka: här ÄR anropet hela informationen.
Formen står i `Former`, genuset på lexemet, rektionen i `MönsterKrav` — men
att tyskans finita verb står på plats två är ingenting annat än renderarens
egen struktur. Sexton anrop lades in i fem renderare (de 6, sv 4, ja 4,
en 3, romansk 3–4).

Regeln loggas där den TILLÄMPAS, inte där den vore möjlig. `satsklammer`
loggas bara när slutfältet har något att bära, `dativ_före_ackusativ` bara
när båda objekten finns, `biff` bara när det finns ett satsadverbial att
flytta. En regel som loggas när den inte gör något mäter fel.

*Uppdelningen skriver sig själv.* Måttet gick in i `mät_exponering`, och
`sätt_schemalagt` gjorde resten. Ingen lista över vilka regler som är
högfrekventa behövde skrivas — det var hela poängen med att E6 redan avgör:

    de  v2            1,000  →  ur schemat
    de  satsklammer   0,375  →  ur schemat
    en  svo           1,000  →  ur schemat
    fr  svo           1,000  →  ur schemat
    ja  sov           1,000  →  ur schemat
        alla övriga   0,000  →  kvar i schemat

*Skulden.* `Rättare._ordföljdskortet` tar de regler som både TILLÄMPADES och
är SCHEMALAGDA. Att filtrera på schemalagda är inte en detalj: varje mening
tillämpar sin grundordföljd, så utan filtret vore svaret nästan alltid
"flera regler, alltså tystnad" och den lågfrekventa regel som faktiskt brast
kunde aldrig fällas. Mätt i drift:

    facit  'Hat ein Bruder den grauen Saft gemischt?'
    svar   'ein Hat Bruder den grauen Saft gemischt'
    tillämpade: satsklammer, v1_fråga   schemalagda: v1_fråga
    → FÄLLD: ordföljd v1_fråga

**Nåbarheten efter bygget**, samma mätning som A3 använder:

    de   6 av 6 ordföljdskort nåbara     en   3 av 3
    fr   3 av 3                          ja   4 av 4

**Japanskan får loggen men inte skulden**, och det är D7 och inte en lucka.
Japanskan skrivs utan mellanslag, så det finns ingen ordvis diff — och utan
diff finns ingen omkastning att upptäcka. Korten går att MÖTA, inte att
skylla på.

**Provet:** `ordbok/verktyg/ordföljdsprov.py`, tre invarianter med tre
sabotage. Den viktigaste kontrollen har två lägen: en mening där FLER regler
tillämpats än som är schemalagda (då ska just den schemalagda fällas) och en
med två schemalagda (då ska svaret vara tystnad). Utan det första läget kan
ett prov utan schemafilter se identiskt ut, och utan det andra kan ett prov
utan entydighetskrav göra det.

**En regression hittades på vägen, och den var min egen.** `_duglig`
konjungerade "noll okända ord" med "ingen upprepning". Vid kallstart är det
första alltid falskt — inget ord är sett — så upprepningsspärren var DÖD och
varje kandidat föll till reservtiern, som saknade spärr. Mätt: japanskan gav
samma mening nio gånger i rad med minnet fyllt av tre kopior av den.
Villkoren hör till olika tiers och är nu tre: `bäst` (klarar allt), `reserv`
(okända ord men ingen upprepning), `nödfall` (upprepning). Efter delningen
varierar japanskan igen.

---

**3. REKTION — BYGGD 2026-08-25**

`warten auf` + ackusativ är samma FORM av problem som genus, och genus är
löst (A5, D2). Renderaren slår upp att prepositionen styr ackusativ och
begär därför cellen med den kasuskomponenten. Skriver användaren dativ är
formen inte påhittad — den är korrekt för en annan rektion.

`_genusbytet` gör redan koordinatdiffen: den byter ut GENUS-komponenten i
cellnamnet mot varje annat genus språket har och ser om någon av de cellerna
är en användaren faktiskt skrev. **Samma kod med KASUS som koordinat svarar
på rektionsfrågan.** Och `_genusgivaren` behöver bara en motsvarande logg
över vilket styrande ord som valde kasus — samma hook som `Uppslag.egenskap`,
med rektion i stället för egenskap.

Generaliseringen är alltså `_givaren(koordinat)` i stället för
`_genusgivaren`, och entydighetskravet står kvar: passar exakt en kandidat
är svaret säkert, passar flera säger vi ingenting.

**BYGGT, i två halvor som svarar på var sin fråga.**

*Nåbarheten.* `Uppslag.rektion(koncept, slot, namn, värde)` — samma tomma
form som `egenskap`, samma skäl: den returnerar sitt argument och finns för
att gå att logga. Skillnaden är vem kunskapen hör till. Genus är ett faktum
om SUBSTANTIVET; rektion är ett faktum om VERBET som styr frasen. Nyckeln är
därför verbets koncept plus slotten. `de.kasus_för` och
`romansk.preposition_för` returnerar numera genom den, och generatorn kopplar
loggen till korten via `(koncept, cell, egenskap)`.

Mätt före och efter, 2 500 samplade meningar med hela ordförrådet öppet:

    fr   2 av 2 rektionskort onåbara  →  0
    de   6 av 6                       →  1

*Attributionen.* `_koordinatbytet` är `_genusbytet` med koordinaten som
argument, och `_rektionsgivaren` är `_genusgivaren` med KASUS i stället för
genus. `KASUSTOKEN` för tyskan är `{Nom: nom, Ack: akk, Dat: dat, Gen: gen}`
— samma tal som renderaren använder. Verifierat på riktiga meningar:

    Hatten seine Ärzte dir geholfen?   → dich   rektion: helfen styr dativ
    Ein Bauer dankt ihm.               → ihn    rektion: danken styr dativ
    …trotz der Stifte dem Schriftsteller helfen?  → den   rektion: helfen
    Halfen Mütter … in dem Auto …      → den    FORM (artikeln)

Den sista är rätt svar och inte ett missat fall: `in dem Auto` styrs av
PREPOSITIONEN, inte av verbet, och där finns inget rektionskort — alltså är
det artikelparadigmet som brast.

**Romanska språk får bara nåbarheten, inte attributionen.** Rektionen
realiseras där med en preposition och inte med kasus, så felet är ett ORD i
diffen och inte en koordinat i en cell. Koordinatdiffen har ingenting att
byta. Det är en annan mekanism och den är inte byggd.

**Provet:** fyra fall i `ordbok/verktyg/attributionsprov.py` (elva totalt) med
två egna sabotage — utan rektionssteget, och med rektionen utan
entydighetskrav. Det andra är samma fel som pinne 7 i D1: att gissa när datan
inte räcker. Med två dativstyrande verb i meningen ska svaret vara tystnad.

**KVAR: ett tyskt rektionskort som fortfarande är onåbart, och det är ett
DATAFEL.** `rektion:de:kom_fråga::Verb::objekt::kasus`. Det universella
mönstret för `fragen` har slotarna `subjekt`, `io` och `kommunikat` — inget
`objekt` — medan det tyskspecifika mönstret ändå deklarerar kasus för
`objekt`. Kravet gäller alltså en slot verbet inte har, och kortet som
genererades ur det kan inte nås av någon mening.

Tyskan har dubbel ackusativ vid `fragen` (`ich frage dich etwas`), så
avsikten var rimligen `kommunikat` och inte `objekt` — men `kommunikat`
renderas inte som en kasusbärande nominalfras idag, så en omdöpning skulle
inte räcka. Det är en rad i språkdatabasen plus ett renderarbeslut, inte en
bugg i attributionen, och står därför här.

---

#### FÖRSLAG SOM FÖLL (2026-08-26) — ändelsekort som målord

Målstyrningen är konceptbaserad: `föreslå` bygger sin målordslista ur
`k["koncept"] for k in kö if k["koncept"]`. Två korttyper har `koncept =
NULL` — `system` (ändelsen delas av en hel böjningsklass) och `ordföljd`
(regeln hör till språket) — och kan därför aldrig bli målord. På en färsk
franskdag var det hälften av de nya korten.

Det såg ut som en strukturell lucka, och en lösning byggdes: `Cellkort` vet
redan vilka ord som rör en viss ändelse, så ett ändelsekort i klass K1 kan
styras genom att bygga kring ett K1-verb användaren kan.

**Den mättes och gav noll.** Fyra frön per kurs, före och efter:

    franska nivå 1    avskrivna 0 → 0    meningar 8,00 → 8,00
    tyska nivå 4      avskrivna 0 → 0    meningar 4,00 → 4,00
    engelska nivå 1   avskrivna 0 → 0    meningar 1,00 → 1,00

Skälet är att poängfunktionen redan hittar dem: ett ändelsekort i kön räknas
som TÄCKT när en mening råkar röra det, och `täckning` väger tio. Målordet
styr vad sökningen bygger KRING; poängen avgör vad som vinner, och för kort
som möts ofta räcker det senare.

**Den togs bort igen**, tillsammans med en generaliserad reservsökning som
byggdes samtidigt och som mättes till att aldrig lösa ut (8 meningar, 8 anrop
till `_sök`, noll extra). Båda var lösningar på ett symptom vars verkliga
orsak låg någon annanstans — se B8: passets och generatorns köer var
disjunkta.

*Gränsen står alltså kvar som en känd gräns och inte som en defekt.* Den
skulle börja bita om kön blev lång nog att poängfunktionen inte hinner se
varje ändelsekort, och då finns mätningen ovan att göra om.

**VAD DET GER A3.** A3:s defekt är att `ordföljd`- och `rektion`-korten inte
kan mötas av någon mening. Punkt 2 och 3 gör dem nåbara — rektionskorten via
rektionsloggen, de lågfrekventa ordföljdskorten via regelloggen. De
högfrekventa ordföljdskorten ska då inte göras nåbara utan **tas ur
schemat** (`schemalagt = 0`), vilket är precis vad E6 redan gör med
allestädes närvarande kort. Efter det finns inget schemalagt kort kvar utan
väg, och G5:s invariant kan skrivas som ett villkor som faktiskt håller.

**Statusen står kvar som `!` tills koden ändrats.**

---

## B. Vad ska övas just nu? — urvalet

### B1 ✓ — Vilka kort är förfallna?

Överlämnat till FSRS 6.3.2. En egen minnesmodell vore månader av tyst
felaktighet.

**Matematiken.** Varje kort bär tre tal:

- **S, stabilitet** — antalet dygn tills sannolikheten att minnas fallit till
  målnivån. Ett kort med S = 10,96 förfaller om 11 dygn.
- **D, svårighet** — 1 till 10. Går in i tillväxten som (11 − D): ett svårt
  kort växer långsammare av samma repetition.
- **R, retention** — modellens skattning av att du minns kortet just nu.
  R = (1 + FAKTOR · t / S)^(−0,1542), där t är dygn sedan senaste
  repetitionen.

Förfallodagen är den dag R når `desired_retention` = 0,90. (Verifierat: R är
0,900 på förfallodagen för S = 1, 3, 10, 40 och 200 — förfallodagen och
retentionsmålet är samma påstående.)

Vid RÄTT växer stabiliteten:

    S_ny = S · (1 + e^w8 · (11 − D) · S^(−w9) · (e^(w10·(1−R)) − 1) · straff)

Den avgörande faktorn är `(e^(w10·(1−R)) − 1)`. Den går mot NOLL när R går
mot 1. **Ett kort du redan kan säkert växer nästan ingenting av att prövas.**
Den enda meningen förklarar B6, E2, E4 och E6 på en gång.

Vid FEL rasar den:

    S_ny = min( w11 · D^(−w12) · ((S+1)^w13 − 1) · e^(w14·(1−R)) , S / e^(w17·w18) )

Mätt på ett moget kort (S = 10,96, D = 2,11, prövat på förfallodagen):
S → 1,54, D → 7,39, nästa repetition om 2 dygn. Ett fel kostar alltså ungefär
86 % av stabiliteten — vilket är skälet till att felattribution (D1) är dyrt
och inte bara slarvigt.

Kön är `WHERE schemalagt = 1 AND förfaller <= nu ORDER BY förfaller`, alltså
det längst försenade först.

### B2 ✓ — Hur mycket nytt tål användaren?

Ett nytt kort kostar inte en repetition utan en avtagande STRÖM av dem: dag
2, dag 13, dag 54, dag 199 … Frågan är hur många sådana strömmar ett dygn
bär. Efter B4 och B5 är detta dessutom **den enda ratten för arbetsbörda som
finns kvar** — dagen kan inte kortas av, bara matas mindre.

**Räkningen idag, och den är fel.**

    belastning        Σ 1/I(S) över SEDDA kort      = repetitioner per dygn just nu
    per_kort          belastning / antal sedda      = vad ETT kort kostar per dygn
    rum               (C − belastning) / per_kort   = hur många kort till som ryms

`per_kort` behandlar kortets NUVARANDE takt som om den vore evig. Mätt
2026-08-23 är den 0,647 för tyskan, alltså påståendet "varje kort ses var
1,5:e dygn för alltid". Men intervallet växer vid varje lyckad repetition —
det är hela poängen med FSRS.

**Simulerat, med FSRS egna formler och inga antaganden** (3 000 kort införs,
repeteras på förfallodagen, fel dras med sannolikhet 1−R, alltså modellens
egen förutsägelse):

    kumulativa repetitioner per kort, dr = 0,90

        7 d   14 d   30 d   90 d   180 d   365 d   730 d
       2,21   3,24   3,68   5,41    6,21    8,40   10,99

Ett kort kostar alltså **3,7 repetitioner på en månad och 8,4 på ett år** —
inte 19 och 236, vilket är vad `per_kort` påstår. Modellen överskattar med
**5,3× på 30 dagar och 28× på ett år.**

**Följd 1: ett stadigt inflöde stannar aldrig.** För man in k nya kort varje
dag blir den dagliga arbetsmängden vid dag D exakt `k × kumulativa(D)`:

    k nya/dag |  dag 30   dag 90  dag 180  dag 365  dag 730
            2 |       7       11       12       17       22
            5 |      18       27       31       42       55
           10 |      37       54       62       84      110
           20 |      74      108      124      168      220

Den växer logaritmiskt och planar aldrig ut. **"Nya kort per dag" har därför
inget fast svar** — talet måste räknas om, och det måste sjunka när leken
mognar om arbetsdagen ska hållas konstant.

**Följd 2: retentionsmålet är också arbetsbörderatten.** Vid k = 5:

    dr      dag 30   dag 90  dag 365  dag 730
    0,85        13       21       35       42
    0,90        18       27       42       55
    0,95        25       40       65       84

0,95 kostar nästan dubbelt så mycket arbete som 0,85 för samma antal ord.
Det är samma ratt C2 landade i är den ärliga svårighetsratten, och det är
konsekvent: hårdare krav på minnet = mer arbete.

---

#### LÖSNING (beslutad 2026-08-23 — inte byggd)

**Regleringen ska vara en STYRNING, inte en prognos.** Det är skillnaden
mellan robust och gissning. En prognos över ett år ärver alla fel den gör; en
styrning som räknas om varje dag korrigerar dem.

    1.  I MORGON ÄR EXAKT KÄNT. Varje sett kort har ett `förfaller`-datum.
        Att räkna hur många som faller på varje kommande dag är en SQL-fråga,
        ingen modell.

    2.  SVANSEN SIMULERAS. Kort som prövas i morgon schemaläggs om, och vart
        de hamnar beror på betyget. Sannolikheten för fel är 1−R, som FSRS
        redan ger. Över en kort horisont är det en andrahandskorrigering.

    3.  KOSTNADEN MÄTS I TID. Sekunder per repetition ur användarens egen
        logg (B4, E7) — det är omräkningen från kort till minuter.

    4.  BESLUTET FATTAS OM VARJE DAG. Antalet nya kort idag väljs så att den
        förutsagda arbetsmängden över horisonten ligger på användarens mål.
        Fel i steg 2 rättas i morgon i stället för att ackumuleras.

**Det här svarar också på vad som händer när användaren slarvar.** Uteblir
ett pass ligger korten kvar OCH blir mer försenade, så både antalet och
svårigheten stiger — steg 1 ser det direkt, och steg 4 skär ned inflödet
samma dag. Ingen särskild regel behövs; det faller ut ur att i morgon räknas
om från de faktiska förfallodatumen.

**Horisonten i steg 4 är det enda som måste bestämmas**, och det ska göras
med öppna ögon. Ett nytt kort gör 2,2 av sina första 3,7 repetitioner inom
sju dagar; marginalkostnaden av dagens beslut ligger alltså nästan helt inom
en till två veckor. En kort horisont gör styrningen snabb men blind för att
inflödet bygger upp sig långsiktigt (följd 1). En lång horisont ser
uppbyggnaden men reagerar trögt.

**BYGGT 2026-08-24** i `kort/arbetsborda.py`. Tre saker föll ut annorlunda än
posten förutsåg, och alla tre hittades genom att räkna.

**HORISONTEN ÄR TVÅ HORISONTER, och att slå ihop dem var fel med en faktor
fem.** De svarar på olika frågor:

    PROGNOSFÖNSTER   14 dygn. Hur långt fram den BEFINTLIGA kortleken
                     simuleras. En ren tillförlitlighetsgräns — bortom ett par
                     veckor beror varje kort på utfall som ännu inte skett.

    KOSTNADSHORISONT 365 dygn. Hur länge ETT nytt korts kostnad räknas. Och
                     den är HÄRLEDD, inte vald.

Härledningen: för man in k kort per dygn i evighet blir dygnets arbete
`k × kum(D)` vid dag D. En styrning som dividerar med `kum(H)` sätter k så att
målet håller vid dag H, och överskjuter med `kum(D)/kum(H)` längre fram:

    H =   7 d   kum 2,21   överskjuter 3,8x vid ett år
    H =  14 d   kum 3,24   överskjuter 2,6x
    H =  90 d   kum 5,41   överskjuter 1,6x
    H = 365 d   kum 8,40   överskjuter 1,0x

**Frågan "hur lång ska horisonten vara" har alltså ett exakt svar så snart man
sagt över vilken tidsrymd användarens mål ska HÅLLA.** Ska tjugo minuter om
dagen betyda tjugo minuter om ett år, är horisonten ett år. Det som såg ut som
en öppen designfråga var en räknefråga.

Kontroll åt andra hållet: 20 repetitioner/dygn är 7 300 om året, och ett kort
kostar 8,40 — alltså 869 kort om året, 2,4 om dagen. Den ärliga takten är
långsammare än den känns.

**TVÅ VILLKOR BEHÖVS, INTE ETT.** Långtidsvillkoret ensamt släppte in 73 nya
kort samma dag ovanpå 34 förfallna, eftersom kurvans första dygn är en etta —
introduktionen kostar en repetition direkt. Därför också ett dagstak,
`prognos[0] + k × kurva[0] ≤ mål`. Senare dygn får vara tunga utan att
blockera; blir de det syns det i den dagens egen beräkning, vilket är hela
skillnaden mellan en styrning och en prognos.

**VÄXELKURSEN FÅR INTE ANVÄNDAS FÖR TIDIGT.** Mätt: med sex tidtagna meningar
gav skattningen 0,16 sekunder per repetition, vilket översatte tjugo minuter
till 7 300 repetitioner om dagen och 813 nya kort. `MINSTA_TIDTAGNA = 10`
hindrar det. Talet är ett val och står som omätt; provet är hur mycket
skattningen rör sig mellan tio och femtio mätningar.

**OMARBETAT 2026-08-24, samma dag: DAGENS TAK ÄR TID, INTE ETT ANTAL.**

Den första byggda formen hade en kallstartskonstant — först 40 kort, sedan
10 — och båda var samma sorts fel: ett fast tal som stod in för en mätning.
Mätt i praktiken tog tio ord några enstaka minuter av en tiominuterssättning.
Talet kunde inte veta något om användaren.

Att räkna om minuter till kort kräver en växelkurs som inte finns dag ett.
Men att mäta hur lång tid dagen HITTILLS tagit kräver ingen växelkurs alls —
och den mätningen finns från första svaret (`tid_idag`). Samma rörelse som B5
gjorde för meningar: sluta räkna enheter, mät arbetet.

**Spärren är INKREMENTELL och räknar aldrig om tid till kort.** Frestelsen är
`tid_kvar / sekunder_per_repetition`, och den prövades och förkastades: en
absurt liten uppmätt takt tar bort spärren helt. Mätt i ett prov som svarade
på 20 ms per glosa blev taket 28 000 kort. Den robusta formen frågar bara
"finns det tid kvar" — ja eller nej — och inflödet sker i portioner med
mätning emellan. Felet kan aldrig bli större än en portion, och ingen skakig
växelkurs kan förstöra något.

**Självstabil på kort sikt, vilket är skälet att den får styra.** Ett
nyinfört kort har `kurva[2] ≈ 1,0` — varje infört kort kommer tillbaka en
gång två dygn senare. Fylls dagen till målet blir dag två exakt målet:

    10 min à  6 s/kort -> 100 kort dag 1 -> dag 2: 100 förfallna = 10 min
    10 min à 15 s/kort ->  40 kort dag 1 -> dag 2:  40 förfallna = 10 min

**Antalet är OBESTÄMT när bara tidsspärren binder**, och gränssnittet säger
det: dag ett vet ingen hur många kort tio minuter räcker till, eftersom det
beror på hur fort användaren arbetar. Hemskärmen visar då minuter i stället
för ett påhittat tal.

**Kostnaden mäts numera också per läge** (`kostnad_per_läge`) — mening mot
glosa. Frågan "går en mening snabbare per kort än en glosa?" har därmed ett
svar. Talet används INTE av styrningen: där är det poolade medelvärdet rätt
statistik, eftersom användarens minuter köper repetitioner i den blandning
som faktiskt uppstår. Att väga med en framtida blandning vi inte känner vore
att gissa.

**PROV BYGGT 2026-08-24: `ordbok/verktyg/arbetsbördeprov.py`.** Åtta
kontroller över B2:s och F1:s aritmetik, var och en med ett sabotage som
återinför det fel den finns för. Kostnadskurvan, tidsspärren,
långsiktsvillkoret och byggbarhetströskeln hade inget nät alls — trots att de
avgör hur mycket användaren lär sig per dag, och trots att en tyst regression
där är osynlig: talen ser rimliga ut oavsett vad de är.

**Och provet hittade ett fel på första körningen: kurvan var inte
deterministisk.** `nykortskurva` har ett fast frö, men FSRS sprider
förfallodagar med en liten slump som dras ur `random`-MODULEN, inte ur ett
frö man kan skicka in. Mätt vandrade kum(365) mellan 8,231 och 8,267 beroende
på globalt slumptillstånd.

Litet i tal, stort i art: kurvan styr hur många nya kort som införs per dag,
och ett tal som ändrar sig mellan anrop går inte att resonera om. Koden
PÅSTOD dessutom motsatsen i en kommentar. Åtgärdat med `fuzza=False` i
simuleringarna — fuzzningen är rätt i drift, där den hindrar att en hel dags
införda kort klumpar ihop sig för alltid, men fel i en mätning.

    ✓ kostnadskurvans form          ✓ tidsspärren är binär
    ✓ horisonten håller målet       ✓ nya är ett saldo
    ✓ prognosens dag noll är exakt  ✓ upplåsningströskeln
    ✓ beslutet är monotont          ✓ båda villkoren binder

**Kvar av 1,3x-överskjutningen vid två år** finns oavsett horisont, eftersom
kurvan växer logaritmiskt utan gräns. Det är samma sak som posten fann: ett
stadigt inflöde stannar aldrig.

**Öppet:** om systemet ska VISA den förutsagda kurvan i stället för att bara
reglera tyst. En användare som kör i tio år får en växande arbetsdag oavsett
vad vi gör, och det bör hen kunna se.

### B3 ~ — I vilken ordning ska nya ord införas?

Ordningen bestäms idag av `_rang()`: källa (kärnordförråd före öppet), nivå
(A1 före A2), och centralitet — hur många av språkets meningar ordet kan
delta i — normaliserad INOM ordklass, eftersom 169 möjliga subjekt och 65
möjliga verb inte är jämförbara tal. `_fläta` varvar sedan kategorier så att
inte fem kroppsdelar kommer i rad, men bara genom att bryta serier, aldrig
genom att offra rangen.

**Det som saknas är frekvensdata, och invändningen mot den är riktig.**
Frekvens är inte en egenskap hos konceptet utan hos ordet i ett språk. Två
sätt att använda den, och de svarar på olika frågor:

1. **Rangordna konceptet efter ordets frekvens i det språk som lärs.** Då blir
   ordningen olika per kurs, vilket är korrekt för inlärningen — tyskkursen
   ska lära ut det som är vanligt på tyska — men komplexitetsstegen blir inte
   längre jämförbar mellan språk.
2. **Rangordna konceptet en gång, ur ett medelvärde.** Då är ordningen delad,
   men snedvriden av just det som invändningen pekar på: ett ord som är
   grammatiskt arbetsredskap i ett språk (franskans `faire`) och marginellt
   i ett annat får fel plats i båda.

Data finns för alla sju språken (frekvenslistor ur undertextkorpusar täcker
sv/en/de/fr/es/it/ja), så problemet är inte tillgång utan val.

**Öppet:** vilket av 1 och 2; och om ordningen ska vara en egenskap hos
konceptet i ordboken eller räknas fram per kurs.

### B4 ! — Hur mycket vill användaren öva?

#### FÖRSTA DAGEN BLEV ETT ENDA ORD (2026-08-27)

Julius: *"Nu när jag kör så består första övningen endast av ett ord
'nous'."* Reproducerat exakt: hela dagen var en glosa, `att_göra = 1`, med
tjugo minuter budgeterade.

Kedjan, mätt led för led:

    inflödestak            7      ← frusen från FÖRE nollställningen
    kort_per_koncept (fr)  4,01
    nya_ord = int(7 / 4,01) = 1   ← hela dagens lektion

**Taket fryses per dygn med flit** — svarar man snabbt sjunker
sekunder-per-repetition, vilket annars höjde målet mitt i ett pass, och
brådska ska inte belönas. Men `nollställ` raderar hela kortleken och rörde
aldrig frysningen. Kursens EGET rum var 51 kort; den läste 7 från en kortlek
som inte längre fanns.

Efter rättelsen: inflödestak 7 → **51**, dagens lektion 1 → **18 ord**,
`att_göra` 1 → 28.

**Heltalsavkortningen förstärkte felet men var inte orsaken.** `int(tak /
kort_per_koncept)` ger noll ord för allt under 4,01 och ett ord ända upp till
8,02 — så ett lågt tak kollapsar till en tom eller nästan tom dag. Talet är
riktigt räknat; det var indatan som var gammal.

#### TVÅ KURSER MOT SAMMA SPRÅK ÄR INTE BYGGT (2026-08-27, `?`)

Fyndet ovan blottade en större sak. Julius har två franskakurser, och de
delar mer än han kan se:

- **`Kort` har `språk` men ingen `kurs_id`.** Båda kurserna övar SAMMA
  kortlek. Nollställer man den ena nollställs den andra.
- **`nollställ` bygger om kortleken på nivå 1** för hela språket, men sätter
  `nivå = 1` bara på den kurs som nollställdes. Grannkursen står kvar på sin
  nivå med en kortlek byggd för nivå 1.
- **Dagens tak och `meningar_per_dag` slås upp med `WHERE målspråk = ?`**,
  som returnerar en enda rad för två kurser. Det är medvetet — en tidigare
  rättelse la det på språk just för att kortleken är gemensam — men taket
  härleds ur `minuter_per_dag`, som är per kurs (10 respektive 20 hos
  honom). Delningen kan alltså inte vara riktig åt något håll.

**Det här är inte en bugg utan en obyggd konfiguration.** Antingen ska
kortleken bli per kurs (`kurs_id` på `Kort`, en stor ändring), eller så ska
en andra kurs mot samma målspråk vägras.

**BESLUTAT 2026-08-27: vägra, tills vidare.** Julius körde sv→fr och en→fr
och trodde att de var skilda åt. Spärren ligger i KODEN och inte i schemat:
`UNIQUE (källspråk, målspråk)` går inte att skärpa till `UNIQUE (målspråk)` i
en databas som redan bryter mot den nya regeln, och hans gör det. En kodspärr
verkar på både nya och befintliga databaser och lyfts med en rad den dag
kortleken blir per kurs.

**Spärren gäller bara NYA kurser, och det är den svåra halvan.** `ny_kurs` är
också vägen man ÖPPNAR en kurs på, så en spärr utan undantag låste ute
användaren från båda sina kurser så snart dubbletten fanns. Jag skrev det
felet först. Invarianten i `tjänsteprov` prövar därför båda riktningarna: att
en ny kurs vägras OCH att den befintliga går att öppna.

`ordbok kurs --ta-bort ID` finns nu, och tar bara bort KURSRADEN. Korten hör
till målspråket — det är hela skälet till att spärren behövs — så en annan
kurs mot samma mål behåller dem, och finns ingen sådan står kortleken kvar
orörd. Att radera den vore en nollställning, och den har en egen knapp med en
egen bekräftelse.



Det enda talet användaren behöver ange, eftersom det är det enda som inte
går att räkna fram: det är inte ett faktum om språket utan om hens dygn.

**BESLUTAT 2026-08-23: talet är MINUTER PER DAG, inte meningar per dag.**

`meningar_per_dag = 20` var fel storhet, och felet var inte bara enheten.
Ingen människas begränsning är "tjugo meningar" — begränsningen är tid. Och
värre: ett tak på antalet övningar konkurrerar med kravet att alla förfallna
kort ska göras (B5). Två krav som kan säga olika saker om när dagen är slut
är ett krav för mycket.

Med minuter försvinner konflikten. **Antalet meningar blir en KONSEKVENS**,
inte ett val: dagen innehåller de kort som förfallit, och hur många meningar
det blir följer av hur många kort en mening rymmer.

Arbetsbördan regleras då inte genom att korta av dagen utan genom att styra
hur mycket nytt som förs in (B2). Det är den enda ratt som faktiskt påverkar
framtida arbete, och det är den Anki också använder.

**Vad som krävs för att det ska gå att bygga:** en omräkning från minuter
till kort, alltså **sekunder per repetition, mätt ur användarens egen logg**.
Den mätningen finns inte — och det är samma tidsloggning som E7 sköt på
framtiden. Beslutet i B4 gör den alltså LASTBÄRANDE och inte valfri.

**BYGGT 2026-08-24.** `Kurs.minuter_per_dag` finns och går att ställa från
kursvyn, `sekunder_per_repetition()` är växelkursen, och `dagsplan` styr
inflödet efter den. Antalet meningar är numera en konsekvens: dagen innehåller
de kort som förfallit, och hur många meningar det blir följer av hur många
kort en mening rymmer.

**INNAN MÄTNINGEN FINNS** faller systemet tillbaka på det gamla målet
(meningar × kort per mening) — men aldrig på det gamla KOSTNADSMÅTTET, som var
fel med en faktor fem till trettio. Reservvägen byter alltså enhet på målet,
inte på räkningen.

**Och gränssnittet säger det.** Ett fält som inte gör något och inte förklarar
varför är värre än inget fält, så kursvyn skriver antingen "your measured pace
is 8,3 s per card" eller "not in effect yet — it needs a few timed sessions
first".

#### DEFEKT (2026-08-25) — ratten är i praktiken frånkopplad

Julius: "20-minutersapproximeringen är helt vrickad. Det går alltid på kanske
5 minuter, och det står alltid *about 1 min left*."

Kedjan, mätt länk för länk på franskan med 20 minuter inställt:

    minuter_per_dag           20
    sekunder_per_repetition   2,81      ← ur loggen
    kapacitet_kort           427        ← 20 min omräknat
    inflödestak               51        ← den hållbara takten
    förfallna                  0
    → dagen blir 51 kort = 2,4 minuter

**Varje länk räknar rätt och resultatet är orimligt.** Det är inte ett fel i
någon av dem utan i sammansättningen, och det är tredje gången det här lagret
producerar samma sorts bugg.

Tre saker är fel på en gång:

**1. `minuter_per_dag` binder aldrig.** `kapacitet_kort` (427) är det enda
stället talet går in, och det överskuggas alltid av `inflödestak` (51). B4
säger att minuterna är användarens ENDA ratt; i praktiken gör den ingenting,
eftersom ett annat villkor alltid tar först. Att inflödestaket binder är
RIKTIGT — B2 finns just för att hindra att man för in mer än man orkar bära —
men då är minuterna ett TAK och inte ett mål, och gränssnittet påstår
motsatsen.

**2. Takten vilar på 16 mätningar från fel aktivitet.** Hela loggen är 16
engelska meningar à 6,5 s och 9 glosor à 3,4 s, tagna medan Julius testade —
svarade snabbt, ibland tomt. Franskan och tyskan ÄRVER det talet (vilket
`sekunder_per_repetition` uttryckligen ska göra). Han upplever ~5 minuter där
modellen säger 1, alltså en underskattning på tre till fem gånger.

**3. Och därför visas ett tal som inte går att lita på.** `MINSTA_TIDTAGNA`
är tio, och tio mätningar från ett testpass räcker uppenbart inte för att
styra ett dygn.

**Det här är samma öppna fråga som nedan, sedd från andra hållet:** växelkursen
saknar en botten, och tröskeln för när den får användas är för låg. Skillnaden
är att det inte längre är hypotetiskt — det syns på skärmen.

**ÖPPET: växelkursen har ett tak men ingen botten.** `AVBROTTSGRÄNS_MS`
klipper en enskild uppgift som tagit för lång tid, och `MINSTA_TIDTAGNA`
kräver tio mätningar innan talet används. Men ingenting hindrar att talet blir
absurt LITET, och kapaciteten är `minuter × 60 / sekunder_per_repetition` —
alltså en division utan undre gräns. Sett i en simulering som svarade på en
millisekund: `inflödestak` blev 30 046 858 kort, och `nya` nådde 367 innan
lagret band.

Det når inte verklig användning — klockan går på servern, från att uppgiften
lämnas ut till att svaret kommer, och en människa svarar inte på fem
millisekunder. Men det är en styrning utan nedre spärr, och det är just den
sortens sak som blir farlig när något annat ändras.

En undre gräns skulle vara ett VALT tal, och sådana ska inte smygas in. Två
härledda alternativ finns: klipp kapaciteten mot vad kortleken faktiskt kan
leverera (samma sorts spärr som `nya = min(osedda, …)` redan är), eller kräv
att en mätning bär en rimlig fördelning innan den får styra. Frågan är inte
avgjord.

**Och den saknade bottnen är inte längre hypotetisk.** En simulering som
svarade på noll millisekunder drog `sekunder_per_repetition` till **2,8
mikrosekunder**, och dagen planerade in 246 nya kort på en tiominutersinställning.
Det når fortfarande inte verklig användning — klockan går på servern — men det
är samma mekanism, körd hela vägen genom tjänsten.

#### DEFEKTEN HADE EN ANDRA HALVA: FEL NÄMNARE (2026-08-26)

Posten ovan handlar om att TALET är opålitligt. Det här handlar om att det
användes på fel storhet.

    minuter_kvar = att_göra × sekunder_per_repetition

`att_göra` räknar **passrader**. `sekunder_per_repetition` har **bedömda
kort** i nämnaren — en menings sekunder delade på de kort den betygsatte. Och
en mening betygsätter fler kort än den stänger rader: den betygsätter allt den
rör, men stänger bara de rader som stod i dagens plan.

Mätt ur verkliga pass:

    glosor     1,00 rader per svar   (per definition — en glosa, ett svar)
    meningar   1,33–1,80 rader per svar   mot 2,4 bedömda kort

Produkten underskattade därför genomgående. Simulerat över en vecka med
användarens egna uppmätta svarstider:

    dag 1   lovade 1 min   verkligt 1,5
    dag 3   lovade 2 min   verkligt 3,4
    dag 5   lovade 3 min   verkligt 4,4
    dag 7   lovade 4 min   verkligt 5,7

*Rättat med en NY MÄTNING och inte en modell.* `sekunder_per_rad` är samma
tid dividerad med antalet STÄNGDA PASSRADER — och det talet är en rak
räkning, eftersom `Passkort.tidpunkt` sätts en gång per `registrera`-anrop,
alltså en gång per svar. Verifierat: 18 rader × 3,45 s = 1,0 min, och dagen
tog 1,0 min.

**De två växelkurserna har nu var sin uppgift, och det är avsiktligt.**
`sekunder_per_repetition` (per bedömt kort) styr INFLÖDET, för det är vad B2
räknar med. `sekunder_per_rad` (per passrad) översätter `att_göra` till
minuter. Att använda den ena där den andra hör hemma var hela felet.

#### OCH TIO MINUTER ÄR ETT JÄMVIKTSMÅL, INTE ETT LÖFTE OM DAG ETT

Julius: *"när jag har ställt in pass att vara 10 minuter så kanske inte det
betyder att första passet är det... de första dagarna är lite kortare för att
komma in i repetitionsrytmen?"*

Det stämmer, och det är B2:s styrning som arbetar. En ny kurs har inga
repetitioner att göra — bara det som förs in. Dagen växer mot målet
allteftersom korten börjar komma tillbaka. Samma simulering som ovan, med
tio minuter inställt:

    dag 1  1,5 min   dag 3  3,4   dag 5  4,4   dag 7  5,7

**Men gränssnittet sa det inte**, och en kort dag såg därför ut som en trasig
inställning. Hemvyn säger numera *"about 2 min left · growing toward 10 min as
reviews build up"* när dagen ligger under halva målet och det finns osett
material kvar att växa med. Villkoret är mätt, inte antaget.

### B5 ✓ — När är dagen slut?

När korten är gjorda. Punkt — det finns inget andra villkor, och det är
avsiktligt.

#### LÖSNING (2026-08-25) — passet blev ett objekt

Regeln ovan var riktig hela tiden. Det som saknades var någonstans att
skriva ner VILKA korten är.

**Före:** det fanns inget objekt som var "dagens pass". Det fanns en databas
som frågades om och om igen, plus åtta lexikon i minnet på `Övningstjänst`
som råkade hänga ihop. `dagsplan` räknade om trettio tal vid varje anrop.
Ingenting tvingade dem att vara överens — och varenda bugg i passet under
vecka 34 var två av dem som inte var det:

    passet avslutades oväntat      innehållet räknades om vid varje anrop
                                   och kunde krympa under användaren
    siffrorna följde inte passet   de beskrev databasen, inte passet
    "7 new" / "1 new" på klar dag  talen hämtades ett anrop före meddelandet
    onåbara kort malde i evighet   ingen kunde skriva ner att de var onåbara

**DAGSPLANEN ÄR POLITIK, PASSET ÄR TILLSTÅND.** Det är hela uppdelningen.
`dagsplan` räknar ut hur mycket som FÅR göras — takten, taket, tiden — och
den ska räknas om, för den är en styrning som korrigerar sig varje dygn (B2).
Men VAD dagen innehåller är ett faktum, och ett faktum bestäms en gång.

    Pass(id, kurs, datum, läge, startad, avslutad)
    Passkort(pass_id, kort_id, roll, ordning, status, tidpunkt)

    roll     glosa · förfallen · ny · igen
    status   väntar · rätt · fel · onåbar

Efter det är varje tal på skärmen en RÄKNING och inte en härledning:
`att_göra` är rader som väntar, `klar` är att inga gör det. **`klar` blev ett
faktum i stället för en slutsats**, och det finns inget andra ställe som kan
komma fram till något annat.

*Den sista meningen blev sann först 2026-08-26.* `dagsplan` fortsatte
returnera ett eget `klar` — `förfallna == 0 and nya == 0 and passkö == 0`,
alltså en härledning ur databasens nuläge — hela tiden. Den var oskadlig i
praktiken, eftersom `Övningstjänst._dagsplan` slår ihop de två med passets tal
SIST och passet därför vann, men den var ett andra svar som väntade på en
anropare. Att den fanns är också skälet till att `dagsplan` var det första man
läste och passet det andra. Nu räknas `klar` på ett ställe, och påståendet
ovan går att kontrollera i stället för att behöva litas på.

**Tre mekanismer försvann, och det är det bästa måttet på att lagret var
fel.** Minnet av onåbarhet med sitt fingeravtryck — onåbara kort får nu
status `onåbar` i tabellen, räknas som gjorda för dagen och betygsätts inte
(D3). Silen på oövade ord — ett drillat ords böjningskort står som `ny` i
passet, så dagen är inte klar förrän de är gjorda eller avskrivna, och att
räkna `oövade` vid sidan av dem var att räkna samma arbete två gånger.
Omräkningen av taket. Generatorns passkö är kvar som SÖKHJÄLP men talet som
visas kommer ur `Passkort`.

**En rad är ett planerat MÖTE, inte ett kort.** Faller ett kort läggs en ny
rad med roll `igen` till och den gamla står kvar med sitt `fel`. Passets
historik är därför en följd av möten, och B7:s "tillbaka i en ANNAN mening"
har en plats att bo på som överlever att processen startas om.

**Dagen har nu två potter, inte en.** Glosor möts i drillen, böjningskort i
en mening. Att de drog ur samma tal dolde att den ena kunde ta slut medan den
andra inte hade börjat — och eftersom `ord` står först i introduktionsordningen
tog ordraden hela taket. Uppdelningen sa 9 där drillen hade 18 att dela ut.

Mätt på en hel dag genom tjänsten, franska från noll:

    passet vid start   4 glosor + 13 nya
    efter drillen      13 kvar
    fyra meningar      8 kvar, 5 böjningskort införda
    nödutgången        8 avskrivna som onåbara
    till slut          att_göra 0, klar

**Provet är hela sviten.** Åtta prov med falsifieringspass gick igenom
ombyggnaden — och tre av dem föll först, alla för att de öppnade sin kopia
med `sqlite3.connect` i stället för `anslut_kort` och därmed förbi
migrationerna. Det var provens fel och inte lagrets, men det är också en
fälla som nu är borta.

#### OCH SÅ FICK PASSET EN LIVSCYKEL (samma dygn)

Att bestämma dagen en gång löste att den kunde krympa under användaren. Men
ett faktum som bestäms en gång får ett nytt problem i stället: **det kan bli
föråldrat.** Och det blev det omedelbart — en nollställd kurs sa
"Done for today" utan att användaren gjort något.

Fyra fall, mätt:

    nollställ en kurs             "Done for today", noll rader i passet
    nollställ en ANNAN kurs mot   samma sak, i en kurs ingen rört
    samma målspråk
    lås upp en nivå               149 nya kort, dagen oförändrad
    ändra minuterna               ratten fungerade men syntes aldrig

**De två första var `ON DELETE CASCADE` på `Passkort.kort_id`.** Raderas
korten tog kaskaden passets rader med sig, och noll rader betyder "inget
väntar", alltså klar. `starta` är idempotent och hittade det tomma passet i
stället för att bygga om.

Projektets egen regel säger vad som var fel: **kasta aldrig bevis du HAR.**
Att raden pekar på ett kort som inte finns ÄR upplysningen — det är så man
vet att passet byggdes ur ett bestånd som är borta. `SET NULL` bevarar den;
`CASCADE` förstörde den. Och först med beviset kvar går giltigheten att
HÄRLEDA i stället för att komma ihåg, vilket spelar roll: beståndet ändras
från fem ställen, varav två är kommandoradsverktyg som aldrig ser tjänsten.

**Två regler, och de drar åt olika håll:**

    ETT PASS ÄR GILTIGT så länge varje rad har ett kort. Saknas ett är passet
    en ruin och byggs om.

    ETT PASS ÄR APPEND-ONLY. Blir mer möjligt — en nivå öppnas, minuterna
    höjs — läggs det till. Blir mindre möjligt tas ingenting bort: det som
    planerats står kvar, och sänkningen syns i morgon.

**Minutratten var aldrig trasig.** Mätt linjärt: 5 min ger 12 nya kort, 10
ger 25, 40 ger 103. Taket fryses per dygn för att BRÅDSKA inte ska belönas —
svarar man snabbt sjunker sekunder-per-repetition, vilket annars höjde målet
mitt i ett pass. Men frysningen gällde också ett UTTRYCKLIGT VAL, och ett val
som inte syns är samma sorts lögn som ett tal som inte stämmer. Nu räknas
taket om när användaren väljer om; en mätning som driver ändrar det fortsatt
inte.

**Ett tredje fall dök upp efteråt, och det var mitt eget residu.** Passen som
tömdes av kaskaden INNAN `SET NULL` fanns hade sina rader hårdraderade — det
fanns inget bevis kvar för `_ruin` att läsa. Ett tomt pass fylls därför nu i
stället för att lämnas: är dagen verkligen tom lägger konstruktionen till noll
rader och passet står oförändrat, id och allt. Att i stället kasta och bygga
om vore att byta identitet på passet vid varje läsning av en tom dag.

**Provet:** `ordbok/verktyg/passprov.py`, sex invarianter med sex sabotage.
Det sista sabotaget är MOTSATSEN till de andra — bygg om passet vid varje
anrop, alltså det gamla lagret — eftersom en livscykelregel går att ha fel om
åt två håll.

FSRS bygger på att rätt kort repeteras i tid; ett pass som slutar efter
N meningar kan lämna hälften av dagens förfallna kort orörda och bryter då
själva garantin. **Ett tak på arbetsmängden motsäger modellen** och får
därför inte finnas. Blir dagen för tung är svaret att föra in färre nya kort
(B2), aldrig att lämna förfallna kort ogjorda.

    klar = förfallna == 0 och nya == 0 och passkö == 0

med en nödutgång för när ett förfallet kort inte går att bygga en mening
kring (B8), så att knappen inte kan låsa sig för alltid.

### B6 ✓ — Vad gör den som vill öva mer?

Tidiga repetitioner: kort som ännu inte förfallit, det som förfaller först
först. Det flyttar fram förfallodagar, sänker Σ 1/I(S), och skapar därmed
plats för nytt material utan att någonting behöver vänta.

**Mätt, och det är värt att veta hur mycket det ger.** Ett kort med S = 10,96
senast repeterat dag 0, förfallet dag 11:

| Repeteras dag | R | ny S | nästa förfallodag |
|---|---|---|---|
| 0 (samma dygn) | 1,000 | 10,96 | 11 |
| 1 | 0,987 | 15,43 | 16 |
| 4 | 0,954 | 26,84 | 31 |
| 11 (i tid) | 0,906 | 43,93 | 54 |

Extraövning fungerar alltså — men avtagande. Att repetera sju dygn för tidigt
ger 27 dygns intervall i stället för 44. Ingenting går sönder; det är
effektivitet som betalas, inte riktighet.

#### RÄTTELSE (2026-08-24) — den ger inte plats åt nytt, den flyttar arbete närmare

Meningen "skapar därmed plats för nytt material utan att någonting behöver
vänta" står kvar ovan därför att den var utgångspunkten, men den är MÄTT FEL.
Tyskan, sex simulerade dygn, samma frö i båda grenarna:

| | belastning | inflödestak i morgon | nya i morgon |
|---|---|---|---|
| utan extrapass | 13,00 | 13 | 13 |
| med extrapass (18 meningar) | 13,21 → 11,83 | 11 | 11 |

Belastningen sjunker precis som beskrivet — 13,21 → 11,83, alltså tio
procent. Men morgondagens utrymme för nytt BLIR MINDRE, inte större.

Skälet är vilket villkor som binder. `nya_idag` har två, och det som styr här
är IDAG-villkoret: `prognos[0] + k × kurva[0] ≤ mål`. En tidig repetition ger
en mindre stabilitetsökning, så kortet kommer tillbaka SNARARE än det annars
skulle ha gjort — och landar därför oftare i morgon. `prognos[0]` stiger, och
utrymmet för nya kort krymper med den. Antalet tidiga kort växte samtidigt
från 44 till 95, av samma orsak.

**Det motsäger inte B6:s syfte, men det ändrar vad extraövningen ÄR.** Den är
inte en ventil som gör plats åt mer nytt material. Den är ett sätt att göra
mer arbete idag mot att göra mer arbete även de närmaste dygnen — man byter
till sig repetitioner, inte utrymme. Långtidsvillkoret (medelbelastningen)
förbättras svagt, men det är inte det som binder.

**Och på dag ett finns ingenting att ta av, med flit.** `kommande()` kräver
`sedd < dygnets_början`: ett kort som införts idag kan inte betygsättas igen
samma dygn (E2), så ett extrapass byggt på dem skulle bokföra noll. Mätt efter
en nollställning var alla 14 kort i "early available" införda samma dag —
hela högen var tom på verkan. "Nothing more ahead" är alltså rätt svar på dag
ett och inte ett fel.

**En bugg låg gömd bakom just den grinden.** `kommande()` hade fyra
platshållare och tre bindningar, så varje anrop som nådde frågan kastade
`ProgrammingError`. Det syntes aldrig, eftersom `finns_extra` var noll i varje
kurs som testats för hand och knappen därför var låst. En trasig SQL-sats kan
ligga tyst hur länge som helst bakom en grind som råkar vara stängd — och det
är skälet till att `extraövningen går att köra` nu är en egen invariant.

#### RÄTTELSEN MÄTTE FEL DYGN (2026-08-26)

Julius invände mot slutsatsen ovan, och invändningen håller: *"Ifall man gör
extrapass så kommer man göra kort en dag tidigt vilket gör att de skjuts upp
lite kortare. Alltså förlorar man en dags lucka på de. Men samtidigt sparar
man massa arbete imorgon."*

RÄTTELSE ovan mätte `nya i morgon`. **Rummet uppstår inte i morgon utan
omedelbart**, och därför såg mätningen bara priset och aldrig varan.

Mätt på fransk kortlek, 740 sedda kort, FSRS-prognos över 30 dygn, samma frö
i alla grenar. Belastning per dygn:

    dygn            0    1    2    3    4    5    6    7    8 …
    ingen extra   136   51   87   28   17   20   18   26   81
    60 extra       76   54   90   29   19   23   20   42   88
    Δ             −60   +3   +3   +1   +2   +3   +2  +16   +7

**Dag noll faller med exakt de sextio kort man gjorde.** Sedan ligger varje
följande dygn någon repetition högre, eftersom en tidig repetition ger mindre
stabilitetsökning och kortet återkommer snarare. Julius beskrivning är alltså
bokstavligt riktig, mekanism för mekanism.

Nettot över horisonten: kortlekens egna arbete faller 1101 → 1091, men man
gjorde 60 repetitioner för att köpa den minskningen. **Extraövning sparar inte
arbete — den jämnar ut det till en premie på omkring fyra procent.**

#### OCH DEN KÖPER NYA KORT, MEN TILL EN BRUTAL KURS (2026-08-26)

Julius andra fråga: *"Om man kopplar in en ärlig algoritm som kan uppskatta
framtida arbete och som lägger till nya kort för att hålla en balans på x
minuters arbete per dag känns det som att den hade föreslagit lite extra nya
kort vid extraövningar."* Den algoritmen ÄR `nya_idag`, och den gör det —
knappt. Mätt direkt efter extrapasset, mål 150 rep/dygn:

| extra gjorda | belastning idag | tak idag | i längden | nya släpps in |
|---|---|---|---|---|
| 0 | 136 | 14 | 11 | **11** |
| 20 | 116 | 34 | 11 | **11** |
| 60 | 76 | 74 | 11 | **11** |
| 150 | 40 | — | 12 | **12** |

**IDAG-villkoret lossnar dramatiskt — taket går 14 → 74 — och ändå rör sig
inte inflödet.** Skälet är att `nya_idag` tar `min(i_längden, idag)`, och det
som binder är LÅNGTIDSVILLKORET. Extraövningen sänker fönstrets medel 56,1 →
48,2, alltså fjorton procent, men ett nytt kort kostar 8,40 repetitioner över
året, så `i_längden` går 11 → 12.

**Växelkursen är alltså omkring 150 extra repetitioner per nytt kort**, och
den är mätt och inte antagen.

**Att det är så är rätt, inte ett fel.** Ett extrapass är en engångshändelse.
Släppte det in nya kort i takt med hur mycket man gjorde skulle man låna mot
en långtidsbudget man inte har ändrat: korten kommer tillbaka i evighet, men
extraövningen sker en gång. Det tal som FÅR flytta inflödet är
`minuter_per_dag`, därför att det är ett stående åtagande. Skillnaden mellan
en engångsinsats och ett åtagande är precis vad de två villkoren i `nya_idag`
skiljer på, och att bara det ena biter är styrningen som fungerar.

**Vill man ha fler nya kort är spaken inställningen, inte extrapasset.**

#### URVALSPOLICYN ÄR REDAN DEN RÄTTA (2026-08-26)

Fyra policyer mätta på samma kortlek, 60 kort var, Δ mot ingen extra:

| policy | Δ dag 0 | Δ arbete 30 d |
|---|---|---|
| `förfaller ASC` (nuvarande) | −60 | +50 |
| förfaller DESC | ±0 | +48 |
| störst framflyttning | −57 | +29 |
| bara inom två dygn | −60 | +50 |

Att ta det som förfaller först är alltså den enda policy som faktiskt tömmer
den närmaste dagen. `förfaller DESC` rör ingenting — de korten ligger 15–55
dygn bort och lämnar fönstret oavsett. Policyn behöver inte ändras.

#### VÄRDET GÅR ATT VISA, OCH DET ÄR NU UTSKRIVET (2026-08-26)

Julius: *"Det borde finnas ett sätt att indikera ungefär hur effektfullt det
är att repetera. Detta kan man kanske approximera med FSRS-funktioner."*

Det behöver inte approximeras — FSRS räknar det exakt, och tabellen överst i
posten är redan svaret för ETT kort. `extranytta()` gör samma räkning för
kön som faktiskt ligger där:

    för varje kort i kommande():
        vinst_nu  = S(betyg=Good, R vid dagens R) − S
        vinst_sen = S(betyg=Good, R vid förfallodagen) − S
        andel     = vinst_nu / vinst_sen

och väger ihop dem. Talet är en andel av full nytta, alltså "hur mycket av
det kortet vore värt vid förfallodagen får du om du gör det nu".

| hur tidigt | andel av full nytta |
|---|---|
| 11 dygn (nyss infört) | 0 % |
| 8 dygn | 35 % |
| 5 dygn | 63 % |
| 3 dygn | 79 % |
| 1 dygn | 93 % |
| i tid | 100 % |

Noll på dag ett är inte en avrundning utan FSRS korttidsformel: samma dygn
är R = 1,000 och stabilitetsfaktorn klämmer till 1,0×. **Julius gissning att
det "kanske inte händer något när man repeterar ord som man har gjort samma
dag" är alltså bokstavligt riktig** — och det är därför knappen är låst just
då, inte av försiktighet.

Mätt på två verkliga lägen: den simulerade fjortondagarsleken gav **56 %**
med hundra kort i kön, och ett läge där korten förfaller inom kort gav
**98 %**. Måttet skiljer alltså på lägena i stället för att visa en konstant.

**Det som INTE går att lova är Julius andra hälft** — *"kanske till och med
skapa tillräckligt med rum i kalendern så att det finns plats för ett nytt
kort"*. Det är precis vad RÄTTELSE ovan mätte och fann omvänt: extrapasset
sänkte belastningen 13,21 → 11,83 men minskade morgondagens utrymme för nya
kort från 13 till 11. Extraövning köper repetitioner, inte rum. Knappen
säger därför vad den ger — "X early available · about 56 % of the value of
waiting" — och lovar ingenting om nya kort.

### B7 ✓ — Ett fel får inte lämnas ofixat

#### ETT FEL KÖAS NU ÄVEN PÅ ETT OPLANERAT KORT (2026-08-27)

`registrera` hoppade över ett fallerat kort som inte stod i dagens plan. En
mening rör sju till tio kort men valdes för ett av dem (E4), och skälet var
att dagen annars aldrig kan ta slut.

**Julius beslutade att priset är rätt:** *"Hela grejen med FSRS är att det
inte finns x antal övningar utan att alla korten ska passeras. Användaren
måste KLARA övningarna för att bli klar med dagen. Det kräver framgång, inte
bara effort."*

**Och farhågan visade sig mindre än den lät.** Tillväxten är bunden av FEL
och inte av antalet meningar — en mening som går rätt lägger till noll, hur
många oplanerade kort den än rörde. Mätt på en ny fransk kurs med var fjärde
mening medvetet fel: dagen tog slut efter **14 meningar**, `att_göra = 0`.

#### VAD SOM FAKTISKT HÄNDER NÄR ETT AVKLARAT KORT FALLERAR (mätt 2026-08-27)

Julius trodde att ett fel på sista meningen inte öppnade dagen igen. Mätt:

    dagen klar (att_göra 9, klar False → allt bedömt)
      → fel på ett redan avklarat kort
      → att_göra 9 → 11, igen 0 → 2, dagen öppen

Mekanismen fungerar alltså. **Och FSRS gör sin del utan att kortet kommer
tillbaka idag:**

| S före | förföll | S efter | ny förfallodag |
|---|---|---|---|
| 11,0 | 7 sep | 1,289 | 28 aug |
| 34,8 | 1 okt | 2,128 | 29 aug |
| 120,0 | 25 dec | 3,412 | 30 aug |

Ett kort uppskjutet till jul kommer tillbaka om tre dagar. Straffet är fullt
ut; bara dygnsgränsen hindrar det från att landa idag (B7 ovan).

#### EN MÄTNING SOM VAR MIN EGEN ARTEFAKT (2026-08-27)

Jag rapporterade först att ändelse- och stamkort ALDRIG bedöms — 602
`undanhållen` mot 0 `bedömd` över 300 meningar — och att dagen därför inte
kunde ta slut. **Det var fel, och felet var mitt svar.**

`uppgift()` innehåller inget facit; det avslöjas först i `svara()`. Min
slinga skickade `u.get("facit") or ""`, alltså TOMMA SVAR trehundra gånger,
och ett svar som inte går att analysera undanhåller varje kort det inte kan
peka på. Med riktiga svar, hämtade ur tjänstens eget `_öppna`:

    9 meningar → att_göra 0, klar True, 10 ändelsekort införda
    system: 10 bedömda   stam: 9 bedömda

**Lärdomen hör hemma här och inte bara i mig:** en simulering som svarar fel
mäter rättningens felväg, inte produktens normalväg, och de två ser likadana
ut i en sammanställning. `Spår` gjorde skillnaden synlig på en fråga — vilket
är precis vad tabellen byggdes för.



Kortet kommer tillbaka i en ANNAN mening samma pass.

**Varför det inte kan ligga i schemat.** Ankis "again → 10 minuter" kommer
inte från FSRS utan från Ankis **learning steps**, en mekanism som ligger
UTANFÖR minnesmodellen: Anki tar kortet ur FSRS händer och stoppar det i en
kort loop, och lämnar tillbaka det till modellen först när loopen är klar.
FSRS själv har ingen tidsupplösning under ett dygn — `_next_interval` avrundar
till hela dygn och klämmer till `max(intervall, 1)`.

Vi kör medvetet med `learning_steps=()` och `relearning_steps=()`. Skälet är
att se SAMMA kort igen om tio minuter är precis det som gör att man fastnar;
generatorn kan i stället ge kortet i en ny mening med andra ord omkring.
Priset är att FSRS då schemalägger det fallerade kortet till i morgon, och
återförsöket måste därför ligga någon annanstans: i generatorns **passkö**,
som är per pass och lever i minnet.

**Mätt att det inte förstör något:** Again, och sedan Good tjugo minuter
senare, ger S 1,538 → 1,571 och D 7,39 → 7,38. Straffet står kvar,
återförsöket köper inte loss det. Det är precis vad man vill.

#### REGELN GÄLLDE INTE ETT KORT SOM REDAN VAR AVKLARAT (2026-08-26)

`pass_.registrera` letade efter en passrad med status `väntar` och hoppade
över allt annat. Ett kort som drillats rätt på morgonen och sedan fallerade i
en mening samma dag fick därför **ingen `igen`-rad**.

Mätt på `ord:avoir`, drillat rätt i glosläget och sedan fällt i `J'ai.`:

    efter drillen   S = 2,307   D = 2,12   förfaller 28 aug
    efter felet     S = 0,775   D = 7,39   förfaller 27 aug   ← ETT DYGN BAKÅT
    passraden       glosa: rätt — oförändrad

Kortet tappade två tredjedelar av sin stabilitet, svårigheten mer än
tredubblades, förfallodagen flyttades bakåt — och passet visste ingenting om
det. Följderna var tre, och alla tre är sådant passlagret finns för att
omöjliggöra:

- `att_göra` rörde sig inte, så dagen kunde säga **"klart" med ett kort som
  just rasat**
- huvudradens `igen` (generatorns minnesinterna passkö) och `dagsläge`s `igen`
  (tabellen) gled isär och återförenades aldrig — mätt 5 mot 3 efter fem
  meningar
- återförsöket levde bara i minnet och dog vid omstart

**Att felet bokförs är riktigt** (E2: "ett FEL får alltid registreras, även om
kortet redan bedömts idag"). Det som saknades var att dagen fick veta om det.
Den här postens regel skiljer inte på om kortet råkade vara avklarat — ett fel
får inte lämnas ofixat.

*Rättat: `igen`-raden läggs till oavsett tidigare status, så länge kortet
tillhör dagens plan.* Ett kort som INTE står i dagen — ett sett kort som råkade
vara med i en mening som valdes för något annat (E4) — får fortfarande ingen
rad, för annars kunde ett pass aldrig ta slut.

### B8 ~ — Vad händer när ett förfallet kort inte går att bygga en mening kring?

Det händer, och det har mätts: två tyska stamkort gick inte att nå med någon
mening samplaren producerade, så villkoret `förfallna == 0` blev aldrig sant
och dagens knapp låste sig aldrig. Därför är `klar` nu kortdriven med en
nödutgång, och `uppgift()` har en reservväg för när noll köade kort täcks.

**Tre orsaker som ser likadana ut men inte är det:**

1. Kortet är strukturellt onåbart (A3) — ordföljd, rektion, hål i `Cellkort`.
2. Kortets cell kräver en konstruktion nivån inte låst upp.
3. Samplaren KAN bygga meningen men råkade inte göra det på 1 000 försök.

Bara 3 är ett sökproblem. 1 och 2 är datafel, och de korten borde inte stå i
kön över huvud taget. Ingenting skiljer dem åt när det händer.

**Att bygga en mindre mening löser bara 3.** Är kortet onåbart hjälper ingen
storlek. Nödutgången idag är därför inte en lösning utan en spärr mot att
låsa sig.

#### LÖSNING (2026-08-24) — spärren gick att gå förbi på tre sätt

Spärren fanns men höll inte, och en franskkurs låste sig i drift: fyra
meningar i rundgång, täckning noll, 330 gånger, medan hemskärmen stod kvar på
"7 new" dygnet ut. Tre orsaker, alla i sömmen mellan kö, mål och räkning.

**1. Nödutgången krävde FÖRFALLNA kort.** `täckta == 0 and förfallna` — men
onåbarheten gäller hela kön, och kön är förfallna PLUS passkön PLUS dagens
nya. Med noll förfallna och sju nya böjningskort som alla krävde ord kursen
inte hade (`pres_2sg` utan `tu`, `sg` utan substantiv, hjälpverbet för en
tempus nivån inte öppnat) föll spärren aldrig ut. *Rättat: villkoret är
`täckta == 0`, punkt.*

**2. Ett målord samplaren inte kan bygga kring ignorerades TYST.**
`Samplare.kandidat(kring=k)` tar `k` bara om det är ett verb i mönstret eller
ett frashuvud något verb tar; allt annat faller till `else` och får ett
slumpvis verb. `un` drillades som ord, blev därmed "infört men inte övat",
och stod först i målordslistan — som ERSATTE kön i stället för att gå före
den. Varje mening byggdes alltså kring ett ignorerat mål, och kön rördes
aldrig. *Rättat: `Samplare.duger_som_mål` läser villkoret ur `kandidat` själv,
och varje prioritetsnivå silas genom det innan nästa får ta över.*

**3. Ett osilat oövat ord låg i KÖN och räknades som täckt.** Därmed var
`täckta` alltid minst ett, och nödutgången i punkt 1 kunde inte lösa ut ens
efter att den rättats. Mätt på engelskan, som fastnade på samma sätt efter att
franskan var lagad. *Rättat: silningen sker en gång, i `föreslå`, så kön och
målorden inte kan säga olika.*

**Och hemskärmen minns svaret.** Har passet sökt igenom flera hundra
kandidater utan att röra något i kön är det en MÄTNING, inte en gissning, och
dagens nya kort räknas då bort. Noteringen självsanerar: fingeravtrycket är
det som skulle kunna göra något nåbart igen — ett infört kort, en ändrad
förfallolista, en tömd passkö, ett övat ord.

**Taket är ett tak, inte en kvot.** Frestelsen var att lägga den outnyttjade
delen på fler ORD, så att minuterna fylls. Det mättes och förkastades: sju
kort omräknat till sju ord blev tjugoåtta, eftersom ett franskt ord drar med
sig 4,01 kort — en dag med taket 25 införde 40. Vid kallstart är ordförrådet
för tunt för att bära sin egen tilldelning, och det botas av att morgondagen
kommer.

**Kvar som öppet:** de tre orsakerna högst upp skiljs fortfarande inte åt. En
kö full av kort av typ 1 och 2 ger nu en dag som tar slut i förtid i stället
för en som aldrig tar slut — bättre, men fortfarande inte samma sak som att
inte köa dem.

#### OCH KVOTEN KOM TILLBAKA, PÅ ETT ANNAT STÄLLE (2026-08-26)

Passlagret byggdes efter posten ovan, och dess `_rader` fick en växelvarvsloop
med ett riktigt syfte: mät nåbarheten EFTER att dagens ord valts, inte före.
Det var nödvändigt — mäter man före är svaret vid kallstart noll, allt går
till ord, och dagen blir sju glosor och noll meningar.

Men loopens avbrottsvillkor var `rest <= 0 or not glosor and not nya_kort`,
alltså "sluta bara om BÅDA listorna är tomma". Det finns nästan alltid ett ord
till att ta, så loopen fortsatte köpa ord långt efter att de slutat låsa upp
något. Mätt på en färsk franskkurs med taket 25:

    varv 0    6 ord  →  7 böjningskort
    varv 1    8 ord  →  2
    varv 2    9 ord  →  0     ← härifrån är varje varv rent slöseri
    varv 3   10 ord  →  0
    varv 4   11 ord  →  0
    varv 5   12 ord  →  0

Dagen fick tolv ord där `nya_ord` räknat fram sex. **Det är exakt vad posten
ovan mätte och förkastade**, återinfört på ett ställe posten inte kände till.

**Rotorsaken under det är växelkursen `_kort_per_koncept`**, och den är mer
intressant än loopen. Den är 4,01 för franskan, mätt så här:

    389 genuskort + 212 stammar + 203 ordkort + 16 former + 2 rektion
    = 822 kort / 205 koncept

Genus kräver artiklar och adjektiv, alltså nivå 3 och 5. Stammar kräver böjda
former. **På nivå 1 låser ett nytt ord bara upp ÄNDELSEKORT — och franskan har
elva sådana totalt, som dessutom har `koncept = NULL` och därför inte ingår i
medelvärdet alls.** Talet 4,01 beskriver en kortlek dagen inte kan använda,
och `nya_ord = tak / 4,01` blir därför för litet, varpå loopen kompenserar åt
andra hållet.

*Rättat: loopen bryter när ett varv inte gav några böjningskort.* Dagen gick
från 12 + 9 = 21 kort till 9 + 9 = 18. Växelkursen står orörd — att räkna om
den mot NÅBARA kort på nivån är en riktigare mätning men ett eget beslut, och
den står som öppen nedan.

#### DAGEN SLUTADE I FÖRTID FÖR ATT DE TVÅ KÖERNA VAR DISJUNKTA (2026-08-26)

Posten ovan skiljer tre orsaker till att ett köat kort inte går att nå. Den
vanligaste var ingen av dem, och den var inte en egenskap hos språket utan ett
fel: **passet och generatorn köade helt olika kort.**

`pass_._rader` väljer dagens nya kort och silar dem genom `nåbara_kort` — bara
kort som någon byggbar mening kan röra kommer med. `Generator.föreslå` frågade
i stället `Schemaläggare.osedda` på nytt, som svarar med de HÖGST RANKADE
osedda korten, oavsett nåbarhet. Mätt på en färsk franskkurs, varv för varv:

    passet väntar på 9 nya kort, generatorn köar 9
    gemensamma 0 · bara i passet 9 · bara i generatorn 9

Noll överlapp, varje varv. Generatorn byggde alltså meningar mot kort som per
konstruktion inte gick att nå, medan de kort dagen faktiskt planerat aldrig
blev målord. När de oövade orden var slut föll `täckta` till noll, nödutgången
löste ut, och passets kort skrevs av som "onåbara" — trots att meningarna som
når dem aldrig hade ställts:

    K0 pres_1pl   `Nous existons.`   (visad var `Nous avons.`)
    K1 pres_1sg   `J'ai.`            (visad var `J'existe.`)
    K1 pres_2pl   `Vous avez.`       (visad var `Vous coûtez.`)
    K1 pres_2sg   `Tu as.`           (visad var `Tu existes.`)

**Det är G6:s felklass en gång till.** `Pass` är auktoriteten på vad dagen
innehåller, och en ändpunkt räknade fram sitt eget svar. Att felet såg ut som
onåbarhet gjorde det svårt att se: nödutgången rapporterade sanningsenligt att
den inte kom längre, men skälet var att den letade på fel ställe.

*Rättat: `uppgift` skickar passets väntande `ny`-rader till `föreslå`, som
använder dem i stället för att fråga om.* Mätt före och efter, fyra frön per
kurs:

    franska nivå 1    4 avskrivna  →  0     (8 meningar, dagen går i mål)
    tyska nivå 4      0            →  0
    engelska nivå 1   0            →  0
    japanska nivå 1   0            →  0

#### OCH MENINGSRUMMET ÄR LITET, MEN VAR INTE GRÄNSEN

Mätningen som gjordes på vägen står kvar därför att den är sann och värd att
veta, inte därför att den förklarade felet:

    12 kända ord, nivå 1, 6 000 kandidatförsök  →  24 olika meningar

Tjugofyra meningar är hela rummet dag ett. Det räcker — dagens nio ändelsekort
täcks av åtta av dem — men marginalen är tunn, och den blir tunnare ju fler
kort en dag planerar. **Öppet:** ska dagens storlek begränsas av meningsrummet
och inte bara av nåbarheten? Talet går att mäta med samma sampling
`byggbarhet` redan gör. Frågan är inte akut nu när köerna är samma, men den
kommer tillbaka om taket höjs.

*(En omväg prövades och förkastades på vägen: att göra ändelsekort till målord
via `Cellkort`. Se A7 — den mättes till noll verkan och togs bort.)*

**Provet:** `passet tar slut` i `ordbok/verktyg/tjänsteprov.py` — rätta svar
hela vägen ska tömma dagen inom 120 steg. Det fällde engelskan direkt efter
att franskan lagats, alltså en andra kurs med samma låsning som ingen hade
sett för hand.

---

## C. Hur byggs uppgiften? — generering

### C1 ✓ — Meningar löses fram, de författas inte

Systemet ser kön och konstruerar en mening som tränar den. 1 000 kandidater
samplas, alla poängsätts, den bästa ställs. Alternativet — en färdig
meningsbank — kan aldrig träffa just de kort just den här användaren är svag
på just idag, och det är hela poängen med systemet.

### C2 ! — Hur svår ska en mening vara?

**Algoritmen idag.** Varje mening får en budget: ett målvärde för Σ(1−R) över
meningens SEDDA kort. Σ(1−R) är FSRS egen förutsägelse av hur många kort som
kommer att bli fel. `Kurs.budget` = 1,5, och poängtermen är

    −4 · (Σ(1−R) − 1,5)²

kvadratisk, så små avvikelser är gratis och stora dyra. Osedda kort räknas
INTE med — R är odefinierat för ett kort som aldrig prövats, och att sätta
det till noll betyder att varje nytt ord räknas som ett säkert fel. Det
provades och sökningen degenererade till kortast möjliga mening.

**Defekten, och den är värre än "har inte nåtts".** Uppmätt utfall är 0,008.
Men räkna på taket. Summan går över meningens SEDDA kort, och ett kort som är
exakt förfallet ligger per definition på R = 0,90 och bidrar med 0,10. Alltså
är det högsta uppnåeliga `0,10 × sedda kort per mening`. Mätt ur `Mening`:

    de   1,60 sedda kort per mening   →  tak 0,16
    en   3,24                         →  tak 0,32
    fr   4,64                         →  tak 0,46

Budgeten 1,5 ligger alltså mellan tre och nio gånger över vad en mening
överhuvudtaget kan bära, även om varenda kort i den vore förfallet. **Talet
1,5 härleddes aldrig ur antalet kort per mening och retentionsmålet — det är
därför det aldrig kan nås.** Det är inte en inställning som ligger fel; det
är en storhet utan koppling till det den mäter.

(Taket stiger när kortleken mognar, eftersom `sedda` går mot totala antalet
kort per mening när färre av dem är nya. Men det når aldrig 1,5 utan
kraftigt försenade kort.)

---

#### LÖSNING (tredje formen, 2026-08-23 — inte byggd)

*Två tidigare former föll. Den första var en TAKTREGEL — dagens
prövningsmassa delad på dagens återstående meningar — och den föll med B4,
eftersom `meningar_per_dag` försvann och ett tak på arbetsmängden dessutom
motsäger FSRS (B5). Den andra var bara ett TAK, utan att säga vad sökningen
skulle maximera under det. Den här formen säger båda delarna, och den är
härledd ur avgränsningens målfunktion i stället för ur intuition.*

**Frågan "hur svår ska en mening vara" har inget svar, och det är svaret.**
Svårigheten är vad kön levererar. Man väljer den inte. Det som återstår är
två helt andra frågor: vad sökningen ska maximera, och vad den inte får
överskrida.

---

**1. VAD SÖKNINGEN MAXIMERAR — återkallelser per sekund**

Avgränsningen överst i dokumentet ger målfunktionen: kunskapsmoment hållna
över retentionsmålet, per minut användaren lägger. Ett förfallet kort är per
definition ett moment som annars faller under målet. Alltså:

    värde  =  antal förfallna kort meningen återkallar
              ────────────────────────────────────────
                    sekunder meningen kostar

Det är inte antal kort som ska maximeras, utan **kort per tid**. Skillnaden
är inte kosmetisk — den prissätter varje extra ord, vilket ingen tidigare
form gjorde.

Fyra av de åtta vikterna försvinner in i kvoten:

    täckning   blir täljaren
    längd      blir nämnaren — och slutar vara en smakfråga, se nedan
    tomgång    behövs inte: noll täckta kort ger täljare noll, alltså värde
               noll, alltså sämst av alla kandidater automatiskt
    budget     blir taket i punkt 2, inte en term

**Tiden måste modelleras, och den är mätbar:**

    sekunder ≈ a + b × ord        a = läsa och tänka, b = skriva per ord

Båda koefficienterna faller ut ur en regression på loggen så snart tiden
registreras (B4, E7). Fram till dess är de PROVISORISKA och ska stå som
omätta.

Det är också det som gör C8 till en räknefråga: en lucka ger en återkallelse
på ett par sekunder, en hel mening två till tre på tjugo. Vilken form som
vinner avgörs av kvoten, inte av tycke.

**Nya kort räknas inte i täljaren.** Deras antal är en kvot från B2, inte ett
sökbeslut, och den kvoten är i stort sett densamma för alla kandidater. Att
låta dem ge poäng vore att låta sökningen förhandla om något B2 redan
bestämt.

---

**2. VAD SÖKNINGEN INTE FÅR ÖVERSKRIDA — korrelationstaket**

    Σ(1−R) över meningens STRETCHKORT  ≤  taket

Utan gräns skulle kvoten packa meningen full: fler täckta kort på nästan
samma tid höjer alltid värdet. Gränsen finns av ett skäl som inte handlar om
upplevelse utan om **dataintegritet.**

FSRS behandlar varje kort som oberoende bevis. Fel i SAMMA mening är det
ofta inte. En enda feluppfattning om `Kind`s genus fäller både artikeln och
adjektivändelsen; systemet ser två fel och sänker stabiliteten på två kort,
när det i själva verket sett ett fel två gånger. Det är samma familj som
allt annat i det här dokumentet: systemet får inte berätta något osant för
FSRS. D6 ("meningen vittnar") är den obyggda motsvarigheten — den skulle
kunna känna igen just den situationen i stället för att undvika den.

**Summan tas bara över stretchkort, och det är nödvändigt.** Idag summeras
Σ(1−R) över ALLA sedda kort; ett stödkort tre dagar från förfall bidrar med
0,05, och fyra sådana fyller ett tak på 0,20 utan att ett enda köat kort
prövats. `STRETCHGRÄNS` finns redan och är redan härledd — den ÄR
`desired_retention`, eftersom förfallodagen per definition är den dag R når
retentionsmålet. `Poängsättare.sätt` beräknar redan `stretch`-listan.

**Ett hårt filter måste ha reserv.** Samma lärdom som okändgränsen (C5): som
absolut villkor tömde den sökningen och engelskan tog slut efter en mening.
Mönstret finns i koden — bästa kandidaten under taket, med bästa kandidaten
oavsett som reserv.

---

**3. VAR ANVÄNDARENS RATT BOR — `desired_retention`**

Ingen av de tre kandidaterna i problemtexten gäller budgeten: prestation
mäter FSRS redan per kort (D), ett globalt fast värde finns inte längre kvar
att sätta, och en dagsformsratt hör inte hemma i budgeten.

Rätt ratt är `desired_retention`, och den är konsekvent i båda riktningar:
höjs den till 0,95 kommer korten upp tidigare och varje kort bidrar med 0,05
i stället för 0,10 — fler prövningar, var och en mindre osäker. B2 visade
att samma ratt också styr arbetsbördan: vid fem nya kort om dagen ger 0,85
trettiofem repetitioner per dag efter ett år, 0,95 ger sextiofem. En ratt,
två effekter, konsekventa.

Den är en **kursinställning, inte en dagsforminställning** — att ändra den
dag för dag flyttar alla förfallodatum fram och tillbaka, vilket är precis
det spacing-effekten inte tål. Och den är den enda ratten som går att välja
på mätning: `compute_optimal_retention` (E7).

---

**4. VAD SOM ÄR OLÖST: EXAKT TVÅ TAL**

    korrelationstaket    hur mycket samtidig osäkerhet en mening bär innan
                         felen slutar vara oberoende bevis
    a och b              sekunder per mening och per ord

**Ingetdera går att härleda, och båda går att mäta.**

Taket mäts med nollmodellen (G1), som redan sparar `förväntat` = Σ(1−R) och
`fel` per mening: gruppera historiska meningar på sin Σ_stretch och jämför
utfall mot förutsägelse. Där faktiska fel börjar överstiga förutsagda ligger
korrelationen, och där ligger taket. Tiden mäts med en regression.

Det flyttar båda från G2:s icke-falsifierbara kolumn till den falsifierbara.
Tills mätningarna finns ska de stå som **omätta**, inte som härledda — det
är hela skillnaden mellan det här dokumentets standard och en snygg gissning.

**Varför C2 känns svårare än den är:** logiken är inte knepig. Det som är
obekvämt är att varje ärligt svar slutar i ett tal som bara mätning kan ge.
Mer tänkande tar inte bort det.

**Statusen står kvar som `!` tills koden ändrats.**

### C3 ~ — Vilka meningar är semantiskt möjliga?

Restriktionerna hindrar "stolen äter". De släpper igenom abstrakta subjekt i
slots som vill ha något levande, och liknande fall där ingen regel råkat
skrivas.

**Riktningen framåt** är löpande granskning under användning: varje ställd
mening loggas med facit, och en modell flaggar det som ser konstigt ut.
Eftersom renderingen är regelbaserad är antalet felsorter ändligt — över tid
och över flera användare täcks de in, och renderingen konvergerar. Det är en
rimlig strategi och den skiljer sig från att försöka tänka ut alla regler i
förväg.

**Skilj C3 från C7.** C3 är semantik: meningen är korrekt tyska men
meningslös. C7 är morfologi och syntax: meningen är felaktig tyska. Samma
flaggning fångar båda, men fixen ligger på olika ställen —
`restriktioner.py` respektive renderarna.

#### VERKTYGET BYGGT 2026-08-24 — `ordbok granska-meningar`

Gemensamt för C3, C7 och G4, eftersom de tre är samma arbete sett från olika
håll: någon måste LÄSA vad renderarna producerar.

**Formuläret är hela poängen.** "Den här ser konstig ut" går inte att
sammanställa. Två kolumner gör anmärkningen till arbete:

    feltyp    böjning · ordföljd · kongruens · saknat_led · överflödigt_led
              · lexikalt · semantiskt          — VAD som är fel
    åtgärd    renderare · former · restriktioner · ordbok   — VAR det lagas

De är avsiktligt två frågor och inte en. En felaktig form kan bero på att
renderaren valde fel cell eller på att cellen innehåller fel sträng, och de
lagas på skilda ställen.

**Två korpusar, som svarar på olika frågor.** `--logg` granskar de meningar
som FAKTISKT ställts — `Mening` bär spec och text för var och en, så korpusen
växer av sig själv medan någon övar. Det är den parallella granskningen, och
den krävde ingen ny insamling. `--svep` renderar den designade korpusen (57
namngivna konstruktioner × 7 språk) och täcker utan att någon övat.

**Specen följer med i prompten**, och det är avgörande: utan den kan
granskaren bara säga att en mening låter konstig, med den kan hen säga att
renderaren realiserade fel numerus — alltså skilja ett fel från ett val.

**`--struktur` kräver ingen modell** och returnerar 1 vid fynd, så den går att
köra som ett regressionstest. Fyra kontroller, och den starkaste är att TVÅ
SPECAR SOM RENDERAR IDENTISKT betyder att en distinktion tappats. Den fann
direkt ett äkta fall — och tvingade fram en uppdelning: skiljer sig specarna
bara i KONCEPT delar två koncept lemma (`gen_spela` och `arb_leka` blir båda
`play`, en ordboksfråga och D5 från andra hållet); skiljer sig något
GRAMMATISKT är det renderarens fel.

Japanskan undantas från ordräkningen — den skrivs utan mellanslag, och utan
undantaget var 42 av 43 fynd falska. Samma gräns som rättningen redan drar
(D7).

**Granskningen ändrar aldrig något.** Den skriver en TSV; att tillämpa är ett
separat beslut. Och den vägrar köra inifrån Claude Code, eftersom anropen går
via `claude -p` som subprocess.

**Öppet:** hur en anmärkning blir en ändring. Rapporten sorterar arbetet
(`--sammanställ` grupperar på språk × åtgärd × feltyp) men ingen tillämpar
den automatiskt — och det ska den kanske inte heller.

### C4 ? — Hur väljs den bästa av tusen kandidater?

Åtta vikter:

    täckning       +10     hur många köade kort meningen packar in
    tomgång        −40     straff för en mening som täcker noll kort
    budget          −4     avståndet till Σ(1−R)-målet, kvadratiskt
    nya             −3     osedda kort över NYKVOT = 2
    koncentration   +3     svårigheten ska bäras av FÅ kort
    interferens     −2     två kort ur samma ändelsetabell i samma mening
    upprepning     −1,5    ord som stod i förra meningen ger mindre
    längd         −0,15    långa meningar, eftersom felet blir svårare att hitta

**Ståndpunkten "den som har bäst svårighetsgrad" är ett riktigt svar** — den
säger att budgettermen ska dominera och resten vara skiljedomare. Det är inte
vad som händer idag: `täckning` väger 10 mot budgetens 4, och eftersom
budgetavvikelsen i praktiken är noll (C2) bidrar budgettermen ingenting alls.
Sökningen maximerar alltså i praktiken antalet köade kort per mening.

**Ordningen på arbetet följer av det:** budgeten måste bli mätbar (C2) innan
vikterna kan viktas om, annars flyttas tyngden till en term som inte mäter
något.

**Öppet:** fyra av vikterna har ett falsifierbart prov (se G2), fyra har det
inte. Ingen är trimmad mot verklig användning.

**VAD SOM ÄR SLUMP OCH VAD SOM ÄR BESLUT.** Invändningen "systemet förlitar
sig för mycket på slumpen — oftast borde prioriteringar räcka för att komma
fram till en bestämd övning" är riktig, och den träffade två ställen.

*Det ena var ett verkligt fel.* Målordet lottades per kandidat
(`rng.choice(mål)`), vilket ger varje mål samma FÖRVÄNTADE antal försök — inte
samma antal. Med trettio mål och tusen kandidater är spridningen stor nog att
ett mål kan få hälften så många chanser som ett annat, och vilket kort som
övas härnäst blir därmed ett lotteri. Nu varvas målen i prioritetsordning
(`mål[i % len(mål)]`): varje mål får exakt sin andel, garanterat. Det kostar
ingenting och tar bort variansen helt.

*Det andra var en vy som kastade ett beslut.* Lämnade man passvyn och kom
tillbaka byggdes en ny mening, och den gamla — som valts för att den täckte
något bestämt — kastades obesvarad. Vilket kort som övades blev alltså en
funktion av hur man klickade. Nu överlever den obesvarade uppgiften att vyn
lämnas.

*Var slumpen ska vara kvar:* i HUR meningen byggs — vilket verb, vilka
fyllnadsord, vilken konstruktion — eftersom variation där är själva poängen
med att generera i stället för att lagra meningar. Ordningen är därmed:
prioritet väljer VAD, slumpen föreslår HUR, poängen avgör VILKEN. Det tredje
ledet är fortfarande det som inte är trimmat, och det är vad resten av C4
handlar om.

#### LÖSNING (delvis, 2026-08-23 — inte byggd)

**Halva frågan försvinner med C2.** Fyra av de åtta vikterna är inte vikter
utan delar av en kvot som avgränsningens målfunktion redan bestämmer:

    täckning   →  täljare i återkallelser/sekund
    längd      →  nämnare, mätt i sekunder
    tomgång    →  behövs inte; noll täckta kort ger kvoten noll av sig självt
    budget     →  blir C2:s tak, alltså ett villkor och inte en term

Kvar blir fyra, och de är av olika slag:

    nya            verkställer B2:s inflödeskvot per mening. Hör egentligen
                   hemma i B2 och inte här — den är en takt, inte en smak.
    interferens    två kort ur samma ändelsetabell. Det är ETT SPECIALFALL
                   av C2:s korrelationstak: två snarlika ändelser som båda
                   blir fel är ett förväxlingsfel, inte två oberoende bevis.
                   Frågan är om den ska smältas in i taket eller stå kvar som
                   en egen, billigare detektor.
    koncentration  mäter ANTAL (3 / antal stretchkort) men dess dokumenterade
                   syfte är FÖRDELNING — "en sak jag sträcker mig efter,
                   omgiven av fast mark". Med taket på plats är antalet redan
                   styrt. Ska termen vara kvar bör den mäta det den påstår,
                   exempelvis max(1−R) / Σ(1−R), som är 1,0 när ett kort bär
                   allt och 1/n när massan är jämnt spridd.
    upprepning     variation. Den ENDA av de åtta som ärligt är en smakfråga,
                   och den får stå som en sådan.

**Det ordningen ger:** åtta otrimmade vikter blir en mätbar kvot, ett mätbart
tak, en takt som hör hemma någon annanstans, och två termer att avgöra. Det
som återstår att trimma mot verklig användning är alltså två tal, inte åtta.

**Öppet:** interferensens plats (egen term eller del av taket), och om
koncentrationen ska formuleras om eller tas bort.

### C5 ✓ — Hur mycket okänt tål en mening?

**Svaret är noll, och det följer av C2/D3 och inte av en avvägning.**
Ordkort införs i glosläget. En mening kan alltså inte längre lära ut ett ord,
bara använda det — och ett ord som står i en mening utan att ha införts är
inte pedagogik utan en oanmäld kostnad: kortet blir sett, betygsatt och
schemalagt utanför dagsplanens tak.

**"Okänd" betyder inte förfallen.** Ett okänt ord är ett `ord`-kort med
`sedd IS NULL` vars koncept dessutom inte har lästs i glosläget. Det handlar
alltså om ord användaren aldrig har mött — inte om ord hen har glömt. Ett
förfallet kort är känt men svagt, och det är själva poängen med att öva det.

**Varför det HÖGST ETT som stod här var fel.** Argumentet var riktigt i sig —
ett okänt ord i en mening man annars förstår går att sluta sig till, två är en
ekvation med två obekanta — men det beskrev en värld där meningen fick införa
ord. Den världen upphörde med glosläget. Kvoten blev då inte en pedagogisk
avvägning utan en glugg: den enda kvarvarande vägen in för ett ord ingen
introducerat.

Gränsen är fortfarande en PREFERENS med reserv och inte ett hårt villkor: som
hårt filter gav den `None` med jämna mellanrum och engelskan tog slut efter en
mening. Skillnaden är att reserven nu är ett UNDANTAG som gäller hela meningen
— vid kallstart, när ingen ren mening finns — i stället för ett ord i taget.

#### EN FJÄRDE VÄG IN, 2026-08-25 — och den öppnades av en rättelse

`Tu existes.` införde `tu` en dag då drillen gett fyra ord, och `tu` var inget
av dem. Vägen var ny och gick genom undantaget självt.

Sökningen har sedan A7 punkt 2 TRE tiers: `bäst` (noll okända ord, ingen
upprepning), `reserv` (okända ord men ingen upprepning) och `nödfall`
(ordagrann upprepning). Undantagsvillkoret prövade bara de två första. När
ordförrådet är mindre än meningsminnet är djupt hamnar varje ren kandidat i
`nödfall` — fyra ord ger fyra meningar, minnet håller tre — och sökningen såg
då TOM ut. Begränsningen släpptes, och `tu` kom in.

**En ordagrann upprepning är sämre pedagogik men ÄRLIG.** Att i stället ta in
ett oanmält ord bryter mot både den här posten och dagsplanens tak, och ger
dessutom en uppgift som inte går att lösa. Upprepningen vinner därför över
undantaget, och undantaget är kvar för det läge det byggdes för: när
ingenting alls gick att bygga. Vid äkta kallstart är minnet tomt, så inget
nödfall finns, och undantaget fungerar precis som förut.

Mätt efter rättelsen, med Julius exakta läge — fyra drillade ord:

    Nous existons. · J'ai. · J'existe. · Nous avons. → "inget mer går att bygga"
    ordkort som passet införde: inga

#### LÖSNING (2026-08-24) — tre vägar in, alla stängda

Felet syntes i bruk så här: sex ord introducerades i drillen 14:19, och passet
gav sedan `Un frère existe.` Loggen visar ordkortet för `artikel_obestamd`
betygsatt 14:21:41 med mening 130 — infört av meningen. I andra körningar var
det `coûter` och `avoir`. Reproducerat: tio meningar i rad införde vart och ett
ett ord som inte var något av dagens — `homme`, `fille`, `famille`,
`frère cadet`.

Det såg ut som ett fel men var tre, som var och en ensam räckte:

**1. Målordet, i `Schemaläggare.osedda`.** `uteslut=("ord",)` uteslöt ordKORTET
men inte ordet. Egenskaps- och stamkorten för samma koncept kom in i kön, blev
MÅLORD, och samplaren byggde meningen kring dem. Målordet går förbi
`Samplare.begränsa`, som bara styr fyllnaden — så spärren såg det aldrig.

*Rättat med en ordningsregel: ett kort får introduceras först när ordet det
hör till är introducerat.* Ett stamkort för ett okänt ord är inte en
böjningsfråga utan en glosfråga i förklädnad.

**2. Nykvoten, i `Generator._sök`.** `okända <= 1`, alltså det här problemets
gamla svar. Den släppte in STRUKTURORDEN — artikeln i `Un frère existe.` väljs
aldrig av `_välj` utan följer av `Bestämdhet.OBESTÄMD`, så `begränsa` ser den
inte. *Rättat till `okända == 0`.*

**3. `schemalagt`, i samma fråga.** Flaggan betyder "möts för ofta för att
spacing ska betyda något" (kort.sql) — inte "kan redan". Som grind på
INTRODUKTIONEN gjorde den vanliga ord till ord som aldrig lärdes ut, och lät
meningarna presentera dem ändå. De tre franska ordkort som hade
`schemalagt = 0` var exakt de tre som dök upp oannonserade: `un` (exponering
0,846), `avoir` (0,354), `coûter` (0,066). Det var inte ett sammanträffande
utan samma rad kod sedd från andra hållet.

*Rättat genom att skilja på att INFÖRA och att SCHEMALÄGGA.* Frågor om `sedd`
använder `INFÖRBAR = (schemalagt = 1 OR typ = 'ord')`; frågor om `förfaller`
behåller `schemalagt = 1`. Ett ord införs en gång oavsett exponering, och
repeteras sedan bara om spacing betyder något för det.

**Provet: `ordbok/verktyg/introduktionsprov.py`.** Fyra invarianter — kön,
drillen, meningen, tjänsten — var och en med sitt sabotage. Att pröva alla tre
fixarna genom MENINGEN gick inte: var och en räcker för att stoppa läckan, så
att ta bort en åt gången syns inte i utfallet. Det är djupförsvar, men ett prov
som bara kan se den yttersta av dem bevisar ingenting om de andra två. Därför
mäts varje fix där den arbetar, och tjänstevägen — som är den enda som ser
sömmen mellan motor och skärm, se G6 — fälls av väg 2 och 3 tillsammans,
alltså av det tillstånd som faktiskt inträffade.

Mätt efter rättelsen, hela vägen genom `Övningstjänst` med fel svar på varje
mening så att passkön hålls full: femton meningar, noll ordkort införda utanför
drillen.

**Den bättre frågan är när ett ord är redo att sättas in i en mening.** Idag
är svaret "så snart det lästs en gång i glosläget" — en enda exponering. Det
är svagt, och kandidaterna är:

- efter första lyckade återkallelsen (kortet har en historik)
- när R passerat någon nivå
- när kortet lämnat passkön (se F4)

**Meningens storlek är en egen fråga** och behandlas i F3.

### C5b ! — Att ge upp är ett svar, och det måste tas emot

*(Upptäckt 2026-08-26. Systerpost till C5: den handlar om vilka ord som får
stå i meningen, den här om vad som händer när INGET ord får det.)*

C5:s lösning gav `Samplare._välj` en regel som är riktig: **ger upp hellre än
faller tillbaka.** Tömde begränsningen till kända ord en slot returnerar den
`None` i stället för att smyga in ett osett ord. Reservutgången flyttades upp
till sökningens nivå, där undantaget blir ett beslut om hela meningen.

**Men `None` är ett svar som måste hanteras, och tolv av fjorton
anropsställen gjorde det inte.** De byggde specen ändå, med ett hål i.

Mätt över 3 000 kandidater per språk och nivå, med begränsat ordförråd:

    nivå  5   attribut          `Attribut(None)`             4–24 %
    nivå  5   objekt            `Nominalfras(None)`          0–10 %
    nivå  8   adverbial         naket `None` i tupeln       ~15 %
    nivå 15   prepositionsfras  `Prepositionsfras(None, …)` ~20 %
    nivå 20   bisatsens verb    `self.o.verb[None]`          KeyError

**Skadan är av två slag, och båda är dyra på var sitt sätt.**

*Tyst.* `Attribut(None)` och `Nominalfras(None)` ger `RenderingsFel`, som
`Generator._rendera` fångar och svarar `None` på. Kandidaten kastas alltså
utan att något räknar det. På engelskans nivå 5 var det 27 % av sökningen —
en fjärdedel av arbetet bortkastat av en orsak ingen mätning kunde se, och
sökningen drogs samtidigt bort från just de konstruktioner nivån nyss öppnat.

*Hård.* Ett naket `None` i `adverbial` träffar renderarens `else`-gren, som
läser `.preposition`. Det ger `AttributeError` — och den ligger UTANFÖR de
undantag `_rendera` fångar (`RenderingsFel, KeyError, ValueError`). Alltså en
krasch rakt ut ur `föreslå`, upp genom `uppgift`, till skärmen. Mätt föll
**40 av 40** anrop för de, en och fr på nivå 21.

**VARFÖR DET INTE HADE SYNTS, och varför det ändå hör hemma här som `!`.**
Konstruktionerna låses upp med nivån, och kurserna stod på nivå 1 och 4 —
alltså ett enda steg under den första fällan. Felet var osynligt i drift och
hundraprocentigt i varje verktyg som öppnar hela stegen. Tyskan hade träffat
`Attribut(None)` första dagen nivå 5 öppnades, och kraschat på nivå 8.

**Det är samma form som A3 och G5 pekar på, sedd i koden i stället för i
datan:** ett villkor som är sant på ett ställe och oläst på tolv andra. Och
det är en trolig förklaring till en del av de "konstiga buggar som kommer
tillbaka" — utfallet beror på ordförrådets storlek och kursens nivå, så
samma kod ger olika symptom olika dagar.

#### LÖSNING — BYGGD 2026-08-26

Regeln är att KONSTRUKTIONEN faller, inte att den byggs med ett hål, och
vilken sorts fall beror på slotten:

    utsmyckning     attribut, adverbial, prepositionsfras, possessiv,
                    genitiv — HOPPAS ÖVER. Meningen är hel utan den.
    obligatorisk    subjekt, objekt, io, komplement, predikativ, bisatsens
                    verb — KANDIDATEN KASTAS, samma svar som verbslotten
                    redan gav.

Att skilja på dem är inte en detalj. En utsmyckning som kastar hela
kandidaten skulle tömma sökningen vid kallstart — precis det fel
okändgränsen redan gjort en gång (C5) — och en obligatorisk slot som hoppas
över ger en mening utan subjekt.

Mätt efter rättelsen, samma svep: **noll defekta specar** på samtliga nivåer
för de, en och fr, och **noll undantag** ur 40 `föreslå`-anrop per språk på
nivå 21 där alla 40 föll förut.

**Provet:** `ordbok/verktyg/samplarprov.py`, två invarianter — *varje spec är
hel* och *`föreslå` kastar aldrig* — med falsifiering.

*Och sabotaget fick skrivas om en gång, vilket är värt att notera.* Det
uppenbara var att göra `_välj` mer benägen att ge upp. Det blev STUMT: med
grindarna på plats hoppar koden över konstruktionen precis som den ska, och
görs `_välj` snål på allt kastas varje kandidat redan på `verb is None`, så
ingen spec byggs och provet blir grönt av fel skäl. Sabotaget injicerar
därför de fyra historiska hålformerna i den färdiga specen. Vad det bevisar
är avgränsat — att kontrollen KAN falla — men det är just det som kan rutta.

### C6 ~ — Vad kan specen överhuvudtaget uttrycka?

`Mening` är den mellanform som beskriver VAD en mening är — tempus, person,
numerus, modus, satstyp, bestämdhet — innan något språk gjort text av den.
Renderarna översätter spec till text. Finns det ingen väg att BE om en form
via specen kan formen aldrig stå i en mening, och dess kort kan aldrig mötas.

Mätt med `ordbok/verktyg/nåbarhet.py`, som instrumenterar `Uppslag.form` och
sveper hela korsprodukten av vad `Mening` kan uttrycka:

    sv  4 728 / 4 988   95 %      de  19 242 / 23 494   82 %
    en  2 034 / 2 293   89 %      it   7 877 / 10 246   77 %
    ja  1 472 / 2 498   59 %      fr   6 650 /  9 070   73 %
                                  es   7 114 / 10 608   67 %

Japanskans 59 % och spanskans 67 % är alltså tak på vad de kurserna någonsin
kan pröva. De onådda blocken är inte samma block i olika språk, så det finns
ingen gemensam fix.

**Öppet:** om korten för onåbara celler ska finnas kvar (de räknas in i
upplåsningen — se A3, samma fråga).

### C7 ! — Producerar renderarna korrekt språk?

Ett känt fel kvar:

- **Tyskans fraslexem får fel deklination.** `älterer Bruder` böjs efter fel
  paradigm; renderaren vägrar numera kombinationen i stället för att svara
  fel, vilket är ärligare men inte löst.

#### DE REFLEXIVA VERBEN — LÖST I FEM SPRÅK 2026-08-26

Posten sade "franskans reflexiva verb tappar sitt pronomen". Det stämde, men
det var en femtedel av felet: **samma fel fanns i spanskan, italienskan,
tyskan och svenskan**, i tre olika former.

    fr/es/it   pronomenet i LEMMAT, formerna nakna
               `se réveiller` → `réveille`      gav "Je réveille"
    de         samma sak
               `sich beeilen` → `beeilt`        gav "Wir beeilen"
    sv         pronomenet INBAKAT I FORMEN
               `skynda sig` → `skyndar sig`     gav "Vi skyndar sig"

Svenskans variant är värst, för den ser rätt ut. `sig` är korrekt i tredje
person och fel i alla andra — jag skyndar MIG, vi skyndar OSS — så felet
syns bara på de subjekt man råkar pröva. Det är samma genväg som en gång gav
224 franska verbformer med subjektspronomenet inbakat: saknas mekanismen
skriver någon in resultatet i datan.

**Rättningen läser reflexiviteten ur LEMMAT och bygger pronomenet.** Det går
inte att kopiera lemmats `se`/`sich`/`sig` rakt av, eftersom pronomenet
kongruerar med subjektet. Formerna i `pronomen_1sg` med flera fanns redan —
`me/te/se/nous/vous`, `mich/dich/sich/uns/euch`, `mig/dig/sig/oss/er` — så
ingenting behövde hittas på. Bara tredje person har ett eget reflexivt
pronomen; första och andra lånar det vanliga objektsklitikat.

Tre saker föll ut gratis när pronomenet väl fanns, och de är kvittot på att
det byggdes på rätt ställe:

    Elle s'est réveillée.        elision + participkongruens med subjektet
    Sie ruht sich nicht aus.     partikelverb + Mittelfeld + negation
    Nous ne nous sommes pas      être-hjälpverbet, negationen runt om
      inquiétés.

Fyra saker krävde egna beslut:

**Svenskans objektsskifte.** "Jag skyndar mig inte" men "vi har inte oroat
oss" — pronomenet flyttar vänster om satsadverbialet bara när huvudverbet
självt har flyttat. Holmbergs generalisering, och den syns bara när
verbfrasen har fler än en del, vilket är skälet att den gick att missa i
presens. Första försöket gav "Vi har oss oroat".

**Tyskans dativreflexiv.** `sich vorstellen` tar dativ — "ich stelle mir vor"
— därför att tyskan inte tillåter två ackusativ och verbet redan har ett
ackusativobjekt. De övriga sex tar ackusativ. **Regeln går inte att härleda
ur mönstren**: `kog_minnas` och `kog_föreställa` har identiska MönsterKrav-
rader och ändå olika kasus. Kasusen hör alltså hemma som en `reflexiv`-slot
i MönsterKrav, bredvid objekt och io. Den slotten finns inte i schemats
CHECK, och att bygga den för ETT verb är oproportionerligt — så listan står
som en sluten lexikal konstant i `de.py`, med samma motivering som franskans
`ELIDERAR`, och ska flytta när ordboken gör den längre.

**Jakande imperativ vägras.** "Réveille-toi", "¡despiértate!", "svegliati!"
är enklitiska OCH byter form. Det är samma vägran som redan gällde
objektsklitika, och den nekade imperativen fungerar.

**Italienskans infinitivceller är oeniga.** `svegliare` står naken medan
`sbrigarsi` och `sedersi` bär klitikat. `infinitivstam` hanterar båda
formerna, men det är att absorbera ett datafel, inte att lösa det — cellerna
borde vara enhetliga. Står kvar som `?`.

#### OCH REGRESSIONSNÄTET BEVISADE SIN EGEN SVAGHET (2026-08-26)

När pronomenet byggdes gav korpusen exakt fyra diffar:

    fr  Elle souvient que …      →  Elle se souvient que …
    de  Sie erinnert, dass …     →  Sie erinnert sich, dass …

**Felet stod alltså som FACIT i bilden.** Det är precis vad G4 säger att
nätet inte kan fånga — förändringar, inte fel som redan fanns när korpusen
frystes — och här syns kostnaden i klartext. Korpusen täckte reflexiva verb
bara av en slump, genom `se souvenir` och `sich erinnern` i två bisatsrader,
och frös därför deras fel.

Korpusen har därför fått **tretton reflexiva konstruktioner**, valda för att
pronomenet realiseras olika i var och en: eget ord före verbet, elision,
kongruens, participkongruens, enklis på infinitiven, objektsskifte. Tre av
dem använder `käns_oroa`, som är reflexivt i alla fem språk som har
konstruktionen, eftersom de första tio byggde på verb som bara romanskan
böjer reflexivt och därmed lämnade svenskan och tyskan otäckta.

**Omfattning i drift.** 23 av franskans 1 153 kort byggde på de tretton
reflexiva verben, och 15 av dem hade redan lärts ut i fjortondagarsleken —
alltså med fel facit. Verben är `stanna, minnas, oroa, vakna, vila, sitta,
stå, öva, undra, gifta sig, skynda, koncentrera`, och flera av dem är bland
de vanligaste som finns.

Regressionsnätets 399 frysta meningar täcker ingendera — se G4: nätet fångar
FÖRÄNDRINGAR, inte fel som redan fanns när korpusen frystes.

Det kommer med säkerhet finnas fler. Strategin (löpande granskning, se C3 och
G5) är rätt: antalet felsorter är ändligt eftersom renderingen är regelbaserad,
och de fångas in över tid. Men "det blir bättre över tid" är inte en mätning,
och tills granskningen finns är antalet okända fel okänt.

### C8 ? — Ska uppgiften alltid vara översättning?

Idag: käll- → målspråk, skriv hela meningen. Det prövar produktion men aldrig
igenkänning, lyssning eller lucktext.

**Efter C2 är formvalet en räknefråga och inte en smakfråga.** Målfunktionen
är återkallelser per sekund. En lucktext ger EN återkallelse på ett par
sekunder och dessutom perfekt attribution — det finns bara ett kort som kan
ha brustit. En hel mening ger två till tre på tjugo sekunder, men prövar
SAMMANSÄTTNINGEN: att välja rätt kasus kräver att man visste att
prepositionen styr det, och en lucka ger den ramen gratis.

Vilken form som vinner är alltså inte en åsikt utan en kvot, och båda leden
är mätbara så snart tiden loggas. Sannolikt är svaret en blandning — lucktext
för billig repetition av enskilda former, full produktion för sammansättningen
— men vilken blandning avgörs av mätningen.

(Lyssning ligger utanför avgränsningen: det är erfarenhet, inte teori.)

**Riktningen är dubbla kort: ett för att översätta TILL språket och ett för
att översätta FRÅN det.** Det är rätt modell — igenkänning och produktion är
olika minnen, och att kunna läsa `Hund` säger inte att man kan producera det.
Tre konsekvenser som måste räknas med:

1. **Kortleken fördubblas.** Tyskan går från 1 112 till 2 224 kort, och därmed
   fördubblas belastningen för samma antal minuter per dag. Det påverkar B2,
   F1 och hela upplåsningsräkningen.
2. **Riktningarna är inte symmetriska när ett koncept har flera varianter.**
   `mamma` → engelska har inget entydigt svar (`mom` eller `mother`), medan
   `mom` → svenska har det. Se D5 — och det är där dubbelriktningen faktiskt
   LÖSER något: igenkänningsriktningen är den enda som kan pröva en enskild
   variant.
3. **Attributionsmaskineriet fungerar bara i produktionsriktningen.** Skriver
   användaren svenska finns inga svenska kort att skylla på, och en diff mot
   en svensk rendering säger ingenting om tysk kunskap. Igenkänning kan alltså
   bara betygsättas grovt — hela meningen rätt eller fel, eller per koncept.
   Stam/ändelse-uppdelningen (D1) är produktionsriktningens verktyg och följer
   inte med.

**Öppet:** om igenkänningskorten ska vara egna rader i `Kort` (med en
riktningskolumn) eller ett eget lager; och hur grov betygsättning i den ena
riktningen ska samsas med fin i den andra utan att den grova förstör den fina.

---

## D. Vad blev rätt och fel? — rättningen

### D1 ~ — Vilket kort fällde meningen?

Skulden avgörs av samma stamuppdelning som definierar korten. `_skyll` går en
stege, och varje pinne kan vara fel på sitt eget sätt:

| # | Villkor | Skylls på | Kan vara fel när |
|---|---|---|---|
| −1 | svaret blir facit om renderarens SANDHI tillämpas | — | ingen; formerna visades, elisionen har inget kort |
| 0 | ingen cell matchar, MEN försöket bär konceptets stam | `system` | den längsta matchande stammen är ett annat ords (3 % fr, 6 % de, 0 % en) |
| 1 | ingen cell matchar och stammen finns inte heller | `ord` | ordet flyttades i stället för att böjas fel (A7); ordboken saknar en giltig form |
| 2 | formen hade varit rätt för ett annat genus | `egenskap` | flera celler matchar → faller igenom |
| 3 | ordet har ett `form`-kort (ingen härledbar stam) | `form` | — |
| 4 | rätt stam, fel ändelse | `system` | stammen råkar vara prefix till fel form |
| 5 | fel stam | `stam` | — |
| 6 | bara ett kort finns i ledet | det kortet | — |
| 7 | **inget av ovanstående** | **det svagaste kortet** | alltid osäkert |

#### DIFFEN GÅR MOT DE OSAMMANSMÄLTA ORDEN (2026-08-25)

Uppslaget är per FORM, diffen per TOKEN, och sandhi slår ihop `je` + `existe`
till `j'existe`. Då finns ingen tokengräns mellan pronomenet och verbet, och
stegen ovan får aldrig se `exister` mot `existe` — bara `je` mot `j'existe`.
Mätt fall: `Je exister` gav ändelsen UNDANHÅLLEN när den skulle ha FALLIT.
Böjningsfelet försvann bakom elisionen.

Renderarna lämnar därför ifrån sig sin ordlista före sandhi, och svarets
tokens delas vid samma gränser — prefixet hämtas ur renderarens egen sandhi,
inte ur en egen tabell som skulle kunna glida isär från den.

    rätt             J'apprends.      ✓7
    bara elision     je apprends      ✓7   "orden ska smälta samman"
    bara böjning     J'apprender.     ✓6 ✗1   ändelsen faller
    båda             je apprender     ✓6 ✗1   BÅDA rapporteras

**Bara när sandhi faktiskt SLÅR IHOP.** Engelskans `a` → `an` byter ut ett
ord utan att röra antalet, och där är den osammansmälta listan direkt fel:
den innehåller `a` medan facit har `an`, så varje korrekt skrivet `an` hade
sett ut som ett fel. Villkoret är antalet ord, inte innehållet.

#### ETT FÄLLT KORT SKYDDAR ALLT BAKOM SIN FORM (2026-08-25)

A4:s regel — böjning förutsätter ordet — täckte bara `stam` och `form`.
ÄNDELSEN är ett `system`-kort och hade ingen koppling till ordet att skyddas
genom. Mätt: `nous coüter` för `Vous coûtez.` fällde ordkortet som det skulle
och gav GOOD åt ändelsen `ez`, i ett svar som var en infinitiv utan `ez` i
sig.

Samma sak när STAMMEN faller: `Männern` för `Mann` är stam `Männ` plus
ändelse `ern` där `Mann` plus `∅` väntades — hela formen var fel, och
ändelsen visades inte heller. 17 av 420 tyska prövningar.

**Åt andra hållet gäller det inte.** Faller ÄNDELSEN har stammen per
definition visats — det är så steget kom fram till att det var ändelsen — och
att undanhålla den vore att kasta bevis man har.

Pinne 7 är den som inte är en mätning. Argumentet för den är att
felattribution självläker: skyller systemet fel klarar det kortet sin extra
repetition och det verkligt svaga förblir svagt. Argumentet är rimligt men
det bryter mot dokumentets egen måttstock — det skriver in en falsk mätning i
loggen — och kostnaden är inte symmetrisk. Mätt: att fälla ett friskt kort tar
S från 10,96 till 1,54, alltså 86 % av dess stabilitet. Ett "extra
repetition"-fel är alltså inte litet.

**Det som saknas för att kunna avgöra hur illa det är:** `Repetition` sparar
inte VILKEN pinne som fällde kortet. Stegens träffsäkerhet går därför inte att
mäta ur loggen, och `osäker`-flaggan går inte att följa upp. Det är en liten
kolumn och den skulle göra hela D-området mätbart.

### D2 ✓ — Cellen är ofta en funktion av ett ANNAT kort

Detta är A5 sett från rättningens håll.

När renderaren ska sätta artikeln framför `Kind` slår den upp `Kind`s genus,
får neutrum, och begär därför cellen `n_nom`. Cellvalet är alltså en FUNKTION
av ett annat kort — genuskortet — och inte ett fristående beslut.

Skriver användaren `die` i stället för `das` är `die` inte en påhittad form.
Det är den korrekta formen för `f_nom`. Alltså behärskar användaren
artikelparadigmet; hen tror bara att `Kind` är femininum. Att skylla på
artikelns formkort vore att mäta fel kunskap, och just det kortet är
dessutom ett av dem som möts i nästan varje mening och därför nästan säkert
sitter.

Regeln: **skiljer sig den skrivna formens cell från den begärda i exakt en
koordinat, och är den koordinaten en lexikal egenskap, är det egenskapen som
brast.**

### D3 ✓ — Vad gör man när skulden inte går att avgöra?

Två olika saker händer idag, och bara den ena är den som posten beskrev.

**Undanhållandet.** Går felet inte att knyta till något kort alls tas ALLA
kort som kan ha burit den formen ur betygsättningen. De står inte kvar som
rätt. Det är riktigt, och det åtgärdade ett mätt fall där facit var
`A cloud lies down.`, användaren skrev `A cloud lie down.`, och systemet
skickade Good till båda korten för verbet som just blivit fel.

**Defekten som genomgången hittade.** Ett undanhållet kort får ingen
`Repetition`-rad. Regeln som skyddar mot dubbla betyg samma dygn (`_redan_idag`,
se E2) läser just `Repetition`-rader — alltså ser den inte det undanhållna
kortet alls. Kortet behåller dessutom sitt gamla förfallodatum, som ligger i
det förflutna, så det står kvar i `förfallna` och plockas gärna till nästa
mening. Under tiden har användaren sett facit.

Mätt vad det kostar. Kortet har S = 10,96, D = 2,11 och är förfallet:

    undanhållet, sedan Good i nästa mening   S → 46,28   nästa om 46 dygn
    (identiskt med att aldrig ha varit i tvivel)

    jämför: Again, sedan Good i passkön      S →  1,57   nästa om  2 dygn

Skillnaden är alltså inte marginell — det är hela poängen med att undanhålla
som går förlorad i nästa mening. Systemet får veta att kortet sitter, tjugo
sekunder efter att det visade svaret.

**Detta är samma fel som E5 och F4.** Se principen överst i dokumentet: ett
kort med historik får inte betygsättas i samma pass som facit visades. Det
undanhållna kortet borde skjutas till i morgon, inte lämnas förfallet idag.

#### LÖSNING — BYGGD 2026-08-23 (utom `visad`)

**Lösningen stänger D3 och E5. F4:s mätfelsdel också; dess andra halva står kvar.** Alla tre är
samma sak — ett kort med historik vars svar användaren just fått se.

**Anki har redan löst det, och av exakt samma skäl.** Funktionen heter
*bury*: syskonkort läggs undan till nästa dag, eftersom att repetera ett
syskon strax efter avslöjar svaret. Vårt fall är detsamma med ett steg
kortare — kortets eget svar stod nyss på skärmen.

**Två saker ska ske, och de behövs båda.**

    1.  KORTET SKJUTS UPP.  förfaller = nästa dygnsgräns.
    2.  ATT DET VISATS SPARAS.  En rad utan betyg.

*Steg 1 rör inte minnesmodellen.* Bara `förfaller` flyttas — inte `sedd`,
inte S, inte D. Och eftersom FSRS räknar R ur `sedd` och inte ur `förfaller`
är kortets retention **oförändrad**: det kommer tillbaka i morgon med sin
sanna svaghet. Uppskjutningen är alltså inte en repetition som saknar betyg,
den är ingen repetition alls.

Steg 1 löser också två andra saker. Kortet lämnar `förfallna`, så dagen kan
bli klar (B5) — det är sannolikt förklaringen till att extraövningen kunde
fastna på återförsök som aldrig löste sig. Och det slutar plockas till nya
meningar samma pass.

*Steg 2 behövs ändå*, eftersom ett kort kan hamna i en mening OAVSIKTLIGT —
en mening vald för ett annat kort kan råka innehålla det, och då skulle det
betygsättas trots uppskjutningen (E4). Regeln som redan finns, `_redan_idag`,
läser `Repetition`-rader från dagens början. En rad **utan betyg** skulle
alltså skydda kortet utan att en enda rad kod i den regeln ändras.

Och asymmetrin faller ut rätt av sig själv: `graderade` fångar raden, så ett
RÄTT senare samma dag hoppas över; `fällda` filtrerar på betyg = FEL, så ett
FEL får fortfarande registreras. Det är korrekt — att inte kunna något vars
svar man nyss sett är information, tvärtemot.

**Vad det kräver i schemat.** `Repetition.betyg` är idag
`NOT NULL CHECK (betyg IN (1,2,3,4))`. Villkoret måste släppas och en
`skäl`-kolumn läggas till (`undanhållen`, `skyddad`, `visad`). Det gör
tabellen till en logg över HÄNDELSER i stället för bara betyg — och det ger
samtidigt det D1 saknar: hur ofta undanhållandet slår till går då att mäta.

**De tre fallen, och det fjärde som inte är ett fall:**

    D3  skulden gick inte att avgöra          skäl = undanhållen
    E5  ordkortet fallerade, formen prövades   skäl = skyddad
        aldrig
    F4  lektionen eller glosläget visade ett   skäl = visad
        kort som redan har historik
    —   NYA kort som visas för första gången   INGET — undantagna

Undantaget för nya kort är inte en eftergift. Deras första möte ÄR
introduktionen, och FSRS begynnelsestabilitet (2,307 för Good, alltså två
dygn) är byggd för precis det. Att skjuta upp dem vore att aldrig kunna
införa något.

**En bieffekt som ska hanteras samtidigt.** Kön sorterar på `förfaller`, och
docstringen kallar det "svagast först". Det stämmer inte, och uppskjutningen
gör felet större. R beror på FÖRHÅLLANDET mellan försening och intervall,
inte på antalet dagar:

    S =   2, intervall   2 d,  1 d försenat  →  R = 0,870
    S = 100, intervall 100 d, 30 d försenat  →  R = 0,881

Kortet som är EN dag försenat är alltså svagare än det som är trettio dagar
försenat. Sorteringen på datum gynnar systematiskt kort med långa intervall.
Rätt sortering är **stigande R** — den mäter det ordet "svagast" betyder, och
den gör dessutom uppskjutningen harmlös, eftersom ett uppskjutet kort behåller
sin plats i ordningen när ordningen inte längre bygger på datumet.

**BYGGT.** `Schemaläggare.skjut_upp(kort_id, skäl)`, anropad från
`registrera_mening` för undanhållna (`rörda − utfall`) och skyddade kort.
`Repetition.betyg` är nu nullbar med en `skäl`-kolumn och ett villkor som
kräver exakt ett av dem — raden är ANTINGEN en bedömning ELLER en anteckning
om att ingen gjordes. Migreringen ligger i
`ordbok/migrationer/kort_betyglos_rad.sql`.

`_redan_idag` ändrades inte med en rad, precis som förutsagt: `graderade`
fångar den betyglösa raden, `fällda` filtrerar på betyg = FEL och släpper
därför igenom ett fel.

Mätt på tyskans kö, kortet undanhålls och klaras sedan i NÄSTA mening samma
pass:

    utan uppskjutning (gamla beteendet)   S 0,101 -> 1,081   3 bedömningar
    med uppskjutning                      S 0,101 -> 0,101   2 bedömningar

Och kortet självt är orört: stabilitet, svårighet och `sedd` står kvar, så R
är exakt oförändrad (0,5205 före och efter). Bara `förfaller` flyttades.

E5 verifierad i samma körning: ordkortet fick Again (S 2,307 → 0,733,
betyg = 1) medan formkortet fick `skäl = 'skyddad'`, oförändrad stabilitet
och en ny förfallodag imorgon.

**KÖORDNINGEN BYTTES SAMTIDIGT**, och det var nödvändigt. `förfallna`
sorterade på `förfaller` medan docstringen påstod "svagast först". Efter
uppskjutningen hade ett kort som varit försenat i tre veckor tappat hela sin
plats i kön. Nu sorteras det på `(förfluten / stabilitet) DESC`, vilket är
samma ordning som stigande R utan att FSRS-formeln behöver in i SQL — och
`sedd` rörs inte av uppskjutningen, så platsen behålls.

**`visad` är definierad men inte inkopplad.** Glosläget visar bara OSEDDA
kort, och lektionen introducerar nya ord, så fallet uppstår inte där. Den
väg som återstår att ta ställning till är ordboksvyn: ska det bura ett kort
att slå upp ordet? Det är en designfråga och inte en bugg.

**Vad lösningen inte gör.** Den avgör fortfarande inte skulden — det är D1:s
och D6:s fråga. Den ser bara till att systemet inte ersätter en saknad mätning
med en falsk.

**En observation, inte ett fel:** det skyddade formkortet skjuts till imorgon
medan dess ordkort schemaläggs av FSRS, ibland något senare. Formen kan
alltså komma upp strax före ordet. Det ger ingen felmätning — går ordet fel
igen skyddas formen igen — men det är en aning slösaktigt.

### D4 ✓ — Flerordiga former

Tyskans partikelverb delar på sig: `zuhören` blir `Ich höre zu` med partikeln
sist i satsen. Diffen är ordvis, så `zu` ser ut som ett eget ord — och ett ord
som inget kort känns vid. Utan åtgärd blir `zu` ett okänt ord OCH `höre` en
form som inte matchar `zuhören`, alltså två fel för noll fel.

`_flerordiga` samlar de flerordiga former som faktiskt slogs upp i den här
meningen, `_segmentera` och `_foga_samman` limmar ihop dem till EN token före
diffen — även när delarna inte står intill varandra. Efter det är `höre … zu`
ett ord för diffen, precis som det är ett kunskapsmoment.

Samma maskineri bär `lies down` och andra flerordiga lexem. Vad det INTE
avgör är hur kunskapen ska modelleras — se A6.

### D5 ? — Användaren skrev något annat som också är rätt

Det dyraste felet i systemet: ett korrekt svar registrerat som fel sänker
stabiliteten på friska kort (mätt: −86 %). Det är den enda feltypen som
FÖRDÄRVAR data i stället för att bara sakna den. Självrättning finns
(`hela` = "mitt svar var också rätt", eller per kort), och överprövningar
bokförs som `Repetition.självrättad = 1` så att de blir mätbara — överprövas
en viss anmärkningstyp ofta är det rättningen som har fel. Men systemet
upptäcker aldrig fallet självt.

**Variantproblemet, som är det svåra fallet.** `mamma` är ett koncept. På
engelska svarar både `mom` och `mother` mot det, som två `variant`-rader på
samma koncept. Systemet renderar en av dem som facit. Då gäller allt detta
samtidigt:

1. Skriver användaren den andra varianten är svaret **korrekt** men markeras
   fel.
2. Accepteras svaret — vilket kort tränades? De är två olika `ord`-kort. Bara
   ett kan få betyg, och det systemet valde var inte det användaren skrev.
3. Systemet BÖR inte ha en preferens mellan varianterna: båda hör till samma
   koncept, och konceptmodellen är hela grunden för att sju språk kan dela
   ordbok.
4. Skriver användaren något FEL vet vi inte vilken variant hen siktade på, och
   därmed inte vilket kort som brast.

**En kandidatlösning som faller ut ur C8.** I igenkänningsriktningen
(`mom` → `mamma`) finns ett entydigt svar, och den prövar exakt en variant.
Variantkort skulle alltså kunna vara enkelriktade: produktionsriktningen
prövar KONCEPTET (och accepterar varje variant), igenkänningsriktningen prövar
VARIANTEN. Det är en verklig upplösning av knuten, men den kräver att C8
avgörs först, och den bryter symmetrin "samma kort åt båda hållen".

**Mätt hur stort problemet är idag:** koncept med flera varianter — de 2,
es 6, fr 1, ja 8, sv 5, en 0, it 0. Alltså litet nu, men det är ett resultat
av att ordlistorna är handskrivna och sparsamma (I5), inte av att språken är
sådana. Växer ordbanken växer detta snabbt.

### D5b ? — Uppgiften kan ha flera riktiga svar

*(Systrapost till D5, som handlar om SVARET. Den här handlar om FRÅGAN.)*

Källspråkets mening är inte alltid entydig. Engelskans `you` är både `du` och
`ni`; svenskans `de` är både `de` och `dem` i tal. Står det `You cost.` och
målspråket är franska går det inte att veta om `tu` eller `vous` väntas — och
då är det femtio procent gissning.

**Det är den dyraste feltypen i systemet, sedd från frågans håll.** Ett rätt
svar som registreras som fel sänker stabiliteten på friska kort (D5), och här
skapar SYSTEMET självt situationen: uppgiften bär inte den information som
krävs för att lösa den.

**Vad som saknas är en disambiguering i uppgiften**, inte i svaret. Något i
stil med

    You cost.  (plural)          numerus, när pronomenet är tvetydigt
    the cost   (noun)            ordklass, när formen kan vara flera
    you (formal)                 tilltal, där språket skiljer

Informationen FINNS — specen vet numerus, person och ordklass, och renderaren
läste dem för att välja formen. Frågan är bara vilken av dem som behöver
sägas, och det beror på KÄLLSPRÅKET: `you` är tvetydigt på engelska men
`du/ni` inte på svenska. Måttet är alltså inte "är ordet tvetydigt" utan
"renderar källspråket två olika specar till samma text" — och just den
mätningen finns redan, som en av strukturkontrollerna i
`ordbok granska-meningar`.

**Öppet:** om disambigueringen ska visas alltid eller bara när sammanfallet
mätts; och hur den skrivs utan att avslöja svaret (att skriva "plural" röjer
inte vilket ord som avses, men "andra person plural" gör nästan det).

### D6 ? — Meningen vittnar

Kongruens sprider ETT faktum över flera ord. `die kleine Kind` är fel två
gånger: artikeln `die` är femininformen, och adjektivändelsen `-e` är också
femininformen efter bestämd artikel. Två av varandra oberoende ord är alltså
eniga om att `Kind` är femininum.

Idag bedöms varje ord för sig. Systemet ser två orelaterade fel. Men två
samstämmiga vittnen är mycket starkare bevis för ETT feluppfattat faktum än
vart och ett för sig — och omvänt: hade bara artikeln varit fel och adjektivet
rätt, vore det troligare ett slarvfel än en feluppfattning.

Att bygga det betyder att resonera över MÄNGDEN anmärkningar i stället för
över varje anmärkning för sig: vilken enskild feluppfattning förklarar flest
av felen? Det är en annan sorts kod än den stege D1 beskriver, och den skulle
göra pinne 7 (gissningen) mycket ovanligare.

### D7 ! — Japanskan har ingen ordvis diff

Japanska skrivs utan mellanslag: 私はパンを食べます. Det finns alltså inga
ordgränser att diffa på, och `difflib` på en teckensträng ger obegripliga
resultat.

I stället gör `_delsträngar` något mycket grövre: för varje form som slogs
upp i facit kontrolleras om just den teckensträngen förekommer någonstans i
svaret. Det ger ett enda besked — "formen saknas" — och kan inte skilja på:

- fel form (användaren skrev 食べる i stället för 食べます)
- ordet saknas helt
- ordet står på fel plats

Varje japansk anmärkning är därför `osäker = True`, och japanskan får i
praktiken bara veta att något saknades. Kombinerat med C6 (59 % nåbarhet) är
japanskan den kurs där systemet vet minst om vad användaren kan.

**Vad som krävs:** en tokeniserare (MeCab, fugashi, SudachiPy) som ger
ordgränser, eller en diff som byggs över de förväntade FORMERNA med
positioner i stället för över tecken.

---

## E. Hur uppdateras kunskapen? — schemaläggning

### E1 ✓ — Vilken minnesmodell?

FSRS 6.3.2, oförändrad, med `learning_steps=()` och `relearning_steps=()`.
En egen minnesmodell vore månader av tyst felaktighet, och det är precis den
sortens fel som kostat mest i det här projektet.

#### PASSET HÖLL KVAR KORT SOM REDAN VAR BEDÖMDA (2026-08-28)

Julius, efter förklaringen nedan: *"Detta är problematiskt. Trots att det
inte går 24 timmar så vill jag inte få övningar som inte gör någon skillnad.
Övningar ska endast ta fram ett kort som behöver tränas. Annars är övningen
meningslös."*

Invändningen är riktig, och felet låg inte i E2 utan i PASSET. Mätt på hans
kurs: **fyra av tio väntande rader var kort som redan hade en dom idag.**
Passet räknade dem som arbete, `att_göra` visade dem, generatorn byggde
meningar för att täcka dem — och bokföringen hoppade över dem, med rätta.
Två delar av systemet hade olika åsikt om vad som återstod.

`_stäng_redan_bedömda` stänger dem numera vid varje läsning av dagen, och
regeln är EXAKT E2:s: ett kort med en dom idag är klart, ett kort som FÄLLTS
idag står kvar och ska tas igen (B7). Skulle de gå isär är det städningen som
är fel.

**OM ANKI, som Julius frågade:** det finns ingen 24-timmarsregel där heller.
Kort förfaller på ett DATUM, inte en tidsstämpel, och blir tillgängliga vid
dygnsgränsen — som standard 04:00 lokal tid ("next day starts at"). En natts
sömn räcker; det som behövs är att gränsen passeras. Det här projektet gör
detsamma med lokal midnatt som gräns (`dygnets_början`), och att flytta den
några timmar är en inställning som kan läggas till om användningen kräver.

#### EGENSKAPEN HADE TRE VAKTER, OCH DET GJORDE PROVET SVÅRT (2026-08-28)

Jag skrev först invarianten på UTFALLET — "varje serverad mening bokför minst
ett kort" — och fick ett prov som inte gick att fälla. Inte med städningen
avslagen, inte med nödutgången (B8) avslagen också, och inte ens när kön
preparerats så att bara obokförbara kort väntade. Generatorn vägrar bygga en
mening utan täckning, så en tredje vakt tog över varje gång.

**Ett prov som inte kan falla bevisar ingenting**, och tre vakter gör ett
utfallsprov till en mätning av vilken som råkar svara först. Invarianten
sitter därför på KÖN — ingen väntande rad får peka på ett kort med en dom
idag — vilket är den plats felet faktiskt uppstod och den enda som går att
fälla rent.

Att det krävdes tre avstängda försvar för att ens nå fram är i sig ett svar
till Julius: den meningslösa övningen var inte ett hål i en vägg utan ett
läge kön aldrig skulle ha hamnat i.

#### ARBETE SOM INTE SYNS ÄR ARBETE MAN MISSTROR (2026-08-28)

Julius, dag 2: *"en övning som jag gjorde helt korrekt flyttade inga kort.
Det var exakt lika många i due, again och new."*

Spåret svarade direkt, och det är första gången `Spår` besvarade en fråga
som annars hade krävt en utredning:

    #142  Il existe.   svar: "Il existe"
      system    e                  rätt  redan_bedömd
      ord       il                 rätt  redan_bedömd
      ord       exister            rätt  redan_bedömd
      ordföljd  subjekt före verb  rätt  redan_bedömd
      … 7 kort, ALLA utanför bedömningen

**Regeln är riktig.** Varje kort hade redan bedömts rätt tidigare samma dag,
och en upprepad rätt samma dygn ger FSRS-faktor 1,0 — den gör bokstavligen
ingenting (E2, mätt: Good, Good, Good lämnar S på 34,797).

**Men den syntes inte.** Användaren gör en övning, allt är rätt, och tre
räknare står stilla utan förklaring. `svara` skickar numera `bokförs` och
`rörda`, och kortlistan skriver ut varför när talet är noll.

### E2 ✓ — Hur många betyg per kort och dag?

#### JULIUS INVÄNDNING, OCH VAD MÄTNINGEN SÄGER (2026-08-27)

*"Jag är rädd att det är fel. Alltså att det är okej att ge en dålig dom och
fälla kortet trots att jag precis klarade det. Jag tycker det ändå är logiskt
att mata in all data i FSRS."*

**Det scenariot är redan beteendet.** Regeln är inte "en dom per dygn" rakt
av utan asymmetrisk, och grenen som fäller ett nyss klarat kort finns:

    rätt + redan bedömt idag   →  hoppas över
    fel  + redan FÄLLT idag    →  hoppas över
    fel  + redan bedömt RÄTT   →  BOKFÖRS

Mätt på ett riktigt kort, rätt och sedan fel samma dygn:
S 2,307 → 0,775 och D 2,12 → 7,39. Felet slår igenom fullt ut.

**Och asymmetrin är FSRS egen, inte vår.** Samma kort, S = 10,96, upprepade
svar samma dygn:

| sekvens | S | nästa förfallodag |
|---|---|---|
| Good | 34,797 | 1 okt |
| Good, Good | 34,797 | 1 okt |
| Good, Good, Good | 34,797 | 1 okt |
| Again | 1,459 | 28 aug |
| Again, Again | 0,505 | 28 aug |
| Again, Again, Again | 0,188 | 28 aug |

**Upprepade rätt gör bokstavligen ingenting** — korttidsformeln klämmer
faktorn till 1,0 samma dygn, samma sak som `extranytta` mätte som noll
procent. Att hoppa över dem kastar alltså ingen information; FSRS hade
ignorerat dem ändå.

**Upprepade fel sammansätts däremot hårt**, 1,459 → 0,505 → 0,188. Att mata
in alla tre vore inte att lämna mer information till modellen utan att utnyttja
att den saknar en modell för massade fel: tre fel på samma kort inom tio
minuter är EN observation — "jag kan inte det här" — inte tre. Regeln bevarar
det första felet helt och avvisar bara upprepningen.

**Julius princip om att bara hoppa över för ett mer fundamentalt kort är
redan implementerad** och heter `skyddad` (E5): ett fallerat ordkort tar sina
form- och stamkort ur betygsättningen, därför att formen aldrig prövades.

**Det som INTE stämmer med förväntan är "again idag".** Ett fällt kort
schemaläggs till I MORGON, inte till idag — FSRS minsta intervall är ett
dygn (B7). Återförsöket samma pass ligger i passkön som en `igen`-rad, inte i
schemat. Ser man bara på `förfaller` ser det därför ut som att felet inte
gjorde något idag.



En mening rör flera kort, och samma kort kan stå i flera meningar samma dag.
Utan regel får ett vanligt kort tio betyg om dagen.

**Vad FSRS gör med dem — mätt.** Är det mindre än ett dygn sedan förra
repetitionen används inte den vanliga tillväxtformeln utan
`_short_term_stability`, som för RÄTT-betyg klämmer ökningen till minst 1,0.
För kort med S över ungefär 2 blir faktorn under 1 och klämningen binder:

    kort med S = 46,280, Good igen två timmar senare   →  S = 46,280
    samma kort, Again två timmar senare                →  S = 12,767, D 2,10 → 7,39

Ett extra RÄTT samma dygn ger alltså exakt noll. Ett extra FEL ger mycket.
Asymmetrin är inte vår uppfinning utan modellens.

**Mätt före regeln, på 705 riktiga repetitioner:**

    48,7 %  skedde inom EN MINUT från förra mötet av samma kort
    62,1 %  skedde vid R ≥ 0,99
     0,4 %  skedde vid R < 0,90, alltså som ett genuint minnesprov

Femtio massade rätt lämnade stabiliteten på 2,31 (intervall 2 dygn); ETT
rätt, vila till förfallodagen, och ett rätt till gav 10,96 (intervall 11
dygn). Samma två svar, fem gånger så lång verkan.

**Regeln:** ett RÄTT per kort och dygn; ett FEL får alltid registreras, även
om kortet redan bedömts idag. Att inte kunna något man nyss skrev rätt är
information. Motsatt ordning — rätt efter fel samma dag — är det inte, och
är dessutom mätt som nästan verkningslös (S 0,61 → 0,66), så passkön förlorar
ingenting på att inte bokföras.

**Dygnsgränsen är LOKAL midnatt**, inte UTC: UTC-midnatt är 02:00 i Sverige,
så ett pass klockan 00:30 skulle räknas till gårdagen.

### E3 ~ — FSRS har fyra betygssteg, vi använder två

`FEL, RÄTT = Rating.Again, Rating.Good`. Hard och Easy lämnas oanvända.

**Vad de fyra betyder i FSRS.** Again = jag kom inte på det. Hard = jag kom
på det, men det tog ansträngning. Good = jag kom på det. Easy = det kom
omedelbart, utan ansträngning. **Hard är alltså ett GODKÄNT betyg**, inte ett
"nästan fel" — det är den vanligaste missuppfattningen.

Mätt på ett kort med S = 10,96, D = 2,11, prövat på förfallodagen (R = 0,88):

| Betyg | ny S | ny D | intervall |
|---|---|---|---|
| Again | 1,58 | 7,39 | 2 dygn |
| Hard | 36,07 | **4,75** | 41 dygn |
| Good | 46,28 | 2,10 | 46 dygn |
| Easy | 89,16 | **1,00** | 85 dygn |

Det avgörande är kolumnen D, inte intervallet. Hard kostar bara fem dygns
intervall — men **mer än fördubblar svårigheten**, och D är trögrörlig
(mean reversion-vikten är 0,001). Ett kort som fått Hard några gånger är
permanent märkt som svårt och får kortare intervall för alltid. Easy trycker
D i botten på en gång.

**Vanan Again/Hard/Good, Easy nästan aldrig, är precis så FSRS är tänkt att
användas.** Easy är till för kort som egentligen inte borde ligga i leken.
Det som är värt att vara försiktig med är i stället Hard, av D-skälet ovan.

**Går de att HÄRLEDA i stället för att frågas?** Tre kandidater, och ingen
håller:

1. **Svarstid.** Det låter som det enda måttet som faktiskt mäter
   ansträngning snarare än korrekthet. Två invändningar sänker det, och den
   andra är avgörande för just vårt system:

   - **Bruset.** Användaren blir avbruten, tänker på annat, går ifrån. En
     lång tid kan betyda "svårt" eller "telefonen ringde", och ingenting i
     datan skiljer dem åt. Det går att dämpa statistiskt (Anki kapar vid 60
     sekunder, och ett medianvärde över hundratals repetitioner tål svansar),
     men bara om måttet får vara grovt.
   - **Tiden går inte att fördela.** En mening ger EN tidsstämpel och två
     till fem betygsatta kort. Vi vet inte vilken del av meningen som tog
     tid. Det är samma attributionsproblem som D1, fast utan diffens hjälp —
     en diff pekar åtminstone på ett ord, en klocka pekar inte på någonting.

   **Mätt i vår egen stack:** FSRS hade möjligheten och valde bort den.
   `fsrs.optimizer` läser `review_datetime` och `rating`; när
   parameteranpassningen spelar upp historiken skickar den uttryckligen
   `review_duration=None`. Förlustfunktionen jämför förutsagd retention mot
   faktiskt utfall, 0 eller 1. **Svarstiden är aldrig en variabel i
   minnesmodellen.** Den används på exakt ett ställe —
   `compute_optimal_retention` — och då som en KOSTNAD: genomsnittligt antal
   sekunder per betyg, för att simulera vilken `desired_retention` som ger
   mest kunskap per minut. Anki gör likadant: `revlog.taken` sparas, syns i
   statistiken, och rör inte schemaläggningen.

   Det Anki har och vi saknar är dessutom ett kort per svar. Även med perfekt
   tidsmätning skulle vi inte kunna adressera den.

2. **Nästan rätt form** — rätt stam, fel ändelse. Men det är redan definierat
   som ett FEL på systemkortet (D1, pinne 4), så signalen är upptagen.
3. **Kortet låg i passkön tidigare samma pass.** Svagt: det säger något om
   dagen, inte om just den här återkallelsen.

**Frågan var förmodligen fel ställd.** "Hur härleder vi Hard?" förutsätter
att två betygssteg är en brist. Men FSRS förlustfunktion är binär — modellen
tränas på om kortet återkallades eller inte, och betyget styr bara vilken
övergång som tillämpas. Och vår binära signal har en egenskap som en
självrapporterad fyrgradig inte har: **den är konsekvent.** Samma upplevelse
betygsätts Hard på tisdagen och Good på torsdagen av en människa; en diff mot
facit gör inte det. En jämn tvågradig signal kan anpassa parametrarna bättre
än en ojämn fyrgradig.

Vi har dessutom det omvända bytet mot Anki: Anki har grov attribution (ett
kort per svar) och fin självskattning. Vi har fin attribution (diffen säger
vilket av fem kort som brast) och grov skattning. Det är en annan avvägning,
inte en sämre.

**Vad binärt faktiskt kostar.** Bara svårigheten. Med enbart Again/Good
rör sig D uppåt vid fel och driver långsamt nedåt vid rätt (mätt: 2,12 → 2,08
över sex rätta, 2,11 → 7,39 på ETT fel). D blir alltså i praktiken
"felhistorik". Det som går förlorat är skillnaden mellan "jag kom på det men
det tog emot" och "det kom direkt", och den skillnaden är verklig. Men den
går inte att återvinna med en klocka.

**BESLUTAT 2026-08-23:** systemet stannar vid två betygssteg. Signalen
kommer från diffen och är därmed konsekvent, vilket är den egenskap som
räknas för parameteranpassningen. Hard och Easy härleds inte, och frågan om
att härleda dem är stängd.

Kvar står ETT antagande, och det är därför posten är `~` och inte `✓`:
**anpassar en konsekvent tvågradig signal parametrarna sämre än en ojämn
fyrgradig?** Vi tror nej och har argumentet för det, men vi har inte mätt
det. Det är en empirisk fråga som `fsrs.optimizer` svarar på när loggen
räcker (E7) — inte en designfråga som måste avgöras i förväg, och inte
heller något som ska stämplas som mätt innan mätningen finns.

**Svarstid har ändå en smal, verifierad användning, och den ligger inte
här.** `compute_optimal_retention` kräver `review_duration` på varje
loggpost och minst 512 poster, och använder den som kostnad för att välja
`desired_retention` — vilket C2 landade i är den ärliga ratten för
svårighetsgrad. **Som kostnad går tiden att fördela**, till skillnad från som
bevis: en menings sekunder delade på dess betygsatta kort är precis rätt
bokföring för "vad kostar en repetition i tid". Ansträngning går inte att
dela mellan kort; sekunder gör det. Det hör alltså till E7:s hög, inte till
den här.

### E4 ✓ — Oavsiktliga repetitioner räknas

En mening rör flera kort men valdes för ETT. Alla får betyg.

**Frågan var vad FSRS tycker om det — här är mätningen.** Kort med S = 10,96,
senast repeterat dag 0, förfallodag 11:

| Repeteras dag | R vid rep | ny S | intervall | nästa förfallodag |
|---|---|---|---|---|
| 0 (samma dygn) | 1,000 | 10,96 | 11 | 11 |
| 1 | 0,987 | 15,43 | 15 | 16 |
| 2 | 0,975 | 19,53 | 20 | 22 |
| 4 | 0,954 | 26,84 | 27 | 31 |
| 8 | 0,920 | 38,87 | 39 | 47 |
| 11 (i tid) | 0,906 | 43,93 | 44 | 54 |
| 20 (sent) | 0,854 | 63,47 | 63 | 83 |

Svaret på frågan "blir det en vecka och en dag, eller två veckor?": **varken
eller.** Förfallodagen flyttas framåt, men mindre än en full period, och ju
tidigare repetitionen görs desto mindre. Ingenting kringgås — FSRS räknar på
faktiskt förfluten tid och rabatterar den tidiga repetitionen korrekt.

**Överrepetition, samma kort repeterat Good VARJE dag:**

    1 repetition i tid (dag 11)      S = 46,28   nästa förfallodag 54
    14 repetitioner (dag 1–14)       S = 64,78   nästa förfallodag 79

Fjorton repetitioner köper alltså 25 extra dygn jämfört med vad en enda
köper. Det är inte skadligt — men det är ungefär en fjortondel så
effektivt per repetition. FSRS "tycker" alltså att vår överrepetition är
tillåten och meningslös, i den ordningen.

### E5 ✓ — Ett fallerat ordkort skyddar sina former

Kan man inte hämta fram ordet testades formen aldrig, och den ska inte
straffas för det.

**Det som händer sedan, och som inte är löst.** Ordkortet får Again och
hamnar i passkön, där det dessutom blir MÅLET för nästa mening. Formkortet
undanhölls — ingenting skrevs — så det behåller sitt gamla förfallodatum,
som ligger i det förflutna. Alltså står formkortet kvar som förfallet IDAG
och plockas gärna till nästa mening, som ju ändå byggs kring samma ord.

I praktiken ger det ofta rätt beteende: nästa mening innehåller både ordet
och formen. Men det är en bieffekt, inte en regel, och det ger fel resultat:
användaren får se facit, och prövas på formen igen tjugo sekunder senare.
Klarar hen den då får formkortet ett fullt Good med hela den förflutna tiden
inräknad — samma mätfel som D3, med samma pris.

**Rätt ordning:** ordet först, och formen först när ordet har återkallats
SJÄLVSTÄNDIGT, vilket tidigast är i morgon. Det skyddade kortet borde alltså
inte bara undanhållas utan skjutas fram minst ett dygn.

**Lösningen står under D3** — det skyddade formkortet skjuts upp till nästa
dygn med `skäl = skyddad`, exakt som det undanhållna kortet. Samma mekanism,
samma skäl.

Det kan också vara förklaringen till den rapporterade symtombilden att
extraövningen fastnade på ett par återförsök som aldrig löste sig.

### E6 ? — Kort som möts i nästan varje mening går inte att schemalägga

Den bestämda artikeln och 3sg-ändelsen finns i nästan varje mening. Vilket
intervall FSRS än sätter kommer kortet att mötas långt innan dess. Ett sådant
kort går inte att pröva i tid — inte för att modellen är fel, utan för att
det inte finns någon tidpunkt då det INTE prövas.

Tröskeln är härledd, inte vald: ett kort som möts minst en gång per dag kan
inte schemaläggas, alltså när `exponering × meningar per dag ≥ 1`.

**Efter B4 är den andra faktorn inte längre ett val utan ett utfall.** Antalet
meningar per dag följer av dagens arbete: `dagliga repetitioner /
kort_per_mening`. Tröskeln blir därmed

    exponering ≥ kort_per_mening / dagliga repetitioner

Den är fortfarande härledd, men den RÖR SIG med hur mycket användaren gör —
ett kort som är oschemalägbart för den som kör mycket kan vara schemalägbart
för den som kör lite. Det är korrekt beteende, men det betyder att mätningen
måste göras om och inte bara en gång.

**KODEN GÖR INTE DET HÄR (kontrollerat 2026-08-24).** `exponeringsgräns` är
`1 / meningar_per_dag`, och `sätt_schemalagt` hämtar talet ur
`MIN(Kurs.meningar_per_dag)` — alltså 20, kolumnen som B4 gjorde till en
kvarleva. Gränsen är därför fast på 0,05 och följer varken minuterna eller
den uppmätta takten. Funktionens egen docstring påstår motsatsen ("Nu när
takten är användarens val måste gränsen följa den"), vilket gör den till ett
påstående i koden som koden inte håller. Sådana kort får `schemalagt = 0` och
lyfts ur kön.

*(2026-08-26: `MIN` går numera över kursen för SPRÅKET i fråga och inte över
alla kurser, och skrivningen har `WHERE språk` — se punkt 3 nedan. Talet är
fortfarande 20 och gränsen fortfarande fast på 0,05, så stycket ovan gäller i
allt utom vilka kurser `MIN` läser.)*

**Men de ska fortfarande INTRODUCERAS.** Flaggan säger att spacing saknar
spak, inte att användaren kan ordet. Att låta den grinda introduktionen
gjorde `un`, `avoir` och `coûter` till ord som aldrig lärdes ut och som
meningarna presenterade ändå — se C5. Villkoret för att få införas är därför
`INFÖRBAR = (schemalagt = 1 OR typ = 'ord')`, medan `förfallna` behåller
`schemalagt = 1`.

**Vad som händer med dem sedan:** de fortsätter mötas, och de växer — men
allt långsammare, eftersom tillväxttermen går mot noll när R går mot 1 (B1).
De skadas inte. De mäts bara inte.

**Mätt 2026-08-23, och det här är varför posten är `~` och inte `✓`:**

    en   7 av 448 kort olåsta från schemat
    fr  10 av 448
    ja   5 av 403
    de   0 av 1 112

Tyskan är den största och äldsta kortleken och har noll. **Kontrollerat
2026-08-23: exponeringen har aldrig mätts för tyskan.** Alla 1 112 tyska kort
har `exponering IS NULL`; de tre andra språken är fullständigt mätta.

Och `sätt_schemalagt` lyder

    UPDATE Kort SET schemalagt = (exponering IS NULL OR exponering <= ?)

alltså **omätta kort lämnas schemalagda** — ett medvetet val ("att gissa vore
att bygga in en tumregel där beslutet säger mätning"), men följden är att
tyskan saknar skyddet helt, tyst. Tyska kursen befolkades innan mätningen
kopplades in och har aldrig befolkats om. Det är alltså ingen kodbugg utan en
**utebliven migrering**, samma klass som I4.

**Två fel till, hittade vid samma kontroll:**

*Mätningen samplar en enda meningsform.* `mät_exponering` bygger alltid
`Mening(verb, subjekt, objekt med adjektiv, tidsreferens)` — en transitiv sats
med objekt. **På nivå 1 finns inga objekt.** Den uppmätta exponeringen gäller
alltså en konstruktion kursen inte kan producera. Docstringen medger att
fördelningen är den slumpmässiga och inte generatorns, men inte att den är
fel KONSTRUKTION.

*Kort som lyfts ur schemat betygsätts ändå.* `registrera_mening` filtrerar
inte på `schemalagt`. Mätt i loggen: 5 engelska och 2 franska
`Repetition`-rader på kort med `schemalagt = 0`. Flaggan tar bort kortet ur
KÖN, inte ur BETYGSÄTTNINGEN — och det är loggen som var problemet.

#### FÖRSLAG SOM FÖLL (2026-08-23)

*Ett förslag skrevs in här och togs bort samma dag: en GRIND som betygsatte
ett möte bara när R ≤ retentionsmålet, eller när svaret blev fel. Tanken var
att skydda loggen från oinformativa rader. Simulering på 400 körningar per
läge visade att den är fel, och felet är principiellt.*

Ett kort som MÖTS var tredje dag i två år, med fel dragna ur modellens egen
förutsägelse:

    läge                    S efter 2 år (median)   betyg   fel
    ─────────────────────────────────────────────────────────
    repeteras bara i tid              1 345,5        11,1   1,06
    grind, möten var 3:e dag             11,7        89,5  21,35
    betygsätt varje möte              1 824,8       244,0   0,80

**Grinden ger ett kort med åtta dagars intervall efter två år, för en
användare som bevisligen producerat ordet 243 gånger.** Och felet är värre
än tabellen visar: under grinden PRODUCERAR användaren fortfarande ordet var
tredje dag och lyckas. Minnet försvagas inte — bara vår modell av det, för
att vi slutade mata den med bevis. Modellen skulle tro att R = 0,56 när
sanningen är nära 1.

**Slutsatsen är principiell och gäller bredare än den här posten:** en lyckad
återhämtning är ett bevis oavsett om vi valde att bokföra den. Att kasta
bevis gör inte loggen renare, det gör modellen fel. Och det är just vad
FSRS-vetenskapen bygger på — parametrarna är anpassade mot faktiska
återhämtningsutfall, inte mot ett urval av dem.

**Vad som DÅ skyddar loggen:** E2:s regel, ett betyg per kort och dygn. Den
träffar det verkliga problemet — MASSAD repetition inom samma dygn, där FSRS
korttidsformel ger exakt noll (mätt: S 46,280 → 46,280). Rader från olika
DAGAR är inte massade och bär genuin information, även vid högt R. Det var
alltid E2 som var skyddet; E6 behövdes inte för det.

#### VAD SOM ÅTERSTÅR AV E6

Mätningen ovan säger också att den ursprungliga motiveringen inte håller. Ett
allestädes närvarande kort GÅR att schemalägga: det betygsätts vid varje möte,
stabiliteten växer till 1 825 dygn, och därmed förfaller det aldrig och stör
inte kön. **Det löser sig självt, och det är dessutom sant** — användaren
producerar ju ordet varje dag.

Kvar står tre iakttagelser, och ingen av dem handlar längre om
schemaläggning:

1. **Tyskans exponering är omätt** (1 112 kort med `exponering IS NULL`).
   Det spelar roll för INFÖRSELORDNINGEN (B3) — ett ord man kommer att möta
   ofta hör hemma tidigt — inte för schemat.
2. **Mätningen samplar en enda meningsform.** Alltid transitiv sats med objekt
   och adjektiv, vilket nivå 1 inte kan producera. Samma sak: fel underlag
   för B3.
3. **`sätt_schemalagt` saknar `WHERE språk`** och använder `MIN(meningar_per_dag)`
   över alla kurser — samma latenta fara som I3, och dessutom byggd på ett tal
   B4 tagit bort.

   *RÄTTAT 2026-08-26, halva vägen.* Skrivningen är numera språkvis, och
   mätningen och skrivningen sker PARVIS: `mät_exponering` följt av
   `sätt_schemalagt(språk=s)` för samma språk, i stället för en mätning per
   språk och en enda skrivning över allt på slutet. Gränsen hämtas ur kursen
   för språket i fråga och inte ur ett `MIN` över alla.
   
   Att skrivningen sträckte sig utanför det språk anroparen bad om var precis
   I3:s felklass, och den behövde inte vänta på att E6 avgörs — en
   språkmätning fick inte ändra ett annat språks kö oavsett vad gränsen är.
   
   **Vad som INTE är rättat är talet självt.** Gränsen är fortfarande
   `1 / meningar_per_dag` med det vilande talet 20, alltså fast 0,05, och
   posten ovan säger att den ska följa den uppmätta takten. Det är ett beslut
   och inte en rättelse, och det hänger på den öppna frågan nedan.

**Den öppna frågan är därför inte längre "hur lyfter vi ut dem" utan "ska de
lyftas ut alls".** Argumentet för är att ett nyinfört allestädes närvarande
kort dominerar kön under de första veckorna. Argumentet emot är att det är
korrekt att det gör det — det ÄR det man möter mest och bör lära sig först.

Om svaret blir nej frigörs `schemalagt` för A3:s betydelse: kort utan väg till
någon mening. Det är ett strukturellt faktum som G5:s invariant kan pröva,
till skillnad från ett statistiskt som måste mätas om.

### E7 ? — FSRS-parametrarna är biblioteksförval

FSRS har 21 parametrar (w0…w20) som formar formlerna i B1. Vi kör med
bibliotekets förval, som är anpassade till ett stort Anki-material —
mestadels glosor, mestadels engelsktalande användare.

De GÅR att räkna om mot en enskild användares egen logg. Det är precis vad
"Optimize FSRS parameters" gör i Anki, och paketet har verktyget
(`fsrs.optimizer`). Två praktiska hinder:

- **Loggen är för kort.** 129 repetitioner totalt. Optimering är meningsfull
  någonstans kring tusen, och de måste dessutom vara informativa — vilket
  var precis det G3 visade att de inte var.
- **`fsrs.optimizer` kräver `torch`,** som inte är installerat. Det är ett
  beroende på ungefär 2 GB och bör vara valfritt, inte del av grundpaketet.

Det här är alltså inte en designfråga utan ett "inte ännu". Men det bör vara
schemalagt, inte bortglömt: förvalsparametrarna är ett antagande om
användaren, och det antagandet är prövbart.

**BESLUTAT 2026-08-23: svarstid sparas, men enbart som aggregerad KOSTNAD.**
Den är inte en signal om minnet (E3) och ska aldrig användas som en. Den har
en enda uppgift: `compute_optimal_retention`, som simulerar vilken
`desired_retention` mellan 0,70 och 0,95 som ger mest kunskap per minut.
C2 landade i att det är den ärliga ratten för svårighetsgrad, så det är den
funktionen som gör talet 0,90 till ett val i stället för ett arv.

Fördelningen fungerar just för att det är en kostnad: en menings sekunder
delade på dess betygsatta kort är rätt bokföring för "vad kostar en
repetition i tid". Ansträngning går inte att dela mellan kort; sekunder gör
det.

**Uppgraderat 2026-08-23:** tidsdatan är inte längre bara till för den här
funktionen. B4 gjorde minuter per dag till användarens enda val, och B2 gör
sekunder per repetition till omräkningen mellan minuter och kort. Loggningen
är därmed **lastbärande för hela arbetsbörderegleringen**, inte en valfri
extramätning för framtiden.

Tre krav `compute_optimal_retention` ställer, och de bestämmer när DEN delen
kan göras:

    review_duration    krävs på VARJE loggpost — funktionen vägrar annars
    ≥ 512 loggposter   hårt villkor i `_validate_review_logs`
    torch              samma beroende som parameteranpassningen

**BYGGT 2026-08-24.** Kolumnerna finns, klockan går, och
`sekunder_per_repetition()` läser dem. Två val i bygget är värda att notera:

*Råtiden sparas OKAPAD.* Anki kapar vid 60 sekunder för att en kafferast inte
ska bli en timmes kostnad, och det taket behövs — men det är ett ANALYSVAL
och ingen mätning. Kapas det vid skrivningen är den verkliga fördelningen
borta för alltid och gränsen går aldrig att mäta fram ur datan. Här kapas det
när talet används (`AVBROTTSGRÄNS_MS`), och talet står som Ankis och som
ovägt tills en egen gräns går att mäta.

*Tiden lagras där den MÄTTES, aldrig som ett härlett tal.* En mening är ett
tidtaget moment hur många kort den än rör, så tiden står på `Mening`. En
glosa är ett kort och ett svar, så där står den på raden själv. Kostnaden per
repetition är en fråga och ingen kolumn.

Den delningen kostade ett fel på vägen, värt att minnas: en rak join ger en
rad per bedömning där VARJE rad bär meningens hela tid, så summan räknade
samma tid en gång per kort. Mätt gav det 26,6 sekunder per repetition där det
rätta var 5,2. Tid och bedömningar har olika kornighet och får inte summeras i
samma svep.

**Kvar av E7:** ≥ 512 loggposter med tid, och `torch`. Ingetdera går att
skynda på — men klockan går nu, och det var hela poängen.

---

## F. När får man mer material? — progression

### F1 ! — Vad avgör att en nivå öppnas?

#### ALFABETET AVGJORDE I VILKEN ORDNING SPRÅKET LÄRS UT (2026-08-27)

Julius: *"Nu t.ex lär vi oss ni och vi innan vi lär oss du."*

`_rang` har tre signaler — källa, CEFR-nivå och centralitet — och när de tar
slut var sista brytpunkten **konceptnyckeln**, alltså strängjämförelsen.

Mätt på franskan: alla sex personliga pronomen kan stå med samma 65 verb, så
centraliteten är IDENTISK (65) för `je`, `tu`, `nous`, `vous`, `elle`, `il`.
Ordningen föll därför helt på alfabetet:

    rang 4  nous     pronomen_1pl  ┐  "p" < "s", alltså
    rang 5  je       pronomen_1sg  ┘  plural före singular
    rang 6  vous     pronomen_2pl
    rang 7  tu       pronomen_2sg

**Ordningen på språkets mest grundläggande ord bestämdes av hur nycklarna
råkade stavas.** Det är samma sorts fel som `byggbarhet` hade: ett tal som
såg härlett ut men mätte något annat än det utgav sig för.

`Koncept.person` och `Koncept.numerus` fanns redan och ger paradigmets egen
ordning. Efter rättelsen, och samma i alla sju språk:

    fr  je, tu, elle, il, on, nous, vous
    de  ich, du, sie, er, man, wir, ihr
    it  io, tu, lei, lui, uno, noi, voi
    ja  私, あなた, 彼女, 彼, 私たち, あなたたち
    sv  jag, du, hon, han, man, vi, ni

Brytpunkten gäller bara där ett paradigm FINNS: koncept utan person och
numerus — substantiv, verb, adjektiv — får 9 och påverkas inte av varandra.

**Rangen skrivs av `befolka`**, så en kurs som redan finns behåller sin gamla
ordning tills korten byggs om. Det sker vid nollställning och vid
nivåupplåsning.

**Och ordningen räcker inte ensam** — se F5b: `je` och `nous` införs var för
sig medan verbets alla sex personändelser redan ligger där från nivå 1.



Idag: **kapacitet, inte behärskning.** Nivån öppnas när belastningen den
skulle ge ryms i det användaren valt att öva.

**"Har vi ens ett sätt att avgöra när användaren kan ett kort tillräckligt?"**
Ja och nej, och skillnaden är viktig. FSRS garanti ÄR svaret: håller man
repetitionerna minns man per konstruktion 90 % av sina kort, hela tiden.
"Kan" är alltså inte ett tillstånd att mäta utan en följd av att hänga med.
Att bygga ett eget behärskningsmått ovanpå vore att implementera om FSRS.
Men garantin gäller bara SEDDA kort. Ett osett kort är inte kunnat i någon
mening — så ett eventuellt förkunskapsvillkor handlar om sedd-het, inte om
behärskning.

**Det som fattas, och som är den riktiga invändningen.** Måttet är helt
blint för RELEVANS. Man kan låsa upp nivå 2 (objekt) med en belastning som
uteslutande består av verb och pronomen, och utan att ha sett ett enda
substantiv eller en enda ackusativändelse. Kapacitetsargumentet säger att det
går bra, eftersom de nya korten införs i kontrollerad takt — men lektionen
för nivå 2 landar då hos någon som inte har något att lägga objekt på.

Ett andra villkor är alltså legitimt och har aldrig prövats: **nivåns egna
förkunskaper.** Nivå 2 kräver några substantiv; nivå 5 (bisatser) kräver
subjunktioner. Det svarar också på frågan om krav per korttyp — det är
antagligen där ett sådant krav hör hemma, som en förkunskapslista per
nivå snarare än en kvot per typ.

#### DEFEKT UPPTÄCKT 2026-08-24 — grinden mäter en regel som inte gäller längre

`byggbarhet()` och `redo_för_nivå()` räknar andelen meningar med HÖGST ETT
okänt ord. Det var C5:s svar när de skrevs. C5 säger nu NOLL — ordkort införs
i glosläget, och en mening som innehåller ett oinfört ord är en oanmäld
kostnad, inte en lektion. Grinden mäter alltså något generatorn inte längre
producerar.

Skillnaden är inte marginell. Samma kurser, 300 kandidater var:

| kurs | `okända ≤ 1` (grinden idag) | `okända == 0` (C5) |
|---|---|---|
| de nivå 4 | 0,135 | 0,048 |
| en nivå 1 | 0,425 | 0,061 |
| fr nivå 1 | 0,130 | 0,000 |
| fr nivå 4 | 0,060 | 0,000 |
| ja nivå 1 | 0,012 | 0,000 |

Engelskan är sju gånger för generös. Franskan och japanskan skulle gå från
"redo" till "inte redo" — tröskeln är `byggbarhet × kandidater ≥ 1`, alltså
0,001 vid tusen kandidater, och 0,000 över 300 sonder säger bara att andelen
är under en trehundradel; den behöver mätas med fler sonder innan man vet
vilken sida av tröskeln den ligger på.

**Att rätta den är ingen mekanisk ändring.** Den skulle strama åt
progressionen märkbart, och frågan om det är RÄTT åtstramning är F1:s egen
öppna fråga — måttet är fortfarande blint för relevans. Rättelsen gör grinden
konsistent med C5; den gör den inte riktig.

**Att kravet känns stort beror delvis på att det RÖR SIG.** Mätt 2026-08-23:

| Kurs | kapacitet C | belastning | rum | nästa nivå | saknas |
|---|---|---|---|---|---|
| de 4→5 | 20 × 5,0 = 100 | 22,0 | 120 kort | 149 | 29 |
| en 1→2 | 20 × 2,9 = 58 | 28,0 | 56 kort | 59 | 3 |
| fr 1→2 | 20 × 2,2 = 44 | 14,0 | 40 kort | 85 | 45 |

Talen är alltså inte 200 längre. Men de svänger med varje pass, eftersom både
`per_kort` och `kort_per_mening` beräknas ur en logg på ett par hundra rader
(B2). Faller `per_kort` från 0,647 till 0,05 när korten mognar går tyskans
`rum` från 120 till över 1 500. Ett krav som ändrar sig med en faktor tio är
svårt att lita på, och omöjligt att planera efter.

**Kapacitetsvillkoret måste räknas om efter B4.** Det står idag som
`meningar_per_dag × kort_per_mening`, och `meningar_per_dag` finns inte
längre. Den nya formen har samma struktur men annan enhet:

    kapacitet = minuter_per_dag / sekunder_per_repetition   [repetitioner/dygn]

Och `per_kort` — nämnaren i `rum` — ska bytas mot den simulerade
kostnadskurvan i B2, som är 5 till 28 gånger lägre. **Kravet kommer alltså
att falla dramatiskt när B2 byggs.** Uppmätta 29 kort för tyskan är räknat
med en kostnad som är fem gånger för hög på en månads horisont.

#### LÖSNING — BYGGD 2026-08-24

**KAPACITETEN ÄR INTE LÄNGRE EN GRIND, och det går att bevisa.** Inflödet
räknas om varje dygn och tittar aldrig på nivå:

    nya = min(osedda, inflödestak, dagstak)

Fler osedda kort kan alltså inte öka `nya`. Att låsa en nivå för kapacitetens
skull skyddar därför ingenting — hela villkoret var ett svar på ett problem
som B2 löste på ett annat ställe.

**KVAR STÅR EN VERKLIG FRÅGA: går nivån att ÖVA?** Franskans allra första
mening blev `Elle regarde.` där båda orden var osedda — en uppgift som bara
gick att gissa. Att låsa upp objekt hos någon som inte sett ett enda
substantiv gör varje mening till en ordlektion.

Måttet är `Generator.byggbarhet()`: andelen samplade meningar på nivån som har
högst ETT okänt ord — samma okändgräns som genereringen redan använder (C5),
och samma skäl.

**TRÖSKELN ÄR HÄRLEDD UR SÖKNINGEN SJÄLV.** Generatorn prövar `kandidater`
kandidater per mening, så andelen dugliga måste vara stor nog att minst en
väntas i varje sökning:

    byggbarhet × kandidater ≥ 1

Samma form som E6:s exponeringströskel, och av samma skäl: gränsen kommer ur
systemets egen takt i stället för ur ett valt tal.

Mätt över kurserna, med 800 kandidater:

    de 4→5   +149 kort   byggbarhet 0,091   redo
    en 1→2    +59 kort   byggbarhet 0,289   redo
    fr 1→2    +85 kort   byggbarhet 0,036   redo
    ja 1→2    +46 kort   byggbarhet 0,000   INTE redo — noll sedda ord

Japanskan är oövad och har noll sedda kort, så varje mening skulle ha två
okända ord. Att den inte är redo är rätt svar, inte en defekt.

**Det gamla villkoret sa `plats = False` för ALLA FYRA kurserna.** Under det
kunde ingen nivå någonsin öppnas — det var det "fler än 200 kort" faktiskt
betydde.

**NIVÅNS STORLEK UTTRYCKS I DYGN, INTE I KORT.** "Ryms N kort" har inget svar
när villkoret sitter på en takt; "hur lång tid tar N kort i den här takten"
har ett: `N / inflödestak`. Gränssnittet säger numera "Level 5 would add 149
cards · at your pace that is 14 days" i stället för att visa ett hinder.

Det är också svaret på att kravet RÖRDE SIG med en faktor tio: ett tal som
bara är upplysning behöver inte vara stabilt på samma sätt som ett tal som
låser en dörr.

**`lås_upp` prövar samma villkor som knappen visas på**, så en gammal
sidladdning inte kan öppna en nivå som inte går att öva.

**Byggbarheten cachas** per (språk, nivå, cefr) och töms vid varje bokförd
mening, eftersom måttet stiger när ord lärs in. Mätt: hemskärmen tar 3 ms med
varm cache och 593 ms efter en bokföring.

#### GRINDEN ÄR MÄTT, OCH DEN ÄR LÅG (2026-08-26)

Postens öppna fråga — att måttet är blint för relevans — har nu ett tal.

`redo_för_nivå` är `byggbarhet × kandidater ≥ 1`, alltså **går det att bygga
minst EN mening av 800 på nästa nivå utan okända ord**. Tröskeln är 0,00125.
Mätt på en färsk franskkurs:

    före dag 1    byggbarhet 0,000     redo = nej
    efter dag 1   byggbarhet 0,071     redo = JA — 57 gånger över tröskeln

Efter ett enda pass med tolv drillade ord står nivå 2 öppen med bred marginal.
Julius: *"varje gång jag gör klart första passet så kan jag levla upp på
direkten vilket är för snabbt."*

#### OCH DEN MÄTTE FEL NIVÅ (rättat 2026-08-26)

Julius: *"Det står att det är drygt 5 dagar tills nästa nivå men ändå kunde
jag direkt låsa upp alla. Man ska inte kunna låsa upp allt på en gång."*

Mätt: efter EN dags franska gick **tjugo nivåer att låsa upp i följd**, 632
kort, utan att öva emellan. Byggbarheten låg på 0,006–0,067 mot tröskeln
0,00125, så varje nivå passerade.

**Skälet är att `byggbarhet` mätte nivån man REDAN hade.** Den samplar
kandidater på den nya nivån och frågar om de har högst ett okänt ord — men
varje ny konstruktion är VALFRI, så på nivå 2 är en vanlig subjekt-verb-mening
fortfarande giltig och utgör nästan hela urvalet. Måttet svarade "nivå 2 går
att öva" genom att visa att nivå 1 går att öva.

*Rättat: `byggbarhet(nivå=N)` kräver att specen faktiskt ANVÄNDER den
konstruktion nivån låser upp.* Predikaten är fält på `Mening` — `m.objekt is
not None` för objekt, `m.bisats is not None` för bisats, och så vidare för
alla tjugo. En konstruktion som inte går att se i specen hör inte hemma på
komplexitetsstegen, så listan är komplett per konstruktion.

**Och urvalet måste kunna upplösa tröskeln.** `redo_för_nivå` frågar om
andelen är minst `1/kandidater` = 1/800, men måttet samplade 200 — ett urval
som inte kan skilja 1/800 från noll. Mätt: nivå 6 (possessiv) hade den sanna
andelen 2/800, alltså över tröskeln, men skattningen blev noll gång på gång
och kursen låstes fast. Talet är nu detsamma som tröskeln härleds ur.

**Utfallet, simulerat med användarens egna svarstider:**

    dag 1  nivå 1 → 2      dag 4  nivå 4 → 5
    dag 2  nivå 2 → 3      dag 5  nivå 5 → 6
    dag 3  nivå 3 → 4      dag 6–13  stängd — nivå 7 (indirekt objekt)
                                     kräver ditransitiva verb och fler
                                     substantiv än ordförrådet har
    dag 14 nivå 6 → 7

Alltså en nivå per dag i början och sedan en verklig platå, i stället för
allt på en gång.

**OMMÄTT 2026-08-27, efter att nollställningen slutade ärva gårdagens tak
(B4).** Takten är nu betydligt långsammare än ovan:

    dag 1     nivå 1 → 2
    dag 2–7   INGEN upplåsning — kursen står på nivå 2

Talen ovan står kvar som det de var: en mätning på en kurs vars inflödestak
satt fast på 7 kort. Med det riktiga taket (51) hämtar dagen in mer material,
och `byggbarhet` mot nivå 3 räcker ändå inte — så platån kommer direkt efter
den första upplåsningen i stället för efter den femte.

**Att nivå 2 öppnas efter dag ett är alltså det mätta beteendet och inte ett
fel.** Grinden frågar om SÖKNINGEN kan bygga meningar med den nya
konstruktionen, och efter arton inlärda ord kan den det. Den frågar
fortfarande ingenting om huruvida INLÄRAREN är redo — se den öppna frågan
nedan. **Grinden mäter numera rätt sak; om den är strängt nog är
en annan fråga** — den släpper fortfarande igenom en nivå per dag så länge
konstruktionen går att bygga, och postens ursprungliga öppna fråga om
förkunskaper står kvar.

**Motsägelsen i gränssnittet var en etikett.** "At your pace that is 4 days"
stod bredvid domen "Ready" och lästes som "fyra dagar tills du kan låsa upp".
Talet säger hur länge det NYA materialet räcker vid din takt. Etiketten heter
numera "Time to work through that", och domen säger vad den gäller.

**Grinden gör precis det den härleddes för**, och härledningen är riktig: den
handlar om huruvida SÖKNINGEN kan fungera. Den säger ingenting om huruvida
INLÄRAREN är redo — och det är just vad posten ovan redan noterat.

**Och två tal om olika saker står under samma rubrik**, vilket gör motsägelsen
synlig i gränssnittet:

    "Ready"    ett golv: kan generatorn bygga en enda mening på nivån
    "4 days"   en varaktighet: 85 kort ÷ 25 kort per dygn i din takt

Det ena är en dörr, det andra en sträcka. Att de ser ut att beskriva samma
beredskap är ett gränssnittsproblem; att grinden är låg är den här postens
öppna fråga, och den kräver förkunskapsvillkoret som aldrig prövats.

**STÄNGT 2026-08-26 — CLI:t räknades om och den gamla matten är borta.**
Posten löd: *"`upplåsningsläge` räknar fortfarande `rum`, `saknas` och `krävs`
med det gamla `per_kort` — fem till trettio gånger för högt. De grindar
ingenting och skickas inte längre till gränssnittet, men de står kvar för
`ordbok kort --läge` och ska bort när CLI:t räknats om."*

`ordbok kort --läge` visar numera de två tal som faktiskt betyder något:
**går nivån att öva** (byggbarheten mot sökningens egen kandidatmängd) och
**hur många dygn den tar i din takt**. Med det försvann sista läsaren, och
`rum`, `saknas`, `krävs`, `kapacitet`, `plats`, `hela_högen_ryms`,
`rep_per_dag`, `per_kort` och `belastning` är borta ur `upplåsningsläge`,
tillsammans med `_rum_exakt` och `kostnad()`s `ryms`.

**Borttagna och inte kommenterade, och det är skillnaden.** Ett tal som är
både fel och oanvänt är en inbjudan att använda det igen — vilket det redan
hade blivit en gång, i underraden som visade `krävs` mot `kapacitet`.

`--meningar-per-dag` föll med dem: flaggan matade bara den matten.
`meningar_per_dag` har därmed **ett enda kvarvarande styrande bruk** i hela
systemet — reservmålet i `dagsplan` innan tiden är mätt (`_kapacitetsval`) —
plus `exponeringsgräns`, som E6 säger ska följa den uppmätta takten i stället.

---

*Nedan står problemtexten som den var innan lösningen. Den är skälet till att
lösningen ser ut som den gör.*

**EFTER B2 ÄR FRÅGAN MALFORMULERAD, och det är den viktigaste följden.**
Upplåsningen frågar "ryms nästa nivås N kort?" — en fråga om ett LAGER. Men
villkoret sitter numera på en TAKT: hur många kort per dygn som är hållbart.
Ett lager har inget svar när kurvan växer logaritmiskt, medan "hur lång tid tar
N kort i den här takten" har ett: `N / inflödestak` dygn.

Det gör också att `dagsplan["inflödestak"]` (kort per dygn) och
`upplåsningsläge["rum"]` (kort) INTE är samma storhet, trots att den senare
hette `rum` i båda. Namnet är därför bytt i `dagsplan`.

`upplåsningsläge` räknar tills vidare som förut, med det gamla `per_kort` —
alltså med en kostnad som är fem till trettio gånger för hög. Det är en känd
inkonsekvens och den hör hit, inte till B2.

**Öppet:** förkunskapsvillkoret; om kravet ska uttryckas i DYGN i stället för
i kort; och om det ska visas som ett tal alls, när talet inte är stabilt.

### F2 ✓ — Frågan gäller nästa nivås MARGINALKOSTNAD

Villkoret var först "ryms ALLA osedda kort i dygnet". Det krävde 453 kort för
engelskans nivå 2 och 958 för tyskans nivå 5 — alltså att man i praktiken
lärt sig hela nivåns ordförråd innan nästa KONSTRUKTION öppnade. Fel av två
skäl:

1. **Det blandar ihop kursens två oberoende tak.** Nivå 2 lägger till objekt.
   Det kräver inte att man kan alla A1-substantiv. Att kräva det vore att
   påstå att den som lärt sig bisatser också kan alla ord — precis det som
   `nivå` och `cefr` finns till för att hålla isär (F3).
2. **Det räknar samma skydd två gånger.** Ett osett kort kostar ingenting
   förrän det INFÖRS, och införseltakten är redan begränsad av `dagsplan`
   genom samma `rum`. Högen kan inte springa i väg; det är takten som är
   farlig, inte lagret.

Kvar blir den ärliga frågan: nästa nivå lägger till N kort — ryms de?

### F5b ? — Böjningsdimensionerna är inga nivåer, men borde vara det

**Julius 2026-08-27:** *"je, tu, nous, vous är ett speciellt fall eftersom de
direkt anknyter till en specifik böjning. Alla nya böjningsparametrar borde
vara en nivå. Sen kanske man kan klumpa ihop vissa nivåer ifall de enskilt är
för små."*

**Stegen har 21 KONSTRUKTIONER** — objekt, bestämdhet, numerus, attribut,
possessiv, io, adverbial, tempus … — och de styr vad en MENING får innehålla.
Böjningens egna dimensioner styrs inte alls. Mätt på franskan: `befolka` på
nivå 1 skapar ändelsekorten `e`, `es`, `ez`, `ons`, `s`, `∅` på en gång, för
två böjningsklasser. Sex personformer, samma dag.

#### TIO MINUTER SOM BLEV EN (2026-08-28)

Julius: *"Sen stod det about 1 minute remaining innan jag startade passet.
Kan det stämma?"*

Ja, och räkningen är riktig: 12 rader × 4,94 sekunder per rad ≈ 1 minut.
**Frågan är i stället varför dagen bara är tolv rader när han bett om tio
minuter.** Mätt på hans franska, dag 2 med 26 sedda kort:

    måltakt                96 rep/dygn    (10 min ÷ 6,26 s per repetition)
    tak IDAG               91 nya kort    tidsvillkoret binder inte alls
    i längden              11 nya kort    ← DET HÄR binder
    förfallna idag          3

**Långtidsvillkoret är det som gör dagen kort.** Ett kort kostar 8,4
repetitioner över året, så 96 repetitioner om dagen bär elva nya kort om
dagen i jämvikt. De elva kostar ungefär elva repetitioner idag, plus tre
förfallna — alltså en och en halv minut av tio.

**Det är beteendet B4 beskriver, och det är riktigt**: minuterna är ett TAK
och inte ett mål. Systemet kan inte tillverka arbete som FSRS inte har
schemalagt, och att införa mer nytt idag vore att låna mot en budget som
inte finns. De återstående minuterna blir användbara när kortleken mognat.

**Men det är obegripligt utifrån.** Skärmen säger "10 min/dag" i
inställningen och "about 1 minute remaining" i dagen, utan att någonstans
säga att skillnaden är avsiktlig och tillfällig. Frågan står öppen: vad ska
gränssnittet säga när kapaciteten är tio gånger dagens arbete?

**Julius poäng är att det är samma sorts axel.** Att låsa upp `nous`-formen
öppnar mängder av kort för ord man redan kan, bara med en böjning till — och
det är exakt vad en nivå gör. Skillnaden mot dagens steg är bara att
konstruktionerna sitter på MENINGEN och böjningen på ORDET.

**Det knyter ihop tre öppna poster:**

- **Ordningsfrågan (den här postens ursprung).** `pronomen_1sg` och
  `pronomen_1pl` fick sin ordning ur alfabetet tills paradigmordningen lades
  in. Men ordningen mellan PRONOMEN spelar bara roll om verbformen följer
  med, och det gör den inte idag: `je` och `nous` införs var för sig medan
  alla sex ändelser redan finns.
- **A3, oåtkomliga kort.** Ändelsekort som ingen mening kan nå är precis de
  som inte hör hemma på den nivå de skapades.
- **F5, stegen är slut vid 21.** Böjningsdimensionerna skulle ge stegen fler
  meningsfulla trappsteg utan att hitta på nya konstruktioner.

#### RÄKNINGEN ÄR GJORD (2026-08-27)

**Axlarna som finns, per språk** — distinkta värden i `Former`:

    språk  numerus species kasus genus tempus grad person diates  celler
    sv          2       2      5     3     10     3      0      2      49
    en          2       2      5     0      8     3      3      1      34
    de          2       3     12     3     14     3      3      2     197
    fr          2       2      9     3     21     3      3      1     101
    ja          0       0      0     0     11     1      0      2      18

**Person/numerus/tempus-cellerna vid FULLT ordförråd**, alltså vad en sådan
nivå skulle bära när kursen mognat:

    fr   60 celler, 5 619 former   36 med ≥50 former, median 106, störst 174
    de   42 celler, 3 374 former   30 med ≥50 former, median  72, störst 174
    sv    0 celler                 svenskan personböjer inte verb alls

Störst = 174 = ett per verb i ordboken, alltså en full kolumn i paradigmet.

**Tre slutsatser, och den tredje är den obekväma.**

**Cellerna är substantiella när kursen mognat.** Median 106 former för
franskan — det är inga småsteg, det är riktiga läromoment.

**Men de är små i början, och det är där problemet uppstod.** På nivå 1:s
franska kortlek finns 11 celler och 36 kort: `pres_3sg` bär 12, `pres_2sg`
bär 5, `pres_1pl` bär 2. Tyskan har 28 celler och 72 kort, och INGEN cell når
tio. Klumpningen är alltså inte en efterjustering utan det som avgör om
konstruktionen fungerar de första veckorna — precis Julius egen misstanke.

**Och stegen skulle sluta vara språkoberoende.** Dagens 21 nivåer sitter på
KONCEPTLAGRET och är därför samma för alla sju språken; det är en av
paradigmets bärande egenskaper. En böjningsstege har 60 steg i franskan, 42 i
tyskan och NOLL i svenskan. Antingen blir stegen språkspecifik — vilket bryter
den delade axeln och kräver att `NIVÅ` blir en tabell per språk i stället för
en dict — eller så måste dimensionerna abstraheras till något som finns i
alla sju, och då är det inte längre "en nivå per böjningsparameter".

**Det är den frågan som ska besvaras innan något byggs**, och den är en
designfråga och inte en mätning.

#### JULIUS SVAR PÅ DEN, OCH DET HÅLLER (2026-08-27)

*"Man hade kunnat ha en universell nivålista som är detaljerad, och sen
renderas nivålistan olika för de olika språken genom att gå igenom och se att
vissa rader faktiskt bidrar till något nytt i språket."*

Det löser motsättningen utan att offra den delade axeln: listan förblir
universell och konceptnära, och STEGEN blir en projektion av den per språk.
Samma form som renderarna redan har — universell spec, språkspecifik
realisering.

**Och predikatet finns redan.** Strukturkontrollen i `meningsgranskning`
frågar exakt detta: *"TVÅ SPECAR SOM RENDERAR IDENTISKT — skiljer sig
specarna men inte texten har renderaren tappat en distinktion."* Det som där
är ett FEL är här ett urvalskriterium: renderar två specar likadant bidrar
raden inget i det språket och hoppas över.

**Mätt på verbets personböjning**, andel av sex verb där själva verbformen
skiljer sig — subjektspronomenet borträknat, annars "syns" varje distinktion
i varje språk bara för att pronomenet byts:

    par        sv    en    de    fr    es    it
    1sg/2sg     0%    0%  100%   67%  100%  100%
    1sg/3sg     0%  100%  100%   33%  100%  100%
    2sg/3sg     0%  100%   67%  100%  100%  100%
    1sg/1pl     0%    0%  100%  100%  100%  100%
    1pl/2pl     0%    0%  100%  100%     ?  100%
    3sg/3pl     0%  100%  100%  100%  100%  100%

Utfallet är språkligt riktigt, vilket är kvittot på att måttet mäter rätt sak:

- **Svenskan noll överallt** — svenska verb personböjs inte. Varje personrad
  hoppas över, och stegen blir kortare utan att någon skriver en regel.
- **Engelskan bara där 3sg ingår** — det enda märkta cellen är `-s`.
- **Tyskans 2sg/3sg 67 %** — `liest`/`liest` faller ihop för en del verb.
- **Franskans 1sg/3sg 33 %** — `parle`/`parle` är identiska för -er-verben,
  och 1sg/2sg skiljer sig bara på ett stumt `-s` (67 %).

**Stegen skulle alltså bli olika långa av sig själv:** noll personnivåer i
svenskan, en i engelskan, fem till sex i de romanska och tyskan. Ingen lista
per språk behöver skrivas eller underhållas.

#### PROJEKTIONEN ÄR BYGGD (2026-08-27) — `kort/dimensioner.py`

Mekanismen finns nu, men är ÄNNU INTE inkopplad i nivåstegen. Den räknar, den
styr ingenting.

**Kriteriet, och varför det inte är ett val:** en cell lär ut något nytt om
dess ÄNDELSE inte redan är känd från en tidigare cell i SAMMA klass.
Franskans K0 har `pres_1sg = e` och `pres_3sg = e`; har man lärt sig den
första finns ingenting kvar i den andra. K1 har `s` och `t` på samma celler,
och där är det två moment. Det är strängidentitet i data som redan finns,
ingen tröskel.

**Partiella rader löser sig av det:** raden står kvar med just de klasser som
realiserar den. `1sg` mot `3sg` blir en nivå i K1 och inte i K0. Att det
sitter på KLASSEN och inte på ordet är hela skillnaden mot invändningen
ovan — `system`-kort hör redan till en klass, så granulariteten finns i
kortmodellen och ingen omskrivning behövs.

**Och listan HÄRLEDS.** Mitt första försök var handskrivet — `pres_1sg`,
`pres_2sg`, … — alltså en fransk lista med universella anspråk. Mätt mot
datan missade den 11 av svenskans 12 celler, 15 av tyskans 31 och ALLA tio
japanska. Svenskan fick ett enda steg, och det var listans fel. Unionen av
alla språks celler är den universella listan.

**Utfallet: 90 universella celler, veckade per språk.**

    sv   5     inf, sup, inf_passiv, pres, sup_passiv
    en   4     pres_3sg, pret, gerund, inf_imp
    de   8
    fr  34     es 45     it 44     ja 9

Talen är språkligt riktiga, vilket är kvittot på att kriteriet mäter rätt
sak: **engelskan får exakt fyra** — walk, walks, walked, walking — och
svenskan fem. Ingen lista per språk är skriven.

**`dimensionsprov` vaktar fyra invarianter**, och den tredje bär idén: varje
ändelse i varje tabell ska läras ut exakt en gång. Två gånger betyder tomma
moment; noll gånger betyder något som inte går att lära sig.

#### MÄRKNINGEN BEHÖVDE INTE GÖRAS — DEN FANNS (2026-08-27)

Ordningen var det som återstod, och jag antog att cellerna måste märkas med
sina axlar först. **De är redan märkta.** `paradigm/{språk}/verb.yaml` ger
varje cell dess tempus, person, numerus och diates, och `ladda_slot` resolvar
dem. Arbetet var att LÄSA märkningen, inte att göra den.

Listan sorteras nu på `(diates, tempus, numerus, person)`, och bara den
första komponenten — tempusordningen — är ett val. Den står som en läsbar
lista över legendens fjorton värden i stället för att gömmas i en
sorteringsfunktion eller spridas över nittio cellnamn.

**Två ordningsfel som mätningen visade, och båda var lärorika:**

*Otaggad diates sorterade före aktiv.* Engelskans yaml utelämnar `diates` på
en del celler medan franskans skriver ut den, och eftersom den delade listan
tar den LÄGSTA rangen över språken vann den otaggade. Franskans steg blev
1sg, 2sg, 1pl, 2pl, 3pl, 3sg. En otaggad diates betyder aktiv, inte "före
aktiv" — men numerus och person behåller sitt nollvärde, och där är det rätt:
svenskans `pres` och japanskans `masu` gör ingen personskillnad och är
paradigmets omarkerade form.

*Diates måste slå tempus.* Svenskans `inf_passiv` (läsas) kom före `pres`
(läser), eftersom infinitiv rankas före presens. Hela aktivum ska läras innan
något passivum — det är en starkare regel än tempusordningen. Samma sak
flyttade japanskans `ukemi` från andra plats till sista.

**Stegarna, färdiga:**

    sv (5)   inf, pres, sup, inf_passiv, sup_passiv
    en (4)   pres_3sg, pret, gerund, inf_imp
    de (8)   inf, pres_1sg, pres_2sg, pres_3sg, pret_1sg, konj2_2sg,
             konj2_2pl, part1
    fr (34)  inf, pres 1sg…3pl, pret 1sg…3pl, particip, imperfekt,
             futurum, konditionalis, presensparticip
    ja (9)   jisho, masu, ta, imp, kond, te, nai, vol, ukemi

**Franskan hoppar över `imperf_2sg` och `kond_2sg`** — de ändelserna är redan
lärda tidigare i paradigmet. Det är projektionen som arbetar, och det syns
utan att någon skrivit en regel om franskan.

#### FLÄTNINGEN BYGGD (2026-08-27) — `dimensioner.stege`

**BESLUTAT AV JULIUS: en gemensam numrering där konstruktioner och böjning
varvas.**

Flätningen är PROPORTIONELL och inte ett-och-ett. Konstruktionerna är tjugo
och lika i alla språk; böjningsstegen är fyra i engelskan och fyrtiofem i
spanskan, så varannan-varannan hade tömt den korta långt före den långa.
Båda listorna sträcks över samma intervall och slås ihop på position —
franskan får ungefär två böjningssteg per konstruktion, engelskan ungefär en
femtedel. Proportionen räknas ur längderna och är alltså ingen inställning.

**Beroenden bryter proportionen, och måste göra det.** Fyra konstruktioner
går inte att bygga förrän en viss böjning är införd:

    tempus     kräver Pret, Imperf eller Fut
    perfekt    kräver Sup eller PresPer
    imperativ  kräver Imp
    passiv     kräver diates Passiv

Utan det lägger flätningen `tempus` på steg 9 medan preteritumändelserna
kommer på steg 30, och användaren möter dåtid trettio steg innan något kort
lär ut hur den böjs — precis felet hela böjningsstegen finns för att laga,
återinfört ett steg senare. Mätt: villkoret flyttar 24 av franskans steg.

**Stegarnas längd, färdigt flätade:**

    sv 25    en 24    de 28    fr 54    es 65    it 63    ja 29

**`dimensionsprov` vaktar sju invarianter**, var och en med sitt eget
sabotage. Två lärdomar ur att skriva dem:

*Ett gemensamt sabotage räcker inte.* "Släpp igenom varje cell" fällde bara
två av fyra; de andra vaktar mot omkastning respektive för LITE undervisning,
och ett sabotage som lär ut för mycket kan inte bryta dem. Ett prov som inte
faller för sitt eget sabotage är stumt; ett som inte faller för någon annans
är bara ett annat prov.

*Ett prov får inte läsa sin förutsättning ur det som prövas.*
`prov_beroenden` läste `BEROENDE` — alltså exakt tabellen sabotaget tömmer —
och gick därför igenom med sabotaget på. Provet har nu sin egen kopia av
kraven, och den kopian är den grammatiska sanningen: säger modulens tabell
något annat är det provet som säger ifrån.

#### GRINDEN BYGGD — OCH DEN BLOTTAR ETT VAL (2026-08-28)

`befolka` tar numera `böjningsceller` och skapar bara ändelsekort för celler
stegen öppnat. `dimensioner.upplåst_vid(språk, nivå)` ger båda mängderna ur
samma lista — konstruktionerna och cellerna — vilket är hela poängen med en
gemensam numrering: de kan inte glida isär, för de var aldrig två.

**Verbändelser per nivå, mätt:**

    fr    nivå 1: 2    nivå 6: 8    nivå 12: 16    nivå 54: 68    ogrindat 90
    de    nivå 1: 0    nivå 6: 4    nivå 12: 8     nivå 28: 16    ogrindat 62
    sv    nivå 1: 0    nivå 6: 2    nivå 12: 4     nivå 25: 8     ogrindat 20

**En bugg i min första grind:** den nycklade på SPRÅK, och eftersom stegen
bara känner verbcellerna föll substantivens och adjektivens ändelser bort
helt — tyskans 241 ändelsekort blev 16. Nyckeln är nu `(språk, ordklass)`,
och en ordklass utan stege passerar ogrindad i stället för att försvinna.

**Och `kort.sql` gick inte att köra.** `Spår` skapades utan `IF NOT EXISTS`
medan migrationen skapar den vid anslutning, och `skapa_kortdatabas` ansluter
FÖRE den kör schemat. Ingen ny kortdatabas kunde skapas — det bröt `ordbok
kort --återinitiera`, tyst, tills ett prov råkade skapa en.

#### VALET: VAD ÄR ETT ÄNDELSEKORT NYCKLAT PÅ? (`?`)

Grinden fungerar men får en följd som måste avgöras först. Franskans K0:

    pres_1sg = e     ← projektionen gör den till ett steg
    pres_3sg = e     ← UTELÄMNAD, ändelsen är redan lärd

Med grinden skapas alltså inget kort för `(K0, pres_3sg)`. Men meningen
`Elle parle.` slår upp just den cellen, och utan kort går ändelsen inte att
attribuera eller pröva där. Att ta bort det tomma läromomentet tog med sig
attributionen.

**Två vägar, och de är olika stora:**

*Nyckla kortet på (klass, ÄNDELSE) i stället för (klass, cell).* Då är `e`
ETT kort som täcker både 1sg och 3sg, och båda cellernas uppslag pekar på
det. Det är vad Julius insikt egentligen säger — det man lär sig är
ändelsen, inte cellen — och det gör det tomma momentet omöjligt i stället
för bortfiltrerat. Kostnaden är `_nyckel` för systemkort plus
beroendekartans (klass, cell) → kort-uppslag.

*Skapa alla cellkort men SCHEMALÄGG bara de upplåsta.* Kortet finns för
attributionens skull, nivån styr när det kommer i kön. Mindre ingrepp, men
det tomma momentet finns kvar som ett kort som aldrig lär ut något.

Den första är riktigare och den andra billigare. Frågan är Julius.

**Inte påbörjat.** Julius: *"Vi behöver inte lösa alla problemen nu."*

### F3 ? — Två oberoende tak, och ett tredje som inte styrs

**Komplexitetsstegen** (21 nivåer) styr konstruktioner: objekt, bisatser,
perfekt. **CEFR** styr ord: A1, A2, B1. De är oberoende, och att blanda ihop
dem vore att påstå att den som lärt sig bisatser också kan alla ord.

**Men meningens STORLEK är en tredje axel, och den styrs inte.** Ingenting
hindrar en gigantisk mening inom nivåns konstruktioner. Det enda som håller
emot är `längd`-vikten på −0,15 per enhet, som inte är ett mål utan en
mjuk motvikt. Det finns ingen målstorlek och ingen tillväxt över tid.

**Storlek och svårighet är samma ratt sedd från två håll.** Σ(1−R) växer med
antalet kort i meningen, så en större mening är en svårare mening redan av
det skälet. **Vore budgeten nåbar (C2) skulle storleken styras av den
automatiskt** — sökningen skulle bygga längre meningar när korten är starka
och korta när de är svaga, utan att någon talar om storlek. Med budgeten
trasig är storleken godtycklig.

F3 är alltså nedströms C2. Att införa ett eget storleksmål vid sidan av
budgeten vore att bygga en andra svårighetsratt, med samma dubbelräkning
som C2 varnar för.

### F4 ~ — Vad ska visas innan en nivå öppnas?

Lektionen: vad steget är, exempel, och orden det för in. Plus glosläget, som
löste kallstarten (H2) — en nybörjare fick meningar där varje ord var okänt.

**Invändningen är riktig och den är samma sak som D3 och E5.** Att visa
facit strax innan kortet prövas gör provet meningslöst för FSRS. Med
skärpning: NYA kort är undantagna — deras första möte ÄR introduktionen, och
FSRS begynnelsestabilitet (2,307 för Good, alltså 2 dygn) är byggd för exakt
det. Problemet gäller kort som redan har historik.

**Förslaget att dra i stället för att trycka** är bra och konkret:

- nya ord låses UPP under passet men tvingas inte på användaren
- en knapp "lär dig nya ord" visar högst tio
- orden kommer ETT i taget
- ord nummer två släpps in först när ord nummer ett lämnat passkön

Den sista punkten är den viktigaste, eftersom den kopplar införseltakten till
faktisk inlärning i stället för till en kvot (`NYKVOT = 2`, som fortfarande
är en gissning). Den gör också glosläget till en frivillig del av passet i
stället för en port man måste igenom.

**Lösningens ena halva står under D3.** Ett kort med historik som visas i
lektionen eller glosläget skjuts upp till nästa dygn med `skäl = visad`, så
att det inte kan betygsättas i samma pass. Nya kort är undantagna: deras
första möte ÄR introduktionen, och FSRS begynnelsestabilitet är byggd för
det. Därmed är den mätfelsdel av F4 som var akut åtgärdad.

**Öppet är den andra halvan** — dra i stället för att trycka: hur "lämnat
passkön" definieras när passet är slut, och hur förslaget samsas med
`dagsplan`, som räknar nya kort som en del av dagens arbete och därmed av
villkoret för att dagen är klar (B5).

**OCH DEN ANDRA HALVAN ÄR AKUT, mätt 2026-08-24.** Med tidsspärren på plats
(B2) fyller INTRODUKTIONEN hela dagen. Provet körde en kallstart och drillen
delade ut portion efter portion tills tiden var slut — noll meningar. Skälet
är att drillen och meningarna drar ur samma budget och drillen erbjuds först:

    portion  1: 10 ord   ...   portion 20: 200 ord   meningar: 0

Användarens egen formulering fångar precis vad som saknas: *"man ska både få
introduceras till ord och få göra meningar — det är två olika saker."* Och
förslaget i den här posten säger redan hur: ord nummer två får inte läggas
till förrän ord nummer ett har övats. En ORDNINGSREGEL, inte en kvot — och
därmed inget nytt tal.

#### LÖSNING — BYGGD 2026-08-24

**Signalen tas ur SPECEN, inte ur betygen.** Det var inte det uppenbara valet
och det var nödvändigt: en mening lämnar inte alltid ett `Repetition`-spår per
koncept — dygnsregeln hoppar över redan bedömda kort (E2), skyddade och
undanhållna får rader utan betyg, och ett kort kan sakna rad helt. Mätt fall:
meningen `You play.` lämnade NOLL koncept med rad. `Mening.spec` är däremot
exakt, eftersom den ÄR vad meningen byggdes av.

**Regeln kräver inget nytt tal.** Portionsstorleken finns redan, och villkoret
är att förra portionen ska vara övad. Den är dessutom SJÄLVUTLÖSANDE: den
gäller bara ord införda IDAG, så ett ord som inte går att bygga en mening
kring (B8) låser inte drillen längre än till nästa dygn.

**Tre saker behövdes, och de två sista hittades genom att mäta:**

    1.  DRILLEN STÄNGS medan oövade ord finns. Ensam gjorde den bara skada:
        drillen stängde utan att ge något i stället.
    2.  ORDEN BLIR MÅLORD. Ett nyinfört ord är SETT och ligger två dygn bort,
        alltså varken förfallet eller osett — det stod inte i kön och kunde
        därför aldrig bli det generatorn byggde kring.
    3.  ORDEN LÄGGS I KÖN. Att bara ge dem som målord räckte inte heller:
        målordet styr vad samplaren bygger kring, men POÄNGEN avgör vilken
        kandidat som vinner, och ett ord utanför kön bidrar noll till
        täckningen. Mätt gav steg 1+2 fjorton meningar i rad om osedda
        substantiv medan de tio drillade orden låg orörda.

**Och att öva ett nyinfört ord räknas nu som arbete.** Utan det trodde dagen
att den var tom så snart budgeten var spenderad — tio ord infördes och
programmet sa "klart" utan att ett enda använts i en mening. Kön är därmed
inte längre bara FSRS kö utan DAGENS ARBETE, vilket är den ärligare
definitionen: B5 säger att dagen är slut när arbetet är gjort.

**KVAR: hur SNABBT de övas är inte löst.** Mätt går tio oövade ord ned till
fem på fjorton meningar — riktningen är rätt men takten är trög, eftersom ett
osett substantiv täcker tre kort (stam, ändelse, genus) mot det oövade ordets
ett. Det är en VIKTNINGSFRÅGA, alltså C4, och den är blockerad på data. Att
trimma den för hand nu vore att uppfinna ett tal.

### F5 ? — Stegen är slut vid 21

**Svaret är att man aldrig blir färdig,** och det är samma svar som Anki ger:
högen krymper, den tar inte slut. Kunskap är inte något man lär sig en gång
utan något som underhålls. Efter nivå 21 finns alltså ingen ny progression —
bara ett dygn som blir kortare och kortare allteftersom intervallen växer.

**Att låta meningarna växa i stället** är en riktig observation med en
räknebar konsekvens: samma antal kort packas i färre meningar, så passet blir
ännu kortare. Tre effekter, och de drar åt olika håll:

- varje kort prövas i rikare sammanhang, vilket rimligen är bättre
- felet blir svårare att lokalisera — det är precis vad `längd`-vikten finns
  till för (C4)
- en misslyckad mening kostar fler kort på en gång, så passkön blir hackigare

Det är samma avvägning som F3 och C2, vilket är ett gott tecken: det betyder
att en lösning på budgeten löser även den här.

**Öppet:** om nivå 21 ska vara slutet på stegen eller om stegen ska fortsätta
med djup inom konstruktionerna (inbäddade bisatser, längre satskedjor). Det
finns djup kvar i renderarna som stegen aldrig ber om.

---

## G. Hur vet vi att systemet fungerar? — mätbarhet

Hela det här området är underarbetat, och det är den ärliga bedömningen. Vi
har byggt mätpunkterna men aldrig ställt oss framför dem och läst av.

### G1 ✓ — Nollmodellen

För varje ställd mening sparas två tal i `Mening`:

    förväntat   Σ(1−R) över meningens SEDDA kort — FSRS egen förutsägelse
                av hur många kort som kommer att bli fel
    fel         hur många som faktiskt blev fel

Skillnaden är det enda som skiljer två förklaringar åt när ett pass gick
dåligt: **"meningen var för svår"** mot **"korten var svaga"**. Blev fyra kort
fel och FSRS förväntade sig fyra fel var meningen normal och kunskapen svag.
Blev fyra fel när FSRS förväntade sig 0,3 var det meningen som var fel byggd
— eller rättningen som skyllde fel (D1).

Utan det talet är varje klagomål på svårighetsgrad ofalsifierbart, och varje
åtgärd blir en gissning som inte går att utvärdera.

Osedda kort räknas INTE in — ett osett kort har R = 0 och att summera det
vore att påstå att FSRS förutsäger ett säkert fel. Talet blev då två
storheter adderade, förväntade fel plus antalet nya ord, och därmed
oanvändbart.

### G2 ? — Vilka av våra tal är falsifierbara?

Ett tal är falsifierbart om det finns en observation som skulle kunna visa
att det är fel. Det är inte en filosofisk finess utan en praktisk
sorteringsregel: den avgör om ett tal får kallas en mätning eller ska kallas
en preferens.

**Falsifierbara:**

    desired_retention = 0,90   mät faktisk andel rätt på förfallodagen.
                               Är den 0,75 är parametrarna fel (E7).
    NYKVOT = 2                 mät felfrekvens som funktion av antal nya
                               kort i meningen.
    okändgränsen = 1           mät felfrekvens vid noll, ett och två okända
                               ord (C5).
    budget                     nollmodellen G1 mäter den direkt.

**Flyttade till den falsifierbara kolumnen 2026-08-23, av C2:s lösning:**

    täckning = 10              upphör att vara en vikt — blir täljaren i
                               kvoten återkallelser/sekund.
    längd = −0,15              upphör att vara en vikt — blir nämnaren, mätt
                               i sekunder per ord. Den motiverades tidigare
                               med lokaliserbarhet, vilket inte mäts; med tid
                               i nämnaren har varje ord en mätbar kostnad.

Det var avgränsningens målfunktion som gjorde det möjligt. Utan ett uttalat
mål ("teorin, så effektivt som möjligt") fanns ingen nämnare att mäta mot,
och då KUNDE effektivitet inte vara annat än en åsikt.

**Kvar som inte falsifierbara:**

    koncentration = 3          en upplevelsepreferens — och den ska kanske
                               formuleras om helt, se C4.
    upprepning = −1,5          variation, alltså smak. Får stå som en sådan.

**Och ett tal som inte stod någonstans alls** (funnet 2026-08-24 genom att
gå igenom varje konstant i koden mot det här dokumentet):

    GLOSPORTION = 10           hur många ord glosläget delar ut åt gången.
                               Ett verkligt val som styr hur inlärningen
                               känns, och det fanns varken härlett eller
                               nämnt. Ett odokumenterat tal går inte ens att
                               bedöma som falsifierbart eller inte.

Genomgången i övrigt: `STANDARD_MENINGAR_PER_DAG = 20` är reservmålet innan
tid mätts, nämnt i B4 men inte som ett tal. Resten av konstanterna i koden är
bitmasker eller hör till ordboksverktygen, utanför inlärarsystemet. `kandidater`
trådas konsekvent som 800 genom både sökningen och F1:s tröskel, så
byggbarhetens härledning vilar på samma tal som verkligheten.

Poängen med listan är att de fyra senare inte ska LÅTSAS vara mätningar. De
är val, de får vara val, och de ska stå som val. Det som däremot inte får
hända är att ett falsifierbart tal aldrig prövas — och det är läget för alla
fyra i den övre listan, eftersom loggen tog slut (G3).

### G3 ! — Loggen var till 98 % oanvändbar

För att pröva något om inlärning behövs repetitioner som BÄR information,
alltså sådana där utfallet var genuint osäkert. Ett rätt svar på "kan du det
här tio sekunder efter att du skrev det?" bär ingen information alls — FSRS
förutsäger rätt med sannolikhet 0,999, och att det blev rätt bekräftar
ingenting.

Mätt: av 447 prövningar av redan sedda kort skedde **438 vid R ≥ 0,99**.
Alltså var 98 % av loggen brus. Orsaken var att varje mening betygsatte alla
sina kort utan avdrag, och samma kort återkom flera gånger per pass.

Orsaken är åtgärdad (E2). Men konsekvensen står kvar: **allt som skulle
mätas mot den loggen är fortfarande omätt**, eftersom mätningen börjar om
från noll. Det är därför så många poster i det här dokumentet är `~` och inte
`✓` — de vilar inte på fel antaganden, de vilar på oprövade.

#### VAD LOGGEN INTE BEVARADE ALLS (2026-08-27)

Julius mätte symptomet: *"jag gjorde jättejättemånga olika typer av fel men
ändå så växte inte again. Vissa gånger krympte till och med new/due."*

Frågan gick inte att svara på ur `Mening` och `Repetition`, därför att de
bara bevarar UTFALLET. **Tre saker fanns i minnet en kort stund och
kastades:** vad användaren skrev, vad diffen såg, och varför varje kort fick
eller inte fick en dom. Den sista är den avgörande — ett kort utan
`Repetition`-rad kan ha hamnat där på fem sätt med helt olika innebörd.

`Spår` bevarar alla tre. Den läses aldrig av schemaläggningen; skulle den
göra det vore den inte ett spår utan en del av modellen.

**Diagnosen på Julius egen kurs, ur de rader som ändå fanns.** Tretton
franska meningar, 26 augusti:

    #132  Tu existes.   fel=2   →  tu: Again   es: Again   ∅: undanhållen
    #133  Tu coûtes.    fel=2   →  ETT kort, och det var undanhållet
    #140  Tu existes.   fel=1   →  NOLL rader
    #141  Tu coûtes.    fel=0   →  NOLL rader
    #142  Tu as.        fel=0   →  NOLL rader

**Fyra av tretton meningar var upprepningar av en tidigare mening i samma
pass** — `J'ai`, `Tu as`, `Tu coûtes`, `Tu existes` ställdes två gånger var.
Andra gången bokförde de ingenting, och på #140 gjorde Julius fel utan att en
enda rad skrevs.

Det är INTE en bugg utan två medvetna regler som möts:

    rätt + redan bedömt idag   →  hoppas över (E2, en dom per kort och dygn)
    fel  + redan fällt idag    →  hoppas över (felet är redan bokfört)

Kortet låg alltså redan i Again, felet var sant, och räknaren stod stilla —
korrekt i varje enskilt steg och obegripligt som helhet. **Och det är precis
vad "new/due krympte" var**: ett kort som bedömdes i mening 3 kan inte
bedömas igen i mening 7, så senare meningar ser tomma ut fast de gjort sitt.

Den verkliga frågan reglerna blottar är alltså inte bokföringen utan
GENERATORN: varför ställdes samma mening två gånger i ett pass om tretton?
Meningsrummet på nivå 1 med franskans ordförråd är litet, och det är samma
gräns som B8 mätte. Den frågan står öppen.

**Ett andra fynd föll ut direkt när spåret fanns.** På svaret `Tu blabla.`
mot facit `Je m'ai.` fick båda `ordföljd`-korten betyget RÄTT — "subjekt före
verb" och "objektspronomen före verbet" bedömdes som klarade, på ett svar
utan igenkännbar struktur. Ordföljdskort får rätt så snart diffen inte kan
visa att ordningen bröts, och ett svar som inte går att analysera bryter
ingenting. Det höjer deras stabilitet på ingenting alls. Står som `?`.

### G4 ~ — Skyddsnät mot tysta fel

Regressionsnätet fryser 490 renderade meningar som förväntad utdata. Varje
ändring som rör deras text faller.

#### VERIFIERINGSMASKINEN FANNS OCH HADE ALDRIG KÖRTS (2026-08-27)

Julius: *"Det är inte svårt att fixa en bugg MEN det är svårt att verifiera
vad som är trasigt. Jag kan inte verifiera eftersom det tar för mycket tid
och eftersom jag inte är expert på grammatik. Just nu känns mycket som en
svart låda."*

`ordbok granska-meningar` var byggt för precis det, med fyra modellfria
kontroller som uttryckligen skrevs för att *"kunna köras som ett
regressionstest"*. **Det stod ändå utanför sviten, och ingen rapport hade
någonsin skrivits.**

Det är nu ett nät, `strukturprov.py`, över svepkorpusen plus varje mening som
faktiskt ställts. Kontrollerna kräver varken expert eller modell:

    saknat_led        renderingen kraschade, eller gav färre än två led
    överflödigt_led   samma ord två gånger i rad
    lexikalt          en intern nyckel läckte ut som ett ord
    kongruens         TVÅ OLIKA SPECAR RENDERAR IDENTISKT

Den sista går inte att se genom att läsa en mening i taget, och det är den
som gör nätet värt mer än en stavningskontroll: skiljer sig specarna men inte
texten har renderaren tappat en distinktion.

**Nätet fällde min egen ändring i samma andetag.** Reflexivbygget gav tre
fynd — `Nous nous dépêchons` — som alla var falsklarm: franskans `nous` och
`vous` är de enda pronomen vars subjektsform sammanfaller med klitikat.
Undantaget är nu en sluten lista. Att lista det gör kontrollen skarpare; att
ta bort kontrollen hade förlorat den.

**Modellgranskningen är fortfarande manuell och hör inte hemma i sviten** —
den ringer ut, kostar tid och pengar, och `_vägra_i_claude_code` hindrar den
från att köras härifrån. Den spärren är riktig: den som skrev renderaren ska
inte vara den som ensam intygar att den är rätt.

#### JAG RAPPORTERADE GRÖNT PÅ EN INAKTUELL KÖRNING (2026-08-26)

Nivågrindens rättelse (F1) gjorde `passprov`-invarianten *upplåsning utökar
dagen* omätbar, och det upptäcktes först dagen efter. Skälet är inte att
provet var svagt utan att **jag startade sviten i bakgrunden och fortsatte
redigera medan den gick** — den rapport jag sedan läste som "elva nät, alla
gröna" beskrev ett träd som inte längre fanns.

Det är samma sorts fel som posten om ärvd förutsättning nedan, fast i tiden i
stället för i databasen: ett resultat som gällde ett annat läge än det man
tror sig ha prövat. **En svit som startats före den sista redigeringen är
inte ett kvitto på den.**

Felet i sak var däremot provets, inte produktens. `utöka` lägger till upp
till `tak_nya − väntande_nytt`, och den drill som gör kursen redo att låsa
upp fyller samtidigt dagen ända till taket. Mätt: varje kurs nådde
upplåsningen med rummet noll — tyskan på tak 5 med 5 redan planerade — så
110 nya kort blev möjliga och dagen stod stilla. Det är RÄTT: taket är
minutbudgeten (B4), och att låsa upp en nivå höjer inte hur lång tid
användaren har.

Provet höjer numera minuterna FÖRE upplåsningen och fångar `före` efter
höjningen, så att minuternas verkan redan ligger i utgångsvärdet och
tillväxten bara kan komma från upplåsningen. Sabotaget fäller fortfarande
invarianten, vilket är det som skiljer en rättad uppsättning från en
bortförklarad.

**Vad det fångar:** förändringar. Om en renderarändring bryter något som
fungerade syns det direkt.

**Näten är numera elva.** `renderarbild` (renderarna), `omkastningsprov`
(omkastningsdetektionen), `attributionsprov` (skuldstegen, D1/A4),
`tjänsteprov` (tjänstens invarianter, G6), `introduktionsprov` (C5:s tre
vägar in), `ordföljdsprov` (A7 punkt 2), `indikatorprov` (hemskärmens tal,
H3), `passprov` (passets livscykel, B5), `felsvep` (attributionen under
systematiska fel), `arbetsbördeprov` (B2:s och F1:s aritmetik) och
`samplarprov` (att en spec är hel, C5b).

#### OCH DE KÖRDES ALDRIG I FÖLJD (2026-08-26)

Elva skript utan gemensam ingång. Ett skyddsnät som kräver att man minns elva
filnamn körs inte, och ett nät som inte körs är inget nät — samma slutsats
som körtiden gav en gång, tillämpad på uppställningen i stället för på
prestandan.

Första gången allt kördes i följd låg **två fel tysta i näten själva**, och
båda är av den sort det här avsnittet varnar för:

    passprov       "upplåsning utökar dagen" var TOM. Uppsättningen
                   nollställde kursen för att få rum att utöka i — men en
                   nollställd kurs har noll sedda ord, alltså byggbarhet
                   noll, alltså "inte redo", vilket är RÄTT beteende (F1).
                   Varje kurs föll ut genom `continue`, ingen kontroll
                   kördes, och provet rapporterade grönt. Det var
                   FALSIFIERINGSPASSET som avslöjade det: sabotaget som
                   slår av `utöka` helt fällde inte provet.

    indikatorprov  "kostnad per läge finns när takten finns" var FÖR STARK.
                   Den krävde ett tal för både mening och glosa så snart den
                   poolade takten fanns. Men takten är poolad över båda
                   lägena medan uppdelningen skiljer dem åt, så en kurs vars
                   hela tidtagna historik är drill har ett giltigt poolat tal
                   och inget meningstal. Mätt är det precis franskans läge:
                   elva glosor tidtagna, noll meningar. Provet fällde koden
                   för att den vägrade hitta på ett tal.

Det är samma två sätt att ha fel som `omkastningsprov` gav på det hårda
sättet — en invariant som är tom, och en som är för stark — och att de kom
tillbaka i nya nät säger att risken är strukturell och inte en engångsmiss.

*Rättat: `passprov` drillar nu upp byggbarheten en portion i taget och prövar
upplåsningen efter var och en, och den KRÄVER att minst en kurs faktiskt
nådde en upplåsning — annars rapporterar den att den inte mätte något.
`indikatorprov` kräver att takten och uppdelningen är ense om VAD som är
mätt, åt båda hållen, i stället för att kräva ett tal som inte finns.*

**Ingången är `ordbok/verktyg/alla_prov.py`**, snabbast först, med `--snabb`
för de fyra som tar sekunder. Hela svepet tar 7,5 minuter och slutar med en
tabell. Mätt 2026-08-26: elva nät, alla håller.

**En gräns som står kvar:** listan i `alla_prov.py` är handskriven. Ett nytt
prov som ingen lägger till körs lika lite som förut.

#### DEN FARLIGASTE FELTYPEN I NÄTEN: EN ÄRVD FÖRUTSÄTTNING (2026-08-26)

Fyra gånger på en dag visade sig ett prov bero på vilket tillstånd
`kort.db` råkade ha, i stället för att ställa upp sitt eget. Fyra olika prov,
fyra olika symptom, samma orsak:

    passprov      "upplåsning utökar dagen" — uppsättningen nollställde
                  kursen, vilket stänger dörren provet skulle gå igenom.
                  Varje kurs föll ut genom `continue`. TOM.

    passprov      "grannkursen överlever" — grannens dag var redan klar
                  innan provet började, så det fanns inget att förlora. TOM.

    introduktions "meningen införde ett ord själv" — 12 brott, och alla
                  falska. Julius låste upp franskan till nivå 21; `befolka`
                  är additiv, så beståndet fick modalverb med rang 0.
                  Modalverb kräver `komplement` (nivå 13), så på en lägre
                  nivå gick INGEN mening att bygga av de drillade orden,
                  reservutgången löste ut, och provet kallade C5:s avsiktliga
                  undantag för en läcka.

    tjänsteprov   "passet tar slut" — sabotaget slutade bita när dagen inte
                  längre behövde nödutgången. Gott tecken, stumt prov.

**Det är samma sak som ett falsifieringspass finns till för**, en nivå upp:
ett prov kan vara grönt av slump lika gärna som av riktighet, och
falsifieringen fångar bara det andra fallet om uppsättningen håller.

**Regeln som föll ut:** ett prov ska ställa upp sin egen förutsättning och
SÄGA IFRÅN när den inte gick att etablera. `passprov` kräver numera att minst
en kurs nådde en upplåsning mitt i en dag, och nollställer grannen först.
`introduktionsprov` bygger om kortbeståndet för den nivå det mäter på —
nivån är provets parameter och tas inte längre ur kursen — och skiljer en
mening som krävde reservutgången från en läcka.

**Och den skillnaden krävde en flagga i koden.** C5 kallar reserven "ett
UNDANTAG som syns, inte den vanliga vägen", men den syntes ingenstans:
`Förslag.reserv_släppt` finns nu och säger att sökningen fick släppa
begränsningen till kända ord. Utan den går "meningen införde ett ord" inte
att skilja från "ingen mening kunde byggas ur det användaren mött", och det
är två helt olika påståenden.

**`felsvep` är av ett annat slag än de andra.** Det svarar inte ja eller nej
utan ger ett TAL. Attributionen hade lagats fem gånger, varje gång utifrån ett
fall Julius råkade skriva — en metod där varje lagning ser komplett ut tills
nästa mening avslöjar nästa hål, och ingen vet hur många som är kvar. Svepet
genererar meningar, förstör dem på KÄNDA sätt (annan cell, annat ord,
utelämnat, extra, omkastning, stavfel, missad sandhi) och räknar tre utfall:
falskt godkännande, fel skuld, tystnad.

Mätt 2026-08-25, 1 258 prövningar:

    fr   418 prövningar   0 falska betyg   0 fel skuld   183 tysta
    de   420              3                0            145
    en   420              0                0            179

De tre kvarvarande är alla samma sort — genusfel på artikeln, där skulden går
till substantivets genuskort (rätt enligt D2) medan artikelns formkort får
Good. Det finns ett argument åt vardera hållet: användaren härledde artikeln
KORREKT ur sin felaktiga tro om genus, vilket är samma form som "rätt stam,
fel ändelse" en koordinat upp. Alla utom det
första har ett FALSIFIERINGSPASS: varje kontroll körs också med felet
återinfört och måste då falla.

Det har lönat sig sex gånger, och fem av dem var provet självt som ljög: en
tom invariant, en för stark, ett sabotage som tystnade när koden omkring
ändrades, ett sabotage som bara återskapade halva det gamla läget, ett som
inte nådde tjänsten eftersom `from ... import` behöll den gamla klassen efter
`reload`, och ett prov vars utfall berodde på hur mycket Julius råkat öva.
**Ett falsifieringspass fångar mest sina egna prov** — och det är dess
huvudsakliga värde, eftersom ett grönt prov annars är omöjligt att skilja
från ett prov som inte mäter något.

**Näten var för dyra att köra, och orsaken var en läcka.** `tjänsteprov` tog
47 minuter väggtid men bara 112 sekunder processortid — fyra procents last,
alltså blockerat på något som inte var räkning.

`with sqlite3.connect(...)` avslutar en TRANSAKTION och inte anslutningen. Varje
prov lämnade därför en läsare kvar mot den riktiga kortdatabasen — sexton
stycken när falsifieringen var klar — och varje ny `backup` fick vänta ut dem.
Att stänga båda anslutningarna tog körningen från 2 830 s till 61 s.

Att felet var svårt att se berodde på att var FAS för sig var snabb: de åtta
invarianterna tar 39 s körda direkt, falsifieringen 68 s. Kostnaden växte med
antalet läckta anslutningar, alltså bara när allt kördes i följd.

Det spelar roll, och inte som en bekvämlighet: ett prov som tar tre kvart körs
inte inför varje ändring, och ett skyddsnät som inte körs är inget skyddsnät.

**Vad regressionsnätet inte fångar:** fel som redan fanns när korpusen frystes. Var
franskans reflexiva verb trasiga då, frös korpusen buggen som facit. Det är
exakt vad som hänt med de fyra kända felen i C7 — de passerar nätet varje
gång.

Problemet är alltså korpusens TÄCKNING, inte nätets konstruktion. Ett nät som
täcker allt kan inte byggas för hand; det kräver antingen sveptäckning (som
`nåbarhet.py` gör för C6) eller extern granskning (G5).

### G5 ? — Hur upptäcks att en koppling försvunnit?

`Cellkort` var tom för tyskan i en månad utan att något sa ifrån. Under den
tiden betygsatte tyska meningar bara ordkort — böjningen mättes inte alls, och
inget i gränssnittet såg annorlunda ut. Det är den farligaste feltypen i hela
systemet, eftersom "inga kort hittades" och "inga kort finns" ser likadana ut
i koden.

En **invariantkontroll** är en uppsättning påståenden som alltid måste vara
sanna om databasen, körda vid start eller i test. Till exempel:

- varje `schemalagt = 1`-kort ska vara nåbart via minst en väg
  (`Cellkort`, ordkort eller egenskapskort)
- varje språk med kort ska ha `Cellkort`-rader
- varje kort ska höra till ett koncept som finns i `sprak.db`
- summan av korttyper per språk ska matcha vad `befolka` säger att den skapar

Det första påståendet hade fångat BÅDE `Cellkort`-tömningen (I3) OCH de
onåbara ordföljds- och rektionskorten (A3). **A3, B8 och G5 är alltså samma
saknade kontroll**, sedd från tre håll.

**Den externa granskningen** — en kraftfull modell som fritt renderar
övningar, kontrollerar dem alla, och enligt formulär kartlägger exakt vad som
inte fungerar — är rätt verktyg för C3, C7 och G4, men inte för G5.
Granskningen läser meningar; invarianten läser databasen. Ett tomt `Cellkort`
ger inga felaktiga meningar, bara färre betyg, och det syns inte i texten.
Båda behövs.

**Öppet:** formulärets form (vad granskaren ska svara på för att svaren ska gå
att sammanställa), och hur en sammanställd brist blir en ändring i databasen
eller renderaren utan handpåläggning per fall.

---

### G6 ~ — Gör alla vägar in i systemet samma sak?

`dagsplan` räknar dagens arbete: hur många kort som förfallit, hur många nya
som får införas, om dagen är klar. Den är systemets enda auktoritet på de
frågorna, och den räknar rätt.

**Men ingenting tvingar ändpunkterna att fråga den.** Varje väg in —
glosläget, uppgiften, extraövningen, hemskärmen — är fri att räkna själv
eller att låta bli att räkna alls. Gör de olika saker finns det inget som
säger ifrån, för båda svaren är i sig giltiga; det är bara att de inte är
samma.

**Fem fall, alla funna vid ett enda testpass 2026-08-24:**

    glosläget       delade ut tio nya ord VARJE gång vyn öppnades, utan att
                    läsa dagsbudgeten. Hemskärmen visade rätt tal hela tiden.
                    Mätt vid upptäckten: 44 införda kort mot ett tak på 34.

    `svara`         läste passkön INNAN `bokför` uppdaterat den, så räknaren
                    för återförsök låg alltid en mening efter. Det såg ut som
                    att fel "ibland" inte hamnade i kön.

    extraknappen    var öppen även när dagens kort inte var gjorda. Att öva
                    extra före de förfallna korten är att välja bort det FSRS
                    garanti vilar på (B6).

    nivåkolumnen    läste fält som tagits bort ur svaret och visade ett
                    trasigt tal i stället för att märkas.

    generatorn      gav samma mening åtta gånger i rad till passkön, trots
                    att B7 uttryckligen säger "i en ANNAN mening".

**Varför det är EN post och inte fem.** Ingen av dem motsäger teorin. Motorn
gjorde vad dokumentet säger; ändpunkterna frågade den bara inte. Det är
samma feltyp fem gånger, och den typen är osynlig för det här dokumentet —
PROBLEM.md beskriver vad systemet ska GÖRA, inte om alla vägar in gör samma
sak.

**Samma form som G5, fast för beteende i stället för data.** G5 saknar en
invariant över databasen ("varje schemalagt kort ska vara nåbart"); G6 saknar
en över anropen. Kandidater till en sådan kontroll:

    · ingen ändpunkt får införa fler nya kort än `dagsplan["nya"]`
    · det tal en vy VISAR ska komma ur samma anrop som styr handlingen
    · en mening får inte ställas två gånger i rad
    · extraövning kräver `dagsplan["klar"]`

De tre första går att pröva automatiskt genom att köra ett pass och jämföra
vad ändpunkterna gjorde med vad `dagsplan` sa. Det är ett prov av samma slag
som `omkastningsprov.py`, fast över tjänsten i stället för över en funktion.

#### LÖSNING — BYGGD 2026-08-24

`ordbok/verktyg/tjänsteprov.py`. Fem invarianter, körda mot en KOPIA av
inlärardatabasen — provet övar, svarar fel och inför kort, så det får aldrig
röra den riktiga:

    dagsbudgeten hålls av alla vägar in    öppnar glosvyn sex gånger och
                                           mäter DELTAT den själv orsakar
    extraövningen går att köra             lovar den kort ska de gå att få ut
    passet tar slut                        rätta svar ska tömma dagen
    uppgiften överlever att vyn lämnas     samma mening när man kommer
                                           tillbaka, ny först efter svar
    visat tal = styrande tal               hemskärmens glostal och
                                           uppdelningens ordrad mot vad vyn ger
    extraövning kräver klar dag            `finns` måste vara noll tills klar
    ingen upprepad mening                  tio meningar, alla besvarade fel
    räknaren i takt med bokföringen        `svara` mot antalet fällda kort

**De tre nya kom av att fem fall till hittades 2026-08-24, alla av samma
sort:**

    uppdelningen    sa "Words 7" på en dag där glosläget hade noll att dela
                    ut. `ord` står först i introduktionsordningen och tog
                    därför hela dagstaket `nya`, medan drillen styrs av
                    `nya_ord` — dagens tilldelning delad mellan drillen och
                    meningarna.

    passvyn         byggde en NY mening varje gång man kom tillbaka, och
                    kastade den obesvarade. Vilket kort som övades blev
                    därmed en funktion av hur man klickade.

    extraknappen    kastade `ProgrammingError` när den faktiskt hade kort —
                    fyra platshållare, tre bindningar i `kommande()`. Osynlig
                    eftersom `finns_extra` var noll i varje kurs som testats
                    för hand, så frågan aldrig ställdes.

    extraläget      lovade ett kort som sökningen inte kunde röra. Samma
                    onåbarhet som dagens kö kan ha (B8), men extraläget har
                    en EGEN kö och behövde därför ett eget minne av
                    mätningen. Mätt på japanskan.

**Och en gräns som står kvar:** minnet av att ingenting går att bygga är
knutet till KURSEN, medan kortbeståndet är per MÅLSPRÅK. Två kurser mot samma
språk (sv→fr och en→fr) mäter alltså var för sig, och den som inte öppnats
lovar arbete som den andra just konstaterat vara onåbart. Det är avsiktligt så
länge det står — källspråket avgör om uppgiften går att rendera, så en mätning
på den ena kursen gäller inte den andra — men det betyder att talet kan vara
gammalt tills passet öppnas.

**Och provet bevisar att det KAN falla.** Varje invariant har ett SABOTAGE:
den gamla, trasiga varianten av regeln, återinförd genom att byta ut metoden.
Körs provet med sabotaget påslaget ska varje kontroll falla — och gör den inte
det är det PROVET som är fel, inte koden. Utfall:

    ✓ föll  dagsbudgeten hålls av alla vägar in
    ✓ föll  visat tal = styrande tal
    ✓ föll  extraövning kräver klar dag
    ✓ föll  ingen upprepad mening
    ✓ föll  räknaren i takt med bokföringen

Det är samma lärdom som `omkastningsprov.py` gav på det hårda sättet: den
första invarianten där var TOM och kunde inte falla, den andra var FÖR STARK
och föll på ett äkta ordfel. Ett prov utan falsifiering är en trosbekännelse.

**Två regler fick namn för att kunna brytas.** `_igen_efter` och `_extraläge`
låg som uttryck inne i en dict och gick inte att sabotera. Att bryta ut dem
gjorde dem både läsbara och prövbara — en invariant som inte går att
falsifiera bevisar ingenting.

**Posten står som `~` och inte `✓`.** De fem invarianterna håller och är
prövade åt båda hållen, men ingenting tvingar en NY ändpunkt att omfattas.
Mekanismen finns; täckningen är ett antagande. Nästa steg vore att låta
provet räkna upp ändpunkterna själv och kräva att var och en rör `dagsplan`.

#### DEN SJÄTTE ÄNDPUNKTEN GICK INTE ATT LAGA (2026-08-26)

`ordbok öva` var en hel övningsslinga i terminalen: generera, visa, läs svar,
rätta, registrera. Den läste aldrig `dagsplan`, skrev aldrig i `Pass`, kände
inte glosläget och lydde inte dagens tak. Den körde mot nivå 21 med
`budget = 1.5` — talet C2 mätte som matematiskt onåbart — och betygsatte rakt
in i den riktiga `kort.db`.

Det är exakt felklassen posten beskriver, men det femte fallet skiljer sig
från de fyra ovan: de gick att laga genom att låta ändpunkten fråga motorn.
Det här kommandot hade ingenting att göra som webbtjänsten inte gör bättre,
och att koppla in det i passlagret hade varit att bygga en andra
användarupplevelse för att kunna hålla den synkroniserad med den första.

**Borttaget.** Behövs ett pass utan webbläsare finns
`ordbok/verktyg/passkörning.py`, som går genom `Övningstjänst` och därmed
genom samma regler användaren möter.

**Det stärker posten i stället för att bara lösa ett fall:** varje ändpunkt
som tas bort är en ändpunkt som inte kan glida isär. Täckningen är fortfarande
ett antagande, men den yta antagandet gäller är mindre.

*(Kommandot var dessutom trasigt vid borttagningen — det föll på C5b i varje
anrop, eftersom det körde nivå 21. Att ingen märkt det på tio dagar är i sig
måttet på hur lite den vägen användes.)*

## H. Gränssnittet

### H1 ✓ — Vad ska synas när man övar?

Så lite som möjligt: meningen, fältet, och de tre talen (nya kort kvar,
återförsök, kvar idag). Detaljen finns bakom en knapp. Serif för språk,
rubriker, tal och dom; sans för gränssnitt.

### H2 ✓ — Kallstarten

En nybörjare fick meningar där varje ord var okänt. Orden läses nu innan de
ska produceras (glosläget), och generatorn föredrar högst ett okänt ord per
mening (C5). Se F4 för hur införseln borde dras i stället för tryckas.

### H3 ~ — Vad betyder siffrorna?

Uppdelning per korttyp, vilka kort meningen prövar, och när de förfaller —
bakom en i-knapp.

**Avvägningen är den svåra delen, och den är inte löst.** Två krav drar åt
motsatt håll:

- programmet får inte bli överväldigande
- programmet får inte vara en svart låda

Anki löser det bra: man ser tydligt de nya korten, vad som ska repeteras, vad
som misslyckades och ska läras om, och har en klar överblick över sin
inlärning — utan att något är abstrakt. Vårt system har mer att förklara än
Anki (varför just den här meningen? varför just de här korten?) och därför är
risken för överväldigande större, men behovet av förklaring också.

**Öppet:** vad som ska vara synligt hela tiden och vad som ska ligga bakom en
knapp. Mycket av trycket lättar när statistiksidan finns (H4).

#### LÖSNING (2026-08-25) — ett prov för talen själva

Frågan ovan handlar om vad som ska VISAS. Den här posten fick en andra halva
som handlar om något enklare och mer akut: **stämmer det som redan står?**

Ett tal som är fel larmar inte. Det ser ut som alla andra tal, det uppdateras
som alla andra, och det enda som avslöjar det är att man gör vad det säger och
får något annat. `ordbok/verktyg/indikatorprov.py` gör just det — invarianterna
är formulerade som HANDLINGAR och inte som formler, för att jämföra `att_göra`
med `förfallna + igen + nya` vore att skriva om samma uttryck en gång till.

    dagen tar slut om man följer skärmen    drilla `glosor`, kör passet, fråga igen
    inget tal lovar mer än ändpunkten ger   `glosor`, `igen`, uppdelningens ordrad
    att_göra är summan av sina delar        på varje MELLANLÄGE, inte bara först
    inget tal för ett låst läge             extraövningen medan den är låst
    minuter_kvar följer arbetet             `att_göra` × mätt takt
    kostnad per läge finns när takten finns två tal ur samma logg

**Tre fel hittades, och alla tre var av samma sort: ett tal som beskrev ett
annat ögonblick än meddelandet bredvid det.**

*"1 new" på en klar dag.* Passvyn hämtar dagsläget, ritar räknarna och
uppdelningen, och frågar SEDAN efter en uppgift. Det är under det anropet
passet kan upptäcka att inget av dagens nya kort går att bygga en mening kring
(B8) — och skärmen sa då "Done for today" med talen kvar på det den trodde
innan. Samma fel gav "7 new" gången före. *Rättat: talen hämtas om när passet
svarar tomt.*

*Extraövningen visade tal medan den var låst.* `finns` nollades redan när
dagen inte var gjord, men `nya` och `tidiga` skickades ändå. Ett tal ingen
knapp kan lösa in är precis den sortens indikator som ser sann ut och inte är
det. *Rättat: låst läge rapporterar noll rakt igenom.*

*Två tal ur samma logg var oense om huruvida något var mätt.* Takten sa
"3,67 s/rep" för tyskan — ärvt från franskan, som `sekunder_per_repetition`
uttryckligen ska göra — medan `kostnad_per_läge` sa None, eftersom den krävde
tyska rader. Och tröskeln räknade BETYG i stället för TIDTAGNA rader, så ett
språk med 33 repetitioner utan en enda klocka såg mätt ut. *Rättat: samma
reservväg och samma tröskel som takten.*

#### OCH DÄRFÖR MISSADE PROVET NÄSTA OMGÅNG (2026-08-26)

Provet ovan mäter API:t. Det som stod på SKÄRMEN mätte ingenting, och sidan
räknade själv — så när en genomgång av gränssnittet gjordes fanns fyra fel
kvar av precis den sort provet skrevs för.

**RUBRIKEN OCH RADEN UNDER DEN SUMMERADE INTE.** Hemvyn räknade fram sin egen
uppdelning i JS: `former = max(0, nya − glosor)`. Men `nya` och `glosor` är
OLIKA ROLLER i `Passkort` och överlappar aldrig — subtraktionen drog bort ett
tal som inte ingick. Mätt på fem kurser:

    kurs 1   rubriken 57 kort, raden under summerade till 52
    kurs 2   rubriken 48, raden 45, knappen under dem 5
    kurs 3   rubriken 50 kort, knapptexten "0 due · 0 new"

Den sista är den värsta: hela dagen var femtio glosor, och knappen sa att det
inte fanns något att göra. Subtraktionen var en kvarleva från när `nya`
innehöll ordkorten.

**TRE VYER, TRE TAL FÖR SAMMA SAK.** "Ord som återstår" fanns på tre skärmar:

    hemvyn      "Words in this level's vocabulary: 1 058"
    kursvyn     "201 left"
    glosvyn     "5 of 205 words left"

`1 058` var OSEDDA KORT av alla sju typer för hela språket — 428 genuskort,
373 stammar, 202 ordkort, 27 ändelser, 18 former, 6 rektioner, 4
ordföljdsregler. Etiketten sa "words" och "this level's". `201` var en
KVOT: osedda kort delat på kort-per-koncept, alltså en skattning. `205` var
det räknade svaret.

**ETIKETTER SOM ÖVERLEVT SITT TAL.** Rutan för nästa nivå visar sedan F1 en
DOM och inte ett antal, men etiketten `cards to go` stod kvar bredvid. Skärmen
sa ordagrant "Ready cards to go".

**ETT TAL SOM RÄKNADES OCH SEDAN KASTADES.** `slut()` deklarerades med ett
argument och anropades med två; det andra var antalet kort som skrivits av som
onåbara (B8). Det betyder att dagen tog slut i FÖRTID, och utan raden ser en
avkortad dag exakt ut som en fullbordad — vilket är precis vad A3 säger att
den inte får göra.

*Rättat, och inte var för sig.* Uppdelningen räknas nu i `pass_.läget` och
skickas som en LISTA av (nyckel, antal) som per konstruktion summerar till
`att_göra`; sidan renderar den och räknar ingenting. Ordräkningen är en
`COUNT(*)` på osedda ordkort och läses av alla tre vyerna ur samma anrop.
Etiketten är borta. Avskrivna kort sägs.

**Invarianten är utökad:** `att_göra är summan av sina delar` prövar numera
också `delar`-listan, alltså det gränssnittet faktiskt ritar, och kräver att
ingen del bär en nolla. Verifierat att den faller: med den gamla
JS-subtraktionen serverflyttad ger den två brott på första varvet.

**Lärdomen är var gränsen gick.** Provet frågade "stämmer talen servern
räknar" — och det gjorde de. Frågan som saknades var "stämmer det som står",
och den kunde bara ställas genom att flytta räkningen till servern. Ett prov
som kör JavaScript hade varit det andra svaret, och det sämre.

#### TVÅ TAL OM TVÅ OLIKA ÖGONBLICK (2026-08-26)

Julius: *"när jag kör pass och har uppe info så ser jag new, due och again
både på huvudraden och vid inforaden... de är inte synkade. De visar olika
info precis efter att man gjort klart en övning men sen klickar next så blir
de samma igen."*

Det var inte en kapplöpning utan två källor.

    huvudradens `igen`   `svara` returnerar `_igen_efter`, en PROGNOS av vad
                         generatorns passkö BLIR när meningen bokförts
    uppdelningens tal    passet SOM DET ÄR, ur `Passkort`

`svara` körs före `bokför` — självrättningens fönster ligger emellan — så de
två beskriver olika ögonblick och kunde aldrig vara ense förrän man klickade
Next. Då blev de det igen, precis som observerat.

*Rättat: räknarna rörs inte längre i `svara`.* Både räknarna och uppdelningen
ritas i `nästa()`, ur samma `/api/dag`-svar. Att kortet gick till återförsök
syns ändå direkt — kortlistan ritar ett ✗ på just det kortet, vilket är
besked om SAKEN i stället för om en totalsumma.

**Meningsräknaren är ett undantag och ett ärligt sådant:** meningen ÄR gjord i
samma stund man svarat, oavsett bokföring.

**Och den andra halvan av observationen — att inga kort tycktes komma till
"again" — var inte gränssnittets fel utan B7:s.** Se den posten: en `igen`-rad
skapades bara för kort som stod som `väntar`, så ett kort som redan var
avklarat idag och sedan fälldes räknades ingenstans.

### H6 ~ — Vilket språk talar gränssnittet? (ny 2026-08-26)

Programspråket är engelska och är avsiktligt INTE kursens källspråk — en
svensk som lär sig tyska kan vilja ha engelskt gränssnitt. All
gränssnittstext ligger därför samlad i `T` i sida.html, med noteringen att
ett andra programspråk är en kolumn där och ingenting annat.

**Utom att den inte låg samlad.** Fyra sorters text gick förbi `T` och rakt
ut på skärmen på svenska, och tre av dem i det ögonblick användaren är som
mest beroende av att förstå — direkt efter ett fel:

    rättningens slutsatser   "fel stam — skrev formen för pres_3sg"
    ordföljdsreglerna        "finita verbet på plats två i huvudsats"
    korttyperna i lektionen  "129 new cards: 115 stam, 9 system, 5 form"
    ordklasserna i ordboken  "Substantiv", "Artikel", "Frågepronomen"

De två första kom ur `Rättare` respektive `Kort.facit`; de två sista var
databasens egna nycklar utskrivna rakt. Och just `stam`, `system` och `form`
är de tre ord en inlärare omöjligt kan känna till — de är systemets
kortmodell, inte språkets grammatik.

**Rättat med samma rörelse tre gånger:** backend skickar en NYCKEL och det
nyckeln handlar om, `T` sätter texten. `Anmärkning` fick `nyckel` och `arg`
vid sidan av `slutsats`; ordföljdskorten fick sin `egenskap` med i
kortlistan; lektionen och ordboken slår upp sina nycklar i `T`.

**Den svenska prosan är KVAR i `Anmärkning.slutsats`**, och det är inte
slarv. Den är vad `__str__` skriver, alltså vad som står i loggar och i
felsvepets utskrifter — och den är gränssnittets reserv när en nyckel saknas.
Ett gränssnitt som tiger om ett fel är värre än ett som säger det på fel
språk.

**Vad som INTE översattes, med flit.** Cellnamnen (`pres_3sg`) och
formsträngarna (`haben`, `hab`, `∅`) står kvar. De förra är ett
paradigmspråk och inte svenska, och de står i samma form i ordboksvyn; de
senare ÄR svaret — att röra dem vore att visa något annat än det kortet
prövar.

**Posten är `~` och inte `✓`.** Ingenting hindrar nästa sträng från att gå
samma väg. Det som skulle stänga felklassen är en kontroll som läser
API-svaren och fäller på svenska ord i fält gränssnittet visar — samma form
som G6 saknar för anrop och G5 för data, alltså tredje gången samma sorts
invariant efterlyses.

### H4 ? — Hur presenteras framsteg över tid?

Det finns ingen vy för utveckling — bara dagens läge och nästa nivå.
Statistiksidan är den planerade lösningen: hur långt man kommit, hur framtiden
ser ut, hur belastningen utvecklas. Den bär också en del av H3.

Notera att den blir svår att göra ärlig så länge B2 gäller: en prognos som
bygger på `per_kort` skulle visa en framtid som är fel med en faktor tio. En
statistiksida som ljuger om framtiden är sämre än ingen.

### H5 ~ — Vad händer på mobil?

Layouten viker sig, men inget är prövat på riktigt. Nedprioriterat: det
viktigaste är att motorn fungerar perfekt först.

#### PRÖVAT 2026-08-26 — den håller

Mätt i en riktig webbläsare på 375 × 812, hela vägen genom hemvyn, glosvyn
och övningen:

    horisontell scroll     ingen (scrollWidth 375 = innerWidth)
    de två kolumnerna      staplas, båda läsbara
    räknarraden            343 px av 375 — och håller med TRESIFFRIGA tal
                           (prövat med 148 / 132 / 276 / 104)
    navigationen           bryter till två rader, allt nåbart
    inmatningsfältet       full bredd, tangentbordet skymmer inget

Posten går därmed från `?` till `~`: den är prövad i en emulerad vy och inte
på en verklig telefon, och tangentbord, `100vh` och safe-area är sådant som
bara riktig hårdvara avslöjar.

**Ett fel hittades och rättades på vägen, och det gällde inte mobilen.**
Ordparen i glosvyn låg i tre kolumner med `flex:1` på målordet, vilket sköt
översättningen till kolumnens högerkant — på en bred skärm två centimeters
tomrum mellan `gehen` och `gå`. Just den vyns enda uppgift är att PARET ska
fastna, och layouten tvingade ögat att leta rätt på vilken översättning som
hörde till vilket ord. Nu står de på två rader, tätt, som i en glosbok.

---

## I. Data och drift

### I1 ✓ — Inlärardatabasen får aldrig gå förlorad

`kort.db` är en egen fil, ligger aldrig i git, och raderas aldrig av en
ombyggnad. Den innehåller repetitionshistorik som inte går att återskapa —
`sprak.db` kan byggas om ur ordlistorna, `kort.db` kan det inte.

**DEFEKT, upptäckt 2026-08-24: `cp kort.db` är ingen giltig säkerhetskopia.**

Databasen körs i WAL-läge. Skrivningar hamnar i `kort.db-wal` och flyttas
till huvudfilen först vid en checkpoint. Mätt vid upptäckten:

    kort.db + kort.db-wal   129 repetitioner, 42 meningar
    bara kort.db            108 repetitioner, 31 meningar

WAL-filen var 515 kB. En kopia gjord med `cp`, Finder, rsync eller vilket
filverktyg som helst tappar alltså allt som ligger där — och det är precis
det NYASTE, alltså det som är dyrast att förlora. Kopian öppnas utan fel och
ser fullt frisk ut; ingenting säger ifrån.

**Rätt sätt** är SQLites egen backup, som läser genom WAL:

    sqlite3.connect("kort.db").backup(sqlite3.connect(mål))

eller `sqlite3 kort.db ".backup mål"`. Att först checkpointa
(`PRAGMA wal_checkpoint(TRUNCATE)`) och sedan kopiera fungerar också, men
bara om ingen skriver samtidigt.

**Åtgärdat i vad som går att åtgärda:** `.gitignore` fångar numera
`kort.db.*` och `säkerhetskopior/` explicit — mönstret `*.db` överst matchade
INTE `kort.db.före-D3-20260824`, eftersom filnamnet slutar på datumet. Två
säkerhetskopior hade alltså kunnat hamna i git.

**ÅTGÄRDAT 2026-08-24: `db.säkerhetskopiera()`, anropad ur `anslut_kort`.**
Alltså vid varje programstart, för varje väg in i databasen — servern, CLI:t,
vad som helst. Fyra egenskaper, och tre av dem finns för att en
säkerhetskopia som ljuger är värre än ingen:

    en per dygn        dagens fil finns redan → returnera den. Mätt: andra
                       anslutningen samma dygn tar 0 ms mot 39 ms för den
                       första.

    verifierad         `integrity_check` OCH radantal per tabell mot
                       originalet. Håller det inte tas filen bort igen.
                       Prövat med två sorters trasiga kopior — en som tappat
                       fem rader och en förstörd på filnivå — och båda
                       avvisas med ett besked som namnger avvikelsen
                       ("Repetition: 129 rader i original, 124 i kopia").

    gallrad            trettio dagliga kopior. Talet kommer ur projektets
                       egen historia: den längsta TYSTA felfunktionen hittills
                       var `Cellkort`-tömningen, oupptäckt i en månad. En
                       kortare fönstring hade inte hjälpt då.

    aldrig blockerande Full disk ska inte låsa användaren ute ur sitt eget
                       program. Men det får inte ske tyst heller: varningen
                       går till stderr.

**Gallringen rör bara de DAGLIGA kopiorna.** Mönstret är avsiktligt strikt —
`kort.db.20*` hade också matchat `kort.db.2026-08-24.före-nollställning`,
alltså precis den kopia som aldrig får försvinna. Namngivna kopior, tagna
före en migrering eller en nollställning, gallras aldrig automatiskt.

**`skapa_kortdatabas` tar en egen kopia först.** Det är den farligaste
funktionen i kodbasen — den raderar repetitionshistoriken — och kopian
namnges med en räknare så att den inte kan skriva över en tidigare.

### I2 ✓ — Ingenting i kortlagret får peka på ett id i språkdatabasen

`sprak.db` har heltals-id för koncept och lexem. De är interna och byts när
databasen byggs om — vilket den gör varje gång ordboken ändras.

Lagrade kortlagret dem skulle en ombyggnad tyst peka om varje kort till ett
annat ord. Inget skulle krascha; kunskapen skulle bara sakta bli fel, och
felet skulle märkas först när användaren undrade varför hen fick frågor på ord
hen aldrig sett.

Därför lagras bara **naturliga nycklar**: `koncept` = `'fam_mamma'`,
`variant`, `cell` = `'n_nom'`. De betyder samma sak före och efter en
ombyggnad. Det är den regeln som gör att ordboksarbete och inlärning kan
pågå samtidigt utan att det ena förstör det andra.

### I3 ✓ — Befolkningen kunde radera andra språks kopplingar

`befolka` körde `DELETE FROM Cellkort` utan språkfilter. Att skapa en
engelsk kurs raderade alltså tyskans hela beroendekarta — och tyskan
betygsatte därefter bara ordkort, i en månad, utan att något syntes.

Åtgärdat: raderingen är numera `WHERE språk = ?`. Data återställdes ur
säkerhetskopia och verifierades byte för byte mot `Repetition`, `Kort` och
`Mening`.

Felet i sig är löst. **Felklassen är det inte** — det som gjorde det farligt
var att ingenting kontrollerade att kopplingarna fanns. Se G5.

### I4 ? — Migrationerna är ett manuellt steg

`kort.sql` är schemat. Ändringar (`Repetition.självrättad`, `Kort.rang`) har
lagts in i den levande databasen för hand med ALTER TABLE. Ingenting
kontrollerar att en given `kort.db` har det skick koden förväntar sig.

Två felsätt, och det andra är det otäcka:

1. Koden läser en kolumn som inte finns → krasch. Synligt, ofarligt.
2. Koden skriver till en kolumn som finns men betyder något annat, eller läser
   ett fält som aldrig fyllts i och tolkar `NULL` som ett värde. Tyst.

Det behövs ett versionsnummer i databasen och en kontroll vid start.

#### ETT TREDJE FELSÄTT, MÄTT 2026-08-26 — migreringen som aldrig blev klar

Sedan posten skrevs fick migrationerna en automatik: `_migrera` körs ur
`anslut_kort`, alltså vid varje anslutning. `NYA_TABELLER` är idempotent av
sig själv (`CREATE TABLE IF NOT EXISTS`), men `OMBYGGNADER` — de som måste
kopiera en tabell, eftersom SQLite inte kan ändra en främmandenyckel med
ALTER — vilar på ett VILLKOR som ska svara "är det här redan gjort".

Villkoret för `passkort_bevara_bevis.sql` löd

    sql LIKE '%ON DELETE CASCADE%kort_id%'

och det matchar `pass_id`-radens `ON DELETE CASCADE` följt av ordet `kort_id`
längre ner. Den FÄRDIGMIGRERADE tabellen ser likadan ut i just det avseendet.
Villkoret var alltså sant för alltid.

**Följden är att användarens passtabell byggdes om vid varje programstart.**
`DROP TABLE Passkort`, med `PRAGMA foreign_keys = OFF`, följt av en
kopiering — i varje CLI-anrop, varje serverstart, varje prov. Mätt genom att
läsa tabellens `rootpage` över fyra anslutningar: 398 → 367 → 394 → 391.

Datan överlevde varje gång, så ingenting syntes. Men det är en oskyddad
DROP av inlärardata på ett ställe där ingen väntade sig en skrivning alls, och
ett avbrott mitt i den hade tagit dagens pass med sig.

**Det som gjorde felet möjligt är samma sak som posten redan pekar på:
ingenting kontrollerar att databasen har det skick koden tror.** Villkoret
LÄSTE schemat, vilket var rätt tanke — men det läste dess TEXT och inte dess
innebörd. `pragma_foreign_key_list('Passkort')` svarar på den faktiska frågan
(vilken ON DELETE-regel `kort_id` har) och kan inte råka matcha en annan
kolumns regel. En textmatchning på ett schema är en gissning; en
pragma-avläsning är en mätning — och det är samma skillnad som resten av det
här dokumentet handlar om.

**Och källan sa emot rättelsen.** `pass.sql`, filen som skapar tabellen på en
NY databas, deklarerade fortfarande `kort_id INTEGER NOT NULL … ON DELETE
CASCADE` — alltså precis det fel ombyggnaden finns för att laga. En ny
installation byggdes fel och reparerades sedan. Nu deklarerar den `SET NULL`
direkt, och ombyggnaden finns kvar bara för databaser som redan är skapade.

*Rättat 2026-08-26. Verifierat åt tre håll: en redan migrerad databas rörs
inte (rootpage står stilla över tre anslutningar), en databas i den gamla
formen lagas exakt en gång (CASCADE → SET NULL, rootpage 6 → 9, raderna
kvar), och en ny databas är rätt från början.*

**Posten står kvar som `?`.** Versionsnumret och startkontrollen finns
fortfarande inte. Det som ändrats är att den ena migreringen nu vet om den är
gjord — vilket är en lagning av ett fall, inte av felklassen.

### I5 ? — Ordlistorna är handskrivna

736 koncept i sju språk (per språk: de 736, en 734, es 740, fr 733, it 733,
ja 732, sv 741 lexem).

**Vem avgör vad som är rätt lemma:** idag en modell, med efterkontroll i
praktiken — fel upptäcks när de dyker upp i övningar och rättas då. Det är en
rimlig ordning så länge granskningen (C3, G5) finns, eftersom den gör
upptäckten systematisk i stället för slumpmässig.

**Hur listorna ska växa,** i tre steg och inte brådskande:

1. Nu: 736 koncept är redan mycket kunskap, och flaskhalsen är inte ordbanken
   utan renderarna och rättningen.
2. Sedan: manuell utökning område för område, med frekvensordböcker som stöd
   för att inte missa något viktigt. Samma data som B3 behöver.
3. Senare: användare lägger själva till koncept — särskilt ord för yrke och
   intressen — och får en personligt anpassad ordbank.

Steg 3 är det som ställer verkliga krav på arkitekturen: användarskapade
koncept måste kunna leva i `sprak.db` utan att kollidera med de inbyggda vid
en ombyggnad, och de saknar per definition den nivå- och CEFR-märkning som
urvalet (B3, F3) bygger på.

---

## Sammanräkning

    ✓  löst          25
    ~  antagande     12   (H5 prövad, H6 ny)
    ?  öppet         16
    !  känd defekt    8   (C5b tillkom 2026-08-26 och är rättad, men står
                    ───    som `!` enligt dokumentets regel: en post byter
                     61    status när NÅGON läst efter, inte när koden ändras)

## Vad som gjordes 2026-08-26 — en genomgång som inte utgick från buggarna

*Uppdraget var inte att jaga symptom utan att förstå systemet och rensa det
som är gammalt eller trasigt. Metoden blev därför: läs hela dokumentet, kör
HELA skyddsnätet för första gången i följd, och mät varje misstanke innan den
kallas ett fel.*

**Det gav fyra fynd som inget symptom hade pekat på.**

    C5b  `_välj` ger upp — tolv av fjorton anropsställen tog inte emot det.
         Krasch ur `föreslå` från nivå 8 (40 av 40 anrop), och 4–27 % tyst
         kastade kandidater från nivå 5. Osynligt i drift bara därför att
         kurserna stod ETT steg under första fällan.

    I4   `passkort_bevara_bevis.sql` körde om vid VARJE anslutning. Villkoret
         som skulle svara "redan gjort" matchade en annan kolumns regel och
         var sant för alltid. Alltså DROP TABLE på användarens passtabell vid
         varje programstart, mätt på tabellens rootpage.

    G4   Två av näten mätte inte det de påstod: ett var TOMT (uppsättningen
         stängde dörren provet skulle gå igenom) och ett var FÖR STARKT (det
         krävde ett tal som inte kan finnas). Det första hittades av
         falsifieringspasset, alltså av näten själva.

    E6   `sätt_schemalagt` skrev över alla språks flagga — I3:s felklass,
         fortfarande på plats i en annan funktion.

**Och tre saker togs bort i stället för att lagas.**

`ordbok öva` var en sjätte ändpunkt förbi `dagsplan` och `Pass`, och den var
dessutom trasig (den föll på C5b i varje anrop, oupptäckt i tio dagar).
Den gamla `per_kort`-matten i `upplåsningsläge` hade en enda läsare kvar.
`dagsplan`s eget `klar` var ett andra svar på en fråga passlagret redan äger.

**Den gemensamma formen på alla sju**, och det är dagens egentliga slutsats:

> Ett villkor som är sant på ett ställe och oläst — eller olikt läst — på ett
> annat.

Det är samma form som A3 (kort utan väg), G5 (kopplingar som försvinner),
G6 (ändpunkter som inte frågar) och I3 (skrivningar utan språkfilter) redan
beskriver, var för sig. **De fyra posterna är inte fyra problem utan ett**,
och det som saknas är inte fler lagningar utan en invariant som ställer
frågan automatiskt.

**Vad som INTE gjordes, med flit.** Ingen av de öppna designfrågorna avgjordes
— C2:s tak, C4:s vikter, E6:s tröskel, F1:s förkunskapsvillkor. De kräver
mätning eller ett beslut, och båda hör till Julius. Det som gjordes var att ta
bort det som var osant eller dubbelt, så att de frågorna ställs mot en grund
som inte rör sig.

    ✓  varje spec som lämnar samplaren är hel        prov: samplarprov
    ✓  migreringen vet om den är gjord               verifierad åt tre håll
    ✓  näten mäter det de påstår                     två rättade, ett tillagt
    ✓  hela nätet körs med ett kommando              alla_prov.py, 7,5 min
    ✓  `klar` räknas på ett ställe                   dagsplan svarar inte längre
    ✓  schemaflaggan skrivs språkvis                 I3:s felklass, sista fallet
    ✓  en ändpunkt färre att hålla synkroniserad     ordbok öva borttaget

## Vad som byggdes 2026-08-24

Sju poster gick från beskrivna till byggda, och två av dem ändrade form under
bygget därför att räkningen sade något annat än planen.

    A7  omkastningsdetektion — ett flyttat ord fäller inte längre ordkortet
    D3  uppskjutning av kort utan mätning; stänger E5, och F4:s mätfelsdel
    B4  minuter per dag ersätter meningar per dag
    B2  inflödesstyrning ur en FSRS-simulerad kostnadskurva
    F1  grinden är byggbarhet, inte kapacitet
    I1  verifierad automatisk säkerhetskopiering
    C5  noll okända ord i en mening — tre vägar in stängda
    A4  stammen i försöket bevisar att ordet hämtades fram
    B8  passet kan ta slut: nödutgången, målsilen och minnet av mätningen
    C4  målorden varvas i prioritetsordning, de lottas inte
    B6  extraövningen går att köra igen — och den ger inte plats åt nytt
    G6  fem fall till i sömmen mellan motor och skärm
    —   tidsloggning, växelkursen mellan minuter och kort

**Två saker visade sig vara räknefrågor, inte designfrågor.** Kostnads-
horisonten i B2 har ett exakt svar så snart man sagt över vilken tidsrymd
målet ska hålla. Och F1:s kapacitetsgrind visade sig skydda ingenting — B2
styr takten oavsett vilka nivåer som är öppna, så villkoret kunde tas bort
i stället för att räknas om.

**Ett förslag föll efter mätning:** E6:s grind på oinformativa möten. Den gav
ett kort med åtta dygns intervall efter två år för en användare som
bevisligen producerat ordet 243 gånger. Att kasta bevis gör inte loggen
renare, det gör modellen fel.

**Och fem fel i sömmarna hittades vid första testpasset** — se G6. Ingen av
dem motsäger teorin; ändpunkterna frågade bara inte motorn.

## Vad genomgången 2026-08-23 ändrade

*Historisk anteckning. Flera av posterna nedan byggdes dagen efter — se
avsnittet ovan och respektive posts egen status, som alltid gäller före den
här sammanfattningen.*


Antalet lösta poster sjönk från 31 till 22. Det är inte att systemet blivit
sämre — det är att nio påståenden visade sig vara oprövade eller falska när
de mättes.

**Nya defekter, alla mätta:**

- **A3 / A7** — `ordföljd`- och `rektion`-korten är strukturellt onåbara (12
  tyska, 5 franska, 3 engelska, 4 japanska). Och en ren ordföljdsomkastning
  skylls idag på ORDKORTET för det flyttade ordet, alltså på kunskap
  användaren bevisligen har.
- **D3** — ett undanhållet kort skyddas inte av dygnsregeln, står kvar som
  förfallet, och kan klaras i nästa mening för fullt Good direkt efter att
  facit visats. Mätt: S 10,96 → 46,28 i stället för till ~11.

**Nedgraderade från `✓` till `~` eller `?`:**

- **B2** — `per_kort` är ett medelvärde över unga kort och överskattar
  kostnaden kraftigt. `kort_per_mening` har fallit från de påstådda 5,3–6,7
  till 2,2–5,0 sedan avdragsreglerna kom.
- **D1** — stegens sista pinne (skyll på det svagaste kortet) är en gissning,
  och loggen sparar inte vilken pinne som fällde kortet, så träffsäkerheten
  går inte att mäta.
- **E5** — det skyddade formkortet står kvar som förfallet samma dag.
- **E6** — tyskan har 0 av 1 112 kort lyfta ur schemat, vilket inte är
  trovärdigt; exponeringsmätningen har sannolikt aldrig körts för den kursen.
- **F1** — upplåsningen är blind för relevans, och kravet rör sig med en
  faktor tio när kortleken mognar.
- **F3** — meningens storlek styrs inte av något, och kan inte göra det förrän
  budgeten (C2) mäter något.
- **F4** — lektionen visar facit strax innan kortet prövas.
- **H3** — avvägningen mellan enkelhet och genomskinlighet är inte gjord.

**Uppgraderat:** I3 från `!` till `✓` — felet är åtgärdat och verifierat.
Felklassen ligger kvar i G5.

**Rättat samma dag:** E3 rekommenderade först att svarstid skulle loggas som
väg till Hard/Easy. Den rekommendationen var fel. Tiden går inte att fördela
över en menings kort, och FSRS egen optimerare skickar uttryckligen
`review_duration=None` när parametrarna anpassas — svarstiden är inte en
variabel i minnesmodellen, bara en kostnad i valet av `desired_retention`.
E3 är omformulerad och därefter STÄNGD: frågan är inte hur Hard härleds utan
om en konsekvent tvågradig signal anpassar parametrarna sämre än en ojämn
fyrgradig, och det avgörs av loggen (E7). Systemet stannar vid två steg.
Svarstid sparas enbart som aggregerad kostnad för `compute_optimal_retention`
och hör därmed till E7. E3 står som `~` och inte `✓` eftersom antagandet bakom
beslutet ännu inte är mätt.

**Ny insikt om C2**, som är den enskilt viktigaste i genomgången: budgeten
1,5 är inte "ännu inte nådd" utan **matematiskt onåbar**. Med
`desired_retention` = 0,90 bidrar ett exakt förfallet kort med 0,10, så en
mening med fem kort där varje kort är förfallet når 0,50. Talet härleddes
aldrig ur kort per mening och retentionsmålet. Det förklarar också varför
C4 (viktningen) och F3 (meningsstorleken) inte går att avgöra ännu: båda är
nedströms budgeten.

## Vad som blockerar vad

    tidsdata       ──►  B4, B2, E7    — loggningen ÄR byggd; talen behöver
                        bara samlas på sig (10 tidtagna pass, sedan 512)
    G1 (nollmod.)  ──►  C2            — taket mäts ur förväntat mot fel
    avgränsningen  ──►  C2, C4, G2    — målfunktionen gav nämnaren
    C2 (kvoten)    ──►  C4, C8, F3, F5  — form, vikter och storlek följer
    G3 (loggen)    ──►  G2, C4, E7, B2, C2  — allt som mäts mot loggen
    G5 (invariant) ──►  A3, B8        — samma saknade kontroll
    C8 (riktning)  ──►  D5            — variantproblemet löses av riktningen
    E7 (loggen)    ──►  E3            — binärt mot fyrgradigt är empiriskt

**Och en post som inte blockerar utan SAMLAR (tillagd 2026-08-26).** Fem
poster i olika delar av dokumentet visade sig vara samma sak, och att de står
på fem ställen är skälet till att var och en lagats för sig, om och om igen:

    A3   ett schemalagt kort utan väg till någon mening
    B8   ett köat kort ingen mening kan byggas kring
    G5   en koppling som försvunnit utan att något sagt ifrån
    G6   en ändpunkt som räknar själv i stället för att fråga `dagsplan`
    I3   en skrivning som sträcker sig utanför språket den bads om
    C5b  ett `None` som ett anropsställe tar emot och elva inte

Formen är densamma i alla sex:

> **Ett villkor som är sant på ett ställe och oläst — eller olikt läst — på
> ett annat.**

G5 föreslår redan svaret för datans del ("varje schemalagt kort ska vara
nåbart via minst en väg") och G6 för anropens. Det som saknas är att någon
STÄLLER frågorna automatiskt i stället för att de upptäcks en i taget när ett
symptom råkar bli synligt. Fem av de sex hittades av en människa som märkte
något konstigt; den sjätte hittades av ett prov.

    G5 + G6  ──►  A3, B8, I3, C5b   — en invariant i stället för sex lagningar
