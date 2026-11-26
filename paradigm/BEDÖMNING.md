# Bedömningen — forskningsläget och tre alternativ

*Plan, 2026-11-26. Metod: läsa vad andra som haft samma problem har gjort, och
ställa vårt upplägg mot deras. Ingen kod är ändrad. Planen fattar inga beslut
— den lägger fram alternativen och säger vilket jag förordar och varför.*

Frågan planen gäller: **hur avgör man vad som blev fel i ett fritextsvar, och
hur lägger man skulden på den kunskapsenhet som ska schemaläggas?**

Det är steg 8 i byggordningen (`KÄRNAN.md` §9). Rättningen är den enda del av
programmet som kan skriva FALSKA rader i inlärarloggen, och en falsk rad
larmar inte — den ser riktig ut.

---

## 1 Vad fältet kallar problemet

Problemet har ett namn och en stor litteratur: **credit/blame assignment vid
flera kunskapsenheter per uppgift.** Formuleringen i översiktslitteraturen:
varje observerad bedömningsenhet som rör flera färdigheter medför betydande
svårigheter att fördela ansvaret.

Två resultat är viktiga för oss.

**1a. Klassisk kunskapsspårning antar EN färdighet per uppgift.** Bayesian
Knowledge Tracing kan inte representera ett steg som kräver flera färdigheter,
och inte heller relationerna mellan dem. Vår mening rör 17 kort. Standard-
verktyget passar alltså inte, och det är inte en implementationsdetalj.

**1b. Ur ett enda felaktigt svar går den skyldiga färdigheten inte att
identifiera.** I konjunktiva modeller (DINA) ger varje saknad nödvändig
egenskap samma utfall — fel. Skulden per egenskap kommer först av att poola
svar över uppgifter vars kravmängder SKILJER SIG. Och särskilt: egenskaper som
bara förekommer TILLSAMMANS med andra är principiellt problematiska.

Punkt 1b är ett omöjlighetsresultat, inte ett svårighetsresultat. Ingen
skicklighet i rättningen tar oss runt det.

---

## 2 Var vi redan står utanför problemet

Vår renderare redovisar vilket kort som bestämde vilket ord (`KÄRNAN` 6.2, 7.3,
8.3). Felet är dessutom lokaliserat till ett ord i en sträng. Alltså **observerar
vi det som litteraturen måste gissa**: för ett ordnivåfel är skulden känd, inte
skattad. Det är projektets största arkitekturfördel och den är inte beskriven
som en sådan någonstans i dokumenten.

Vi står kvar INNANFÖR problemet i precis tre fall:

| Fall | Varför skulden inte är lokaliserbar |
|---|---|
| flera kort bestämmer samma ords form | mätt 2026-11-26: «How many books does the girl **write**?» fäller `do_omskrivning` och `tempusform/presens` fast båda hedrades |
| ordföljd och utelämnade ord | felet sitter mellan orden, inte på ett ord |
| kort som aldrig uppträder ensamma | identifierbarhetsvillkoret i 1b |

**Tredje raden har vi redan rätt datastruktur för.** `KÄRNAN` räknar nivåerna
som de starka komponenterna i kravgrafen (§4). Det är exakt mängderna av kort
som inte går att separera med någon mening. Litteraturens identifierbarhets-
klasser och våra nivåer är samma objekt. Två oberoende härledningar landade i
samma struktur, och det är det starkaste stödet designen har fått.

---

## 3 Tre familjer av lösningar

### A · Deterministiska regler

Handskrivna attributionsregler plus prerekvisitsteg. Traditionen heter ICALL
och har två skolor: **mal-rules** (koda typiska fel som extra grammatikregler)
och **constraint relaxation** (släpp på grammatiken tills meningen parsar, och
rapportera vilka villkor som bröts). Heifts German Tutor och E-Tutor håller en
elevmodell per grammatiskt villkor — strukturellt våra kort plus FSRS.

Det här är vad vi har.

- **För:** exakt, förklarbar, inga parametrar, ingen träningsdata.
- **Mot:** varje regel är en härledd bedömning; den växer med antalet språk;
  och den är tyst fel i fall ingen förutsåg. De 13 anteckningarna i
  `rattning/__init__.py` är alla sådana fall, upptäckta en i taget av en
  människa som körde programmet.

### B · Sannolik skuld

Modellera P(kortet kan) och låt en felaktig mening uppdatera alla inblandade
kort efter sin posterior. Tekniken finns färdig: **conjunctive knowledge
tracing** (Koedinger, Pavlik, Stamper, Nixon & Ritter 2011) med noisy-AND-grindar
i ett bayesianskt nät, vars inferenskostnad växer linjärt och inte exponentiellt.
PFA gör samma sak genom att summera bidragen från alla krävda färdigheter.

- **För:** principiell; hanterar de icke-identifierbara fallen graciöst; kan
  representera «vi vet inte vilket av dessa två».
- **Mot:** den kräver parametrar — slip och guess — som måste skattas ur data
  vi inte har. Vi har en användare och en kursdatabas som nollställs vid varje
  prov. Gissade parametrar är precis de påhittade konstanter projektet förbjuder.
  Den ersätter dessutom FSRS:s per-korttillstånd med en gemensam modell, och
  den tar bort förklarbarheten: frågan «varför kom det här kortet tillbaka»
  får inget svar en människa kan kontrollera.

**Jag förordar att vi avstår från B**, och att vi skriver ner skälet så att det
inte prövas om av slarv. Det är inte ett estetiskt skäl: B byter bort en mätt
storhet mot en skattad, i den enda del av programmet som kan skriva falska rader.

### C · Separera genom konstruktion

Avgör inte från ett svar. Är skulden tvetydig, **generera nästa mening så att
den skiljer kandidaterna** — den minsta meningen som innehåller det ena kortet
men inte det andra.

