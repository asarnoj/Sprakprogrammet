"""Mät hur stor del av formbeståndet dagens `Mening` kan nå.

Metod: instrumentera Uppslag.form så varje begärd (ordklass, cell) loggas,
svep sedan en bred korsprodukt av specifikationer. Unionen av begärda celler
per ordklass är det renderaren KAN be om. Räkna till sist, över hela
språkets lexikon, hur många ifyllda celler som ligger i den mängden.

Cellmängden per ordklass är densamma för alla lexem i klassen, så några få
sondord räcker för att kartlägga den — men flera sonder per klass behövs
ändå, eftersom valet av cell kan bero på ordet (deponens, adjektiv utan
komparativcell som får perifrastisk komparation).

VARNING: siffran mäter svepet lika mycket som specen. En dimension som
saknas i `specar()` ser ut som en spec-brist utan att vara det. Två sådana
artefakter är redan hittade och rättade: subjektet var alltid tredje person
(hela person­böjningen såg onåbar ut) och attributet satt bara i objektet
(bara ackusativ mättes). Lägg till en dimension i svepet innan du drar
slutsatsen att specen inte når en cell.

Kör: .venv/bin/python ordbok/verktyg/nåbarhet.py [språk...] [-v]
"""
import sqlite3
import sys
from collections import defaultdict

from sprakprog.generering.granskning import _former_per_cell
from sprakprog.rendering import (
    Aspekt, Bestämdhet, Diates, Grad, Mening, Nominalfras, Numerus,
    Bisats, Prepositionsfras, RenderingsFel, Satsmodus, Tidsreferens, Uppslag,
)
from sprakprog.rendering import (
    EngelskRenderare, FranskRenderare, ItalienskRenderare, JapanskRenderare,
    SpanskRenderare, SvenskRenderare, TyskRenderare,
)

RENDERARE = {"sv": SvenskRenderare, "de": TyskRenderare, "en": EngelskRenderare,
             "fr": FranskRenderare, "es": SpanskRenderare,
             "it": ItalienskRenderare, "ja": JapanskRenderare}

# ── instrumentering ──────────────────────────────────────────────────
begärda: dict[str, set[str]] = defaultdict(set)
_original = Uppslag.form


def _loggande_form(self, lexem, cell):
    begärda[lexem["ordklass"]].add(cell)
    return _original(self, lexem, cell)


Uppslag.form = _loggande_form

# ── sonder ───────────────────────────────────────────────────────────
SUBJ = Nominalfras("pers_flicka", Bestämdhet.BESTÄMD)
SUBJEKT = [SUBJ,
           Nominalfras("pers_flicka", Bestämdhet.BESTÄMD, Numerus.PL),
           *(Nominalfras(p) for p in (
               "pronomen_1sg", "pronomen_2sg", "pronomen_3sg_fem",
               "pronomen_3sg_mask", "pronomen_1pl", "pronomen_2pl",
               "pronomen_3pl"))]
OBJ = "skol_bok"
# tre genus i de/fr/es/it, två i sv — samma koncept bär olika genus per språk
HUVUDORD = ["skol_bok", "fam_pappa", "fam_mamma", "fam_barn", "hem_hus"]
VERB_TRANS = ["fys_ge", "kom_läsa", "per_se"]
VERB_INTRANS = ["krop_v_sova", "rör_springa"]
MODALER = ["modal_kan", "modal_vill", "asp_börja", "gen_försöka"]
ADJ = ["färg_röd", "adj_s_stor", "adj_ev_vacker", "adj_es_glad"]
PREP = ["prep_i", "prep_på", "prep_med"]


