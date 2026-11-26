#!/usr/bin/env bash
#
# Nattkörning 2 — generera om tyska, granska resten.
#
#   ./kör_natt2.sh
#
# Starta en gång och låt det gå. Tar kvoten slut väntar skriptet ut den och
# fortsätter av sig självt — ingen schemaläggning behövs.
#
# Ctrl-C när som helst är ofarligt. Varje fas kvitteras i .natt2_status och
# granskningen kvitterar varje granskat lexem, så en omstart med exakt samma
# kommando tar vid där den slutade. Ingenting görs om.
#
# Slutkoder:
#   0   allt klart
#   75  gav upp efter DEADLINE_TIMMAR — starta om när kvoten är tillbaka
#   1   något gick fel som inte löser sig av att vänta
#
# ── Bakgrund ────────────────────────────────────────────────────────────
# Nattkörning 1 rapporterade 2 088 fel. 568 var falska — granskningens
# cellmatchning läste imperfekt konjunktiv ur presens konjunktivs cell.
# Rättat. Verklig felfrekvens:
#   de/Adjektiv 16,9 %  ← enda riktiga problemet
#   de/Verb 2,9 %   de/Substantiv 2,2 %   es/Verb 0,3 %   en/* 0,4 %
# Spanskan behöver alltså inte genereras om.

MODELL_GEN="${MODELL_GEN:-claude-opus-5}"
MODELL_GRANSK="${MODELL_GRANSK:-claude-sonnet-5}"
# Kvoten återställs i ett rullande fönster, så det räcker att vänta ut den.
# Skriptet försöker om och om igen tills allt är klart, eller tills
# DEADLINE_TIMMAR passerat sedan starten.
VANTAN="${VANTAN:-1800}"                    # sekunder mellan försök (30 min)
DEADLINE_TIMMAR="${DEADLINE_TIMMAR:-10}"    # ge upp efter så här länge

set -uo pipefail
cd "$(dirname "$0")"

LOGG="natt2.log"
STATUS=".natt2_status"
exec > >(tee -a "$LOGG") 2>&1
touch "$STATUS"

steg()  { echo; echo "═══════════════════════════════════════════════════"; echo "  $* — $(date '+%H:%M:%S')"; echo "═══════════════════════════════════════════════════"; }
fatal() { echo "AVBRYTER: $*" >&2; exit 1; }
klar()  { grep -qxF "$1" "$STATUS"; }
kvittera() { echo "$1" >> "$STATUS"; }

SLUTTID=$(( $(date +%s) + DEADLINE_TIMMAR * 3600 ))

# Kör ett kommando och vänta ut kvoten om det misslyckas. Returnerar 0 när
# kommandot lyckats, 1 om deadline passerats. Ctrl-C under sleep avbryter
# hela skriptet, vilket är precis vad man vill.
med_vantan() {
  local vad="$1"; shift
  local n=0
  while true; do
    n=$((n + 1))
    [ "$n" -gt 1 ] && echo "  → $vad, försök $n — $(date '+%H:%M')"
    if "$@"; then return 0; fi
    if [ "$(date +%s)" -ge "$SLUTTID" ]; then
      echo "  $vad: ger upp, ${DEADLINE_TIMMAR} timmar har gått sedan start."
      return 1
    fi
    echo "  $vad avbröts — troligen slut på kvot."
    echo "    Väntar $((VANTAN / 60)) min och försöker igen. Ctrl-C när du vill."
    sleep "$VANTAN"
  done
}

steg "0. Förberedelser"
echo "  Generering: $MODELL_GEN     Granskning: $MODELL_GRANSK"
echo "  Redan klart: $(tr '\n' ' ' < "$STATUS")"

[ -n "${ANTHROPIC_API_KEY:-}" ] && fatal "ANTHROPIC_API_KEY är satt — ta bort den."
command -v claude >/dev/null || fatal "'claude' hittades inte."
[ -d .venv ] || fatal "Ingen .venv."
# shellcheck disable=SC1091
source .venv/bin/activate
git pull --ff-only || fatal "git pull misslyckades."

steg "1. Bygg om databasen"

# Deterministiskt och billigt — körs varje gång. former.tsv i git är facit,
# så inget går förlorat. OBS ordningen: exportera-former i steg 7 skriver
# tillbaka det som genererats om, så nästa körning läser in de nya formerna.
ordbok import ordbok/nivålistor/bas_kärna.csv ordbok/nivålistor/grundord.csv --återinitiera || fatal "importen misslyckades"
for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m" || fatal "migration $m misslyckades"; done
ordbok importera-former ordbok/former.tsv --ersätt || fatal "kunde inte läsa in former.tsv"
[ "$(sqlite3 sprak.db 'SELECT COUNT(*) FROM Koncept;')" = "733" ] || fatal "fel antal koncept."
echo "  Former: $(sqlite3 sprak.db 'SELECT COUNT(*) FROM Former;')"

steg "2. Generera om de/Adjektiv (~55 anrop)"

if klar de_adjektiv; then
  echo "  Redan gjort i en tidigare körning."
else
  # 16,9 % fel med haiku. Instruktionen har nu de fullständiga
  # ändelsetabellerna. Utan --fortsätt: formerna SKA skrivas över.
  if med_vantan "de/Adjektiv" ordbok generera --språk de --ordklass Adjektiv \
       --modell "$MODELL_GEN" --verbose; then
    kvittera de_adjektiv
  fi
fi

steg "3. Generera om de/Verb (~20 anrop)"

if klar de_verb; then
  echo "  Redan gjort i en tidigare körning."
