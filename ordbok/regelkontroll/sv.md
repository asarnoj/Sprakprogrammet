# Regelkontroll: svenska

*Genererad av `python -m sprakprog.bojning.kontroll sv`. Ändra inte för hand — ändra reglerna i `src/sprakprog/bojning/sv.py` och kör om.*

Reglerna förutsäger varje ords former ur grundformen (KÄRNAN 3.4). Det reglerna inte når blir **undantagskort**, i införandeordning: den första avvikande formen först, och sedan förutsägs resten med den känd.

Varje undantagskort nedan är antingen **ett äkta undantag**, **en regel som saknas** eller **ett fel i datan**. Former som bryter mot en regel utan undantag är redan utsorterade som misstänkta datafel.

## Sammanfattning

| ordklass | ord | regelbundna | med kort | undantagskort | misstänkta datafel |
|---|---|---|---|---|---|
| Verb | 174 | 80 | 94 | 199 | 19 |
| Substantiv | 259 | 136 | 123 | 141 | 18 |
| Adjektiv | 111 | 98 | 13 | 20 | 15 |

## Ljudregler som används

En ljudanpassning som beror på ljudet och inte på klassen är ett eget regelkort. Antal ord där regeln ger minst en form:

| regel | ord | vad den gör |
|---|---|---|
| `mm_nn_före_konsonant` | 8 | m och n dubbeltecknas inte före konsonant: känn + de → kände, komm + na → komna |
| `mm_i_ordslut` | 3 | m dubbeltecknas inte i ordslut: glömm → glöm (men känn) |
| `konsonant_dt_tar_e` | 5 | stam på konsonant + d/t tar bara -e i preteritum: använd → använde, lyft → lyfte |
| `s_x_tar_es` | 3 | stam på s eller x tar -es i presens passiv: läs → läses |
| `obetonat_e_faller` | 23 | e i obetonat -el/-er/-en faller före ändelse: fågel → fåglar, öppen → öppna |
| `en_blir_et` | 6 | adjektiv på obetonat -en tar -et i neutrum: öppen → öppet |
| `d_blir_t` | 9 | d blir t i neutrum: hård → hårt, röd → rött |
| `vokal_t_blir_tt` | 3 | vokal + t dubbeltecknas i neutrum: vit → vitt |
| `slutvokal_tar_tt` | 3 | adjektiv på vokal tar -tt i neutrum: ny → nytt |
| `sam_dubblar_m` | 2 | -sam dubbeltecknar m före ändelse: ensam → ensamma |

## Att granska

1. **Komparation.** Datan har syntetisk komparativ för ord där svenskan hellre säger mer (`intressantare`, `normalare`). Reglerna förutsäger dem, så de syns inte som kort här — men de avgör om renderaren skriver `intressantare` eller `mer intressant`.

## Verb: ord med undantagskort (94)

