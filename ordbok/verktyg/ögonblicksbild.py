"""Ta en ögonblicksbild av cell → form för varje lexem.

Används före och efter tillämpa-granskning för att se exakt vad som ändrades,
i stället för att lita på statistikraderna (ÖVERLÄMNING.md: tre buggar under
förra sessionen rapporterade '0 saknade, 0 tomma' och såg lyckade ut).
"""
import json
import sqlite3
import sys

from sprakprog.generering.granskning import _former_per_cell
from sprakprog.kaikki_mappning.paradigm import ladda_legend, ladda_slot

conn = sqlite3.connect("sprak.db")
conn.row_factory = sqlite3.Row
legend = ladda_legend()

lexem = conn.execute(
    """SELECT l.id, l.språk, l.lemma, k.ordklass, k.nyckel
       FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id"""
).fetchall()

slotcache = {}
ut = {}
for lx in lexem:
    nyckel = (lx["språk"], lx["ordklass"])
    if nyckel not in slotcache:
        try:
            slotcache[nyckel] = ladda_slot(lx["språk"], lx["ordklass"], legend=legend)
        except FileNotFoundError:
            slotcache[nyckel] = None
    slot = slotcache[nyckel]
    if slot is None:
        continue
    rader = conn.execute("SELECT * FROM Former WHERE lexem_id = ?", (lx["id"],)).fetchall()
    ident = f'{lx["språk"]}/{lx["nyckel"]}/{lx["lemma"]}'
    ut[ident] = _former_per_cell(rader, slot)

json.dump(ut, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
tomma = sum(1 for c in ut.values() for v in c.values() if not v)
fyllda = sum(1 for c in ut.values() for v in c.values() if v)
print(f"{len(ut)} lexem, {fyllda} fyllda celler, {tomma} tomma celler → {sys.argv[1]}")
