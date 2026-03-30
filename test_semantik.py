"""
Temporärt testprogram för semantisk meningsgenerering.

Genererar meningar automatiskt genom att:
1. Slumpa en grammatisk struktur (antal_delar styr komplexiteten)
2. Fylla i ord uppifrån-ner i beroendeordning med semantiska krav
3. Rendera och printa resultatet

Kör med:  python test_semantik.py [antal_delar] [antal_meningar] [språk]
          python test_semantik.py 4 10 sv
"""

import sqlite3
import random
import sys

from fraser import Sats, Verbfras, Nominalfras, Adjektivfras, Prepositionsfras
from ordklasser import Substantiv, Pronomen, Verb, Adjektiv, Preposition
from renderare import rendera_sats
from bitflaggor import Valens, Personlighet, Species, Numerus, Tempus, Kasus, Semantik, Genus, Grad
from ordbokläsare import hämta_lexem_id, kolla_lexems_egenskap

db = sqlite3.connect("ordbok/sprak.db")


# ── DB-hjälpfunktioner ──────────────────────────────────────────────

def slumpa_koncept(ordklass, tagg=None):
    """Returnerar (koncept_id, namn) eller None."""
    if tagg:
        rad = db.execute(
            "SELECT id, namn FROM Koncept WHERE ordklass = ? AND semantik & ? ORDER BY RANDOM() LIMIT 1",
            (ordklass, int(tagg))
        ).fetchone()
        return rad  # None om inget matchar
    return db.execute(
        "SELECT id, namn FROM Koncept WHERE ordklass = ? ORDER BY RANDOM() LIMIT 1",
        (ordklass,)
    ).fetchone()


def hämta_mönster_krav(verb_koncept_id, språk):
    """Returnerar dict: slot → tagg (int) för ett slumpmässigt mönster, eller {}."""
    mönster = db.execute(
        "SELECT id FROM Mönster WHERE koncept_id = ? AND (språk IS NULL OR språk = ?) ORDER BY RANDOM() LIMIT 1",
        (verb_koncept_id, språk)
    ).fetchone()
    if not mönster:
        return {}
    krav = {}
    for slot, tagg, koncept_id in db.execute(
        "SELECT slot, tagg, koncept_id FROM MönsterKrav WHERE mönster_id = ?",
        (mönster[0],)
    ).fetchall():
        krav[slot] = (tagg, koncept_id)
    return krav


# ── Byggfunktioner ──────────────────────────────────────────────────

def bygg_nominalfras_substantiv(koncept_id):
    """Bygger en Nominalfras med ett substantiv."""
    nf = Nominalfras()
    nf.huvuddel = Substantiv(koncept_id)
    nf.numerus = random.choice([Numerus.SINGULAR, Numerus.PLURAL])
    nf.species = random.choice([Species.OBESTAMD, Species.BESTAMD])
    return nf


def bygg_nominalfras_pronomen(koncept_id):
    """Bygger en Nominalfras med ett pronomen."""
    nf = Nominalfras()
    nf.huvuddel = Pronomen(koncept_id)
    return nf


def välj_subjekt(krav, logg):
    """Väljer ett koncept för subjektsloten. Returnerar (Nominalfras, namn) eller (None, felmeddelande)."""
    tagg = krav.get('subjekt', (None, None))[0]

    # Försök substantiv, sedan pronomen
    for ordklass, byggare in [('Substantiv', bygg_nominalfras_substantiv),
                               ('Pronomen',  bygg_nominalfras_pronomen)]:
        koncept = slumpa_koncept(ordklass, tagg)
        if koncept:
            nf = byggare(koncept[0])
            nf.kasus = Kasus.NOMINATIV
            tagg_info = f" [krav: {Semantik(tagg)}]" if tagg else ""
            logg.append(f"  Subjekt: {koncept[1]} ({ordklass}){tagg_info}")
            return nf

    # Inget matchade med tagg — prova utan
    if tagg:
        koncept = slumpa_koncept('Substantiv')
        if koncept:
            logg.append(f"  ⚠ Subjekt: {koncept[1]} (fritt val — inga {Semantik(tagg)}-substantiv hittades)")
            nf = bygg_nominalfras_substantiv(koncept[0])
            nf.kasus = Kasus.NOMINATIV
            return nf

    logg.append("  ⚠ Kunde inte hitta subjekt!")
    return None


