# Överlämning — Språkprogrammet, 2026-08-14

Klistra in det här i en ny chatt.

---

## Vad projektet är

En språkinlärningsapp som bygger meningar på sju språk (sv, en, fr, de, es,
it, ja) ur en gemensam språkoberoende beskrivning. Meningen definieras en
gång och renderas till valfritt språk. Spårar vad inläraren kan ner till
enskild ordform, med FSRS-schemaläggning.

**Scope:** grammatik och böjning. INTE talspråk, idiomatik eller register.

Databasen har tre lager: `Koncept` (språkoberoende begrepp) → `Lexem` (ordet
på ett språk) → `Former` (alla böjda former). Plus `Mönster`/`MönsterKrav`
som styr vilka ord som får kombineras.

---

## Var vi står

**Datalagret, renderaren och restriktionerna är klara. Meningsformen är
utbyggd genom arton nivåer. Generatorn är inte byggd.**

```
Koncept        736        Mönster        271   (universella
Lexem        5 149        MönsterKrav    390    + språkspecifika)
Former      50 026        Attributkrav    73
```

Tre lager fungerar:

1. **Böjning och taggning.** Alla 1 043 fel granskningen hittade är
   åtgärdade; `ordbok tillämpa-granskning --torkörning` ger noll satser.
   Alla sju språk är granskade av en starkare modell.
2. **Renderaren.** Sju språk, en klass per språk, `RomanskRenderare` som
   gemensam bas för fr/es/it. `ordbok rendera --exempel --språk <xx>`.
3. **Semantiska restriktioner.** `Koncept.semantik` × `MönsterKrav.tagg`,
   matchat i disjunktiv normalform: bitar inom en rad är OCH, flera rader
   är ELLER. Validatorn arbetar på **specen**, inte på den renderade
   strängen — alltså en gång för alla sju språk. 68 % av slumpmässiga
   ord­kombinationer avvisas (28 % när mätningen började).

**Nästa steg är meningsgeneratorn** — se
[`paradigm/GENERATOR.md`](paradigm/GENERATOR.md). Den var blockerad av
uttrycksförmågan. Det är den inte längre; se nåbarhetsmätningen nedan.

---

## Vad som gjordes sist (2026-08-13 — 08-14)

Åtta konstruktioner byggdes, en i taget, var och en i alla sju språk innan
nästa påbörjades. Ordningen togs inte på känsla utan **härleddes ur
`MönsterKrav.slot` × `MönsterKrav.frastyp`** — en kolumn som legat ifylld
sedan mönstertaggningen utan att någon läst den. Metoden flyttade
predikativ och modalverb från sist till först, och avslöjade att stegen har
fyra dimensioner och inte en. Se GENERATOR.md, avsnittet med samma namn.

| Nivå | Konstruktion | Fältet i `Mening` |
|---|---|---|
| 10 | genitiv | `Nominalfras.ägare` |
| 11 | predikativ | `predikativ` |
| 12 | negation | `negerad` |
| 13 | infinitivkomplement | `komplement` |
| 14 | perfekt | `Aspekt.PERFEKT` |
| 15 | prepositionsfras | `Prepositionsfras` i `adverbial` |
| 16 | ja/nej-fråga | `fråga` |
| 17 | passiv | `Diates`, båda svenska passiverna |
| 18 | komparation | `Grad`, `jämförelse` |

Renderarna växte med det: `kein` i tyskan, do-support i engelskan,
klitikaordning och sandhi i de romanska, ukemi-passiv och より-jämförelse i
japanskan, Satzklammer och kasusrektion i tyskan.

**Varje utökning drog fram datahål som granskningen inte kunde se**, därför
att hålen inte är felaktiga former utan *saknade* eller *felavgränsade*:

- 47 tyska substantivformer hade artikeln inbakad (`Schwester` →
  `"der Schwester"`). Syntes som "in der der Schule". Granskningen missade
  dem för att de är rätt böjda, fel avgränsade.
- Engelskans `be` saknade am/are/were. "The girls be happy" gick att bygga
  långt innan passiven fanns.