def specar():
    """Alla meningsspecar som dagens `Mening` kan uttrycka."""
    # nominalfrasens inre: bestämdhet × numerus × attribut × possessiv × ägare,
    # i VARJE nominalfrasslot — kasus kommer in via slotten, så en attributiv
    # fras bara i objektet mäter bara ackusativ.
    for huvud in HUVUDORD:
        for best in Bestämdhet:
            for num in Numerus:
                for attribut in ((), ("färg_röd",)):
                    for poss in (None, "poss_3sg_fem"):
                        for ägare in (None, *(Nominalfras(
                                ä, Bestämdhet.BESTÄMD, attribut=("färg_röd",))
                                for ä in HUVUDORD)):
                            nf = Nominalfras(huvud, best, num, attribut, poss,
                                             possessiv_koreferent=poss is not None,
                                             ägare=ägare)
                            # subjekt (nom), objekt (ack), io (dat)
                            yield Mening("fys_ge", nf, objekt=Nominalfras(OBJ),
                                         io=Nominalfras("fam_bror"))
                            yield Mening("fys_ge", SUBJ, objekt=nf,
                                         io=Nominalfras("fam_bror"))
                            yield Mening("fys_ge", SUBJ, objekt=Nominalfras(OBJ), io=nf)
                            # prepositionens komplement
                            yield Mening("krop_v_sova", SUBJ, adverbial=(
                                Prepositionsfras("prep_i", nf),))
    # verbparametrar: tempus × aspekt × diates × negation × fråga,
    # för varje person — personen kommer in via subjektet, så pronomenen
    # måste vara med eller mäts hela böjningen som onåbar.
    for verb in VERB_TRANS + VERB_INTRANS:
        objekt = Nominalfras(OBJ) if verb in VERB_TRANS else None
        for subj in SUBJEKT:
            for tid in Tidsreferens:
                for aspekt in Aspekt:
                    for diates in Diates:
                        for negerad in (False, True):
                            for fråga in (False, True):
                                yield Mening(verb, subj, objekt=objekt, tid=tid,
                                             aspekt=aspekt, diates=diates,
                                             negerad=negerad, fråga=fråga)
    # predikativ: adjektiv och substantiv, i alla grader
    for adj in ADJ:
        for grad in Grad:
            for jfr in (None, Nominalfras("hem_hus", Bestämdhet.BESTÄMD)):
                for num in Numerus:
                    yield Mening("verb_vara",
                                 Nominalfras(OBJ, Bestämdhet.BESTÄMD, num),
                                 predikativ=adj, grad=grad, jämförelse=jfr)
    for tid in Tidsreferens:
        yield Mening("verb_vara", SUBJ, tid=tid,
                     predikativ=Nominalfras("yrke_läkare", Bestämdhet.OBESTÄMD))
    # infinitivkomplement
    for modal in MODALER:
        for tid in Tidsreferens:
            for negerad in (False, True):
                yield Mening(modal, SUBJ, komplement="kom_läsa",
                             tid=tid, negerad=negerad)
    # prepositionsfraser, som adverbial
    for prep in PREP:
        for best in Bestämdhet:
            yield Mening("krop_v_sova", SUBJ, adverbial=(
                Prepositionsfras(prep, Nominalfras("plats_skola", best)),))
    # imperativ: fyra tilltal × jakande/nekande. Tilltalet är subjektet,
    # och det är också det som väljer cell.
    for verb in VERB_TRANS + VERB_INTRANS:
        objekt = Nominalfras(OBJ) if verb in VERB_TRANS else None
        for tilltalad in ("pronomen_2sg", "pronomen_2pl",
                          "pronomen_2sg_formal", "pronomen_1pl"):
            for negerad in (False, True):
                yield Mening(verb, Nominalfras(tilltalad), objekt=objekt,
                             modus=Satsmodus.IMPERATIV, negerad=negerad)
    # bisatser: allt en huvudsats kan uttrycka går att uttrycka i bisats,
    # och i två språk med annan ordföljd. Japanskans enkla former (jisho,
    # ta, nai) är onåbara utan den här slingan.
    for verb in VERB_TRANS + VERB_INTRANS:
        objekt = Nominalfras(OBJ) if verb in VERB_TRANS else None
        for tid in Tidsreferens:
            for negerad in (False, True):
                for diates in Diates:
                    inre = Mening(verb, SUBJ, objekt=objekt, tid=tid,
                                  negerad=negerad, diates=diates)
                    yield Mening("kog_veta", SUBJ, bisats=Bisats("subj_att", inre))
                    yield Mening("krop_v_sova", SUBJ,
                                 adverbial=(Bisats("subj_när", inre),))
    # wh-frågor: tre argumentslottar plus sex frågadverb
    for fråga_om in ("subjekt", "objekt", "io", "frågadverb_tid",
                     "frågadverb_plats", "frågadverb_sätt", "frågadverb_orsak",
                     "frågadverb_riktning", "frågadverb_ursprung"):
        for tid in Tidsreferens:
            yield Mening("fys_ge", SUBJ, objekt=Nominalfras(OBJ),
                         io=Nominalfras("fam_bror"), tid=tid, fråga_om=fråga_om)
    # frågedeterminanter: hela frasen flyttas, huvudordet står kvar
    for det in ("interr_det_vilken", "interr_det_hur_många", "interr_det_hur_mycket"):
        for huvud in HUVUDORD:
            for num in Numerus:
                nf = Nominalfras(huvud, numerus=num, frågedeterminant=det)
                yield Mening("fys_ge", nf, objekt=Nominalfras(OBJ),
                             io=Nominalfras("fam_bror"), fråga_om="subjekt")
                yield Mening("fys_ge", SUBJ, objekt=nf,
                             io=Nominalfras("fam_bror"), fråga_om="objekt")
                yield Mening("fys_ge", SUBJ, objekt=Nominalfras(OBJ),
                             io=nf, fråga_om="io")
    # adverb
    yield Mening("fys_ge", SUBJ, objekt=Nominalfras(OBJ), adverbial=("adv_igår",),
                 tid=Tidsreferens.FÖRFLUTEN)