def välj_objekt(slot_namn, krav_nyckel, krav, logg):
    """Väljer ett koncept för en objektslot. Returnerar Nominalfras eller None."""
    tagg = krav.get(krav_nyckel, (None, None))[0]

    koncept = slumpa_koncept('Substantiv', tagg)
    if not koncept and tagg:
        logg.append(f"  ⚠ {slot_namn}: SKIPPAS — inga Substantiv med {Semantik(tagg)} finns i ordboken")
        return None

    if not koncept:
        koncept = slumpa_koncept('Substantiv')

    if koncept:
        nf = bygg_nominalfras_substantiv(koncept[0])
        tagg_info = f" [krav: {Semantik(tagg)}]" if tagg else ""
        logg.append(f"  {slot_namn}: {koncept[1]}{tagg_info}")
        return nf

    logg.append(f"  ⚠ Kunde inte hitta {slot_namn}!")
    return None


def lägg_till_adjektiv(nf: Nominalfras, slot_namn: str, logg) -> bool:
    """Lägger till ett slumpmässigt adjektiv på en nominalfras. Returnerar True om lyckat."""
    koncept = slumpa_koncept('Adjektiv')
    if not koncept:
        return False
    af = Adjektivfras()
    af.adjektiv = Adjektiv(koncept[0])
    af.grad = Grad.POSITIV
    nf.attribut = af
    logg.append(f"  Adjektiv på {slot_namn}: {koncept[1]}")
    return True


def välj_adverbial_prepositionsfras(verb_koncept_id, logg):
    """Bygger en prepositionsfras med semantiska krav. Returnerar Prepositionsfras eller None.

    Kontrollerar att riktningsprepositioner (till, från) bara kombineras med rörelseverb.
    """
    # Kolla om verbet har RÖRELSE-tagg
    verb_semantik = db.execute(
        "SELECT semantik FROM Koncept WHERE id = ?", (verb_koncept_id,)
    ).fetchone()[0] or 0
    verb_har_rörelse = verb_semantik & int(Semantik.RÖRELSE)

    # Filtrera prepositioner: riktningsprepositioner bara med rörelseverb
    if verb_har_rörelse:
        prep_koncept = slumpa_koncept('Preposition')
    else:
        # Exkludera riktningsprepositioner
        rad = db.execute(
            "SELECT id, namn FROM Koncept WHERE ordklass = 'Preposition' "
            "AND (semantik IS NULL OR NOT (semantik & ?)) ORDER BY RANDOM() LIMIT 1",
            (int(Semantik.RIKTNING),)
        ).fetchone()
        prep_koncept = rad

    if not prep_koncept:
        logg.append(f"  ⚠ Adverbial: SKIPPAS — ingen passande preposition")
        return None

    pf = Prepositionsfras()
    pf.preposition = Preposition(prep_koncept[0])

    # Kolla om prepositionen har egna krav
    prep_krav = hämta_mönster_krav(prep_koncept[0], 'sv')
    komp_tagg = prep_krav.get('komplement', (None, None))[0]

    koncept = slumpa_koncept('Substantiv', komp_tagg)
    if not koncept and komp_tagg:
        logg.append(f"  ⚠ Prep.komplement: inga Substantiv med {Semantik(komp_tagg)} — väljer fritt")
        koncept = slumpa_koncept('Substantiv')

    if koncept:
        nf = bygg_nominalfras_substantiv(koncept[0])
        pf.komplementfras = nf
        tagg_info = f" [krav: {Semantik(komp_tagg)}]" if komp_tagg else ""
        logg.append(f"  Adverbial: {prep_koncept[1]} + {koncept[1]}{tagg_info}")
        return pf

    return None


# ── Huvudfunktion ───────────────────────────────────────────────────