| ord | kort |
|---|---|
| använda | presens **använder** |
| beskriva | presens **beskriver** · preteritum **beskrev** · supinum **beskrivit** |
| bestämma | presens **bestämmer** |
| besöka | presens **besöker** |
| betala | supinum **betalt** · particip utr **betald** |
| bjuda | presens **bjuder** · preteritum **bjöd** · supinum **bjudit** |
| bli | preteritum **blev** · supinum **blivit** |
| bryta | presens **bryter** · preteritum **bröt** · supinum **brutit** |
| bygga | presens **bygger** |
| byta | presens **byter** |
| bära | presens **bär** · preteritum **bar** · supinum **burit** |
| bör | presens **bör** · preteritum **borde** |
| dra | preteritum **drog** · supinum **dragit** |
| dricka | presens **dricker** · preteritum **drack** · supinum **druckit** |
| drömma | presens **drömmer** · pres. passiv **drömms** |
| dö | preteritum **dog** · supinum **dött** · particip utr **död** |
| erbjuda | presens **erbjuder** · preteritum **erbjöd** · supinum **erbjudit** |
| falla | presens **faller** · preteritum **föll** · supinum **fallit** |
| finnas | pres. passiv **finns** · pret. passiv **fanns** · sup. passiv **funnits** |
| flyga | presens **flyger** · preteritum **flög** · supinum **flugit** |
| fortsätta | presens **fortsätter** · preteritum **fortsatte** |
| fylla | presens **fyller** |
| får (modal_får) | preteritum **fick** · supinum **fått** · particip utr **fådd** |
| följa | presens **följer** |
| förbereda | presens **förbereder** |
| föreställa sig | presens **föreställer** |
| förlåta | presens **förlåter** · preteritum **förlät** · supinum **förlåtit** |
| förstå | preteritum **förstod** · supinum **förstått** · particip utr **förstådd** |
| försöka | presens **försöker** |
| ge | preteritum **gav** · supinum **gett** · particip utr **given** |
| gifta sig | presens **gifter** |
| glömma | presens **glömmer** · imperativ **glömma** · pres. passiv **glömmas** |
| gråta | presens **gråter** · preteritum **grät** · supinum **gråtit** · particip utr **gråtad** · particip neutr **gråtat** · particip pl **gråtade** |
| gå | preteritum **gick** · supinum **gått** · particip utr **gången** |
| göra | presens **gör** · preteritum **gjorde** |
| ha | supinum **haft** |
| hjälpa | presens **hjälper** |
| hända | presens **händer** |
| hålla | presens **håller** · preteritum **höll** · supinum **hållit** |
| hålla med | presens **håller** · preteritum **höll** · supinum **hållit** |
| höra | presens **hör** |
| jämföra | presens **jämför** |
| kan | presens **kan** · preteritum **kunde** · supinum **kunnat** |
| komma | presens **kommer** · preteritum **kom** · supinum **kommit** |
| krypa | presens **kryper** · preteritum **kröp** · supinum **krupit** |
| känna | presens **känner** |
| köpa | presens **köper** |
| köra | presens **kör** |
| le | preteritum **log** · supinum **lett** · particip utr **legen** · particip neutr **legit** |
| leka | presens **leker** |
| leva | presens **lever** |
| ligga | presens **ligger** · preteritum **låg** · supinum **legat** |
| lyfta | presens **lyfter** |
| lägga | presens **lägger** · preteritum **la** · supinum **lagt** · particip utr **lagd** |
| lära sig | presens **lär** |
| läsa | presens **läser** |
| lösa | presens **löser** |
| minnas | pres. passiv **minns** · sup. passiv **minnits** |
| märka | presens **märker** |
| måste | presens **måste** · preteritum **måste** |
| njuta | presens **njuter** · preteritum **njöt** · supinum **njutit** |
| resa | presens **reser** |
| ringa | presens **ringer** |
| röra | presens **rör** |
| se | preteritum **såg** · supinum **sett** · particip utr **sedd** |
| sitta | presens **sitter** · preteritum **satt** · supinum **suttit** |
| sjunga | presens **sjunger** · preteritum **sjöng** · supinum **sjungit** |
| ska | presens **ska** · preteritum **skulle** |
| skriva | presens **skriver** · preteritum **skrev** · supinum **skrivit** |
| skära | presens **skär** · preteritum **skar** · supinum **skurit** |
| slå | preteritum **slog** · supinum **slagit** |
| sova | presens **sover** · preteritum **sov** · supinum **sovit** · pres. passiv **sovas** |
| springa | presens **springer** · preteritum **sprang** · supinum **sprungit** |
| stänga | presens **stänger** |
| stå | preteritum **stod** · supinum **stått** |
| säga | presens **säger** · preteritum **sade** · supinum **sagt** · particip utr **sagd** |
| sälja | presens **säljer** · preteritum **sålde** |
| söka | presens **söker** |
| ta | preteritum **tog** · supinum **tagit** |
| trycka | presens **trycker** |
| tycka | presens **tycker** |
| tänka | presens **tänker** |
| undvika | presens **undviker** · preteritum **undvek** · supinum **undvikit** |
| vakna | particip utr **vaken** |
| vara | presens **är** · preteritum **var** · supinum **varit** · imperativ **var** |
| veta | presens **vet** · preteritum **visste** · supinum **vetat** |
| vill | presens **vill** · preteritum **ville** · supinum **velat** |
| vinna | presens **vinner** · preteritum **vann** · supinum **vunnit** |
| välja | presens **väljer** · preteritum **valde** |
| vända | presens **vänder** |
| växa | presens **växer** · supinum **vuxit** · pres. passiv **växs** |
| äga | presens **äger** |
| äta | presens **äter** · preteritum **åt** · supinum **ätit** |
| åka | presens **åker** |

