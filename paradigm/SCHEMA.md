# Paradigm-katalog — schemaspecifikation

*Version 2. Fastställd 2026-05-04 efter arkitektur-pivot från klassifikations-modellen.*

Denna fil är auktoritativ för formatet på slot-filer i `paradigm/`. Pipelinen
i Fas B3 vägrar köra mot filer som inte följer schemat.

---

## 1. Syfte och arkitektur

Paradigm-katalogen specificerar **inflektionsrummet** för varje (språk, ordklass) —
det vill säga, vilka celler som *kan* existera. Vilka celler som faktiskt fylls
för ett enskilt lexem avgörs reaktivt av två datakällor:

1. **Kaikki-dumpar** (Wiktionarys strukturerade böjningstabeller, lokalt i
   `gammal/datafiler/kaikki/`) — primär källa, human-curated ground truth.
2. **LLM** — fyller endast i celler som saknas i kaikki.

Slot-filerna gör **ingen klassifikation av lexem**. Ett AR-verb och ett starkt
verb läggs in i `paradigm/sv/verb.yaml` på exakt samma sätt; skillnaden är
att olika celler råkar få identiska formsträngar (vilket hanteras vid
lagring, ej i paradigm-design).

Defektiva paradigm (modalverb utan imperativ, deponens med bara s-former etc.)
hanteras med **lexem-modifierare** — flaggor på lexem-nivå, *inte* i
paradigm-filerna.

---

## 2. Filstruktur

En slot-fil per (språk, ordklass). Sökväg:

```
paradigm/{språk}/{ordklass}.yaml
```

Exempel: `paradigm/sv/verb.yaml`, `paradigm/de/adjektiv.yaml`, `paradigm/ja/pronomen.yaml`.

Två toppnivåsektioner — båda obligatoriska:

```yaml
meta:        # version, språk, ordklass, beskrivning
celler:      # listan av celler i inflektionsrummet
```

---

## 3. `meta`

| Fält          | Typ | Obligatorisk | Beskrivning                                                |
|---------------|-----|:------------:|------------------------------------------------------------|
| `version`     | int | ja           | Schemaversion. Pipelinen vägrar okända versioner. Aktuell: 2. |
| `språk`       | str | ja           | sv / en / fr / de / es / it / ja                           |
| `ordklass`    | str | ja           | Måste matcha en av `Koncept.ordklass`-värdena.             |
| `beskrivning` | str | ja           | Flerradig prosa: kort om vilka axlar som varierar, regionala/registermässiga avgränsningar, kommentar om defektiva typer som hanteras via lexem-modifierare. |

Inga andra meta-fält tillåts. (`paradigm`, `alias`, `källa`, `lexem_input` har
tagits bort i v2.)

---

## 4. `celler`

En cell = en möjlig rad i `Former` (per lexem som faktiskt har den formen).
Schemat per cell:

| Fält      | Typ       | Obligatorisk | Beskrivning |
|-----------|-----------|:------------:|-------------|
| `id`      | str       | ja           | Mänskligt läsbar etikett. Följer cell-ID-konvention (§7). Behöver INTE vara unikt inom filen — en cell unikidentifieras av hela sin axeltupel. Typiskt fall där id återanvänds: aktiv/passiv-par i sv verb (`pres` förekommer både med `diates: Aktiv` och `diates: Passiv`). |
| `tempus`  | list[str] | villkorad    | Lista av namnkonstanter från `_legend.yaml/tempus`. OR:as till bitmask. |
| `kasus`   | list[str] | villkorad    | Som ovan; från `_legend.yaml/kasus`. |
| `numerus` | str       | villkorad    | EN namnkonstant från `_legend.yaml/numerus`. |
| `species` | str       | villkorad    | EN namnkonstant från `_legend.yaml/species`. |
| `genus`   | str       | villkorad    | EN namnkonstant från `_legend.yaml/genus`. |
| `grad`    | str       | villkorad    | EN namnkonstant från `_legend.yaml/grad`. |
| `person`  | str       | villkorad    | EN namnkonstant från `_legend.yaml/person`. |
| `diates`  | str       | villkorad    | EN namnkonstant från `_legend.yaml/diates`. Aktuell för verb (sv synthetisk passiv -s, ja -(r)areru). Analytiska språk: NULL. |
| `not`     | str       | nej          | Fri kommentar — bara om något i cellen kräver kontext. |

Inga `ex`, `kollaps_med`, eller `lexem_input` — dessa har tagits bort i v2.
Exempel hör hemma i tester (Steg 4-validering), inte i schemat.

---

## 5. Bitmask-OR-kollaps som lagringsregel

När en cell täcker flera värden på *samma* IntFlag-axel (`tempus` eller
`kasus`) — uttryck cellen som en lista. Pipelinen OR:ar bitarna och lagrar
EN rad i `Former` med kombinerat värde:

