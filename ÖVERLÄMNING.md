# Överlämning — Språkprogrammet, 2026-08-12

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

**Böjnings- och taggningslagret är klart.**

```
Koncept        733        Mönster        197   (174 universella
Lexem        5 130        MönsterKrav    329    + 23 språkspecifika)
Former      48 573        genus        1 295/1 295
                          prenominal     777/777
                          gradbarhet     111/111
                          räknebar       259/259
                          semantik       323
                          hjälpverb    522/522
                          variant        42/42
                          determinerare 117/117
```

**Alla 1 043 fel granskningen hittade är åtgärdade.** `ordbok
tillämpa-granskning --torkörning` ger noll satser att köra. Alla sju språk är
granskade av en starkare modell.

**Renderaren finns inte.** Det är nästa fas.

---

## Vad som gjordes sist (2026-08-12)

De 59 rader som förra överlämningen lämnade öppna är inskrivna. De krävde
inte 59 bedömningar — de krävde tre operationer som `tillämpa-granskning`
saknade. Kommandot gör nu fyra saker i stället för en: skriver om, **lägger
till** (cellen var tom, alltså INSERT och inte UPDATE), **delar** (en rad
täckte flera celler som visade sig behöva olika former) och **tar bort**.

27 celler fick form, 11 tömdes, 21 bytte form. Ingen annan cell rördes —
kontrollerat genom att jämföra cell-för-cell-bilder före och efter, inte
genom att lita på statistikraderna.

**Två fel i granskningen själv, som nu står i `ordbok/beslut.tsv`:**

| Fall | Granskningen sa | Rätt |
|---|---|---|
| `de/sie` dativ (3pl) | `ihr` | `ihnen` — den trodde två identiska sie-paradigm angivits, men lexemen är åtskilda och båda var redan rätt |
| `de/blau superl_bland_pl_gen` | `blauester` | `blauesten` — blandad deklination tar svaga ändelser i hela pluralen |

`beslut.tsv` går före `granskning.tsv`. Granskningen är en stark modells
förslag, inte facit; när den har fel skrivs svaret in där med motivering,
i stället för att granskningsrapporten ändras. Rapporten ska förbli vad
modellen faktiskt sa.

### Ett fel som satt i tillämpningen, inte i datan

`tillämpa-granskning` slog upp lexem på `lemma + språk` och lät
granskningens `koncept`-kolumn ligga oanvänd. 177 lemman är flera lexem
inom samma språk. Rättelsen hamnade då på det lexem vars rad råkade komma
först: `giocherebbero` skrevs till `arb_leka` medan `gen_spela`, som
granskningen gällde, blev kvar med fel form. Samma sak för `de/finden`.
Statistiken räknade båda som lyckade rättelser.

Uppslaget är nu nycklat på koncept. De felplacerade rättelserna är rättade.

---

## Vad som återstår i stort

Fullständig lista i [`paradigm/RENDERARE_KRAV.md`](paradigm/RENDERARE_KRAV.md),
framtagen genom att rendera meningen *"flickan gav sin bror en röd bok igår"*
för hand till alla sju språk. Varje avsnitt där har en statusrad överst.

Det som förra överlämningen kallade **"det enda verkliga schemahålet"** —
kasusrektion — var inget hål alls. `Mönster.språk` fanns redan och är
nullbar just för det: ett mönster med `språk='de'` skuggar det universella
och bär bara det som skiljer. Se `ordbok/migrationer/rektion.sql`.

**Datalagret är slut.** Sju av elva brister i `RENDERARE_KRAV.md` är
åtgärdade, och de fyra som återstår är alla kod, inte data:

1. **Meningsspecifikationen** — `Mönster` säger vilka ord som får kombineras,
   men det finns ingen datastruktur för en *färdig* mening: tempus,
   bestämdhet, negation, vem som är koreferent med vem. Designarbete, och
   det som allt annat vilar på.
2. **Tempusmappningen** (§3.6) — "förfluten tid, perfektiv" måste bli passé
   composé i franska och preteritum i svenska. Tabellen finns inte.
3. **Renderaren, ett språk i taget.** Svenska först (du kan bedöma resultatet
   direkt), sedan tyska (kasus + V2 tvingar fram rätt arkitektur medan den
   är billig att ändra). Klarar den de två är resten arbete, inte problem.
4. **Ordföljd** (§3.10) — de V2/verbfinal, TeKaMoLo, ja SOV, fr klitikaordning.
   Ingenting av det är representerat. Största enskilda posten.

Kvar i datan finns bara två småposter, båda nyfunna: räkneord i sex språk
(sv är klart) och adverb i alla sju — 358 lexem utan former, varav bara
sv/en syntetiska komparativer (fort/fortare) faktiskt behöver böjas.

Håll FSRS, ljuduppläsning och appen utanför tills en mening renderas korrekt.

**Kända täckningsgränser** (inga fel, men bra att veta):
- Mönster finns bara på verb. Schemat tillåter adjektiv och prepositioner
  som styrande ord (`rädd för`, `intresserad av`) — inte taggat.
- Ett mönster per verb. `äta` har ett transitivt mönster, men "hon äter"
  utan objekt är också korrekt. Additivt att lägga till.
- ~~Determinerarna har inga slot-filer.~~ **Åtgärdat 2026-08-12.** Beslutet
  blev att lägga dem i `Former`, tvärtemot PARAMETER_AUDIT §3, eftersom FSRS
  spårar per ordform och en hårdkodad artikel inte kan övas.