- `verb_ha` es var `tener`; spanskan bildar perfekt med `haber`. Tillagt som
  ett andra lexem under samma koncept med `variant='hjälpverb'`.
- Pronomenen saknade `genus` i fem språk → "elle est heureux".
- Tyskan saknade predikativa adjektivformer (111) och predikativ
  komparativ/superlativ (218). Adjektivparadigmets 144 celler är alla
  attributiva.
- `komp_mer`/`komp_mest` fanns inte. `adv2_mest` en betyder "mestadels".

Det generella mönstret: **det som inte händer syns aldrig i en räknare.**
Sex tysta icke-matchande strängersättningar hittades bara genom att läsa
utdata ord för ord, och två egna bitmask-buggar (`& 65535` och `& 1048575`
som båda skar av semantikbitar) syntes bara som "en dyr sol" respektive
som att 29 av 77 ord fick sin klass.

---

## Nåbarhet: hur mycket av beståndet specen når

Nytt verktyg: [`ordbok/verktyg/nåbarhet.py`](ordbok/verktyg/nåbarhet.py).
Det instrumenterar `Uppslag.form`, sveper hela korsprodukten av det
`Mening` kan uttrycka, och räknar unionen av begärda celler mot lexikonet.

```
sv  3 526 / 4 988   71 %      fr  5 088 /  9 070   56 %
en  1 645 / 2 293   72 %      it  5 097 / 10 246   50 %
                              es  4 637 / 10 596   44 %
ja    770 / 2 498   31 %      de  7 839 / 23 493   33 %
```

Svenskan: 37 % → 45 % (genitiv) → **71 %** (de åtta utökningarna).

**Siffran mäter svepet lika mycket som specen.** Två artefakter hittades och
rättades under mätningen: subjektet var alltid tredje person, vilket fick
hela personböjningen att se onåbar ut, och attributet satt bara i objektet,
vilket bara mätte ackusativ. Tyskan gick 13 % → 20 % → 33 % på de två
rättelserna ensamma. Lägg till dimensionen i svepet innan du drar slutsatsen
att specen inte når en cell.

Vad som faktiskt är onått, efter de rättelserna:

| Språk | Block | Vad som krävs |
|---|---|---|
| de | 96 av 147 adjektivceller — attributiv komparation | `Nominalfras.attribut` bär ingen grad |
| fr/es/it | konjunktiv + konditionalis | bisatser respektive villkorssatser |
| alla | imperativ | satsmodus |
| de | stark deklination m/n sg — "roter Wein" | `Bestämdhet` saknar artikellös fras |
| ja | jisho/ta/nai | register, utanför scope |

**Tyskans 33 % beror på en enda sak.** 16 121 av 23 493 tyska former är
adjektivformer, och två tredjedelar av det paradigmet är komparativ och
superlativ i attributiv ställning. `Grad` finns på `Mening` men styr bara
predikativet. Att flytta graden in i `Nominalfras.attribut` är den enskilt
största utökningen som återstår — värd omkring 10 500 tyska former, mer än
alla åtta gjorda utökningar tillsammans på det språket.

---

## Passivbuggen — lagad 2026-08-14

Nåbarhetssvepet hittade att passiv i futurum och perfekt renderades som
presens i fem språk, och att `PASSIV_HÄNDELSE` + `FRAMTID` kastade
`KeyError` i svenskan. Regressionssvepen såg det aldrig: de sveper inte
diates × tempus × aspekt.

**Orsaken var densamma i alla fem.** Passivgrenen låg först i `verbdelar`
och returnerade innan tempus- och aspektlogiken — den byggde hjälpverbet
med en egen liten tempusmappning som bara kände presens och preteritum.

**Rättelsen tar bort de mappningarna i stället för att fylla på dem.**
Passiven är hjälpverb + particip, och hjälpverbet är ett verb: det böjs som
alla andra. Grenen bygger nu om meningen med `replace(m, verb=<hjälpverbet>,
diates=AKTIV)` och skickar den genom den aktiva grenen. Varje framtida
tempusutökning når därmed passiven gratis, i stället för att behöva skrivas
in på två ställen.

