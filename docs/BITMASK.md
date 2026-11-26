# Bitmask-specifikation — Språkprogrammet
*Fastställd 2026-04-10. Denna fil är den auktoritativa källan för alla numeriska koder i databasen.*

---

## Filosofi

Varje grammatisk dimension lagras som ett heltal. Dimensioner som är bitmasks (IntFlag)
kan kombineras med | (bitvisa OR). Dimensioner som är exklusiva (IntEnum) tar bara
ett värde i taget.

**Nyckelprincipen:** Former-tabellen representerar ett universellt grammatikrum.
Varje språks renderer frågar bara efter de dimensioner det språket bryr sig om —
alla andra kolumner är NULL och ignoreras. En form kan täcka flera värden
på en dimension (t.ex. samma adjektivform för alla kasus utom genitiv).

---

## Tabellöversikt — vilka kolumner används per språk

| Kolumn    | sv | en | fr | de | es | it | ja |
|-----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| numerus   | ✓  | ✓  | ✓  | ✓  | ✓  | ✓  | —  |
| species   | ✓  | —  | —  | ✓  | —  | —  | —  |
| kasus     | △  | —  | —  | ✓  | —  | —  | —  |
| genus     | ✓  | —  | ✓  | ✓  | ✓  | ✓  | —  |
| tempus    | ✓  | ✓  | ✓  | ✓  | ✓  | ✓  | ✓  |
| grad      | ✓  | ✓  | ✓  | ✓  | ✓  | ✓  | △  |
| person    | —  | —  | ✓  | ✓  | ✓  | ✓  | —  |
| diates    | ✓  | △  | △  | △  | △  | △  | ✓  |

△ = delvis / begränsat.  sv kasus: bara Genitiv (8) används.
ja numerus: bara för pronomen och kvantifierade fraser, annars implicit.
ja grad: i-adjektiv böjs syntetiskt; na-adjektiv analytiskt (mer + lemma).

---

## 1. Tempus (IntFlag — kombinerbar)

Lagras i `Former.tempus`. Bitmask: flera värden kan kombineras om samma form
täcker flera funktioner (t.ex. tyska Konjunktiv I = presens i lärd stil).

```
Bit    Värde   Funktion                     sv          fr              de          es/it       en          ja
───────────────────────────────────────────────────────────────────────────────────────────────────────────
  1        1   Infinitiv / Grundform        äta         manger          essen       comer       eat         食べる (辞書形)
  2        2   Presens / Nutid              äter        mange (sg 1p)   esse        como        eats        食べます (ます形)
  4        4   Preteritum / Imperfekt       åt          mangeais        aß          comía       ate         —
  8        8   Supinum / Perfektparticip    ätit        mangé           gegessen    comido      eaten       食べた (た形)
 16       16   Imperativ                   ät          mange (2p sg)   iss         come        eat!        食べろ (命令形)
 32       32   Preteritum perfekt *        —           passé composé   —           —           —           —
 64       64   Futurum *                   —           mangera         —           comeré      will eat    —
128      128   Te-form / Gerundium         —           —               —           —           —           食べて (て形)
256      256   Negationsstam               —           —               —           —           —           食べない (ない形)
512      512   Potentialisform             —           —               —           —           —           食べられる (可能形)
1024    1024   Volitiv / Konjunktiv *      —           mange (subj)    esse (Konj) coma        —           食べよう (意志形)
2048    2048   Konditionalis *             —           mangerait       —           comería     would eat   —
```

`*` = analytisk form (bildas av renderer + hjälpverb) — formen som lagras är
     stammen/participet, inte den fullständiga frasen.

### Kombinerade bitar
Kombineras med | när samma skrivna form tjänar flera funktioner:

- `sv: Infinitiv|Imperativ = 17` — många svenska verb har identisk form (gå, spring)
- `de: Infinitiv|Presens(1p pl)|Presens(3p pl) = 3` — essen/essen/essen
- `fr: Preteritum|Preteritum_perfekt = 36` — passé simple räknas som båda (litterär)

