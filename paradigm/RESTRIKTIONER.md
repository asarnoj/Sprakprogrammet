# Semantiska restriktioner — plan

*2026-08-12. Framtagen genom att mäta hur mycket det befintliga
restriktionssystemet faktiskt filtrerar, och vilka meningar som slipper
igenom. Skriven innan något byggdes.*

---

## Varför nu

Meningarna ska genereras **ur repetitionskön**: systemet ser vilka kort som
är på tur, och konstruerar en mening som tränar dem plus en del användaren
redan kan. Det inverterar den vanliga ordningen — meningar författas inte,
de *löses fram*.

Det gör restriktionerna bärande. En människa som skriver meningar fångar
strunt av sig själv. En sökalgoritm som optimerar för täckning gör det inte,
och kommer att producera `flickan gav ett rött barn` systematiskt.

---

## Scope-beslut

> **Osannolikt men välformat är godkänt.** `Flickan köpte en dörr.` är en
> acceptabel mening. Ingen säger så, men den är grammatiskt korrekt och
> semantiskt välformad, och det räcker.

Beslutat 2026-08-12. Konsekvensen är att klassbaserade restriktioner är
tillräckliga — ingen LLM-validering av rimlighet behövs, och inga klasser
behöver bli finare än vad som krävs för att stoppa *kategorifel*.

Det som ska stoppas är alltså `flickan gav en näsa` (kroppsdelar överlåts
inte), inte `flickan köpte en dörr` (osannolikt men möjligt).

---

## Läget före

`MönsterKrav.tagg` är ett semantiskt krav per slot, `Koncept.semantik` en
17-bitars mask. Samma bitmask på båda ställena. Alla 259 substantiv taggade.

**Mekanismen fungerar. Problemet är att ett enda krav bär nästan allt:**

| Krav | Verb som använder det | Substantiv som passerar |
|---|---|---|
| HÄNDELSE | 1 | 2 av 259 |
| KOMMUNIKAT | 2 | 5 |
| DRICKBAR | 1 | 8 |
| ÄTBAR | 1 | 17 |
| PLATS | 2 | 36 |
| MÄNSKLIG | 1 | 45 |
| ABSTRAKT | 6 | 48 |
| ANIMAT | 9 | 54 |
| **KONKRET** | **36** | **211** |

`äta` filtrerar hårt. KONKRET används av 36 verb och släpper igenom 81 %.

**Och renderaren tittar aldrig på `tagg`.** Noll referenser i hela
renderarlagret. Taggning utan validator ändrar ingenting — därför byggs
validatorn först.

### Utgångsmätning 2026-08-12

Validatorn byggd och körd mot 93 verb × 259 substantiv = 24 087 kombinationer:

```
passerar   17 330   (72 %)
avvisas     6 757   (28 %)
```

Det befintliga systemet gör alltså redan en fjärdedel av jobbet. `äta`
avvisar 242 av 259, `dricka` 251, `läsa` 254.

**Men mätningen avslöjade ett hål jag inte letat efter.** Sex verb avvisar
noll — inte för att kravet är svagt, utan för att det inte finns:

| Slot | Antal | Med krav | **Utan krav** |
|---|---|---|---|
| subjekt | 174 | 154 | 20 |
| objekt | 93 | 59 | **34** |
| komplement | 12 | 0 | **12** |
| kommunikat | 10 | 5 | 5 |
| predikativ | 4 | 0 | **4** |
| io | 5 | 5 | 0 |
| adverbial | 3 | 3 | 0 |

**75 av 301 slots har ingen semantisk restriktion alls.** För objektsslotten
är det 34 stycken — nästan lika många som de 36 som har den för svaga
KONKRET-biten. Otaggade slots är alltså ett minst lika stort problem som
trubbiga bitar, och det stod inte i planen ovan.

Två slottyper är helt otaggade: `komplement` (12) och `predikativ` (4).
Ingen av dem går heller att uttrycka i `Mening` idag — specen har fält för
subjekt, objekt, io och adverbial, inget annat. Det hör till
meningskomplexiteten, inte till restriktionerna, men de möts här.

### Mätning efter de tre bitarna

```
           passerar   avvisas
före        17 330     6 757   (28 %)
efter       15 306     8 781   (36 %)
```

Åtta procentenheter — mindre än jag gissade, och skälet är värt att veta.

`ÖVERLÅTBAR` omfattar **176 av 259**, inte de ~100 jag uppskattade. Under
taggningen visade det sig att mycket mer är överlåtbart än jag först
räknade: hus och lägenheter köps, idéer och exempel ges, möbler säljs. Att
smalna av den skulle vara felaktig modellering, inte ett bättre filter.

**Procenttalet är inte måttet.** Det som skulle stoppas stoppas:

```
ge en näsa      AVVISAS   kräver ÖVERLÅTBAR, har KONKRET+KROPPSDEL
ge ett barn     AVVISAS   kräver ÖVERLÅTBAR, har ANIMAT+KONKRET+MÄNSKLIG
kasta ett bord  AVVISAS   kräver HANTERBAR, har KONKRET+INREDNING+ÖVERLÅTBAR
öppna snön      AVVISAS   kräver ÖPPNINGSBAR, har KONKRET+NATURFENOMEN
ge en bok       passerar
öppna dörren    passerar
köpa ett hus    passerar
```

### De 34 otaggade objektsslotarna — mest korrekt otaggade