```
              nutid          förfluten        framtid              perfekt
sv   passiv   läses          lästes           ska läsas            har lästs
sv   bli      blir läst      blev läst        ska bli läst         har blivit läst
en            is read        was read         will be read         has been read
de            wird gelesen   wurde gelesen    wird gelesen werden  ist gelesen worden
fr            est lu         était lu         sera lu              a été lu
es            es leído       era leído        será leído           ha sido leído
it            è letto        era letto        sarà letto           è stato letto
ja            読まれます      読まれました      読まれます            読まれました
```

Tre saker föll ut på köpet:

- **Den sammansatta perfektiva passiven** ("a été lu", "è stato letto",
  "ha sido leído") stod som känd gräns och krävde tre verbdelar. Den byggs
  nu av sig själv, och kongruensen blir rätt utan en rad kod om den: `stato`
  böjs i italienskan men `été` inte i franskan, därför att essere tar
  essere och être tar avoir — och hjälpverbsvalet stod redan i datan.
- **Engelskan tappade negationen i passiv** ("The book is read" med
  `negerad=True`) och byggde "does not read" i stället för "has not read".
  Do-omskrivningen finns bara därför att en enkel presens saknar hjälpverb
  att fästa negationen på; den ligger nu sist, dit bara de fallen når.
- **Spanskans sammansatta gren slog upp `verb_vara` utan variant**, vilket
  gav RenderingsFel på "ha sido" eftersom ser och estar är två lexem. Den
  enkla grenen skickade varianten, den sammansatta inte.

**Ett datahål:** tyskt perfekt passiv heter "ist gelesen **worden**", inte
"geworden". Den ge-lösa formen finns bara som passivhjälpverb och låg inte i
databasen. Den ligger nu som en egen cell `part2_passiv` (Sup + Passiv) i
`paradigm/de/verb.yaml`, tom för alla verb utom `werden` — samma lösning som
svenskans s-passivceller, och samma mönster som engelskans nio be-celler.

**Kända täckningsgränser** (inga fel, men bra att veta):

- Mönster finns bara på verb. Schemat tillåter adjektiv och prepositioner
  som styrande ord (`rädd för`, `intresserad av`) — inte taggat.
- Ett mönster per verb. `äta` har ett transitivt mönster, men "hon äter"
  utan objekt är också korrekt. Additivt att lägga till.
- Japanskan saknar infinitivkomplement (modaliteten är suffixal) och skiljer
  inte perfekt från preteritum (た täcker båda).
- Tyska Wechselpräpositionen defaultar till dativ. Riktning kräver en
  målroll som specen inte har.
- `mappa-kaikki` (validering mot Wiktionary-dumpar) är bara implementerad
  för svenska.
- **Granskningens kvittofil skiljer inte på homonymer — men luckan är
  liten.** `granskning.tsv.klara` har en rad per `(språk, lemma)`. Av 177
  homonymgrupper har 126 identiska paradigm (de/finden = hitta/tycka), så en
  granskning av det ena täcker det andra morfologiskt. Kvar: 51 grupper där
  formerna skiljer sig, de flesta korsordklassiga med bara en form på ena
  sidan (en `back`, en `open`). Verkligt behov i en handfull: de/sein,
  de/sicher, es/poder, de/ihr. Fixen är densamma som `tillämpa-granskning`
  fick: nyckla kvittot på koncept i stället för lemma. **Kräver
  `granska-former`, som inte får köras från Claude Code.**
- **`paradigm/it/frågepronomen.yaml` har två celler med identiska
  koordinater.** `chi` och `cosa` är båda `kasus: [Nom, Ack, Dat]` och inget
  annat. Former lagrar axlar, inte cell-id, så en rad som täcker den ena
  täcker med nödvändighet den andra. Ofarligt för renderaren. Går inte att
  åtgärda i datan, bara i slot-filen. Beslutet att låta det vara står i
  `beslut.tsv`. Det enda sådana fallet i alla slot-filer (kontrollerat).

---

## Vad som återstår

