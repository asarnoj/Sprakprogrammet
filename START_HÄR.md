# Start här

Tack för att du kör det här. Nedan står allt du behöver, i ordning.
Räkna med **en förmiddag**, varav det mesta är väntetid.

`RUNBOOK.md` har detaljerna om något går snett.

---

## Vad du gör, och varför

Projektet är en språkinlärningsapp som bygger meningar på sju språk från en
gemensam, språkoberoende beskrivning. För att kunna göra det måste databasen
känna till varje ords **alla böjda former**.

Just nu vet den att svenska ordet för att springa heter `springa` och att
tyskans heter `laufen`. Den vet **inte** att det heter *sprang* i preteritum
eller *liefe* i Konjunktiv II. Utan det kan appen bara rada upp grundformer.

Ditt jobb är att fylla den luckan: **3 964 ord → ungefär 65 000 böjda former**,
på sju språk.

Det görs genom att fråga Claude, ungefär 500 gånger. Och det är därför det är
du som kör — anropen faktureras på det Claude-konto som är inloggat, och vi
delar på belastningen.

Ingen kod behöver skrivas. Du kör färdiga kommandon och skickar tillbaka
resultatet.

---

## 1. Installera

```bash
git clone https://github.com/asarnoj/Spra-kprogrammet.git && cd Spra-kprogrammet
```

```bash
uv venv --python 3.13 && uv pip install -e . && source .venv/bin/activate
```

Har du inte `uv`: `brew install uv`.

## 2. Logga in på Claude

```bash
claude
```

Följ inloggningen, välj din prenumeration, avsluta med `/exit`.

> **Viktigt:** ha inte `ANTHROPIC_API_KEY` satt i din miljö. Den tar tyst över
> och fakturerar API-credits i stället för prenumerationen. Kontrollera med
> `echo $ANTHROPIC_API_KEY` — ska vara tomt.

Kör allt nedan i ett **vanligt terminalfönster**, inte inifrån Claude Code.
Verktyget vägrar köra där, med flit.

## 3. Bygg databasen

```bash
ordbok import ordbok/nivålistor/bas_kärna.csv ordbok/nivålistor/grundord.csv --återinitiera
```

```bash
for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m"; done
```

Kontrollera att det blev rätt:

```bash
sqlite3 sprak.db "SELECT COUNT(*) FROM Koncept;"
```

Ska ge **733**. Får du något annat, hör av dig innan du går vidare.

## 4. Testa i liten skala

Det här kostar nästan ingenting och tar ett par minuter. Hoppa inte över det.

```bash
ordbok generera --språk sv --ordklass Verb --lemma springa --torkörning --verbose
```

`--torkörning` frågar Claude men skriver ingenting till databasen. Du ska få
12 rader: springa, springer, sprang, sprungit, spring, springas, springs,
sprangs, sprungits, sprungen, sprunget, sprungna.

Ser det rimligt ut? Bra. Vidare.

## 5. Kör de tunga jobben först

Fyra jobb är mycket större än de andra. Tyska adjektiv har 144 former per ord —
be om tio ord åt gången och svaret blir 1 440 former i ett svep, vilket blir
sämre. Därför mindre portioner just här:

```bash
ordbok generera --språk de --ordklass Adjektiv --batch-storlek 2 --verbose
```

```bash
for s in fr es it; do ordbok generera --språk "$s" --ordklass Verb --batch-storlek 5 --verbose; done
```

## 6. Kör resten

```bash
ordbok generera --alla-språk --fortsätt --verbose
```

`--fortsätt` hoppar över det som redan är klart, så steg 5 görs inte om.

**Det här är det långa steget.** Ungefär 400 anrop kvar.

### Om du behöver avbryta

Ctrl-C när som helst. Allt som hunnit bli klart ligger kvar i databasen —
varje portion sparas för sig. Starta igen med exakt samma kommando, så tar
den vid där den slutade.

Slår du i taket för din prenumeration: vänta tills det nollställs och kör
samma kommando igen.

### Följa hur långt det gått

`--verbose` visar `Batch 3/18` per språk och ordklass. För helheten, öppna
**ett andra terminalfönster** och kör:

```bash
sqlite3 sprak.db "SELECT COUNT(DISTINCT lexem_id) || ' av 3964 ord klara' FROM Former;"
```

## 7. Skicka tillbaka

```bash
ordbok exportera-former ordbok/former.tsv
```

```bash
git add ordbok/former.tsv && git commit -m "Genererade former" && git push
```

Det är allt. Säg till när det är pushat.

> **Skicka inte `sprak.db`-filen.** Den är avsiktligt utesluten ur git.
> Textfilen går att läsa igenom och granska, och den kan importeras även om
> databasen har ändrats i andra änden under tiden — vilket den har, för
> ordboken taggas parallellt.

---

## Om något ser fel ut

Det viktigaste är att **inte tolka en snygg utskrift som att allt gick bra.**
Titta efter de här raderna i slutet av varje jobb:

| Rad | Betyder |
|---|---|
| `Saknade (LLM-miss): 0` | bra — modellen svarade på alla celler |
| `Saknade (LLM-miss): 4` | fyra celler obesvarade. Sänk `--batch-storlek` för det jobbet och kör om |
| `Tomma (defektiva): 8` | normalt — former som inte finns (t.ex. komparativ av "alive") |
| `LLM returnerade inte 'X'` | ordet hoppades över helt. Kör om det riktat med `--lemma X` |

Ungefär 1 % av formerna brukar bli fel. Det är väntat — de fångas i en
granskning i andra änden, så du behöver inte leta efter dem.

Kör om ett enskilt ord så här:

```bash
ordbok generera --språk de --ordklass Substantiv --lemma Abend --verbose
```

Fastnar något annat: skicka utskriften, så tittar vi på den.
