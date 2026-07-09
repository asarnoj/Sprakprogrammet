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

### Systemets avgränsning: grammatik, inte talspråk

Systemet siktar **enbart på teorin och grammatiken för vanliga, korrekta
meningar som får fram ett budskap**. Det siktar INTE på:

- Talspråklighet, idiomatik eller register (formellt/informellt)
- Nyanser i vilka ord som passar i vilka kontexter
- Kulturella konventioner kring ordval

Sådana mönster går inte att fånga i detta system och är uttryckligen utanför
scope. Projektet ger grundkunskapen; kulturen och nyanserna lär sig
användaren efteråt, i mötet med det riktiga språket.

**Konsekvens för granskning:** flagga ALDRIG ett lemma eller en form för att
den är "stel", "formell", "ovanlig i talspråk" eller "inte vad en
modersmålstalare skulle säga" — så länge den är grammatiskt korrekt och
begriplig. Flagga endast det som är *fel*: fel form, fel betydelse, fel
genus, brott mot lemmaformatet (§2).

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

### Flerordslemman — böjbart huvud

Vissa lemman är flerordiga: sv "laga mat", "lita på", "gifta sig";
fr "faire confiance", "se marier"; es "pedir prestado"; it "prendere in
prestito". Konventionen för vilket ord som böjs:

> **Det böjbara huvudet är det första ordet som inte är reflexivmarkör.**
> Reflexivmarkörer: fr `se`/`s'`, de `sich`. Övriga ord i lemmat är
> oböjliga satelliter (partiklar, objekt, particip) som följer med oförändrade.

Exempel: "laga mat" → *laga* böjs ("lagar mat"); "faire confiance" → *faire*;
"se marier" → *marier* (se-pronomenet böjs av renderaren: me/te/se/nous/vous);
"sich erinnern" → *erinnern*; "pedir prestado" → *pedir*.

Böjningspipelinen (`ordbok generera`) ska skicka hela lemmat till LLM:en och
instruera den att böja huvudet enligt denna regel. Undantag som inte följer
regeln dokumenteras här (inga kända ännu).

Sv-reflexiver ("gifta sig", "skynda sig") och ja-suffixkonstruktioner följer
samma princip: första icke-markör-ordet böjs, "sig" står kvar oförändrat
(renderaren väljer mig/dig/sig).

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
| prep_i + prep_vid | es | en | Polysemi; spanska "en" täcker båda (prep_på = "sobre") |
| prep_på + prep_om | fr | sur | Polysemi; franska "sur" täcker båda |
| prep_på + prep_om | it | su | Polysemi; italienska "su" täcker båda |
| adv_då (sekventiell) | de | dann | Två tyska former under adv_då: "dann" = sekventiell |
| adv_då (retrospektiv) | de | damals | Två tyska former under adv_då: "damals" = retrospektiv |
| modal_måste + modal_bör | fr | devoir | Polysemi; franska "devoir" täcker båda |
| modal_kan + modal_får | fr | pouvoir | Polysemi; franska "pouvoir" täcker båda |
| adj_eko_dyr + adj_s_hög | ja | 高い | Polysemi; 高い täcker dyr och hög |
| adj_ev_intressant + adj_ev_rolig | ja | 面白い | Polysemi |
| adj_k_normal + adj_m_vanlig | ja | 普通 | Polysemi |
| adj_t_het + adj_t_varm | fr | chaud | Franska skiljer inte het/varm |
| adj_k_dålig + adj_ev_elak | es, it | malo, cattivo | Polysemi |
| rör_köra + rör_åka | de | fahren | Polysemi; fahren täcker köra och åka |
| kom_fråga + per_höra + per_lyssna | ja | 聞く | Polysemi; 聞く täcker alla tre |
| per_känna + per_lukta | fr, es | sentir | Polysemi (it sentire täcker även höra) |
| fys_hitta + gen_tycka | fr, de, it | trouver, finden, trovare | Polysemi ("jag finner att…") |
| tid_eftermiddag + tid_kväll | es | tarde | Polysemi; noche börjar sent |
| krop_ben + krop_fot | ja | 足 | Polysemi; 足 täcker båda |
| hem_badrum + hem_toalett | es, it | baño, bagno | Polysemi |
| hem_hus + plats_hem | fr, es, it | maison, casa, casa | Polysemi |
| skol_lärare + skol_professor | fr, es | professeur, profesor | Polysemi |
| kläd_kalsong + kläd_trosor | de, ja | Unterhose, パンツ | Ingen genusdistinktion |
| kom_berätta + kom_prata | ja | 話す | Polysemi |
| fys_göra + gen_spela | ja | する | Polysemi |
| arb_leka + gen_spela | en, fr, de, es, it | play, jouer, spielen, jugar, giocare | Polysemi; bara sv/ja skiljer leka/spela |

---

## 9. Beslutsprocess

**Du som granskare presenterar ALDRIG ändringen som ett beslut.** Du presenterar:
- Vad du observerade
- Varför det eventuellt är ett problem i systemets kontext
- Ett eller flera alternativa lemman med motivering

Användaren undersöker och beslutar. Ändringar genomförs sedan separat.
