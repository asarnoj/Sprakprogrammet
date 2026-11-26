#!/usr/bin/env bash
#
# Nattkörning — granskning av böjningar + taggning av koncept och mönster.
#
#   ./kör_natt.sh
#
# Kör i ett VANLIGT terminalfönster med `claude` inloggat, inte inifrån
# Claude Code. Tar 2–4 timmar, nästan allt är väntetid. Ctrl-C är ofarligt:
# starta om med samma kommando, allt färdigt hoppas över.
#
# Ordningen är medveten: de billiga jobben (~35 anrop, några minuter) körs
# först och hinner alltid bli klara. Granskningen (~500 anrop) ligger sist,
# så att ett rate-limit mitt i natten inte tar med sig resten.

set -uo pipefail
cd "$(dirname "$0")"

LOGG="natt.log"
exec > >(tee -a "$LOGG") 2>&1

steg() { echo; echo "═══════════════════════════════════════════════════"; echo "  $* — $(date '+%H:%M:%S')"; echo "═══════════════════════════════════════════════════"; }
fatal() { echo "AVBRYTER: $*" >&2; exit 1; }

steg "0. Förberedelser"

[ -n "${ANTHROPIC_API_KEY:-}" ] && fatal "ANTHROPIC_API_KEY är satt — ta bort den, annars faktureras API-credits i stället för prenumerationen."
command -v claude >/dev/null || fatal "'claude' hittades inte. Installera Claude Code och logga in."
[ -d .venv ] || fatal "Ingen .venv. Kör: uv venv --python 3.13 && uv pip install -e ."
# shellcheck disable=SC1091
source .venv/bin/activate

git pull --ff-only || fatal "git pull misslyckades — lös det manuellt först."

steg "1. Bygg om databasen"

# setup.sql har ändrats (nya kolumner i MönsterKrav), så databasen måste
# byggas om. former.tsv ligger i git, så inga böjningar går förlorade.
ordbok import ordbok/nivålistor/bas_kärna.csv ordbok/nivålistor/grundord.csv --återinitiera || fatal "importen misslyckades"
for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m" || fatal "migration $m misslyckades"; done
ordbok importera-former ordbok/former.tsv --ersätt || fatal "kunde inte läsa in former.tsv"

KONCEPT=$(sqlite3 sprak.db "SELECT COUNT(*) FROM Koncept;")
FORMER=$(sqlite3 sprak.db "SELECT COUNT(*) FROM Former;")
echo "  Koncept: $KONCEPT (väntat 733)   Former: $FORMER (väntat 48135)"
[ "$KONCEPT" = "733" ] || fatal "fel antal koncept — databasen är inte den väntade."

steg "2. Koncepttaggning (~19 anrop)"

# gradbarhet, räknebar, valens för modalverben, semantik för pronomen,
# adverb och prepositioner.
ordbok tagga-koncept --verbose || echo "  VARNING: koncepttaggningen gav fel, se ovan. Fortsätter."

steg "2b. Lexemtaggning — genus och prenominal (~150 anrop, ~20 min)"

# Det här är det som faktiskt blockerar renderingen: utan genus går det inte
# att välja artikel eller böja adjektiv och possessiv i sv/de/fr/es/it.
ordbok tagga-lexem --verbose || echo "  VARNING: lexemtaggningen gav fel, se ovan. Fortsätter."

steg "3. Mönstertaggning — provkörning på 5 verb"

# Mönsterprompten har aldrig körts skarpt. Fem verb först, med en
# automatisk rimlighetskontroll, så att en trasig prompt inte tyst
# producerar 174 dåliga mönster medan ingen tittar.
#
# Verben är valda för att täcka de svåra fallen: ditransitivt (ge),
# kopula (vara), och kosta/finnas vars subjekt inte har något semantiskt
# krav alls — den sista är den väg som just rättats i schemat och som
# aldrig körts skarpt.
ordbok tagga-monster --koncept fys_ge,verb_vara,eko_v_kosta,verb_finnas,arb_hjälpa \
  --migration /tmp/prov_monster.sql --verbose

