"""Regressionsnät för de sju renderarna: spec → mening, fryst i en fil.

VARFÖR DET HÄR OCH INTE `rendera_prov.py`. Det verktyget skriver ut meningar
för en människa att läsa, och säger det själv: "inte något som kan verifieras
automatiskt". Det duger för att UPPTÄCKA fel men inte för att märka att något
annat gick sönder på vägen. `ögonblicksbild.py` skyddar datalagret, cell → form
per lexem. Mellan dem finns ett hål precis där renderarna bor.

Hålet blev akut när flera ändringar i renderarna pågick samtidigt: en rättelse
i tyskans ordföljd får inte tyst flytta något i franskan, och ingen läser 900
meningar för att kontrollera det.

FILEN SÄGER VAD SYSTEMET GÖR, INTE VAD SOM ÄR RÄTT. Kända fel står i den — det
är meningen. En rättelse SKA ge en diff, och diffen ska läsas: den visar exakt
vad som ändrades och, viktigare, vad som ändrades utöver det man tänkte ändra.
Att blint skriva om filen är att kasta bort hela nyttan.

KORPUSEN ÄR DESIGNAD OCH INTE SAMPLAD. Varje rad är en namngiven konstruktion,
så en diff går att läsa som "det här slutade fungera" i stället för "kandidat
417 ändrades". Ordförrådet är litet och fast, och varje koncept finns i alla
sju språken med former — annars mäter provet datatäckning i stället för
renderare.

EN FÖRLEGAD `__pycache__` KAN FÅ NÄTET ATT LJUGA. Byter man renderarfil på ett
sätt som inte flyttar fram mtime — `cp` från en säkerhetskopia, vissa
utcheckningar — kör Python vidare på gammal bytekod och diffen beskriver kod som
inte längre finns. Ser en diff omöjlig ut: `find src -name __pycache__ -exec rm
-rf {} +` och kör om.

Kör:  python ordbok/verktyg/renderarbild.py            jämför mot filen
      python ordbok/verktyg/renderarbild.py --skriv    skriv om den
      python ordbok/verktyg/renderarbild.py --src X    jämför ett ANNAT träds
                                                       renderare mot bilden
"""
from __future__ import annotations

import sys
from pathlib import Path

# --src pekar ut ETT ANNAT renderarbibliotek än det här trädets. Det är så
# man jämför en gren mot basbilden utan att checka ut den: worktreen har sin
# egen `src`, och `sprak.db` och bilden ligger kvar här.
_SRC = (sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv
        else str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(_SRC).resolve()))

import sqlite3

from sprakprog.rendering import (
    Aspekt, Attribut, Bestämdhet, Bisats, Diates, EngelskRenderare,
    FranskRenderare, Grad, ItalienskRenderare, JapanskRenderare, Mening,
    Nominalfras, Numerus, Prepositionsfras, Referentgenus, RenderingsFel,
    Satsmodus, SpanskRenderare, SvenskRenderare, Tidsreferens, TyskRenderare,
)

BILD = Path(__file__).resolve().parents[2] / "paradigm" / "renderarbild.tsv"

RENDERARE = {"sv": SvenskRenderare, "en": EngelskRenderare, "de": TyskRenderare,
             "fr": FranskRenderare, "es": SpanskRenderare,
             "it": ItalienskRenderare, "ja": JapanskRenderare}

# Fast ordförråd. Alla finns i sju språk med former (kontrollerat 2026-08-15).
HUND = Nominalfras("djur_hund", Bestämdhet.BESTÄMD)
KATT = Nominalfras("djur_katt", Bestämdhet.OBESTÄMD)
HÄST = Nominalfras("djur_häst", Bestämdhet.BESTÄMD, Numerus.PL)
HON = Nominalfras("pronomen_3sg_fem")
# Referentgenus behövs på pluralpronomen: spanskan och franskan har två
# lemman (nosotros/nosotras, ils/elles) och specen måste peka ut ett.
VI = Nominalfras("pronomen_1pl", referent=Referentgenus.MASKULIN)
DE = Nominalfras("pronomen_3pl", referent=Referentgenus.FEMININ)
DU = Nominalfras("pronomen_2sg")


