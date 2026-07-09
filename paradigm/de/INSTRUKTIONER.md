# Böjningsinstruktioner — tyska (de)

> Injiceras i LLM-prompten av `ordbok generera`: sektionen **Allmänt** plus
> sektionen för aktuell ordklass.

## Allmänt

- Tysk standardortografi efter reformen (dass, ß enligt regel: ß efter lång
  vokal/diftong — groß, heißen; ss efter kort — muss, essen).
- Substantiv och substantiverade former ALLTID med versal.
- Flerordslemman: böj det första ordet som inte är reflexivmarkör (sich).
  "sich erinnern" → böj erinnern (erinnere, erinnerst …) utan pronomen;
  renderaren sätter mich/dich/sich.
- **Partikelverb (trennbare Verben)** — anrufen, aufhören, anfangen,
  einladen, aufwachen, weitermachen, zuhören, stattfinden: i finita former
  skrivs partikeln EFTER verbet med mellanslag: "rufe an", "hörst auf",
  "fängt an". I infinitiv, participen och konjunktiv skrivs de ihop:
  anrufen, angerufen, anzurufen (lagra "angerufen" som partizip 2 — ge-
  hamnar mellan partikel och stam). Renderaren flyttar partikeln till
  satsslut.
- Lämna "" endast när formen inte existerar.

## Verb

Axlar: tempus × person × numerus. Tempus: Präsens, Präteritum, Konjunktiv I
(Vol), Konjunktiv II (Kond), Imperativ (2sg/1pl/2pl/3sg-Sie), Infinitiv,
Partizip I (Te), Partizip II (Sup).

- **Svaga verb:** kaufe/kaufst/kauft…, kaufte…, gekauft. Stam på -t/-d får
  e-inskott: arbeitest, arbeitet, arbeitete.
- **Starka verb:** vokalväxling i pres 2/3sg (fahre→fährst/fährt,
  lese→liest, nehme→nimmst/nimmt, gebe→gibst/gibt), ablaut i präteritum
  (fuhr, las, nahm, gab) och partizip (gefahren, gelesen, genommen, gegeben).
- **Konjunktiv I** (indirekt tal): stammen + e-ändelser: er komme, er habe,
  er sei (sein är helt oregelbundet: sei/seist/sei/seien/seiet/seien).
- **Konjunktiv II:** präteritumstam + omljud där möjligt: käme, gäbe, führe,
  wäre, hätte, könnte, müsste, würde. Svaga verb = präteritum (kaufte) —
  fyll i formen ändå (renderaren väljer würde-omskrivning).
- **Imperativ:** komm!, lies!, nimm! (starka med e→i-växling behåller den);
  arbeite! (e-inskott); Gehen wir! (1pl), kommt! (2pl), Kommen Sie! (3sg-Sie).
- **Partizip II:** ge- + stam + -t/-en (gekauft, gefahren); INGET ge- för
  verb på -ieren (studiert, repariert) och oavskiljbara prefix (be-, er-,
  ver-, zer-, ent-, emp-, miss-: bezahlt, verloren, erklärt).
- **Modalverb:** pres 1sg=3sg utan ändelse (kann/kann, muss/muss,
  darf/darf); imperativceller = "".
- Hjälpverb: sein (bin/bist/ist/sind/seid/sind; war; gewesen),
  haben (habe/hast/hat; hatte; gehabt), werden (werde/wirst/wird; wurde;
  geworden).

## Substantiv

6 celler: nom_sg, akk_sg, dat_sg, gen_sg, nom_akk_gen_pl, dat_pl.

- **gen_sg:** maskulinum/neutrum -s eller -es (des Hauses, des Tags/Tages —
  välj -es för enstaviga: Hauses, Tages; -s för flerstaviga: Lehrers);
  femininum oförändrad (der Frau).
- **Svaga maskuliner (n-deklination):** Junge, Kollege, Bauer, Herr, Polizist,
  Student, Elefant, Löwe, Nachbar: -n/-en i ALLA celler utom nom_sg
  (den Jungen, dem Jungen, des Jungen, die Jungen, den Jungen).
- **dat_pl:** alltid -n om pluralen inte redan slutar på -n eller -s
  (den Kindern, den Häusern; MEN den Autos).
- **Plural:** -e (+omljud: Stühle), -er (+omljud: Häuser, Kinder), -(e)n
  (Frauen, Lampen), -s (Autos, Cafés), ∅ (+omljud: Väter, Mütter). Ge akt på
  omljud.
- **Defekta:** oräknebara (Milch, Reis, Geld, Obst): pluralceller = "".
  Plurale tantum (Eltern, Leute): singularceller = "".

## Adjektiv

144 celler: grad (pos/komp/superl) × deklination (stark/svag/bland) ×
genus (m/f/n) × kasus (nom/akk/dat/gen) — plus predikativa grundformer per
grad om sådana celler finns.

- **Ändelsetabellerna är helt regelbundna** — det enda ordspecifika är:
  1. komparativ-/superlativstammen: -er/-st (+omljud för många enstaviga:
     alt→älter→ältest-, groß→größer→größt-, jung→jünger, warm→wärmer;
     -est efter -t/-d/-ß/-sch: ältest-, kürzest-);
  2. e-bortfall: teuer→teur- (teure), dunkel→dunkl- (dunkle);
  3. suppletiva: gut→besser→best-, viel→mehr→meist-, hoch→höher→höchst-
     (obs stamväxling hoch/hoh-: das hohe Haus), nah→näher→nächst-.
- Stark deklination = pronominal ändelse (guter Mann, gutem Mann); svag =
  -e/-en (der gute Mann, dem guten Mann); blandad efter ein/kein/possessiv
  (ein guter Mann, ein gutes Kind).
- **mehr** (komparativ av viel) är OBÖJLIGT: alla mehr-celler = "mehr".
- Oböjliga färger: rosa, lila, orange — samma form i alla celler.

## Pronomen

4 celler: nom, akk, dat, gen. Personliga: ich/mich/mir/meiner,
du/dich/dir/deiner, er/ihn/ihm/seiner, sie/sie/ihr/ihrer, es/es/ihm/seiner,
wir/uns/uns/unser, ihr/euch/euch/euer, sie/sie/ihnen/ihrer, Sie/Sie/Ihnen/
Ihrer. Genitivformerna är arkaiska men hör till paradigmet — fyll i dem.
man: akk=einen, dat=einem, gen="".

## Frågepronomen

wer → wen/wem/wessen. was → was/was/wessen (dat = "" — "was" saknar dativ;
renderaren använder wo-konstruktion).