PROV_M=$(sqlite3 sprak.db "SELECT COUNT(*) FROM Mönster;")
PROV_K=$(sqlite3 sprak.db "SELECT COUNT(*) FROM MönsterKrav;")
PROV_S=$(sqlite3 sprak.db "SELECT COUNT(*) FROM MönsterKrav WHERE slot='subjekt';")
echo
echo "  Provresultat: $PROV_M mönster, $PROV_K krav, varav $PROV_S subjekt"
sqlite3 sprak.db "
  SELECT '    '||k.nyckel||'  '||mk.slot||'  tagg='||COALESCE(mk.tagg,'(inget krav)')||'  frastyp='||COALESCE(mk.frastyp,'-')
  FROM MönsterKrav mk JOIN Mönster m ON m.id=mk.mönster_id JOIN Koncept k ON k.id=m.koncept_id
  ORDER BY k.nyckel, mk.slot;"

if [ "$PROV_M" -lt 5 ] || [ "$PROV_K" -lt 5 ] || [ "$PROV_S" -lt 3 ]; then
  echo
  echo "  ✗ Provkörningen ser fel ut — hoppar över den fullständiga"
  echo "    mönstertaggningen. Granskningen körs ändå."
  HOPPA_MONSTER=1
else
  echo "  ✓ Rimligt. Kör hela satsen."
  HOPPA_MONSTER=0
fi

steg "4. Mönstertaggning — alla 174 verb (~18 anrop)"

if [ "$HOPPA_MONSTER" = "1" ]; then
  echo "  Överhoppad (se steg 3)."
else
  # Nollställ provet så att migrationsfilen blir komplett — taggaren hoppar
  # annars över de fem redan taggade verben och filen skulle sakna dem.
  sqlite3 sprak.db "DELETE FROM MönsterKrav; DELETE FROM Mönster;"
  ordbok tagga-monster --verbose || echo "  VARNING: mönstertaggningen gav fel, se ovan."
fi

steg "5. Granskning av alla böjningar (~500 anrop, 2–4 timmar)"

ordbok granska-former --alla-språk --rapport ordbok/granskning.tsv --fortsätt --verbose \
  || echo "  VARNING: granskningen avslutades med fel. Kör om skriptet — --fortsätt tar vid."

steg "6. Sammanfattning"

sqlite3 sprak.db "
  SELECT '  Mönster:          '||COUNT(*) FROM Mönster
  UNION ALL SELECT '  MönsterKrav:      '||COUNT(*) FROM MönsterKrav
  UNION ALL SELECT '  gradbarhet satt:  '||COUNT(*) FROM Koncept WHERE gradbarhet IS NOT NULL
  UNION ALL SELECT '  räknebar satt:    '||COUNT(*) FROM Koncept WHERE räknebar IS NOT NULL
  UNION ALL SELECT '  valens satt:      '||COUNT(*) FROM Koncept WHERE valens IS NOT NULL
  UNION ALL SELECT '  genus satt:       '||COUNT(*)||' av 3669' FROM Lexem WHERE genus IS NOT NULL
  UNION ALL SELECT '  prenominal satt:  '||COUNT(*) FROM Lexem WHERE prenominal IS NOT NULL;"

if [ -f ordbok/granskning.tsv ]; then
  echo "  Granskade avvikelser: $(($(wc -l < ordbok/granskning.tsv) - 1))"
  echo "    varav 'fel':        $(awk -F'\t' 'NR>1 && $8=="fel"' ordbok/granskning.tsv | wc -l | tr -d ' ')"
fi

steg "7. Skicka tillbaka"

git add -A ordbok/granskning.tsv ordbok/granskning.tsv.klara \
        ordbok/migrationer/ natt.log 2>/dev/null
if git diff --cached --quiet; then
  echo "  Inget nytt att committa."
else
  git commit -q -m "Nattkörning: granskning av böjningar + koncept- och mönstertaggning" \
    && git push -q origin main \
    && echo "  ✓ Pushat till origin/main." \
    || echo "  Kunde inte pusha automatiskt — kör 'git push' för hand imorgon."
fi

echo
echo "Klart $(date '+%Y-%m-%d %H:%M'). Hela loggen finns i $LOGG."
