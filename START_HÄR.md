# Start här

Databasen känner ordet `springa` men inte `sprang`. Ditt jobb är att fylla
den luckan: 3 964 ord → ~65 000 böjda former, på sju språk. Det görs genom
att fråga Claude ungefär 500 gånger, och det tar en förmiddag — nästan bara
väntetid.

## Sätt upp

```bash
git clone https://github.com/asarnoj/Spra-kprogrammet.git && cd Spra-kprogrammet
```

```bash
uv venv --python 3.13 && uv pip install -e . && source .venv/bin/activate
```

```bash
claude
```

Logga in, avsluta med `/exit`. Har du `ANTHROPIC_API_KEY` satt — ta bort den,
annars faktureras API-credits i stället för prenumerationen.

```bash
ordbok import ordbok/nivålistor/bas_kärna.csv ordbok/nivålistor/grundord.csv --återinitiera && for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m"; done
```

## Kör

```bash
ordbok generera --alla-språk --fortsätt --verbose
```

Det är hela körningen.

**Avbryt** med Ctrl-C, när som helst. Allt som hunnit bli klart ligger kvar.

**Fortsätt** med exakt samma kommando. Den tar vid där den slutade.

Slår du i taket för prenumerationen: vänta tills det nollställs, kör samma
kommando igen.

## Följ läget

Utskriften visar `Batch 3/18` per språk och ordklass. För helheten, i ett
annat terminalfönster:

```bash
sqlite3 sprak.db "SELECT COUNT(DISTINCT lexem_id) || ' av 3964 ord klara' FROM Former;"
```

## Skicka tillbaka

```bash
ordbok exportera-former ordbok/former.tsv && git add ordbok/former.tsv && git commit -m "Genererade former" && git push
```

Skicka inte `sprak.db` — den är utesluten ur git med flit.

---

## Om något ser fel ut

Titta på sammanfattningen efter varje jobb:

| Rad | Betyder |
|---|---|
| `Saknade (LLM-miss): 0` | bra |
| `Saknade (LLM-miss): 4` | fyra celler obesvarade — kör om jobbet med `--batch-storlek 1` |
| `Tomma (defektiva): 8` | normalt, former som inte finns |
| `LLM returnerade inte 'X'` | ordet hoppades över — `--lemma X` för att köra om det |

Cirka 1 % av formerna brukar bli fel. Det är väntat och fångas i en granskning
i andra änden — leta inte efter dem.

`RUNBOOK.md` har detaljerna. Fastnar något: skicka utskriften.
