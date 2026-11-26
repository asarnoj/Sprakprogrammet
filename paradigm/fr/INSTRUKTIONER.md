# Böjningsinstruktioner — franska (fr)

> Injiceras i LLM-prompten av `ordbok generera`: sektionen **Allmänt** plus
> sektionen för aktuell ordklass.

## Allmänt

- Standardfranska (France), alla diakritiska tecken obligatoriska
  (é è ê ë à â ç î ï ô û ù œ).
- Flerordslemman: böj det första ordet som inte är reflexivmarkör (se/s').
  "se marier" → böj marier (marie, maries …) — utan pronomenet; renderaren
  sätter me/te/se/nous/vous. "faire confiance" → böj faire (fais confiance,
  fait confiance …) med "confiance" kvar oförändrat.
- Lämna "" endast när formen inte existerar.

## Verb

Axlar: tempus × person (P1–P3) × numerus. Tempus: présent, imparfait,
passé simple (pret), futur simple, conditionnel présent, subjonctif présent
(subj), impératif (2sg/1pl/2pl), infinitif, participe présent, participe
passé (4 genus/numerus-former).

- **Grupper:** -er (parler), -ir/-issant (finir: finis/finissons), tredje
  gruppen (vendre, partir, prendre, voir …). Blanda aldrig mönster.
- **Stavningsväxlingar i -er-verb:** -ger → -geons (mangeons), -cer → -çons
  (commençons); -eler/-eter dubblerar eller får grav accent (appelle,
  achète); e/é + konsonant + er → è i betonade former (lève, préfère);
  -yer → -ie (paie/paye: välj -ie-formen, envoie).
- **Passé simple:** fyll alltid i (litterär men del av paradigmet):
  parlai/parlas/parla/parlâmes/parlâtes/parlèrent; finis…finirent;
  vendis…vendirent; oregelbundna: fus, eus, fis, vins.
- **Subjonctif présent:** que je parle …; oregelbundna: sois, aie, fasse,
  aille, puisse, sache, veuille.
- **Impératif:** parle! (utan -s för -er-verb; MEN parles-en/vas-y hanteras
  av renderaren — lagra utan -s), finis!, parlons!, parlez!. Oregelbundna:
  sois/soyons/soyez, aie/ayons/ayez, sache/sachons/sachez.
- **Participe passé, 4 former:** parlé/parlée/parlés/parlées. Oregelbundna:
  fait/faite, mis/mise, pris/prise, ouvert/ouverte, né/née. Verb vars pp
  aldrig kongruerar i praktiken fylls ändå i regelrätt (couru/courue).
- **Défectiva:** pleuvoir (bara 3sg: pleut, pleuvait, plut, pleuvra,
  pleuvrait, pleuve) — övriga personceller "". falloir likaså (il faut).
- Fallgropar: aller (vais/vas/va/allons/allez/vont; irai; aille),
  être/avoir/faire/pouvoir/vouloir/savoir/venir/prendre helt oregelbundna.

## Substantiv

2 celler: sg, pl. (Genus är en lexemegenskap, inte en form.)

- Plural: +s; -eau/-eu → +x (couteaux, jeux); -al → -aux (animaux, MEN
  festivals); -ail → -aux där etablerat (travaux); -s/-x/-z oförändrade
  (mois, prix, nez); œil → yeux.
- Oräknebara (lait, riz, argent): pl = "".

## Adjektiv

12 celler: pos/komp/superl × msc/fem × sg/pl.

- **Positiv:** fem = +e (grand→grande); -e oförändrat (rouge); -eux → -euse
  (heureux→heureuse); -er → -ère (premier→première); -f → -ve (neuf→neuve);
  -on/-en → -onne/-enne (bon→bonne, ancien→ancienne); oregelbundna:
  beau→belle, nouveau→nouvelle, vieux→vieille, blanc→blanche, long→longue,
  frais→fraîche, sec→sèche, doux→douce, faux→fausse. Plural: +s; -eau → +x
  (beaux); -al → -aux (normaux); -s/-x oförändrade (gris, heureux).
  (Formerna bel/nouvel/vieil framför vokal hanteras av renderaren — lagra
  beau/nouveau/vieux.)
- **Komparation är analytisk** (plus grand — renderarens jobb): komp- och
  superl-celler = "" för ALLA adjektiv UTOM de syntetiska:
  bon → komp meilleur/meilleure/meilleurs/meilleures, superl = samma former
  (renderaren sätter le/la/les); mauvais → pire/pires (valfritt — fyll i);
  petit → moindre endast i abstrakt betydelse: lämna "" och låt "plus petit"
  bildas analytiskt.

## Pronomen

Per slot-fil. Personliga subjekt/objekt: je/me, tu/te, il/le+lui, elle/la+lui,
nous/nous, vous/vous, ils/les+leur, elles/les+leur. Följ cellbeskrivningarna;
vid en enda objektcell: ange direkt objekt-formen (me, te, le, la, nous,
vous, les).

**Tonique-cellen har `kasus=Gen`** — en ren etikett, inte en genitiv
(franskan saknar kasus). Cellen ska innehålla den disjunktiva formen:
moi, toi, lui, elle, nous, vous, eux, elles. Skriv pronomenet ensamt —
aldrig "de lui".

## Possessiv

7 celler. Kongruensen gäller det ÄGDA substantivet, aldrig ägaren:
"son livre" är hans ELLER hennes bok — cellens genus syftar på "livre".

- **Attributiv** (obest_m_sg / obest_f_sg / obest_a_pl):
  mon/ma/mes, ton/ta/tes, son/sa/ses, notre/notre/nos, votre/votre/vos,
  leur/leur/leurs. Plural saknar genusdistinktion — obest_a_pl är en cell.
  notre/votre/leur fyller m- och f-cellen med samma sträng.
- **Självständig** (best_m_sg / best_f_sg / best_m_pl / best_f_pl):
  mien/mienne/miens/miennes, tien/…, sien/…, nôtre/nôtre/nôtres/nôtres,
  vôtre/…, leur/leur/leurs/leurs. Här FINNS genusdistinktion i plural.
  Skriv formen **utan artikel** — renderaren sätter le/la/les ("le mien").
  Observera cirkumflexen: nôtre/vôtre (självständig) mot notre/votre
  (attributiv).
- Elisionen ma → mon framför vokal ("mon amie") är renderarens ansvar —
  ange "ma" i f-cellen.

## Frågepronomen

qui (person) är oböjligt; que (sak) — objektsform que, efter preposition
quoi (om cell finns).