def _m(**kw) -> Mening:
    kw.setdefault("subjekt", HON)
    return Mening(**kw)


#: (namn, mening). Namnet är konstruktionen, inte ett nummer — en diff ska
#: gå att läsa som "det här slutade fungera".
KORPUS: tuple[tuple[str, Mening], ...] = (
    # ── kärnan ────────────────────────────────────────────────────────
    ("intransitiv", _m(verb="ext_leva")),
    ("transitiv", _m(verb="fys_hitta", objekt=HUND)),
    ("transitiv-obestämd", _m(verb="fys_köpa", objekt=KATT)),
    ("plural-objekt", _m(verb="fys_hålla", objekt=HÄST)),
    ("pronomen-subjekt-1pl", _m(verb="arb_arbeta", subjekt=VI)),
    ("bitransitiv", _m(verb="fys_ge", objekt=HUND, io=DE)),

    # ── tempus och aspekt ─────────────────────────────────────────────
    ("preteritum", _m(verb="arb_leka", tid=Tidsreferens.FÖRFLUTEN)),
    ("futurum", _m(verb="fys_göra", objekt=HUND, tid=Tidsreferens.FRAMTID)),
    ("perfekt", _m(verb="fys_stänga", objekt=HUND, aspekt=Aspekt.PERFEKT)),
    ("pluskvamperfekt", _m(verb="fys_hitta", objekt=KATT,
                           tid=Tidsreferens.FÖRFLUTEN, aspekt=Aspekt.PERFEKT)),
    ("futurum-perfekt", _m(verb="fys_köpa", objekt=KATT,
                           tid=Tidsreferens.FRAMTID, aspekt=Aspekt.PERFEKT)),

    # ── negation, fråga, passiv ───────────────────────────────────────
    ("negation", _m(verb="arb_hjälpa", objekt=HUND, negerad=True)),
    ("negation-preteritum", _m(verb="arb_leka", negerad=True,
                               tid=Tidsreferens.FÖRFLUTEN)),
    ("ja-nej-fråga", _m(verb="fys_använda", objekt=HUND, fråga=True)),
    ("fråga-negerad", _m(verb="fys_hitta", objekt=KATT, fråga=True, negerad=True)),
    ("passiv", _m(verb="fys_göra", subjekt=HUND, diates=Diates.PASSIV)),
    ("passiv-perfekt", _m(verb="fys_stänga", subjekt=HUND,
                          diates=Diates.PASSIV, aspekt=Aspekt.PERFEKT)),
    ("passiv-futurum", _m(verb="fys_köpa", subjekt=KATT,
                          diates=Diates.PASSIV, tid=Tidsreferens.FRAMTID)),

    # ── nominalfrasens inre ───────────────────────────────────────────
    ("attribut", _m(verb="fys_hitta",
                    objekt=Nominalfras("djur_hund", Bestämdhet.BESTÄMD,
                                       attribut=("adj_ev_snäll",)))),
    ("attribut-obestämd", _m(verb="fys_köpa",
                             objekt=Nominalfras("djur_katt", attribut=("adj_ev_vacker",)))),
    ("attribut-plural", _m(verb="fys_hålla",
                           objekt=Nominalfras("djur_häst", Bestämdhet.BESTÄMD,
                                              Numerus.PL, ("adj_ev_rolig",)))),
    ("possessiv", _m(verb="fys_hitta",
                     objekt=Nominalfras("djur_hund", possessiv="poss_1sg"))),
    ("possessiv-plural", _m(verb="fys_hålla",
        objekt=Nominalfras("djur_häst", numerus=Numerus.PL, possessiv="poss_3pl"))),
    ("genitivägare", _m(verb="fys_hitta",
                        objekt=Nominalfras("djur_hund", Bestämdhet.BESTÄMD,
                                           ägare=Nominalfras("djur_katt",
                                                             Bestämdhet.BESTÄMD)))),
    ("artikellös-plural", _m(verb="fys_hitta",
                             objekt=Nominalfras("djur_fisk", Bestämdhet.OBESTÄMD,
                                                Numerus.PL))),

    # ── predikativ och komparation ────────────────────────────────────
    ("predikativ-adjektiv", _m(verb="verb_vara", predikativ="adj_es_glad")),
    ("predikativ-plural", _m(verb="verb_vara", subjekt=VI, predikativ="adj_es_frisk")),
    ("komparativ", _m(verb="verb_vara", predikativ="adj_ev_rolig",
                      grad=Grad.KOMPARATIV)),
    ("superlativ", _m(verb="verb_vara", predikativ="adj_ev_vacker",
                      grad=Grad.SUPERLATIV)),
    ("jämförelse", _m(verb="verb_vara", predikativ="adj_ev_snäll",
                      grad=Grad.KOMPARATIV, jämförelse=HUND)),
    ("attributiv-komparativ", _m(verb="fys_hitta",
        objekt=Nominalfras("djur_hund", Bestämdhet.BESTÄMD,
                           attribut=(Attribut("adj_ev_rolig", Grad.KOMPARATIV),)))),

    # ── adverbial ─────────────────────────────────────────────────────
    ("prepositionsfras", _m(verb="arb_arbeta",
                            adverbial=(Prepositionsfras("prep_bakom", HUND),))),
    ("två-adverbial", _m(verb="arb_leka",
                         adverbial=(Prepositionsfras("prep_framför", HUND),
                                    Prepositionsfras("prep_bredvid", KATT)))),

    # ── infinitiv, imperativ, bisats, wh ──────────────────────────────
    ("infinitivkomplement", _m(verb="asp_börja", komplement="arb_arbeta")),
    ("infinitiv-negerad", _m(verb="asp_sluta", komplement="arb_leka", negerad=True)),
    ("infinitiv-futurum", _m(verb="asp_börja", komplement="fys_göra",
                             tid=Tidsreferens.FRAMTID)),
    ("imperativ", _m(verb="fys_stänga", subjekt=DU, objekt=HUND,
                     modus=Satsmodus.IMPERATIV)),
    ("imperativ-plural", _m(verb="arb_hjälpa", subjekt=Nominalfras("pronomen_2pl"),
                            objekt=HUND, modus=Satsmodus.IMPERATIV)),
    # Verbalkomplexet: ren infinitiv mot zu-infinitiv, i huvudsats och bisats,
    # med och utan hjälpverb i slutfältet. Tillagda 2026-08-15 därför att den
    # första korpusen INTE täckte dem — tre parallella rättelser arbetade i
    # precis den luckan och nätet såg inget. Ett regressionsnät är bara så bra
    # som sin korpus, och den växer när man upptäcker var den är tunn.
    ("modal-ren-infinitiv", _m(verb="modal_kan", komplement="arb_arbeta")),
    ("modal-futurum", _m(verb="modal_bör", komplement="arb_leka",
                         tid=Tidsreferens.FRAMTID)),
    ("modal-perfekt", _m(verb="modal_kan", komplement="arb_arbeta",
                         aspekt=Aspekt.PERFEKT)),
    ("modal-negerad-futurum", _m(verb="modal_får", komplement="fys_ge",
                                 negerad=True, tid=Tidsreferens.FRAMTID)),
    ("zu-infinitiv", _m(verb="gen_försöka", komplement="arb_arbeta")),
    ("zu-infinitiv-futurum", _m(verb="gen_försöka", komplement="arb_leka",
                                tid=Tidsreferens.FRAMTID)),
    ("zu-infinitiv-perfekt", _m(verb="gen_försöka", komplement="arb_arbeta",
                                aspekt=Aspekt.PERFEKT)),
    ("modal-i-bisats", _m(verb="kog_förstå", bisats=Bisats("subj_att",
        Mening(verb="modal_kan", subjekt=VI, komplement="arb_arbeta")))),
    ("modal-i-bisats-futurum", _m(verb="kog_förstå", bisats=Bisats("subj_att",
        Mening(verb="modal_bör", subjekt=VI, komplement="arb_leka",
               tid=Tidsreferens.FRAMTID)))),
    ("modal-i-bisats-perfekt", _m(verb="kog_minnas", bisats=Bisats("subj_att",
        Mening(verb="modal_kan", subjekt=VI, komplement="arb_arbeta",
               aspekt=Aspekt.PERFEKT)))),
    ("zu-infinitiv-i-bisats", _m(verb="kog_förstå", bisats=Bisats("subj_att",
        Mening(verb="gen_försöka", subjekt=VI, komplement="arb_arbeta")))),
    ("zu-infinitiv-i-bisats-futurum", _m(verb="kog_förstå", bisats=Bisats("subj_att",
        Mening(verb="gen_försöka", subjekt=VI, komplement="arb_leka",
               tid=Tidsreferens.FRAMTID)))),

    ("bisats", _m(verb="kog_förstå",
                  bisats=Bisats("subj_att", Mening(verb="arb_arbeta", subjekt=VI)))),
    ("bisats-preteritum", _m(verb="kog_minnas",
        bisats=Bisats("subj_att", Mening(verb="fys_köpa", subjekt=VI, objekt=KATT,
                                         tid=Tidsreferens.FÖRFLUTEN)))),
    ("bisats-negerad", _m(verb="gen_tycka",
        bisats=Bisats("subj_att", Mening(verb="arb_leka", subjekt=VI, negerad=True)))),
    ("adverbialbisats", _m(verb="arb_arbeta",
        adverbial=(Bisats("subj_när", Mening(verb="arb_leka", subjekt=VI)),))),
    ("wh-subjekt", _m(verb="fys_hitta", objekt=HUND, fråga_om="subjekt")),
    ("wh-objekt", _m(verb="fys_hitta", objekt=HUND, fråga_om="objekt")),
    ("wh-negerad", _m(verb="fys_köpa", objekt=KATT, fråga_om="objekt", negerad=True)),
)