Förra mätningen flaggade 34 objektsslots utan krav som ett hål. Vid
genomgång är de flesta rätt som de är: `älska`, `hata`, `sakna`, `glömma`,
`minnas`, `önska`, `se`, `höra`, `välja`, `ha`, `förlora` tar genuint nästan
vilket objekt som helst. Känslo-, kognitions- och perceptionsverb ÄR
oselektiva.

Bara `erbjuda` behövde tagg (ÖVERLÅTBAR, tillagd) och `köra`
(RÖRELSE+INSTRUMENT, tillagd). Kvar att titta på: `kosta` (objektet är ett
belopp, inte en sak) och `spela` (spel eller instrument).

---

## Fem relationer, inte en

Bara den första finns idag.

| # | Relation | Läge | Slipper igenom nu |
|---|---|---|---|
| 1 | Verb → sina argument | Finns, 197 mönster | `flickan gav en näsa` |
| 2 | Adjektiv → huvudordet | Saknas helt | `ett rött barn` |
| 3 | Adverb → tempus | Saknas | `Flickan ger en bok igår` |
| 4 | Preposition → komplement | Semantik finns, mönster saknas | `på måndag` / `på bordet` |
| 5 | Determinerare → räknebarhet | `räknebar` finns, används inte | `två ris` |

Punkt 3 är verklig: renderaren producerar `Flickan ger en bok igår.` idag.
Alla tidsadverb — *igår*, *nu*, *snart*, *alltid* — har samma bit (TID=512),
så dåtidsadverb går inte att skilja från nutidsadverb.

Punkt 5 är delvis löst av en olyckshändelse: massord saknar pluralformer,
så `två ris` kraschar redan. Rätt beteende, fel skäl.

---

## Matchningsregeln

`BITMASK.md` §11 säger att masken används för att matcha koncept mot
slot-krav, men aldrig **hur**. Odefinierat, eftersom meningsbyggaren inte
funnits.

> **Regel: OCH.** Konceptet måste ha ALLA bitar som kravet anger.
> `Koncept.semantik & MönsterKrav.tagg == MönsterKrav.tagg`

Med OCH går konjunktioner att uttrycka. Med ELLER går de inte, och hela
resonemanget nedan faller.

---

## Förbud behövs inte — bitar räcker

Första utkastet föreslog en förbudskolumn: `ge` skulle säga "KONKRET men
INTE kroppsdel". Det är onödigt.

Inför i stället en positiv bit `ÖVERLÅTBAR` och tagga de substantiv som kan
byta ägare. Då kräver `ge` en enda bit.

Bättre av tre skäl:

- **En matchningsregel i stället för två.**
- **Biten är ett påstående om världen, inte om verbet** — `ÖVERLÅTBAR`
  återanvänds direkt av `sälja`, `låna`, `köpa`, `erbjuda`.
- **Förbud samlar undantag, bitar samlar ordförråd.** Det första växer med
  verben, det andra med orden.

Plats finns: 17 av 64 bitar används.

---

## De 36 KONKRET-verben

| Grupp | Verb | Krav |
|---|---|---|
| Ägarbyte (10) | ge, ta, köpa, sälja, låna, äga, tjäna, betala, dela, byta | `ÖVERLÅTBAR` |
| Fysisk hantering (8) | bära, dra, kasta, lyfta, lägga, hålla, trycka, samla | `HANTERBAR` |
| Öppning (2) | öppna, stänga | `ÖPPNINGSBAR` |
| Redan täckta (2) | räkna → kolumnen `räknebar`; köra → RÖRELSE+INSTRUMENT (8 fordon) | — |
| Står kvar (6) | hitta, röra, slå, visa, använda, lämna | KONKRET är rätt här |
| Långsvans (8) | reparera, tvätta, måla, skära, bryta, blanda, fylla, bygga | okänt |

`ÖVERLÅTBAR` skulle omfatta ~100 av 259 i stället för 211.

Långsvansen är där uppskattningen kan spricka: de åtta behöver var sitt
kriterium (skärbart, tvättbart, behållare, konstruerbart) och kan kräva
egna bitar.

---

## Ordning

1. **Validatorn först.** Utan den ändrar taggning ingenting, och ingen
   mätning går att göra. Byggs mot befintliga krav och ger ett
   utgångsvärde: hur många av dagens meningar skulle avvisas?
2. Matchningsregeln skrivs in i `BITMASK.md`.
3. Tre bitar definieras och taggas; de 36 verben skrivs om.
4. Adjektivrelationen — behöver egen representation, `MönsterKrav.slot` har
   ingen `attribut`-roll. Åtta adjektivklasser × 21 substantivklasser.
5. Adverb → tempus. Tidsadverben behöver skiljas åt.
6. Preposition → komplement, determinerare → räknebarhet.
7. Mätning efter varje steg: hur mycket strunt är kvar?

Uppskattning: 8–12 arbetspass i den storlek projektet kört hittills.

---

## Vad detta INTE ger

Efter allt ovan är meningarna grammatiskt korrekta och semantiskt
välformade. De är inte garanterat *idiomatiska*. `Flickan köpte en dörr`
överlever, och enligt scope-beslutet ovan ska den göra det.

Klassbaserade restriktioner kan inte fånga osannolikhet, bara kategorifel.
Att sträcka sig längre skulle kräva antingen klasser som blir allt finare
utan gräns, eller världskunskap — och ingetdera hör hemma i en bitmask.
