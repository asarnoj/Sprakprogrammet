# Renderarnas tysta beslut

*Inventering för steg 1 i byggordningen (KÄRNAN.md punkt 9), 2026-09-12. Ingen
kod är ändrad.*

Grundregel R3 säger att allt renderaren avgör är något användaren måste kunna,
och därför måste gå att grinda och pröva. Det kräver att beslutet **redovisas**:
att det går genom ett av de instrumenterade anropen i `Uppslag` — `form`,
`egenskap`, `rektion` eller `ordföljd` (KÄRNAN 8.3). Den här filen listar de
beslut som i dag inte gör det.

**Metod.** Alla sju renderare samt `romansk.py`, `spec.py` och `uppslag.py` är
genomlästa. Ett beslut räknas när renderaren väljer mellan alternativ som ger
olika text, och valet inte går genom något av de fyra anropen. Former som slås
upp med `form` räknas inte — de är redan kort. Det som räknas är valet *av* cell,
konstruktion eller plats.

## Sammanfattning

| | sv | en | de | fr | es | it | ja | summa |
|---|---|---|---|---|---|---|---|---|
| ordföljdsregler som redan redovisas | 4 | 3 | 6 | 3 | 4 | 3 | 4 | **27** |
| tysta beslut (punkt 3 och 4) | 29 | 23 | 35 | 36 | 34 | 37 | 12 | **206** |
| kort som läses förbi instrumenteringen (punkt 1) | 2 | 2 | 5 | 5 | 5 | 5 | 2 | **26** |
| ord utan lexem (punkt 2) | 0 | 0 | 0 | 2 | 2 | 0 | 6 | **10** |
| *specens uppskattning av tysta beslut* | 11 | 9 | 10 | 22 | 24 | 23 | 6 | **105** |

Uppskattningen i KÄRNAN 4.1 var 105 tysta beslut. Inventeringen hittar **206** tysta beslut räknat per språk, plus **26** kort som finns men inte går att mäta och **10** ord utan lexem. Ett beslut som gäller flera språk räknas en gång per språk, eftersom varje språk får sitt eget kort.

---

## 1 · Kort som finns men inte går att mäta

**Det viktigaste fyndet.** Specen räknar med att korttyperna `egenskap` och
`rektion` redan fungerar. För flera av dem gör de inte det: renderaren läser
värdet direkt ur databasen, förbi instrumenteringen, och kortet kan då aldrig
prövas eller få skulden för ett fel.

`uppslag.egenskap` säger det själv: *«Att läsa `lexem["genus"]` direkt förbi den
här går fortfarande — och gör kortet osynligt igen.»* Genus går rätt väg i alla
språk. Följande gör det inte:

| id | beslut | var det läses | språk | blir |
|---|---|---|---|---|
| A1 | hjälpverb: haben/sein, avoir/être, avere/essere | `verb["hjälpverb"]` i `de.verbdelar` och `romansk.verbdelar` | de fr it | egenskap |
| A2 | adjektivets plats före eller efter substantivet | `adjektiv["prenominal"]` i `romansk.nominalfras` | fr es it | egenskap |
| A3 | japanskt adjektiv: い, な, の eller verbfras | `adjektiv["ja_adjektiv_typ"]` i `ja.nominalfras` och `ja.predikativ` | ja | egenskap |
| A4 | konjunktiv efter subjunktion eller verb | `romansk.modusrektion` läser `MönsterKrav` direkt | fr es it | rektion |
| A5 | prepositionens kasus: mit + dativ, für + ackusativ | `de.prepositionskasus` läser `MönsterKrav` direkt | de | rektion |
| A6 | infinitivmarkör: att, to, zu, à, di — eller ingen | `Uppslag.infinitivmarkör` är inte instrumenterad | sv en de fr es it | rektion |
| A7 | reflexivpronomen i dativ: sich vorstellen | hårdkodad `REFLEXIV_DATIV` i `de.py` | de | rektion |
| A8 | reflexivt verb: skynda sig, sich beeilen, se réveiller | läses ur lemmat (`" sig"`, `"sich "`, `"se "`, `-se`, `-si`) | sv de fr es it | egenskap (ny) |
| A9 | ser eller estar | `es.kopulavariant` läser konceptnyckelns prefix `adj_es_` | es | egenskap (ny) |
| A10 | gerundium efter stop: stop reading | hårdkodat `asp_sluta` i `en.satsled` | en | rektion |
| A11 | どこ tar で | hårdkodad `FRÅGEADVERBPARTIKEL` i `ja.py` | ja | rektion |

A8 och A9 är nya egenskaper enligt kriteriet i KÄRNAN 3.5: värdet hör till ett
ord men syns på ett annat — reflexivpronomenet, kopulan.

