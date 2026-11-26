# Parameterrevision av inflektionsrummen — 2026-07-09

Svar på frågan: *"täcker slot-filerna alla böjningsparametrar som behövs för
att rendera det universella språket till alla 7 språk?"* Genomgång av samtliga
slot-filer mot respektive språks fullständiga morfologi, inom projektets
scope (grammatiskt korrekta standardmeningar; tal-/litterära register utanför).

## Slutsats

Rummen är **nästan kompletta**. Ett verkligt hål (sv perfekt particip), tre
medvetna scope-val som bör bekräftas, och två strukturfrågor som kan vänta
tills renderaren byggs.

*Tillägg 2026-08-01: ytterligare ett verkligt hål hittat i efterhand —
possessiverna (§1b). Revisionen granskade slot-filerna mot varje språks
morfologi men kontrollerade inte att lagringskonventionerna i CSV-filerna
faktiskt hade en ledig plats i cellrummet. Värt att upprepa som kontrollfråga
vid nästa revision.*

---

## 1. ~~Verkligt hål: svenska saknar perfekt particip~~  ✅ ÅTGÄRDAT 2026-07-09

**Löst:** tre perfpart-celler tillagda i `sv/verb.yaml` (perfpart_obest_utr_sg,
perfpart_obest_neu_sg, perfpart_a), modellerade som adjektivböjning och
skilda från supinum via satt genus. INSTRUKTIONER.md uppdaterad. Ursprunglig
analys nedan bevarad för kontext.



`sv/verb.yaml` har supinum (har **ätit**) men inte perfekt particip
(**äten/ätet/ätna**, **stängd/stängt/stängda**). De är olika former i
svenskan, och perfekt particip krävs för:

- analytisk passiv med bli/vara: "dörren **är stängd**", "boken **blev läst**"
- predikativ/attributiv användning: "en **stängd** dörr"

Utan den kan renderaren inte bilda svensk analytisk passiv (bara s-passiven).
**Förslag:** lägg 3 celler i `sv/verb.yaml` (tempus=Sup, genus=UtrMask/
NeuFem/Alla + numerus) analogt med franskans pp-celler, alternativt hantera
particip som härledda adjektiv. Kräver beslut innan sv-verbkörningen —
annars måste sv Verb köras om.

Presens particip (springande) saknas också, men det är derivation snarare än
böjning och kan vänta.

## 1b. Verkligt hål: possessiverna saknade plats i 5 av 7 språk  ✅ ÅTGÄRDAT 2026-08-01

*Missat i den ursprungliga revisionen — funnet vid genomgång 2026-08-01.*

Konventionen sa att possessiver skulle lagras som genitivformer av det
personliga pronomenet (`bas_kärna.csv`, kasus=Gen). Den bar inte:

- **Platsen var upptagen** — fr/es/it använder `kasus=Gen` för tonique/
  tónico/tonico (moi, mí, me). Possessiven hade krockat med dem.
- **Rummet var för litet** — de `mein` böjs som ein-ord i 16 former över
  kasus × genus × numerus. Pronomenfilens fyra kasusceller rymde dem inte.
- **Kongruensen kom från fel håll** — fr `son/sa` rättar sig efter det ÄGDA
  substantivet, en `his/her` efter ägaren. Mappningen
  `pronomen_3sg_fem → sa` var därför fel: `sa` betyder inte "hennes".

**Löst:** ny ordklass `Possessiv` med nio koncept (ett per ägare) och sju
slot-filer, 41 celler totalt (sv 3, en 2, fr 7, de 16, es 8, it 4, ja 1).
Ägarens drag ligger på Koncept-nivå, kongruens med det ägda på Former-axlarna.
Reflexiva sv `sin/sitt/sina` är ett andra lemma under 3:e-personskoncepten —
reflexivitet är en egenskap hos satsen, inte hos ordet. Cellerna m_sg/f_sg/a_pl
är borttagna ur sv/pronomen.yaml och poss_attr/poss_pred ur en/pronomen.yaml.

Konventionerna (`species` = attributiv/självständig, `kasus=Gen` = tonisk form
i fr/es/it) är dokumenterade i `_legend.yaml`.

