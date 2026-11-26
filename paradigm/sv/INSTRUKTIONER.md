# Böjningsinstruktioner — svenska (sv)

> Injiceras i LLM-prompten av `ordbok generera`: sektionen **Allmänt** plus
> sektionen för aktuell ordklass. Rubrikerna på `##`-nivå måste exakt matcha
> ordklassnamnen i databasen (Verb, Substantiv, Adjektiv, …).

## Allmänt

- Svara med formerna exakt som de skrivs i modern standardsvenska
  (SAOL-norm). Inga talspråksformer ("dom", "sen", "nån").
- Flerordslemman: böj det första ordet som inte är reflexivmarkör; resten
  följer med oförändrat ("laga mat" → "lagar mat"; "gifta sig" → "gifter sig" —
  "sig" står alltid kvar som "sig", renderaren byter till mig/dig).
- Lämna "" endast när formen inte existerar — gissa aldrig fram en form som
  inte används.

## Verb

Axlar: tempus (inf/pres/pret/sup/imp) × diates (aktiv/passiv).

- **Konjugationer:** grupp 1 (-ar: talar/talade/talat), grupp 2 (-er:
  ringer/ringde/ringt; stänger/stängde/stängt), grupp 3 (kortverb: bor/bodde/
  bott), grupp 4 (starka: springer/sprang/sprungit). Bestäm grupp per verb —
  blanda aldrig mönster.
- **Imperativ** = verbstammen: tala!, ring!, bo!, spring!. Grupp 1 behåller
  -a (tala!), övriga är stam utan ändelse.
- **Passiv (-s):** läggs på respektive aktiv form: talas/talades/talats;
  pres-passiv av grupp 2/4 stryker -er: stängs (inte "stängers"), sprungits
  som supinum. Ingen passiv imperativ.
- **Perfekt particip** (perfpart_*): böjs som ett adjektiv, skilt från
  supinum. obest_utr_sg = -d/-t/-dd (stängd, målad, byggd, sprungen),
  obest_neu_sg = -t/-tt (stängt, målat, byggt, sprunget), a = -da/-dda/-na
  (stängda, målade, byggda, sprungna). Grupp 1: -ad/-at/-ade (målad).
  Starka verb ofta -en/-et/-na (skriven/skrivet/skrivna, sprungen). Verb
  utan passiv betydelse (intransitiva som springa, gå) har ändå particip
  för perfekttempus — fyll i det. Rent intransitiva utan particip = "".
- **Deponensverb** (hoppas, finnas, minnas, andas, trivas): fyll ENDAST
  passivcellerna (lemmat är redan s-form); aktivceller inkl. particip = "".
- **Modalverb** (kunna, vilja, måste, böra): imperativ = "". "måste" är
  oböjligt: pres=måste, pret=måste, sup="" (eller "måst" — använd "").
- Fallgropar: gå→gick→gått, stå→stod→stått, se→såg→sett, ge→gav→gett,
  komma→kom→kommit, äta→åt→ätit, vara→var→varit, bli→blev→blivit.

Exempel (springa): inf=springa, pres=springer, pret=sprang, sup=sprungit,
imp=spring, inf_passiv=springas, pres_passiv=springs, pret_passiv=sprangs,
sup_passiv=sprungits.

## Substantiv

Axlar: species (obest/best) × numerus (sg/pl) × kasus (grundform/genitiv).
8 celler: obest_sg, obest_sg_gen, best_sg, best_sg_gen, obest_pl,
obest_pl_gen, best_pl, best_pl_gen.

- **Bestämdhetssuffix** styrs av genus: utrum -en/-n (flickan, bilen),
  neutrum -et/-t (huset, äpplet).
- **Pluraltyper:** -or (flickor), -ar (bilar), -er (gäster), -n (äpplen),
  ∅ (hus, lärare). Bestämd plural: -na/-a/-en (flickorna, husen, lärarna).
- **Genitiv:** alltid -s utan apostrof (flickans, husets). Ord som redan
  slutar på -s får ingen ändelse (ett hus tak → genitiv = "hus").
- **Defekta:** plurale tantum (pengar, kläder, glasögon): sg-celler = "".
  Oräknebara (mjölk, ris, snö): pl-celler = "".
- Fallgropar: omljudsplural (man→män, hand→händer, fot→fötter, natt→nätter),
  öga→ögon, öra→öron.

Exempel (flicka): obest_sg=flicka, obest_sg_gen=flickas, best_sg=flickan,
best_sg_gen=flickans, obest_pl=flickor, obest_pl_gen=flickors,
best_pl=flickorna, best_pl_gen=flickornas.

## Adjektiv

8 celler. OBS terminologi i cell-id: **"m" = utrum, "f" = neutrum**
(genusaxelns kodning), "a" = alla genus.

- obest_m_sg_pos: utrumform (grön, fin)
- obest_f_sg_pos: neutrumform (grönt, fint). Stavning: -d→-tt (röd→rött,
  död→dött), -t→oförändrat (svart→svart, trött→trött), vokal→-tt (blå→blått,
  fri→fritt), -en→-et (mogen→moget).
- best_a_sg_pos / obest_a_pl_pos / best_a_pl_pos: -a-form (gröna). Vanligen
  identiska tre celler — fyll alla tre ändå. -el/-en/-er tappar e:t
  (enkel→enkla, mogen→mogna, vacker→vackra).
- komp: -are (grönare) eller suppletiv (äldre, större, bättre, sämre, mindre).
- obest_superl: -ast (grönast) eller suppletiv (äldst, störst, bäst).
- best_superl: -aste (grönaste); suppletiva får -a (äldsta, största, bästa).
- **Oböjliga adjektiv** (bra, gratis, fel, rosa, lila, orange, äkta): samma
  form i alla pos-celler.
- **Analytisk komparation** (typiskt particip och långa ord: intresserad,
  spännande): komp/superl-celler = "" — renderaren bildar "mer/mest X".
- Suppletiv: liten → litet (f) / lilla (best sg) / små (pl) / mindre / minst.
  gammal → gammalt / gamla / äldre / äldst. god/bra → bättre / bäst.

## Pronomen

Celler per slot-fil (nom, ack_dat samt possessiva m_sg/f_sg/a_pl där sådana
finns). Personliga: jag/mig, du/dig, han/honom, hon/henne, den/den, det/det,
vi/oss, ni/er, de/dem. Possessiv: min/mitt/mina, din/ditt/dina, sin/sitt/sina,
vår/vårt/våra, er/ert/era; hans/hennes/dess/deras är oböjliga (samma form i
alla tre possessivceller).

## Frågepronomen

vem → ack_dat=vem (modern svenska; "vem såg du?"), genitiv=vems (om cell
finns). vad är oböjligt.

## Räkneord

Celler: inv (grundform: tre, fyra …). "en" är det enda genusböjda: m_sg=en,
f_sg=ett. Ordningstal böjs som adjektiv i bestämdhet: obest_a_sg=tredje
(oböjligt mönster för -e-slut), a_pl=tredje.