def mät(språk: str) -> tuple[int, int, dict[str, tuple[int, int]]]:
    conn = sqlite3.connect("sprak.db")
    conn.row_factory = sqlite3.Row
    begärda.clear()
    r = RENDERARE[språk](conn)
    fel = 0
    krascher: dict[str, str] = {}
    for m in specar():
        try:
            r.rendera(m)
        except RenderingsFel:
            fel += 1          # saknad form stoppar inte kartläggningen
        except Exception as e:  # ← inte RenderingsFel: en verklig krasch
            krascher.setdefault(
                f"{type(e).__name__}: {e}",
                f"{m.verb} tid={m.tid.value} aspekt={m.aspekt.value} "
                f"diates={m.diates.value} fråga={m.fråga} neg={m.negerad}")
    for sort, exempel in krascher.items():
        print(f"  ⚠ {språk}  {sort:40} ← {exempel}")

    # hela lexikonet mot den nåbara cellmängden
    upp = Uppslag(conn, språk)
    per_klass: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for lex in conn.execute(
            """SELECT l.*, k.ordklass FROM Lexem l JOIN Koncept k ON k.id=l.koncept_id
               WHERE l.språk = ?""", (språk,)):
        try:
            celler = _former_per_cell(
                conn.execute("SELECT * FROM Former WHERE lexem_id = ?",
                             (lex["id"],)).fetchall(),
                upp._slot_för(lex["ordklass"]))
        except Exception:
            continue
        nåbara = begärda.get(lex["ordklass"], set())
        for cell, form in celler.items():
            if not form:
                continue
            per_klass[lex["ordklass"]][1] += 1
            if cell in nåbara:
                per_klass[lex["ordklass"]][0] += 1
    nådda = sum(v[0] for v in per_klass.values())
    totalt = sum(v[1] for v in per_klass.values())
    return nådda, totalt, {k: tuple(v) for k, v in per_klass.items()}


if __name__ == "__main__":
    språk = sys.argv[1:] or list(RENDERARE)
    print(f"{'':4} {'nådda':>7} {'totalt':>7}   andel")
    for s in språk:
        nådda, totalt, per_klass = mät(s)
        print(f"{s:4} {nådda:7} {totalt:7}   {nådda / totalt:5.0%}")
        if "-v" in sys.argv:
            for klass, (n, t) in sorted(per_klass.items(), key=lambda x: -x[1][1]):
                print(f"       {klass:22} {n:6}/{t:<6} {n / t:4.0%}")
