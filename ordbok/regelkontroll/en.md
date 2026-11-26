# Regelkontroll: engelska

*Genererad av `python -m sprakprog.bojning.kontroll en`. Ändra inte för hand — ändra reglerna i `src/sprakprog/bojning/en.py` och kör om.*

Reglerna förutsäger varje ords former ur grundformen (KÄRNAN 3.4). Det reglerna inte når blir **undantagskort**, i införandeordning: den första avvikande formen först, och sedan förutsägs resten med den känd.

Varje undantagskort nedan är antingen **ett äkta undantag**, **en regel som saknas** eller **ett fel i datan**. Former som bryter mot en regel utan undantag är redan utsorterade som misstänkta datafel.

## Sammanfattning

| ordklass | ord | regelbundna | med kort | undantagskort | misstänkta datafel |
|---|---|---|---|---|---|
| Verb | 174 | 114 | 60 | 98 | 0 |
| Substantiv | 259 | 242 | 17 | 17 | 0 |
| Adjektiv | 111 | 105 | 6 | 8 | 0 |

## Ljudregler som används

En ljudanpassning som beror på ljudet och inte på klassen är ett eget regelkort. Antal ord där regeln ger minst en form:

| regel | ord | vad den gör |
|---|---|---|
| `sibilant_tar_es` | 18 | efter s, x, z, ch och sh blir -s -es: misses, beaches, buses |
| `konsonant_y_blir_i` | 33 | y efter konsonant blir i före -s, -ed, -er och -est: carries, cried, cities, happier |
| `e_smälter_med_e` | 41 | ett slut-e smälter ihop med en ändelse på e: liked, agreed, braver, freest |
| `stumt_e_faller` | 45 | stumt slut-e faller före -ing: making, using — men seeing, being |
| `ie_blir_y` | 2 | ie blir y före -ing: dying, lying |
| `enstavig_dubblar` | 18 | enstavigt ord på vokal + konsonant dubbeltecknar före en vokal: stopped, running, bigger |

## Att granska

1. **Amerikansk engelska.** Datan stavar och böjer amerikanskt: `traveled`, `practiced`, `gotten`, `learned`, `gray`, `neighbor`. Brittiska former (`travelled`, `got`, `learnt`, `grey`) räknas i dag som fel. Ska de godtas som varianter (KÄRNAN 8.3)?
2. **Komparation.** För `half`, `whole` och `wrong` ger reglerna en form på -er som datan saknar; orden går knappast att komparera alls. `purpler` och `yellower` står i datan men är ovanliga mot `more purple`, och `deader`, `readier` och `pinker` följer reglerna men är ovanliga.

## Verb: ord med undantagskort (60)

| ord | kort |
|---|---|
| be | presens 3 sg **is** · preteritum **was** · particip **been** · presens 1 sg **am** · presens 2 sg **are** · preteritum 2 sg **were** |
| become | preteritum **became** · particip **become** |
| break | preteritum **broke** · particip **broken** |
| build | preteritum **built** |
| buy | preteritum **bought** |
| can | presens 3 sg **can** · preteritum **could** |
| choose | preteritum **chose** · particip **chosen** |
| come | preteritum **came** · particip **come** |
| cost | preteritum **cost** |
| cut | preteritum **cut** |
| do | presens 3 sg **does** · preteritum **did** · particip **done** |
| drink | preteritum **drank** · particip **drunk** |
| drive | preteritum **drove** · particip **driven** |
| eat | preteritum **ate** · particip **eaten** |
| fall | preteritum **fell** · particip **fallen** |
| feel | preteritum **felt** |
| find | preteritum **found** |
| fly | preteritum **flew** · particip **flown** |
| forget | preteritum **forgot** · particip **forgotten** · ing-form **forgetting** |
| forgive | preteritum **forgave** · particip **forgiven** |
| get married | preteritum **got** · particip **gotten** |
| give | preteritum **gave** · particip **given** |
| go | presens 3 sg **goes** · preteritum **went** · particip **gone** |
| grow | preteritum **grew** · particip **grown** |
| have | presens 3 sg **has** · preteritum **had** |
| hear | preteritum **heard** |
| hit | preteritum **hit** |
| hold | preteritum **held** |
| know | preteritum **knew** · particip **known** |
| leave | preteritum **left** |
| lie down | preteritum **lay** · particip **lain** |
| lose | preteritum **lost** |
| may | presens 3 sg **may** · preteritum **might** |
| mean (gen_mena) | preteritum **meant** |
| meet | preteritum **met** |
| must | presens 3 sg **must** |
| pay | preteritum **paid** |
| put | preteritum **put** |
| read | preteritum **read** |
| run | preteritum **ran** · particip **run** |
| say | preteritum **said** |
| see | preteritum **saw** · particip **seen** |
| sell | preteritum **sold** |
| should | presens 3 sg **should** |
| show | particip **shown** |
| sing | preteritum **sang** · particip **sung** |
| sit | preteritum **sat** |
| sleep | preteritum **slept** |
| stand | preteritum **stood** |
| swim | preteritum **swam** · particip **swum** |
| take | preteritum **took** · particip **taken** |
| tell | preteritum **told** |
| think (gen_tycka) | preteritum **thought** |
| think (kog_tänka) | preteritum **thought** |
| throw | preteritum **threw** · particip **thrown** |
| understand | preteritum **understood** |
| wake up | preteritum **woke** · particip **woken** |
| will | presens 3 sg **will** · preteritum **would** |
| win | preteritum **won** |
| write | preteritum **wrote** · particip **written** |

## Substantiv: ord med undantagskort (17)

| ord | kort |
|---|---|
| bookshelf | plural **bookshelves** |
| child | plural **children** |
| fish (djur_fisk) | plural **fish** |
| fish (mat_fisk) | plural **fish** |
| foot | plural **feet** |
| life | plural **lives** |
| man | plural **men** |
| mouse | plural **mice** |
| person | plural **people** |
| potato | plural **potatoes** |
| salesperson | plural **salespeople** |
| scarf | plural **scarves** |
| sheep | plural **sheep** |
| stomach | plural **stomachs** |
| tooth | plural **teeth** |
| wife | plural **wives** |
| woman | plural **women** |

## Adjektiv: ord med undantagskort (6)

| ord | kort |
|---|---|
| bad | komparativ **worse** · superlativ **worst** |
| good | komparativ **better** · superlativ **best** |
| lonely | komparativ **lonelier** |
| narrow | komparativ **narrower** |
| purple | komparativ **purpler** |
| yellow | komparativ **yellower** |

## Former som reglerna ger men datan saknar (3)

Här betyder en saknad form något: ordet uttrycks med ett annat ord (`mer`, `more`) eller böjs inte så. Antingen avviker ordet från reglerna — och det är kunskap om ordet — eller så saknas formen i datan.

| ord | cell | reglerna ger |
|---|---|---|
| half | komparativ | halfer |
| whole | komparativ | wholer |
| wrong | komparativ | wronger |

## Misstänkta datafel (0)

| ord | cell | i datan | skäl |
|---|---|---|---|