## Substantiv: ord med undantagskort (123)

| ord | kort |
|---|---|
| arm | plural **armar** |
| badrum | best. sg **badrummet** |
| bar | plural **barer** |
| bekant | plural **bekanta** · best. pl **bekanta** |
| bil | plural **bilar** |
| biljett | plural **biljetter** |
| bok | plural **böcker** |
| bonde | plural **bönder** |
| brandman | best. sg **brandmannen** · plural **brandmän** · best. pl **brandmännen** |
| bror | best. sg **brodern** · plural **bröder** |
| buss | plural **bussar** |
| busshållplats | plural **busshållplatser** |
| by | plural **byar** |
| byrå | plural **byråer** |
| båt | plural **båtar** |
| café | best. sg **caféet** · plural **cafés** · best. pl **caféerna** |
| chef | plural **chefer** |
| dag | plural **dagar** |
| del | plural **delar** |
| dotter | plural **döttrar** |
| dörr | plural **dörrar** |
| eftermiddag | plural **eftermiddagar** |
| eld | plural **eldar** |
| elev | plural **elever** |
| familj | plural **familjer** |
| finger | plural **fingrar** |
| fisk (djur_fisk) | plural **fiskar** |
| fisk (mat_fisk) | plural **fiskar** |
| flod | plural **floder** |
| flygplats | plural **flygplatsers** · best. pl **flygplatserna** |
| form | plural **former** |
| fot | plural **fötter** |
| framtid | plural **framtider** |
| fru | plural **fruar** |
| frukt | plural **frukter** |
| frys | plural **frysar** |
| gris | plural **grisar** |
| grönsak | plural **grönsaker** |
| gäst | plural **gäster** |
| hagel | best. pl **hagelen** |
| hals | plural **halsar** |
| halsduk | plural **halsdukar** |
| hand | plural **händer** |
| hatt | plural **hattar** |
| hem | best. sg **hemmet** |
| historia | best. sg **historien** · plural **historier** |
| hund | plural **hundar** |
| huvud | plural **huvuden** |
| häst | plural **hästar** |
| jord | plural **jordar** |
| juice | plural **juicer** |
| kaffe | plural **kaffe** · best. pl **kaffena** |
| kalsong | plural **kalsonger** |
| katt | plural **katter** |
| kjol | plural **kjolar** |
| klass | plural **klasser** |
| ko | plural **kor** |
| kock | plural **kockar** |
| kväll | plural **kvällar** |
| kärlek | plural **kärlekar** |
| land | plural **länder** |
| lillebror | plural **lillebröder** |
| luft | plural **lufter** |
| makt | plural **makter** |
| man (fam_make) | best. sg **mannen** · plural **män** · best. pl **männen** |
| man (pers_man) | best. sg **mannen** · plural **män** · best. pl **männen** |
| marknad | plural **marknader** |
| middag | plural **middagar** |
| miljö | plural **miljöer** |
| minut | plural **minuter** |
| morgon | plural **morgnar** |
| mun | best. sg **munnen** · plural **munnar** |
| mus | plural **möss** |
| månad | plural **månader** |
| natt | plural **nätter** |
| orm | plural **ormar** |
| ost | plural **ostar** |
| park | plural **parker** |
| person | plural **personer** |
| polis | plural **poliser** |
| potatis | plural **potatisar** |
| pris | plural **priser** |
| restaurang | plural **restauranger** |
| rum | best. sg **rummet** |
| rygg | plural **ryggar** |
| rök | plural **rök** |
| salt | plural **salter** |
| sand | plural **sand** |
| sekund | plural **sekunder** |
| sjö | plural **sjöar** |
| skafferi | best. sg **skafferiet** |
| sko | plural **skor** |
| skog | plural **skogar** |
| smak | plural **smakar** |
| sol | plural **solar** |
| son | plural **söner** |
| stad | plural **städer** |
| sten | plural **stenar** |
| stol | plural **stolar** |
| storebror | best. sg **storebrodern** · plural **storebröder** |
| storm | plural **stormar** |
| strand | plural **stränder** |
| säng | plural **sängar** |
| t-shirt | plural **t-shirtar** |
| tand | plural **tänder** |
| taxi | plural **taxiar** |
| te | best. sg **teet** |
| telefon | plural **telefoner** |
| tid | plural **tider** |
| toalett | plural **toaletter** |
| typ | plural **typer** |
| ugn | plural **ugnar** |
| vin | plural **viner** |
| vind | plural **vindar** |
| vuxen | best. sg **vuxnen** · plural **vuxna** · best. pl **vuxna** |
| väg | plural **vägar** |
| vägg | plural **väggar** |
| vän | best. sg **vännen** · plural **vänner** |
| värld | plural **världar** |
| växt | plural **växter** |
| öga | plural **ögon** |
| öl | plural **öl** |
| öra | plural **öron** |