def generera_mening(antal_delar=3, språk='sv'):
    """Genererar en semantiskt korrekt mening.

    antal_delar styr hur många grammatiska delar som byggs:
      1 = bara verb (+ obligatoriskt subjekt)
      2 = + objekt (om transitivt) eller adverbial
      3 = + ytterligare slot
      ...

    språk kan vara en sträng ('sv') eller en lista (['sv', 'fr']) för att
    rendera samma grammatikobjekt till flera språk.
    """
    render_språk = språk if isinstance(språk, list) else [språk]
    bygg_språk = render_språk[0]  # använd första språket för mönster/valens-sökning

    logg = []

    # ── 1. Verb ──────────────────────────────────────────────
    verb_rad = db.execute(
        "SELECT id, namn FROM Koncept WHERE ordklass = 'Verb' ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    verb_koncept_id, verb_namn = verb_rad

    lexem_id = hämta_lexem_id(verb_koncept_id, bygg_språk)
    valens = Valens(int(kolla_lexems_egenskap(lexem_id, 'valens') or 0))
    personlighet = Personlighet(int(kolla_lexems_egenskap(lexem_id, 'personlighet') or 0))

    krav = hämta_mönster_krav(verb_koncept_id, bygg_språk)

    logg.append(f"Verb: {verb_namn}  valens={valens!r}  personlighet={personlighet!r}")
    if krav:
        krav_str = ", ".join(f"{s}: {Semantik(t) if t else f'koncept={k}'}" for s, (t, k) in krav.items())
        logg.append(f"  Mönster: {krav_str}")
    else:
        logg.append(f"  Inga mönsterkrav")

    # ── Bygg sats ────────────────────────────────────────────
    sats = Sats()
    sats.predikatfras = Verbfras(sats)
    vf = sats.predikatfras
    vf.verb = Verb(verb_koncept_id)
    vf.tempus = random.choice([Tempus.PRESENS, Tempus.PRETERITUM])

    delar_kvar = antal_delar - 1  # verbet tog en del

    # ── 2. Subjekt (obligatoriskt om personligt) ─────────────
    if Personlighet.OPERSONLIG in personlighet:
        logg.append("  Opersonligt — inget subjekt")
    else:
        nf = välj_subjekt(krav, logg)
        if nf:
            vf.subjektfras = nf
        delar_kvar -= 1

    # ── 3. Möjliga slots att fylla ───────────────────────────
    möjliga_slots = []

    if Valens.TRANSITIV in valens or Valens.DITRANSITIV in valens:
        möjliga_slots.append('direktobjekt')
    if Valens.DITRANSITIV in valens:
        möjliga_slots.append('indirektobjekt')
    möjliga_slots.append('adverbial_prep')
    # Adjektiv-slots — läggs till flera gånger för att kunna slumpas in
    möjliga_slots += ['adj_subjekt', 'adj_objekt', 'adj_io', 'adj_prep_komplement']

    random.shuffle(möjliga_slots)

    for slot in möjliga_slots:
        if delar_kvar <= 0:
            break

        if slot == 'direktobjekt' and not vf.direktobjektfras:
            nf = välj_objekt("Direkt objekt", "objekt", krav, logg)
            if nf:
                nf.kasus = Kasus.ACKUSATIV
                vf.direktobjektfras = nf
                delar_kvar -= 1

        elif slot == 'indirektobjekt' and not vf.indirektobjektfras:
            nf = välj_objekt("Indirekt objekt", "io", krav, logg)
            if nf:
                nf.kasus = Kasus.DATIV
                vf.indirektobjektfras = nf
                delar_kvar -= 1

        elif slot == 'adverbial_prep':
            pf = välj_adverbial_prepositionsfras(verb_koncept_id, logg)
            if pf:
                sats.adverbial.append(pf)
                delar_kvar -= 1

        elif slot == 'adj_subjekt':
            nf = vf.subjektfras if isinstance(vf.subjektfras, Nominalfras) else None
            if nf and isinstance(nf.huvuddel, Substantiv) and not nf.attribut:
                adj = lägg_till_adjektiv(nf, "Subjekt", logg)
                if adj:
                    delar_kvar -= 1

        elif slot == 'adj_objekt':
            nf = vf.direktobjektfras if isinstance(vf.direktobjektfras, Nominalfras) else None
            if nf and isinstance(nf.huvuddel, Substantiv) and not nf.attribut:
                adj = lägg_till_adjektiv(nf, "Direkt objekt", logg)
                if adj:
                    delar_kvar -= 1

        elif slot == 'adj_io':
            nf = vf.indirektobjektfras if isinstance(vf.indirektobjektfras, Nominalfras) else None
            if nf and isinstance(nf.huvuddel, Substantiv) and not nf.attribut:
                adj = lägg_till_adjektiv(nf, "Indirekt objekt", logg)
                if adj:
                    delar_kvar -= 1

        elif slot == 'adj_prep_komplement':
            # Adjektiv på första prepositionsfrasens komplement
            pf = next((a for a in sats.adverbial if isinstance(a, Prepositionsfras)), None)
            if pf and isinstance(pf.komplementfras, Nominalfras):
                nf = pf.komplementfras
                if isinstance(nf.huvuddel, Substantiv) and not nf.attribut:
                    adj = lägg_till_adjektiv(nf, "Prep.komplement", logg)
                    if adj:
                        delar_kvar -= 1

    # ── 4. Rendera ───────────────────────────────────────────
    print("\n".join(logg))
    for s in språk if isinstance(språk, list) else [språk]:
        try:
            mening = rendera_sats(sats, s)
            print(f"  {s} → {mening}")
        except Exception as e:
            print(f"  {s} ⚠ Renderingsfel: {e}")
    print()


# ── Körning ─────────────────────────────────────────────────────────

if __name__ == '__main__':
    antal_delar    = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    antal_meningar = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    print("=" * 60)
    print(f"SEMANTISK MENINGSGENERATOR — {antal_meningar} meningar, {antal_delar} delar")
    print("=" * 60)

    for i in range(antal_meningar):
        print(f"\n── Mening {i+1} ──────────────────────────────────")
        generera_mening(antal_delar=antal_delar, språk=['sv', 'fr'])