### Japanskt specialfall
Japanska har inte tempus i västerländsk mening. Bitarnas semantiska betydelse
för japanska:

| Bit | Japansk funktion         | Exempel      |
|-----|--------------------------|--------------|
|   1 | 辞書形 (lemmaform)       | 食べる       |
|   2 | ます形 (artig presens)   | 食べます     |
|   4 | Implicit (ej lagrat)     | —            |
|   8 | た形 (perfekt/förflutet) | 食べた       |
|  16 | 命令形 (imperativ)       | 食べろ/食べなさい |
| 128 | て形 (te-form)           | 食べて       |
| 256 | ない形 (negativ stam)    | 食べない     |
| 512 | 可能形 (potentialis)     | 食べられる   |
|1024 | 意志形 (volitiv)         | 食べよう     |

Japanska adjektiv (i-adjektiv) har egna former lagrade med samma tempusbitar:

| Bit | i-adjektiv-funktion  | Exempel (高い)  |
|-----|----------------------|-----------------|
|   1 | Grundform (positiv)  | 高い            |
|   4 | Preteritum           | 高かった        |
| 256 | Negation             | 高くない        |
|   8 | Adverbform           | 高く (= supinum)|

na-adjektiv böjs analytiskt (renderer lägger till だ/です/じゃない etc.),
bara grundformen utan な lagras.

---

## 2. Numerus (IntEnum — exklusiv)

Lagras i `Former.numerus` och `Lexem.numerus` (för pronomen).

```
1 = Singular
2 = Plural
```

Används av: sv, en, fr, de, es, it.
Ej used av: ja (antal uttrycks med räkneord + klassifikator; renderer lägger inte till ändelse).

---

## 3. Species (IntEnum — exklusiv)

Lagras i `Former.species`. Anger bestämdhet via suffix (syntetisk artikel).

```
1 = Obestämd (indefinit)
2 = Bestämd  (definit)
```

| Språk | Metod                                              |
|-------|----------------------------------------------------|
| sv    | Suffix på substantiv (boll/bollen) och adjektiv    |
| de    | Suffix på adjektiv beror på artikeltyp (stark/svag/blandad böjning) |
| fr    | Analytisk — separat artikel (un/le); species=NULL i Former |
| en    | Analytisk — separat artikel (a/the); species=NULL  |
| es/it | Analytisk — separat artikel; species=NULL          |
| ja    | Ingen artikel; species=NULL                        |

### Tyskt specialfall: adjektivböjning
Tyska adjektiv böjs olika beroende på föregående artikel (stark/svag/blandad).
Detta kodas med species-värdet på adjektivformen:

```
species=1 = Stark böjning    (inget föregående bestämningsord: guter Wein)
species=2 = Svag böjning     (efter bestämd artikel: der gute Wein)
species=3 = Blandad böjning  (efter obestämd artikel: ein guter Wein)
```

OBS: species=3 är tyskt exklusivt — existerar ej för andra språk.

---

## 4. Kasus (IntFlag — kombinerbar)

Lagras i `Former.kasus`. Anger nominalfrasens grammatiska roll.

```
Bit   Funktion
──────────────────────────────────────────────────────────────────
  1   Nominativ  — subjekt, predikativ
  2   Ackusativ  — direkt objekt
  4   Dativ      — indirekt objekt, efter vissa prepositioner
  8   Genitiv    — ägande, samband
```

### Användning per språk

| Språk | Distinktioner                           | Typiska värden i Former        |
|-------|-----------------------------------------|--------------------------------|
| sv    | Bara genitiv (-s) är morfologisk        | kasus=7 (nom+ack+dat), kasus=8 |
| de    | Alla fyra kasus distinkt på artikel+adj | 1, 2, 4, 8 var för sig         |
| fr    | Ingen kasusböjning                      | kasus=7 (alla utom gen), NULL  |
| en    | Ingen kasusböjning (utom pronomen)      | kasus=7 eller NULL             |
| es/it | Ingen kasusböjning                      | kasus=7 eller NULL             |
| ja    | Partiklar hanterar kasus — renderer-ansvar | kasus=NULL alltid           |

