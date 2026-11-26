#!/usr/bin/env bash
#
# Nattkörning 2 — generera om de två trasiga jobben, granska resten.
#
#   ./kör_natt2.sh
#
# Bakgrund: nattkörning 1 rapporterade 2 088 fel. 568 av dem var falska —
# granskningens cellmatchning läste imperfekt konjunktiv ur presens
# konjunktivs cell, eftersom Imperf|Vol är en bitmässig supermängd av Vol.
# Rättat i granskning.py; spanskan visade sig ha 0,3 % fel och behöver
# INTE genereras om.
#
# Verklig felfrekvens per jobb:
#   de/Adjektiv    16,9 %  ← enda riktiga problemet
#   de/Verb         2,9 %
#   de/Substantiv   2,2 %
#   es/Verb         0,3 %
#   en/*            0,4 %
#
# Tyska adjektiv genereras därför om med en starkare modell, nu när
# ändelsetabellerna finns i instruktionen. Tyska verb följer med — de är
# billiga och felen där är systematiska (imperativens pronomen, konjunktiv
# II-omljud).

# Modellval. Nattkörning 1 gjorde ~388 opus-anrop innan kvoten tog slut.
# Natt 2 skulle bli ~400 med opus rakt igenom och ta slut på samma sätt.
# Därför: opus BARA till omgenereringen av tyska, som är den dyra biten
# kvalitetsmässigt (16,9 % fel). Granskningen går på sonnet — spanskan och
# engelskan låg på 0,3–0,4 % fel, så där behövs ingen tung modell.
#
# Vill du styra om: MODELL_GEN=... MODELL_GRANSK=... ./kör_natt2.sh
MODELL_GEN="${MODELL_GEN:-claude-opus-5}"
MODELL_GRANSK="${MODELL_GRANSK:-claude-sonnet-5}"

set -uo pipefail
cd "$(dirname "$0")"

LOGG="natt2.log"
exec > >(tee -a "$LOGG") 2>&1

steg() { echo; echo "═══════════════════════════════════════════════════"; echo "  $* — $(date '+%H:%M:%S')"; echo "═══════════════════════════════════════════════════"; }
fatal() { echo "AVBRYTER: $*" >&2; exit 1; }

steg "0. Förberedelser"

echo "  Generering: $MODELL_GEN     Granskning: $MODELL_GRANSK"

[ -n "${ANTHROPIC_API_KEY:-}" ] && fatal "ANTHROPIC_API_KEY är satt — ta bort den."
command -v claude >/dev/null || fatal "'claude' hittades inte."
[ -d .venv ] || fatal "Ingen .venv."
# shellcheck disable=SC1091
source .venv/bin/activate
git pull --ff-only || fatal "git pull misslyckades."

steg "1. Bygg om databasen"

