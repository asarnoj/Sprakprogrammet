"""Facit för renderarna: samma specar före och efter en ombyggnad.

Steg 1 i KÄRNAN bygger om renderarna så att varje beslut redovisas, men den
utskrivna texten får inte ändras. Verktyget renderar en stor, fast mängd
specar och sparar resultatet; efter ombyggnaden renderas samma specar igen och
varje skillnad skrivs ut.

Specarna kommer ur den gamla samplaren med ett fast frö, plus varianter som
samplaren inte själv bygger: bli-passiv, predikativ komparation, imperativ,
naken fras, frågedeterminant, reflexiv possessiv och negerade bisatser.
Samplaren används bara som källa till testdata; den nya kärnan importerar den
inte (KÄRNAN 8.1).

Ett resultat är texten, eller felets klass när renderaren vägrar. Felmeddelandet
jämförs inte, eftersom det får skrivas om.

Kör:  python ordbok/verktyg/renderarfacit.py spara sv FIL
      python ordbok/verktyg/renderarfacit.py jämför sv FIL
"""
from __future__ import annotations

import pickle
import random
import sqlite3
import sys
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.rendering import RENDERARE, RenderingsFel          # noqa: E402
from sprakprog.rendering import spec as S                          # noqa: E402
from sprakprog.generator.urval import Ordförråd, Samplare, upplåst  # noqa: E402

ANTAL = 100000
FRÖ = 20260913
TILLTALADE = ("pronomen_2sg", "pronomen_2pl", "pronomen_2sg_formal",
              "pronomen_1pl")


def _nf_variant(nf: S.Nominalfras, rng, o: Ordförråd) -> S.Nominalfras:
    if o.ordklass.get(nf.koncept) == "Pronomen":
        return nf
    val = rng.randrange(6)
    if val == 0:
        return replace(nf, bestämdhet=rng.choice(list(S.Bestämdhet)))
    if val == 1 and nf.attribut:
        return replace(nf, bestämdhet=S.Bestämdhet.BESTÄMD, attribut=(
            S.Attribut(S.attribut_med_grad(nf.attribut[0]).koncept,
                       rng.choice(list(S.Grad))),))
    if val == 2 and o.per_ordklass.get("Interrogativdeterminant"):
        return replace(nf, frågedeterminant=rng.choice(
            o.per_ordklass["Interrogativdeterminant"]), possessiv=None,
            ägare=None)
    if val == 3 and o.per_ordklass.get("Possessiv"):
        return replace(nf, possessiv=rng.choice(o.per_ordklass["Possessiv"]),
                       possessiv_koreferent=rng.random() < 0.5, ägare=None)
    if val == 4:
        return replace(nf, numerus=rng.choice(list(S.Numerus)))
    return replace(nf, referent=rng.choice([None, *S.Referentgenus]))


def varianter(m: S.Mening, rng, o: Ordförråd) -> list[S.Mening]:
    ut = []
    for _ in range(3):
        v = m
        for _ in range(rng.randrange(1, 4)):
            val = rng.randrange(12)
            if val == 0 and v.objekt is not None:
                v = replace(v, subjekt=v.objekt, objekt=None,
                            diates=rng.choice([S.Diates.PASSIV,
                                               S.Diates.PASSIV_HÄNDELSE]))
            elif val == 1 and isinstance(v.predikativ, str):
                grad = rng.choice([S.Grad.KOMPARATIV, S.Grad.SUPERLATIV])
                v = replace(v, grad=grad, jämförelse=(
                    v.subjekt if grad is S.Grad.KOMPARATIV
                    and rng.random() < 0.5 else None))
            elif val == 2:
                v = replace(v, aspekt=rng.choice(list(S.Aspekt)),
                            tid=rng.choice(list(S.Tidsreferens)))
            elif val == 3:
                v = replace(v, negerad=not v.negerad)
            elif val == 4:
                v = replace(v, fråga=not v.fråga)
            elif val == 5:
                v = replace(v, modus=S.Satsmodus.IMPERATIV, fråga=False,
                            fråga_om=None,
                            subjekt=S.Nominalfras(rng.choice(TILLTALADE)))
            elif val == 6:
                v = replace(v, subjekt=_nf_variant(v.subjekt, rng, o))
            elif val == 7 and v.objekt is not None:
                v = replace(v, objekt=_nf_variant(v.objekt, rng, o))
            elif val == 8 and v.bisats is not None:
                v = replace(v, bisats=replace(v.bisats, sats=replace(
                    v.bisats.sats, negerad=True,
                    aspekt=rng.choice(list(S.Aspekt)))))
            elif val == 9:
                pronomen = o.per_ordklass.get("Pronomen", [])
                if pronomen:
                    v = replace(v, subjekt=S.Nominalfras(rng.choice(pronomen)))
            elif val == 10 and v.objekt is not None:
                v = replace(v, fråga_om=rng.choice(["subjekt", "objekt"]),
                            fråga=False)
            elif val == 11:
                v = replace(v, predikativ=None, grad=S.Grad.POSITIV,
                            jämförelse=None)
        ut.append(v)
    return ut


def specar(conn, språk: str) -> list[S.Mening]:
    rng = random.Random(FRÖ)
    o = Ordförråd(conn, språk)
    samplare = Samplare(o, 21, rng, tillåtet=upplåst(21))
    ut: list[S.Mening] = []
    försök = 0
    while len(ut) < ANTAL and försök < ANTAL * 20:
        försök += 1
        m = samplare.kandidat()
        if m is None:
            continue
        ut.append(m)
        ut.extend(varianter(m, rng, o))
    return ut


def utfall(renderare, m: S.Mening) -> str:
    try:
        return renderare.rendera(m)
    except RenderingsFel:
        return "FEL:RenderingsFel"
    except Exception as e:                                          # noqa: BLE001
        return f"FEL:{type(e).__name__}"


def main() -> None:
    läge, språk, fil = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    conn = sqlite3.connect(ROT / "sprak.db")
    conn.row_factory = sqlite3.Row
    renderare = RENDERARE[språk](conn)
    t = time.perf_counter()
    if läge == "spara":
        lista = specar(conn, språk)
        facit = [(m, utfall(renderare, m)) for m in lista]
        fil.write_bytes(pickle.dumps(facit))
        typer = Counter(u if u.startswith("FEL:") else "text" for _, u in facit)
        print(f"{len(facit)} specar sparade, {len({u for _, u in facit})} olika "
              f"utfall, {dict(typer)}, {time.perf_counter() - t:.1f} s")
        return
    facit = pickle.loads(fil.read_bytes())
    skillnader = [(m, före, efter) for m, före in facit
                  if (efter := utfall(renderare, m)) != före]
    print(f"{len(facit)} specar jämförda, {len(skillnader)} skillnader, "
          f"{time.perf_counter() - t:.1f} s")
    for m, före, efter in skillnader[:25]:
        print(f"  före:  {före}\n  efter: {efter}\n  spec:  {m}\n")
    sys.exit(1 if skillnader else 0)


if __name__ == "__main__":
    main()