## 2 · Ord som inte är lexem

Ord som renderaren skriver ut men som inte finns i databasen. De har inget
`ord`-kort, så en mening kan bli fel på dem utan att något kort bär skulden —
precis det täckningskravet i KÄRNAN 3.8 förbjuder.

| id | ord | vad | språk | var |
|---|---|---|---|---|
| F1 | ne | negationens förled | fr | `FranskRenderare.NEKANDE_FÖRLED` |
| F2 | est-ce que | frågeinledning | fr | `FranskRenderare.FRÅGEINLEDNING` |
| F3 | は を に が | partiklar för tema, objekt, dativ, subjekt | ja | konstanter i `ja.py` |
| F4 | か | frågepartikel | ja | `ja.rendera` |
| F5 | です ました ません でした ましょう なかった | artighet, tempus och negation, komponerade | ja | `ja.verbform` m.fl. |
| F6 | な の | attributiv markör | ja | `ja.nominalfras` |
| F7 | で | efter どこ | ja | `FRÅGEADVERBPARTIKEL` |
| F8 | se | le/les framför lo/la | es | `SpanskRenderare.ordna_klitika` |
| F9 | ¿ ¡ | inledande skiljetecken | es | `FRÅGETECKEN_FÖRE`, `UTROPSTECKEN_FÖRE` |
| F10 | 、 | komma efter adverbial | ja | `ja.satsled` |

## 3 · Tysta beslut i flera språk

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| G1 | pronomenets form efter roll | jag/mig, I/me, je/me/moi | sv en fr es it | regel |
| G2 | artikelbruk efter bestämdhet | en bok, a book, ein Buch, un livre | sv en de fr es it | regel |
| G3 | obestämd plural utan artikel | böcker, books, Bücher | sv en de | regel |
| G4 | naken fras, generisk eller partitiv | vatten; les livres; de l'eau; bebo agua | sv en de fr es it | regel |
| G5 | possessiv tar artikelns plats | sin bror, her brother, sein Bruder, son frère | sv en de fr es | regel |
| G6 | genitivattribut: form och plats | flickans bok, das Buch des Mädchens, le livre de la fille, 女の子の本 | sv en de fr es it ja | regel |
| G7 | frågedeterminant tar artikelns plats | vilken bok, which book, welches Buch, quel livre | sv en de fr es it | regel |
| G8 | adjektivkongruens | stor/stort/stora, grand/grande/grands | sv de fr es it | regel |
| G9 | predikativt adjektiv: form | barnet är glatt, sie ist glücklich, elle est heureuse | sv de fr es it | regel |
| G10 | predikativt substantiv: artikel eller inte | hon är läkare / she is a doctor | sv en de fr es it | regel |
| G11 | syntetisk eller perifrastisk komparation, per ord | större / mer intressant, bigger / more interesting | sv en fr es it | egenskap eller undantag |
| G12 | attributiv superlativ kräver bestämd fras | den största boken, the biggest book | sv en de fr es it | regel |
| G13 | verbets personkongruens | she reads, er gibt, il donne | en de fr es it | regel |
| G14 | frågeord som subjekt kongruerar som 3 sg | who follows, wer ändert | en de fr es it | regel |
| G15 | artigt tilltal kongruerar annorlunda än det betyder | Sie fliegen, usted vuela, vous volez | de fr es it | regel |
| G16 | perfekt: hjälpverb + supinum eller particip | har läst, has read, hat gelesen, a lu | sv en de fr es it | regel |
| G17 | futurum: hjälpverb + infinitiv | ska läsa, will read, wird lesen | sv en de | regel |
| G18 | passiv som konstruktion | blev läst, is read, wird gelesen, est lu | sv en de fr es it | regel |
| G19 | reflexivpronomenet kongruerar med subjektet | vi skyndar oss, wir beeilen uns, nous nous réveillons | sv de fr es it | regel |
| G20 | frågepronomen efter mänsklighet | vem/vad, who/what, wer/was, 誰/何 | sv en de fr es it ja | regel |
| G21 | imperativ: form per tilltal, subjektet utelämnas | läs!, read!, Lesen Sie!, lisez! | sv en de fr es it | regel |
| G22 | negationens form och plats | inte, not, nicht, ne … pas, no, non | sv en de fr es it | regel |

## 4 · Tysta beslut per språk

### Svenska

