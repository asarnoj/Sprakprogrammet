# Lexem-granskning 2026-07-09

Fullständig genomgång av samtliga 736 koncept / 5 149 lexem i `sprak.db`,
mot KONVENTIONER.md (lemmaformat §2, förenklingsfilosofi §5, kända undantag §8).
Scope-avgränsningen respekterad: inget flaggas för stilnivå/talspråk — endast
faktiska fel, formatbrott och strukturproblem.

**Detta är observationer och förslag, inte beslut** (per KONVENTIONER §9).
Varje punkt har en checkruta så beslut kan bockas av.

> **Status 2026-07-09 (kväll):** Del A samt de entydiga felen i del B är
> genomförda efter godkännande — i CSV:erna (source of truth), följt av
> databasombygge. C4 löst via `Lexem.ja_adjektiv_typ` +
> `ordbok/migrationer/ja_adjektiv_typ.sql`; C5 löst via böjbart-huvud-
> konventionen i KONVENTIONER.md §6. **Obockade rutor är öppna beslut**
> (gränsfall + designfrågorna C1–C3, C6–C7).

Helhetsintryck: **datan håller hög kvalitet.** Koncepthubben är konsekvent,
polysemi-hanteringen (fahren=köra/åka, sentir=känna/lukta, 聞く=fråga/höra/lyssna)
är genomtänkt. Fynden nedan är ~60 punkter av 5 149 lexem ≈ 1 %.

---

## A. Strukturella dubbletter — påverkar databasen (hög prioritet)

`adv2_*`-serien (från grundord.csv) dubblerar `adv_*`-serien (från bas_kärna.csv):

- [x] **Exakta dubbletter** (identiska lemman i alla 7 språk — slå ihop):
  `adv2_alltid`=`adv_alltid`, `adv2_ofta`=`adv_ofta`, `adv2_också`=`adv_också`,
  `adv2_redan`=`adv_redan`, `adv2_snart`=`adv_snart`,
  `adv2_aldrig`=`neg_aldrig` (obs: olika ordklass — Adverb vs Negationsadverb;
  behåll `neg_aldrig` eftersom ja 決して kräver negationskoppling)
- [x] **Nära-dubbletter** (samma lemman i 5–6 språk):
  `adv2_bara`/`adv_bara` (en: just/only), `adv2_ibland`/`adv_ibland` (ja: ときどき/時々),
  `adv2_ännu`/`adv_fortfarande` (sv skiljer, resten identiska),
  `adv2_väldigt`/`adv_mycket` (sv skiljer, resten identiska)
- [x] **`verb_finnas` = `ext_finnas`** — exakt dubblett i alla 7 språk. Slå ihop.
- [x] **`fam_kollega` = `yrke_kollega`** — exakt dubblett i alla 7 språk. Slå ihop.

---

## B. Fel/formatbrott per språk

### Svenska
- [x] `kog_lära` — lemma **"lära"** men konceptet är *learn* (alla andra språk:
  learn/apprendre/lernen/aprender/imparare/学ぶ). "lära" = undervisa.
  → **"lära sig"**
- [x] `interj_sorry` — **"ursäkt"** är ett substantiv, inte en interjektion.
  → **"förlåt"** (alt. "ursäkta")
- [ ] `interj_please` — "var god" fungerar men är skriftspråksmall.
  → **"snälla"** (eller behåll — gränsfall)

### Franska
- [x] `adj_es_frisk` — **"en bonne santé"** är en fras, inte ett adjektiv;
  kan inte böjas i fr-adjektivparadigmet (12 celler). → **"sain"**
- [x] `adj_es_arg` — **"en colère"** samma problem. → **"fâché"**
- [x] `abs_nyhet` — **"nouvelles"** är pluralform; lemmaformat kräver singular.
  → **"nouvelle"**