## Adjektiv: ord med undantagskort (13)

| ord | kort |
|---|---|
| bra | komparativ **bättre** · superlativ **bäst** |
| dålig | komparativ **sämre** |
| fel | neutrum **fel** · plural **fel** |
| gammal | plural **gamla** · komparativ **äldre** |
| gratis | neutrum **gratis** · plural **gratis** |
| hög | komparativ **högre** |
| lat | neutrum **lat** |
| liten | plural **små** · best. sg **lilla** · komparativ **mindre** · superlativ **minst** |
| lång | komparativ **längre** |
| privat | neutrum **privat** |
| stor | komparativ **större** |
| tom | plural **tomma** |
| ung | komparativ **yngre** |

## Former som reglerna ger men datan saknar (9)

Här betyder en saknad form något: ordet uttrycks med ett annat ord (`mer`, `more`) eller böjs inte så. Antingen avviker ordet från reglerna — och det är kunskap om ordet — eller så saknas formen i datan.

| ord | cell | reglerna ger |
|---|---|---|
| besviken | komparativ | besviknare |
| död | komparativ | dödare |
| fel | komparativ | felare |
| halv | komparativ | halvare |
| hel | komparativ | helare |
| lik | komparativ | likare |
| officiell | komparativ | officiellare |
| speciell | komparativ | speciellare |
| stängd | komparativ | stängdare |

## Misstänkta datafel (52)