*Redovisat 2026-09-13 i `rendering/sv.py` (KÄRNAN 8.3).* G-besluten och S1–S7 är val
(`regel`), S8–S10 ordningsregler (`ordning`), A6 är rektion och A8 egenskap. Texten
ändrades inte utom i tre rättade fall; se KÄRNAN 8.3.

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| S1 | dubbel bestämdhet med attribut | den röda boken | sv | regel |
| S2 | possessiv och genitiv ger svag adjektivform | sin röda bok, flickans röda bok | sv | regel |
| S3 | komparativ är oböjlig | en större bok, de större böckerna | sv | regel |
| S4 | predikativ superlativ i obestämd form | boken är störst | sv | regel |
| S5 | bli-passivens particip kongruerar | huset blev målat | sv | regel |
| S6 | artigt ni tar er | ni skyndar er | sv | regel |
| S7 | deponens: s-formen är aktiv | hon minns | sv | regel |
| S8 | objektsskifte bara i enkla tempus | jag skyndar mig inte / vi har inte oroat oss | sv | ordföljd |
| S9 | negationen efter det finita verbet i huvudsats | hon ska inte ge | sv | ordföljd |
| S10 | indirekt objekt före direkt | gav sin bror en bok | sv | ordföljd |

### Engelska

*Redovisat 2026-09-14 i `rendering/en.py` (KÄRNAN 8.3).* G-besluten, E1, E2, E4 och E5
är val (`regel`), E3 och dativväxlingen ordningsregler (`ordning`), A6 och A10 rektion.
Artikelns ljud och om ett verb tar do läses som ordets egna drag, inte som egenskaper.
Passiven är inget val, eftersom engelskan bara har en.

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| E1 | a eller an | an apple | en | regel |
| E2 | do-omskrivning i negation (loggas bara i frågor) | she does not read | en | regel |
| E3 | not efter hjälpverbet; kopulan negeras direkt | she is not happy | en | ordföljd |
| E4 | nekad imperativ utan kongruens | don't read! | en | regel |
| E5 | who eller whom | whom did you see | en | regel |

### Tyska

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| D1 | adjektivdeklination efter determinerare | der rote / ein roter / roter Wein | de | regel |
| D2 | kein i stället för nicht ein | sie gab kein Buch | de | regel |
| D3 | nicht sist i Mittelfeld | sie gab das Buch nicht | de | ordföljd |
| D4 | reflexivet först i Mittelfeld | warum beeilst du dich | de | ordföljd |
| D5 | Sie och wir sägs ut i imperativ | Lesen Sie! | de | regel |
| D6 | passiv i perfekt tar worden | ist gelesen worden | de | regel |
| D7 | ersatzinfinitiv | er hat lesen können | de | regel |
| D8 | futur II | sie wird gekauft haben | de | regel |
| D9 | dubbelinfinitiv: det finita verbet före klustret i bisats | weil er hat hören können | de | ordföljd |
| D10 | verbalkomplexet: det styrda före det styrande | wird hören sollen | de | ordföljd |
| D11 | zu-infinitivens plats | versucht das Buch zu lesen / dass wir zu spielen versuchen | de | ordföljd |
| D12 | partikelverb: partikeln sist, ihop i bisats | ruft den Bruder an / dass sie anruft | de | ordföljd |
| D13 | predikativt adjektiv oböjt; am -sten i superlativ | sie ist am größten | de | regel |
| D14 | als eller wenn | als er kam / wenn er kommt | de | regel |
| D15 | adverbialets plats i Mittelfeld | gab ihm gestern das Buch | de | ordföljd |

### Franska, spanska, italienska

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| R1 | aspekt → tempus: imparfait mot passé composé | je travaillais / j'ai travaillé | fr es it | regel |
| R2 | perfektiv dåtid sammansatt eller syntetisk | a donné / dio | fr es it | regel |
| R3 | hjälpverbets tempus bär pluskvamperfekt, futurum exaktum och konjunktiv | avait lu, aura lu, ait lu | fr es it | regel |
| R4 | participkongruens efter être och efter föregående objekt | elle est venue, il les a donnés | fr it | regel |
| R5 | possessiven kongruerar med det ägda | son livre, sa maison | fr es it | regel |
| R6 | komparerat adjektiv efterställt | un libro mayor | es it | ordföljd |
| R7 | klitikaordning | me le donne / le lui donne | fr es it | ordföljd |
| R8 | reflexivet först i klitikakedjan | je me le rappelle | fr es it | ordföljd |
| R9 | reflexiv infinitiv: klitikat fäst eller före | quiero despertarme / je veux me réveiller | fr es it | regel |
| R10 | nekad imperativ byter form | ¡no leas!, non leggere! | es it | regel |
| R11 | konjunktivens tidsföljd | que venga / que viniera | es it | regel |
| R12 | prepositionen följer frågeordet | à qui a-t-elle donné | fr es it | regel |
| R13 | elision | l'enfant, dell'acqua | fr it | regel |
| R14 | sammandragning | au, del, nella | fr es it | regel |

