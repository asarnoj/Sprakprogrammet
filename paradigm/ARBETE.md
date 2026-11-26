# Arbetet — vad som är kvar, per byggsteg

*Skriven 2026-11-11. Den här filen är det ENDA stället som svarar på frågan
«vad jobbar vi på». Den fattar inga beslut och förklarar ingenting: varje post
hänvisar till det avsnitt som äger den.*

**Tre regler, så att filen inte blir en nionde sanning:**

1. **Inga nya nummer.** En post hänvisas med det namn den redan har — `C2`,
   `G7`, `§12 rad 18`, `§10`. Ett påhittat id blir dubbeltydigt: `K1` krockade
   med konjugationsklass `K1`, och det var felet som gjorde den förra versionen
   av den här listan oläsbar.
2. **Ingen text dupliceras.** Skälen står i `KÄRNAN.md`, frågorna i
   `PROBLEM.md`, felen i `KÄRNAN.md` §12. Här står bara läget.
3. **Blir filen osann är den värre än ingen fil.** Stämmer den inte med
   `KÄRNAN.md` §9 är det §9 som gäller.

Stegen och deras ordning är `KÄRNAN.md` §9. Kärnan byggs först för paret
**svenska–engelska**; de fem andra språken tar samma steg när paret går från
början till slut.

---

## Det som blockerar

| | Vad | Äger frågan |
|---|---|---|
| **steg 5a** | **Entydighetsfiltret och märkningen finns inte i koden.** Det blockerar villkor 3 och 7 i 6.1, nivåernas filter i steg 4, hela steg 5, rättningens parning i steg 8, och `D5b` | 6.5 |
| **steg 2** | **Sammansättningens fart.** En dagsplan kostar 42,7 s, varmt minne 1,1 s. Det gör steg P3 ogörligt — de simulerade kurserna är 40–80 dagar styck | §12 sista raderna; mätt 2026-10-11 |

Resten går att arbeta på i vilken ordning som helst.

---

## Per steg

| Steg | Läge | Kvar |
|---|---|---|
| 0 · böjningsreglerna | sv + en klara | svensk komparation (`§10`); fem språk |
| 1 · renderarna redovisar | sv + en byggda och mätta (8.3) | godtagbara utfall; 23 tysta beslut i en; fem språk (`TYSTA_BESLUT.md`) |
| 1b · kartan | sv + en klara (6.7) | fem språk |
| 2 · sammansättningen | byggd sv + en | **farten** — se ovan |
| 3 · kortmodellen | korten för sv + en gjorda, besluten kopplade | delen av formen per kort (3.4) |
| 3b · datamodellen | byggd (`kurs/`) | — |
| 3c · FSRS-lagret | byggt, 131 rader | parameteroptimeringen (`E7`); mätningen av p (6.2) |
| 4 · nivåerna och grafen | version 1: första meningens kortmängd, utan krympning | språkpar och filter (kräver 5a); krympningen; **nivåfilen behöver byggas om** — kravet rättades 2026-11-11, men `kartor/nivaer_en.json` är från 6 oktober |
| **5a · entydighetsfiltret** | **finns inte** | allt |
| 5 · sökningen | inte byggd | värdet och budgeten (`C2`, avgjord i 6.3); villkor 6–8 i 6.1 |
| 5b · aspektkrav på koncept | — | parallellt (6.5) |
| 6 · dagspasset | två faser, glosan, ensamövningen, tidsmodellen byggda | villkor 3 och 7 (kräver 5a); täckningen inom en nivå (5.6) |
| 7 · urvalet | inte byggt | p och värdet per mening (6.2, 6.6); reservstegen (6.3) |
| 8 · rättningen | diffen, omrättningen, prerekvisitstegen byggda | parningen mot flera varianter (kräver 5a); **numerus som inget kort äger** (§12) |
| 9 · gränssnittet | inte byggt | allt (`H3`, `H4`, `H5`, `H6`) |
| 9b · gamla kärnan raderas | **12 178 rader**: `kort` 4 875, `generator` 3 012, `webb` 2 361, `cli` 1 930 | skarven är mätt — två importer, se 8.1 |

### Parallella spår

| | Läge |
|---|---|
| P1 · lektionerna | väntar på beslut (`§10`) |
| P2 · frekvenserna | väntar på beslut (`§10`). Behövs av 4.2 för att välja mellan flera minsta kravmängder — utan dem väljs den kortaste meningen, och kortast är inte lättast att lära |
| P3 · provsviten | **blockerad av farten i steg 2** |
| P4 · valideringen | löpande |
| P5 · täckningen | ersätter kandidatmängden och ordningen i 5.6 |
| P6 · semantiken | mekanismen finns (`docs/BITMASK.md` §11), tabellen halvfylld, och kravet släpps tyst i `urval.py:219` (§12) |

---

## Det som behöver tänkas igenom

Tre poster, och de är de enda som kräver ett vägval snarare än arbete. Ordningen
är din.

1. **Numerus ägs av inget kort** (§12; `D1` `~`; `D6` `?`). Antingen ett kort för
   numerusvalet, eller att attributionen får svara «ingen bär detta» i stället
   för att ta närmaste granne. Det andra svaret kräver att bokföringen tål ett
   möte som inte graderar något — alltså `D6`.
2. **Sammansättningens fart** (§12; mätt 2026-10-11). Härled beroendet per
   grammatikposition vid bygget. Att spela in vid körtid är prövat och räcker
   inte; provet måste gå minst tre mängder djupt.
3. **Semantiken** (`C3` `~`; P6). Nio verb ställer inget krav på sitt subjekt, och
   dag ett använder tre av dem. Det tysta släppet i `urval.py:219` är den
   egentliga bristen.

## Beslut som väntar på Julius

Sju, i `KÄRNAN.md` §10, och de blockerar nästan ingenting: lektionstexterna,
frekvensdatan, svensk komparation, de tre frågorna i `TYSTA_BESLUT.md` punkt 6,
komparationens typ, översättning åt båda hållen, japansk skrift.

## Rent arbete — riktningen är känd

Ur `KÄRNAN.md` §12 och `PARAMETER_AUDIT.md` §3. Sorterat efter vad det kostar i
fallna meningar:

- italienskans obestämda artikel i plural — **29 % av alla meningsspecar faller**
- tyska fraslexem med adjektiv först — 79 specar
- japanskans 36 `no`- och verbfrasadjektiv utan former; godan-verben
- 52 misstänkta svenska former (`ordbok/regelkontroll/sv.md`)
- 24 oinstrumenterade läsningar i sex språk; tio ord som inte är lexem
- stam/ändelse-gränsen dragen med stränganalys i stället för ur böjningsreglerna
- `neg_heller`, `kvant_båda`, `alla`/`några` + oräknebart, «all the books»
- slutna ordklasser saknar slot-filer — tyskan kritisk
- steg 0 och 1 för de fem återstående språken

---

## Lärdomen som gäller allt ovan

En rättelse är inte klar när koden är ändrad, utan när det som läser koden har
körts om. Kravfelet i §12 var rättat i `nivaer/__init__.py` och ändå levande i
programmet, eftersom `kartor/nivaer_en.json` var byggd fem veckor tidigare.
Varje post ovan som vilar på en fil i `kartor/` har samma hållhake.
