# Överlämning — Språkprogrammet, 2026-08-12

Klistra in det här i en ny chatt. Allt är committat och pushat (`7071e41`).

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
Koncept        733        Mönster        174   (alla verb)
Lexem        5 130        MönsterKrav    301
Former      48 191        genus        1 295/1 295
                          prenominal     777/777
                          gradbarhet     111/111
                          räknebar       259/259
                          semantik       323
```

Kända fel i formerna: **0,12 %** (57 stycken), efter att 834 rättelser
skrivits in. Alla sju språk är granskade av en starkare modell.

**Renderaren finns inte.** Det är nästa fas.

---

## Det enda som väntar på dig just nu

**59 rader i `ordbok/granskning.tsv` kräver ett mänskligt beslut**, inte en
modell. Lista dem med:

```bash
ordbok tillämpa-granskning --torkörning
```

De är av tre slag:

| Slag | Antal | Vad det betyder |
|---|---|---|
| Tomt förslag | 13 | Granskningen menar att formen inte borde finnas. Att radera raden tar bort den för alla celler den täcker — därför inget automatiskt beslut. Ex: `de/Schnee` plural. |
| Kollaps med olika förslag | 18 | En Former-rad täcker flera celler som fått olika förslag. Samma rad kan inte få båda; formen behöver troligen delas i två rader. Ex: `de/blau superl_bland_pl` → `blauesten` eller `blauester`. |
| Hittade ingen rad | 28 | Granskningen flaggade en cell som saknar form i databasen. Ex: `fr/vouloir imp_2sg`. |

Det är en genomläsning, ingen körning.

---

## Vad som återstår i stort

Datalagret är färdigt. Det som fattas är **kod och design**, inte data.
Fullständig lista i [`paradigm/RENDERARE_KRAV.md`](paradigm/RENDERARE_KRAV.md),
framtagen genom att rendera meningen *"flickan gav sin bror en röd bok igår"*
för hand till alla sju språk.

**Det enda verkliga schemahålet:** `MönsterKrav` saknade kasusrektion —
tyska `geben` styr dativ. Kolumnerna `kasus` och `preposition_koncept_id`
är tillagda men inte fyllda. Det är ett andra pass som hör till renderarfasen.

**Fyra saker att bygga, i föreslagen ordning:**

1. **Meningsspecifikationen** — `Mönster` säger vilka ord som får kombineras,
   men det finns ingen datastruktur för en *färdig* mening: tempus,
   bestämdhet, negation, vem som är koreferent med vem. Designarbete.
2. **Hjälpverbsvalet** — fr être/avoir, de sein/haben, it essere/avere är
   lexikala egenskaper per verb. `Lexem` har ingen kolumn.
3. **Renderaren, ett språk i taget.** Svenska först (du kan bedöma resultatet
   direkt), sedan tyska (kasus + V2 tvingar fram rätt arkitektur medan den
   är billig att ändra). Klarar den de två är resten arbete, inte problem.
4. **Ordföljd** — de V2/verbfinal, TeKaMoLo, ja SOV, fr klitikaordning.
   Ingenting av det är representerat. Största enskilda posten.

Håll FSRS, ljuduppläsning och appen utanför tills en mening renderas korrekt.

**Kända täckningsgränser** (inga fel, men bra att veta):
- Mönster finns bara på verb. Schemat tillåter adjektiv och prepositioner
  som styrande ord (`rädd för`, `intresserad av`) — inte taggat.
- Ett mönster per verb. `äta` har ett transitivt mönster, men "hon äter"
  utan objekt är också korrekt. Additivt att lägga till.
- Determinerarna (Artikel, Demonstrativ, Kvantifikator,
  Interrogativdeterminant, Relativpronomen) har inga slot-filer — 117 lexem
  utan former. Beslut behövs: generera eller hårdkoda i renderaren.
- `mappa-kaikki` (validering mot Wiktionary-dumpar) är bara implementerad
  för svenska.

---

## Saker en ny session måste veta

**Kör aldrig LLM-kommandon inifrån Claude Code.** `generera`,
`granska-former`, `tagga-*` anropar `claude -p` som subprocess och hänger.
Alla fyra vägrar med ett tydligt besked.

**Migrationer är inte valfria.** `ordbok import --återinitiera` bygger om
databasen från CSV och tappar all taggning. Kör alltid
`for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m"; done`
efteråt, sedan `ordbok importera-former ordbok/former.tsv --ersätt`.

**`sprak.db` ligger i `.gitignore`.** Sanningen är `ordbok/former.tsv` plus
migrationerna. Skicka aldrig databasfilen.

**Lita inte på statistikrader.** Tre buggar under den här sessionen
rapporterade "0 saknade, 0 tomma" och såg ut som lyckade körningar:
duplicerade cell-ID:n som tyst tappade hela svenska s-passiven,
lemma-nycklat uppslag som gav 96 homonymer noll former, och en cellmatchning
som läste fel form och gav 588 falska fel. Jämför alltid antal producerade
rader mot antal celler.

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

Nattkörningarna gjordes med `kör_natt.sh` och `kör_natt2.sh` på en väns
maskin och kontot. Båda är idempotenta, väntar ut kvoten själva och kan
avbrytas med Ctrl-C. De behövs inte längre — inget som återstår kräver
LLM-anrop.