1. **Meningsgeneratorn.** Kortmodellen är utredd och nedskriven i
   [`paradigm/GENERATOR.md`](paradigm/GENERATOR.md): fem korttyper, formen
   som bärare, attribution via renderarens beroendekarta, FSRS på faktisk
   förfluten tid. **Den var blockerad av meningskomplexiteten och är det
   inte längre.** Frågan om täckande mot opportunistisk urvalsstrategi är
   nu mogen — med 71 % nåbart avgörs det som övas av strategin, inte av
   uttrycksförmågan.
2. **Tre konstruktioner kvar på stegen:** imperativ (satsmodus, 161 svenska
   former, `imp`-celler finns i alla sju språk), bisatser (`Mening` måste
   kunna innehålla en `Mening` — 22 verb har Bisatsfras-slots) och
   wh-frågor (de 76 frågeorden har former; specen saknar sätt att markera
   vilken slot som efterfrågas). Bisatserna är strukturellt tyngst och låser
   dessutom upp de romanska konjunktiverna.
3. **Attributiv komparation** — se nåbarhetsavsnittet. Störst avkastning av
   allt som återstår, och billig: graden finns redan som `Grad`.
4. **Appen.** Desktop först, mobil senare.

Håll FSRS, ljuduppläsning och appen utanför tills generatorn löser fram
meningar.

---

## Saker en ny session måste veta

**Kör aldrig LLM-kommandon inifrån Claude Code.** `generera`,
`granska-former`, `tagga-*` anropar `claude -p` som subprocess och hänger.
Alla fyra vägrar med ett tydligt besked.

**Migrationer är inte valfria.** `ordbok import --återinitiera` bygger om
databasen från CSV och tappar all taggning. Kör alltid
`for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m"; done`
efteråt, sedan `ordbok importera-former ordbok/former.tsv --ersätt`.
Migrationerna ska vara idempotenta. `semantik_utökad.sql` var det inte:
den satte bitar som dess egen villkorsjämförelse sedan läste, så andra
körningen gav ett annat resultat än första.

**`ordbok/granskningsrattelser.sql` och `ordbok/artikellackage.sql` är
LOGGAR, inga migrationer.** De ligger utanför `migrationer/` just för att
loopen ovan skulle ha spelat upp dem. Satserna är knutna till `Former.id`,
och DELETE/INSERT flyttar id:n — mot en ombyggd databas träffar de fel
rader. Rättelserna bevaras i stället i `former.tsv`, som exporteras om
direkt efter körningen.

**`sprak.db` ligger i `.gitignore`.** Sanningen är `ordbok/former.tsv` plus
migrationerna. Skicka aldrig databasfilen.

**Lita inte på statistikrader.** Sex buggar hittills har rapporterat
"0 saknade, 0 tomma" och sett ut som lyckade körningar: duplicerade cell-ID:n
som tyst tappade hela svenska s-passiven, lemma-nycklat uppslag som gav 96
homonymer noll former, en cellmatchning som läste fel form och gav 588 falska
fel, ett lemma-nycklat uppslag i `tillämpa-granskning` som skrev rättelser
till fel homonym och räknade dem som lyckade, och två bitmaskjämförelser som
skar av semantikbitar. Jämför alltid antal producerade rader mot antal
celler — och för rättelser: ta en cell-för-cell-bild före och efter:

```bash
python ordbok/verktyg/ögonblicksbild.py före.json   # kör rättelsen   # sedan:
python ordbok/verktyg/ögonblicksbild.py efter.json && diff före.json efter.json
```

**Läs den renderade meningen ord för ord.** Sex strängersättningar i
renderarna matchade inte och gjorde alltså ingenting, utan att något
felmeddelande uppstod. De hittades bara genom genomläsning. Ett svep som
räknar krascher hittar dem aldrig.

**En gren som returnerar tidigt ser aldrig logiken under sig.** Det var
hela passivbuggen — och samma sak gjorde att engelsk negation aldrig nådde
perfektgrenen. Bygger du en konstruktion som lägger sig först i en
verbfunktion: fråga vad den skär bort, och delegera hellre till den
befintliga grenen än att bygga en egen liten kopia av tempuslogiken. Den
lilla kopian blir efter vid nästa utökning, och ingen räknare visar det.

