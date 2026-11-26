# Språkprogrammet

Ett språkinlärningssystem som bryter ner varje läromoment till minsta enhet
som kan vara fel var för sig, gör den till ett FSRS-kort, och bygger sedan
nya meningar som prövar precis de kort du är på väg att glömma. När du svarar
jämförs ditt svar med facit ord för ord, och systemet försöker avgöra vilken
enskild bit som brast.

Det är det som skiljer det från vanliga glosor: **Anki vet att du missade
kortet, det här systemet försöker veta VARFÖR.**

Sju språk (sv, en, de, fr, es, it, ja) delar ett språkoberoende konceptlager.
En mening definieras en gång och renderas till valfritt språk.

**Avgränsning:** grammatik och böjning — teorin. Inte talspråk, idiomatik
eller register. Varför det är ett beslut och inte en brist står under
"Avgränsningen" i `paradigm/PROBLEM.md`.

---

## Var man börjar läsa

| Fil | Vad den är |
|---|---|
| **`paradigm/KÄRNAN.md`** | **Spec:en.** Vad systemet ska vara — korten, nivåerna, dagspasset, meningsbygget, bedömningen — och byggordningen i §9. Den styr bygget. |
| **`paradigm/ARBETE.md`** | **Arbetslistan.** Vad som är kvar, per byggsteg. Det enda stället som svarar på «vad jobbar vi på». |
| **`paradigm/PROBLEM.md`** | **Frågorna.** Systemets 67 öppna och lösta frågor, var och en med status, mätning och lösning. Skälen bakom spec:en står här. |
| `paradigm/SCHEMA.md` | Datamodellen |
| `docs/BITMASK.md` | De numeriska koderna — auktoritativ |
| `kort.sql` / `setup.sql` | Inlärardatabasens respektive språkdatabasens schema |
| `paradigm/GENERATOR.md` | Historisk — besluten i den ordning de fattades, överspelad av `KÄRNAN.md` |
| `ARBETSLOGG_till_2026-08-15.md` | Historisk — dagbok till och med 2026-08-15 |

Läs dem i den ordningen: `KÄRNAN.md` säger vad som ska byggas, `ARBETE.md` vad
som är kvar, `PROBLEM.md` varför det ser ut som det gör.

`PROBLEM.md` är ordnad efter FRÅGOR systemet måste kunna svara på.
Statusmarkören beskriver systemet, inte dokumentet:

    ✓   löst, och lösningen är mätt eller härledd
    ~   löst i praktiken, men vilar på ett antagande som inte prövats
    ?   öppen — vi vet att problemet finns men inte vad svaret är
    !   känd defekt: systemet gör något vi vet är fel

Måttstocken på en lösning är inte "fungerar det" utan **"är det sant"** — ett
system som påstår sig veta något det inte vet är sämre än ett som säger att
det inte vet.

---

## Köra

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```

Övningsgränssnittet — **den enda vägen in i systemet**:

```bash
ordbok webb
```

Att det är den enda vägen är ett beslut och inte en tillfällighet. Varje
ändpunkt som räknar dagens arbete själv i stället för att fråga `dagsplan` är
ett ställe där två svar kan gå isär, och varenda bugg i passet under vecka 34
var två sådana svar. Se G6 i `PROBLEM.md`.

Behöver man köra ett pass utan webbläsare finns
`ordbok/verktyg/passkörning.py`, som går genom samma tjänst.

Beståndet och nästa nivås kostnad:

```bash
ordbok kort --läge --kostnad 5
```

---

## Skyddsnätet

Elva prov, ungefär 7,5 minuter, ett kommando:

```bash
.venv/bin/python ordbok/verktyg/alla_prov.py
```

`--snabb` kör de fyra som tar sekunder. `--fortsätt` kör vidare förbi ett
fallet nät.

**Varje prov har ett falsifieringspass** — det gamla, trasiga beteendet
återinfört — och måste falla när det slås på. Ett prov utan falsifiering är
en trosbekännelse, och det har lönat sig: fler fel har hittats i proven
själva än i koden de vaktar. Två av dem hittades så sent som 2026-08-26, en
tom invariant och en för stark.

---

## Datan

`sprak.db` byggs om ur `ordbok/former.tsv` och nivålistorna och ligger inte i
git. `kort.db` — repetitionshistoriken — går **inte** att återskapa och ligger
inte heller i git. Den säkerhetskopieras automatiskt en gång per dygn vid
första anslutningen, verifierad rad för rad, till `säkerhetskopior/`.

Att kopiera `kort.db` med `cp` är INTE en giltig säkerhetskopia: databasen
körs i WAL-läge, och en filkopia tappar precis det nyaste. Se I1 i
`PROBLEM.md`.

Att bygga om ordboken från grunden — 3 964 ord till ~65 000 böjda former via
LLM — beskrivs i `START_HÄR.md` (kortversionen) och `RUNBOOK.md` (detaljerna).
Det är ett engångsjobb som redan är gjort.

---

## Kataloger

    src/sprakprog/
        kort/          inlärardatabasen: kort, pass, schemaläggning, arbetsbörda
        generator/     samplaren, poängsättningen, rättningen
        rendering/     en renderare per språk, plus specen de delar
        webb/          övningstjänsten och gränssnittet
        generering/    LLM-pipelinen som fyller Former (engångsjobbet)
        cli/           `ordbok`-kommandot

    ordbok/
        verktyg/       proven och mätverktygen
        migrationer/   additiva schemaändringar för kort.db
        nivålistor/    källan till ordförrådet

    gammal/            data från tidigare skeden. KODEN är borttagen
                       2026-08-26 — den var ersatt av src/ och importerades
                       ingenstans. Ligger kvar i git-historiken.

    ARBETSLOGG_till_2026-08-15.md
                       historisk logg, ordnad efter datum. Läs den för
                       språkspecifik renderarkunskap, inte för hur systemet
                       fungerar idag.