### Kombinerade bitar (vanliga)
- `kasus=7` (1+2+4): formen gäller för alla kasus utom genitiv — vanligast
- `kasus=3` (1+2): formen gäller för nominativ och ackusativ (t.ex. tyska neutrum sg)
- `kasus=6` (2+4): ackusativ och dativ (t.ex. tyska femininum sg: der→der i dat, die→die i ack)

---

## 5. Genus (IntEnum — exklusiv)

Lagras i `Lexem.genus` (substantivets inherenta genus) och `Former.genus`
(adjektivformens böjningsklass vid kongruens).

```
1 = Utrum / Maskulin   (sv: en-ord | fr/es/it: maskulin | de: maskulin)
2 = Neutrum / Feminin  (sv: ett-ord | fr/es/it: feminin  | de: feminin)
3 = Tyskt neutrum      (de: Neutrum — det=das)
```

OBS: genus=3 i Former används också i **svenska** för adjektivformer
som gäller för alla genus (plural, bestämd form):

```
sv adjektiv Former:
  genus=1, numerus=1, species=1 → gullig    (utrum sg obestämd)
  genus=2, numerus=1, species=1 → gulligt   (neutrum sg obestämd)
  genus=3, numerus=2, species=1 → gulliga   (pl obestämd)
  genus=3, numerus=*, species=2 → gulliga   (alla genus, bestämd)
```

Praktisk regel: `genus=3` = "form gäller oavsett genus" (svenska plural/bestämd)
eller "tyskt neutrum".

---

## 6. Grad (IntEnum — exklusiv)

Lagras i `Former.grad`. Gäller adjektiv och adverb.

```
1 = Positiv
2 = Komparativ
3 = Superlativ
```

### Syntetisk vs. analytisk komparation

| Språk | Metod                                               |
|-------|-----------------------------------------------------|
| sv    | Syntetisk suffix (-are/-ast) + analytisk (mer/mest) |
| de    | Syntetisk suffix (-er/-sten) med umlaut             |
| en    | Syntetisk (-er/-est) för korta adj; analytisk annars|
| fr    | Alltid analytisk (plus/le plus) — lagras ej i Former|
| es/it | Alltid analytisk (más/più) — lagras ej i Former     |
| ja    | i-adj syntetisk (suffix); na-adj analytisk (もっと) |

När komparation är analytisk (fr/es/it) lagras bara positiv-formen.
Renderer lägger till gradordet.

---

## 7. Person (IntEnum — exklusiv)

Lagras i `Former.person` och `Lexem.person` (för pronomen).

```
1 = Första person  (jag/vi, je/nous, ich/wir, yo/nosotros, io/noi)
2 = Andra person   (du/ni, tu/vous, du/ihr, tú/vosotros, tu/voi)
3 = Tredje person  (han/hon/det/de, il/elle/ils, er/sie/es/sie, él/ella/ellos, lui/lei/loro)
```

Används av: fr, de, es, it (fullständig personböjning).
Ej used av: sv (ingen personböjning på verb), en (bara 3p sg: eats vs eat), ja (ingen).

Svenska och engelska verb har person=NULL i Former utom eventuellt 3p sg engelska.

---

## 7.5. Diates (IntEnum — exklusiv)

Lagras i `Former.diates`. Anger om en form är aktiv eller passiv.

```
1 = Aktiv   (default — vanlig morfologisk form)
2 = Passiv  (synthetisk passiv-/deponens-form)
```

| Språk | Distinktion                              | Användning                                    |
|-------|------------------------------------------|-----------------------------------------------|
| sv    | -s-suffix på verbets stam                | talas, talades, talats — synthetisk           |
| ja    | -(r)areru-suffix                         | 食べられる — synthetisk                       |
| en    | analytisk: be + perfektparticip          | diates=NULL i Former; renderaren bygger       |
| fr    | analytisk: être + perfektparticip        | diates=NULL i Former                          |
| de    | analytisk: werden + perfektparticip      | diates=NULL i Former                          |
| es    | analytisk: ser + perfektparticip         | diates=NULL i Former                          |
| it    | analytisk: essere/venire + perfektparticip | diates=NULL i Former                        |