```yaml
- id: imp_inf
  tempus: [Imp, Inf]    # → tempus=17 i Former, en rad
```

Detta är en **lagringsregel**, inte ett paradigmval. När pipelinen skriver
former till databasen detekterar den celler som producerar identiska
formsträngar för samma lexem; om cellerna skiljer sig endast i en IntFlag-axel
slås de samman till en rad med OR:ade bitar.

Slot-filen kan välja att deklarera vanliga kollapser explicit (som
`tempus: [Imp, Inf]`) för att signalera att en sådan kollaps är förväntad.
Det är en optimeringshint till pipelinen, inte en strikt regel — pipelinen
kan kollapsa även celler som var deklarerade som separata om formsträngarna
visar sig vara identiska.

### IntEnum-axlar — alltid separata rader

IntEnum-axlar (`numerus`, `species`, `genus`, `grad`, `person`) kan **inte**
bitmask-OR:as — schemat tillåter bara ett värde per rad
(`numerus IN (1, 2)`, `species IN (1, 2, 3)`, `person IN (1, 2, 3)`, etc.).

Två celler som skiljer sig i en IntEnum-axel men ger identisk form (t.ex. sv
substantiv `lärare` är samma form i sg obest och pl obest) lagras som
**separata rader** i `Former` med samma form-text. Pipelinen optimerar
LLM-anrop genom att hämta formen en gång och replikera den till båda raderna.

---

## 6. Lexem-modifierare för defektiva paradigm

Vissa lexem följer inte hela inflektionsrummet:

- **Modalverb** (sv: kunna, vilja, skola, må, böra) saknar imperativ
- **Deponens** (sv: finnas, hoppas, trivas, minnas) har bara s-former (passiv-suffix)
- **Defektiva substantiv** (sv: pengar — bara plural; mat — bara singular)

Dessa hanteras med **flaggor på lexem-nivå** — antingen som kolumner på
`Lexem`-tabellen eller som en separat `LexemEgenskaper`-tabell. Slot-filen
listar fortfarande imp-cellen i `verb.yaml`, eftersom andra verb använder
den. Modalverbet märks som "saknar imperativ" på lexem-raden och pipelinen
hoppar över imp-cellen för det lexemet.

**Slot-filerna är språk-/ordklass-globala. Defektiv-information är lexem-lokal.**

---

## 7. Cell-ID-konvention

Lowercase, underscore-separerat, ordningen följer axlarna:

```
{species}_{genus}_{numerus}_{kasus}_{tempus}_{person}_{grad}
```

Bara aktiva axlar inkluderas. Bitmask-listor sorteras **alfabetiskt**
(`ack_dat_nom`, `dat_gen`, `imp_inf`).

### Förkortningar

| Axel    | Förkortning                                      |
|---------|--------------------------------------------------|
| species | `obest` / `best` / `stark` / `svag` / `bland`    |
| genus   | `m` / `f` / `n` / `a` (a = Alla)                 |
| numerus | `sg` / `pl`                                      |
| kasus   | `nom` / `ack` / `dat` / `gen`                    |
| tempus  | `inf` / `pres` / `pret` / `sup` / `imp` / `te` / `neg` / `pot` / `vol` / `kond` / `fut` / `presper` |
| person  | `1` / `2` / `3`                                  |
| grad    | `pos` / `komp` / `superl`                        |

Cell-ID:n med en enda axisvärde-komponent skriver bara värdet (`pres`, inte
`pres_only`). Cell-ID:n med flera axlar konkatenerar enligt ovanstående
ordning (`obest_m_sg_pos`, `imp_inf`).

---

## 8. Versionshantering

- `meta.version` är obligatorisk. Aktuellt: `2`.
- Pipelinen vägrar läsa filer med okänd version.
- Schemaändringar som bryter bakåtkompatibilitet → höj version, dokumentera
  migrationsregel här.

### Migrationsregel: v1 → v2 (2026-05-04)

Hela v1-arkitekturen (klassifikations-filer) är övergiven. Inga v1-filer ska
existera. Migrationsregeln är: **radera och bygg om i v2**. Inget innehåll
överförs eftersom v2 inte klassificerar lexem.

---

## 9. Vad slot-filerna *inte* hanterar

- **Hur** former bildas — slot-filerna specificerar VAD som kan existera, inte
  HUR. Generering är kaikki/LLM:s ansvar.
- **Klassifikation av lexem** — ingen verbgrupp, ingen deklinationsklass.
- **Suppletion / oregelbundenhet** — kaikki har redan formerna; LLM hanterar
  saknade fall. Inga per-lexem paradigm-filer.
- **Defektiva paradigm** — hanteras via lexem-modifierare (§6).
- **Ordbildning, sammansättning, derivation** — slot-filerna täcker bara
  böjningsmorfologi, inte derivationsmorfologi.