else
  if med_vantan "de/Verb" ordbok generera --språk de --ordklass Verb \
       --modell "$MODELL_GEN" --verbose; then
    kvittera de_verb
  fi
fi

if klar de_adjektiv; then
  echo
  echo "  Kontroll — stark dativ mask komparativ ska sluta på -em:"
  sqlite3 sprak.db "
    SELECT '    '||l.lemma||' → '||f.form
    FROM Former f JOIN Lexem l ON l.id=f.lexem_id
    WHERE l.lemma IN ('blau','alt','durstig') AND l.språk='de'
      AND f.grad=2 AND f.species=1 AND f.genus=1 AND f.kasus=4;"
fi

steg "4. Granska resten"

# De omgenererade tyska lexemen plockas ur kvittofilen EN gång, så att de
# granskas på nytt. Görs det vid varje körning skulle de granskas om i
# all oändlighet.
if ! klar kvitto_rensad && klar de_adjektiv && klar de_verb; then
  sqlite3 -separator $'\t' sprak.db "
    SELECT DISTINCT 'de', l.lemma FROM Lexem l JOIN Koncept k ON k.id=l.koncept_id
    WHERE l.språk='de' AND k.ordklass IN ('Adjektiv','Verb');" > /tmp/omgjorda.tsv
  if [ -f ordbok/granskning.tsv.klara ]; then
    grep -vxF -f /tmp/omgjorda.tsv ordbok/granskning.tsv.klara > /tmp/klara.ny || true
    mv /tmp/klara.ny ordbok/granskning.tsv.klara
  fi
  kvittera kvitto_rensad
  echo "  Kvittofilen rensad från omgenererade tyska lexem."
fi

GRANSKNING_KLAR=0
if klar granskning; then
  echo "  Redan klar i en tidigare körning."
  GRANSKNING_KLAR=1
else
  if med_vantan "Granskningen" ordbok granska-former --alla-språk \
       --rapport ordbok/granskning.tsv --fortsätt \
       --modell "$MODELL_GRANSK" --verbose; then
    kvittera granskning
    GRANSKNING_KLAR=1
  fi
fi

steg "5. Rensa inaktuella rader ur rapporten"

# En rad är inaktuell om "nuvarande" inte längre stämmer med databasen —
# antingen för att formen genererats om, eller för att den var en falsk
# träff från den gamla cellmatchningen. Självkorrigerande.
python3 - <<'PY'
import csv, pathlib, sqlite3, sys
sys.path.insert(0, "src")
from sprakprog.generering.granskning import _former_per_cell
from sprakprog.kaikki_mappning.paradigm import ladda_slot, ladda_legend

p = pathlib.Path("ordbok/granskning.tsv")
if not p.exists():
    print("  Ingen rapport än."); raise SystemExit
lg = ladda_legend()
con = sqlite3.connect("sprak.db"); con.row_factory = sqlite3.Row
rader = list(csv.DictReader(p.open(encoding="utf-8"), delimiter="\t"))
cache, kvar = {}, []
for r in rader:
    n = (r["språk"], r["ordklass"], r["lemma"])
    if n not in cache:
        f = con.execute("""SELECT f.* FROM Former f JOIN Lexem l ON l.id=f.lexem_id
                           WHERE l.lemma=? AND l.språk=?""", (r["lemma"], r["språk"])).fetchall()
        cache[n] = _former_per_cell(f, ladda_slot(r["språk"], r["ordklass"], legend=lg))
    if cache[n].get(r["cell"], "") == r["nuvarande"]:
        kvar.append(r)
with p.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rader[0].keys(), delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(kvar)
print(f"  {len(rader)} rader → {len(kvar)} aktuella")
PY

steg "6. Sammanfattning"

KVAR=$(python3 -c "
import sqlite3, pathlib
f = pathlib.Path('ordbok/granskning.tsv.klara')
k = len([r for r in f.read_text().splitlines() if chr(9) in r]) if f.exists() else 0
c = sqlite3.connect('sprak.db')
n = c.execute('''SELECT COUNT(*) FROM Lexem l JOIN Koncept k ON k.id=l.koncept_id
  WHERE k.ordklass IN ('Verb','Substantiv','Adjektiv','Pronomen','Possessiv','Frågepronomen')''').fetchone()[0]
print(max(0, n - k))")
echo "  Kvar att granska: $KVAR lexem"
[ -f ordbok/granskning.tsv ] && awk -F'\t' 'NR>1 && $8=="fel"{n[$1]++} END{for(x in n) printf "  fel i %s: %d\n", x, n[x]}' ordbok/granskning.tsv | sort

steg "7. Skicka tillbaka"

ordbok exportera-former ordbok/former.tsv
git add -A ordbok/former.tsv ordbok/granskning.tsv ordbok/granskning.tsv.klara natt2.log 2>/dev/null
if git diff --cached --quiet; then
  echo "  Inget nytt att committa."
else
  git commit -q -m "Nattkörning 2: omgenererade de/Adjektiv och de/Verb, granskning" \
    && git push -q origin main && echo "  ✓ Pushat." \
    || echo "  Kunde inte pusha — kör 'git push' för hand."
fi

echo
if klar de_adjektiv && klar de_verb && [ "$GRANSKNING_KLAR" = "1" ]; then
  echo "ALLT KLART $(date '+%Y-%m-%d %H:%M')."
  exit 0
fi
echo "MER ÅTERSTÅR — starta om skriptet med samma kommando när kvoten är"
echo "tillbaka. Det tar vid där det slutade. $(date '+%H:%M')"
exit 75