### Deponens (sv)

Svenska deponensverb (hoppas, finnas, trivas, minnas, andas) har bara
s-former trots att betydelsen är aktiv. De lagras med `diates=Passiv`
i Former; en lexem-modifierare markerar att verbet är deponens — vilket
upplyser renderaren om att inte tolka formerna passivt och att inte
försöka bilda aktiva former.

---

## 8. Valens (IntFlag — kombinerbar)

Lagras i `Koncept.valens`. Styr vilka argument-slots meningsbyggaren öppnar.

```
Bit   Värde   Funktion
─────────────────────────────────────────────────────────────────────────────
  1       1   Intransitiv   — inget objekt (springa, sova, existera)
  2       2   Transitiv     — direkt objekt (äta [mat], se [hunden])
  4       4   Ditransitiv   — direkt + indirekt objekt (ge [honom] [boken])
  8       8   Reflexiv      — reflexivt pronomen (tvätta sig, gifta sig)
 16      16   Kopula        — predikativlucka (vara [trött], bli [lärare])
```

Vanliga kombinationer:
- `3` (1+2): verb som kan användas med eller utan objekt (äta / äta mat)
- `6` (2+4): ditransitivt verb som alltid tar båda objekten (ge)
- `10` (2+8): transitiv + reflexiv (skära sig / skära brödet)
- `17` (1+16): kopula utan obligatoriskt komplement (verka, vara)

---

## 9. Personlighet (IntFlag — kombinerbar)

Lagras i `Koncept.personlighet`. Styr dummy-subjekt i opersonliga konstruktioner.

```
1 = Personlig   — tar riktigt subjekt (springa, äta)
2 = Opersonlig  — tar dummy-subjekt "det" (sv) / "il" (fr) / "es" (de) (regna, hända)
```

Kombination `3` (1+2): verb som kan vara båda beroende på konstruktion (t.ex. "det händer" / "något händer").

---

## 10. Frastyp (IntFlag — kombinerbar)

Lagras i `MönsterKrav.frastyp`. Styr vilken syntaktisk frastyp som accepteras i en slot.

```
Bit   Värde   Frastyp
─────────────────────────────────────────────────────────────
  1       1   Nominalfras       (en hund, bollen, han)
  2       2   Adjektivfras      (glad, mycket trött)
  4       4   Prepositionsfras  (i skolan, på bordet)
  8       8   Adverbfras        (snabbt, gärna, aldrig)
 16      16   Infinitivfras     (att springa, att äta mat)
 32      32   Bisatsfras        (att han springer, när du äter)
```

---

## 11. Semantik (IntFlag — kombinerbar)

Lagras i `Koncept.semantik`. Används av meningsbyggaren för att matcha koncept
mot slot-krav (MönsterKrav.tagg). Samma bitmask används på båda ställena.

Semantikbitar är ordklassoberoende — en bit som ANIMAT gäller på substantivets
`Koncept.semantik` OCH som krav i `MönsterKrav.tagg` ("subjekt måste vara animat").

