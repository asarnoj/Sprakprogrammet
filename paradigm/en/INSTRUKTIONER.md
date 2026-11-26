# Böjningsinstruktioner — engelska (en)

> Injiceras i LLM-prompten av `ordbok generera`: sektionen **Allmänt** plus
> sektionen för aktuell ordklass.

## Allmänt

- Amerikansk standardstavning (color, traveled, organize).
- Flerordslemman: böj huvudverbet/huvudordet, partiklar oförändrade
  ("wake up" → "wakes up", "woke up").
- Lämna "" endast när formen inte existerar.

## Verb

5 celler: inf_imp (grundform), pres_3sg, pret, sup (past participle), gerund.

- **pres_3sg:** +s; -es efter s/sh/ch/x/o (goes, watches); konsonant+y → -ies
  (studies, carries).
- **pret/sup regelbundet:** +ed; konsonantdubblering vid betonad kort
  slutstavelse (stopped, planned); y→ied (studied); -e → +d (danced).
- **gerund:** +ing; slut-e stryks (making); konsonantdubblering (running,
  swimming, sitting); -ie → -ying (dying, lying).
- **Oregelbundna:** ange den etablerade formen (speak/spoke/spoken,
  go/went/gone, eat/ate/eaten, buy/bought/bought). Verb med två godtagna
  former: välj den amerikanska (learned, inte learnt; gotten som sup av get).
- **be** är unikt: pres_3sg=is, pret=was, sup=been, gerund=being.
  (was/were-distinktionen hanteras av renderaren; lagra was.)
- **Modalverb** (can, must, may, should, will): inf_imp="" (kan ej stå som
  infinitiv med to), pres_3sg=samma som grundformen utan -s (can), pret där
  den finns (could, might, would), sup="", gerund="".

## Substantiv

4 celler: sg, pl, sg_gen, pl_gen.

- **Plural:** +s; -es efter s/sh/ch/x (boxes, dishes); konsonant+y → -ies
  (cities); -f/-fe → -ves där etablerat (knives, leaves; men roofs).
- **Oregelbundna:** child→children, man→men, woman→women, foot→feet,
  tooth→teeth, mouse→mice, person→people, sheep→sheep, fish→fish.
- **Genitiv:** sg_gen = 's (girl's, James's); pl_gen = s' för -s-plural
  (girls'), 's för oregelbunden plural (children's, men's).
- **Defekta:** oräknebara (milk, rice, money, information): pl och pl_gen =
  "". Plurale tantum (trousers, glasses, clothes): sg och sg_gen = "".

## Adjektiv

3 celler: pos, komp, superl.

- **Syntetisk komparation ENDAST** när den är etablerad: 1 stavelse
  (bigger/biggest, hotter/hottest — konsonantdubblering) och 2 stavelser på
  -y (happier/happiest), -le (simpler/simplest), -ow (narrower/narrowest).
- **Analytisk komparation** (interesting, dangerous, beautiful, tired …):
  komp och superl = "" — renderaren bildar "more/most X". Skriv ALDRIG
  "more interesting" i en cell.
- Suppletiv: good→better→best, bad→worse→worst, far→farther→farthest,
  little→less→least, much/many→more→most.

## Pronomen

2 celler: nom, obl. Personliga: I/me, you/you, he/him, she/her, it/it,
we/us, they/them.

## Possessiv

2 celler: obest (attributiv) och best (självständig).

- obest = determineraren framför substantivet: my, your, his, her, its,
  our, their — "my book".
- best = den självständiga formen: mine, yours, his, hers, its, ours,
  theirs — "it's mine".
- "his" och "its" har samma sträng i båda cellerna — fyll i båda ändå.
- Engelska possessiver kongruerar inte med det ägda substantivet; det finns
  ingen genus- eller numerusvariation att fylla i.

## Frågepronomen

who → objektsform whom (om cell finns; annars who), genitiv whose.
what är oböjligt.