**Kvarstår att lösa någon annanstans:** fr `son` ligger under tre koncept och
es `su` under fem, vilket ger identiska Former-rader och därmed flera
FSRS-item för samma sträng — frågan om vad som utgör *ett* övningsobjekt bör
avgöras för hela systemet. Multi-lemma saknar dessutom en diskriminator som
säger vilken variant som är vilken (gäller redan ja 私/僕 och es ser/estar).

## 2. Medvetna scope-val — bekräfta att de är OK

| Språk | Utelämnat | Bedömning |
|-------|-----------|-----------|
| fr | subjonctif imparfait (qu'il parlât) | Rätt val — död i modern standard |
| en | was/were-distinktionen (en cell för pret) | OK — hanteras som specialfall i renderern för "be" |
| ja | たら-konditionalis, kausativ (させる), kausativ-passiv | OK — analytiska/härledbara; ば-formen + renderare täcker behovet |
| ja | plain nonpast = jisho-cellen; artighetsregister är renderarens val (ます-cellen finns som hjälp) | OK men dokumentera i renderarens spec: register är INTE en Former-axel |
| de | Konjunktiv II analytisk (würde) | OK — syntetisk form lagras, würde är renderarens fallback |

## 3. Strukturfrågor — kan vänta till renderaren

**Slutna ordklasser saknar slot-filer:** Artikel, Demonstrativ,
Kvantifikator, Relativpronomen, Interrogativdeterminant, Räkneord (utom sv).
Tyskan är kritisk: der/die/das/dem/den…, dieser/jeder/welcher/alle böjs i
full kasus×genus×numerus-tabell som rendering INTE klarar sig utan.

*Rekommendation:* hårdkoda dessa i renderaren (små, frusna paradigm — 6–30
former per ord, ~15 ord) i stället för att LLM-generera till Former.
Alternativet (slot-filer + generering) ger enhetlighet men mer schema-arbete
för liten datamängd. Beslut behövs först när renderaren påbörjas.

**Adverb har ingen slot-fil:** sv/en har syntetisk adverbkomparation
(fort/fortare/fortast, fast/faster). Berör en handfull adverb; romanska
språk + ja är analytiska/oböjliga här. *Rekommendation:* lägg minimal
`adverb.yaml` (pos/komp/superl) för sv+en när behovet uppstår; övriga språk
behöver ingen.

## 4. Kontrollerat och komplett

- **fr/es/it verb:** alla levande syntetiska tempus finns (inkl. es/it
  konjunktiv imperfekt, es usted/ustedes-imperativ, it Lei-imperativ,
  passato remoto/passé simple/indefinido, pp-genusformer). ✓
- **de:** Konjunktiv I+II, Sie-imperativ, Partizip I+II, n-deklination
  täcks av substantivcellerna (kasusaxeln), adjektivens 144 celler ✓
- **en:** 5 verbformer + genitiv-celler ✓
- **ja:** 10 verbformer inkl. potentialis/volitiv/ば/passiv ✓;
  adjektivceller fungerar för både i- och na-typ via `ja_adjektiv_typ` ✓
- **sv:** substantiv (species×numerus×genitiv) ✓, adjektiv inkl.
  best/obest superlativ ✓, s-passiv ✓
- **Genus-axeln** täcker alla språks behov via UtrMask/NeuFem/Alla-
  kodningen (de neutrum = Alla — dokumenterat i legenden) ✓
- **Diates** täcker sv -s och ja 受身 ✓

## 5. Koppling till böjningsinstruktionerna

Per-språk-instruktioner för LLM-generering ligger i
`paradigm/{språk}/INSTRUKTIONER.md`. Pipelinen injicerar automatiskt
sektionen "Allmänt" + aktuell ordklass-sektion i varje prompt
(`_ladda_instruktioner` i `generering/pipeline.py`). Instruktionerna
dokumenterar även lagringskonventionerna som revisionen identifierade:

- de trennbare Verben: finita former lagras "rufe an" (renderaren flyttar
  partikeln); partizip ihopskrivet (angerufen)
- Analytisk komparation (en more/most, fr plus, es más, it più): cellerna
  lämnas tomma; bara syntetiska/suppletiva former lagras
- Reflexiver: böjs utan pronomen; renderaren sätter mig/te/sich/me/mi
- ja na-adjektiv: だった/ではない/に/なら-serien i i-adjektivens celler
