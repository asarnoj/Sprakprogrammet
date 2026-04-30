# Konventioner — Flerspråkig bas-ordbok

## 1. Vad är systemet?

Det här är en **bas-ordbok för ett datoriserat språkinlärningssystem**. Systemet genererar meningar på 7 språk: svenska (sv), engelska (en), franska (fr), tyska (de), spanska (es), italienska (it) och japanska (ja).

Databasen är organiserad som en **hub-modell**: varje *Koncept* representerar ett semantiskt begrepp. Alla Lexem kopplade till samma Koncept är **ekvivalenta uttryck** på respektive språk — inte synonymer, utan den bästa/standardiserade representationen av det begreppet på varje språk.

Lemman används som **bas för meningsbyggnad och böjning**. Det är viktigt att:
- Lemmat kan generera korrekta meningar i de vanligaste kontexterna
- Lemmat är i rätt grundform för morfologisk böjning

---

## 2. Lemmaformat per språk

| Språk | Verb | Substantiv/Pronomen | Adj/Adv | Övrigt |
|-------|------|---------------------|---------|--------|
| sv | infinitiv ("springa") | nominativ singular | positiv form | — |
| en | infinitiv utan "to" ("run") | nominativ singular | positiv form | — |
| fr | infinitiv ("courir") | maskulinum singular obestämd | maskulinum positiv | — |
| de | infinitiv ("laufen") | nominativ singular obestämd | maskulinum positiv | — |
| es | infinitiv ("correr") | maskulinum singular | maskulinum positiv | — |
| it | infinitiv ("correre") | maskulinum singular | maskulinum positiv | — |
| ja | verb: u-form/辞書形 ("走る") | kanji+kana standardform | — | se Japanska-specifikt |

---

## 3. Nivåbedömning (CEFR)

- **A1** — Grundläggande överlevnadsord; de allra vanligaste funktionsorden
- **A2** — Elementär kommunikation; vanliga fraser och konstruktioner
- **B1** — Tröskelkompetens; mer nyanserade uttryck

Nivån avser *mottagningssvårighetsgrad* för en genomsnittlig vuxen inlärare.

---

## 4. Renderarens ansvar (flagga INTE dessa)

Systemets **renderare** (en separat komponent) ansvarar för:

- **Genus-kongruens**: ett/eine/un/une, alemán/alemana osv. — lemmat är maskulinum/utrum, renderaren böjer
- **Kasus**: tyskt kasus (den/dem/des), franska prepositioner som kräver genitiv-form osv.
- **Subjunktiv**: "bien que tu **sois**", "para que **vayas**", "affinché **impari**" — lemmat är infinitiv, renderaren sätter rätt modus
- **Franska "ne"**: lemmat är "pas" (talspråksnorm); renderaren lägger till "ne" i formell text
- **Japanska postpositioners placering**: に/で/へ/は/も/だけ placeras EFTER det de modifierar — detta hanteras av renderaren, inte lemmaformen
- **Japanska räknarord**: 一冊/二人 osv. — renderaren kombinerar siffra + räknare per kontext

---

## 5. Förenklingsfilosofi

**Semantisk perfekthet är inte målet.** Förenklingar är tillåtna om de är:

1. **Konsistenta** — samma strategi inom hela ordklassen
2. **Icke-vilseledande** — inläraren genererar inga *felaktiga* meningar, bara meningar med reducerad nyans
3. **Dokumenterade** — kommenterad i CSV:en om avvikelsen är signifikant

**Exempel på hållbar förenkling:**
> Japanska demonstrativ har 3 avståndsnivåer (nära talaren / nära lyssnaren / fjärran från båda). Västerländska språk har 2 (nära / fjärran). Lösning: その (nära lyssnaren) och あの (fjärran från båda) samlas båda under konceptet `demonstrativ_fjärran`. En inlärare som använder detta lemma skapar aldrig en *fel* mening — bara en något oprecis en.

---

## 6. Böjning och Former

Lemmat är **bas för Former-tabellen** (morfologidata). Det är kritiskt att lemmaformen:
- Är korrekt grundform (inte böjd form, inte sammansättning)
- Är den form som morfologisystemet kan böja vidare från

**Flagga om:** lemmat är i fel kasus (t.ex. tyskt pronomen i ackusativ istf nominativ), fel verbform (böjt istf infinitiv), eller om lemmaformen orsakar tvetydighet i böjningsparadigmet.

---

## 7. Japanska-specifikt

**Postpositioner** — Japanska prepositioner är postpositioner: に, で, へ, から, まで, と osv. Lemmat är partikeln ensam. Renderaren placerar den efter substantivet. Flagga inte ordföljd.

**Bundna morfem (modala suffix)** — たい (vill), なければならない (måste), てもいい (får), べき (bör) är suffix som fästs på verbstammen. Lemmat är suffixet/konstruktionen. Renderaren fogar det till verbstammen. Flagga inte att det "inte kan stå ensamt".

**Negativkrav** — Följande kräver att *huvudverbet* står i negativ form (ない/ません):
- 決して (aldrig), めったに (sällan), 誰も (ingen), 何も (inget), もう～ない (inte längre)
Detta är korrekt och dokumenterat — flagga det inte som fel.

**Trepunktsdemonstrativ** → tvåpunkts-förenkling:
- この (nära talaren) = `demonstrativ_nara`
- その (nära lyssnaren) + あの (fjärran från båda) = båda under `demonstrativ_fjärran`
Detta är en medveten, hållbar förenkling — flagga det inte.

---

## 8. Kända undantag (INTE fel)

Dessa är **medvetna designbeslut** — flagga dem inte som fel:

| Koncept | Språk | Lemma | Anledning |
|---------|-------|-------|-----------|
| verb_bli + modal_ska | de | werden | Polysemi; tyska "werden" täcker båda |
| adv_fortfarande + adv_igen | fr | encore | Polysemi; franska "encore" täcker båda |
| prep_i + prep_på + prep_vid | es | en | Polysemi; spanska "en" täcker alla tre |
| prep_på + prep_om | fr | sur | Polysemi; franska "sur" täcker båda |
| prep_på + prep_om | it | su | Polysemi; italienska "su" täcker båda |
| adv_då (sekventiell) | de | dann | Två tyska former under adv_då: "dann" = sekventiell |
| adv_då (retrospektiv) | de | damals | Två tyska former under adv_då: "damals" = retrospektiv |
| modal_måste + modal_bör | fr | devoir | Polysemi; franska "devoir" täcker båda |
| modal_kan + modal_får | fr | pouvoir | Polysemi; franska "pouvoir" täcker båda |

---

## 9. Beslutsprocess

**Du som granskare presenterar ALDRIG ändringen som ett beslut.** Du presenterar:
- Vad du observerade
- Varför det eventuellt är ett problem i systemets kontext
- Ett eller flera alternativa lemman med motivering

Användaren undersöker och beslutar. Ändringar genomförs sedan separat.
