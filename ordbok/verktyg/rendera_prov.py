"""Provkör den svenska renderaren brett mot databasen.

Två svep:

  GRAMMATISKT   Ett litet ordförråd, men ALLA kombinationer av bestämdhet,
                numerus, attribut, possessiv och tempus. Skrivs ut i sin
                helhet för genomläsning — det här är meningar en människa
                måste titta på, inte något som kan verifieras automatiskt.

  BRETT         Varje verb med objektsmönster, mot ett urval substantiv och
                adjektiv. Letar inte efter fula meningar utan efter krascher
                och saknade former: celler som är tomma, lexem utan genus,
                paradigm som inte går att slå upp.

Kör: python ordbok/verktyg/rendera_prov.py [--språk sv|de] [--alla]
"""
import sqlite3
import sys
from collections import Counter

from sprakprog.rendering import (
    Bestämdhet, FranskRenderare, ItalienskRenderare, Mening, Nominalfras,
    EngelskRenderare, JapanskRenderare, Numerus, RenderingsFel,
    SpanskRenderare, SvenskRenderare, Tidsreferens, TyskRenderare,
)

SPRÅK = "sv"
if "--språk" in sys.argv:
    SPRÅK = sys.argv[sys.argv.index("--språk") + 1]

conn = sqlite3.connect("sprak.db")
conn.row_factory = sqlite3.Row
r = {"sv": SvenskRenderare, "de": TyskRenderare, "fr": FranskRenderare,
     "es": SpanskRenderare, "it": ItalienskRenderare,
     "en": EngelskRenderare, "ja": JapanskRenderare}[SPRÅK](conn)


def koncept(ordklass, **filter):
    sql = """SELECT k.nyckel, l.lemma, l.genus FROM Lexem l
             JOIN Koncept k ON k.id = l.koncept_id
             WHERE l.språk = ? AND k.ordklass = ?"""
    param = [SPRÅK, ordklass]
    if "genus" in filter:
        sql += " AND l.genus = ?"
        param.append(filter["genus"])
    if filter.get("med_objekt"):
        sql += """ AND k.id IN (SELECT m.koncept_id FROM Mönster m
                   JOIN MönsterKrav mk ON mk.mönster_id = m.id
                   WHERE mk.slot = 'objekt' AND m.språk IS NULL)"""
    return conn.execute(sql + " ORDER BY k.nyckel", param).fetchall()


# ── svep 1: grammatiskt ──────────────────────────────────────────────
print("═" * 72)
print("GRAMMATISKT SVEP — samma ord, alla kombinationer")
print("═" * 72)

# Två substantiv med olika genus, där språket har genus alls. en och ja
# saknar det helt och får två godtyckliga ord i stället.
GENUS_2 = {"de": 3, "sv": 2, "fr": 2, "es": 2, "it": 2}
if SPRÅK in GENUS_2:
    utrum = koncept("Substantiv", genus=1)[0]
    neutrum = koncept("Substantiv", genus=GENUS_2[SPRÅK])[0]
else:
    utrum, neutrum = koncept("Substantiv")[:2]
subjekt = Nominalfras("pers_flicka", Bestämdhet.BESTÄMD)

rader = 0
for huvud in (utrum, neutrum):
    print(f"\n── {huvud['lemma']} (genus={huvud['genus']}) ──")
    for best in Bestämdhet:
        for num in Numerus:
            for attribut in ((), ("färg_röd",)):
                for poss in (None, "poss_3sg_fem"):
                    nf = Nominalfras(huvud["nyckel"], best, num, attribut, poss,
                                     possessiv_koreferent=poss is not None)
                    m = Mening("fys_ge", subjekt, objekt=nf,
                               tid=Tidsreferens.FÖRFLUTEN)
                    etikett = (f"{best.value[:6]:6} {num.value:2} "
                               f"{'+adj' if attribut else '    '} "
                               f"{'+poss' if poss else '     '}")
                    try:
                        print(f"  {etikett} → {r.rendera(m)}")
                    except RenderingsFel as e:
                        print(f"  {etikett} ✋ {e}")
                    rader += 1

print(f"\n── tempus ──")
for tid in Tidsreferens:
    m = Mening("fys_ge", subjekt, objekt=Nominalfras("skol_bok"),
               io=Nominalfras("fam_bror", possessiv="poss_3sg_fem",
                              possessiv_koreferent=True),
               adverbial=("adv_igår",), tid=tid)
    try:
        print(f"  {tid.value:10} → {r.rendera(m)}")
    except RenderingsFel as e:
        print(f"  {tid.value:10} ✋ {e}")

# ── svep 2: brett ────────────────────────────────────────────────────
print("\n" + "═" * 72)
print("BRETT SVEP — varje verb med objektsmönster mot hela substantivlistan")
print("═" * 72)

verb = koncept("Verb", med_objekt=True)
substantiv = koncept("Substantiv")
adjektiv = koncept("Adjektiv")
print(f"{len(verb)} verb × {len(substantiv)} substantiv, plus {len(adjektiv)} adjektiv\n")

fel = Counter()
exempelfel = {}
lyckade = misslyckade = 0
visa_alla = "--alla" in sys.argv

for v in verb:
    for s in substantiv:
        for best in (Bestämdhet.OBESTÄMD, Bestämdhet.BESTÄMD):
            m = Mening(v["nyckel"], subjekt,
                       objekt=Nominalfras(s["nyckel"], best),
                       tid=Tidsreferens.FÖRFLUTEN)
            try:
                mening = r.rendera(m)
                lyckade += 1
                if visa_alla:
                    print(" ", mening)
            except RenderingsFel as e:
                misslyckade += 1
                sort = str(e).split(":", 1)[-1].strip()[:60]
                fel[sort] += 1
                exempelfel.setdefault(sort, str(e))

# adjektivsvepet separat: varje adjektiv mot ett utrum- och ett neutrumord
for a in adjektiv:
    for s in (utrum, neutrum):
        for best in (Bestämdhet.OBESTÄMD, Bestämdhet.BESTÄMD):
            m = Mening("fys_ge", subjekt,
                       objekt=Nominalfras(s["nyckel"], best, attribut=(a["nyckel"],)),
                       tid=Tidsreferens.FÖRFLUTEN)
            try:
                mening = r.rendera(m)
                lyckade += 1
                if visa_alla:
                    print(" ", mening)
            except RenderingsFel as e:
                misslyckade += 1
                sort = str(e).split(":", 1)[-1].strip()[:60]
                fel[sort] += 1
                exempelfel.setdefault(sort, str(e))

print(f"lyckade   : {lyckade}")
print(f"misslyckade: {misslyckade}")
if fel:
    print("\nfelsorter:")
    for sort, n in fel.most_common():
        print(f"  {n:5}  {exempelfel[sort][:100]}")