- `mappa-kaikki` (validering mot Wiktionary-dumpar) är bara implementerad
  för svenska.
- **Granskningens kvittofil skiljer inte på homonymer.**
  `granskning.tsv.klara` har en rad per `(språk, lemma)`, men 177 lemman är
  flera lexem. För 120 av dem är lemmat kvitterat som granskat, vilket kan
  betyda att bara det ena lexemet faktiskt granskades — upp till ~140 lexem
  kan alltså vara ogranskade utan att det syns. Att stänga hålet kräver en
  ny `granska-former`-körning, alltså LLM-anrop, alltså inte inifrån Claude
  Code. Kvittot bör nycklas på koncept, samma fix som `tillämpa-granskning`
  fick.
- **`paradigm/it/frågepronomen.yaml` har två celler med identiska
  koordinater.** `chi` och `cosa` är båda `kasus: [Nom, Ack, Dat]` och inget
  annat. Former lagrar axlar, inte cell-id, så en rad som täcker den ena
  täcker med nödvändighet den andra. Granskningen rapporterar därför den
  främmande cellen som fel hos båda lemmana. Ofarligt för renderaren, som
  väljer lemma på koncept och sedan axlar — men det går inte att åtgärda i
  datan, bara i slot-filen. Beslutet att låta det vara står i `beslut.tsv`.
  Det är det enda sådana fallet i alla slot-filer (kontrollerat).

---

## Saker en ny session måste veta

**Kör aldrig LLM-kommandon inifrån Claude Code.** `generera`,
`granska-former`, `tagga-*` anropar `claude -p` som subprocess och hänger.
Alla fyra vägrar med ett tydligt besked.

**Migrationer är inte valfria.** `ordbok import --återinitiera` bygger om
databasen från CSV och tappar all taggning. Kör alltid
`for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m"; done`
efteråt, sedan `ordbok importera-former ordbok/former.tsv --ersätt`.

**`ordbok/granskningsrattelser.sql` är en LOGG, ingen migration.** Den låg
i `ordbok/migrationer/` men är flyttad ut, just för att loopen ovan skulle
ha spelat upp den. Satserna är knutna till `Former.id`, och DELETE/INSERT
flyttar id:n — mot en ombyggd databas träffar de fel rader. Rättelserna
bevaras i stället i `former.tsv`, som exporteras om direkt efter körningen.

**`sprak.db` ligger i `.gitignore`.** Sanningen är `ordbok/former.tsv` plus
migrationerna. Skicka aldrig databasfilen.

**Lita inte på statistikrader.** Fyra buggar hittills har rapporterat
"0 saknade, 0 tomma" och sett ut som lyckade körningar: duplicerade cell-ID:n
som tyst tappade hela svenska s-passiven, lemma-nycklat uppslag som gav 96
homonymer noll former, en cellmatchning som läste fel form och gav 588 falska
fel, och ett lemma-nycklat uppslag i `tillämpa-granskning` som skrev
rättelser till fel homonym och räknade dem som lyckade. Jämför alltid antal
producerade rader mot antal celler — och för rättelser: ta en
cell-för-cell-bild före och efter och diffa den:

```bash
python ordbok/verktyg/ögonblicksbild.py före.json   # kör rättelsen   # sedan:
python ordbok/verktyg/ögonblicksbild.py efter.json && diff före.json efter.json
```

**`bash -n` räcker inte** för att validera ett skript. `FÖRSÖK="${FÖRSÖK:-4}"`
passerade syntaxkontrollen men kraschar — bash tillåter inte å/ä/ö i
variabelnamn. Kör skriptet med stubbade LLM-anrop i stället.

**Granskningsprocessen:** presentera observationer och alternativ, Julius
beslutar. Ändringar genomförs separat, aldrig direkt.

---

## Var det står dokumenterat

| Fil | Innehåll |
|---|---|
| `paradigm/SCHEMA.md` | slot-filernas format; §4 om unika cell-ID, §5 om bitmask-kollaps |
| `paradigm/PARAMETER_AUDIT.md` | revision av inflektionsrummen; §1b possessivhålet |
| `paradigm/RENDERARE_KRAV.md` | vad renderaren behöver — den vertikala skivan |
| `paradigm/_legend.yaml` | axelkodningen, auktoritativ |
| `docs/BITMASK.md` | alla numeriska koder; §11 semantikbitarna |
| `ordbok/nivålistor/KONVENTIONER.md` | lemmaformat, förenklingsfilosofi §5, beslutsprocess §9 |
| `RUNBOOK.md` | operativ referens för genereringskörningen |
| `START_HÄR.md` | kort körinstruktion för den som genererar |
| `ordbok/beslut.tsv` | fattade beslut som går före granskningen, med motivering |
| `src/sprakprog/generering/rattelse.py` | modulhuvudet förklarar de fyra operationerna och koncept-nyckeln |

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
```

Efter `tillämpa-granskning`: kör alltid `ordbok exportera-former
ordbok/former.tsv`. Annars ligger rättelserna bara i `sprak.db`, som inte
versionshanteras.

Nattkörningarna gjordes med `kör_natt.sh` och `kör_natt2.sh` på en väns
maskin och kontot. Båda är idempotenta, väntar ut kvoten själva och kan
avbrytas med Ctrl-C. De behövs inte längre — inget som återstår kräver
LLM-anrop.