### Franska

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| FR1 | un/une/des blir de under negation | elle ne trouve pas de chat | fr | regel |
| FR2 | dubbel superlativartikel | le livre le plus grand | fr | regel |
| FR3 | negationens efterled efter det finita verbet | elle n'a pas donné | fr | ordföljd |
| FR4 | est-ce que i ja/nej-fråga (loggas bara i wh-fråga) | Est-ce qu'elle lit ? | fr | ordföljd |
| FR5 | elision före sammandragning | à l'enfant, inte au enfant | fr | regel |

### Spanska

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| ES1 | el framför betonat a | el agua | es | regel |
| ES2 | tener eller haber | tengo un libro / he leído | es | regel |

### Italienska

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| IT1 | lo/gli framför z, gn, ps, s + konsonant och vokal | lo studente, gli amici | it | regel |
| IT2 | bestämd artikel före possessiv, utom ensam släkting i singular | il mio libro, mia madre, il loro padre | it | regel |
| IT3 | avere eller essere när hjälpverbet är «båda» | ha corso i 100 m / è corso via | it | regel |
| IT4 | sammandragning före elision | dell'acqua | it | regel |

### Japanska

| id | beslut | exempel | språk | blir |
|---|---|---|---|---|
| JA1 | は eller が | 彼は来た / 彼が来たと | ja | regel |
| JA2 | artig form på huvudverbet, enkel i bisats | 読みます / 読むと | ja | regel |
| JA3 | な efter na-adjektiv, の efter no-adjektiv | 静かな部屋 | ja | regel |
| JA4 | i-adjektivet bär tempus i predikativ; substantivet tar でした | 嬉しかったです / 医者でした | ja | regel |
| JA5 | なる med く-form | 嬉しくなりました | ja | regel |
| JA6 | passiv komponerad ur ukemi | 読まれます | ja | regel |
| JA7 | uppmaning: てください, ないでください, ましょう | 読んでください | ja | regel |
| JA8 | possessiven utelämnas vid koreferens | 女の子は兄弟に本をあげました | ja | regel |
| JA9 | komparation med もっと/一番; より före det jämförda | 本より大きい | ja | regel |
| JA10 | ということ nominaliserar bisatsen, som tar を | 来るということを | ja | regel |

---

## 5 · Förslag till hur besluten redovisas

**1. Byt namn på `ordföljd` till `regel`.** Anropet har redan rätt form — tomt,
bara namnet — men namnet är för smalt: de flesta tysta besluten gäller kongruens,
konstruktion och ljud, inte ordföljd. Samma anrop räcker för alla.

**2. Laga förbigångarna i punkt 1 först.** Det är mekaniskt och viktigast, för
utan det går tre av de fyra egenskaperna i KÄRNAN 3.5 — hjälpverb, prenominal och
japansk adjektivtyp — och flera sorters rektion inte att mäta.

**3. Ge orden i punkt 2 lexem.** Annars bryter varje mening som innehåller dem
mot täckningskravet.

**4. Logga regeln där cellen väljs.** När renderaren väljer cell efter kongruens
loggas i dag bara formen. Skriver användaren `il parles` får formkortet för
`parles` skulden, fast det som föll är kongruensregeln. Ett `regel`-anrop intill
uppslaget räcker.

**5. Mät sedan hur många regler en mening använder.** Det är steg 1:s egentliga
prov (KÄRNAN 9): håller attributionen när alla beslut redovisas?

## 6 · Frågor till Julius

1. **Skiljetecken.** `¿`, `¡` och japanskans `、` är beslut enligt R3, men ett
   kort för dem är kanske för smått för att vara ett läromoment. Kort eller inte?
2. **Språkets fasta val.** Att franskan uttrycker perfektiv dåtid med passé
   composé (R2) varierar inte mellan meningar. Är det ett kort, eller en del av
   lektionen när nivån öppnas?
3. **Samma skillnad som i svenskan.** `vem/vad` motsvarar `wer/was` ett till ett
   (G20). Är det ett läromoment för en svensk, eller följer det av betydelsen?

## 7 · Där renderaren vägrar

Inga beslut, men luckor som gör att meningar inte kan byggas:

- **it** två klitika som smälter ihop (`glielo`, `me lo`)
- **fr es it** jakande imperativ med klitika (`donne-le-moi`, `¡dámelo!`)
- **ja** infinitivkomplement och modalsuffix (`読みたい`)
- **de** fraslexem med framförställt adjektiv utanför bestämd fras (`ein älterer Bruder`)
- **ja** `なる` med な- och の-adjektiv
- **en** `a`/`an` efter ljud och inte stavning (`an hour`)
