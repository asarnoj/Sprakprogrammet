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

**Importsteget måste köras** även om `sprak.db` följde med. En medskickad
databas kan vara byggd före ordklassen `Possessiv` lades till (2026-08-01) och
saknar då de nio possessivkoncepten — körningen skulle tyst hoppa över dem.

Kontroll efter import:

```bash
sqlite3 sprak.db "SELECT COUNT(*) FROM Koncept; SELECT COUNT(*) FROM Lexem WHERE koncept_id IN (SELECT id FROM Koncept WHERE ordklass='Possessiv');"
```

Förväntat: **733** koncept och **65** possessivlexem. Får du 724 och 0 är
databasen för gammal — kör importen med `--återinitiera`.

## 4. Testa i liten skala först

```bash
ordbok generera --språk sv --ordklass Verb --lemma tala,springa,vara --torkörning --verbose
```

Läs utskriften: formerna ska se rätt ut (talar/talade/talat/talas …).
Testa gärna även ett morfologiskt tungt språk:

```bash
ordbok generera --språk ja --ordklass Verb --lemma 話す,食べる,行く --torkörning --verbose
```

### 4b. Smoke-test av alla kombinationer — hoppa inte över det här

Kör ett lemma per (språk, ordklass) innan den skarpa körningen. Det är ~42
anrop och några minuter, och det är billigare än att upptäcka ett fel efter
65 000 rader.

`--lemma` är det som begränsar körningen. **`--batch-storlek` gör det inte** —
den styr bara hur många ord som klumpas per anrop. Utan `--lemma` körs hela
ordboken: 3 964 anrop i stället för 42, och flera timmars väntan.

```bash
for s in sv en fr de es it ja; do
  for o in Verb Substantiv Adjektiv Pronomen Possessiv Frågepronomen; do
    L=$(sqlite3 sprak.db "select l.lemma from Lexem l join Koncept k on k.id=l.koncept_id where l.språk='$s' and k.ordklass='$o' order by l.lemma limit 1;")
    [ -z "$L" ] && continue
    echo "── $s / $o  ($L)"
    ordbok generera --språk "$s" --ordklass "$o" --lemma "$L" --torkörning --verbose 2>&1
  done
done | tee smoke.log
```

```bash
grep -E "Saknade \(LLM-miss\): [1-9]|LLM returnerade inte|FEL|Parse-fel" smoke.log
```

Vad du letar efter i utskriften:

- **`Saknade (LLM-miss)` > 0** — modellen svarade inte på alla celler. Sänk
  `--batch-storlek` eller byt modell för just den kombinationen.
- **Färre `[torr]`-rader än celler i slot-filen** utan att `Tomma` eller
  `Saknade` förklarar mellanskillnaden. Då tappas celler tyst — det var så
  ID-kollisionen i `sv/verb.yaml` upptäcktes (2026-08-01).
- **Axelvärden som ser fel ut** — t.ex. aktiva former med `diates=2`.

Historik: två fel har hittats exakt så här, och båda hade sett ut som
lyckade körningar i statistiken.

### 4c. Batch-storlek för de tunga jobben

Standardbatchen är 10 lemman. För de morfologiskt tyngsta kombinationerna
blir svaret då orimligt stort — modellen ska returnera ett JSON-objekt med
`lemman × celler` formsträngar:

| Jobb | Celler | Formsträngar vid batch 10 | Kör med |
|---|---|---|---|
| de/Adjektiv | 144 | 1 440 | `--batch-storlek 2` |
| es/Verb | 53 | 530 | `--batch-storlek 5` |
| it/Verb | 52 | 520 | `--batch-storlek 5` |
| fr/Verb | 45 | 450 | `--batch-storlek 5` |
| de/Verb | 31 | 310 | `--batch-storlek 5` |

Kör dem separat före den stora körningen, så plockar `--fortsätt` upp
resten:

```bash
ordbok generera --språk de --ordklass Adjektiv --batch-storlek 2 --verbose
```

```bash
for s in fr es it de; do ordbok generera --språk "$s" --ordklass Verb --batch-storlek 5 --verbose; done
```

## 5. Skarp körning

```bash
ordbok generera --alla-språk --fortsätt --verbose
```

- Kör alla 7 språk × ordklasserna i `ALLA_ORDKLASSER_MED_MORFOLOGI`
  (Verb, Substantiv, Adjektiv, Pronomen, Possessiv, Frågepronomen).
  En ordklass som har slot-filer men saknas i den listan genereras aldrig.
- **`--fortsätt`** gör körningen återupptagbar: avbryts den (nätfel,
  rate-limit, stängt lock) är det bara att köra exakt samma kommando igen —
  redan genererade lexem hoppas över.
- Rate-limit på prenumerationen? Vänta tills fönstret nollställs och kör
  igen med `--fortsätt`.
