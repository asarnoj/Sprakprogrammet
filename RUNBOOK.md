# RUNBOOK — köra böjningsgenereringen

Engångsjobb: fylla `Former`-tabellen i `sprak.db` med böjda former för alla
7 språk via Claude. Körs på **din egen maskin med din egen
Claude-prenumeration** (Pro/Max) — inga API-credits behövs.

## 1. Förutsättningar

- Python ≥ 3.13
- Node.js (för claude-CLI:t)
- En Claude Pro/Max-prenumeration

## 2. Installation

```bash
git clone <repo-url> && cd Språkprogrammet
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                       # ger `ordbok`-kommandot
npm install -g @anthropic-ai/claude-code
claude                                 # logga in med DITT Claude-konto, avsluta sen
```

**Viktigt:** kontrollera att `ANTHROPIC_API_KEY` INTE är satt
(`echo $ANTHROPIC_API_KEY` ska vara tomt) — annars faktureras API-credits i
stället för att prenumerationen används.

**Varför inte `claude-agent-sdk`?** Den var med i ett tidigare utkast av
den här pipelinen men är enligt Anthropics egen dokumentation designad för
`ANTHROPIC_API_KEY`-fakturering — dokumentationen ber uttryckligen verktyg
byggda på Agent SDK:t att INTE erbjuda prenumerationsinloggning utan
förhandsgodkännande, och en öppen feature-request om just detta
(Max/Pro-fakturering för SDK:t) är stängd som ej stödd. Pipelinen anropar
i stället `claude -p` direkt via subprocess — det är den officiellt
avsedda vägen för att köra Claude Code icke-interaktivt mot en Pro/Max-
prenumeration, med samma faktureringslogik som interaktiv användning.
Inget extra Python-paket behövs utöver Node + claude-CLI:t.

Kör allt från en **vanlig terminal**, inte inifrån Claude Code (pipelinen
vägrar köra där, avsiktligt).

## 3. Bygg databasen

```bash
ordbok import ordbok/nivålistor/bas_kärna.csv ordbok/nivålistor/grundord.csv --återinitiera
for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m"; done   # efter VARJE import
```

(Migrationerna taggar ja-adjektivtyp, verbvalens och substantivsemantik —
importen bygger om databasen från CSV och tappar taggningen, därav omkörningen.)

(Om `sprak.db` redan följde med och `SELECT COUNT(*) FROM Koncept` ger 724 —
hoppa över det här steget.)

## 4. Testa i liten skala först

```bash
ordbok generera --språk sv --ordklass Verb --lemma tala,springa,vara --torkörning --verbose
```

Läs utskriften: formerna ska se rätt ut (talar/talade/talat/talas …).
Testa gärna även ett morfologiskt tungt språk:

```bash
ordbok generera --språk ja --ordklass Verb --lemma 話す,食べる,行く --torkörning --verbose
```

## 5. Skarp körning

```bash
ordbok generera --alla-språk --fortsätt --verbose
```

- Kör alla 7 språk × alla ordklasser med slot-filer (Verb, Substantiv,
  Adjektiv, Pronomen, Frågepronomen).
- **`--fortsätt`** gör körningen återupptagbar: avbryts den (nätfel,
  rate-limit, stängt lock) är det bara att köra exakt samma kommando igen —
  redan genererade lexem hoppas över.
- Rate-limit på prenumerationen? Vänta tills fönstret nollställs och kör
  igen med `--fortsätt`.
- Modellval: default är Haiku. Vid kvalitetsproblem, kör om ordklassen med
  `--modell claude-sonnet-5` (utan `--fortsätt`, så att formerna skrivs om).

Grov storleksordning: ~500 LLM-anrop totalt, någon–några timmar beroende på
rate-limits.

## 6. Verifiera resultatet

```bash
sqlite3 sprak.db "SELECT l.språk, k.ordklass, COUNT(*) FROM Former f
  JOIN Lexem l ON l.id=f.lexem_id JOIN Koncept k ON k.id=l.koncept_id
  GROUP BY 1,2 ORDER BY 1,2;"
```

Stickprova några ord:

```bash
sqlite3 sprak.db "SELECT form, tempus, diates FROM Former f
  JOIN Lexem l ON l.id=f.lexem_id WHERE l.lemma='springa';"
```

Fel i enstaka ord? Kör om dem riktat:

```bash
ordbok generera --språk sv --ordklass Verb --lemma springa --modell claude-sonnet-5
```

## 7. Leverera tillbaka

Skicka hela `sprak.db`-filen (den är inte git-spårad), eller en dump:

```bash
sqlite3 sprak.db ".dump Former" > former_dump.sql
```

## Hur det funkar under huven

`ordbok generera` → [pipeline.py](src/sprakprog/generering/pipeline.py):
läser inflektionsrummet ur `paradigm/{språk}/{ordklass}.yaml`, injicerar
språkinstruktionerna ur `paradigm/{språk}/INSTRUKTIONER.md` i prompten,
skickar batchar om 10 lemman till Claude via `claude -p` (subprocess),
parsar JSON-svaret, bitmask-kollapsar identiska former och skriver till
`Former`. Skrivningen är idempotent per lexem.