```
Bit     Värde   Etikett       Vad det markerar
────────────────────────────────────────────────────────────────────────────────
   1        1   ANIMAT        Levande varelse som rör sig på eget initiativ
                              (människa, djur — ej växt, eld, flod)
   2        2   KONKRET       Har fysisk, gripbar existens (boll, bord, träd)
   4        4   ABSTRAKT      Idé, känsla, egenskap utan fysisk form (frihet, kärlek)
   8        8   ÄTBAR         Kan ätas eller drickas (bröd, äpple, vin, vatten)
  16       16   PLATS         Geografisk plats eller behållare (stad, rum, skog)
  32       32   MÄNSKLIG      En människa eller mänsklig roll (lärare, barn, granne)
  64       64   RÖRELSE       Sak som typiskt är i rörelse eller transporterar
                              (bil, flod, vind, boll i rörelsekontext)
 128      128   RIKTNING      Riktning eller orienterat läge (norr, höger)
 256      256   HÄNDELSE      Händelse som kan anordnas eller deltas i
                              (fest, möte, kurs, match, krig)
 512      512   TID           Tidsperiod eller tidpunkt (dag, år, morgon, april)
1024     1024   INSTRUMENT    Föremål som används som verktyg (kniv, penna, bil)
2048     2048   KOMMUNIKAT    Kommunikat / yttrande (fråga, ord, berättelse, svar)
4096     4096   DRICKBAR      Dricks snarare än äts (vatten, mjölk, kaffe, öl, vin)
8192     8192   KROPPSDEL     Kroppsdel (näsa, hand, hjärta) — kan inte ges bort
16384   16384   KLÄDESPLAGG   Bärs på kroppen (byxa, sko, glasögon)
32768   32768   INREDNING     Möbel, husgeråd, byggnadsdel (bord, lampa, dörr)
65536   65536   NATURFENOMEN  Väder och naturkraft (regn, storm, eld) — ej föremål
131072 131072   ÖVERLÅTBAR    Kan byta ägare (ge, sälja, låna, köpa, erbjuda)
262144 262144   HANTERBAR     Kan lyftas och bäras för hand
524288 524288   ÖPPNINGSBAR   Har en öppning som kan öppnas och stängas
```

**Matchningsregeln är OCH.** Konceptet måste ha ALLA bitar kravet anger:
`Koncept.semantik & MönsterKrav.tagg == MönsterKrav.tagg`. Regeln var
odefinierad fram till 2026-08-12 — texten ovan sade att masken används för
att matcha, men aldrig hur. Implementerad i
`src/sprakprog/rendering/restriktioner.py`.

Bitarna 131072–524288 tillkom 2026-08-12. Motivet står i
`paradigm/RESTRIKTIONER.md`: KONKRET-kravet användes av 36 verb och släppte
igenom 211 av 259 substantiv, så `flickan gav en näsa` passerade. Bitarna är
POSITIVA påståenden om världen i stället för förbud knutna till verb — då
räcker en matchningsregel, och biten återanvänds mellan verb.

Bitarna 4096–65536 tillkom 2026-08-10. Mätning visade att 259 substantiv föll
på bara 15 distinkta värden, med 84 ord i ett enda fack (enbart KONKRET) där
näsa, byxa, bord och regn var utbytbara — "flickan gav sin bror en näsa"
passerade varje semantiskt krav. Kategorierna fanns redan i konceptnycklarnas
prefix och lyftes in i bitmasken via `ordbok/migrationer/semantik_utökad.sql`.
Efter tillägget: 21 distinkta värden, största facket 42 (och det facket är
MÄNSKLIG, alltså en sammanhängande klass).

**ÄTBAR och DRICKBAR utesluter varandra** för rena drycker — vatten har
DRICKBAR men inte ÄTBAR, så att "äta vatten" faller. Soppa har båda.

### Kombinationsexempel

| Koncept       | Bitar                  | Värde | Förklaring                          |
|---------------|------------------------|-------|-------------------------------------|
| hund          | ANIMAT+KONKRET         |   3   | levande, fysisk varelse             |
| lärare        | ANIMAT+KONKRET+MÄNSKLIG|  35   | människa i roll                     |
| boll          | KONKRET                |   2   | fysisk men ej animat                |
| äpple         | KONKRET+ÄTBAR          |  10   | fysisk och ätbar                    |
| park          | KONKRET+PLATS          |  18   | fysisk plats                        |
| stad          | KONKRET+PLATS+MÄNSKLIG |  50   | plats med mänsklig kontext          |
| kärlek        | ABSTRAKT               |   4   | ren abstraktion                     |
| möte          | ABSTRAKT+HÄNDELSE      | 260   | abstrakt händelse                   |
| bil           | KONKRET+RÖRELSE+INSTRUMENT| 66 | fysisk, transporterande, verktyg    |
| dag           | ABSTRAKT+TID           | 516   | tidsperiod                          |
| fråga         | ABSTRAKT+KOMMUNIKAT    |2052   | abstrakt kommunikat                 |
| mat           | KONKRET+ÄTBAR          |  10   | substans (oräknebar)                |