**`bash -n` räcker inte** för att validera ett skript. `FÖRSÖK="${FÖRSÖK:-4}"`
passerade syntaxkontrollen men kraschar — bash tillåter inte å/ä/ö i
variabelnamn. Kör skriptet med stubbade LLM-anrop i stället.

**Julius kan svensk och engelsk grammatik, inte de övriga fem.**
Språkfrågor avgörs av assistenten, som redovisar grunden. Granskningar och
förslag är förslag; Julius beslutar. Fattade beslut skrivs in i
`ordbok/beslut.tsv` med motivering — `beslut.tsv` går före `granskning.tsv`,
och granskningsrapporten ändras aldrig i efterhand. Den ska förbli vad
modellen faktiskt sa.

**Inga quick fixes.** Är det ett verkligt problem som systemet inte kan
hantera, gås det igenom metodiskt — det lappas inte.

---

## Var det står dokumenterat

| Fil | Innehåll |
|---|---|
| `paradigm/SCHEMA.md` | slot-filernas format; §4 om unika cell-ID, §5 om bitmask-kollaps |
| `paradigm/PARAMETER_AUDIT.md` | revision av inflektionsrummen; §1b possessivhålet |
| `paradigm/RENDERARE_KRAV.md` | vad renderaren behöver — den vertikala skivan; statusrad per avsnitt |
| `paradigm/_legend.yaml` | axelkodningen, auktoritativ |
| `docs/BITMASK.md` | alla numeriska koder; §11 semantikbitarna |
| `ordbok/nivålistor/KONVENTIONER.md` | lemmaformat, förenklingsfilosofi §5, beslutsprocess §9 |
| `RUNBOOK.md` | operativ referens för genereringskörningen |
| `START_HÄR.md` | kort körinstruktion för den som genererar |
| `paradigm/RESTRIKTIONER.md` | semantiska restriktioner; scope-beslutet står där |
| `paradigm/GENERATOR.md` | kortmodellen, komplexitetsstegen, nåbarheten — alla beslut med motiveringar |
| `ordbok/beslut.tsv` | fattade beslut som går före granskningen, med motivering |
| `src/sprakprog/rendering/spec.py` | meningsspecifikationen — enda källan till vad som går att uttrycka |
| `src/sprakprog/generering/rattelse.py` | modulhuvudet förklarar de fyra operationerna och koncept-nyckeln |

**Scope-beslutet, ordagrant:** *"Flickan köpte en dörr."* är helt okej trots
att det är osannolikt. Osannolikt men välformat är godkänt. Konsekvensen är
att klassbaserade restriktioner räcker — ingen LLM-validering av rimlighet
behövs, och inga klasser behöver bli finare än vad som krävs för att stoppa
*kategorifel*.

---

## Kommandon

```bash
ordbok import <csv...> --återinitiera     # bygg om från CSV
ordbok exportera-former <fil.tsv>         # Former → TSV (delningsformat)
ordbok importera-former <fil.tsv> --ersätt
ordbok generera --alla-språk --fortsätt   # böj alla ord (LLM)
ordbok granska-former --alla-språk --fortsätt --rapport <fil.tsv>
ordbok tillämpa-granskning                # skriv in granskningens förslag
ordbok tagga-koncept | tagga-lexem | tagga-monster
ordbok visa <koncept>                     # drill-down
ordbok rendera --exempel --språk <xx>     # rendera exempelmeningen
```

Mätverktygen körs med venvens python:

```bash
.venv/bin/python ordbok/verktyg/nåbarhet.py          # alla sju språk
.venv/bin/python ordbok/verktyg/nåbarhet.py de -v    # per ordklass
.venv/bin/python ordbok/verktyg/rendera_prov.py --språk sv
```

Efter `tillämpa-granskning`: kör alltid `ordbok exportera-former
ordbok/former.tsv`. Annars ligger rättelserna bara i `sprak.db`, som inte
versionshanteras.

Nattkörningarna gjordes med `kör_natt.sh` och `kör_natt2.sh` på en väns
maskin och konto. Båda är idempotenta, väntar ut kvoten själva och kan
avbrytas med Ctrl-C. De behövs inte längre — inget som återstår kräver
LLM-anrop.
