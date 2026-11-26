"""Hur många `oregelbunden`-kort blir det, och hur svänger talet med
granulariteten?

Regelbunden definieras av klassens EGEN majoritet: för varje (språk, ordklass,
klass, cell) är den regelbundna stammen lemmat avkortat med det antal tecken
som flest lexem i klassen använder. Ett lexem är oregelbundet i cellen när dess
stam avviker. Definitionen kräver ingen handskriven regel per språk.
"""
import csv, sqlite3, collections, sys

STAMMAR = "ordbok/stammar.tsv"

lemma: dict[tuple[str, str, str], str] = {}
s = sqlite3.connect("sprak.db")
for språk, nyckel, lem, var in s.execute(
    "select l.språk, k.nyckel, l.lemma, coalesce(l.variant,'')"
    " from Lexem l join Koncept k on k.id=l.koncept_id"
):
    lemma[(språk, nyckel, var)] = lem

rader = list(csv.DictReader(open(STAMMAR, encoding="utf-8"), delimiter="\t"))

# En rad i stammar.tsv = en stam som bär flera celler. Platta ut till celler.
celler: list[tuple] = []   # (språk, ordklass, klass, nyckel, variant, cell, stam)
utan_lemma = collections.Counter()
for r in rader:
    nyckel = (r["språk"], r["koncept"], r["variant"])
    lem = lemma.get(nyckel)
    if lem is None:
        utan_lemma[r["språk"]] += 1
        continue
    for c in r["celler"].split(","):
        celler.append((r["språk"], r["ordklass"], r["klass"],
                       r["koncept"], r["variant"], c, r["form"]))

# Klassens majoritetsavkortning per cell.
avkortning: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
for språk, ordklass, klass, nyckel, variant, cell, stam in celler:
    lem = lemma[(språk, nyckel, variant)]
    if lem.startswith(stam):
        avkortning[(språk, ordklass, klass, cell)][len(lem) - len(stam)] += 1
    else:
        avkortning[(språk, ordklass, klass, cell)][None] += 1

modal = {k: v.most_common(1)[0][0] for k, v in avkortning.items()}

def regelbunden(språk, ordklass, klass, nyckel, variant, cell, stam) -> bool:
    k = modal.get((språk, ordklass, klass, cell))
    if k is None:
        return False           # klassen har ingen gemensam avkortning
    lem = lemma[(språk, nyckel, variant)]
    return k <= len(lem) and stam == lem[: len(lem) - k]

# Tre granulariteter.
per_form = collections.Counter();  per_form_tot = collections.Counter()
per_grupp = collections.Counter(); per_grupp_tot = collections.Counter()
per_tempus: dict[str, set] = collections.defaultdict(set)
per_tempus_tot: dict[str, set] = collections.defaultdict(set)

# per stamgrupp: en rad i stammar.tsv är redan gruppen.
for r in rader:
    nyckel = (r["språk"], r["koncept"], r["variant"])
    if nyckel not in lemma:
        continue
    cs = r["celler"].split(",")
    oreg = any(
        not regelbunden(r["språk"], r["ordklass"], r["klass"],
                        r["koncept"], r["variant"], c, r["form"])
        for c in cs
    )
    per_grupp_tot[r["språk"]] += 1
    if oreg:
        per_grupp[r["språk"]] += 1

for språk, ordklass, klass, nyckel, variant, cell, stam in celler:
    ok = regelbunden(språk, ordklass, klass, nyckel, variant, cell, stam)
    per_form_tot[språk] += 1
    dim = cell.split("_")[0]
    per_tempus_tot[språk].add((nyckel, variant, dim))
    if not ok:
        per_form[språk] += 1
        per_tempus[språk].add((nyckel, variant, dim))

print(f"{'språk':6}{'per form':>22}{'per stamgrupp':>20}{'per (ord × dim)':>20}")
for sp in sorted(per_form_tot):
    print(f"{sp:6}"
          f"{per_form[sp]:>10} / {per_form_tot[sp]:<9}"
          f"{per_grupp[sp]:>8} / {per_grupp_tot[sp]:<9}"
          f"{len(per_tempus[sp]):>9} / {len(per_tempus_tot[sp]):<9}")
if utan_lemma:
    print("\nrader utan lemma:", dict(utan_lemma))

# Hur många lexem är HELT regelbundna — inget oregelbundet kort alls?
helt = collections.Counter(); alla = collections.Counter()
brutna = collections.defaultdict(set)
for språk, ordklass, klass, nyckel, variant, cell, stam in celler:
    alla[(språk, ordklass)] and None
    if not regelbunden(språk, ordklass, klass, nyckel, variant, cell, stam):
        brutna[(språk, ordklass)].add((nyckel, variant))
lexem = collections.defaultdict(set)
for språk, ordklass, klass, nyckel, variant, cell, stam in celler:
    lexem[(språk, ordklass)].add((nyckel, variant))
print()
print(f"{'språk':6}{'ordklass':14}{'lexem':>7}{'helt regelbundna':>19}")
for k in sorted(lexem):
    if k[0] not in ("fr", "de", "ja", "en"):
        continue
    n = len(lexem[k]); b = len(brutna.get(k, ()))
    print(f"{k[0]:6}{k[1]:14}{n:>7}{n-b:>13} ({100*(n-b)/n:.0f} %)")