### Verbsemantikets relation till Semantik
Verb har i allmänhet semantik=NULL — deras betydelse kodas i Valens och MönsterKrav.
Undantag: verb med stark semantisk signatur som styr meningsbyggaren:

```
RÖRELSE (64):   rör_gå, rör_springa, rör_flyga — kräver rörelsekontroll på adverbial
KOMMUNIKATION:  se MönsterKrav-slot 'kommunikat' med tagg=KOMMUNIKAT (2048)
```

---

## 12. Gradbarhet (TEXT — exklusiv)

Lagras i `Koncept.gradbarhet`. Gäller adjektiv.

```
'Gradbar'      — kan jämföras (glad → gladare → gladast)
'Icke gradbar' — kan ej jämföras (gravid, kvadratisk, dead)
NULL           — ej tillämplig (ej adjektiv)
```

---

## 13. Räknebar (INTEGER — boolean)

Lagras i `Koncept.räknebar`. Gäller substantiv.

```
1   = Räknebar (default / NULL tolkas som räknebar)
0   = Oräknebar / masssubstantiv (vatten, mat, kärlek, luft)
```

Oräknebara substantiv renderas alltid i singular och tar ingen obestämd artikel
("mat" inte "en mat"; "vatten" inte "ett vatten").

---

## 14. Prenominal (INTEGER — boolean)

Lagras i `Lexem.prenominal`. Gäller adjektiv-lexem.

```
1   = Adjektivet placeras FÖRE substantivet (default / NULL tolkas som 1)
0   = Adjektivet placeras EFTER substantivet
```

Används för franska adjektiv som normalt följer substantivet (rouge, bleu, français)
kontra adjektiv som föregår (petit, grand, beau, nouveau, vieux).

---

## Fullständig böjningsmatris per språk och ordklass

### Substantiv

| Språk | Dimensioner som varierar                   | Antal radtyper (typisk) |
|-------|--------------------------------------------|-------------------------|
| sv    | numerus × species × kasus(2)               | 4×2×2 = 8 (varav kasus bara ger +4) |
| en    | numerus                                    | 2                        |
| fr    | numerus                                    | 2                        |
| de    | numerus × kasus × genus(artikel)           | 2×4 = 8 (men ofta fler pga synkretism) |
| es    | numerus × genus                            | 2×2 = 4 (men genus fixerat per ord) |
| it    | numerus × genus                            | 2×2 = 4                  |
| ja    | (ingen böjning — bara en rad)              | 1                        |

### Verb

| Språk | Dimensioner som varierar             | Antal radtyper (typisk) |
|-------|--------------------------------------|-------------------------|
| sv    | tempus(5)                            | 5                        |
| en    | tempus(3) × person(delvis)           | 4–5                      |
| fr    | tempus(4+) × person(3) × numerus(2) | 20–30                    |
| de    | tempus(4+) × person(3) × numerus(2) | 20–30                    |
| es    | tempus(6+) × person(3) × numerus(2) | 40–60                    |
| it    | tempus(6+) × person(3) × numerus(2) | 40–60                    |
| ja    | tempus(6 japanska bitar)             | 6–8                      |

### Adjektiv

| Språk | Dimensioner som varierar                       | Antal radtyper (typisk) |
|-------|------------------------------------------------|-------------------------|
| sv    | genus(3) × numerus × species × grad(3)         | 7–10                    |
| en    | grad(3) — eller analytisk                      | 1–3                     |
| fr    | genus(2) × numerus × grad(analytisk)           | 4                        |
| de    | genus(3) × numerus × kasus × species(3 böjn.) | 16–24                   |
| es    | genus(2) × numerus                             | 4                        |
| it    | genus(2) × numerus                             | 4                        |
| ja    | i-adj: tempus(4 bitar); na-adj: 1 rad          | 4 / 1                   |

---

*Sist reviderad: 2026-04-10*
