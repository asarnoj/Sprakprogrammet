"""ordbok rendera — bygg en mening ur en specifikation och skriv ut den.

  ordbok rendera --exempel
  ordbok rendera --spec mening.json --språk sv

Specifikationen är språkoberoende; `--språk` väljer vilken renderare som
läser den. Bara svenska finns än.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..db import STANDARD_DB, anslut
from ..rendering import (
    Bestämdhet, Mening, Nominalfras, Numerus, RenderingsFel, Tidsreferens,
)

RENDERARE = ("sv", "de", "fr")

# Meningen ur paradigm/RENDERARE_KRAV.md §1, den som hela kravlistan togs
# fram ur. Att den renderas korrekt är den vertikala skivans kvitto.
EXEMPEL = Mening(
    verb="fys_ge",
    subjekt=Nominalfras("pers_flicka", Bestämdhet.BESTÄMD),
    io=Nominalfras("fam_bror", possessiv="poss_3sg_fem", possessiv_koreferent=True),
    objekt=Nominalfras("skol_bok", attribut=("färg_röd",)),
    adverbial=("adv_igår",),
    tid=Tidsreferens.FÖRFLUTEN,
)


def _nominalfras(d: dict) -> Nominalfras:
    return Nominalfras(
        koncept=d["koncept"],
        bestämdhet=Bestämdhet(d.get("bestämdhet", "obestämd")),
        numerus=Numerus(d.get("numerus", "sg")),
        attribut=tuple(d.get("attribut", ())),
        possessiv=d.get("possessiv"),
        possessiv_koreferent=bool(d.get("possessiv_koreferent", False)),
    )


def _mening(d: dict) -> Mening:
    return Mening(
        verb=d["verb"],
        subjekt=_nominalfras(d["subjekt"]),
        objekt=_nominalfras(d["objekt"]) if d.get("objekt") else None,
        io=_nominalfras(d["io"]) if d.get("io") else None,
        adverbial=tuple(d.get("adverbial", ())),
        tid=Tidsreferens(d.get("tid", "nutid")),
    )


def lägg_till_argument(p: argparse.ArgumentParser) -> None:
    p.add_argument("--spec", help="JSON-fil med meningsspecifikationen")
    p.add_argument("--exempel", action="store_true",
                   help="Rendera exempelmeningen ur RENDERARE_KRAV.md §1")
    p.add_argument("--språk", default="sv", choices=sorted(RENDERARE),
                   help="Målspråk. sv, de och fr finns; övriga fyra är inte byggda.")


def kör(args: argparse.Namespace) -> int:
    if not args.spec and not args.exempel:
        print("FEL: ange --spec eller --exempel.", file=sys.stderr)
        return 1
    if not STANDARD_DB.exists():
        print(f"FEL: {STANDARD_DB.name} finns inte.", file=sys.stderr)
        return 1

    mening = EXEMPEL if args.exempel else _mening(
        json.loads(Path(args.spec).read_text(encoding="utf-8")))

    from ..rendering import FranskRenderare, SvenskRenderare, TyskRenderare
    renderare = {"sv": SvenskRenderare, "de": TyskRenderare,
                 "fr": FranskRenderare}[args.språk]
    conn = anslut()
    try:
        print(renderare(conn).rendera(mening))
    except RenderingsFel as e:
        print(f"Kan inte rendera: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0