| ord | cell | i datan | skäl |
|---|---|---|---|
| byta | inf. passiv | byts | passiv ≠ aktiv form + s (byta → bytas) |
| förbereda | pret. passiv | förberedades | passiv ≠ aktiv form + s (förberedde → förbereddes) |
| försöka | inf. passiv | försöks | passiv ≠ aktiv form + s (försöka → försökas) |
| gråta | inf. passiv | gråts | passiv ≠ aktiv form + s (gråta → gråtas) |
| krypa | sup. passiv | krypits | passiv ≠ aktiv form + s (krupit → krupits) |
| leva | inf. passiv | levs | passiv ≠ aktiv form + s (leva → levas) |
| lyfta | inf. passiv | lyfts | passiv ≠ aktiv form + s (lyfta → lyftas) |
| lägga | pret. passiv | lades | passiv ≠ aktiv form + s (la → las) |
| röra | inf. passiv | rörs | passiv ≠ aktiv form + s (röra → röras) |
| sälja | sup. passiv | sålt | passiv ≠ aktiv form + s (sålt → sålts) |
| söka | sup. passiv | sökt | passiv ≠ aktiv form + s (sökt → sökts) |
| tacka | sup. passiv | tackat | passiv ≠ aktiv form + s (tackat → tackats) |
| titta | sup. passiv | tittat | passiv ≠ aktiv form + s (tittat → tittats) |
| tjäna | sup. passiv | tjänat | passiv ≠ aktiv form + s (tjänat → tjänats) |
| tro | sup. passiv | trott | passiv ≠ aktiv form + s (trott → trotts) |
| trycka | sup. passiv | tryckt | passiv ≠ aktiv form + s (tryckt → tryckts) |
| träffa | sup. passiv | träffat | passiv ≠ aktiv form + s (träffat → träffats) |
| tvätta | sup. passiv | tvättat | passiv ≠ aktiv form + s (tvättat → tvättats) |
| äga | inf. passiv | ägs | passiv ≠ aktiv form + s (äga → ägas) |
| bekant | best. sg | bekanta | bestämd form stämmer inte med genus (utrum i datan) |
| bekant | gen. best. sg | bekantas | följer av bestämd singular, som är misstänkt fel |
| byrå | gen. sg | byråns | genitiv ≠ form + s (byrå → byrås) |
| exempel | gen. sg | exempel | genitiv ≠ form + s (exempel → exempels) |
| exempel | gen. pl | exempel | genitiv ≠ form + s (exempel → exempels) |
| fråga (skol_fråga) | gen. sg | frågans | genitiv ≠ form + s (fråga → frågas) |
| fråga (skol_fråga) | gen. best. pl | frågorna | genitiv ≠ form + s (frågorna → frågornas) |
| får (djur_får) | gen. sg | får | genitiv ≠ form + s (får → fårs) |
| får (djur_får) | gen. best. sg | farens | genitiv ≠ form + s (fåren → fårens) |
| får (djur_får) | gen. pl | får | genitiv ≠ form + s (får → fårs) |
| får (djur_får) | gen. best. pl | farens | genitiv ≠ form + s (fåren → fårens) |
| får (djur_får) | best. sg | fåren | bestämd form stämmer inte med genus (neutrum i datan) |
| grönsak | gen. best. sg | grönsaksens | genitiv ≠ form + s (grönsaken → grönsakens) |
| häst | gen. best. pl | hästarna | genitiv ≠ form + s (hästarna → hästarnas) |
| hår | gen. pl | hår | genitiv ≠ form + s (hår → hårs) |
| kaffe | gen. pl | kaffe | genitiv ≠ form + s (kaffe → kaffes) |
| öl | best. sg | ölet | bestämd form stämmer inte med genus (utrum i datan) |
| öl | gen. best. sg | ölets | följer av bestämd singular, som är misstänkt fel |
| dum | komparativ | dummare | plural och komparativ har olika stam (duma / dummare) |
| dum | superlativ | dummast | plural och komparativ har olika stam (duma / dummare) |
| dum | best. superlativ | dummaste | plural och komparativ har olika stam (duma / dummare) |
| gratis | komparativ | gratis | gradform lika med grundformen |
| gratis | superlativ | gratis | gradform lika med grundformen |
| gratis | best. superlativ | gratis | gradform lika med grundformen |
| nyfiken | komparativ | nyfikenare | plural och komparativ har olika stam (nyfikna / nyfikenare) |
| nyfiken | superlativ | nyfikenast | plural och komparativ har olika stam (nyfikna / nyfikenare) |
| nyfiken | best. superlativ | nyfikenaste | plural och komparativ har olika stam (nyfikna / nyfikenare) |
| orange | komparativ | orange | gradform lika med grundformen |
| orange | superlativ | orange | gradform lika med grundformen |
| orange | best. superlativ | orange | gradform lika med grundformen |
| rosa | komparativ | rosa | gradform lika med grundformen |
| rosa | superlativ | rosa | gradform lika med grundformen |
| rosa | best. superlativ | rosa | gradform lika med grundformen |