ordbok import ordbok/nivålistor/bas_kärna.csv ordbok/nivålistor/grundord.csv --återinitiera || fatal "importen misslyckades"
for m in ordbok/migrationer/*.sql; do sqlite3 sprak.db < "$m" || fatal "migration $m misslyckades"; done
ordbok importera-former ordbok/former.tsv --ersätt || fatal "kunde inte läsa in former.tsv"
[ "$(sqlite3 sprak.db 'SELECT COUNT(*) FROM Koncept;')" = "733" ] || fatal "fel antal koncept."
echo "  Former: $(sqlite3 sprak.db 'SELECT COUNT(*) FROM Former;')"

steg "2. Generera om de/Adjektiv med starkare modell (~55 anrop)"

# 16,9 % fel med haiku. Instruktionen har nu de fullständiga
# ändelsetabellerna; kombinationen med en starkare modell ska ta ner det.
# Utan --fortsätt: formerna SKA skrivas över.
ordbok generera --språk de --ordklass Adjektiv --modell "$MODELL_GEN" --verbose \
  || echo "  VARNING: se ovan."

steg "3. Generera om de/Verb (~20 anrop)"

ordbok generera --språk de --ordklass Verb --modell "$MODELL_GEN" --verbose \
  || echo "  VARNING: se ovan."

echo
echo "  Kontroll — stark dativ mask komparativ, ska sluta på -em:"
sqlite3 sprak.db "
  SELECT '    '||l.lemma||' → '||f.form
  FROM Former f JOIN Lexem l ON l.id=f.lexem_id
  WHERE l.lemma IN ('blau','alt','durstig') AND l.språk='de'
    AND f.grad=2 AND f.species=1 AND f.genus=1 AND f.kasus=4;"

steg "4. Granska resten (~300 anrop, 2–3 timmar)"

# Kvittofilen granskning.tsv.klara säger vad som redan är gjort. De tyska
# lexem som just genererats om plockas bort ur den, så att de granskas på
# nytt.
sqlite3 -separator $'\t' sprak.db "
  SELECT DISTINCT 'de', l.lemma FROM Lexem l JOIN Koncept k ON k.id=l.koncept_id
  WHERE l.språk='de' AND k.ordklass IN ('Adjektiv','Verb');" > /tmp/omgjorda.tsv
grep -vxF -f /tmp/omgjorda.tsv ordbok/granskning.tsv.klara > /tmp/klara.ny || true
mv /tmp/klara.ny ordbok/granskning.tsv.klara
echo "  kvitterade kvar: $(wc -l < ordbok/granskning.tsv.klara)"

ordbok granska-former --alla-språk --rapport ordbok/granskning.tsv --fortsätt \
  --modell "$MODELL_GRANSK" --verbose \
  || echo "  Granskningen avbröts (troligen slut på kvot). Allt färdigt är
  sparat — kör skriptet igen i morgon natt, det tar vid där det slutade."

steg "5. Rensa inaktuella rader ur rapporten"

# En rad är inaktuell om "nuvarande" inte längre stämmer med vad databasen
# innehåller — antingen för att formen genererats om, eller för att raden
# var en falsk träff från den gamla cellmatchningen. Självkorrigerande:
# behöver ingen lista över vilka jobb som gjorts om.
python3 - <<'PY'
import csv, pathlib, sqlite3, sys
sys.path.insert(0, "src")
from sprakprog.generering.granskning import _former_per_cell
from sprakprog.kaikki_mappning.paradigm import ladda_slot, ladda_legend

lg = ladda_legend()
con = sqlite3.connect("sprak.db"); con.row_factory = sqlite3.Row
p = pathlib.Path("ordbok/granskning.tsv")
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

echo "  Kvar att granska: $(python3 -c "
import sqlite3,pathlib
k=set()
f=pathlib.Path('ordbok/granskning.tsv.klara')
if f.exists():
    k={tuple(r.split(chr(9))) for r in f.read_text().splitlines() if chr(9) in r}
c=sqlite3.connect('sprak.db')
n=c.execute('''select count(*) from Lexem l join Koncept k on k.id=l.koncept_id
  where k.ordklass in ('Verb','Substantiv','Adjektiv','Pronomen','Possessiv','Frågepronomen')''').fetchone()[0]
print(n-len(k))")"
awk -F'\t' 'NR>1{n[$8]++} END{for(x in n) printf "  %-8s %d\n", x, n[x]}' ordbok/granskning.tsv
echo "  per språk (fel):"
awk -F'\t' 'NR>1 && $8=="fel"{n[$1]++} END{for(x in n) printf "    %s  %d\n", x, n[x]}' ordbok/granskning.tsv | sort

steg "7. Skicka tillbaka"

ordbok exportera-former ordbok/former.tsv
git add -A ordbok/former.tsv ordbok/granskning.tsv ordbok/granskning.tsv.klara natt2.log 2>/dev/null
if git diff --cached --quiet; then
  echo "  Inget nytt att committa."
else
  git commit -q -m "Nattkörning 2: omgenererade de/Adjektiv och de/Verb, granskning av resten" \
    && git push -q origin main && echo "  ✓ Pushat." \
    || echo "  Kunde inte pusha — kör 'git push' för hand."
fi

echo
echo "Klart $(date '+%Y-%m-%d %H:%M'). Logg: $LOGG"