- Modellval: default är Haiku. Vid kvalitetsproblem, kör om ordklassen med
  `--modell claude-sonnet-5` (utan `--fortsätt`, så att formerna skrivs om).

Grov storleksordning: ~500 LLM-anrop totalt, någon–några timmar beroende på
rate-limits.

### Avbryta och återuppta

Ctrl-C är ofarligt. Varje batch skrivs i en egen transaktion, så allt som
hunnit bli klart ligger kvar i databasen — bara den pågående batchen tappas,
och den görs om vid nästa körning. Kör samma kommando igen med `--fortsätt`.

### Följa hur långt det gått

`--verbose` skriver `Batch 3/18` per (språk, ordklass). För helhetsbilden,
kör i **ett annat terminalfönster**:

```bash
sqlite3 sprak.db "SELECT COUNT(DISTINCT lexem_id) || ' av 3964 lexem klara (' || ROUND(COUNT(DISTINCT lexem_id)*100.0/3964,1) || '%), ' || COUNT(*) || ' former' FROM Former;"
```

Fördelningen per språk och ordklass:

```bash
sqlite3 sprak.db "SELECT l.språk, k.ordklass, COUNT(DISTINCT l.id) FROM Former f JOIN Lexem l ON l.id=f.lexem_id JOIN Koncept k ON k.id=l.koncept_id GROUP BY 1,2 ORDER BY 1,2;"
```

Ett lexem som legitimt får noll former (alla celler tomma) räknas aldrig som
klart och kommer att köras om vid varje `--fortsätt`. Det rör en handfull ord
och kostar bara några extra anrop.

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

### 6b. Maskinell granskning med en starkare modell

Genereringen körs med `claude-haiku-4-5` för att 65 000 former ska vara
möjliga att producera. Smoke-testet 2026-08-01 visade ~1 % avvikelser,
koncentrerade till oregelbunden morfologi.

Att i stället generera allt med en stark modell är dyrt — utdata är 65 000
formsträngar. Granskning vänder på ekonomin: formerna går IN i prompten och
bara avvikelserna kommer ut, ungefär 30 gånger mindre utdata.

```bash
ordbok granska-former --alla-språk --rapport ordbok/granskning.tsv --verbose
```

Avbruten körning återupptas med `--fortsätt` (hoppar över lexem som redan
står i rapporten). Billigare modell med `--modell claude-sonnet-5`.

Rapporten är en TSV med kolumnerna `språk, ordklass, koncept, lemma, cell,
nuvarande, förslag, allvar, motivering`. `allvar` är `fel` eller `osäker`.

```bash
awk -F'\t' '$8=="fel"' ordbok/granskning.tsv | column -t -s $'\t' | head -40
```

**Granskningen ändrar aldrig databasen.** Den skriver förslag; att tillämpa
dem är ett mänskligt beslut (KONVENTIONER.md §9). Rätta genom att köra om de
berörda lemmana riktat, eller genom att justera slot-fil/instruktion om
mönstret återkommer.

Kaikki-dumparna är ett komplement, inte en ersättning: `ordbok mappa-kaikki`
är än så länge bara implementerad för **sv**, och de två formfel smoke-testet
hittade satt i de och es.

## 7. Leverera tillbaka

Exportera `Former` till TSV och committa filen — skicka **inte** `sprak.db`.

```bash
ordbok exportera-former ordbok/former.tsv
```

```bash
git add ordbok/former.tsv && git commit -m "Genererade former" && git push
```

TSV:n nycklas på `(koncept, språk, lemma)`, inte på `lexem_id`. Radnummer i
Lexem-tabellen ändras varje gång databasen byggs om från CSV; den naturliga
nyckeln gör det inte. Därför spelar det ingen roll om mottagarens databas är
ombyggd sedan dess.

Filen är dessutom granskningsbar och diffbar, vilket en binär `.db` inte är.
`sprak.db` är `.gitignore`:ad och åker aldrig med.

### Mottagarsidan

```bash
ordbok importera-former ordbok/former.tsv --ersätt
```

Importen är transaktionell och vägrar skriva om en enda rad inte matchar ett
lexem i den lokala ordboken — det betyder att TSV:n och CSV-filerna är
osynkade, och en halvskriven tabell vore värre än ingen.

## Hur det funkar under huven

`ordbok generera` → [pipeline.py](src/sprakprog/generering/pipeline.py):
läser inflektionsrummet ur `paradigm/{språk}/{ordklass}.yaml`, injicerar
språkinstruktionerna ur `paradigm/{språk}/INSTRUKTIONER.md` i prompten,
skickar batchar om 10 lemman till Claude via `claude -p` (subprocess),
parsar JSON-svaret, bitmask-kollapsar identiska former och skriver till
`Former`. Skrivningen är idempotent per lexem.