Det är litteraturens egen lösning på 1b, «poola över uppgifter vars kravmängder
skiljer sig», men konstruerad i stället för avvaktad. Fältet som gör detta heter
**CD-CAT** (cognitive diagnostic computerized adaptive testing): välj nästa
uppgift så att den maximerar informationen om vilken egenskap som saknas.
Standardmåttet är Kullback–Leibler-information (Xu m.fl. 2003), i praktiken
posterior-viktad (PWKL, Cheng 2009), med senare index som MPWKL och GDI som
också balanserar täckningen av egenskaper.

- **För:** det är det vi är ensamma om att KUNNA, eftersom vi genererar
  uppgifter i stället för att dra dem ur en bank. Allt förblir förklarbart och
  parameterfritt. Och vi har redan kravgrafen och minsta meningar.
- **Mot:** det kostar en mening; det kräver entydighetsfiltret (steg 5a) som
  inte finns; och kort i samma starka komponent går aldrig att separera, så en
  oreducerbar rest återstår.

---

## 4 Vad planen förordar

**A för det som är lokaliserbart, C för det som inte är det, aldrig B.**

Och ett tredje tillstånd för betyget, som följer ur C och inte finns i dag:

> Skulden landar på det som är säkert. Det som är tvetydigt **hålls** — inget
> betyg skrivs till FSRS för de korten — och en separerande mening bokförs som
> skyldig.

Det bryter inte mot «rättningen får aldrig tiga» (7.3). Spärren kräver att
NÅGON bär felet, och det gör det kort vars ord faktiskt var fel. Hållna betyg
rör bara de kort som annars hade fått ett påhittat betyg.

I det mätta fallet «How many books does the girl **write**?» betyder det:
`ord:kom_läsa` faller, `ändelse` ograderas som i dag, och `do_omskrivning` och
`tempusform` hålls i stället för att få ett falskt `again`.

Rest som planen inte löser: kort i samma starka komponent. För dem är varken A,
B eller C ett svar — nivån är den enhet som går att mäta, och det är vad en nivå
är till för.

---

## 5 Vad som behöver avgöras innan koden skrivs

| | Fråga | Äger | Läge |
|---|---|---|---|
| 1 | Jämför rättningen mot ETT facit eller en MÄNGD varianter? | Julius; följer av 6.5 | öppen |
| 2 | Får ett betyg hållas, eller måste varje inblandat kort få ett betyg samma dag? | Julius | **ja**, 2026-11-26 |
| 3 | Var bokförs en skyldig separerande mening? | 6.5 + 7.1 | öppen, kräver 5a |
| 4 | Ska beslut om ORDVAL alltid graderas, även när ordet var okänt? | Julius | **frågan upplöstes**, se nedan |

**Fråga 4 behövde inget svar.** Den förutsatte att «beslut om ordval» och
«beslut om form» måste skiljas med en lista över kortfamiljer. Punkt 3 i 7.3
skiljer dem utan lista: artikelbeslutet faller för att ett annat av DESS utfall
skriver just det ord användaren skrev, och tempusvalet hålls för att inget av
dess utfall gör det. Byggt 2026-11-26.

**Rättelse till §3 C.** Planen skrev att C kräver steg 5a. Det gäller den
separerande MENINGEN, som måste genereras. Det gäller inte beslutet om vad som
ska hållas: omrenderingarna som avgör det låg redan i `Beslut.alternativ`, och
rättningen läste dem aldrig. Första delen av C är därför byggd utan 5a.

**Följd i bokföringen.** Ett hållet kort får ingen rad i loggen och blir därmed
inte infört (5.1). Det är riktigt: införandet kräver att kortet gick rätt i en
mening, och ett hållet kort prövades inte.

---

## Källor

- Credit/blame och kunskapsspårningens begränsningar: [Knowledge Tracing: A Survey](https://arxiv.org/pdf/2201.06953) · [BKT-LSTM](https://arxiv.org/pdf/2012.12218)
- Konjunktiv kunskapsspårning: [Koedinger m.fl., Avoiding problem selection thrashing with conjunctive knowledge tracing](https://digitalcommons.memphis.edu/facpubs/7461)
- DINA och identifierbarhet: [Sufficient and Necessary Condition for the Identifiability of DINA](https://arxiv.org/pdf/1711.03174) · [Q-matrix-skattning](https://arxiv.org/pdf/1106.0721)
- CD-CAT och uppgiftsval: [KL-baserade urvalsregler](https://pmc.ncbi.nlm.nih.gov/articles/PMC5978538) · [MPWKL och GDI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6953845/) · [täckningsbalanserad MMGDI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7059599/)
- ICALL, mal-rules och constraint relaxation: [Heift, ZIF](https://tuprints.ulb.tu-darmstadt.de/12151/1/zif-2860-heift.pdf) · [Heift, IJAIED 2016](https://link.springer.com/content/pdf/10.1007/s40593-015-0061-0.pdf) · [ILTS-översikt, BEA 2018](https://preview.aclanthology.org/fix_video/W18-0513.pdf)
- Justering och feltypning: [Bryant, Felice & Briscoe, ACL 2017](https://www.cl.cam.ac.uk/~cjb255/papers/2017-acl/acl2017.pdf) · [Felice m.fl., COLING 2016](https://www.cl.cam.ac.uk/~cjb255/papers/2016-coling/coling2016.pdf)
- Översättningsdivergenser: [Dorr, CL 1994](https://aclanthology.org/www.mt-archive.info/CL-1994-Dorr.pdf) · [Grammatical Framework, Ranta](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/09C4B3F43447ADDB0F632C64F195BC9C/S0956796803004738a.pdf/grammatical_framework.pdf)