- [x] `frågepronomen_sak` — **"quoi"** används efter preposition/finalt;
  objektsfrågor bildas med **"que"** (qu'est-ce que). → "que"
- [ ] `demonstrativ_fjärran` — **"cela"** är ett *pronomen*; `demonstrativ_nara`
  har **"ce"** som är en *determinant*. Inkonsekvent par. Bestäm om Demonstrativ
  ska vara determinant (ce …-ci / ce …-là) eller pronomen (ceci/cela) — i båda
  fallen behöver ett av lexemen bytas.
- [x] `adv2_tillbaka` — **"en retour"** = "i gengäld", inte "tillbaka (riktning)".
  → **"de retour"** alt. markera att fr uttrycker detta i verbet (revenir).

### Tyska
- [x] `interj_goodbye` — **"auf wiedersehen"** → **"auf Wiedersehen"** (versal).
- [x] `interj_sorry` — **"entschuldigung"** → **"Entschuldigung"** (versal).
- [ ] `adj_es_rädd` — **"ängstlich"** = ängslig (karaktärsdrag); *scared* (tillstånd)
  → **"verängstigt"** (alt. acceptera som förenkling — dokumentera i så fall)
- [x] `adj_ev_elak` — **"böse"** = arg/ond; *mean* → **"gemein"**
- [x] `rör_stanna` — **"stoppen"** är främst transitivt (stoppa ngt); konceptet är
  intransitivt (s'arrêter/parar/fermarsi/止まる). → **"anhalten"**
- [x] `fam_bekant` — **"Bekannte"** är f/svag form; m sg-konventionen (jfr
  `pers_vuxen` "Erwachsener") → **"Bekannter"**
- [ ] `mat_kyckling` — "Hühnchen" fungerar; **"Hähnchen"** är standardordet för
  maträtten. (mindre)

### Spanska
- [x] `frågadverb_riktning` — es-lexem **saknas** men **"adónde"** finns och är
  standard. Lägg till. (en/fr/it saknas med rätta — where/où/dove täcker.)
- [x] `adv2_alltså` — **"entonces"** = "då" (dubblerar `adv_då`); *alltså/därför*
  → **"por lo tanto"** (alt. "o sea", "así que")
- [ ] `soc_träffa` — **"encontrar"** = hitta (dubblerar `fys_hitta`); *träffa ngn*
  = **"encontrarse (con)"** eller **"quedar con"**. Som polysemi-förenkling
  genererar bar "encontrar" fel mening ("encuentro a mi amigo" = stöter på).
  Gränsfall — bedöm.

### Italienska
- [x] `adj_es_skamsen` — **"vergognoso"** betyder *skamlig* (om saker), inte
  *skamsen* (om personer). → **"imbarazzato"** (alt. acceptera att det uttrycks
  med verbet *vergognarsi* och byt strategi)
- [x] `kläd_kläder` — **"vestito"** = klänning/kostym och dubblerar
  `kläd_klänning` (också "vestito"). Kläder = **"vestiti"** (pl) eller
  **"abbigliamento"**. → "vestiti" + plural-modifierare
- [x] `mat_frukt` — **"frutto"** = enskild frukt (även bildligt); kollektivet/
  matvaran = **"frutta"**. → "frutta"
- [x] `frågepronomen_sak` — **"che"** ensamt som frågepronomen är
  litterärt/regionalt; standard är **"cosa"** / "che cosa". → "cosa"
- [ ] `modal_brukar` — **"solere"** är defekt och arkaiskt i modern italienska.
  → **"essere solito"** eller lexem-modifierare + acceptera defekt paradigm
- [ ] `modal_ska` — **"stare per"** = "vara på väg att (strax)", inte framtid/
  intention. Italienska saknar futurum-hjälpverb (syntetiskt futurum: -rò).
  → överväg NULL här + låt renderern använda futurum-formen (som analytiska
  tempus i BITMASK.md), i stället för ett missvisande lemma.

### Japanska
- [x] `eko_v_äga` / `fys_bära` / `fys_hålla` — **alla tre = 持つ**. Trippel-kollaps
  som ger fel meningar (bära väskan ≠ hålla väskan).
  → äga = **所有する** (el. 持っている), bära = **運ぶ**, hålla = **持つ**
- [x] `verb_ha` — **ある** = finnas (dubblerar `ext_finnas` ある) och gäller bara
  inanimata subjekt. Ägande = **持っている**. → byt
- [ ] `gen_sakna` — **恋しい är ett i-adjektiv, inte ett verb.** Kan inte böjas i
  ja/verb-paradigmet. Ingen perfekt verbmotsvarighet finns; alternativ:
  懐かしむ (nostalgiskt sakna) eller acceptera adjektivstrategi + ordklassbyte
  för ja-lexemet. Kräver designbeslut.
- [x] `kog_minnas` — **覚える** = memorera/lära in; *minnas/dra sig till minnes* =
  **思い出す**. → 思い出す
- [ ] `gen_förlora` — **負ける** = förlora (match/strid). *Tappa bort (sak)* =
  なくす. Bestäm konceptets kärnbetydelse; om båda behövs → två koncept.
- [x] `komp_som` — **ほど** används bara i *negerade* jämförelser (AはBほど…ない).
  Jakande likhet = **と同じくらい**. Med ほど i jakande mening blir det fel.
  → と同じくらい, alt. mönsterkrav som binder ほど till negation.
- [x] `frågadverb_sätt` — **"どう やって"** innehåller mellanslag → **"どうやって"**.
  (Även dubblett どう/どうやって inom konceptet — avsiktlig?)
- [x] `rör_snubbla` — dubblett つまずく/よろめく; よろめく = ragla/vackla.
  → behåll **つまずく**, ta bort よろめく
- [ ] `verb_vara` — **です** är kopula; för befintlighet (vara någonstans) krävs
  いる/ある. Hänger ihop med animat/inanimat-frågan (se C4).
- [ ] `kog_veta` — 知る är punktuellt ("få veta"); tillståndet "vet" = 知っている.
  Kräver te-iru-hantering i renderern (gäller även 持っている ovan). Designnot.

---

## C. Systematiska mönster — kräver designbeslut före böjningskörningen

### C1. Positionsverben blandar tillstånd och handling
`pos_ligga`/`pos_sitta`/`pos_stå`: sv/de-lexemen är *tillstånd* (ligga/liegen,
sitta/sitzen, stå/stehen) men fr/es/it/ja är *inchoativa handlingar*
(s'allonger/tumbarse/sdraiarsi/横になる = lägga sig; s'asseoir/sentarse/sedersi
= sätta sig; 立つ = ställa sig). Samma mening genererad över språken får olika
betydelse. **Förslag:** bestäm att koncepten är tillstånd och byt de romanska/
japanska till être allongé/assis/debout-strategi (estar tumbado/sentado/de pie,
essere sdraiato/seduto/in piedi, 横になっている/座っている/立っている) — eller
splitta i två konceptserier (tillstånd + inchoativ).

### C2. `rör_lämna` blandar transitivt och intransitivt
sv lämna / de verlassen / en leave = transitiva (lämna ngt); fr partir /
es salir / it partire / ja 出る = intransitiva (ge sig av). "Jag lämnar huset"
→ "*je pars la maison". **Förslag:** transitiv linje: fr **quitter**,
es **dejar**, it **lasciare** — alt. splitta i lämna(trans) + åka_iväg(intrans).

### C3. `käns_gilla`: inverterad valens (gustar/piacere)
es "gustar" och it "piacere" har dativ-upplevare ("me gusta X" — X är subjekt).
Genereras de som vanliga transitiva verb blir varje mening fel. Detta är
exakt vad `MönsterKrav` ska fånga — men kräver att mönstret finns innan
meningsgenerering. `käns_ogilla` ("no gustar"/"non piacere"/"ne pas aimer")
är dessutom negerade flerordslemman — bör sannolikt vara samma lexem som
gilla + negationssystemet. **Förslag:** markera inverterad valens som
lexem-egenskap redan nu; ta bort negationslemman.

### C4. Japanska adjektiv: fyra olika typer i samma ordklass
ja-adjektivlexemen blandar: **i-adjektiv** (安い), **na-adjektiv** (健康, 普通),
**no-substantiv** (灰色, 緑, 紫, ピンク, オレンジ) och **verbformer/fraser**
(怒った, 驚いた, 疲れた, お腹が空いた, 恋している, ストレスを感じた, 死んでいる,
生きている, 閉まっている, 開いている, 準備できた, わかった). Bara typ 1–2 kan böjas
i ja/adjektiv-paradigmet; typ 3 tar の, typ 4 böjs som verb eller inte alls.
**Förslag:** typkolumn/lexem-modifierare för ja-adjektiv (i/na/no/verbfras)
innan böjningskörningen — annars producerar pipelinen skräp för ~25 lexem.
Samma mekanism löser ある/いる-valet (animat/inanimat) för finnas/vara via
semantik-taggen Animat.

### C5. Flerordslemman i böjbara ordklasser
Verb: sv "laga mat", "lita på", "hålla med", "gifta sig", "skynda sig",
"oroa sig" m.fl.; fr "faire confiance", "vouloir dire", "être d'accord";
es "pedir prestado", "querer decir", "estar de acuerdo", "ir a"; it "prendere
in prestito", "voler dire", "essere d'accordo". Pipelinen måste veta **vilket
ord som böjs** (laga, faire, pedir, prendere …). **Förslag:** konvention
"första ordet böjs" + undantagskolumn, alternativt markera böjbart huvud
explicit i lexemet. Måste lösas innan `ordbok generera` körs på verb.

### C6. Plurale tantum / defekt numerus otaggat
pengar/soldi, glasögon, kläder, trousers/calzoncillos/mutande (medan sv har
"byxa" sg) — behöver numerus-defekt-modifierare (redan planerat i SCHEMA.md §6,
men taggningen är inte gjord). Även oräknebara: mat, vatten, Obst …
(`räknebar`-kolumnen är helt otaggad).

### C7. Koncept-taggarna är 0 % ifyllda
`Lexem.genus` (kritiskt för fr/de/es/it/sv-rendering), `Lexem.prenominal`,
`Koncept.valens`, `Koncept.semantik`, `Koncept.räknebar`, `Koncept.person`,
`Koncept.numerus` — samtliga NULL i hela databasen. Allt är LLM-taggbart i
ett pass per kolumn med manuell stickprovskontroll.

---

## D. Mindre observationer — ingen åtgärd nödvändig

- KONVENTIONER §8 säger es "en" täcker prep_i+på+vid, men datan har
  prep_på=**sobre**. Datan är rimlig — uppdatera doc-tabellen.
- `plats_väg`: fr "rue"/es "calle" = gata, sv "väg"/en "road" = väg. Lätt
  semantisk drift — samordna vid tillfälle (fr "route", es "carretera")
  eller acceptera.
- `tid_middag` (noon): sv "middag" betyder numera oftast måltiden. Övriga
  språk = klockan tolv. Överväg "mitt på dagen" eller acceptera.
- `skol_lärare`/`skol_professor` båda fr "professeur" — korrekt polysemi;
  "enseignant" finns om distinktion önskas.
- `verb_bli` es "llegar a ser" — rimlig förenkling (es saknar ett enhetligt
  "bli"); notera bara att hacerse/ponerse/volverse-nyanserna är utanför scope.
- Polysemier värda att föra in i §8-tabellen (avsiktliga, korrekta):
  高い (dyr+hög), 面白い (intressant+rolig), 普通 (normal+vanlig),
  chaud (het+varm), malo/cattivo (dålig+elak), fahren (köra+åka),
  聞く (fråga+höra+lyssna), 話す (berätta+prata), sentir(e) (känna+lukta+it:höra),
  trouver/finden (hitta+tycka), encontrar (hitta+träffa), tarde (eftermiddag+kväll),
  足 (ben+fot), baño/bagno (badrum+toalett), maison/casa (hus+hem),
  professeur (lärare+professor), Unterhose (kalsong+trosor).

---

## Rekommenderad åtgärdsordning

1. **A** — slå ihop dubbletterna (minskar till ~726 koncept; görs säkrast
   via SQL-migrering som flyttar ev. referenser).
2. **B** — lemma-korrigeringar (ren UPDATE per rad efter beslut).
3. **C4 + C5** — ja-adjektivtyp och böjbart-huvud-konvention, eftersom
   böjningspipelinen är blockerad av dem.
4. **C1–C3** — semantiska designbeslut (kan göras parallellt med 3).
5. **C6–C7** — taggningspass (genus, räknebar, valens, semantik, defekter)
   via LLM + stickprov. Genus först — den behövs för all rendering.