def rendera_alla(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """(konstruktion, språk, utfall) för hela korpusen.

    Ett fel är också ett utfall och skrivs ut. En konstruktion som SLUTAR
    kastas är lika intressant som en som börjar.
    """
    ut = []
    for språk, klass in RENDERARE.items():
        r = klass(conn)
        for namn, m in KORPUS:
            try:
                ut.append((namn, språk, r.rendera(m)))
            except RenderingsFel as e:
                ut.append((namn, språk, f"FEL {e}"))
            except Exception as e:                 # noqa: BLE001
                ut.append((namn, språk, f"KRASCH {type(e).__name__}: {e}"))
    return ut


def läs() -> dict[tuple[str, str], str]:
    if not BILD.exists():
        return {}
    return {(d[0], d[1]): d[2]
            for rad in BILD.read_text(encoding="utf-8").splitlines()[1:]
            if len(d := rad.split("\t")) == 3}


def main() -> int:
    conn = sqlite3.connect("sprak.db")
    conn.row_factory = sqlite3.Row
    nu = rendera_alla(conn)
    fel = sum(1 for _, _, t in nu if t.startswith(("FEL", "KRASCH")))
    print(f"{len(KORPUS)} konstruktioner × 7 språk = {len(nu)} rader, "
          f"{fel} utan resultat")

    if "--src" in sys.argv:
        print(f"renderare ur {_SRC}")
    if "--skriv" in sys.argv:
        if "--src" in sys.argv:
            print("Vägrar skriva bilden från ett annat träd — bilden hör till "
                  "det här trädets kod.")
            return 1
        BILD.write_text("konstruktion\tspråk\tutfall\n" + "".join(
            f"{n}\t{s}\t{t}\n" for n, s, t in nu), encoding="utf-8")
        print(f"→ {BILD.relative_to(BILD.parents[1])}")
        return 0

    förr = läs()
    if not förr:
        print("Ingen bild finns än. Kör med --skriv för att lägga grunden.")
        return 1

    ändrade = [(n, s, förr.get((n, s), "—"), t) for n, s, t in nu
               if förr.get((n, s), "—") != t]
    if not ändrade:
        print("✓ Ingen skillnad mot bilden.")
        return 0

    print(f"\n{len(ändrade)} rader skiljer sig. LÄS DEM — en rättelse ska ge "
          f"en diff,\nmen bara den diff man tänkte sig.\n")
    for n, s, gammalt, nytt in ändrade:
        print(f"  {s}  {n}")
        print(f"      förr  {gammalt}")
        print(f"      nu    {nytt}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
